# HN HIT Predictor: An MLOps Pipeline on AWS

**HN HIT Predictor** is an end-to-end Machine Learning Operations (MLOps) pipeline that predicts whether a Hacker News submission will become a "Hit" (gain significant traction, reach the front page, or score 50+ upvotes).

The project is designed to run seamlessly in **local Docker containers** for zero-cost development and testing, before deploying to **AWS Free Tier** using **CloudFormation**, **Jenkins**, and **CloudWatch**.

---

## 🏗️ Architecture Overview

```text
 ┌────────────────────────────────────────────────────────┐
 │                      Local / AWS                       │
 │                                                        │
 │   Hacker News Data ──► Data Loader & Feature Extractor │
 │                                   │                    │
 │                                   ▼                    │
 │                       Model Training Pipeline          │
 │                      (TF-IDF + ColumnTransformer       │
 │                        + Logistic Classifier)          │
 │                                   │                    │
 │                                   ▼                    │
 │                          Trained Artifacts             │
 │                      (model.joblib & metrics.json)     │
 │                                   │                    │
 │                                   ▼                    │
 │                          FastAPI Service               │
 │                   (GET /health, POST /predict)         │
 └───────────────────────────────────┬────────────────────┘
                                     │
           ┌─────────────────────────┴────────────────────────┐
           ▼                                                  ▼
┌───────────────────────┐                         ┌───────────────────────┐
│     CI/CD Pipeline    │                         │  AWS CloudFormation   │
│   (Jenkins in Docker) │                         │   & CloudWatch Logs   │
│ • Unit testing        │                         │ • EC2 t2.micro        │
│ • Container smoke test│                         │ • S3 Model Artifacts  │
│ • Auto-deployment     │                         │ • Latency/Error Alarms│
└───────────────────────┘                         └───────────────────────┘
```

---

## 🚀 Quickstart: Running Locally with Docker

### 1. Build and Run the Prediction API
```bash
# Build the Docker image
docker build -t hn-hit-predictor:latest -f docker/Dockerfile .

# Run the container
docker run -d --name hn-api -p 8000:8000 hn-hit-predictor:latest
```

### 2. Test the API Endpoints
Open your browser or run curl:
* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:**
```bash
curl http://localhost:8000/health
```

* **Make a Prediction:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Show HN: RustKV – High performance distributed cache in Rust",
    "url": "https://github.com/developer/rustkv",
    "submission_time": "2026-11-08T15:30:00Z"
  }'
```

Sample Response:
```json
{
  "title": "Show HN: RustKV – High performance distributed cache in Rust",
  "is_hit": true,
  "hit_probability": 0.8841,
  "confidence_level": "High",
  "prediction_label": "Likely Hit (Frontpage Material)",
  "features": {
    "title": "Show HN: RustKV – High performance distributed cache in Rust",
    "domain_type": "github",
    "submission_hour": 15,
    "submission_day": 6,
    "title_len": 58,
    "title_word_count": 8
  }
}
```

---

## 🛡️ DevSecOps Security Scanning

This project integrates automated security testing into both local development and the Jenkins CI/CD pipeline:

### 1. Infrastructure as Code (IaC) Security with Checkov
Scans `cloudformation/infra.yaml` for AWS security flaws and compliance issues:
```bash
docker run --rm -v "${PWD}:/work" bridgecrew/checkov:latest \
  -f /work/cloudformation/infra.yaml --framework cloudformation
```
* **Security Controls Applied:**
  * Strict SSH (port 22) and Jenkins (port 8080) CIDR restrictions (`CKV_AWS_24`).
  * Enforced default S3 AES-256 Server-Side Encryption (`CKV_AWS_19`).
  * S3 Public Access Block Configuration (`CKV_AWS_53` - `CKV_AWS_56`).
  * CloudWatch 7-day log retention to prevent unbounded disk growth.

### 2. Container Vulnerability Scanning with Aqua Trivy
Scans `hn-hit-predictor:latest` for operating system and application CVEs:
```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image --severity HIGH,CRITICAL hn-hit-predictor:latest
```

### 3. One-Click Security Audit Script
Run both scans simultaneously:
```powershell
.\scripts\security_scan.ps1
```

---

## 🧪 Running Automated Unit Tests
To run unit and model tests inside Docker:
```bash
docker run --rm hn-hit-predictor:latest pytest -v tests/
```

---

## 🛠️ Running Local Jenkins CI/CD
You can run the full environment including Jenkins using Docker Compose:
```bash
docker compose up -d
```
* **Jenkins UI:** [http://localhost:8080](http://localhost:8080)
* **FastAPI Service:** [http://localhost:8000](http://localhost:8000)

The declarative pipeline in [`Jenkinsfile`](./Jenkinsfile) automates:
1. Environment validation
2. Model testing & Pytest validation
3. Production Docker image packaging
4. Smoke testing the running container
5. Production rollout

---

## ☁️ Deploying to AWS (100% Free Tier)

The [`cloudformation/infra.yaml`](./cloudformation/infra.yaml) template sets up:
1. **EC2 Instance:** `t2.micro` or `t3.micro` (Within 750 free hours/month).
2. **S3 Bucket:** Private bucket for versioning model artifacts (Within 5 GB free tier).
3. **IAM Roles:** Grants EC2 permissions to push logs to CloudWatch and download model artifacts from S3.
4. **CloudWatch Log Group & Alarms:** Monitored CPU utilization and container logs.

To deploy via AWS CLI:
```bash
aws cloudformation create-stack \
  --stack-name hn-hit-predictor-stack \
  --template-body file://cloudformation/infra.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```
