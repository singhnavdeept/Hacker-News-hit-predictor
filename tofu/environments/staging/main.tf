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
      Environment = "staging"
      ManagedBy   = "OpenTofu"
    }
  }
}

module "app_stack" {
  source = "../../modules/app_stack"

  environment      = "staging"
  aws_region       = var.aws_region
  instance_type    = var.instance_type
  root_volume_size = var.root_volume_size
  alert_email      = var.alert_email
}
