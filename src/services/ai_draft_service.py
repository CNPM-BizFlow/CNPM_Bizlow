# AI Draft Service - Mock AI parser for natural language orders

import re
from typing import Optional
from extensions import db
from infrastructure.models import (
    DraftOrder, Product, ProductUnit, Customer, User
)
from domain.constants import DraftOrderStatus
from domain.exceptions import NotFoundError, DraftOrderAlreadyProcessedError
from services.order_service import OrderService


class AIDraftService:
    """
    Mock AI service for parsing natural language to draft orders.
    
    MVP Implementation: Simple keyword/regex matching
    Future: Replace with actual NLP/LLM integration
    """
    
    # Common Vietnamese units
    UNIT_PATTERNS = [
        (r'(\d+)\s*(bao|bịch)', 'bao'),
        (r'(\d+)\s*(kg|kilô|kí)', 'kg'),
        (r'(\d+)\s*(cái|chiếc)', 'cái'),
        (r'(\d+)\s*(thùng|hộp)', 'thùng'),
        (r'(\d+)\s*(lon|chai)', 'lon'),
        (r'(\d+)\s*(m|mét|met)', 'm'),
        (r'(\d+)\s*(tấn)', 'tấn'),
    ]
    
    # Credit indicators
    CREDIT_KEYWORDS = ['ghi nợ', 'thiếu', 'chịu', 'nợ', 'ghi sổ', 'ký sổ']
    
    @classmethod
    def parse_order_text(cls, text: str, store_id: int) -> dict:
        """
        Parse natural language text to extract order information.
        
        Example input: "Lấy 5 bao xi măng cho chú Ba, ghi nợ"
        
        Returns:
        {
            "customer_name": "chú Ba",
            "customer_id": 123 or null,
            "is_credit": true,
            "items": [
                {"product_name": "xi măng", "unit": "bao", "quantity": 5, 
                 "product_id": null, "product_unit_id": null}
            ],
            "warnings": ["Không tìm thấy sản phẩm 'xi măng'"]
        }
        """
        text_lower = text.lower()
        result = {
            "customer_name": None,
            "customer_id": None,
            "is_credit": False,
            "items": [],
            "raw_text": text
        }
        warnings = []
        
        # Detect credit sale
        for keyword in cls.CREDIT_KEYWORDS:
            if keyword in text_lower:
                result["is_credit"] = True
                break
        
        # Extract customer name (simple pattern: "cho [name]")
        customer_match = re.search(r'cho\s+([\w\s]+?)(?:,|\.|$|ghi|thiếu)', text_lower)
        if customer_match:
            customer_name = customer_match.group(1).strip()
            result["customer_name"] = customer_name
            
            # Try to find matching customer
            customer = Customer.query.filter(
                Customer.store_id == store_id,
                Customer.name.ilike(f'%{customer_name}%')
            ).first()
            
            if customer:
                result["customer_id"] = customer.id
                result["customer_name"] = customer.name
            else:
                warnings.append(f"Không tìm thấy khách hàng '{customer_name}' trong hệ thống")
        
        # Extract items with quantities
        for pattern, unit_name in cls.UNIT_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                quantity = int(match.group(1))
                
                # Try to find product name after the quantity+unit
                remaining_text = text_lower[match.end():match.end() + 50]
                product_name = cls._extract_product_name(remaining_text)
                
                if not product_name:
                    # Try before the quantity
                    preceding_text = text_lower[max(0, match.start() - 30):match.start()]
                    product_name = cls._extract_product_name_before(preceding_text)
                
                item = {
                    "quantity": quantity,
                    "unit": unit_name,
                    "product_name": product_name,
                    "product_id": None,
                    "product_unit_id": None
                }
                
                # Try to find matching product
                if product_name:
                    product = Product.query.filter(
                        Product.store_id == store_id,
                        Product.name.ilike(f'%{product_name}%'),
                        Product.is_active == True
                    ).first()
                    
                    if product:
                        item["product_id"] = product.id
                        item["product_name"] = product.name
                        
                        # Find matching unit
                        product_unit = ProductUnit.query.filter(
                            ProductUnit.product_id == product.id,
                            ProductUnit.unit_name.ilike(f'%{unit_name}%'),
                            ProductUnit.is_active == True
                        ).first()
                        
                        if product_unit:
                            item["product_unit_id"] = product_unit.id
                        else:
                            # Use default unit
                            default_unit = product.default_unit
                            if default_unit:
                                item["product_unit_id"] = default_unit.id
                                item["unit"] = default_unit.unit_name
                                warnings.append(
                                    f"Đơn vị '{unit_name}' không có cho '{product.name}', "
                                    f"sử dụng đơn vị mặc định '{default_unit.unit_name}'"
                                )
                    else:
                        warnings.append(f"Không tìm thấy sản phẩm '{product_name}'")
                else:
                    warnings.append(f"Không xác định được tên sản phẩm cho {quantity} {unit_name}")
                
                result["items"].append(item)
        
        # If no items found, try a simpler extraction
        if not result["items"]:
            simple_match = re.search(r'(\d+)\s+(\S+)', text_lower)
            if simple_match:
                quantity = int(simple_match.group(1))
                product_hint = simple_match.group(2)
                
                result["items"].append({
                    "quantity": quantity,
                    "unit": "cái",
                    "product_name": product_hint,
                    "product_id": None,
                    "product_unit_id": None
                })
                warnings.append(f"Cần xác nhận: {quantity} {product_hint}")
        
        return result, warnings
    
    @classmethod
    def _extract_product_name(cls, text: str) -> Optional[str]:
        """Extract product name from text after quantity."""
        # Remove common words
        text = re.sub(r'^(của|cho|lấy|mua)\s*', '', text.strip())
        
        # Get first meaningful word(s)
        match = re.match(r'([\w\s]{2,20})', text)
        if match:
            name = match.group(1).strip()
            # Remove trailing common words
            name = re.sub(r'\s*(cho|của|ghi|thiếu|nợ).*$', '', name)
            return name if len(name) > 1 else None
        return None
    
    @classmethod
    def _extract_product_name_before(cls, text: str) -> Optional[str]:
        """Extract product name from text before quantity."""
        # Get last meaningful word(s)
        words = text.strip().split()
        if words:
            return words[-1] if len(words[-1]) > 1 else None
        return None
    
    @classmethod
    def create_draft_order(cls, store_id: int, source_text: str, source_type: str = 'text') -> DraftOrder:
        """Create a draft order from natural language input."""
        parsed_data, warnings = cls.parse_order_text(source_text, store_id)
        
        draft = DraftOrder(
            store_id=store_id,
            source_text=source_text,
            source_type=source_type,
            parsed_data=parsed_data,
            warnings=warnings if warnings else None,
            status=DraftOrderStatus.DRAFT,
            created_by_ai=True
        )
        
        db.session.add(draft)
        db.session.commit()
        
        return draft
    
    @classmethod
    def confirm_draft_order(cls, draft_id: int, current_user: User, modifications: dict = None) -> dict:
        """
        Confirm a draft order and create the actual order.
        Implements BR-04: Draft must be confirmed by user.
        
        Args:
            draft_id: Draft order ID
            current_user: Current user confirming
            modifications: Optional modifications to the parsed data
        
        Returns:
            dict with draft and created order
        """
        draft = DraftOrder.query.get(draft_id)
        
        if not draft:
            raise NotFoundError("Đơn nháp không tồn tại")
        
        if not current_user.can_access_store(draft.store_id):
            from domain.exceptions import AuthorizationError
            raise AuthorizationError("Bạn không có quyền xác nhận đơn nháp này")
        
        if not draft.is_pending:
            raise DraftOrderAlreadyProcessedError()
        
        # Merge modifications if provided
        data = draft.parsed_data.copy() if draft.parsed_data else {}
        if modifications:
            data.update(modifications)
        
        # Validate items have product_unit_id
        items_for_order = []
        for item in data.get('items', []):
            if not item.get('product_unit_id'):
                raise ValidationError(
                    f"Sản phẩm '{item.get('product_name', 'không xác định')}' chưa được xác nhận đúng"
                )
            items_for_order.append({
                'product_unit_id': item['product_unit_id'],
                'quantity': item['quantity']
            })
        
        if not items_for_order:
            from domain.exceptions import ValidationError
            raise ValidationError("Đơn nháp không có sản phẩm hợp lệ")
        
        # Create the actual order
        order = OrderService.create_order(
            store_id=draft.store_id,
            items=items_for_order,
            current_user=current_user,
            customer_id=data.get('customer_id'),
            is_credit=data.get('is_credit', False),
            notes=f"Từ đơn nháp AI: {draft.source_text}",
            source_draft_order_id=draft.id
        )
        
        # Mark draft as confirmed
        draft.confirm(current_user.id)
        db.session.commit()
        
        return {
            'draft': draft.to_dict(),
            'order': order.to_dict()
        }
    
    @classmethod
    def reject_draft_order(cls, draft_id: int, current_user: User, reason: str = None) -> DraftOrder:
        """Reject a draft order."""
        draft = DraftOrder.query.get(draft_id)
        
        if not draft:
            raise NotFoundError("Đơn nháp không tồn tại")
        
        if not current_user.can_access_store(draft.store_id):
            from domain.exceptions import AuthorizationError
            raise AuthorizationError("Bạn không có quyền từ chối đơn nháp này")
        
        if not draft.is_pending:
            raise DraftOrderAlreadyProcessedError()
        
        draft.reject(current_user.id, reason)
        db.session.commit()
        
        return draft
    
    @classmethod
    def get_pending_drafts(cls, store_id: int, current_user: User) -> list:
        """Get all pending draft orders for a store."""
        if not current_user.can_access_store(store_id):
            from domain.exceptions import AuthorizationError
            raise AuthorizationError("Bạn không có quyền xem đơn nháp của cửa hàng này")
        
        drafts = DraftOrder.query.filter_by(
            store_id=store_id,
            status=DraftOrderStatus.DRAFT
        ).order_by(DraftOrder.created_at.desc()).all()
        
        return [d.to_dict() for d in drafts]
