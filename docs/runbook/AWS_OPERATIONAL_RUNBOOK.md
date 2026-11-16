# AWS OPERATIONAL RUNBOOK: HN HIT PREDICTOR
## Complete Deployment, Configuration, Operations & Teardown Manual

* **Project:** HN HIT Predictor: An MLOps & DevSecOps Pipeline on AWS
* **Target Environment:** AWS Free Tier (100% Zero Cost - $0.00/mo)
* **Stack Components:** CloudFormation, EC2 (`t2.micro`), Docker, Jenkins LTS, S3, CloudWatch Logs & Alarms
* **Author:** Navdeep Singh (Reg No: 12308217 | Roll No: 43 | Section: K2O2313)
* **Guide:** Arshiya (UID-29453) | Lovely Professional University

---

## 1. PRE-DEPLOYMENT PREREQUISITES & CHECKLIST

Before launching any resources on AWS, ensure the following items are ready:

| Item | Requirement | Verification / Action |
| :--- | :--- | :--- |
| **AWS Account** | AWS Free Tier eligible account | Ensure your account can launch EC2 instances in your chosen region. |
| **Target AWS Region** | US East (N. Virginia) `us-east-1` OR Asia Pacific (Mumbai) `ap-south-1` | Select one region and use it consistently for all steps. |
| **EC2 Key Pair** | Key Pair created in target region | Format: `.pem` (OpenSSH) for terminal SSH access. |
| **Source Code Repo** | Public GitHub repository | `https://github.com/singhnavdeept/Hacker-News-hit-predictor.git` |
| **CloudFormation Template** | Local copy ready for upload | `cloudformation/infra.yaml` in your project folder. |

### Step 1.1: Create an EC2 Key Pair (If not already created)
1. Log in to the [AWS Management Console](https://console.aws.amazon.com/).
2. In the top search bar, search for **EC2** and click it.
3. In the left navigation sidebar under **Network & Security**, click **Key Pairs**.
4. Click the orange button **Create key pair**.
5. Configure the key pair:
   * **Name:** `hn-key` (remember this exact name).
   * **Key pair type:** `RSA`.
   * **Private key file format:** `.pem` (for Mac/Linux/Windows PowerShell OpenSSH).
6. Click **Create key pair**.
7. The file `hn-key.pem` will download automatically to your computer. **Keep it in a safe folder** (e.g. `C:\Users\navde\Desktop\INTCLOUD\` or `~/.ssh/`).

---

## 2. INFRASTRUCTURE PROVISIONING VIA CLOUDFORMATION

You can provision the entire architecture using the **AWS Console (Browser UI)** or the **AWS CLI**. Choose **Option A** for a visual click-by-click experience.

### Option A: Via AWS Console (Visual Step-by-Step)

#### Step 2.1: Open CloudFormation
1. In the AWS Console search bar, type **CloudFormation** and press Enter.
2. Verify in the top-right corner that your active region is correct (e.g., **N. Virginia `us-east-1`** or **Mumbai `ap-south-1`**).
3. Click the orange **Create stack** button > select **With new resources (standard)**.

#### Step 2.2: Upload the Template
1. Under **Prerequisite - Prepare template**, choose **Template is ready**.
2. Under **Specify template**, choose **Upload a template file**.
3. Click **Choose file** and browse to:
   `C:\Users\navde\Desktop\INTCLOUD\cloudformation\infra.yaml`
4. Click **Next** at the bottom right.

#### Step 2.3: Enter Stack Details & Parameters
1. **Stack name:** Enter `hn-hit-predictor-stack`.
2. **Parameters:**
   * **`InstanceType`:** Select `t2.micro` (Free-tier eligible).
   * **`KeyName`:** Select `hn-key` from the dropdown list.
   * **`AdminCidr`:** 
     * *Recommended for testing:* Enter `0.0.0.0/0` (allows you to access from any network/Wi-Fi).
     * *Production DevSecOps strict:* Enter your public IP followed by `/32` (e.g., `103.45.67.89/32`).
3. Click **Next**.

#### Step 2.4: Configure Stack Options
1. Leave **Tags**, **Permissions**, and **Advanced options** as their default values.
2. Click **Next** to proceed to the Review page.

#### Step 2.5: Review & Acknowledge IAM Creation
1. Scroll down to the bottom of the Review page.
2. Locate the blue Capabilities callout box.
3. Check the required acknowledgment box:
   > 🗹 **"I acknowledge that AWS CloudFormation might create IAM resources with custom names."**
4. Click **Submit**.

#### Step 2.6: Monitor Creation Progress
1. CloudFormation will display the **Events** tab with status `CREATE_IN_PROGRESS`.
2. Over the next 2 to 3 minutes, it will automatically provision:
   * S3 Bucket: `hn-hit-predictor-<account-id>-<region>` with AES-256 encryption.
   * IAM Role & Instance Profile: `HNHitPredictor-EC2Role-<region>`.
   * Security Group: `ServerSecurityGroup` (Ports 22, 8000, 8080).
   * CloudWatch Log Group: `/aws/ec2/hn-hit-predictor` (7-day retention).
   * CloudWatch Alarm: `HighCPUAlarm` (>80% CPU).
   * EC2 Instance: Amazon Linux 2023 with pre-configured UserData script.
3. Wait until the stack status turns green: **`CREATE_COMPLETE`**.

#### Step 2.7: Retrieve Stack Outputs
1. Click the **Outputs** tab in CloudFormation.
2. Copy and save these values:
   * **`PublicIP`** (e.g., `54.210.123.45`)
   * **`FastApiUrl`** (`http://54.210.123.45:8000/docs`)
   * **`JenkinsUrl`** (`http://54.210.123.45:8080`)
   * **`S3ArtifactsBucketName`** (`hn-hit-predictor-...`)

---

### Option B: Via AWS CLI (For Terminal Power Users)

If your local terminal has `aws configure` set up:
```bash
aws cloudformation create-stack \
  --stack-name hn-hit-predictor-stack \
  --template-body file://cloudformation/infra.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=KeyName,ParameterValue=hn-key \
               ParameterKey=AdminCidr,ParameterValue=0.0.0.0/0

# Wait for completion:
aws cloudformation wait stack-create-complete --stack-name hn-hit-predictor-stack

# View outputs:
aws cloudformation describe-stacks --stack-name hn-hit-predictor-stack --query "Stacks[0].Outputs" --output table
```

---

## 3. SERVER BOOTSTRAP & APPLICATION STARTUP

The CloudFormation template automatically executes a bootstrap script (`UserData`) that installs Docker, Git, Docker Compose, and the AWS CloudWatch agent. Now we connect to the server and start the microservice containers.

### Step 3.1: Connect to the EC2 Instance

#### Method 1: Using SSH (From your local PowerShell / Terminal)
Open PowerShell in the folder where your `hn-key.pem` is stored:
```powershell
# Set permissions on Windows (if needed):
icacls.exe .\hn-key.pem /reset
icacls.exe .\hn-key.pem /grant:r "$($env:username):(R)"
icacls.exe .\hn-key.pem /inheritance:r

# Connect to EC2:
ssh -i .\hn-key.pem ec2-user@<YOUR_EC2_PUBLIC_IP>
```

#### Method 2: Using EC2 Instance Connect (100% Browser-Based, No SSH Key Needed)
1. Go to **AWS Console > EC2 > Instances**.
2. Select `HN-Hit-Predictor-Server`.
3. Click the **Connect** button at the top right.
4. Select the **EC2 Instance Connect** tab.
5. Click **Connect**. A terminal window opens directly in your browser.

---

### Step 3.2: Verify Server Setup & Docker Daemon
Inside the EC2 terminal, verify that Docker and Git are active:
```bash
docker --version
git --version
docker compose version
```
*(If Docker was just installed by UserData, give it 30-45 seconds to finish its background bootstrap).*

---

### Step 3.3: Clone the GitHub Repository on EC2
```bash
cd /home/ec2-user
git clone https://github.com/singhnavdeept/Hacker-News-hit-predictor.git
cd Hacker-News-hit-predictor
```

---

### Step 3.4: Launch Application & Jenkins Containers
Launch the FastAPI prediction service and Jenkins controller using Docker Compose:
```bash
docker compose up -d --build
```

Monitor the container startup:
```bash
docker ps
```
You should see both containers running:
```text
CONTAINER ID   IMAGE                               COMMAND                  STATUS                    PORTS
xxxxxxxxx      hacker-news-hit-predictor-api       "uvicorn app.main:ap…"   Up (healthy)              0.0.0.0:8000->8000/tcp
yyyyyyyyy      jenkins/jenkins:lts-jdk17           "/usr/bin/tini -- /u…"   Up                        0.0.0.0:8080->8080/tcp
```

---

## 4. VERIFYING THE LIVE REST API SERVICE

### Step 4.1: Access the Interactive Swagger UI
Open your web browser on your PC or mobile and navigate to:
```text
http://<YOUR_EC2_PUBLIC_IP>:8000/docs
```
You will see the interactive **FastAPI Swagger Documentation** with all endpoints:
* `GET /health`
* `GET /metrics`
* `POST /predict`

### Step 4.2: Test Health Check Endpoint
In your browser or terminal:
```bash
curl -s http://<YOUR_EC2_PUBLIC_IP>:8000/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "hn-hit-predictor-api",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### Step 4.3: Test Model Metrics Endpoint
```bash
curl -s http://<YOUR_EC2_PUBLIC_IP>:8000/metrics
```
**Expected Response:**
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

### Step 4.4: Test Live Prediction Endpoint

#### Test 1: High-Virality Frontpage Story Candidate
```bash
curl -X POST http://<YOUR_EC2_PUBLIC_IP>:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Show HN: RustKV – High performance distributed cache in Rust",
    "url": "https://github.com/developer/rustkv",
    "submission_time": "2026-11-08T15:30:00Z"
  }'
```
**Expected Response:**
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

#### Test 2: Low-Traction / Commercial Post
```bash
curl -X POST http://<YOUR_EC2_PUBLIC_IP>:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Top 5 Crypto trading signals for today",
    "url": "https://my-marketing-hub.net/deal",
    "submission_time": "2026-11-08T03:00:00Z"
  }'
```
**Expected Response:**
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

## 5. JENKINS CI/CD CONFIGURATION & PIPELINE EXECUTION

### Step 5.1: Open Jenkins Dashboard
In your browser, visit:
```text
http://<YOUR_EC2_PUBLIC_IP>:8080
```

### Step 5.2: Retrieve the Initial Administrator Password
On the EC2 terminal, run:
```bash
docker exec -it hn-jenkins-local cat /var/jenkins_home/secrets/initialAdminPassword
```
1. Copy the 32-character string.
2. Paste it into the Jenkins **Administrator password** box in your browser.
3. Click **Continue**.

### Step 5.3: Complete Initial Jenkins Wizard
1. Choose **Install suggested plugins** (takes ~1–2 minutes).
2. Create an admin user (e.g., username `admin`, enter your password).
3. On the **Instance Configuration** screen, confirm URL `http://<YOUR_EC2_PUBLIC_IP>:8080` and click **Save and Finish**.

### Step 5.4: Create the CI/CD Pipeline Job
1. On the Jenkins home screen, click **New Item**.
2. Enter item name: `HN-HIT-Predictor-CI-CD`.
3. Select **Pipeline** and click **OK**.
4. Scroll down to the **Pipeline** section:
   * **Definition:** Select `Pipeline script from SCM`.
   * **SCM:** Select `Git`.
   * **Repository URL:** `https://github.com/singhnavdeept/Hacker-News-hit-predictor.git`
   * **Branch Specifier:** `*/main`
   * **Script Path:** `Jenkinsfile`
5. Click **Save**.

### Step 5.5: Run the 7-Stage Pipeline
1. On the job page, click **Build Now**.
2. Click on the build number (e.g. `#1`) > click **Console Output**.
3. Watch the 7 declarative stages execute:
   * **Stage 1:** Checkout & Directory Validation.
   * **Stage 2:** DevSecOps IaC Security Scan with **Checkov** (Audits `cloudformation/infra.yaml`).
   * **Stage 3:** Unit & Model Tests with **Pytest** (Runs 7/7 tests).
   * **Stage 4:** Package Production Image (`hn-hit-predictor:latest`).
   * **Stage 5:** DevSecOps Container Scan with **Aqua Trivy** (Checks image CVEs).
   * **Stage 6:** Integration Smoke Test (Starts container on ephemeral port, validates `/health` & `/predict`).
   * **Stage 7:** Production Rollout (Zero-downtime container replacement on port 8000).
4. Status turns green: **SUCCESS**.

---

## 6. CLOUDWATCH MONITORING, LOGS & ALARMS VERIFICATION

### Step 6.1: View Centralized CloudWatch Logs
1. Open the [AWS CloudWatch Console](https://console.aws.amazon.com/cloudwatch/).
2. In the left navigation menu, click **Logs** > **Log groups**.
3. Click on the log group created by CloudFormation:
   `/aws/ec2/hn-hit-predictor`
4. Click on the active log stream (`<instance-id>/system`).
5. You can see live system events, boot logs, and container activity streamed in real-time.

### Step 6.2: View CloudWatch Metric Alarms
1. In CloudWatch left navigation, click **Alarms** > **All alarms**.
2. Locate the alarm: `hn-hit-predictor-stack-HighCPUAlarm-...`.
3. Click into it to inspect:
   * **Metric:** `CPUUtilization` (Namespace: `AWS/EC2`).
   * **Condition:** `CPUUtilization >= 80% for 2 consecutive 5-minute periods`.
   * **State:** Should show **OK** (green checkmark).

---

## 7. BACKUP MODEL ARTIFACTS TO S3

Your CloudFormation stack created an S3 bucket configured with **AES-256 Server-Side Encryption**. You can synchronize model artifacts from EC2 to S3 anytime:

On the EC2 terminal:
```bash
# Get your bucket name automatically:
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name hn-hit-predictor-stack --query "Stacks[0].Outputs[?OutputKey=='S3ArtifactsBucketName'].OutputValue" --output text)

# Upload trained model artifacts:
aws s3 sync /home/ec2-user/Hacker-News-hit-predictor/models/ s3://$BUCKET_NAME/models/

# Verify S3 contents:
aws s3 ls s3://$BUCKET_NAME/models/
```

---

## 8. TROUBLESHOOTING & COMMON OPERATIONAL ISSUES

### Issue 1: Browser cannot reach `http://<PublicIP>:8000/docs` or `:8080`
* **Root Cause:** Security Group restricting your IP, or Docker container not started.
* **Fix:**
  1. In EC2 Console > Instances > Select instance > Security tab > Click Security Group.
  2. Verify Inbound Rules:
     * Port 8000 should allow `0.0.0.0/0`.
     * Port 8080 should allow your current IP address (or `0.0.0.0/0`).
  3. Verify containers are running: on EC2 terminal, run `docker ps`.

### Issue 2: `ssh: connect to host ... port 22: Connection timed out`
* **Root Cause:** Your local public IP changed, or AdminCidr was set to a different IP.
* **Fix:** In the AWS Console, edit the EC2 Security Group inbound rule for port 22 and update the CIDR to `0.0.0.0/0` or click "My IP". Alternatively, use **EC2 Instance Connect** in your browser.

### Issue 3: Docker permission denied inside Jenkins pipeline
* **Root Cause:** Jenkins container needs access to the host Docker daemon socket.
* **Fix:** Ensure `docker-compose.yml` mounts `/var/run/docker.sock:/var/run/docker.sock` and Jenkins runs with privileged access (already configured in your repository's `docker-compose.yml`).

---

## 9. TEARDOWN & CLEANUP (100% ZERO RESIDUAL COST GUARANTEE)

When your academic evaluation, viva, or testing is complete, destroy all cloud resources with **one click** to ensure you are never billed:

### Step 9.1: Empty the S3 Bucket (Required before deleting stack)
AWS prevents deleting non-empty S3 buckets:
```bash
# From EC2 terminal or AWS CloudShell:
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name hn-hit-predictor-stack --query "Stacks[0].Outputs[?OutputKey=='S3ArtifactsBucketName'].OutputValue" --output text)
aws s3 rm s3://$BUCKET_NAME --recursive
```
*(Or in AWS Console: Open **S3** > select bucket > click **Empty** > type `permanently delete`)*.

### Step 9.2: Delete the CloudFormation Stack

#### Via AWS Console:
1. Open **CloudFormation Console**.
2. Select `hn-hit-predictor-stack`.
3. Click the **Delete** button at the top right.
4. Confirm deletion.

#### Via AWS CLI:
```bash
aws cloudformation delete-stack --stack-name hn-hit-predictor-stack
```

**What CloudFormation deletes automatically:**
* Terminating and removing the EC2 instance.
* Deleting the 20 GB EBS volume.
* Deleting the Security Group.
* Deleting the IAM Role and Instance Profile.
* Deleting the CloudWatch Alarms and Log Group.
* Deleting the S3 Bucket.

Within 3 minutes, the stack status will show `DELETE_COMPLETE`. Your AWS balance will remain **$0.00**.
