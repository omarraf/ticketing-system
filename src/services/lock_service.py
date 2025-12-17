"""
Redis-based distributed lock service for preventing race conditions.
Uses Redis locks to ensure only one process can reserve a seat at a time.
"""
import os
import redis
from redis.lock import Lock
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LockService:
    """
    Distributed locking service using Redis.
    Prevents concurrent access to shared resources (seats).
    """

    def __init__(self):
        redis_endpoint = os.getenv('REDIS_ENDPOINT')
        redis_port = int(os.getenv('REDIS_PORT', 6379))

        if not redis_endpoint:
            raise ValueError("REDIS_ENDPOINT environment variable not set")

        self.redis_client = redis.Redis(
            host=redis_endpoint,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

        logger.info(f"Redis lock service initialized: {redis_endpoint}:{redis_port}")

    def acquire_lock(self, resource_id: str, timeout: int = 10, blocking_timeout: int = 5) -> Optional[Lock]:
        """
        Acquire a distributed lock for a resource (e.g., seat).

        Args:
            resource_id: Unique identifier for the resource (e.g., seat_id)
            timeout: Lock expiration time in seconds (prevents deadlocks)
            blocking_timeout: Max time to wait for lock acquisition (0 = non-blocking)

        Returns:
            Lock object if acquired, None if lock could not be acquired
        """
        lock_key = f"lock:seat:{resource_id}"

        try:
            lock = self.redis_client.lock(
                lock_key,
                timeout=timeout,
                blocking_timeout=blocking_timeout
            )

            # Try to acquire the lock
            acquired = lock.acquire(blocking=True)

            if acquired:
                logger.info(f"Lock acquired for resource: {resource_id}")
                return lock
            else:
                logger.warning(f"Failed to acquire lock for resource: {resource_id}")
                return None

        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error acquiring lock for {resource_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error acquiring lock for {resource_id}: {str(e)}")
            return None

    def release_lock(self, lock: Lock) -> bool:
        """
        Release a distributed lock.

        Args:
            lock: Lock object to release

        Returns:
            True if released successfully, False otherwise
        """
        if not lock:
            return False

        try:
            lock.release()
            logger.info("Lock released successfully")
            return True
        except redis.exceptions.LockError as e:
            logger.warning(f"Lock already expired or not owned: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error releasing lock: {str(e)}")
            return False

    def is_locked(self, resource_id: str) -> bool:
        """
        Check if a resource is currently locked.

        Args:
            resource_id: Unique identifier for the resource

        Returns:
            True if locked, False otherwise
        """
        lock_key = f"lock:seat:{resource_id}"
        try:
            return self.redis_client.exists(lock_key) > 0
        except Exception as e:
            logger.error(f"Error checking lock status: {str(e)}")
            return False


# Singleton instance for Lambda reuse across invocations
_lock_service_instance: Optional[LockService] = None


def get_lock_service() -> LockService:
    """
    Get or create singleton LockService instance.
    Lambda containers reuse this across invocations for efficiency.
    """
    global _lock_service_instance

    if _lock_service_instance is None:
        _lock_service_instance = LockService()

    return _lock_service_instance
