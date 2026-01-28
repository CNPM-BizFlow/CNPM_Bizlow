# Flask Extensions - Centralized initialization

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
import redis

# Database
db = SQLAlchemy()

# JWT Manager
jwt = JWTManager()

# Migrations
migrate = Migrate()

# Redis client (lazy initialization)
redis_client = None


def init_redis(app):
    """Initialize Redis client."""
    global redis_client
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        app.logger.info("Redis connected successfully")
    except Exception as e:
        app.logger.warning(f"Redis connection failed: {e}. Realtime features disabled.")
        redis_client = None
    return redis_client


def get_redis():
    """Get Redis client instance."""
    return redis_client


def init_extensions(app):
    """Initialize all Flask extensions."""
    # SQLAlchemy
    db.init_app(app)
    
    # Migrations
    migrate.init_app(app, db)
    
    # JWT
    jwt.init_app(app)
    
    # CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    
    # Redis (optional, won't fail if unavailable)
    init_redis(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {
            "success": False,
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token đã hết hạn"
            }
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {
            "success": False,
            "error": {
                "code": "INVALID_TOKEN",
                "message": "Token không hợp lệ"
            }
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {
            "success": False,
            "error": {
                "code": "MISSING_TOKEN",
                "message": "Yêu cầu xác thực"
            }
        }, 401
