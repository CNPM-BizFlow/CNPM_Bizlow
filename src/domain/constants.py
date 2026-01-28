# Domain Constants - Enums and Constants for BizFlow

from enum import Enum


class Role(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    OWNER = "owner"
    EMPLOYEE = "employee"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class OrderStatus(str, Enum):
    """Order processing status."""
    NEW = "new"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELED = "canceled"


class DraftOrderStatus(str, Enum):
    """AI Draft Order status."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class TransactionType(str, Enum):
    """Bookkeeping transaction types (TT88 compliance)."""
    REVENUE = "revenue"          # Doanh thu
    EXPENSE = "expense"          # Chi phí
    DEBT_IN = "debt_in"          # Công nợ phải thu (bán chịu)
    DEBT_OUT = "debt_out"        # Công nợ phải trả
    PAYMENT_IN = "payment_in"    # Thu tiền công nợ
    PAYMENT_OUT = "payment_out"  # Trả tiền công nợ
    INVENTORY_IN = "inventory_in"   # Nhập kho
    INVENTORY_OUT = "inventory_out" # Xuất kho


class SubscriptionPlan(str, Enum):
    """Store subscription plans."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"


# Permission definitions for RBAC
PERMISSIONS = {
    Role.ADMIN: [
        "manage_owners",
        "manage_subscriptions",
        "view_system_reports",
        "manage_system_config"
    ],
    Role.OWNER: [
        "manage_store",
        "manage_products",
        "manage_inventory",
        "manage_customers",
        "manage_employees",
        "create_orders",
        "view_orders",
        "manage_orders",
        "view_reports",
        "manage_debt",
        "confirm_draft_orders"
    ],
    Role.EMPLOYEE: [
        "create_orders",
        "view_orders",
        "view_products",
        "view_customers",
        "confirm_draft_orders"
    ]
}


def has_permission(role: Role, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in PERMISSIONS.get(role, [])


def get_permissions(role: Role) -> list:
    """Get all permissions for a role."""
    return PERMISSIONS.get(role, [])