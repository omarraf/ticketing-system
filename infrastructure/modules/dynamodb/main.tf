# Events Table
resource "aws_dynamodb_table" "events" {
  name           = "${var.project_name}-events-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST" # On-demand pricing for MVP
  hash_key       = "event_id"

  attribute {
    name = "event_id"
    type = "S" # String
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-events-${var.environment}"
      Environment = var.environment
      TableType   = "events"
    }
  )
}

# Seats Table
resource "aws_dynamodb_table" "seats" {
  name           = "${var.project_name}-seats-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "seat_id"
  range_key      = "event_id"

  attribute {
    name = "seat_id"
    type = "S"
  }

  attribute {
    name = "event_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # Global Secondary Index to query seats by event_id and status
  global_secondary_index {
    name            = "event_id-status-index"
    hash_key        = "event_id"
    range_key       = "status"
    projection_type = "ALL"
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-seats-${var.environment}"
      Environment = var.environment
      TableType   = "seats"
    }
  )
}

# Bookings Table
resource "aws_dynamodb_table" "bookings" {
  name           = "${var.project_name}-bookings-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_id"

  attribute {
    name = "booking_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  # Global Secondary Index to query bookings by user_id
  global_secondary_index {
    name            = "user_id-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  # Enable TTL for automatic cleanup of expired reservations (optional)
  ttl {
    attribute_name = "expiry_time"
    enabled        = true
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-bookings-${var.environment}"
      Environment = var.environment
      TableType   = "bookings"
    }
  )
}
