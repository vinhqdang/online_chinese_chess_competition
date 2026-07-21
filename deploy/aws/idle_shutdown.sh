#!/bin/bash
# Stops this EC2 instance once no real HTTP traffic (page loads, API calls)
# has hit the server for IDLE_LIMIT_SEC seconds. Bot-vs-bot WebSocket
# traffic is deliberately NOT counted as activity -- the demo bots run
# forever on their own, so counting them would mean the box never shuts
# down. "Idle" here means "nobody opened the page recently."
#
# Relies on the default EBS-backed EC2 behavior where an in-guest
# `shutdown -h now` is treated by AWS as an instance Stop (not just a
# guest poweroff), so this needs no AWS credentials or IAM permissions.
set -euo pipefail

ACTIVITY_FILE="/opt/xiangqi/last_activity"
IDLE_LIMIT_SEC="${XIANGQI_IDLE_LIMIT_SEC:-600}"

if [ ! -f "$ACTIVITY_FILE" ]; then
  logger "xiangqi-idle-check: no activity file yet, skipping"
  exit 0
fi

now=$(date +%s)
last=$(stat -c %Y "$ACTIVITY_FILE")
idle=$((now - last))

if [ "$idle" -ge "$IDLE_LIMIT_SEC" ]; then
  logger "xiangqi-idle-check: ${idle}s since last HTTP activity (limit ${IDLE_LIMIT_SEC}s), shutting down"
  /sbin/shutdown -h now
else
  logger "xiangqi-idle-check: ${idle}s idle, under limit ${IDLE_LIMIT_SEC}s"
fi
