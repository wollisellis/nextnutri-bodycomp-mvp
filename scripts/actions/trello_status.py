#!/usr/bin/env python3
"""Trello status snapshot for Faraday Ops.

Reads board/list ids from reports/trello_faraday_ops.json.
Auth comes from OpenClaw env vars:
  - TRELLO_API_KEY (or TRELLO_KEY)
  - TRELLO_TOKEN

Usage:
  python scripts/actions/trello_status.py
  python scripts/actions/trello_status.py --json
  python scripts/actions/trello_status.py --limit 10

Output: compact, chat-friendly.
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


def _req(path: str, *, key: str, token: str, params: dict | None = None):
    params = dict(params or {})
    params["key"] = key
    params["token"] = token
    url = f"{TRELLO_API}{path}?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_cfg() -> dict:
    here = Path(__file__).resolve()
    cfg_path = here.parents[2] / "reports" / "trello_faraday_ops.json"
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    oc = _openclaw_vars()
    # Prefer OpenClaw config over shell env to avoid stale exported tokens.
    key = oc.get("TRELLO_API_KEY") or oc.get("TRELLO_KEY") or os.getenv("TRELLO_API_KEY") or os.getenv("TRELLO_KEY")
    token = oc.get("TRELLO_TOKEN") or os.getenv("TRELLO_TOKEN")
    if not key or not token:
        print("Missing TRELLO_API_KEY/TRELLO_TOKEN (env or ~/.openclaw/openclaw.json)", file=sys.stderr)
        return 2

    cfg = _load_cfg()
    board_url = cfg.get("boardUrl")
    lists = cfg.get("lists") or {}

    out = {"boardUrl": board_url, "lists": {}}
    for list_name, list_id in lists.items():
        cards = _req(
            f"/lists/{list_id}/cards",
            key=key,
            token=token,
            params={"fields": "name,url,due,closed", "filter": "open"},
        )
        cards = [c for c in cards if not c.get("closed")]
        out["lists"][list_name] = {
            "count": len(cards),
            "top": [
                {
                    "name": c.get("name"),
                    "url": c.get("url"),
                    "due": c.get("due"),
                }
                for c in cards[: max(0, args.limit)]
            ],
        }

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    # human output
    print(f"Trello board: {board_url}")
    for ln in ["Inbox", "Todo", "Doing", "Done"]:
        if ln not in out["lists"]:
            continue
        info = out["lists"][ln]
        print(f"\n{ln} ({info['count']}):")
        for item in info["top"]:
            print(f"- {item['name']} ({item['url']})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
