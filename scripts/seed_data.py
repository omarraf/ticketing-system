#!/usr/bin/env python3
"""
Seed DynamoDB tables with demo data for the ticketing system.
Run this after deploying infrastructure with Terraform.

Usage:
    # Seed with defaults (dev env, us-east-1)
    python scripts/seed_data.py

    # Clear existing data first, then seed
    python scripts/seed_data.py --clear

    # Target a specific environment or region
    python scripts/seed_data.py --env prod --region us-west-2

    # Read table names from terraform output (run from project root)
    python scripts/seed_data.py --from-tf-output

    # Only seed a specific component
    python scripts/seed_data.py --only events
    python scripts/seed_data.py --only seats
    python scripts/seed_data.py --only bookings

    # Dry-run: print what would be seeded without writing anything
    python scripts/seed_data.py --dry-run
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# ---------------------------------------------------------------------------
# Event definitions
# ---------------------------------------------------------------------------

def build_events(now: datetime):
    """Return a list of event item dicts ready for DynamoDB put_item."""
    return [
        {
            "event_id": "event-001",
            "name": "NBA Finals – Game 7",
            "venue": "Madison Square Garden",
            "date": (now + timedelta(days=14)).strftime("%Y-%m-%dT19:30:00"),
            "total_seats": 60,
            "available_seats": 60,
            "price": Decimal("299.99"),
            "description": "The deciding game of the NBA Finals. High demand expected.",
        },
        {
            "event_id": "event-002",
            "name": "AWS re:Invent 2025",
            "venue": "Las Vegas Convention Center",
            "date": (now + timedelta(days=60)).strftime("%Y-%m-%dT09:00:00"),
            "total_seats": 100,
            "available_seats": 100,
            "price": Decimal("1799.00"),
            "description": "AWS annual cloud computing conference — keynotes, workshops, and more.",
        },
        {
            "event_id": "event-003",
            "name": "DevOps World Summit",
            "venue": "Moscone Center, San Francisco",
            "date": (now + timedelta(days=45)).strftime("%Y-%m-%dT10:00:00"),
            "total_seats": 75,
            "available_seats": 75,
            "price": Decimal("499.00"),
            "description": "The premier DevOps conference covering CI/CD, platform engineering, and SRE.",
        },
    ]


# ---------------------------------------------------------------------------
# Seat layout definitions
# Each entry: (event_id, sections)
# Each section: { name, rows, seats_per_row, price_multiplier }
# ---------------------------------------------------------------------------

EVENT_SEAT_LAYOUTS = [
    {
        "event_id": "event-001",
        "sections": [
            {"name": "VIP Floor",        "rows": ["A", "B"],               "seats_per_row": 10},
            {"name": "Front Orchestra",  "rows": ["C", "D", "E"],          "seats_per_row": 10},
            {"name": "Rear Orchestra",   "rows": ["F", "G", "H", "I", "J"], "seats_per_row": 10},
        ],
    },
    {
        "event_id": "event-002",
        "sections": [
            {"name": "Front Row",        "rows": ["A", "B"],               "seats_per_row": 10},
            {"name": "Main Hall",        "rows": ["C", "D", "E", "F", "G", "H"], "seats_per_row": 10},
            {"name": "Upper Tier",       "rows": ["I", "J"],               "seats_per_row": 10},
        ],
    },
    {
        "event_id": "event-003",
        "sections": [
            {"name": "VIP",              "rows": ["A"],                    "seats_per_row": 15},
            {"name": "Main Stage",       "rows": ["B", "C", "D"],          "seats_per_row": 15},
            {"name": "General Admission","rows": ["E"],                    "seats_per_row": 15},
        ],
    },
]


# Seats that should start out in a non-available state to make the demo
# more interesting. Format: { "event_id-ROWnum": status }
PRESOLD_SEATS = {
    # NBA Finals – a handful of VIP seats already gone
    "event-001-A1": "sold",
    "event-001-A2": "sold",
    "event-001-A3": "sold",
    "event-001-B1": "sold",
    "event-001-B2": "reserved",
    "event-001-C1": "reserved",
    # AWS re:Invent – a few front-row seats taken
    "event-002-A1": "sold",
    "event-002-A2": "sold",
    "event-002-B1": "reserved",
}


def build_seats(now: datetime):
    """Return (seats_list, per_event_sold_count) ready for batch writing."""
    ts = now.isoformat()
    seats = []
    sold_counts = {}  # event_id → number of sold seats

    for layout in EVENT_SEAT_LAYOUTS:
        event_id = layout["event_id"]
        sold_counts[event_id] = 0

        for section in layout["sections"]:
            section_name = section["name"]
            for row in section["rows"]:
                for num in range(1, section["seats_per_row"] + 1):
                    seat_id = f"{event_id}-{row}{num}"
                    status = PRESOLD_SEATS.get(seat_id, "available")

                    if status == "sold":
                        sold_counts[event_id] += 1

                    seat = {
                        "seat_id": seat_id,
                        "event_id": event_id,
                        "row": row,
                        "number": num,
                        "section": section_name,
                        "status": status,
                        "created_at": ts,
                    }

                    if status in ("reserved", "sold"):
                        seat["reserved_by"] = "seed-demo-user"
                        seat["reserved_at"] = ts

                    seats.append(seat)

    return seats, sold_counts


def build_sample_bookings(now: datetime):
    """Return a small list of realistic sample bookings."""
    ts = now.isoformat()
    return [
        {
            "booking_id": "booking-demo-0001",
            "user_id": "user-demo-alice",
            "event_id": "event-001",
            "seat_id": "event-001-A1",
            "confirmed_at": ts,
            "price": Decimal("299.99"),
            "payment_status": "confirmed",
            "email": "alice@example.com",
            "payment_intent_id": "pi_demo_alice_001",
        },
        {
            "booking_id": "booking-demo-0002",
            "user_id": "user-demo-bob",
            "event_id": "event-001",
            "seat_id": "event-001-A2",
            "confirmed_at": ts,
            "price": Decimal("299.99"),
            "payment_status": "confirmed",
            "email": "bob@example.com",
            "payment_intent_id": "pi_demo_bob_001",
        },
        {
            "booking_id": "booking-demo-0003",
            "user_id": "user-demo-carol",
            "event_id": "event-001",
            "seat_id": "event-001-B2",
            "confirmed_at": ts,
            "price": Decimal("299.99"),
            "payment_status": "pending",
            "email": "carol@example.com",
        },
        {
            "booking_id": "booking-demo-0004",
            "user_id": "user-demo-dave",
            "event_id": "event-002",
            "seat_id": "event-002-A1",
            "confirmed_at": ts,
            "price": Decimal("1799.00"),
            "payment_status": "confirmed",
            "email": "dave@example.com",
            "payment_intent_id": "pi_demo_dave_001",
        },
    ]


# ---------------------------------------------------------------------------
# DynamoDB helpers
# ---------------------------------------------------------------------------

def get_dynamodb(region: str):
    try:
        return boto3.resource("dynamodb", region_name=region)
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Configure via 'aws configure' or environment variables.")
        sys.exit(1)


def get_table_names_from_tf(env: str):
    """Try to read table names from 'terraform output -json' in the infrastructure dir."""
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd="infrastructure",
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            print(f"WARNING: terraform output failed: {result.stderr.strip()}")
            return None
        outputs = json.loads(result.stdout)
        return {
            "events":   outputs.get("events_table_name", {}).get("value"),
            "seats":    outputs.get("seats_table_name", {}).get("value"),
            "bookings": outputs.get("bookings_table_name", {}).get("value"),
        }
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"WARNING: Could not read terraform outputs ({e}). Falling back to defaults.")
        return None


def clear_table(table, key_attrs: list[str], label: str, dry_run: bool):
    if dry_run:
        print(f"  [dry-run] Would clear {label} table")
        return
    print(f"  Clearing {label}...")
    scan = table.scan(ProjectionExpression=", ".join(key_attrs))
    items = scan.get("Items", [])
    while "LastEvaluatedKey" in scan:
        scan = table.scan(
            ProjectionExpression=", ".join(key_attrs),
            ExclusiveStartKey=scan["LastEvaluatedKey"],
        )
        items.extend(scan.get("Items", []))

    if not items:
        print(f"    (empty, nothing to delete)")
        return

    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={k: item[k] for k in key_attrs})
    print(f"    Deleted {len(items)} items from {label}")


def batch_write(table, items: list, label: str, dry_run: bool):
    if dry_run:
        print(f"  [dry-run] Would write {len(items)} items to {label}")
        return 0

    written = 0
    errors = 0
    with table.batch_writer() as batch:
        for item in items:
            try:
                batch.put_item(Item=item)
                written += 1
            except ClientError as e:
                print(f"    ERROR writing item: {e.response['Error']['Message']}")
                errors += 1

    print(f"    Wrote {written} items to {label}" + (f" ({errors} errors)" if errors else ""))
    return written


def verify(dynamodb, table_names: dict):
    print("\nVerifying seeded data...")
    for label, name in table_names.items():
        try:
            count = dynamodb.Table(name).scan(Select="COUNT")["Count"]
            print(f"  {label.capitalize():10s}: {count} items")
        except ClientError as e:
            print(f"  {label.capitalize():10s}: ERROR — {e.response['Error']['Message']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Seed DynamoDB tables for the ticketing system demo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--env", default="dev",
        help="Environment suffix used in default table names (default: dev)",
    )
    parser.add_argument(
        "--region", default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--clear", action="store_true",
        help="Delete all existing items from tables before seeding",
    )
    parser.add_argument(
        "--from-tf-output", action="store_true",
        help="Read table names from 'terraform output -json' (runs inside ./infrastructure/)",
    )
    parser.add_argument(
        "--only", choices=["events", "seats", "bookings"], default=None,
        help="Seed only this component (default: all)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be seeded without writing to DynamoDB",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    now = datetime.now(timezone.utc)

    print()
    print("=" * 62)
    print("  Ticketing System — DynamoDB Seed Script")
    print("=" * 62)
    print(f"  Environment : {args.env}")
    print(f"  Region      : {args.region}")
    print(f"  Dry run     : {'yes' if args.dry_run else 'no'}")
    print(f"  Clear first : {'yes' if args.clear else 'no'}")
    print()

    # Resolve table names
    table_names = {
        "events":   f"ticketing-system-events-{args.env}",
        "seats":    f"ticketing-system-seats-{args.env}",
        "bookings": f"ticketing-system-bookings-{args.env}",
    }

    if args.from_tf_output:
        tf_names = get_table_names_from_tf(args.env)
        if tf_names:
            table_names.update({k: v for k, v in tf_names.items() if v})
            print("  Table names read from Terraform outputs.")

    print(f"  Events   table : {table_names['events']}")
    print(f"  Seats    table : {table_names['seats']}")
    print(f"  Bookings table : {table_names['bookings']}")
    print()

    db = get_dynamodb(args.region)
    events_table   = db.Table(table_names["events"])
    seats_table    = db.Table(table_names["seats"])
    bookings_table = db.Table(table_names["bookings"])

    seed_all    = args.only is None
    seed_events_flag   = seed_all or args.only == "events"
    seed_seats_flag    = seed_all or args.only == "seats"
    seed_bookings_flag = seed_all or args.only == "bookings"

    # ── Clear ──────────────────────────────────────────────────────────────
    if args.clear:
        print("Clearing existing data...")
        if seed_events_flag:
            clear_table(events_table,   ["event_id"],              "events",   args.dry_run)
        if seed_seats_flag:
            clear_table(seats_table,    ["seat_id", "event_id"],   "seats",    args.dry_run)
        if seed_bookings_flag:
            clear_table(bookings_table, ["booking_id"],            "bookings", args.dry_run)
        print()

    # ── Events ─────────────────────────────────────────────────────────────
    if seed_events_flag:
        events = build_events(now)
        print(f"Seeding events ({len(events)} items)...")
        if args.dry_run:
            for e in events:
                print(f"  [dry-run] {e['event_id']} — {e['name']}")
        else:
            batch_write(events_table, events, "events", dry_run=False)
        print()

    # ── Seats ──────────────────────────────────────────────────────────────
    if seed_seats_flag:
        seats, sold_counts = build_seats(now)

        # If we seeded events too, update their available_seats counts
        if seed_events_flag and not args.dry_run:
            events_list = build_events(now)
            for event in events_list:
                sold = sold_counts.get(event["event_id"], 0)
                if sold > 0:
                    try:
                        events_table.update_item(
                            Key={"event_id": event["event_id"]},
                            UpdateExpression="SET available_seats = available_seats - :sold",
                            ExpressionAttributeValues={":sold": sold},
                        )
                    except ClientError as e:
                        print(f"  WARNING: Could not adjust available_seats for {event['event_id']}: "
                              f"{e.response['Error']['Message']}")

        print(f"Seeding seats ({len(seats)} items across {len(EVENT_SEAT_LAYOUTS)} events)...")
        for layout in EVENT_SEAT_LAYOUTS:
            eid = layout["event_id"]
            event_seats = [s for s in seats if s["event_id"] == eid]
            sold = sum(1 for s in event_seats if s["status"] == "sold")
            reserved = sum(1 for s in event_seats if s["status"] == "reserved")
            available = sum(1 for s in event_seats if s["status"] == "available")
            print(f"  {eid}: {len(event_seats)} seats  "
                  f"({available} available, {reserved} reserved, {sold} sold)")

        batch_write(seats_table, seats, "seats", dry_run=args.dry_run)
        print()

    # ── Bookings ───────────────────────────────────────────────────────────
    if seed_bookings_flag:
        bookings = build_sample_bookings(now)
        print(f"Seeding sample bookings ({len(bookings)} items)...")
        if args.dry_run:
            for b in bookings:
                print(f"  [dry-run] {b['booking_id']}  seat={b['seat_id']}  "
                      f"status={b['payment_status']}")
        else:
            batch_write(bookings_table, bookings, "bookings", dry_run=False)
        print()

    # ── Verify ─────────────────────────────────────────────────────────────
    if not args.dry_run:
        verify(db, table_names)

    print()
    print("=" * 62)
    if args.dry_run:
        print("  Dry-run complete. No data was written.")
    else:
        print("  Seed complete. Your demo data is ready.")
    print("=" * 62)
    print()

    if not args.dry_run:
        print("Next steps:")
        print("  1. Set REACT_APP_API_URL in frontend/.env to your API Gateway URL")
        print("  2. cd frontend && npm start")
        print("  3. Or run the concurrency tests: python tests/test_concurrency.py")
        print()


if __name__ == "__main__":
    main()
