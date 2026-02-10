#!/usr/bin/env python3
"""Create a Trello card in the Faraday Ops Inbox.

Usage:
  python scripts/actions/trello_add_inbox.py "title" --desc "..."

Auth via env:
  TRELLO_API_KEY (or TRELLO_KEY)
  TRELLO_TOKEN

Board/list ids from reports/trello_faraday_ops.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def _openclaw_vars() -> dict:
    """Read env vars from OpenClaw config (so scripts work without exported shell env)."""
    p = Path.home() / ".openclaw" / "openclaw.json"
    if not p.exists():
        return {}
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
        return (cfg.get("env") or {}).get("vars") or {}
    except Exception:
        return {}

TRELLO_API = "https://api.trello.com/1"


def _load_cfg() -> dict:
    here = Path(__file__).resolve()
    cfg_path = here.parents[2] / "reports" / "trello_faraday_ops.json"
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _post(path: str, *, key: str, token: str, data: dict):
    params = {"key": key, "token": token}
    url = f"{TRELLO_API}{path}?" + urllib.parse.urlencode(params)
    body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--desc", default="")
    args = ap.parse_args()

    oc = _openclaw_vars()
    # Prefer OpenClaw config over shell env to avoid stale exported tokens.
    key = oc.get("TRELLO_API_KEY") or oc.get("TRELLO_KEY") or os.getenv("TRELLO_API_KEY") or os.getenv("TRELLO_KEY")
    token = oc.get("TRELLO_TOKEN") or os.getenv("TRELLO_TOKEN")
    if not key or not token:
        print("Missing TRELLO_API_KEY/TRELLO_TOKEN (env or ~/.openclaw/openclaw.json)", file=sys.stderr)
        return 2

    cfg = _load_cfg()
    inbox_id = (cfg.get("lists") or {}).get("Inbox")
    if not inbox_id:
        print("Missing Inbox list id in trello_faraday_ops.json", file=sys.stderr)
        return 2

    card = _post(
        "/cards",
        key=key,
        token=token,
        data={"idList": inbox_id, "name": args.title, "desc": args.desc},
    )

    print(card.get("url"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
