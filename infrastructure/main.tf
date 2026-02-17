terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# VPC data sources commented out - not needed for minimal demo without Redis
# data "aws_vpc" "default" {
#   default = true
# }
#
# data "aws_subnets" "default" {
#   filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.default.id]
#   }
# }

# Module: DynamoDB Tables
module "dynamodb" {
  source = "./modules/dynamodb"

  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
}

# Module: SQS Queues
module "sqs" {
  source = "./modules/sqs"

  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
}

# Module: EventBridge
module "eventbridge" {
  source = "./modules/eventbridge"

  environment       = var.environment
  project_name      = var.project_name
  payment_queue_arn = module.sqs.payment_queue_arn
  tags              = var.tags
}

# Module: Redis (ElastiCache) - COMMENTED OUT FOR MINIMAL DEMO
# Uncomment after demo to enable distributed locking with Redis
# module "redis" {
#   source = "./modules/redis"
#
#   environment                 = var.environment
#   project_name                = var.project_name
#   vpc_id                      = data.aws_vpc.default.id
#   subnet_ids                  = data.aws_subnets.default.ids
#   allowed_security_group_ids  = []
#   tags                        = var.tags
# }
#
# resource "aws_security_group_rule" "redis_from_lambda" {
#   type                     = "ingress"
#   from_port                = 6379
#   to_port                  = 6379
#   protocol                 = "tcp"
#   security_group_id        = module.redis.redis_security_group_id
#   source_security_group_id = module.lambda.lambda_security_group_id
#   description              = "Allow Redis access from Lambda"
# }

# Module: Lambda Functions (without VPC for minimal demo)
module "lambda" {
  source = "./modules/lambda"

  environment              = var.environment
  project_name             = var.project_name
  vpc_id                   = "" # No VPC needed for minimal demo
  subnet_ids               = [] # No subnets needed
  redis_security_group_id  = "" # No Redis for minimal demo
  redis_endpoint           = "localhost" # Placeholder
  redis_port               = 6379
  events_table_name        = module.dynamodb.events_table_name
  seats_table_name         = module.dynamodb.seats_table_name
  bookings_table_name      = module.dynamodb.bookings_table_name
  events_table_arn         = module.dynamodb.events_table_arn
  seats_table_arn          = module.dynamodb.seats_table_arn
  bookings_table_arn       = module.dynamodb.bookings_table_arn
  event_bus_name           = module.eventbridge.event_bus_name
  payment_queue_url        = module.sqs.payment_queue_url
  payment_queue_arn        = module.sqs.payment_queue_arn
  tags                     = var.tags
}

# Module: API Gateway
module "api_gateway" {
  source = "./modules/api_gateway"

  environment                 = var.environment
  project_name                = var.project_name
  get_events_invoke_arn       = module.lambda.get_events_invoke_arn
  get_events_function_name    = module.lambda.get_events_function_name
  get_seats_invoke_arn        = module.lambda.get_seats_invoke_arn
  get_seats_function_name     = module.lambda.get_seats_function_name
  reserve_seat_invoke_arn     = module.lambda.reserve_seat_invoke_arn
  reserve_seat_function_name  = module.lambda.reserve_seat_function_name
  tags                        = var.tags
}
