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

variable "vpc_id" {
  description = "VPC ID where Lambda functions will run (optional for demo)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "List of subnet IDs for Lambda VPC config (optional for demo)"
  type        = list(string)
  default     = []
}

variable "redis_security_group_id" {
  description = "Security group ID for Redis cluster (optional for demo)"
  type        = string
  default     = ""
}

variable "redis_endpoint" {
  description = "Redis cluster endpoint"
  type        = string
}

variable "redis_port" {
  description = "Redis cluster port"
  type        = number
}

variable "events_table_name" {
  description = "DynamoDB events table name"
  type        = string
}

variable "seats_table_name" {
  description = "DynamoDB seats table name"
  type        = string
}

variable "bookings_table_name" {
  description = "DynamoDB bookings table name"
  type        = string
}

variable "events_table_arn" {
  description = "DynamoDB events table ARN"
  type        = string
}

variable "seats_table_arn" {
  description = "DynamoDB seats table ARN"
  type        = string
}

variable "bookings_table_arn" {
  description = "DynamoDB bookings table ARN"
  type        = string
}

variable "event_bus_name" {
  description = "EventBridge event bus name"
  type        = string
}

variable "payment_queue_url" {
  description = "SQS payment queue URL"
  type        = string
}

variable "payment_queue_arn" {
  description = "SQS payment queue ARN"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
