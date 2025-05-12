from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app import db
from app.utils.validators import validate_email, validate_password
from app.utils.cloudinary import upload_image

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """
    List all users (Admin only)
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        description: Page number
        example: 1
      - name: per_page
        in: query
        type: integer
        required: false
        description: Results per page
        example: 10
      - name: role
        in: query
        type: string
        required: false
        description: Filter by user role
        enum: [admin, owner, client]
    responses:
      200:
        description: List of users
        content:
          application/json:
            schema:
              type: object
              properties:
                users:
                  type: array
                  items:
                    $ref: '#/components/schemas/User'
                total:
                  type: integer
                  example: 100
                pages:
                  type: integer
                  example: 10
                current_page:
                  type: integer
                  example: 1
      401:
        description: Unauthorized
      403:
        description: Forbidden - user is not admin
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role = request.args.get('role')
    
    query = User.query
    if role:
        query = query.filter_by(role=role)
    
    users = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': users.page
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Get user by ID
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User details
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      401:
        description: Unauthorized
      403:
        description: Forbidden - user not authorized to view this profile
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user_id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """
    Update user details
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: User ID
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              first_name:
                type: string
                example: John
              last_name:
                type: string
                example: Doe
              email:
                type: string
                format: email
                example: john.doe@example.com
              password:
                type: string
                format: password
                example: NewStrongP@ssw0rd
              role:
                type: string
                enum: [admin, owner, client]
                description: Can only be set by admin users
    responses:
      200:
        description: User updated successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      400:
        description: Invalid input
      401:
        description: Unauthorized
      403:
        description: Forbidden - user not authorized to update this profile
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user_id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # Update user fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        if User.query.filter(User.email == data['email'], User.id != user_id).first():
            return jsonify({'error': 'Email already in use'}), 400
        user.email = data['email']
    if 'password' in data:
        if not validate_password(data['password']):
            return jsonify({'error': 'Invalid password format'}), 400
        user.set_password(data['password'])
    if 'role' in data and current_user.role == 'admin':
        if data['role'] not in ['admin', 'owner', 'client']:
            return jsonify({'error': 'Invalid role'}), 400
        user.role = data['role']
    
    db.session.commit()
    return jsonify(user.to_dict()), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """
    Delete user (Admin only)
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User deleted successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: User deleted successfully
      400:
        description: Cannot delete own account
      401:
        description: Unauthorized
      403:
        description: Forbidden - user is not admin
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user_id == current_user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@users_bp.route('/verify/<token>', methods=['GET'])
def verify_user(token):
    """
    Verify user email
    ---
    tags:
      - Users
    parameters:
      - name: token
        in: path
        type: string
        required: true
        description: Email verification token
    responses:
      200:
        description: Email verified successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Email verified successfully
      400:
        description: Invalid or expired verification link
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        
        user = User.query.get_or_404(user_id)
        user.is_verified = True
        db.session.commit()
        
        return jsonify({'message': 'Email verified successfully'}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Verification link has expired'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid verification link'}), 400

@users_bp.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def user_profile():
    """
    Get or update current user profile
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    get:
      responses:
        200:
          description: Current user profile
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        401:
          description: Unauthorized
    put:
      parameters:
        - in: formData
          name: first_name
          type: string
          required: false
          description: User's first name
          example: John
        - in: formData
          name: last_name
          type: string
          required: false
          description: User's last name
          example: Doe
        - in: formData
          name: email
          type: string
          format: email
          required: false
          description: User's email address
          example: john.doe@example.com
        - in: formData
          name: phone
          type: string
          required: false
          description: Phone number in format 254XXXXXXXXX
          example: "254712345678"
        - in: formData
          name: bio
          type: string
          required: false
          description: User's bio
          example: Software developer with 5 years experience
        - in: formData
          name: avatar
          type: file
          required: false
          description: User's profile picture
      consumes:
        - multipart/form-data
      responses:
        200:
          description: Profile updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        400:
          description: Invalid input
        401:
          description: Unauthorized
        500:
          description: Failed to upload avatar
    """
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    if request.method == 'GET':
        return jsonify(user.to_dict()), 200
    if request.method == 'PUT':
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            data = request.form
            file = request.files.get('avatar')
        else:
            data = request.get_json()
            file = None
        if 'name' in data:
            name_parts = data['name'].split()
            user.first_name = name_parts[0]
            user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            if not validate_email(data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            user.email = data['email']
        if 'phone' in data:
            phone = data['phone']
            if phone and not phone.isdigit():
                return jsonify({'error': 'Invalid phone number'}), 400
            user.phone = phone
        if 'bio' in data:
            user.bio = data['bio']
        if file:
            try:
                image_url = upload_image(file, folder='avatars')
                user.avatar_url = image_url
            except Exception as e:
                return jsonify({'error': f'Failed to upload avatar: {str(e)}'}), 500
        db.session.commit()
        return jsonify(user.to_dict()), 200

@users_bp.route('/activities', methods=['GET'])
@jwt_required()
def user_activities():
    """
    Get current user's activities
    ---
    tags:
      - Users
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of user activities
        content:
          application/json:
            schema:
              type: object
              properties:
                activities:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 1
                      type:
                        type: string
                        example: booking
                      description:
                        type: string
                        example: Booked space Conference Room for meeting
                      created_at:
                        type: string
                        format: date-time
                        example: 2025-05-06T13:37:03.739683
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    activities = []
    for b in user.bookings:
        activities.append({
            'id': b.id,
            'type': 'booking',
            'description': f'Booked space {b.space.name} for {b.purpose}',
            'created_at': b.created_at.isoformat(),
        })
    return jsonify({'activities': activities}), 200 