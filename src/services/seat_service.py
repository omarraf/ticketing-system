"""
Seat reservation business logic.
Orchestrates the entire reservation flow:
1. Acquire distributed lock (Redis)
2. Check seat availability (DynamoDB)
3. Reserve seat (DynamoDB conditional write)
4. Create booking (DynamoDB)
5. Publish event (EventBridge)
6. Release lock
"""
import os
import uuid
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

# Import our services
from src.utils import dynamodb
from src.services import eventbridge_service

# Check if Redis is enabled
REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'

if REDIS_ENABLED:
    from src.services.lock_service import get_lock_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def reserve_seat(
    event_id: str,
    seat_id: str,
    user_id: str,
    email: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Reserve a seat for a user.

    This is the main orchestration function that coordinates:
    - Distributed locking (if Redis enabled)
    - Seat availability check
    - Seat reservation (DynamoDB conditional write)
    - Booking creation
    - Event publishing

    Args:
        event_id: Event ID
        seat_id: Seat ID to reserve
        user_id: User making the reservation
        email: User email (optional)

    Returns:
        Tuple of (success: bool, message: str, booking_data: Optional[Dict])
    """
    lock = None
    booking_id = f"booking-{uuid.uuid4().hex[:12]}"

    try:
        logger.info(f"Starting reservation: seat={seat_id}, user={user_id}, event={event_id}")

        # Step 1: Acquire distributed lock (if Redis enabled)
        if REDIS_ENABLED:
            try:
                lock_service = get_lock_service()
                lock = lock_service.acquire_lock(seat_id, timeout=10, blocking_timeout=5)

                if not lock:
                    logger.warning(f"Failed to acquire lock for seat {seat_id}")
                    return False, "Seat is currently being reserved by another user. Please try again.", None
            except Exception as e:
                logger.error(f"Redis lock error (continuing without lock): {str(e)}")
                # Continue without lock - DynamoDB conditional write will still protect us

        # Step 2: Get event details (for pricing)
        event = dynamodb.get_event(event_id)
        if not event:
            return False, f"Event {event_id} not found", None

        price = float(event.get('price', 0))

        # Step 3: Check seat availability
        seat = dynamodb.get_seat(seat_id, event_id)
        if not seat:
            return False, f"Seat {seat_id} not found", None

        if seat.get('status') != 'available':
            return False, f"Seat {seat_id} is not available", None

        # Step 4: Reserve seat with conditional write (CRITICAL - prevents double booking)
        # This will FAIL if another process reserved the seat between our check and update
        seat_updated = dynamodb.update_seat_status(
            seat_id=seat_id,
            event_id=event_id,
            status='reserved',
            user_id=user_id
        )

        if not seat_updated:
            logger.warning(f"Seat {seat_id} was reserved by another user")
            return False, "Seat was just reserved by another user. Please select another seat.", None

        # Step 5: Decrement available seats count for the event
        seats_updated = dynamodb.decrement_available_seats(event_id)
        if not seats_updated:
            logger.error(f"Failed to decrement available seats for event {event_id}")
            # Note: Seat is already reserved, so we continue

        # Step 6: Create booking record
        booking_data = {
            'booking_id': booking_id,
            'user_id': user_id,
            'event_id': event_id,
            'seat_id': seat_id,
            'price': price,
            'payment_status': 'pending',
            'confirmed_at': datetime.utcnow().isoformat(),
            'email': email
        }

        booking_created = dynamodb.create_booking(booking_data)
        if not booking_created:
            logger.error(f"Failed to create booking {booking_id}")
            return False, "Failed to create booking record", None

        # Step 7: Publish SeatReserved event to EventBridge
        # This triggers payment processing via SQS
        event_published = eventbridge_service.publish_seat_reserved_event(
            event_id=event_id,
            seat_id=seat_id,
            user_id=user_id,
            booking_id=booking_id,
            price=price,
            email=email
        )

        if not event_published:
            logger.warning(f"Failed to publish SeatReserved event for booking {booking_id}")
            # Booking is still created, so we continue

        logger.info(f"Successfully reserved seat {seat_id} for user {user_id}, booking {booking_id}")

        return True, "Seat reserved successfully. Payment processing initiated.", booking_data

    except Exception as e:
        logger.error(f"Error reserving seat {seat_id}: {str(e)}")
        return False, f"Reservation failed: {str(e)}", None

    finally:
        # Step 8: Release lock
        if REDIS_ENABLED and lock:
            try:
                lock_service = get_lock_service()
                lock_service.release_lock(lock)
                logger.info(f"Released lock for seat {seat_id}")
            except Exception as e:
                logger.error(f"Error releasing lock for seat {seat_id}: {str(e)}")


def check_seat_availability(event_id: str, seat_id: str) -> Tuple[bool, str]:
    """
    Check if a seat is available for reservation.

    Args:
        event_id: Event ID
        seat_id: Seat ID

    Returns:
        Tuple of (available: bool, message: str)
    """
    try:
        seat = dynamodb.get_seat(seat_id, event_id)

        if not seat:
            return False, "Seat not found"

        if seat.get('status') == 'available':
            return True, "Seat is available"
        else:
            return False, f"Seat is {seat.get('status')}"

    except Exception as e:
        logger.error(f"Error checking seat availability: {str(e)}")
        return False, f"Error checking availability: {str(e)}"


def release_seat(event_id: str, seat_id: str) -> bool:
    """
    Release a reserved seat (e.g., payment timeout or failure).

    Args:
        event_id: Event ID
        seat_id: Seat ID

    Returns:
        True if released successfully
    """
    try:
        logger.info(f"Releasing seat {seat_id}")

        # Update seat status back to available
        # Note: We don't use conditional write here since we want to force release
        seat = dynamodb.get_seat(seat_id, event_id)
        if not seat:
            return False

        # Only release if currently reserved (don't release sold seats)
        if seat.get('status') != 'reserved':
            logger.warning(f"Seat {seat_id} is not reserved, status: {seat.get('status')}")
            return False

        dynamodb.update_seat_status(
            seat_id=seat_id,
            event_id=event_id,
            status='available',
            user_id=None
        )

        logger.info(f"Successfully released seat {seat_id}")
        return True

    except Exception as e:
        logger.error(f"Error releasing seat {seat_id}: {str(e)}")
        return False
