
import requests
import logging
from django.conf import settings
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class ChapaService:
    """
    Service class for interacting with Chapa Payment API
    """
    
    def __init__(self):
        self.base_url = "https://api.chapa.co/v1"
        self.secret_key = getattr(settings, 'CHAPA_SECRET_KEY', '')
        
        if not self.secret_key:
            logger.warning("CHAPA_SECRET_KEY not found in settings")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Chapa API requests"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def initialize_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize payment with Chapa API
        
        Args:
            payment_data: Dictionary containing payment information
            
        Returns:
            Dictionary containing API response
        """
        url = f"{self.base_url}/transaction/initialize"
        headers = self._get_headers()
        
        try:
            response = requests.post(url, json=payment_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"Payment initialized successfully: {response_data.get('data', {}).get('tx_ref')}")
            
            return {
                'status': 'success',
                'data': response_data.get('data', {}),
                'message': response_data.get('message', 'Payment initialized successfully')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initializing payment: {str(e)}")
            return {
                'status': 'error',
                'message': f'Payment initialization failed: {str(e)}',
                'data': {}
            }
        except Exception as e:
            logger.error(f"Unexpected error initializing payment: {str(e)}")
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}',
                'data': {}
            }
    
    def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify payment status with Chapa API
        
        Args:
            tx_ref: Transaction reference to verify
            
        Returns:
            Dictionary containing verification response
        """
        url = f"{self.base_url}/transaction/verify/{tx_ref}"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"Payment verification completed for: {tx_ref}")
            
            return {
                'status': 'success',
                'data': response_data.get('data', {}),
                'message': response_data.get('message', 'Payment verified successfully')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying payment {tx_ref}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Payment verification failed: {str(e)}',
                'data': {}
            }
        except Exception as e:
            logger.error(f"Unexpected error verifying payment {tx_ref}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}',
                'data': {}
            }
    
    def get_banks(self) -> Dict[str, Any]:
        """
        Get list of supported banks from Chapa API
        
        Returns:
            Dictionary containing banks list
        """
        url = f"{self.base_url}/banks"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            
            return {
                'status': 'success',
                'data': response_data.get('data', []),
                'message': response_data.get('message', 'Banks retrieved successfully')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting banks: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to get banks: {str(e)}',
                'data': []
            }
        except Exception as e:
            logger.error(f"Unexpected error getting banks: {str(e)}")
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}',
                'data': []
            }
    
    def format_payment_data(self, payment_instance) -> Dict[str, Any]:
        """
        Format payment data for Chapa API
        
        Args:
            payment_instance: Payment model instance
            
        Returns:
            Formatted payment data dictionary
        """
        return {
            'amount': float(payment_instance.amount),
            'currency': payment_instance.currency,
            'email': payment_instance.customer_email,
            'first_name': payment_instance.customer_name.split(' ')[0] if payment_instance.customer_name else '',
            'last_name': ' '.join(payment_instance.customer_name.split(' ')[1:]) if payment_instance.customer_name else '',
            'phone_number': payment_instance.customer_phone or '',
            'tx_ref': payment_instance.chapa_reference,
            'callback_url': self._get_callback_url(),
            'return_url': self._get_return_url(),
            'description': f'Booking payment for {payment_instance.booking.listing.title}',
            'meta': {
                'booking_id': str(payment_instance.booking.id),
                'listing_id': str(payment_instance.booking.listing.id),
                'payment_id': str(payment_instance.id)
            }
        }
    
    def _get_callback_url(self) -> str:
        """Get callback URL for payment webhooks"""
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}/api/payments/webhook/"
    
    def _get_return_url(self) -> str:
        """Get return URL after payment completion"""
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}/payment/success/"