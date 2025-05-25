"""
Real Fiat Payment Gateway Integration for Escrow Bot
Supports major payment processors for traditional currency transactions
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from enum import Enum
import aiohttp
import hashlib
import hmac

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentGateway:
    """Base class for payment gateway implementations"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        
    async def create_payment(self, amount: float, currency: str, description: str, 
                           return_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new payment request"""
        raise NotImplementedError
        
    async def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify payment status"""
        raise NotImplementedError
        
    async def refund_payment(self, payment_id: str, amount: float = None) -> Dict[str, Any]:
        """Process refund"""
        raise NotImplementedError

class StripeGateway(PaymentGateway):
    """Stripe payment gateway integration"""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.api_key = config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = config.get('STRIPE_WEBHOOK_SECRET')
        self.base_url = "https://api.stripe.com/v1"
        
    async def create_payment(self, amount: float, currency: str, description: str, 
                           return_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        if not self.api_key:
            raise ValueError("Stripe API key not configured")
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Convert amount to cents for Stripe
        amount_cents = int(amount * 100)
        
        data = {
            'payment_method_types[]': 'card',
            'line_items[0][price_data][currency]': currency.lower(),
            'line_items[0][price_data][product_data][name]': description,
            'line_items[0][price_data][unit_amount]': str(amount_cents),
            'line_items[0][quantity]': '1',
            'mode': 'payment',
            'success_url': f"{return_url}?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': return_url,
        }
        
        if metadata:
            for key, value in metadata.items():
                data[f'metadata[{key}]'] = str(value)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/checkout/sessions",
                headers=headers,
                data=data
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    return {
                        'success': True,
                        'payment_id': result['id'],
                        'payment_url': result['url'],
                        'status': PaymentStatus.PENDING.value,
                        'gateway': 'stripe'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', {}).get('message', 'Unknown error'),
                        'gateway': 'stripe'
                    }
    
    async def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify Stripe payment status"""
        if not self.api_key:
            raise ValueError("Stripe API key not configured")
            
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/checkout/sessions/{payment_id}",
                headers=headers
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    payment_status = result.get('payment_status')
                    status_map = {
                        'paid': PaymentStatus.COMPLETED.value,
                        'unpaid': PaymentStatus.PENDING.value,
                        'no_payment_required': PaymentStatus.COMPLETED.value
                    }
                    
                    return {
                        'success': True,
                        'status': status_map.get(payment_status, PaymentStatus.PENDING.value),
                        'amount': result.get('amount_total', 0) / 100,
                        'currency': result.get('currency', '').upper(),
                        'payment_intent': result.get('payment_intent'),
                        'gateway': 'stripe'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', {}).get('message', 'Unknown error'),
                        'gateway': 'stripe'
                    }

class PayPalGateway(PaymentGateway):
    """PayPal payment gateway integration"""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.client_id = config.get('PAYPAL_CLIENT_ID')
        self.client_secret = config.get('PAYPAL_CLIENT_SECRET')
        self.sandbox = config.get('PAYPAL_SANDBOX', 'true').lower() == 'true'
        self.base_url = "https://api.sandbox.paypal.com" if self.sandbox else "https://api.paypal.com"
        self._access_token = None
        
    async def _get_access_token(self) -> str:
        """Get PayPal access token"""
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal credentials not configured")
            
        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = 'grant_type=client_credentials'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=auth,
                headers=headers,
                data=data
            ) as response:
                result = await response.json()
                if response.status == 200:
                    self._access_token = result['access_token']
                    return self._access_token
                else:
                    raise Exception(f"Failed to get PayPal access token: {result}")
    
    async def create_payment(self, amount: float, currency: str, description: str, 
                           return_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create PayPal payment"""
        token = await self._get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payment_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency.upper(),
                    "value": f"{amount:.2f}"
                },
                "description": description
            }],
            "application_context": {
                "return_url": return_url,
                "cancel_url": return_url,
                "brand_name": "Escrow Bot",
                "user_action": "PAY_NOW"
            }
        }
        
        if metadata:
            payment_data["purchase_units"][0]["custom_id"] = json.dumps(metadata)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=headers,
                json=payment_data
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    approval_link = next(
                        (link['href'] for link in result['links'] if link['rel'] == 'approve'),
                        None
                    )
                    
                    return {
                        'success': True,
                        'payment_id': result['id'],
                        'payment_url': approval_link,
                        'status': PaymentStatus.PENDING.value,
                        'gateway': 'paypal'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('message', 'Unknown error'),
                        'gateway': 'paypal'
                    }

class RazorpayGateway(PaymentGateway):
    """Razorpay payment gateway integration (for Indian market)"""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.key_id = config.get('RAZORPAY_KEY_ID')
        self.key_secret = config.get('RAZORPAY_KEY_SECRET')
        self.base_url = "https://api.razorpay.com/v1"
        
    async def create_payment(self, amount: float, currency: str, description: str, 
                           return_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create Razorpay payment"""
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials not configured")
            
        auth = aiohttp.BasicAuth(self.key_id, self.key_secret)
        headers = {'Content-Type': 'application/json'}
        
        # Convert amount to smallest currency unit (paise for INR)
        amount_smallest = int(amount * 100)
        
        payment_data = {
            "amount": amount_smallest,
            "currency": currency.upper(),
            "description": description,
            "callback_url": return_url,
            "callback_method": "get"
        }
        
        if metadata:
            payment_data["notes"] = metadata
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/payment_links",
                auth=auth,
                headers=headers,
                json=payment_data
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    return {
                        'success': True,
                        'payment_id': result['id'],
                        'payment_url': result['short_url'],
                        'status': PaymentStatus.PENDING.value,
                        'gateway': 'razorpay'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', {}).get('description', 'Unknown error'),
                        'gateway': 'razorpay'
                    }

class PaymentGatewayManager:
    """Manager for multiple payment gateways"""
    
    def __init__(self):
        self.gateways = {}
        self._initialize_gateways()
    
    def _initialize_gateways(self):
        """Initialize available payment gateways"""
        config = {
            'STRIPE_SECRET_KEY': os.environ.get('STRIPE_SECRET_KEY'),
            'STRIPE_WEBHOOK_SECRET': os.environ.get('STRIPE_WEBHOOK_SECRET'),
            'PAYPAL_CLIENT_ID': os.environ.get('PAYPAL_CLIENT_ID'),
            'PAYPAL_CLIENT_SECRET': os.environ.get('PAYPAL_CLIENT_SECRET'),
            'PAYPAL_SANDBOX': os.environ.get('PAYPAL_SANDBOX', 'true'),
            'RAZORPAY_KEY_ID': os.environ.get('RAZORPAY_KEY_ID'),
            'RAZORPAY_KEY_SECRET': os.environ.get('RAZORPAY_KEY_SECRET'),
        }
        
        # Initialize Stripe if configured
        if config.get('STRIPE_SECRET_KEY'):
            self.gateways['stripe'] = StripeGateway(config)
            logger.info("Stripe gateway initialized")
        
        # Initialize PayPal if configured
        if config.get('PAYPAL_CLIENT_ID') and config.get('PAYPAL_CLIENT_SECRET'):
            self.gateways['paypal'] = PayPalGateway(config)
            logger.info("PayPal gateway initialized")
        
        # Initialize Razorpay if configured
        if config.get('RAZORPAY_KEY_ID') and config.get('RAZORPAY_KEY_SECRET'):
            self.gateways['razorpay'] = RazorpayGateway(config)
            logger.info("Razorpay gateway initialized")
    
    def get_available_gateways(self) -> list:
        """Get list of available payment gateways"""
        return list(self.gateways.keys())
    
    def get_gateway(self, gateway_name: str) -> Optional[PaymentGateway]:
        """Get specific payment gateway"""
        return self.gateways.get(gateway_name)
    
    async def create_payment(self, gateway_name: str, amount: float, currency: str, 
                           description: str, return_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create payment using specified gateway"""
        gateway = self.get_gateway(gateway_name)
        if not gateway:
            return {
                'success': False,
                'error': f'Gateway {gateway_name} not available',
                'gateway': gateway_name
            }
        
        try:
            return await gateway.create_payment(amount, currency, description, return_url, metadata)
        except Exception as e:
            logger.error(f"Payment creation failed for {gateway_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'gateway': gateway_name
            }
    
    async def verify_payment(self, gateway_name: str, payment_id: str) -> Dict[str, Any]:
        """Verify payment using specified gateway"""
        gateway = self.get_gateway(gateway_name)
        if not gateway:
            return {
                'success': False,
                'error': f'Gateway {gateway_name} not available',
                'gateway': gateway_name
            }
        
        try:
            return await gateway.verify_payment(payment_id)
        except Exception as e:
            logger.error(f"Payment verification failed for {gateway_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'gateway': gateway_name
            }

# Global payment manager instance
payment_manager = PaymentGatewayManager()