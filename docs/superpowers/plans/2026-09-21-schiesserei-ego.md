# Schießerei in Ego-Sicht (Stufe 2) – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Schießerei wird eine Action-Sequenz in Ego-Sicht auf einer Canvas-Bühne (Gegner aus dem Cutscene-Rig, eigene Waffe, Mündungsfeuer, Zeitlupe, Blut) mit Zielen als Mechanik – Fehlschüsse kosten Zeit, der Gegner schießt von sich aus; Balance und Story-Anbindung bleiben.

**Architecture:** `GangRules` bekommt reine Funktionen (`hitTest`, `foeTime`, `foeFiresAt`, `resolveRound`); ein neues, rein darstellendes Modul `DuelStage` (Welt-Canvas mit vorgerenderter Kulisse, DOM-Gegnerfigur aus `CsCast.figureHtml`, Effekt-Canvas mit Partikel-Pool, Waffen-SVG, Anzeige) ersetzt das alte Emoji-Panel; `Shootout` behält seine Schnittstelle (`start/ready/tap/resolve/finish/leave/onKey/pending/forced`, `fight:done`/`fight:leave`) und bekommt `shoot(ev)` (Zeiger → Trefferprüfung), Tipp-Liste und Gegner-Timer. `tap()` ohne Argument bleibt „Schuss mit Treffer" (Tastatur, Playtest, bestehender DOM-Test).

**Tech Stack:** Vanilla JS/CSS, Canvas 2D, Inline-SVG in einer Datei; Node-Selbsttest (`node tests/run-selftest.mjs`), Headless-Chrome-Selbsttest (`tests/dom-selftest.sh`), CDP-Playtest (`python3 tests/playtest-story.py`), Trace (`python3 tests/perf-trace.py`).

**Spec:** `docs/superpowers/specs/2026-09-21-schiesserei-ego-design.md`

Die Code-Blöcke dieses Plans wurden in einem Wegwerf-Prototyp gegen den aktuellen `main` verifiziert (Node 315/315, DOM 357/357, Story-Playtest grün) – wörtlich übernehmen.

## Global Constraints

- Eine Datei `keller37.html`, keine Bilddateien, keine externen Abhängigkeiten.
- `Shootout.start(cfg)`, `Shootout.pending`, `Shootout.forced`, `Shootout.leave()`, `Shootout.tap()` (ohne Argument = Schuss mit Treffer), Events `fight:done { kind, won, rounds[, aborted] }` und `fight:leave { kind, won[, aborted] }` bleiben; `Story.forceFight` und die Story-Auswertung werden nicht angefasst.
- Balance-Zahlen unverändert: `GangRules.FOES`, `GangRules.WEAPONS`, `GangRules.DRAW_WAIT`, `duelRound` (liefert weiter dieselben Werte).
- Bewegung von DOM-Elementen nur über `transform`/`opacity`; jedes `@keyframes cs*`/`duel*` animiert nur transform/opacity. Canvas zeichnet pro Frame nur, was sich bewegt; Kulisse vorgerendert.
- IDs `#duelStage`, `#duelStatus`, `#btnDuelStart`, `#btnDuelDone`, `#duelCount`, `#duelFoeName` bleiben (Tests/Playtest lesen sie).
- Deutsche Spieltexte, deutsche Kommentare wie im Rest der Datei.
- Commit-Trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`. Kein Push, kein Merge nach main ohne ausdrückliche Freigabe.
- `main` bewegt sich parallel (andere Instanz): vor Task 1 auf den aktuellen `main` aufsetzen.

---

## Dateistruktur

| Stelle | Inhalt |
|---|---|
| `keller37.html` Block `gang-rules` | `hitTest`, `foeTime`, `foeFiresAt`, `resolveRound`, `HIT_MARGIN`; `duelRound` nutzt `foeTime` |
| `keller37.html` Block `cutscene-cast` | Looks `laeufer`, `junge`; Option `gun: true` (Pistole im rechten Arm-Teil) |
| `keller37.html` Block `cutscene-director` | `POSES` + `draw`, `hit` |
| `keller37.html` CSS (`.duel-panel` … `@media … .duel-stage`) | wird komplett ersetzt: Bühne, Ebenen, Waffe, Anzeige, Posen `draw`/`hit`, Keyframes `duelRecoil`/`csHit` |
| `keller37.html` `<template id="tpl-shootout">` | leere Bühne `#duelStage` + Status + Knöpfe |
| `keller37.html` Block `game-shootout` | neues Objekt `DuelStage` vor `Shootout`; `Shootout` ersetzt (bis `</script>`) |
| `keller37.html` Block `sfx` | `ricochet` |
| `keller37.html` Block `selftest` | Node-Tests hinter dem Test `GangRules.duelRound: …`; DOM-Tests vor `const pseudoAnim = …`; bestehender Test `Shootout: Fehlschuss vor dem Blitz …` wartet `NEXT_MS` |
| `tests/playtest-story.py` | Helfer `__pt.duelShoot()`, ersetzt `Shootout.tap()` im Story-3-Tutorial |
| `tests/perf-trace.py`, `README.md`, Spec | Trace-Szenario „Duell", Doku |

Fundstellen per `grep -n`: `'duelRound({ reaction'`, `'  drawWait(rng) {'`, `"    kowalski:    { name: 'Kowalski',"`, `'const arm = (side) =>'`, `'  POSES: ['`, `'.duel-panel { align-items: stretch; }'`, `'<template id="tpl-shootout">'`, `'const Shootout = {'`, `'    gunshot() {'`, `"T.test('GangRules.duelRound"`, `'const pseudoAnim = '`, `'nextTimer (900 ms)'`.

---

### Task 1: Regeln – Trefferprüfung, Gegnerzeit, Rundenauflösung

**Files:**
- Modify: `keller37.html` Block `gang-rules` (Objekt `GangRules`)
- Modify: `keller37.html` Block `selftest` (hinter dem Test `GangRules.duelRound: …`)

**Interfaces:**
- Produces: `GangRules.HIT_MARGIN = { mouse: 24, touch: 32 }`; `GangRules.hitTest(tap {x,y}, box {left,top,width,height}, margin = 24) → boolean`; `GangRules.foeTime(foe, rng) → number` (ein rng-Aufruf); `GangRules.foeFiresAt(foeTime, bonus = 0) → number`; `GangRules.resolveRound({ taps: [{ t, hit }], foeTime, bonus = 0 }) → { won, misfire, foeTime, you, misses }`. `duelRound` unverändert im Verhalten.

- [ ] **Step 1: Fehlschlagende Tests schreiben**

Direkt hinter dem bestehenden Test `T.test('GangRules.duelRound: …')` (er endet mit `});`) einfügen:

```js
T.test('GangRules.hitTest: innen, am Rand, außen, Touch-Rand', () => {
  const box = { left: 100, top: 50, width: 80, height: 160 };
  T.eq(GangRules.hitTest({ x: 140, y: 120 }, box), true, 'innen');
  T.eq(GangRules.hitTest({ x: 80, y: 120 }, box, 24), true, 'im Rand (24)');
  T.eq(GangRules.hitTest({ x: 70, y: 120 }, box, 24), false, 'außerhalb des Rands');
  T.eq(GangRules.hitTest({ x: 70, y: 120 }, box, 32), true, 'Touch-Rand 32');
  T.eq(GangRules.hitTest({ x: 140, y: 240 }, box, 24), false, 'unterhalb');
  T.eq(GangRules.HIT_MARGIN, { mouse: 24, touch: 32 });
});
T.test('GangRules.foeTime/foeFiresAt: base ± spread, ein rng-Aufruf; Gegner schießt bei foeTime + bonus', () => {
  const foe = { base: 320, spread: 60 };
  let calls = 0; const counting = () => { calls++; return 0.5; };
  T.eq(GangRules.foeTime(foe, counting), 320); T.eq(calls, 1);
  T.eq(GangRules.foeTime(foe, seq(0)), 260); T.eq(GangRules.foeTime(foe, seq(1)), 380);
  T.eq(GangRules.foeFiresAt(320, 100), 420); T.eq(GangRules.foeFiresAt(320), 320);
});
T.test('GangRules.resolveRound: Fehlschuss vor dem Signal, erster Treffer zählt, misses, Bonus, kein Treffer', () => {
  T.eq(GangRules.resolveRound({ taps: [{ t: -1, hit: true }], foeTime: 320, bonus: 100 }), { won: false, misfire: true, foeTime: 320, you: null, misses: 0 });
  T.eq(GangRules.resolveRound({ taps: [{ t: 250, hit: true }], foeTime: 320, bonus: 0 }), { won: true, misfire: false, foeTime: 320, you: 250, misses: 0 });
  T.eq(GangRules.resolveRound({ taps: [{ t: 120, hit: false }, { t: 260, hit: false }, { t: 380, hit: true }], foeTime: 320, bonus: 100 }), { won: true, misfire: false, foeTime: 320, you: 280, misses: 2 }, 'daneben kostet nur Zeit');
  T.eq(GangRules.resolveRound({ taps: [{ t: 120, hit: false }], foeTime: 320, bonus: 0 }), { won: false, misfire: false, foeTime: 320, you: null, misses: 1 }, 'kein Treffer: der Gegner war schneller');
  T.eq(GangRules.resolveRound({ taps: [], foeTime: 320, bonus: 0 }), { won: false, misfire: false, foeTime: 320, you: null, misses: 0 });
  T.eq(GangRules.resolveRound({ taps: [{ t: 50, hit: true }, { t: 900, hit: true }], foeTime: 320, bonus: 300 }).you, 0, 'Bonus zieht ab, nie unter 0; spätere Tipps egal');
  T.eq(GangRules.resolveRound({ taps: [{ t: 100, hit: false }, { t: -5, hit: true }], foeTime: 320 }).misfire, true, 'ein negativer Tipp irgendwo in der Liste = Fehlschuss');
});
T.test('GangRules.resolveRound ≡ duelRound bei genau einem Treffer (Balance-Invariante)', () => {
  const foe = GangRules.FOES.junge;
  for (const [t, bonus, r] of [[250, 0, 0.5], [90, 300, 0.1], [400, 100, 0.9], [330, 0, 0.5]]) {
    const old = GangRules.duelRound({ reaction: t, bonus, foe, rng: seq(r) });
    const neu = GangRules.resolveRound({ taps: [{ t, hit: true }], foeTime: GangRules.foeTime(foe, seq(r)), bonus });
    T.eq([neu.won, neu.you, neu.foeTime, neu.misfire], [old.won, old.you, old.foeTime, old.misfire], `t=${t} bonus=${bonus}`);
  }
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: 4 fehlgeschlagen (`GangRules.hitTest is not a function` usw.).

- [ ] **Step 3: Regeln einfügen**

Im Objekt `GangRules` direkt vor der Zeile `  drawWait(rng) {` einfügen:

```js
  /* ---- Duell in Ego-Sicht: Zielen, Fehlschüsse, Gegnerschuss ---- */
  HIT_MARGIN: { mouse: 24, touch: 32 },
  /* Tipp trifft, wenn er in der um margin vergrößerten Figuren-Box liegt (Bühnenkoordinaten) */
  hitTest(tap, box, margin = 24) {
    return tap.x >= box.left - margin && tap.x <= box.left + box.width + margin && tap.y >= box.top - margin && tap.y <= box.top + box.height + margin;
  },
  /* Gegnerzeit für eine Runde: base ± spread, gleichverteilt, genau ein rng-Aufruf */
  foeTime(foe, rng) { return Math.round(foe.base + (rng() * 2 - 1) * foe.spread); },
  /* Zeitpunkt (ms nach dem Signal), zu dem der Gegner schießt, wenn bis dahin kein Treffer kam – genau der Punkt, ab dem duelRound verliert */
  foeFiresAt(foeTime, bonus = 0) { return foeTime + bonus; },
  /* taps: [{ t (ms relativ zum Signal, < 0 = vor dem Signal), hit }]. Der erste Tipp vor dem Signal ist ein Fehlschuss (Runde verloren),
     sonst entscheidet der erste treffende Tipp; daneben getippte Schüsse zählen als misses und kosten nur Zeit. */
  resolveRound({ taps, foeTime, bonus = 0 }) {
    let misses = 0;
    for (const tap of taps) {
      if (tap.t < 0) return { won: false, misfire: true, foeTime, you: null, misses };
      if (!tap.hit) { misses++; continue; }
      const you = Math.max(0, tap.t - bonus);
      return { won: you < foeTime, misfire: false, foeTime, you, misses };
    }
    return { won: false, misfire: false, foeTime, you: null, misses };
  },
```

Dann in `duelRound` die Zeile `    const foeTime = Math.round(foe.base + (rng() * 2 - 1) * foe.spread);` ersetzen durch `    const foeTime = GangRules.foeTime(foe, rng);`.

- [ ] **Step 4: Tests laufen lassen**

Run: `node tests/run-selftest.mjs`
Expected: `0 fehlgeschlagen`, vier Tests mehr als vorher (der bestehende `duelRound`-Test bleibt grün – gleiche Werte, ein rng-Aufruf).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(duell): Regeln fürs Zielen – hitTest, foeTime, foeFiresAt, resolveRound (Fehlschüsse kosten Zeit, Gegner schießt von sich aus)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Gegner-Looks, Pistole, Posen `draw`/`hit`

**Files:**
- Modify: `keller37.html` Block `cutscene-cast` (`CsCast.CAST`, `figureHtml` → `arm()`)
- Modify: `keller37.html` Block `cutscene-director` (`CsDirector.POSES`)
- Modify: `keller37.html` Block `selftest` (hinter den Tests aus Task 1)

**Interfaces:**
- Produces: `CsCast.CAST.laeufer`, `CsCast.CAST.junge` (Namen wie `GangRules.FOES`); `CsCast.figureHtml(who, { gun: true })` zeichnet `<path class="pistole" …>` im Teil `armR`; `CsDirector.POSES` enthält `draw`, `hit` (die CSS-Posen kommen in Task 3 mit dem Duell-CSS).

- [ ] **Step 1: Fehlschlagende Tests schreiben**

Hinter den Tests aus Task 1 einfügen:

```js
if (typeof CsCast !== 'undefined') {
  T.test('CsCast: Looks für Bahnhof-Läufer und -Junge, gun: true zeichnet die Pistole in die rechte Hand', () => {
    for (const id of ['laeufer', 'junge']) { T.ok(CsCast.CAST[id] && CsCast.CAST[id].look, `Look ${id}`); T.eq(CsCast.CAST[id].name, GangRules.FOES[id].name, `${id}: Name wie in FOES`); }
    T.ok(CsCast.figureHtml('junge', { gun: true }).includes('class="pistole"'), 'Pistole');
    T.ok(!CsCast.figureHtml('junge').includes('class="pistole"'), 'ohne gun keine Pistole');
    const html = CsCast.figureHtml('anabi', { gun: true });
    T.ok(html.indexOf('class="pistole"') > html.indexOf('class="part armR"') && html.indexOf('class="pistole"') < html.indexOf('class="part head"'), 'Pistole liegt im rechten Arm-Teil');
  });
  T.test('CsDirector.POSES kennt draw und hit', () => { T.ok(CsDirector.POSES.includes('draw') && CsDirector.POSES.includes('hit')); });
}
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: 2 fehlgeschlagen (`Look laeufer`, `draw`/`hit` fehlen).

- [ ] **Step 3: Looks und Pistole einfügen**

In `CsCast.CAST` direkt vor der Zeile `    kowalski:    { name: 'Kowalski',` einfügen:

```js
    laeufer:     { name: 'Bahnhof-Läufer',   emoji: '🏃', color: 'var(--neon-red)',   look: { skin: '#e8c8a8', cloth: '#2a5a3a', accent: '#f2f2f2', hair: 'kurz',   hairColor: '#3a2414', hat: 'muetze', hatColor: '#222', extra: [],           build: 'schmal' } },
    junge:       { name: 'Bahnhof-Junge',    emoji: '🧢', color: 'var(--neon-red)',   look: { skin: '#e8b48a', cloth: '#3a3a3a', accent: '#ff7a1a', hair: 'kurz',   hairColor: '#111',    hat: 'cap', hatColor: '#1e3a5c', extra: [],          build: 'klein' } },
```

In `figureHtml` im Helfer `arm(side)` die Zeile mit der Krücke ergänzen – aus

```js
        ${side === 'L' && opts.hurt === 'kruecke' ? `<path d="M${cx - 14} 118 L${cx - 14} 172" stroke="#8a6a3a" stroke-width="4"/><path d="M${cx - 22} 118 L${cx - 6} 118" stroke="#8a6a3a" stroke-width="4"/>` : ''}`);
```

wird

```js
        ${side === 'L' && opts.hurt === 'kruecke' ? `<path d="M${cx - 14} 118 L${cx - 14} 172" stroke="#8a6a3a" stroke-width="4"/><path d="M${cx - 22} 118 L${cx - 6} 118" stroke="#8a6a3a" stroke-width="4"/>` : ''}
        ${side === 'R' && opts.gun ? `<path class="pistole" d="M${cx - 4} 126 h18 v6 h-10 v9 h-8z" fill="#1a1a1a"/>` : ''}`);
```

In `CsDirector` die Zeile `  POSES: ['idle', 'talk', 'point', 'arms-crossed', 'hands-up', 'walk', 'down', 'flinch'],` ersetzen durch `  POSES: ['idle', 'talk', 'point', 'arms-crossed', 'hands-up', 'walk', 'down', 'flinch', 'draw', 'hit'],`.

- [ ] **Step 4: Tests laufen lassen**

Run: `node tests/run-selftest.mjs && tests/dom-selftest.sh`
Expected: Node `0 fehlgeschlagen`; DOM `failed=0` (die Regie-Validierung und der Cast-Test „alle Figuren haben einen Look" bleiben grün – die neuen Looks erfüllen sie).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(cast): Looks für Bahnhof-Läufer und -Junge, Pistole in der Hand, Posen draw und hit

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `DuelStage` – Canvas-Bühne, Figur, Waffe, Effekte; CSS; Template; Sound

**Files:**
- Modify: `keller37.html` CSS: den Block von `.duel-panel { align-items: stretch; }` bis einschließlich der Zeile `@media (max-width: 760px) { .duel-stage { height: 240px; } .duel-fighter { font-size: 3rem; } }` ersetzen
- Modify: `keller37.html` `<template id="tpl-shootout">` ersetzen
- Modify: `keller37.html` Block `game-shootout`: `DuelStage` direkt vor `const Shootout = {` einfügen
- Modify: `keller37.html` Block `sfx`: `ricochet`
- Modify: `keller37.html` Block `selftest`: DOM-Test vor `const pseudoAnim = …`

**Interfaces:**
- Consumes: `CsCast.figureHtml(id, { mood, gun })`, `h`, `qs`, `qsa`.
- Produces: `DuelStage` mit `SETS` (`gasse`, `bahnhof`, `keller`), `SET_BY_KIND` (`tutorial→bahnhof, hinterhalt→gasse, finale→keller, dev→gasse`), `mount(root, { set, weapon, reduced })`, `unmount()`, `enter(foeId, idx, n, foeName)`, `signal()`, `foeBox() → {left,top,width,height}`, `shot({ x, y, hit, early })`, `foeDown()`, `foeShoots()`, `flash(text, ms)`, `setTimeScale(k)`; Zustand `mounted`, `raf`, `t`, `timeScale`, `flashUntil`, `redUntil`, `shakeUntil`, `parts`, `stains`, `set`, `reduced`. Template-IDs `#duelStage`, `#duelStatus`, `#btnDuelStart`, `#btnDuelDone`; Anzeige-IDs `#duelFoeName`, `#duelCount` (werden von `DuelStage.mount` erzeugt). Das alte Shootout läuft in dieser Task noch mit dem alten Template-Inhalt NICHT mehr – deshalb wird der bestehende DOM-Test `Shootout: Fehlschuss vor dem Blitz …` erst in Task 4 wieder grün; in Task 3 darf genau dieser eine Test rot sein (Zwischenstand, im Commit-Text vermerkt).

- [ ] **Step 1: Fehlschlagenden DOM-Test schreiben**

Vor `  const pseudoAnim = (el, pseudo) => getComputedStyle(el, pseudo).animationName;` einfügen:

```js
  T.test('DuelStage: Canvas, Gegnerfigur, Waffe; enter/signal/shot/foeDown/foeShoots/flash/unmount; reduced-motion', async () => {
    const host = h('div', { class: 'duel-stage', style: 'width:600px;height:400px;position:relative' }); document.body.append(host);
    try {
      DuelStage.mount(host, { set: 'bahnhof', weapon: 3, reduced: false });
      T.eq([qsa('canvas', host).length, DuelStage.set, DuelStage.mounted, DuelStage.W, DuelStage.H], [2, 'bahnhof', true, 600, 400]);
      T.ok(qs('.duel-gun svg path[fill="#8a6a1a"]', host), 'Stufe 3: „Die Goldene“'); T.ok(DuelStage.raf > 0, 'Schleife läuft');
      DuelStage.enter('junge', 0, 3, 'Bahnhof-Junge');
      T.eq([qs('#duelCount', host).textContent, qs('#duelFoeName', host).textContent, qsa('.duel-foe svg.part', host).length, qs('.duel-foe', host).dataset.pose, qs('.duel-foe', host).style.getPropertyValue('--s')], ['1 / 3', 'Bahnhof-Junge', 8, 'idle', '1']);
      T.ok(qs('.duel-foe .pistole', host), 'Gegner mit Pistole');
      DuelStage.signal(); T.eq(qs('.duel-foe', host).dataset.pose, 'draw'); T.ok(DuelStage.flashUntil > DuelStage.t, 'Blitz');
      const before = DuelStage.parts.length; DuelStage.shot({ x: 50, y: 50, hit: false });
      T.ok(DuelStage.parts.length > before && DuelStage.parts.some((p) => p.kind === 'spark') && DuelStage.parts.some((p) => p.kind === 'trace'), 'daneben: Funken + Spur'); T.ok(qs('.duel-gun', host).classList.contains('recoil'), 'Rückstoß');
      DuelStage.shot({ hit: true }); T.ok(DuelStage.parts.some((p) => p.kind === 'blood'), 'Treffer: Blut');
      DuelStage.foeDown(); T.eq([qs('.duel-foe', host).dataset.pose, DuelStage.timeScale, qs('.duel-foe', host).style.getPropertyValue('--fall')], ['hit', 0.3, '1.2s'], 'Zucken + Zeitlupe');
      await wait(300); T.eq([qs('.duel-foe', host).dataset.pose, DuelStage.stains.length], ['down', 1], 'Fall + Fleck');
      DuelStage.foeShoots(); T.ok(DuelStage.redUntil > DuelStage.t && DuelStage.shakeUntil > DuelStage.t && DuelStage.parts.some((p) => p.kind === 'drop'), 'Gegnerschuss: roter Rand, Ruck, Tropfen');
      DuelStage.flash('ZIEH!'); T.eq([qs('.duel-flash', host).textContent, qs('.duel-flash', host).classList.contains('on')], ['ZIEH!', true]);
      T.eq(DuelStage.SET_BY_KIND, { tutorial: 'bahnhof', hinterhalt: 'gasse', finale: 'keller', dev: 'gasse' });
      DuelStage.unmount(); T.eq([DuelStage.mounted, DuelStage.raf, host.children.length], [false, 0, 0], 'abgebaut');
      DuelStage.mount(host, { set: 'nirgendwo', weapon: 0, reduced: true }); T.eq(DuelStage.set, 'gasse', 'unbekannte Kulisse → gasse');
      DuelStage.enter('anabi', 0, 1, 'Anabi Stash'); DuelStage.signal(); T.eq(DuelStage.flashUntil, 0, 'reduced: kein Blitz');
      DuelStage.foeDown(); T.eq(DuelStage.timeScale, 1, 'reduced: keine Zeitlupe'); DuelStage.foeShoots(); T.eq(DuelStage.shakeUntil, 0, 'reduced: kein Ruck');
    } finally { DuelStage.unmount(); host.remove(); }
  });
```

- [ ] **Step 2: DOM-Suite laufen lassen – muss fehlschlagen**

Run: `tests/dom-selftest.sh`
Expected: `failed=` ≥ 1 (`DuelStage is not defined`).

- [ ] **Step 3: CSS ersetzen**

Den Block von `.duel-panel { align-items: stretch; }` bis einschließlich `@media (max-width: 760px) { .duel-stage { height: 240px; } .duel-fighter { font-size: 3rem; } }` ersetzen durch:

```css
.duel-panel { align-items: stretch; }
/* Ego-Sicht: Welt-Canvas hinten, Gegnerfigur, Effekt-Canvas, eigene Waffe, Anzeige – alles absolut in der Bühne */
.duel-stage { position: relative; width: 100%; height: min(72vh, 720px); min-height: 360px; border-radius: 10px; background: #000; overflow: hidden; touch-action: none; user-select: none; cursor: crosshair; contain: paint; }
.duel-stage canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
.duel-world { z-index: 0; }
.duel-fx { z-index: 3; pointer-events: none; }
.duel-stage .cs-fig.duel-foe { left: 50%; bottom: 34%; height: 46%; z-index: 1; --x: 0px; --s: 1; transform: translateX(-50%) scale(var(--s)); transform-origin: 50% 100%; transition: transform .8s ease-out; }
.duel-gun { position: absolute; right: 0; bottom: 0; width: 38%; max-width: 360px; aspect-ratio: 200 / 160; z-index: 4; pointer-events: none; transform: translateY(100%); transition: transform .5s ease-out; filter: drop-shadow(0 0 12px rgba(0,0,0,.8)); }
.duel-gun.up { transform: translateY(0); }
.duel-gun.recoil { animation: duelRecoil .18s ease-out both; }
.duel-gun svg { width: 100%; height: 100%; display: block; }
.duel-tag { position: absolute; left: 12px; top: 10px; z-index: 5; display: flex; gap: 10px; font-family: var(--font-mono); font-size: .8rem; color: rgba(255,255,255,.8); background: rgba(0,0,0,.45); padding: 4px 10px; border-radius: 4px; pointer-events: none; }
.duel-flash { position: absolute; left: 50%; top: 30%; transform: translate(-50%, -50%); z-index: 6; font-family: var(--font-display); font-size: 3.4rem; letter-spacing: .2em; color: #fff; text-shadow: 0 0 20px var(--neon-red), 0 0 40px var(--neon-red); opacity: 0; pointer-events: none; }
.duel-flash.on { animation: stampIn .15s both; opacity: 1; }
.duel-foe[data-pose="idle"] .armR { animation: duelTwitch 2.6s ease-in-out infinite; }   /* die Hand zuckt zur Waffe */
.cs-fig[data-pose="draw"] .armR { transform: rotate(-100deg); transition-duration: .1s; }
.cs-fig[data-pose="hit"] .cs-body { animation: csHit .35s ease both; }
@keyframes duelTwitch { 0%, 88%, 100% { transform: rotate(0); } 92% { transform: rotate(-14deg); } 96% { transform: rotate(-4deg); } }
@keyframes duelRecoil { 0% { transform: translate(0, 0) rotate(0); } 30% { transform: translate(6px, 18px) rotate(-6deg); } 100% { transform: translate(0, 0) rotate(0); } }
@keyframes csHit { 0% { transform: translateY(0) rotate(0); } 30% { transform: translateY(-8px) rotate(4deg); } 100% { transform: translateY(0) rotate(-2deg); } }
@media (max-width: 760px) { .duel-stage { height: 62vh; min-height: 380px; } .duel-stage .cs-fig.duel-foe { height: 44%; bottom: 36%; } .duel-gun { width: 46%; } }
@media (orientation: landscape) and (max-height: 500px) { .duel-stage { height: 80vh; min-height: 280px; } .duel-stage .cs-fig.duel-foe { height: 55%; bottom: 30%; } }
@media (prefers-reduced-motion: reduce) { .duel-stage .cs-fig.duel-foe, .duel-gun { transition: none; } .duel-gun.recoil, .duel-flash.on, .duel-foe[data-pose="idle"] .armR { animation: none; } }
```

- [ ] **Step 4: Template ersetzen**

```html
<template id="tpl-shootout">
  <div class="panel duel-panel">
    <div class="duel-stage" id="duelStage"></div>
    <div class="status" id="duelStatus">Warte, bis er zieht – dann auf ihn tippen (oder Leertaste). Zu früh ist ein Fehlschuss.</div>
    <div class="bet-bar">
      <button class="btn solid" id="btnDuelStart">Bereit</button>
      <button class="btn ghost hidden" id="btnDuelDone">Weiter</button>
    </div>
  </div>
</template>
```

- [ ] **Step 5: `DuelStage` einfügen**

Direkt vor `const Shootout = {` im Block `game-shootout`:

```js
/* ================= DUEL STAGE – Ego-Sicht: Welt-Canvas, Gegnerfigur aus dem Cutscene-Rig, Effekt-Canvas, eigene Waffe =================
   Rein darstellend: trifft keine Spielentscheidung. Shootout ruft enter/signal/shot/foeShoots/foeDown/flash. */
const DuelStage = {
  root: null, world: null, fx: null, back: null, fig: null, gun: null, tag: null, flashEl: null,
  W: 0, H: 0, dpr: 1, raf: 0, last: 0, t: 0, timeScale: 1, slowUntil: 0, flashUntil: 0, redUntil: 0, shakeUntil: 0, tenseFrom: 0, lamp: 1,
  parts: [], stains: [], set: 'gasse', reduced: false, ro: null, mounted: false,
  /* Kulissen: Farben + welche Silhouetten/Ambient-Elemente gezeichnet werden */
  SETS: {
    gasse: { sky: ['#05070d', '#1a1e2a'], wall: '#23232b', ground: '#1c1a16', rain: true, lamp: true, bins: true },
    bahnhof: { sky: ['#05070d', '#1a2233'], wall: '#1b2130', ground: '#2a2820', rain: false, lamp: true, rails: true },
    keller: { sky: ['#1a1914', '#050503'], wall: '#1e1c16', ground: '#171410', rain: false, lamp: true, table: true },
  },
  SET_BY_KIND: { tutorial: 'bahnhof', hinterhalt: 'gasse', finale: 'keller', dev: 'gasse' },
  MAX_PARTS: 160,
  /* Waffe des Spielers: Stufe 0 = geliehene Pistole (Story: Anabis Makarov), 3 = „Die Goldene" */
  WEAPON_COLORS: [['#2a2a2e', '#4a4a50'], ['#2a2a2e', '#4a4a50'], ['#1e2226', '#3a4048'], ['#8a6a1a', '#d4af37']],
  mount(root, { set = 'gasse', weapon = 0, reduced = false } = {}) {
    this.unmount();
    this.root = root; this.set = this.SETS[set] ? set : 'gasse'; this.reduced = reduced;
    this.dpr = Math.min(2, window.devicePixelRatio || 1);
    this.world = h('canvas', { class: 'duel-world' }); this.fx = h('canvas', { class: 'duel-fx' });
    this.fig = h('div', { class: 'cs-fig duel-foe' });
    this.gun = h('div', { class: 'duel-gun', html: this.gunSvg(weapon) });
    this.tag = h('div', { class: 'duel-tag' }, h('span', { id: 'duelFoeName' }), h('span', { id: 'duelCount' }));
    this.flashEl = h('div', { class: 'duel-flash' });
    root.append(this.world, this.fig, this.fx, this.gun, this.tag, this.flashEl);
    this.parts = []; this.stains = []; this.timeScale = 1; this.slowUntil = this.flashUntil = this.redUntil = this.shakeUntil = this.tenseFrom = 0; this.t = 0; this.last = 0;
    this.mounted = true;
    this.resize();
    if (typeof ResizeObserver !== 'undefined') { this.ro = new ResizeObserver(() => this.resize()); this.ro.observe(root); }
    this.raf = requestAnimationFrame((now) => this.loop(now));
    requestAnimationFrame(() => { if (this.mounted) this.gun.classList.add('up'); });
  },
  unmount() {
    if (!this.mounted) return;
    cancelAnimationFrame(this.raf); this.raf = 0;
    if (this.ro) { this.ro.disconnect(); this.ro = null; }
    for (const el of [this.world, this.fx, this.fig, this.gun, this.tag, this.flashEl]) if (el) el.remove();
    this.root = this.world = this.fx = this.back = this.fig = this.gun = this.tag = this.flashEl = null;
    this.parts = []; this.stains = []; this.mounted = false;
  },
  resize() {
    if (!this.mounted) return;
    this.W = this.root.clientWidth; this.H = this.root.clientHeight;
    for (const c of [this.world, this.fx]) { c.width = Math.round(this.W * this.dpr); c.height = Math.round(this.H * this.dpr); }
    this.back = document.createElement('canvas'); this.back.width = this.world.width; this.back.height = this.world.height;
    this.drawBackdrop(this.back.getContext('2d'));
    this.draw();
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
    if (S.lamp) { ctx.fillStyle = '#555'; ctx.fillRect(W * 0.5 - 2, 0, 4, hz * 0.22); ctx.fillStyle = '#8a8a70'; ctx.fillRect(W * 0.5 - 26, hz * 0.22, 52, 10); }
    const vig = ctx.createRadialGradient(W / 2, H * 0.5, H * 0.3, W / 2, H * 0.5, H); vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, 'rgba(0,0,0,.75)');
    ctx.fillStyle = vig; ctx.fillRect(0, 0, W, H);
  },
  /* Gegner tritt aus dem Dunkel auf: Figur klein setzen, dann per Transition auf volle Größe */
  enter(foeId, idx, n, foeName) {
    if (!this.mounted) return;
    this.fig.innerHTML = CsCast.figureHtml(foeId, { mood: 'angry', gun: true });
    this.fig.dataset.pose = 'idle'; this.fig.style.setProperty('--fall', '');
    this.fig.classList.remove('gone'); this.fig.style.setProperty('--s', '0.4');
    void this.fig.offsetWidth; // Startgröße festschreiben, damit die Annäherung animiert
    this.fig.style.setProperty('--s', '1');
    qs('#duelFoeName', this.tag).textContent = foeName; qs('#duelCount', this.tag).textContent = `${idx + 1} / ${n}`;
  },
  /* Anspannung: der Rand dunkelt über ~4 s langsam ab, bis das Signal kommt */
  tension(on) { if (this.mounted) this.tenseFrom = on ? this.t || 1 : 0; },
  /* Signal: Arm hoch, Blitz */
  signal() { if (!this.mounted) return; this.fig.dataset.pose = 'draw'; if (!this.reduced) this.flashUntil = this.t + 110; },
  /* Rechteck der Figur in Bühnenkoordinaten (für die Trefferprüfung) */
  foeBox() {
    if (!this.mounted) return { left: 0, top: 0, width: 0, height: 0 };
    const r = this.fig.getBoundingClientRect(), R = this.root.getBoundingClientRect();
    return { left: r.left - R.left, top: r.top - R.top, width: r.width, height: r.height };
  },
  gunTip() { const r = this.gun.getBoundingClientRect(), R = this.root.getBoundingClientRect(); return { x: r.left - R.left + r.width * 0.3, y: r.top - R.top + r.height * 0.12 }; },
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
    setTimeout(() => { if (this.mounted) { this.fig.dataset.pose = 'down'; this.burst(b.left + b.width / 2, b.top + b.height, 'dust', 16); this.stains.push({ x: b.left + b.width * 0.6, y: b.top + b.height - 4, r: b.width * 0.35 }); } }, 220);
    if (!this.reduced) { this.timeScale = 0.3; this.slowUntil = this.t + 500; this.fig.style.setProperty('--fall', '1.2s'); } // Zeitlupe: Partikel langsamer, Fall länger
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
    if (this.slowUntil && now >= this.slowUntil) { this.slowUntil = 0; this.timeScale = 1; }
    const dt = raw * this.timeScale; this.t += dt;
    for (const p of this.parts) { p.age += dt; const s = dt / 1000; p.vy += (p.g || 0) * s; p.x += p.vx * s; p.y += p.vy * s; }
    this.parts = this.parts.filter((p) => p.age < p.ttl);
    if (!this.reduced) { this.lamp = 0.85 + Math.random() * 0.15; if (Math.random() < 0.04) this.lamp = 0.4; if (this.parts.length < 60 && Math.random() < 0.3) this.spawn({ x: Math.random() * this.W, y: this.H * 0.2 + Math.random() * this.H * 0.5, vx: 8 + Math.random() * 10, vy: -4 + Math.random() * 8, g: 0, ttl: 4000, size: 1.5, color: 'rgba(220,210,180,.35)', kind: 'dust' }); }
    this.draw();
    this.raf = requestAnimationFrame((n) => this.loop(n));
  },
  draw() {
    if (!this.mounted) return;
    const W = this.W, H = this.H, S = this.SETS[this.set];
    const wc = this.world.getContext('2d'), fc = this.fx.getContext('2d');
    wc.setTransform(1, 0, 0, 1, 0, 0); wc.drawImage(this.back, 0, 0);
    wc.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    if (S.lamp) { const g = wc.createRadialGradient(W / 2, H * 0.14, 0, W / 2, H * 0.14, H * 0.5); g.addColorStop(0, `rgba(255,240,200,${0.22 * this.lamp})`); g.addColorStop(1, 'rgba(255,240,200,0)'); wc.fillStyle = g; wc.fillRect(0, 0, W, H); }
    if (S.rain && !this.reduced) { wc.strokeStyle = 'rgba(160,180,200,.25)'; wc.lineWidth = 1; const off = (this.t * 0.6) % 40; for (let i = 0; i < 24; i++) { const x = (i * 97) % W, y = ((i * 53) + off * 4) % H; wc.beginPath(); wc.moveTo(x, y); wc.lineTo(x - 4, y + 18); wc.stroke(); } }
    for (const st of this.stains) { wc.fillStyle = 'rgba(90,8,14,.85)'; wc.beginPath(); wc.ellipse(st.x, st.y, st.r, st.r * 0.28, 0, 0, Math.PI * 2); wc.fill(); }
    for (const p of this.parts) if (p.kind === 'dust') { wc.fillStyle = p.color; wc.globalAlpha = 1 - p.age / p.ttl; wc.fillRect(p.x, p.y, p.size, p.size); }
    wc.globalAlpha = 1;
    fc.setTransform(this.dpr, 0, 0, this.dpr, 0, 0); fc.clearRect(0, 0, W, H);
    const shake = this.shakeUntil > this.t ? (Math.random() - 0.5) * 12 : 0;
    if (shake) fc.translate(shake, (Math.random() - 0.5) * 12);
    for (const p of this.parts) {
      if (p.kind === 'dust') continue;
      const k = 1 - p.age / p.ttl;
      if (p.kind === 'trace') { fc.strokeStyle = p.color; fc.globalAlpha = k; fc.lineWidth = p.size; fc.beginPath(); fc.moveTo(p.x, p.y); fc.lineTo(p.x2, p.y2); fc.stroke(); continue; }
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
  /* Hand mit Waffe von hinten, unten rechts – Farben nach Waffenstufe */
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
```

- [ ] **Step 6: Sound**

Im Block `sfx` in `LIB` direkt vor `    gunshot() {` einfügen:

```js
    ricochet() { this.noise({ dur: 0.12, vol: 0.25, freq: 2500, type: 'highpass' }); this.tone({ freq: 1800, type: 'square', dur: 0.05, vol: 0.12, slide: -900, delay: 0.02 }); },
```

- [ ] **Step 7: Suites laufen lassen**

Run: `node tests/run-selftest.mjs && tests/dom-selftest.sh`
Expected: Node grün; DOM: der neue `DuelStage`-Test grün, **genau ein** roter Test (`Shootout: Fehlschuss vor dem Blitz …`, weil das alte `Shootout` noch `#duelFoe`/`#duelSignal` sucht) – wird in Task 4 behoben. Mehr als ein roter Test = Fehler in dieser Task.

- [ ] **Step 8: Commit**

```bash
git add keller37.html
git commit -m "feat(duell): DuelStage – Ego-Sicht mit Welt-Canvas, Gegnerfigur aus dem Rig, Effekt-Canvas, Waffe; Duell-CSS und Template (Shootout folgt)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: `Shootout` auf die Bühne – Zielen, Fehlschüsse, Gegnerschuss

**Files:**
- Modify: `keller37.html` Block `game-shootout`: von `const Shootout = {` bis vor `</script>` ersetzen (inkl. `UI.register('shootout', …)`)
- Modify: `keller37.html` Block `selftest`: bestehender Test `Shootout: Fehlschuss vor dem Blitz …` (eine Zeile), zwei neue DOM-Tests vor `const pseudoAnim = …`
- Modify: `tests/playtest-story.py`: Helfer + ein Aufruf

**Interfaces:**
- Consumes: alles aus Task 1–3.
- Produces: `Shootout.shoot(ev {clientX, clientY, pointerType})`, `Shootout.tap(hit = true, pt = null)`, `Shootout.taps`, `Shootout.foeTime`, `Shootout.foeTimer`, `Shootout.NEXT_MS = 1400`, `Shootout.foeIds`; `fight:done`-Runden mit `misses`.

- [ ] **Step 1: Fehlschlagende DOM-Tests schreiben**

Vor `  const pseudoAnim = …` (hinter dem `DuelStage`-Test) einfügen:

```js
  T.test('Duell in Ego-Sicht: Bühne, Trefferprüfung, Fehlschuss kostet Zeit, Gegner schießt von sich aus, Fehlschuss vor dem Signal', async () => {
    const keep = { cur: UI.current, wait: GangRules.drawWait, s: State.s, mode: State.mode, save: State.save, ft: GangRules.foeTime };
    State.save = () => {}; State.mode = 'free'; State.s = State.fresh(); State.s.weapon = 1;
    const events = []; const off = Bus.on('fight:done', (e) => events.push([e.kind, e.won, e.rounds.map((r) => r.misses)]));
    const stageRect = () => qs('#duelStage').getBoundingClientRect();
    const shootAt = (x, y, type = 'mouse') => { const R = stageRect(); Shootout.shoot({ clientX: R.left + x, clientY: R.top + y, pointerType: type }); };
    const foeCenter = () => { const b = DuelStage.foeBox(); return [b.left + b.width / 2, b.top + b.height / 2]; };
    try {
      GangRules.drawWait = () => 30; GangRules.foeTime = () => 300;
      await UI.show('shootout');
      Shootout.start({ kind: 'e1', foes: ['junge', 'laeufer'], bonus: 100 });
      const stage = qs('#duelStage');
      T.eq([qsa('canvas.duel-world', stage).length, qsa('canvas.duel-fx', stage).length, qsa('.cs-fig.duel-foe svg.part', stage).length], [1, 1, 8], 'Welt- und Effekt-Canvas, Gegner aus dem Rig');
      T.ok(qs('.cs-fig.duel-foe .pistole', stage), 'Gegner hält eine Pistole'); T.ok(qs('.duel-gun svg', stage), 'eigene Waffe');
      T.eq([qs('#duelCount').textContent, qs('#duelFoeName').textContent, DuelStage.set], ['1 / 2', 'Bahnhof-Junge', 'gasse']);
      T.ok(DuelStage.raf > 0, 'Canvas-Schleife läuft');
      /* Runde 1: vor dem Signal ist ein Tipp kein Schuss auf den Gegner … erst daneben, dann Treffer */
      Shootout.ready(); T.eq([Shootout.phase, DuelStage.tenseFrom > 0], ['wait', true], 'Anspannung an');
      await wait(120); T.eq([Shootout.phase, qs('.cs-fig.duel-foe').dataset.pose, qs('.duel-flash').textContent, DuelStage.tenseFrom], ['draw', 'draw', 'ZIEH!', 0], 'Signal: Arm hoch + ZIEH!, Anspannung aus');
      shootAt(10, 10); T.eq([Shootout.phase, Shootout.taps.length, Shootout.taps[0].hit], ['draw', 1, false], 'daneben: Runde läuft weiter');
      const [cx, cy] = foeCenter(); shootAt(cx, cy);
      T.eq([Shootout.phase, Shootout.results[0].won, Shootout.results[0].misses, qs('.cs-fig.duel-foe').dataset.pose], ['result', true, 1, 'hit'], 'Treffer nach einem Fehlschuss');
      await wait(300); T.eq(qs('.cs-fig.duel-foe').dataset.pose, 'down', 'Gegner fällt');
      await wait(Shootout.NEXT_MS + 100); T.eq([Shootout.phase, qs('#duelCount').textContent, qs('#duelFoeName').textContent], ['idle', '2 / 2', 'Bahnhof-Läufer']);
      /* Runde 2: Touch-Rand trifft knapp außerhalb der Box */
      Shootout.ready(); await wait(120);
      const b = DuelStage.foeBox(); shootAt(b.left - 28, b.top + b.height / 2, 'touch');
      T.eq([Shootout.results[1].won, Shootout.results[1].misses, events], [true, 0, [['e1', true, [1, 0]]]], 'Touch-Rand 32 px trifft, Duell gewonnen');
      await Shootout.leave();
      /* Gegner schießt von sich aus, wenn kein Treffer kommt (foeTime 300 + Bonus 100 = 400 ms) */
      events.length = 0; await UI.show('shootout');
      Shootout.start({ kind: 'e2', foes: ['junge'], bonus: 100 });
      Shootout.ready(); await wait(120); shootAt(5, 5); shootAt(5, 5);
      T.eq(Shootout.phase, 'draw'); await wait(450);
      T.eq([Shootout.phase, Shootout.results[0].won, Shootout.results[0].you, Shootout.results[0].misses, events], ['done', false, null, 2, [['e2', false, [2]]]], 'Gegnerschuss beendet die Runde');
      T.ok(DuelStage.redUntil > DuelStage.t, 'roter Rand nach dem Gegnerschuss');
      await Shootout.leave();
      /* Fehlschuss vor dem Signal – egal wohin getippt */
      events.length = 0; await UI.show('shootout');
      Shootout.start({ kind: 'e3', foes: ['junge'], bonus: 0 });
      Shootout.ready(); const [fx, fy] = foeCenter(); shootAt(fx, fy);
      T.eq([Shootout.results[0].misfire, Shootout.results[0].won, events], [true, false, [['e3', false, [0]]]]);
      await Shootout.leave();
    } finally {
      off(); GangRules.drawWait = keep.wait; GangRules.foeTime = keep.ft; State.save = keep.save; State.s = keep.s; State.mode = keep.mode;
      clearTimeout(Shootout.timer); clearTimeout(Shootout.foeTimer); clearTimeout(Shootout.nextTimer); Shootout.running = false; Shootout.forced = false; Shootout.pending = null;
      await UI.show(keep.cur ? keep.cur.id : 'hub');
      T.eq(DuelStage.mounted, false, 'Bühne beim Verlassen abgebaut'); T.eq(DuelStage.raf, 0, 'Canvas-Schleife gestoppt');
    }
  });
  T.test('Duell: reduced-motion lässt Zeitfaktor bei 1 und ohne Blitz; Duell-Keyframes nur transform/opacity', async () => {
    const keep = { cur: UI.current, wait: GangRules.drawWait, s: State.s, mode: State.mode, save: State.save, mm: window.matchMedia };
    State.save = () => {}; State.mode = 'free'; State.s = State.fresh();
    window.matchMedia = (q) => ({ matches: q.includes('reduced-motion'), addEventListener() {}, removeEventListener() {} });
    try {
      GangRules.drawWait = () => 30;
      await UI.show('shootout');
      Shootout.start({ kind: 'r1', foes: ['junge'], bonus: 300 });
      T.eq(DuelStage.reduced, true);
      Shootout.ready(); await wait(900); T.eq(Shootout.phase, 'draw', 'reduced: festes Signal nach 800 ms');
      T.eq(DuelStage.flashUntil, 0, 'kein Blitz');
      Shootout.tap(); T.eq(Shootout.results[0].won, true);
      T.eq(DuelStage.timeScale, 1, 'keine Zeitlupe');
      await Shootout.leave();
      for (const name of ['duelRecoil', 'duelTwitch', 'csHit']) { const kf = keyframesOf(name); T.ok(kf, `@keyframes ${name}`); for (const p of animatedProps(kf)) T.ok(p === 'transform' || p === 'opacity', `${name}: ${p}`); }
    } finally {
      window.matchMedia = keep.mm; GangRules.drawWait = keep.wait; State.save = keep.save; State.s = keep.s; State.mode = keep.mode;
      clearTimeout(Shootout.timer); clearTimeout(Shootout.foeTimer); clearTimeout(Shootout.nextTimer); Shootout.running = false; Shootout.forced = false; Shootout.pending = null;
      await UI.show(keep.cur ? keep.cur.id : 'hub');
    }
  });
```

Im bestehenden Test `Shootout: Fehlschuss vor dem Blitz …` die Zeile `      await wait(1000); // nextTimer (900 ms) räumt auf Runde 2 um` ersetzen durch `      await wait(Shootout.NEXT_MS + 100); // nextTimer räumt auf Runde 2 um`.

- [ ] **Step 2: DOM-Suite laufen lassen – muss fehlschlagen**

Run: `tests/dom-selftest.sh`
Expected: die neuen Duell-Tests und der bestehende Shootout-Test rot.

- [ ] **Step 3: `Shootout` ersetzen**

Von `const Shootout = {` bis unmittelbar vor `</script>` des Blocks `game-shootout` ersetzen durch:

```js
const Shootout = {
  root: null, gen: 0, running: false, forced: false, pending: null, cfg: null, foes: [], foeIds: [], idx: 0, phase: 'idle', signalAt: 0, foeTime: 0, taps: [],
  timer: null, foeTimer: null, nextTimer: null, pulseTimer: null, results: [], won: false,
  NEXT_MS: 1400,            // nächster Gegner erst, wenn der Fall (Zeitlupe) durch ist
  alive(gen) { return !!this.root && this.gen === gen; },
  /* cfg: { kind, foes: ['junge', …], bonus (ms), forced } */
  start(cfg) {
    if (!this.root || this.running) return;
    this.cfg = cfg; this.foeIds = cfg.foes.filter((id) => GangRules.FOES[id]); this.foes = this.foeIds.map((id) => GangRules.FOES[id]); this.idx = 0; this.results = [];
    if (!this.foes.length) { qs('#duelStatus', this.root).textContent = 'Kein Gegner.'; return; }
    this.running = true; this.forced = !!cfg.forced; this.phase = 'idle';
    DuelStage.mount(qs('#duelStage', this.root), { set: DuelStage.SET_BY_KIND[cfg.kind] || 'gasse', weapon: State.s.weapon || 0, reduced: matchMedia('(prefers-reduced-motion: reduce)').matches });
    qs('#btnDuelStart', this.root).classList.remove('hidden'); qs('#btnDuelDone', this.root).classList.add('hidden');
    qs('#btnDuelStart', this.root).textContent = 'Bereit';
    qs('#duelStatus', this.root).textContent = `${this.foes.length} Gegner. ${cfg.bonus ? `Waffe: ${cfg.bonus} ms Vorsprung.` : 'Ohne Vorsprung.'} „Bereit“ – dann warten, bis er zieht, und auf ihn tippen.`;
    this.renderFoe();
  },
  renderFoe() {
    if (!this.root) return;
    const foe = this.foes[this.idx];
    if (foe) DuelStage.enter(this.foeIds[this.idx], this.idx, this.foes.length, foe.name);
  },
  ready() {
    if (!this.running || this.phase !== 'idle' || !this.root) return;
    const gen = this.gen;
    this.phase = 'wait';
    qs('#btnDuelStart', this.root).classList.add('hidden');
    qs('#duelStatus', this.root).textContent = 'Warte, bis er zieht.';
    SFX.loop('heartbeat', 900); DuelStage.tension(true);
    this.pulseTimer = setTimeout(() => { if (this.alive(gen) && this.phase === 'wait') SFX.loop('heartbeat', 550); }, 1200); // Anspannung: Herz schlägt schneller
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.timer = setTimeout(() => {
      if (!this.alive(gen) || this.phase !== 'wait') return;
      const foe = this.foes[this.idx], bonus = this.cfg.bonus || 0;
      this.phase = 'draw'; this.signalAt = performance.now(); this.taps = [];
      this.foeTime = GangRules.foeTime(foe, Math.random);
      clearTimeout(this.pulseTimer); SFX.stop('heartbeat'); SFX.play('reelStop');
      DuelStage.tension(false); DuelStage.signal(); DuelStage.flash('ZIEH!', 500);
      /* Der Gegner wartet nicht: zu seiner Zeit (plus dein Vorsprung) schießt er, wenn bis dahin kein Treffer kam */
      this.foeTimer = setTimeout(() => { if (this.alive(gen) && this.phase === 'draw') this.resolve(); }, GangRules.foeFiresAt(this.foeTime, bonus));
    }, reduced ? 800 : GangRules.drawWait(Math.random));
  },
  /* Schuss per Zeiger: Trefferprüfung gegen die Figuren-Box (Rand: Maus 24 px, Touch 32 px) */
  shoot(ev) {
    if (!this.running || !this.root || (this.phase !== 'wait' && this.phase !== 'draw')) return;
    const R = qs('#duelStage', this.root).getBoundingClientRect();
    const pt = { x: ev.clientX - R.left, y: ev.clientY - R.top };
    const margin = ev.pointerType === 'touch' ? GangRules.HIT_MARGIN.touch : GangRules.HIT_MARGIN.mouse;
    this.tap(GangRules.hitTest(pt, DuelStage.foeBox(), margin), pt);
  },
  /* tap(): Tastatur/Playtest = Schuss mit automatischem Treffer; hit=false = daneben (kostet nur Zeit) */
  tap(hit = true, pt = null) {
    if (!this.running) return;
    if (this.phase === 'wait') {
      clearTimeout(this.timer); SFX.stop('heartbeat'); SFX.play('gunshot');
      this.taps = [{ t: -1, hit }]; DuelStage.shot({ early: true });
      this.resolve();
    } else if (this.phase === 'draw') {
      const t = Math.round(performance.now() - this.signalAt);
      this.taps.push({ t, hit });
      SFX.play(hit ? 'gunshot' : 'ricochet'); if (navigator.vibrate) navigator.vibrate(30);
      DuelStage.shot({ x: pt ? pt.x : null, y: pt ? pt.y : null, hit });
      if (hit) this.resolve(); else if (this.root) qs('#duelStatus', this.root).textContent = 'Daneben!';
    }
  },
  resolve() {
    const gen = this.gen;
    clearTimeout(this.foeTimer); clearTimeout(this.timer); clearTimeout(this.pulseTimer); SFX.stop('heartbeat'); DuelStage.tension(false);
    this.phase = 'result';
    const foe = this.foes[this.idx];
    const r = GangRules.resolveRound({ taps: this.taps, foeTime: this.foeTime, bonus: this.cfg.bonus || 0 });
    this.results.push(r);
    if (r.won) DuelStage.foeDown();
    else if (r.misfire) DuelStage.flash('Zu früh!', 900);
    else { DuelStage.foeShoots(); SFX.play('gunshot'); if (navigator.vibrate) navigator.vibrate([40, 40, 80]); }
    if (this.root) {
      const missTxt = r.misses ? ` ${r.misses}× daneben.` : '';
      qs('#duelStatus', this.root).innerHTML = r.misfire ? `<span class="loss">Zu früh! Der Schuss geht in den Asphalt. ${foe.name} nicht.</span>`
        : r.won ? `<span class="win">${foe.name}: ${r.foeTime} ms. Du: ${r.you} ms.${missTxt} Er liegt.</span>`
        : r.you == null ? `<span class="loss">${foe.name}: ${r.foeTime} ms.${missTxt} Er war schneller.</span>`
        : `<span class="loss">${foe.name}: ${r.foeTime} ms. Du: ${r.you} ms.${missTxt} Zu langsam.</span>`;
    }
    SFX.play(r.won ? 'cash' : 'lose');
    if (!r.won) return this.finish(false);
    this.idx++;
    if (this.idx >= this.foes.length) return this.finish(true);
    this.nextTimer = setTimeout(() => { if (!this.alive(gen)) return; this.phase = 'idle'; this.renderFoe(); const b = qs('#btnDuelStart', this.root); b.textContent = 'Nächster'; b.classList.remove('hidden'); }, this.NEXT_MS);
  },
  finish(won) {
    this.running = false; this.phase = 'done'; this.won = won;
    if (this.root) {
      qs('#btnDuelStart', this.root).classList.add('hidden'); qs('#btnDuelDone', this.root).classList.remove('hidden');
      const line = won ? 'Alle liegen. Du gehst.' : 'Du liegst. Sie gehen.';
      qs('#duelStatus', this.root).innerHTML += ` <b>${line}</b>`;
    }
    Bus.emit('fight:done', { kind: this.cfg.kind, won, rounds: this.results });
  },
  async leave() {
    if (this.running) return;
    const kind = this.cfg ? this.cfg.kind : null, won = this.won;
    const forced = this.forced; this.forced = false;
    await Bus.emit('fight:leave', { kind, won });
    if (!forced) await UI.show('hub'); // Story/Dev: die Story entscheidet, wohin es geht (Nacht läuft weiter, Ende, …)
  },
  onKey(e) {
    if (!qs('#cutscene').hidden || e.repeat) return;
    if (e.code === 'Space' || e.code === 'Enter') { e.preventDefault(); if (Shootout.phase === 'idle') Shootout.ready(); else Shootout.tap(); }
  },
};
UI.register('shootout', {
  template: 'tpl-shootout',
  mount(root) {
    Shootout.gen++; Shootout.root = root; Shootout.running = false; Shootout.phase = 'idle';
    qs('#btnDuelStart', root).addEventListener('click', () => { SFX.play('click'); Shootout.ready(); });
    qs('#btnDuelDone', root).addEventListener('click', (e) => { e.currentTarget.disabled = true; SFX.play('click'); Shootout.leave(); });
    qs('#duelStage', root).addEventListener('pointerdown', (e) => { e.preventDefault(); Shootout.shoot(e); });
    document.addEventListener('keydown', Shootout.onKey);
    if (Shootout.pending) { const c = Shootout.pending; Shootout.pending = null; Shootout.start(c); return; }
    const params = new URLSearchParams(location.search);
    const foe = params.get('foe');
    if (foe && GangRules.FOES[foe]) {
      if (params.has('weapon')) State.s.weapon = Math.max(0, Math.min(3, parseInt(params.get('weapon'), 10) || 0));
      Shootout.start({ kind: 'dev', foes: [foe], bonus: GangRules.weapon(State.s).bonus });
    } else {
      qs('#duelStatus', root).textContent = 'Kein Gegner. (Dev: ?screen=shootout&foe=junge)';
      qs('#btnDuelStart', root).classList.add('hidden');
    }
  },
  unmount() {
    document.removeEventListener('keydown', Shootout.onKey);
    clearTimeout(Shootout.timer); clearTimeout(Shootout.foeTimer); clearTimeout(Shootout.nextTimer); clearTimeout(Shootout.pulseTimer); SFX.stop('heartbeat');
    DuelStage.unmount();
    const wasRunning = Shootout.running;
    const kind = Shootout.cfg ? Shootout.cfg.kind : null;
    Shootout.gen++; Shootout.root = null; Shootout.running = false; Shootout.phase = 'idle';
    /* Screen mitten im Kampf verlassen (Brand-Knopf, Reload-Schutz greift nicht): zählt als verloren, damit ein wartendes forceFight nicht hängt */
    if (wasRunning) Bus.emit('fight:done', { kind, won: false, rounds: Shootout.results, aborted: true });
    /* forced bleibt nach dem Ergebnis gesetzt, bis „Weiter" (leave()) geklickt wird – wer stattdessen wegnavigiert (Escape, Marke, Sidebar),
       muss das wartende forceFight trotzdem auflösen, sonst bleibt Story.night() für immer gesperrt (sleeping = true) */
    if (Shootout.forced) { Bus.emit('fight:leave', { kind, won: !wasRunning && Shootout.won, aborted: wasRunning }); Shootout.forced = false; }
  },
});
```

- [ ] **Step 4: Playtest-Helfer**

In `tests/playtest-story.py` in `PAGE_HELPERS` direkt nach der Zeile `__pt.cutsceneActive = function() { return typeof Cutscene !== 'undefined' && Cutscene.active; };` einfügen:

```js
__pt.duelShoot = function() {
  // Schuss auf die Gegnerfigur (Ego-Duell): Tipp in die Mitte der Figuren-Box
  const b = DuelStage.foeBox(), R = document.querySelector('#duelStage').getBoundingClientRect();
  Shootout.shoot({ clientX: R.left + b.left + b.width / 2, clientY: R.top + b.top + b.height / 2, pointerType: 'mouse' });
  return true;
};
```

und die Zeile `    await cdp.eval("Shootout.tap()", await_promise=False)` (Story-3-Tutorial) ersetzen durch `    await cdp.eval("__pt.duelShoot()", await_promise=False)`.

- [ ] **Step 5: Alle Tests**

Run: `node tests/run-selftest.mjs && tests/dom-selftest.sh`
Expected: Node grün; DOM `failed=0` (alter Shootout-Test grün, zwei Duell-Tests grün).

Run: `python3 tests/playtest-story.py 2>&1 | grep -E "FEHLGESCHLAGEN|ERRORS|Checks:"` (vorher `pgrep -f playtest-story.py` leer – Port 9335 und `/tmp/k37story-profile` sind exklusiv; ein liegengebliebener Chrome mit `--remote-debugging-port=9335` muss vorher beendet werden).
Expected: `Checks: …, davon fehlgeschlagen: 0`, `ERRORS 0`.

- [ ] **Step 6: Sichtprüfung in Echtzeit**

Headless-Screenshots per virtueller Zeit zeigen kein Canvas (kein rAF). Ein kleines CDP-Skript im Scratchpad (Vorlage: `tests/playtest-story.py`, Klasse `CDP`, mit `K37_PORT=9392 K37_PROFILE=/tmp/k37duel-profile K37_SHOTS=<scratchpad>`) lädt `?screen=shootout&foe=junge&weapon=1&fresh`, wartet 1,4 s (Screenshot: Gegner da, Waffe unten rechts), setzt `GangRules.drawWait = () => 300; Shootout.ready()` und plant im Seitenkontext `setTimeout(daneben, 380)` und `setTimeout(treffer, 470)` (`Shootout.shoot` mit Koordinaten aus `DuelStage.foeBox()`); Screenshots bei 0,34 s (ZIEH!, Arm hoch), 0,41 s (Funken), 0,5 s (Blut), 1,4 s (liegt, Fleck). Zweiter Lauf mit `foe=anabi&weapon=0` ohne Schuss: Screenshot bei 1,0 s nach `ready()` (roter Rand, Tropfen). Beides zusätzlich mit `Emulation.setDeviceMetricsOverride` 412×915 @2. PNGs mit dem Read-Tool ansehen und im Report beschreiben.

- [ ] **Step 7: Commit**

```bash
git add keller37.html tests/playtest-story.py
git commit -m "feat(duell): Schießerei in Ego-Sicht – Zielen per Tipp, Fehlschüsse kosten Zeit, Gegner schießt zur Gegnerzeit; Playtest-Helfer duelShoot

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Performance-Nachweis, Doku, Abschluss

**Files:**
- Modify: `tests/perf-trace.py` (ein Szenario)
- Modify: `README.md`, `docs/superpowers/specs/2026-09-21-schiesserei-ego-design.md`

- [ ] **Step 1: Trace-Szenario**

In `tests/perf-trace.py` in `SCENARIOS` (Tupel: Name, URL-Query, Sekunden, Auslöser-JS, Vorbereitungs-JS) hinter dem Eintrag `("Cutscene Regie", …)` ergänzen:

```python
    ("Duell", "?screen=shootout&foe=junge&weapon=1", 4,
     "GangRules.drawWait = () => 400; Shootout.ready(); setTimeout(() => { const b = DuelStage.foeBox(), R = document.querySelector('#duelStage').getBoundingClientRect();"
     " Shootout.shoot({ clientX: R.left + b.left + b.width / 2, clientY: R.top + b.top + b.height / 2, pointerType: 'mouse' }); }, 600)", None),
```

(Auslöser läuft beim Start der Aufzeichnung: Signal nach 400 ms, Treffer bei 600 ms, Fall in Zeitlupe – alles innerhalb der 4 s.)

- [ ] **Step 2: Messen**

Run: `python3 tests/perf-trace.py "Duell"` und `python3 tests/perf-trace.py --mobile "Duell"`.
Expected: Unter „meistgemalte Elemente" nur die beiden Canvas (`canvas.duel-world`, `canvas.duel-fx`) – keine `.cs-fig`/`.part`-Knoten, keine `Layout/s` über ~2 (der einzige Layout-Lesevorgang ist `foeBox()` beim Tipp). Raster-ms pro Sekunde notieren. Liegt die Zeichenzeit pro Frame (Raster-ms ÷ Frames) über 2 ms auf dem Mac, Partikel-Obergrenze `MAX_PARTS` senken oder Regen-Striche reduzieren und erneut messen.

- [ ] **Step 3: README**

Im Abschnitt „Was drin ist" (bei der Story-3-/Schießerei-Erwähnung, sonst direkt unter „Cutscene-Bühne") einen Absatz „Schießerei" ergänzen:

```markdown
### Schießerei

Duelle (Story 3: Tutorial, Hinterhalte, Finale; Dev: `?screen=shootout&foe=junge&weapon=2`) laufen in Ego-Sicht: Welt-Canvas mit Kulisse (Bahnhof, Gasse, Keller), der Gegner als Comic-Figur aus dem Cutscene-Rig, unten rechts die eigene Waffe (Makarov, Glock, „Die Goldene"). Ablauf: der Gegner kommt aus dem Dunkel, zieht (Arm hoch + „ZIEH!"), dann zählt der erste Tipp, der ihn trifft (Figur plus 24 px Rand, Touch 32 px). Daneben getippt = Schuss ins Leere, die Uhr läuft weiter; der Gegner schießt von sich aus bei seiner Zeit plus Waffenbonus (`GangRules.foeFiresAt`) – das ist exakt der Punkt, an dem die alte Rechnung verloren hätte, die Balance ist unverändert (`GangRules.resolveRound` ≡ `duelRound` bei einem Treffer). Zu früh getippt bleibt ein Fehlschuss. Treffer: Mündungsfeuer, Blutspritzer, Zeitlupe beim Fall; getroffen werden: roter Rand, Tropfen über der Kamera. Leertaste/Enter schießt mit automatischem Treffer. `prefers-reduced-motion`: keine Zeitlupe, kein Ruck, kein Blitz, Partikel als Standbild.
```

Im Tests-Abschnitt ergänzen: Node-Tests `hitTest`, `foeTime/foeFiresAt`, `resolveRound` (+ Invariante zu `duelRound`), Cast-Looks/Pistole; DOM-Tests „DuelStage: …", „Duell in Ego-Sicht: …", „Duell: reduced-motion …"; Playtest-Helfer `__pt.duelShoot`; Trace-Szenario „Duell" mit den gemessenen Werten (Desktop/mobil).

- [ ] **Step 4: Spec-Notiz**

Am Ende der Spec einen Abschnitt anfügen:

```markdown
## Umsetzungsnotiz

Die Pistole des Gegners ist ein Extra im rechten Arm-Teil (`class="pistole"`), die Pose `draw` dreht den Arm um 100° nach oben – in der Frontansicht zeigt der Lauf zur Seite, das Mündungsfeuer kommt aus dem Effekt-Canvas an der Hand. Die Zeitlupe verlangsamt die Partikel (Zeitfaktor 0,3) und verlängert den Fall (`--fall: 1.2s`); der nächste Gegner kommt nach `Shootout.NEXT_MS = 1400` ms statt 900. Anspannung: `DuelStage.tension(true)` dunkelt den Rand über ~4 s ab, der Herzschlag wechselt nach 1,2 s auf 550 ms Takt, die Hand des Gegners zuckt im `idle` alle 2,6 s zur Waffe (`duelTwitch`). `Shootout.tap()` ohne Argument bleibt „Schuss mit Treffer" (Tastatur, Playtest, alte Tests); `Shootout.shoot(ev)` ist der Zeigerpfad mit Trefferprüfung.
```

- [ ] **Step 5: Abschluss-Checks**

```bash
grep -n "duel-fighter\|duelSignal\|duel-moon\|#duelYou\|#duelFoe\b" keller37.html tests/*.py   # muss leer sein
node tests/run-selftest.mjs && tests/dom-selftest.sh
python3 tests/playtest-story.py 2>&1 | grep -E "FEHLGESCHLAGEN|ERRORS|Checks:"
```

Expected: grep leer; Node/DOM grün; Playtest `ERRORS 0`, keine Fehlschläge.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/superpowers/specs/2026-09-21-schiesserei-ego-design.md tests/perf-trace.py
git commit -m "docs(duell): Schießerei dokumentiert, Trace-Szenario Duell

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

Danach: nicht mergen, nicht pushen – Freigabe des Auftraggebers einholen.
