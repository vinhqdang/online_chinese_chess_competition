# AWS demo deployment

Runs the server plus the two test bots (looping bot-vs-bot matches via
`auto_admin.py`, restarted forever) on a single cheap EC2 instance, with an
idle-shutdown timer that stops the instance after the server has had no
real HTTP traffic for 10 minutes (bot WebSocket traffic doesn't count —
see `idle_shutdown.sh`). This is a demo/reference deployment, not meant to
double as a production competition host: with both seats permanently
occupied by bots, no human player can join unless the admin kicks a bot
first from `/admin`.

## How code gets onto the instance

No SSH key pair or open SSH port is used. The app is tarred up, uploaded
to a private S3 bucket, and pulled onto the instance via `aws s3 cp` using
an IAM instance role (`s3:GetObject` on that one bucket only). Setup runs
via AWS Systems Manager Run Command (`bootstrap.sh`), which the SSM Agent
preinstalled on Amazon Linux 2023 executes as root — this only needs
outbound HTTPS to AWS's SSM/S3 endpoints, no inbound SSH.

## Files

- `bootstrap.sh` — one-shot setup script (installs Python, pulls and
  extracts the app, creates a venv, installs the systemd units below).
- `systemd/xiangqi-server.service` — the FastAPI/uvicorn server.
- `systemd/xiangqi-bot-random.service`, `xiangqi-bot-greedy.service` — the
  two demo bots.
- `systemd/xiangqi-auto-admin.service` — runs `auto_admin.py`, which
  configures + starts + resets matches in a loop so there's always a live
  game to watch.
- `systemd/xiangqi-idle-check.timer` / `.service` — every minute, checks
  how long it's been since the last HTTP request; past 10 minutes idle,
  runs `shutdown -h now`, which AWS treats as an instance Stop (billing
  stops; the tiny EBS volume cost remains).
- `idle_shutdown.sh` — the actual idle check, reading the mtime of
  `/opt/xiangqi/last_activity` (touched by `server/main.py`'s
  `XIANGQI_ACTIVITY_FILE`-driven middleware on every HTTP request).

## Restarting after an idle shutdown

The instance stops itself; it does not terminate (no data/config is
lost) and nothing currently auto-starts it back up on demand. To resume:

```bash
aws ec2 start-instances --instance-ids <instance-id>
```

then wait ~30-60s for boot and the systemd services to come up.
