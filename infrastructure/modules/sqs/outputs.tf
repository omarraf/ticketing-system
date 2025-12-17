output "payment_queue_url" {
  description = "URL of the payment processing queue"
  value       = aws_sqs_queue.payment_queue.url
}

output "payment_queue_arn" {
  description = "ARN of the payment processing queue"
  value       = aws_sqs_queue.payment_queue.arn
}

output "payment_queue_name" {
  description = "Name of the payment processing queue"
  value       = aws_sqs_queue.payment_queue.name
}

output "payment_dlq_url" {
  description = "URL of the payment processing dead letter queue"
  value       = aws_sqs_queue.payment_dlq.url
}

output "payment_dlq_arn" {
  description = "ARN of the payment processing dead letter queue"
  value       = aws_sqs_queue.payment_dlq.arn
}
