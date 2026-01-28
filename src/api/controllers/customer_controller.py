# Customer Controller - Customer and debt management

from flask import Blueprint, request
from decimal import Decimal
from api.responses import success_response, error_response, created_response, paginated_response
from api.decorators import require_auth, require_permission, get_current_user_identity
from services.auth_service import AuthService
from domain.exceptions import BizFlowException, NotFoundError, AuthorizationError
from extensions import db
from infrastructure.models import Customer, CustomerPayment, create_payment_entry

customer_bp = Blueprint('customers', __name__, url_prefix='/api/v1')


@customer_bp.route('/customers', methods=['GET'])
@require_auth
@require_permission('view_customers')
def list_customers():
    """List customers for a store"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            raise AuthorizationError()
        
        query = Customer.query.filter_by(store_id=store_id, is_active=True)
        
        # Search by name or phone
        search = request.args.get('search')
        if search:
            query = query.filter(
                db.or_(
                    Customer.name.ilike(f'%{search}%'),
                    Customer.phone.ilike(f'%{search}%')
                )
            )
        
        # Filter by debt
        has_debt = request.args.get('has_debt')
        if has_debt == 'true':
            query = query.filter(Customer.debt_balance > 0)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = query.order_by(Customer.name).paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_response(
            [c.to_dict() for c in pagination.items],
            page, per_page, pagination.total
        )
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@customer_bp.route('/customers', methods=['POST'])
@require_auth
@require_permission('manage_customers')
def create_customer():
    """Create a new customer"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        store_id = data.get('store_id')
        if not current_user.can_access_store(store_id):
            raise AuthorizationError()
        
        customer = Customer(
            store_id=store_id,
            name=data.get('name'),
            phone=data.get('phone'),
            address=data.get('address'),
            email=data.get('email'),
            notes=data.get('notes'),
            debt_limit=Decimal(str(data.get('debt_limit', 0))) if data.get('debt_limit') else None,
            is_active=True
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return created_response(data=customer.to_dict(), message="Tạo khách hàng thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        db.session.rollback()
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@customer_bp.route('/customers/<int:customer_id>', methods=['GET'])
@require_auth
@require_permission('view_customers')
def get_customer(customer_id):
    """Get customer details"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        customer = Customer.query.get(customer_id)
        if not customer:
            raise NotFoundError("Khách hàng không tồn tại")
        
        if not current_user.can_access_store(customer.store_id):
            raise AuthorizationError()
        
        return success_response(data=customer.to_dict())
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@require_auth
@require_permission('manage_customers')
def update_customer(customer_id):
    """Update customer"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        customer = Customer.query.get(customer_id)
        if not customer:
            raise NotFoundError("Khách hàng không tồn tại")
        
        if not current_user.can_access_store(customer.store_id):
            raise AuthorizationError()
        
        for field in ['name', 'phone', 'address', 'email', 'notes']:
            if field in data:
                setattr(customer, field, data[field])
        
        if 'debt_limit' in data:
            customer.debt_limit = Decimal(str(data['debt_limit'])) if data['debt_limit'] else None
        
        db.session.commit()
        
        return success_response(data=customer.to_dict(), message="Cập nhật thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        db.session.rollback()
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@customer_bp.route('/customers/<int:customer_id>/debts', methods=['GET'])
@require_auth
@require_permission('view_customers')
def get_customer_debts(customer_id):
    """Get customer debt history"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        customer = Customer.query.get(customer_id)
        if not customer:
            raise NotFoundError("Khách hàng không tồn tại")
        
        if not current_user.can_access_store(customer.store_id):
            raise AuthorizationError()
        
        # Get credit orders (debts)
        from infrastructure.models import Order
        credit_orders = Order.query.filter_by(
            customer_id=customer_id,
            is_credit=True
        ).order_by(Order.created_at.desc()).all()
        
        # Get payments
        payments = customer.payments.order_by(CustomerPayment.created_at.desc()).all()
        
        return success_response(data={
            'customer': customer.to_dict(),
            'current_balance': float(customer.debt_balance),
            'credit_orders': [o.to_dict(include_items=False) for o in credit_orders],
            'payments': [p.to_dict() for p in payments]
        })
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@customer_bp.route('/customers/<int:customer_id>/payments', methods=['POST'])
@require_auth
@require_permission('manage_debt')
def record_payment(customer_id):
    """
    Record a debt payment from customer
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - amount
          properties:
            amount:
              type: number
            payment_method:
              type: string
              enum: [cash, transfer, card]
              default: cash
            notes:
              type: string
    responses:
      201:
        description: Payment recorded
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        customer = Customer.query.get(customer_id)
        if not customer:
            raise NotFoundError("Khách hàng không tồn tại")
        
        if not current_user.can_access_store(customer.store_id):
            raise AuthorizationError()
        
        amount = Decimal(str(data.get('amount', 0)))
        
        if amount <= 0:
            return error_response("VALIDATION_ERROR", "Số tiền phải lớn hơn 0", status_code=400)
        
        # Create payment record
        payment = CustomerPayment(
            customer_id=customer_id,
            store_id=customer.store_id,
            amount=amount,
            payment_method=data.get('payment_method', 'cash'),
            notes=data.get('notes'),
            received_by_user_id=current_user.id
        )
        db.session.add(payment)
        
        # Reduce customer debt
        customer.reduce_debt(amount)
        
        # Create bookkeeping entry
        entry = create_payment_entry(
            store_id=customer.store_id,
            payment_id=payment.id,
            amount=amount,
            user_id=current_user.id,
            customer_name=customer.name
        )
        db.session.add(entry)
        
        db.session.commit()
        
        return created_response(
            data={
                'payment': payment.to_dict(),
                'new_balance': float(customer.debt_balance)
            },
            message=f"Thu tiền thành công. Công nợ còn lại: {float(customer.debt_balance):,.0f} VNĐ"
        )
    
    except BizFlowException as e:
        db.session.rollback()
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        db.session.rollback()
        return error_response("INTERNAL_ERROR", str(e), status_code=500)
