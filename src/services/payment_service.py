"""
Payment processing service.
Simulates payment processing for demo purposes.
In production, this would integrate with Stripe, Square, or similar.
"""
import uuid
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_payment(
    booking_id: str,
    user_id: str,
    amount: float,
    email: str = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Process payment for a booking.

    This is a MOCK implementation for demo purposes.
    In production, integrate with a real payment processor (Stripe, Square, etc.)

    Args:
        booking_id: The booking ID
        user_id: User ID
        amount: Payment amount in USD
        email: User email (optional)

    Returns:
        Tuple of (success: bool, message: str, payment_data: dict)
    """
    try:
        logger.info(f"Processing payment for booking {booking_id}, amount: ${amount}")

        # Generate a mock payment intent ID
        payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"

        # Simulate payment processing with 95% success rate
        # In production, this would call Stripe/Square API
        success = random.random() > 0.05  # 95% success rate

        if success:
            payment_data = {
                'payment_intent_id': payment_intent_id,
                'status': 'succeeded',
                'amount': amount,
                'currency': 'usd',
                'user_id': user_id,
                'booking_id': booking_id,
                'processed_at': datetime.utcnow().isoformat(),
                'payment_method': 'card',
                'last4': '4242'  # Mock card number
            }

            logger.info(f"Payment successful for booking {booking_id}: {payment_intent_id}")
            return True, "Payment processed successfully", payment_data

        else:
            # Simulate payment failure
            error_reasons = [
                "Insufficient funds",
                "Card declined",
                "Payment timeout",
                "Invalid card details"
            ]
            error_message = random.choice(error_reasons)

            payment_data = {
                'payment_intent_id': payment_intent_id,
                'status': 'failed',
                'amount': amount,
                'user_id': user_id,
                'booking_id': booking_id,
                'error_message': error_message,
                'failed_at': datetime.utcnow().isoformat()
            }

            logger.warning(f"Payment failed for booking {booking_id}: {error_message}")
            return False, error_message, payment_data

    except Exception as e:
        logger.error(f"Error processing payment for booking {booking_id}: {str(e)}")
        return False, f"Payment processing error: {str(e)}", {}


def refund_payment(payment_intent_id: str, amount: float) -> Tuple[bool, str]:
    """
    Refund a payment.

    Mock implementation for demo purposes.

    Args:
        payment_intent_id: Payment processor ID
        amount: Amount to refund

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info(f"Processing refund for payment {payment_intent_id}, amount: ${amount}")

        # Generate mock refund ID
        refund_id = f"re_{uuid.uuid4().hex[:24]}"

        # Simulate successful refund
        logger.info(f"Refund successful: {refund_id}")
        return True, f"Refund processed successfully: {refund_id}"

    except Exception as e:
        logger.error(f"Error processing refund for {payment_intent_id}: {str(e)}")
        return False, f"Refund failed: {str(e)}"


def validate_payment_amount(amount: float) -> Tuple[bool, str]:
    """
    Validate payment amount.

    Args:
        amount: Payment amount

    Returns:
        Tuple of (valid: bool, message: str)
    """
    if amount <= 0:
        return False, "Payment amount must be greater than 0"

    if amount > 10000:
        return False, "Payment amount exceeds maximum allowed ($10,000)"

    return True, "Valid amount"


# Production Stripe Integration Example (commented out for demo)
"""
import stripe
import os

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def process_payment_stripe(booking_id: str, amount: float, email: str) -> Tuple[bool, str, Dict]:
    try:
        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency='usd',
            metadata={
                'booking_id': booking_id,
                'email': email
            }
        )

        return True, "Payment intent created", {
            'payment_intent_id': payment_intent.id,
            'client_secret': payment_intent.client_secret,
            'status': payment_intent.status
        }
    except stripe.error.StripeError as e:
        return False, str(e), {}
"""
