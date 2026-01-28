# Inventory Model - Stock tracking

from decimal import Decimal
from extensions import db
from infrastructure.models.base import BaseModel


class InventoryTransaction(BaseModel):
    """Inventory transaction model for stock in/out tracking."""
    __tablename__ = 'inventory_transactions'
    
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    product_unit_id = db.Column(db.Integer, db.ForeignKey('product_units.id'), nullable=True)
    
    # Positive = stock in, Negative = stock out
    qty_change = db.Column(db.Numeric(15, 4), nullable=False)
    
    # Reference to source (order, manual import, etc.)
    ref_type = db.Column(db.String(50), nullable=True)  # order, import, adjustment, return
    ref_id = db.Column(db.Integer, nullable=True)
    
    unit_cost = db.Column(db.Numeric(15, 2), nullable=True)  # Cost per unit at time of transaction
    notes = db.Column(db.Text, nullable=True)
    
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    product = db.relationship('Product')
    product_unit = db.relationship('ProductUnit')
    created_by = db.relationship('User')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'product_id': self.product_id,
            'product_unit_id': self.product_unit_id,
            'qty_change': float(self.qty_change),
            'ref_type': self.ref_type,
            'ref_id': self.ref_id,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<InventoryTransaction {self.id}: {self.qty_change}>'


def get_product_stock(store_id: int, product_id: int) -> Decimal:
    """Get current stock level for a product in a store."""
    result = db.session.query(
        db.func.sum(InventoryTransaction.qty_change)
    ).filter(
        InventoryTransaction.store_id == store_id,
        InventoryTransaction.product_id == product_id
    ).scalar()
    return Decimal(str(result)) if result else Decimal('0')


def get_all_stock_levels(store_id: int) -> dict:
    """Get current stock levels for all products in a store."""
    results = db.session.query(
        InventoryTransaction.product_id,
        db.func.sum(InventoryTransaction.qty_change).label('stock')
    ).filter(
        InventoryTransaction.store_id == store_id
    ).group_by(
        InventoryTransaction.product_id
    ).all()
    
    return {r.product_id: float(r.stock) for r in results}
