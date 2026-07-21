#!/usr/bin/env python3
"""Entry point: start the Xiangqi competition server.

Usage:
    python run_server.py --host 0.0.0.0 --port 8000

The admin dashboard is at http://<host>:<port>/admin
Players connect at    http://<host>:<port>/player
"""

import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Online Xiangqi competition server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (0.0.0.0 to accept LAN/internet connections)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Auto-reload on code changes (development only)")
    args = parser.parse_args()

    uvicorn.run("server.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
