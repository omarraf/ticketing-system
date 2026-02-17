"""
DynamoDB utility functions for the ticketing system.
Handles database operations for events, seats, and bookings.
"""
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Table names from environment variables
EVENTS_TABLE = os.getenv('EVENTS_TABLE_NAME', 'ticketing-system-events-dev')
SEATS_TABLE = os.getenv('SEATS_TABLE_NAME', 'ticketing-system-seats-dev')
BOOKINGS_TABLE = os.getenv('BOOKINGS_TABLE_NAME', 'ticketing-system-bookings-dev')

# Get table instances
events_table = dynamodb.Table(EVENTS_TABLE)
seats_table = dynamodb.Table(SEATS_TABLE)
bookings_table = dynamodb.Table(BOOKINGS_TABLE)


def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Get an event by ID.

    Args:
        event_id: The event ID

    Returns:
        Event data or None if not found
    """
    try:
        response = events_table.get_item(Key={'event_id': event_id})
        return response.get('Item')
    except ClientError as e:
        logger.error(f"Error getting event {event_id}: {e.response['Error']['Message']}")
        return None


def get_all_events() -> List[Dict[str, Any]]:
    """
    Get all events.

    Returns:
        List of all events
    """
    try:
        response = events_table.scan()
        items = response.get('Items', [])

        # Handle pagination if there are many events
        while 'LastEvaluatedKey' in response:
            response = events_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        return items
    except ClientError as e:
        logger.error(f"Error scanning events: {e.response['Error']['Message']}")
        return []


def get_seat(seat_id: str, event_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a seat by ID.

    Args:
        seat_id: The seat ID
        event_id: The event ID (required for composite key)

    Returns:
        Seat data or None if not found
    """
    try:
        response = seats_table.get_item(
            Key={
                'seat_id': seat_id,
                'event_id': event_id
            }
        )
        return response.get('Item')
    except ClientError as e:
        logger.error(f"Error getting seat {seat_id}: {e.response['Error']['Message']}")
        return None


def get_seats_by_event(event_id: str) -> List[Dict[str, Any]]:
    """
    Get all seats for an event.

    Args:
        event_id: The event ID

    Returns:
        List of seats for the event
    """
    try:
        response = seats_table.query(
            IndexName='EventIndex',  # Assumes GSI on event_id
            KeyConditionExpression=Key('event_id').eq(event_id)
        )
        return response.get('Items', [])
    except ClientError as e:
        # If GSI doesn't exist, fall back to scan with filter
        logger.warning(f"GSI query failed, falling back to scan: {e.response['Error']['Message']}")
        try:
            response = seats_table.scan(
                FilterExpression=Attr('event_id').eq(event_id)
            )
            return response.get('Items', [])
        except ClientError as scan_error:
            logger.error(f"Error getting seats for event {event_id}: {scan_error.response['Error']['Message']}")
            return []


def update_seat_status(
    seat_id: str,
    event_id: str,
    status: str,
    user_id: Optional[str] = None
) -> bool:
    """
    Update seat status with conditional write to prevent double-booking.

    Args:
        seat_id: The seat ID
        event_id: The event ID
        status: New status (available, reserved, sold)
        user_id: User ID if reserving/sold

    Returns:
        True if update succeeded, False if seat already taken
    """
    try:
        update_expr = "SET #status = :status"
        expr_attr_names = {"#status": "status"}
        expr_attr_values = {":status": status}

        if user_id:
            update_expr += ", reserved_by = :user_id, reserved_at = :reserved_at"
            expr_attr_values[":user_id"] = user_id
            expr_attr_values[":reserved_at"] = datetime.utcnow().isoformat()

        # Conditional write: only update if seat is available
        seats_table.update_item(
            Key={
                'seat_id': seat_id,
                'event_id': event_id
            },
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ConditionExpression=Attr('status').eq('available')
        )

        logger.info(f"Successfully updated seat {seat_id} to status {status}")
        return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"Seat {seat_id} is no longer available")
            return False
        else:
            logger.error(f"Error updating seat {seat_id}: {e.response['Error']['Message']}")
            raise


def create_booking(booking_data: Dict[str, Any]) -> Optional[str]:
    """
    Create a new booking.

    Args:
        booking_data: Booking information

    Returns:
        booking_id if successful, None otherwise
    """
    try:
        bookings_table.put_item(Item=booking_data)
        logger.info(f"Successfully created booking {booking_data['booking_id']}")
        return booking_data['booking_id']
    except ClientError as e:
        logger.error(f"Error creating booking: {e.response['Error']['Message']}")
        return None


def update_booking_status(booking_id: str, payment_status: str) -> bool:
    """
    Update booking payment status.

    Args:
        booking_id: The booking ID
        payment_status: New payment status

    Returns:
        True if successful, False otherwise
    """
    try:
        bookings_table.update_item(
            Key={'booking_id': booking_id},
            UpdateExpression="SET payment_status = :status",
            ExpressionAttributeValues={":status": payment_status}
        )
        logger.info(f"Updated booking {booking_id} status to {payment_status}")
        return True
    except ClientError as e:
        logger.error(f"Error updating booking {booking_id}: {e.response['Error']['Message']}")
        return False


def decrement_available_seats(event_id: str) -> bool:
    """
    Atomically decrement available seats count for an event.

    Args:
        event_id: The event ID

    Returns:
        True if successful, False otherwise
    """
    try:
        events_table.update_item(
            Key={'event_id': event_id},
            UpdateExpression="SET available_seats = available_seats - :dec",
            ExpressionAttributeValues={":dec": 1},
            ConditionExpression=Attr('available_seats').gt(0)
        )
        logger.info(f"Decremented available seats for event {event_id}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"No available seats for event {event_id}")
            return False
        else:
            logger.error(f"Error decrementing seats for event {event_id}: {e.response['Error']['Message']}")
            return False


def get_booking(booking_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a booking by ID.

    Args:
        booking_id: The booking ID

    Returns:
        Booking data or None if not found
    """
    try:
        response = bookings_table.get_item(Key={'booking_id': booking_id})
        return response.get('Item')
    except ClientError as e:
        logger.error(f"Error getting booking {booking_id}: {e.response['Error']['Message']}")
        return None
