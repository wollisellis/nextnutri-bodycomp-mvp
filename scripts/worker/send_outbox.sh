#!/usr/bin/env bash
set -euo pipefail
cd /home/unienutri/.openclaw/workspace/nextnutri-bodycomp-mvp
OUT="reports/outbox_telegram.txt"
if [[ ! -s "$OUT" ]]; then
  exit 0
fi
cat "$OUT"
# clear after printing (cron will send what it printed)
: > "$OUT"
