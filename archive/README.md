# 📦 Archived Legacy Infrastructure & Pipelines (v1)

This directory archives early v1 iterations of the project for historical and evolutionary context:

* **`archive/cloudformation/`**: Initial monolithic AWS provisioning template from v1. Superseded in v2 by modular **OpenTofu** (`tofu/`) with S3 remote state, DynamoDB locking, automated security controls, and environment separation (`staging`/`prod`).
* **`archive/Jenkinsfile`**: Early on-host CI/CD pipeline from v1. Decommissioned to conserve EC2 `t3.micro` memory (freed ~1 GB RAM, eliminating host OOM crashes) and replaced with cloud-native **GitHub Actions** using AWS OIDC federation (eliminating stored static AWS credentials and open SSH keys).
