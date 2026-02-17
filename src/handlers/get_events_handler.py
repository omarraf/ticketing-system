"""
Lambda handler for GET /events
Returns list of all available events.
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
    Lambda handler for GET /events endpoint.

    Args:
        event: Lambda event from API Gateway
        context: Lambda context

    Returns:
        API Gateway response with list of events
    """
    try:
        logger.info("GET /events - Fetching all events")

        # Get all events from DynamoDB
        events = dynamodb.get_all_events()

        logger.info(f"Found {len(events)} events")

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # CORS
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'events': events,
                'count': len(events)
            }, default=decimal_to_float)
        }

    except Exception as e:
        logger.error(f"Error fetching events: {str(e)}")

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
