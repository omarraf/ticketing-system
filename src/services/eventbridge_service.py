"""
EventBridge service for publishing events.
Enables event-driven architecture for seat reservations and payments.
"""
import os
import boto3
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize EventBridge client
eventbridge = boto3.client('events')

# Event bus name from environment
EVENT_BUS_NAME = os.getenv('EVENT_BUS_NAME', 'ticketing-system-event-bus-dev')
SOURCE = 'ticketing.system'


def publish_event(
    detail_type: str,
    detail: Dict[str, Any],
    source: str = SOURCE
) -> bool:
    """
    Publish an event to EventBridge.

    Args:
        detail_type: Type of the event (e.g., "SeatReserved", "PaymentConfirmed")
        detail: Event payload
        source: Event source identifier

    Returns:
        True if published successfully, False otherwise
    """
    try:
        response = eventbridge.put_events(
            Entries=[
                {
                    'Time': datetime.utcnow(),
                    'Source': source,
                    'DetailType': detail_type,
                    'Detail': json.dumps(detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )

        # Check if event was published successfully
        if response['FailedEntryCount'] == 0:
            logger.info(f"Successfully published event: {detail_type}")
            return True
        else:
            logger.error(f"Failed to publish event: {response['Entries']}")
            return False

    except Exception as e:
        logger.error(f"Error publishing event {detail_type}: {str(e)}")
        return False


def publish_seat_reserved_event(
    event_id: str,
    seat_id: str,
    user_id: str,
    booking_id: str,
    price: float,
    email: Optional[str] = None
) -> bool:
    """
    Publish a SeatReserved event.

    This triggers:
    - Payment processing via SQS
    - Email confirmation
    - Analytics updates

    Args:
        event_id: Event ID
        seat_id: Seat ID
        user_id: User ID
        booking_id: Booking ID
        price: Ticket price
        email: User email (optional)

    Returns:
        True if published successfully
    """
    detail = {
        'event_id': event_id,
        'seat_id': seat_id,
        'user_id': user_id,
        'booking_id': booking_id,
        'price': price,
        'timestamp': datetime.utcnow().isoformat()
    }

    if email:
        detail['email'] = email

    return publish_event(
        detail_type='SeatReserved',
        detail=detail
    )


def publish_payment_confirmed_event(
    booking_id: str,
    payment_intent_id: str,
    amount: float
) -> bool:
    """
    Publish a PaymentConfirmed event.

    This triggers:
    - Email confirmation
    - Booking finalization
    - Analytics updates

    Args:
        booking_id: Booking ID
        payment_intent_id: Payment processor ID
        amount: Payment amount

    Returns:
        True if published successfully
    """
    detail = {
        'booking_id': booking_id,
        'payment_intent_id': payment_intent_id,
        'amount': amount,
        'timestamp': datetime.utcnow().isoformat()
    }

    return publish_event(
        detail_type='PaymentConfirmed',
        detail=detail
    )


def publish_payment_failed_event(
    booking_id: str,
    error_message: str
) -> bool:
    """
    Publish a PaymentFailed event.

    This triggers:
    - Seat release
    - User notification
    - Error logging

    Args:
        booking_id: Booking ID
        error_message: Failure reason

    Returns:
        True if published successfully
    """
    detail = {
        'booking_id': booking_id,
        'error_message': error_message,
        'timestamp': datetime.utcnow().isoformat()
    }

    return publish_event(
        detail_type='PaymentFailed',
        detail=detail
    )
