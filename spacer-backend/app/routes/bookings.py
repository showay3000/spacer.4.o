from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.booking import Booking, Payment
from app.models.space import Space
from app.models.user import User
from app import db
from app.utils.validators import validate_booking_dates
from app.utils.email import send_booking_confirmation_email
from datetime import datetime

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('', methods=['GET'])
@bookings_bp.route('/', methods=['GET'])
def get_bookings():
    """
    List all bookings with related space data including images
    ---
    tags:
      - Bookings
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
    responses:
      200:
        description: List of bookings with space data
        content:
          application/json:
            schema:
              type: object
              properties:
                bookings:
                  type: array
                  items:
                    type: object
                total:
                  type: integer
                  example: 100
                pages:
                  type: integer
                  example: 10
                current_page:
                  type: integer
                  example: 1
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Booking.query.options(db.joinedload(Booking.space).joinedload(Space.images))
    bookings = query.paginate(page=page, per_page=per_page)
    
    bookings_with_space = []
    for booking in bookings.items:
        booking_dict = booking.to_dict()
        if booking.space:
            booking_dict['space'] = booking.space.to_dict()
        else:
            booking_dict['space'] = None
        bookings_with_space.append(booking_dict)
    
    return jsonify({
        'bookings': bookings_with_space,
        'total': bookings.total,
        'pages': bookings.pages,
        'current_page': bookings.page
    })

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """
    Get a booking by ID
    ---
    tags:
      - Bookings
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
        description: Booking ID
    responses:
      200:
        description: Booking details
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Booking'
      404:
        description: Booking not found
    """
    booking = Booking.query.get_or_404(booking_id)
    return jsonify(booking.to_dict())

@bookings_bp.route('/', methods=['POST'])
@jwt_required()
def create_booking():
    """
    Create a new booking
    ---
    tags:
      - Bookings
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - space_id
            - start_time
            - end_time
            - purpose
          properties:
            space_id:
              type: integer
              example: 1
              description: ID of the space to book
            start_time:
              type: string
              format: date-time
              example: 2024-03-20T14:00:00Z
              description: Booking start time (ISO 8601 format)
            end_time:
              type: string
              format: date-time
              example: 2024-03-20T16:00:00Z
              description: Booking end time (ISO 8601 format)
            purpose:
              type: string
              example: Team meeting
              description: Purpose of the booking
    responses:
      201:
        description: Booking created successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Booking'
      400:
        description: Invalid input
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: Space is not available or booking dates are invalid
      401:
        description: Unauthorized - valid JWT token required
      403:
        description: Forbidden - insufficient permissions
      404:
        description: Space not found
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['space_id', 'start_time', 'end_time', 'purpose']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate dates
    is_valid, error_message = validate_booking_dates(data['start_time'], data['end_time'])
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    # Check if space exists and is available
    space = Space.query.get_or_404(data['space_id'])
    if not space.is_available:
        return jsonify({'error': 'Space is not available'}), 400
    
    # Check for overlapping bookings
    start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
    
    overlapping_booking = Booking.query.filter(
        Booking.space_id == space.id,
        Booking.status != 'cancelled',
        (
            (Booking.start_time <= start_time) & (Booking.end_time > start_time) |
            (Booking.start_time < end_time) & (Booking.end_time >= end_time) |
            (Booking.start_time >= start_time) & (Booking.end_time <= end_time)
        )
    ).first()
    
    if overlapping_booking:
        return jsonify({'error': 'Space is already booked for this time period'}), 400
    
    # Calculate total price
    duration_hours = (end_time - start_time).total_seconds() / 3600
    total_price = space.price_per_hour * duration_hours
    
    # Create booking
    booking = Booking(
        space_id=space.id,
        user_id=current_user_id,
        start_time=start_time,
        end_time=end_time,
        total_price=total_price,
        purpose=data['purpose']
    )
    
    db.session.add(booking)
    # Set space as unavailable
    space.is_available = False
    db.session.commit()
    # Send confirmation email
    send_booking_confirmation_email(booking)
    return jsonify(booking.to_dict()), 201

@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    """
    Cancel a booking
    ---
    tags:
      - Bookings
    security:
      - BearerAuth: []
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
        description: Booking ID
    responses:
      200:
        description: Booking cancelled
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Booking'
      400:
        description: Invalid booking status
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: Booking is already cancelled
      401:
        description: Unauthorized
      403:
        description: Forbidden - user not authorized to cancel this booking
      404:
        description: Booking not found
    """
    current_user_id = get_jwt_identity()
    booking = Booking.query.get_or_404(booking_id)
    
    # Check authorization
    if booking.user_id != current_user_id and booking.space.owner_id != current_user_id:
        user = User.query.get(current_user_id)
        if user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if booking can be cancelled
    if booking.status == 'cancelled':
        return jsonify({'error': 'Booking is already cancelled'}), 400
    
    if booking.status == 'completed':
        return jsonify({'error': 'Cannot cancel completed booking'}), 400
    
    # Cancel booking
    booking.status = 'cancelled'
    # If payment exists, mark it as refunded
    if booking.payment:
        booking.payment.status = 'refunded'
    # Set space as available again
    booking.space.is_available = True
    db.session.commit()
    return jsonify(booking.to_dict()), 200

@bookings_bp.route('/<int:booking_id>/payment', methods=['POST'])
@jwt_required()
def process_payment(booking_id):
    """
    Process payment for a booking
    ---
    tags:
      - Bookings
    security:
      - BearerAuth: []
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
        description: Booking ID
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - payment_method
            properties:
              payment_method:
                type: string
                enum: [mpesa, card, cash]
                example: mpesa
              transaction_id:
                type: string
                example: MPESA123456789
    responses:
      201:
        description: Payment processed
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Payment'
      400:
        description: Invalid input or booking status
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: Invalid booking status for payment
      401:
        description: Unauthorized
      403:
        description: Forbidden - user not authorized to process payment
      404:
        description: Booking not found
    """
    current_user_id = get_jwt_identity()
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if booking.status != 'pending':
        return jsonify({'error': 'Invalid booking status for payment'}), 400
    
    data = request.get_json()
    if 'payment_method' not in data:
        return jsonify({'error': 'Payment method is required'}), 400
    
    # Create payment record
    payment = Payment(
        booking_id=booking.id,
        amount=booking.total_price,
        payment_method=data['payment_method'],
        transaction_id=data.get('transaction_id')  # For external payment systems
    )
    
    db.session.add(payment)
    
    # Update booking status
    booking.status = 'confirmed'
    booking.payment_status = 'paid'
    
    db.session.commit()
    return jsonify(payment.to_dict()), 201

@bookings_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_bookings():
    """
    Get current user's bookings
    ---
    tags:
      - Bookings
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
    responses:
      200:
        description: List of user's bookings
        content:
          application/json:
            schema:
              type: object
              properties:
                bookings:
                  type: array
                  items:
                    type: object
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
    """
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Booking.query.filter_by(user_id=current_user_id).options(
        db.joinedload(Booking.space).joinedload(Space.images)
    )
    bookings = query.paginate(page=page, per_page=per_page)
    
    bookings_with_space = []
    for booking in bookings.items:
        booking_dict = booking.to_dict()
        if booking.space:
            booking_dict['space'] = booking.space.to_dict()
        else:
            booking_dict['space'] = None
        bookings_with_space.append(booking_dict)
    
    return jsonify({
        'bookings': bookings_with_space,
        'total': bookings.total,
        'pages': bookings.pages,
        'current_page': bookings.page
    }) 