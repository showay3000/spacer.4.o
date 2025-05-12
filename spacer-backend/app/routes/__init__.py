from flask import Blueprint
from .main import main_bp
from .auth import auth_bp
from .spaces import spaces_bp
from .bookings import bookings_bp
 
# def init_routes(app):
#     app.register_blueprint(main_bp)
#     app.register_blueprint(auth_bp, url_prefix='/api/auth')
#     app.register_blueprint(spaces_bp, url_prefix='/api/spaces')
#     app.register_blueprint(bookings_bp, url_prefix='/api/bookings') 