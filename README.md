# High-Concurrency Event Ticketing System

A serverless event ticketing platform built with AWS services, demonstrating distributed locking, event-driven architecture, and infrastructure as code.

## Problem Statement

**How do you prevent double-booking when thousands of users try to reserve the same seat simultaneously?**

This project solves the race condition problem using:
- **Distributed Locking** (Redis Redlock)
- **Event-Driven Architecture** (EventBridge + SQS)
- **Atomic Database Operations** (DynamoDB conditional writes)

## Architecture

```
Client → API Gateway → Lambda (FastAPI)
                          ↓
                    Redis (Lock)
                          ↓
                    DynamoDB (Reserve)
                          ↓
                    EventBridge (Event)
                          ↓
                      SQS Queue
                          ↓
                    Lambda (Payment)
                          ↓
                    DynamoDB (Confirm)
```

## AWS Services Used

| Service | Purpose |
|---------|---------|
| **AWS Lambda** | Serverless compute for API and event handlers |
| **Amazon DynamoDB** | NoSQL database for events, seats, and bookings |
| **Amazon ElastiCache (Redis)** | Distributed locking with Redlock algorithm |
| **Amazon EventBridge** | Event bus for decoupled service orchestration |
| **Amazon SQS** | Message queue for reliable payment processing |
| **AWS API Gateway** | HTTP API endpoints |
| **Terraform** | Infrastructure as Code for reproducible deployments |

## Project Structure

```
ticketing-system/
├── infrastructure/              # Terraform IaC
│   ├── modules/
│   │   ├── dynamodb/           # DynamoDB tables
│   │   ├── lambda/             # Lambda functions
│   │   ├── redis/              # ElastiCache Redis cluster
│   │   ├── eventbridge/        # Event bus and rules
│   │   ├── sqs/                # SQS queues
│   │   └── api_gateway/        # API Gateway configuration
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── src/                        # Python application
│   ├── api/
│   │   ├── main.py            # FastAPI app
│   │   └── routes/            # API routes
│   ├── services/              # Business logic
│   │   ├── lock_service.py   # Redis Redlock
│   │   ├── seat_service.py   # Seat reservation
│   │   └── eventbridge_service.py
│   ├── handlers/              # Lambda event handlers
│   │   ├── payment_handler.py
│   │   └── email_handler.py
│   ├── models/                # Data models
│   └── utils/                 # Utilities
├── tests/
│   └── test_concurrency.py   # Load testing
├── scripts/
│   ├── seed_data.py          # Database seeding
│   └── destroy.sh            # Cleanup script
├── requirements.txt
├── MVP_ROADMAP.md            # Implementation guide
└── README.md
```

## Prerequisites

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Terraform** (>= 1.0)
- **Python** (>= 3.9)
- **Git**

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ticketing-system

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### 3. Deploy Infrastructure

```bash
cd infrastructure

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Deploy to AWS
terraform apply
```

This will create:
- DynamoDB tables (events, seats, bookings)
- ElastiCache Redis cluster
- EventBridge event bus and rules
- SQS queues (payment processing + DLQ)
- Lambda functions (placeholder)
- API Gateway

**Note**: Deployment takes ~10-15 minutes.

### 4. Deploy Lambda Functions

```bash
cd ../src

# Package dependencies
pip install -r requirements.txt -t package/
cd package && zip -r ../function.zip .

# Add application code
cd ..
zip -r function.zip api/ services/ handlers/ models/ utils/

# Update Lambda functions
aws lambda update-function-code \
  --function-name reserve-seat \
  --zip-file fileb://function.zip

aws lambda update-function-code \
  --function-name payment-processor \
  --zip-file fileb://function.zip
```

### 5. Seed Database

```bash
cd ../scripts
python seed_data.py
```

### 6. Test the API

Get your API Gateway URL from Terraform outputs:
```bash
cd ../infrastructure
terraform output api_gateway_url
```

Test endpoints:
```bash
# Get all events
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/events

# Get seats for an event
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/events/event1/seats

# Reserve a seat
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/reserve \
  -H "Content-Type: application/json" \
  -d '{"event_id": "event1", "seat_id": "A1", "user_id": "user123"}'
```

## Testing Concurrency

Run the load test to verify distributed locking works:

```bash
cd tests
python test_concurrency.py
```

This simulates 100 concurrent users trying to book the same seat. Expected result:
- **1 successful reservation**
- **99 failures** (seat unavailable or lock timeout)

## Monitoring

View logs and metrics in AWS CloudWatch:
- Lambda function logs
- EventBridge event deliveries
- SQS queue depth
- DynamoDB read/write activity

## Teardown

**IMPORTANT**: To avoid ongoing AWS costs, destroy all resources when done:

```bash
cd infrastructure
terraform destroy
```

Or use the cleanup script:
```bash
cd scripts
./destroy.sh
```

This will delete:
- All Lambda functions
- API Gateway
- DynamoDB tables (and all data)
- ElastiCache Redis cluster
- EventBridge event bus and rules
- SQS queues
- IAM roles and policies

## How It Works

### Three Layers of Protection Against Double Booking

#### 1. Application-Level Locking (Redis Redlock)
```python
lock = acquire_lock(f"seat:{seat_id}", ttl=10000)
if lock:
    # Critical section - only one process can enter
    reserve_seat(seat_id, user_id)
    release_lock(lock)
```

#### 2. Event-Driven Architecture (EventBridge + SQS)
```python
# Publish event after reservation
publish_to_eventbridge({
    "source": "ticketing.reservations",
    "detail-type": "SeatReserved",
    "detail": {"seat_id": seat_id, "user_id": user_id}
})

# EventBridge routes to SQS → Payment Lambda
# Ensures reliable processing with retry logic
```

#### 3. Database Constraints (DynamoDB Conditional Writes)
```python
# Final safety check - only update if seat is available
dynamodb.update_item(
    Key={'seat_id': seat_id},
    UpdateExpression='SET status = :sold',
    ConditionExpression='status = :available'
)
# Raises exception if condition fails (seat already sold)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/events` | List all events |
| GET | `/events/{id}/seats` | Get available seats for an event |
| POST | `/reserve` | Reserve a seat (requires event_id, seat_id, user_id) |

## Development

### Local Testing

```bash
cd src
uvicorn api.main:app --reload
```

API will be available at `http://localhost:8000`

### Running Tests

```bash
pytest tests/
```

## Key Concepts Demonstrated

1. **Serverless Architecture**: No servers to manage, auto-scaling
2. **Distributed Systems**: Handling race conditions in concurrent environments
3. **Event-Driven Design**: Decoupled services communicating via events
4. **Infrastructure as Code**: Reproducible, version-controlled infrastructure
5. **NoSQL Database Design**: Efficient data modeling with DynamoDB
6. **Message Queuing**: Reliable processing with SQS
7. **API Design**: RESTful endpoints with proper error handling

## Common Issues

### Lambda can't connect to Redis
- Ensure Lambda is in the same VPC as ElastiCache
- Check security group rules allow inbound traffic on port 6379

### DynamoDB ConditionalCheckFailedException
- This is expected behavior when a seat is already reserved
- Indicates the safety mechanism is working correctly

### EventBridge events not triggering Lambda
- Check EventBridge rules are enabled
- Verify event pattern matches published events
- Check Lambda permissions allow EventBridge invocation

## Cost Estimate

For development/testing (assuming moderate usage):
- Lambda: ~$0.20/day (generous free tier)
- DynamoDB: ~$0.30/day (on-demand pricing)
- ElastiCache: ~$1.50/day (t3.micro node)
- EventBridge: ~$0.10/day
- SQS: ~$0.05/day
- API Gateway: ~$0.10/day

**Total**: ~$2.25/day or ~$70/month

**Remember to run `terraform destroy` when done to avoid charges!**

## Next Steps

- [ ] Add authentication (AWS Cognito)
- [ ] Implement payment integration (Stripe)
- [ ] Add frontend (React/Vue)
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Add monitoring dashboards
- [ ] Implement reservation expiry with TTL
- [ ] Scale to multi-region deployment

## Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Redlock Algorithm](https://redis.io/docs/manual/patterns/distributed-locks/)
- [EventBridge Event Patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## License

MIT

## Author

Built as a demonstration of AWS services, distributed systems, and infrastructure as code.
