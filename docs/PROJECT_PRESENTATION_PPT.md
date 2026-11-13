# HN HIT PREDICTOR
## An MLOps & DevSecOps Pipeline on AWS using CloudFormation, Jenkins & CloudWatch

**Presentation & Viva Slides Deck**  
* **Candidate:** Navdeep Singh (Reg No: 12308217 | Roll No: 43 | Section: K2O2313)  
* **Guide:** Arshiya (UID-29453)  
* **Institution:** School of Computer Science & Engineering, Lovely Professional University (LPU)

---

## SLIDE 1: Title & Introduction
* **Project Title:** HN HIT Predictor
* **Subtitle:** An End-to-End MLOps & DevSecOps Pipeline on AWS
* **Key Innovations:**
  * NLP & metadata-driven classification of Hacker News post virality.
  * 100% reproducible local environment using Docker & Docker Compose.
  * 7-Stage declarative Jenkins CI/CD pipeline with automated smoke testing.
  * Automated DevSecOps security gating (Checkov IaC & Aqua Trivy container scanner).
  * Zero-cost AWS Free Tier deployment via CloudFormation and CloudWatch.

---

## SLIDE 2: Problem Statement & Motivation
* **The Problem:**
  * Over 10,000 links submitted weekly to Hacker News; $<25\%$ make the front page.
  * Technical writers, indie hackers, and developers lack tools to optimize post timing and headline structure.
  * Traditional academic ML models stay trapped in notebooks without automated tests, deployment scripts, or security scans.
* **Our Solution:**
  * Build a production-grade inference service backed by automated CI/CD and cloud monitoring.

---

## SLIDE 3: System Architecture
```text
[HN Algolia API] ──► [Feature Pipeline] ──► [Classifier Training] ──► [model.joblib]
                                                                            │
   ┌────────────────────────────────────────────────────────────────────────┘
   ▼
[FastAPI REST API] ──► [Docker Container] ──► [Jenkins CI/CD] ──► [AWS Free Tier]
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
             [Checkov IaC Audit]                                           [Trivy Security Scan]
```

---

## SLIDE 4: Machine Learning Pipeline
* **Feature Engineering:**
  * **Title Text:** `TfidfVectorizer` (unigrams + bigrams, sublinear TF, 3000 max features).
  * **Source Domain:** Categorization (`github`, `tech_media`, `blogs`, `paper`, `self`).
  * **Timing Signals:** Submission hour (0–23 UTC) and day of the week (0–6).
  * **Length Signals:** Character and token length standard scaling.
* **Classifier Engine:**
  * Balanced `LogisticRegression` with L2 regularization.
  * Serialized size $<1\text{ MB}$, sub-millisecond inference time on micro-tier instances.

---

## SLIDE 5: API Microservice (FastAPI & Pydantic)
* **Endpoints:**
  * `GET /health` – Automated container health monitoring.
  * `GET /metrics` – Exposes latest model accuracy, F1, and ROC-AUC.
  * `POST /predict` – Live inference with probability scores and confidence indicators.
  * `GET /docs` – Auto-generated interactive Swagger UI.
* **Validation:** Strict Pydantic models for incoming JSON payloads with descriptive examples.

---

## SLIDE 6: Automated CI/CD (Jenkinsfile)
* **7-Stage Declarative Pipeline:**
  1. **Checkout & Lint:** Validates repository structure and dependency files.
  2. **DevSecOps IaC Scan:** Scans `cloudformation/infra.yaml` using **Checkov**.
  3. **Build & Test:** Runs 7 automated Pytest suites inside container.
  4. **Package Production Image:** Builds and tags `hn-hit-predictor:latest`.
  5. **DevSecOps Container Scan:** Scans image vulnerabilities with **Aqua Trivy**.
  6. **Integration Smoke Test:** Deploys container on ephemeral port and tests endpoints.
  7. **Production Rollout:** Zero-downtime deployment.

---

## SLIDE 7: DevSecOps Implementation & Results
* **Checkov (Infrastructure as Code):**
  * Audited CloudFormation template against CIS AWS benchmarks.
  * **Resolved Issues:** Restricted SSH/Jenkins port access, enforced S3 AES-256 encryption, blocked public ACLs.
  * **Result:** **24 Checks Passed!**
* **Aqua Trivy (Container Vulnerability Scanner):**
  * Scanned base OS packages and Python wheels.
  * Hardened base image using `python:3.11-slim` with patched runtime dependencies.

---

## SLIDE 8: AWS Free Tier Cloud Infrastructure
* **Provisioned via CloudFormation (`cloudformation/infra.yaml`):**
  * **Compute:** 1x EC2 `t2.micro` (750 free hours/month).
  * **Storage:** 1x Private Amazon S3 bucket for model backups (5 GB free tier).
  * **Security:** AWS IAM instance profile with least-privilege CloudWatch & S3 access.
  * **Monitoring:** Amazon CloudWatch Log Group with 7-day retention + High CPU Alarm.
* **Total Operating Cost:** **\$0.00 / month**.

---

## SLIDE 9: Live Demonstration & Results
* **Test Case A (High Virality):**
  * *Title:* `"Show HN: RustKV – High performance distributed cache in Rust"`
  * *Domain:* `github.com` | *Time:* `15:30 UTC`
  * *Result:* **Hit: True | Probability: 91.1% (High Confidence)**
* **Test Case B (Low Virality):**
  * *Title:* `"Top 5 Crypto trading signals for today"`
  * *Domain:* `external` | *Time:* `03:00 UTC`
  * *Result:* **Hit: False | Probability: 2.47% (Low Confidence)**

---

## SLIDE 10: Conclusion & Summary
* **Key Achievements:**
  * Successfully built a complete, production-grade MLOps & DevSecOps lifecycle.
  * 100% test pass rate with fully automated security validation.
  * Completely aligned with AWS Free Tier constraints for zero cloud spend.
* **GitHub Repository:**
  `https://github.com/singhnavdeept/Hacker-News-hit-predictor`
