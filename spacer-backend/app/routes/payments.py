from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.booking import Booking, Payment
from app.models.user import User
from app import db
from app.utils.mpesa import MpesaAPI

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/mpesa/initiate/<int:booking_id>', methods=['POST'])
@jwt_required()
def initiate_mpesa_payment(booking_id):
    """
    Initiate M-Pesa STK push payment
    ---
    tags:
      - Payments
    security:
      - BearerAuth: []
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
        description: ID of the booking to pay for
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - phone_number
          properties:
            phone_number:
              type: string
              description: Phone number in format 254XXXXXXXXX (12 digits)
              example: 254712345678
              pattern: ^254[0-9]{9}$
    responses:
      200:
        description: Payment initiated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Payment initiated successfully
                checkout_request_id:
                  type: string
                  example: ws_CO_123456789
                  description: M-Pesa checkout request ID for tracking
      400:
        description: Invalid input
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: Invalid phone number format
      401:
        description: Unauthorized - valid JWT token required
      403:
        description: Forbidden - user not authorized to pay for this booking
      404:
        description: Booking not found
      422:
        description: Payment processing error
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: M-Pesa service unavailable
    """
    current_user_id = get_jwt_identity()
    
    # Get the booking
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking
    if booking.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if booking can be paid for
    if booking.status != 'pending' or booking.payment_status != 'pending':
        return jsonify({'error': 'Invalid booking status for payment'}), 400
    
    # Get phone number from request
    data = request.get_json()
    if not data or 'phone_number' not in data:
        return jsonify({'error': 'Phone number is required'}), 400
    
    phone_number = data['phone_number']
    
    # Initialize M-Pesa API
    mpesa = MpesaAPI()
    
    # Initiate STK push
    success, result = mpesa.initiate_stk_push(
        phone_number=phone_number,
        amount=booking.total_price,
        booking_id=booking.id
    )
    
    if success:
        # Create payment record
        payment = Payment(
            booking_id=booking.id,
            amount=booking.total_price,
            payment_method='mpesa',
            transaction_id=result  # result contains CheckoutRequestID
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment initiated successfully',
            'checkout_request_id': result
        }), 200
    else:
        return jsonify({'error': result}), 400

@payments_bp.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    """
    M-Pesa payment callback endpoint
    ---
    tags:
      - Payments
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              Body:
                type: object
                properties:
                  stkCallback:
                    type: object
                    properties:
                      MerchantRequestID:
                        type: string
                        example: 123456-7890123-1
                      CheckoutRequestID:
                        type: string
                        example: ws_CO_123456789
                      ResultCode:
                        type: integer
                        example: 0
                      ResultDesc:
                        type: string
                        example: The service request is processed successfully.
                      CallbackMetadata:
                        type: object
                        properties:
                          Item:
                            type: array
                            items:
                              type: object
                              properties:
                                Name:
                                  type: string
                                  example: Amount
                                Value:
                                  type: number
                                  example: 1000.00
    responses:
      200:
        description: Callback processed successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Callback processed successfully
      400:
        description: Invalid callback data
    """
    data = request.get_json()
    
    try:
        # Extract relevant information from callback data
        result_code = data['Body']['stkCallback']['ResultCode']
        checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']
        
        # Find payment by checkout_request_id
        payment = Payment.query.filter_by(transaction_id=checkout_request_id).first()
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        if result_code == 0:
            # Payment successful
            payment.status = 'completed'
            payment.booking.status = 'confirmed'
            payment.booking.payment_status = 'paid'
        else:
            # Payment failed
            payment.status = 'failed'
            payment.booking.status = 'pending'
            payment.booking.payment_status = 'pending'
        
        db.session.commit()
        return jsonify({'message': 'Callback processed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 