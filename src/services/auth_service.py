# Auth Service - Authentication and JWT handling

from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from extensions import db
from infrastructure.models import User
from domain.constants import Role, UserStatus
from domain.exceptions import AuthenticationError, ValidationError, NotFoundError


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def login(email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            raise AuthenticationError("Email hoặc mật khẩu không đúng")
        
        if not user.check_password(password):
            raise AuthenticationError("Email hoặc mật khẩu không đúng")
        
        if not user.is_active():
            raise AuthenticationError("Tài khoản đã bị khóa")
        
        # Create tokens with user identity
        identity = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'store_id': user.store_id
        }
        
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    
    @staticmethod
    def register_admin(email: str, password: str, full_name: str) -> User:
        """Register a new admin user (initial setup only)."""
        # Check if any admin exists
        existing_admin = User.query.filter_by(role=Role.ADMIN).first()
        if existing_admin:
            raise ValidationError("Admin đã tồn tại")
        
        user = User(
            email=email,
            full_name=full_name,
            role=Role.ADMIN,
            status=UserStatus.ACTIVE
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def get_current_user(identity: dict) -> User:
        """Get current user from JWT identity."""
        user_id = identity.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            raise NotFoundError("Người dùng không tồn tại")
        
        if not user.is_active():
            raise AuthenticationError("Tài khoản đã bị khóa")
        
        return user
    
    @staticmethod
    def refresh_token(identity: dict) -> dict:
        """Generate new access token from refresh token."""
        access_token = create_access_token(identity=identity)
        return {'access_token': access_token}