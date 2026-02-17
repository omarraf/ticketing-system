"""
Lambda handler for POST /reserve
Handles seat reservation requests with distributed locking.
"""
import json
import logging
from typing import Dict, Any
from decimal import Decimal

from src.services import seat_service
from src.models.schemas import ReservationRequest
from pydantic import ValidationError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for POST /reserve endpoint.

    Expected request body:
    {
        "event_id": "event-001",
        "seat_id": "event-001-A5",
        "user_id": "user-123",
        "email": "user@example.com" (optional)
    }

    Args:
        event: Lambda event from API Gateway
        context: Lambda context

    Returns:
        API Gateway response with reservation result
    """
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)

        logger.info(f"POST /reserve - Request: {json.dumps(body)}")

        # Validate request using Pydantic model
        try:
            reservation_req = ReservationRequest(**body)
        except ValidationError as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Validation error',
                    'message': str(e)
                })
            }

        # Call seat service to reserve the seat
        success, message, booking_data = seat_service.reserve_seat(
            event_id=reservation_req.event_id,
            seat_id=reservation_req.seat_id,
            user_id=reservation_req.user_id,
            email=reservation_req.email
        )

        if success:
            logger.info(f"Reservation successful: {booking_data.get('booking_id')}")

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({
                    'success': True,
                    'message': message,
                    'booking_id': booking_data.get('booking_id'),
                    'seat_id': booking_data.get('seat_id'),
                    'event_id': booking_data.get('event_id'),
                    'price': booking_data.get('price'),
                    'payment_status': booking_data.get('payment_status')
                }, default=decimal_to_float)
            }
        else:
            logger.warning(f"Reservation failed: {message}")

            # Return 409 Conflict if seat is not available
            status_code = 409 if 'not available' in message.lower() or 'reserved' in message.lower() else 400

            return {
                'statusCode': status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'message': message
                })
            }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")

        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Bad request',
                'message': 'Invalid JSON in request body'
            })
        }

    except Exception as e:
        logger.error(f"Error processing reservation: {str(e)}")

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
