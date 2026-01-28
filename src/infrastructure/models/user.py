# User Model - Authentication and RBAC

from datetime import datetime
import bcrypt
from extensions import db
from infrastructure.models.base import BaseModel
from domain.constants import Role, UserStatus


class User(BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    role = db.Column(db.Enum(Role), nullable=False, default=Role.EMPLOYEE)
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    
    # For OWNER: null (they own stores)
    # For EMPLOYEE: the store they work at
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    
    # Relationships
    store = db.relationship('Store', foreign_keys=[store_id], back_populates='employees')
    owned_stores = db.relationship('Store', foreign_keys='Store.owner_id', back_populates='owner')
    
    def set_password(self, password: str):
        """Hash and set password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == Role.ADMIN
    
    def is_owner(self) -> bool:
        """Check if user is owner."""
        return self.role == Role.OWNER
    
    def is_employee(self) -> bool:
        """Check if user is employee."""
        return self.role == Role.EMPLOYEE
    
    def can_access_store(self, store_id: int) -> bool:
        """Check if user can access a specific store."""
        if self.is_admin():
            return True
        if self.is_owner():
            return any(s.id == store_id for s in self.owned_stores)
        if self.is_employee():
            return self.store_id == store_id
        return False
    
    def to_dict(self, include_sensitive: bool = False):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role.value,
            'status': self.status.value,
            'store_id': self.store_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'
