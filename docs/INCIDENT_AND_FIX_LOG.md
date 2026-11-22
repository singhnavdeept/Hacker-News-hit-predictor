# 🛠️ System Incident, Bug & Security Fix Log

> **Purpose:** Living record of all production, pipeline, security, and infrastructure bugs encountered, their root causes, and how they were permanently resolved.

---

## 📌 Incident 001: CI/CD Gate 2 Failure — Starlette Transitive CVEs in `pip-audit`

| Metadata | Details |
|---|---|
| **Date** | 2026-11-22 |
| **Component** | `requirements.txt` (FastAPI / Starlette) |
| **Severity** | **HIGH (CVSS 7.5)** |
| **Detected By** | CI/CD Gate 2 (`pip-audit -r requirements.txt`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
The GitHub Actions DevSecOps pipeline failed at **Step 2 (pip-audit)** with exit code 1. `pip-audit` reported 4 vulnerabilities in `starlette 0.41.3` (which was transitively installed by `fastapi==0.115.6`):

1. **`PYSEC-2026-1942` (CVE-2025-62727):**
   - **Vulnerability:** Denial of Service (DoS) via crafted HTTP `Range` header in `FileResponse` / `StaticFiles`.
   - **Mechanism:** Starlette's `_parse_range_header()` used an $O(n^2)$ regular expression and range-merging loop. An attacker sending thousands of small ranges caused massive CPU exhaustion, freezing worker processes.
   - **Fixed in:** Starlette `0.49.1` (and `1.1.0+`).
2. **`PYSEC-2026-1941`:**
   - **Vulnerability:** `UploadFile` disk rollover blocking the main event thread when parsing large multipart forms.
   - **Fixed in:** Starlette `0.47.2` (and `1.1.0+`).
3. **`PYSEC-2026-2281`:**
   - **Vulnerability:** `StaticFiles` UNC path SSRF / credential exposure on Windows.
   - **Fixed in:** Starlette `1.1.0`.
4. **`PYSEC-2026-2280`:**
   - **Vulnerability:** `HTTPEndpoint` method dispatching flaw allowing non-standard HTTP methods to invoke unauthenticated internal methods via `getattr`.
   - **Fixed in:** Starlette `1.1.0`.

### 2. Root Cause Analysis (RCA)
In `requirements.txt`, FastAPI was rigidly pinned to an older release:
```text
fastapi==0.115.6  # Internally restricted Starlette to ">=0.40.0,<0.42.0"
```
Because of this hard ceiling (`<0.42.0`), `pip` was prevented from pulling any patched Starlette release (`>=1.1.0`), leaving `starlette 0.41.3` in the dependency tree.

### 3. How Was It Fixed?
1. Updated `requirements.txt` to remove the outdated strict pin on `fastapi==0.115.6` and explicitly enforce a secure minimum version of `starlette`:
   ```text
   fastapi>=0.115.8
   starlette>=1.1.0
   uvicorn[standard]>=0.34.0
   scikit-learn==1.6.0
   joblib==1.4.2
   pandas==2.2.3
   numpy==2.2.1
   pydantic>=2.10.4
   pytest==8.3.4
   httpx==0.28.1
   requests==2.32.3
   ```
2. By setting `starlette>=1.1.0` and `fastapi>=0.115.8`, `pip` resolves modern, safe releases that patch all four advisories.

### 4. Verification
`pip-audit` passes with **0 vulnerabilities found**.

---

## 📌 Incident 002: CI/CD Gate 2 Failure — CVEs in `pytest 8.3.4` and `requests 2.32.3`

| Metadata | Details |
|---|---|
| **Date** | 2026-11-22 |
| **Component** | `requirements.txt` (`pytest`, `requests`) |
| **Severity** | **HIGH** |
| **Detected By** | CI/CD Gate 2 (`pip-audit -r requirements.txt`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
`pip-audit` found 6 known vulnerability instances across 2 pinned packages:
1. **`pytest 8.3.4` (`PYSEC-2026-1845`):**
   - **Vulnerability:** On UNIX systems, `pytest` relied on directories with predictable `/tmp/pytest-of-{user}` naming patterns, allowing local unprivileged users to cause Denial of Service or escalate privileges.
   - **Fixed in:** `pytest >= 9.0.3` (Latest stable: `9.2.0`).
2. **`requests 2.32.3` (`PYSEC-2026-1872` & `PYSEC-2026-2275`):**
   - **`PYSEC-2026-1872`:** Maliciously-crafted URLs triggered a URL parsing defect that leaked `.netrc` authentication credentials to untrusted third parties (Fixed in `2.32.4`).
   - **`PYSEC-2026-2275`:** `requests.utils.extract_zipped_paths()` extracted files to predictable filenames in `/tmp` without validation, allowing local attackers to overwrite and inject malicious payloads (Fixed in `2.33.0`).

### 2. Root Cause Analysis (RCA)
`requirements.txt` pinned exact legacy releases:
```text
pytest==8.3.4     # Vulnerable to PYSEC-2026-1845
requests==2.32.3  # Vulnerable to PYSEC-2026-1872 and PYSEC-2026-2275
```
Because of rigid `==` pinning, `pip` was prevented from pulling patched versions released upstream.

### 3. How Was It Fixed?
Updated `requirements.txt` to lift the version constraints to patched releases:
```text
pytest>=9.0.3
requests>=2.33.0
httpx>=0.28.1
```

### 4. Verification
Both `pytest` and `requests` are upgraded beyond their vulnerability thresholds (`pytest 9.2.0` and `requests 2.34.2`). `pip-audit -r requirements.txt` passes cleanly.

---

## 📌 Incident 003: CI/CD Gate 3 Failure — Checkov IaC Security Violations on OpenTofu Stack

| Metadata | Details |
|---|---|
| **Date** | 2026-11-22 |
| **Component** | `tofu/modules/app_stack/main.tf` |
| **Severity** | **HIGH** |
| **Detected By** | CI/CD Gate 3 (`checkov -d tofu/modules/app_stack`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
Checkov static analysis scanned `tofu/modules/app_stack` and flagged 10 checks (3 actionable security fixes + 7 enterprise policies conflicting with AWS Free Tier):
- `CKV_AWS_382`: Security group allowed egress to `0.0.0.0/0` on port `-1` (all ports).
- `CKV_AWS_26`: SNS topic data was not encrypted at rest.
- `CKV2_AWS_61`: S3 artifacts bucket lacked lifecycle management configuration.
- 7 enterprise checks that force paid non-free-tier services: KMS Customer Managed Keys ($1.00/month per key for S3 and CloudWatch), 365-day CloudWatch log retention (exceeds 5GB free tier), S3 cross-region replication, and S3 access logging.

### 2. Root Cause Analysis (RCA)
- **Egress:** The security group egress had default `protocol = "-1"` and `from_port = 0`, which violates CIS Benchmark egress filtering best practices.
- **SNS:** The SNS topic lacked `kms_master_key_id`.
- **S3 Lifecycle:** The bucket had versioning enabled but no expiration rules, risking long-term storage bloat from noncurrent model versions.
- **Cost Guardrails vs Enterprise Rules:** In production enterprises, Customer Managed KMS keys and 1-year log retention are standard, but on an AWS Free Tier account, they trigger immediate monthly billing charges.

### 3. How Was It Fixed?
1. **Restricted Egress Security Group Rules:**
   Replaced all-port egress with explicit rules allowing only:
   - TCP Port `443` (HTTPS for AWS APIs, SSM, CloudWatch, and Docker Registry)
   - TCP Port `80` (HTTP for Amazon Linux dnf package repository updates)
2. **Encrypted SNS Topic with Zero Cost:**
   Configured `kms_master_key_id = "alias/aws/sns"`, which uses AWS's built-in managed KMS key at **$0.00 cost**.
3. **Implemented S3 Lifecycle Configuration:**
   Added `aws_s3_bucket_lifecycle_configuration` expiring noncurrent versions after 90 days and aborting incomplete multipart uploads after 7 days.
4. **Documented Inline Checkov Suppressions for Free Tier Cost Protection:**
   Annotated cost-violating enterprise checks with `# checkov:skip=...` and technical rationales:
   - `CKV_AWS_158` & `CKV_AWS_145`: Documented AES-256 / AWS-managed encryption to avoid $1.00/mo KMS CMK charges.
   - `CKV_AWS_338`: Documented 7-day log retention to prevent breaching the 5GB Free Tier limit.
   - `CKV_AWS_144` & `CKV_AWS_18`: Documented single-region Free Tier guardrails for cross-region replication and logging buckets.
   - `CKV2_AWS_5`: Documented security group attachment via EC2 `vpc_security_group_ids`.

### 4. Verification
- `tofu/modules/app_stack`: 34 checks PASSED, 7 checks SKIPPED with documented cost rationales, **0 checks FAILED**.
- Note on `CKV_AWS_145`: Checkov inspects `CKV_AWS_145` against `aws_s3_bucket` directly rather than the separate `aws_s3_bucket_server_side_encryption_configuration` resource. Moving the suppression comment directly into `aws_s3_bucket` resolves the final scan blocker.

---

## 📌 Incident 004: Pytest `ModuleNotFoundError: No module named 'app'/'src'` in CI Test Collection

| Metadata | Details |
|---|---|
| **Date** | 2026-11-22 |
| **Component** | Test Suite Execution (`pytest`) |
| **Severity** | **MEDIUM (CI Build Blocker)** |
| **Detected By** | GitHub Actions Runner (`pytest -v tests/`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
During the `Run Pytest Suite & Model Validation` step in GitHub Actions, `pytest` crashed during test collection with:
```text
ImportError while importing test module 'tests/test_api.py':
from app.main import app, load_model
ModuleNotFoundError: No module named 'app'

ImportError while importing test module 'tests/test_model.py':
from src.train import train_and_evaluate, MODEL_PATH, METRICS_PATH
ModuleNotFoundError: No module named 'src'
```

### 2. Root Cause Analysis (RCA)
Inside Docker containers, `ENV PYTHONPATH=/workspace` was explicitly set. However, in the GitHub Actions runner (which executes pytest directly on the Linux host), Python's `sys.path` only contains site-packages and standard libraries — the project root directory was not in `sys.path`. Without explicit configuration, pytest could not resolve top-level packages `app` and `src`.

### 3. How Was It Fixed?
1. **Created `pytest.ini` in Repository Root:**
   Utilized pytest's native rootdir resolution:
   ```ini
   [pytest]
   pythonpath = .
   testpaths = tests
   filterwarnings =
       ignore::DeprecationWarning
       ignore::UserWarning
   ```
2. **Updated CI Workflow:**
   Hardened the step in `.github/workflows/ci-cd.yml` to:
   ```yaml
   - name: Run Pytest Suite & Model Validation
     run: |
       PYTHONPATH=. pytest -v tests/
   ```

### 4. Verification
Pytest automatically loads `pytest.ini`, appends `.` to `sys.path`, and cleanly collects and executes all tests across `tests/test_api.py` and `tests/test_model.py`.

---

## 📌 Incident 005: Pytest `test_predict_endpoint_success` 503 Service Unavailable (Model Artifact Missing in Clean CI)

| Metadata | Details |
|---|---|
| **Date** | 2026-11-22 |
| **Component** | Test Suite (`tests/test_api.py`) |
| **Severity** | **LOW (Test Suite Ordering Dependency)** |
| **Detected By** | GitHub Actions Runner (`PYTHONPATH=. pytest -v tests/`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
Pytest failed on `test_predict_endpoint_success`:
```text
FAILED tests/test_api.py::test_predict_endpoint_success - assert 503 == 200
where 503 = <Response [503 Service Unavailable]>.status_code

Captured log setup:
WARNING hn-hit-predictor:main.py Model file not found at .../models/model.joblib. Prediction requests will fail until trained.
```

### 2. Root Cause Analysis (RCA)
- **Alphabetical Execution Order:** In pytest, `tests/test_api.py` executes before `tests/test_model.py`.
- **Missing Artifact in Clean CI:** In a fresh CI checkout, the trained model artifact (`models/model.joblib`) does not exist until created. In previous runs, `test_model.py` trained the model during its run, which inadvertently satisfied subsequent runs if the directory was dirty. In a clean runner, `test_api.py` ran first against an empty `models/` directory.
- Because `model.joblib` was missing, `load_model()` logged a warning and left `model_pipeline = None`.
- The `/predict` route properly raised HTTP 503 Service Unavailable when invoked without an active model artifact.

### 3. How Was It Fixed?
1. **Created `tests/conftest.py` with Session Fixture:**
   Added a session-scoped autouse fixture `setup_test_environment()` that verifies `models/model.joblib` exists before *any* test file runs. If missing, it immediately invokes `train_and_evaluate(force_synthetic=True)` (~0.5s execution time).
2. **Hardened `tests/test_api.py`:**
   Added an explicit check in `ensure_model_is_loaded()` to ensure model generation and loading prior to executing prediction assertions.

### 4. Verification
All 8 test cases pass cleanly (`8 passed in 1.8s`):
- `tests/test_api.py::test_root_endpoint PASSED`
- `tests/test_api.py::test_health_endpoint PASSED`
- `tests/test_api.py::test_version_endpoint PASSED`
- `tests/test_api.py::test_predict_endpoint_success PASSED`
- `tests/test_api.py::test_predict_endpoint_validation_error PASSED`
- `tests/test_model.py::test_extract_domain_type PASSED`
- `tests/test_model.py::test_model_training_and_artifacts PASSED`
- `tests/test_model.py::test_model_inference PASSED`

---

## 📌 Incident 006: GitHub Actions Workflow Action Resolution Failure: `aquasec/trivy-action` Repository Not Found

| Metadata | Details |
|---|---|
| **Date** | 2026-11-23 |
| **Component** | CI/CD Pipeline (`.github/workflows/ci-cd.yml`) |
| **Severity** | **LOW (Action Reference Typo)** |
| **Detected By** | GitHub Actions Runner (`Prepare all required actions`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
The GitHub Actions runner failed during the workflow preparation step:
```text
Getting action download info
Error: Unable to resolve action aquasec/trivy-action, repository not found
```

### 2. Root Cause Analysis (RCA)
- In the Docker Hub registry, Aqua Security's official container image is located under `aquasec/trivy`.
- However, in GitHub Actions, the official GitHub Action repository is registered under **`aquasecurity/trivy-action`** (organization name is `aquasecurity`, not `aquasec`).
- Because `.github/workflows/ci-cd.yml` referenced `aquasec/trivy-action@master`, GitHub could not locate the repository.

### 3. How Was It Fixed?
Updated line 87 in `.github/workflows/ci-cd.yml`:
```yaml
# Before:
uses: aquasec/trivy-action@master

# After:
uses: aquasecurity/trivy-action@master
```

### 4. Verification
GitHub Actions runner successfully resolves, downloads, and executes `aquasecurity/trivy-action@master`.

---

## 📌 Incident 007: Aqua Trivy Container Scan Failure (Exit Code 1) — High CVEs in `zlib1g` and bundled `setuptools`

| Metadata | Details |
|---|---|
| **Date** | 2026-11-23 |
| **Component** | Container Image Build (`docker/Dockerfile`) |
| **Severity** | **HIGH** |
| **Detected By** | CI/CD Gate 4 (`aquasecurity/trivy-action`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
Aqua Trivy scanned `hn-hit-predictor:<SHA>` with `--exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed` and failed the pipeline with 3 HIGH vulnerabilities:
1. **Debian OS package `zlib1g 1:1.3.dfsg+really1.3.1-1+b1` (`CVE-2026-85091`):**
   - Heap buffer overflow in `gz_vacate()` allowing arbitrary code execution (Fixed in `1:1.3.dfsg+really1.3.1-1+deb13u1`).
2. **Vendored Python library `jaraco.context 5.3.0` (`CVE-2026-23949`):**
   - Path traversal via malicious tar archives (Fixed in `6.1.0`).
3. **Vendored Python library `wheel 0.45.1` (`CVE-2026-24049`):**
   - Privilege escalation / arbitrary code execution via malicious wheel file (Fixed in `0.46.2`).

### 2. Root Cause Analysis (RCA)
- **Stale Base Image OS Packages:** The Docker base image `python:3.11-slim` is based on Debian 13. While Debian released a security patch (`deb13u1`) for `zlib1g`, the base Docker image had not been refreshed. The Dockerfile only ran `apt-get install -y curl` without `apt-get upgrade -y`, leaving existing OS packages unpatched.
- **Outdated Pre-installed Bundled Setuptools:** Python slim base images ship with a pre-installed `setuptools` (`79.0.1`) under `/usr/local/lib/python3.11/site-packages/`. This specific setuptools release vendored older versions of `jaraco.context` (5.3.0) and `wheel` (0.45.1). Even though top-level dependencies were upgraded, Trivy's deep scanner inspected `setuptools/_vendor/` and flagged the vendored code.

### 3. How Was It Fixed?
Updated `docker/Dockerfile`:
1. Added `apt-get upgrade -y` to upgrade base Debian OS packages during image build, automatically updating `zlib1g` to `1:1.3.dfsg+really1.3.1-1+deb13u1`.
2. Added `RUN pip install --no-cache-dir --upgrade pip "setuptools>=84.0.0" "wheel>=0.46.3"` prior to installing requirements, which replaces the legacy bundled setuptools with modern `setuptools 84.2.1+` (incorporating patched `jaraco.context 6.1.0+` and `wheel 0.46.3+`).

### 4. Verification
Rebuilding the image and scanning with Aqua Trivy reports **0 High/Critical vulnerabilities**.

---

## 📌 Incident 008: Aqua Trivy Container Scan Failure (Exit Code 1) — `CVE-2025-47273` in Lingering `setuptools 70.3.0` Metadata

| Metadata | Details |
|---|---|
| **Date** | 2026-11-23 |
| **Component** | Container Image Build (`docker/Dockerfile`) |
| **Severity** | **HIGH** |
| **Detected By** | CI/CD Gate 4 (`aquasecurity/trivy-action`) |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
Aqua Trivy caught a single remaining HIGH vulnerability:
```text
Python (python-pkg)
Library: setuptools
Vulnerability: CVE-2025-47273
Severity: HIGH
Status: fixed
Installed Version: 70.3.0
Fixed Version: 78.1.1
Title: setuptools: Path Traversal Vulnerability in setuptools PackageIndex
```

### 2. Root Cause Analysis (RCA)
- In Debian 13 (`trixie`), the system package repository installs `python3-setuptools 70.3.0` into `/usr/lib/python3/dist-packages/`.
- Even though `zlib1g` was patched by `apt-get upgrade -y` and application dependencies were clean, Trivy's filesystem crawler scanned system python directories and detected the unpatched `setuptools 70.3.0` `.dist-info` package metadata.
- **Runtime Requirement Analysis:** Neither FastAPI, Uvicorn, Scikit-learn, Pandas, nor Joblib require `setuptools` at runtime. `setuptools` is purely a build-time toolchain component. Keeping build tools in a production container violates container minimization principles and leaves unnecessary attack surface.

### 3. How Was It Fixed?
Applied **production container hardening** in `docker/Dockerfile`:
After dependencies are installed and `python -m src.train` finishes building the model artifact, purged `setuptools` and `wheel` completely from the final runtime image:
```dockerfile
# Security hardening: remove build-time packaging tools (setuptools, wheel)
# Eliminates CVE-2025-47273 and reduces runtime attack surface
RUN pip uninstall -y setuptools wheel || true \
    && rm -rf /usr/lib/python3/dist-packages/setuptools* \
              /usr/local/lib/python3.11/site-packages/setuptools* \
              /usr/local/lib/python3.11/site-packages/wheel*
```

### 4. Verification
Trivy scans the hardened image with **0 vulnerabilities detected** across both OS and Python packages. All 4 CI/CD gates pass cleanly.

---

## 📌 Incident 000-A: Jenkins Container-to-Host Loopback Failure in Smoke Test

| Metadata | Details |
|---|---|
| **Date** | 2026-11-17 |
| **Component** | `Jenkinsfile` (Stage 6: Integration Smoke Test) |
| **Severity** | MEDIUM (Deployment Blocker) |
| **Detected By** | Jenkins Pipeline Run |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
Stage 6 spun up a test container on port 8009 and ran:
```bash
curl -s -f http://localhost:8009/health
```
The command failed with exit code 1 (`Failed to connect to localhost port 8009: Connection refused`).

### 2. Root Cause Analysis (RCA)
The Jenkins agent was executing inside a Docker container (`hn-jenkins-local`). In Docker networking, `localhost` inside a container resolves to that container's private network namespace, **not** the EC2 host where port 8009 was bound.

### 3. How Was It Fixed?
Bypassed host loopback routing by executing the curl verification directly inside the smoke container via Docker socket:
```bash
docker exec ${APP_NAME}-smoke curl -s -f http://localhost:8000/health
docker exec ${APP_NAME}-smoke curl -s -X POST http://localhost:8000/predict ...
```
This directly queries Uvicorn inside the container's own loopback namespace, guaranteeing 100% reliability.

---

## 📌 Incident 000-B: Out-of-Memory (OOM) Process Termination on EC2 `t3.micro`

| Metadata | Details |
|---|---|
| **Date** | 2026-11-16 |
| **Component** | EC2 Memory Management |
| **Severity** | HIGH (Instance Freeze / Build Crash) |
| **Detected By** | SSH `client_loop: send disconnect` during `docker build` |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
Running `pip install` and `scikit-learn` model training concurrently inside Docker on a 1 GB RAM `t3.micro` instance caused Linux OOM killer to terminate the build process or freeze the SSH session.

### 2. Root Cause Analysis (RCA)
The `t3.micro` instance only provides 1,024 MB of physical DRAM. During peak compilation/pip wheel decompression and scikit-learn matrix allocation, memory spiked to ~1.3 GB, exceeding physical RAM with no swap space available.

### 3. How Was It Fixed?
1. **Allocated 2 GB Swapfile on EBS gp3:**
   ```bash
   fallocate -l 2G /swapfile
   chmod 600 /swapfile
   mkswap /swapfile
   swapon /swapfile
   echo '/swapfile none swap sw 0 0' >> /etc/fstab
   ```
2. **Decommissioned On-Host Jenkins:** Shifted all CI/CD compute and scanning to **GitHub Actions** runners (7 GB RAM, free), reserving 100% of the EC2 instance's memory strictly for the FastAPI inference runtime.

---

## 📌 Incident 000-C: Checkov IaC Security Violations (CIS AWS Benchmark)

| Metadata | Details |
|---|---|
| **Date** | 2026-11-16 |
| **Component** | Infrastructure as Code |
| **Severity** | HIGH (Compliance Failure) |
| **Detected By** | Checkov Static Analysis |
| **Status** | **RESOLVED** ✅ |

### 1. What Broke?
Checkov reported security violations:
- `CKV_AWS_24`: Security group allows unrestricted SSH (`0.0.0.0/0:22`).
- `CKV_AWS_19`: S3 bucket does not have server-side encryption enabled.
- `CKV_AWS_54`: S3 bucket public access not explicitly blocked.

### 2. Root Cause Analysis (RCA)
Default infrastructure templates left port 22 open and relied on unencrypted S3 defaults.

### 3. How Was It Fixed?
1. **Port 22 completely eliminated** in OpenTofu security group. Host administration shifted to **AWS Systems Manager (SSM) Session Manager** with IAM role authentication.
2. Added `aws_s3_bucket_server_side_encryption_configuration` with `AES256`.
3. Added `aws_s3_bucket_public_access_block` enabling all 4 block settings (`block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`).
4. Enforced **IMDSv2** on the EC2 instance (`http_tokens = "required"`).
