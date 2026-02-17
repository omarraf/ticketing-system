output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "events_table_name" {
  description = "DynamoDB Events table name"
  value       = module.dynamodb.events_table_name
}

output "seats_table_name" {
  description = "DynamoDB Seats table name"
  value       = module.dynamodb.seats_table_name
}

output "bookings_table_name" {
  description = "DynamoDB Bookings table name"
  value       = module.dynamodb.bookings_table_name
}

# Redis outputs commented out for minimal demo
# output "redis_endpoint" {
#   description = "Redis cluster endpoint"
#   value       = module.redis.redis_endpoint
# }
#
# output "redis_port" {
#   description = "Redis cluster port"
#   value       = module.redis.redis_port
# }

output "event_bus_name" {
  description = "EventBridge event bus name"
  value       = module.eventbridge.event_bus_name
}

output "payment_queue_url" {
  description = "SQS payment queue URL"
  value       = module.sqs.payment_queue_url
}

output "payment_dlq_url" {
  description = "SQS payment DLQ URL"
  value       = module.sqs.payment_dlq_url
}

output "get_events_function_name" {
  description = "Get Events Lambda function name"
  value       = module.lambda.get_events_function_name
}

output "get_seats_function_name" {
  description = "Get Seats Lambda function name"
  value       = module.lambda.get_seats_function_name
}

output "reserve_seat_function_name" {
  description = "Reserve Seat Lambda function name"
  value       = module.lambda.reserve_seat_function_name
}

output "payment_handler_function_name" {
  description = "Payment Handler Lambda function name"
  value       = module.lambda.payment_handler_function_name
}
