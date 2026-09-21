# Überfall und Russisch Roulette auf der Ego-Bühne (Stufe 3) – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Überfall (Kampf/Flucht) und Russisches Roulette werden Action-Sequenzen auf der gemeinsamen Ego-Bühne: Kampf und Flucht als Vollbild-Einschub mit Timing-Ring (+10 Prozentpunkte bei gutem Tipp, Ausgang bleibt gewürfelt), Roulette in Ego-Sicht mit Mündung auf der Kamera und Igor gegenüber am Tisch.

**Architecture:** `DuelStage` wird zu `EgoStage` (Alias `DuelStage` bleibt) und bekommt Hand-Varianten, Timing-Ring, laufende Kulisse, Trommel-Nahaufnahme, Kulisse `hinterzimmer` und die Effekte `punch/grab/muzzleAt/selfShot/slideProp`. Neues Objekt `MugAction` (Block `mugging`) öffnet das Vollbild-Overlay `#ego`, spielt Anlauf → Ring → Tipp → Würfeln → Ausgang und gibt `{ won, bonus }` an `Mugging.run` zurück. `Russian` behält seine Schnittstelle und ersetzt das Emoji-Panel durch `EgoStage`-Aufrufe (`#rrStage`). Reine Regeln (`GangRules.TIMING`, `timingBonus`, `chanceWithBonus`) sind Node-testbar.

**Tech Stack:** Vanilla JS/CSS, Canvas 2D, Inline-SVG in einer Datei; Node-Selbsttest (`node tests/run-selftest.mjs`), Headless-Chrome-Selbsttest (`tests/dom-selftest.sh`), CDP-Playtest (`python3 tests/playtest-story.py`), Trace (`python3 tests/perf-trace.py`).

**Spec:** `docs/superpowers/specs/2026-09-21-ego-buehne-ueberfall-roulette-design.md`

Die Code-Blöcke dieses Plans wurden in einem Wegwerf-Prototyp gegen den aktuellen `main` (`55a30a2`) verifiziert – Node 323/323, DOM 371/371, Story-Playtest 188 Checks grün, Trace-Szenarien gemessen. Wörtlich übernehmen.

## Global Constraints

- Eine Datei `keller37.html`, keine Bilddateien, keine externen Abhängigkeiten.
- Unverändert: `Rules.mugChance`, `Rules.fightChance`, `Rules.fleeChance`, `Rules.mugLoot`, `mugWallet`, `fleeFailExtra`, Cooldown, Stärke-Regeln; `Rules.rrCylinder`, `rrDelta`, Einsatzabzug, Events `rr:result`/`rr:forced`, `Game.settle`, `Russian.start({ forced: true })`, Szene `rr.headshot`; `Shootout` und seine Tests.
- Schnittstellen bleiben: `Mugging.maybe/run/force/running/TYPES`; `mug:done` trägt zusätzlich `bonus`; `Russian.start/pull/end/drop/inDuel/duel/busy`; Template-IDs `#rrStatus`, `#rrBetControls`, `#rrActionControls`, `#btnTrigger`, `#btnDuel`, `#rrBet`, `#chambersLeft`; `const DuelStage = EgoStage` (Duell, Tests und Playtest sprechen die Bühne weiter als `DuelStage` an).
- Timing-Regel exakt: `GangRules.TIMING = { window: 900, gold: 250, bonus: 0.10, cap: 0.95 }`; `timingBonus(t)` liefert `bonus` nur für `t != null && window − gold ≤ t ≤ window`; `chanceWithBonus(p, bonus) = min(0.95, p + bonus)`. Nur der erste Tipp zählt; Tipps vor Ringstart werden ignoriert; kein Malus.
- Bewegung von DOM-Elementen nur über `transform`/`opacity`; jedes `@keyframes cs*`/`duel*`/`ego*` animiert nur transform/opacity. Canvas zeichnet pro Frame nur Bewegtes; Kulisse vorgerendert.
- `prefers-reduced-motion`: Ring als statische Leiste mit Marker, Kulisse steht (keine `run`-Klasse), Figur wechselt Größe ohne Transition, Trommel springt, kein Blitz/Ruck, Revolver direkt in Mündungssicht.
- Deutsche Spieltexte, deutsche Kommentare wie im Rest der Datei.
- Commit-Trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`. Kein Push, kein Merge nach main ohne ausdrückliche Freigabe.
- `main` bewegt sich parallel (andere Instanz): vor Task 1 auf den aktuellen `main` aufsetzen; Fundstellen per `grep -n` (unten), nicht per Zeilennummer.
- Playtests nur starten, wenn `pgrep -f "playtest-story|remote-debugging-port=9335"` leer ist (die andere Instanz teilt Port 9335 und `/tmp/k37story-profile`).

---

## Dateistruktur

| Stelle | Inhalt |
|---|---|
| `keller37.html` Block `gang-rules` | `TIMING`, `timingBonus`, `chanceWithBonus` hinter `HIT_MARGIN` |
| `keller37.html` Block `cutscene-director` | `POSES` + `windup`, `temple`, `relief` |
| `keller37.html` Block `sfx` | `punch`, `whoosh` hinter `gunshot` |
| `keller37.html` CSS | Posen `windup/temple/relief` + Keyframes `csWindup/csRelief` (Cutscene-Teil); `#ego`-Overlay hinter `#cutscene[hidden]`; `.unarmed`, `.duel-gun.up.muzzle`, `.run`/`.jerk`, Keyframes `egoBob/egoJerk` hinter `csHit`; reduced-motion-Zeile der Bühne; Roulette-Block `.rr-panel …` ersetzt; `cylZoom` entfällt |
| `keller37.html` HTML | `<div id="ego" hidden></div>` hinter `#cutscene`; `tpl-russian` mit `#rrStage` |
| `keller37.html` Block `game-shootout` | `DuelStage` → `EgoStage` (Block komplett ersetzt) + Alias |
| `keller37.html` Block `mugging` | `Mugging.run` (Kampf/Flucht über `MugAction`, `bonus` im Event); neues Objekt `MugAction` vor `Cutscene.define('mug.intro'` |
| `keller37.html` Block `game-russian` | `Russian` komplett ersetzt; `UI.register('russian')` mount/unmount |
| `keller37.html` Block `selftest` | Node-Tests vor `if (typeof CsCast !== 'undefined') {` (Test `CsCast: Looks für Bahnhof-Läufer…`) und hinter dem Test `CsDirector.POSES kennt draw und hit`; DOM-Tests vor `const pseudoAnim = …` |
| `tests/playtest-story.py` | Helfer `__pt.egoTap()`, `__pt.lastMug`; Überfall-Szenario tippt in den Ring; Tag-10-Duell klickt nur, wenn `!Russian.busy` |
| `tests/perf-trace.py`, `README.md`, Spec | Szenarien „Ueberfall Kampf", „Russisch Roulette"; Doku |

Fundstellen per `grep -n`: `'  HIT_MARGIN: { mouse: 24, touch: 32 },'`, `"  POSES: ['idle'"`, `'    gunshot() {'`, `'#cutscene[hidden] { display: none; }'`, `'.cs-fig[data-pose="flinch"]'`, `'@keyframes csFade'`, `'@keyframes csHit'`, `'@media (prefers-reduced-motion: reduce) { .duel-stage'`, `'/* -- Russisches Roulette -- */'`, `'@keyframes cylZoom'`, `'<div id="cutscene" hidden></div>'`, `'<template id="tpl-russian">'`, `'/* ================= DUEL STAGE'`, `'/* ================= SCHIESSEREI „ZIEH!“'`, `"if (choice === 'fight') {"`, `"Cutscene.define('mug.intro'"`, `'/* ================= RUSSISCHES ROULETTE ================= */'`, `"UI.register('russian', {"`, `"T.test('CsDirector.POSES kennt draw und hit'"`, `"if (typeof CsCast !== 'undefined') {"`, `'const pseudoAnim = '`.

---

### Task 1: Regeln, Posen, Sounds

**Files:**
- Modify: `keller37.html` Block `gang-rules` (Objekt `GangRules`, hinter `HIT_MARGIN`)
- Modify: `keller37.html` Block `cutscene-director` (`CsDirector.POSES`)
- Modify: `keller37.html` Block `sfx` (`SFX.LIB`, hinter `gunshot`)
- Modify: `keller37.html` Block `selftest`

**Interfaces:**
- Produces: `GangRules.TIMING = { window: 900, gold: 250, bonus: 0.10, cap: 0.95 }`; `GangRules.timingBonus(t, { window, gold, bonus } = GangRules.TIMING) → number` (`t` = Bühnen-ms seit Ringstart oder `null`); `GangRules.chanceWithBonus(p, bonus, cap = GangRules.TIMING.cap) → number`; Posen `windup`, `temple`, `relief` in `CsDirector.POSES` (Regie-Validierung akzeptiert sie); `SFX.play('punch')`, `SFX.play('whoosh')`.

- [ ] **Step 1: Fehlschlagende Tests schreiben**

Im Block `selftest` direkt **vor** der Zeile `if (typeof CsCast !== 'undefined') {` (gefolgt von `T.test('CsCast: Looks für Bahnhof-Läufer und -Junge…`) einfügen:

```js
T.test('GangRules.timingBonus: Bonus nur im goldenen Fenster [window − gold, window], null = kein Tipp; chanceWithBonus deckelt', () => {
  T.eq(GangRules.TIMING, { window: 900, gold: 250, bonus: 0.10, cap: 0.95 });
  T.eq([GangRules.timingBonus(null), GangRules.timingBonus(0), GangRules.timingBonus(649), GangRules.timingBonus(650), GangRules.timingBonus(900), GangRules.timingBonus(901)], [0, 0, 0, 0.10, 0.10, 0]);
  T.eq([GangRules.timingBonus(80, { window: 100, gold: 30, bonus: 0.2 }), GangRules.timingBonus(60, { window: 100, gold: 30, bonus: 0.2 })], [0.2, 0], 'eigenes Fenster');
  T.ok(Math.abs(GangRules.chanceWithBonus(0.35, 0.10) - 0.45) < 1e-9, '0,35 + 0,10 = 0,45');
  T.eq([GangRules.chanceWithBonus(0.9, 0.10), GangRules.chanceWithBonus(0.5, 0), GangRules.chanceWithBonus(0.9, 0.10, 0.99)], [0.95, 0.5, 0.99], 'Deckel 0,95 (Standard) bzw. eigener');
});
```

Direkt **hinter** der Zeile `T.test('CsDirector.POSES kennt draw und hit', () => { … });` (innerhalb desselben `if (typeof CsCast …)`-Blocks) einfügen:

```js
  T.test('CsDirector.POSES kennt windup, temple und relief (Überfall/Roulette)', () => { for (const p of ['windup', 'temple', 'relief']) T.ok(CsDirector.POSES.includes(p), p); });
```

- [ ] **Step 2: Tests laufen lassen – sie müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -5`
Expected: 2 fehlgeschlagen (`GangRules.timingBonus …` mit „TIMING erwartet …" bzw. `timingBonus is not a function`; `CsDirector.POSES kennt windup …`).

- [ ] **Step 3: Regeln**

In `GangRules` direkt hinter der Zeile `  HIT_MARGIN: { mouse: 24, touch: 32 },` einfügen:

```js
  /* ---- Überfall: Timing-Tipp (Ring schrumpft window ms, die letzten gold ms sind gold) → additiver Bonus auf die Kampf-/Fluchtchance, Deckel cap ---- */
  TIMING: { window: 900, gold: 250, bonus: 0.10, cap: 0.95 },
  /* t = Bühnen-ms seit Ringstart des ersten Tipps, null = kein Tipp → bonus im goldenen Fenster [window − gold, window], sonst 0 */
  timingBonus(t, { window, gold, bonus } = GangRules.TIMING) { return t != null && t >= window - gold && t <= window ? bonus : 0; },
  chanceWithBonus(p, bonus, cap = GangRules.TIMING.cap) { return Math.min(cap, p + bonus); },
```

`CsDirector.POSES` ersetzen:

```js
  POSES: ['idle', 'talk', 'point', 'arms-crossed', 'hands-up', 'walk', 'down', 'flinch', 'draw', 'hit', 'windup', 'temple', 'relief'],
```

In `SFX.LIB` direkt hinter der Zeile `    gunshot() { … },` einfügen:

```js
    punch() { this.noise({ dur: 0.1, vol: 0.35, freq: 300 }); this.tone({ freq: 120, type: 'sine', dur: 0.18, vol: 0.4, slide: -70 }); },
    whoosh() { this.noise({ dur: 0.28, vol: 0.18, freq: 1800, type: 'highpass' }); },
```

- [ ] **Step 4: Tests grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1`
Expected: `… bestanden, 0 fehlgeschlagen` (zwei Tests mehr als vorher).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(ego): Timing-Bonus-Regeln, Posen windup/temple/relief, Sounds punch/whoosh

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `EgoStage` – Hand-Varianten, Ring, laufende Kulisse, Trommel, Hinterzimmer; CSS

**Files:**
- Modify: `keller37.html` Block `game-shootout` (Objekt `DuelStage` → `EgoStage`)
- Modify: `keller37.html` CSS (Cutscene-Posen, Bühne)
- Modify: `keller37.html` Block `selftest` (DOM-Test vor `const pseudoAnim = …`)

**Interfaces:**
- Consumes: `CsCast.figureHtml(id, { mood, gun })`, `h`, `qs`, `qsa` (vorhanden); Posen aus Task 1 (CSS hier).
- Produces (zusätzlich zu allem, was `DuelStage` schon hatte – `mount/unmount/resize/toStage/enter/tension/signal/foeBox/gunTip/foeHand/shot/foeDown/foeShoots/flash/setTimeScale/spawn/burst/trace/loop/draw/gunSvg`):
  - `EgoStage.mount(root, { set, weapon, reduced, hand = 'gun' })` – `hand` ∈ `gun | fist | revolver | revolverMuzzle | none`; bei `none` hebt sich keine Hand.
  - `EgoStage.enter(foeId, idx, n, foeName, { gun = true, mood = 'angry' } = {})` – Zähler `#duelCount` nur bei `n > 1`; `gun: false` setzt Klasse `unarmed` (Pistole unsichtbar). `EgoStage.foeGun(on)` schaltet sie später um.
  - `hand(kind)`, `handRise()`, `handDrop()` (Klasse `up`; `revolverMuzzle` trägt zusätzlich Klasse `muzzle`).
  - `ring(ms, goldMs)`, `ringTime() → ms | null` (Bühnen-Uhr, läuft mit dem Zeitfaktor), `ringStop()`; der Ring endet nach `ms` von selbst.
  - `motion(on)` (Root-Klasse `run`, nicht bei reduced), `foeScale(s, ms)` (`--s` per Transition, reduced: `0s`), `foePose(pose)`.
  - `cylinder({ idx, spent }) | null` – Nahaufnahme unten links, Winkel `−60°·idx` weich (reduced: springt); Feld `EgoStage.cyl = { idx, spent, angle }`.
  - `punch(hit)`, `grab()`, `muzzleAt(x, y)`, `selfShot()`, `slideProp(a, b, ms)`.
  - Kulisse `SETS.hinterzimmer` (Kerze, Vordergrund-Tisch im Effekt-Canvas); `const DuelStage = EgoStage`.
  - `loop(now)` bleibt öffentlich: Tests takten die Bühnen-Uhr von Hand (`loop(last + 50)` addiert 50 ms), weil Headless-Chrome mit `virtual-time-budget` kaum rAF-Frames liefert.

- [ ] **Step 1: Fehlschlagenden DOM-Test schreiben**

Im Block `selftest` direkt **vor** der Zeile `  const pseudoAnim = (el, pseudo) => getComputedStyle(el, pseudo).animationName;` einfügen:

```js
  T.test('EgoStage: Hand-Varianten, Ring, laufende Kulisse, Trommel, Faust/Griff/Requisite, Kulisse hinterzimmer, Alias, reduced', async () => {
    const host = h('div', { class: 'duel-stage', style: 'width:600px;height:400px;position:relative' }); document.body.append(host);
    try {
      T.ok(DuelStage === EgoStage, 'DuelStage bleibt Alias von EgoStage');
      EgoStage.mount(host, { set: 'hinterzimmer', weapon: 0, reduced: false, hand: 'none' });
      T.eq([EgoStage.set, EgoStage.handKind, qs('.duel-gun', host).innerHTML, qs('.duel-gun', host).classList.contains('up')], ['hinterzimmer', 'none', '', false], 'hinterzimmer, keine Hand');
      await wait(40); T.ok(!qs('.duel-gun', host).classList.contains('up'), 'hand none: hebt sich auch nach dem ersten Frame nicht');
      EgoStage.enter('igor', 0, 1, 'Igor', { gun: false, mood: 'calm' }); T.eq([qsa('.duel-foe svg.part', host).length, qs('#duelFoeName', host).textContent, qs('#duelCount', host).textContent, qs('.duel-foe', host).classList.contains('unarmed'), !!qs('.duel-foe .mood-calm', host)], [8, 'Igor', '', true, true], 'ein Gegner: kein Zähler; unbewaffnet, ruhig');
      EgoStage.foeGun(true); T.ok(!qs('.duel-foe', host).classList.contains('unarmed'), 'foeGun(true)'); EgoStage.foeGun(false);
      EgoStage.hand('fist'); T.ok(qs('.duel-gun svg', host) && !qs('.duel-gun', host).classList.contains('muzzle'), 'Faust');
      EgoStage.handRise(); T.ok(qs('.duel-gun', host).classList.contains('up'), 'hebt sich');
      EgoStage.hand('revolver'); T.ok(qs('.duel-gun svg circle', host), 'Revolver von hinten (Trommel sichtbar)');
      EgoStage.hand('revolverMuzzle'); T.ok(qs('.duel-gun', host).classList.contains('muzzle'), 'Mündungssicht');
      EgoStage.hand('revolver'); T.ok(!qs('.duel-gun', host).classList.contains('muzzle'), 'zurück: muzzle weg');
      EgoStage.handDrop(); T.ok(!qs('.duel-gun', host).classList.contains('up'), 'senkt sich');
      EgoStage.hand('gun'); T.ok(qs('.duel-gun svg path[fill="#2a2a2e"]', host), 'Pistole Stufe 0');
      /* Ring: läuft auf der Bühnen-Uhr, ringTime() misst seit dem Start, ringStop() beendet */
      T.eq(EgoStage.ringTime(), null, 'kein Ring: null');
      /* Headless (virtual time) liefert kaum rAF-Frames – die Bühnen-Uhr wird hier von Hand getaktet: loop(now) addiert min(50, now − last) ms */
      const tick = (n) => { for (let i = 0; i < n; i++) { EgoStage.last = EgoStage.last || 1000; EgoStage.loop(EgoStage.last + 50); } };
      EgoStage.ring(900, 250); T.eq([EgoStage.ringOn, EgoStage.ringMs, EgoStage.ringGold], [true, 900, 250]); T.eq(EgoStage.ringTime(), 0, 'ringTime ab 0');
      tick(3); T.eq(EgoStage.ringTime(), 150, 'Bühnen-Uhr: 3 × 50 ms');
      EgoStage.ringStop(); T.eq([EgoStage.ringOn, EgoStage.ringTime()], [false, null]);
      EgoStage.ring(30, 10); tick(2); T.eq(EgoStage.ringOn, false, 'Ring läuft nach ms von selbst aus');
      EgoStage.setTimeScale(0.5); EgoStage.ring(900, 250); tick(3); T.eq(EgoStage.ringTime(), 75, 'Zeitlupe bremst auch den Ring'); EgoStage.setTimeScale(1); EgoStage.ringStop();
      /* laufende Kulisse + Figurengröße */
      EgoStage.motion(true); T.ok(EgoStage.moving && host.classList.contains('run'), 'run-Klasse');
      EgoStage.foeScale(0.5, 0); T.eq(qs('.duel-foe', host).style.getPropertyValue('--s'), '0.5');
      EgoStage.motion(false); T.ok(!EgoStage.moving && !host.classList.contains('run'));
      /* Trommel-Nahaufnahme */
      EgoStage.cylinder({ idx: 2, spent: [0, 1] }); T.eq([EgoStage.cyl.idx, EgoStage.cyl.spent], [2, [0, 1]]);
      tick(30); T.ok(Math.abs(EgoStage.cyl.angle + 120) < 1, `Trommel dreht weich auf −120° (angle=${EgoStage.cyl.angle})`);
      EgoStage.cylinder(null); T.eq(EgoStage.cyl, null, 'ausgeblendet');
      /* Faustkampf, Kragengriff, Requisite, eigener Kopfschuss, Mündungsfeuer */
      EgoStage.hand('fist'); EgoStage.parts = [];
      EgoStage.punch(true); T.ok(EgoStage.parts.some((p) => p.kind === 'blood') && qs('.duel-gun', host).classList.contains('recoil'), 'Treffer: Blut + Faust ruckt');
      EgoStage.parts = []; EgoStage.punch(false); T.ok(EgoStage.parts.some((p) => p.kind === 'fist') && EgoStage.redUntil > EgoStage.t && EgoStage.shakeUntil > EgoStage.t, 'daneben: seine Faust auf die Kamera, roter Rand, Ruck');
      EgoStage.redUntil = 0; EgoStage.grab(); T.ok(host.classList.contains('jerk') && EgoStage.redUntil > EgoStage.t, 'Kragengriff: jerk + roter Rand');
      EgoStage.parts = []; EgoStage.slideProp({ x: 0, y: 0 }, { x: 100, y: 100 }, 300); T.ok(EgoStage.parts.some((p) => p.kind === 'prop'), 'Requisite gleitet');
      EgoStage.parts = []; EgoStage.selfShot(); T.ok(EgoStage.flashUntil > EgoStage.t && EgoStage.parts.some((p) => p.kind === 'drop'), 'Kopfschuss: Blitz + Tropfen');
      EgoStage.parts = []; EgoStage.muzzleAt(10, 10); T.ok(EgoStage.parts.some((p) => p.kind === 'muzzle'), 'Mündungsfeuer an Position');
      EgoStage.unmount(); T.eq([EgoStage.mounted, host.children.length, host.classList.contains('run')], [false, 0, false]);
      /* reduced motion: keine run-Klasse, kein jerk, kein Blitz, Trommel springt, Figurengröße ohne Transition */
      EgoStage.mount(host, { set: 'gasse', weapon: 0, reduced: true, hand: 'fist' }); EgoStage.enter('raeuber', 0, 1, 'X');
      EgoStage.motion(true); T.ok(EgoStage.moving && !host.classList.contains('run'), 'reduced: Kulisse steht');
      EgoStage.grab(); T.ok(!host.classList.contains('jerk') && EgoStage.shakeUntil === 0, 'reduced: kein Ruck');
      EgoStage.selfShot(); T.eq(EgoStage.flashUntil, 0, 'reduced: kein Blitz');
      EgoStage.foeScale(0.5, 900); T.eq(qs('.duel-foe', host).style.transitionDuration, '0s', 'reduced: springt');
      EgoStage.cylinder({ idx: 3, spent: [] }); EgoStage.loop(5000); T.eq(EgoStage.cyl.angle, -180, 'reduced: Trommel springt');
    } finally { EgoStage.unmount(); host.remove(); }
  });
```

- [ ] **Step 2: Test laufen lassen – er muss fehlschlagen**

Run: `tests/dom-selftest.sh`
Expected: `failed=1` (`EgoStage is not defined`). Fehlermeldungen liefert: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --virtual-time-budget=60000 --enable-logging=stderr --v=0 --dump-dom "file://$PWD/keller37.html?selftest&fresh" 2>&1 >/dev/null | grep -o "\[selftest\] FAIL .*" | grep -v "FAIL', f" | cut -c1-600`.

- [ ] **Step 3: `DuelStage` durch `EgoStage` ersetzen**

Im Block `game-shootout` alles von der Zeile `/* ================= DUEL STAGE – Ego-Sicht: …` bis **vor** die Zeile `/* ================= SCHIESSEREI „ZIEH!“ – Reaktionsduell, ein Gegner nach dem anderen ================= */` (also das komplette Objekt `DuelStage` inklusive schließendem `};`) durch Folgendes ersetzen (endet mit dem Alias):

```js
/* ================= EGO STAGE – Ego-Sicht: Welt-Canvas, Gegnerfigur aus dem Cutscene-Rig, Effekt-Canvas, eigene Hand =================
   Rein darstellend: trifft keine Spielentscheidung. Nutzer: Shootout (Duell), MugAction (Überfall), Russian (Roulette).
   Hand-Varianten (gun/fist/revolver/revolverMuzzle/none), Timing-Ring, laufende Kulisse, Trommel-Nahaufnahme. */
const EgoStage = {
  root: null, world: null, fx: null, back: null, fig: null, gun: null, tag: null, flashEl: null,
  W: 0, H: 0, dpr: 1, raf: 0, last: 0, t: 0, timeScale: 1, slowUntil: 0, flashUntil: 0, redUntil: 0, shakeUntil: 0, tenseFrom: 0, lamp: 1,
  parts: [], stains: [], set: 'gasse', reduced: false, ro: null, mounted: false, riseRaf: 0, flashTimer: null, downTimer: null,
  handKind: 'gun', weapon: 0, ringOn: false, ringStart: 0, ringMs: 0, ringGold: 0, moving: false, runT: 0, cyl: null,
  /* Kulissen: Farben + welche Silhouetten/Ambient-Elemente gezeichnet werden */
  SETS: {
    gasse: { sky: ['#05070d', '#1a1e2a'], wall: '#23232b', ground: '#1c1a16', rain: true, lamp: true, bins: true },
    bahnhof: { sky: ['#05070d', '#1a2233'], wall: '#1b2130', ground: '#2a2820', rain: false, lamp: true, rails: true },
    keller: { sky: ['#1a1914', '#050503'], wall: '#1e1c16', ground: '#171410', rain: false, lamp: true, table: true },
    hinterzimmer: { sky: ['#2a1a08', '#0a0603'], wall: '#1e1207', ground: '#150e06', rain: false, lamp: false, candle: true, fgTable: true },
  },
  SET_BY_KIND: { tutorial: 'bahnhof', hinterhalt: 'gasse', finale: 'keller', dev: 'gasse' },
  MAX_PARTS: 160,
  /* Waffe des Spielers: Stufe 0 = geliehene Pistole (Story: Anabis Makarov), 3 = „Die Goldene" */
  WEAPON_COLORS: [['#2a2a2e', '#4a4a50'], ['#2a2a2e', '#4a4a50'], ['#1e2226', '#3a4048'], ['#8a6a1a', '#d4af37']],
  mount(root, { set = 'gasse', weapon = 0, reduced = false, hand = 'gun' } = {}) {
    this.unmount();
    this.root = root; this.set = this.SETS[set] ? set : 'gasse'; this.reduced = reduced; this.weapon = weapon; this.handKind = hand;
    this.dpr = Math.min(2, window.devicePixelRatio || 1);
    this.world = h('canvas', { class: 'duel-world' }); this.fx = h('canvas', { class: 'duel-fx' });
    this.fig = h('div', { class: 'cs-fig duel-foe' });
    this.gun = h('div', { class: 'duel-gun', html: this.handSvg(hand, weapon) });
    this.tag = h('div', { class: 'duel-tag' }, h('span', { id: 'duelFoeName' }), h('span', { id: 'duelCount' }));
    this.flashEl = h('div', { class: 'duel-flash' });
    root.append(this.world, this.fig, this.fx, this.gun, this.tag, this.flashEl);
    this.parts = []; this.stains = []; this.timeScale = 1; this.slowUntil = this.flashUntil = this.redUntil = this.shakeUntil = this.tenseFrom = 0; this.t = 0; this.last = 0;
    this.ringOn = false; this.moving = false; this.runT = 0; this.cyl = null;
    this.mounted = true;
    this.resize();
    if (typeof ResizeObserver !== 'undefined') { this.ro = new ResizeObserver(() => this.resize()); this.ro.observe(root); }
    this.raf = requestAnimationFrame((now) => this.loop(now));
    if (hand !== 'none') this.riseRaf = requestAnimationFrame(() => { this.riseRaf = 0; if (this.mounted) this.gun.classList.add('up'); }); // Hand hebt sich im nächsten Frame (Transition ab translateY(100%))
  },
  /* Hand unten rechts wechseln: gun (Duell), fist (Überfall), revolver / revolverMuzzle (Roulette), none */
  hand(kind) {
    if (!this.mounted) return;
    this.handKind = kind;
    this.gun.innerHTML = this.handSvg(kind, this.weapon);
    this.gun.classList.toggle('muzzle', kind === 'revolverMuzzle');
    if (kind === 'none') this.gun.classList.remove('up');
  },
  handRise() { if (this.mounted) this.gun.classList.add('up'); },
  handDrop() { if (this.mounted) this.gun.classList.remove('up'); },
  /* Timing-Ring um die Figur: schrumpft über ms, die letzten goldMs sind gold; ringTime() = Bühnen-ms seit Start (null wenn kein Ring läuft) */
  ring(ms, goldMs) { if (!this.mounted) return; this.ringOn = true; this.ringStart = this.t; this.ringMs = ms; this.ringGold = goldMs; },
  ringTime() { return this.ringOn ? this.t - this.ringStart : null; },
  ringStop() { this.ringOn = false; },
  /* laufende Kulisse (Flucht): Bodenlinien und Wandkanten ziehen zum Betrachter, Laufwackeln per CSS-Klasse */
  motion(on) { if (!this.mounted) return; this.moving = !!on; this.root.classList.toggle('run', this.moving && !this.reduced); },
  /* Figurengröße per Transition (Aufholen / Zurückfallen) */
  foeScale(s, ms) { if (!this.mounted) return; this.fig.style.transitionDuration = this.reduced ? '0s' : `${ms}ms`; this.fig.style.setProperty('--s', String(s)); },
  foePose(pose) { if (this.mounted) this.fig.dataset.pose = pose; },
  /* Trommel-Nahaufnahme unten links: idx = aktuelle Kammer (dreht um 60° je Kammer), spent = leere Kammern; null blendet aus */
  cylinder(state) { this.cyl = state ? { idx: state.idx, spent: state.spent || [], angle: this.cyl ? this.cyl.angle : 0 } : null; },
  /* Faustkampf: Treffer = Einschlag beim Gegner; daneben = seine Faust auf die Kamera (wachsender Kreis), Ruck, roter Rand */
  punch(hit) {
    if (!this.mounted) return;
    if (this.handKind === 'fist') { this.gun.classList.remove('recoil'); void this.gun.offsetWidth; this.gun.classList.add('recoil'); }
    const b = this.foeBox();
    if (hit) { const p = { x: b.left + b.width * 0.5, y: b.top + b.height * 0.3 }; this.burst(p.x, p.y, 'spark', 8); this.burst(p.x, p.y, 'blood', 16); }
    else { const p = { x: b.left + b.width * 0.5, y: b.top + b.height * 0.4 }; this.spawn({ x: p.x, y: p.y, x2: this.W * 0.55, y2: this.H * 0.55, vx: 0, vy: 0, g: 0, ttl: 260, size: 18, color: '#e8b48a', kind: 'fist' }); this.redUntil = this.t + 1200; if (!this.reduced) this.shakeUntil = this.t + 350; }
  },
  /* Griff am Kragen (Flucht erwischt): Bild reißt nach hinten, roter Rand */
  grab() {
    if (!this.mounted) return;
    this.redUntil = this.t + 1200;
    if (!this.reduced) { this.shakeUntil = this.t + 400; this.root.classList.remove('jerk'); void this.root.offsetWidth; this.root.classList.add('jerk'); }
  },
  muzzleAt(x, y) { if (this.mounted) this.burst(x, y, 'muzzle', 12); },
  /* eigener Kopfschuss (Roulette): Blitz, Ruck, roter Rand, Tropfen */
  selfShot() { if (!this.mounted) return; if (!this.reduced) this.flashUntil = this.t + 110; this.foeShoots(); },
  /* Requisite (Revolver) gleitet über den Tisch von a nach b */
  slideProp(a, b, ms) { if (this.mounted) this.spawn({ x: a.x, y: a.y, x2: b.x, y2: b.y, vx: 0, vy: 0, g: 0, ttl: ms, size: 14, color: '#2a2a2e', kind: 'prop' }); },
  unmount() {
    if (!this.mounted) return;
    cancelAnimationFrame(this.raf); this.raf = 0; cancelAnimationFrame(this.riseRaf); this.riseRaf = 0;
    clearTimeout(this.flashTimer); clearTimeout(this.downTimer);
    if (this.ro) { this.ro.disconnect(); this.ro = null; }
    for (const el of [this.world, this.fx, this.fig, this.gun, this.tag, this.flashEl]) if (el) el.remove();
    this.root.classList.remove('run', 'jerk');
    this.root = this.world = this.fx = this.back = this.fig = this.gun = this.tag = this.flashEl = null;
    this.parts = []; this.stains = []; this.mounted = false;
  },
  resize() {
    if (!this.mounted) return;
    const w = this.root.clientWidth, h = this.root.clientHeight;
    if (w === this.W && h === this.H && this.back) return; // unveränderte Größe: nicht neu vorrendern
    this.W = w; this.H = h;
    for (const c of [this.world, this.fx]) { c.width = Math.round(this.W * this.dpr); c.height = Math.round(this.H * this.dpr); }
    this.back = document.createElement('canvas'); this.back.width = this.world.width; this.back.height = this.world.height;
    this.drawBackdrop(this.back.getContext('2d'));
    this.draw();
  },
  /* Viewport-Koordinaten → Bühnenpixel: die Seite zoomt .body auf großen Bildschirmen (zoom 1.15–1.65), Rechtecke kommen dann gezoomt zurück */
  toStage(clientX, clientY) {
    const R = this.root.getBoundingClientRect(), z = R.width / this.W || 1;
    return { x: (clientX - R.left) / z, y: (clientY - R.top) / z };
  },
  /* Kulisse einmal vorrendern: Himmel, Wand-Silhouetten, Boden mit Fluchtpunkt */
  drawBackdrop(ctx) {
    const S = this.SETS[this.set], W = this.W, H = this.H, hz = H * 0.58;
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    const sky = ctx.createLinearGradient(0, 0, 0, hz); sky.addColorStop(0, S.sky[0]); sky.addColorStop(1, S.sky[1]);
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, hz);
    ctx.fillStyle = S.ground; ctx.fillRect(0, hz, W, H - hz);
    ctx.strokeStyle = 'rgba(255,255,255,.06)'; ctx.lineWidth = 1;
    for (let i = -6; i <= 6; i++) { ctx.beginPath(); ctx.moveTo(W / 2 + i * W * 0.06, hz); ctx.lineTo(W / 2 + i * W * 0.5, H); ctx.stroke(); }
    for (let k = 1; k <= 5; k++) { const y = hz + (H - hz) * (k * k) / 25; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    ctx.fillStyle = S.wall;
    ctx.fillRect(0, hz * 0.25, W * 0.16, hz * 0.75); ctx.fillRect(W * 0.84, hz * 0.18, W * 0.16, hz * 0.82);
    ctx.fillRect(W * 0.16, hz * 0.45, W * 0.1, hz * 0.55); ctx.fillRect(W * 0.74, hz * 0.4, W * 0.1, hz * 0.6);
    if (S.bins) { ctx.fillStyle = '#2f2f36'; ctx.fillRect(W * 0.05, hz - 40, 34, 44); ctx.fillRect(W * 0.1, hz - 32, 30, 36); }
    if (S.rails) { ctx.strokeStyle = 'rgba(200,200,220,.18)'; ctx.lineWidth = 3; for (const dx of [-0.12, 0.12]) { ctx.beginPath(); ctx.moveTo(W * (0.5 + dx * 0.4), hz); ctx.lineTo(W * (0.5 + dx * 4), H); ctx.stroke(); } }
    if (S.table) { ctx.fillStyle = '#3a2410'; ctx.fillRect(W * 0.3, hz - 6, W * 0.4, 8); ctx.fillRect(W * 0.32, hz, 6, H * 0.12); ctx.fillRect(W * 0.66, hz, 6, H * 0.12); }
    if (S.candle) { ctx.fillStyle = '#e8e0c0'; ctx.fillRect(W * 0.78, hz * 0.62, 8, 26); ctx.fillStyle = '#ffb347'; ctx.beginPath(); ctx.ellipse(W * 0.78 + 4, hz * 0.6, 5, 10, 0, 0, Math.PI * 2); ctx.fill(); const g = ctx.createRadialGradient(W * 0.78, hz * 0.6, 0, W * 0.78, hz * 0.6, H * 0.35); g.addColorStop(0, 'rgba(255,180,80,.25)'); g.addColorStop(1, 'rgba(255,180,80,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
    if (S.lamp) { ctx.fillStyle = '#555'; ctx.fillRect(W * 0.5 - 2, 0, 4, hz * 0.22); ctx.fillStyle = '#8a8a70'; ctx.fillRect(W * 0.5 - 26, hz * 0.22, 52, 10); }
    const vig = ctx.createRadialGradient(W / 2, H * 0.5, H * 0.3, W / 2, H * 0.5, H); vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, 'rgba(0,0,0,.75)');
    ctx.fillStyle = vig; ctx.fillRect(0, 0, W, H);
  },
  /* Gegner tritt aus dem Dunkel auf: Figur klein setzen, dann per Transition auf volle Größe */
  enter(foeId, idx, n, foeName, { gun = true, mood = 'angry' } = {}) {
    if (!this.mounted) return;
    this.fig.innerHTML = CsCast.figureHtml(foeId, { mood, gun: true });
    this.fig.classList.toggle('unarmed', !gun);
    this.fig.dataset.pose = 'idle'; this.fig.style.setProperty('--fall', '');
    this.fig.style.transition = 'none'; this.fig.style.setProperty('--s', '0.4');
    void this.fig.offsetWidth; // Startgröße ohne Transition festschreiben
    this.fig.style.transition = ''; this.fig.style.setProperty('--s', '1');
    qs('#duelFoeName', this.tag).textContent = foeName; qs('#duelCount', this.tag).textContent = n > 1 ? `${idx + 1} / ${n}` : '';
  },
  /* Pistole in der Hand des Gegners ein-/ausblenden (Roulette: Igor hält den Revolver nur in seinem Zug) */
  foeGun(on) { if (this.mounted) this.fig.classList.toggle('unarmed', !on); },
  /* Anspannung: der Rand dunkelt über ~4 s langsam ab, bis das Signal kommt */
  tension(on) { if (this.mounted) this.tenseFrom = on ? this.t || 1 : 0; },
  /* Signal: Arm hoch, Blitz */
  signal() { if (!this.mounted) return; this.fig.dataset.pose = 'draw'; if (!this.reduced) this.flashUntil = this.t + 110; },
  /* Rechteck der Figur in Bühnenkoordinaten (für die Trefferprüfung) */
  foeBox() {
    if (!this.mounted) return { left: 0, top: 0, width: 0, height: 0 };
    const r = this.fig.getBoundingClientRect(), a = this.toStage(r.left, r.top), b = this.toStage(r.right, r.bottom);
    return { left: a.x, top: a.y, width: b.x - a.x, height: b.y - a.y };
  },
  gunTip() {
    const r = this.gun.getBoundingClientRect(), a = this.toStage(r.left, r.top), b = this.toStage(r.right, r.bottom);
    return { x: a.x + (b.x - a.x) * 0.3, y: a.y + (b.y - a.y) * 0.12 };
  },
  foeHand() { const b = this.foeBox(); return { x: b.left + b.width * 0.9, y: b.top + b.height * 0.42 }; },
  /* Eigener Schuss: Rückstoß, Mündungsfeuer, Hülse, Spur – Treffer: Blut am Gegner; daneben: Funken am Tippunkt; Fehlschuss (kein Punkt): in den Boden */
  shot({ x = null, y = null, hit = false, early = false } = {}) {
    if (!this.mounted) return;
    this.gun.classList.remove('recoil'); void this.gun.offsetWidth; this.gun.classList.add('recoil');
    const tip = this.gunTip();
    this.burst(tip.x, tip.y, 'muzzle', 10);
    this.spawn({ x: tip.x + 10, y: tip.y + 10, vx: 60 + Math.random() * 60, vy: -160, g: 500, ttl: 700, size: 3, color: '#d4af37', kind: 'shell' });
    if (early) { const b = this.foeBox(); this.trace(tip, { x: b.left + b.width / 2, y: this.H * 0.95 }); this.burst(b.left + b.width / 2, this.H * 0.95, 'dust', 10); return; }
    if (hit) { const b = this.foeBox(); const p = { x: b.left + b.width * 0.5, y: b.top + b.height * 0.42 }; this.trace(tip, p); this.burst(p.x, p.y, 'blood', 22); }
    else if (x != null) { this.trace(tip, { x, y }); this.burst(x, y, 'spark', 12); }
  },
  /* Gegner fällt: Zucken, dann Fall in Zeitlupe, Staub und Fleck am Boden */
  foeDown() {
    if (!this.mounted) return;
    this.fig.dataset.pose = 'hit';
    const b = this.foeBox();
    this.downTimer = setTimeout(() => { if (this.mounted) { this.fig.dataset.pose = 'down'; this.burst(b.left + b.width / 2, b.top + b.height, 'dust', 16); this.stains.push({ x: b.left + b.width * 0.6, y: b.top + b.height - 4, r: b.width * 0.35 }); } }, 220);
    if (!this.reduced) { this.timeScale = 0.3; this.slowUntil = this.t + 150; this.fig.style.setProperty('--fall', '1.2s'); } // Zeitlupe (Bühnen-Uhr): Partikel langsamer, Fall länger
  },
  /* Gegner schießt: sein Mündungsfeuer, Ruck, roter Rand, Tropfen über die Kamera */
  foeShoots() {
    if (!this.mounted) return;
    const hp = this.foeHand();
    this.burst(hp.x, hp.y, 'muzzle', 12);
    this.redUntil = this.t + 1400;
    if (!this.reduced) { this.shakeUntil = this.t + 350; for (let i = 0; i < 7; i++) this.spawn({ x: this.W * (0.3 + Math.random() * 0.4), y: this.H * (0.1 + Math.random() * 0.3), vx: 0, vy: 40 + Math.random() * 60, g: 30, ttl: 1400, size: 5 + Math.random() * 5, color: '#8a0f1a', kind: 'drop' }); }
  },
  flash(text, ms = 700) {
    if (!this.mounted) return;
    this.flashEl.textContent = text; this.flashEl.classList.remove('on'); void this.flashEl.offsetWidth; this.flashEl.classList.add('on');
    clearTimeout(this.flashTimer); this.flashTimer = setTimeout(() => { if (this.flashEl) this.flashEl.classList.remove('on'); }, ms);
  },
  setTimeScale(k) { this.timeScale = k; },
  spawn(p) { if (this.parts.length >= this.MAX_PARTS) this.parts.shift(); p.age = 0; this.parts.push(p); },
  burst(x, y, kind, n) {
    if (this.reduced && (kind === 'spark' || kind === 'dust')) n = Math.min(n, 4);
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2, sp = kind === 'muzzle' ? 40 + Math.random() * 120 : kind === 'blood' ? 60 + Math.random() * 220 : kind === 'spark' ? 80 + Math.random() * 200 : 20 + Math.random() * 60;
      this.spawn({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - (kind === 'dust' ? 20 : 0), g: kind === 'muzzle' ? 0 : kind === 'dust' ? -10 : 600,
        ttl: kind === 'muzzle' ? 90 : kind === 'dust' ? 900 : 500, size: kind === 'muzzle' ? 6 + Math.random() * 10 : kind === 'blood' ? 2 + Math.random() * 4 : 2, kind,
        color: kind === 'muzzle' ? '#ffd27a' : kind === 'blood' ? '#a3121e' : kind === 'spark' ? '#ffe7a0' : 'rgba(180,170,150,.5)' });
      if (this.reduced && kind !== 'muzzle') { const p = this.parts[this.parts.length - 1]; p.vx = p.vy = 0; p.g = 0; p.ttl = 150; }
    }
  },
  trace(a, b) { this.spawn({ x: a.x, y: a.y, x2: b.x, y2: b.y, vx: 0, vy: 0, g: 0, ttl: 70, size: 2, color: 'rgba(255,240,200,.85)', kind: 'trace' }); },
  loop(now) {
    if (!this.mounted) return;
    const raw = this.last ? Math.min(50, now - this.last) : 16; this.last = now;
    const dt = raw * this.timeScale; this.t += dt;
    if (this.slowUntil && this.t >= this.slowUntil) { this.slowUntil = 0; this.timeScale = 1; }
    if (this.ringOn && this.t - this.ringStart > this.ringMs) this.ringOn = false;
    if (this.moving) this.runT += dt;
    if (this.cyl) { const target = -60 * this.cyl.idx; const d = target - this.cyl.angle; this.cyl.angle += this.reduced ? d : d * Math.min(1, dt / 120); }
    for (const p of this.parts) { p.age += dt; const s = dt / 1000; p.vy += (p.g || 0) * s; p.x += p.vx * s; p.y += p.vy * s; }
    this.parts = this.parts.filter((p) => p.age < p.ttl);
    if (!this.reduced) { this.lamp = 0.85 + Math.random() * 0.15; if (Math.random() < 0.04) this.lamp = 0.4; if (this.parts.length < 60 && Math.random() < 0.3) this.spawn({ x: Math.random() * this.W, y: this.H * 0.2 + Math.random() * this.H * 0.5, vx: 8 + Math.random() * 10, vy: -4 + Math.random() * 8, g: 0, ttl: 4000, size: 1.5, color: 'rgba(220,210,180,.35)', kind: 'dust' }); }
    this.draw();
    this.raf = requestAnimationFrame((n) => this.loop(n));
  },
  draw() {
    if (!this.mounted || !this.W || !this.H) return;
    const W = this.W, H = this.H, S = this.SETS[this.set];
    const wc = this.world.getContext('2d'), fc = this.fx.getContext('2d');
    wc.setTransform(1, 0, 0, 1, 0, 0); wc.drawImage(this.back, 0, 0);
    wc.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    if (S.lamp) { const g = wc.createRadialGradient(W / 2, H * 0.14, 0, W / 2, H * 0.14, H * 0.5); g.addColorStop(0, `rgba(255,240,200,${0.22 * this.lamp})`); g.addColorStop(1, 'rgba(255,240,200,0)'); wc.fillStyle = g; wc.fillRect(0, 0, W, H); }
    if (S.rain && !this.reduced) { wc.strokeStyle = 'rgba(160,180,200,.25)'; wc.lineWidth = 1; const off = (this.t * 0.6) % 40; for (let i = 0; i < 24; i++) { const x = (i * 97) % W, y = ((i * 53) + off * 4) % H; wc.beginPath(); wc.moveTo(x, y); wc.lineTo(x - 4, y + 18); wc.stroke(); } }
    if (this.moving) { const hz = H * 0.58, ph = (this.runT / 700) % 1; wc.strokeStyle = 'rgba(255,255,255,.14)'; wc.lineWidth = 2; for (let k = 0; k < 6; k++) { const f = ((k + ph) / 6); const y = hz + (H - hz) * f * f; wc.beginPath(); wc.moveTo(0, y); wc.lineTo(W, y); wc.stroke(); } for (const side of [-1, 1]) for (let k = 0; k < 4; k++) { const f = (k + ph) / 4; const x = W / 2 + side * (W * 0.08 + W * 0.45 * f); wc.beginPath(); wc.moveTo(x, hz * (1 - f * 0.6)); wc.lineTo(x, hz); wc.stroke(); } }
    if (this.moving && this.ringOn) { const k = Math.min(1, (this.t - this.ringStart) / this.ringMs), x = W * (0.72 + 0.2 * k), y = H * 0.6, s = 30 + 70 * k; wc.fillStyle = '#2f2f36'; wc.fillRect(x, y - s, s * 0.7, s); wc.fillRect(x - 4, y - s - 6, s * 0.7 + 8, 8); } // Abzweigung: die Mülltonne rechts kommt näher
    for (const st of this.stains) { wc.fillStyle = 'rgba(90,8,14,.85)'; wc.beginPath(); wc.ellipse(st.x, st.y, st.r, st.r * 0.28, 0, 0, Math.PI * 2); wc.fill(); }
    for (const p of this.parts) if (p.kind === 'dust') { wc.fillStyle = p.color; wc.globalAlpha = 1 - p.age / p.ttl; wc.fillRect(p.x, p.y, p.size, p.size); }
    wc.globalAlpha = 1;
    fc.setTransform(this.dpr, 0, 0, this.dpr, 0, 0); fc.clearRect(0, 0, W, H);
    const shake = this.shakeUntil > this.t ? (Math.random() - 0.5) * 12 : 0;
    if (shake) fc.translate(shake, (Math.random() - 0.5) * 12);
    if (S.fgTable) { fc.fillStyle = '#4a2e12'; fc.beginPath(); fc.moveTo(-W * 0.1, H * 0.66); fc.lineTo(W * 1.1, H * 0.66); fc.lineTo(W * 1.3, H); fc.lineTo(-W * 0.3, H); fc.closePath(); fc.fill(); fc.fillStyle = '#5a3a1a'; fc.fillRect(-W * 0.1, H * 0.66, W * 1.2, 6); fc.fillStyle = '#3a3a40'; fc.beginPath(); fc.ellipse(W * 0.5, H * 0.75, 22, 7, 0, 0, Math.PI * 2); fc.fill(); fc.fillStyle = '#e8e0c0'; fc.fillRect(W * 0.5 - 2, H * 0.75 - 9, 18, 3); fc.fillStyle = '#ff7a30'; fc.fillRect(W * 0.5 + 16, H * 0.75 - 9, 3, 3); } // Tisch vor der Figur (Igor „sitzt“ dahinter), Aschenbecher mit Kippe
    if (this.ringOn) { const b = this.foeBox(), el = this.t - this.ringStart, k = Math.min(1, el / this.ringMs), gold = el >= this.ringMs - this.ringGold; const cx = b.left + b.width / 2, cy = b.top + b.height * 0.45, r0 = b.width * 0.9 + 40, r1 = b.width * 0.55; fc.strokeStyle = gold ? '#ffd166' : 'rgba(255,255,255,.75)'; fc.lineWidth = gold ? 6 : 3; if (this.reduced) { const bw = b.width * 1.6, bx = cx - bw / 2, by = b.top + b.height + 18; fc.fillStyle = 'rgba(255,255,255,.25)'; fc.fillRect(bx, by, bw, 8); fc.fillStyle = 'rgba(255,209,102,.7)'; fc.fillRect(bx + bw * (1 - this.ringGold / this.ringMs), by, bw * this.ringGold / this.ringMs, 8); fc.fillStyle = '#fff'; fc.fillRect(bx + bw * k - 2, by - 4, 4, 16); } else { fc.beginPath(); fc.arc(cx, cy, r0 + (r1 - r0) * k, 0, Math.PI * 2); fc.stroke(); } }
    if (this.cyl) { const r = W * (W < 760 ? 0.15 : 0.11), cx = r + 16, cy = H - r - 16; fc.save(); fc.translate(cx, cy); fc.rotate(this.cyl.angle * Math.PI / 180); fc.fillStyle = '#2a2f36'; fc.strokeStyle = '#8a94a0'; fc.lineWidth = 3; fc.beginPath(); fc.arc(0, 0, r, 0, Math.PI * 2); fc.fill(); fc.stroke(); for (let i = 0; i < 6; i++) { const a = (-90 + i * 60) * Math.PI / 180; fc.fillStyle = this.cyl.spent.includes(i) ? '#3a3f46' : '#0b0d10'; fc.beginPath(); fc.arc(r * 0.6 * Math.cos(a), r * 0.6 * Math.sin(a), r * 0.2, 0, Math.PI * 2); fc.fill(); fc.stroke(); } fc.fillStyle = '#8a94a0'; fc.beginPath(); fc.arc(0, 0, r * 0.14, 0, Math.PI * 2); fc.fill(); fc.restore(); fc.fillStyle = '#ffd166'; fc.beginPath(); fc.moveTo(cx - 7, cy - r - 12); fc.lineTo(cx + 7, cy - r - 12); fc.lineTo(cx, cy - r - 2); fc.closePath(); fc.fill(); }
    for (const p of this.parts) {
      if (p.kind === 'dust') continue;
      const k = 1 - p.age / p.ttl;
      if (p.kind === 'trace') { fc.strokeStyle = p.color; fc.globalAlpha = k; fc.lineWidth = p.size; fc.beginPath(); fc.moveTo(p.x, p.y); fc.lineTo(p.x2, p.y2); fc.stroke(); continue; }
      if (p.kind === 'fist' || p.kind === 'prop') { const f = p.age / p.ttl, x = p.x + (p.x2 - p.x) * f, y = p.y + (p.y2 - p.y) * f; fc.globalAlpha = p.kind === 'fist' ? 1 : 0.95; fc.fillStyle = p.color; if (p.kind === 'fist') { fc.beginPath(); fc.arc(x, y, p.size * (1 + f * 9), 0, Math.PI * 2); fc.fill(); } else { fc.fillRect(x - p.size, y - p.size * 0.35, p.size * 2, p.size * 0.7); fc.fillRect(x + p.size * 0.4, y, p.size * 0.6, p.size); } continue; } // Faust wächst auf die Kamera zu; Requisite gleitet
      fc.globalAlpha = p.kind === 'muzzle' ? k : Math.min(1, k * 1.5);
      fc.fillStyle = p.color;
      if (p.kind === 'drop') { fc.beginPath(); fc.ellipse(p.x, p.y, p.size * 0.55, p.size * (1.2 + p.age / p.ttl * 2), 0, 0, Math.PI * 2); fc.fill(); continue; } // Tropfen laufen als Streifen nach unten
      fc.beginPath(); fc.arc(p.x, p.y, p.size, 0, Math.PI * 2); fc.fill();
    }
    fc.globalAlpha = 1;
    if (this.tenseFrom) { const a = Math.min(0.4, (this.t - this.tenseFrom) / 4000 * 0.4); const g = fc.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.85); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`); fc.fillStyle = g; fc.fillRect(0, 0, W, H); }
    if (this.flashUntil > this.t) { fc.fillStyle = `rgba(255,255,255,${0.9 * (this.flashUntil - this.t) / 110})`; fc.fillRect(-20, -20, W + 40, H + 40); }
    if (this.redUntil > this.t) { const a = Math.min(0.75, (this.redUntil - this.t) / 1400); const g = fc.createRadialGradient(W / 2, H / 2, H * 0.25, W / 2, H / 2, H * 0.8); g.addColorStop(0, 'rgba(120,0,10,0)'); g.addColorStop(1, `rgba(120,0,10,${a})`); fc.fillStyle = g; fc.fillRect(-20, -20, W + 40, H + 40); }
    if (this.timeScale < 1) { const g = fc.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.9); g.addColorStop(0, 'rgba(40,60,120,0)'); g.addColorStop(1, 'rgba(40,60,120,.45)'); fc.fillStyle = g; fc.fillRect(0, 0, W, H); }
    fc.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
  },
  /* Hand-Varianten unten rechts: gun = Pistole (Duell), fist = Faust, revolver = Revolver von hinten, revolverMuzzle = Mündung auf die Kamera */
  handSvg(kind, tier) {
    if (kind === 'none') return '';
    if (kind === 'fist') return `<svg viewBox="0 0 200 160" preserveAspectRatio="xMaxYMax meet"><path d="M60 70 Q58 40 90 36 L138 36 Q160 40 156 70 L152 120 Q150 160 110 160 L64 160 Q52 150 54 120 Z" fill="#e8b48a"/><path d="M66 74 h84 M66 92 h84 M66 110 h84" stroke="#d9a67c" stroke-width="4"/><path d="M52 96 Q36 100 44 130 Q54 148 68 136 Z" fill="#d9a67c"/></svg>`;
    if (kind === 'revolver') return `<svg viewBox="0 0 200 160" preserveAspectRatio="xMaxYMax meet"><path d="M60 92 L126 14 L142 26 L84 100 Z" fill="#2a2a2e"/><circle cx="96" cy="86" r="22" fill="#3a3f46" stroke="#8a94a0" stroke-width="3"/><circle cx="96" cy="86" r="6" fill="#8a94a0"/><path d="M78 104 L100 112 L110 160 L76 160 Z" fill="#2a2a2e"/><path d="M54 110 Q44 150 62 160 L118 160 Q124 132 106 114 Q88 102 68 106 Z" fill="#e8b48a"/><path d="M64 106 Q50 98 54 118 Q62 126 80 120 Z" fill="#d9a67c"/></svg>`;
    if (kind === 'revolverMuzzle') return `<svg viewBox="0 0 200 160" preserveAspectRatio="xMaxYMax meet"><circle cx="112" cy="70" r="58" fill="#3a3f46" stroke="#8a94a0" stroke-width="4"/><circle cx="112" cy="70" r="30" fill="#0b0d10" stroke="#555" stroke-width="3"/><circle cx="112" cy="70" r="12" fill="#000"/><path d="M96 128 L128 128 L136 160 L88 160 Z" fill="#2a2a2e"/><path d="M60 136 Q52 152 66 160 L150 160 Q156 140 132 132 Q112 126 84 130 Z" fill="#e8b48a"/><rect x="150" y="30" width="10" height="26" rx="3" fill="#8a94a0"/></svg>`;
    return this.gunSvg(tier);
  },
  /* Hand mit Pistole von hinten, unten rechts – Farben nach Waffenstufe */
  gunSvg(tier) {
    const [dark, light] = this.WEAPON_COLORS[Math.max(0, Math.min(3, tier | 0))];
    /* Schlitten und Lauf zeigen zum Fluchtpunkt (oben links), Griff in der Faust, Daumen außen */
    return `<svg viewBox="0 0 200 160" preserveAspectRatio="xMaxYMax meet">
      <path d="M56 89 L117 11 L136 25 L75 103 Z" fill="${dark}"/>
      <path d="M62 86 L116 17 L126 24 L72 93 Z" fill="${light}"/>
      <path d="M70 100 L96 112 L106 160 L74 160 Z" fill="${dark}"/>
      <path d="M52 108 Q42 150 60 160 L118 160 Q124 130 104 112 Q86 100 66 104 Z" fill="#e8b48a"/>
      <path d="M62 104 Q48 96 52 116 Q60 124 78 118 Z" fill="#d9a67c"/>
      <circle cx="126" cy="18" r="4.5" fill="#000"/>
    </svg>`;
  },
};
const DuelStage = EgoStage; // Alias: Duell, Tests und Playtest sprechen die Bühne weiter als DuelStage an
```

Was sich gegenüber `DuelStage` geändert hat (für die Prüfung, kein zweiter Arbeitsschritt): Kopfkommentar und Name; Zustandsfelder `handKind, weapon, ringOn, ringStart, ringMs, ringGold, moving, runT, cyl, riseRaf, flashTimer, downTimer`; `SETS.hinterzimmer`; `mount` mit `hand`, `handSvg`, `riseRaf` (wird in `unmount` abgebrochen – sonst hebt ein alter Frame die Hand einer neu gemounteten Bühne mit `hand: 'none'`); neue Methoden `hand … slideProp`, `foeGun`; `unmount` entfernt `run`/`jerk` vom Root; `enter` mit Optionen und Zähler nur bei `n > 1`; `drawBackdrop` mit Kerze; `loop` mit Ring-Ende, `runT`, Trommelwinkel; `draw` mit laufenden Bodenlinien, Abzweigungs-Mülltonne (`moving && ringOn`), Vordergrund-Tisch, Ring (Kreis bzw. reduced: Leiste), Trommel, Partikelarten `fist`/`prop`; `handSvg`.

- [ ] **Step 4: CSS**

(a) Direkt hinter `.cs-fig[data-pose="flinch"] .cs-body { animation: csFlinch .4s ease both; }` einfügen:

```css
.cs-fig[data-pose="windup"] .armR { transform: rotate(120deg); transition-duration: .25s; }   /* holt aus: Arm weit nach hinten oben */
.cs-fig[data-pose="windup"] .cs-body { animation: csWindup .9s ease-in-out both; }
.cs-fig[data-pose="temple"] .armR { transform: rotate(-130deg); transition-duration: .4s; }   /* Revolver an der Schläfe */
.cs-fig[data-pose="relief"] .armR { transform: rotate(-20deg); }
.cs-fig[data-pose="relief"] .cs-body { animation: csRelief .6s ease both; }                    /* Ausatmen: sackt kurz zusammen, nickt */
```

(b) Direkt hinter `@keyframes csFade { from { opacity: 0; } to { opacity: 1; } }` einfügen:

```css
@keyframes csWindup { 0% { transform: rotate(0); } 60% { transform: rotate(-6deg) translateX(-3%); } 100% { transform: rotate(-8deg) translateX(-4%); } }
@keyframes csRelief { 0% { transform: translateY(0); } 40% { transform: translateY(4%) rotate(2deg); } 70% { transform: translateY(1%) rotate(-1deg); } 100% { transform: translateY(0); } }
```

(c) Direkt hinter der Zeile `@keyframes csHit { … }` (im Bühnen-CSS, vor dem Kommentar „Handy: Bühne so hoch …") einfügen:

```css
/* Ego-Bühne: Mündungssicht (Revolver dreht auf die Kamera), Laufwackeln (Flucht), Kragengriff */
.cs-fig.unarmed .pistole { opacity: 0; transition: opacity .2s; }   /* Überfall: Räuber ohne Waffe; Roulette: Igor hält den Revolver nur in seinem Zug */
.duel-gun.up.muzzle { transform: translateY(0) scale(1.35); transform-origin: 60% 100%; transition: transform .6s cubic-bezier(.3,1.2,.5,1); }
.duel-stage.run .duel-world { animation: egoBob .35s ease-in-out infinite alternate; }   /* nur die Welt wackelt – der Figur-Transform trägt --s */
.duel-stage.jerk .duel-world { animation: egoJerk .45s ease-out both; }
@keyframes egoBob { from { transform: translateY(0); } to { transform: translateY(-6px) rotate(.4deg); } }
@keyframes egoJerk { 0% { transform: scale(1); } 30% { transform: scale(1.12) translateY(3%); } 100% { transform: scale(1.06) translateY(1%); } }
```

(d) Die reduced-motion-Zeile der Bühne ersetzen – alt:

```css
@media (prefers-reduced-motion: reduce) { .duel-stage .cs-fig.duel-foe, .duel-gun { transition: none; } .duel-gun.recoil, .duel-flash.on, .duel-foe[data-pose="idle"] .armR { animation: none; } }
```

neu:

```css
@media (prefers-reduced-motion: reduce) { .duel-stage .cs-fig.duel-foe, .duel-gun { transition: none; } .duel-gun.recoil, .duel-flash.on, .duel-foe[data-pose="idle"] .armR, .duel-stage.run .duel-world, .duel-stage.jerk .duel-world, .cs-fig[data-pose="windup"] .cs-body, .cs-fig[data-pose="relief"] .cs-body { animation: none; } }
```

- [ ] **Step 5: Tests grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && tests/dom-selftest.sh`
Expected: Node unverändert grün; DOM `failed=0` (ein Test mehr). Die bestehenden Tests „DuelStage: …", „Duell in Ego-Sicht: …", „Duell: reduced-motion …" und „Cutscene-Keyframes (cs*) …" bleiben grün (Alias; `csWindup`/`csRelief` animieren nur transform).

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(ego): DuelStage wird EgoStage – Hand-Varianten, Timing-Ring, laufende Kulisse, Trommel, Hinterzimmer

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Überfall – Overlay `#ego`, `MugAction`, `Mugging.run`

**Files:**
- Modify: `keller37.html` HTML (hinter `<div id="cutscene" hidden></div>`), CSS (hinter `#cutscene[hidden] { display: none; }`)
- Modify: `keller37.html` Block `mugging` (`Mugging.run`, neues Objekt `MugAction`)
- Modify: `keller37.html` Block `selftest` (DOM-Test vor `const pseudoAnim = …`, hinter dem Test aus Task 2)

**Interfaces:**
- Consumes: `EgoStage` (Task 2), `GangRules.TIMING/timingBonus/chanceWithBonus`, `SFX.play('punch'|'whoosh'|'chip'|'click')` (Task 1), `Mugging.TYPES[id].name`, `Rules.fightChance`, `Rules.fleeChance`.
- Produces: `MugAction.TIMES = { intro: 800, run: 1200, outcome: 1300, tail: 500 }`; `MugAction.running`, `MugAction.tapT`; `MugAction.open(set, hand)`, `close()`, `tap()`, `ringPhase(text) → Promise<bonus>`, `brawl(type, baseChance) → Promise<{ won, bonus }>`, `chase(type, baseChance) → Promise<{ won, bonus }>`; Overlay `#ego` mit Bühne `#egoStage.duel-stage.ego-full`, `body.ego-open`; `mug:done { outcome, loot, strength, bonus }`. `MugAction.close()` gibt dem Roulette-Screen seine Bühne zurück (`Russian.mountStage()`, Task 4 – bis dahin `typeof Russian !== 'undefined' && Russian.root` = alter `Russian` ohne `mountStage` → der Aufruf ist mit `Russian.mountStage` guarded, siehe Code).

- [ ] **Step 1: Fehlschlagenden DOM-Test schreiben**

Im Block `selftest` direkt vor `  const pseudoAnim = …` (hinter dem Test „EgoStage: …" aus Task 2) einfügen:

```js
  T.test('Überfall auf der Ego-Bühne: Kampf mit Timing-Treffer (Bonus 0,10), Kampf verloren ohne Tipp, Flucht erwischt (Bonus 0), Zahlen ohne Overlay', async () => {
    const keep = { play: Cutscene.play, rnd: Math.random, s: State.s, save: State.save, mode: State.mode, times: MugAction.TIMES, timing: GangRules.TIMING, open: MugAction.open };
    State.save = () => {}; State.mode = 'free'; State.s = State.fresh(); State.s.balance = 1000; State.s.strength = 2;
    MugAction.TIMES = { intro: 20, run: 40, outcome: 30, tail: 10 }; GangRules.TIMING = { window: 300, gold: 250, bonus: 0.10, cap: 0.95 };
    let choice = 'fight', opens = 0, overlayDuringOutcome = null; const scenes = [];
    Cutscene.play = async (id) => { scenes.push(id); if (id === 'mug.intro') return choice; overlayDuringOutcome = !qs('#ego').hidden; return null; };
    MugAction.open = function (...a) { opens++; return keep.open.apply(this, a); };
    const done = []; const off = Bus.on('mug:done', (e) => done.push(e));
    const untilRing = async () => { for (let i = 0; i < 100; i++) { if (EgoStage.mounted && EgoStage.ringOn) return true; await wait(5); } return false; };
    const tick = (n) => { for (let i = 0; i < n; i++) { EgoStage.last = EgoStage.last || 1000; EgoStage.loop(EgoStage.last + 50); } };
    const key = (code) => document.dispatchEvent(new KeyboardEvent('keydown', { code, bubbles: true, cancelable: true }));
    try {
      /* Kampf, Tipp per Leertaste im goldenen Fenster (Bühnen-Uhr von Hand auf 100 ms getaktet, Fenster 50–300), Würfel 0 → gewonnen */
      Math.random = () => 0;
      let p = Mugging.run('junkie');
      T.ok(await untilRing(), 'Ring läuft');
      T.eq([qs('#ego').hidden, document.body.classList.contains('ego-open'), EgoStage.set, EgoStage.handKind, qs('#ego .duel-foe').dataset.pose, qs('#duelFoeName').textContent], [false, true, 'gasse', 'fist', 'windup', 'Der Junkie'], 'Overlay offen: Gasse, Faust, Räuber holt aus');
      tick(2); key('Space'); T.eq(MugAction.tapT, EgoStage.ringTime(), 'Leertaste = Tipp (capture, vor den Screens)'); T.eq(qs('#ego .duel-flash').textContent, 'TREFFER!');
      key('Space'); tick(1); T.ok(MugAction.tapT < EgoStage.ringTime(), 'nur der erste Tipp zählt');
      await p;
      T.eq([done.length, done[0].outcome, done[0].bonus, done[0].strength, State.s.strength, State.s.stats.fightsWon, qs('#ego').hidden, document.body.classList.contains('ego-open'), overlayDuringOutcome, EgoStage.mounted], [1, 'fightWon', 0.10, 3, 3, 1, true, false, false, false], 'gewonnen mit Bonus, Overlay vor dem Text-Panel geschlossen, Bühne abgebaut');
      T.eq(scenes, ['mug.intro', 'mug.fightWon']);
      /* Kampf ohne Tipp, Würfel 0,99 → verloren: Faust auf die Kamera, „Du liegst“, Bonus 0, Stärke trotzdem +1 */
      Math.random = () => 0.99; scenes.length = 0;
      p = Mugging.run('cousin'); T.ok(await untilRing()); await p;
      T.eq([done[1].outcome, done[1].bonus, State.s.strength, State.s.balance < 1000, scenes], ['fightLost', 0, 4, true, ['mug.intro', 'mug.fightLost']], 'verloren ohne Bonus');
      /* Flucht ohne Tipp, Würfel 0,99 → erwischt: laufende Kulisse, Räuber holt auf */
      choice = 'flee'; scenes.length = 0; const bal = State.s.balance;
      p = Mugging.run('jugend');
      let running = false; for (let i = 0; i < 100 && !running; i++) { await wait(5); running = EgoStage.mounted && EgoStage.moving && qs('#egoStage').classList.contains('run'); }
      T.ok(running, 'Flucht: Kulisse läuft'); T.eq([EgoStage.handKind, qs('#ego .duel-foe').dataset.pose], ['none', 'walk'], 'keine Hand, Räuber rennt');
      T.ok(await untilRing(), 'Abzweigung: Ring'); await p;
      T.eq([done[2].outcome, done[2].bonus, State.s.balance < bal, State.s.strength, scenes, qs('#ego').hidden], ['caught', 0, true, 4, ['mug.intro', 'mug.caught'], true], 'erwischt, Bonus 0, Stärke unverändert');
      /* Zahlen: kein Overlay */
      choice = 'pay'; await Mugging.run('junkie');
      T.eq([opens, done[3].outcome, done[3].bonus], [3, 'paid', 0], 'Zahlen öffnet die Bühne nicht');
    } finally {
      off(); Cutscene.play = keep.play; Math.random = keep.rnd; State.save = keep.save; State.s = keep.s; State.mode = keep.mode; MugAction.TIMES = keep.times; GangRules.TIMING = keep.timing; MugAction.open = keep.open;
      if (MugAction.running) MugAction.close();
    }
  });
```

- [ ] **Step 2: Test laufen lassen – er muss fehlschlagen**

Run: `tests/dom-selftest.sh`
Expected: `failed=1` (`MugAction is not defined`).

- [ ] **Step 3: Overlay**

HTML: direkt hinter `<div id="cutscene" hidden></div>` einfügen:

```html
<div id="ego" hidden></div>
```

CSS: direkt hinter `#cutscene[hidden] { display: none; }` einfügen:

```css
/* Ego-Overlay (Überfall): Vollbild-Bühne über allem, wie #cutscene */
#ego { position: fixed; inset: 0; z-index: 80; background: #000; animation: fadeIn .3s ease both; }
#ego[hidden] { display: none; }
#ego .duel-stage.ego-full { height: 100%; min-height: 0; border-radius: 0; }
body.ego-open #toasts { bottom: auto; top: 64px; right: 20px; left: auto; }
```

- [ ] **Step 4: `MugAction`**

Im Block `mugging` direkt **vor** `Cutscene.define('mug.intro', (ctx) => [` einfügen:

```js
/* ================= ÜBERFALL-ACTION – Kampf und Flucht als Ego-Einschub zwischen Wahl-Panel und Ausgangs-Text =================
   Ausgang wird gewürfelt wie bisher; ein Tipp im goldenen Fenster des Timing-Rings gibt GangRules.TIMING.bonus dazu. */
const MugAction = {
  TIMES: { intro: 800, run: 1200, outcome: 1300, tail: 500 },   // Tests kürzen diese Werte; das Ring-Fenster steht in GangRules.TIMING
  running: false, tapT: null, stage: null,
  reduced() { return matchMedia('(prefers-reduced-motion: reduce)').matches; },
  open(set, hand) {
    const ov = qs('#ego');
    ov.innerHTML = ''; ov.hidden = false;
    this.stage = h('div', { class: 'duel-stage ego-full', id: 'egoStage' });
    ov.append(this.stage);
    document.body.classList.add('ego-open');
    EgoStage.mount(this.stage, { set, weapon: 0, reduced: this.reduced(), hand });
    this.running = true; this.tapT = null;
    this.onPointer = (e) => { e.preventDefault(); this.tap(); };
    this.onKey = (e) => { if (e.code === 'Space' || e.code === 'Enter') { e.preventDefault(); e.stopImmediatePropagation(); if (!e.repeat) this.tap(); } };
    ov.addEventListener('pointerdown', this.onPointer);
    document.addEventListener('keydown', this.onKey, true); // capture: die Spiel-Screens darunter bekommen die Taste nicht
  },
  close() {
    const ov = qs('#ego');
    ov.removeEventListener('pointerdown', this.onPointer); document.removeEventListener('keydown', this.onKey, true);
    EgoStage.unmount();
    ov.hidden = true; ov.innerHTML = ''; this.stage = null;
    document.body.classList.remove('ego-open');
    this.running = false;
    if (typeof Russian !== 'undefined' && Russian.root && !Russian.inDuel && Russian.mountStage) Russian.mountStage(); // die Bühne ist ein Singleton: dem Roulette-Screen seine zurückgeben
  },
  /* Nur der erste Tipp zählt, und nur während der Ring läuft */
  tap() {
    if (!this.running || this.tapT !== null) return;
    const t = EgoStage.ringTime();
    if (t == null) return;
    this.tapT = t;
    const bonus = GangRules.timingBonus(t);
    if (bonus) { EgoStage.flash(this.flashText, 600); SFX.play('chip'); if (navigator.vibrate) navigator.vibrate(20); }
    else SFX.play('click');
  },
  async ringPhase(text) {
    this.flashText = text; this.tapT = null;
    EgoStage.ring(GangRules.TIMING.window, GangRules.TIMING.gold);
    await wait(GangRules.TIMING.window + 60);
    EgoStage.ringStop();
    return GangRules.timingBonus(this.tapT);
  },
  /* Faustkampf: Räuber holt aus, Ring, Tipp, Würfeln, Ausgang → { won, bonus } */
  async brawl(type, baseChance) {
    this.open('gasse', 'fist');
    try {
      EgoStage.enter('raeuber', 0, 1, type.name, { gun: false });
      await wait(this.TIMES.intro);
      EgoStage.foePose('windup'); SFX.play('whoosh');
      const bonus = await this.ringPhase('TREFFER!');
      const won = Math.random() < GangRules.chanceWithBonus(baseChance, bonus);
      if (won) { EgoStage.punch(true); SFX.play('punch'); EgoStage.foeDown(); if (navigator.vibrate) navigator.vibrate(30); }
      else { EgoStage.foePose('idle'); EgoStage.punch(false); SFX.play('punch'); if (navigator.vibrate) navigator.vibrate([40, 40, 80]); EgoStage.flash('Du liegst', 900); }
      await wait(this.TIMES.outcome);
      return { won, bonus };
    } finally { this.close(); }
  },
  /* Flucht: laufende Kulisse, Räuber holt auf, Abzweigung + Ring, Tipp, Würfeln, Ausgang → { won, bonus } */
  async chase(type, baseChance) {
    this.open('gasse', 'none');
    try {
      EgoStage.enter('raeuber', 0, 1, type.name, { gun: false });
      EgoStage.foeScale(0.5, 0); EgoStage.foePose('walk');
      await wait(this.TIMES.intro);
      EgoStage.motion(true); SFX.play('whoosh');
      EgoStage.foeScale(0.8, this.TIMES.run);
      await wait(this.TIMES.run);
      const bonus = await this.ringPhase('HAKEN!');
      const won = Math.random() < GangRules.chanceWithBonus(baseChance, bonus);
      if (won) { EgoStage.foeScale(0.3, this.TIMES.outcome); EgoStage.flash('Weg!', 700); }
      else { EgoStage.foeScale(1.3, Math.round(this.TIMES.outcome * 0.55)); await wait(Math.round(this.TIMES.outcome * 0.55)); EgoStage.foePose('point'); EgoStage.grab(); SFX.play('punch'); if (navigator.vibrate) navigator.vibrate([40, 40, 80]); EgoStage.flash('Erwischt', 900); }
      await wait(this.TIMES.outcome);
      EgoStage.motion(false);
      await wait(this.TIMES.tail);
      return { won, bonus };
    } finally { this.close(); }
  },
};
```

- [ ] **Step 5: `Mugging.run` umbauen**

In `Mugging.run` den Kampf-Zweig ersetzen – alt:

```js
    if (choice === 'fight') {
      const won = Math.random() < Rules.fightChance(s.strength, mods);
      if (won) {
```

neu:

```js
    let bonus = 0;
    if (choice === 'fight') {
      const r = await MugAction.brawl(T, Rules.fightChance(s.strength, mods));
      const won = r.won; bonus = r.bonus;
      if (won) {
```

Den Flucht-Zweig ersetzen – alt:

```js
    } else if (choice === 'flee') {
      if (Math.random() < Rules.fleeChance(gear)) outcome = 'fled';
      else { outcome = 'caught'; delta = -Math.min(s.balance, loot + Rules.fleeFailExtra(s.balance)); }
    } else { outcome = 'paid'; delta = -loot; }
```

neu:

```js
    } else if (choice === 'flee') {
      const r = await MugAction.chase(T, Rules.fleeChance(gear));
      bonus = r.bonus;
      if (r.won) outcome = 'fled';
      else { outcome = 'caught'; delta = -Math.min(s.balance, loot + Rules.fleeFailExtra(s.balance)); }
    } else { outcome = 'paid'; delta = -loot; }
```

Das Event am Ende von `run` ersetzen – alt: `    await Bus.emit('mug:done', { outcome, loot, strength: s.strength });` neu:

```js
    await Bus.emit('mug:done', { outcome, loot, strength: s.strength, bonus });
```

- [ ] **Step 6: Tests grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && tests/dom-selftest.sh`
Expected: beide grün (DOM: ein Test mehr).

- [ ] **Step 7: Von Hand ansehen (Dev)**

`keller37.html?fresh&screen=hub&mug=cousin` im Browser öffnen, Tür wählen, „Kämpfen": Räuber holt aus (Arm nach hinten), Ring zieht sich zu, Tipp im Gold → „TREFFER!"; Ausgang gewonnen (Faust ruckt, Blut, Fall in Zeitlupe) oder verloren (Faust auf die Kamera, roter Rand, „Du liegst"); Overlay schließt vor dem Text-Panel. Noch einmal mit „Wegrennen": Kulisse läuft, Räuber holt auf, Mülltonne rechts, Ring „HAKEN!", „Weg!" oder „Erwischt".

- [ ] **Step 8: Commit**

```bash
git add keller37.html
git commit -m "feat(ueberfall): Kampf und Flucht als Ego-Einschub mit Timing-Ring (+10 pp), mug:done meldet bonus

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Russisches Roulette auf der Ego-Bühne

**Files:**
- Modify: `keller37.html` Block `game-russian` (Objekt `Russian`, `UI.register('russian')`)
- Modify: `keller37.html` `<template id="tpl-russian">`, CSS-Block `/* -- Russisches Roulette -- */`, `@keyframes cylZoom`
- Modify: `keller37.html` Block `selftest` (DOM-Test vor `const pseudoAnim = …`, hinter dem Test aus Task 3)

**Interfaces:**
- Consumes: `EgoStage` (Task 2), `SFX`, `Rules.rrCylinder/rrDelta`, `Game.readBet/beginSpin/forfeit/settle`, `Cutscene.play`, `Bus`, `UI.fmt`, `wait`.
- Produces: `Russian.TIMES = { turn: 600, igor: 1100, spin: 350, bang: 600, relief: 500 }` (Tests kürzen); `Russian.mountStage()`, `stageEl()`, `chambers(idx, spent)`, `setTurn(who, gen)`, `onKey(e)`; unverändert `start/pull/end/drop/inDuel/duel/busy/heartbeat/bang`; `duel.spent` (Liste leerer Kammern); Template-Bühne `#rrStage`. Die Trommel dreht (wie bisher `rotateTo`) am Anfang jedes Abzugs auf die aktuelle Kammer; nach dem Zug bleibt `EgoStage.cyl.idx` also auf der zuletzt gedrehten Kammer.

- [ ] **Step 1: Fehlschlagenden DOM-Test schreiben**

Im Block `selftest` direkt vor `  const pseudoAnim = …` (hinter dem Überfall-Test aus Task 3) einfügen:

```js
  T.test('Russisch Roulette in Ego-Sicht: Hinterzimmer, Igor, Trommel, Mündungssicht; Klick/Klick/Kugel beim Spieler; forced: Igor liegt; drop beim Verlassen', async () => {
    const keep = { cur: UI.current, s: State.s, save: State.save, mode: State.mode, cyl: Rules.rrCylinder, play: Cutscene.play, times: Russian.TIMES };
    State.save = () => {}; State.mode = 'free'; State.s = State.fresh(); State.s.balance = 1000; State.s.flags.igor = true;
    Russian.TIMES = { turn: 20, igor: 30, spin: 10, bang: 250, relief: 10 }; // bang ≥ 220 ms: der Fall (foeDown-Timer) muss wie im Spiel vor end() kommen
    const scenes = []; Cutscene.play = async (id) => { scenes.push(id); return null; };
    const ev = []; const off1 = Bus.on('rr:result', (e) => ev.push(['result', e.victim, e.bet])); const off2 = Bus.on('rr:forced', (e) => ev.push(['forced', e.victim]));
    const key = (code) => document.dispatchEvent(new KeyboardEvent('keydown', { code, bubbles: true, cancelable: true }));
    try {
      await UI.show('russian');
      T.eq([EgoStage.mounted, EgoStage.set, EgoStage.root === qs('#rrStage'), qsa('#rrStage .duel-foe svg.part').length, EgoStage.cyl.idx, EgoStage.handKind, qs('#chambersLeft').textContent], [true, 'hinterzimmer', true, 8, 0, 'none', '6 Kammern'], 'Bühne steht beim Betreten: Hinterzimmer, Igor, Trommel, keine Hand');
      Rules.rrCylinder = () => [false, false, true, false, false, false];
      qs('#rrBet').value = '10';
      await Russian.start();
      T.eq([Russian.inDuel, State.s.balance, qs('#rrActionControls').classList.contains('hidden'), EgoStage.handKind, qs('#rrStage .duel-gun').classList.contains('muzzle'), qs('#rrStage .duel-gun').classList.contains('up'), EgoStage.tenseFrom > 0], [true, 990, false, 'revolverMuzzle', true, true, true], 'Einsatz abgezogen, Revolver hebt sich in Mündungssicht, Anspannung');
      /* Zug 1 per Leertaste: Klick beim Spieler → Igor (Revolver gleitet, Schläfe) → Klick → Erleichterung → wieder Spieler */
      key('Space'); T.eq([Russian.busy, qs('#btnTrigger').disabled], [true, true], 'Leertaste drückt ab, Knopf gesperrt');
      const seen = new Set(); for (let i = 0; i < 200 && Russian.busy; i++) { seen.add(qs('#rrStage .duel-foe').dataset.pose); await wait(5); }
      T.ok(seen.has('temple') && seen.has('relief'), `Igor: Schläfe und Erleichterung (${[...seen].join(',')})`);
      T.eq([Russian.inDuel, Russian.busy, EgoStage.cyl.idx, EgoStage.cyl.spent, qs('#chambersLeft').textContent, qs('#btnTrigger').disabled, EgoStage.handKind, qs('#rrStage .duel-foe').dataset.pose, EgoStage.parts.some((p) => p.kind === 'prop')], [true, false, 1, [0, 1], '4 Kammern übrig', false, 'revolverMuzzle', 'idle', true], 'zwei leere Kammern (Trommel dreht erst beim nächsten Abzug weiter), Revolver wieder bei dir');
      /* Zug 2: Kugel beim Spieler → Blitz, roter Rand, rr:result, rr.headshot, Abrechnung −(10 + 100) */
      await Russian.pull();
      T.eq([Russian.inDuel, ev, scenes, State.s.balance, qs('#rrBetControls').classList.contains('hidden'), EgoStage.redUntil > EgoStage.t, qs('#rrStage .duel-gun').classList.contains('up')], [false, [['result', 'player', 10]], ['rr.headshot'], 890, false, true, false], 'Streifschuss abgerechnet, Hand gesenkt');
      /* forced (Vitos Prüfung): kein Einsatz, Igor erwischt es → rr:forced igor, Igor fällt */
      ev.length = 0; Rules.rrCylinder = () => [false, true, false, false, false, false];
      await Russian.start({ forced: true }); T.eq([Russian.inDuel, State.s.balance, qs('#rrStatus').textContent.includes('Vitos Prüfung')], [true, 890, true]);
      await Russian.pull();
      T.eq([Russian.inDuel, ev, State.s.balance, qs('#rrStage .duel-foe').dataset.pose, EgoStage.stains.length >= 1, qs('#rrStage .duel-gun').classList.contains('up')], [false, [['forced', 'igor']], 890, 'down', true, false], 'Igor liegt (und bleibt liegen), kein Geld bewegt, Hand unten');
      /* drop: Screen mitten im Duell verlassen → Einsatz verfällt, Bühne abgebaut */
      ev.length = 0; Rules.rrCylinder = () => [false, false, false, false, false, true];
      await Russian.start(); T.eq([Russian.inDuel, State.s.balance, Game.inFlight], [true, 880, 1]);
      await UI.show('hub');
      T.eq([Russian.inDuel, Russian.root, Game.inFlight, State.s.balance, EgoStage.mounted, ev], [false, null, 0, 880, false, []], 'drop: Einsatz weg, kein Event, Bühne weg');
      for (const name of ['egoBob', 'egoJerk']) { const kf = keyframesOf(name); T.ok(kf, `@keyframes ${name}`); for (const p of animatedProps(kf)) T.ok(p === 'transform' || p === 'opacity', `${name}: ${p}`); }
    } finally {
      off1(); off2(); Cutscene.play = keep.play; Rules.rrCylinder = keep.cyl; Russian.TIMES = keep.times; State.save = keep.save; State.s = keep.s; State.mode = keep.mode;
      SFX.stop('heartbeat');
      await UI.show(keep.cur ? keep.cur.id : 'hub');
    }
  });
```

- [ ] **Step 2: Test laufen lassen – er muss fehlschlagen**

Run: `tests/dom-selftest.sh`
Expected: `failed=1` (Meldung „Bühne steht beim Betreten …" – `EgoStage.mounted` ist false, oder `qs('#rrStage')` null).

- [ ] **Step 3: Template und CSS**

Im `<template id="tpl-russian">` die alten Kämpfer/Trommel-Knoten ersetzen – alt:

```html
    <div class="rr-flash" id="rrFlash"></div>
    <div class="duel">
      <div class="fighter" id="fPlayer"><div class="face">🤠</div><div class="fname">Du</div></div>
      <div class="cylinder-box">
        <div class="cyl-wrap"><svg id="cylinder" viewBox="0 0 200 200" width="200" height="200" aria-hidden="true"></svg><div class="cyl-pointer">▼</div></div>
        <div class="chambers-left" id="chambersLeft">6 Kammern</div>
      </div>
      <div class="fighter" id="fIgor"><div class="face">🐻</div><div class="fname">Igor</div></div>
    </div>
```

neu:

```html
    <div class="duel-stage" id="rrStage"></div>
    <div class="chambers-left" id="chambersLeft">6 Kammern</div>
```

Den CSS-Block von `/* -- Russisches Roulette -- */` bis **vor** `/* -- Post austragen -- */` komplett ersetzen durch:

```css
/* -- Russisches Roulette -- */
.rr-panel { position: relative; background: radial-gradient(circle at 50% 0%, #1b2430, #0b0f14 70%); border-color: rgba(76,201,240,.25); overflow: hidden; }
.rr-panel .duel-stage { cursor: pointer; }
.chambers-left { font-family: var(--font-mono); font-size: .85rem; color: var(--dim); }
```

Die Zeile `@keyframes cylZoom { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.12); } }` löschen (nur der alte Trommel-Zoom nutzte sie; `@keyframes flash` bleibt – andere Stellen nutzen sie).

- [ ] **Step 4: `Russian` ersetzen**

Im Block `game-russian` alles von der Zeile `/* ================= RUSSISCHES ROULETTE ================= */` bis **vor** die Zeile `UI.register('russian', {` (also Kopfkommentar und das komplette Objekt `Russian` inklusive `};`) durch Folgendes ersetzen:

```js
/* ================= RUSSISCHES ROULETTE – Ego-Sicht: Igor gegenüber am Tisch, der Revolver dreht sich auf die Kamera ================= */
const Russian = {
  root: null, duel: null, inDuel: false, busy: false, gen: 0,
  TIMES: { turn: 600, igor: 1100, spin: 350, bang: 600, relief: 500 },   // Tests kürzen; Regeln bleiben in Rules
  alive(gen) { return !!this.root && this.gen === gen; },
  reduced() { return matchMedia('(prefers-reduced-motion: reduce)').matches; },
  stageEl() { return this.root ? qs('#rrStage', this.root) : null; },
  /* Leertaste/Enter = Abzug (nur im Duell, nicht während Igors Zug, nicht unter Cutscene/Ego-Overlay) */
  onKey(e) { if ((e.code === 'Space' || e.code === 'Enter') && qs('#cutscene').hidden && qs('#ego').hidden && Russian.inDuel && !Russian.busy && !e.repeat) { e.preventDefault(); Russian.pull(); } },
  /* Bühne aufbauen: Hinterzimmer, Igor tritt an den Tisch, Trommel unten links */
  mountStage() {
    if (!this.root) return;
    EgoStage.mount(this.stageEl(), { set: 'hinterzimmer', weapon: 0, reduced: this.reduced(), hand: 'none' });
    EgoStage.enter('igor', 0, 1, 'Igor', { gun: false });
    EgoStage.cylinder({ idx: 0, spent: [] });
  },
  chambers(idx, spent) {
    if (!this.root) return;
    EgoStage.cylinder({ idx, spent });
    const left = 6 - spent.length;
    qs('#chambersLeft', this.root).textContent = spent.length ? `${left} Kammer${left === 1 ? '' : 'n'} übrig` : '6 Kammern';
  },
  /* Wer ist dran: Spieler → Revolver hebt sich und dreht zur Mündungssicht; Igor → Revolver gleitet über den Tisch, Igor hebt ihn an die Schläfe */
  async setTurn(who, gen) {
    if (!this.alive(gen)) return;
    if (who === 'player') {
      EgoStage.foePose('idle'); EgoStage.foeGun(false);
      if (this.reduced()) { EgoStage.hand('revolverMuzzle'); EgoStage.handRise(); }
      else { EgoStage.hand('revolver'); EgoStage.handRise(); await wait(this.TIMES.turn); if (this.alive(gen)) EgoStage.hand('revolverMuzzle'); }
      EgoStage.tension(true);
    } else if (who === 'igor') {
      EgoStage.tension(false); EgoStage.handDrop();
      const hp = EgoStage.foeHand();
      EgoStage.slideProp({ x: EgoStage.W * 0.7, y: EgoStage.H * 0.9 }, hp, this.reduced() ? 1 : 500);
      await wait(this.reduced() ? 0 : 500);
      if (this.alive(gen)) { EgoStage.foeGun(true); EgoStage.foePose('temple'); }
    } else { EgoStage.tension(false); EgoStage.handDrop(); } // Ende: Pose bleibt (Igor liegt ggf.)
  },
  heartbeat(duel) {
    if (!this.alive(duel.gen)) return;
    SFX.loop('heartbeat', Math.max(380, 900 - duel.idx * 110));
  },
  /* Duell ohne Abrechnung abbrechen (Screen verlassen) – Einsatz ist bereits abgezogen */
  drop(duel) {
    if (!duel || duel.done) return;
    duel.done = true;
    if (duel.forced) { Bus.emit('rr:forced', { victim: 'aborted' }); return; }
    Game.forfeit();
  },
  async start(opts = {}) {
    if (this.inDuel || !this.root) return;
    const forced = !!opts.forced;
    const bet = forced ? 0 : Game.readBet('rrBet');
    if (!forced && !Game.beginSpin(bet)) return;
    const gen = this.gen;
    const duel = { cylinder: Rules.rrCylinder(Math.random), idx: 0, bet, gen, run: forced ? null : Game.run, done: false, forced, spent: [] };
    this.duel = duel;
    this.inDuel = true;
    if (this.alive(gen)) {
      this.mountStage();
      qs('#chambersLeft', this.root).textContent = '6 Kammern';
      qs('#rrBetControls', this.root).classList.add('hidden');
      qs('#rrActionControls', this.root).classList.remove('hidden');
    }
    if (!State.s.flags.igor) { State.s.flags.igor = true; State.save(); await Cutscene.play('igor.first', {}); }
    if (!this.alive(gen)) return;
    qs('#rrStatus', this.root).textContent = forced ? 'Vitos Prüfung. Kein Einsatz – nur dein Kopf. Drück ab.' : 'Du bist dran. Drück ab.';
    await this.setTurn('player', gen);
    this.heartbeat(duel);
  },
  /* Knall: Spieler → Blitz/Ruck/roter Rand/Tropfen; Igor → Mündungsblitz am Kopf, Blut, Fall in Zeitlupe */
  async bang(who, gen) {
    if (this.alive(gen)) {
      SFX.stopAll(); SFX.play('gunshot');
      if (who === 'player') { EgoStage.selfShot(); if (navigator.vibrate) navigator.vibrate([40, 40, 80]); }
      else { const hp = EgoStage.foeHand(); EgoStage.muzzleAt(hp.x, hp.y - 10); const b = EgoStage.foeBox(); EgoStage.burst(b.left + b.width * 0.5, b.top + b.height * 0.25, 'blood', 22); EgoStage.foeDown(); }
    }
    await wait(this.TIMES.bang);
  },
  async pull() {
    if (!this.inDuel || this.busy || !this.root) return;
    const duel = this.duel;
    const gen = duel.gen;
    this.busy = true;
    try {
      if (this.alive(gen)) qs('#btnTrigger', this.root).disabled = true;
      this.chambers(duel.idx, duel.spent);
      await wait(this.TIMES.spin);
      if (duel.cylinder[duel.idx]) {
        if (this.alive(gen)) qs('#rrStatus', this.root).innerHTML = duel.forced ? `<span class="loss">PÄNG · Streifschuss</span>` : `<span class="loss">PÄNG · Streifschuss · −${UI.fmt(duel.bet)} & 100 € Spital</span>`;
        await this.bang('player', gen);
        await this.end('player', duel);
        return;
      }
      if (this.alive(gen)) { SFX.play('dryfire'); if (navigator.vibrate) navigator.vibrate(15); }
      duel.spent.push(duel.idx); this.chambers(duel.idx, duel.spent);
      duel.idx++;
      if (this.alive(gen)) qs('#rrStatus', this.root).textContent = '*Klick*… Leer. Igor ist dran…';
      await this.setTurn('igor', gen);
      this.heartbeat(duel);
      await wait(this.TIMES.igor);
      this.chambers(duel.idx, duel.spent);
      await wait(this.TIMES.spin);
      if (duel.cylinder[duel.idx]) {
        if (this.alive(gen)) qs('#rrStatus', this.root).innerHTML = duel.forced ? `<span class="win">PÄNG · Igor liegt</span>` : `<span class="win">PÄNG · Igor liegt · +${UI.fmt(duel.bet)}</span>`;
        await this.bang('igor', gen);
        await this.end('igor', duel);
        return;
      }
      if (this.alive(gen)) { SFX.play('dryfire'); EgoStage.foePose('relief'); }
      duel.spent.push(duel.idx); this.chambers(duel.idx, duel.spent);
      duel.idx++;
      await wait(this.TIMES.relief);
      if (this.alive(gen)) {
        qs('#rrStatus', this.root).textContent = '*Klick*… Igor lebt. Du bist dran.';
        await this.setTurn('player', gen);
        if (this.alive(gen)) qs('#btnTrigger', this.root).disabled = false;
      }
      this.heartbeat(duel);
      if (!this.alive(gen)) this.drop(duel); // Screen während des Zugs verlassen, Duell nicht entschieden
    } finally {
      if (this.gen === gen) this.busy = false;
    }
  },
  async end(victim, duel) {
    if (duel.done) return;
    duel.done = true;
    const gen = duel.gen;
    if (this.alive(gen)) SFX.stopAll(); else SFX.stop('heartbeat');
    try {
      if (this.alive(gen)) {
        await this.setTurn(null, gen);
        qs('#rrActionControls', this.root).classList.add('hidden');
        qs('#rrBetControls', this.root).classList.remove('hidden');
        qs('#btnTrigger', this.root).disabled = false;
      }
    } finally {
      if (this.gen === gen) { this.inDuel = false; this.busy = false; }
    }
    if (duel.forced) { await Bus.emit('rr:forced', { victim }); return; }
    const delta = Rules.rrDelta(victim, duel.bet);
    await Bus.emit('rr:result', { victim, bet: duel.bet });
    if (victim === 'player' && this.alive(gen)) await Cutscene.play('rr.headshot', {});
    await Game.settle(delta, { from: this.alive(gen) ? this.stageEl() : null, game: 'russian', bet: duel.bet, run: duel.run });
  },
};
```

- [ ] **Step 5: Screen-Registrierung**

In `UI.register('russian', { … })` `mount` und den Anfang von `unmount` ersetzen – alt:

```js
  mount(root) {
    Russian.gen++;
    Russian.root = root;
    Russian.drawCylinder();
    Game.bindBet(root, 'rrBet');
    qs('#btnDuel', root).addEventListener('click', () => Russian.start());
    qs('#btnTrigger', root).addEventListener('click', () => Russian.pull());
  },
  unmount() {
    Russian.gen++;
    SFX.stop('heartbeat');
```

neu:

```js
  mount(root) {
    Russian.gen++;
    Russian.root = root;
    Russian.mountStage();
    Game.bindBet(root, 'rrBet');
    qs('#btnDuel', root).addEventListener('click', () => Russian.start());
    qs('#btnTrigger', root).addEventListener('click', () => Russian.pull());
    qs('#rrStage', root).addEventListener('pointerdown', (e) => { e.preventDefault(); Russian.pull(); });
    document.addEventListener('keydown', Russian.onKey);
  },
  unmount() {
    Russian.gen++;
    document.removeEventListener('keydown', Russian.onKey);
    if (EgoStage.root && EgoStage.root === Russian.stageEl()) EgoStage.unmount(); // nur die eigene Bühne abbauen (nicht ein laufendes Überfall-Overlay)
    SFX.stop('heartbeat');
```

Der Rest von `unmount` (Abbruch mit `drop`, Toast, `root = null`, `inDuel/busy = false`) bleibt.

- [ ] **Step 6: Tests grün, Altlasten weg**

Run: `grep -n "rrFlash\|fPlayer\|fIgor\|#cylinder\|drawCylinder\|rotateTo\|markSpent\|cylZoom\|cylinder-box" keller37.html tests/*.py`
Expected: leer.

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && tests/dom-selftest.sh`
Expected: beide grün (DOM: ein Test mehr).

- [ ] **Step 7: Von Hand ansehen (Dev)**

`keller37.html?fresh&screen=russian`: Hinterzimmer mit Kerze, Igor tritt an den Tisch, Trommel unten links, keine Hand. „Duell starten": Revolver hebt sich und dreht in die Mündungssicht, Rand dunkelt, Herzschlag. Abzug (Knopf, Tipp auf die Bühne, Leertaste): Klick → Kammer grau, Revolver gleitet zu Igor, er hebt ihn an die Schläfe, Klick → Erleichterung → „Du bist dran". Mit `Rules.rrCylinder = () => [true]` in der Konsole: Blitz, Ruck, roter Rand, Tropfen, Doc-Szene, −(Einsatz + 100 €). Mit `[false, true]`: Mündungsfeuer am Kopf, Blut, Igor fällt in Zeitlupe und bleibt liegen, +Einsatz.

- [ ] **Step 8: Commit**

```bash
git add keller37.html
git commit -m "feat(roulette): Russisches Roulette in Ego-Sicht – Hinterzimmer, Igor am Tisch, Mündungssicht, Trommel-Nahaufnahme

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Playtest, Trace, Doku, Abschluss

**Files:**
- Modify: `tests/playtest-story.py` (Helfer, Überfall-Szenario, Tag-10-Duell)
- Modify: `tests/perf-trace.py` (zwei Szenarien)
- Modify: `README.md`, `docs/superpowers/specs/2026-09-21-ego-buehne-ueberfall-roulette-design.md`

**Interfaces:**
- Consumes: `MugAction.running/tap()/tapT`, `EgoStage.ringTime()/moving/mounted/set/cyl/handKind`, `GangRules.TIMING`, `Russian.busy/inDuel/TIMES`, `mug:done.bonus`.
- Produces: `__pt.egoTap() → Promise<boolean>` (wartet bis zu 8 s auf den Ring und tippt 40 ms nach Beginn des goldenen Fensters), `__pt.lastMug` (letztes `mug:done`-Event).

- [ ] **Step 1: Playtest-Helfer**

In `PAGE_HELPERS` direkt **vor** `__pt.duelShoot = function() {` einfügen:

```js
__pt.lastMug = null;
if (typeof Bus !== 'undefined' && !__pt.mugHooked) { __pt.mugHooked = true; Bus.on('mug:done', (e) => { __pt.lastMug = e; }); }
__pt.egoTap = function() {
  // Ueberfall-Einschub (Ego-Buehne): wartet, bis der Timing-Ring laeuft, und tippt im goldenen Fenster (Bonus +10 pp)
  return new Promise((resolve) => {
    const t0 = Date.now();
    const iv = setInterval(() => {
      if (Date.now() - t0 > 8000) { clearInterval(iv); resolve(false); return; }
      if (typeof MugAction === 'undefined' || !MugAction.running) return;
      const t = EgoStage.ringTime();
      if (t != null && t >= GangRules.TIMING.window - GangRules.TIMING.gold + 40) { MugAction.tap(); clearInterval(iv); resolve(MugAction.tapT != null); }
    }, 15);
  });
};
```

- [ ] **Step 2: Überfall-Szenario (`scenario_mugging`)**

Den Kampf-Abschnitt ersetzen – alt (beginnt hinter `await cdp.eval("window.__origRandom = Math.random; Math.random = () => 0; 0", await_promise=False)`):

```python
    await cdp.eval("__pt.advance('Kämpfen')", await_promise=False)
    await asyncio.sleep(0.5)
    # Screenshot mitten in der Ergebnis-Szene (Gasse-Hintergrund, Portrait, Kampftext) statt erst
    # nach deren vollstaendiger Aufloesung -- die Brief-Version schoss erst nach dem kompletten
    # Durchklicken, als bereits wieder das Roulette-Blatt zu sehen war (siehe Report).
    await cdp.screenshot("mug-fight.png")
    await cdp.advance_cutscene()
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    await asyncio.sleep(0.4)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    won = await cdp.eval("State.s.stats.fightsWon", await_promise=False)
    record("mug: Kampf mit Staerke 20 gewonnen, Brieftasche 50-150, Staerke 21", bal == 1050 and st == 21 and won == 1, "bal=%s st=%s won=%s" % (bal, st, won))
```

neu:

```python
    await cdp.eval("__pt.advance('Kämpfen')", await_promise=False)
    # Ego-Einschub: Raeuber holt aus, Timing-Ring, Tipp im goldenen Fenster (+10 pp); gewuerfelt wird
    # erst danach im Einschub -- der Math.random-Stub bleibt bis zum Ausgangs-Panel stehen.
    tapped = await cdp.eval("__pt.egoTap()", await_promise=True)
    ego_open = await cdp.eval("!document.querySelector('#ego').hidden && MugAction.running && EgoStage.handKind === 'fist'", await_promise=False)
    record("mug: Kampf-Einschub auf der Ego-Buehne (Faust, Ring), Tipp im goldenen Fenster", tapped is True and ego_open is True, "tapped=%s ego_open=%s" % (tapped, ego_open))
    await cdp.screenshot("mug-fight.png")
    active = await cdp.wait_for("__pt.cutsceneActive()", timeout=8.0)
    record("mug: Einschub schliesst sich von selbst, Ausgangs-Panel folgt", bool(active), "active=%s" % active)
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.4)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    won = await cdp.eval("State.s.stats.fightsWon", await_promise=False)
    bonus = await cdp.eval("__pt.lastMug && __pt.lastMug.bonus", await_promise=False)
    record("mug: Kampf mit Staerke 20 gewonnen, Brieftasche 50-150, Staerke 21, Timing-Bonus 0.1 gemeldet", bal == 1050 and st == 21 and won == 1 and bonus == 0.1, "bal=%s st=%s won=%s bonus=%s" % (bal, st, won, bonus))
```

Den Flucht-Abschnitt ersetzen – alt:

```python
    await cdp.eval("window.__origRandom = Math.random; Math.random = () => 0.99; 0", await_promise=False)
    await cdp.advance_cutscene(label_hint="Wegrennen")
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    await asyncio.sleep(0.6)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    record("mug: Flucht erwischt (RNG gestubbt) kostet 300, Staerke bleibt 0", bal == 700 and st == 0, "bal=%s st=%s" % (bal, st))
```

neu:

```python
    await cdp.eval("window.__origRandom = Math.random; Math.random = () => 0.99; 0", await_promise=False)
    await cdp.advance_cutscene(label_hint="Wegrennen")
    # Flucht-Einschub ohne Tipp (Bonus 0): laufende Kulisse, Raeuber holt auf, Abzweigung, dann erwischt
    running = await cdp.wait_for("MugAction.running && EgoStage.moving", timeout=4.0)
    record("mug: Flucht-Einschub mit laufender Kulisse", bool(running), "running=%s" % running)
    await cdp.screenshot("mug-flee.png")
    await cdp.wait_for("__pt.cutsceneActive()", timeout=8.0)
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.4)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    bonus = await cdp.eval("__pt.lastMug && __pt.lastMug.bonus", await_promise=False)
    record("mug: Flucht erwischt (RNG gestubbt) kostet 300, Staerke bleibt 0, Bonus 0 ohne Tipp", bal == 700 and st == 0 and bonus == 0, "bal=%s st=%s bonus=%s" % (bal, st, bonus))
```

- [ ] **Step 3: Tag-10-Duell (Story 1)**

In `scenario_story_schuld_days` (Abschnitt „Tag 10 … erzwungenes Duell", hinter `if duel_seen:` und dem Kommentar zu `igor.first`) die Klick-Schleife ersetzen – alt:

```python
        for _ in range(30):
            in_duel = await cdp.eval("typeof Russian !== 'undefined' && Russian.inDuel", await_promise=False)
            if not in_duel:
                break
            active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            if active:
                await cdp.advance_cutscene(max_steps=5)
            else:
                await cdp.click("#btnTrigger")
            await asyncio.sleep(0.4)
```

neu:

```python
        stage_ok = await cdp.wait_for("EgoStage.mounted && EgoStage.set === 'hinterzimmer' && !!document.querySelector('#rrStage .duel-foe svg.part') && EgoStage.cyl != null", timeout=3.0)
        record("duell: Ego-Buehne Hinterzimmer mit Igor und Trommel", bool(stage_ok), "stage_ok=%s" % stage_ok)
        for _ in range(60):
            in_duel = await cdp.eval("typeof Russian !== 'undefined' && Russian.inDuel", await_promise=False)
            if not in_duel:
                break
            active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            if active:
                await cdp.advance_cutscene(max_steps=5)
            else:
                busy = await cdp.eval("Russian.busy", await_promise=False)
                if not busy:
                    await cdp.click("#btnTrigger")
            await asyncio.sleep(0.4)
```

- [ ] **Step 4: Playtest laufen lassen**

Erst prüfen: `pgrep -f "playtest-story|remote-debugging-port=9335"` muss leer sein.
Run: `python3 -u tests/playtest-story.py 2>&1 | grep -E "^FAIL|FEHLGESCHLAGEN|ERRORS|mug:|duell:"`
Expected: alle `mug:`- und `duell:`-Zeilen `OK` (vier neue Checks: Kampf-Einschub, Einschub schließt, Flucht-Einschub, Ego-Bühne Hinterzimmer), `ERRORS 0`, keine Fehlschläge. Screenshots `/tmp/k37story/mug-fight.png` (Räuber im Ring, Faust unten rechts, „TREFFER!") und `mug-flee.png` (laufende Kulisse) kurz ansehen.

- [ ] **Step 5: Trace-Szenarien**

In `tests/perf-trace.py` in `SCENARIOS` direkt **vor** `("Taxi fahren", "?story", 4,` einfügen:

```python
    ("Ueberfall Kampf", "?screen=hub", 4,
     "Math.random = () => 0; MugAction.brawl(Mugging.TYPES.junkie, 0.5); setTimeout(() => MugAction.tap(), 1500)", None),
    ("Russisch Roulette", "?screen=russian", 4,
     "State.s.flags.igor = true; State.s.balance = 1000; Rules.rrCylinder = () => [false, false, false, false, false, true]; Russian.start().then(() => Russian.pull())", None),
```

Run: `python3 tests/perf-trace.py "Ueberfall Kampf" "Russisch Roulette" "Duell"` und dasselbe mit `--mobile`.
Expected (Prototyp, Desktop): „Ueberfall Kampf" ≈ 4 Paint/s, ≈ 48 Raster-ms über 4 s, Layout ≈ 1,5/s; „Russisch Roulette" ≈ 25 Paint/s und ≈ 11 Layout/s, meistgemalt `header#wallet` – das ist der Geldzähler nach dem Einsatzabzug und auf `main` identisch (24 Paint/s, 10 Layout/s, `header#wallet ×37`); die Raster-Zeit sinkt gegenüber `main` (≈ 52 ms statt ≈ 80 ms je 4 s), weil das alte Emoji-Panel (`div.face ×6`) entfällt. Werte notieren (Desktop/Mobil) für die README.

- [ ] **Step 6: README**

Hinter dem Abschnitt „### Schießerei" einen Abschnitt einfügen:

```markdown
### Überfall und Russisches Roulette auf der Ego-Bühne

Die Ego-Bühne der Schießerei (`EgoStage`, Alias `DuelStage`) trägt auch die beiden anderen Sonderszenen. **Überfall:** nach „Kämpfen" oder „Wegrennen" öffnet sich ein Vollbild-Einschub in der Gasse – beim Kampf holt der Räuber aus und ein Ring zieht sich um ihn zusammen, beim Wegrennen läuft die Kulisse, der Räuber holt auf, bis rechts die Abzweigung auftaucht. Ein Tipp (Bühne, Leertaste, Enter) im goldenen Fenster des Rings (die letzten 250 von 900 ms) gibt +10 Prozentpunkte auf die Kampf- bzw. Fluchtchance (Deckel 95 %, `GangRules.timingBonus`/`chanceWithBonus`); der Ausgang wird wie bisher gewürfelt, nur der erste Tipp zählt, es gibt keinen Malus. Gewonnen: Faust ruckt, Einschlag, Räuber fällt in Zeitlupe; verloren: seine Faust auf die Kamera, roter Rand, „Du liegst"; entkommen: er schrumpft ins Dunkel; erwischt: Kragengriff. Danach die bekannten Text-Panels, „Zahlen" bleibt reiner Text. **Russisches Roulette:** Ego-Sicht im Hinterzimmer, Igor gegenüber am Tisch, Trommel-Nahaufnahme unten links. In deinem Zug hebt sich der Revolver und dreht in die Mündungssicht; Abzug per Knopf, Tipp auf die Bühne oder Leertaste/Enter. Klick: Kammer grau, der Revolver gleitet zu Igor, der ihn an die Schläfe hebt – Klick: Erleichterung, Knall: Mündungsfeuer, Blut, Fall in Zeitlupe. Dein Knall: Blitz, Ruck, roter Rand, Tropfen, dann der Doc wie bisher. Regeln, Einsatz und Abrechnung sind unverändert. `prefers-reduced-motion`: Ring als Leiste mit Marker, Kulisse steht, Trommel springt, Revolver direkt in Mündungssicht, kein Blitz/Ruck.
```

Im Abschnitt „## Tests" hinter dem Absatz „Die Schießerei bringt eigene Tests mit …" ergänzen:

```markdown
Stufe 3 (Überfall/Roulette): `run-selftest.mjs` prüft `GangRules.timingBonus` (vor/im/nach dem Fenster, ohne Tipp, eigenes Fenster) und `chanceWithBonus` (Deckel 0,95) sowie die Posen `windup/temple/relief`. `dom-selftest.sh` ergänzt „EgoStage: Hand-Varianten, Ring, laufende Kulisse, Trommel, …", „Überfall auf der Ego-Bühne: Kampf mit Timing-Treffer (Bonus 0,10), …" und „Russisch Roulette in Ego-Sicht: …" – Headless-Chrome liefert unter `virtual-time-budget` kaum rAF-Frames, darum takten diese Tests die Bühnen-Uhr von Hand (`EgoStage.loop(last + 50)`); Stand 2026-09-21: 323 node-seitig, 371 im DOM, je 0 fehlgeschlagen. `playtest-story.py` tippt den Überfall-Ring über `__pt.egoTap()` und liest den Bonus aus `__pt.lastMug`.
```

In die Trace-Tabelle (oder als eigenen Absatz darunter) die gemessenen Werte für „Ueberfall Kampf" und „Russisch Roulette" (Desktop/Mobil) eintragen, mit dem Hinweis, dass beim Roulette der Geldzähler (`header#wallet`) die Paints dominiert – auf `main` gleich – und die Raster-Zeit gegenüber dem alten Emoji-Panel sinkt.

- [ ] **Step 7: Spec-Notiz**

Am Ende der Spec anfügen:

```markdown
## Umsetzungsnotiz

`chanceWithBonus` liegt neben `timingBonus` in `GangRules` (nicht in `Mugging`), damit der Node-Selbsttest es ohne DOM prüfen kann; `MugAction.brawl/chase` bekommen die Grundchance als zweites Argument, `Mugging.run` rechnet sie wie bisher aus. Die Trommel dreht wie vorher am Anfang jedes Abzugs auf die aktuelle Kammer. Igor trägt die Pistole des Rigs nur in seinem Zug (`EgoStage.foeGun`, Klasse `unarmed`), der Räuber nie; der Zähler `#duelCount` bleibt bei einem einzelnen Gegner leer. Am Ende eines Duells setzt `setTurn(null)` keine Pose mehr – sonst stünde ein gefallener Igor wieder auf. Headless-Tests takten die Bühnen-Uhr per `EgoStage.loop(last + 50)`, weil `virtual-time-budget` kaum rAF-Frames liefert.
```

- [ ] **Step 8: Abschluss-Checks**

```bash
node tests/run-selftest.mjs 2>&1 | tail -1 && tests/dom-selftest.sh
python3 -u tests/playtest-story.py 2>&1 | grep -E "FEHLGESCHLAGEN|ERRORS"
```

Expected: Node/DOM grün; Playtest `ERRORS 0`, keine Fehlschläge.

- [ ] **Step 9: Commit**

```bash
git add tests/playtest-story.py tests/perf-trace.py README.md docs/superpowers/specs/2026-09-21-ego-buehne-ueberfall-roulette-design.md
git commit -m "test(ego): Playtest tippt den Überfall-Ring, Trace-Szenarien Überfall/Roulette, Doku Stufe 3

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

Danach: nicht mergen, nicht pushen – Freigabe des Auftraggebers einholen.
