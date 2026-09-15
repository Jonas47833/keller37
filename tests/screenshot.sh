#!/bin/sh
# Nutzung: tests/screenshot.sh out.png "?screen=slots"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,900 \
  --virtual-time-budget=4000 --screenshot="$1" "file://$DIR/keller37.html$2" 2>/dev/null
echo "Screenshot: $1"
