output "event_bus_name" {
  description = "Name of the EventBridge event bus"
  value       = aws_cloudwatch_event_bus.ticketing.name
}

output "event_bus_arn" {
  description = "ARN of the EventBridge event bus"
  value       = aws_cloudwatch_event_bus.ticketing.arn
}

output "seat_reserved_rule_arn" {
  description = "ARN of the SeatReserved event rule"
  value       = aws_cloudwatch_event_rule.seat_reserved_to_payment_queue.arn
}
