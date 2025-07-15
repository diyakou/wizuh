from typing import Dict, Optional, Union
import requests
import logging
from datetime import datetime
from database.models import Setting, SettingType, Transaction, User
from database.db import session

logger = logging.getLogger(__name__)

class PaymentGateway:
    """Base class for payment gateways."""
    def __init__(self, api_key: str, sandbox: bool = False):
        self.api_key = api_key
        self.sandbox = sandbox
    
    def create_payment(self, amount: int, description: str) -> Dict:
        """Create a payment request."""
        raise NotImplementedError
    
    def verify_payment(self, token: str) -> bool:
        """Verify a payment."""
        raise NotImplementedError

class ZarinpalGateway(PaymentGateway):
    """Zarinpal payment gateway implementation."""
    SANDBOX_URL = "https://sandbox.zarinpal.com/pg/rest/WebGate"
    PRODUCTION_URL = "https://www.zarinpal.com/pg/rest/WebGate"
    
    def __init__(self, api_key: str, sandbox: bool = False):
        super().__init__(api_key, sandbox)
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
    
    def create_payment(self, amount: int, description: str) -> Dict:
        """
        Create a payment request with Zarinpal.
        
        Args:
            amount: Amount in Tomans
            description: Payment description
            
        Returns:
            Dict containing payment URL and authority token
        """
        try:
            response = requests.post(
                f"{self.base_url}/PaymentRequest.json",
                json={
                    "MerchantID": self.api_key,
                    "Amount": amount,
                    "Description": description,
                    "CallbackURL": "https://your-callback-url.com/verify",  # Replace with actual callback URL
                    "Email": "",  # Optional
                    "Mobile": ""  # Optional
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("Status") == 100:
                return {
                    "success": True,
                    "payment_url": f"https://www.zarinpal.com/pg/StartPay/{data['Authority']}",
                    "token": data["Authority"]
                }
            
            logger.error(f"Failed to create Zarinpal payment: {data.get('Status')}")
            return {
                "success": False,
                "error": f"Payment creation failed with status {data.get('Status')}"
            }
            
        except Exception as e:
            logger.error(f"Error creating Zarinpal payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_payment(self, token: str) -> bool:
        """
        Verify a Zarinpal payment.
        
        Args:
            token: Payment authority token
            
        Returns:
            True if payment is verified, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/PaymentVerification.json",
                json={
                    "MerchantID": self.api_key,
                    "Authority": token,
                    "Amount": 0  # Amount should be stored in session/database
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("Status") == 100
            
        except Exception as e:
            logger.error(f"Error verifying Zarinpal payment: {e}")
            return False

class PaymentManager:
    """Manager class for handling payments."""
    GATEWAYS = {
        "zarinpal": ZarinpalGateway
    }
    
    @classmethod
    def get_gateway(cls, gateway_type: str) -> Optional[PaymentGateway]:
        """Get payment gateway instance by type."""
        try:
            # Get gateway settings from database
            gateway_settings = Setting.get_by_type(SettingType.PAYMENT_GATEWAY)
            if not gateway_settings:
                logger.error("No payment gateway settings found")
                return None
            
            # Parse settings
            settings = gateway_settings.value
            if not isinstance(settings, dict):
                logger.error("Invalid payment gateway settings format")
                return None
            
            # Get gateway class
            gateway_class = cls.GATEWAYS.get(gateway_type.lower())
            if not gateway_class:
                logger.error(f"Unsupported payment gateway: {gateway_type}")
                return None
            
            # Create gateway instance
            return gateway_class(
                api_key=settings.get("api_key"),
                sandbox=settings.get("sandbox", False)
            )
            
        except Exception as e:
            logger.error(f"Error creating payment gateway: {e}")
            return None
    
    @classmethod
    def create_transaction(
        cls,
        user_id: int,
        amount: int,
        description: str,
        gateway_type: str = "zarinpal"
    ) -> Optional[Dict]:
        """
        Create a new payment transaction.
        
        Args:
            user_id: User's Telegram ID
            amount: Amount in Tomans
            description: Payment description
            gateway_type: Payment gateway type (default: zarinpal)
            
        Returns:
            Dict containing payment URL and transaction details if successful
        """
        try:
            # Get user
            user = User.get_by_telegram_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return None
            
            # Get payment gateway
            gateway = cls.get_gateway(gateway_type)
            if not gateway:
                return None
            
            # Create payment request
            payment = gateway.create_payment(amount, description)
            if not payment.get("success"):
                return None
            
            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                amount=amount,
                description=description,
                payment_method=gateway_type,
                payment_token=payment["token"],
                status="pending"
            )
            transaction.save()
            
            return {
                "success": True,
                "payment_url": payment["payment_url"],
                "transaction_id": transaction.id
            }
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    @classmethod
    def verify_transaction(cls, transaction_id: int) -> bool:
        """
        Verify a payment transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if transaction is verified, False otherwise
        """
        try:
            # Get transaction
            transaction = Transaction.get_by_id(transaction_id)
            if not transaction:
                logger.error(f"Transaction not found: {transaction_id}")
                return False
            
            # Get payment gateway
            gateway = cls.get_gateway(transaction.payment_method)
            if not gateway:
                return False
            
            # Verify payment
            if gateway.verify_payment(transaction.payment_token):
                # Update transaction status
                transaction.status = "completed"
                transaction.completed_at = datetime.now()
                transaction.save()
                return True
            
            # Payment failed
            transaction.status = "failed"
            transaction.save()
            return False
            
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return False

class NextPayAPI:
    """
    TODO: Implement NextPay payment gateway integration
    """
    pass

class NowPaymentsAPI:
    """
    TODO: Implement NowPayments crypto payment gateway integration
    """
    pass 

def create_payment_link(method: str, amount: int, plan_id: int, telegram_id: int) -> str:
    """
    Wrapper to create a payment link using the PaymentManager.

    Args:
        method: Gateway type (e.g., "zarinpal")
        amount: Amount in Tomans
        plan_id: ID of the selected plan
        telegram_id: Telegram user ID

    Returns:
        Payment URL string if successful, otherwise a fallback or error message
    """
    description = f"خرید پلن {plan_id} توسط کاربر {telegram_id}"

    result = PaymentManager.create_transaction(
        user_id=telegram_id,
        amount=amount,
        description=description,
        gateway_type=method
    )

    if result and result.get("success"):
        return result["payment_url"]

    # Optional: fallback URL or error page
    return "https://your-website.com/payment-error"
