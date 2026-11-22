variable "environment" {
  type        = string
  description = "Deployment environment (staging or prod)"
}

variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "AWS Region"
}

variable "app_name" {
  type        = string
  default     = "hn-hit-predictor"
  description = "Base application name"
}

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type (Free Tier eligible: t3.micro)"
}

variable "root_volume_size" {
  type        = number
  default     = 20
  description = "Root EBS volume size in GB (Free tier allows up to 30 GB)"
}

variable "alert_email" {
  type        = string
  default     = ""
  description = "Optional email address for CloudWatch alarm notifications via SNS"
}
