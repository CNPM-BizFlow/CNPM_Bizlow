# Seed Data Script - Create sample data for BizFlow

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from infrastructure.models import User, Store, Customer, Product, ProductUnit, InventoryTransaction
from domain.constants import Role, UserStatus, SubscriptionPlan
from decimal import Decimal


def seed_database():
    """Create sample data for testing."""
    app = create_app()
    
    with app.app_context():
        print("Creating sample data...")
        
        # Check if data already exists
        if User.query.filter_by(role=Role.ADMIN).first():
            print("Data already exists. Skipping seed.")
            return
        
        # 1. Create Admin
        admin = User(
            email='admin@bizflow.vn',
            full_name='Admin BizFlow',
            phone='0901234567',
            role=Role.ADMIN,
            status=UserStatus.ACTIVE
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.flush()
        print(f"  Created Admin: {admin.email}")
        
        # 2. Create Owner
        owner = User(
            email='owner@bizflow.vn',
            full_name='Nguyễn Văn Chủ',
            phone='0912345678',
            role=Role.OWNER,
            status=UserStatus.ACTIVE
        )
        owner.set_password('owner123')
        db.session.add(owner)
        db.session.flush()
        print(f"  Created Owner: {owner.email}")
        
        # 3. Create Store
        store = Store(
            name='Cửa hàng Vật liệu Xây dựng ABC',
            address='123 Đường Lê Lợi, Quận 1, TP.HCM',
            phone='0283123456',
            owner_id=owner.id,
            subscription_plan=SubscriptionPlan.BASIC
        )
        db.session.add(store)
        db.session.flush()
        print(f"  Created Store: {store.name}")
        
        # 4. Create Employee
        employee = User(
            email='nhanvien@bizflow.vn',
            full_name='Trần Thị Nhân Viên',
            phone='0923456789',
            role=Role.EMPLOYEE,
            status=UserStatus.ACTIVE,
            store_id=store.id
        )
        employee.set_password('nhanvien123')
        db.session.add(employee)
        db.session.flush()
        print(f"  Created Employee: {employee.email}")
        
        # 5. Create Customers
        customers_data = [
            {'name': 'Chú Ba', 'phone': '0934567890', 'address': '456 Nguyễn Huệ, Q1'},
            {'name': 'Anh Tư', 'phone': '0945678901', 'address': '789 Lý Tự Trọng, Q3'},
            {'name': 'Cô Năm', 'phone': '0956789012', 'address': '321 Pasteur, Q1'},
        ]
        
        customers = []
        for c_data in customers_data:
            customer = Customer(
                store_id=store.id,
                name=c_data['name'],
                phone=c_data['phone'],
                address=c_data['address'],
                debt_limit=Decimal('10000000')
            )
            db.session.add(customer)
            customers.append(customer)
        db.session.flush()
        print(f"  Created {len(customers)} customers")
        
        # 6. Create Products with Units
        products_data = [
            {
                'name': 'Xi măng', 
                'category': 'Vật liệu xây dựng',
                'units': [
                    {'unit_name': 'bao', 'price': 95000, 'is_default': True, 'conversion_factor': 1},
                    {'unit_name': 'tấn', 'price': 1900000, 'conversion_factor': 20}
                ]
            },
            {
                'name': 'Gạch ống', 
                'category': 'Vật liệu xây dựng',
                'units': [
                    {'unit_name': 'viên', 'price': 2500, 'is_default': True, 'conversion_factor': 1},
                    {'unit_name': 'pallet (500 viên)', 'price': 1200000, 'conversion_factor': 500}
                ]
            },
            {
                'name': 'Cát xây dựng', 
                'category': 'Vật liệu xây dựng',
                'units': [
                    {'unit_name': 'm3', 'price': 350000, 'is_default': True, 'conversion_factor': 1}
                ]
            },
            {
                'name': 'Sắt phi 10', 
                'category': 'Sắt thép',
                'units': [
                    {'unit_name': 'cây', 'price': 120000, 'is_default': True, 'conversion_factor': 1},
                    {'unit_name': 'kg', 'price': 20000, 'conversion_factor': 0.167}
                ]
            },
            {
                'name': 'Sơn nước', 
                'category': 'Sơn',
                'units': [
                    {'unit_name': 'thùng 18L', 'price': 850000, 'is_default': True, 'conversion_factor': 1},
                    {'unit_name': 'lon 5L', 'price': 250000, 'conversion_factor': 0.278}
                ]
            }
        ]
        
        products = []
        for p_data in products_data:
            product = Product(
                store_id=store.id,
                name=p_data['name'],
                category=p_data['category'],
                is_active=True
            )
            db.session.add(product)
            db.session.flush()
            
            for u_data in p_data['units']:
                unit = ProductUnit(
                    product_id=product.id,
                    unit_name=u_data['unit_name'],
                    price=Decimal(str(u_data['price'])),
                    conversion_factor=Decimal(str(u_data['conversion_factor'])),
                    is_default=u_data.get('is_default', False),
                    is_active=True
                )
                db.session.add(unit)
            
            products.append(product)
        
        db.session.flush()
        print(f"  Created {len(products)} products with units")
        
        # 7. Create initial inventory
        for product in products:
            unit = ProductUnit.query.filter_by(product_id=product.id, is_default=True).first()
            inv = InventoryTransaction(
                store_id=store.id,
                product_id=product.id,
                product_unit_id=unit.id if unit else None,
                qty_change=Decimal('100'),
                ref_type='import',
                notes='Nhập kho ban đầu',
                created_by_user_id=owner.id
            )
            db.session.add(inv)
        
        db.session.commit()
        print(f"  Created initial inventory for all products")
        
        print("\n✅ Seed completed successfully!")
        print("\n📝 Test accounts:")
        print("   Admin:    admin@bizflow.vn / admin123")
        print("   Owner:    owner@bizflow.vn / owner123")
        print("   Employee: nhanvien@bizflow.vn / nhanvien123")
        print(f"\n   Store ID: {store.id}")


if __name__ == '__main__':
    seed_database()
