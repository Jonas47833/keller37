# Casino Royal Look Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das Casino Royal (Lobby, Mega Seven, Craps, Glücksrad) bekommt einen Art-déco-Look in Gold und Schwarz, der die ganze Seite umschaltet, dazu die Royal-Fassade in der Stadt, ein grafisches Kater-HUD mit Zitter-Tag, ein Kronleuchter-Cutscene-Hintergrund und Gewinn-/Verlust-Momente – ohne dass sich der Keller am Desktop um ein Pixel ändert.

**Architecture:** `UI.show` setzt `body[data-zone]` (`keller`|`royal`) und blendet beim Zonenwechsel einen Gold-Vorhang (`#zonefade`). Alle Shell-Änderungen (Kopfzeile, Seitenleiste, Chips, Knöpfe, Tafeln) hängen an `body[data-zone="royal"]`; die drei Royal-Spiele und die Lobby existieren nur in der Zone und werden direkt umgestylt. Reine Helfer (`RoyalRules.zoneFor`, `leberTone`, `deckelMarks`, `wheelTone`) liegen im Block `royal-rules` und werden im Node-Selftest geprüft; DOM-Verhalten prüfen `tests/mobile-check.py` und ein neues Playtest-Szenario.

**Tech Stack:** Eine HTML-Datei (`keller37.html`, Vanilla JS/CSS, Google Font „Cinzel"), Node-Selftest (`tests/run-selftest.mjs`), Browser-Selftest (`tests/dom-selftest.sh`), CDP-Playtest (`tests/playtest-story.py`), Handy-Check (`tests/mobile-check.py`), Screenshot-Diff mit Pillow.

**Spec:** `docs/superpowers/specs/2026-09-18-casino-royal-look-design.md`

## Global Constraints

- Eine Datei `keller37.html`, Deutsch, keine Bilddateien – Texturen nur als CSS-Verläufe oder DOM-Elemente.
- Schrift „Cinzel" (Google Fonts, 400/700) zusätzlich laden; Fallback `Georgia, "Times New Roman", serif`; Zahlen bleiben Courier Prime.
- Shell-Regeln (Kopfzeile, Seitenleiste, Chips, Knöpfe, Tafeln, Status, `.neon`, Zettel) hängen ausnahmslos an `body[data-zone="royal"]`. Der Desktop-Keller bleibt pixelidentisch: Screenshot-Diff `main` vs. Branch auf `hub`, `roulette`, `slots`, `finance` muss 0 Pixel > 24 Differenz ergeben (Skript in Task 1).
- Handy (≤ 760 px): kein Backdrop-Blur, kein Filmkorn, Opacity-Wechsel, Tap-Ziele ≥ 40 px, keine horizontale Überbreite (`tests/mobile-check.py` muss grün bleiben). Lauflichter, Lichtläufe, Goldregen nur unter `@media (hover: hover)`.
- `prefers-reduced-motion: reduce`: alle Royal-Animationen aus (Lauflicht, Lichtlauf, Zittern, Goldregen, Blackout-Fade, Vorhang werden sofortige Zustandswechsel).
- Performance-Budget: höchstens drei geschichtete Verläufe auf großen Flächen pro Screen, kein `filter: blur` auf dem Handy, keine Dauer-Animation außer Marquee-Lauflicht am Desktop.
- Keine Änderung an Spielregeln, Auszahlungen, Story-Texten, Story-Logik.
- Tests vor jedem Commit: `node tests/run-selftest.mjs` und `sh tests/dom-selftest.sh` grün.
- Commit-Nachrichten Deutsch, Format `feat(royal): …` / `test(royal): …` / `docs(royal): …`, jeweils mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Für alle Shell-Kommandos mit Umlauten/typografischen Zeichen Python-Skripte mit dreifachen Anführungszeichen (`'''…'''`) verwenden – die geraden Anführungszeichen `"` in deutschen Texten (`„…"`) brechen `"…"`-Strings.

---

## Dateistruktur

- `keller37.html` – alle Änderungen:
  - `<head>`: Font-Link.
  - CSS-Abschnitt (vor `/* -- Reduced Motion -- */`, Zeile ~470): neuer Block `/* ==== ROYAL ZONE ==== */` für Tokens, Shell, Vorhang, Lobby, Spiele, Fassade, Kater-HUD, Cutscene.
  - Block `ui`: `UI.show` (Zone + Vorhang), `UI.mountShell` (`.brand-sub`), `UI.renderWallet` (`body.zitter`).
  - Block `casino-royal`: Lobby-Template, `MegaSlots.drawLines/freeTotal`, `Craps.render` (Marker), `Wheel.COLORS/build/spin` (Blackout), `Royal.goldRain`.
  - Block `room-stadt`: Fassade.
  - Block `royal-rules`: reine Helfer.
  - Block `story-engine`: `Story.katerHud`.
  - Block `story-kater`: `hudRender: 'kater'`, Toast-Effekte an `zitterEnde`/`zitterEndeBrownie`.
  - Block `cutscene-engine`: Sylvie-Goldrahmen.
  - Block `achievements`: Konfetti bei `royalHigh`.
  - Block `selftest`: neue Tests.
- `tests/desktop-diff.py` – neu: Screenshot-Diff `main` vs. Arbeitskopie.
- `tests/mobile-check.py` – Zonen-Check.
- `tests/playtest-story.py` – `scenario_royal_look`.
- `docs/superpowers/screenshots/royal-*.png`, `kater-hud.png`, `scene-royal.png`, `mobile-royal.png`, `mobile-craps.png`.
- `README.md` – Abschnitt Casino Royal / Kater-HUD.

---

### Task 1: Zone, Tokens, Gold-Vorhang, Kopfzeile/Seitenleiste, Desktop-Diff

**Files:**
- Modify: `keller37.html` (`<head>` Zeile 9; CSS vor `/* -- Reduced Motion -- */`; `UI.show` ~Zeile 1950; `UI.mountShell` ~Zeile 2100; Block `royal-rules` ~Zeile 5021; Block `selftest`)
- Create: `tests/desktop-diff.py`
- Test: Block `selftest` (Node), `tests/desktop-diff.py`

**Interfaces:**
- Produces: `RoyalRules.SCREENS = ['royal', 'megaslots', 'craps', 'wheel']`, `RoyalRules.zoneFor(screenId) → 'royal' | 'keller'`; `UI.zoneFade(on: boolean) → Promise` ; `body[data-zone]`; CSS-Tokens `--gold --gold-2 --bronze --emerald --bordeaux --ivory` unter `body[data-zone="royal"]`; `#zonefade`; `.brand-sub`.
- Consumes: nichts Neues.

- [ ] **Step 1: Failing Node-Tests für `zoneFor` schreiben**

Im Block `<script id="selftest">` hinter den vorhandenen `RoyalRules`-Tests (suche `T.test('RoyalRules.wheel`) anfügen:

```js
T.test('RoyalRules.zoneFor: Royal-Screens sind Zone royal, alles andere keller', () => {
  T.eq(RoyalRules.SCREENS, ['royal', 'megaslots', 'craps', 'wheel']);
  for (const id of RoyalRules.SCREENS) T.eq(RoyalRules.zoneFor(id), 'royal');
  for (const id of ['hub', 'roulette', 'stadt', 'jobs', 'skills', undefined, null]) T.eq(RoyalRules.zoneFor(id), 'keller');
});
```

- [ ] **Step 2: Test laufen lassen – muss fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `FAIL RoyalRules.zoneFor …` und `… 1 fehlgeschlagen`.

- [ ] **Step 3: Helfer in `royal-rules` anlegen**

In `const RoyalRules = {` direkt nach `GUEST_WIN: 5000,` einfügen:

```js
  /* Screens, die in der Zone „royal“ liegen (Body-Attribut data-zone, Gold-Vorhang beim Wechsel) */
  SCREENS: ['royal', 'megaslots', 'craps', 'wheel'],
  zoneFor(id) { return RoyalRules.SCREENS.includes(id) ? 'royal' : 'keller'; },
```

Run: `node tests/run-selftest.mjs 2>&1 | tail -1` → `… 0 fehlgeschlagen`.

- [ ] **Step 4: Font-Link, `#zonefade`-Element und Zone in `UI.show`**

Zeile 9 ersetzen durch:

```html
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Cinzel:wght@400;700&family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
```

Direkt hinter `<div id="nightfade" aria-hidden="true"></div>` einfügen:

```html
<div id="zonefade" aria-hidden="true"></div>
```

In `UI` (Block `ui`) neben `mobile()` ergänzen:

```js
  /* Gold-Vorhang beim Zonenwechsel Keller ↔ Royal; Reduced-Motion: sofort */
  zoneFade(on) {
    const el = qs('#zonefade');
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ms = reduced ? 0 : (this.mobile() ? 250 : 400);
    el.style.setProperty('--zf', ms + 'ms');
    el.classList.toggle('on', on);
    return wait(ms);
  },
```

`UI.show` so umbauen (der Rumpf nach der Mugging-Prüfung):

```js
    this.busy = true;
    const stage = qs('#stage');
    const curZone = document.body.dataset.zone || 'keller';
    const nextZone = typeof RoyalRules !== 'undefined' ? RoyalRules.zoneFor(id) : 'keller';
    const zoneChange = curZone !== nextZone;
    if (this.current) {
      try { this.current.def.unmount?.(); } catch (e) { console.error(e); }
      if (zoneChange) await this.zoneFade(true);
      else { stage.classList.add('leaving'); await wait(UI.mobile() ? 120 : 180); }
    } else if (zoneChange) { await this.zoneFade(true); }
    stage.innerHTML = '';
    stage.classList.remove('leaving');
    stage.appendChild(qs('#' + def.template).content.cloneNode(true));
    this.current = { id, def };
    document.body.dataset.screen = id;
    document.body.dataset.zone = nextZone;
    if (!zoneChange) stage.classList.add('entering');
    try { def.mount?.(stage); } catch (e) { console.error(e); }
    if (zoneChange) { this.renderWallet(); await this.zoneFade(false); }
    else { await wait(UI.mobile() ? 180 : 250); stage.classList.remove('entering'); }
    this.busy = false;
```

`renderWallet` wird beim Zonenwechsel aufgerufen, damit `.brand-sub` (Step 5) den richtigen Text zeigt.

- [ ] **Step 5: `.brand-sub` in `mountShell` und `renderWallet`**

In `mountShell` die Marke ersetzen:

```js
      h('button', { class: 'brand neon', id: 'brand', style: '--neon: var(--neon-amber)', title: 'Zurück in den Gang', onclick: () => { if (State.mode === 'story' && Story.s && Story.s.phase === 'morning') UI.show(UI.screens.has('jobs') ? 'jobs' : 'hub'); else UI.show('hub'); } },
        'Keller 37', h('span', { class: 'brand-sub', id: 'brandSub' }, 'Gast im Casino Royal')),
```

In `renderWallet` vor `qs('#mute').textContent = …` einfügen:

```js
    const sub = qs('#brandSub'); if (sub) sub.textContent = s.flags && s.flags.royalGuest ? 'Gast des Hauses' : 'Gast im Casino Royal';
```

- [ ] **Step 6: CSS-Block ROYAL ZONE (Tokens, Body, Vorhang, Shell)**

Vor `/* -- Reduced Motion -- */` einfügen:

```css
/* ==== ROYAL ZONE (Art déco, nur unter body[data-zone="royal"]) ==== */
#zonefade { position: fixed; inset: 0; z-index: 78; background: radial-gradient(ellipse at 50% 50%, rgba(201,169,97,.35), #000 70%); opacity: 0; pointer-events: none; transition: opacity var(--zf, .4s) ease; }
#zonefade.on { opacity: 1; }
.brand-sub { display: none; }
body[data-zone="royal"] {
  --bg: #0b0a0c; --panel: #141216; --panel-2: #1c1920;
  --gold: #c9a961; --gold-2: #f1dfa8; --bronze: #8a6a2e;
  --emerald: #1d6b4a; --bordeaux: #5a1a24; --ivory: #efe6cf; --text: #efe6cf; --dim: #9d9481;
  --font-display: "Cinzel", Georgia, "Times New Roman", serif;
  --radius: 4px; --shadow: 0 12px 34px rgba(0,0,0,.7);
  background: radial-gradient(ellipse at 50% 0%, rgba(255,255,255,.02), transparent 60%),
    conic-gradient(from 180deg at 50% -10%, transparent 0deg, rgba(201,169,97,.03) 7.5deg, transparent 15deg) 0 0 / 100% 100%,
    var(--bg);
  color: var(--text);
}
body[data-zone="royal"] .grain { opacity: .03; }
/* Kopfzeile */
body[data-zone="royal"] .wallet { background: #0b0a0c; border-bottom: 1px solid var(--gold); box-shadow: 0 4px 0 -3px var(--bronze); backdrop-filter: none; }
body[data-zone="royal"] .brand { font-family: var(--font-display); font-weight: 700; color: var(--gold); text-shadow: 0 0 10px rgba(201,169,97,.35); animation: none; letter-spacing: .12em; display: flex; flex-direction: column; align-items: flex-start; line-height: 1; }
body[data-zone="royal"] .brand-sub { display: block; font-size: .6rem; letter-spacing: .18em; text-transform: uppercase; color: var(--bronze); margin-top: 3px; }
body[data-zone="royal"] .balance { background: linear-gradient(#2a2418, #14110b); border: 1px solid var(--gold); box-shadow: inset 0 0 0 3px #14110b, inset 0 0 0 4px var(--bronze); color: var(--gold-2); font-family: var(--font-mono); border-radius: 4px; }
body[data-zone="royal"] .note { background: var(--ivory); color: #2a2418; border: 1px solid var(--bronze); box-shadow: 2px 3px 6px rgba(0,0,0,.6); }
body[data-zone="royal"] .note.danger { border-left: 4px solid var(--bordeaux); background: var(--ivory); }
body[data-zone="royal"] .note.pink { background: var(--ivory); border-left: 4px solid #a04a6a; }
body[data-zone="royal"] .luck .seg { background: #1c1920; border-color: var(--bronze); }
body[data-zone="royal"] .luck .seg.on { background: var(--gold); box-shadow: 0 0 6px rgba(201,169,97,.6); }
body[data-zone="royal"] .lv-badge { border-color: var(--bronze); color: var(--gold-2); }
body[data-zone="royal"] .icon-btn { border-color: var(--bronze); border-radius: 4px; }
body[data-zone="royal"] .icon-btn:hover { border-color: var(--gold); }
/* Seitenleiste */
body[data-zone="royal"] .side-sec { background: var(--panel); border: 1px solid var(--gold); border-radius: 4px; box-shadow: var(--shadow); }
body[data-zone="royal"] .side-sec h3 { font-family: var(--font-display); font-variant: small-caps; letter-spacing: .18em; font-size: .85rem; color: var(--gold); text-align: center; }
body[data-zone="royal"] .side-sec h3::after { content: "— ✦ —"; display: block; font-size: .65rem; color: var(--bronze); margin-top: 2px; letter-spacing: .3em; }
body[data-zone="royal"] .side-btn { background: var(--panel-2); border: 1px solid var(--bronze); border-radius: 3px; color: var(--ivory); }
body[data-zone="royal"] .side-btn:hover:not(:disabled) { border-color: var(--gold); background: #24202a; }
body[data-zone="royal"] .side-btn .price { color: var(--gold-2); }
body[data-zone="royal"] .side-hint { color: var(--dim); }
body[data-zone="royal"] .side-tabs button.on { color: var(--gold-2); border-top-color: var(--gold); }
/* Gemeinsame Bausteine: Chips, Knöpfe, Tafeln, Status, Neon */
body[data-zone="royal"] .chip { --chip: #141216; background: var(--chip); border: 4px dashed var(--gold); box-shadow: inset 0 0 0 3px #0b0a0c, inset 0 0 0 4px var(--bronze), 0 3px 6px rgba(0,0,0,.6); color: var(--gold-2); }
body[data-zone="royal"] .chip:hover, body[data-zone="royal"] .chip:active { --chip: var(--gold); color: #141216; }
body[data-zone="royal"] .btn { font-family: var(--font-display); font-weight: 700; letter-spacing: .15em; border-radius: 3px; --c: var(--gold); color: var(--gold-2); background: transparent; }
body[data-zone="royal"] .btn.solid { background: linear-gradient(#e2c77a, #b8923f); color: #1a1208; border-color: #e2c77a; }
body[data-zone="royal"] .btn.solid:hover:not(:disabled) { background: linear-gradient(#f1dfa8, #c9a961); box-shadow: 0 0 14px rgba(201,169,97,.5); }
body[data-zone="royal"] .btn.ghost { --c: var(--bronze); color: var(--ivory); }
body[data-zone="royal"] .btn.green { --c: var(--emerald); color: #bfe8d0; background: transparent; }
body[data-zone="royal"] .btn.blue { --c: var(--gold-2); color: var(--gold-2); background: transparent; }
body[data-zone="royal"] .btn.red { --c: var(--bordeaux); color: #f0c0c8; background: transparent; }
body[data-zone="royal"] .chalk.paytable { background: linear-gradient(160deg, #b8923f, #e2c77a 45%, #9a7a2f); color: #2a1d08; border: 2px solid #5a4520; box-shadow: inset 0 0 0 1px #e2c77a, var(--shadow); font-family: var(--font-mono); }
body[data-zone="royal"] .chalk.paytable h4 { font-family: var(--font-display); color: #2a1d08; letter-spacing: .12em; }
body[data-zone="royal"] .chalk.paytable td, body[data-zone="royal"] .chalk.paytable .side-hint { color: #2a1d08; }
body[data-zone="royal"] .status { font-family: var(--font-display); font-size: .95rem; color: var(--gold-2); letter-spacing: .08em; }
body[data-zone="royal"] .neon { animation: none; color: var(--gold-2); text-shadow: 0 0 12px rgba(201,169,97,.5); }
body[data-zone="royal"] .panel { background: var(--panel); border: 1px solid var(--bronze); border-radius: 4px; }
@media (max-width: 760px) { body[data-zone="royal"] .side { background: #0b0a0c; border-top: 1px solid var(--gold); } }
@media (prefers-reduced-motion: reduce) { #zonefade { transition: none; } }
```

Hinweis: Die vorhandene Regel `.chip[data-v="10"] { --chip: … }` hat Spezifität 0,2,0; `body[data-zone="royal"] .chip` hat 0,2,1 und gewinnt – gewollt.

- [ ] **Step 7: Desktop-Diff-Skript anlegen**

`tests/desktop-diff.py`:

```python
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
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
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
```

Run: `python3 tests/desktop-diff.py`
Expected: vier `OK … px>24: 0` (die Zone ist im Keller nie aktiv; der Font-Link ändert am Keller nichts, weil Cinzel dort nicht verwendet wird).

- [ ] **Step 8: Browser-Selftest, Sichtprüfung, Commit**

Run: `sh tests/dom-selftest.sh | tail -1` → `failed=0`.
Run: `tests/screenshot.sh /tmp/royal-zone.png "?fresh&mode=free&screen=royal"` und Bild ansehen: dunkler Onyx-Hintergrund, Goldlinie unter der Kopfzeile, Marke in Cinzel mit Untertitel, Seitenleiste mit Ornamentstrich, Chips schwarz-gold.

```bash
git add keller37.html tests/desktop-diff.py
git commit -m "feat(royal): Zone royal mit Art-déco-Tokens, Gold-Vorhang, Kopfzeile und Seitenleiste; Desktop-Diff-Skript

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Lobby als Art-déco-Foyer

**Files:**
- Modify: `keller37.html` (`<template id="tpl-royal">` ~Zeile 1080; CSS-Block ROYAL ZONE; `UI.register('royal', …)` im Block `casino-royal`)
- Test: `tests/mobile-check.py` (bestehende Checks `royal`), Sichtprüfung

**Interfaces:**
- Consumes: Zone aus Task 1.
- Produces: Klassen `.royal-foyer .deco-arch .deco-card .deco-portals .portal .plaque .engraved`; `#royalLine`, `#royalLeave` bleiben.

- [ ] **Step 1: Template ersetzen**

`<template id="tpl-royal">` komplett ersetzen:

```html
<template id="tpl-royal">
  <div class="royal-foyer">
    <div class="deco-arch"><h2>Casino Royal</h2></div>
    <div class="deco-card"><span class="hat">🎩</span><p id="royalLine"></p></div>
    <div class="deco-portals">
      <button class="portal" data-screen="megaslots"><span class="portal-crown"></span><span class="plaque">Mega Seven</span><span class="glyph">🎰</span><span class="engraved">5 Walzen · Freispiele</span></button>
      <button class="portal" data-screen="craps"><span class="portal-crown"></span><span class="plaque">Craps</span><span class="glyph">🎲</span><span class="engraved">Pass Line · Field</span></button>
      <button class="portal" data-screen="wheel"><span class="portal-crown"></span><span class="plaque">Glücksrad</span><span class="glyph">🎡</span><span class="engraved">bis 10×</span></button>
    </div>
    <div class="bet-bar"><button class="btn ghost sm" id="royalLeave">← Zurück in die Stadt</button></div>
  </div>
</template>
```

Im `UI.register('royal', …)`-Mount muss der Klick weiterhin über `data-screen` laufen; falls dort `qsa('.door', root)` steht, auf `qsa('.portal, .door', root)` erweitern (prüfen mit `grep -n "UI.register('royal'" -A8 keller37.html`).

- [ ] **Step 2: CSS Lobby**

An den Block ROYAL ZONE anfügen:

```css
/* Lobby */
.royal-foyer { display: flex; flex-direction: column; gap: 18px; align-items: center; }
.deco-arch { position: relative; width: 100%; height: 120px; display: flex; align-items: flex-end; justify-content: center; overflow: hidden; border-bottom: 1px solid var(--bronze); }
.deco-arch::before { content: ""; position: absolute; inset: 0; background: conic-gradient(from 180deg at 50% 100%, transparent 0deg, rgba(201,169,97,.06) 3.75deg, transparent 7.5deg); }
.deco-arch::after { content: ""; position: absolute; left: 50%; bottom: -1px; width: 420px; height: 210px; transform: translateX(-50%); border: 2px solid var(--gold); border-bottom: 0; border-radius: 210px 210px 0 0; box-shadow: inset 0 0 0 4px #0b0a0c, inset 0 0 0 5px var(--bronze); pointer-events: none; }
.deco-arch h2 { position: relative; z-index: 1; margin: 0 0 18px; font-family: var(--font-display); font-weight: 700; font-size: 2.4rem; letter-spacing: .25em; text-transform: uppercase; color: var(--gold-2); text-shadow: 0 0 18px rgba(201,169,97,.45); }
.deco-card { display: flex; align-items: center; gap: 10px; background: var(--ivory); color: #2a2418; border: 1px solid var(--bronze); padding: 8px 16px; font-family: var(--font-mono); font-style: italic; font-size: .9rem; box-shadow: 2px 3px 8px rgba(0,0,0,.6); transform: rotate(-.6deg); max-width: 640px; }
.deco-card .hat { font-size: 1.2rem; }
.deco-card p { margin: 0; }
.deco-portals { position: relative; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; width: 100%; padding: 28px 22px 34px;
  background: linear-gradient(180deg, #0b0a0c 0%, transparent 45%), repeating-linear-gradient(45deg, #141216 0 28px, #1a171c 28px 56px), repeating-linear-gradient(-45deg, transparent 0 28px, rgba(0,0,0,.35) 28px 56px); }
.portal { position: relative; height: 260px; display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 34px 12px 16px; cursor: pointer; background: #141216; border: 2px solid var(--gold); box-shadow: inset 0 0 0 4px #141216, inset 0 0 0 5px var(--bronze), var(--shadow); color: var(--ivory); font-family: inherit; transition: transform .12s; }
.portal-crown { position: absolute; top: 8px; left: 50%; transform: translateX(-50%); width: 60%; height: 4px; background: var(--gold); }
.portal-crown::before, .portal-crown::after { content: ""; position: absolute; left: 50%; transform: translateX(-50%); height: 4px; background: var(--gold); }
.portal-crown::before { top: 7px; width: 66%; }
.portal-crown::after { top: 14px; width: 33%; }
.plaque { display: inline-block; margin-top: 12px; padding: 6px 18px; background: linear-gradient(160deg, #b8923f, #e2c77a 45%, #9a7a2f); color: #2a1d08; font-family: var(--font-display); font-weight: 700; letter-spacing: .12em; font-size: 1.15rem; text-transform: uppercase; text-shadow: 0 1px 0 rgba(255,255,255,.35); border: 1px solid #5a4520; box-shadow: inset 0 0 0 1px #e2c77a; position: relative; overflow: hidden; }
.portal .glyph { font-size: 3rem; line-height: 1; }
.engraved { margin-top: auto; font-family: var(--font-display); font-size: .75rem; letter-spacing: .12em; color: var(--bronze); text-transform: uppercase; }
.portal:active { transform: scale(.98); }
@media (hover: hover) {
  .portal .glyph { filter: drop-shadow(0 4px 6px rgba(0,0,0,.7)); }
  .portal:hover { background: radial-gradient(ellipse at 50% 60%, rgba(201,169,97,.12), #141216 70%); }
  .portal:hover .plaque::after { content: ""; position: absolute; inset: 0; background: linear-gradient(105deg, transparent 30%, rgba(255,255,255,.45) 50%, transparent 70%); animation: royalSheen .5s ease both; }
}
@keyframes royalSheen { from { transform: translateX(-100%); } to { transform: translateX(100%); } }
@media (max-width: 760px) {
  .deco-arch { height: 90px; } .deco-arch h2 { font-size: 1.6rem; margin-bottom: 12px; } .deco-arch::after { width: 300px; height: 150px; }
  .deco-portals { grid-template-columns: 1fr 1fr; gap: 12px; padding: 18px 12px 22px; }
  .portal { height: 170px; padding-top: 28px; gap: 6px; } .portal .glyph { font-size: 2.2rem; } .plaque { font-size: .95rem; padding: 4px 10px; }
  .portal:last-child:nth-child(odd) { grid-column: 1 / -1; }
}
@media (prefers-reduced-motion: reduce) { .portal:hover .plaque::after { animation: none; display: none; } }
```

- [ ] **Step 3: Prüfen und committen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh | tail -1` → beide grün.
Run: `python3 tests/mobile-check.py 2>&1 | grep -v "^screenshot\|^OK"` → `… 0 fehlgeschlagen`.
Run: `tests/screenshot.sh /tmp/royal-lobby.png "?fresh&mode=free&screen=royal"` und ansehen: Bogen mit Strahlen, Visitenkarte, drei Portale mit Plakette auf Schachbrettboden.

```bash
git add keller37.html
git commit -m "feat(royal): Lobby als Art-déco-Foyer mit Bogen, Visitenkarte und Portalen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Mega Seven – Gehäuse, Gewinnlinien, Freispiel-Banner

**Files:**
- Modify: `keller37.html` (`<template id="tpl-megaslots">`; CSS `.mega-*` ~Zeile 616–626 → ersetzen; `MegaSlots` im Block `casino-royal`)
- Test: Block `selftest` (Node: `RoyalRules.megaLinePoints`), Sichtprüfung

**Interfaces:**
- Produces: `RoyalRules.megaLinePoints(line, count, cell, gap, pad) → [[x,y],…]` (Mittelpunkte der getroffenen Zellen einer Linie), `MegaSlots.drawLines(lines)`, `MegaSlots.clearLines()`, `MegaSlots.freeTotal`.
- Consumes: `RoyalRules.MEGA.LINES` (vorhanden).

- [ ] **Step 1: Failing Node-Test für die Linien-Geometrie**

Im Block `selftest`:

```js
T.test('RoyalRules.megaLinePoints: Zellmittelpunkte einer Linie', () => {
  // Zelle 64, Lücke 6, Innenabstand 10: Spalte r → x = 10 + r*70 + 32, Reihe row → y = 10 + row*70 + 32
  T.eq(RoyalRules.megaLinePoints(1, 3, 64, 6, 10), [[42, 42], [112, 42], [182, 42]]);          // Linie 2 = obere Reihe
  T.eq(RoyalRules.megaLinePoints(3, 5, 64, 6, 10), [[42, 42], [112, 112], [182, 182], [252, 112], [322, 42]]); // V-Form
  T.eq(RoyalRules.megaLinePoints(0, 0, 64, 6, 10), []);
});
```

Run: `node tests/run-selftest.mjs 2>&1 | tail -2` → FAIL.

- [ ] **Step 2: Helfer in `royal-rules`**

Hinter `zoneFor` einfügen:

```js
  /* Mittelpunkte der ersten `count` Zellen einer Gewinnlinie (für die goldene Linie über dem Raster) */
  megaLinePoints(line, count, cell, gap, pad) {
    const rows = RoyalRules.MEGA.LINES[line] || [];
    return rows.slice(0, count).map((row, r) => [pad + r * (cell + gap) + cell / 2, pad + row * (cell + gap) + cell / 2]);
  },
```

Run: Node-Selftest grün.

- [ ] **Step 3: Template und CSS**

In `<template id="tpl-megaslots">` das Element `.mega-grid` in einen Wrapper legen und das Banner umbauen:

```html
    <div class="mega-machine">
      <div class="mega-free" id="megaFree">FREISPIELE ×2 · noch <span id="megaFreeLeft">0</span></div>
      <div class="slot-head neon" style="--neon: var(--gold-2)">Mega Seven</div>
      <div class="mega-reels"><div class="mega-grid" id="megaGrid"></div><svg class="mega-lines-svg" id="megaLinesSvg" aria-hidden="true"></svg></div>
      <div class="mega-lines" id="megaLines"></div>
    </div>
```

Die bisherigen CSS-Zeilen `.mega-machine`, `.mega-grid`, `.mega-grid .cell`, `.mega-grid .cell.bar`, `.mega-grid .cell.spin`, `.mega-grid .cell.hit`, `.mega-lines`, `.mega-free` ersetzen durch:

```css
.mega-machine { --cell: 64px; --gap: 6px; --pad: 10px; position: relative; background: #141216; border: 2px solid var(--gold); box-shadow: inset 0 0 0 4px #141216, inset 0 0 0 5px var(--bronze), var(--shadow); padding: 26px 18px 16px; overflow: hidden; }
.mega-machine::before { content: ""; position: absolute; top: 8px; left: 50%; transform: translateX(-50%); width: 60%; height: 4px; background: var(--gold); box-shadow: 0 7px 0 -0px var(--gold); }
.mega-machine .slot-head { font-family: var(--font-display); font-weight: 700; font-size: 1.6rem; letter-spacing: .25em; text-align: center; color: var(--gold-2); margin-bottom: 12px; }
.mega-reels { position: relative; }
.mega-grid { display: grid; grid-template-columns: repeat(5, var(--cell)); gap: var(--gap); background: #0a0a0a; padding: var(--pad); border: 1px solid var(--bronze); }
.mega-grid .cell { width: var(--cell); height: var(--cell); display: flex; align-items: center; justify-content: center; font-size: calc(var(--cell) * .5); background: var(--ivory); color: #2a2418; border: 1px solid var(--gold); font-family: var(--font-display); font-weight: 700; }
.mega-grid .cell.bar { font-size: calc(var(--cell) * .3); letter-spacing: .05em; }
.mega-grid .cell.spin { animation: megaFlicker .12s linear infinite; }
.mega-grid .cell.hit { box-shadow: 0 0 0 3px var(--gold-2), 0 0 18px var(--gold-2); animation: hitGlow .6s ease 3; }
.mega-lines-svg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible; }
.mega-lines-svg polyline { fill: none; stroke: var(--gold-2); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; filter: drop-shadow(0 0 6px rgba(241,223,168,.8)); stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: megaLineDraw .4s ease forwards; }
@keyframes megaLineDraw { to { stroke-dashoffset: 0; } }
.mega-lines { font-family: var(--font-mono); font-size: .8rem; color: var(--gold-2); min-height: 1.2em; margin-top: 8px; text-align: center; }
.mega-free { position: absolute; left: 0; right: 0; top: 0; z-index: 3; padding: 8px; text-align: center; background: #0b0a0c; border-bottom: 1px solid var(--gold); font-family: var(--font-display); font-weight: 700; letter-spacing: .2em; color: var(--gold); transform: translateY(-100%); transition: transform .35s ease; }
.mega-free.show { transform: translateY(0); }
.mega-machine.free .mega-grid .cell { border-color: var(--gold-2); box-shadow: inset 0 0 0 1px var(--gold-2); }
@media (hover: hover) { .mega-grid .cell.spin { filter: blur(2px); }
  .mega-machine .slot-head { background: linear-gradient(100deg, var(--gold-2) 0 40%, #fff 50%, var(--gold-2) 60% 100%) 0 0 / 300% 100%; -webkit-background-clip: text; background-clip: text; color: transparent; animation: royalSheenText 6s linear infinite; } }
@keyframes royalSheenText { 0%, 80% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
@media (max-width: 760px) { .mega-panel { grid-template-columns: 1fr; } .mega-panel .paytable { justify-self: center; } .mega-machine { --cell: 50px; --gap: 5px; --pad: 8px; } }
@media (prefers-reduced-motion: reduce) { .mega-machine .slot-head { animation: none; } .mega-lines-svg polyline { animation: none; stroke-dashoffset: 0; } .mega-free { transition: none; } .mega-grid .cell.spin { animation: none; } }
```

Die vorhandene `@media (max-width: 760px) { .mega-panel …}`-Zeile (alt) löschen, da oben ersetzt.

- [ ] **Step 4: `MegaSlots` – Linien zeichnen, Banner, Freispiel-Summe**

In `const MegaSlots = {` Feld `freeTotal: 0` ergänzen (`root: null, spinning: false, gen: 0, freeLeft: 0, lastBet: 0, freeRun: null, freeTotal: 0,`) und Methoden ergänzen:

```js
  clearLines() { const svg = qs('#megaLinesSvg', this.root); if (svg) svg.innerHTML = ''; },
  /* Goldene Polylinie je Gewinnlinie über den getroffenen Zellen; Maße aus den CSS-Variablen der Maschine */
  drawLines(lines) {
    const svg = qs('#megaLinesSvg', this.root); if (!svg) return;
    svg.innerHTML = '';
    const cs = getComputedStyle(qs('.mega-machine', this.root));
    const cell = parseFloat(cs.getPropertyValue('--cell')), gap = parseFloat(cs.getPropertyValue('--gap')), pad = parseFloat(cs.getPropertyValue('--pad'));
    for (const w of lines) {
      const pts = RoyalRules.megaLinePoints(w.line, w.count, cell, gap, pad);
      const pl = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      pl.setAttribute('points', pts.map((p) => p.join(',')).join(' '));
      svg.append(pl);
    }
  },
```

`syncFree` ersetzen:

```js
  syncFree() {
    this.checkFreeRun();
    if (!this.root) return;
    qs('#megaFree', this.root).classList.toggle('show', this.freeLeft > 0);
    qs('.mega-machine', this.root).classList.toggle('free', this.freeLeft > 0);
    qs('#megaFreeLeft', this.root).textContent = this.freeLeft;
    const b = qs('#btnMega', this.root); if (b) b.textContent = this.freeLeft > 0 ? `Freispiel (${this.freeLeft})` : 'Drehen';
  },
```

In `spin()`:
- nach `qs('#megaLines', this.root).textContent = '';` ergänzen: `this.clearLines();`
- nach `if (w.freeSpins) { … }` ergänzen: `if (free) this.freeTotal += w.payout; else if (!w.freeSpins) this.freeTotal = 0; else this.freeTotal = 0;` – vereinfacht: `if (free) this.freeTotal += w.payout; else this.freeTotal = 0;`
- in `if (this.alive(gen)) {` nach `this.markHits(w.lines);` ergänzen: `this.drawLines(w.lines);`
- die Status-Zeile: wenn dies das letzte Freispiel war (`free && this.freeLeft === 0`), hinter dem Status anhängen: `` st.innerHTML += ` · <span class="win">Freispiele vorbei · +${UI.fmt(this.freeTotal)}</span>`; ``

In `mount` nach `MegaSlots.render(…)` ergänzen: `MegaSlots.clearLines();`.

- [ ] **Step 5: Prüfen und committen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh | tail -1` → grün.
Run: `python3 tests/mobile-check.py 2>&1 | grep -v "^screenshot\|^OK"` → 0 fehlgeschlagen.
Sichtprüfung im Browser (CDP oder manuell): `RoyalRules.megaRoll = () => [['7️⃣','🍒','💎'],['7️⃣','🔔','BAR'],['7️⃣','💎','🍒'],['BAR','7️⃣','🔔'],['🍒','7️⃣','💎']]` setzen, drehen → goldene Linie über der oberen Reihe (Zellen 1–3).

```bash
git add keller37.html
git commit -m "feat(royal): Mega Seven im Art-déco-Gehäuse, goldene Gewinnlinien, Freispiel-Banner

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Craps – Smaragdtisch mit Goldborte und Chip-Marker

**Files:**
- Modify: `keller37.html` (CSS `.craps-*` ~Zeile 627–639 → ersetzen; `<template id="tpl-craps">`; `Craps.render`)
- Test: Sichtprüfung, `tests/mobile-check.py`

**Interfaces:**
- Consumes: `.chip-stack` (Roulette-CSS, vorhanden: `.chip-stack`, `.chip-stack.won`, `.chip-stack.lost`).
- Produces: `#passStack`, `#fieldStack` (Marker-Elemente).

- [ ] **Step 1: Template**

Die beiden `.craps-bet`-Boxen ersetzen:

```html
        <div class="craps-bet" id="passBox"><span class="chip-stack hidden" id="passStack">0</span><h4>PASS LINE</h4><div class="amt" id="passAmt">0 €</div><p>7/11 gewinnt · 2/3/12 verliert · sonst Punkt</p></div>
        <div class="craps-bet" id="fieldBox"><span class="chip-stack hidden" id="fieldStack">0</span><h4>FIELD</h4><div class="amt" id="fieldAmt">0 €</div><p>3 4 9 10 11 zahlen 1:1 · 2 und 12 zahlen 2:1</p></div>
```

- [ ] **Step 2: CSS ersetzen** (alle `.craps-*`-, `.die`-Regeln und die `@media`-Zeile dazu)

```css
.craps-panel { align-items: stretch; }
.craps-table { position: relative; background: radial-gradient(ellipse at 50% 30%, #1f6b4a, #0e3d2a 70%, #082416); border: 6px solid #141216; border-radius: 80px / 30px; padding: 18px 26px 22px; box-shadow: 0 0 0 2px var(--gold), var(--shadow); }
.craps-head { display: flex; justify-content: space-between; align-items: center; font-family: var(--font-display); font-weight: 700; font-size: 1.4rem; letter-spacing: .2em; color: var(--gold-2); }
.craps-point { font-family: var(--font-display); font-size: .8rem; letter-spacing: .1em; background: #141216; color: var(--gold-2); border: 2px solid var(--gold); border-radius: 50%; padding: 8px 10px; min-width: 64px; text-align: center; }
.craps-point.on { background: var(--gold); color: #141216; }
.craps-dice { display: flex; gap: 18px; justify-content: center; margin: 16px 0; }
.die { width: 70px; height: 70px; border-radius: 12px; background: var(--ivory); color: #141216; font-size: 3.2rem; display: flex; align-items: center; justify-content: center; border: 2px solid var(--gold); box-shadow: 0 6px 10px rgba(0,0,0,.6); }
.die.rolling { animation: dieRoll .5s linear infinite; }
@keyframes dieRoll { 0% { transform: rotate(0) translateY(0); } 50% { transform: rotate(180deg) translateY(-14px); } 100% { transform: rotate(360deg) translateY(0); } }
.craps-bets { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.craps-bet { position: relative; border: 1px solid var(--gold); border-radius: 6px; padding: 12px 10px; text-align: center; color: var(--ivory); background: rgba(0,0,0,.25); box-shadow: inset 0 2px 8px rgba(0,0,0,.6); }
.craps-bet h4 { margin: 0; font-family: var(--font-display); font-weight: 700; letter-spacing: .18em; color: var(--gold-2); }
.craps-bet .amt { font-family: var(--font-mono); font-size: 1.2rem; color: var(--gold-2); }
.craps-bet p { font-size: .75rem; color: rgba(239,230,207,.7); margin: 4px 0 0; }
.craps-bet .chip-stack { right: 8px; top: 8px; }
.craps-bet.won { box-shadow: 0 0 0 2px var(--gold-2), inset 0 2px 8px rgba(0,0,0,.6); }
.craps-bet.lost { opacity: .5; }
.craps-history { font-family: var(--font-display); font-size: .8rem; letter-spacing: .08em; color: rgba(241,223,168,.7); text-align: center; margin-top: 10px; min-height: 1.2em; }
@media (max-width: 760px) { .craps-table { border-radius: 40px / 22px; padding: 14px 16px; } .craps-bets { grid-template-columns: 1fr; } }
```

- [ ] **Step 3: `Craps.render` – Marker**

In `render()` nach den beiden `Amt`-Zeilen ergänzen:

```js
    for (const k of ['pass', 'field']) {
      const st = qs(`#${k}Stack`, this.root);
      st.textContent = this.bets[k] >= 1000 ? `${Math.round(this.bets[k] / 100) / 10}k` : String(this.bets[k]);
      st.classList.toggle('hidden', this.bets[k] === 0);
    }
```

In `roll()` dort, wo `won`/`lost` gesetzt werden, die Marker mitfärben:

```js
        if (r.pass === 'win') { qs('#passBox', this.root).classList.add('won'); qs('#passStack', this.root).classList.add('won'); }
        if (r.pass === 'lose') { qs('#passBox', this.root).classList.add('lost'); qs('#passStack', this.root).classList.add('lost'); }
        if (r.field === 'win') { qs('#fieldBox', this.root).classList.add('won'); qs('#fieldStack', this.root).classList.add('won'); }
        if (r.field === 'lose') { qs('#fieldBox', this.root).classList.add('lost'); qs('#fieldStack', this.root).classList.add('lost'); }
```

und am Anfang von `roll()` (bei `qsa('.craps-bet', …).forEach(remove 'won','lost')`) zusätzlich `qsa('.chip-stack', this.root).forEach((c) => c.classList.remove('won', 'lost'));`. Da `render()` nach dem Wurf die Marker anhand der Restbeträge ausblendet, bleibt bei Pass-Gewinn/Verlust der Marker nur bis zum `render()` sichtbar – deshalb `this.render()` im `alive`-Block **vor** dem Färben aufrufen und die Marker danach für die Anzeige des Ergebnisses per `classList.remove('hidden')` sichtbar lassen, wenn `bets.pass`/`bets.field` > 0 waren:

```js
        this.render();
        if (bets.pass > 0) qs('#passStack', this.root).classList.remove('hidden');
        if (bets.field > 0) qs('#fieldStack', this.root).classList.remove('hidden');
        // …danach die won/lost-Zeilen von oben
```

- [ ] **Step 4: Prüfen und committen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh | tail -1` → grün. `python3 tests/mobile-check.py 2>&1 | tail -1` → 0 fehlgeschlagen.
Sichtprüfung: Chip 200 auf Pass → Marker „200" rechts oben im Feld; würfeln → Marker gold/grau.

```bash
git add keller37.html
git commit -m "feat(royal): Craps-Tisch in Smaragd mit Goldborte, Puck und Chip-Markern

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Glücksrad – Art-déco-Segmente, Zahnkranz, Lichter, Bankrott-Blackout

**Files:**
- Modify: `keller37.html` (CSS `.wheel-*` ~Zeile 640–650 → ersetzen; `Wheel` im Block `casino-royal`; `royal-rules`; `selftest`)
- Test: Node (`RoyalRules.wheelTone`), Sichtprüfung

**Interfaces:**
- Produces: `RoyalRules.wheelTone(mult) → 'x10'|'x5'|'x2'|'x1'|'half'|'bust'`, `RoyalRules.WHEEL_COLORS`; Klassen `.wheel-panel.blackout`, `.wheel.spinning`, `.wheel-lights`.

- [ ] **Step 1: Failing Node-Test**

```js
T.test('RoyalRules.wheelTone: Segmentklasse je Multiplikator', () => {
  T.eq([10, 5, 2, 1, 0.5, 0].map(RoyalRules.wheelTone), ['x10', 'x5', 'x2', 'x1', 'half', 'bust']);
  T.eq(Object.keys(RoyalRules.WHEEL_COLORS).sort(), ['0', '0.5', '1', '10', '2', '5']);
});
```

Run: Node-Selftest → FAIL.

- [ ] **Step 2: Helfer**

In `royal-rules` hinter `megaLinePoints`:

```js
  /* Glücksrad-Farben (Art déco): Gold ×10, Champagner ×5, Smaragd ×2, Onyx-hell ×1, Bordeaux Hälfte, Onyx-dunkel Bankrott */
  WHEEL_COLORS: { 10: '#c9a961', 5: '#f1dfa8', 2: '#1d6b4a', 1: '#2a262e', 0.5: '#5a1a24', 0: '#141216' },
  wheelTone(m) { return m === 0 ? 'bust' : m === 0.5 ? 'half' : `x${m}`; },
```

- [ ] **Step 3: `Wheel` anpassen**

`COLORS` entfernen und in `build()` `RoyalRules.WHEEL_COLORS` verwenden; Segmente bekommen Klasse und Label:

```js
  label(m) { return m === 0 ? '☠ BANKROTT' : m === 0.5 ? 'HÄLFTE' : `×${m}`; },
  build() {
    const el = qs('#wheel', this.root); if (!el) return;
    const S = RoyalRules.WHEEL.SEGMENTS, n = S.length, step = 360 / n;
    el.style.background = `conic-gradient(${S.map((m, i) => `${RoyalRules.WHEEL_COLORS[m]} ${i * step}deg ${(i + 1) * step}deg`).join(', ')})`;
    el.innerHTML = '';
    S.forEach((m, i) => el.append(h('div', { class: `seg ${RoyalRules.wheelTone(m)}`, 'data-mult': m, style: `transform: rotate(${i * step + step / 2 - 90}deg)` }, this.label(m))));
  },
```

In `spin()`:
- nach `el.classList.remove('hit');` → `el.classList.add('spinning');`
- nach `await wait(reduced ? 200 : 4600);` → `el.classList.remove('spinning');`
- im `alive`-Block nach dem Status-Text bei `mult === 0`:

```js
        if (mult === 0) {
          const panel = qs('.wheel-panel', this.root);
          panel.classList.add('blackout');
          UI.toast({ icon: '🎩', title: 'Das Haus dankt.', text: `−${UI.fmt(bet)}`, tone: 'loss' });
          setTimeout(() => panel.classList.remove('blackout'), reduced ? 0 : 900);
        }
```

- [ ] **Step 4: CSS ersetzen** (`.wheel-panel` bis zur `@media`-Zeile)

```css
.wheel-panel { display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: center; transition: filter .6s ease; }
.wheel-panel.blackout { filter: brightness(.15); }
.wheel-panel .status, .wheel-panel .bet-bar { grid-column: 1 / -1; }
.wheel-stage { position: relative; width: min(360px, 80vw); aspect-ratio: 1; margin: 0 auto; }
.wheel-stage::before { content: ""; position: absolute; inset: -10px; border-radius: 50%; background: repeating-conic-gradient(var(--gold) 0deg 7.5deg, var(--bronze) 7.5deg 15deg); z-index: 0; }
.wheel-lights { position: absolute; inset: -6px; border-radius: 50%; background: repeating-conic-gradient(transparent 0deg 13deg, rgba(241,223,168,.9) 13deg 15deg); -webkit-mask: radial-gradient(circle, transparent 0 calc(50% - 8px), #000 calc(50% - 7px)); mask: radial-gradient(circle, transparent 0 calc(50% - 8px), #000 calc(50% - 7px)); opacity: .35; z-index: 1; pointer-events: none; }
.wheel { position: absolute; inset: 0; border-radius: 50%; border: 8px solid var(--gold); box-shadow: var(--shadow), inset 0 0 30px rgba(0,0,0,.6); transition: transform 4.5s cubic-bezier(.12,.88,.22,1); z-index: 1; }
.wheel.snap { transition: none; }
.wheel .seg { position: absolute; left: 50%; top: 50%; width: 50%; height: 1.2em; line-height: 1.2em; margin-top: -.6em; transform-origin: 0 50%; font-family: var(--font-display); font-weight: 700; font-size: .72rem; letter-spacing: .06em; text-align: right; padding-right: 14px; color: var(--gold-2); }
.wheel .seg.x10, .wheel .seg.x5 { color: #141216; }
.wheel .seg.bust { color: var(--bronze); }
.wheel-pointer { position: absolute; left: 50%; top: -20px; transform: translateX(-50%); width: 18px; height: 26px; background: var(--gold); clip-path: polygon(0 0, 100% 0, 50% 100%); z-index: 3; filter: drop-shadow(0 0 6px rgba(201,169,97,.7)); font-size: 0; }
.wheel-hub { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 64px; height: 64px; border-radius: 50%; background: #141216; border: 3px solid var(--gold); box-shadow: inset 0 0 0 2px var(--bronze), 0 4px 10px rgba(0,0,0,.7); display: flex; align-items: center; justify-content: center; font-size: 1.8rem; z-index: 2; }
.wheel.hit { animation: hitGlow .6s ease 3; }
@media (hover: hover) { .wheel.spinning ~ .wheel-lights, .wheel-stage:has(.wheel.spinning) .wheel-lights { animation: wheelLights .15s steps(2) infinite; } }
@keyframes wheelLights { to { opacity: 1; } }
@media (max-width: 760px) { .wheel-panel { grid-template-columns: 1fr; } .wheel-panel .paytable { justify-self: center; } .wheel .seg { font-size: .6rem; } }
@media (prefers-reduced-motion: reduce) { .wheel-panel { transition: none; } .wheel-lights { animation: none !important; } }
```

Im Template `tpl-wheel` hinter `<div class="wheel" id="wheel"></div>` einfügen: `<div class="wheel-lights" aria-hidden="true"></div>`. Der Zeiger-Text „▼" bleibt im Markup, wird durch `font-size: 0` und `clip-path` zur goldenen Feder.

- [ ] **Step 5: Prüfen und committen**

Node/DOM-Selftests grün, `mobile-check.py` grün. Sichtprüfung: Rad mit Zahnkranz, Gold/Champagner/Smaragd/Onyx/Bordeaux-Segmente, Nabe mit Goldrand; `RoyalRules.wheelSpin = () => 0` setzen und drehen → Panel dunkelt kurz ab, Toast „Das Haus dankt.".

```bash
git add keller37.html
git commit -m "feat(royal): Glücksrad mit Art-déco-Segmenten, Zahnkranz, Lauflichtern und Bankrott-Blackout

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Royal-Fassade in der Stadt

**Files:**
- Modify: `keller37.html` (`Stadt.render` Royal-Karte ~Zeile 2941–2949; CSS `.storefront.royal` ~Zeile 609–612 ersetzen)
- Test: Sichtprüfung in drei Zuständen, `tests/mobile-check.py` (`stadt`)

**Interfaces:**
- Produces: `.facade`, `.marquee`, `.bulbs`, `.portal-door`, `.brass-sign`, `.doorman`; Klick weiterhin `Royal.enter()`.

- [ ] **Step 1: Markup in `Stadt.render`**

Den `if (roomOpen) street.append(h('div', { class: 'storefront royal' … }))`-Block ersetzen:

```js
      if (roomOpen) {
        const open = chk.ok && !gate;
        street.append(h('div', { class: 'facade' + (open ? '' : ' locked') + (gate ? ' gated' : ''), 'data-shop': 'royal', onclick: () => Royal.enter() },
          h('div', { class: 'marquee' }, h('span', { class: 'bulbs' }), h('h3', {}, 'Casino Royal'), h('span', { class: 'bulbs' })),
          h('div', { class: 'portal-door' }, '🎩'),
          h('div', { class: 'brass-sign' }, gate ? 'Hausordnung' : chk.ok ? (State.s.flags.royalGuest ? 'Gast des Hauses' : `Eintritt ${UI.fmt(RoyalRules.ENTRY_FEE)}`) : chk.text),
          gate ? h('div', { class: 'doorman' }, h('span', { class: 'who' }, '🕴️'), h('span', {}, gate)) : null));
      }
```

- [ ] **Step 2: CSS** (die vier `.storefront.royal`-Zeilen und `.strasse .storefront.royal` ersetzen)

```css
/* Casino Royal – Fassade in der Stadt */
.facade { position: relative; grid-column: 1 / -1; min-height: 240px; display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 14px 16px 18px; cursor: pointer; border: 2px solid #c9a961; border-radius: 4px; overflow: hidden;
  background: repeating-linear-gradient(180deg, #141216 0 22px, #0e0d10 22px 24px); box-shadow: inset 0 0 0 4px #141216, inset 0 0 0 5px #8a6a2e, var(--shadow); }
.facade.locked { filter: saturate(.6) brightness(.85); }
.marquee { display: flex; align-items: center; gap: 12px; }
.marquee h3 { margin: 0; font-family: "Cinzel", Georgia, serif; font-weight: 700; font-size: 1.8rem; letter-spacing: .25em; text-transform: uppercase; color: #f1dfa8; text-shadow: 0 0 14px rgba(201,169,97,.5); }
.bulbs { width: 96px; height: 10px; background: radial-gradient(circle, #f1dfa8 0 2px, rgba(241,223,168,.25) 3px, transparent 4px) 0 50% / 12px 10px repeat-x; }
.portal-door { width: 120px; height: 120px; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 12px; font-size: 2.6rem; background: #0b0a0c; border: 2px solid #c9a961; border-radius: 60px 60px 4px 4px; box-shadow: inset 0 0 0 4px #0b0a0c, inset 0 0 0 5px #8a6a2e; position: relative; }
.portal-door::before { content: ""; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); width: 60%; height: 4px; background: #c9a961; box-shadow: 0 -6px 0 -1px #c9a961, 0 -12px 0 -2px #c9a961; }
.facade:not(.locked) .portal-door { background: radial-gradient(ellipse at 50% 70%, rgba(201,169,97,.18), #0b0a0c 70%); }
.brass-sign { padding: 6px 16px; background: linear-gradient(160deg, #b8923f, #e2c77a 45%, #9a7a2f); color: #2a1d08; font-family: var(--font-mono); font-size: .8rem; font-weight: 700; border: 1px solid #5a4520; box-shadow: inset 0 0 0 1px #e2c77a; text-shadow: 0 1px 0 rgba(255,255,255,.35); text-align: center; }
.doorman { position: absolute; left: 50%; bottom: 14px; transform: translateX(-50%); display: flex; align-items: center; gap: 10px; padding: 8px 14px; background: #0b0a0c; border: 1px solid #c9a961; color: #efe6cf; font-family: var(--font-mono); font-size: .8rem; white-space: nowrap; }
.doorman .who { font-size: 1.6rem; }
.facade.gated .portal-door { opacity: .35; }
@media (hover: hover) { .bulbs { animation: marquee 1.2s linear infinite; } .facade:hover:not(.locked) { border-color: #f1dfa8; } }
@keyframes marquee { to { background-position: 12px 50%; } }
@media (max-width: 760px) { .facade { min-height: 200px; } .marquee h3 { font-size: 1.3rem; } .bulbs { width: 60px; } .doorman { white-space: normal; width: 90%; } }
@media (prefers-reduced-motion: reduce) { .bulbs { animation: none; } }
```

Hinweis: Die Fassade liegt im Keller (Zone `keller`), daher stehen die Farben hier als Werte, nicht als Royal-Tokens. `.strasse` bleibt unverändert; die Fassade nutzt `grid-column: 1 / -1` selbst.

- [ ] **Step 3: Prüfen und committen**

Run: Node/DOM-Selftests grün. `python3 tests/desktop-diff.py hub roulette slots finance` → 0 (die Stadt ist bewusst nicht in der Liste).
Drei Screenshots per CDP oder `tests/screenshot.sh`: `?fresh&mode=free&screen=stadt` (ohne Auto: `.locked`, Schild „Parkservice only…"), mit `State.s.car='audiA3'` (Portal warm, „Eintritt 100 €"), Story Kater mit `flags.zitter` (Türsteher-Panel).

```bash
git add keller37.html
git commit -m "feat(royal): Fassade mit Marquee, Goldportal, Messingschild und Türsteher in der Stadt

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Kater-HUD und Zitter-Tag

**Files:**
- Modify: `keller37.html` (`royal-rules`; `Story.hudNotes` im Block `story-engine` ~Zeile 5576; `UI.renderWallet`; `STORY_KATER` Block `story-kater`: `hudRender`, Hooks `zitterEnde`/`zitterEndeBrownie`; CSS)
- Test: Node (`leberTone`, `deckelMarks`), Sichtprüfung

**Interfaces:**
- Produces: `RoyalRules.leberTone(v) → 'ok'|'warn'|'danger'`, `RoyalRules.deckelMarks(v) → 0…8`, `Story.katerHud() → HTMLElement`, `body.zitter`.

- [ ] **Step 1: Failing Node-Tests**

```js
T.test('RoyalRules.leberTone/deckelMarks', () => {
  T.eq([100, 61, 60, 31, 30, 0].map(RoyalRules.leberTone), ['ok', 'ok', 'warn', 'warn', 'danger', 'danger']);
  T.eq([0, 49, 50, 100, 400, 450, 9999].map(RoyalRules.deckelMarks), [0, 0, 1, 2, 8, 8, 8]);
});
```

- [ ] **Step 2: Helfer**

```js
  /* Kater-HUD: Leber-Farbstufe und Strichliste auf dem Bierdeckel (ein Strich je 50 €, höchstens 8) */
  leberTone(v) { return v > 60 ? 'ok' : v > 30 ? 'warn' : 'danger'; },
  deckelMarks(v) { return Math.min(8, Math.floor((v || 0) / 50)); },
```

Run: Node-Selftest grün.

- [ ] **Step 3: `Story.katerHud` und Abzweig in `hudNotes`**

`hudNotes` ersetzen:

```js
  hudNotes() {
    if (this.story.hudRender === 'kater') return [this.katerHud()];
    return (this.story.hud || []).map((hd) => {
      const v = this.s.vars[hd.var] || 0;
      const txt = hd.fmt === 'money' ? UI.fmt(v) : (hd.max ? `${v}/${hd.max}` : String(v));
      const label = typeof hd.label === 'function' ? hd.label(State.s) : hd.label;
      return h('span', { class: `note ${hd.tone || 'gold'}` }, `${label} ${txt}`);
    });
  },
  /* Story 2: Leber-Balken, Bierkrüge, Bierdeckel statt drei Zettel */
  katerHud() {
    const v = this.s.vars, f = this.s.flags;
    const leber = Math.max(0, Math.min(100, v.leber || 0)), pegel = v.pegel || 0, deckel = v.deckel || 0;
    const tone = RoyalRules.leberTone(leber);
    const covered = pegel >= 3 || (f.sucht && (v.brownieHeute || 0) > 0);
    const kruege = [0, 1, 2].map((i) => h('span', { class: 'krug' + (i < pegel ? ' on' : '') }, '🍺'));
    if (f.sucht) kruege.push(h('span', { class: 'krug' + ((v.brownieHeute || 0) > 0 ? ' on' : '') }, '🍪'));
    const marks = RoyalRules.deckelMarks(deckel);
    return h('div', { class: 'kater-hud' },
      h('span', { class: `hud-leber ${tone}`, title: `Leber ${leber}/100` }, '🫀', h('span', { class: 'bar' }, h('span', { class: 'fill', style: `width:${leber}%` })), h('span', { class: 'val' }, `${leber}`)),
      h('span', { class: 'hud-pegel' + (covered ? ' covered' : ''), title: `Pegel ${pegel}/3` }, ...kruege),
      h('span', { class: 'hud-deckel' + (deckel > 0 ? '' : ' empty'), title: `Deckel ${UI.fmt(deckel)}` },
        h('span', { class: 'coaster' }, '𝍸'.repeat(Math.floor(marks / 5)) + '𝍷'.repeat(marks % 5) + (deckel >= 450 ? '…' : '')), h('span', { class: 'val' }, UI.fmt(deckel))),
      f.zitter ? h('span', { class: 'note danger' }, '🫨 Zittern · −15 Glück') : null);
  },
```

Hinweis: `𝍷` (U+1D377, ein Strich) und `𝍸` (U+1D378, fünf Striche) sind Tally-Marks-Zeichen; Fallback in den meisten Systemschriften vorhanden. Wenn die Anzeige im Screenshot leer bleibt, stattdessen `'|'.repeat(marks)` verwenden.

In `STORY_KATER` direkt nach `id: 'kater', …` (Zeile ~6339) `hudRender: 'kater',` ergänzen. Die bestehende `hud:`-Liste bleibt.

- [ ] **Step 4: Zittern – Body-Klasse und Hook-Toasts**

In `UI.renderWallet` (vor `const notes = qs('#notes')`):

```js
    document.body.classList.toggle('zitter', State.mode === 'story' && typeof Story !== 'undefined' && !!(Story.s && Story.s.flags && Story.s.flags.zitter));
```

Hooks in `STORY_KATER.hooks` ergänzen (Effekte anhängen):

```js
    { id: 'zitterEnde', when: { flag: 'zitter' }, at: 'buy:beer', effects: [{ unflag: 'zitter' }, { luckMod: 0 }, { jobMod: null }, { toast: { icon: '🍺', title: 'Ruhige Hände.', tone: 'win' } }] },
    { id: 'zitterEndeBrownie', when: { flag: 'zitter' }, at: 'buy:brownie', effects: [{ unflag: 'zitter' }, { luckMod: 0 }, { jobMod: null }, { toast: { icon: '🍪', title: 'Ruhige Hände.', tone: 'win' } }] },
```

Prüfen, dass der Node-Test `runHook(s, 'buy:beer').includes('zitterEnde')` weiter grün ist (Toast-Effekte werden im Node-Kontext ignoriert bzw. `UI` existiert dort nicht – falls `out.toast` im Node-Test aufgerufen wird, den Aufruf mit `typeof UI !== 'undefined'` schützen).

- [ ] **Step 5: CSS**

```css
/* Kater-HUD (Story 2) */
.kater-hud { display: inline-flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.kater-hud > span { display: inline-flex; align-items: center; gap: 5px; font-family: var(--font-mono); font-size: .78rem; color: var(--text); }
.hud-leber .bar { width: 90px; height: 10px; background: #1c1f1a; border: 1px solid #3a3f35; border-radius: 2px; overflow: hidden; }
.hud-leber .fill { display: block; height: 100%; background: var(--neon-green); transition: width .3s; }
.hud-leber.warn .fill { background: #e8c65a; }
.hud-leber.danger .fill { background: var(--neon-red); animation: pulseText 1.2s infinite; }
.hud-pegel .krug { opacity: .3; font-size: 1rem; }
.hud-pegel .krug.on { opacity: 1; }
.hud-pegel.covered { border-bottom: 2px solid var(--neon-green); padding-bottom: 1px; }
.hud-deckel .coaster { width: 34px; height: 34px; border-radius: 50%; background: #d9c7a3; color: #4a3a22; border: 2px solid #b8a27a; box-shadow: inset 0 0 0 4px #d9c7a3, inset 0 0 0 5px #b8a27a; display: inline-flex; align-items: center; justify-content: center; font-size: .6rem; line-height: 1; letter-spacing: -1px; }
.hud-deckel.empty .coaster { opacity: .4; }
body.zitter .balance, body.zitter .hud-pegel { animation: zitter 3s infinite; }
@keyframes zitter { 0%, 8%, 100% { transform: translateX(0); } 1% { transform: translateX(-1px); } 3% { transform: translateX(1px); } 5% { transform: translateX(-1px); } 7% { transform: translateX(1px); } }
@media (max-width: 760px) { .hud-leber .bar { width: 70px; } }
@media (prefers-reduced-motion: reduce) { body.zitter .balance, body.zitter .hud-pegel, .hud-leber.danger .fill { animation: none; } }
```

- [ ] **Step 6: Prüfen und committen**

Node/DOM-Selftests grün. Screenshot Story Kater (`?fresh&story=kater&prev=doc&day=5`, Intro durchklicken): Balken grün 100, drei blasse Krüge, Deckel. Dann per Konsole `Story.s.flags.zitter = true; Story.s.vars.leber = 25; Story.s.vars.deckel = 250; UI.renderWallet()` → roter pulsierender Balken, 5 Striche, roter Zettel, Kontostand zittert.

```bash
git add keller37.html
git commit -m "feat(kater): HUD mit Leber-Balken, Bierkrügen und Bierdeckel; Zitter-Tag sichtbar

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Cutscene-Hintergrund, Sylvie-Rahmen, Goldregen, Trophäen-Konfetti

**Files:**
- Modify: `keller37.html` (CSS `.cs-bg.royal` ~Zeile 601–602; `Cutscene._panel` ~Zeile 2234; `Royal.onWin`; `Achievements.unlock`; CSS)
- Test: Sichtprüfung (`?fresh&story=kater&prev=doc&day=5` → Royal-Szene), `tests/playtest-story.py` läuft weiter grün

**Interfaces:**
- Produces: `Royal.goldRain(n)`, `.cs-portrait.royal-frame`, `.balance.gold-flash`, `.confetti`.

- [ ] **Step 1: Cutscene-Hintergrund und Portrait**

`.cs-bg.royal` und `.cs-bg.royal::after` ersetzen:

```css
.cs-bg.royal { background: linear-gradient(180deg, transparent 70%, rgba(0,0,0,.5)), conic-gradient(from 180deg at 50% -5%, transparent 0deg, rgba(201,169,97,.05) 7.5deg, transparent 15deg), radial-gradient(ellipse at 50% 0%, #4a1520 0%, #1c080e 45%, #0b0508 100%); }
.cs-bg.royal::before { content: ""; position: absolute; left: 50%; top: 4%; width: 220px; height: 60px; transform: translateX(-50%); border: 2px solid #c9a961; border-top: 0; border-radius: 0 0 110px 110px;
  background: radial-gradient(circle at 10% 100%, #f1dfa8 0 3px, rgba(241,223,168,.5) 5px, transparent 8px), radial-gradient(circle at 25% 100%, #f1dfa8 0 3px, rgba(241,223,168,.5) 5px, transparent 8px), radial-gradient(circle at 40% 100%, #f1dfa8 0 3px, rgba(241,223,168,.5) 5px, transparent 8px), radial-gradient(circle at 50% 100%, #f1dfa8 0 3px, rgba(241,223,168,.5) 5px, transparent 8px), radial-gradient(circle at 60% 100%, #f1dfa8 0 3px, rgba(241,223,168,.5) 5px, transparent 8px), radial-gradient(circle at 75% 100%, #f1dfa8 0 3px, rgba(241,223,168,.5) 5px, transparent 8px), radial-gradient(circle at 90% 100%, #f1dfa8 0 3px, rgba(241,223,168,.5) 5px, transparent 8px); }
.cs-bg.royal::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 30%; background: linear-gradient(180deg, transparent, rgba(0,0,0,.4)), repeating-linear-gradient(45deg, #141216 0 28px, #1a171c 28px 56px); opacity: .7; }
.cs-portrait.royal-frame { border-color: #c9a961; box-shadow: 0 0 0 3px #0b0a0c, 0 0 0 4px #8a6a2e, 0 0 24px rgba(201,169,97,.4); }
```

In `Cutscene._panel` nach `els.portrait.className = …` ergänzen:

```js
      els.portrait.classList.toggle('royal-frame', p.bg === 'royal' || p.who === 'sylvie');
```

- [ ] **Step 2: Goldregen und Kontostand-Blitz**

In `Royal` ergänzen:

```js
  /* Goldregen über der Bühne (Gast des Hauses); Handy/Reduced-Motion: weniger Partikel */
  goldRain(n = 30) {
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const count = reduced || UI.mobile() ? 12 : n;
    const stage = qs('#stage'); if (!stage) return;
    for (let i = 0; i < count; i++) {
      const p = h('span', { class: 'gold-drop', style: `left:${rand(2, 98)}%; animation-delay:${rand(0, 0.8)}s; font-size:${rand(1, 2)}rem` }, pick(['🪙', '✨', '✦']));
      stage.append(p); setTimeout(() => p.remove(), 2600);
    }
    const bal = qs('#balance'); if (bal) { bal.classList.remove('gold-flash'); void bal.offsetWidth; bal.classList.add('gold-flash'); }
  },
```

In `Royal.onWin` vor `await Cutscene.play('royal.guest', …)`: `this.goldRain(); await wait(reduced ? 0 : 900);` mit `const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;` davor.

CSS:

```css
.gold-drop { position: absolute; top: -10%; z-index: 5; pointer-events: none; animation: goldDrop 2.2s ease-in both; text-shadow: 0 0 8px rgba(241,223,168,.8); }
@keyframes goldDrop { from { transform: translateY(0) rotate(0); opacity: 1; } to { transform: translateY(110vh) rotate(360deg); opacity: .2; } }
#stage { position: relative; }
.balance.gold-flash { animation: goldFlash .8s ease both; }
@keyframes goldFlash { 0% { box-shadow: 0 0 0 0 rgba(241,223,168,.9); } 100% { box-shadow: 0 0 0 22px rgba(241,223,168,0); } }
.confetti { position: fixed; z-index: 96; pointer-events: none; color: var(--gold-2); animation: confettiBurst 1s ease-out both; }
@keyframes confettiBurst { from { transform: translate(0, 0) scale(1); opacity: 1; } to { transform: translate(var(--dx), var(--dy)) scale(.4); opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .gold-drop, .confetti { animation: none; display: none; } .balance.gold-flash { animation: none; } }
```

(`.stage` hat bereits `position: relative`; die `#stage`-Zeile nur ergänzen, falls `#stage` nicht `.stage` ist – prüfen mit `grep -n 'id="stage"' keller37.html`.)

- [ ] **Step 3: Konfetti bei `royalHigh`**

In `Achievements.unlock` nach `UI.toast(…)`:

```js
    if (id === 'royalHigh' && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const box = qs('#toasts'); const r = box.getBoundingClientRect();
      for (let i = 0; i < 12; i++) {
        const a = (i / 12) * Math.PI * 2;
        const c = h('span', { class: 'confetti', style: `left:${r.left + r.width / 2}px; top:${r.top + 20}px; --dx:${Math.round(Math.cos(a) * 90)}px; --dy:${Math.round(Math.sin(a) * 90)}px` }, '✦');
        document.body.append(c); setTimeout(() => c.remove(), 1100);
      }
    }
```

- [ ] **Step 4: Prüfen und committen**

Node/DOM-Selftests grün. Sichtprüfung: `?fresh&mode=free&screen=royal` mit `State.s.car='audiA3'` → `Cutscene.play('royal.first')` per Konsole: Kronleuchter oben, Marmorboden unten, Sylvie mit Goldrahmen. `Royal.goldRain()` in der Lobby → Münzen fallen, Kontostand blitzt. `Achievements.unlock('royalHigh')` → Toast mit Konfetti.

```bash
git add keller37.html
git commit -m "feat(royal): Kronleuchter-Hintergrund, Sylvie-Goldrahmen, Goldregen und Trophäen-Konfetti

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Tests, Screenshots, README

**Files:**
- Modify: `tests/mobile-check.py`, `tests/playtest-story.py`, `README.md`
- Create/Update: `docs/superpowers/screenshots/royal-lobby.png`, `royal-mega.png`, `royal-craps.png`, `royal-wheel.png`, `royal-fassade.png`, `kater-hud.png`, `scene-royal.png`, `mobile-royal.png`, `mobile-craps.png`
- Test: alle Läufe grün

- [ ] **Step 1: Zonen-Check in `tests/mobile-check.py`**

Nach dem Tab-Check einfügen:

```python
        # Zone: Royal-Screens setzen body[data-zone=royal], Keller-Screens keller
        zones = {}
        for sc in ["hub", "royal", "craps", "megaslots", "wheel", "stadt"]:
            await cdp.navigate(URL + "?fresh&mode=free&screen=" + sc, wait=1.2)
            zones[sc] = await cdp.eval("document.body.dataset.zone", await_promise=False)
        record("zone: Royal-Screens royal, Keller-Screens keller",
               all(zones[k] == "royal" for k in ["royal", "craps", "megaslots", "wheel"]) and zones["hub"] == "keller" and zones["stadt"] == "keller", zones)
```

- [ ] **Step 2: Playtest-Szenario `scenario_royal_look`**

In `tests/playtest-story.py` vor `async def main():` einfügen und in `main()` nach `await scenario_royal_free(cdp)` aufrufen:

```python
async def scenario_royal_look(cdp):
    """Art-deco-Paket: Zone + Vorhang beim Betreten/Verlassen, Fassade in drei Zustaenden,
    Kater-HUD, Freispiel-Banner, Bankrott-Blackout, Goldregen."""
    # Fassade ohne Auto
    await cdp.navigate(URL_BASE + "?fresh&mode=free&screen=stadt")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.eval("localStorage.removeItem('keller37.meta')", await_promise=False)
    f = await cdp.eval("(function(){ const f=document.querySelector('.facade'); return f && {locked: f.classList.contains('locked'), sign: f.querySelector('.brass-sign').textContent, doorman: !!f.querySelector('.doorman')}; })()", await_promise=False) or {}
    record("fassade: ohne Auto gesperrt mit Parkservice-Schild", f.get("locked") and "Parkservice" in (f.get("sign") or "") and not f.get("doorman"), f)
    # Fassade mit Auto + Zone beim Betreten
    await cdp.eval("State.s.car = 'audiA3'; State.s.balance = 5000; State.s.flags.royalSeen = true; State.save(); Stadt.render();", await_promise=False)
    f = await cdp.eval("(function(){ const f=document.querySelector('.facade'); return {locked: f.classList.contains('locked'), sign: f.querySelector('.brass-sign').textContent}; })()", await_promise=False) or {}
    record("fassade: mit Auto offen, Schild Eintritt 100", not f.get("locked") and "100" in (f.get("sign") or ""), f)
    zone_before = await cdp.eval("document.body.dataset.zone", await_promise=False)
    await cdp.eval("document.querySelector('.facade').click()", await_promise=False)
    await asyncio.sleep(0.15)
    fade_on = await cdp.eval("document.querySelector('#zonefade').classList.contains('on')", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'royal' && !UI.busy", timeout=4.0)
    zone_after = await cdp.eval("document.body.dataset.zone", await_promise=False)
    sub = await cdp.eval("getComputedStyle(document.querySelector('#brandSub')).display", await_promise=False)
    record("zone: Vorhang beim Betreten, Zone royal, Untertitel sichtbar", zone_before == "keller" and fade_on is True and zone_after == "royal" and sub == "block",
           "before=%s fade=%s after=%s sub=%s" % (zone_before, fade_on, zone_after, sub))
    portals = await cdp.eval("document.querySelectorAll('.portal').length", await_promise=False)
    record("lobby: drei Portale", portals == 3, "portals=%s" % portals)
    # Mega Seven: Freispiel-Banner + Gewinnlinie
    await cdp.eval("UI.show('megaslots')")
    mega = await cdp.eval("""(async function(){
      RoyalRules.megaRoll = function(){ return [['⭐','7️⃣','💎'],['⭐','7️⃣','BAR'],['⭐','7️⃣','🍒'],['BAR','7️⃣','🔔'],['🍒','7️⃣','💎']]; };
      RoyalRules.megaLuckOverride = function(g){ return g; };
      document.querySelector('#megaBet').value = '100';
      await MegaSlots.spin();
      return { banner: document.querySelector('#megaFree').classList.contains('show'), free: MegaSlots.freeLeft,
               lines: document.querySelectorAll('#megaLinesSvg polyline').length, cls: document.querySelector('.mega-machine').classList.contains('free') };
    })()""")
    record("mega: Freispiel-Banner und goldene Gewinnlinie", mega and mega.get("banner") and mega.get("free", 0) > 0 and mega.get("lines", 0) >= 1 and mega.get("cls"), mega)
    # Glücksrad: Bankrott -> Blackout-Klasse + Sylvie-Toast
    await cdp.eval("UI.show('wheel')")
    wheel = await cdp.eval("""(async function(){
      RoyalRules.wheelSpin = function(){ return 0; };
      RoyalRules.wheelLuckOverride = function(i){ return i; };
      document.querySelector('#wheelBet').value = '100';
      const p = Wheel.spin();
      await new Promise(r => setTimeout(r, 4800));
      const black = document.querySelector('.wheel-panel').classList.contains('blackout');
      const toast = document.querySelector('#toasts').textContent.includes('Das Haus dankt');
      const seg = document.querySelector('.wheel .seg.bust') !== null;
      await p;
      return { black, toast, seg };
    })()""", timeout=20)
    record("wheel: Bankrott dunkelt ab, Sylvie-Toast, Bust-Segmente", wheel and wheel.get("black") and wheel.get("toast") and wheel.get("seg"), wheel)
    # Goldregen + zurueck in die Stadt = Zone keller
    rain = await cdp.eval("Royal.goldRain(); document.querySelectorAll('.gold-drop').length", await_promise=False)
    record("royal: Goldregen erzeugt Partikel", (rain or 0) >= 12, "drops=%s" % rain)
    await cdp.eval("UI.show('royal')")
    await cdp.click("#royalLeave")
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=4.0)
    zone_back = await cdp.eval("document.body.dataset.zone", await_promise=False)
    record("zone: zurueck in die Stadt = keller", zone_back == "keller", "zone=%s" % zone_back)
    # Kater-HUD + Zitter + Tuersteher
    await cdp.navigate(URL_BASE + "?fresh&story=kater&prev=doc&day=5")
    await asyncio.sleep(1.2)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=30)
    hud = await cdp.eval("""(function(){
      Story.s.vars.leber = 25; Story.s.vars.pegel = 2; Story.s.vars.deckel = 250; Story.s.flags.zitter = true; State.s.car = 'audiA3'; State.save(); UI.renderWallet();
      const bar = document.querySelector('.hud-leber .fill'); const kr = document.querySelectorAll('.hud-pegel .krug.on').length;
      return { width: bar && bar.style.width, danger: !!document.querySelector('.hud-leber.danger'), kruege: kr,
               marks: (document.querySelector('.hud-deckel .coaster') || {}).textContent, zitter: document.body.classList.contains('zitter'),
               note: document.querySelector('#notes').textContent.includes('Zittern') };
    })()""", await_promise=False) or {}
    record("kater-hud: Leber 25 rot, 2 Kruege, 5 Striche, Zittern", hud.get("width") == "25%" and hud.get("danger") and hud.get("kruege") == 2 and hud.get("zitter") and hud.get("note") and len(hud.get("marks") or "") >= 1, hud)
    await cdp.eval("UI.show('stadt')")
    door = await cdp.eval("(function(){ const f=document.querySelector('.facade'); return f && {gated: f.classList.contains('gated'), doorman: !!f.querySelector('.doorman'), txt: (f.querySelector('.doorman')||{}).textContent}; })()", await_promise=False) or {}
    record("fassade: Zitter-Tag zeigt Tuersteher", door.get("gated") and door.get("doorman") and "zittern" in (door.get("txt") or "").lower(), door)
```

Falls `cdp.wait_for` in der Datei anders heißt, den vorhandenen Helfer verwenden (`grep -n "async def wait_for" tests/playtest-story.py`).

- [ ] **Step 3: Alle Tests laufen lassen**

```bash
node tests/run-selftest.mjs 2>&1 | tail -1
sh tests/dom-selftest.sh | tail -1
python3 tests/desktop-diff.py
python3 tests/mobile-check.py 2>&1 | grep -v "^screenshot\|^OK"
K37_PORT=9375 K37_PROFILE=/tmp/k37-royal-profile K37_SHOTS=/tmp/k37-royal-shots python3 tests/playtest-story.py > /tmp/k37-royal.log 2>&1; tail -3 /tmp/k37-royal.log; grep "^FAIL" /tmp/k37-royal.log
```

Expected: alles grün, Desktop-Diff 0 Pixel, Playtest 0 fehlgeschlagen. Fehlschläge zuerst beheben.

- [ ] **Step 4: Screenshots erneuern**

Desktop (`tests/screenshot.sh`) reicht für `royal-lobby.png` (`?fresh&mode=free&screen=royal`), `royal-mega.png` (`screen=megaslots`), `royal-craps.png` (`screen=craps`), `royal-wheel.png` (`screen=wheel`). Für `royal-fassade.png` (mit Auto), `kater-hud.png` (Zitter-Zustand) und `scene-royal.png` (Cutscene `royal.first`) ein kurzes CDP-Skript nach dem Muster von `scenario_royal_look` schreiben (Zustand setzen, `cdp.screenshot`). Handy: `K37_SHOTS=docs/superpowers/screenshots python3 tests/mobile-check.py` erzeugt `mobile-royal.png`, `mobile-craps.png` (die übrigen `mobile-*.png` dürfen mit erneuert werden). Alte `royal-lobby.png`, `royal-mega.png`, `royal-craps.png` werden überschrieben.

- [ ] **Step 5: README**

Im Abschnitt „Was drin ist" den Casino-Royal-Punkt (suche `Casino Royal`) um einen Satz zum Look ergänzen und einen Punkt „Kater-HUD" anfügen:

```markdown
- **Casino Royal:** … Ein anderer Ort: Art déco in Gold und Schwarz – beim Betreten wechselt die ganze Seite (Kopfzeile, Seitenleiste, Chips) hinter einem Gold-Vorhang, die Lobby ist ein Foyer mit drei Portalen, Mega Seven zeichnet Gewinnlinien in Gold und klappt bei Freispielen ein Banner aus, Craps markiert Einsätze mit Chip-Stapeln, das Glücksrad hat Zahnkranz, Lauflichter und beim Bankrott gehen kurz die Lichter aus. In der Stadt steht die Fassade mit Marquee, Messingschild und – am Zitter-Tag – einem Türsteher.
- **Kater-HUD (Story 2):** Leber als Balken (grün → gelb → rot, pulsiert ab 30), Pegel als drei Bierkrüge, Deckel als Bierdeckel mit Strichliste; am Zitter-Tag zittern Kontostand und Krüge, ein roter Zettel zeigt −15 Glück, das erste Bier beendet es („Ruhige Hände.").
```

Im Abschnitt „Tests" die Zeile `python3 tests/desktop-diff.py       # Keller-Screens pixelidentisch zu main? (1280×900, Pillow)` ergänzen und beim `mobile-check.py`-Satz „… und den Zonen-Wechsel (Royal/Keller)" anfügen.

- [ ] **Step 6: Commit**

```bash
git add tests/mobile-check.py tests/playtest-story.py README.md docs/superpowers/screenshots/
git commit -m "test(royal): Playtest-Szenario Art-déco-Paket, Zonen-Check, Screenshots; docs: README

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:** §3 Zone/Vorhang/Tokens → Task 1. §4 Kopfzeile/Seitenleiste → Task 1. §5 Lobby → Task 2. §6 gemeinsame Bausteine → Task 1; 6.1 → Task 3; 6.2 → Task 4; 6.3 → Task 5. §7 Fassade → Task 6. §8 Kater-HUD/Zitter → Task 7. §9 Cutscene/Goldregen/Trophäe → Task 8 (Toast-Ton `gold` existiert bereits; nur Konfetti neu). §10 Tests/Screenshots/README → Task 1 (Desktop-Diff), Task 9. §2 Reduced-Motion/Hover/Handy: in jedem CSS-Block enthalten.

**Placeholder scan:** keine TBD/TODO; jeder Code-Schritt hat Code.

**Type consistency:** `RoyalRules.SCREENS/zoneFor` (T1) ← `UI.show` (T1), `mobile-check` (T9). `megaLinePoints(line, count, cell, gap, pad)` (T3) ← `drawLines` (T3). `wheelTone/WHEEL_COLORS` (T5) ← `build` (T5), Playtest `.seg.bust` (T9). `leberTone/deckelMarks` (T7) ← `katerHud` (T7), Playtest (T9). `Royal.goldRain(n)` (T8) ← Playtest (T9). `#brandSub` (T1) ← Playtest (T9). `.facade/.gated/.doorman/.brass-sign` (T6) ← Playtest (T9). `#megaFree.show`, `.mega-machine.free`, `#megaLinesSvg polyline` (T3) ← Playtest (T9). `.wheel-panel.blackout` (T5) ← Playtest (T9).
