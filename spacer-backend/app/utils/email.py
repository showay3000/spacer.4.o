import os
from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail, SendSmtpEmailTo
from flask import current_app
import jwt
from datetime import datetime, timedelta

def get_email_client():
    configuration = Configuration()
    configuration.api_key['api-key'] = current_app.config['SENDINBLUE_API_KEY']
    api_client = ApiClient(configuration)
    return TransactionalEmailsApi(api_client)

def generate_verification_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def send_verification_email(user):
    try:
        api_instance = get_email_client()
        
        # Generate verification token
        token = generate_verification_token(user)
        verification_url = f"{current_app.config['FRONTEND_URL']}/verify-email/{token}"
        
        # Create email content
        to = [SendSmtpEmailTo(email=user.email, name=f"{user.first_name} {user.last_name}")]
        email = SendSmtpEmail(
            to=to,
            subject="Verify your Spacer account",
            html_content=f"""
            <h1>Welcome to Spacer!</h1>
            <p>Hi {user.first_name},</p>
            <p>Thank you for registering with Spacer. Please click the link below to verify your email address:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, you can safely ignore this email.</p>
            """
        )
        
        # Send email
        api_instance.send_transac_email(email)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        return False

def send_booking_confirmation_email(booking):
    try:
        api_instance = get_email_client()
        user = booking.user
        space = booking.space
        
        to = [SendSmtpEmailTo(email=user.email, name=f"{user.first_name} {user.last_name}")]
        email = SendSmtpEmail(
            to=to,
            subject="Booking Confirmation - Spacer",
            html_content=f"""
            <h1>Booking Confirmation</h1>
            <p>Hi {user.first_name},</p>
            <p>Your booking for {space.name} has been confirmed.</p>
            <p>Details:</p>
            <ul>
                <li>Space: {space.name}</li>
                <li>Date: {booking.start_time.strftime('%Y-%m-%d')}</li>
                <li>Time: {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}</li>
                <li>Total: ${booking.total_price}</li>
            </ul>
            <p>Thank you for using Spacer!</p>
            """
        )
        
        api_instance.send_transac_email(email)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send booking confirmation email: {str(e)}")
        return False 