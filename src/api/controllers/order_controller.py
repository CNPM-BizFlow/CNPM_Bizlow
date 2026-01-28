# Order Controller - Order management endpoints

from flask import Blueprint, request
from api.responses import success_response, error_response, created_response, paginated_response
from api.decorators import require_auth, require_permission, get_current_user_identity
from services.auth_service import AuthService
from services.order_service import OrderService
from domain.exceptions import BizFlowException

order_bp = Blueprint('orders', __name__, url_prefix='/api/v1')


@order_bp.route('/orders', methods=['POST'])
@require_auth
@require_permission('create_orders')
def create_order():
    """
    Create a new order (at-counter sale)
    ---
    tags:
      - Orders
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
            - items
          properties:
            store_id:
              type: integer
            customer_id:
              type: integer
            is_credit:
              type: boolean
              default: false
            notes:
              type: string
            items:
              type: array
              items:
                type: object
                required:
                  - product_unit_id
                  - quantity
                properties:
                  product_unit_id:
                    type: integer
                  quantity:
                    type: number
                  unit_price:
                    type: number
                  discount:
                    type: number
    responses:
      201:
        description: Order created
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        order = OrderService.create_order(
            store_id=data.get('store_id'),
            items=data.get('items', []),
            current_user=current_user,
            customer_id=data.get('customer_id'),
            is_credit=data.get('is_credit', False),
            notes=data.get('notes')
        )
        
        return created_response(data=order.to_dict(), message="Tạo đơn hàng thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@order_bp.route('/orders', methods=['GET'])
@require_auth
@require_permission('view_orders')
def list_orders():
    """
    List orders for a store
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
      - in: query
        name: status
        type: string
        enum: [new, confirmed, completed, canceled]
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
    responses:
      200:
        description: List of orders
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        result = OrderService.get_orders(store_id, current_user, page, per_page, status)
        
        return paginated_response(
            result['items'],
            result['page'],
            result['per_page'],
            result['total']
        )
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@require_auth
@require_permission('view_orders')
def get_order(order_id):
    """Get order details"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        order = OrderService.get_order_by_id(order_id, current_user)
        
        return success_response(data=order.to_dict())
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@order_bp.route('/orders/<int:order_id>/confirm', methods=['PATCH'])
@require_auth
@require_permission('manage_orders')
def confirm_order(order_id):
    """
    Confirm order and update inventory
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    responses:
      200:
        description: Order confirmed
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        order = OrderService.confirm_order(order_id, current_user)
        
        return success_response(data=order.to_dict(), message="Xác nhận đơn hàng thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@order_bp.route('/orders/<int:order_id>/cancel', methods=['PATCH'])
@require_auth
@require_permission('manage_orders')
def cancel_order(order_id):
    """Cancel an order"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json() or {}
        
        order = OrderService.cancel_order(order_id, current_user, data.get('reason'))
        
        return success_response(data=order.to_dict(), message="Hủy đơn hàng thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@order_bp.route('/orders/<int:order_id>/print', methods=['GET'])
@require_auth
@require_permission('view_orders')
def print_order(order_id):
    """
    Get printable order (HTML format)
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    responses:
      200:
        description: Printable HTML
        content:
          text/html:
            schema:
              type: string
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        order = OrderService.get_order_by_id(order_id, current_user)
        
        # Generate simple HTML invoice
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Hóa đơn #{order.order_number}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 80mm; }}
        h1 {{ font-size: 18px; text-align: center; }}
        .info {{ margin: 10px 0; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        th, td {{ border-bottom: 1px dashed #ccc; padding: 5px 0; text-align: left; }}
        .total {{ font-weight: bold; font-size: 14px; margin-top: 10px; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 10px; }}
    </style>
</head>
<body>
    <h1>HÓA ĐƠN BÁN HÀNG</h1>
    <div class="info">
        <p><strong>Số HĐ:</strong> {order.order_number}</p>
        <p><strong>Ngày:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else ''}</p>
        <p><strong>Khách hàng:</strong> {order.customer.name if order.customer else 'Khách lẻ'}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Sản phẩm</th>
                <th>SL</th>
                <th>Đơn giá</th>
                <th>T.Tiền</th>
            </tr>
        </thead>
        <tbody>
"""
        for item in order.items.all():
            html += f"""
            <tr>
                <td>{item.product.name if item.product else ''}</td>
                <td>{float(item.quantity)}</td>
                <td>{float(item.unit_price):,.0f}</td>
                <td>{float(item.line_total):,.0f}</td>
            </tr>
"""
        
        html += f"""
        </tbody>
    </table>
    <div class="total">
        <p>TỔNG CỘNG: {float(order.total_amount):,.0f} VNĐ</p>
        {'<p style="color: red;">CÔNG NỢ</p>' if order.is_credit else '<p>ĐÃ THANH TOÁN</p>'}
    </div>
    <div class="footer">
        <p>Cảm ơn quý khách!</p>
        <p>Powered by BizFlow</p>
    </div>
</body>
</html>
"""
        from flask import Response
        return Response(html, mimetype='text/html')
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)
