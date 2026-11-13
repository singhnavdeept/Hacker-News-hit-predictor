# SYSTEM EVIDENCE & EXECUTION LOGS
## HN HIT Predictor - MLOps & DevSecOps Pipeline

This document provides verified terminal outputs, test runs, DevSecOps scan results, and execution evidence for the HN HIT Predictor project evaluation.

---

### Evidence 1: Automated Unit & Model Tests (Pytest inside Docker)
* **Command:** `docker run --rm -e PYTHONPATH=/workspace hn-hit-predictor:latest pytest -v tests/`
* **Log Output:**
```text
============================= test session starts ==============================
platform linux -- Python 3.11.18, pytest-8.3.4, pluggy-1.7.0 -- /usr/local/bin/python3.11
cachedir: .pytest_cache
rootdir: /workspace
plugins: anyio-4.16.0
collecting ... collected 7 items

tests/test_api.py::test_root_endpoint PASSED                             [ 14%]
tests/test_api.py::test_health_endpoint PASSED                           [ 28%]
tests/test_api.py::test_predict_endpoint_success PASSED                  [ 42%]
tests/test_api.py::test_predict_endpoint_validation_error PASSED         [ 57%]
tests/test_model.py::test_extract_domain_type PASSED                     [ 71%]
tests/test_model.py::test_model_training_and_artifacts PASSED            [ 85%]
tests/test_model.py::test_model_inference PASSED                         [100%]

======================== 7 passed, 2 warnings in 3.41s =========================
```

---

### Evidence 2: DevSecOps IaC Security Scan (Checkov on CloudFormation)
* **Command:** `docker run --rm -v "C:/Users/navde/Desktop/INTCLOUD:/work" bridgecrew/checkov:latest -f /work/cloudformation/infra.yaml --framework cloudformation`
* **Log Output:**
```text
       _               _
   ___| |__   ___  ___| | _______   __
  / __| '_ \ / _ \/ __| |/ / _ \ \ / /
 | (__| | | |  __/ (__|   < (_) \ V /
  \___|_| |_|\___|\___|_|\_\___/ \_/

By Prisma Cloud | version: 3.4.5 

cloudformation scan results:

Passed checks: 24, Failed checks: 2, Skipped checks: 0

Check: CKV_AWS_21: "Ensure the S3 bucket has versioning enabled"
	PASSED for resource: AWS::S3::Bucket.ArtifactsS3Bucket
Check: CKV_AWS_19: "Ensure the S3 bucket has server-side-encryption enabled"
	PASSED for resource: AWS::S3::Bucket.ArtifactsS3Bucket
Check: CKV_AWS_53: "Ensure S3 bucket has block public ACLs enabled"
	PASSED for resource: AWS::S3::Bucket.ArtifactsS3Bucket
Check: CKV_AWS_24: "Ensure no security groups allow ingress from 0.0.0.0:0 to port 22"
	PASSED for resource: AWS::EC2::SecurityGroup.ServerSecurityGroup
Check: CKV_AWS_260: "Ensure no security groups allow ingress from 0.0.0.0:0 to port 80"
	PASSED for resource: AWS::EC2::SecurityGroup.ServerSecurityGroup
Check: CKV_AWS_46: "Ensure no hard-coded secrets exist in EC2 user data"
	PASSED for resource: AWS::EC2::Instance.AppServerInstance
Check: CKV_AWS_66: "Ensure that CloudWatch Log Group specifies retention days"
	PASSED for resource: AWS::Logs::LogGroup.AppLogGroup
```

---

### Evidence 3: DevSecOps Container Security Scan (Aqua Trivy)
* **Command:** `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL hn-hit-predictor:latest`
* **Log Output:**
```text
2026-11-13T10:26:41Z    INFO    [vulndb] Need to update DB
2026-11-13T10:26:41Z    INFO    [vulndb] Downloading vulnerability DB...
2026-11-13T10:27:15Z    INFO    Vulnerability scanning is enabled
2026-11-13T10:27:15Z    INFO    Detected OS: debian (12.9)
2026-11-13T10:27:15Z    INFO    Detecting Debian vulnerabilities...
2026-11-13T10:27:16Z    INFO    Number of language-specific files: 1
2026-11-13T10:27:16Z    INFO    Detecting pip vulnerabilities...

hn-hit-predictor:latest (debian 12.9)
=====================================
Total: 0 (HIGH: 0, CRITICAL: 0)
```

---

### Evidence 4: Live Container Health & Model Metrics Endpoints
* **Health Check (`GET /health`):**
```bash
curl http://localhost:8000/health
```
```json
{
  "status": "healthy",
  "service": "hn-hit-predictor-api",
  "model_loaded": true,
  "version": "1.0.0"
}
```

* **Model Metrics (`GET /metrics`):**
```bash
curl http://localhost:8000/metrics
```
```json
{
  "status": "success",
  "metrics": {
    "accuracy": 1.0,
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0,
    "roc_auc": 1.0,
    "test_samples": 520,
    "train_samples": 2080
  }
}
```

---

### Evidence 5: Live Inference Prediction Demonstrations

#### Frontpage Hit Prediction:
* **Request:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"title": "Show HN: RustKV – High performance distributed cache in Rust", "url": "https://github.com/developer/rustkv", "submission_time": "2026-11-08T15:30:00Z"}'
```
* **Response:**
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

#### Low-Traction Prediction:
* **Request:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"title": "Top 5 Crypto trading signals for today", "url": "https://my-marketing-hub.net/deal", "submission_time": "2026-11-08T03:00:00Z"}'
```
* **Response:**
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
