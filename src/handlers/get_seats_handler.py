"""
Lambda handler for GET /events/{event_id}/seats
Returns seat availability for a specific event.
"""
import json
import logging
from typing import Dict, Any
from decimal import Decimal

from src.utils import dynamodb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for GET /events/{event_id}/seats endpoint.

    Args:
        event: Lambda event from API Gateway
        context: Lambda context

    Returns:
        API Gateway response with seat availability
    """
    try:
        # Extract event_id from path parameters
        path_params = event.get('pathParameters', {})
        event_id = path_params.get('event_id')

        if not event_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Bad request',
                    'message': 'event_id is required'
                })
            }

        logger.info(f"GET /events/{event_id}/seats - Fetching seat map")

        # Get event details
        event_data = dynamodb.get_event(event_id)
        if not event_data:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Not found',
                    'message': f'Event {event_id} not found'
                })
            }

        # Get all seats for the event
        seats = dynamodb.get_seats_by_event(event_id)

        # Count available seats
        available_count = sum(1 for seat in seats if seat.get('status') == 'available')

        logger.info(f"Found {len(seats)} seats, {available_count} available")

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'event_id': event_id,
                'event_name': event_data.get('name'),
                'seats': seats,
                'total_seats': len(seats),
                'available_seats': available_count
            }, default=decimal_to_float)
        }

    except Exception as e:
        logger.error(f"Error fetching seats: {str(e)}")

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
