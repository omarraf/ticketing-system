variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "ticketing-system"
}

variable "get_events_invoke_arn" {
  description = "Invoke ARN for get_events Lambda function"
  type        = string
}

variable "get_events_function_name" {
  description = "Name of get_events Lambda function"
  type        = string
}

variable "get_seats_invoke_arn" {
  description = "Invoke ARN for get_seats Lambda function"
  type        = string
}

variable "get_seats_function_name" {
  description = "Name of get_seats Lambda function"
  type        = string
}

variable "reserve_seat_invoke_arn" {
  description = "Invoke ARN for reserve_seat Lambda function"
  type        = string
}

variable "reserve_seat_function_name" {
  description = "Name of reserve_seat Lambda function"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
