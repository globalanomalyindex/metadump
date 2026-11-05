#!/usr/bin/env bash
# Render each t3 hero to a 1440x900 PNG with headless Chrome (no network needed: files are self-contained).
set -u
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cd "$(dirname "$0")"
mkdir -p shots
for f in runs/*.html; do
  n=$(basename "$f" .html)
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
    --user-data-dir="$(mktemp -d)" --window-size=1280,800 --virtual-time-budget=3000 \
    --screenshot="$PWD/shots/$n.png" "file://$PWD/$f" >/dev/null 2>&1
  echo "$n $(wc -c < shots/$n.png 2>/dev/null || echo FAILED)"
done
