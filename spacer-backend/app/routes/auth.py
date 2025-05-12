from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models.user import User
from app import db
from app.utils.email import send_verification_email
from app.utils.validators import validate_email, validate_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('', methods=['GET'])
@auth_bp.route('/', methods=['GET'])
def auth_index():
    return jsonify({
        'message': 'Auth endpoints',
        'endpoints': {
            'register': '/api/auth/register',
            'login': '/api/auth/login',
            'refresh': '/api/auth/refresh',
            'me': '/api/auth/me'
        }
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: Password123!
            first_name:
              type: string
              example: John
            last_name:
              type: string
              example: Doe
            role:
              type: string
              enum: [client, owner, admin]
              example: client
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: User registered successfully
            user:
              $ref: '#/components/schemas/User'
            access_token:
              type: string
            refresh_token:
              type: string
      400:
        description: Invalid input
    """
    data = request.get_json()
    current_app.logger.info(f"Registration data received: {data}")
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate role if provided
    role = data.get('role', 'client').lower()
    current_app.logger.info(f"Role from request (lowercase): {role}")
    if role not in User.VALID_ROLES:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(User.VALID_ROLES)}'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    try:
        # Create new user with explicit role setting
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=role
        )
        current_app.logger.info(f"User role before save: {user.role}")
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"User role after save: {user.role}")
        
        # Create access and refresh tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    except ValueError as ve:
        current_app.logger.error(f"Role assignment error: {str(ve)}")
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login a user
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: Password123!
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
            user:
              $ref: '#/components/schemas/User'
      400:
        description: Invalid input
      401:
        description: Invalid email or password
    """
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    # Implement email verification logic here
    # This would typically involve decoding the token and updating the user's verification status
    pass

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user profile
    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Current user profile
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Getting user details for ID: {current_user_id}")
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        current_app.logger.info(f"User role: {user.role}")
        return jsonify(user.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f"Error getting current user: {str(e)}")
        return jsonify({'error': str(e)}), 401 