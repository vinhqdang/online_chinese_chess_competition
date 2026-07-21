#!/bin/bash
# Runs as root on a fresh Amazon Linux 2023 instance (via SSM Run Command).
# Expects XIANGQI_BUCKET to be set to the S3 bucket holding app.tar.gz
# (the instance's IAM role must grant s3:GetObject on that bucket).
set -euxo pipefail

: "${XIANGQI_BUCKET:?XIANGQI_BUCKET must be set}"

dnf install -y python3.11 python3.11-pip tar gzip || dnf install -y python3 python3-pip tar gzip

mkdir -p /opt/xiangqi/app
aws s3 cp "s3://${XIANGQI_BUCKET}/app.tar.gz" /opt/xiangqi/app.tar.gz
tar xzf /opt/xiangqi/app.tar.gz -C /opt/xiangqi/app

cd /opt/xiangqi/app
(command -v python3.11 >/dev/null && python3.11 -m venv .venv) || python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

install -m 0755 deploy/aws/idle_shutdown.sh /opt/xiangqi/idle_shutdown.sh
cp deploy/aws/systemd/*.service deploy/aws/systemd/*.timer /etc/systemd/system/
chown -R ec2-user:ec2-user /opt/xiangqi

systemctl daemon-reload
systemctl enable --now xiangqi-server.service
systemctl enable --now xiangqi-bot-random.service
systemctl enable --now xiangqi-bot-greedy.service
systemctl enable --now xiangqi-auto-admin.service
systemctl enable --now xiangqi-idle-check.timer

echo "XIANGQI_DEPLOY_COMPLETE"
