from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.space import Space, SpaceImage, SpaceAmenity
from app.models.user import User
from app import db
from app.utils.validators import validate_space_data
from app.utils.cloudinary import upload_image
from datetime import datetime
from sqlalchemy.orm import joinedload

spaces_bp = Blueprint('spaces', __name__)

@spaces_bp.route('', methods=['GET'])
@spaces_bp.route('/', methods=['GET'])
def get_spaces():
    """
    List all available spaces
    ---
    tags:
      - Spaces
    parameters:
      - in: query
        name: page
        schema:
          type: integer
        required: false
        description: Page number
      - in: query
        name: per_page
        schema:
          type: integer
        required: false
        description: Results per page
      - in: query
        name: status
        schema:
          type: string
        required: false
        description: Filter by status (available, booked, or empty for all)
      - in: query
        name: city
        schema:
          type: string
        required: false
      - in: query
        name: min_price
        schema:
          type: number
        required: false
      - in: query
        name: max_price
        schema:
          type: number
        required: false
    responses:
      200:
        description: List of spaces
        content:
          application/json:
            schema:
              type: object
              properties:
                spaces:
                  type: array
                  items:
                    $ref: '#/components/schemas/Space'
                total:
                  type: integer
                pages:
                  type: integer
                current_page:
                  type: integer
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '')
    city = request.args.get('city')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    query = Space.query.options(joinedload(Space.images))
    
    # Handle status filter
    if status == 'available':
        query = query.filter_by(is_available=True)
    elif status == 'booked':
        query = query.filter_by(is_available=False)
    
    if city:
        query = query.filter(Space.city.ilike(f'%{city}%'))
    if min_price:
        query = query.filter(Space.price_per_hour >= min_price)
    if max_price:
        query = query.filter(Space.price_per_hour <= max_price)
    
    spaces = query.paginate(page=page, per_page=per_page)
    
    # Debug log for images URLs
    for space in spaces.items:
        print(f"Space ID: {space.id}, Images: {[img.image_url for img in space.images]}")
    
    response = jsonify({
        'spaces': [space.to_dict() for space in spaces.items],
        'total': spaces.total,
        'pages': spaces.pages,
        'current_page': spaces.page
    })
    
    return response, 200

@spaces_bp.route('/<int:space_id>', methods=['GET'])
def get_space(space_id):
    """
    Get space details by ID
    ---
    tags:
      - Spaces
    parameters:
      - name: space_id
        in: path
        type: integer
        required: true
        description: Space ID
    responses:
      200:
        description: Space details
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Space'
      404:
        description: Space not found
    """
    try:
        space = Space.query.get_or_404(space_id)
        
        if not space:
            response = jsonify({'error': 'Space not found'})
            return response, 404
            
        response = jsonify(space.to_dict())
        return response, 200
        
    except Exception as e:
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        return response, 500

@spaces_bp.route('/', methods=['POST'])
@jwt_required()
def create_space():
    """
    Create a new space
    ---
    tags:
      - Spaces
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            required:
              - name
              - description
              - address
              - city
              - price_per_hour
              - capacity
            properties:
              name:
                type: string
                example: "Cozy Office Space"
              description:
                type: string
                example: "A comfortable and quiet office space in downtown."
              address:
                type: string
                example: "123 Main St, Cityville"
              city:
                type: string
                example: "Cityville"
              price_per_hour:
                type: number
                example: 25.0
              capacity:
                type: integer
                example: 10
              amenities:
                type: string
                description: Comma separated list of amenities
                example: "WiFi,Projector,Whiteboard"
              images:
                type: array
                items:
                  type: string
                  format: binary
    responses:
      201:
        description: Space created successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Space'
      400:
        description: Invalid input
      403:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form.to_dict() if request.form else request.get_json() or {}
    is_valid, error_message = validate_space_data(data)
    
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    space = Space(
        name=data['name'],
        description=data['description'],
        address=data['address'],
        city=data['city'],
        price_per_hour=float(data['price_per_hour']),
        capacity=int(data['capacity']),
        owner_id=current_user_id
    )
    
    db.session.add(space)
    db.session.flush()
    
    if 'amenities' in data:
        amenities_list = [a.strip() for a in data['amenities'].split(',') if a.strip()]
        for amenity_name in amenities_list:
            amenity = SpaceAmenity(name=amenity_name, space_id=space.id)
            db.session.add(amenity)
    
    if 'images' in request.files:
        images = request.files.getlist('images')
        for i, image in enumerate(images):
            if image:
                image_url = upload_image(image)
                space_image = SpaceImage(
                    space_id=space.id,
                    image_url=image_url,
                    is_primary=(i == 0)
                )
                db.session.add(space_image)
    
    db.session.commit()
    return jsonify(space.to_dict()), 201

@spaces_bp.route('/<int:space_id>', methods=['PUT'])
@jwt_required()
def update_space(space_id):
    current_user_id = get_jwt_identity()
    space = Space.query.get_or_404(space_id)
    
    if space.owner_id != current_user_id and User.query.get(current_user_id).role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form.to_dict() if request.form else request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        space.name = data['name']
    if 'description' in data:
        space.description = data['description']
    if 'address' in data:
        space.address = data['address']
    if 'city' in data:
        space.city = data['city']
    if 'price_per_hour' in data:
        try:
            space.price_per_hour = float(data['price_per_hour'])
        except ValueError:
            return jsonify({'error': 'Invalid price format'}), 400
    if 'capacity' in data:
        try:
            space.capacity = int(data['capacity'])
        except ValueError:
            return jsonify({'error': 'Invalid capacity format'}), 400
    
    if request.files and 'images' in request.files:
        SpaceImage.query.filter_by(space_id=space.id).delete()
        
        images = request.files.getlist('images')
        for i, image in enumerate(images):
            if image:
                try:
                    image_url = upload_image(image)
                    space_image = SpaceImage(
                        space_id=space.id,
                        image_url=image_url,
                        is_primary=(i == 0)
                    )
                    db.session.add(space_image)
                except Exception as e:
                    return jsonify({'error': f'Failed to upload image: {str(e)}'}), 422
    
    try:
        db.session.commit()
        return jsonify(space.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update space: {str(e)}'}), 422

@spaces_bp.route('/<int:space_id>', methods=['DELETE'])
@jwt_required()
def delete_space(space_id):
    current_user_id = get_jwt_identity()
    space = Space.query.get_or_404(space_id)
    
    if space.owner_id != current_user_id and User.query.get(current_user_id).role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(space)
    db.session.commit()
    return jsonify({'message': 'Space deleted successfully'}), 200
