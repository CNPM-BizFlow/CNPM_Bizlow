# Product Controller - Product and inventory endpoints

from flask import Blueprint, request
from decimal import Decimal
from api.responses import success_response, error_response, created_response, paginated_response
from api.decorators import require_auth, require_role, require_permission, get_current_user_identity
from services.auth_service import AuthService
from domain.constants import Role
from domain.exceptions import BizFlowException, NotFoundError, AuthorizationError
from extensions import db
from infrastructure.models import Product, ProductUnit, InventoryTransaction, get_all_stock_levels

product_bp = Blueprint('products', __name__, url_prefix='/api/v1')


@product_bp.route('/products', methods=['GET'])
@require_auth
def list_products():
    """
    List products for a store
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
      - in: query
        name: category
        type: string
      - in: query
        name: search
        type: string
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
    responses:
      200:
        description: List of products
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            raise AuthorizationError()
        
        query = Product.query.filter_by(store_id=store_id, is_active=True)
        
        # Filter by category
        category = request.args.get('category')
        if category:
            query = query.filter(Product.category.ilike(f'%{category}%'))
        
        # Search by name
        search = request.args.get('search')
        if search:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.sku.ilike(f'%{search}%'),
                    Product.barcode.ilike(f'%{search}%')
                )
            )
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
        
        products = [p.to_dict() for p in pagination.items]
        
        return paginated_response(products, page, per_page, pagination.total)
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@product_bp.route('/products', methods=['POST'])
@require_auth
@require_permission('manage_products')
def create_product():
    """
    Create a new product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - store_id
            - name
          properties:
            store_id:
              type: integer
            name:
              type: string
            sku:
              type: string
            barcode:
              type: string
            category:
              type: string
            description:
              type: string
            image_url:
              type: string
            units:
              type: array
              items:
                type: object
                properties:
                  unit_name:
                    type: string
                  price:
                    type: number
                  is_default:
                    type: boolean
    responses:
      201:
        description: Product created
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        store_id = data.get('store_id')
        if not current_user.can_access_store(store_id):
            raise AuthorizationError()
        
        product = Product(
            store_id=store_id,
            name=data.get('name'),
            sku=data.get('sku'),
            barcode=data.get('barcode'),
            category=data.get('category'),
            description=data.get('description'),
            image_url=data.get('image_url'),
            is_active=True
        )
        db.session.add(product)
        db.session.flush()
        
        # Add units
        units = data.get('units', [])
        if not units:
            # Create default unit
            units = [{'unit_name': 'cái', 'price': 0, 'is_default': True}]
        
        for unit_data in units:
            unit = ProductUnit(
                product_id=product.id,
                unit_name=unit_data.get('unit_name', 'cái'),
                price=Decimal(str(unit_data.get('price', 0))),
                cost_price=Decimal(str(unit_data.get('cost_price', 0))) if unit_data.get('cost_price') else None,
                conversion_factor=Decimal(str(unit_data.get('conversion_factor', 1))),
                is_default=unit_data.get('is_default', False),
                is_active=True
            )
            db.session.add(unit)
        
        db.session.commit()
        
        return created_response(data=product.to_dict(), message="Tạo sản phẩm thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        db.session.rollback()
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@product_bp.route('/products/<int:product_id>', methods=['GET'])
@require_auth
def get_product(product_id):
    """Get product by ID"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        product = Product.query.get(product_id)
        if not product:
            raise NotFoundError("Sản phẩm không tồn tại")
        
        if not current_user.can_access_store(product.store_id):
            raise AuthorizationError()
        
        return success_response(data=product.to_dict())
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@require_auth
@require_permission('manage_products')
def update_product(product_id):
    """Update product"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        product = Product.query.get(product_id)
        if not product:
            raise NotFoundError("Sản phẩm không tồn tại")
        
        if not current_user.can_access_store(product.store_id):
            raise AuthorizationError()
        
        # Update fields
        for field in ['name', 'sku', 'barcode', 'category', 'description', 'image_url']:
            if field in data:
                setattr(product, field, data[field])
        
        db.session.commit()
        
        return success_response(data=product.to_dict(), message="Cập nhật thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        db.session.rollback()
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
@require_auth
@require_permission('manage_products')
def delete_product(product_id):
    """Delete product (soft delete)"""
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        product = Product.query.get(product_id)
        if not product:
            raise NotFoundError("Sản phẩm không tồn tại")
        
        if not current_user.can_access_store(product.store_id):
            raise AuthorizationError()
        
        product.is_active = False
        db.session.commit()
        
        return success_response(message="Xóa sản phẩm thành công")
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


# Inventory endpoints
@product_bp.route('/inventory/imports', methods=['POST'])
@require_auth
@require_permission('manage_inventory')
def import_inventory():
    """
    Record stock import
    ---
    tags:
      - Inventory
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - store_id
            - items
          properties:
            store_id:
              type: integer
            items:
              type: array
              items:
                type: object
                properties:
                  product_id:
                    type: integer
                  quantity:
                    type: number
                  unit_cost:
                    type: number
                  notes:
                    type: string
    responses:
      201:
        description: Import recorded
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        data = request.get_json()
        
        store_id = data.get('store_id')
        if not current_user.can_access_store(store_id):
            raise AuthorizationError()
        
        items = data.get('items', [])
        transactions = []
        
        for item in items:
            product = Product.query.get(item.get('product_id'))
            if not product or product.store_id != store_id:
                raise NotFoundError(f"Sản phẩm ID {item.get('product_id')} không tồn tại")
            
            transaction = InventoryTransaction(
                store_id=store_id,
                product_id=product.id,
                qty_change=Decimal(str(item.get('quantity', 0))),
                unit_cost=Decimal(str(item.get('unit_cost', 0))) if item.get('unit_cost') else None,
                ref_type='import',
                notes=item.get('notes', 'Nhập kho'),
                created_by_user_id=current_user.id
            )
            db.session.add(transaction)
            transactions.append(transaction)
        
        db.session.commit()
        
        return created_response(
            data=[t.to_dict() for t in transactions],
            message=f"Nhập kho thành công {len(transactions)} sản phẩm"
        )
    
    except BizFlowException as e:
        db.session.rollback()
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        db.session.rollback()
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@product_bp.route('/inventory/levels', methods=['GET'])
@require_auth
def get_inventory_levels():
    """
    Get current stock levels
    ---
    tags:
      - Inventory
    security:
      - Bearer: []
    parameters:
      - in: query
        name: store_id
        type: integer
        required: true
    responses:
      200:
        description: Stock levels
    """
    try:
        identity = get_current_user_identity()
        current_user = AuthService.get_current_user(identity)
        
        store_id = request.args.get('store_id', type=int)
        if not store_id:
            return error_response("VALIDATION_ERROR", "store_id là bắt buộc", status_code=400)
        
        if not current_user.can_access_store(store_id):
            raise AuthorizationError()
        
        stock_levels = get_all_stock_levels(store_id)
        
        # Get product info
        products = Product.query.filter_by(store_id=store_id, is_active=True).all()
        result = []
        
        for product in products:
            result.append({
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'category': product.category,
                'current_stock': stock_levels.get(product.id, 0)
            })
        
        return success_response(data=result)
    
    except BizFlowException as e:
        return error_response(e.code, e.message, e.details, e.status_code)
    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e), status_code=500)
