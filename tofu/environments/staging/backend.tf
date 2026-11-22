# Remote State Configuration for Staging
# In CI/CD or local runs:
# tofu init -backend-config="bucket=<STATE_BUCKET_NAME>" \
#            -backend-config="key=envs/staging/tofu.tfstate" \
#            -backend-config="region=ap-south-1" \
#            -backend-config="dynamodb_table=hn-hit-predictor-tofu-locks"
terraform {
  backend "s3" {
    key            = "envs/staging/tofu.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "hn-hit-predictor-tofu-locks"
    encrypt        = true
  }
}
