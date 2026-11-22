output "instance_id" {
  description = "Staging EC2 Instance ID"
  value       = module.app_stack.instance_id
}

output "public_ip" {
  description = "Staging EC2 Public IP"
  value       = module.app_stack.public_ip
}

output "api_url" {
  description = "Staging API URL"
  value       = module.app_stack.api_url
}

output "version_url" {
  description = "Staging Version Endpoint URL"
  value       = module.app_stack.version_url
}

output "log_group_name" {
  description = "Staging CloudWatch Log Group"
  value       = module.app_stack.log_group_name
}

output "artifacts_bucket_name" {
  description = "Staging Artifacts S3 Bucket"
  value       = module.app_stack.artifacts_bucket_name
}

output "sns_topic_arn" {
  description = "Staging SNS Topic ARN"
  value       = module.app_stack.sns_topic_arn
}

output "dashboard_name" {
  description = "Staging CloudWatch Dashboard"
  value       = module.app_stack.dashboard_name
}
