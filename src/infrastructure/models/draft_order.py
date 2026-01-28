# DraftOrder Model - AI-generated draft orders

from datetime import datetime
from extensions import db
from infrastructure.models.base import BaseModel
from domain.constants import DraftOrderStatus


class DraftOrder(BaseModel):
    """AI-generated draft order model."""
    __tablename__ = 'draft_orders'
    
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False, index=True)
    
    # Source
    source_text = db.Column(db.Text, nullable=False)  # Original text/voice transcript
    source_type = db.Column(db.String(20), default='text', nullable=False)  # text, voice
    
    # Parsed data (JSON)
    parsed_data = db.Column(db.JSON, nullable=True)
    # Expected format:
    # {
    #   "customer_name": "chú Ba",
    #   "customer_id": 123 or null,
    #   "is_credit": true,
    #   "items": [
    #     {"product_name": "xi măng", "unit": "bao", "quantity": 5, "product_id": null, "product_unit_id": null}
    #   ]
    # }
    
    # Warnings/issues from parsing
    warnings = db.Column(db.JSON, nullable=True)
    # e.g., ["Không tìm thấy sản phẩm 'xi măng'", "Khách hàng 'chú Ba' không tồn tại"]
    
    status = db.Column(db.Enum(DraftOrderStatus), nullable=False, default=DraftOrderStatus.DRAFT)
    
    # Audit
    created_by_ai = db.Column(db.Boolean, default=True, nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    rejected_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Relationships
    store = db.relationship('Store', back_populates='draft_orders')
    confirmed_by = db.relationship('User', foreign_keys=[confirmed_by_user_id])
    rejected_by = db.relationship('User', foreign_keys=[rejected_by_user_id])
    confirmed_order = db.relationship('Order', back_populates='source_draft', uselist=False)
    
    def confirm(self, user_id: int):
        """Confirm the draft order."""
        self.status = DraftOrderStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()
        self.confirmed_by_user_id = user_id
    
    def reject(self, user_id: int, reason: str = None):
        """Reject the draft order."""
        self.status = DraftOrderStatus.REJECTED
        self.rejected_at = datetime.utcnow()
        self.rejected_by_user_id = user_id
        self.rejection_reason = reason
    
    @property
    def is_pending(self) -> bool:
        """Check if draft is still pending."""
        return self.status == DraftOrderStatus.DRAFT
    
    @property
    def has_warnings(self) -> bool:
        """Check if draft has parsing warnings."""
        return bool(self.warnings)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'source_text': self.source_text,
            'source_type': self.source_type,
            'parsed_data': self.parsed_data,
            'warnings': self.warnings,
            'status': self.status.value,
            'created_by_ai': self.created_by_ai,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by_user_id': self.confirmed_by_user_id,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'rejected_by_user_id': self.rejected_by_user_id,
            'rejection_reason': self.rejection_reason,
            'has_warnings': self.has_warnings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DraftOrder {self.id}>'
