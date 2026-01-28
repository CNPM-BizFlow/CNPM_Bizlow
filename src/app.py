# BizFlow API - Main Application

from flask import Flask, jsonify
from flasgger import Swagger
from flask_swagger_ui import get_swaggerui_blueprint

from config import FactoryConfig, swagger_template, swagger_config
from extensions import init_extensions, db
from domain.exceptions import BizFlowException


def create_app(config_name: str = None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config_class = FactoryConfig.get_config(config_name)
    app.config.from_object(config_class)
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize Swagger
    Swagger(app, template=swagger_template, config=swagger_config)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Swagger UI
    SWAGGER_URL = '/docs'
    API_URL = '/apispec.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "BizFlow API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Health check
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'app': 'BizFlow API',
            'version': '1.0.0'
        })
    
    # Root
    @app.route('/')
    def root():
        return jsonify({
            'app': 'BizFlow API',
            'version': '1.0.0',
            'docs': '/docs',
            'health': '/health'
        })
    
    # Create tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    return app


def register_blueprints(app):
    """Register all API blueprints."""
    from api.controllers.auth_controller import auth_bp
    from api.controllers.user_controller import user_bp
    from api.controllers.product_controller import product_bp
    from api.controllers.order_controller import order_bp
    from api.controllers.customer_controller import customer_bp
    from api.controllers.draft_order_controller import draft_bp
    from api.controllers.report_controller import report_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(draft_bp)
    app.register_blueprint(report_bp)
    
    print("All blueprints registered:")
    print("  - /api/v1/auth")
    print("  - /api/v1/owners, /api/v1/employees")
    print("  - /api/v1/products, /api/v1/inventory")
    print("  - /api/v1/orders")
    print("  - /api/v1/customers")
    print("  - /api/v1/draft-orders, /api/v1/ai/draft-orders")
    print("  - /api/v1/reports")


def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(BizFlowException)
    def handle_bizflow_exception(e):
        return jsonify({
            'success': False,
            'error': e.to_dict()
        }), e.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e.description) if hasattr(e, 'description') else 'Bad request'
            }
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            }
        }), 500


# Run the application
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=9999, debug=True)