# Customer Model - Customer with debt tracking

from decimal import Decimal
from extensions import db
from infrastructure.models.base import BaseModel


class Customer(BaseModel):
    """Customer model with debt balance tracking."""
    __tablename__ = 'customers'
    
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False, index=True)
    
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True, index=True)
    address = db.Column(db.String(500), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Debt tracking
    debt_balance = db.Column(db.Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    debt_limit = db.Column(db.Numeric(15, 2), default=Decimal('0.00'), nullable=True)  # 0 = no limit
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    store = db.relationship('Store', back_populates='customers')
    orders = db.relationship('Order', back_populates='customer', lazy='dynamic')
    payments = db.relationship('CustomerPayment', back_populates='customer', lazy='dynamic')
    
    def can_add_debt(self, amount: Decimal) -> bool:
        """Check if customer can add more debt."""
        if self.debt_limit is None or self.debt_limit == 0:
            return True  # No limit
        return (self.debt_balance + amount) <= self.debt_limit
    
    def add_debt(self, amount: Decimal):
        """Add debt to customer balance."""
        self.debt_balance = Decimal(str(self.debt_balance)) + Decimal(str(amount))
    
    def reduce_debt(self, amount: Decimal):
        """Reduce debt from customer balance."""
        self.debt_balance = max(Decimal('0'), Decimal(str(self.debt_balance)) - Decimal(str(amount)))
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'email': self.email,
            'notes': self.notes,
            'debt_balance': float(self.debt_balance),
            'debt_limit': float(self.debt_limit) if self.debt_limit else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Customer {self.name}>'


class CustomerPayment(BaseModel):
    """Customer payment record for debt reduction."""
    __tablename__ = 'customer_payments'
    
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False, index=True)
    
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_method = db.Column(db.String(50), default='cash', nullable=False)  # cash, transfer, card
    notes = db.Column(db.Text, nullable=True)
    
    received_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    customer = db.relationship('Customer', back_populates='payments')
    received_by = db.relationship('User')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'notes': self.notes,
            'received_by_user_id': self.received_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
