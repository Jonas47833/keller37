#!/bin/sh
# Führt den In-Browser-Selbsttest headless aus und gibt das Ergebnis aus.
# Chrome: K37_CHROME oder erster Fund aus den ueblichen Pfaden (macOS, ~/.local/opt, apt)
for c in "$K37_CHROME" "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "$HOME/.local/opt/chrome-linux64/chrome" /usr/bin/google-chrome /usr/bin/chromium; do
  [ -n "$c" ] && [ -x "$c" ] && CHROME="$c" && break
done
DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$CHROME" --headless=new --disable-gpu --virtual-time-budget=30000 \
  --dump-dom "file://$DIR/keller37.html?selftest&fresh" 2>/dev/null | grep -o 'data-selftest="[^"]*"'
