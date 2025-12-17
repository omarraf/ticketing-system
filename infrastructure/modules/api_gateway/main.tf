# HTTP API Gateway (simpler than REST API, perfect for Lambda proxy)
resource "aws_apigatewayv2_api" "ticketing_api" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
  description   = "HTTP API for ticketing system"

  cors_configuration {
    allow_origins = ["*"] # For MVP - restrict in production
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
    max_age       = 300
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-api-${var.environment}"
      Environment = var.environment
    }
  )
}

# Integration: GET /events -> get_events Lambda
resource "aws_apigatewayv2_integration" "get_events" {
  api_id           = aws_apigatewayv2_api.ticketing_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.get_events_invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Integration: GET /events/{event_id}/seats -> get_seats Lambda
resource "aws_apigatewayv2_integration" "get_seats" {
  api_id           = aws_apigatewayv2_api.ticketing_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.get_seats_invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Integration: POST /reserve -> reserve_seat Lambda
resource "aws_apigatewayv2_integration" "reserve_seat" {
  api_id           = aws_apigatewayv2_api.ticketing_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.reserve_seat_invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Route: GET /events
resource "aws_apigatewayv2_route" "get_events" {
  api_id    = aws_apigatewayv2_api.ticketing_api.id
  route_key = "GET /events"
  target    = "integrations/${aws_apigatewayv2_integration.get_events.id}"
}

# Route: GET /events/{event_id}/seats
resource "aws_apigatewayv2_route" "get_seats" {
  api_id    = aws_apigatewayv2_api.ticketing_api.id
  route_key = "GET /events/{event_id}/seats"
  target    = "integrations/${aws_apigatewayv2_integration.get_seats.id}"
}

# Route: POST /reserve
resource "aws_apigatewayv2_route" "reserve_seat" {
  api_id    = aws_apigatewayv2_api.ticketing_api.id
  route_key = "POST /reserve"
  target    = "integrations/${aws_apigatewayv2_integration.reserve_seat.id}"
}

# Stage: $default (auto-deploy)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.ticketing_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-api-stage-${var.environment}"
      Environment = var.environment
    }
  )
}

# CloudWatch Log Group for API Gateway logs
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-api-logs-${var.environment}"
      Environment = var.environment
    }
  )
}

# Lambda Permissions: Allow API Gateway to invoke Lambda functions
resource "aws_lambda_permission" "api_gateway_get_events" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.get_events_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ticketing_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_get_seats" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.get_seats_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ticketing_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_reserve_seat" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.reserve_seat_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ticketing_api.execution_arn}/*/*"
}
