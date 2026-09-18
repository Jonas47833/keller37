#!/usr/bin/env python3
"""
Desktop-Gegenprobe: rendert Screens aus git `main` und aus der Arbeitskopie (1280x900) und zaehlt
Pixel mit Differenz > 24 (RGB-Maximum). Standard-Screens sind Keller-Screens, die sich NICHT aendern duerfen.
    python3 tests/desktop-diff.py                # hub roulette slots finance
    python3 tests/desktop-diff.py hub stadt      # eigene Liste
Exit 1, wenn ein Screen mehr als K37_DIFF_MAX (Standard 0) abweichende Pixel hat.
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = next(c for c in [os.environ.get("K37_CHROME", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                          os.path.expanduser("~/.local/opt/chrome-linux64/chrome"), "/usr/bin/google-chrome", "/usr/bin/chromium"]
              if c and os.path.exists(c))
SCREENS = sys.argv[1:] or ["hub", "roulette", "slots", "finance"]
MAX = int(os.environ.get("K37_DIFF_MAX", "0"))
tmp = tempfile.mkdtemp(prefix="k37diff-")
old = os.path.join(tmp, "old.html")
with open(old, "wb") as f:
    f.write(subprocess.check_output(["git", "-C", ROOT, "show", "main:keller37.html"]))
new = os.path.join(ROOT, "keller37.html")

def shot(html, sc, out):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1280,900",
                    "--virtual-time-budget=4000", "--screenshot=" + out, "file://%s?fresh&mode=free&screen=%s" % (html, sc)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

bad = 0
for sc in SCREENS:
    a, b = os.path.join(tmp, "old-%s.png" % sc), os.path.join(tmp, "new-%s.png" % sc)
    shot(old, sc, a); shot(new, sc, b)
    d = ImageChops.difference(Image.open(a).convert("RGB"), Image.open(b).convert("RGB"))
    px = sum(1 for p in d.getdata() if max(p) > 24)
    ok = px <= MAX
    bad += 0 if ok else 1
    print("%s %-10s px>24: %d" % ("OK  " if ok else "FAIL", sc, px))
print("Screenshots:", tmp)
sys.exit(1 if bad else 0)
