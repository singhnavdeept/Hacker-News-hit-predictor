#!/bin/bash
set -ex

# Update OS and install prerequisites
dnf update -y
dnf install -y docker git amazon-cloudwatch-agent

# Enable and start Docker daemon
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# Configure 2GB swap space for t3.micro memory stabilization
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Configure Amazon CloudWatch Agent for custom metrics and structured logs
cat << 'EOF' > /opt/aws/amazon-cloudwatch-agent/bin/config.json
{
  "agent": {
    "metrics_collection_interval": 60
  },
  "metrics": {
    "metrics_collected": {
      "mem": {
        "measurement": ["mem_used_percent"]
      },
      "disk": {
        "measurement": ["used_percent"],
        "resources": ["/"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/messages",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/system"
          },
          {
            "file_path": "/var/log/hn-hit-predictor.log",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/app-json"
          }
        ]
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json -s

echo "Base bootstrap finished. Instance ready for SSM-managed deployments."
