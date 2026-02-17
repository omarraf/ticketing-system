"""
Lambda handler for SQS payment processing.
Triggered by SeatReserved events via EventBridge -> SQS.
Processes payment and updates booking status.
"""
import json
import logging
from typing import Dict, Any

from src.services import payment_service, eventbridge_service
from src.utils import dynamodb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for SQS payment processing.

    Processes messages from SQS queue containing SeatReserved events.

    Expected SQS message format (from EventBridge):
    {
        "Records": [
            {
                "body": "{
                    "detail": {
                        "booking_id": "booking-abc123",
                        "user_id": "user-456",
                        "price": 299.99,
                        "email": "user@example.com"
                    }
                }"
            }
        ]
    }

    Args:
        event: SQS event with payment processing records
        context: Lambda context

    Returns:
        Success/failure response for SQS batch processing
    """
    successful_messages = []
    failed_messages = []

    try:
        # Process each SQS record
        records = event.get('Records', [])
        logger.info(f"Processing {len(records)} payment records")

        for record in records:
            try:
                # Parse the SQS message body (which contains EventBridge event)
                message_body = json.loads(record['body'])

                # Extract event detail
                # EventBridge events have structure: { "detail": {...} }
                if 'detail' in message_body:
                    detail = message_body['detail']
                else:
                    # If direct SQS message (not from EventBridge)
                    detail = message_body

                booking_id = detail.get('booking_id')
                user_id = detail.get('user_id')
                price = detail.get('price')
                email = detail.get('email')

                logger.info(f"Processing payment for booking {booking_id}, amount: ${price}")

                # Process payment (mock implementation)
                success, message, payment_data = payment_service.process_payment(
                    booking_id=booking_id,
                    user_id=user_id,
                    amount=price,
                    email=email
                )

                if success:
                    # Update booking status to confirmed
                    dynamodb.update_booking_status(booking_id, 'confirmed')

                    # Update seat status to sold
                    booking = dynamodb.get_booking(booking_id)
                    if booking:
                        dynamodb.update_seat_status(
                            seat_id=booking['seat_id'],
                            event_id=booking['event_id'],
                            status='sold',
                            user_id=user_id
                        )

                    # Publish PaymentConfirmed event
                    eventbridge_service.publish_payment_confirmed_event(
                        booking_id=booking_id,
                        payment_intent_id=payment_data.get('payment_intent_id'),
                        amount=price
                    )

                    logger.info(f"Payment successful for booking {booking_id}")
                    successful_messages.append(record['messageId'])

                else:
                    # Payment failed - update booking status
                    dynamodb.update_booking_status(booking_id, 'failed')

                    # Publish PaymentFailed event (could trigger seat release)
                    eventbridge_service.publish_payment_failed_event(
                        booking_id=booking_id,
                        error_message=message
                    )

                    logger.warning(f"Payment failed for booking {booking_id}: {message}")
                    # Note: We still mark as successful to remove from queue
                    # Failed payments are tracked in DynamoDB
                    successful_messages.append(record['messageId'])

            except Exception as e:
                logger.error(f"Error processing payment record: {str(e)}")
                failed_messages.append({
                    'itemIdentifier': record['messageId'],
                    'error': str(e)
                })

        # Return batch processing results
        logger.info(f"Processed {len(successful_messages)} successful, {len(failed_messages)} failed")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'successful': len(successful_messages),
                'failed': len(failed_messages)
            })
        }

    except Exception as e:
        logger.error(f"Fatal error processing payment batch: {str(e)}")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Payment processing error',
                'message': str(e)
            })
        }
