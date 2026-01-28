# User Controller - User management endpoints

from flask import Blueprint, request, g
from api.responses import success_response, error_response, created_response
from api.decorators import require_auth, require_role, get_current_user_identity
from services.user_service import UserService
from services.auth_service import AuthService
from domain.constants import Role, UserStatus
from domain.exceptions import BizFlowException

user_bp = Blueprint('users', __name__, url_prefix='/api/v1')


@user_bp.route('/owners', methods=['POST'])
@require_auth
@require_role(Role.ADMIN)
def create_owner():
    """
    Create a new owner with store (Admin only)
    ---
    tags:
      - Users
    security:
      - Bearer: []
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
            phone:
              type: string
            store_name:
              type: string
    responses:
      201:
        description: Owner created with store
      403:
        description: Admin access required
    """
    try:
        data = request.get_json()
        
        result = UserService.create_owner(
            email=data.get('email'),
            password=data.get('password'),
            full_name=data.get('full_name'),
            phone=data.get('phone'),
            store_name=data.get('store_name')
        )
        
        return created_response(data=result, message="Tạo chủ cửa hàng thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@user_bp.route('/employees', methods=['POST'])
@require_auth
@require_role(Role.OWNER, Role.ADMIN)
def create_employee():
    """
    Create a new employee (Owner only)
    ---
    tags:
      - Users
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
            - email
            - password
            - full_name
          properties:
            store_id:
              type: integer
            email:
              type: string
            password:
              type: string
            full_name:
              type: string
            phone:
              type: string
    responses:
      201:
        description: Employee created
    """
    try:
        data = request.get_json()
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        employee = UserService.create_employee(
            store_id=data.get('store_id'),
            email=data.get('email'),
            password=data.get('password'),
            full_name=data.get('full_name'),
            phone=data.get('phone'),
            current_user=current_user
        )
        
        return created_response(data=employee.to_dict(), message="Tạo nhân viên thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@user_bp.route('/employees/<int:employee_id>/status', methods=['PATCH'])
@require_auth
@require_role(Role.OWNER, Role.ADMIN)
def update_employee_status(employee_id):
    """
    Update employee status (activate/deactivate)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: employee_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [active, inactive, suspended]
    responses:
      200:
        description: Status updated
    """
    try:
        data = request.get_json()
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        status_str = data.get('status')
        try:
            status = UserStatus(status_str)
        except ValueError:
            return error_response("VALIDATION_ERROR", f"Status không hợp lệ: {status_str}", status_code=400)
        
        employee = UserService.update_employee_status(employee_id, status, current_user)
        
        return success_response(data=employee.to_dict(), message="Cập nhật trạng thái thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@user_bp.route('/stores/<int:store_id>/employees', methods=['GET'])
@require_auth
@require_role(Role.OWNER, Role.ADMIN)
def get_employees(store_id):
    """
    Get all employees of a store
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: store_id
        type: integer
        required: true
    responses:
      200:
        description: List of employees
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        employees = UserService.get_employees(store_id, current_user)
        
        return success_response(data=employees)
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)
