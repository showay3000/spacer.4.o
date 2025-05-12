import requests
import base64
from datetime import datetime
from flask import current_app
import json

class MpesaAPI:
    def __init__(self):
        self.consumer_key = current_app.config['MPESA_CONSUMER_KEY']
        self.consumer_secret = current_app.config['MPESA_CONSUMER_SECRET']
        self.business_shortcode = current_app.config['MPESA_BUSINESS_SHORTCODE']
        self.passkey = current_app.config['MPESA_PASSKEY']
        self.callback_url = f"{current_app.config['BACKEND_URL']}/api/payments/mpesa-callback"
        
        # API endpoints
        self.auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    def get_auth_token(self):
        """Get OAuth token from Safaricom."""
        try:
            auth_string = base64.b64encode(
                f"{self.consumer_key}:{self.consumer_secret}".encode('utf-8')
            ).decode('utf-8')
            
            headers = {
                "Authorization": f"Basic {auth_string}"
            }
            
            response = requests.get(self.auth_url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('access_token')
        except Exception as e:
            current_app.logger.error(f"Error getting Mpesa auth token: {str(e)}")
            return None
    
    def generate_password(self):
        """Generate password for STK push."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(password_string.encode('utf-8')).decode('utf-8'), timestamp
    
    def initiate_stk_push(self, phone_number, amount, booking_id):
        """Initiate STK push to customer's phone."""
        try:
            access_token = self.get_auth_token()
            if not access_token:
                return False, "Could not get authentication token"
            
            password, timestamp = self.generate_password()
            
            # Format phone number (remove leading 0 or +254)
            if phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": f"SPACER-{booking_id}",
                "TransactionDesc": f"Payment for booking {booking_id}"
            }
            
            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ResponseCode') == "0":
                return True, result.get('CheckoutRequestID')
            else:
                return False, result.get('ResponseDescription', 'Unknown error occurred')
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error initiating Mpesa payment: {str(e)}")
            return False, "Failed to initiate payment. Please try again."
        except Exception as e:
            current_app.logger.error(f"Unexpected error in Mpesa payment: {str(e)}")
            return False, "An unexpected error occurred. Please try again." 