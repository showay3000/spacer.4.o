from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/api/')
def index():
    return jsonify({
        'message': 'Welcome to Spacer API',
        'endpoints': {
            'auth': '/api/auth',
            'spaces': '/api/spaces',
            'bookings': '/api/bookings'
        }
    }) 