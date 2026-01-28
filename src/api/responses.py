# API Responses - Standardized JSON response format

from flask import jsonify, Response
from typing import Any, Optional
import json


def success_response(
    data: Any = None,
    message: str = None,
    meta: dict = None,
    status_code: int = 200
) -> tuple[Response, int]:
    """Create a successful JSON response.
    
    Format:
    {
        "success": true,
        "data": {...},
        "message": "...",
        "meta": {...}
    }
    """
    response = {
        "success": True,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    if meta:
        response["meta"] = meta
    
    return jsonify(response), status_code


def error_response(
    code: str,
    message: str,
    details: Any = None,
    status_code: int = 400
) -> tuple[Response, int]:
    """Create an error JSON response.
    
    Format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Error message",
            "details": {...}
        }
    }
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return jsonify(response), status_code


def paginated_response(
    data: list,
    page: int,
    per_page: int,
    total: int,
    message: str = None
) -> tuple[Response, int]:
    """Create a paginated response.
    
    Format:
    {
        "success": true,
        "data": [...],
        "meta": {
            "page": 1,
            "per_page": 20,
            "total": 100,
            "total_pages": 5,
            "has_next": true,
            "has_prev": false
        }
    }
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return success_response(data=data, message=message, meta=meta)


def created_response(data: Any = None, message: str = "Tạo thành công") -> tuple[Response, int]:
    """Response for successful creation (201)."""
    return success_response(data=data, message=message, status_code=201)


def no_content_response() -> tuple[Response, int]:
    """Response for successful deletion (204)."""
    return '', 204


def validation_error_response(errors: dict) -> tuple[Response, int]:
    """Response for validation errors."""
    return error_response(
        code="VALIDATION_ERROR",
        message="Dữ liệu không hợp lệ",
        details=errors,
        status_code=400
    )


def not_found_response(resource: str = "Dữ liệu") -> tuple[Response, int]:
    """Response for resource not found."""
    return error_response(
        code="NOT_FOUND",
        message=f"{resource} không tìm thấy",
        status_code=404
    )


def unauthorized_response(message: str = "Yêu cầu đăng nhập") -> tuple[Response, int]:
    """Response for unauthorized access."""
    return error_response(
        code="UNAUTHORIZED",
        message=message,
        status_code=401
    )


def forbidden_response(message: str = "Không có quyền truy cập") -> tuple[Response, int]:
    """Response for forbidden access."""
    return error_response(
        code="FORBIDDEN",
        message=message,
        status_code=403
    )


def conflict_response(message: str = "Xung đột dữ liệu") -> tuple[Response, int]:
    """Response for conflict errors."""
    return error_response(
        code="CONFLICT",
        message=message,
        status_code=409
    )


def internal_error_response(message: str = "Lỗi hệ thống") -> tuple[Response, int]:
    """Response for internal server errors."""
    return error_response(
        code="INTERNAL_ERROR",
        message=message,
        status_code=500
    )