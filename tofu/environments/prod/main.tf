terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "HNHitPredictor"
      Environment = "prod"
      ManagedBy   = "OpenTofu"
    }
  }
}

# AWS Billing metrics are strictly collected in us-east-1
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

module "app_stack" {
  source = "../../modules/app_stack"

  environment      = "prod"
  aws_region       = var.aws_region
  instance_type    = var.instance_type
  root_volume_size = var.root_volume_size
  alert_email      = var.alert_email
}

# Billing Alarm (Alerts when estimated charges cross $1.00 USD)
resource "aws_cloudwatch_metric_alarm" "billing_alarm" {
  provider            = aws.us_east_1
  alarm_name          = "HNHitPredictor-prod-BillingAlert"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours
  statistic           = "Maximum"
  threshold           = 1.0 # $1.00 USD Free-tier protection
  alarm_description   = "Triggers if estimated monthly AWS bill exceeds 1.00 USD"
  alarm_actions       = [module.app_stack.sns_topic_arn]

  dimensions = {
    Currency = "USD"
  }
}
