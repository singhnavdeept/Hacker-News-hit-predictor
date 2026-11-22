# HN HIT Predictor: Production MLOps & DevSecOps Platform on AWS

[![CI/CD Pipeline](https://github.com/singhnavdeept/Hacker-News-hit-predictor/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/singhnavdeept/Hacker-News-hit-predictor/actions/workflows/ci-cd.yml)
[![OpenTofu](https://img.shields.io/badge/IaC-OpenTofu-blue.svg)](https://opentofu.org)
[![AWS OIDC](https://img.shields.io/badge/Security-AWS%20OIDC-green.svg)](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
[![DevSecOps](https://img.shields.io/badge/Scanners-Gitleaks%20|%20pip--audit%20|%20Checkov%20|%20Trivy-orange.svg)]()
[![Free Tier](https://img.shields.io/badge/Cost-%240.00%20(AWS%20Free%20Tier)-brightgreen.svg)]()

**HN HIT Predictor** is an enterprise-grade Machine Learning Operations (MLOps) and DevSecOps platform that predicts whether a Hacker News submission will reach the front page (50+ points).

Built to industry standards matching production engineering requirements:
* **Infrastructure as Code (IaC):** Modular **OpenTofu** with remote S3 backend, DynamoDB state locking, and separate `staging` / `prod` environments.
* **CI/CD with Zero Stored AWS Keys:** **GitHub Actions** authenticates to AWS via **OIDC (OpenID Connect)** federation.
* **4-Tier Shift-Left DevSecOps:** Automated scans for secrets (**Gitleaks**), Python dependencies (**pip-audit**), IaC misconfigurations (**Checkov**), and container vulnerabilities (**Aqua Trivy**) that fail on high-severity findings.
* **Deploy Verification & Fast Rollback:** Automated verification asserting the live `/version` Git SHA matches release, paired with a 1-click rollback workflow.
* **SRE Observability:** Structured JSON logs to CloudWatch, custom metric filters, high CPU / 5xx error alarms, AWS billing alarms, and SNS email notifications.
* **Zero-SSH Attack Surface:** Port 22 closed; host access strictly via **AWS Systems Manager (SSM) Session Manager** with **IMDSv2 enforced** and **encrypted gp3 EBS volumes**.

---

## 🏗️ End-to-End System Architecture

```mermaid
flowchart TD
    subgraph DEV["1. Developer & Git Workflow"]
        GIT["Developer commit & push"] --> GH["GitHub Repository\nsinghnavdeept/Hacker-News-hit-predictor"]
    end

    subgraph GHA["2. GitHub Actions CI/CD Pipeline"]
        OIDC["AWS OIDC Federation\n(Zero Stored AWS Keys)"]
        
        subgraph SCAN["4-Tier Security Scanning Gates (Fails on High/Crit)"]
            S1["1. Gitleaks\nSecrets Detection"]
            S2["2. pip-audit\nPyPI CVE Scan"]
            S3["3. Checkov\nOpenTofu IaC Scan"]
            S4["4. Aqua Trivy\nContainer CVE Scan"]
            S1 --> S2 --> S3 --> S4
        end

        TEST["5. Unit & ML Sanity Tests (pytest)"]
        BUILD["6. Docker Build (Bakes model & Git SHA)"]
        PLAN["7. OpenTofu Plan & Apply (Reviewed Plan)"]
        DEPLOY["8. Remote Deploy via AWS SSM Run Command"]
        VERIFY["9. Verify /version Endpoint == Git SHA"]
        
        OIDC --> SCAN --> TEST --> BUILD --> PLAN --> DEPLOY --> VERIFY
    end

    subgraph AWS["3. AWS Cloud (Free Tier - 0 USD)"]
        subgraph IAM_S["Identity & State"]
            ROLE["GitHubActionsWorkflowRole\n(OIDC scoped to repo)"]
            S3_STATE["S3 Bucket: tofu-state\n+ DynamoDB State Lock"]
        end

        subgraph VPC["VPC / Compute"]
            EC2["EC2 t3.micro (Amazon Linux 2023)\n- IMDSv2 Enforced\n- EBS gp3 Encrypted (20GB)\n- Port 22 CLOSED (SSM Session Manager only)\n- Port 8000 OPEN (FastAPI Inference)"]
            API_CONT["Docker Container: hn-hit-predictor\n- Structured JSON Logging\n- /health, /version, /predict, /metrics"]
        end

        subgraph OBS["CloudWatch Observability & Alerting"]
            CWL["CloudWatch Logs Group\n(/aws/ec2/hn-hit-predictor-prod)"]
            METRIC_FILTER["Metric Filter: 5xx Errors & Health Failures"]
            DASH["CloudWatch Metric Dashboard"]
            ALARM1["High CPU Alarm (>80%)"]
            ALARM2["5xx Error Rate Alarm"]
            ALARM3["AWS Billing Alarm (>1.00 USD)"]
            SNS["Amazon SNS Topic\nEmail Alerts to Developer"]
        end
    end

    GH --> GHA
    GHA -->|"Assumes Role via OIDC"| ROLE
    GHA -->|"Locks & Reads State"| S3_STATE
    VERIFY -->|"Queries http://EC2:8000/version"| API_CONT
    API_CONT -->|"Streams JSON Logs"| CWL
    CWL --> METRIC_FILTER --> ALARM2
    EC2 --> ALARM1
    ALARM1 & ALARM2 & ALARM3 --> SNS
```

---

## 🔒 Security Posture & DevSecOps Compliance

| Security Dimension | Implementation | Standard / Benefit |
|---|---|---|
| **Cloud Authentication** | AWS IAM OIDC Provider | Zero static access keys; short-lived STS tokens |
| **Host Access** | AWS Systems Manager (SSM) | Port 22 (SSH) is completely closed to the internet |
| **Metadata Protection** | IMDSv2 Strictly Enforced | Mitigates Server-Side Request Forgery (SSRF) credential theft |
| **Data at Rest** | AES-256 (S3) & KMS/AES (EBS gp3) | Full disk and object storage encryption |
| **Secrets in Code** | Gitleaks in CI | Blocks commits containing API keys, AWS tokens, or passwords |
| **Dependency Security** | `pip-audit` in CI | Halts builds if Python dependencies have published CVEs |
| **IaC Compliance** | Checkov in CI | Validates OpenTofu against CIS AWS Foundations Benchmark |
| **Image Hardening** | Aqua Trivy in CI | Scans container layers and fails on unfixed High/Critical CVEs |

---

## 🚀 API Endpoints

Once deployed on EC2 (or run locally on port 8000):

* **Web UI Dashboard:** `GET /` — Interactive dark-themed Hacker News UI.
* **Health Check:** `GET /health` — Liveness & readiness probe.
* **Deployment Verification:** `GET /version` — Returns active Git commit SHA, environment, and build metadata.
* **Real-Time Prediction:** `POST /predict` — Analyzes submission title, domain category, and timing.
* **Operational Metrics:** `GET /metrics` — Precision, recall, F1, and AUC statistics.
* **Interactive Swagger UI:** `GET /docs` — Live API documentation and testing interface.

### Sample Prediction Request:
```bash
curl -X POST http://<EC2_IP>:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Show HN: FastKV – High Performance Key-Value Store in Rust",
    "url": "https://github.com/developer/fastkv",
    "submission_time": "2026-11-22T15:30:00Z"
  }'
```

### Sample Prediction Response:
```json
{
  "title": "Show HN: FastKV – High Performance Key-Value Store in Rust",
  "is_hit": true,
  "hit_probability": 0.8421,
  "confidence_level": "High",
  "prediction_label": "Likely Hit (Frontpage Material)",
  "features": {
    "title": "Show HN: FastKV – High Performance Key-Value Store in Rust",
    "domain_type": "github",
    "submission_hour": 15,
    "submission_day": 6,
    "title_len": 58,
    "title_word_count": 9
  }
}
```

---

## 🛠️ Infrastructure Management with OpenTofu

### 1. One-Time Bootstrap (State Bucket & DynamoDB Lock)
```bash
cd tofu/bootstrap
tofu init
tofu plan -out=tfplan
tofu apply tfplan
```

### 2. Deploy Staging or Production
```bash
cd tofu/environments/prod
tofu init
tofu plan -out=tfplan
tofu apply tfplan
```

### 3. Clean Teardown (Zero Cost After Testing)
```bash
cd tofu/environments/prod
tofu destroy -auto-approve

cd ../../bootstrap
tofu destroy -auto-approve
```

---

## 📚 Complete Project Documentation

* 📖 **[Operational Runbook](docs/OPERATIONAL_RUNBOOK.md):** Step-by-step incident response, alarm troubleshooting, and 1-click rollback guide.
* 📋 **[Production Upgrade Plan](docs/PRODUCTION_UPGRADE_PLAN.md):** Full JD alignment, cost analysis, and architectural design specification.
* 🎓 **[Viva & Technical Question Bank](docs/VIVA_QUESTIONS.md):** 100 comprehensive questions covering MLOps, Docker, AWS, OpenTofu, and DevSecOps.
* 📘 **[Complete Learning Guide](docs/LEARNING_GUIDE.md):** In-depth technical reference explaining every architectural decision and component.
