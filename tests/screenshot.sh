#!/bin/sh
# Nutzung: tests/screenshot.sh out.png "?screen=slots"
# Chrome: K37_CHROME oder erster Fund aus den ueblichen Pfaden (macOS, ~/.local/opt, apt)
for c in "$K37_CHROME" "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "$HOME/.local/opt/chrome-linux64/chrome" /usr/bin/google-chrome /usr/bin/chromium; do
  [ -n "$c" ] && [ -x "$c" ] && CHROME="$c" && break
done
DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,900 \
  --virtual-time-budget=4000 --screenshot="$1" "file://$DIR/keller37.html$2" 2>/dev/null
echo "Screenshot: $1"
