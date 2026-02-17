"""
Data models and schemas for the ticketing system.
Uses Pydantic for validation and serialization.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal


class Event(BaseModel):
    """Event model representing a ticketing event."""
    event_id: str
    name: str
    venue: str
    date: str  # ISO format datetime string
    total_seats: int
    available_seats: int
    price: float
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "event-001",
                "name": "NBA Finals",
                "venue": "Madison Square Garden",
                "date": "2025-03-15T19:00:00",
                "total_seats": 50,
                "available_seats": 45,
                "price": 299.99,
                "description": "The most anticipated basketball game of the year"
            }
        }


class Seat(BaseModel):
    """Seat model representing an individual seat."""
    seat_id: str
    event_id: str
    row: str
    number: int
    status: Literal["available", "reserved", "sold"]
    section: str = "General Admission"
    reserved_by: Optional[str] = None  # user_id
    reserved_at: Optional[str] = None  # ISO format datetime
    created_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "seat_id": "event-001-A5",
                "event_id": "event-001",
                "row": "A",
                "number": 5,
                "status": "available",
                "section": "General Admission"
            }
        }


class Booking(BaseModel):
    """Booking model representing a confirmed reservation."""
    booking_id: str
    user_id: str
    event_id: str
    seat_id: str
    confirmed_at: str  # ISO format datetime
    price: float
    payment_status: Literal["pending", "confirmed", "failed", "refunded"]
    email: Optional[str] = None
    payment_intent_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "booking-abc123",
                "user_id": "user-456",
                "event_id": "event-001",
                "seat_id": "event-001-A5",
                "confirmed_at": "2025-02-13T10:30:00",
                "price": 299.99,
                "payment_status": "confirmed",
                "email": "user@example.com"
            }
        }


class ReservationRequest(BaseModel):
    """Request model for seat reservation."""
    event_id: str = Field(..., description="ID of the event")
    seat_id: str = Field(..., description="ID of the seat to reserve")
    user_id: str = Field(..., description="ID of the user making reservation")
    email: Optional[str] = Field(None, description="User's email for confirmation")

    @field_validator('event_id', 'seat_id', 'user_id')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "event-001",
                "seat_id": "event-001-A5",
                "user_id": "user-456",
                "email": "user@example.com"
            }
        }


class ReservationResponse(BaseModel):
    """Response model for seat reservation."""
    success: bool
    message: str
    booking_id: Optional[str] = None
    seat_id: Optional[str] = None
    event_id: Optional[str] = None
    price: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Seat reserved successfully",
                "booking_id": "booking-abc123",
                "seat_id": "event-001-A5",
                "event_id": "event-001",
                "price": 299.99
            }
        }


class EventListResponse(BaseModel):
    """Response model for listing events."""
    events: list[Event]
    count: int


class SeatMapResponse(BaseModel):
    """Response model for seat availability."""
    event_id: str
    event_name: str
    seats: list[Seat]
    total_seats: int
    available_seats: int
