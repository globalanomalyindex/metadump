#!/usr/bin/env bash
# Screenshot each run at desktop (1280x800) and mobile (390x844) width with headless Chrome. Files are self-contained.
set -u
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cd "$(dirname "$0")"
mkdir -p shots
for f in runs/*.html; do
  n=$(basename "$f" .html)
  for spec in desktop:1280,800 mobile:390,844; do
    name=${spec%%:*}; size=${spec#*:}
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
      --user-data-dir="$(mktemp -d)" --window-size=$size --virtual-time-budget=3000 \
      --screenshot="$PWD/shots/$n-$name.png" "file://$PWD/$f" >/dev/null 2>&1
    echo "$n-$name $(wc -c < shots/$n-$name.png 2>/dev/null || echo FAILED)"
  done
done
