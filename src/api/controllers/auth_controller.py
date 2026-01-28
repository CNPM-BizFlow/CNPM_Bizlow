# Auth Controller - Authentication endpoints

from flask import Blueprint, request
from flasgger import swag_from
from api.responses import success_response, error_response
from api.decorators import require_auth
from services.auth_service import AuthService
from domain.exceptions import BizFlowException

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: owner@bizflow.vn
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                access_token:
                  type: string
                refresh_token:
                  type: string
                user:
                  type: object
      401:
        description: Invalid credentials
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("VALIDATION_ERROR", "Request body is required", status_code=400)
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return error_response("VALIDATION_ERROR", "Email và mật khẩu là bắt buộc", status_code=400)
        
        result = AuthService.login(email, password)
        return success_response(data=result, message="Đăng nhập thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@auth_bp.route('/register-admin', methods=['POST'])
def register_admin():
    """
    Register initial admin (first-time setup only)
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - full_name
          properties:
            email:
              type: string
            password:
              type: string
            full_name:
              type: string
    responses:
      201:
        description: Admin created
      409:
        description: Admin already exists
    """
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        if not all([email, password, full_name]):
            return error_response("VALIDATION_ERROR", "Thiếu thông tin bắt buộc", status_code=400)
        
        user = AuthService.register_admin(email, password, full_name)
        return success_response(data=user.to_dict(), message="Tạo admin thành công", status_code=201)
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    """
    Get current user info
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user info
    """
    try:
        from flask import g
        identity = g.current_user_identity
        user = AuthService.get_current_user(identity)
        return success_response(data=user.to_dict())
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)