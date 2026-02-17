"""
Lambda handler for email notifications.
Triggered by EventBridge events (SeatReserved, PaymentConfirmed, PaymentFailed).
Sends confirmation emails to users.
"""
import json
import logging
from typing import Dict, Any

from src.utils import dynamodb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def send_email_stub(to_email: str, subject: str, body: str) -> bool:
    """
    Mock email sending function.

    In production, integrate with:
    - Amazon SES (Simple Email Service)
    - SendGrid
    - Mailgun
    - etc.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body

    Returns:
        True if sent successfully (always True for mock)
    """
    logger.info(f"[MOCK EMAIL] To: {to_email}")
    logger.info(f"[MOCK EMAIL] Subject: {subject}")
    logger.info(f"[MOCK EMAIL] Body: {body}")

    # In production, use SES:
    # import boto3
    # ses = boto3.client('ses')
    # ses.send_email(...)

    return True


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for EventBridge email notifications.

    Processes events:
    - SeatReserved: Send reservation confirmation
    - PaymentConfirmed: Send payment receipt
    - PaymentFailed: Send payment failure notice

    Expected EventBridge event format:
    {
        "detail-type": "SeatReserved" | "PaymentConfirmed" | "PaymentFailed",
        "detail": {
            "booking_id": "booking-abc123",
            "email": "user@example.com",
            ...
        }
    }

    Args:
        event: EventBridge event
        context: Lambda context

    Returns:
        Success/failure response
    """
    try:
        detail_type = event.get('detail-type')
        detail = event.get('detail', {})

        logger.info(f"Processing email for event type: {detail_type}")

        email = detail.get('email')
        booking_id = detail.get('booking_id')

        if not email:
            logger.warning(f"No email address provided for booking {booking_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No email address provided'})
            }

        # Get booking details for email content
        booking = None
        if booking_id:
            booking = dynamodb.get_booking(booking_id)

        # Handle different event types
        if detail_type == 'SeatReserved':
            subject = "Seat Reservation Confirmed"
            body = f"""
            Your seat reservation has been confirmed!

            Booking ID: {booking_id}
            Event: {detail.get('event_id')}
            Seat: {detail.get('seat_id')}
            Price: ${detail.get('price')}

            Payment processing is underway. You'll receive another email when payment is confirmed.

            Thank you for your purchase!
            """

            send_email_stub(email, subject, body)
            logger.info(f"Sent reservation confirmation to {email}")

        elif detail_type == 'PaymentConfirmed':
            subject = "Payment Confirmed - Ticket Ready!"

            event_name = "Your Event"
            seat_id = "N/A"
            price = detail.get('amount', 0)

            if booking:
                # Get event details
                event_data = dynamodb.get_event(booking.get('event_id', ''))
                if event_data:
                    event_name = event_data.get('name', 'Your Event')
                seat_id = booking.get('seat_id', 'N/A')
                price = booking.get('price', 0)

            body = f"""
            Congratulations! Your payment has been confirmed.

            Booking ID: {booking_id}
            Event: {event_name}
            Seat: {seat_id}
            Amount Paid: ${price}

            Your ticket is now confirmed and ready!

            See you at the event!
            """

            send_email_stub(email, subject, body)
            logger.info(f"Sent payment confirmation to {email}")

        elif detail_type == 'PaymentFailed':
            subject = "Payment Failed - Reservation Cancelled"
            error_message = detail.get('error_message', 'Payment processing failed')

            body = f"""
            Unfortunately, your payment could not be processed.

            Booking ID: {booking_id}
            Reason: {error_message}

            Your seat reservation has been released.
            Please try again or contact support if you need assistance.

            Thank you for your understanding.
            """

            send_email_stub(email, subject, body)
            logger.info(f"Sent payment failure notice to {email}")

        else:
            logger.warning(f"Unknown event type: {detail_type}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Email processed successfully',
                'detail_type': detail_type
            })
        }

    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Email processing error',
                'message': str(e)
            })
        }
