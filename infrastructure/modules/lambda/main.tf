# Security Group for Lambda Functions (optional - for VPC/Redis access)
# Commented out for minimal demo without Redis
# resource "aws_security_group" "lambda" {
#   name_prefix = "${var.project_name}-lambda-${var.environment}-"
#   description = "Security group for Lambda functions"
#   vpc_id      = var.vpc_id
#
#   egress {
#     description = "Allow HTTPS to AWS services"
#     from_port   = 443
#     to_port     = 443
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = merge(
#     var.tags,
#     {
#       Name        = "${var.project_name}-lambda-sg-${var.environment}"
#       Environment = var.environment
#     }
#   )
#
#   lifecycle {
#     create_before_destroy = true
#   }
# }

# IAM Role for Lambda Execution
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-lambda-role-${var.environment}"
      Environment = var.environment
    }
  )
}

# IAM Policy for Lambda - DynamoDB Access
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "dynamodb-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.events_table_arn,
          var.seats_table_arn,
          var.bookings_table_arn,
          "${var.seats_table_arn}/index/*",
          "${var.bookings_table_arn}/index/*"
        ]
      }
    ]
  })
}

# IAM Policy for Lambda - EventBridge Access
resource "aws_iam_role_policy" "lambda_eventbridge" {
  name = "eventbridge-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = "arn:aws:events:*:*:event-bus/${var.event_bus_name}"
      }
    ]
  })
}

# IAM Policy for Lambda - SQS Access
resource "aws_iam_role_policy" "lambda_sqs" {
  name = "sqs-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.payment_queue_arn
      }
    ]
  })
}

# Attach AWS Managed Policy for VPC Execution
resource "aws_iam_role_policy_attachment" "lambda_vpc_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Attach AWS Managed Policy for Basic Execution (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Placeholder Lambda deployment package (will be replaced with actual code)
data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda_placeholder.zip"

  source {
    content  = <<-EOT
      def lambda_handler(event, context):
          return {
              'statusCode': 200,
              'body': 'Placeholder Lambda - Deploy actual code'
          }
    EOT
    filename = "lambda_function.py"
  }
}

# Lambda Function: Get Events
resource "aws_lambda_function" "get_events" {
  filename         = data.archive_file.lambda_placeholder.output_path
  function_name    = "${var.project_name}-get-events-${var.environment}"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "get_events_handler.lambda_handler"
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = {
      EVENTS_TABLE = var.events_table_name
    }
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-get-events-${var.environment}"
      Environment = var.environment
    }
  )
}

# Lambda Function: Get Seats
resource "aws_lambda_function" "get_seats" {
  filename         = data.archive_file.lambda_placeholder.output_path
  function_name    = "${var.project_name}-get-seats-${var.environment}"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "get_seats_handler.lambda_handler"
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = {
      SEATS_TABLE = var.seats_table_name
    }
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-get-seats-${var.environment}"
      Environment = var.environment
    }
  )
}

# Lambda Function: Reserve Seat (VPC disabled for minimal demo)
resource "aws_lambda_function" "reserve_seat" {
  filename         = data.archive_file.lambda_placeholder.output_path
  function_name    = "${var.project_name}-reserve-seat-${var.environment}"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "reserve_seat_handler.lambda_handler"
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256
  runtime          = "python3.11"
  timeout          = 60

  # VPC config commented out for minimal demo (no Redis)
  # vpc_config {
  #   subnet_ids         = var.subnet_ids
  #   security_group_ids = [aws_security_group.lambda.id]
  # }

  environment {
    variables = {
      SEATS_TABLE    = var.seats_table_name
      REDIS_ENDPOINT = var.redis_endpoint
      REDIS_PORT     = tostring(var.redis_port)
      EVENT_BUS_NAME = var.event_bus_name
    }
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-reserve-seat-${var.environment}"
      Environment = var.environment
    }
  )
}

# Lambda Function: Payment Handler (triggered by SQS)
resource "aws_lambda_function" "payment_handler" {
  filename         = data.archive_file.lambda_placeholder.output_path
  function_name    = "${var.project_name}-payment-handler-${var.environment}"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "payment_handler.lambda_handler"
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256
  runtime          = "python3.11"
  timeout          = 60

  environment {
    variables = {
      SEATS_TABLE    = var.seats_table_name
      BOOKINGS_TABLE = var.bookings_table_name
    }
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-payment-handler-${var.environment}"
      Environment = var.environment
    }
  )
}

# SQS Event Source Mapping for Payment Handler
resource "aws_lambda_event_source_mapping" "payment_queue_trigger" {
  event_source_arn = var.payment_queue_arn
  function_name    = aws_lambda_function.payment_handler.arn
  batch_size       = 10
  enabled          = true
}
