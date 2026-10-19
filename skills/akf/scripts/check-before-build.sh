#!/usr/bin/env bash
# Read-only: runs `akf check` on each file and lists the ones that need re-verification.
# Usage: check-before-build.sh <file>...
# Exit: 0 all OK, 1 something needs re-verification, 127 akf not installed.
set -u

if ! command -v akf >/dev/null 2>&1; then
  echo "akf not found. Install with: pip install akf" >&2
  exit 127
fi
if [ "$#" -eq 0 ]; then
  echo "usage: $0 <file>..." >&2
  exit 2
fi

need=0
for f in "$@"; do
  out=$(akf check "$f" 2>&1)
  rc=$?
  echo "$out"
  [ "$rc" -ne 0 ] && need=1
done

if [ "$need" -eq 1 ]; then
  echo "-- some files are LOW, STALE, or UNSTAMPED: verify them before building on them" >&2
  exit 1
fi
exit 0
