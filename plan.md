# High-Concurrency Event Ticketing System

**The Resume Hook**: Solving the "Double Booking" problem with distributed systems and AWS services.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | **Python + FastAPI** | Fast async API framework, easy Lambda deployment |
| **Infrastructure** | **Terraform** | IaC for reproducible AWS deployments |
| **Compute** | **AWS Lambda** | Serverless, auto-scaling, cost-effective |
| **Database** | **DynamoDB** | NoSQL, high-throughput, atomic operations |
| **Distributed Lock** | **Redis (ElastiCache)** | Redlock algorithm to prevent race conditions |
| **Event Bus** | **AWS EventBridge** | Event-driven orchestration, pub/sub pattern |
| **Queue** | **AWS SQS** | Buffering for critical payment processing |
| **API Gateway** | **AWS API Gateway** | HTTP endpoints for Lambda functions |
| **Monitoring** | **CloudWatch** | Logs and metrics |

**Core Services Count**: Lambda, EventBridge, SQS, DynamoDB, ElastiCache (Redis), API Gateway = 6 AWS services + Terraform = 7 total

---

## Architecture Overview

```
User Request → API Gateway → Lambda (FastAPI)
                                ↓
                          Redis (Redlock)
                                ↓
                          Reserve Seat → EventBridge: "SeatReserved" event
                                            ├─> SQS Queue → Worker Lambda → DynamoDB (payment)
                                            ├─> Lambda (send confirmation email)
                                            └─> Lambda (analytics/fraud detection)
```

**Key Components**:
1. **API Layer**: FastAPI on Lambda handles incoming reservation requests
2. **Distributed Lock**: Redis Redlock prevents multiple users from reserving same seat
3. **Event Bus**: EventBridge decouples reservation event from downstream actions
4. **Critical Path**: SQS buffers payment processing for guaranteed delivery
5. **Parallel Processing**: Non-critical tasks (email, analytics) subscribe to EventBridge directly
6. **Data Store**: DynamoDB with conditional writes as final safety net
7. **Infrastructure**: Terraform manages all AWS resources

---

## Core Problem: Preventing Double Bookings

**Three Layers of Protection**:

1. **Application-Level Locking** (Redis Redlock)
   - Acquire distributed lock before seat reservation
   - Lock expires after timeout (prevents deadlock)
   - Multiple Redis nodes for fault tolerance

2. **Event-Driven Architecture** (EventBridge + SQS)
   - EventBridge decouples reservation event from downstream processing
   - SQS buffers critical payment processing (handles traffic spikes)
   - Retry logic and DLQ for failed operations
   - Parallel processing of non-critical tasks (email, analytics)

3. **Database Constraints** (DynamoDB Conditional Writes)
   - Final safety check with `condition-expression`
   - Atomic update only if seat status is "available"
   - Prevents race conditions at data layer

---

## Implementation Plan

### Phase 1: Infrastructure Setup (Terraform)

**Tasks**:
1. Set up Terraform project structure
2. Define DynamoDB tables:
   - `events` - event details and total capacity
   - `seats` - seat inventory with status tracking
   - `bookings` - confirmed reservations
3. Create ElastiCache Redis cluster (multi-node for Redlock)
4. Set up EventBridge event bus:
   - Custom event bus for ticketing events
   - Event rules for routing to targets
   - Dead letter queue for failed events
5. Set up SQS queues:
   - `payment-processing-queue` - critical path for payments
   - `payment-processing-dlq` - failed payment processing
6. Configure IAM roles for Lambda execution and EventBridge
7. Set up API Gateway with Lambda integration

**Terraform Modules**:
```
infrastructure/
├── modules/
│   ├── dynamodb/
│   ├── lambda/
│   ├── redis/
│   ├── eventbridge/
│   ├── sqs/
│   └── api-gateway/
├── main.tf
├── variables.tf
└── outputs.tf
```

---

### Phase 2: Core API Development (FastAPI)

**Lambda Functions**:

1. **`get_events`** - List available events
   ```python
   GET /events
   ```

2. **`get_seats`** - Get seat availability for event
   ```python
   GET /events/{event_id}/seats
   ```

3. **`reserve_seat`** - Reserve seat with distributed lock
   ```python
   POST /reserve
   Body: {event_id, seat_id, user_id}

   Flow:
   1. Acquire Redis lock (seat_id)
   2. Check seat availability
   3. Create temp reservation
   4. Publish "SeatReserved" event to EventBridge
   5. Release lock
   6. Return reservation_id
   ```

4. **`process_payment`** - SQS worker for payment processing
   ```python
   Triggered by SQS message (from EventBridge rule)

   Flow:
   1. Validate payment (stub/Stripe integration)
   2. DynamoDB conditional update
   3. Update seat status to "sold"
   4. Create booking record
   5. Publish "PaymentConfirmed" event to EventBridge
   ```

5. **`send_confirmation_email`** - Email notification handler
   ```python
   Triggered by EventBridge "SeatReserved" event

   Flow:
   1. Get user details
   2. Format confirmation email
   3. Send via SES/SendGrid
   ```

6. **`update_analytics`** - Analytics/fraud detection
   ```python
   Triggered by EventBridge "SeatReserved" event

   Flow:
   1. Log reservation event
   2. Check for suspicious patterns
   3. Update metrics dashboard
   ```

7. **`release_expired`** - Cleanup expired reservations
   ```python
   Scheduled Lambda (EventBridge Scheduler)
   Runs every minute
   ```

**FastAPI Structure**:
```
src/
├── api/
│   ├── main.py (FastAPI app)
│   ├── routes/
│   │   ├── events.py
│   │   └── reservations.py
│   └── dependencies.py
├── services/
│   ├── lock_service.py (Redlock)
│   ├── seat_service.py
│   ├── eventbridge_service.py (publish events)
│   └── payment_service.py
├── handlers/
│   ├── email_handler.py (EventBridge subscriber)
│   └── analytics_handler.py (EventBridge subscriber)
├── models/
│   └── schemas.py
└── utils/
    └── dynamodb.py
```

---

### Phase 3: Distributed Locking Implementation

**Redlock Algorithm** (using `python-redis-lock`):

```python
import redis
from redlock import Redlock

# Connect to Redis cluster
redis_nodes = [
    {'host': 'node1', 'port': 6379},
    {'host': 'node2', 'port': 6379},
    {'host': 'node3', 'port': 6379},
]

redlock = Redlock(redis_nodes)

def reserve_with_lock(seat_id, user_id, event_id):
    lock_key = f"seat:{seat_id}"
    lock = redlock.lock(lock_key, 10000)  # 10 sec TTL

    if lock:
        try:
            # Critical section
            seat = check_availability(seat_id)
            if seat.status == "available":
                reservation_id = create_reservation(seat_id, user_id, event_id)

                # Publish event to EventBridge
                publish_to_eventbridge({
                    "source": "ticketing.reservations",
                    "detail-type": "SeatReserved",
                    "detail": {
                        "reservation_id": reservation_id,
                        "event_id": event_id,
                        "seat_id": seat_id,
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })

                return {"status": "reserved", "reservation_id": reservation_id}
            else:
                return {"status": "unavailable"}
        finally:
            redlock.unlock(lock)
    else:
        return {"status": "lock_failed"}
```

**Why Redlock?**:
- Multi-node consensus prevents single point of failure
- Time-based expiry prevents deadlocks
- Industry-standard solution (used by Ticketmaster, etc.)

---

### Phase 4: EventBridge + SQS Integration

**EventBridge Publisher** (in reservation endpoint):
```python
import boto3

eventbridge = boto3.client('events')
event_bus_name = os.environ['EVENT_BUS_NAME']

def publish_to_eventbridge(event_data):
    response = eventbridge.put_events(
        Entries=[
            {
                'Source': event_data['source'],
                'DetailType': event_data['detail-type'],
                'Detail': json.dumps(event_data['detail']),
                'EventBusName': event_bus_name
            }
        ]
    )
    return response
```

**EventBridge Rules** (configured in Terraform):
```hcl
# Rule 1: Route to SQS for payment processing
resource "aws_cloudwatch_event_rule" "seat_reserved_to_sqs" {
  name           = "seat-reserved-to-payment-queue"
  event_bus_name = aws_cloudwatch_event_bus.ticketing.name
  event_pattern  = jsonencode({
    source      = ["ticketing.reservations"]
    detail-type = ["SeatReserved"]
  })
}

# Rule 2: Route to email Lambda
resource "aws_cloudwatch_event_rule" "seat_reserved_to_email" {
  name           = "seat-reserved-to-email"
  event_bus_name = aws_cloudwatch_event_bus.ticketing.name
  event_pattern  = jsonencode({
    source      = ["ticketing.reservations"]
    detail-type = ["SeatReserved"]
  })
}

# Rule 3: Route to analytics Lambda
resource "aws_cloudwatch_event_rule" "seat_reserved_to_analytics" {
  name           = "seat-reserved-to-analytics"
  event_bus_name = aws_cloudwatch_event_bus.ticketing.name
  event_pattern  = jsonencode({
    source      = ["ticketing.reservations"]
    detail-type = ["SeatReserved"]
  })
}
```

**SQS Consumer** (payment processing Lambda):
```python
def lambda_handler(event, context):
    for record in event['Records']:
        # EventBridge sends the event detail wrapped in SQS message
        event_detail = json.loads(record['body'])['detail']

        try:
            # Process payment
            process_payment(
                event_detail['reservation_id'],
                event_detail['seat_id'],
                event_detail['user_id']
            )
        except Exception as e:
            # Let SQS retry or send to DLQ
            raise e
```

**EventBridge Direct Subscribers** (email/analytics):
```python
# Email handler
def lambda_handler(event, context):
    detail = event['detail']
    send_confirmation_email(
        user_id=detail['user_id'],
        seat_id=detail['seat_id'],
        reservation_id=detail['reservation_id']
    )

# Analytics handler
def lambda_handler(event, context):
    detail = event['detail']
    log_reservation_metric(detail)
    check_fraud_patterns(detail)
```

**Benefits**:
- **EventBridge**: Decouples services, enables pub/sub, easy to add new subscribers
- **SQS (for critical path)**: Buffers payment processing, handles traffic spikes
- **Direct Lambda (for non-critical)**: Email and analytics run in parallel
- **Failure isolation**: Email failure doesn't block payment processing
- **Dead letter queues**: Monitoring and retry for failed operations

---

### Phase 5: DynamoDB Schema & Operations

**Tables**:

```
Events Table:
PK: event_id
Attributes: name, date, venue, total_seats, available_seats

Seats Table:
PK: seat_id
SK: event_id
Attributes: status, reserved_by, reserved_at, expiry_ttl
GSI: event_id-status-index (query available seats by event)

Bookings Table:
PK: booking_id
SK: user_id
Attributes: event_id, seat_id, confirmed_at, price
```

**Conditional Update** (final safety):
```python
def confirm_booking(seat_id, user_id, reservation_id):
    try:
        response = dynamodb.update_item(
            TableName='Seats',
            Key={'seat_id': seat_id},
            UpdateExpression='SET #status = :sold, reserved_by = :user',
            ConditionExpression='#status = :available',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':available': 'available',
                ':sold': 'sold',
                ':user': user_id
            }
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Seat already sold - race condition prevented!
            return False
        raise e
```

---

## Testing Concurrency

**Load Test Script** (simulate double booking):

```python
import concurrent.futures
import requests

def reserve_seat(user_id):
    response = requests.post(
        'https://api.example.com/reserve',
        json={'event_id': '1', 'seat_id': 'A1', 'user_id': user_id}
    )
    return response.json()

# Simulate 100 concurrent requests for same seat
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(reserve_seat, f'user_{i}') for i in range(100)]
    results = [f.result() for f in futures]

# Expected: Only 1 success, 99 failures
successes = [r for r in results if r['status'] == 'reserved']
print(f"Successful reservations: {len(successes)}")  # Should be 1
```

---

## Deployment

**Using Terraform**:
```bash
cd infrastructure
terraform init
terraform plan
terraform apply

# Deploy Lambda functions
cd ../src
pip install -r requirements.txt -t package/
cd package && zip -r ../function.zip .
cd .. && zip -g function.zip api/*.py services/*.py

aws lambda update-function-code \
  --function-name reserve-seat \
  --zip-file fileb://function.zip
```

**Environment Variables** (set via Terraform):
- `DYNAMODB_EVENTS_TABLE`
- `DYNAMODB_SEATS_TABLE`
- `REDIS_CLUSTER_ENDPOINT`
- `EVENT_BUS_NAME`
- `SQS_PAYMENT_QUEUE_URL`

---

## Resume Bullets

> **High-Concurrency Event Ticketing System | Python, AWS, Terraform, Redis**
>
> - Architected a serverless ticketing platform on AWS Lambda and FastAPI, capable of handling traffic spikes during simulated high-demand releases
>
> - Implemented **Distributed Locking** using Redis Redlock algorithm across 3+ nodes to eliminate race conditions and prevent overselling of inventory in high-concurrency scenarios
>
> - Designed **event-driven architecture** using AWS EventBridge for service decoupling, routing reservation events to multiple downstream handlers (payment processing, notifications, analytics) with independent failure isolation
>
> - Integrated **AWS SQS** as a buffering layer for critical payment processing, ensuring guaranteed delivery and retry logic while handling traffic spikes without blocking the main application thread
>
> - Deployed infrastructure as code using **Terraform**, managing DynamoDB tables, ElastiCache clusters, EventBridge event buses, SQS queues, Lambda functions, and API Gateway with reproducible configurations
>
> - Validated data integrity with DynamoDB conditional writes as a final safeguard against double-booking under 100+ concurrent requests

---

## Monitoring & Observability

**CloudWatch Dashboards**:
- API latency (p50, p99)
- EventBridge event publishing rate and failures
- SQS queue depth (payment processing)
- Lambda error rates (by function)
- Redis lock acquisition success rate
- DynamoDB throttling events
- EventBridge rule invocation metrics

**Alarms**:
- EventBridge failed invocations > 5
- SQS DLQ message count > 10
- Lambda error rate > 5%
- Redis cluster CPU > 80%
- Email/analytics Lambda failures (warning, non-critical)

---

## Project Structure

```
ticketing-system/
├── infrastructure/           # Terraform IaC
│   ├── modules/
│   │   ├── dynamodb/
│   │   ├── lambda/
│   │   ├── redis/
│   │   ├── eventbridge/
│   │   ├── sqs/
│   │   └── api-gateway/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── src/                      # Python FastAPI app
│   ├── api/
│   │   ├── main.py
│   │   └── routes/
│   ├── services/
│   │   ├── lock_service.py
│   │   ├── seat_service.py
│   │   ├── eventbridge_service.py
│   │   └── payment_service.py
│   ├── handlers/
│   │   ├── email_handler.py
│   │   └── analytics_handler.py
│   ├── models/
│   └── utils/
├── tests/
│   ├── test_concurrency.py
│   ├── test_eventbridge.py
│   └── test_api.py
├── requirements.txt
└── README.md
```

---

## Next Steps

1. Initialize Terraform project and provision AWS resources
2. Implement FastAPI endpoints with Redis locking
3. Set up EventBridge event bus and routing rules
4. Configure SQS integration for payment processing
5. Implement Lambda handlers for email and analytics
6. Deploy Lambda functions and test with concurrent requests
7. Document architecture with diagram
8. Add to GitHub with clear README

**Time Estimate**: 3-5 days for MVP, resume-ready version

---

## DevOps Class Presentation: 3 Services to Highlight

### 1. **Terraform** - Infrastructure as Code
**What it does**: Provisions and manages all AWS resources declaratively
**Why it's substantial**:
- Manages 6+ AWS services with dependencies
- Enables reproducible deployments
- State management and drift detection
- Modular architecture for reusability

**Talking points**:
- Show terraform modules for each service
- Demonstrate `terraform plan` vs `terraform apply`
- Explain state management and remote backends
- Discuss IaC best practices (variables, outputs, DRY)

### 2. **Amazon ElastiCache (Redis with Redlock)** - Distributed Locking
**What it does**: Prevents race conditions in high-concurrency seat reservations
**Why it's substantial**:
- Multi-node cluster configuration for fault tolerance
- Redlock algorithm implementation (consensus-based locking)
- Critical for solving the core business problem (double-booking)
- Performance tuning (TTL, connection pooling)

**Talking points**:
- Explain the double-booking problem
- Show how Redlock prevents race conditions
- Discuss multi-node setup and failover
- Demo concurrent request testing (100+ requests for same seat)

### 3. **Amazon EventBridge** - Event-Driven Orchestration
**What it does**: Decouples reservation events from downstream processing
**Why it's substantial**:
- Pub/sub pattern for service decoupling
- Event routing with pattern matching
- Integrates multiple targets (SQS, Lambda, etc.)
- Enables independent scaling and failure isolation

**Talking points**:
- Explain event-driven architecture benefits
- Show EventBridge rules and event patterns
- Demonstrate how one event triggers multiple workflows
- Discuss SQS vs EventBridge (when to use each)
- Show how easy it is to add new features (just add a rule)

---

## EventBridge vs SQS: When to Use Each

### **EventBridge (Event Bus)**
**Pattern**: Pub/Sub (1 event → many subscribers)

**Use when**:
- Multiple systems need to react to the same event
- You want to decouple services completely
- You need event filtering/routing based on patterns
- You want to add new features without code changes

**In this project**:
- "SeatReserved" event → triggers payment, email, analytics simultaneously

### **SQS (Queue)**
**Pattern**: Point-to-point work queue (1 message → 1 consumer)

**Use when**:
- You need guaranteed processing with buffering
- Critical path that requires retry logic
- You want to throttle/rate-limit processing
- Order matters (FIFO queue)

**In this project**:
- EventBridge routes to SQS → payment processing (most critical)
- SQS provides buffering for traffic spikes

### **Why Use Both?**
```
EventBridge = Broadcaster ("Something happened!")
     ↓
     ├─> SQS → Critical processing (with buffering)
     ├─> Lambda → Non-critical tasks (direct)
     └─> Lambda → Analytics
```

**Benefits**:
- Critical path gets SQS reliability
- Non-critical tasks don't slow down the system
- Easy to add new subscribers later
- Each service can fail independently
