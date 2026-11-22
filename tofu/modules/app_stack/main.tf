terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}

# Fetch latest Amazon Linux 2023 AMI dynamically
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# ----------------------------------------------------------------------
# 1. S3 Bucket for Model Artifacts and Datasets
# ----------------------------------------------------------------------
resource "aws_s3_bucket" "artifacts" {
  # checkov:skip=CKV_AWS_18: "Access logging requires dedicated target bucket incurring additional storage and PUT request fees outside Free Tier."
  # checkov:skip=CKV_AWS_144: "Cross-region replication incurs inter-region transfer and duplicate storage fees outside Free Tier."
  # checkov:skip=CKV2_AWS_62: "S3 event notifications not required for model artifact storage."
  # checkov:skip=CKV_AWS_145: "AES-256 standard server-side encryption is enforced. KMS Customer Managed Key incurs $1.00/month charges outside Free Tier."
  bucket        = "${var.app_name}-artifacts-${var.environment}-${data.aws_caller_identity.current.account_id}"
  force_destroy = false

  tags = {
    Name        = "${var.app_name}-artifacts-${var.environment}"
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "OpenTofu"
  }
}

resource "aws_s3_bucket_versioning" "artifacts_versioning" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts_crypto" {
  # checkov:skip=CKV_AWS_145: "AES-256 standard server-side encryption is enforced. KMS Customer Managed Key incurs $1.00/month charges."
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts_public_block" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Lifecycle Configuration (Satisfies CKV2_AWS_61 and prevents storage bloat)
resource "aws_s3_bucket_lifecycle_configuration" "artifacts_lifecycle" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# ----------------------------------------------------------------------
# 2. Security Group (DevSecOps: Port 22 SSH Removed, Restricted Egress)
# ----------------------------------------------------------------------
resource "aws_security_group" "app_sg" {
  # checkov:skip=CKV2_AWS_5: "Security group is attached to aws_ec2_instance.app_server via vpc_security_group_ids."
  name        = "${var.app_name}-${var.environment}-sg"
  description = "Security group for ${var.app_name} (${var.environment}) - SSM access only, no open SSH"

  # Public Inference API Endpoint (Demo/Free Tier Architecture)
  # Architectural Note: Under strict $0.00 AWS Free Tier constraints, an Application Load Balancer
  # ($16+/mo) and Route 53 domain are omitted. In a funded production environment, this EC2 instance
  # resides in a private subnet behind an ALB with ACM TLS termination (port 443) and AWS WAF, with
  # ingress restricted solely to the ALB's security group.
  ingress {
    description = "FastAPI Inference Port (Demo HTTP - Production uses ALB with TLS)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress restricted to HTTPS (AWS APIs, SSM, CloudWatch, Docker) and HTTP (OS updates)
  egress {
    description = "Allow outbound HTTPS for AWS services and Docker Registry"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow outbound HTTP for Amazon Linux package updates"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-sg"
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "OpenTofu"
  }
}

# ----------------------------------------------------------------------
# 3. IAM Role & Profile (Least Privilege with SSM and CloudWatch)
# ----------------------------------------------------------------------
resource "aws_iam_role" "ec2_role" {
  name = "${var.app_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "OpenTofu"
  }
}

resource "aws_iam_role_policy_attachment" "ssm_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_policy" "s3_artifacts_policy" {
  name        = "${var.app_name}-${var.environment}-s3-artifacts"
  description = "Scoped S3 access for ${var.app_name} model artifacts"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_artifacts_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_artifacts_policy.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.app_name}-${var.environment}-profile"
  role = aws_iam_role.ec2_role.name
}

# ----------------------------------------------------------------------
# 4. CloudWatch Log Group
# ----------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "app_logs" {
  # checkov:skip=CKV_AWS_158: "KMS Customer Managed Key incurs $1.00/month charge outside Free Tier. CloudWatch default AWS-managed encryption is active."
  # checkov:skip=CKV_AWS_338: "Retaining logs for 365 days exceeds AWS Free Tier 5GB log storage. 7-day retention enforced for Free Tier cost guardrail."
  name              = "/aws/ec2/${var.app_name}-${var.environment}"
  retention_in_days = 7 # Cost-effective: keeps log storage well within Free Tier

  tags = {
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "OpenTofu"
  }
}

# ----------------------------------------------------------------------
# 5. EC2 Instance (Hardened with IMDSv2 and Encrypted EBS)
# ----------------------------------------------------------------------
resource "aws_ec2_instance" "app_server" {
  ami                  = data.aws_ssm_parameter.al2023_ami.value
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  vpc_security_group_ids = [aws_security_group.app_sg.id]

  # Enforce IMDSv2 for DevSecOps best practice (prevents SSRF credential theft)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  # Encrypted gp3 root EBS volume
  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name        = "${var.app_name}-${var.environment}-root"
      Environment = var.environment
    }
  }

  user_data = templatefile("${path.module}/userdata.sh", {
    log_group_name = aws_cloudwatch_log_group.app_logs.name
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-server"
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "OpenTofu"
  }
}

# ----------------------------------------------------------------------
# 6. Observability: CloudWatch Metric Filters, Alarms & SNS Alerting
# ----------------------------------------------------------------------
resource "aws_sns_topic" "alerts" {
  name              = "${var.app_name}-${var.environment}-alerts"
  kms_master_key_id = "alias/aws/sns" # Free AWS-managed encryption satisfying CKV_AWS_26

  tags = {
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "OpenTofu"
  }
}

resource "aws_sns_topic_subscription" "email_sub" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Metric Filter 1: 5xx Server Errors from JSON logs
resource "aws_cloudwatch_log_metric_filter" "api_5xx" {
  name           = "${var.app_name}-${var.environment}-5xx-errors"
  log_group_name = aws_cloudwatch_log_group.app_logs.name
  pattern        = "{ $.status >= 500 }"

  metric_transformation {
    name          = "Api5xxErrors"
    namespace     = "HNHitPredictor/${var.environment}"
    value         = "1"
    default_value = "0"
  }
}

# Metric Filter 2: Health Check Failures
resource "aws_cloudwatch_log_metric_filter" "health_failure" {
  name           = "${var.app_name}-${var.environment}-health-failures"
  log_group_name = aws_cloudwatch_log_group.app_logs.name
  pattern        = "{ $.path = \"/health\" && $.status != 200 }"

  metric_transformation {
    name          = "HealthCheckFailures"
    namespace     = "HNHitPredictor/${var.environment}"
    value         = "1"
    default_value = "0"
  }
}

# Alarm 1: High CPU (> 80% for 10 min)
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.app_name}-${var.environment}-HighCPU"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Triggers when instance CPU utilization exceeds 80% for 10 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = aws_ec2_instance.app_server.id
  }
}

# Alarm 2: 5xx Error Rate (> 5 errors in 5 min)
resource "aws_cloudwatch_metric_alarm" "high_5xx" {
  alarm_name          = "${var.app_name}-${var.environment}-High5xxRate"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Api5xxErrors"
  namespace           = "HNHitPredictor/${var.environment}"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Triggers when API returns 5 or more 5xx errors in a 5-minute window"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

# Alarm 3: Health Check Failure (> 1 failure in 1 min)
resource "aws_cloudwatch_metric_alarm" "health_failed" {
  alarm_name          = "${var.app_name}-${var.environment}-HealthCheckFailing"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "HealthCheckFailures"
  namespace           = "HNHitPredictor/${var.environment}"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Triggers immediately if an endpoint health check fails"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

# ----------------------------------------------------------------------
# 7. CloudWatch Dashboard
# ----------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "app_dashboard" {
  dashboard_name = "${var.app_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", "InstanceId", aws_ec2_instance.app_server.id],
            ["CWAgent", "mem_used_percent", "InstanceId", aws_ec2_instance.app_server.id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Compute: CPU & Memory Utilization (%)"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["HNHitPredictor/${var.environment}", "Api5xxErrors"],
            ["HNHitPredictor/${var.environment}", "HealthCheckFailures"]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Reliability: 5xx Errors & Health Failures"
        }
      }
    ]
  })
}
