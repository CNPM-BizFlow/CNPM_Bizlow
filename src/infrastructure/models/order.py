# Order Model - Order and OrderDetail

from decimal import Decimal
from datetime import datetime
from extensions import db
from infrastructure.models.base import BaseModel
from domain.constants import OrderStatus


class Order(BaseModel):
    """Order model."""
    __tablename__ = 'orders'
    
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    
    # Order info
    order_number = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.NEW)
    
    # Payment
    is_credit = db.Column(db.Boolean, default=False, nullable=False)  # Bán chịu
    total_amount = db.Column(db.Numeric(15, 2), default=Decimal('0'), nullable=False)
    paid_amount = db.Column(db.Numeric(15, 2), default=Decimal('0'), nullable=False)
    
    notes = db.Column(db.Text, nullable=True)
    
    # Audit
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Source (for AI draft orders)
    source_draft_order_id = db.Column(db.Integer, db.ForeignKey('draft_orders.id'), nullable=True)
    
    # Relationships
    store = db.relationship('Store', back_populates='orders')
    customer = db.relationship('Customer', back_populates='orders')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    confirmed_by = db.relationship('User', foreign_keys=[confirmed_by_user_id])
    items = db.relationship('OrderDetail', back_populates='order', lazy='dynamic', cascade='all, delete-orphan')
    source_draft = db.relationship('DraftOrder', back_populates='confirmed_order')
    
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount to pay."""
        return Decimal(str(self.total_amount)) - Decimal(str(self.paid_amount))
    
    @property
    def is_fully_paid(self) -> bool:
        """Check if order is fully paid."""
        return self.remaining_amount <= 0
    
    def calculate_total(self):
        """Calculate and update total amount from items."""
        total = sum(item.line_total for item in self.items.all())
        self.total_amount = total
        return total
    
    def confirm(self, user_id: int):
        """Confirm the order."""
        self.status = OrderStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()
        self.confirmed_by_user_id = user_id
    
    def complete(self):
        """Mark order as completed."""
        self.status = OrderStatus.COMPLETED
    
    def cancel(self):
        """Cancel the order."""
        self.status = OrderStatus.CANCELED
    
    def to_dict(self, include_items: bool = True):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'store_id': self.store_id,
            'customer_id': self.customer_id,
            'order_number': self.order_number,
            'status': self.status.value,
            'is_credit': self.is_credit,
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'remaining_amount': float(self.remaining_amount),
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by_user_id': self.confirmed_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_items:
            data['items'] = [item.to_dict() for item in self.items.all()]
        if self.customer:
            data['customer'] = {'id': self.customer.id, 'name': self.customer.name}
        return data
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderDetail(BaseModel):
    """Order detail/line item model."""
    __tablename__ = 'order_details'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_unit_id = db.Column(db.Integer, db.ForeignKey('product_units.id'), nullable=False)
    
    quantity = db.Column(db.Numeric(15, 4), nullable=False)
    unit_price = db.Column(db.Numeric(15, 2), nullable=False)
    discount = db.Column(db.Numeric(15, 2), default=Decimal('0'), nullable=False)
    line_total = db.Column(db.Numeric(15, 2), nullable=False)
    
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product')
    product_unit = db.relationship('ProductUnit')
    
    def calculate_line_total(self):
        """Calculate and update line total."""
        subtotal = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        self.line_total = subtotal - Decimal(str(self.discount))
        return self.line_total
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_unit_id': self.product_unit_id,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'discount': float(self.discount),
            'line_total': float(self.line_total),
            'notes': self.notes,
            'product': {
                'id': self.product.id,
                'name': self.product.name
            } if self.product else None,
            'unit': {
                'id': self.product_unit.id,
                'name': self.product_unit.unit_name
            } if self.product_unit else None
        }
    
    def __repr__(self):
        return f'<OrderDetail {self.id}>'


def generate_order_number(store_id: int) -> str:
    """Generate unique order number."""
    from datetime import datetime
    today = datetime.now()
    prefix = f"ORD{store_id:03d}{today.strftime('%y%m%d')}"
    
    # Count orders today
    count = Order.query.filter(
        Order.store_id == store_id,
        db.func.date(Order.created_at) == today.date()
    ).count()
    
    return f"{prefix}{count + 1:04d}"
