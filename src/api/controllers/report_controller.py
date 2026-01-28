# Report Controller - Reports for Owner (BR-02)

from flask import Blueprint, request
from datetime import datetime, date, timedelta
from decimal import Decimal
from api.responses import success_response, error_response
from api.decorators import require_auth, require_role, get_current_user_identity
from services.auth_service import AuthService
from domain.constants import Role, TransactionType
from domain.exceptions import BizFlowException, AuthorizationError
from extensions import db
from infrastructure.models import Order, Customer, BookkeepingEntry

report_bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')


def parse_date(date_str: str, default: date = None) -> date:
    """Parse date string to date object."""
    if not date_str:
        return default
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return default


@report_bp.route('/revenue', methods=['GET'])
@require_auth
@require_role(Role.OWNER, Role.ADMIN)
def revenue_report():
    """
    Get revenue report (Owner only - BR-02)
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
      - in: query
        name: from
        type: string
        format: date
        description: Start date (YYYY-MM-DD)
      - in: query
        name: to
        type: string
        format: date
        description: End date (YYYY-MM-DD)
      - in: query
        name: group
        type: string
        enum: [day, month]
        default: day
    responses:
      200:
        description: Revenue report
      403:
        description: Owner access required
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            raise AuthorizationError("Chỉ chủ cửa hàng mới có quyền xem báo cáo")
        
        # Date range
        today = date.today()
        from_date = parse_date(request.args.get('from'), today - timedelta(days=30))
        to_date = parse_date(request.args.get('to'), today)
        group_by = request.args.get('group', 'day')
        
        # Query bookkeeping entries
        entries = BookkeepingEntry.query.filter(
            BookkeepingEntry.store_id == store_id,
            BookkeepingEntry.entry_type == TransactionType.REVENUE,
            BookkeepingEntry.entry_date >= from_date,
            BookkeepingEntry.entry_date <= to_date
        ).all()
        
        # Aggregate by day or month
        aggregated = {}
        for entry in entries:
            if group_by == 'month':
                key = entry.entry_date.strftime('%Y-%m')
            else:
                key = entry.entry_date.strftime('%Y-%m-%d')
            
            if key not in aggregated:
                aggregated[key] = Decimal('0')
            aggregated[key] += entry.amount
        
        # Format result
        data = [
            {'period': key, 'revenue': float(value)}
            for key, value in sorted(aggregated.items())
        ]
        
        total = sum(item['revenue'] for item in data)
        
        return success_response(data={
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
            'group_by': group_by,
            'total_revenue': total,
            'details': data
        })
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@report_bp.route('/debts', methods=['GET'])
@require_auth
@require_role(Role.OWNER, Role.ADMIN)
def debt_report():
    """
    Get debt report (Owner only - BR-02)
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
    responses:
      200:
        description: Debt report
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            raise AuthorizationError("Chỉ chủ cửa hàng mới có quyền xem báo cáo")
        
        # Get customers with debt
        customers_with_debt = Customer.query.filter(
            Customer.store_id == store_id,
            Customer.debt_balance > 0,
            Customer.is_active == True
        ).order_by(Customer.debt_balance.desc()).all()
        
        total_debt = sum(float(c.debt_balance) for c in customers_with_debt)
        
        return success_response(data={
            'total_debt': total_debt,
            'customer_count': len(customers_with_debt),
            'customers': [
                {
                    'id': c.id,
                    'name': c.name,
                    'phone': c.phone,
                    'debt_balance': float(c.debt_balance)
                }
                for c in customers_with_debt
            ]
        })
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@report_bp.route('/operations', methods=['GET'])
@require_auth
@require_role(Role.OWNER, Role.ADMIN)
def operations_report():
    """
    Get operations report (TT88/2021 format) - Owner only
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
      - in: query
        name: from
        type: string
        format: date
      - in: query
        name: to
        type: string
        format: date
    responses:
      200:
        description: Operations report (TT88 format)
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            raise AuthorizationError("Chỉ chủ cửa hàng mới có quyền xem báo cáo")
        
        # Date range
        today = date.today()
        from_date = parse_date(request.args.get('from'), today.replace(day=1))
        to_date = parse_date(request.args.get('to'), today)
        
        # Query all bookkeeping entries
        entries = BookkeepingEntry.query.filter(
            BookkeepingEntry.store_id == store_id,
            BookkeepingEntry.entry_date >= from_date,
            BookkeepingEntry.entry_date <= to_date
        ).order_by(BookkeepingEntry.entry_date, BookkeepingEntry.id).all()
        
        # Aggregate by type
        summary = {
            'revenue': Decimal('0'),
            'debt_in': Decimal('0'),
            'debt_out': Decimal('0'),
            'payment_in': Decimal('0'),
            'payment_out': Decimal('0'),
            'inventory_in': Decimal('0'),
            'inventory_out': Decimal('0')
        }
        
        for entry in entries:
            key = entry.entry_type.value
            if key in summary:
                summary[key] += entry.amount
        
        # TT88 format summary
        tt88_summary = {
            'doanh_thu': float(summary['revenue']),
            'cong_no_phai_thu': float(summary['debt_in']),
            'da_thu_cong_no': float(summary['payment_in']),
            'cong_no_con_lai': float(summary['debt_in'] - summary['payment_in']),
            'nhap_kho': float(summary['inventory_in']),
            'xuat_kho': float(summary['inventory_out'])
        }
        
        return success_response(data={
            'report_title': 'BÁO CÁO TÌNH HÌNH KINH DOANH',
            'subtitle': f'Theo Thông tư 88/2021/TT-BTC',
            'period': {
                'from': from_date.isoformat(),
                'to': to_date.isoformat()
            },
            'summary': tt88_summary,
            'entries': [e.to_dict() for e in entries]
        })
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@report_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_role(Role.OWNER, Role.ADMIN)
def dashboard():
    """
    Get dashboard summary for owner
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
    responses:
      200:
        description: Dashboard data
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            raise AuthorizationError()
        
        today = date.today()
        month_start = today.replace(day=1)
        
        # Today's revenue
        today_revenue = db.session.query(
            db.func.sum(BookkeepingEntry.amount)
        ).filter(
            BookkeepingEntry.store_id == store_id,
            BookkeepingEntry.entry_type == TransactionType.REVENUE,
            BookkeepingEntry.entry_date == today
        ).scalar() or 0
        
        # Month's revenue
        month_revenue = db.session.query(
            db.func.sum(BookkeepingEntry.amount)
        ).filter(
            BookkeepingEntry.store_id == store_id,
            BookkeepingEntry.entry_type == TransactionType.REVENUE,
            BookkeepingEntry.entry_date >= month_start
        ).scalar() or 0
        
        # Today's orders
        from domain.constants import OrderStatus
        today_orders = Order.query.filter(
            Order.store_id == store_id,
            db.func.date(Order.created_at) == today
        ).count()
        
        # Pending drafts
        from infrastructure.models import DraftOrder
        from domain.constants import DraftOrderStatus
        pending_drafts = DraftOrder.query.filter(
            DraftOrder.store_id == store_id,
            DraftOrder.status == DraftOrderStatus.DRAFT
        ).count()
        
        # Total debt
        total_debt = db.session.query(
            db.func.sum(Customer.debt_balance)
        ).filter(
            Customer.store_id == store_id,
            Customer.is_active == True
        ).scalar() or 0
        
        return success_response(data={
            'today': today.isoformat(),
            'today_revenue': float(today_revenue),
            'month_revenue': float(month_revenue),
            'today_orders': today_orders,
            'pending_drafts': pending_drafts,
            'total_debt': float(total_debt)
        })
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)
