output "get_events_function_name" {
  description = "Name of the get_events Lambda function"
  value       = aws_lambda_function.get_events.function_name
}

output "get_events_function_arn" {
  description = "ARN of the get_events Lambda function"
  value       = aws_lambda_function.get_events.arn
}

output "get_events_invoke_arn" {
  description = "Invoke ARN of the get_events Lambda function"
  value       = aws_lambda_function.get_events.invoke_arn
}

output "get_seats_function_name" {
  description = "Name of the get_seats Lambda function"
  value       = aws_lambda_function.get_seats.function_name
}

output "get_seats_function_arn" {
  description = "ARN of the get_seats Lambda function"
  value       = aws_lambda_function.get_seats.arn
}

output "get_seats_invoke_arn" {
  description = "Invoke ARN of the get_seats Lambda function"
  value       = aws_lambda_function.get_seats.invoke_arn
}

output "reserve_seat_function_name" {
  description = "Name of the reserve_seat Lambda function"
  value       = aws_lambda_function.reserve_seat.function_name
}

output "reserve_seat_function_arn" {
  description = "ARN of the reserve_seat Lambda function"
  value       = aws_lambda_function.reserve_seat.arn
}

output "reserve_seat_invoke_arn" {
  description = "Invoke ARN of the reserve_seat Lambda function"
  value       = aws_lambda_function.reserve_seat.invoke_arn
}

output "payment_handler_function_name" {
  description = "Name of the payment_handler Lambda function"
  value       = aws_lambda_function.payment_handler.function_name
}

output "payment_handler_function_arn" {
  description = "ARN of the payment_handler Lambda function"
  value       = aws_lambda_function.payment_handler.arn
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  value       = aws_security_group.lambda.id
}
