# 📖 HN Hit Predictor — Operational Runbook

> **Target:** SRE & On-Call Engineers  
> **Service:** `hn-hit-predictor-api` (Port 8000)  
> **AWS Account Region:** `ap-south-1` (Mumbai)  
> **Access Method:** AWS Systems Manager (SSM) Session Manager (Zero open SSH ports)

---

## 1. Quick Reference & System Topology

| Resource | Value / Access Path |
|---|---|
| **Public API** | `http://<EC2_PUBLIC_IP>:8000` |
| **Deploy Verification** | `http://<EC2_PUBLIC_IP>:8000/version` |
| **Health Check** | `http://<EC2_PUBLIC_IP>:8000/health` |
| **Metrics Endpoint** | `http://<EC2_PUBLIC_IP>:8000/metrics` |
| **Interactive Docs** | `http://<EC2_PUBLIC_IP>:8000/docs` |
| **CloudWatch Log Group** | `/aws/ec2/hn-hit-predictor-prod` |
| **CloudWatch Dashboard** | `hn-hit-predictor-prod-dashboard` |
| **SSM Terminal Session** | `aws ssm start-session --target <INSTANCE_ID>` |

---

## 2. Alarm Triage & Incident Response

### 🚨 Alarm 1: `HighCPU` (> 80% for 10 minutes)
1. **Connect via AWS SSM:**
   ```bash
   aws ssm start-session --target $(tofu -chdir=tofu/environments/prod output -raw instance_id)
   ```
2. **Inspect Top CPU Processes:**
   ```bash
   top -b -n 1 | head -n 20
   docker stats --no-stream
   ```
3. **Remediation:**
   - If container has runaway thread:
     ```bash
     docker restart hn-hit-predictor-api
     ```
   - Check if swap space is active:
     ```bash
     free -h && swapon --show
     ```

---

### 🚨 Alarm 2: `High5xxRate` (≥ 5 Server Errors in 5 min)
1. **Query CloudWatch JSON Logs:**
   Navigate to AWS Console ➔ CloudWatch ➔ Log Groups ➔ `/aws/ec2/hn-hit-predictor-prod`.
2. **Run CloudWatch Insights Query:**
   ```sql
   fields @timestamp, status, path, latency_ms, message
   | filter status >= 500
   | sort @timestamp desc
   | limit 25
   ```
3. **Remediation:**
   - Check if `model.joblib` artifact is missing or corrupted:
     ```bash
     docker exec hn-hit-predictor-api ls -lh /workspace/models/model.joblib
     ```
   - If regression was introduced in the latest release, trigger **Fast Rollback** (Section 3).

---

### 🚨 Alarm 3: `HealthCheckFailing` (> 1 failure in 1 min)
1. **Verify Local Container State:**
   ```bash
   docker ps -a
   docker logs --tail 50 hn-hit-predictor-api
   ```
2. **Test Container Loopback:**
   ```bash
   curl -i http://localhost:8000/health
   ```
3. **Restart Service:**
   ```bash
   docker restart hn-hit-predictor-api
   ```

---

### 🚨 Alarm 4: `BillingAlert` (Estimated Charges > $1.00 USD)
1. Navigate to **AWS Billing & Cost Management** ➔ **Cost Explorer**.
2. Group by **Usage Type** to identify billing source:
   - Ensure old unattached EBS volumes or Elastic IPs are deleted.
   - Ensure NAT Gateways or load balancers were not provisioned outside OpenTofu.

---

## 3. Fast Rollback Procedures

### Method A: 1-Click Rollback via GitHub Actions (Recommended)
1. Go to GitHub Repository ➔ **Actions** tab.
2. Select workflow: **Fast Production Rollback**.
3. Click **Run workflow**:
   - `target_git_sha`: Enter previous known-good commit hash (e.g. `3d1c76f...`) or tag.
   - `reason`: e.g. "5xx error rate spike in build".
4. The workflow will restart the container via AWS SSM and verify `/version`.

### Method B: Emergency CLI Rollback via AWS SSM
If GitHub Actions is unavailable, execute via AWS CLI:
```bash
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=hn-hit-predictor-prod-server" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" --output text)

# Roll back container to previous image tag
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=[
    "docker rm -f hn-hit-predictor-api || true",
    "docker run -d --name hn-hit-predictor-api --restart unless-stopped -p 8000:8000 -e ENV=prod hn-hit-predictor:<PREVIOUS_TAG>"
  ]'
```

---

## 4. Disaster Recovery & Clean Teardown

### Full Stack Recreation from Scratch:
```bash
# 1. Initialize bootstrap (S3 State + DynamoDB Locks)
cd tofu/bootstrap
tofu init && tofu apply -auto-approve

# 2. Deploy Production Environment
cd ../environments/prod
tofu init
tofu apply -auto-approve
```

### Complete Teardown (Zero Cost Footprint):
When the project or testing window concludes:
```bash
cd tofu/environments/prod
tofu destroy -auto-approve

cd ../../bootstrap
tofu destroy -auto-approve
```
