from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from flasgger import Swagger
from app.extensions import db, migrate, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Import models
    from app.models import user, space, booking, testimonial
    
    # Configure CORS - Development configuration
    CORS(app, 
         resources={r"/api/*": {
             "origins": ["http://localhost:5173", "http://127.0.0.1:5173",
                        "http://localhost:5174", "http://127.0.0.1:5174",
                        "http://localhost:5175", "http://127.0.0.1:5175"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
             "expose_headers": ["Content-Range", "X-Content-Range"],
             "supports_credentials": True,
             "max_age": 120
         }})

    # Add error handlers
    @app.errorhandler(500)
    def handle_500_error(e):
        response = jsonify({"error": "Internal server error", "message": str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5174')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 500

    @app.errorhandler(404)
    def handle_404_error(e):
        response = jsonify({"error": "Not found", "message": str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5174')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 404

    @app.after_request
    def after_request(response):
        if not response.headers.get('Access-Control-Allow-Origin'):
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5174')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Configure Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Spacer API",
            "description": "API for managing space bookings",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header"
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "email": {"type": "string", "example": "user@example.com"},
                        "first_name": {"type": "string", "example": "John"},
                        "last_name": {"type": "string", "example": "Doe"},
                        "name": {"type": "string", "example": "John Doe"},
                        "role": {"type": "string", "enum": ["admin", "owner", "client"], "example": "client"},
                        "phone": {"type": "string", "example": "254712345678"},
                        "bio": {"type": "string", "example": "Software developer"},
                        "avatar_url": {"type": "string", "example": "https://example.com/avatar.jpg"},
                        "is_verified": {"type": "boolean", "example": True},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    }
                },
                "Space": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "name": {"type": "string", "example": "Conference Room"},
                        "description": {"type": "string", "example": "Spacious room for meetings"},
                        "address": {"type": "string", "example": "123 Main St"},
                        "city": {"type": "string", "example": "Nairobi"},
                        "price_per_hour": {"type": "number", "example": 100.0},
                        "capacity": {"type": "integer", "example": 20},
                        "is_available": {"type": "boolean", "example": True},
                        "owner_id": {"type": "integer", "example": 1},
                        "images": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 1},
                                    "image_url": {"type": "string", "example": "https://example.com/space.jpg"},
                                    "is_primary": {"type": "boolean", "example": True}
                                }
                            }
                        },
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    }
                },
                "Booking": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "space_id": {"type": "integer", "example": 1},
                        "user_id": {"type": "integer", "example": 1},
                        "start_time": {"type": "string", "format": "date-time"},
                        "end_time": {"type": "string", "format": "date-time"},
                        "total_price": {"type": "number", "example": 200.0},
                        "purpose": {"type": "string", "example": "Team meeting"},
                        "status": {"type": "string", "enum": ["pending", "confirmed", "cancelled", "completed"], "example": "pending"},
                        "payment_status": {"type": "string", "enum": ["pending", "paid", "refunded"], "example": "pending"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    }
                },
                "Payment": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "booking_id": {"type": "integer", "example": 1},
                        "amount": {"type": "number", "example": 200.0},
                        "payment_method": {"type": "string", "enum": ["mpesa", "card", "cash"], "example": "mpesa"},
                        "transaction_id": {"type": "string", "example": "MPESA123456789"},
                        "status": {"type": "string", "enum": ["pending", "completed", "failed", "refunded"], "example": "completed"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    }
                }
            }
        }
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.spaces import spaces_bp
    from app.routes.bookings import bookings_bp
    from app.routes.users import users_bp
    from app.routes.payments import payments_bp
    from app.routes.testimonials import testimonials_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(spaces_bp, url_prefix='/api/spaces')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(testimonials_bp, url_prefix='/api/testimonials')
    
    return app 