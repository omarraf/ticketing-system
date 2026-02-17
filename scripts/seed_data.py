#!/usr/bin/env python3
"""
Seed DynamoDB tables with sample data for demo.
Run this after deploying infrastructure with Terraform.

Usage:
    python scripts/seed_data.py
"""
import boto3
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table names (these will match what Terraform creates)
EVENTS_TABLE = 'ticketing-system-events-dev'
SEATS_TABLE = 'ticketing-system-seats-dev'
BOOKINGS_TABLE = 'ticketing-system-bookings-dev'


def seed_events():
    """Create sample events in DynamoDB."""
    table = dynamodb.Table(EVENTS_TABLE)

    events = [
        {
            'event_id': 'event-001',
            'name': 'NBA Finals',
            'venue': 'Madison Square Garden',
            'date': (datetime.now() + timedelta(days=30)).isoformat(),
            'total_seats': 50,
            'available_seats': 50,
            'price': Decimal('299.99'),
            'description': 'The most anticipated game of the year'
        },
        {
            'event_id': 'event-002',
            'name': 'AWS re:Invent 2025',
            'venue': 'Las Vegas Convention Center',
            'date': (datetime.now() + timedelta(days=60)).isoformat(),
            'total_seats': 100,
            'available_seats': 100,
            'price': Decimal('1799.00'),
            'description': 'AWS annual cloud computing conference'
        },
        {
            'event_id': 'event-003',
            'name': 'DevOps Summit',
            'venue': 'San Francisco Moscone Center',
            'date': (datetime.now() + timedelta(days=45)).isoformat(),
            'total_seats': 75,
            'available_seats': 75,
            'price': Decimal('499.00'),
            'description': 'Learn the latest in DevOps and cloud infrastructure'
        }
    ]

    print("🎫 Seeding Events table...")
    for event in events:
        try:
            table.put_item(Item=event)
            print(f"  ✅ Created event: {event['name']}")
        except Exception as e:
            print(f"  ❌ Error creating event {event['event_id']}: {str(e)}")

    print(f"\n✅ Successfully seeded {len(events)} events\n")


def seed_seats():
    """Create sample seats for each event."""
    table = dynamodb.Table(SEATS_TABLE)

    # Event configurations: (event_id, num_rows, seats_per_row)
    event_configs = [
        ('event-001', 5, 10),   # Taylor Swift: 5 rows x 10 seats = 50 seats
        ('event-002', 10, 10),  # AWS re:Invent: 10 rows x 10 seats = 100 seats
        ('event-003', 5, 15),   # DevOps Summit: 5 rows x 15 seats = 75 seats
    ]

    print("💺 Seeding Seats table...")
    total_seats = 0

    for event_id, num_rows, seats_per_row in event_configs:
        for row in range(1, num_rows + 1):
            row_letter = chr(64 + row)  # A, B, C, D, E...

            for seat_num in range(1, seats_per_row + 1):
                seat = {
                    'seat_id': f'{event_id}-{row_letter}{seat_num}',
                    'event_id': event_id,
                    'row': row_letter,
                    'number': seat_num,
                    'status': 'available',  # available, reserved, sold
                    'section': 'General Admission',
                    'created_at': datetime.now().isoformat()
                }

                try:
                    table.put_item(Item=seat)
                    total_seats += 1
                except Exception as e:
                    print(f"  ❌ Error creating seat {seat['seat_id']}: {str(e)}")

        print(f"  ✅ Created {num_rows * seats_per_row} seats for {event_id}")

    print(f"\n✅ Successfully seeded {total_seats} total seats\n")


def seed_sample_booking():
    """Create one sample booking to show what confirmed bookings look like."""
    table = dynamodb.Table(BOOKINGS_TABLE)

    sample_booking = {
        'booking_id': 'booking-sample-001',
        'user_id': 'demo-user-123',
        'event_id': 'event-001',
        'seat_id': 'event-001-A1',
        'confirmed_at': datetime.now().isoformat(),
        'price': Decimal('299.99'),
        'payment_status': 'confirmed',
        'email': 'demo@example.com'
    }

    print("📋 Seeding sample booking...")
    try:
        table.put_item(Item=sample_booking)
        print(f"  ✅ Created sample booking: {sample_booking['booking_id']}")
        print(f"     User: {sample_booking['user_id']}")
        print(f"     Seat: {sample_booking['seat_id']}\n")
    except Exception as e:
        print(f"  ❌ Error creating sample booking: {str(e)}\n")


def clear_tables():
    """Clear all data from tables (optional - for clean demo)."""
    print("🗑️  Clearing existing data...\n")

    tables = {
        'Events': EVENTS_TABLE,
        'Seats': SEATS_TABLE,
        'Bookings': BOOKINGS_TABLE
    }

    for name, table_name in tables.items():
        try:
            table = dynamodb.Table(table_name)

            # Scan and delete all items
            scan = table.scan()
            with table.batch_writer() as batch:
                for item in scan['Items']:
                    if name == 'Events':
                        batch.delete_item(Key={'event_id': item['event_id']})
                    elif name == 'Seats':
                        batch.delete_item(Key={'seat_id': item['seat_id'], 'event_id': item['event_id']})
                    elif name == 'Bookings':
                        batch.delete_item(Key={'booking_id': item['booking_id']})

            print(f"  ✅ Cleared {name} table")
        except Exception as e:
            print(f"  ⚠️  Could not clear {name} table: {str(e)}")

    print()


def verify_seed():
    """Verify that data was seeded correctly."""
    print("🔍 Verifying seeded data...\n")

    # Check events
    events_table = dynamodb.Table(EVENTS_TABLE)
    events_count = events_table.scan(Select='COUNT')['Count']
    print(f"  Events: {events_count} items")

    # Check seats
    seats_table = dynamodb.Table(SEATS_TABLE)
    seats_count = seats_table.scan(Select='COUNT')['Count']
    print(f"  Seats: {seats_count} items")

    # Check bookings
    bookings_table = dynamodb.Table(BOOKINGS_TABLE)
    bookings_count = bookings_table.scan(Select='COUNT')['Count']
    print(f"  Bookings: {bookings_count} items")

    print("\n✅ Verification complete!\n")


def main():
    print("\n" + "="*60)
    print("  🎟️  Ticketing System - DynamoDB Seed Script")
    print("="*60 + "\n")

    try:
        # Optional: Clear existing data for clean demo
        clear_tables()

        # Seed data
        seed_events()
        seed_seats()
        seed_sample_booking()

        # Verify
        verify_seed()

        print("="*60)
        print("  ✅ Seed complete! Your demo data is ready.")
        print("="*60 + "\n")

        print("Next steps:")
        print("  1. Open AWS Console → DynamoDB")
        print("  2. Browse the tables to see your data")
        print("  3. Ready for your demo!\n")

    except Exception as e:
        print(f"\n❌ Error seeding data: {str(e)}")
        print("Make sure you've deployed infrastructure with Terraform first!\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
