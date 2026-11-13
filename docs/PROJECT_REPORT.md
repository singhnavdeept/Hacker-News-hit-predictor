# PROJECT REPORT: HN HIT PREDICTOR
## An End-to-End MLOps & DevSecOps Pipeline on AWS using CloudFormation, Jenkins, and CloudWatch

**Academic Submission & Capstone Project**  
* **Student Name:** Navdeep Singh  
* **Registration Number:** 12308217  
* **Roll Number:** 43  
* **Section:** K2O2313  
* **Supervisor / Guide:** Arshiya (UID-29453)  
* **Institution:** School of Computer Science & Engineering, Lovely Professional University (LPU)  
* **Repository:** [https://github.com/singhnavdeept/Hacker-News-hit-predictor](https://github.com/singhnavdeept/Hacker-News-hit-predictor)

---

## EXECUTIVE SUMMARY

Machine Learning systems in modern enterprise environments require rigorous engineering beyond model training—namely continuous integration, automated testing, containerized packaging, automated security auditing (DevSecOps), infrastructure as code (IaC), and continuous monitoring. 

The **HN HIT Predictor** project implements a production-grade, end-to-end MLOps and DevSecOps system designed to predict whether a Hacker News story submission will become a "Hit" (defined as gaining major traction, frontpage placement, and reaching $\ge 50$ community upvotes) based on natural language title features, submission timing, and domain taxonomy.

The entire solution is architected with dual-environment parity:
1. **Local Development Simulation:** Fully reproducible on local machines using Docker, Docker Compose, and local Jenkins, incurring \$0 cost.
2. **Cloud Deployment (AWS Free Tier):** Provisioned via declarative AWS CloudFormation, utilizing EC2 (`t2.micro`/`t3.micro`), Amazon S3, Amazon CloudWatch Logs and Alarms, and least-privilege IAM roles.

---

## 1. PROBLEM STATEMENT & OBJECTIVES

### 1.1 Problem Statement
Content discovery platforms like Hacker News (Y Combinator) experience thousands of technical submissions daily. However, less than 25% of submissions gain frontpage traction or community visibility. Creators, engineering teams, and technical writers struggle to identify whether their headline, target submission timing (hour of the day, day of the week), and content source domain will resonate with the technical community before publishing.

Furthermore, academic machine learning projects frequently suffer from the "works on my machine" syndrome, where models remain isolated inside Jupyter notebooks without automated deployment pipelines, continuous testing, vulnerability assessments, or cloud monitoring.

### 1.2 Objectives
1. **Model Engineering:** Design and train a lightweight, interpretable classification pipeline using TF-IDF n-grams, categorical domain encoders, and temporal feature scalers to classify post virality.
2. **Inference Microservice:** Build a robust, low-latency REST API using FastAPI and Pydantic with strict schema validation and interactive OpenAPI/Swagger documentation.
3. **Containerization & Reproducibility:** Containerize the entire Python serving stack using lightweight, multi-stage Docker configurations (`python:3.11-slim`).
4. **CI/CD Automation with Jenkins:** Implement a 7-stage declarative Jenkins pipeline (`Jenkinsfile`) handling code checkout, linting, model testing (`pytest`), container packaging, integration smoke tests, and deployment.
5. **DevSecOps Integration:** Embed Static Application Security Testing (SAST), Software Composition Analysis (SCA), Infrastructure as Code security scanning (Checkov), and container vulnerability scanning (Aqua Trivy).
6. **Infrastructure as Code (IaC) & Cloud Operations:** Provision a 100% AWS Free Tier infrastructure using AWS CloudFormation, integrating Amazon CloudWatch for metrics collection and automated threshold alarms.

---

## 2. TOOLS, TECHNOLOGIES & SYSTEM ARCHITECTURE

| Layer | Tools / Technologies | Purpose & Role |
| :--- | :--- | :--- |
| **Language & Core ML** | Python 3.11, Scikit-Learn, Pandas, NumPy, Joblib | Data ingestion, TF-IDF NLP feature extraction, classifier modeling, artifact serialization |
| **Serving Framework** | FastAPI, Uvicorn, Pydantic | High-performance ASGI REST API with automatic docs (`/docs`), `/health`, `/metrics`, and `/predict` |
| **Testing** | Pytest, HTTPX | Automated unit tests, API schema tests, and model probability distribution checks |
| **Containerization** | Docker, Docker Compose | Immutable, isolated application runtime and local Jenkins controller orchestration |
| **Continuous Integration** | Jenkins (Declarative Pipeline) | 7-stage automated build, test, security gate, smoke test, and delivery pipeline |
| **IaC Security** | Checkov (Bridgecrew / Prisma Cloud) | Static security analysis of CloudFormation templates against CIS AWS Foundations |
| **Container Security** | Aqua Trivy | CVE scanner for operating system packages and third-party Python dependencies |
| **Version Control** | Git & GitHub | Distributed version control, branch management, and remote code collaboration |
| **Cloud Infrastructure** | AWS CloudFormation | Declarative, repeatable provisioning of AWS EC2, S3, IAM, and Security Groups |
| **Cloud Monitoring** | AWS CloudWatch | System metrics (CPU, Memory, Disk), container log collection, and CloudWatch Alarms |

### 2.1 Architectural Flow Diagram

```text
+---------------------------------------------------------------------------------------------------+
|                                      LOCAL DEVELOPMENT & TESTING                                  |
|                                                                                                   |
|  [Hacker News Algolia API]                                                                        |
|             |                                                                                     |
|             v                                                                                     |
|    src/data_loader.py  ===>  src/train.py  ===>  models/model.joblib & metrics.json               |
|                                                         |                                         |
|                                                         v                                         |
|    tests/test_model.py & test_api.py  <===  app/main.py (FastAPI REST Service)                    |
+---------------------------------------------------------+-----------------------------------------+
                                                          |
                                                          v
+---------------------------------------------------------------------------------------------------+
|                                      AUTOMATED CI/CD & DEVSECOPS                                  |
|                                                                                                   |
|                                        [ Jenkins Pipeline ]                                       |
|                                                 |                                                 |
|  Stage 1: Checkout & Structure Validation       v                                                 |
|  Stage 2: DevSecOps - IaC Security (Checkov)    v  --> Audits cloudformation/infra.yaml           |
|  Stage 3: Pytest & ML Sanity Verification      v  --> Runs 7/7 tests inside test container       |
|  Stage 4: Production Image Packaging           v  --> Tags hn-hit-predictor:latest               |
|  Stage 5: DevSecOps - Container Scan (Trivy)    v  --> Scans image for CVEs and security flaws    |
|  Stage 6: Integration Smoke Test               v  --> Probes /health and /predict endpoints       |
|  Stage 7: Production Deployment Rollout        v  --> Deploys hardened container                  |
+---------------------------------------------------------+-----------------------------------------+
                                                          |
                                                          v
+---------------------------------------------------------------------------------------------------+
|                                      AWS FREE TIER DEPLOYMENT                                     |
|                                                                                                   |
|                              [ AWS CloudFormation: infra.yaml ]                                   |
|                                                 |                                                 |
|        +----------------------------------------+---------------------------------------+         |
|        |                                        |                                       |         |
|        v                                        v                                       v         |
|  [ Amazon EC2 ]                          [ Amazon S3 ]                       [ AWS CloudWatch ]   |
|  • Instance: t2.micro / t3.micro         • Bucket: Model artifacts backup    • Log Group: /aws/ec2|
|  • Security Group: 8000 (API),           • AES-256 Server-Side Encryption    • High CPU Alarm     |
|    Restricted 22 & 8080 (Admin CIDR)     • Versioning Enabled                • Memory/Disk metrics|
+---------------------------------------------------------------------------------------------------+
```

---

## 3. METHODOLOGY & IMPLEMENTATION

### 3.1 Data Acquisition & Feature Engineering
* **Data Ingestion (`src/data_loader.py`):** Integrates directly with the official Hacker News Algolia REST API (`https://hn.algolia.com/api/v1/search`) to retrieve real stories. For offline/air-gapped builds, it includes a deterministic benchmark generator modeling viral vs. low-traction submissions.
* **Feature Engineering:**
  1. **Title NLP Vectorization:** Scikit-Learn `TfidfVectorizer` extracting unigrams and bigrams (max 3,000 features, sublinear term frequency, English stop-word removal).
  2. **Domain Categorization:** Custom URL parser categorizing links into `github`, `tech_media`, `blogs`, `paper`, `self` (Ask HN/Show HN text posts), and `external`.
  3. **Temporal Features:** Extraction of submission hour (0–23 UTC) and day of the week (0–6).
  4. **Text Characteristics:** Character length and token/word count scaled using `StandardScaler`.
* **Label Formulation:** Binary classification where `is_hit = 1` if community upvotes $\ge 50$, and `0` otherwise.

### 3.2 Machine Learning Model (`src/train.py`)
* The complete workflow is encapsulated in an end-to-end `Pipeline` using `ColumnTransformer` to prevent data leakage during train/test splits.
* The classification engine utilizes a balanced, L2-regularized `LogisticRegression` model.
* **Advantages for Cloud Free Tier:**
  * Sub-millisecond inference time.
  * Serialized model artifact size is $< 1\text{ MB}$, saving storage and memory overhead.
  * Produces well-calibrated posterior probabilities ($0.0 \le P(\text{Hit}) \le 1.0$).

### 3.3 Inference API Microservice (`app/main.py`)
* Implemented using **FastAPI** with asynchronous lifespan event handling for model loading.
* **Endpoints:**
  * `GET /`: API metadata, overview, and docs links.
  * `GET /health`: Microservice readiness and model loading status.
  * `GET /metrics`: Returns recorded model performance metrics (`accuracy`, `precision`, `recall`, `f1_score`, `roc_auc`).
  * `POST /predict`: Ingests JSON payload (`title`, `url`, `submission_time`) and returns classification status, probability, confidence level, and extracted features.

### 3.4 Containerization (`docker/Dockerfile`)
* Built on top of official `python:3.11-slim`.
* Configured with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`.
* Enforces `ENV PYTHONPATH=/workspace` ensuring test and execution consistency.
* Contains an embedded container healthcheck directive:
  `HEALTHCHECK --interval=20s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1`

---

## 4. DEVSECOPS & QUALITY ASSURANCE

### 4.1 Infrastructure as Code Security (Checkov)
The AWS CloudFormation template was scanned using Bridgecrew Checkov:
* **Initial Audit Result:** 22 checks passed, 4 failed (`CKV_AWS_24` open SSH port 22, `CKV_AWS_260` open port 80, missing S3 encryption).
* **Hardening Remediations Applied:**
  * Replaced wildcard `0.0.0.0/0` SSH and Jenkins ingress with a parameterized `AdminCidr` block.
  * Removed unencrypted HTTP port 80.
  * Enforced default S3 `AES256` Server-Side Encryption (`BucketEncryption`).
  * Added S3 `PublicAccessBlockConfiguration` preventing public data exposure.
* **Post-Hardening Result:** **24 Checks Passed** out of 24 eligible rules.

### 4.2 Container Vulnerability Scanning (Aqua Trivy)
* Scanned `hn-hit-predictor:latest` for OS and package CVEs.
* Audited Python dependencies, identifying outdated sub-dependencies and ensuring patched version requirements.

### 4.3 Automated Pytest Verification
Seven automated test cases pass with 100% success rate:
```text
tests/test_api.py::test_root_endpoint PASSED                    [ 14%]
tests/test_api.py::test_health_endpoint PASSED                  [ 28%]
tests/test_api.py::test_predict_endpoint_success PASSED         [ 42%]
tests/test_api.py::test_predict_endpoint_validation_error PASSED[ 57%]
tests/test_model.py::test_extract_domain_type PASSED            [ 71%]
tests/test_model.py::test_model_training_and_artifacts PASSED   [ 85%]
tests/test_model.py::test_model_inference PASSED                [100%]
============================== 7 passed in 3.41s ==============================
```

---

## 5. RESULTS & INFERENCE DEMONSTRATIONS

### 5.1 Model Evaluation Results
* **Accuracy:** 100% on benchmark evaluation set.
* **ROC-AUC Score:** 1.0000.
* **Precision / Recall / F1-Score:** 1.0000.

### 5.2 Real Inference Tests

#### Test Case 1: Likely Frontpage Post (High Virality)
* **Input Payload:**
  ```json
  {
    "title": "Show HN: RustKV – High performance distributed cache in Rust",
    "url": "https://github.com/developer/rustkv",
    "submission_time": "2026-11-08T15:30:00Z"
  }
  ```
* **API Output:**
  ```json
  {
    "title": "Show HN: RustKV – High performance distributed cache in Rust",
    "is_hit": true,
    "hit_probability": 0.911,
    "confidence_level": "High",
    "prediction_label": "Likely Hit (Frontpage Material)",
    "features": {
      "title": "Show HN: RustKV – High performance distributed cache in Rust",
      "domain_type": "github",
      "submission_hour": 15,
      "submission_day": 6,
      "title_len": 60,
      "title_word_count": 10
    }
  }
  ```

#### Test Case 2: Low-Traction / Spam Post
* **Input Payload:**
  ```json
  {
    "title": "Top 5 Crypto trading signals for today",
    "url": "https://my-marketing-hub.net/deal",
    "submission_time": "2026-11-08T03:00:00Z"
  }
  ```
* **API Output:**
  ```json
  {
    "title": "Top 5 Crypto trading signals for today",
    "is_hit": false,
    "hit_probability": 0.0247,
    "confidence_level": "Low",
    "prediction_label": "Unlikely Hit",
    "features": {
      "title": "Top 5 Crypto trading signals for today",
      "domain_type": "external",
      "submission_hour": 3,
      "submission_day": 6,
      "title_len": 38,
      "title_word_count": 7
    }
  }
  ```

---

## 6. AWS CLOUD & COST ANALYSIS (FREE TIER COMPLIANCE)

| AWS Resource | CloudFormation Configuration | AWS Free Tier Allowance | Project Cost |
| :--- | :--- | :--- | :--- |
| **Amazon EC2** | 1 instance (`t2.micro` or `t3.micro`) | 750 hours/month (Linux) | **\$0.00 / month** |
| **Amazon EBS** | 20 GB `gp3` storage volume | Up to 30 GB SSD storage | **\$0.00 / month** |
| **Amazon S3** | 1 private bucket with versioning & AES256 | 5 GB standard storage | **\$0.00 / month** |
| **AWS CloudWatch** | 1 log group (7-day retention), 1 metric alarm | 5 GB log ingestion, 10 alarms | **\$0.00 / month** |
| **CloudFormation** | Stacks and resource orchestration | Free service | **\$0.00 / month** |
| **Total Cost** | | | **\$0.00 (100% Free)** |

---

## 7. CONCLUSION & FUTURE SCOPE

### 7.1 Conclusion
The **HN HIT Predictor** successfully bridges the gap between academic machine learning modeling and modern software operations. By incorporating Docker containerization, Jenkins CI/CD automation, Checkov and Trivy DevSecOps security gates, and AWS Free Tier CloudFormation deployment, the project proves that robust, enterprise-grade cloud systems can be implemented affordably and reliably.

### 7.2 Future Scope
1. **Transformer Embeddings:** Upgrade from TF-IDF to transformer models (e.g., MiniLM / RoBERTa) using ONNX Runtime for CPU acceleration.
2. **Kubernetes (EKS/k3s) Deployment:** Implement Helm charts for horizontal pod autoscaling.
3. **Automated Retraining Loop:** Ingest daily Hacker News Firebase dumps into Amazon S3 and trigger Jenkins training jobs via CloudWatch EventBridge schedules.
