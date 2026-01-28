# User Service - User management

from extensions import db
from infrastructure.models import User, Store
from domain.constants import Role, UserStatus
from domain.exceptions import ValidationError, NotFoundError, AuthorizationError, DuplicateError


class UserService:
    """Service for user management operations."""
    
    @staticmethod
    def create_owner(email: str, password: str, full_name: str, phone: str = None, store_name: str = None) -> dict:
        """Create a new owner with their store."""
        # Check duplicate email
        if User.query.filter_by(email=email).first():
            raise DuplicateError("Email đã được sử dụng")
        
        # Create owner user
        owner = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role=Role.OWNER,
            status=UserStatus.ACTIVE
        )
        owner.set_password(password)
        
        db.session.add(owner)
        db.session.flush()  # Get the ID
        
        # Create default store for owner
        store = Store(
            name=store_name or f"Cửa hàng của {full_name}",
            owner_id=owner.id
        )
        db.session.add(store)
        db.session.commit()
        
        return {
            'user': owner.to_dict(),
            'store': store.to_dict()
        }
    
    @staticmethod
    def create_employee(
        store_id: int,
        email: str,
        password: str,
        full_name: str,
        phone: str = None,
        current_user: User = None
    ) -> User:
        """Create a new employee for a store."""
        # Verify store exists and current user owns it
        store = Store.query.get(store_id)
        if not store:
            raise NotFoundError("Cửa hàng không tồn tại")
        
        if current_user and not current_user.is_admin():
            if store.owner_id != current_user.id:
                raise AuthorizationError("Bạn không có quyền thêm nhân viên cho cửa hàng này")
        
        # Check duplicate email
        if User.query.filter_by(email=email).first():
            raise DuplicateError("Email đã được sử dụng")
        
        employee = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role=Role.EMPLOYEE,
            status=UserStatus.ACTIVE,
            store_id=store_id
        )
        employee.set_password(password)
        
        db.session.add(employee)
        db.session.commit()
        
        return employee
    
    @staticmethod
    def update_employee_status(employee_id: int, status: UserStatus, current_user: User) -> User:
        """Update employee status (activate/deactivate)."""
        employee = User.query.get(employee_id)
        
        if not employee:
            raise NotFoundError("Nhân viên không tồn tại")
        
        if employee.role != Role.EMPLOYEE:
            raise ValidationError("Chỉ có thể thay đổi trạng thái nhân viên")
        
        # Verify current user owns the store
        if not current_user.is_admin():
            store = Store.query.get(employee.store_id)
            if not store or store.owner_id != current_user.id:
                raise AuthorizationError("Bạn không có quyền quản lý nhân viên này")
        
        employee.status = status
        db.session.commit()
        
        return employee
    
    @staticmethod
    def get_employees(store_id: int, current_user: User) -> list:
        """Get all employees of a store."""
        store = Store.query.get(store_id)
        
        if not store:
            raise NotFoundError("Cửa hàng không tồn tại")
        
        if not current_user.is_admin():
            if store.owner_id != current_user.id:
                raise AuthorizationError("Bạn không có quyền xem danh sách nhân viên")
        
        employees = User.query.filter_by(store_id=store_id, role=Role.EMPLOYEE).all()
        return [e.to_dict() for e in employees]
    
    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        """Get user by ID."""
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError("Người dùng không tồn tại")
        return user
