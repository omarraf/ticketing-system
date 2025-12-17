output "events_table_name" {
  description = "Name of the Events DynamoDB table"
  value       = aws_dynamodb_table.events.name
}

output "events_table_arn" {
  description = "ARN of the Events DynamoDB table"
  value       = aws_dynamodb_table.events.arn
}

output "seats_table_name" {
  description = "Name of the Seats DynamoDB table"
  value       = aws_dynamodb_table.seats.name
}

output "seats_table_arn" {
  description = "ARN of the Seats DynamoDB table"
  value       = aws_dynamodb_table.seats.arn
}

output "bookings_table_name" {
  description = "Name of the Bookings DynamoDB table"
  value       = aws_dynamodb_table.bookings.name
}

output "bookings_table_arn" {
  description = "ARN of the Bookings DynamoDB table"
  value       = aws_dynamodb_table.bookings.arn
}
