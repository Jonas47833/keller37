#!/usr/bin/env python3
"""
Handy-Ansicht (400x800, DPR 2) fuer KELLER 37 pruefen: Screenshots aller Screens
plus harte Layout-Checks (keine Ueberbreite, Tap-Ziele >= 40 px, Roulette-Tisch hochkant,
Einsatz-Leiste in festen Zeilen, Header klappt beim Scrollen ein).

Nutzt den CDP-Helfer aus tests/playtest-story.py. Aufruf:
    python3 tests/mobile-check.py                 # Screenshots nach /tmp/k37mobile
    K37_SHOTS=docs/superpowers/screenshots python3 tests/mobile-check.py
Env: K37_PORT (Standard 9361), K37_PROFILE, K37_SHOTS.
"""
import asyncio
import importlib.util
import json
import os
import sys

sys.argv = [sys.argv[0]]
os.environ.setdefault("K37_PORT", "9361")
os.environ.setdefault("K37_PROFILE", "/tmp/k37mobile-profile")
os.environ.setdefault("K37_SHOTS", "/tmp/k37mobile")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("pt", os.path.join(ROOT, "tests", "playtest-story.py"))
pt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pt)
URL = "file://" + os.path.join(ROOT, "keller37.html")
MIN_TAP = 40

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("%s %s%s" % ("OK  " if ok else "FAIL", name, (" - " + str(detail)) if detail else ""))


# Screens im freien Spiel; jobs ist Story-only und wird unten separat geladen
FREE_SCREENS = ["hub", "slots", "blackjack", "roulette", "horses", "russian", "postman", "finance", "invest", "life", "stadt", "skills", "royal", "craps", "megaslots", "wheel"]

TAP_SELECTORS = [".side-tabs button", ".icon-btn", ".chip", ".bet-bar .btn", ".bet-field button", ".rcell", ".table-bar .btn", ".door", ".side-btn"]

CHECK_JS = r"""
(function(sel, minTap){
  const out = { overflow: document.documentElement.scrollWidth - window.innerWidth, small: [] };
  for (const s of sel) for (const el of document.querySelectorAll(s)) {
    if (el.offsetParent === null) continue;   // unsichtbar
    const r = el.getBoundingClientRect();
    if (r.width < minTap || r.height < minTap) out.small.push(s + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' "' + (el.textContent || '').trim().slice(0, 12) + '"');
  }
  return out;
})(%s, %d)
"""


async def check_screen(cdp, name):
    res = await cdp.eval(CHECK_JS % (json.dumps(TAP_SELECTORS), MIN_TAP), await_promise=False) or {}
    record("%s: keine horizontale Ueberbreite" % name, res.get("overflow", 1) <= 0, "overflow=%s" % res.get("overflow"))
    record("%s: Tap-Ziele >= %d px" % (name, MIN_TAP), not res.get("small"), res.get("small"))


async def main():
    cdp = pt.CDP()
    cdp.launch()
    await cdp.connect()
    await cdp.set_mobile(True)
    try:
        for sc in FREE_SCREENS:
            await cdp.navigate(URL + "?fresh&mode=free&screen=" + sc, wait=1.4)
            await cdp.eval("localStorage.removeItem('keller37.meta')", await_promise=False)
            await check_screen(cdp, sc)
            await cdp.screenshot("mobile-%s.png" % sc)

        # Roulette: Tisch hochkant (1-2-3 nebeneinander, 4 darunter), Drehen breit
        await cdp.navigate(URL + "?fresh&mode=free&screen=roulette", wait=1.4)
        r = await cdp.eval(r"""
          (function(){ const b = (k) => document.querySelector('.rcell[data-key="'+k+'"]').getBoundingClientRect();
            const n1 = b('n1'), n2 = b('n2'), n3 = b('n3'), n4 = b('n4'), zero = b('n0'), rot = b('red'), schwarz = b('black');
            const table = document.querySelector('.rtable').getBoundingClientRect();
            const spin = document.querySelector('#btnSpin').getBoundingClientRect();
            const bar = document.querySelector('.table-bar').getBoundingClientRect();
            const wheel = document.querySelector('#wheelCanvas').getBoundingClientRect();
            return { row: n1.left < n2.left && n2.left < n3.left && Math.abs(n1.top - n3.top) < 2, below: n4.top > n1.bottom - 1,
                     zeroWide: zero.width > table.width * 0.9, outside: rot.top > b('n36').bottom - 1 && Math.abs(rot.top - schwarz.top) < 2,
                     spinWide: spin.width > bar.width * 0.9, spinLast: spin.top > rot.bottom, wheel: Math.round(wheel.width) }; })()
        """, await_promise=False) or {}
        record("roulette: Zahlen 1-2-3 nebeneinander, 4 darunter", r.get("row") and r.get("below"), r)
        record("roulette: Zero ueber volle Breite, Aussenfelder unter 36", r.get("zeroWide") and r.get("outside"), r)
        record("roulette: Drehen breit und unter dem Tisch", r.get("spinWide") and r.get("spinLast"), r)
        record("roulette: Rad verkleinert (< 260 px)", 0 < r.get("wheel", 999) < 260, "wheel=%s" % r.get("wheel"))
        await cdp.eval("window.scrollTo(0, 700)", await_promise=False)
        await asyncio.sleep(0.5)
        await cdp.screenshot("mobile-roulette-table.png")
        s = await cdp.eval("({scrolled: document.body.classList.contains('scrolled'), h: document.querySelector('.wallet').getBoundingClientRect().height})", await_promise=False) or {}
        record("header: Mittelzeile beim Scrollen eingeklappt", s.get("scrolled") and s.get("h", 999) < 80, s)
        await cdp.eval("window.scrollTo(0, 0)", await_promise=False)
        await asyncio.sleep(0.5)
        s = await cdp.eval("({scrolled: document.body.classList.contains('scrolled'), h: document.querySelector('.wallet').getBoundingClientRect().height})", await_promise=False) or {}
        record("header: oben wieder ausgeklappt", not s.get("scrolled") and s.get("h", 0) > 80, s)

        # Einsatz-Leiste: Stepper und Hauptknopf volle Breite, Chips in einer Zeile dazwischen
        await cdp.navigate(URL + "?fresh&mode=free&screen=slots", wait=1.4)
        b = await cdp.eval(r"""
          (function(){ const bar = document.querySelector('.bet-bar').getBoundingClientRect();
            const f = document.querySelector('.bet-field').getBoundingClientRect(); const btn = document.querySelector('#btnSpin').getBoundingClientRect();
            const chips = [...document.querySelectorAll('.bet-bar .chip')].map(c => c.getBoundingClientRect());
            return { field: f.width > bar.width * 0.9, btn: btn.width > bar.width * 0.9 && btn.height >= 46,
                     chipsRow: chips.every(c => Math.abs(c.top - chips[0].top) < 2) && chips[0].top > f.bottom - 1 && btn.top > chips[0].bottom - 1 }; })()
        """, await_promise=False) or {}
        record("slots: Einsatz-Leiste in drei Zeilen (Stepper / Chips / Drehen)", b.get("field") and b.get("btn") and b.get("chipsRow"), b)

        # Tab-Leiste: Icons + Label, kein Umbruch
        t = await cdp.eval(r"""
          (function(){ const tabs = [...document.querySelectorAll('.side-tabs button')];
            return { n: tabs.length, icons: tabs.filter(b => b.querySelector('.tab-ic')).length,
                     oneRow: tabs.every(b => Math.abs(b.getBoundingClientRect().top - tabs[0].getBoundingClientRect().top) < 2),
                     h: Math.round(document.querySelector('.side-tabs').getBoundingClientRect().height) }; })()
        """, await_promise=False) or {}
        record("tabs: alle mit Icon, eine Zeile, >= 52 px", t.get("n", 0) >= 4 and t.get("icons") == t.get("n") and t.get("oneRow") and t.get("h", 0) >= 52, t)

        # Zone: Royal-Screens setzen body[data-zone=royal], Keller-Screens keller
        zones = {}
        for sc in ["hub", "royal", "craps", "megaslots", "wheel", "stadt"]:
            await cdp.navigate(URL + "?fresh&mode=free&screen=" + sc, wait=1.2)
            zones[sc] = await cdp.eval("document.body.dataset.zone", await_promise=False)
        record("zone: Royal-Screens royal, Keller-Screens keller",
               all(zones[k] == "royal" for k in ["royal", "craps", "megaslots", "wheel"]) and zones["hub"] == "keller" and zones["stadt"] == "keller", zones)

        # Story: Pinnwand + Tagesleiste
        await cdp.navigate(URL + "?fresh&story=schuld&day=1", wait=2.0)
        await cdp.inject_helpers()
        await cdp.advance_cutscene()
        await asyncio.sleep(0.4)
        await check_screen(cdp, "story-jobs")
        await cdp.screenshot("mobile-story-jobs.png")

        # Desktop-Gegenprobe: Roulette-Tisch bleibt 13 Spalten breit
        await cdp.set_mobile(False)
        await cdp.navigate(URL + "?fresh&mode=free&screen=roulette", wait=1.4)
        d = await cdp.eval(r"""
          (function(){ const b = (k) => document.querySelector('.rcell[data-key="'+k+'"]').getBoundingClientRect();
            return { rowOf3: Math.abs(b('n3').top - b('n6').top) < 2 && b('n6').left > b('n3').left, colOf3: b('n1').top > b('n2').top && b('n2').top > b('n3').top,
                     rot: b('red').left > b('n0').right - 1 && b('red').left < b('n3').left + 2 }; })()
        """, await_promise=False) or {}
        record("desktop: Roulette-Tisch unveraendert quer (3 Reihen x 12)", d.get("rowOf3") and d.get("colOf3") and d.get("rot"), d)

        errs = [e for e in cdp.console_errors if "unlocked" not in e]
        record("keine Konsolenfehler", not errs, errs[:3])
    finally:
        cdp.proc.terminate()

    failed = [n for n, ok in RESULTS if not ok]
    print("\n%d Checks, %d fehlgeschlagen" % (len(RESULTS), len(failed)))
    for n in failed:
        print("  FAIL", n)
    sys.exit(1 if failed else 0)


asyncio.run(main())
