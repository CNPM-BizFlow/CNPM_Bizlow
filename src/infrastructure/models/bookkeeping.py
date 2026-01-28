# BookkeepingEntry Model - TT88/2021 compliance

from decimal import Decimal
from extensions import db
from infrastructure.models.base import BaseModel
from domain.constants import TransactionType


class BookkeepingEntry(BaseModel):
    """Bookkeeping entry for TT88/2021 compliance."""
    __tablename__ = 'bookkeeping_entries'
    
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False, index=True)
    
    entry_type = db.Column(db.Enum(TransactionType), nullable=False)
    
    # Reference to source document
    ref_type = db.Column(db.String(50), nullable=False)  # order, payment, inventory, adjustment
    ref_id = db.Column(db.Integer, nullable=False)
    
    # Amount (always positive, type determines direction)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Description for reporting
    description = db.Column(db.Text, nullable=True)
    
    # Entry date (for reporting, may differ from created_at)
    entry_date = db.Column(db.Date, nullable=False, index=True)
    
    # Audit
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    created_by = db.relationship('User')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'entry_type': self.entry_type.value,
            'ref_type': self.ref_type,
            'ref_id': self.ref_id,
            'amount': float(self.amount),
            'description': self.description,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<BookkeepingEntry {self.id}: {self.entry_type.value}>'


def create_revenue_entry(store_id: int, order_id: int, amount: Decimal, user_id: int, description: str = None):
    """Create a revenue entry from an order."""
    from datetime import date
    entry = BookkeepingEntry(
        store_id=store_id,
        entry_type=TransactionType.REVENUE,
        ref_type='order',
        ref_id=order_id,
        amount=amount,
        description=description or f"Doanh thu từ đơn hàng #{order_id}",
        entry_date=date.today(),
        created_by_user_id=user_id
    )
    return entry


def create_debt_entry(store_id: int, order_id: int, amount: Decimal, user_id: int, customer_name: str = None):
    """Create a debt entry from a credit sale."""
    from datetime import date
    entry = BookkeepingEntry(
        store_id=store_id,
        entry_type=TransactionType.DEBT_IN,
        ref_type='order',
        ref_id=order_id,
        amount=amount,
        description=f"Công nợ phải thu từ {customer_name or 'khách hàng'}",
        entry_date=date.today(),
        created_by_user_id=user_id
    )
    return entry


def create_payment_entry(store_id: int, payment_id: int, amount: Decimal, user_id: int, customer_name: str = None):
    """Create a payment entry for debt collection."""
    from datetime import date
    entry = BookkeepingEntry(
        store_id=store_id,
        entry_type=TransactionType.PAYMENT_IN,
        ref_type='payment',
        ref_id=payment_id,
        amount=amount,
        description=f"Thu tiền công nợ từ {customer_name or 'khách hàng'}",
        entry_date=date.today(),
        created_by_user_id=user_id
    )
    return entry


def create_inventory_entry(store_id: int, transaction_id: int, amount: Decimal, user_id: int, is_import: bool = True):
    """Create an inventory entry."""
    from datetime import date
    entry_type = TransactionType.INVENTORY_IN if is_import else TransactionType.INVENTORY_OUT
    description = "Nhập kho" if is_import else "Xuất kho"
    
    entry = BookkeepingEntry(
        store_id=store_id,
        entry_type=entry_type,
        ref_type='inventory',
        ref_id=transaction_id,
        amount=amount,
        description=description,
        entry_date=date.today(),
        created_by_user_id=user_id
    )
    return entry
