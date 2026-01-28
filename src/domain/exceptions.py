# Domain Exceptions - Custom exceptions for BizFlow

class BizFlowException(Exception):
    """Base exception for BizFlow."""
    code = "BIZFLOW_ERROR"
    message = "Lỗi hệ thống"
    status_code = 500

    def __init__(self, message: str = None, details: dict = None):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# Authentication & Authorization Errors
class AuthenticationError(BizFlowException):
    """Invalid credentials."""
    code = "AUTHENTICATION_FAILED"
    message = "Email hoặc mật khẩu không đúng"
    status_code = 401


class AuthorizationError(BizFlowException):
    """Permission denied."""
    code = "PERMISSION_DENIED"
    message = "Bạn không có quyền thực hiện thao tác này"
    status_code = 403


class TokenExpiredError(BizFlowException):
    """JWT token expired."""
    code = "TOKEN_EXPIRED"
    message = "Phiên đăng nhập đã hết hạn"
    status_code = 401


# Validation Errors
class ValidationError(BizFlowException):
    """Request validation failed."""
    code = "VALIDATION_ERROR"
    message = "Dữ liệu không hợp lệ"
    status_code = 400


class DuplicateError(BizFlowException):
    """Duplicate resource."""
    code = "DUPLICATE_ERROR"
    message = "Dữ liệu đã tồn tại"
    status_code = 409


# Resource Errors
class NotFoundError(BizFlowException):
    """Resource not found."""
    code = "NOT_FOUND"
    message = "Không tìm thấy dữ liệu"
    status_code = 404


class ResourceConflictError(BizFlowException):
    """Resource conflict (e.g., insufficient stock)."""
    code = "RESOURCE_CONFLICT"
    message = "Lỗi xung đột dữ liệu"
    status_code = 409


# Business Logic Errors
class InsufficientStockError(BizFlowException):
    """Not enough stock to complete order."""
    code = "INSUFFICIENT_STOCK"
    message = "Không đủ hàng trong kho"
    status_code = 400


class InsufficientBalanceError(BizFlowException):
    """Customer debt limit exceeded."""
    code = "INSUFFICIENT_BALANCE"
    message = "Vượt quá hạn mức công nợ"
    status_code = 400


class OrderAlreadyConfirmedError(BizFlowException):
    """Order already confirmed, cannot modify."""
    code = "ORDER_ALREADY_CONFIRMED"
    message = "Đơn hàng đã được xác nhận, không thể thay đổi"
    status_code = 400


class DraftOrderAlreadyProcessedError(BizFlowException):
    """Draft order already confirmed or rejected."""
    code = "DRAFT_ALREADY_PROCESSED"
    message = "Đơn nháp đã được xử lý"
    status_code = 400


# Store Errors
class StoreNotFoundError(NotFoundError):
    """Store not found."""
    code = "STORE_NOT_FOUND"
    message = "Không tìm thấy cửa hàng"


class StoreLimitExceededError(BizFlowException):
    """Store limit for subscription plan exceeded."""
    code = "STORE_LIMIT_EXCEEDED"
    message = "Đã đạt giới hạn cửa hàng theo gói dịch vụ"
    status_code = 403


# External Service Errors
class AIServiceError(BizFlowException):
    """AI service unavailable or failed."""
    code = "AI_SERVICE_ERROR"
    message = "Dịch vụ AI không khả dụng"
    status_code = 503


class RedisConnectionError(BizFlowException):
    """Redis connection failed."""
    code = "REDIS_CONNECTION_ERROR"
    message = "Lỗi kết nối realtime"
    status_code = 503