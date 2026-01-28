# API Decorators - RBAC and validation helpers

from functools import wraps
from flask import request, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from api.responses import forbidden_response, unauthorized_response, validation_error_response
from domain.constants import Role, has_permission
from domain.exceptions import AuthorizationError


def require_auth(f):
    """Require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            g.current_user_identity = identity
            return f(*args, **kwargs)
        except Exception as e:
            return unauthorized_response(str(e))
    return decorated


def require_role(*roles):
    """Require specific role(s)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            identity = getattr(g, 'current_user_identity', None)
            if not identity:
                return unauthorized_response()
            
            user_role = identity.get('role')
            if user_role not in [r.value if isinstance(r, Role) else r for r in roles]:
                return forbidden_response(f"Yêu cầu quyền: {', '.join(str(r.value if isinstance(r, Role) else r) for r in roles)}")
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_permission(permission: str):
    """Require specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            identity = getattr(g, 'current_user_identity', None)
            if not identity:
                return unauthorized_response()
            
            user_role = identity.get('role')
            try:
                role = Role(user_role)
            except ValueError:
                return forbidden_response("Role không hợp lệ")
            
            if not has_permission(role, permission):
                return forbidden_response(f"Bạn không có quyền: {permission}")
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_store_access(f):
    """Require access to the store in the request."""
    @wraps(f)
    def decorated(*args, **kwargs):
        identity = getattr(g, 'current_user_identity', None)
        if not identity:
            return unauthorized_response()
        
        # Get store_id from request
        store_id = kwargs.get('store_id') or request.view_args.get('store_id')
        if not store_id:
            data = request.get_json(silent=True) or {}
            store_id = data.get('store_id')
        
        if not store_id:
            return validation_error_response({"store_id": "Store ID is required"})
        
        user_role = identity.get('role')
        user_store_id = identity.get('store_id')
        
        # Admin can access all stores
        if user_role == Role.ADMIN.value:
            return f(*args, **kwargs)
        
        # Owner can access their own stores (need to check in service)
        if user_role == Role.OWNER.value:
            return f(*args, **kwargs)
        
        # Employee can only access their assigned store
        if user_role == Role.EMPLOYEE.value:
            if user_store_id != int(store_id):
                return forbidden_response("Bạn không có quyền truy cập cửa hàng này")
        
        return f(*args, **kwargs)
    return decorated


def get_current_user_identity():
    """Get current user identity from request context."""
    return getattr(g, 'current_user_identity', None)


def get_current_store_id():
    """Get current user's store ID."""
    identity = get_current_user_identity()
    return identity.get('store_id') if identity else None
