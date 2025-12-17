# Custom Event Bus for Ticketing System
resource "aws_cloudwatch_event_bus" "ticketing" {
  name = "${var.project_name}-event-bus-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-event-bus-${var.environment}"
      Environment = var.environment
      Purpose     = "Event-driven orchestration for ticketing system"
    }
  )
}

# Event Rule: Route "SeatReserved" events to SQS for payment processing
resource "aws_cloudwatch_event_rule" "seat_reserved_to_payment_queue" {
  name           = "${var.project_name}-seat-reserved-to-payment-${var.environment}"
  description    = "Route SeatReserved events to payment processing queue"
  event_bus_name = aws_cloudwatch_event_bus.ticketing.name

  event_pattern = jsonencode({
    source      = ["ticketing.reservations"]
    detail-type = ["SeatReserved"]
  })

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-seat-reserved-rule-${var.environment}"
      Environment = var.environment
    }
  )
}

# Target: Send matched events to SQS payment queue
resource "aws_cloudwatch_event_target" "payment_queue_target" {
  rule           = aws_cloudwatch_event_rule.seat_reserved_to_payment_queue.name
  event_bus_name = aws_cloudwatch_event_bus.ticketing.name
  arn            = var.payment_queue_arn
  target_id      = "PaymentQueueTarget"
}

# Archive: Optional - store all events for replay/debugging
resource "aws_cloudwatch_event_archive" "ticketing_archive" {
  name             = "${var.project_name}-event-archive-${var.environment}"
  event_source_arn = aws_cloudwatch_event_bus.ticketing.arn
  retention_days   = 7 # Keep events for 7 days

  description = "Archive of all ticketing events for debugging and replay"
}
