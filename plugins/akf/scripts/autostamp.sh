#!/bin/bash
# PostToolUse auto-stamp: reads the hook payload from stdin and stamps the
# written file with AKF trust metadata. A provenance hook must never block
# the agent — always exits 0, silent when akf isn't installed.
if command -v akf >/dev/null 2>&1; then
  akf hook claude 2>/dev/null || true
elif command -v python3 >/dev/null 2>&1; then
  python3 -m akf hook claude 2>/dev/null || true
fi
exit 0
