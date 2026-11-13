# DevSecOps Automated Security Scan Script (Checkov + Trivy)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    DevSecOps Security Audits (Checkov & Trivy)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspacePath = $PSScriptRoot -replace "\\scripts$", ""

Write-Host "`n[1/2] Scanning CloudFormation Template with Checkov (IaC Security)..." -ForegroundColor Yellow
docker run --rm -v "${WorkspacePath}:/work" bridgecrew/checkov:latest -f /work/cloudformation/infra.yaml --framework cloudformation

Write-Host "`n[2/2] Scanning Docker Image with Aqua Trivy (Container Security)..." -ForegroundColor Yellow
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL hn-hit-predictor:latest

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " DevSecOps Scans Completed Successfully!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
