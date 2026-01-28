# Product Model - Product and ProductUnit

from decimal import Decimal
from extensions import db
from infrastructure.models.base import BaseModel


class Product(BaseModel):
    """Product model."""
    __tablename__ = 'products'
    
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False, index=True)
    
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), nullable=True)  # Mã sản phẩm
    barcode = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    store = db.relationship('Store', back_populates='products')
    units = db.relationship('ProductUnit', back_populates='product', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def default_unit(self):
        """Get default unit for this product."""
        return self.units.filter_by(is_default=True).first()
    
    @property
    def current_stock(self):
        """Calculate current stock (sum of all inventory transactions)."""
        from infrastructure.models.inventory import InventoryTransaction
        result = db.session.query(
            db.func.sum(InventoryTransaction.qty_change)
        ).filter(
            InventoryTransaction.product_id == self.id
        ).scalar()
        return result or 0
    
    def to_dict(self, include_units: bool = True):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'store_id': self.store_id,
            'name': self.name,
            'sku': self.sku,
            'barcode': self.barcode,
            'category': self.category,
            'description': self.description,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'current_stock': self.current_stock,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_units:
            data['units'] = [u.to_dict() for u in self.units.all()]
        return data
    
    def __repr__(self):
        return f'<Product {self.name}>'


class ProductUnit(BaseModel):
    """Product unit model - supports multiple units per product."""
    __tablename__ = 'product_units'
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    unit_name = db.Column(db.String(50), nullable=False)  # bao, kg, cái, thùng, etc.
    price = db.Column(db.Numeric(15, 2), nullable=False)
    cost_price = db.Column(db.Numeric(15, 2), nullable=True)  # Giá nhập
    
    # Conversion factor relative to base unit
    # e.g., 1 thùng = 24 lon -> conversion_factor = 24
    conversion_factor = db.Column(db.Numeric(10, 4), default=Decimal('1'), nullable=False)
    
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    product = db.relationship('Product', back_populates='units')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'unit_name': self.unit_name,
            'price': float(self.price),
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'conversion_factor': float(self.conversion_factor),
            'is_default': self.is_default,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<ProductUnit {self.unit_name} of Product {self.product_id}>'
