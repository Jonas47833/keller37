#!/bin/sh
# Führt den In-Browser-Selbsttest headless aus und gibt das Ergebnis aus.
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$CHROME" --headless=new --disable-gpu --virtual-time-budget=4000 \
  --dump-dom "file://$DIR/keller37.html?selftest&fresh" 2>/dev/null | grep -o 'data-selftest="[^"]*"'
