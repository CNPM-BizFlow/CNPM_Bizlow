# Base Model - Common fields for all models

from datetime import datetime
from extensions import db


class BaseModel(db.Model):
    """Abstract base model with common fields."""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def save(self):
        """Save the model to database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the model from database."""
        db.session.delete(self)
        db.session.commit()
    
    @classmethod
    def get_by_id(cls, id: int):
        """Get model by ID."""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """Get all records."""
        return cls.query.all()
