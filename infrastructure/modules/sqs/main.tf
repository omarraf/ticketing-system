# Dead Letter Queue (DLQ) - Holds failed payment processing messages
resource "aws_sqs_queue" "payment_dlq" {
  name                      = "${var.project_name}-payment-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days (max retention)

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-payment-dlq-${var.environment}"
      Environment = var.environment
      Purpose     = "Dead letter queue for failed payment processing"
    }
  )
}

# Payment Processing Queue - Main queue for handling seat reservation payments
resource "aws_sqs_queue" "payment_queue" {
  name                       = "${var.project_name}-payment-queue-${var.environment}"
  visibility_timeout_seconds = 300 # 5 minutes (should be >= Lambda timeout)
  message_retention_seconds  = 345600 # 4 days
  receive_wait_time_seconds  = 20 # Long polling for efficiency

  # Redrive policy - send to DLQ after 3 failed attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.payment_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-payment-queue-${var.environment}"
      Environment = var.environment
      Purpose     = "Payment processing queue for seat reservations"
    }
  )
}

# Queue Policy - Allow EventBridge to send messages to the queue
resource "aws_sqs_queue_policy" "payment_queue_policy" {
  queue_url = aws_sqs_queue.payment_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.payment_queue.arn
      }
    ]
  })
}
