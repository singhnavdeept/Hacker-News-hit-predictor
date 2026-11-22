output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_ec2_instance.app_server.id
}

output "public_ip" {
  description = "EC2 Public IPv4 address"
  value       = aws_ec2_instance.app_server.public_ip
}

output "api_url" {
  description = "FastAPI Public Endpoint URL"
  value       = "http://${aws_ec2_instance.app_server.public_ip}:8000"
}

output "version_url" {
  description = "FastAPI /version Endpoint URL"
  value       = "http://${aws_ec2_instance.app_server.public_ip}:8000/version"
}

output "log_group_name" {
  description = "CloudWatch Log Group Name"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "artifacts_bucket_name" {
  description = "S3 Bucket Name for Model Artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "sns_topic_arn" {
  description = "SNS Topic ARN for alert notifications"
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_name" {
  description = "CloudWatch Dashboard Name"
  value       = aws_cloudwatch_dashboard.app_dashboard.dashboard_name
}
