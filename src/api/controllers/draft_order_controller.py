# Draft Order Controller - AI draft order endpoints

from flask import Blueprint, request, Response
from api.responses import success_response, error_response, created_response
from api.decorators import require_auth, require_permission, get_current_user_identity
from services.auth_service import AuthService
from services.ai_draft_service import AIDraftService
from domain.exceptions import BizFlowException

draft_bp = Blueprint('drafts', __name__, url_prefix='/api/v1')


@draft_bp.route('/ai/draft-orders', methods=['POST'])
@require_auth
@require_permission('confirm_draft_orders')
def create_draft_order():
    """
    Create draft order from natural language (AI)
    ---
    tags:
      - AI Draft Orders
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - store_id
            - text
          properties:
            store_id:
              type: integer
            text:
              type: string
              description: Natural language order text
              example: "Lấy 5 bao xi măng cho chú Ba, ghi nợ"
            source_type:
              type: string
              enum: [text, voice]
              default: text
    responses:
      201:
        description: Draft order created
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                id:
                  type: integer
                parsed_data:
                  type: object
                warnings:
                  type: array
                  items:
                    type: string
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        store_id = data.get('store_id')
        if not current_user.can_access_store(store_id):
            from domain.exceptions import AuthorizationError
            raise AuthorizationError()
        
        text = data.get('text')
        if not text:
            return error_response("VALIDATION_ERROR", "Nội dung đơn hàng là bắt buộc", status_code=400)
        
        source_type = data.get('source_type', 'text')
        
        draft = AIDraftService.create_draft_order(store_id, text, source_type)
        
        message = "Đã tạo đơn nháp"
        if draft.has_warnings:
            message += f" với {len(draft.warnings)} cảnh báo cần xác nhận"
        
        return created_response(data=draft.to_dict(), message=message)
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@draft_bp.route('/draft-orders', methods=['GET'])
@require_auth
@require_permission('confirm_draft_orders')
def list_draft_orders():
    """List pending draft orders"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        drafts = AIDraftService.get_pending_drafts(store_id, current_user)
        
        return success_response(data=drafts)
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@draft_bp.route('/draft-orders/<int:draft_id>/confirm', methods=['PATCH'])
@require_auth
@require_permission('confirm_draft_orders')
def confirm_draft_order(draft_id):
    """
    Confirm draft order and create actual order (BR-04)
    ---
    tags:
      - AI Draft Orders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: draft_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            modifications:
              type: object
              description: Optional modifications to the parsed data
    responses:
      200:
        description: Draft confirmed and order created
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json() or {}
        
        result = AIDraftService.confirm_draft_order(
            draft_id,
            current_user,
            modifications=data.get('modifications')
        )
        
        return success_response(
            data=result,
            message=f"Xác nhận thành công. Đã tạo đơn hàng #{result['order']['order_number']}"
        )
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@draft_bp.route('/draft-orders/<int:draft_id>/reject', methods=['PATCH'])
@require_auth
@require_permission('confirm_draft_orders')
def reject_draft_order(draft_id):
    """Reject a draft order"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json() or {}
        
        draft = AIDraftService.reject_draft_order(
            draft_id,
            current_user,
            reason=data.get('reason')
        )
        
        return success_response(data=draft.to_dict(), message="Đã từ chối đơn nháp")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@draft_bp.route('/draft-orders/notifications', methods=['GET'])
@require_auth
def draft_order_notifications():
    """
    SSE endpoint for realtime draft order notifications
    ---
    tags:
      - AI Draft Orders
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
    responses:
      200:
        description: SSE stream
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            from domain.exceptions import AuthorizationError
            raise AuthorizationError()
        
        def generate():
            """SSE generator for draft order notifications."""
            import time
            import json
            from extensions import get_redis
            
            redis = get_redis()
            
            if redis:
                # Use Redis pub/sub
                pubsub = redis.pubsub()
                pubsub.subscribe(f'draft_orders:{store_id}')
                
                try:
                    for message in pubsub.listen():
                        if message['type'] == 'message':
                            data = message['data']
                            yield f"data: {data}\n\n"
                finally:
                    pubsub.unsubscribe()
            else:
                # Fallback: simple polling
                last_check = time.time()
                while True:
                    # Check for new drafts
                    from infrastructure.models import DraftOrder
                    from domain.constants import DraftOrderStatus
                    
                    new_drafts = DraftOrder.query.filter(
                        DraftOrder.store_id == store_id,
                        DraftOrder.status == DraftOrderStatus.DRAFT,
                        DraftOrder.created_at >= last_check
                    ).all()
                    
                    for draft in new_drafts:
                        yield f"data: {json.dumps(draft.to_dict())}\n\n"
                    
                    last_check = time.time()
                    time.sleep(5)  # Poll every 5 seconds
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)
