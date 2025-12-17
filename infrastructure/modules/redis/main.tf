# Security Group for Redis
resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-${var.environment}-"
  description = "Security group for ElastiCache Redis cluster"
  vpc_id      = var.vpc_id

  # Allow inbound Redis traffic from Lambda (port 6379)
  ingress {
    description     = "Redis from Lambda"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
    self            = true # Allow Redis nodes to talk to each other
  }

  # Allow all outbound traffic
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-redis-sg-${var.environment}"
      Environment = var.environment
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# Subnet Group for Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_name}-redis-subnet-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-redis-subnet-${var.environment}"
      Environment = var.environment
    }
  )
}

# ElastiCache Redis Cluster (Single Node)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis-${var.environment}"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.node_type
  num_cache_nodes      = 1 # Single node for MVP
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  # Maintenance and backup settings
  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_retention_limit = 0 # No backups for MVP (saves cost)

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-redis-${var.environment}"
      Environment = var.environment
      Purpose     = "Distributed locking for seat reservations"
    }
  )
}