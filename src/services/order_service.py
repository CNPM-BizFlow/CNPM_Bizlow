# Order Service - Order management with business rules

from decimal import Decimal
from datetime import datetime
from extensions import db
from infrastructure.models import (
    Order, OrderDetail, Product, ProductUnit, Customer, User, Store,
    InventoryTransaction, generate_order_number,
    create_revenue_entry, create_debt_entry
)
from domain.constants import OrderStatus, Role
from domain.exceptions import (
    ValidationError, NotFoundError, AuthorizationError,
    InsufficientStockError, OrderAlreadyConfirmedError
)


class OrderService:
    """Service for order management operations."""
    
    @staticmethod
    def create_order(
        store_id: int,
        items: list,
        current_user: User,
        customer_id: int = None,
        is_credit: bool = False,
        notes: str = None,
        source_draft_order_id: int = None
    ) -> Order:
        """
        Create a new order.
        
        Args:
            store_id: Store ID
            items: List of {product_unit_id, quantity, unit_price?, discount?}
            current_user: Current authenticated user
            customer_id: Optional customer ID
            is_credit: Is this a credit sale (bán chịu)
            notes: Optional notes
            source_draft_order_id: Optional source draft order ID
        """
        # Verify store access
        if not current_user.can_access_store(store_id):
            raise AuthorizationError("Bạn không có quyền tạo đơn hàng cho cửa hàng này")
        
        # Validate customer if provided
        customer = None
        if customer_id:
            customer = Customer.query.filter_by(id=customer_id, store_id=store_id).first()
            if not customer:
                raise NotFoundError("Khách hàng không tồn tại")
        
        # Credit sale requires customer
        if is_credit and not customer:
            raise ValidationError("Bán chịu phải có thông tin khách hàng")
        
        # Create order
        order = Order(
            store_id=store_id,
            customer_id=customer_id,
            order_number=generate_order_number(store_id),
            status=OrderStatus.NEW,
            is_credit=is_credit,
            notes=notes,
            created_by_user_id=current_user.id,
            source_draft_order_id=source_draft_order_id
        )
        db.session.add(order)
        db.session.flush()
        
        # Add order items
        total = Decimal('0')
        for item in items:
            product_unit = ProductUnit.query.get(item['product_unit_id'])
            if not product_unit:
                raise NotFoundError(f"Đơn vị sản phẩm ID {item['product_unit_id']} không tồn tại")
            
            product = product_unit.product
            if product.store_id != store_id:
                raise ValidationError(f"Sản phẩm {product.name} không thuộc cửa hàng này")
            
            quantity = Decimal(str(item['quantity']))
            unit_price = Decimal(str(item.get('unit_price', product_unit.price)))
            discount = Decimal(str(item.get('discount', 0)))
            line_total = (quantity * unit_price) - discount
            
            order_detail = OrderDetail(
                order_id=order.id,
                product_id=product.id,
                product_unit_id=product_unit.id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                line_total=line_total,
                notes=item.get('notes')
            )
            db.session.add(order_detail)
            total += line_total
        
        order.total_amount = total
        
        if not is_credit:
            order.paid_amount = total
        
        db.session.commit()
        return order
    
    @staticmethod
    def confirm_order(order_id: int, current_user: User) -> Order:
        """
        Confirm order and update inventory/bookkeeping.
        Implements BR-05: Auto-update inventory and revenue.
        """
        order = Order.query.get(order_id)
        
        if not order:
            raise NotFoundError("Đơn hàng không tồn tại")
        
        if not current_user.can_access_store(order.store_id):
            raise AuthorizationError("Bạn không có quyền xác nhận đơn hàng này")
        
        if order.status != OrderStatus.NEW:
            raise OrderAlreadyConfirmedError()
        
        # Check stock availability
        for item in order.items.all():
            current_stock = item.product.current_stock
            required = float(item.quantity) * float(item.product_unit.conversion_factor)
            
            if current_stock < required:
                raise InsufficientStockError(
                    f"Không đủ hàng: {item.product.name}. Cần {required}, chỉ còn {current_stock}"
                )
        
        # Deduct inventory
        for item in order.items.all():
            qty_base = float(item.quantity) * float(item.product_unit.conversion_factor)
            
            inv_transaction = InventoryTransaction(
                store_id=order.store_id,
                product_id=item.product_id,
                product_unit_id=item.product_unit_id,
                qty_change=-qty_base,  # Negative = stock out
                ref_type='order',
                ref_id=order.id,
                notes=f"Xuất kho cho đơn hàng {order.order_number}",
                created_by_user_id=current_user.id
            )
            db.session.add(inv_transaction)
        
        # Create bookkeeping entries
        if order.is_credit:
            # Credit sale -> debt entry
            entry = create_debt_entry(
                store_id=order.store_id,
                order_id=order.id,
                amount=order.total_amount,
                user_id=current_user.id,
                customer_name=order.customer.name if order.customer else None
            )
            db.session.add(entry)
            
            # Update customer debt balance
            if order.customer:
                order.customer.add_debt(order.total_amount)
        else:
            # Cash sale -> revenue entry
            entry = create_revenue_entry(
                store_id=order.store_id,
                order_id=order.id,
                amount=order.total_amount,
                user_id=current_user.id
            )
            db.session.add(entry)
        
        # Confirm order
        order.confirm(current_user.id)
        db.session.commit()
        
        return order
    
    @staticmethod
    def cancel_order(order_id: int, current_user: User, reason: str = None) -> Order:
        """Cancel an order."""
        order = Order.query.get(order_id)
        
        if not order:
            raise NotFoundError("Đơn hàng không tồn tại")
        
        if not current_user.can_access_store(order.store_id):
            raise AuthorizationError("Bạn không có quyền hủy đơn hàng này")
        
        if order.status == OrderStatus.COMPLETED:
            raise ValidationError("Không thể hủy đơn hàng đã hoàn thành")
        
        if order.status == OrderStatus.CONFIRMED:
            # Restore inventory if already confirmed
            for item in order.items.all():
                qty_base = float(item.quantity) * float(item.product_unit.conversion_factor)
                
                inv_transaction = InventoryTransaction(
                    store_id=order.store_id,
                    product_id=item.product_id,
                    product_unit_id=item.product_unit_id,
                    qty_change=qty_base,  # Positive = stock in (restore)
                    ref_type='order_cancel',
                    ref_id=order.id,
                    notes=f"Hoàn kho do hủy đơn hàng {order.order_number}",
                    created_by_user_id=current_user.id
                )
                db.session.add(inv_transaction)
            
            # Restore customer debt if credit sale
            if order.is_credit and order.customer:
                order.customer.reduce_debt(order.total_amount)
        
        order.cancel()
        if reason:
            order.notes = (order.notes or '') + f"\nLý do hủy: {reason}"
        
        db.session.commit()
        return order
    
    @staticmethod
    def get_orders(store_id: int, current_user: User, page: int = 1, per_page: int = 20, status: str = None) -> dict:
        """Get orders for a store with pagination."""
        if not current_user.can_access_store(store_id):
            raise AuthorizationError("Bạn không có quyền xem đơn hàng của cửa hàng này")
        
        query = Order.query.filter_by(store_id=store_id)
        
        if status:
            try:
                order_status = OrderStatus(status)
                query = query.filter_by(status=order_status)
            except ValueError:
                pass
        
        query = query.order_by(Order.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [o.to_dict() for o in pagination.items],
            'page': page,
            'per_page': per_page,
            'total': pagination.total
        }
    
    @staticmethod
    def get_order_by_id(order_id: int, current_user: User) -> Order:
        """Get order by ID."""
        order = Order.query.get(order_id)
        
        if not order:
            raise NotFoundError("Đơn hàng không tồn tại")
        
        if not current_user.can_access_store(order.store_id):
            raise AuthorizationError("Bạn không có quyền xem đơn hàng này")
        
        return order
