output "api_endpoint" {
  description = "Base URL for the API Gateway"
  value       = aws_apigatewayv2_api.ticketing_api.api_endpoint
}

output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_apigatewayv2_api.ticketing_api.id
}

output "api_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_apigatewayv2_api.ticketing_api.execution_arn
}
