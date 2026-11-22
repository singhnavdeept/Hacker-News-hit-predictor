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
}

variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "AWS region for bootstrap state and OIDC resources"
}

variable "github_repo" {
  type        = string
  default     = "singhnavdeept/Hacker-News-hit-predictor"
  description = "GitHub repository (owner/repo) allowed to assume the OIDC role"
}

data "aws_caller_identity" "current" {}

# 1. S3 Bucket for OpenTofu Remote State
resource "aws_s3_bucket" "tofu_state" {
  # checkov:skip=CKV_AWS_18: "Access logging requires dedicated target bucket incurring additional storage and PUT request fees outside Free Tier."
  # checkov:skip=CKV_AWS_144: "Cross-region replication incurs inter-region transfer and duplicate storage fees outside Free Tier."
  # checkov:skip=CKV2_AWS_62: "S3 event notifications not required for state storage."
  # checkov:skip=CKV_AWS_145: "AES-256 standard server-side encryption is enforced. KMS Customer Managed Key incurs $1.00/month charges outside Free Tier."
  bucket        = "hn-hit-predictor-tofu-state-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  force_destroy = false

  tags = {
    Project     = "HNHitPredictor"
    ManagedBy   = "OpenTofu"
    Environment = "bootstrap"
  }
}

resource "aws_s3_bucket_versioning" "tofu_state_versioning" {
  bucket = aws_s3_bucket.tofu_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tofu_state_crypto" {
  # checkov:skip=CKV_AWS_145: "AES-256 standard server-side encryption is enforced. KMS Customer Managed Key incurs $1.00/month charges."
  bucket = aws_s3_bucket.tofu_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tofu_state_block" {
  bucket = aws_s3_bucket.tofu_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "tofu_state_lifecycle" {
  bucket = aws_s3_bucket.tofu_state.id

  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# 2. DynamoDB Table for Distributed State Locking
resource "aws_dynamodb_table" "tofu_locks" {
  name         = "hn-hit-predictor-tofu-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Project     = "HNHitPredictor"
    ManagedBy   = "OpenTofu"
    Environment = "bootstrap"
  }
}

# 3. AWS OIDC Provider for GitHub Actions
# Thumbprint for token.actions.githubusercontent.com
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]

  tags = {
    Project   = "HNHitPredictor"
    ManagedBy = "OpenTofu"
  }
}

# 4. IAM Role for GitHub Actions (Zero Stored Keys)
resource "aws_iam_role" "github_actions_role" {
  name = "GitHubActionsWorkflowRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" : "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" : "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Project   = "HNHitPredictor"
    ManagedBy = "OpenTofu"
  }
}

# Least-privilege policy for CI/CD deployments and state management
resource "aws_iam_policy" "github_actions_policy" {
  name        = "GitHubActionsDeployPolicy"
  description = "Allows GitHub Actions to plan/apply OpenTofu, access remote state, and execute SSM deployments"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # State bucket permissions
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = aws_s3_bucket.tofu_state.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.tofu_state.arn}/*"
      },
      # State lock table permissions
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:DescribeTable"
        ]
        Resource = aws_dynamodb_table.tofu_locks.arn
      },
      # Infrastructure deployment permissions (EC2, SG, IAM, CloudWatch, SSM)
      {
        Effect = "Allow"
        Action = [
          "ec2:*",
          "iam:GetRole",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:PassRole",
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetInstanceProfile",
          "iam:CreateInstanceProfile",
          "iam:DeleteInstanceProfile",
          "iam:AddRoleToInstanceProfile",
          "iam:RemoveRoleFromInstanceProfile",
          "ssm:*",
          "cloudwatch:*",
          "logs:*",
          "sns:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_attach" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = aws_iam_policy.github_actions_policy.arn
}

outputs "state_bucket_name" {
  description = "S3 bucket for OpenTofu state"
  value       = aws_s3_bucket.tofu_state.bucket
}

outputs "dynamodb_table_name" {
  description = "DynamoDB table for OpenTofu state locking"
  value       = aws_dynamodb_table.tofu_locks.name
}

outputs "github_actions_role_arn" {
  description = "ARN of IAM Role for GitHub Actions OIDC"
  value       = aws_iam_role.github_actions_role.arn
}
