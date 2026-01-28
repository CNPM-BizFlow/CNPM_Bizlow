# Store Model - Business/Household entity

from extensions import db
from infrastructure.models.base import BaseModel
from domain.constants import SubscriptionPlan


class Store(BaseModel):
    """Store/Business Household model."""
    __tablename__ = 'stores'
    
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    tax_code = db.Column(db.String(50), nullable=True)  # Mã số thuế
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_plan = db.Column(
        db.Enum(SubscriptionPlan), 
        nullable=False, 
        default=SubscriptionPlan.FREE
    )
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], back_populates='owned_stores')
    employees = db.relationship('User', foreign_keys='User.store_id', back_populates='store')
    products = db.relationship('Product', back_populates='store', lazy='dynamic')
    customers = db.relationship('Customer', back_populates='store', lazy='dynamic')
    orders = db.relationship('Order', back_populates='store', lazy='dynamic')
    draft_orders = db.relationship('DraftOrder', back_populates='store', lazy='dynamic')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'tax_code': self.tax_code,
            'owner_id': self.owner_id,
            'subscription_plan': self.subscription_plan.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Store {self.name}>'
