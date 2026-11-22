variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "AWS Region"
}

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type"
}

variable "root_volume_size" {
  type        = number
  default     = 20
  description = "Root EBS volume size in GB"
}

variable "alert_email" {
  type        = string
  default     = ""
  description = "Optional alert email address"
}
