# KELLER 37 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das bestehende Ein-Datei-Casino-Spiel `Gamble Game.html` als neue Datei `keller37.html` komplett neu aufbauen – gleiche Mechanik, neuer Look („Seedy Underground"), Visual-Novel-Cutscenes statt `alert()`, echte Animationen, Sound, Speichern, Game Over, Achievements.

**Architecture:** Eine HTML-Datei mit mehreren `<script id="…">`-Blöcken (rules, state, bus, util, sfx, ui, cutscene, core, rooms, game-*, achievements, selftest, boot). `Rules` sind pure Funktionen und werden per Node-Runner getestet, der die Script-Blöcke aus der HTML extrahiert. Spiellogik kommuniziert über `Bus.emit()` mit Cutscenes/Sound/Achievements. Screens sind `<template>`-Tags, die ein Router in die Bühne klont.

**Tech Stack:** Vanilla HTML/CSS/JS (ES2020), Web Audio API, Canvas 2D, localStorage, Google Fonts (mit Fallback). Tests: Node 20 (`node:vm`), Headless Chrome für Screenshots.

**Spec:** `docs/superpowers/specs/2026-09-15-keller37-redesign.md`

## Global Constraints

- Genau eine Auslieferungsdatei: `keller37.html`. `Gamble Game.html` bleibt unverändert als Referenz.
- Läuft per Doppelklick (`file://`). Keine npm-Abhängigkeiten, kein Build. `tests/` enthält nur Dev-Werkzeuge (Node-Runner, Screenshot-Script).
- Mechanik exakt wie in Spec Abschnitt 9. Einzige neue Regel: Bank-Limit 3.000 € und Game Over (`balance < 0 && bankDebt >= 3000 && mafiaDebt > 0`).
- Kein `alert()`, `confirm()`, `prompt()` in `keller37.html`.
- Kein `onclick=""` im HTML; Events werden in `mount()` gebunden.
- UI-Sprache Deutsch. Zahlen in Courier Prime, Überschriften/Buttons in Bebas Neue, Fallbacks laut Spec.
- Cutscene-Effekte (`fx`) verändern **nie** den State; sie animieren nur. State ändert die Spiellogik vor dem `emit`.
- Alle Script-Blöcke teilen sich den globalen Lexical Scope (top-level `const`), d.h. `Rules`, `State`, `Bus`, `UI`, … sind in späteren Blöcken direkt sichtbar.
- Commits nach jedem Task; Commit-Nachrichten enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Marker in der HTML, an denen spätere Tasks einfügen: `<!-- /TEMPLATES -->` (Templates davor), `/* ==== 7. ANIMATIONEN ==== */` (Spiel-CSS davor), `<script id="selftest">` (neue Script-Blöcke davor), `/* --- SELFTEST CASES END --- */` (Tests davor).

**Verifikations-Werkzeuge (in Task 1 erstellt):**
- `node tests/run-selftest.mjs` – führt `SelfTest.run()` unter Node aus (lädt rules, state, bus, util, selftest).
- `tests/screenshot.sh out.png "?screen=slots"` – Headless-Chrome-Screenshot; danach die PNG mit dem Read-Tool ansehen.
- `tests/dom-selftest.sh` – lädt `keller37.html?selftest` headless und gibt `data-selftest="passed=N failed=M"` aus.
- Dev-Query-Parameter in `boot`: `?screen=<id>` öffnet direkt einen Screen, `?scene=<id>` spielt eine Szene, `?selftest` führt die Tests aus, `?fresh` ignoriert den Spielstand.

---

### Task 1: Gerüst, Test-Harness, Rules (Wirtschaft)

**Files:**
- Create: `keller37.html`
- Create: `tests/run-selftest.mjs`
- Create: `tests/screenshot.sh`
- Create: `tests/dom-selftest.sh`

**Interfaces:**
- Produces: `Rules.PRICES`, `Rules.BEER_LUCK`, `Rules.luck(s)`, `Rules.bankInterest(debt)`, `Rules.spinCosts(s)`, `Rules.maxBet(s)`, `Rules.checkSpin(s, bet)`, `Rules.mafiaBill(debt)`, `Rules.bankLoanAllowed(s, amt)`, `Rules.isGameOver(s)`, `Rules.passiveTick(s)`, `Rules.passivePerMin(s)`; `SelfTest.test(name, fn)`, `SelfTest.eq(a,b,msg)`, `SelfTest.ok(v,msg)`, `SelfTest.run()`, `seq(...values)` (deterministischer rng); `wait(ms)`, `rand(a,b)`, `pick(arr)`, `qs(sel, root)`, `qsa(sel, root)`, `h(tag, attrs, ...children)`.

- [ ] **Step 1: HTML-Gerüst anlegen**

`keller37.html`:

```html
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KELLER 37</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
<style>
/* ==== 1. TOKENS ==== */
:root {
  --bg: #0a0c09;
  --panel: #141712;
  --panel-2: #1b1f19;
  --felt: #0f3d2e;
  --felt-2: #0b2e22;
  --gold: #c9a227;
  --gold-2: #e8c65a;
  --neon-red: #ff3b3b;
  --neon-amber: #ffb432;
  --neon-blue: #4cc9f0;
  --neon-green: #3ddc84;
  --neon-pink: #ff5fa2;
  --neon-purple: #b066ff;
  --day: #f5d67a;
  --text: #e8e2d0;
  --dim: #8a8577;
  --paper: #e9dcc0;
  --paper-ink: #2a2418;
  --font-display: "Bebas Neue", Impact, "Arial Narrow", sans-serif;
  --font-mono: "Courier Prime", "Courier New", monospace;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --radius: 10px;
  --shadow: 0 10px 30px rgba(0,0,0,.6);
}
/* ==== 2. BASIS & TEXTUR ==== */
/* ==== 3. LAYOUT ==== */
/* ==== 4. KOMPONENTEN ==== */
/* ==== 5. CUTSCENE ==== */
/* ==== 6. SPIELE & RÄUME ==== */
/* ==== 7. ANIMATIONEN ==== */
</style>
</head>
<body>
<div class="grain" aria-hidden="true"></div>
<div class="vignette" aria-hidden="true"></div>
<div class="shell" id="shell">
  <header class="wallet" id="wallet"></header>
  <div class="body">
    <main class="stage" id="stage"></main>
    <aside class="side" id="side"></aside>
  </div>
</div>
<div id="toasts" aria-live="polite"></div>
<div id="cutscene" hidden></div>

<!-- TEMPLATES -->
<!-- /TEMPLATES -->

<script id="rules">
/* ================= RULES – reine Spielregeln, kein DOM, kein State ================= */
const Rules = {
};
</script>

<script id="util">
/* ================= UTIL ================= */
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const rand = (a, b) => a + Math.random() * (b - a);
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
const qs = (sel, root = document) => root.querySelector(sel);
const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'style') el.style.cssText = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'html') el.innerHTML = v;
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null) continue;
    el.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return el;
}
</script>

<script id="selftest">
/* ================= SELFTEST – läuft mit ?selftest im Browser und via node tests/run-selftest.mjs ================= */
const SelfTest = {
  cases: [],
  test(name, fn) { this.cases.push({ name, fn }); },
  eq(a, b, msg = '') {
    const ja = JSON.stringify(a), jb = JSON.stringify(b);
    if (ja !== jb) throw new Error(`${msg} erwartet ${jb}, bekommen ${ja}`);
  },
  ok(v, msg = 'erwartet wahr') { if (!v) throw new Error(msg); },
  run() {
    let passed = 0, failed = 0; const failures = [];
    for (const c of this.cases) {
      try { c.fn(); passed++; } catch (e) { failed++; failures.push(`${c.name}: ${e.message}`); }
    }
    return { passed, failed, failures };
  },
};
/* deterministischer rng: liefert die Werte der Reihe nach, dann von vorn */
const seq = (...vals) => { let i = 0; return () => vals[i++ % vals.length]; };
const T = SelfTest;

/* --- SELFTEST CASES END --- */
</script>

<script id="boot">
/* ================= BOOT ================= */
(function boot() {
  const params = new URLSearchParams(location.search);
  if (params.has('selftest')) {
    const r = SelfTest.run();
    document.documentElement.dataset.selftest = `passed=${r.passed} failed=${r.failed}`;
    console.log('[selftest]', r);
    r.failures.forEach((f) => console.error('[selftest] FAIL', f));
  }
})();
</script>
</body>
</html>
```

- [ ] **Step 2: Node-Runner und Screenshot-Scripts anlegen**

`tests/run-selftest.mjs`:

```js
// Führt SelfTest.run() aus keller37.html unter Node aus.
// Lädt nur die DOM-freien Script-Blöcke: rules, state, bus, util, selftest.
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(new URL('../keller37.html', import.meta.url), 'utf8');
const block = (id) => {
  const m = html.match(new RegExp(`<script id="${id}">([\\s\\S]*?)<\\/script>`));
  if (!m) throw new Error(`Script-Block "${id}" fehlt`);
  return m[1];
};
const storage = {
  data: {},
  getItem(k) { return k in this.data ? this.data[k] : null; },
  setItem(k, v) { this.data[k] = String(v); },
  removeItem(k) { delete this.data[k]; },
  clear() { this.data = {}; },
};
const ctx = { console, localStorage: storage, setTimeout, clearTimeout };
vm.createContext(ctx);
for (const id of ['rules', 'util', 'state', 'bus', 'selftest']) {
  if (!html.includes(`<script id="${id}">`)) continue; // state/bus kommen erst in Task 4
  vm.runInContext(block(id), ctx, { filename: `${id}.js` });
}
const r = vm.runInContext('SelfTest.run()', ctx);
for (const f of r.failures) console.error('FAIL', f);
console.log(`${r.passed} bestanden, ${r.failed} fehlgeschlagen`);
process.exit(r.failed ? 1 : 0);
```

`tests/screenshot.sh`:

```sh
#!/bin/sh
# Nutzung: tests/screenshot.sh out.png "?screen=slots"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,900 \
  --virtual-time-budget=4000 --screenshot="$1" "file://$DIR/keller37.html$2" 2>/dev/null
echo "Screenshot: $1"
```

`tests/dom-selftest.sh`:

```sh
#!/bin/sh
# Führt den In-Browser-Selbsttest headless aus und gibt das Ergebnis aus.
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$CHROME" --headless=new --disable-gpu --virtual-time-budget=4000 \
  --dump-dom "file://$DIR/keller37.html?selftest&fresh" 2>/dev/null | grep -o 'data-selftest="[^"]*"'
```

Dann: `chmod +x tests/screenshot.sh tests/dom-selftest.sh`

- [ ] **Step 3: Failing Tests für die Wirtschafts-Regeln schreiben**

Vor `/* --- SELFTEST CASES END --- */` einfügen:

```js
/* ---- Rules: Wirtschaft ---- */
const base = (o = {}) => Object.assign({
  balance: 50, beers: 0, beerTimer: 0, brownieTimer: 0, kidneySold: false,
  bankDebt: 0, mafiaDebt: 0, hasHouse: false, hasDealer: false,
  isMarried: false, isHeartbroken: false,
}, o);

T.test('luck: nichts aktiv = 0', () => T.eq(Rules.luck(base()), 0));
T.test('luck: 1/2/3 Bier = 10/15/20', () => {
  T.eq(Rules.luck(base({ beers: 1, beerTimer: 2 })), 10);
  T.eq(Rules.luck(base({ beers: 2, beerTimer: 1 })), 15);
  T.eq(Rules.luck(base({ beers: 3, beerTimer: 2 })), 20);
});
T.test('luck: Bier ohne Timer zählt nicht', () => T.eq(Rules.luck(base({ beers: 2, beerTimer: 0 })), 0));
T.test('luck: Brownie +40, mit 3 Bier 60', () => {
  T.eq(Rules.luck(base({ brownieTimer: 1 })), 40);
  T.eq(Rules.luck(base({ beers: 3, beerTimer: 2, brownieTimer: 1 })), 60);
});
T.test('bankInterest: 30% gerundet', () => {
  T.eq(Rules.bankInterest(0), 0);
  T.eq(Rules.bankInterest(200), 60);
  T.eq(Rules.bankInterest(1000), 300);
  T.eq(Rules.bankInterest(333), 100);
});
T.test('spinCosts: Zinsen + Meds', () => {
  T.eq(Rules.spinCosts(base()), { interest: 0, meds: 0 });
  T.eq(Rules.spinCosts(base({ bankDebt: 200, kidneySold: true })), { interest: 60, meds: 20 });
});
T.test('maxBet: Guthaben minus Kosten, mindestens 1', () => {
  T.eq(Rules.maxBet(base()), 50);
  T.eq(Rules.maxBet(base({ bankDebt: 200, kidneySold: true })), 1);
  T.eq(Rules.maxBet(base({ balance: 500, bankDebt: 200 })), 440);
});
T.test('checkSpin: ungültiger Einsatz', () => {
  T.eq(Rules.checkSpin(base(), 0).ok, false);
  T.eq(Rules.checkSpin(base(), 0).reason, 'invalid');
  T.eq(Rules.checkSpin(base(), NaN).ok, false);
  T.eq(Rules.checkSpin(base(), -5).ok, false);
});
T.test('checkSpin: zu wenig Geld inkl. Kosten', () => {
  const r = Rules.checkSpin(base({ balance: 80, bankDebt: 200, kidneySold: true }), 10);
  T.eq(r, { ok: false, reason: 'funds', total: 90, interest: 60, meds: 20 });
});
T.test('checkSpin: ok', () => {
  T.eq(Rules.checkSpin(base({ balance: 100, bankDebt: 200, kidneySold: true }), 10), { ok: true, total: 90, interest: 60, meds: 20 });
  T.eq(Rules.checkSpin(base(), 50).ok, true);
  T.eq(Rules.checkSpin(base(), 51).ok, false);
});
T.test('mafiaBill = 3x', () => T.eq(Rules.mafiaBill(300), 900));
T.test('bankLoanAllowed: Limit 3000', () => {
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 2000 }), 1000), true);
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 2500 }), 1000), false);
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 3000 }), 200), false);
});
T.test('isGameOver: nur wenn negativ und beide Quellen zu', () => {
  T.eq(Rules.isGameOver(base({ balance: -10, bankDebt: 3000, mafiaDebt: 300 })), true);
  T.eq(Rules.isGameOver(base({ balance: 0, bankDebt: 3000, mafiaDebt: 300 })), false);
  T.eq(Rules.isGameOver(base({ balance: -10, bankDebt: 2000, mafiaDebt: 300 })), false);
  T.eq(Rules.isGameOver(base({ balance: -10, bankDebt: 3000, mafiaDebt: 0 })), false);
});
T.test('passiveTick / passivePerMin', () => {
  T.eq(Rules.passiveTick(base()), 0);
  T.eq(Rules.passiveTick(base({ hasHouse: true })), 3);
  T.eq(Rules.passiveTick(base({ hasHouse: true, hasDealer: true })), 8);
  T.eq(Rules.passivePerMin(base({ hasHouse: true, hasDealer: true })), 80);
});
T.test('PRICES', () => T.eq(Rules.PRICES, { beer: 50, brownie: 1000, brownieNext: 10000, kidney: 2000, house: 2500, tinder: 50, therapy: 5000, dealer: 5000 }));
```

- [ ] **Step 4: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: mehrere `FAIL … Rules.luck is not a function`, Exit-Code 1.

- [ ] **Step 5: Wirtschafts-Regeln implementieren**

Inhalt von `const Rules = { … }` ersetzen durch:

```js
const Rules = {
  PRICES: { beer: 50, brownie: 1000, brownieNext: 10000, kidney: 2000, house: 2500, tinder: 50, therapy: 5000, dealer: 5000 },
  MEDS_PER_SPIN: 20,
  HOSPITAL_RR: 100,
  HEARTBREAK_BILL: 250,
  BANK_LIMIT: 3000,
  BANK_RATE: 0.3,
  POST_PENALTY: 25,
  BEER_LUCK: [0, 10, 15, 20],
  BROWNIE_LUCK: 40,
  BEER_SPINS: 2,
  BROWNIE_SPINS: 1,
  MARRIAGE_SPINS: 2,
  MAFIA_SPINS: 5,
  MAX_BEERS: 3,

  luck(s) {
    let l = 0;
    if (s.beerTimer > 0) l += Rules.BEER_LUCK[Math.min(s.beers, 3)];
    if (s.brownieTimer > 0) l += Rules.BROWNIE_LUCK;
    return l;
  },
  bankInterest(debt) { return debt > 0 ? Math.round(debt * Rules.BANK_RATE) : 0; },
  spinCosts(s) {
    return { interest: Rules.bankInterest(s.bankDebt), meds: s.kidneySold ? Rules.MEDS_PER_SPIN : 0 };
  },
  maxBet(s) {
    const c = Rules.spinCosts(s);
    return Math.max(1, s.balance - c.interest - c.meds);
  },
  checkSpin(s, bet) {
    if (!Number.isFinite(bet) || bet <= 0) return { ok: false, reason: 'invalid' };
    const c = Rules.spinCosts(s);
    const total = bet + c.interest + c.meds;
    if (s.balance < total) return { ok: false, reason: 'funds', total, interest: c.interest, meds: c.meds };
    return { ok: true, total, interest: c.interest, meds: c.meds };
  },
  mafiaBill(debt) { return debt * 3; },
  bankLoanAllowed(s, amt) { return s.bankDebt + amt <= Rules.BANK_LIMIT; },
  isGameOver(s) { return s.balance < 0 && s.bankDebt >= Rules.BANK_LIMIT && s.mafiaDebt > 0; },
  passiveTick(s) { return (s.hasHouse ? 3 : 0) + (s.hasDealer ? 5 : 0); },
  passivePerMin(s) { return (s.hasHouse ? 30 : 0) + (s.hasDealer ? 50 : 0); },
};
```

- [ ] **Step 6: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs`
Expected: `15 bestanden, 0 fehlgeschlagen`, Exit-Code 0.

- [ ] **Step 7: Browser-Selbsttest prüfen**

Run: `tests/dom-selftest.sh`
Expected: `data-selftest="passed=15 failed=0"`

- [ ] **Step 8: Commit**

```bash
git add keller37.html tests/
git commit -m "feat: Gerüst, Test-Harness und Wirtschafts-Regeln

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Rules – Roulette & Slots

**Files:**
- Modify: `keller37.html` (`<script id="rules">`, `<script id="selftest">`)

**Interfaces:**
- Produces: `Rules.WHEEL`, `Rules.RED`, `Rules.isRed(n)`, `Rules.rouletteRoll(rng)`, `Rules.rouletteLuckOverride(type, chosen, rolled, luck, rng)`, `Rules.roulettePayout(type, chosen, rolled, bet)`; `Rules.SYMBOLS`, `Rules.slotRoll(rng)`, `Rules.slotLuckOverride(res, luck, rng)`, `Rules.slotMultiplier(a,b,c)`, `Rules.slotDelta(bet, m)`.
- `type` ist eins von `'red' | 'black' | 'even' | 'odd' | 'number'`. Payout/Delta-Funktionen liefern immer die **Kontostand-Differenz** (positiv = Gewinn, negativ = Verlust).

- [ ] **Step 1: Failing Tests schreiben**

Vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- Rules: Roulette ---- */
T.test('WHEEL hat 37 Fächer in Kesselreihenfolge', () => {
  T.eq(Rules.WHEEL.length, 37);
  T.eq(Rules.WHEEL.slice(0, 5), [0, 32, 15, 19, 4]);
  T.eq(Rules.WHEEL[36], 26);
});
T.test('isRed', () => { T.ok(Rules.isRed(1)); T.ok(Rules.isRed(36)); T.ok(!Rules.isRed(2)); T.ok(!Rules.isRed(0)); });
T.test('rouletteRoll: floor(rng*37)', () => {
  T.eq(Rules.rouletteRoll(seq(0)), 0);
  T.eq(Rules.rouletteRoll(seq(0.999)), 36);
});
T.test('rouletteLuckOverride: greift bei Glück, nicht bei 0', () => {
  T.eq(Rules.rouletteLuckOverride('red', null, 20, 40, seq(0.1)), 7);
  T.eq(Rules.rouletteLuckOverride('black', null, 20, 40, seq(0.1)), 8);
  T.eq(Rules.rouletteLuckOverride('number', 17, 20, 40, seq(0.1)), 17);
  T.eq(Rules.rouletteLuckOverride('even', null, 21, 40, seq(0.1)), 21, 'even unbeeinflusst');
  T.eq(Rules.rouletteLuckOverride('red', null, 0, 40, seq(0.1)), 0, 'Null bleibt');
  T.eq(Rules.rouletteLuckOverride('red', null, 20, 40, seq(0.5)), 20, 'rng 50 >= luck 40');
  T.eq(Rules.rouletteLuckOverride('red', null, 20, 0, seq(0)), 20, 'kein Glück');
});
T.test('roulettePayout: Farben 1:1, Null verliert', () => {
  T.eq(Rules.roulettePayout('red', null, 7, 10), 10);
  T.eq(Rules.roulettePayout('red', null, 8, 10), -10);
  T.eq(Rules.roulettePayout('black', null, 8, 10), 10);
  T.eq(Rules.roulettePayout('black', null, 0, 10), -10);
  T.eq(Rules.roulettePayout('red', null, 0, 10), -10);
});
T.test('roulettePayout: gerade/ungerade, Null verliert', () => {
  T.eq(Rules.roulettePayout('even', null, 4, 10), 10);
  T.eq(Rules.roulettePayout('even', null, 0, 10), -10);
  T.eq(Rules.roulettePayout('odd', null, 3, 10), 10);
  T.eq(Rules.roulettePayout('odd', null, 0, 10), -10);
});
T.test('roulettePayout: Zahl 35:1', () => {
  T.eq(Rules.roulettePayout('number', 17, 17, 10), 350);
  T.eq(Rules.roulettePayout('number', 0, 0, 10), 350);
  T.eq(Rules.roulettePayout('number', 17, 18, 10), -10);
});

/* ---- Rules: Slots ---- */
T.test('SYMBOLS', () => T.eq(Rules.SYMBOLS, ['🍒', '🍋', '🍇', '🔔', '💎', '7️⃣']));
T.test('slotRoll: drei Züge', () => T.eq(Rules.slotRoll(seq(0, 0.5, 0.99)), ['🍒', '🔔', '7️⃣']));
T.test('slotLuckOverride: Jackpot-Zweig', () => {
  T.eq(Rules.slotLuckOverride(['🍒', '🍋', '🍇'], 40, seq(0.1, 0.2, 0.4)), ['7️⃣', '7️⃣', '7️⃣']);
  T.eq(Rules.slotLuckOverride(['🍒', '🍋', '🍇'], 40, seq(0.1, 0.2, 0.6)), ['💎', '💎', '💎']);
});
T.test('slotLuckOverride: Paar-Zweig', () => {
  T.eq(Rules.slotLuckOverride(['🍒', '🍋', '🍇'], 40, seq(0.1, 0.5)), ['🍒', '🍒', '🍇']);
});
T.test('slotLuckOverride: kein Glück', () => {
  T.eq(Rules.slotLuckOverride(['🍒', '🍋', '🍇'], 40, seq(0.5)), ['🍒', '🍋', '🍇']);
  T.eq(Rules.slotLuckOverride(['🍒', '🍋', '🍇'], 0, seq(0)), ['🍒', '🍋', '🍇']);
});
T.test('slotMultiplier', () => {
  T.eq(Rules.slotMultiplier('7️⃣', '7️⃣', '7️⃣'), 50);
  T.eq(Rules.slotMultiplier('💎', '💎', '💎'), 25);
  T.eq(Rules.slotMultiplier('🔔', '🔔', '🔔'), 15);
  T.eq(Rules.slotMultiplier('🍒', '🍒', '🍒'), 5);
  T.eq(Rules.slotMultiplier('🍒', '🍒', '🍋'), 1.5);
  T.eq(Rules.slotMultiplier('🍒', '🍋', '🍒'), 1.5);
  T.eq(Rules.slotMultiplier('🍋', '🍒', '🍒'), 1.5);
  T.eq(Rules.slotMultiplier('🍒', '🍋', '🍇'), 0);
});
T.test('slotDelta', () => {
  T.eq(Rules.slotDelta(10, 50), 490);
  T.eq(Rules.slotDelta(10, 1.5), 5);
  T.eq(Rules.slotDelta(15, 1.5), 8, 'round(22.5)-15');
  T.eq(Rules.slotDelta(10, 0), -10);
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: FAIL-Zeilen für alle Roulette/Slots-Tests, Exit 1.

- [ ] **Step 3: Implementieren** – in `Rules` vor der schließenden `};` einfügen:

```js
  /* ---- Roulette ---- */
  WHEEL: [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26],
  RED: [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
  isRed(n) { return Rules.RED.includes(n); },
  rouletteRoll(rng) { return Math.floor(rng() * 37); },
  rouletteLuckOverride(type, chosen, rolled, luck, rng) {
    const r = rng() * 100;
    if (r < luck && rolled !== 0) {
      if (type === 'red') return 7;
      if (type === 'black') return 8;
      if (type === 'number') return chosen;
    }
    return rolled;
  },
  roulettePayout(type, chosen, rolled, bet) {
    const red = Rules.isRed(rolled);
    if (type === 'red' && red) return bet;
    if (type === 'black' && !red && rolled !== 0) return bet;
    if (type === 'even' && rolled !== 0 && rolled % 2 === 0) return bet;
    if (type === 'odd' && rolled % 2 !== 0) return bet;
    if (type === 'number' && rolled === chosen) return bet * 35;
    return -bet;
  },

  /* ---- Slots ---- */
  SYMBOLS: ['🍒', '🍋', '🍇', '🔔', '💎', '7️⃣'],
  slotRoll(rng) { return [0, 1, 2].map(() => Rules.SYMBOLS[Math.floor(rng() * Rules.SYMBOLS.length)]); },
  slotLuckOverride(res, luck, rng) {
    const [a, b, c] = res;
    if (rng() * 100 < luck) {
      if (rng() < 0.3) { const j = rng() < 0.5 ? '7️⃣' : '💎'; return [j, j, j]; }
      return [a, a, c];
    }
    return [a, b, c];
  },
  slotMultiplier(a, b, c) {
    if (a === b && b === c) return a === '7️⃣' ? 50 : a === '💎' ? 25 : a === '🔔' ? 15 : 5;
    if (a === b || b === c || a === c) return 1.5;
    return 0;
  },
  slotDelta(bet, m) { return m > 0 ? Math.round(bet * m) - bet : -bet; },
```

- [ ] **Step 4: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs`
Expected: `29 bestanden, 0 fehlgeschlagen`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Rules für Roulette und Slots

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Rules – Pferde, Russisches Roulette, Blackjack, Post, Anlagen, Leben

**Files:**
- Modify: `keller37.html` (`<script id="rules">`, `<script id="selftest">`)

**Interfaces:**
- Produces: `Rules.HORSES` (`[{id,name,col,dot}]`), `Rules.horseStep(isSelected, luck, rng)`, `Rules.horseDelta(won, bet)`; `Rules.rrCylinder(rng)`, `Rules.rrDelta(victim, bet)` (`victim: 'player'|'igor'`); `Rules.SUITS`, `Rules.VALUES`, `Rules.newDeck(rng)`, `Rules.cardValue(v)`, `Rules.handSum(hand)`, `Rules.dealerShouldHit(hand)`, `Rules.bjOutcome(pSum, dSum)` → `'bust'|'win'|'push'|'dealer'`, `Rules.bjDelta(outcome, bet)`; `Rules.POST_HOUSES`, `Rules.postmanTier(streak)` → `{t, r}`; `Rules.INVEST`, `Rules.investmentResolve(inv, rng)` → `{won, payout}`; `Rules.canBuyHouse(s)`, `Rules.canTinder(s)`, `Rules.canTherapy(s)`, `Rules.canDealer(s)`, `Rules.canBeer(s)`, `Rules.canBrownie(s)` → je `{ok, reason}`.

- [ ] **Step 1: Failing Tests schreiben**

Vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- Rules: Pferde ---- */
T.test('HORSES', () => T.eq(Rules.HORSES.map((x) => x.name), ['Blitz', 'Donner', 'Phantom', 'Lucky']));
T.test('horseStep: (rng*3+1)*1.5, Glück nur für gewähltes Pferd', () => {
  T.eq(Rules.horseStep(false, 40, seq(0)), 1.5);
  T.eq(Rules.horseStep(true, 0, seq(0)), 1.5);
  T.eq(Rules.horseStep(true, 40, seq(0)), 2.7);
  T.eq(Rules.horseStep(false, 0, seq(1)), 6);
});
T.test('horseDelta', () => { T.eq(Rules.horseDelta(true, 10), 30); T.eq(Rules.horseDelta(false, 10), -10); });

/* ---- Rules: Russisches Roulette ---- */
T.test('rrCylinder: 6 Kammern, eine Kugel', () => {
  const c = Rules.rrCylinder(seq(0.5));
  T.eq(c.length, 6);
  T.eq(c.filter(Boolean).length, 1);
  T.eq(c[3], true);
});
T.test('rrDelta', () => { T.eq(Rules.rrDelta('player', 10), -110); T.eq(Rules.rrDelta('igor', 10), 10); });

/* ---- Rules: Blackjack ---- */
T.test('newDeck: 52 eindeutige Karten', () => {
  const d = Rules.newDeck(Math.random);
  T.eq(d.length, 52);
  T.eq(new Set(d.map((c) => c.val + c.suit)).size, 52);
});
T.test('newDeck: rng=0 lässt Reihenfolge stehen', () => {
  const d = Rules.newDeck(seq(0));
  T.eq(d[0], { suit: '♠', val: '2' });
});
T.test('cardValue', () => { T.eq(Rules.cardValue('K'), 10); T.eq(Rules.cardValue('A'), 11); T.eq(Rules.cardValue('7'), 7); });
const H = (...vals) => vals.map((val) => ({ suit: '♠', val }));
T.test('handSum: Ass-Logik', () => {
  T.eq(Rules.handSum(H('A', 'K')), 21);
  T.eq(Rules.handSum(H('A', 'A', '9')), 21);
  T.eq(Rules.handSum(H('A', '9', '5')), 15);
  T.eq(Rules.handSum(H('K', 'Q', '5')), 25);
  T.eq(Rules.handSum([]), 0);
});
T.test('dealerShouldHit: unter 17', () => {
  T.ok(Rules.dealerShouldHit(H('K', '6')));
  T.ok(!Rules.dealerShouldHit(H('K', '7')));
  T.ok(!Rules.dealerShouldHit(H('A', '6')), 'Soft 17 steht');
});
T.test('bjOutcome', () => {
  T.eq(Rules.bjOutcome(22, 18), 'bust');
  T.eq(Rules.bjOutcome(20, 22), 'win');
  T.eq(Rules.bjOutcome(20, 18), 'win');
  T.eq(Rules.bjOutcome(18, 18), 'push');
  T.eq(Rules.bjOutcome(17, 18), 'dealer');
});
T.test('bjDelta', () => {
  T.eq(Rules.bjDelta('win', 10), 10); T.eq(Rules.bjDelta('bust', 10), -10);
  T.eq(Rules.bjDelta('dealer', 10), -10); T.eq(Rules.bjDelta('push', 10), 0);
});

/* ---- Rules: Post ---- */
T.test('POST_HOUSES', () => T.eq(Rules.POST_HOUSES.map((x) => x.n), [12, 45, 88, 99]));
T.test('postmanTier: Grenzen', () => {
  T.eq(Rules.postmanTier(0), { t: 5, r: 5 });
  T.eq(Rules.postmanTier(1), { t: 5, r: 5 });
  T.eq(Rules.postmanTier(2), { t: 3, r: 10 });
  T.eq(Rules.postmanTier(5), { t: 3, r: 10 });
  T.eq(Rules.postmanTier(6), { t: 1.5, r: 25 });
  T.eq(Rules.postmanTier(10), { t: 1.5, r: 25 });
  T.eq(Rules.postmanTier(11), { t: 0.5, r: 50 });
});

/* ---- Rules: Anlagen ---- */
T.test('INVEST', () => {
  T.eq(Rules.INVEST.bank, { name: 'Festgeld', rate: 0.08, spins: 5, risk: 10, min: 10 });
  T.eq(Rules.INVEST.stock, { name: 'Aktien', rate: 1.0, spins: 2, risk: 85, min: 10 });
  T.eq(Rules.INVEST.scam, { name: 'Trickbetrug', rate: 0.3, spins: 10, risk: 55, min: 10 });
});
T.test('investmentResolve: rng*100 >= risk gewinnt', () => {
  const inv = { amount: 100, rate: 0.08, risk: 10 };
  T.eq(Rules.investmentResolve(inv, seq(0.10)), { won: true, payout: 108 });
  T.eq(Rules.investmentResolve(inv, seq(0.09)), { won: false, payout: 0 });
  T.eq(Rules.investmentResolve({ amount: 33, rate: 1.0, risk: 85 }, seq(0.9)), { won: true, payout: 66 });
});

/* ---- Rules: Leben ---- */
T.test('canBuyHouse', () => {
  T.eq(Rules.canBuyHouse(base({ balance: 2500 })), { ok: true });
  T.eq(Rules.canBuyHouse(base({ balance: 2499 })), { ok: false, reason: 'funds' });
  T.eq(Rules.canBuyHouse(base({ balance: 9999, hasHouse: true })), { ok: false, reason: 'owned' });
  T.eq(Rules.canBuyHouse(base({ balance: 9999, bankDebt: 1 })), { ok: false, reason: 'debts' });
  T.eq(Rules.canBuyHouse(base({ balance: 9999, mafiaDebt: 1 })), { ok: false, reason: 'debts' });
  T.eq(Rules.canBuyHouse(base({ balance: 9999, isHeartbroken: true })), { ok: false, reason: 'heartbroken' });
  T.eq(Rules.canBuyHouse(base({ balance: 9999, isMarried: true })), { ok: false, reason: 'married' });
});
T.test('canTinder', () => {
  T.eq(Rules.canTinder(base({ balance: 50, hasHouse: true })), { ok: true });
  T.eq(Rules.canTinder(base({ balance: 50 })), { ok: false, reason: 'house' });
  T.eq(Rules.canTinder(base({ balance: 50, hasHouse: true, isMarried: true })), { ok: false, reason: 'married' });
  T.eq(Rules.canTinder(base({ balance: 50, hasHouse: true, isHeartbroken: true })), { ok: false, reason: 'heartbroken' });
  T.eq(Rules.canTinder(base({ balance: 49, hasHouse: true })), { ok: false, reason: 'funds' });
});
T.test('canTherapy / canDealer', () => {
  T.eq(Rules.canTherapy(base({ balance: 5000, isHeartbroken: true })), { ok: true });
  T.eq(Rules.canTherapy(base({ balance: 5000 })), { ok: false, reason: 'notNeeded' });
  T.eq(Rules.canTherapy(base({ balance: 4999, isHeartbroken: true })), { ok: false, reason: 'funds' });
  T.eq(Rules.canDealer(base({ balance: 5000 })), { ok: true });
  T.eq(Rules.canDealer(base({ balance: 5000, hasDealer: true })), { ok: false, reason: 'owned' });
  T.eq(Rules.canDealer(base({ balance: 4999 })), { ok: false, reason: 'funds' });
});
T.test('canBeer / canBrownie', () => {
  T.eq(Rules.canBeer(base()), { ok: true });
  T.eq(Rules.canBeer(base({ beers: 3 })), { ok: false, reason: 'max' });
  T.eq(Rules.canBeer(base({ balance: 49 })), { ok: false, reason: 'funds' });
  T.eq(Rules.canBrownie(base({ balance: 1000, brownieCost: 1000 })), { ok: true });
  T.eq(Rules.canBrownie(base({ balance: 1000, brownieCost: 1000, brownieTimer: 1 })), { ok: false, reason: 'active' });
  T.eq(Rules.canBrownie(base({ balance: 999, brownieCost: 1000 })), { ok: false, reason: 'funds' });
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs` → FAIL für alle neuen Tests.

- [ ] **Step 3: Implementieren** – in `Rules` vor `};` einfügen:

```js
  /* ---- Pferde ---- */
  HORSES: [
    { id: 1, name: 'Blitz', col: '#ff3b3b', dot: '🔴' },
    { id: 2, name: 'Donner', col: '#4cc9f0', dot: '🔵' },
    { id: 3, name: 'Phantom', col: '#b066ff', dot: '🟣' },
    { id: 4, name: 'Lucky', col: '#ffd23f', dot: '🟡' },
  ],
  horseStep(isSelected, luck, rng) {
    let step = rng() * 3 + 1;
    if (isSelected && luck > 0) step += luck * 0.02;
    return step * 1.5;
  },
  horseDelta(won, bet) { return won ? bet * 3 : -bet; },

  /* ---- Russisches Roulette ---- */
  rrCylinder(rng) {
    const c = [false, false, false, false, false, false];
    c[Math.floor(rng() * 6)] = true;
    return c;
  },
  rrDelta(victim, bet) { return victim === 'player' ? -(bet + Rules.HOSPITAL_RR) : bet; },

  /* ---- Blackjack ---- */
  SUITS: ['♠', '♥', '♦', '♣'],
  VALUES: ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'],
  newDeck(rng) {
    const d = [];
    for (const suit of Rules.SUITS) for (const val of Rules.VALUES) d.push({ suit, val });
    for (let i = d.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [d[i], d[j]] = [d[j], d[i]];
    }
    return d;
  },
  cardValue(v) { return ['J', 'Q', 'K'].includes(v) ? 10 : v === 'A' ? 11 : parseInt(v, 10); },
  handSum(hand) {
    let s = 0, aces = 0;
    for (const c of hand) { s += Rules.cardValue(c.val); if (c.val === 'A') aces++; }
    while (s > 21 && aces > 0) { s -= 10; aces--; }
    return s;
  },
  dealerShouldHit(hand) { return Rules.handSum(hand) < 17; },
  bjOutcome(pSum, dSum) {
    if (pSum > 21) return 'bust';
    if (dSum > 21 || pSum > dSum) return 'win';
    if (pSum === dSum) return 'push';
    return 'dealer';
  },
  bjDelta(outcome, bet) { return outcome === 'win' ? bet : outcome === 'push' ? 0 : -bet; },

  /* ---- Post ---- */
  POST_HOUSES: [{ n: 12, c: '#ffb432' }, { n: 45, c: '#4cc9f0' }, { n: 88, c: '#3ddc84' }, { n: 99, c: '#ff3b3b' }],
  postmanTier(streak) {
    if (streak < 2) return { t: 5, r: 5 };
    if (streak < 6) return { t: 3, r: 10 };
    if (streak < 11) return { t: 1.5, r: 25 };
    return { t: 0.5, r: 50 };
  },

  /* ---- Anlagen ---- */
  INVEST: {
    bank: { name: 'Festgeld', rate: 0.08, spins: 5, risk: 10, min: 10 },
    stock: { name: 'Aktien', rate: 1.0, spins: 2, risk: 85, min: 10 },
    scam: { name: 'Trickbetrug', rate: 0.3, spins: 10, risk: 55, min: 10 },
  },
  investmentResolve(inv, rng) {
    const won = rng() * 100 >= inv.risk;
    return { won, payout: won ? Math.round(inv.amount * (1 + inv.rate)) : 0 };
  },

  /* ---- Leben ---- */
  canBuyHouse(s) {
    if (s.hasHouse) return { ok: false, reason: 'owned' };
    if (s.bankDebt > 0 || s.mafiaDebt > 0) return { ok: false, reason: 'debts' };
    if (s.isHeartbroken) return { ok: false, reason: 'heartbroken' };
    if (s.isMarried) return { ok: false, reason: 'married' };
    if (s.balance < Rules.PRICES.house) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
  canTinder(s) {
    if (!s.hasHouse) return { ok: false, reason: 'house' };
    if (s.isMarried) return { ok: false, reason: 'married' };
    if (s.isHeartbroken) return { ok: false, reason: 'heartbroken' };
    if (s.balance < Rules.PRICES.tinder) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
  canTherapy(s) {
    if (!s.isHeartbroken) return { ok: false, reason: 'notNeeded' };
    if (s.balance < Rules.PRICES.therapy) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
  canDealer(s) {
    if (s.hasDealer) return { ok: false, reason: 'owned' };
    if (s.balance < Rules.PRICES.dealer) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
  canBeer(s) {
    if (s.beers >= Rules.MAX_BEERS) return { ok: false, reason: 'max' };
    if (s.balance < Rules.PRICES.beer) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
  canBrownie(s) {
    if (s.brownieTimer > 0) return { ok: false, reason: 'active' };
    if (s.balance < s.brownieCost) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
```

- [ ] **Step 4: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs`
Expected: `49 bestanden, 0 fehlgeschlagen`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Rules für Pferde, RR, Blackjack, Post, Anlagen, Leben

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: State & Bus

**Files:**
- Modify: `keller37.html` (neue Blöcke `<script id="state">`, `<script id="bus">` direkt nach `<script id="util">`; Tests in selftest)

**Interfaces:**
- Produces: `State.VERSION`, `State.KEY`, `State.META_KEY`, `State.s` (Spielstand), `State.meta` (Achievements, Mute, GameOvers), `State.fresh()`, `State.freshMeta()`, `State.init(storage)` → `{loaded}`, `State.save()`, `State.saveMeta()`, `State.reset()`; `Bus.on(name, fn)` → unsubscribe-fn, `Bus.off(name, fn)`, `Bus.emit(name, payload)` → `Promise<results[]>`.
- State-Form exakt wie Spec 3.3 (`flags` hat zusätzlich `bankLimit`).

- [ ] **Step 1: Failing Tests schreiben**

Vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- State ---- */
const memStorage = () => ({
  data: {},
  getItem(k) { return k in this.data ? this.data[k] : null; },
  setItem(k, v) { this.data[k] = String(v); },
  removeItem(k) { delete this.data[k]; },
});
T.test('State.init: leer → frisch, loaded=false', () => {
  const st = memStorage();
  T.eq(State.init(st), { loaded: false });
  T.eq(State.s.balance, 50);
  T.eq(State.s.v, 1);
  T.eq(State.s.flags, { intro: false, mafiaLoan: false, bankLoan: false, bankLimit: false, brownie: false, igor: false });
  T.eq(State.meta, { v: 1, achievements: [], muted: false, gameOvers: 0 });
});
T.test('State.save/init: Spielstand überlebt', () => {
  const st = memStorage();
  State.init(st);
  State.s.balance = 1234; State.s.hasHouse = true; State.s.investments.push({ name: 'Festgeld', amount: 50, rate: 0.08, spins: 5, risk: 10 });
  State.save();
  T.ok(st.getItem('keller37.state').includes('1234'));
  T.eq(State.init(st), { loaded: true });
  T.eq(State.s.balance, 1234);
  T.eq(State.s.hasHouse, true);
  T.eq(State.s.investments.length, 1);
});
T.test('State.init: falsche Version oder Müll → frisch', () => {
  const st = memStorage();
  st.setItem('keller37.state', JSON.stringify({ v: 99, balance: 5 }));
  T.eq(State.init(st), { loaded: false });
  T.eq(State.s.balance, 50);
  st.setItem('keller37.state', '{kaputt');
  T.eq(State.init(st), { loaded: false });
});
T.test('State.init: fehlende Felder werden aufgefüllt', () => {
  const st = memStorage();
  st.setItem('keller37.state', JSON.stringify({ v: 1, balance: 70, flags: { intro: true } }));
  State.init(st);
  T.eq(State.s.balance, 70);
  T.eq(State.s.flags.intro, true);
  T.eq(State.s.flags.igor, false);
  T.eq(State.s.stats.spins, 0);
});
T.test('State.reset: Spielstand frisch, meta bleibt', () => {
  const st = memStorage();
  State.init(st);
  State.s.balance = 9; State.meta.achievements.push('firstWin'); State.saveMeta();
  State.reset();
  T.eq(State.s.balance, 50);
  T.eq(State.meta.achievements, ['firstWin']);
  T.eq(State.init(st), { loaded: true });
  T.eq(State.meta.achievements, ['firstWin']);
});

/* ---- Bus ---- */
T.test('Bus.emit ohne Handler liefert ein Promise', () => {
  T.ok(Bus.emit('nix', {}) instanceof Promise);
});
T.test('Bus.on/off/emit synchron sichtbar', () => {
  const seen = [];
  const off = Bus.on('t1', (p) => { seen.push(p.x); return p.x * 2; });
  Bus.emit('t1', { x: 2 });
  T.eq(seen, [2]);
  off();
  Bus.emit('t1', { x: 3 });
  T.eq(seen, [2]);
});
```

Hinweis: Promise-Auflösung kann der synchrone Runner nicht abwarten; die `async`-Semantik wird in Step 3 durch die Implementierung und in Task 7 (Cutscene wartet auf `emit`) manuell geprüft.

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs` → `State is not defined` / `Bus is not defined`.

- [ ] **Step 3: State und Bus implementieren** – nach `</script>` von `util` einfügen:

```html
<script id="state">
/* ================= STATE – ein Objekt, localStorage, versioniert ================= */
const State = {
  VERSION: 1,
  KEY: 'keller37.state',
  META_KEY: 'keller37.meta',
  s: null,
  meta: null,
  storage: null,
  fresh() {
    return {
      v: 1,
      balance: 50,
      beers: 0, beerTimer: 0,
      brownieTimer: 0, brownieCost: 1000,
      kidneySold: false,
      bankDebt: 0, mafiaDebt: 0, mafiaSpins: 0,
      investments: [],
      hasHouse: false, isMarried: false, marriageSpins: 0, isHeartbroken: false, hasDealer: false,
      flags: { intro: false, mafiaLoan: false, bankLoan: false, bankLimit: false, brownie: false, igor: false },
      stats: { spins: 0, maxBalance: 50, biggestWin: 0, kidneys: 0, postStreakBest: 0 },
      selectedHorse: 1,
    };
  },
  freshMeta() { return { v: 1, achievements: [], muted: false, gameOvers: 0 }; },
  _read(key, freshFn) {
    try {
      const raw = this.storage.getItem(key);
      if (!raw) return { value: freshFn(), loaded: false };
      const p = JSON.parse(raw);
      if (!p || p.v !== this.VERSION) return { value: freshFn(), loaded: false };
      const f = freshFn();
      const merged = Object.assign(f, p);
      if (f.flags) merged.flags = Object.assign(freshFn().flags, p.flags || {});
      if (f.stats) merged.stats = Object.assign(freshFn().stats, p.stats || {});
      return { value: merged, loaded: true };
    } catch (e) {
      return { value: freshFn(), loaded: false };
    }
  },
  init(storage) {
    this.storage = storage;
    const s = this._read(this.KEY, () => this.fresh());
    const m = this._read(this.META_KEY, () => this.freshMeta());
    this.s = s.value;
    this.meta = m.value;
    return { loaded: s.loaded };
  },
  save() { try { this.storage.setItem(this.KEY, JSON.stringify(this.s)); } catch (e) { /* privater Modus o.ä. */ } },
  saveMeta() { try { this.storage.setItem(this.META_KEY, JSON.stringify(this.meta)); } catch (e) { /* ignorieren */ } },
  reset() { this.s = this.fresh(); this.save(); },
};
</script>

<script id="bus">
/* ================= BUS – Spiellogik → Cutscenes/Sound/Achievements ================= */
const Bus = {
  handlers: new Map(),
  on(name, fn) {
    if (!this.handlers.has(name)) this.handlers.set(name, []);
    this.handlers.get(name).push(fn);
    return () => this.off(name, fn);
  },
  off(name, fn) {
    const list = this.handlers.get(name);
    if (!list) return;
    const i = list.indexOf(fn);
    if (i >= 0) list.splice(i, 1);
  },
  emit(name, payload = {}) {
    const list = (this.handlers.get(name) || []).slice();
    const results = list.map((fn) => { try { return Promise.resolve(fn(payload)); } catch (e) { console.error('[bus]', name, e); return Promise.resolve(); } });
    return Promise.all(results);
  },
};
</script>
```

- [ ] **Step 4: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs` → `56 bestanden, 0 fehlgeschlagen`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: State mit localStorage und Event-Bus

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: SFX – synthetisierter Sound

**Files:**
- Modify: `keller37.html` (neuer Block `<script id="sfx">` nach `bus`)

**Interfaces:**
- Consumes: `State.meta.muted`, `State.saveMeta()`.
- Produces: `SFX.init()`, `SFX.play(name)`, `SFX.loop(name, ms)`, `SFX.stop(name)`, `SFX.stopAll()`, `SFX.setMuted(bool)`, `SFX.muted` (Getter). Sound-Namen: `click, chip, coin, cash, lose, reelSpin, reelStop, ballTick, whinny, gallop, heartbeat, dryfire, gunshot, cardSlide, neonBuzz, typewriter, unlock, stamp, dog, blackout`.
- `SFX.init()` wird automatisch beim ersten `pointerdown`/`keydown` aufgerufen (Autoplay-Regel der Browser). Vorher ist `play()` ein No-op.

- [ ] **Step 1: SFX-Block einfügen** – nach `</script>` von `bus`:

```html
<script id="sfx">
/* ================= SFX – Web-Audio-Synth, keine Dateien ================= */
const SFX = {
  ctx: null,
  master: null,
  loops: new Map(),
  get muted() { return !!(State.meta && State.meta.muted); },
  init() {
    if (this.ctx) { if (this.ctx.state === 'suspended') this.ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = this.muted ? 0 : 0.5;
    this.master.connect(this.ctx.destination);
  },
  setMuted(m) {
    if (State.meta) { State.meta.muted = m; State.saveMeta(); }
    if (this.master) this.master.gain.value = m ? 0 : 0.5;
    if (m) this.stopAll();
  },
  tone({ freq = 440, type = 'sine', dur = 0.1, vol = 0.3, slide = 0, delay = 0 }) {
    const t0 = this.ctx.currentTime + delay;
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t0);
    if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(20, freq + slide), t0 + dur);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(vol, t0 + 0.006);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g).connect(this.master);
    o.start(t0);
    o.stop(t0 + dur + 0.02);
  },
  noise({ dur = 0.1, vol = 0.3, freq = 1000, type = 'lowpass', delay = 0 }) {
    const t0 = this.ctx.currentTime + delay;
    const len = Math.max(1, Math.floor(this.ctx.sampleRate * dur));
    const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    const f = this.ctx.createBiquadFilter();
    f.type = type; f.frequency.value = freq;
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(vol, t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(f).connect(g).connect(this.master);
    src.start(t0);
    src.stop(t0 + dur + 0.02);
  },
  play(name) {
    if (!this.ctx || this.muted) return;
    const f = this.LIB[name];
    if (!f) { console.warn('[sfx] unbekannt:', name); return; }
    try { f.call(this); } catch (e) { console.error('[sfx]', name, e); }
  },
  loop(name, ms) {
    this.stop(name);
    this.play(name);
    this.loops.set(name, setInterval(() => this.play(name), ms));
  },
  stop(name) {
    const id = this.loops.get(name);
    if (id) { clearInterval(id); this.loops.delete(name); }
  },
  stopAll() { for (const k of [...this.loops.keys()]) this.stop(k); },
  LIB: {
    click() { this.tone({ freq: 1200, type: 'square', dur: 0.03, vol: 0.12 }); },
    chip() { this.tone({ freq: 2200, type: 'triangle', dur: 0.05, vol: 0.2 }); this.tone({ freq: 1800, type: 'triangle', dur: 0.06, vol: 0.15, delay: 0.04 }); },
    coin() { this.tone({ freq: 1760, type: 'square', dur: 0.08, vol: 0.15 }); this.tone({ freq: 2349, type: 'square', dur: 0.18, vol: 0.15, delay: 0.07 }); },
    cash() { [523, 659, 784, 1047].forEach((f, i) => this.tone({ freq: f, type: 'triangle', dur: 0.25, vol: 0.2, delay: i * 0.07 })); },
    lose() { this.tone({ freq: 220, type: 'sawtooth', dur: 0.4, vol: 0.2, slide: -150 }); },
    reelSpin() { this.noise({ dur: 0.12, vol: 0.08, freq: 600 }); },
    reelStop() { this.noise({ dur: 0.08, vol: 0.2, freq: 1200 }); this.tone({ freq: 300, type: 'square', dur: 0.08, vol: 0.15 }); },
    ballTick() { this.tone({ freq: 2600, type: 'square', dur: 0.012, vol: 0.08 }); },
    whinny() { this.tone({ freq: 900, type: 'sawtooth', dur: 0.35, vol: 0.12, slide: -500 }); this.noise({ dur: 0.3, vol: 0.05, freq: 2000, type: 'highpass' }); },
    gallop() { this.noise({ dur: 0.05, vol: 0.12, freq: 250 }); this.noise({ dur: 0.05, vol: 0.1, freq: 250, delay: 0.09 }); },
    heartbeat() { this.tone({ freq: 60, type: 'sine', dur: 0.12, vol: 0.5 }); this.tone({ freq: 50, type: 'sine', dur: 0.15, vol: 0.4, delay: 0.16 }); },
    dryfire() { this.tone({ freq: 800, type: 'square', dur: 0.02, vol: 0.2 }); this.noise({ dur: 0.05, vol: 0.15, freq: 3000, type: 'highpass' }); },
    gunshot() { this.noise({ dur: 0.45, vol: 0.6, freq: 900 }); this.tone({ freq: 90, type: 'sine', dur: 0.4, vol: 0.5, slide: -60 }); },
    cardSlide() { this.noise({ dur: 0.09, vol: 0.12, freq: 3500, type: 'highpass' }); },
    neonBuzz() { this.tone({ freq: 60, type: 'sawtooth', dur: 0.12, vol: 0.05 }); this.tone({ freq: 120, type: 'square', dur: 0.1, vol: 0.03 }); },
    typewriter() { this.tone({ freq: 3000 + Math.random() * 800, type: 'square', dur: 0.012, vol: 0.05 }); },
    unlock() { [784, 988, 1175, 1568].forEach((f, i) => this.tone({ freq: f, type: 'sine', dur: 0.3, vol: 0.2, delay: i * 0.09 })); },
    stamp() { this.noise({ dur: 0.08, vol: 0.3, freq: 500 }); this.tone({ freq: 150, type: 'square', dur: 0.1, vol: 0.2 }); },
    dog() { this.tone({ freq: 500, type: 'sawtooth', dur: 0.12, vol: 0.2, slide: 200 }); this.tone({ freq: 450, type: 'sawtooth', dur: 0.14, vol: 0.2, slide: 250, delay: 0.18 }); },
    blackout() { this.tone({ freq: 80, type: 'sine', dur: 0.8, vol: 0.3, slide: -50 }); },
  },
};
document.addEventListener('pointerdown', () => SFX.init(), { capture: true });
document.addEventListener('keydown', () => SFX.init(), { capture: true });
</script>
```

- [ ] **Step 2: Manuell prüfen**

`keller37.html` im Browser öffnen (Doppelklick), einmal in die Seite klicken, in der Konsole:
```js
State.init(localStorage); ['click','chip','coin','cash','lose','reelStop','gunshot','heartbeat','unlock','dog'].forEach((n, i) => setTimeout(() => SFX.play(n), i * 500));
```
Expected: zehn unterschiedliche Sounds im Halbsekundentakt, keine Fehler in der Konsole. Dann `SFX.setMuted(true); SFX.play('cash')` → Stille.

- [ ] **Step 3: Node-Tests weiterhin grün**

Run: `node tests/run-selftest.mjs` → `56 bestanden`.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat: SFX-Modul mit Web-Audio-Synth

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Shell – Basis-CSS, Wallet, Seitenleiste, Router, Hub, Toasts

**Files:**
- Modify: `keller37.html` (CSS-Sektionen 2, 3, 4, 7; Template `tpl-hub`; neuer Block `<script id="ui">` nach `sfx`; `boot`)

**Interfaces:**
- Consumes: `State`, `Rules`, `SFX`, `Bus`, `h/qs/qsa/wait`.
- Produces: `UI.fmt(n)`, `UI.register(id, {template, mount(root), unmount()})`, `UI.show(id)`, `UI.current` (`{id, def}`), `UI.toast({icon,title,text,tone,ms})` (tone: `info|win|loss|gold|pink`), `UI.setBalance(target, {animate, duration})`, `UI.pulseBalance(delta)`, `UI.floatNumber(delta, fromEl)`, `UI.shake(el)`, `UI.renderWallet()`, `UI.renderSide()`, `UI.mountShell()`; `Actions` (Objekt, Seitenleisten-Aktionen `beer|brownie|kidney|finance|invest|life`; Task 8 füllt `beer/brownie/kidney`); CSS-Klassen `.panel .panel.stretch .btn (.red .blue .green .pink .ghost .solid) .chip[data-v] .bet-bar .bet-field .chalk .paper .status .win .loss .neon .felt .hidden .money-live`.
- Alle Elemente mit Klasse `money-live` zeigen den Kontostand (Wallet und später das Cutscene-Overlay).

- [ ] **Step 1: CSS-Sektionen 2, 3, 4 und 7 füllen**

Unter `/* ==== 2. BASIS & TEXTUR ==== */`:

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { min-height: 100%; }
body { background: var(--bg); color: var(--text); font-family: var(--font-body); font-size: 15px; line-height: 1.45; overflow-x: hidden; }
button { font-family: inherit; cursor: pointer; color: inherit; }
input { font-family: var(--font-mono); }
.grain { position: fixed; inset: 0; pointer-events: none; z-index: 90; opacity: .06; background-size: 200px 200px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
.vignette { position: fixed; inset: 0; pointer-events: none; z-index: 89; background: radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.75) 100%); }
.felt { background: repeating-linear-gradient(45deg, rgba(255,255,255,.02) 0 2px, transparent 2px 4px), radial-gradient(ellipse at 50% 30%, #145240 0%, var(--felt) 45%, var(--felt-2) 100%); }
.neon { font-family: var(--font-display); letter-spacing: .08em; text-transform: uppercase; color: #fff;
  text-shadow: 0 0 4px #fff, 0 0 10px var(--neon, var(--neon-amber)), 0 0 24px var(--neon, var(--neon-amber)), 0 0 48px var(--neon, var(--neon-amber));
  animation: neonFlicker 7s infinite; }
.hidden { display: none !important; }
```

Unter `/* ==== 3. LAYOUT ==== */`:

```css
.shell { min-height: 100vh; display: flex; flex-direction: column; }
.wallet { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  padding: 10px 20px; background: rgba(12,14,10,.92); border-bottom: 1px solid rgba(201,162,39,.25); backdrop-filter: blur(6px); }
.wallet-mid { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; flex: 1; }
.wallet-right { display: flex; align-items: center; gap: 8px; }
.brand { background: none; border: 0; font-size: 2rem; line-height: 1; padding: 2px 6px; }
.notes { display: flex; gap: 8px; flex-wrap: wrap; }
.note { font-family: var(--font-mono); font-size: .78rem; background: var(--paper); color: var(--paper-ink); padding: 3px 8px; transform: rotate(-1.5deg);
  box-shadow: 2px 3px 6px rgba(0,0,0,.5); animation: popIn .25s ease both; }
.note:nth-child(even) { transform: rotate(1.2deg); }
.note.danger { background: #f2b2a6; }
.note.pink { background: #f3c0d8; }
.note.gold { background: #f2dc9a; }
.luck { display: flex; align-items: center; gap: 4px; font-size: 1rem; }
.luck .seg { width: 14px; height: 10px; border-radius: 2px; background: #2a2e26; border: 1px solid #3a3f35; }
.luck .seg.on { background: var(--neon-green); box-shadow: 0 0 8px var(--neon-green); }
.luck .luck-val { font-family: var(--font-mono); font-size: .8rem; color: var(--dim); margin-left: 4px; }
.balance { font-family: var(--font-mono); font-size: 1.6rem; font-weight: 700; color: var(--gold-2); padding: 6px 14px; border: 1px solid rgba(201,162,39,.4);
  border-radius: 8px; background: rgba(0,0,0,.4); min-width: 150px; text-align: right; }
.balance.up { animation: pulseGold .6s ease both; }
.balance.down { animation: pulseRed .6s ease both; }
.icon-btn { background: transparent; border: 1px solid rgba(255,255,255,.12); border-radius: 6px; width: 34px; height: 34px; font-size: 1rem; }
.icon-btn:hover { border-color: var(--gold); }
.body { flex: 1; display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 18px; padding: 18px 20px 40px; max-width: 1180px; width: 100%; margin: 0 auto; }
.stage { min-width: 0; position: relative; transition: opacity .25s ease, transform .25s ease; }
.stage.leaving { opacity: 0; transform: translateY(-8px); transition-duration: .18s; pointer-events: none; }
.stage.entering { animation: screenIn .25s ease both; }
.side { display: flex; flex-direction: column; gap: 14px; }
.side-sec { background: var(--panel); border: 1px solid rgba(255,255,255,.06); border-radius: var(--radius); padding: 10px 12px; box-shadow: var(--shadow); }
.side-sec h3 { font-family: var(--font-display); letter-spacing: .12em; font-size: 1.05rem; color: var(--dim); margin-bottom: 8px; }
.side-btn { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 8px 10px; margin-bottom: 6px; background: var(--panel-2);
  border: 1px solid rgba(255,255,255,.06); border-radius: 8px; font-size: .9rem; text-align: left; transition: transform .12s, border-color .12s, background .12s; }
.side-btn:hover:not(:disabled) { border-color: var(--gold); background: #22261f; transform: translateX(2px); }
.side-btn:disabled { opacity: .45; cursor: not-allowed; }
.side-btn .price { font-family: var(--font-mono); color: var(--gold-2); font-size: .85rem; }
.side-hint { font-size: .75rem; color: var(--dim); font-family: var(--font-mono); }
/* Hub */
.hub { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.door { position: relative; height: 220px; border-radius: 8px 8px 4px 4px; background: linear-gradient(180deg, #2a2118, #17120d); border: 2px solid #3a2e20;
  box-shadow: inset 0 0 0 6px #1d1610, inset 0 -40px 60px rgba(0,0,0,.6), var(--shadow); cursor: pointer; display: flex; flex-direction: column; align-items: center;
  padding-top: 22px; gap: 12px; overflow: hidden; transition: transform .2s; --neon: var(--neon-amber); }
.door::after { content: ""; position: absolute; left: 10%; right: 10%; bottom: 0; height: 6px; background: var(--neon); filter: blur(6px); opacity: 0; transition: opacity .25s; }
.door:hover { transform: translateY(-3px); }
.door:hover::after { opacity: .9; }
.door:hover .sign { opacity: 1; }
.door .sign { font-family: var(--font-display); font-size: 1.7rem; letter-spacing: .1em; color: #fff; padding: 2px 14px; border: 2px solid var(--neon); border-radius: 6px; opacity: .8;
  text-shadow: 0 0 6px #fff, 0 0 14px var(--neon), 0 0 30px var(--neon); box-shadow: 0 0 12px var(--neon), inset 0 0 12px rgba(255,255,255,.08); transition: opacity .2s; }
.door .glyph { font-size: 2.6rem; filter: drop-shadow(0 4px 6px rgba(0,0,0,.7)); }
.door .chalk-tag { font-family: var(--font-mono); font-size: .8rem; color: #d8d2c0; background: #1a1a1a; border: 1px solid #333; padding: 3px 10px; border-radius: 3px; transform: rotate(-2deg); }
.door .knob { position: absolute; right: 22px; top: 52%; width: 12px; height: 12px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, var(--gold-2), #6b5313); box-shadow: 0 1px 3px #000; }
.door.day { background: linear-gradient(180deg, #6a6250, #3b3629); border-color: #8a8060; }
.door.day::before { content: ""; position: absolute; inset: 8px; background: linear-gradient(180deg, rgba(245,214,122,.25), transparent 60%); pointer-events: none; }
.door.day .sign { color: #fff7dd; }
```

Unter `/* ==== 4. KOMPONENTEN ==== */`:

```css
.panel { background: var(--panel); border: 1px solid rgba(255,255,255,.06); border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px; display: flex; flex-direction: column; gap: 16px; align-items: center; }
.panel.stretch { align-items: stretch; }
.panel h2 { font-family: var(--font-display); letter-spacing: .12em; font-size: 1.6rem; }
.btn { font-family: var(--font-display); font-size: 1.1rem; letter-spacing: .1em; text-transform: uppercase; padding: 9px 20px; border-radius: 6px; --c: var(--gold);
  border: 2px solid var(--c); background: rgba(201,162,39,.08); color: var(--gold-2); transition: transform .1s, box-shadow .15s, background .15s; }
.btn:hover:not(:disabled) { background: rgba(201,162,39,.18); box-shadow: 0 0 14px rgba(201,162,39,.35), inset 0 0 10px rgba(201,162,39,.15); }
.btn:active:not(:disabled) { transform: scale(.97); }
.btn:disabled { opacity: .35; cursor: not-allowed; }
.btn.red { --c: var(--neon-red); color: #ffb3b3; background: rgba(255,59,59,.08); }
.btn.red:hover:not(:disabled) { background: rgba(255,59,59,.2); box-shadow: 0 0 14px rgba(255,59,59,.4); }
.btn.blue { --c: var(--neon-blue); color: #bfeeff; background: rgba(76,201,240,.08); }
.btn.blue:hover:not(:disabled) { background: rgba(76,201,240,.2); box-shadow: 0 0 14px rgba(76,201,240,.4); }
.btn.green { --c: var(--neon-green); color: #c8ffe0; background: rgba(61,220,132,.08); }
.btn.green:hover:not(:disabled) { background: rgba(61,220,132,.2); box-shadow: 0 0 14px rgba(61,220,132,.4); }
.btn.pink { --c: var(--neon-pink); color: #ffd0e4; background: rgba(255,95,162,.08); }
.btn.pink:hover:not(:disabled) { background: rgba(255,95,162,.2); box-shadow: 0 0 14px rgba(255,95,162,.4); }
.btn.ghost { --c: rgba(255,255,255,.2); color: var(--text); background: rgba(255,255,255,.04); }
.btn.ghost:hover:not(:disabled) { background: rgba(255,255,255,.1); box-shadow: none; }
.btn.solid { background: var(--gold); color: #1a1408; }
.btn.solid:hover:not(:disabled) { background: var(--gold-2); }
.btn.sm { font-size: .95rem; padding: 6px 12px; }
.chip { width: 46px; height: 46px; border-radius: 50%; border: 4px dashed #fff; background: var(--chip, #b3261e); color: #fff; font-family: var(--font-mono); font-weight: 700; font-size: .8rem;
  box-shadow: 0 3px 6px rgba(0,0,0,.6), inset 0 0 0 3px rgba(0,0,0,.3); display: inline-flex; align-items: center; justify-content: center; transition: transform .12s; }
.chip:hover { transform: translateY(-3px) rotate(8deg); }
.chip[data-v="10"] { --chip: #b3261e; } .chip[data-v="25"] { --chip: #1e6fb3; } .chip[data-v="50"] { --chip: #1f8a4c; } .chip[data-v="100"] { --chip: #2b2b2b; } .chip[data-v="max"] { --chip: #8a6d1a; }
.bet-bar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: center; }
.bet-field { display: inline-flex; align-items: center; background: rgba(0,0,0,.45); border: 1px solid rgba(201,162,39,.35); border-radius: 8px; overflow: hidden; }
.bet-field input { width: 90px; background: transparent; border: 0; color: var(--gold-2); font-size: 1.1rem; font-weight: 700; text-align: center; padding: 8px 4px; outline: none; -moz-appearance: textfield; }
.bet-field input::-webkit-inner-spin-button, .bet-field input::-webkit-outer-spin-button { -webkit-appearance: none; }
.bet-field button { background: rgba(255,255,255,.05); border: 0; width: 32px; height: 38px; font-size: 1.1rem; }
.bet-field button:hover { background: rgba(255,255,255,.12); }
.chalk { background: #1c1e1a; border: 6px solid #4a3a2a; border-radius: 4px; padding: 12px 16px; color: #e6e2d3; font-family: var(--font-mono); text-shadow: 0 0 2px rgba(255,255,255,.4); box-shadow: inset 0 0 30px rgba(0,0,0,.6); }
.chalk h4 { font-family: var(--font-display); letter-spacing: .1em; font-size: 1.2rem; color: #fff; margin-bottom: 6px; }
.chalk .dim { color: #a9a596; }
.chalk table { border-collapse: collapse; width: 100%; }
.chalk td { padding: 2px 6px; } .chalk td:last-child { text-align: right; color: var(--gold-2); }
.paper { background: var(--paper); color: var(--paper-ink); font-family: var(--font-mono); padding: 12px 14px; box-shadow: 3px 4px 10px rgba(0,0,0,.6); transform: rotate(-.6deg); border-radius: 2px; }
.paper h4 { font-family: var(--font-display); letter-spacing: .1em; font-size: 1.2rem; margin-bottom: 4px; }
.status { min-height: 30px; text-align: center; font-family: var(--font-display); font-size: 1.3rem; letter-spacing: .06em; color: var(--dim); }
.status .win { color: var(--gold-2); text-shadow: 0 0 10px rgba(232,198,90,.6); }
.status .loss { color: var(--neon-red); text-shadow: 0 0 10px rgba(255,59,59,.5); }
#toasts { position: fixed; right: 18px; bottom: 18px; display: flex; flex-direction: column; gap: 10px; z-index: 95; pointer-events: none; }
.toast { display: flex; gap: 10px; align-items: flex-start; min-width: 240px; max-width: 340px; background: var(--paper); color: var(--paper-ink); padding: 10px 12px;
  box-shadow: 3px 4px 12px rgba(0,0,0,.7); transform: rotate(-1deg); animation: toastIn .25s ease both; font-family: var(--font-mono); font-size: .85rem; border-left: 5px solid var(--neon-blue); }
.toast.win { border-left-color: var(--gold); background: #f2e2a8; }
.toast.loss { border-left-color: var(--neon-red); background: #f0b8ad; }
.toast.gold { border-left-color: var(--gold-2); background: #f6e6b3; }
.toast.pink { border-left-color: var(--neon-pink); background: #f3c8dc; }
.toast .ic { font-size: 1.4rem; line-height: 1; }
.toast b { display: block; font-family: var(--font-display); letter-spacing: .08em; font-size: 1.05rem; margin-bottom: 2px; }
.toast.out { animation: toastOut .25s ease both; }
.floatnum { position: fixed; z-index: 94; font-family: var(--font-mono); font-weight: 700; font-size: 1.3rem; pointer-events: none; animation: floatUp 1.1s ease-out both; text-shadow: 0 2px 6px #000; }
.floatnum.up { color: var(--gold-2); }
.floatnum.down { color: var(--neon-red); }
.shake { animation: shake .35s ease both; }
```

Unter `/* ==== 7. ANIMATIONEN ==== */`:

```css
@keyframes screenIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes neonFlicker { 0%, 100% { opacity: 1; } 3% { opacity: .55; } 4% { opacity: 1; } 41% { opacity: 1; } 42% { opacity: .7; } 43% { opacity: 1; } 71% { opacity: 1; } 72% { opacity: .5; } 72.5% { opacity: 1; } }
@keyframes popIn { from { transform: scale(.6) rotate(-6deg); opacity: 0; } to { opacity: 1; } }
@keyframes pulseGold { 0% { box-shadow: 0 0 0 0 rgba(232,198,90,.7); } 100% { box-shadow: 0 0 0 18px rgba(232,198,90,0); } }
@keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(255,59,59,.7); color: #ff8080; } 100% { box-shadow: 0 0 0 18px rgba(255,59,59,0); } }
@keyframes shake { 0%, 100% { transform: translateX(0); } 20% { transform: translateX(-6px); } 40% { transform: translateX(6px); } 60% { transform: translateX(-4px); } 80% { transform: translateX(4px); } }
@keyframes toastIn { from { transform: translateX(40px) rotate(-1deg); opacity: 0; } to { transform: rotate(-1deg); opacity: 1; } }
@keyframes toastOut { to { transform: translateX(40px); opacity: 0; } }
@keyframes floatUp { 0% { transform: translateY(0); opacity: 1; } 100% { transform: translateY(-70px); opacity: 0; } }
```

- [ ] **Step 2: Hub-Template einfügen** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-hub">
  <div class="hub">
    <div class="door" data-screen="roulette" style="--neon: var(--neon-red)"><div class="sign">Roulette</div><div class="glyph">🎡</div><div class="chalk-tag">Plein 35:1</div><div class="knob"></div></div>
    <div class="door" data-screen="slots" style="--neon: var(--neon-amber)"><div class="sign">Slots</div><div class="glyph">🎰</div><div class="chalk-tag">bis 50×</div><div class="knob"></div></div>
    <div class="door" data-screen="horses" style="--neon: var(--neon-green)"><div class="sign">Rennbahn</div><div class="glyph">🏇</div><div class="chalk-tag">Quote 4.0</div><div class="knob"></div></div>
    <div class="door" data-screen="russian" style="--neon: var(--neon-blue)"><div class="sign">Igor</div><div class="glyph">🔫</div><div class="chalk-tag">Duell · 1 Kugel</div><div class="knob"></div></div>
    <div class="door" data-screen="blackjack" style="--neon: var(--neon-green)"><div class="sign">Black Jack</div><div class="glyph">🃏</div><div class="chalk-tag">bis 21</div><div class="knob"></div></div>
    <div class="door day" data-screen="postman" style="--neon: var(--day)"><div class="sign">Ausgang</div><div class="glyph">📬</div><div class="chalk-tag">Post austragen</div><div class="knob"></div></div>
  </div>
</template>
```

- [ ] **Step 3: UI-Block einfügen** – nach `</script>` von `sfx`:

```html
<script id="ui">
/* ================= UI – Router, Wallet, Seitenleiste, Toasts, Money-Counter ================= */
const Actions = {
  finance: () => UI.show('finance'),
  invest: () => UI.show('invest'),
  life: () => UI.show('life'),
};

const UI = {
  screens: new Map(),
  current: null,
  busy: false,
  shownBalance: 0,
  tweenId: null,
  fmt(n) { return Math.round(n).toLocaleString('de-DE') + ' €'; },
  register(id, def) { this.screens.set(id, def); },
  async show(id) {
    if (this.busy) return;
    const def = this.screens.get(id);
    if (!def) { console.warn('[ui] Screen fehlt:', id); return; }
    this.busy = true;
    const stage = qs('#stage');
    if (this.current) {
      try { this.current.def.unmount?.(); } catch (e) { console.error(e); }
      stage.classList.add('leaving');
      await wait(180);
    }
    stage.innerHTML = '';
    stage.classList.remove('leaving');
    stage.appendChild(qs('#' + def.template).content.cloneNode(true));
    this.current = { id, def };
    document.body.dataset.screen = id;
    stage.classList.add('entering');
    try { def.mount?.(stage); } catch (e) { console.error(e); }
    await wait(250);
    stage.classList.remove('entering');
    this.busy = false;
  },
  toast({ icon = '📌', title = '', text = '', tone = 'info', ms = 3000 } = {}) {
    const box = qs('#toasts');
    while (box.children.length >= 3) box.firstChild.remove();
    const t = h('div', { class: `toast ${tone}` }, h('span', { class: 'ic' }, icon), h('div', {}, title ? h('b', {}, title) : null, text));
    box.appendChild(t);
    setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 260); }, ms);
    return t;
  },
  _writeMoney(v) { for (const el of qsa('.money-live')) el.textContent = this.fmt(v); },
  setBalance(target, { animate = true, duration = 600 } = {}) {
    if (this.tweenId) cancelAnimationFrame(this.tweenId);
    const from = this.shownBalance;
    if (!animate || from === target || matchMedia('(prefers-reduced-motion: reduce)').matches) {
      this.shownBalance = target; this._writeMoney(target); return;
    }
    const t0 = performance.now();
    const step = (now) => {
      const p = Math.min(1, (now - t0) / duration);
      const e = 1 - Math.pow(1 - p, 3);
      this.shownBalance = from + (target - from) * e;
      this._writeMoney(this.shownBalance);
      if (p < 1) this.tweenId = requestAnimationFrame(step);
      else { this.shownBalance = target; this._writeMoney(target); this.tweenId = null; }
    };
    this.tweenId = requestAnimationFrame(step);
  },
  pulseBalance(delta) {
    for (const el of qsa('.money-live')) {
      el.classList.remove('up', 'down'); void el.offsetWidth;
      el.classList.add(delta >= 0 ? 'up' : 'down');
    }
  },
  floatNumber(delta, fromEl) {
    const r = (fromEl || qs('#stage')).getBoundingClientRect();
    const n = h('div', { class: `floatnum ${delta >= 0 ? 'up' : 'down'}`, style: `left:${r.left + r.width / 2 - 40}px; top:${r.top + r.height / 3}px` },
      (delta >= 0 ? '+' : '−') + this.fmt(Math.abs(delta)));
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 1200);
  },
  shake(el = qs('#shell')) {
    if (!el || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    el.classList.remove('shake'); void el.offsetWidth; el.classList.add('shake');
    setTimeout(() => el.classList.remove('shake'), 400);
  },
  renderWallet() {
    const s = State.s;
    const luck = Rules.luck(s);
    const segs = luck >= 60 ? 5 : luck >= 40 ? 4 : luck >= 20 ? 3 : luck >= 15 ? 2 : luck >= 10 ? 1 : 0;
    const luckEl = qs('#luck');
    luckEl.title = `Glück +${luck} %`;
    luckEl.innerHTML = '';
    luckEl.append('🍀', ...[0, 1, 2, 3, 4].map((i) => h('span', { class: 'seg' + (i < segs ? ' on' : '') })), h('span', { class: 'luck-val' }, `+${luck}%`));
    const notes = qs('#notes');
    notes.innerHTML = '';
    if (s.isHeartbroken) notes.append(h('span', { class: 'note pink' }, `💔 Liebeskummer · ${s.beers}/2 🍺`));
    else if (s.isMarried) notes.append(h('span', { class: 'note pink' }, `💍 Chantal · noch ${Rules.MARRIAGE_SPINS - s.marriageSpins} Spins`));
    if (s.bankDebt > 0) notes.append(h('span', { class: 'note danger' }, `🏦 ${this.fmt(s.bankDebt)} · −${this.fmt(Rules.bankInterest(s.bankDebt))}/Spin`));
    if (s.mafiaDebt > 0) notes.append(h('span', { class: 'note danger' }, `🕶️ ${this.fmt(s.mafiaDebt)} · ${s.mafiaSpins} Spins`));
    if (s.kidneySold) notes.append(h('span', { class: 'note danger' }, '💊 −20 €/Spin'));
    if (s.hasHouse || s.hasDealer) notes.append(h('span', { class: 'note gold' }, `💸 +${Rules.passivePerMin(s)} €/min`));
    qs('#mute').textContent = State.meta.muted ? '🔇' : '🔊';
  },
  renderSide() {
    const s = State.s;
    const side = qs('#side');
    side.innerHTML = '';
    const sec = (title, ...kids) => h('section', { class: 'side-sec' }, h('h3', {}, title), ...kids);
    const btn = (label, price, action, disabled = false) =>
      h('button', { class: 'side-btn', 'data-action': action, disabled: disabled ? '' : null }, h('span', {}, label), h('span', { class: 'price' }, price));
    side.append(
      sec('Die Bar',
        btn(`🍺 Bier${s.beers > 0 ? ` (${s.beers}/3)` : ''}`, '50 €', 'beer', !Rules.canBeer(s).ok),
        btn('🍪 Brownie', s.brownieCost >= 10000 ? '10.000 €' : '1.000 €', 'brownie', !Rules.canBrownie(s).ok),
        h('p', { class: 'side-hint' }, 'Bier hält 2 Spins, Brownie 1 Spin.')),
      sec('Hinterzimmer',
        btn(s.kidneySold ? '🫁 Niere verkauft' : '🫁 Niere verkaufen', s.kidneySold ? '' : '+2.000 €', 'kidney', s.kidneySold),
        btn('🏦 Kredite', s.bankDebt + s.mafiaDebt > 0 ? `−${this.fmt(s.bankDebt + s.mafiaDebt)}` : '', 'finance'),
        btn('📈 Anlagen', s.investments.length ? `${s.investments.length} aktiv` : '', 'invest')),
      sec('Zuhause', btn('🏡 Leben', s.hasHouse ? '🏰' : '', 'life')),
    );
    side.onclick = (e) => {
      const b = e.target.closest('[data-action]');
      if (!b || b.disabled) return;
      SFX.play('click');
      const a = Actions[b.dataset.action];
      if (a) a(); else console.warn('[ui] Aktion fehlt:', b.dataset.action);
    };
  },
  mountShell() {
    const w = qs('#wallet');
    w.innerHTML = '';
    w.append(
      h('button', { class: 'brand neon', id: 'brand', style: '--neon: var(--neon-amber)', title: 'Zurück in den Gang', onclick: () => UI.show('hub') }, 'Keller 37'),
      h('div', { class: 'wallet-mid' }, h('div', { class: 'luck', id: 'luck' }), h('div', { class: 'notes', id: 'notes' })),
      h('div', { class: 'wallet-right' },
        h('button', { class: 'icon-btn', id: 'mute', title: 'Ton an/aus', onclick: () => { SFX.setMuted(!State.meta.muted); UI.renderWallet(); } }, '🔊'),
        h('button', { class: 'icon-btn', id: 'newgame', title: 'Neues Spiel', onclick: () => Bus.emit('newgame.request', {}) }, '↺'),
        h('div', { class: 'balance money-live', id: 'balance' }, '0 €')),
    );
    this.shownBalance = State.s.balance;
    this.setBalance(State.s.balance, { animate: false });
    this.renderWallet();
    this.renderSide();
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && qs('#cutscene').hidden && UI.current && UI.current.id !== 'hub') UI.show('hub');
    });
  },
};

UI.register('hub', {
  template: 'tpl-hub',
  mount(root) {
    qsa('.door', root).forEach((d) => {
      d.addEventListener('click', () => { SFX.play('click'); UI.show(d.dataset.screen); });
      d.addEventListener('mouseenter', () => SFX.play('neonBuzz'));
    });
  },
});
</script>
```

- [ ] **Step 4: Boot erweitern** – Inhalt von `<script id="boot">` ersetzen:

```js
/* ================= BOOT ================= */
(async function boot() {
  const params = new URLSearchParams(location.search);
  if (params.has('fresh')) { try { localStorage.removeItem('keller37.state'); } catch (e) { /* egal */ } }
  const { loaded } = State.init(localStorage);
  UI.mountShell();
  if (params.has('selftest')) {
    const r = SelfTest.run();
    document.documentElement.dataset.selftest = `passed=${r.passed} failed=${r.failed}`;
    console.log('[selftest]', r);
    r.failures.forEach((f) => console.error('[selftest] FAIL', f));
    UI.toast({ icon: r.failed ? '❌' : '✅', title: 'Selbsttest', text: `${r.passed} bestanden, ${r.failed} fehlgeschlagen`, tone: r.failed ? 'loss' : 'win', ms: 6000 });
  }
  await UI.show(params.get('screen') || 'hub');
  if (loaded && !params.has('screen')) UI.toast({ icon: '💾', title: 'Spielstand geladen', text: `Willkommen zurück. ${UI.fmt(State.s.balance)} in der Tasche.` });
})();
```

- [ ] **Step 5: Screenshot & Selbsttest prüfen**

Run: `tests/screenshot.sh /tmp/k37-hub.png "?fresh"` und die PNG mit Read ansehen.
Expected: Neonschild „KELLER 37" oben links, Glück-Meter mit 5 Segmenten, `50 €` rechts in Gold, sechs Türen in 3×2 mit Neonschildern (Roulette rot, Slots amber, Rennbahn grün, Igor blau, Black Jack grün, Ausgang hell), rechts drei Seitenleisten-Sektionen „Die Bar / Hinterzimmer / Zuhause". Sichtbare Körnung und dunkle Ränder.

Run: `tests/dom-selftest.sh` → `data-selftest="passed=56 failed=0"`.

Im Browser öffnen: Tür-Hover erzeugt Lichtstreifen unten und Buzz; Klick auf Tür loggt `[ui] Screen fehlt: slots` (Screens kommen später); Klick auf 🔊 wechselt zu 🔇 und bleibt nach Reload; Konsole ohne Fehler.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat: Shell mit Wallet, Seitenleiste, Hub und Router

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Cutscene-Engine, Cast, Orte, Intro

**Files:**
- Modify: `keller37.html` (CSS-Sektion 5, Keyframes; neuer Block `<script id="cutscene">` nach `ui`; `boot`)

**Interfaces:**
- Consumes: `UI.setBalance/pulseBalance/renderWallet/shake`, `SFX`, `State`, `h/qs/qsa/wait/rand/pick`.
- Produces: `Cutscene.CAST`, `Cutscene.define(id, panels | (ctx) => panels)`, `Cutscene.bind(eventName, sceneId)` (registriert `Bus.on(eventName, (ctx) => Cutscene.play(sceneId, ctx))`), `Cutscene.play(id, ctx)` → `Promise<choiceValue | undefined>`, `Cutscene.active`.
- Panel-Format: `{ bg, who, mood: 'calm'|'angry'|'happy'|'shock'|'dead', text, fx?: 'flash'|'shake'|'blackout'|'hearts'|'coins'|'drain'|'gain'|'stats', choices?: [{label, value, cls?}] }`. Platzhalter `{{key}}` im Text werden aus `ctx` gefüllt. `fx: 'stats'` rendert `ctx.stats` (Objekt) als Tabelle.
- **fx ändern nie den State.** `drain`/`gain` animieren nur den Kontostand auf `State.s.balance`, den die Logik vorher gesetzt hat.

- [ ] **Step 1: CSS-Sektion 5 füllen**

Unter `/* ==== 5. CUTSCENE ==== */`:

```css
#cutscene { position: fixed; inset: 0; z-index: 80; display: flex; flex-direction: column; justify-content: flex-end; background: #000; overflow: hidden; animation: fadeIn .3s ease both; }
#cutscene[hidden] { display: none; }
.cs-bg { position: absolute; inset: 0; transition: background 1s; }
.cs-bg::after { content: ""; position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 40%, transparent 30%, rgba(0,0,0,.8) 100%); }
.cs-bg .prop { position: absolute; font-size: 6rem; opacity: .22; filter: blur(1px) grayscale(.4); }
.cs-bg.bar { background: linear-gradient(180deg, #3a1f0c 0%, #1a0d05 60%, #000 100%); }
.cs-bg.hinterzimmer { background: radial-gradient(circle at 50% 20%, #5a3a12 0%, #1e1207 40%, #000 100%); }
.cs-bg.standesamt { background: linear-gradient(180deg, #f3e6c8 0%, #c9b58f 60%, #6b5b3f 100%); }
.cs-bg.villa { background: linear-gradient(180deg, #0a1636 0%, #16244d 50%, #0a0f1f 100%); }
.cs-bg.hafen { background: linear-gradient(180deg, #02050f 0%, #0a1a33 55%, #041020 100%); }
.cs-bg.hafen-morgen { background: linear-gradient(180deg, #2c2a4a 0%, #c4573b 45%, #f0a35a 70%, #3b2a2a 100%); }
.cs-bg.klinik { background: linear-gradient(180deg, #0d3b3f 0%, #0a2224 60%, #020a0b 100%); }
.cs-bg.bank { background: linear-gradient(180deg, #0c1f33 0%, #123a5c 50%, #06131f 100%); }
.cs-bg.strasse { background: linear-gradient(180deg, #7fb2e5 0%, #c7d7e3 50%, #5b5b4d 100%); }
.cs-bg.keller { background: radial-gradient(circle at 50% 10%, #4a4a3a 0%, #151512 40%, #000 100%); }
.cs-money { position: absolute; top: 16px; left: 20px; z-index: 3; font-family: var(--font-mono); font-size: 1.3rem; font-weight: 700; color: var(--gold-2); background: rgba(0,0,0,.5); padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(201,162,39,.4); }
.cs-money.up { animation: pulseGold .6s ease both; }
.cs-money.down { animation: pulseRed .6s ease both; }
.cs-stage { position: relative; z-index: 2; display: flex; align-items: flex-end; gap: 24px; padding: 0 6vw 4vh; max-width: 1100px; width: 100%; margin: 0 auto; }
.cs-portrait { flex: 0 0 auto; width: 170px; height: 170px; border-radius: 50%; border: 5px solid var(--c, var(--gold)); background: radial-gradient(circle at 40% 35%, #3a3a33, #0d0d0b);
  display: flex; align-items: center; justify-content: center; font-size: 6rem; box-shadow: 0 0 30px rgba(0,0,0,.8), 0 0 24px var(--c, var(--gold)); margin-bottom: 10px; }
.cs-portrait.calm { animation: breathe 3s ease-in-out infinite; }
.cs-portrait.angry { animation: shake .5s infinite; }
.cs-portrait.happy { animation: bounce .7s infinite; }
.cs-portrait.shock { animation: shockZoom .5s ease both; }
.cs-portrait.dead { filter: grayscale(1) brightness(.6); transform: rotate(12deg); }
.cs-box { flex: 1; --c: var(--gold); background: rgba(12,12,10,.92); border: 2px solid var(--c); border-radius: 10px; padding: 18px 22px 26px; min-height: 150px; position: relative; box-shadow: 0 0 40px rgba(0,0,0,.8); }
.cs-name { font-family: var(--font-display); letter-spacing: .14em; font-size: 1.3rem; color: var(--c); margin-bottom: 8px; text-shadow: 0 0 10px var(--c); }
.cs-text { font-size: 1.15rem; line-height: 1.55; min-height: 3.2em; }
.cs-next { position: absolute; right: 16px; bottom: 8px; color: var(--c); animation: bob 1s infinite; font-size: 1.1rem; }
.cs-choices { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.cs-choices:empty { display: none; }
.cs-skip { position: absolute; top: 16px; right: 20px; z-index: 3; background: rgba(0,0,0,.4); border: 1px solid rgba(255,255,255,.2); color: var(--dim); font-family: var(--font-display); letter-spacing: .1em; padding: 6px 12px; border-radius: 4px; }
.cs-skip:hover { color: var(--text); border-color: var(--text); }
.cs-flash { position: absolute; inset: 0; background: #fff; z-index: 4; pointer-events: none; opacity: 0; }
.cs-flash.on { animation: flash .18s ease both; }
.cs-black { position: absolute; inset: 0; background: #000; z-index: 4; pointer-events: none; opacity: 0; transition: opacity .5s; }
.cs-black.on { opacity: 1; }
.cs-particle { position: absolute; z-index: 3; pointer-events: none; animation: particleUp 1.6s ease-out both; }
.cs-stats { margin-top: 10px; display: grid; grid-template-columns: 1fr auto; gap: 4px 20px; font-family: var(--font-mono); }
.cs-stats span:nth-child(even) { text-align: right; color: var(--gold-2); }
```

Zu `/* ==== 7. ANIMATIONEN ==== */` ergänzen:

```css
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes breathe { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.03); } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
@keyframes shockZoom { 0% { transform: scale(1); } 40% { transform: scale(1.18); } 100% { transform: scale(1.05); } }
@keyframes bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(4px); } }
@keyframes flash { 0% { opacity: 1; } 100% { opacity: 0; } }
@keyframes particleUp { 0% { transform: translateY(0) rotate(0); opacity: 1; } 100% { transform: translateY(-260px) rotate(40deg); opacity: 0; } }
```

- [ ] **Step 2: Cutscene-Block einfügen** – nach `</script>` von `ui`:

```html
<script id="cutscene">
/* ================= CUTSCENE – Visual-Novel-Engine ================= */
const Cutscene = {
  active: false,
  SKIP: Symbol('skip'),
  CAST: {
    wirt: { name: 'Der Wirt', emoji: '🍺', color: 'var(--neon-amber)' },
    chantal: { name: 'Chantal-Monique', emoji: '💅', color: 'var(--neon-pink)' },
    vito: { name: 'Don Vito', emoji: '🕶️', color: 'var(--neon-red)' },
    igor: { name: 'Igor', emoji: '🐻', color: 'var(--neon-blue)' },
    doc: { name: 'Der Doc', emoji: '🥼', color: '#5fe0d0' },
    krause: { name: 'Herr Krause', emoji: '👔', color: 'var(--neon-blue)' },
    makler: { name: 'Der Makler', emoji: '🧑‍💼', color: 'var(--gold-2)' },
    schmalz: { name: 'Dr. Schmalz', emoji: '⚖️', color: '#c0c0c0' },
    kevin: { name: 'Kevin', emoji: '🧢', color: 'var(--neon-purple)' },
    postmeister: { name: 'Der Postmeister', emoji: '📬', color: 'var(--day)' },
    du: { name: 'Du', emoji: '🤠', color: '#ffffff' },
  },
  PROPS: {
    bar: ['🍾', '🪑'], hinterzimmer: ['🕯️', '🚬'], standesamt: ['💐', '🔔'], villa: ['🏙️', '🌙'], hafen: ['🏗️', '🌙'],
    'hafen-morgen': ['🏗️', '🌅'], klinik: ['🩺', '💡'], bank: ['🏧', '🪴'], strasse: ['🏠', '🚗'], keller: ['💡', '🪑'],
  },
  SCENES: {},
  define(id, panels) { this.SCENES[id] = panels; },
  bind(eventName, sceneId) { Bus.on(eventName, (ctx) => this.play(sceneId, ctx)); },
  fill(text, ctx) { return text.replace(/\{\{(\w+)\}\}/g, (_, k) => (k in ctx ? String(ctx[k]) : `{{${k}}}`)); },
  async play(id, ctx = {}) {
    const def = this.SCENES[id];
    if (!def) { console.warn('[cutscene] Szene fehlt:', id); return undefined; }
    const panels = typeof def === 'function' ? def(ctx) : def;
    while (this.active) await wait(50);
    this.active = true;
    SFX.stopAll();
    const root = qs('#cutscene');
    root.innerHTML = '';
    const els = {
      root,
      bg: h('div', { class: 'cs-bg' }),
      flash: h('div', { class: 'cs-flash' }),
      black: h('div', { class: 'cs-black' }),
      money: h('div', { class: 'cs-money money-live' }, UI.fmt(UI.shownBalance)),
      portrait: h('div', { class: 'cs-portrait' }),
      name: h('div', { class: 'cs-name' }),
      text: h('div', { class: 'cs-text' }),
      extra: h('div', { class: 'cs-extra' }),
      choices: h('div', { class: 'cs-choices' }),
      next: h('div', { class: 'cs-next' }, '▼'),
      skip: h('button', { class: 'cs-skip' }, 'Überspringen ⏭'),
    };
    els.box = h('div', { class: 'cs-box' }, els.name, els.text, els.extra, els.choices, els.next);
    root.append(els.bg, els.flash, els.black, els.money, els.skip, h('div', { class: 'cs-stage' }, els.portrait, els.box));
    root.hidden = false;
    let result;
    for (let i = 0; i < panels.length; i++) {
      const isLast = i === panels.length - 1;
      const r = await this._panel(els, panels[i], ctx, isLast);
      if (r === this.SKIP) {
        for (let j = i + 1; j < panels.length - 1; j++) this._fx(els, panels[j].fx, ctx, true);
        i = panels.length - 2; // nächster Durchlauf zeigt das letzte Panel
        continue;
      }
      if (r !== undefined) result = r;
    }
    root.hidden = true;
    root.innerHTML = '';
    this.active = false;
    UI.setBalance(State.s.balance, { animate: false });
    UI.renderWallet();
    return result;
  },
  _panel(els, p, ctx, isLast) {
    return new Promise((resolve) => {
      const who = this.CAST[p.who] || this.CAST.du;
      els.bg.className = `cs-bg ${p.bg || 'bar'}`;
      els.bg.innerHTML = '';
      (this.PROPS[p.bg] || []).forEach((e, i) => els.bg.append(h('span', { class: 'prop', style: `left:${i ? 78 : 12}%; top:${i ? 22 : 30}%` }, e)));
      els.portrait.className = `cs-portrait ${p.mood || 'calm'}`;
      els.portrait.textContent = who.emoji;
      els.portrait.style.setProperty('--c', who.color);
      els.box.style.setProperty('--c', who.color);
      els.name.textContent = who.name;
      els.choices.innerHTML = '';
      els.extra.innerHTML = '';
      els.next.style.visibility = 'hidden';
      els.skip.style.display = isLast ? 'none' : '';
      this._fx(els, p.fx, ctx, false);
      const full = this.fill(p.text || '', ctx);
      let typing = true, pos = 0, timer = null;
      const renderChoices = () => {
        for (const c of p.choices) {
          els.choices.append(h('button', { class: 'btn ' + (c.cls || ''), onclick: (e) => { e.stopPropagation(); SFX.play('click'); done(c.value); } }, c.label));
        }
      };
      const finish = () => {
        typing = false; clearTimeout(timer); els.text.textContent = full;
        if (p.choices) renderChoices(); else els.next.style.visibility = 'visible';
      };
      const tick = () => {
        if (!typing) return;
        pos++;
        els.text.textContent = full.slice(0, pos);
        if (pos % 3 === 0) SFX.play('typewriter');
        if (pos >= full.length) { finish(); return; }
        const ch = full[pos - 1];
        timer = setTimeout(tick, /[.!?…]/.test(ch) ? 120 : /[,;:]/.test(ch) ? 60 : 30);
      };
      const onClick = (e) => {
        if (e.target.closest('.cs-choices') || e.target.closest('.cs-skip')) return;
        if (typing) finish(); else if (!p.choices) done(undefined);
      };
      const onKey = (e) => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); onClick({ target: els.text }); } };
      const onSkip = (e) => { e.stopPropagation(); done(this.SKIP); };
      const cleanup = () => { els.root.removeEventListener('click', onClick); document.removeEventListener('keydown', onKey); els.skip.removeEventListener('click', onSkip); };
      const done = (v) => { cleanup(); resolve(v); };
      els.root.addEventListener('click', onClick);
      document.addEventListener('keydown', onKey);
      els.skip.addEventListener('click', onSkip);
      if (matchMedia('(prefers-reduced-motion: reduce)').matches) finish(); else tick();
    });
  },
  _fx(els, fx, ctx, instant) {
    if (!fx) return;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    switch (fx) {
      case 'flash': if (!instant) { els.flash.classList.remove('on'); void els.flash.offsetWidth; els.flash.classList.add('on'); } break;
      case 'shake': if (!instant) UI.shake(els.root); break;
      case 'blackout': if (!instant && !reduced) { els.black.classList.add('on'); SFX.play('blackout'); setTimeout(() => els.black.classList.remove('on'), 900); } break;
      case 'hearts': if (!instant && !reduced) this._particles(els, ['❤️', '💕', '💖'], 14); break;
      case 'coins': if (!instant && !reduced) { this._particles(els, ['🪙', '💶', '💰'], 24); SFX.play('cash'); } break;
      case 'drain': UI.setBalance(State.s.balance, { animate: !instant, duration: 1800 }); if (!instant) { UI.pulseBalance(-1); SFX.play('lose'); } break;
      case 'gain': UI.setBalance(State.s.balance, { animate: !instant, duration: 1200 }); if (!instant) { UI.pulseBalance(1); SFX.play('cash'); } break;
      case 'stats': {
        const grid = h('div', { class: 'cs-stats' });
        for (const [k, v] of Object.entries(ctx.stats || {})) grid.append(h('span', {}, k), h('span', {}, String(v)));
        els.extra.append(grid);
        break;
      }
      default: console.warn('[cutscene] fx unbekannt:', fx);
    }
  },
  _particles(els, glyphs, n) {
    for (let i = 0; i < n; i++) {
      const p = h('span', { class: 'cs-particle', style: `left:${rand(5, 95)}%; top:${rand(40, 90)}%; animation-delay:${rand(0, 0.6)}s; font-size:${rand(1.2, 2.4)}rem` }, pick(glyphs));
      els.root.append(p);
      setTimeout(() => p.remove(), 2400);
    }
  },
};

/* ---- Szenen: Intro & Neues Spiel ---- */
Cutscene.define('intro', [
  { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Neu hier? Fünfzig Euro in der Tasche und dieser Blick. Den kenn ich.' },
  { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Hier unten gibt es keine Regeln, nur Quoten. Die Bar ist rechts, das Hinterzimmer daneben. Frag nicht, was im Brownie ist.' },
  { bg: 'bar', who: 'wirt', mood: 'happy', text: 'Die Türen sind da drüben. Viel Glück – du wirst es brauchen.' },
]);
Cutscene.define('newgame.confirm', [
  { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Alles auf Anfang? Konto, Haus, Schulden, Chantal – alles weg. Die Trophäen an der Wand bleiben hängen.',
    choices: [{ label: 'Ja, alles weg', value: 'yes', cls: 'red' }, { label: 'Doch nicht', value: 'no', cls: 'ghost' }] },
]);
</script>
```

- [ ] **Step 3: Boot um Intro und `?scene` erweitern** – in `boot` nach `await UI.show(...)`:

```js
  if (params.has('scene')) {
    await Cutscene.play(params.get('scene'), { bill: 900, before: 1000, after: 500, price: '1.000 €', debt: 300, stats: { Spins: 12, 'Höchster Kontostand': '1.234 €' } });
  } else if (!State.s.flags.intro) {
    await Cutscene.play('intro');
    State.s.flags.intro = true;
    State.save();
  }
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-intro.png "?fresh"` → PNG ansehen. Expected: Vollbild-Overlay in Bar-Farben (braun/orange), Portrait 🍺 links im Goldrahmen, Name-Tag „DER WIRT" in Amber, Dialogbox mit Text (mindestens teilweise getippt), oben links Kontostand `50 €`, oben rechts „Überspringen".

Im Browser: `keller37.html?fresh` – Text tippt sich mit Klacker-Sound; Klick beendet Zeile, nächster Klick blättert; „Überspringen" springt zum letzten Panel; nach dem letzten Panel verschwindet das Overlay, Hub sichtbar; Reload ohne `?fresh` zeigt kein Intro mehr (Flag gespeichert). `keller37.html?scene=newgame.confirm` zeigt zwei Buttons; Klick schließt die Szene.

Run: `node tests/run-selftest.mjs` → weiterhin `56 bestanden`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Cutscene-Engine mit Cast, Orten und Intro

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Core-Spielschleife & die Bar

**Files:**
- Modify: `keller37.html` (neuer Block `<script id="core">` nach `cutscene`; neuer Block `<script id="rooms">` nach `core`; Szenen in `rooms`)

**Interfaces:**
- Consumes: `Rules`, `State`, `Bus`, `UI`, `SFX`, `Cutscene`, `Actions`.
- Produces: `Game.applyDelta(delta, {from, quiet})` (ändert `State.s.balance`, Stats, Wallet-Animation, speichert), `Game.beginSpin(bet)` → `boolean` (prüft Einsatz, zieht Zinsen/Meds ab, Toast bei Ablehnung), `Game.settle(delta, {from, game})` → `Promise` (Gewinn/Verlust verbuchen, `win`/`loss` emittieren, dann `afterSpin`), `Game.afterSpin()` → `Promise`, `Game.bindBet(root, inputId)` (bindet `[data-step]`-Tasten und `[data-chip]`-Chips an ein Einsatzfeld), `Game.readBet(inputId)` → `number`; `Actions.beer/brownie/kidney`.
- Bus-Events aus `afterSpin`: `divorce {before, after}`, `heartbreak.collapse {bill}`, `mafia.legbreak {bill}`, `mafia.lastcall {debt}`, `invest.resolved {inv, won, payout}`, `spin:after`, `gameover`; aus `settle`: `win {amount, game}`, `loss {amount, game}`; aus `beginSpin`: `spin:before {bet}`; aus der Bar: `beer {beers}`, `brownie`, `kidney.sold`.

- [ ] **Step 1: Core-Block einfügen** – nach `</script>` von `cutscene`:

```html
<script id="core">
/* ================= CORE – Kontostand, Spin-Kosten, afterSpin (Reihenfolge wie im Original) ================= */
const Game = {
  _passiveAcc: 0,
  applyDelta(delta, { from = null, quiet = false } = {}) {
    const s = State.s;
    if (delta === 0) quiet = true;
    s.balance += delta;
    if (s.balance > s.stats.maxBalance) s.stats.maxBalance = s.balance;
    if (delta > s.stats.biggestWin) s.stats.biggestWin = delta;
    UI.setBalance(s.balance);
    if (!quiet) {
      UI.pulseBalance(delta);
      UI.floatNumber(delta, from);
      if (delta < 0) UI.shake(qs('#balance'));
    }
    State.save();
    UI.renderWallet();
    UI.renderSide();
  },
  readBet(inputId) { return parseInt(qs('#' + inputId).value, 10); },
  bindBet(root, inputId) {
    const input = qs('#' + inputId, root);
    const clamp = () => { const v = parseInt(input.value, 10); input.value = Number.isFinite(v) ? Math.max(1, v) : 1; };
    input.addEventListener('change', clamp);
    qsa('[data-step]', root).forEach((b) => b.addEventListener('click', () => {
      const v = parseInt(input.value, 10) || 0;
      input.value = Math.max(1, v + parseInt(b.dataset.step, 10));
      SFX.play('click');
    }));
    qsa('[data-chip]', root).forEach((c) => c.addEventListener('click', () => {
      const v = c.dataset.chip;
      input.value = v === 'max' ? Rules.maxBet(State.s) : parseInt(v, 10);
      SFX.play('chip');
    }));
  },
  beginSpin(bet) {
    const chk = Rules.checkSpin(State.s, bet);
    if (!chk.ok) {
      if (chk.reason === 'invalid') UI.toast({ icon: '🚫', title: 'Ungültiger Einsatz', text: 'Mindestens 1 €.', tone: 'loss' });
      else UI.toast({ icon: '🚫', title: 'Zu wenig Geld', tone: 'loss', ms: 4500,
        text: `Benötigt ${UI.fmt(chk.total)} (Einsatz ${UI.fmt(bet)} + Zinsen ${UI.fmt(chk.interest)} + Meds ${UI.fmt(chk.meds)}).` });
      SFX.play('lose');
      return false;
    }
    const costs = chk.interest + chk.meds;
    if (costs > 0) {
      this.applyDelta(-costs, { quiet: true });
      const parts = [];
      if (chk.interest) parts.push(`Zinsen ${UI.fmt(chk.interest)}`);
      if (chk.meds) parts.push(`Meds ${UI.fmt(chk.meds)}`);
      UI.toast({ icon: '🧾', title: 'Abzüge vor dem Spin', text: parts.join(' · '), tone: 'loss', ms: 2000 });
    }
    Bus.emit('spin:before', { bet });
    return true;
  },
  async settle(delta, { from = null, game = '' } = {}) {
    this.applyDelta(delta, { from });
    if (delta > 0) { SFX.play('cash'); await Bus.emit('win', { amount: delta, game }); }
    else if (delta < 0) { SFX.play('lose'); await Bus.emit('loss', { amount: -delta, game }); }
    await this.afterSpin();
  },
  async afterSpin() {
    const s = State.s;
    s.stats.spins++;
    if (s.beerTimer > 0) {
      s.beerTimer--;
      if (s.beerTimer === 0) { s.beers = 0; UI.toast({ icon: '🍺', title: 'Ausgenüchtert', text: 'Die Bierwirkung ist verflogen.' }); }
    }
    if (s.brownieTimer > 0) {
      s.brownieTimer--;
      if (s.brownieTimer === 0) UI.toast({ icon: '🍪', title: 'Brownie verdaut', text: 'Die +40 % sind weg.' });
    }
    if (s.isMarried) {
      s.marriageSpins++;
      if (s.marriageSpins >= Rules.MARRIAGE_SPINS) {
        s.isMarried = false; s.hasHouse = false; s.isHeartbroken = true;
        const before = s.balance;
        s.balance = Math.floor(s.balance / 2);
        State.save();
        await Bus.emit('divorce', { before: UI.fmt(before), after: UI.fmt(s.balance) });
      }
    }
    if (s.isHeartbroken && s.beers < 2) {
      s.balance -= Rules.HEARTBREAK_BILL;
      State.save();
      await Bus.emit('heartbreak.collapse', { bill: UI.fmt(Rules.HEARTBREAK_BILL) });
    }
    if (s.mafiaDebt > 0) {
      s.mafiaSpins--;
      if (s.mafiaSpins <= 0) {
        const bill = Rules.mafiaBill(s.mafiaDebt);
        s.balance -= bill; s.mafiaDebt = 0; s.mafiaSpins = 0;
        State.save();
        await Bus.emit('mafia.legbreak', { bill: UI.fmt(bill) });
      } else if (s.mafiaSpins === 1) {
        await Bus.emit('mafia.lastcall', { debt: UI.fmt(s.mafiaDebt) });
      }
    }
    for (let i = s.investments.length - 1; i >= 0; i--) {
      const inv = s.investments[i];
      inv.spins--;
      if (inv.spins <= 0) {
        const r = Rules.investmentResolve(inv, Math.random);
        s.investments.splice(i, 1);
        if (r.won) {
          this.applyDelta(r.payout, { quiet: true });
          SFX.play('coin');
          UI.toast({ icon: '📈', title: `${inv.name} ausgezahlt`, text: `+${UI.fmt(r.payout)}`, tone: 'win' });
        } else {
          UI.toast({ icon: '📉', title: `${inv.name}: Totalverlust`, text: `${UI.fmt(inv.amount)} sind weg.`, tone: 'loss' });
        }
        await Bus.emit('invest.resolved', { inv, won: r.won, payout: r.payout });
      }
    }
    State.save();
    UI.setBalance(s.balance);
    UI.renderWallet();
    UI.renderSide();
    await Bus.emit('spin:after', {});
    if (Rules.isGameOver(s)) await Bus.emit('gameover', {});
  },
};

/* Passives Einkommen: alle 6 s, gesammelt als Toast pro Minute */
setInterval(() => {
  if (!State.s) return;
  const inc = Rules.passiveTick(State.s);
  if (inc > 0) { Game.applyDelta(inc, { quiet: true }); Game._passiveAcc += inc; }
}, 6000);
setInterval(() => {
  if (Game._passiveAcc > 0) {
    UI.toast({ icon: '💸', title: 'Passives Einkommen', text: `+${UI.fmt(Game._passiveAcc)} in der letzten Minute.`, tone: 'gold' });
    Game._passiveAcc = 0;
  }
}, 60000);
</script>
```

- [ ] **Step 2: Rooms-Block mit der Bar einfügen** – nach `</script>` von `core`:

```html
<script id="rooms">
/* ================= ROOMS – Bar, Kredite, Anlagen, Zuhause ================= */

/* ---- Die Bar (Seitenleiste) ---- */
Actions.beer = async () => {
  const s = State.s;
  const c = Rules.canBeer(s);
  if (!c.ok) {
    UI.toast({ icon: '🍺', title: c.reason === 'max' ? 'Maximal 3 Bier' : 'Bier kostet 50 €', text: c.reason === 'max' ? 'Der Wirt schüttelt den Kopf.' : 'Zu wenig Geld.', tone: 'loss' });
    return;
  }
  Game.applyDelta(-Rules.PRICES.beer, { quiet: true });
  s.beers++;
  s.beerTimer = Rules.BEER_SPINS;
  State.save();
  UI.renderWallet(); UI.renderSide();
  SFX.play('coin');
  UI.toast({ icon: '🍺', title: `Prost! Bier #${s.beers}`, text: `+${Rules.BEER_LUCK[s.beers]} % Glück für 2 Spins.`, tone: 'gold' });
  await Bus.emit('beer', { beers: s.beers });
};

Actions.brownie = async () => {
  const s = State.s;
  const c = Rules.canBrownie(s);
  if (!c.ok) {
    UI.toast({ icon: '🍪', title: c.reason === 'active' ? 'Brownie wirkt bereits' : `Kostet ${UI.fmt(s.brownieCost)}`, text: c.reason === 'active' ? 'Einer reicht. Wirklich.' : 'Zu wenig Geld.', tone: 'loss' });
    return;
  }
  const price = s.brownieCost;
  Game.applyDelta(-price, { quiet: true });
  s.brownieTimer = Rules.BROWNIE_SPINS;
  s.brownieCost = Rules.PRICES.brownieNext;
  State.save();
  UI.renderWallet(); UI.renderSide();
  if (!s.flags.brownie) {
    s.flags.brownie = true; State.save();
    await Cutscene.play('brownie.first', { price: UI.fmt(price) });
  } else {
    UI.toast({ icon: '🍪', title: 'Brownie', text: '+40 % Glück für 1 Spin. Frag nicht.', tone: 'gold' });
  }
  await Bus.emit('brownie', {});
};

Actions.kidney = async () => {
  const s = State.s;
  if (s.kidneySold) return;
  const choice = await Cutscene.play('kidney.offer', {});
  if (choice !== 'yes') return;
  s.kidneySold = true;
  s.stats.kidneys++;
  s.balance += Rules.PRICES.kidney;
  if (s.balance > s.stats.maxBalance) s.stats.maxBalance = s.balance;
  State.save();
  await Cutscene.play('kidney.sold', {});
  UI.renderWallet(); UI.renderSide();
  await Bus.emit('kidney.sold', {});
};

Cutscene.define('brownie.first', [
  { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Der Brownie. Vierzig Prozent Glück, einen Spin lang. Nur dass du es weißt: Der nächste kostet zehntausend. Beschwer dich beim Lieferanten.' },
]);
Cutscene.define('kidney.offer', [
  { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Ah, der Kandidat. Setz dich. Zwei Nieren, ein Hobby – das geht sich rechnerisch nicht aus.' },
  { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Zweitausend Euro, bar, Eiswanne inklusive. Dafür schluckst du ab jetzt bei jedem Spin für zwanzig Euro Tabletten. Deal?',
    choices: [{ label: 'Ja, brauch das Geld', value: 'yes', cls: 'red' }, { label: 'Nein danke', value: 'no', cls: 'ghost' }] },
]);
Cutscene.define('kidney.sold', [
  { bg: 'klinik', who: 'doc', mood: 'shock', fx: 'blackout', text: 'Zähl rückwärts von zehn. Zehn… neun…' },
  { bg: 'klinik', who: 'doc', mood: 'happy', fx: 'gain', text: 'Wach? Gut. Die Naht hält, meistens. Zweitausend liegen auf dem Nachttisch. Die Meds gehen auf dich.' },
]);
</script>
```

- [ ] **Step 3: Prüfen im Browser**

`keller37.html?fresh` öffnen, Intro wegklicken.
- Bier klicken: Kontostand rattert auf `0 €`, Toast „Prost! Bier #1", Glück-Meter zeigt ein Segment und `+10%`, Bier-Button zeigt `(1/3)`. Nochmal klicken → Toast „Bier kostet 50 €".
- In der Konsole `Game.applyDelta(5000)` → Kontostand zählt gold hoch, Wallet pulst, „+5.000 €" fliegt.
- Brownie klicken → Szene beim Wirt, danach Glück `+50%`, Brownie-Preis in der Seitenleiste `10.000 €`.
- Niere klicken → Doc-Szene, „Nein danke" → nichts passiert. Nochmal → „Ja" → Blackout, dann Münzen und Kontostand zählt um +2.000 hoch; Seitenleiste zeigt „Niere verkauft", Wallet-Zettel `💊 −20 €/Spin`.
- Konsole: `Game.beginSpin(10)` → Toast „Abzüge vor dem Spin – Meds 20 €", Rückgabe `true`; `Game.beginSpin(99999)` → Toast „Zu wenig Geld", `false`.
- Konsole: `await Game.afterSpin()` zweimal → nach dem zweiten: Toast „Ausgenüchtert", Glück sinkt.
- Reload ohne `?fresh` → Zustand erhalten, Toast „Spielstand geladen".

Run: `node tests/run-selftest.mjs` → `56 bestanden`.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat: Core-Spielschleife, afterSpin und die Bar

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Kredite (Bank & Don Vito)

**Files:**
- Modify: `keller37.html` (Template `tpl-finance`; CSS in Sektion 6; JS in `rooms`)

**Interfaces:**
- Consumes: `Game.applyDelta`, `Rules.bankLoanAllowed/bankInterest`, `Cutscene.play/define/bind`, `UI.register`.
- Produces: Screen `finance`; `Finance.render()`, `Finance.loanBank(amt)`, `Finance.repayBank()`, `Finance.loanMafia(amt)`, `Finance.repayMafia()`; Bus-Event `mafia.repaid`; Szenen `bank.loan`, `bank.limit`, `mafia.loan`, `mafia.lastcall`, `mafia.legbreak` (die letzten beiden per `Cutscene.bind` an die Core-Events).

- [ ] **Step 1: Template einfügen** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-finance">
  <div class="finance">
    <section class="counter bank">
      <h2 class="neon" style="--neon: var(--neon-blue)">Bank</h2>
      <p class="dim">Herr Krause · 30 % Zinsen pro Spin · Limit 3.000 €</p>
      <div class="paper iou" id="bankIou"></div>
      <div class="bet-bar">
        <button class="btn blue sm" data-loan="200">+200 €</button>
        <button class="btn blue sm" data-loan="500">+500 €</button>
        <button class="btn blue sm" data-loan="1000">+1.000 €</button>
        <button class="btn solid sm" id="repayBank">Tilgen</button>
      </div>
    </section>
    <section class="counter vito">
      <h2 class="neon" style="--neon: var(--neon-red)">Don Vito</h2>
      <p class="dim">Frist 5 Spins · danach 300 % OP-Kosten</p>
      <div class="paper iou" id="mafiaIou"></div>
      <div class="bet-bar">
        <button class="btn red sm" data-mloan="300">+300 €</button>
        <button class="btn red sm" data-mloan="600">+600 €</button>
        <button class="btn red sm" data-mloan="1000">+1.000 €</button>
        <button class="btn solid sm" id="repayMafia">Begleichen</button>
      </div>
    </section>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Kredite -- */
.finance { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.counter { padding: 22px; border-radius: 12px; display: flex; flex-direction: column; gap: 12px; align-items: center; text-align: center; box-shadow: var(--shadow); }
.counter.bank { background: linear-gradient(180deg, #0c1f33, #071322); border: 1px solid rgba(76,201,240,.3); }
.counter.vito { background: linear-gradient(180deg, #2a1608, #150a03); border: 1px solid rgba(255,59,59,.3); }
.counter h2 { font-size: 2rem; }
.counter .dim { color: var(--dim); font-size: .85rem; }
.iou { min-width: 230px; text-align: left; }
.iou .amt { font-size: 1.4rem; font-weight: 700; }
.iou .deadline { color: #b3261e; font-weight: 700; animation: pulseText 1s infinite; }
```

Zu Sektion 7 ergänzen: `@keyframes pulseText { 0%, 100% { opacity: 1; } 50% { opacity: .45; } }`

- [ ] **Step 3: JS in `rooms` ergänzen** – am Ende des `rooms`-Blocks vor `</script>`:

```js
/* ---- Kredite ---- */
const Finance = {
  root: null,
  render() {
    if (!this.root) return;
    const s = State.s;
    qs('#bankIou', this.root).innerHTML = s.bankDebt > 0
      ? `<h4>Schuldschein</h4><div class="amt">${UI.fmt(s.bankDebt)}</div><div>−${UI.fmt(Rules.bankInterest(s.bankDebt))} Zinsen pro Spin</div>`
      : `<h4>Schuldschein</h4><div class="amt">0 €</div><div>Sauberes Konto. Noch.</div>`;
    qs('#mafiaIou', this.root).innerHTML = s.mafiaDebt > 0
      ? `<h4>Vitos Zettel</h4><div class="amt">${UI.fmt(s.mafiaDebt)}</div><div class="deadline">Noch ${s.mafiaSpins} Spin${s.mafiaSpins === 1 ? '' : 's'}</div>`
      : `<h4>Vitos Zettel</h4><div class="amt">0 €</div><div>„Wir kennen uns nicht."</div>`;
    qsa('[data-loan]', this.root).forEach((b) => { b.disabled = !Rules.bankLoanAllowed(s, parseInt(b.dataset.loan, 10)); });
    qsa('[data-mloan]', this.root).forEach((b) => { b.disabled = s.mafiaDebt > 0; });
    qs('#repayBank', this.root).disabled = s.bankDebt === 0;
    qs('#repayMafia', this.root).disabled = s.mafiaDebt === 0;
  },
  async loanBank(amt) {
    const s = State.s;
    if (!Rules.bankLoanAllowed(s, amt)) {
      if (!s.flags.bankLimit) { s.flags.bankLimit = true; State.save(); await Cutscene.play('bank.limit', {}); }
      else UI.toast({ icon: '👔', title: 'Kreditlimit erreicht', text: 'Herr Krause bedauert. 3.000 € sind das Ende.', tone: 'loss' });
      return;
    }
    s.bankDebt += amt;
    Game.applyDelta(amt, { quiet: true });
    SFX.play('cash');
    this.render();
    if (!s.flags.bankLoan) { s.flags.bankLoan = true; State.save(); await Cutscene.play('bank.loan', {}); }
    else UI.toast({ icon: '🏦', title: `+${UI.fmt(amt)} Kredit`, text: `Schulden jetzt ${UI.fmt(s.bankDebt)}.`, tone: 'info' });
    this.render();
  },
  repayBank() {
    const s = State.s;
    if (s.bankDebt === 0) return;
    if (s.balance < s.bankDebt) { UI.toast({ icon: '🏦', title: 'Zu wenig Geld', text: `Du brauchst ${UI.fmt(s.bankDebt)}.`, tone: 'loss' }); SFX.play('lose'); return; }
    const d = s.bankDebt;
    s.bankDebt = 0;
    Game.applyDelta(-d, { from: qs('#bankIou') });
    SFX.play('stamp');
    UI.toast({ icon: '✅', title: 'Schuldenfrei', text: 'Herr Krause nickt anerkennend.', tone: 'win' });
    this.render();
  },
  async loanMafia(amt) {
    const s = State.s;
    if (s.mafiaDebt > 0) { UI.toast({ icon: '🕶️', title: 'Erst zahlen', text: 'Vito gibt keinen zweiten Kredit.', tone: 'loss' }); return; }
    s.mafiaDebt = amt;
    s.mafiaSpins = Rules.MAFIA_SPINS;
    Game.applyDelta(amt, { quiet: true });
    SFX.play('cash');
    this.render();
    if (!s.flags.mafiaLoan) { s.flags.mafiaLoan = true; State.save(); await Cutscene.play('mafia.loan', {}); }
    else UI.toast({ icon: '🕶️', title: `+${UI.fmt(amt)} von Vito`, text: 'Fünf Spins. Er zählt mit.', tone: 'loss' });
    this.render();
  },
  async repayMafia() {
    const s = State.s;
    if (s.mafiaDebt === 0) return;
    if (s.balance < s.mafiaDebt) { UI.toast({ icon: '🕶️', title: 'Zu wenig Geld', text: `Du brauchst ${UI.fmt(s.mafiaDebt)}.`, tone: 'loss' }); SFX.play('lose'); return; }
    const d = s.mafiaDebt;
    s.mafiaDebt = 0; s.mafiaSpins = 0;
    Game.applyDelta(-d, { from: qs('#mafiaIou') });
    SFX.play('stamp');
    UI.toast({ icon: '🕶️', title: 'Beglichen', text: '„Ich wusste, du bist ein Freund."', tone: 'win' });
    this.render();
    await Bus.emit('mafia.repaid', {});
  },
};

UI.register('finance', {
  template: 'tpl-finance',
  mount(root) {
    Finance.root = root;
    qsa('[data-loan]', root).forEach((b) => b.addEventListener('click', () => Finance.loanBank(parseInt(b.dataset.loan, 10))));
    qsa('[data-mloan]', root).forEach((b) => b.addEventListener('click', () => Finance.loanMafia(parseInt(b.dataset.mloan, 10))));
    qs('#repayBank', root).addEventListener('click', () => Finance.repayBank());
    qs('#repayMafia', root).addEventListener('click', () => Finance.repayMafia());
    Finance.render();
  },
  unmount() { Finance.root = null; },
});

Cutscene.define('bank.loan', [
  { bg: 'bank', who: 'krause', mood: 'calm', text: 'Willkommen bei der Sparkasse Keller 37. Ich sehe, Sie möchten liquide bleiben. Sehr vernünftig.' },
  { bg: 'bank', who: 'krause', mood: 'happy', text: 'Dreißig Prozent Zinsen – pro Spin, versteht sich. Marktüblich. Hier unten. Unterschreiben Sie bitte da, da und da.' },
]);
Cutscene.define('bank.limit', [
  { bg: 'bank', who: 'krause', mood: 'calm', text: 'Dreitausend Euro Gesamtschuld. Da geht nichts mehr, tut mir leid. Ich kann Ihnen einen Kaffee anbieten. Der ist auch nicht umsonst.' },
]);
Cutscene.define('mafia.loan', [
  { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Setz dich. Du brauchst Geld, ich habe Geld. So einfach ist das Leben manchmal.' },
  { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Fünf Spins. Dann liegt es hier auf dem Tisch. Ich rede nicht gern über das, was sonst passiert. Der Doc redet gern darüber.' },
  { bg: 'hinterzimmer', who: 'vito', mood: 'happy', text: 'Ich mag dich. Enttäusch mich nicht.' },
]);
Cutscene.define('mafia.lastcall', [
  { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Noch ein Spin, mein Freund. {{debt}}. Ich habe den Doc schon angerufen – nur zur Sicherheit.' },
]);
Cutscene.define('mafia.legbreak', [
  { bg: 'hinterzimmer', who: 'vito', mood: 'angry', fx: 'blackout', text: 'Die Frist ist um. Es tut mir leid. Wirklich. Luigi – das Bein.' },
  { bg: 'klinik', who: 'doc', mood: 'shock', fx: 'shake', text: 'KNACK. Ja, das war das Schienbein. Halt still, ich hab nur noch Zahnseide.' },
  { bg: 'klinik', who: 'doc', mood: 'calm', fx: 'drain', text: 'Not-OP, Titanplatte, Krücken: {{bill}}. Ich schreib es dir auf den Zettel. Vito lässt grüßen.' },
]);
Cutscene.bind('mafia.lastcall', 'mafia.lastcall');
Cutscene.bind('mafia.legbreak', 'mafia.legbreak');
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-finance.png "?screen=finance"` → zwei Schalter nebeneinander (blau links, rot-braun rechts), Neon-Überschriften, Papier-Schuldscheine.

Im Browser (`?screen=finance`): +500 € → Szene bei Krause, danach Schuldschein `500 €`, Wallet-Zettel `🏦 500 € · −150 €/Spin`. Dreimal +1.000 → beim vierten Versuch Szene „bank.limit", Buttons für 1.000 deaktiviert, sobald `bankDebt` 2.000 überschreitet. Tilgen ohne Geld → Toast „Zu wenig Geld". Vito +300 → Vito-Szene (3 Panels), Zettel mit rot pulsierender Frist „Noch 5 Spins"; zweiter Vito-Button deaktiviert. Konsole: `for (let i=0;i<4;i++) await Game.afterSpin()` → nach dem 4. Spin Szene „mafia.lastcall"; ein weiteres `await Game.afterSpin()` → Legbreak-Szene mit Blackout, Shake, Kontostand rattert um 900 runter.

Run: `node tests/run-selftest.mjs` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Kredite bei Bank und Don Vito mit Szenen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Anlagen

**Files:**
- Modify: `keller37.html` (Template `tpl-invest`; CSS Sektion 6; JS in `rooms`)

**Interfaces:**
- Consumes: `Rules.INVEST`, `Game.applyDelta`, `Bus` (`invest.resolved` aus Core).
- Produces: Screen `invest`; `Invest.invest(type)`, `Invest.render()`.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-invest">
  <div class="panel stretch">
    <h2>📈 Anlagen</h2>
    <div class="tickets" id="tickets"></div>
    <div class="invest-grid">
      <div class="chalk inv" data-type="bank">
        <h4>🏦 Festgeld</h4>
        <p class="dim">+8 % · 5 Spins · 10 % Risiko</p>
        <div class="bet-field"><button data-step="-10">−</button><input type="number" id="invBank" value="50" min="10"><button data-step="10">+</button></div>
        <button class="btn blue sm" data-invest="bank">Anlegen</button>
      </div>
      <div class="chalk inv" data-type="stock">
        <h4>🚀 Aktien</h4>
        <p class="dim">+100 % · 2 Spins · <strong>85 % Risiko</strong></p>
        <div class="bet-field"><button data-step="-10">−</button><input type="number" id="invStock" value="20" min="10"><button data-step="10">+</button></div>
        <button class="btn red sm" data-invest="stock">Zocken</button>
      </div>
      <div class="chalk inv" data-type="scam">
        <h4>🕶️ Trickbetrug</h4>
        <p class="dim">+30 % · 10 Spins · <strong>55 % Risiko</strong></p>
        <div class="bet-field"><button data-step="-10">−</button><input type="number" id="invScam" value="50" min="10"><button data-step="10">+</button></div>
        <button class="btn sm" style="--c: var(--neon-purple); color: #e0c8ff" data-invest="scam">Riskieren</button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Anlagen -- */
.invest-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.chalk.inv { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }
.chalk.inv .dim { font-size: .85rem; }
.tickets { display: flex; flex-wrap: wrap; gap: 10px; min-height: 40px; }
.ticket { background: #f6e6b3; color: var(--paper-ink); font-family: var(--font-mono); font-size: .85rem; padding: 8px 12px; border: 1px dashed #8a6d1a; transform: rotate(-1deg); animation: popIn .25s ease both; }
.ticket b { font-family: var(--font-display); letter-spacing: .08em; }
.tickets .empty { color: var(--dim); font-family: var(--font-mono); font-size: .85rem; align-self: center; }
```

- [ ] **Step 3: JS in `rooms`** – am Ende vor `</script>`:

```js
/* ---- Anlagen ---- */
const Invest = {
  root: null,
  INPUT: { bank: 'invBank', stock: 'invStock', scam: 'invScam' },
  render() {
    if (!this.root) return;
    const box = qs('#tickets', this.root);
    box.innerHTML = '';
    if (State.s.investments.length === 0) { box.append(h('span', { class: 'empty' }, 'Keine laufenden Anlagen.')); return; }
    for (const inv of State.s.investments) {
      box.append(h('div', { class: 'ticket' }, h('b', {}, inv.name), ` · ${UI.fmt(inv.amount)} · noch ${inv.spins} Spin${inv.spins === 1 ? '' : 's'}`));
    }
  },
  invest(type) {
    const s = State.s;
    const def = Rules.INVEST[type];
    const amt = parseInt(qs('#' + this.INPUT[type], this.root).value, 10);
    if (!Number.isFinite(amt) || amt < def.min) { UI.toast({ icon: '🚫', title: 'Mindestens 10 €', tone: 'loss' }); SFX.play('lose'); return; }
    if (s.balance < amt) { UI.toast({ icon: '🚫', title: 'Zu wenig Geld', text: `Du hast ${UI.fmt(s.balance)}.`, tone: 'loss' }); SFX.play('lose'); return; }
    Game.applyDelta(-amt, { from: qs(`[data-type="${type}"]`, this.root) });
    s.investments.push({ name: def.name, amount: amt, rate: def.rate, spins: def.spins, risk: def.risk });
    State.save();
    SFX.play('chip');
    UI.toast({ icon: '📈', title: `${def.name} angelegt`, text: `${UI.fmt(amt)} für ${def.spins} Spins.`, tone: 'info' });
    this.render();
    UI.renderSide();
  },
};

UI.register('invest', {
  template: 'tpl-invest',
  mount(root) {
    Invest.root = root;
    qsa('.chalk.inv', root).forEach((card) => Game.bindBet(card, Invest.INPUT[card.dataset.type]));
    qsa('[data-invest]', root).forEach((b) => b.addEventListener('click', () => Invest.invest(b.dataset.invest)));
    Invest.render();
  },
  unmount() { Invest.root = null; },
});
Bus.on('invest.resolved', () => Invest.render());
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-invest.png "?screen=invest"` → drei Kreidetafeln nebeneinander, oben „Keine laufenden Anlagen.".

Im Browser (`?screen=invest`): Festgeld 50 → Kontostand −50, Ticket „FESTGELD · 50 € · noch 5 Spins", Seitenleiste „1 aktiv". Wert 5 eintragen → Toast „Mindestens 10 €". Konsole: `for (let i=0;i<5;i++) await Game.afterSpin()` → Ticket verschwindet, Toast „Festgeld ausgezahlt +54 €" (oder Totalverlust bei 10 %).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Anlagen-Raum mit Tickets

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Zuhause (Leben) mit Villa, Chantal, Scheidung, Therapie, Dealer

**Files:**
- Modify: `keller37.html` (Template `tpl-life`; CSS Sektion 6; JS + Szenen in `rooms`)

**Interfaces:**
- Consumes: `Rules.canBuyHouse/canTinder/canTherapy/canDealer`, `Game.applyDelta`, `Cutscene`, Core-Events `divorce`, `heartbreak.collapse`.
- Produces: Screen `life`; `Life.render()`, `Life.buyHouse()`, `Life.tinder()`, `Life.therapy()`, `Life.dealer()`; Bus-Events `house.bought`, `tinder.match`, `therapy.done`, `dealer.hired`; Szenen `house.bought`, `tinder.match`, `divorce`, `heartbreak.collapse`, `therapy.done`, `dealer.hired`. Der Container `#trophyGrid` bleibt leer bis Task 18.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-life">
  <div class="panel stretch life">
    <h2>🏡 Lebenslauf</h2>
    <div class="life-grid">
      <div class="life-card" id="lifeHouse"></div>
      <div class="life-card" id="lifeLove"></div>
      <div class="life-card" id="lifeDealer"></div>
    </div>
    <div class="chalk" id="trophies"><h4>🏆 Trophäenwand</h4><div class="trophy-grid" id="trophyGrid"></div></div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Zuhause -- */
.life-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.life-card { background: var(--panel-2); border: 1px solid rgba(255,255,255,.06); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; gap: 10px; align-items: center; text-align: center; }
.life-card .pic { font-size: 3.2rem; height: 70px; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0 4px 8px rgba(0,0,0,.6)); }
.life-card .pic.empty { opacity: .3; filter: grayscale(1); }
.life-card h4 { font-family: var(--font-display); letter-spacing: .1em; font-size: 1.3rem; }
.life-card p { font-size: .85rem; color: var(--dim); }
.life-card .reason { font-family: var(--font-mono); font-size: .8rem; color: #d8d2c0; background: #1a1a1a; border: 1px solid #333; padding: 4px 10px; transform: rotate(-1deg); }
.life-card .reason.warn { color: #ffb3b3; }
.trophy-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-top: 6px; }
```

- [ ] **Step 3: JS + Szenen in `rooms`** – am Ende vor `</script>`:

```js
/* ---- Zuhause ---- */
const Life = {
  root: null,
  REASON: {
    debts: 'Erst Schulden tilgen', heartbroken: 'Erst Liebeskummer heilen', married: 'Chantal will kein zweites Haus',
    funds: 'Zu wenig Geld', house: 'Ohne Haus keine Matches', owned: 'Schon erledigt', notNeeded: 'Kein Liebeskummer',
  },
  card(el, { pic, empty, title, text, action, label, cls, check }) {
    el.innerHTML = '';
    el.append(h('div', { class: 'pic' + (empty ? ' empty' : '') }, pic), h('h4', {}, title), h('p', {}, text));
    if (!check) return;
    if (check.ok) el.append(h('button', { class: `btn ${cls || ''}`, onclick: action }, label));
    else el.append(h('span', { class: 'reason' + (check.reason === 'funds' ? '' : ' warn') }, this.REASON[check.reason] || check.reason));
  },
  render() {
    if (!this.root) return;
    const s = State.s;
    this.card(qs('#lifeHouse', this.root), s.hasHouse
      ? { pic: '🏰', title: 'Penthouse-Villa', text: 'Blick auf den Hafen. +30 €/min von Untermietern, nach denen du nicht fragst.' }
      : { pic: '🏚️', empty: true, title: 'Kein Haus', text: 'Penthouse für 2.500 €. Nur ohne Schulden, nüchtern im Herzen und ledig.', action: () => Life.buyHouse(), label: 'Kaufen · 2.500 €', check: Rules.canBuyHouse(s) });
    const love = s.isHeartbroken
      ? { pic: '💔', title: 'Liebeskummer', text: 'Chantal ist weg, das Haus auch. Ohne 2 Bier pro Spin klappst du zusammen (−250 €).', action: () => Life.therapy(), label: 'Therapie & Anwalt · 5.000 €', cls: 'pink', check: Rules.canTherapy(s) }
      : s.isMarried
        ? { pic: '💍', title: 'Verheiratet', text: `Mit Chantal-Monique. Noch ${Rules.MARRIAGE_SPINS - s.marriageSpins} Spin${Rules.MARRIAGE_SPINS - s.marriageSpins === 1 ? '' : 's'} bis… irgendwas.` }
        : { pic: '🔥', empty: !s.hasHouse, title: 'Tinder Gold', text: 'Chantal-Monique steht auf Penthouses. 50 €, und ihr heiratet sofort.', action: () => Life.tinder(), label: 'Matchen · 50 €', cls: 'pink', check: Rules.canTinder(s) };
    this.card(qs('#lifeLove', this.root), love);
    this.card(qs('#lifeDealer', this.root), s.hasDealer
      ? { pic: '🧢', title: 'Kevin arbeitet', text: '+50 €/min. Pünktlich wie die Bahn. Also pünktlicher.' }
      : { pic: '🧢', empty: true, title: 'Drogendealer', text: 'Kevin will 5.000 € Startkapital. Dafür +50 €/min, dauerhaft.', action: () => Life.dealer(), label: 'Anheuern · 5.000 €', cls: 'blue', check: Rules.canDealer(s) });
  },
  async buyHouse() {
    const s = State.s;
    if (!Rules.canBuyHouse(s).ok) return;
    Game.applyDelta(-Rules.PRICES.house, { from: qs('#lifeHouse') });
    s.hasHouse = true; State.save();
    this.render(); UI.renderWallet(); UI.renderSide();
    await Bus.emit('house.bought', {});
    this.render();
  },
  async tinder() {
    const s = State.s;
    if (!Rules.canTinder(s).ok) return;
    Game.applyDelta(-Rules.PRICES.tinder, { from: qs('#lifeLove') });
    s.isMarried = true; s.marriageSpins = 0; State.save();
    this.render(); UI.renderWallet();
    await Bus.emit('tinder.match', {});
    this.render();
  },
  async therapy() {
    const s = State.s;
    if (!Rules.canTherapy(s).ok) return;
    Game.applyDelta(-Rules.PRICES.therapy, { from: qs('#lifeLove') });
    s.isHeartbroken = false; State.save();
    this.render(); UI.renderWallet();
    await Bus.emit('therapy.done', {});
    this.render();
  },
  async dealer() {
    const s = State.s;
    if (!Rules.canDealer(s).ok) return;
    Game.applyDelta(-Rules.PRICES.dealer, { from: qs('#lifeDealer') });
    s.hasDealer = true; State.save();
    this.render(); UI.renderWallet();
    await Bus.emit('dealer.hired', {});
    this.render();
  },
};

UI.register('life', {
  template: 'tpl-life',
  mount(root) { Life.root = root; Life.render(); if (typeof Achievements !== 'undefined') Achievements.renderWall(qs('#trophyGrid', root)); },
  unmount() { Life.root = null; },
});
Bus.on('spin:after', () => Life.render());

Cutscene.define('house.bought', [
  { bg: 'villa', who: 'makler', mood: 'happy', text: 'Traumlage! Penthouse, Blick auf den Hafen, Nachbarn, die nicht fragen. Hier sind die Schlüssel.' },
  { bg: 'villa', who: 'makler', mood: 'calm', text: 'Dreißig Euro die Minute wirft die Bude ab – Untermieter, frag nicht welche. Und jetzt: Tinder Gold. Du hast schließlich ein Penthouse.' },
]);
Cutscene.define('tinder.match', [
  { bg: 'standesamt', who: 'chantal', mood: 'happy', text: 'Ehrlich jetzt – ein Penthouse?! Du bist ja soooo reif. ✨ It’s a match!' },
  { bg: 'standesamt', who: 'chantal', mood: 'happy', fx: 'hearts', text: 'Ich hab schon das Standesamt gebucht. Meine Follower flippen aus.' },
  { bg: 'standesamt', who: 'du', mood: 'happy', text: '„Ja, ich will." – Irgendwo in der Ferne lacht ein Anwalt.' },
]);
Cutscene.define('divorce', [
  { bg: 'hafen', who: 'chantal', mood: 'angry', text: 'Ehrlich jetzt, Schatz… es liegt nicht an dir. Es liegt an deinem Kontostand.' },
  { bg: 'hafen', who: 'schmalz', mood: 'calm', text: 'Dr. Schmalz, Fachanwalt für Familienrecht. Das Penthouse geht an meine Mandantin. Das Konto teilen wir. Fair ist fair.' },
  { bg: 'hafen', who: 'schmalz', mood: 'calm', fx: 'drain', text: '{{before}} durch zwei macht {{after}}. Ich runde zu ihren Gunsten.' },
  { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Komm, setz dich. Ab jetzt brauchst du zwei Bier intus, sonst klappst du zusammen. Ärztlicher Rat. Meiner.' },
]);
Cutscene.define('heartbreak.collapse', [
  { bg: 'klinik', who: 'doc', mood: 'shock', fx: 'shake', text: 'Kreislauf! Weniger als zwei Bier bei akutem Liebeskummer – das ist grob fahrlässig.' },
  { bg: 'klinik', who: 'doc', mood: 'calm', fx: 'drain', text: 'Notarzt, Infusion, ein Brownie zur Beruhigung: {{bill}}. Trink nächstes Mal.' },
]);
Cutscene.define('therapy.done', [
  { bg: 'hinterzimmer', who: 'schmalz', mood: 'calm', text: 'Fünftausend. Davon gehen viertausendneunhundert an mich und hundert an die Therapeutin. Sie sagt, Sie sollen loslassen.' },
  { bg: 'hinterzimmer', who: 'schmalz', mood: 'happy', text: 'Herzlichen Glückwunsch, Sie sind geheilt. Kein Bierzwang mehr. Rechtlich gesehen.' },
]);
Cutscene.define('dealer.hired', [
  { bg: 'strasse', who: 'kevin', mood: 'calm', text: 'Digga, fünf Riesen Startkapital, und ich mach den Rest. Frag nicht, was der Rest ist.' },
  { bg: 'strasse', who: 'kevin', mood: 'happy', text: 'Fuffzig die Minute, pünktlich wie die Bahn. Also pünktlicher.' },
]);
Cutscene.bind('house.bought', 'house.bought');
Cutscene.bind('tinder.match', 'tinder.match');
Cutscene.bind('divorce', 'divorce');
Cutscene.bind('heartbreak.collapse', 'heartbreak.collapse');
Cutscene.bind('therapy.done', 'therapy.done');
Cutscene.bind('dealer.hired', 'dealer.hired');
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-life.png "?screen=life&fresh"` → drei Karten (🏚️ ausgegraut mit Kreide-Notiz „Zu wenig Geld", 🔥 mit „Ohne Haus keine Matches", 🧢 mit „Zu wenig Geld"), darunter Kreidetafel „Trophäenwand".

Im Browser (`?screen=life&fresh`): Konsole `Game.applyDelta(10000)`; Kaufen → Makler-Szene, Karte zeigt 🏰, Wallet-Zettel `💸 +30 €/min`. Matchen → Chantal-Szene mit Herzen, Karte 💍 „Noch 2 Spins". Konsole `await Game.afterSpin(); await Game.afterSpin()` → Scheidungs-Szene (4 Panels), Kontostand rattert im Panel 3 auf die Hälfte, Haus-Karte wieder 🏚️, Liebes-Karte 💔 mit Therapie-Button. `await Game.afterSpin()` ohne Bier → Kollaps-Szene, −250. Zwei Bier kaufen, `await Game.afterSpin()` → keine Szene. Therapie → Schmalz-Szene, Karte zurück auf 🔥. Dealer → Kevin-Szene, Zettel `+50 €/min` (bzw. `+80` mit Haus). Eine Minute warten → Toast „Passives Einkommen".

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Zuhause mit Villa, Chantal, Scheidung, Therapie und Dealer

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Slots mit echten Walzen

**Files:**
- Modify: `keller37.html` (Template `tpl-slots`; CSS Sektion 6 + Keyframes; neuer Block `<script id="game-slots">` nach `rooms`)

**Interfaces:**
- Consumes: `Rules.SYMBOLS/slotRoll/slotLuckOverride/slotMultiplier/slotDelta/luck`, `Game.beginSpin/readBet/bindBet/settle`, `SFX`, `UI`.
- Produces: Screen `slots`; `Slots.spin()`; Bus-Event `slots:result {res, m, bet}`.
- Walzen-Zellhöhe kommt aus der CSS-Variable `--cell` (Desktop 90px, Mobile später 64px); JS liest sie aus dem DOM.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-slots">
  <div class="panel slots-panel">
    <div class="slots-top">
      <div class="slot-machine">
        <div class="slot-head neon" style="--neon: var(--neon-amber)">Lucky Seven</div>
        <div class="reels">
          <div class="reel-win" id="reel1"><div class="strip"></div></div>
          <div class="reel-win" id="reel2"><div class="strip"></div></div>
          <div class="reel-win" id="reel3"><div class="strip"></div></div>
          <div class="payline"></div>
        </div>
        <div class="lever" id="lever" title="Hebel ziehen (Leertaste)"><div class="lever-arm"></div><div class="lever-knob"></div></div>
      </div>
      <div class="chalk paytable">
        <h4>Auszahlung</h4>
        <table>
          <tr><td>7️⃣ 7️⃣ 7️⃣</td><td>50×</td></tr>
          <tr><td>💎 💎 💎</td><td>25×</td></tr>
          <tr><td>🔔 🔔 🔔</td><td>15×</td></tr>
          <tr><td>Drilling</td><td>5×</td></tr>
          <tr><td>Paar</td><td>1,5×</td></tr>
        </table>
      </div>
    </div>
    <div class="status" id="slotStatus">Einsatz wählen und Hebel ziehen</div>
    <div class="bet-bar">
      <div class="bet-field"><button data-step="-5">−</button><input type="number" id="slotBet" value="10" min="1"><button data-step="5">+</button></div>
      <button class="chip" data-chip="10" data-v="10">10</button>
      <button class="chip" data-chip="25" data-v="25">25</button>
      <button class="chip" data-chip="50" data-v="50">50</button>
      <button class="chip" data-chip="max" data-v="max">MAX</button>
      <button class="btn solid" id="btnSpin">Drehen</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Slots -- */
.slots-top { display: flex; gap: 20px; align-items: flex-start; justify-content: center; flex-wrap: wrap; }
.slot-machine { --cell: 90px; position: relative; background: linear-gradient(180deg, #5a1d1d, #2a0d0d); border: 4px solid var(--gold); border-radius: 18px; padding: 16px 70px 22px 22px; box-shadow: var(--shadow), inset 0 0 40px rgba(0,0,0,.6); }
.slot-head { text-align: center; font-size: 2rem; margin-bottom: 10px; }
.reels { position: relative; display: flex; gap: 10px; background: #0a0a0a; padding: 12px; border-radius: 10px; border: 3px solid #3a2a12; }
.reel-win { width: var(--cell); height: var(--cell); overflow: hidden; background: linear-gradient(180deg, #fff 0%, #e8e2d0 50%, #cfc8b3 100%); border-radius: 6px; position: relative;
  box-shadow: inset 0 8px 12px rgba(0,0,0,.35), inset 0 -8px 12px rgba(0,0,0,.35); }
.reel-win .strip { display: flex; flex-direction: column; will-change: transform; }
.reel-win .cell { height: var(--cell); display: flex; align-items: center; justify-content: center; font-size: calc(var(--cell) * .55); }
.strip.spinning { animation: reelSpin .35s linear infinite; filter: blur(2px); }
.reel-win.locked { box-shadow: inset 0 8px 12px rgba(0,0,0,.35), inset 0 -8px 12px rgba(0,0,0,.35), 0 0 0 3px var(--gold); }
.reel-win.hit { animation: hitGlow .6s ease 3; }
.payline { position: absolute; left: 6px; right: 6px; top: 50%; height: 2px; background: rgba(255,59,59,.5); pointer-events: none; }
.lever { position: absolute; right: 14px; top: 60px; width: 40px; height: 140px; cursor: pointer; }
.lever::after { content: ""; position: absolute; left: 12px; bottom: 0; width: 16px; height: 30px; background: #333; border-radius: 4px 4px 0 0; }
.lever-arm { position: absolute; left: 16px; top: 20px; width: 8px; height: 90px; background: linear-gradient(90deg, #888, #ddd, #777); border-radius: 4px; transform-origin: 50% 100%; transition: transform .25s cubic-bezier(.3,1.4,.5,1); }
.lever-knob { position: absolute; left: 4px; top: 4px; width: 32px; height: 32px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #ff7b7b, #a00); box-shadow: 0 3px 6px #000; transition: transform .25s cubic-bezier(.3,1.4,.5,1); }
.lever.pulled .lever-arm { transform: rotateX(140deg); }
.lever.pulled .lever-knob { transform: translateY(80px) scale(.8); }
.paytable { min-width: 190px; }
.jackpot { position: absolute; left: 50%; top: 40%; transform: translate(-50%, -50%); font-size: 3.5rem; z-index: 5; animation: jackpotPop .5s cubic-bezier(.3,1.5,.5,1) both; pointer-events: none; }
.coin-p { position: absolute; font-size: 1.6rem; pointer-events: none; animation: coinFall 1.5s ease-in both; z-index: 4; }
```

Zu Sektion 7 ergänzen:

```css
@keyframes reelSpin { from { transform: translateY(0); } to { transform: translateY(calc(var(--cell) * -6)); } }
@keyframes hitGlow { 0%, 100% { box-shadow: 0 0 0 3px var(--gold); } 50% { box-shadow: 0 0 22px 6px var(--gold-2); } }
@keyframes jackpotPop { from { transform: translate(-50%, -50%) scale(.2); opacity: 0; } to { transform: translate(-50%, -50%) scale(1); opacity: 1; } }
@keyframes coinFall { 0% { transform: translateY(-40px) rotate(0); opacity: 1; } 100% { transform: translateY(260px) rotate(360deg); opacity: 0; } }
```

- [ ] **Step 3: JS-Block einfügen** – nach `</script>` von `rooms`:

```html
<script id="game-slots">
/* ================= SLOTS ================= */
const Slots = {
  root: null,
  spinning: false,
  cell() { const c = qs('.cell', this.root); return c ? c.offsetHeight : 90; },
  buildStrips() {
    qsa('.strip', this.root).forEach((strip) => {
      strip.innerHTML = '';
      for (let r = 0; r < 3; r++) for (const s of Rules.SYMBOLS) strip.append(h('div', { class: 'cell' }, s));
    });
  },
  setReel(i, sym, animate) {
    const strip = qs(`#reel${i} .strip`, this.root);
    if (!strip) return;
    const idx = Rules.SYMBOLS.indexOf(sym);
    strip.classList.remove('spinning');
    strip.style.transition = animate ? 'transform .45s cubic-bezier(.2,1.5,.4,1)' : 'none';
    strip.style.transform = `translateY(${-(6 + idx) * this.cell()}px)`;
  },
  async spin() {
    if (this.spinning || !this.root) return;
    const bet = Game.readBet('slotBet');
    if (!Game.beginSpin(bet)) return;
    this.spinning = true;
    qs('#btnSpin', this.root).disabled = true;
    const lever = qs('#lever', this.root);
    lever.classList.add('pulled');
    setTimeout(() => lever.classList.remove('pulled'), 500);
    qs('#slotStatus', this.root).textContent = 'Walzen laufen…';
    qsa('.reel-win', this.root).forEach((r) => r.classList.remove('locked', 'hit'));
    let res = Rules.slotRoll(Math.random);
    res = Rules.slotLuckOverride(res, Rules.luck(State.s), Math.random);
    qsa('.strip', this.root).forEach((s) => { s.style.transition = 'none'; s.style.transform = 'translateY(0)'; void s.offsetHeight; s.classList.add('spinning'); });
    SFX.loop('reelSpin', 120);
    [800, 1400, 2000].forEach((ms, i) => setTimeout(() => {
      if (!this.root) return;
      this.setReel(i + 1, res[i], true);
      qs(`#reel${i + 1}`, this.root).classList.add('locked');
      SFX.play('reelStop');
      if (i === 2) SFX.stop('reelSpin');
    }, ms));
    await wait(2450);
    SFX.stop('reelSpin');
    const m = Rules.slotMultiplier(...res);
    const delta = Rules.slotDelta(bet, m);
    if (this.root) {
      const stat = qs('#slotStatus', this.root);
      if (m > 0) {
        stat.innerHTML = `<span class="win">${String(m).replace('.', ',')}× · +${UI.fmt(Math.round(bet * m))}</span>`;
        qsa('.reel-win', this.root).forEach((r) => r.classList.add('hit'));
        if (m >= 25) this.jackpot(m === 50 ? 'JACKPOT' : 'DIAMANTEN');
      } else {
        stat.innerHTML = `<span class="loss">Niete · −${UI.fmt(bet)}</span>`;
      }
    }
    await Bus.emit('slots:result', { res, m, bet });
    await Game.settle(delta, { from: this.root ? qs('.slot-machine', this.root) : null, game: 'slots' });
    this.spinning = false;
    if (this.root) qs('#btnSpin', this.root).disabled = false;
  },
  jackpot(label) {
    const machine = qs('.slot-machine', this.root);
    const sign = h('div', { class: 'jackpot neon', style: '--neon: var(--neon-amber)' }, label);
    machine.append(sign);
    setTimeout(() => sign.remove(), 2500);
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    for (let i = 0; i < 40; i++) {
      const c = h('span', { class: 'coin-p', style: `left:${rand(5, 90)}%; top:${rand(0, 30)}%; animation-delay:${rand(0, 0.8)}s` }, pick(['🪙', '💰', '💶']));
      machine.append(c);
      setTimeout(() => c.remove(), 2600);
    }
  },
  onKey(e) { if (e.code === 'Space' && qs('#cutscene').hidden && !e.repeat) { e.preventDefault(); Slots.spin(); } },
};

UI.register('slots', {
  template: 'tpl-slots',
  mount(root) {
    Slots.root = root;
    Slots.buildStrips();
    ['🍒', '7️⃣', '💎'].forEach((s, i) => Slots.setReel(i + 1, s, false));
    Game.bindBet(root, 'slotBet');
    qs('#btnSpin', root).addEventListener('click', () => Slots.spin());
    qs('#lever', root).addEventListener('click', () => Slots.spin());
    document.addEventListener('keydown', Slots.onKey);
  },
  unmount() { document.removeEventListener('keydown', Slots.onKey); Slots.root = null; },
});
</script>
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-slots.png "?screen=slots"` → rote Maschine mit Goldrahmen, drei weiße Walzenfenster mit 🍒 7️⃣ 💎, Hebel rechts, Kreidetafel „Auszahlung", Chips und „Drehen".

Im Browser: Hebel klicken → Hebel klappt, Walzen scrollen mit Blur, stoppen nacheinander mit Bounce (0,8 / 1,4 / 2,0 s) und Goldrahmen, Kontostand bewegt sich, Status zeigt Ergebnis. Leertaste startet ebenfalls. Konsole `State.s.beers=3; State.s.beerTimer=2; State.s.brownieTimer=1; State.save()` (Glück 60 %) und mehrfach drehen → häufig Paare/Jackpots; bei 💎💎💎 oder 7️⃣7️⃣7️⃣ Münzregen + Neonschild. Während des Laufens auf das Neonschild „Keller 37" klicken → Hub erscheint, keine Fehler in der Konsole, Kontostand wird trotzdem korrekt verbucht.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Slots mit scrollenden Walzen, Hebel und Jackpot

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: Blackjack am Filztisch

**Files:**
- Modify: `keller37.html` (Template `tpl-blackjack`; CSS Sektion 6 + Keyframes; neuer Block `<script id="game-blackjack">`)

**Interfaces:**
- Consumes: `Rules.newDeck/handSum/dealerShouldHit/bjOutcome/bjDelta`, `Game`, `SFX`, `UI`.
- Produces: Screen `blackjack`; `Blackjack.start/hit/stand`; Bus-Event `blackjack:result {outcome, bet}`.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-blackjack">
  <div class="panel bj-panel felt">
    <div class="bj-table">
      <div class="shoe" id="shoe"></div>
      <div class="bj-hand dealer">
        <div class="hand-label">Dealer <span class="hand-val" id="bjDealerVal">–</span></div>
        <div class="cards" id="dealerCards"></div>
      </div>
      <div class="bj-arc">Black Jack zahlt 1:1 · Dealer zieht bis 17</div>
      <div class="bj-hand player">
        <div class="cards" id="playerCards"></div>
        <div class="hand-label">Du <span class="hand-val" id="bjPlayerVal">–</span></div>
      </div>
    </div>
    <div class="status" id="bjStatus">Einsatz setzen</div>
    <div class="bet-bar" id="bjBetControls">
      <div class="bet-field"><button data-step="-5">−</button><input type="number" id="bjBet" value="10" min="1"><button data-step="5">+</button></div>
      <button class="chip" data-chip="10" data-v="10">10</button>
      <button class="chip" data-chip="25" data-v="25">25</button>
      <button class="chip" data-chip="50" data-v="50">50</button>
      <button class="chip" data-chip="max" data-v="max">MAX</button>
      <button class="btn solid" id="btnDeal">Austeilen</button>
    </div>
    <div class="bet-bar hidden" id="bjActionControls">
      <button class="btn green" id="btnHit">Hit</button>
      <button class="btn red" id="btnStand">Stand</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Blackjack -- */
.bj-panel { border: 6px solid #3b2a12; border-radius: 160px 160px 14px 14px; }
.bj-panel .status { color: #d9e6d0; }
.bj-table { position: relative; width: 100%; display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 10px 0; }
.shoe { position: absolute; right: 24px; top: 0; width: 60px; height: 84px; border-radius: 6px; background: repeating-linear-gradient(135deg, #7a2a2a 0 6px, #5a1a1a 6px 12px); border: 2px solid #c9a227; box-shadow: 0 6px 12px rgba(0,0,0,.6); }
.shoe::after { content: ""; position: absolute; inset: 6px; border: 1px solid rgba(255,255,255,.3); border-radius: 3px; }
.bj-arc { font-family: var(--font-display); letter-spacing: .2em; color: rgba(232,198,90,.45); font-size: 1rem; border-top: 1px solid rgba(232,198,90,.25); border-bottom: 1px solid rgba(232,198,90,.25); padding: 4px 30px; }
.bj-hand { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.hand-label { font-family: var(--font-display); letter-spacing: .12em; color: #d9e6d0; font-size: 1.1rem; }
.hand-val { font-family: var(--font-mono); background: #1c1e1a; border: 2px solid #4a3a2a; padding: 0 8px; margin-left: 6px; color: #fff; }
.hand-val.push { color: var(--gold-2); }
.cards { display: flex; gap: 8px; min-height: 96px; align-items: center; }
.pcard { width: 66px; height: 94px; perspective: 600px; }
.pcard.dealing { animation: dealIn .35s cubic-bezier(.2,.9,.3,1) both; }
.pcard .inner { position: relative; width: 100%; height: 100%; transform-style: preserve-3d; transition: transform .5s; }
.pcard.hidden-card .inner { transform: rotateY(180deg); }
.pcard .face, .pcard .back { position: absolute; inset: 0; border-radius: 6px; backface-visibility: hidden; box-shadow: 0 4px 8px rgba(0,0,0,.6); }
.pcard .face { background: #fdfaf0; color: #111; font-family: var(--font-mono); font-weight: 700; }
.pcard .face.red { color: #c1121f; }
.pcard .corner { position: absolute; font-size: .8rem; line-height: 1; }
.pcard .corner.tl { top: 5px; left: 6px; }
.pcard .corner.br { bottom: 5px; right: 6px; transform: rotate(180deg); }
.pcard .pip { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 2rem; }
.pcard .back { background: repeating-linear-gradient(45deg, #7a2a2a 0 4px, #5a1a1a 4px 8px); border: 4px solid #fdfaf0; transform: rotateY(180deg); }
.pcard.bust .face { box-shadow: 0 0 18px 4px rgba(255,59,59,.7); }
.pcard.bust { animation: bustSlide .6s ease .2s both; }
```

Zu Sektion 7 ergänzen:

```css
@keyframes dealIn { from { transform: translate(220px, -120px) rotate(25deg); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes bustSlide { to { transform: translateY(30px) rotate(6deg); opacity: .4; } }
```

- [ ] **Step 3: JS-Block** – nach `</script>` von `game-slots`:

```html
<script id="game-blackjack">
/* ================= BLACKJACK ================= */
const Blackjack = {
  root: null, deck: [], pHand: [], dHand: [], bet: 0, dealing: false, inRound: false,
  cardEl(c, hidden = false) {
    const red = ['♥', '♦'].includes(c.suit);
    return h('div', { class: `pcard dealing${hidden ? ' hidden-card' : ''}` },
      h('div', { class: 'inner' },
        h('div', { class: `face${red ? ' red' : ''}` },
          h('span', { class: 'corner tl' }, c.val, h('br'), c.suit),
          h('span', { class: 'pip' }, c.suit),
          h('span', { class: 'corner br' }, c.val, h('br'), c.suit)),
        h('div', { class: 'back' })));
  },
  async dealTo(elId, card, hidden = false) {
    if (!this.root) return;
    qs('#' + elId, this.root).append(this.cardEl(card, hidden));
    SFX.play('cardSlide');
    await wait(240);
  },
  updateVals(revealDealer) {
    if (!this.root) return;
    qs('#bjPlayerVal', this.root).textContent = Rules.handSum(this.pHand);
    qs('#bjDealerVal', this.root).textContent = revealDealer ? Rules.handSum(this.dHand) : '?';
  },
  async start() {
    if (this.inRound || !this.root) return;
    const bet = Game.readBet('bjBet');
    if (!Game.beginSpin(bet)) return;
    this.inRound = true; this.dealing = true; this.bet = bet;
    this.deck = Rules.newDeck(Math.random); this.pHand = []; this.dHand = [];
    qs('#playerCards', this.root).innerHTML = ''; qs('#dealerCards', this.root).innerHTML = '';
    qsa('.hand-val', this.root).forEach((v) => v.classList.remove('push'));
    qs('#bjBetControls', this.root).classList.add('hidden');
    qs('#bjActionControls', this.root).classList.remove('hidden');
    qs('#bjStatus', this.root).textContent = 'Hit oder Stand?';
    this.pHand.push(this.deck.pop()); await this.dealTo('playerCards', this.pHand[0]);
    this.dHand.push(this.deck.pop()); await this.dealTo('dealerCards', this.dHand[0], true);
    this.pHand.push(this.deck.pop()); await this.dealTo('playerCards', this.pHand[1]);
    this.dHand.push(this.deck.pop()); await this.dealTo('dealerCards', this.dHand[1]);
    this.updateVals(false);
    this.dealing = false;
  },
  async hit() {
    if (this.dealing || !this.inRound) return;
    this.dealing = true;
    const c = this.deck.pop();
    this.pHand.push(c);
    await this.dealTo('playerCards', c);
    this.updateVals(false);
    this.dealing = false;
    if (Rules.handSum(this.pHand) > 21) await this.finish('bust');
  },
  async stand() {
    if (this.dealing || !this.inRound) return;
    this.dealing = true;
    if (this.root) {
      qs('#bjActionControls', this.root).classList.add('hidden');
      const hole = qs('#dealerCards .pcard', this.root);
      if (hole) hole.classList.remove('hidden-card');
      SFX.play('cardSlide');
      await wait(550);
      this.updateVals(true);
    }
    while (Rules.dealerShouldHit(this.dHand)) {
      const c = this.deck.pop();
      this.dHand.push(c);
      await this.dealTo('dealerCards', c);
      this.updateVals(true);
      await wait(300);
    }
    this.dealing = false;
    await this.finish(Rules.bjOutcome(Rules.handSum(this.pHand), Rules.handSum(this.dHand)));
  },
  async finish(outcome) {
    const delta = Rules.bjDelta(outcome, this.bet);
    if (this.root) {
      const msgs = {
        win: `<span class="win">Gewonnen · +${UI.fmt(this.bet)}</span>`,
        bust: `<span class="loss">Bust · über 21 · −${UI.fmt(this.bet)}</span>`,
        dealer: `<span class="loss">Dealer gewinnt · −${UI.fmt(this.bet)}</span>`,
        push: 'Push · Unentschieden',
      };
      qs('#bjStatus', this.root).innerHTML = msgs[outcome];
      if (outcome === 'bust') qsa('#playerCards .pcard', this.root).forEach((c) => c.classList.add('bust'));
      if (outcome === 'push') qsa('.hand-val', this.root).forEach((v) => v.classList.add('push'));
      qs('#bjActionControls', this.root).classList.add('hidden');
      qs('#bjBetControls', this.root).classList.remove('hidden');
    }
    this.inRound = false;
    await Bus.emit('blackjack:result', { outcome, bet: this.bet });
    await Game.settle(delta, { from: this.root ? qs('#playerCards', this.root) : null, game: 'blackjack' });
  },
};

UI.register('blackjack', {
  template: 'tpl-blackjack',
  mount(root) {
    Blackjack.root = root;
    Game.bindBet(root, 'bjBet');
    qs('#btnDeal', root).addEventListener('click', () => Blackjack.start());
    qs('#btnHit', root).addEventListener('click', () => Blackjack.hit());
    qs('#btnStand', root).addEventListener('click', () => Blackjack.stand());
  },
  unmount() { Blackjack.root = null; Blackjack.inRound = false; Blackjack.dealing = false; },
});
</script>
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-bj.png "?screen=blackjack"` → grüner Filztisch mit gerundeter Oberkante, Kartenschuh oben rechts, Bogentext, Chips.

Im Browser: Austeilen → vier Karten fliegen nacheinander vom Schuh, Dealer-Karte 1 zeigt Rückseite, Werte „?" und Summe. Hit → weitere Karte; bei > 21 rutschen die Karten rot glühend weg, Status „Bust". Stand → Rückseite flippt (3D), Dealer zieht bis ≥ 17, Ergebnis + Kontostand. Push färbt beide Werte gold. Neue Runde setzt Tisch zurück.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Blackjack am Filztisch mit Kartenflip

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: Roulette mit Setztisch, Kessel und Kugel

**Files:**
- Modify: `keller37.html` (Template `tpl-roulette`; CSS Sektion 6; neuer Block `<script id="game-roulette">`)

**Interfaces:**
- Consumes: `Rules.WHEEL/RED/isRed/rouletteRoll/rouletteLuckOverride/roulettePayout/luck`, `Game`, `SFX`, `UI`.
- Produces: Screen `roulette`; `Roulette.play(type, chosen, cellEl)`; Bus-Event `roulette:result {type, chosen, rolled, win, bet}`.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-roulette">
  <div class="panel roulette-panel felt">
    <div class="roulette-top">
      <div class="wheel-box">
        <canvas id="wheelCanvas" width="320" height="320"></canvas>
        <div class="ball" id="ball"></div>
        <div class="pointer">▼</div>
        <div class="result-num" id="resultNum"></div>
      </div>
      <div class="table-box">
        <div class="rtable" id="rtable"></div>
        <div class="bet-bar">
          <div class="bet-field"><button data-step="-5">−</button><input type="number" id="rouletteBet" value="10" min="1"><button data-step="5">+</button></div>
          <button class="chip" data-chip="10" data-v="10">10</button>
          <button class="chip" data-chip="25" data-v="25">25</button>
          <button class="chip" data-chip="50" data-v="50">50</button>
          <button class="chip" data-chip="max" data-v="max">MAX</button>
        </div>
        <div class="status" id="rouletteStatus">Chip auf ein Feld legen</div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Roulette -- */
.roulette-top { display: flex; gap: 24px; align-items: center; justify-content: center; flex-wrap: wrap; }
.wheel-box { position: relative; width: 320px; height: 320px; flex: 0 0 auto; }
#wheelCanvas { border-radius: 50%; transition: transform 4s cubic-bezier(0.12, 0.88, 0.22, 1); box-shadow: 0 10px 30px rgba(0,0,0,.8), 0 0 0 6px #2b1a0c, 0 0 0 9px #c9a227; }
.ball { position: absolute; left: 0; top: 0; width: 14px; height: 14px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #fff, #999); box-shadow: 0 2px 4px rgba(0,0,0,.8); z-index: 5; transform: translate(153px, 8px); pointer-events: none; }
.pointer { position: absolute; top: -18px; left: 50%; transform: translateX(-50%); color: var(--gold-2); font-size: 1.6rem; z-index: 7; filter: drop-shadow(0 2px 3px #000); }
.result-num { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%) scale(0); width: 74px; height: 74px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 2.3rem; color: #fff; border: 3px solid var(--gold-2); z-index: 6; transition: transform .35s cubic-bezier(.3,1.5,.5,1); box-shadow: 0 0 20px rgba(0,0,0,.8); }
.result-num.show { transform: translate(-50%, -50%) scale(1); }
.result-num.red { background: #b3261e; } .result-num.black { background: #111; } .result-num.green { background: #1f7a4d; }
.table-box { display: flex; flex-direction: column; gap: 12px; align-items: center; }
.rtable { display: grid; grid-template-columns: 34px repeat(12, 34px); grid-auto-rows: 34px; gap: 2px; padding: 8px; background: rgba(0,0,0,.25); border-radius: 8px; border: 1px solid rgba(232,198,90,.35); }
.rtable.locked .rcell { pointer-events: none; }
.rcell { position: relative; border: 1px solid rgba(255,255,255,.35); color: #fff; font-family: var(--font-mono); font-weight: 700; font-size: .85rem; background: #1c1c1c; transition: filter .1s; padding: 0; }
.rcell.red { background: #b3261e; }
.rcell.zero { grid-row: 1 / span 3; background: #1f7a4d; }
.rcell.out { grid-column: span 3; background: rgba(0,0,0,.35); font-family: var(--font-display); letter-spacing: .08em; font-size: 1rem; }
.rcell.out.red { background: #b3261e; }
.rcell.out.black { background: #111; }
.rcell:hover { filter: brightness(1.35); }
.chip.fly { position: fixed; z-index: 96; transition: transform .4s cubic-bezier(.3,.8,.4,1); pointer-events: none; }
.chip.placed { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%) scale(.68); pointer-events: none; animation: popIn .2s ease both; }
.chip.placed.won { animation: chipWin .5s ease both; }
.chip.placed.lost { animation: chipLost .5s ease both; }
```

Zu Sektion 7:

```css
@keyframes chipWin { 0% { transform: translate(-50%, -50%) scale(.68); } 50% { transform: translate(-50%, -50%) scale(1.1); } 100% { transform: translate(-50%, -250%) scale(.68); opacity: 0; } }
@keyframes chipLost { to { transform: translate(120px, -50%) scale(.5); opacity: 0; } }
```

- [ ] **Step 3: JS-Block** – nach `</script>` von `game-blackjack`:

```html
<script id="game-roulette">
/* ================= ROULETTE ================= */
const Roulette = {
  root: null, wheelDeg: 0, spinning: false, ballRaf: null,
  buildTable() {
    const t = qs('#rtable', this.root);
    t.innerHTML = '';
    const cell = (label, cls, type, chosen, style) =>
      h('button', { class: `rcell ${cls}`, style, onclick: (e) => this.play(type, chosen, e.currentTarget) }, label);
    t.append(cell('0', 'zero', 'number', 0));
    for (let row = 0; row < 3; row++) for (let col = 0; col < 12; col++) {
      const n = col * 3 + (3 - row);
      t.append(cell(String(n), Rules.isRed(n) ? 'red' : 'black', 'number', n));
    }
    t.append(cell('Rot', 'out red', 'red', null, 'grid-column: 2 / span 3'), cell('Schwarz', 'out black', 'black', null),
      cell('Gerade', 'out', 'even', null), cell('Ungerade', 'out', 'odd', null));
  },
  drawWheel(highlight = -1) {
    const c = qs('#wheelCanvas', this.root);
    if (!c) return;
    const ctx = c.getContext('2d');
    const cx = 160, cy = 160, r = 150, total = 37, slice = (2 * Math.PI) / total;
    ctx.clearRect(0, 0, 320, 320);
    ctx.beginPath(); ctx.arc(cx, cy, r + 8, 0, 2 * Math.PI); ctx.fillStyle = '#4a2c14'; ctx.fill();
    for (let i = 0; i < total; i++) {
      const center = -Math.PI / 2 + i * slice;
      const num = Rules.WHEEL[i];
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r, center - slice / 2, center + slice / 2); ctx.closePath();
      ctx.fillStyle = i === highlight ? '#e8c65a' : num === 0 ? '#1f7a4d' : Rules.isRed(num) ? '#b3261e' : '#1c1c1c';
      ctx.fill();
      ctx.strokeStyle = 'rgba(201,162,39,.5)'; ctx.lineWidth = 1; ctx.stroke();
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(center); ctx.translate(r - 16, 0); ctx.rotate(Math.PI / 2);
      ctx.fillStyle = i === highlight ? '#000' : '#fff'; ctx.font = 'bold 11px "Courier Prime", "Courier New", monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(num), 0, 0); ctx.restore();
    }
    ctx.beginPath(); ctx.arc(cx, cy, r - 32, 0, 2 * Math.PI); ctx.fillStyle = '#141712'; ctx.fill(); ctx.strokeStyle = '#c9a227'; ctx.lineWidth = 3; ctx.stroke();
    for (let k = 0; k < 8; k++) { ctx.save(); ctx.translate(cx, cy); ctx.rotate((k * Math.PI) / 4); ctx.fillStyle = '#c9a227'; ctx.fillRect(-2, -(r - 34), 4, r - 34 - 40); ctx.restore(); }
    ctx.beginPath(); ctx.arc(cx, cy, 40, 0, 2 * Math.PI); ctx.fillStyle = '#1b1f19'; ctx.fill(); ctx.strokeStyle = '#e8c65a'; ctx.lineWidth = 2; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, 14, 0, 2 * Math.PI); ctx.fillStyle = '#e8c65a'; ctx.fill();
  },
  flyChip(cell, label) {
    const from = qs('#balance').getBoundingClientRect();
    const to = cell.getBoundingClientRect();
    const c = h('div', { class: 'chip fly', style: `left:${from.left}px; top:${from.top}px` }, label);
    document.body.append(c);
    void c.offsetWidth;
    c.style.transform = `translate(${to.left + to.width / 2 - from.left - 23}px, ${to.top + to.height / 2 - from.top - 23}px)`;
    setTimeout(() => { c.remove(); cell.append(h('div', { class: 'chip placed' }, label)); }, 420);
  },
  animateBall(dur) {
    const ball = qs('#ball', this.root);
    if (!ball) return;
    if (this.ballRaf) cancelAnimationFrame(this.ballRaf);
    const start = performance.now(), R0 = 152, R1 = 134, turns = 4;
    let lastPocket = -1;
    const frame = (now) => {
      if (!this.root) return;
      const p = Math.min(1, (now - start) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      const angle = -90 - turns * 360 * e;           // endet bei −90° = oben, unter dem Zeiger
      let r = R0;
      if (p > 0.65) { const q = (p - 0.65) / 0.35; r = R1 + (R0 - R1) * (1 - q) * Math.abs(Math.cos(q * Math.PI * 3)); }
      const rad = (angle * Math.PI) / 180;
      ball.style.transform = `translate(${160 + r * Math.cos(rad) - 7}px, ${160 + r * Math.sin(rad) - 7}px)`;
      const pocket = Math.floor((((angle % 360) + 360) % 360) / (360 / 37));
      if (pocket !== lastPocket && p < 0.97) { lastPocket = pocket; SFX.play('ballTick'); }
      if (p < 1) this.ballRaf = requestAnimationFrame(frame); else this.ballRaf = null;
    };
    this.ballRaf = requestAnimationFrame(frame);
  },
  async play(type, chosen, cell) {
    if (this.spinning || !this.root) return;
    const bet = Game.readBet('rouletteBet');
    if (!Game.beginSpin(bet)) return;
    this.spinning = true;
    qs('#rtable', this.root).classList.add('locked');
    qsa('.chip.placed', this.root).forEach((c) => c.remove());
    this.flyChip(cell, String(bet));
    SFX.play('chip');
    qs('#rouletteStatus', this.root).textContent = 'Kugel rollt…';
    qs('#resultNum', this.root).className = 'result-num';
    let rolled = Rules.rouletteRoll(Math.random);
    rolled = Rules.rouletteLuckOverride(type, chosen, rolled, Rules.luck(State.s), Math.random);
    const targetIdx = Rules.WHEEL.indexOf(rolled);
    const sliceDeg = 360 / 37;
    const targetDeg = (360 - targetIdx * sliceDeg) % 360;
    const currentMod = this.wheelDeg % 360;
    let diff = targetDeg - currentMod;
    if (diff <= 0) diff += 360;
    this.wheelDeg += 5 * 360 + diff;
    this.drawWheel(-1);
    qs('#wheelCanvas', this.root).style.transform = `rotate(${this.wheelDeg}deg)`;
    this.animateBall(4000);
    await wait(4100);
    const delta = Rules.roulettePayout(type, chosen, rolled, bet);
    if (this.root) {
      this.drawWheel(targetIdx);
      const res = qs('#resultNum', this.root);
      res.textContent = rolled;
      res.className = `result-num show ${rolled === 0 ? 'green' : Rules.isRed(rolled) ? 'red' : 'black'}`;
      const colName = rolled === 0 ? '🟢 0' : Rules.isRed(rolled) ? `🔴 ${rolled}` : `⚫ ${rolled}`;
      qs('#rouletteStatus', this.root).innerHTML = delta > 0
        ? `<span class="win">${colName} · +${UI.fmt(delta)}</span>`
        : `<span class="loss">${colName} · Niete · −${UI.fmt(bet)}</span>`;
      qsa('.chip.placed', this.root).forEach((c) => c.classList.add(delta > 0 ? 'won' : 'lost'));
      qs('#rtable', this.root).classList.remove('locked');
    }
    await Bus.emit('roulette:result', { type, chosen, rolled, win: delta > 0, bet });
    await Game.settle(delta, { from: this.root ? qs('.wheel-box', this.root) : null, game: 'roulette' });
    this.spinning = false;
  },
};

UI.register('roulette', {
  template: 'tpl-roulette',
  mount(root) {
    Roulette.root = root;
    Roulette.buildTable();
    Roulette.drawWheel();
    qs('#wheelCanvas', root).style.transform = `rotate(${Roulette.wheelDeg}deg)`;
    Game.bindBet(root, 'rouletteBet');
  },
  unmount() { if (Roulette.ballRaf) cancelAnimationFrame(Roulette.ballRaf); Roulette.ballRaf = null; Roulette.root = null; },
});
</script>
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-roulette.png "?screen=roulette"` → Kessel links mit Holzrand, Goldspeichen, 37 Fächern und Zahlen; rechts Setztisch mit grüner 0, 12×3 Zahlen in Rot/Schwarz, darunter Rot/Schwarz/Gerade/Ungerade.

Im Browser: Klick auf „Rot" → Chip fliegt vom Wallet aufs Feld, Kessel dreht 4 s, Kugel läuft gegenläufig außen, wird langsamer, hüpft und landet oben unter dem Zeiger; Klackern wird langsamer. Ergebnis: Zielfach gold, Zahl groß in der Mitte, Chip verdoppelt sich nach oben (Gewinn) oder wird nach rechts weggezogen (Verlust). Klick auf eine Zahl → Zahlwette, bei Treffer +35× (Konsole: `State.s.brownieTimer=1; State.s.beers=3; State.s.beerTimer=2` und Zahl 17 setzen → mit 60 % Glück fällt oft die 17). Während der Drehung ist der Tisch gesperrt. Konsole ohne Fehler.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Roulette mit Setztisch, Kessel und laufender Kugel

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 15: Pferderennen mit Bahn, Staub und Kommentar

**Files:**
- Modify: `keller37.html` (Template `tpl-horses`; CSS Sektion 6 + Keyframes; neuer Block `<script id="game-horses">`)

**Interfaces:**
- Consumes: `Rules.HORSES/horseStep/horseDelta/luck`, `Game`, `SFX`, `UI`, `State.s.selectedHorse`.
- Produces: Screen `horses`; `Horses.start()`, `Horses.pick(id)`; Bus-Event `horses:result {winner, selected, bet}`.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-horses">
  <div class="panel horses-panel">
    <div class="commentary" id="commentary">Wähle dein Pferd und setz.</div>
    <div class="track" id="track"><div class="finish"></div><div class="photo-flash" id="photoFlash"></div></div>
    <div class="horse-picks" id="horsePicks"></div>
    <div class="status" id="horseStatus"></div>
    <div class="bet-bar">
      <div class="bet-field"><button data-step="-5">−</button><input type="number" id="horseBet" value="10" min="1"><button data-step="5">+</button></div>
      <button class="chip" data-chip="10" data-v="10">10</button>
      <button class="chip" data-chip="25" data-v="25">25</button>
      <button class="chip" data-chip="50" data-v="50">50</button>
      <button class="chip" data-chip="max" data-v="max">MAX</button>
      <button class="btn green" id="btnRace">Start</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Pferderennen -- */
.commentary { font-family: var(--font-display); letter-spacing: .1em; font-size: 1.3rem; color: var(--neon-green); text-shadow: 0 0 10px rgba(61,220,132,.5); min-height: 1.6em; text-align: center; }
.track { position: relative; width: 100%; background: linear-gradient(180deg, #3d2a17, #2a1c0f); border-top: 6px solid #8a6d1a; border-bottom: 6px solid #8a6d1a; border-radius: 6px; padding: 6px 0; overflow: hidden; }
.track .finish { position: absolute; right: 56px; top: 0; bottom: 0; width: 10px; background: repeating-linear-gradient(0deg, #fff 0 8px, #111 8px 16px); opacity: .8; }
.lane { position: relative; height: 54px; border-bottom: 1px dashed rgba(255,255,255,.15); }
.lane:last-child { border-bottom: 0; }
.gate { position: absolute; left: 0; top: 0; bottom: 0; width: 8px; background: #555; }
.runner { position: absolute; left: 10px; top: 4px; display: flex; align-items: center; gap: 4px; will-change: transform; }
.runner .horse { font-size: 2rem; display: inline-block; filter: drop-shadow(0 3px 3px rgba(0,0,0,.6)); }
.runner.running .horse { animation: gallop .2s ease-in-out infinite; }
.runner .tag { font-family: var(--font-display); letter-spacing: .08em; font-size: .85rem; padding: 1px 6px; border-radius: 3px; color: #111; background: var(--hc, #fff); }
.dust { position: absolute; width: 8px; height: 8px; border-radius: 50%; background: rgba(200,170,120,.6); pointer-events: none; animation: dust .6s ease-out both; }
.photo-flash { position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; }
.photo-flash.on { animation: flash .15s ease both; }
.horse-picks { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
.pick { --hc: #fff; width: 120px; padding: 8px; border-radius: 8px; border: 2px solid var(--hc); background: rgba(0,0,0,.35); color: var(--text); font-family: var(--font-display); letter-spacing: .08em; font-size: 1.1rem;
  display: flex; flex-direction: column; align-items: center; gap: 2px; transition: transform .15s, background .15s; transform-style: preserve-3d; }
.pick small { font-family: var(--font-mono); font-size: .75rem; color: var(--dim); letter-spacing: 0; }
.pick:hover { transform: translateY(-2px); }
.pick.on { background: var(--hc); color: #111; transform: rotateX(8deg) translateY(-3px); box-shadow: 0 0 16px var(--hc); }
.pick.on small { color: #222; }
```

Zu Sektion 7:

```css
@keyframes gallop { 0%, 100% { transform: translateY(0) rotate(-3deg); } 50% { transform: translateY(-5px) rotate(3deg); } }
@keyframes dust { from { transform: translate(0, 0) scale(1); opacity: .8; } to { transform: translate(-30px, -6px) scale(2.2); opacity: 0; } }
```

- [ ] **Step 3: JS-Block** – nach `</script>` von `game-roulette`:

```html
<script id="game-horses">
/* ================= PFERDERENNEN ================= */
const Horses = {
  root: null, racing: false, loop: null, commentTimer: null,
  build() {
    const track = qs('#track', this.root);
    qsa('.lane', track).forEach((l) => l.remove());
    const picks = qs('#horsePicks', this.root);
    picks.innerHTML = '';
    for (const hrs of Rules.HORSES) {
      track.append(h('div', { class: 'lane' }, h('div', { class: 'gate' }),
        h('div', { class: 'runner', id: `h-${hrs.id}`, style: `--hc: ${hrs.col}` }, h('span', { class: 'horse' }, '🏇'), h('span', { class: 'tag' }, hrs.name))));
      picks.append(h('button', { class: 'pick' + (hrs.id === State.s.selectedHorse ? ' on' : ''), id: `pick-${hrs.id}`, style: `--hc: ${hrs.col}`, onclick: () => this.pick(hrs.id) },
        `${hrs.dot} ${hrs.name}`, h('small', {}, 'Quote 4.0')));
    }
  },
  pick(id) {
    if (this.racing) return;
    State.s.selectedHorse = id;
    State.save();
    qsa('.pick', this.root).forEach((p) => p.classList.toggle('on', p.id === `pick-${id}`));
    SFX.play('click');
  },
  comment(pos) {
    if (!this.root) return;
    const order = Rules.HORSES.map((hrs, i) => ({ hrs, p: pos[i] })).sort((a, b) => b.p - a.p);
    const lead = order[0], second = order[1], last = order[3];
    const gap = lead.p - second.p;
    const mine = lead.hrs.id === State.s.selectedHorse;
    const lines = gap < 10 ? [`Kopf an Kopf – ${lead.hrs.name} und ${second.hrs.name}!`, 'Das wird eng!']
      : gap > 40 ? [`${lead.hrs.name} zieht davon!`, `${lead.hrs.name} führt klar, ${last.hrs.name} hängt hinten.`]
        : [`${lead.hrs.name} vorn, ${second.hrs.name} dran.`, `${second.hrs.name} holt auf!`];
    if (mine) lines.push('Dein Pferd liegt vorn!');
    qs('#commentary', this.root).textContent = pick(lines);
  },
  dust(runner) {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const lane = runner.parentElement;
    const d = h('span', { class: 'dust', style: `left:${runner.offsetLeft + 4}px; top:${runner.offsetTop + 34}px` });
    lane.append(d);
    setTimeout(() => d.remove(), 650);
  },
  async start() {
    if (this.racing || !this.root) return;
    const bet = Game.readBet('horseBet');
    if (!Game.beginSpin(bet)) return;
    this.racing = true;
    qs('#btnRace', this.root).disabled = true;
    qs('#horseStatus', this.root).textContent = '';
    const track = qs('#track', this.root);
    const goal = track.clientWidth - 65;
    const pos = [0, 0, 0, 0];
    const luck = Rules.luck(State.s);
    const selected = State.s.selectedHorse;
    const runners = Rules.HORSES.map((hrs) => qs(`#h-${hrs.id}`, this.root));
    runners.forEach((r) => { r.style.transform = 'translateX(0)'; r.classList.add('running'); });
    SFX.play('whinny');
    SFX.loop('gallop', 260);
    this.commentTimer = setInterval(() => this.comment(pos), 600);
    let tick = 0;
    const winner = await new Promise((resolve) => {
      this.loop = setInterval(() => {
        if (!this.root) { clearInterval(this.loop); resolve(null); return; }
        let win = null;
        Rules.HORSES.forEach((hrs, i) => {
          pos[i] += Rules.horseStep(hrs.id === selected, luck, Math.random);
          runners[i].style.transform = `translateX(${pos[i]}px)`;
          if (tick % 4 === i) this.dust(runners[i]);
          if (pos[i] >= goal && !win) win = hrs;
        });
        tick++;
        if (win) { clearInterval(this.loop); resolve(win); }
      }, 30);
    });
    clearInterval(this.commentTimer);
    SFX.stop('gallop');
    if (!winner) { this.racing = false; return; }
    const won = winner.id === selected;
    const delta = Rules.horseDelta(won, bet);
    if (this.root) {
      const flash = qs('#photoFlash', this.root);
      flash.classList.remove('on'); void flash.offsetWidth; flash.classList.add('on');
      runners.forEach((r) => r.classList.remove('running'));
      const wr = qs(`#h-${winner.id}`, this.root);
      wr.classList.add('running');
      wr.style.transition = 'transform .7s ease-in';
      wr.style.transform = `translateX(${track.clientWidth + 40}px)`;
      setTimeout(() => { if (wr.isConnected) { wr.style.transition = ''; wr.classList.remove('running'); } }, 800);
      qs('#commentary', this.root).textContent = `${winner.name} gewinnt!`;
      qs('#horseStatus', this.root).innerHTML = won
        ? `<span class="win">${winner.name} siegt · +${UI.fmt(bet * 3)}</span>`
        : `<span class="loss">${winner.name} siegt · −${UI.fmt(bet)}</span>`;
      qs('#btnRace', this.root).disabled = false;
    }
    this.racing = false;
    await Bus.emit('horses:result', { winner: winner.id, selected, bet });
    await Game.settle(delta, { from: this.root ? qs('#track', this.root) : null, game: 'horses' });
  },
};

UI.register('horses', {
  template: 'tpl-horses',
  mount(root) {
    Horses.root = root;
    Horses.build();
    Game.bindBet(root, 'horseBet');
    qs('#btnRace', root).addEventListener('click', () => Horses.start());
  },
  unmount() { clearInterval(Horses.loop); clearInterval(Horses.commentTimer); SFX.stop('gallop'); Horses.root = null; Horses.racing = false; },
});
</script>
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-horses.png "?screen=horses"` → braune Bahn mit 4 Spuren, Startboxen links, Zielstreifen rechts, Pferde mit farbigen Namensschildern, 4 Setzkarten darunter (eine aktiv).

Im Browser: Karte „Phantom" klicken → Karte kippt und leuchtet lila; Start → Pferde bobben, Staub hinter ihnen, Kommentarzeile wechselt alle 0,6 s, Galopp-Sound; Ziel: weißer Blitz, Sieger läuft aus dem Bild, Ergebnis + Kontostand (+3× Einsatz bei Sieg). Mid-Race Neonschild klicken → keine Fehler, Geld wird nicht verbucht (Rennen abgebrochen, Einsatz bereits geprüft, aber nicht abgezogen – wie im Original, wo nur Zinsen/Meds vorab fällig sind).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Pferderennen mit Bahn, Staub und Kommentar

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 16: Russisches Roulette mit Trommel

**Files:**
- Modify: `keller37.html` (Template `tpl-russian`; CSS Sektion 6; neuer Block `<script id="game-russian">`; Szenen `igor.first`, `rr.headshot`)

**Interfaces:**
- Consumes: `Rules.rrCylinder/rrDelta`, `Game`, `SFX`, `UI`, `Cutscene`, `State.s.flags.igor`.
- Produces: Screen `russian`; `Russian.start()`, `Russian.pull()`; Bus-Event `rr:result {victim: 'player'|'igor', bet}`.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-russian">
  <div class="panel rr-panel">
    <div class="rr-flash" id="rrFlash"></div>
    <div class="duel">
      <div class="fighter" id="fPlayer"><div class="face">🤠</div><div class="fname">Du</div></div>
      <div class="cylinder-box">
        <svg id="cylinder" viewBox="0 0 200 200" width="200" height="200" aria-hidden="true"></svg>
        <div class="chambers-left" id="chambersLeft">6 Kammern</div>
      </div>
      <div class="fighter" id="fIgor"><div class="face">🐻</div><div class="fname">Igor</div></div>
    </div>
    <div class="status" id="rrStatus">Duell gegen Igor. Streifschuss = 100 € Spital.</div>
    <div class="bet-bar" id="rrBetControls">
      <div class="bet-field"><button data-step="-5">−</button><input type="number" id="rrBet" value="10" min="1"><button data-step="5">+</button></div>
      <button class="chip" data-chip="10" data-v="10">10</button>
      <button class="chip" data-chip="25" data-v="25">25</button>
      <button class="chip" data-chip="max" data-v="max">MAX</button>
      <button class="btn blue" id="btnDuel">Duell starten</button>
    </div>
    <div class="bet-bar hidden" id="rrActionControls">
      <button class="btn red" id="btnTrigger">💥 Abzug drücken</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Russisches Roulette -- */
.rr-panel { position: relative; background: radial-gradient(circle at 50% 0%, #1b2430, #0b0f14 70%); border-color: rgba(76,201,240,.25); overflow: hidden; }
.rr-flash { position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; z-index: 5; }
.rr-flash.on { animation: flash .12s ease both; }
.duel { display: flex; align-items: center; justify-content: space-around; width: 100%; gap: 16px; }
.fighter { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.fighter .face { width: 120px; height: 120px; border-radius: 50%; border: 4px solid rgba(76,201,240,.5); background: radial-gradient(circle at 40% 35%, #2a3440, #0d1117); display: flex; align-items: center; justify-content: center; font-size: 4rem; transition: transform .2s, filter .3s; }
.fighter.turn .face { border-color: var(--neon-blue); box-shadow: 0 0 22px rgba(76,201,240,.6); transform: scale(1.06); }
.fighter.dead .face { filter: grayscale(1) brightness(.6); transform: rotate(14deg); border-color: var(--neon-red); }
.fighter .fname { font-family: var(--font-display); letter-spacing: .12em; font-size: 1.2rem; color: var(--neon-blue); }
.cylinder-box { display: flex; flex-direction: column; align-items: center; gap: 6px; }
#cylinder { transition: transform .25s cubic-bezier(.3,1.3,.5,1); filter: drop-shadow(0 6px 10px rgba(0,0,0,.8)); }
.cylinder-box.zoom { animation: cylZoom .3s ease both; }
.chambers-left { font-family: var(--font-mono); font-size: .85rem; color: var(--dim); }
```

Zu Sektion 7: `@keyframes cylZoom { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.12); } }`

- [ ] **Step 3: JS-Block** – nach `</script>` von `game-horses`:

```html
<script id="game-russian">
/* ================= RUSSISCHES ROULETTE ================= */
const Russian = {
  root: null, cylinder: [], idx: 0, bet: 0, inDuel: false, busy: false,
  drawCylinder() {
    const svg = qs('#cylinder', this.root);
    const ns = 'http://www.w3.org/2000/svg';
    svg.innerHTML = '';
    const el = (tag, attrs) => { const e = document.createElementNS(ns, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); return e; };
    svg.append(el('circle', { cx: 100, cy: 100, r: 92, fill: '#2a2f36', stroke: '#8a94a0', 'stroke-width': 4 }));
    for (let i = 0; i < 6; i++) {
      const a = (-90 + i * 60) * Math.PI / 180;
      const c = el('circle', { cx: 100 + 56 * Math.cos(a), cy: 100 + 56 * Math.sin(a), r: 19, fill: '#0b0d10', stroke: '#8a94a0', 'stroke-width': 3, class: 'chamber', 'data-i': i });
      svg.append(c);
    }
    svg.append(el('circle', { cx: 100, cy: 100, r: 14, fill: '#8a94a0' }));
    svg.append(el('polygon', { points: '100,4 92,16 108,16', fill: '#e8c65a' }));
  },
  rotateTo(idx) {
    const svg = qs('#cylinder', this.root);
    if (!svg) return;
    svg.style.transform = `rotate(${-60 * idx}deg)`;
    const box = svg.parentElement;
    box.classList.remove('zoom'); void box.offsetWidth; box.classList.add('zoom');
    qs('#chambersLeft', this.root).textContent = `${6 - idx} Kammer${6 - idx === 1 ? '' : 'n'}`;
  },
  markSpent(idx) {
    const c = qs(`.chamber[data-i="${idx}"]`, this.root);
    if (c) { c.setAttribute('fill', '#3a3f46'); c.setAttribute('stroke', '#555'); }
  },
  setTurn(who) {
    if (!this.root) return;
    qs('#fPlayer', this.root).classList.toggle('turn', who === 'player');
    qs('#fIgor', this.root).classList.toggle('turn', who === 'igor');
  },
  heartbeat() { SFX.loop('heartbeat', Math.max(380, 900 - this.idx * 110)); },
  async start() {
    if (this.inDuel || !this.root) return;
    const bet = Game.readBet('rrBet');
    if (!Game.beginSpin(bet)) return;
    this.inDuel = true; this.bet = bet;
    this.cylinder = Rules.rrCylinder(Math.random);
    this.idx = 0;
    qs('#fPlayer', this.root).classList.remove('dead'); qs('#fIgor', this.root).classList.remove('dead');
    this.drawCylinder();
    qs('#cylinder', this.root).style.transform = 'rotate(0deg)';
    qs('#chambersLeft', this.root).textContent = '6 Kammern';
    qs('#rrBetControls', this.root).classList.add('hidden');
    qs('#rrActionControls', this.root).classList.remove('hidden');
    if (!State.s.flags.igor) { State.s.flags.igor = true; State.save(); await Cutscene.play('igor.first', {}); }
    if (!this.root) { this.inDuel = false; return; }
    qs('#rrStatus', this.root).textContent = 'Du bist dran. Drück ab.';
    this.setTurn('player');
    this.heartbeat();
  },
  async bang(who) {
    if (!this.root) return;
    const flash = qs('#rrFlash', this.root);
    flash.classList.remove('on'); void flash.offsetWidth; flash.classList.add('on');
    SFX.stopAll(); SFX.play('gunshot');
    UI.shake(qs('#shell'));
    qs(who === 'player' ? '#fPlayer' : '#fIgor', this.root).classList.add('dead');
    qs(who === 'player' ? '#fPlayer .face' : '#fIgor .face', this.root).textContent = '💀';
    await wait(600);
  },
  async pull() {
    if (!this.inDuel || this.busy || !this.root) return;
    this.busy = true;
    const btn = qs('#btnTrigger', this.root);
    btn.disabled = true;
    this.rotateTo(this.idx);
    await wait(350);
    if (this.cylinder[this.idx]) {
      await this.bang('player');
      if (this.root) qs('#rrStatus', this.root).innerHTML = `<span class="loss">PÄNG · Streifschuss · −${UI.fmt(this.bet)} & 100 € Spital</span>`;
      await this.end('player');
      return;
    }
    SFX.play('dryfire');
    this.markSpent(this.idx);
    this.idx++;
    qs('#rrStatus', this.root).textContent = '*Klick*… Leer. Igor ist dran…';
    this.setTurn('igor');
    this.heartbeat();
    await wait(1100);
    if (!this.root) { this.busy = false; return; }
    this.rotateTo(this.idx);
    await wait(350);
    if (this.cylinder[this.idx]) {
      await this.bang('igor');
      if (this.root) qs('#rrStatus', this.root).innerHTML = `<span class="win">PÄNG · Igor liegt · +${UI.fmt(this.bet)}</span>`;
      await this.end('igor');
      return;
    }
    SFX.play('dryfire');
    this.markSpent(this.idx);
    this.idx++;
    qs('#rrStatus', this.root).textContent = '*Klick*… Igor lebt. Du bist dran.';
    this.setTurn('player');
    this.heartbeat();
    btn.disabled = false;
    this.busy = false;
  },
  async end(victim) {
    SFX.stopAll();
    this.inDuel = false; this.busy = false;
    const delta = Rules.rrDelta(victim, this.bet);
    if (this.root) {
      this.setTurn(null);
      qs('#rrActionControls', this.root).classList.add('hidden');
      qs('#rrBetControls', this.root).classList.remove('hidden');
      qs('#btnTrigger', this.root).disabled = false;
    }
    await Bus.emit('rr:result', { victim, bet: this.bet });
    if (victim === 'player') await Cutscene.play('rr.headshot', {});
    await Game.settle(delta, { from: this.root ? qs('.duel', this.root) : null, game: 'russian' });
  },
};

UI.register('russian', {
  template: 'tpl-russian',
  mount(root) {
    Russian.root = root;
    Russian.drawCylinder();
    Game.bindBet(root, 'rrBet');
    qs('#btnDuel', root).addEventListener('click', () => Russian.start());
    qs('#btnTrigger', root).addEventListener('click', () => Russian.pull());
  },
  unmount() { SFX.stop('heartbeat'); Russian.root = null; Russian.inDuel = false; Russian.busy = false; },
});

Cutscene.define('igor.first', [
  { bg: 'keller', who: 'igor', mood: 'calm', text: '…' },
  { bg: 'keller', who: 'igor', mood: 'calm', text: 'Eine Kugel. Sechs Kammern. Du zuerst. Ich habe Zeit.' },
]);
Cutscene.define('rr.headshot', [
  { bg: 'klinik', who: 'doc', mood: 'shock', fx: 'flash', text: 'Streifschuss! Du Glückspilz. Hundert Euro fürs Pflaster – und für meine Nerven.' },
]);
</script>
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-rr.png "?screen=russian"` → dunkelblauer Raum, links 🤠, rechts 🐻, Mitte SVG-Trommel mit 6 Kammern und goldenem Zeiger, „6 Kammern".

Im Browser: Duell starten → beim ersten Mal Igor-Szene im Keller; danach Herzschlag, Spieler-Portrait leuchtet. Abzug → Trommel dreht 60° mit Zoom, *Klick* oder Schuss; leere Kammern werden grau, Zähler sinkt, Herzschlag wird schneller. Schuss beim Spieler: Blitz, Shake, 💀, Doc-Szene, −(Einsatz+100). Schuss bei Igor: Igor 💀, +Einsatz. Danach Bet-Controls wieder sichtbar; erneutes Duell setzt Portraits zurück. Herzschlag stoppt beim Verlassen des Screens.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Russisches Roulette mit Trommel, Herzschlag und Igor-Szene

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 17: Post austragen (Tageslicht-Screen)

**Files:**
- Modify: `keller37.html` (Template `tpl-postman`; CSS Sektion 6 + Keyframes; neuer Block `<script id="game-postman">`)

**Interfaces:**
- Consumes: `Rules.POST_HOUSES/postmanTier/POST_PENALTY`, `Game.applyDelta`, `SFX`, `UI`, `State.s.stats.postStreakBest`.
- Produces: Screen `postman`; `Postman.startShift()`, `Postman.deliver(n)`; Bus-Event `post:streak {streak}`. Post ist **kein** Spin (kein `afterSpin`).

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-postman">
  <div class="panel postman-panel">
    <div class="street" id="street">
      <div class="sun"></div>
      <div class="houses" id="houses"></div>
      <div class="road"></div>
      <div class="fuse-wrap hidden" id="fuseWrap"><div class="fuse" id="fuse"></div><div class="spark" id="spark">✨</div></div>
      <div class="letter paper hidden" id="letter"></div>
      <div class="streak" id="streak"></div>
      <div class="stamp hidden" id="stamp">TEMPO!</div>
    </div>
    <div class="status" id="jobStatus">Schicht beginnen. Falscher Kasten oder zu langsam: 25 € Strafe.</div>
    <div class="bet-bar"><button class="btn solid" id="btnShift">Schicht beginnen</button></div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Post austragen -- */
.postman-panel { background: linear-gradient(180deg, #8fc3f0 0%, #dbe7ef 60%, #6b6a55 60%, #4e4c3c 100%); border-color: #8a8060; color: #222; }
.postman-panel .status { color: #2a2418; }
.postman-panel .status .win { color: #2f7a1f; text-shadow: none; }
.postman-panel .status .loss { color: #b3261e; text-shadow: none; }
.street { position: relative; width: 100%; min-height: 260px; }
.sun { position: absolute; right: 30px; top: 10px; width: 60px; height: 60px; border-radius: 50%; background: radial-gradient(circle, #fff4b0, #f5d67a 60%, transparent 62%); filter: blur(1px); }
.houses { position: absolute; left: 0; right: 0; bottom: 70px; display: flex; justify-content: space-around; align-items: flex-end; padding: 0 20px; }
.house { --hc: #999; position: relative; width: 110px; background: none; border: 0; padding: 0; cursor: pointer; display: flex; flex-direction: column; align-items: center; transition: transform .12s; }
.house:hover { transform: translateY(-4px); }
.house .roof { width: 0; height: 0; border-left: 55px solid transparent; border-right: 55px solid transparent; border-bottom: 34px solid #5a3a2a; }
.house .wall { width: 96px; height: 70px; background: var(--hc); border: 2px solid rgba(0,0,0,.25); display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-size: 1.6rem; color: #fff; text-shadow: 0 1px 2px #000; }
.house .mailbox { position: relative; margin-top: 6px; font-size: 1.8rem; }
.house .flag { position: absolute; right: -6px; top: 4px; width: 4px; height: 16px; background: #c1121f; transform-origin: bottom; transform: rotate(90deg); transition: transform .25s; }
.house.delivered .flag { transform: rotate(0deg); }
.house .dog { position: absolute; left: 50%; bottom: 40px; font-size: 2.2rem; transform: translateX(-50%); animation: dogJump .6s ease both; }
.road { position: absolute; left: 0; right: 0; bottom: 0; height: 60px; background: #4e4c3c; border-top: 4px dashed #ddd; }
.fuse-wrap { position: absolute; left: 20px; right: 20px; top: 14px; height: 10px; }
.fuse { height: 6px; margin-top: 2px; background: linear-gradient(90deg, #333, #666); border-radius: 3px; width: 100%; transition: width .05s linear; box-shadow: 0 0 6px rgba(255,120,0,.6); }
.spark { position: absolute; top: -10px; margin-left: -10px; font-size: 1.2rem; filter: drop-shadow(0 0 6px orange); animation: sparkle .3s infinite alternate; }
.letter { position: absolute; left: 20px; top: 34px; font-size: 1rem; }
.letter b { font-family: var(--font-display); font-size: 1.4rem; letter-spacing: .08em; }
.streak { position: absolute; right: 20px; top: 40px; font-family: var(--font-display); font-size: 2.4rem; color: #2a2418; letter-spacing: .1em; }
.streak span { font-size: 1rem; color: #555; }
.stamp { position: absolute; left: 50%; top: 40%; transform: translate(-50%, -50%) rotate(-12deg); font-family: var(--font-display); font-size: 3.5rem; color: #b3261e; border: 6px solid #b3261e; padding: 4px 18px; letter-spacing: .2em; animation: stampIn .4s cubic-bezier(.3,1.6,.5,1) both; pointer-events: none; z-index: 5; }
.envelope { position: absolute; font-size: 1.6rem; pointer-events: none; transition: transform .35s ease-in, opacity .35s; z-index: 4; }
```

Zu Sektion 7:

```css
@keyframes sparkle { from { transform: scale(.8) rotate(0); } to { transform: scale(1.2) rotate(30deg); } }
@keyframes stampIn { from { transform: translate(-50%, -50%) rotate(-12deg) scale(3); opacity: 0; } to { transform: translate(-50%, -50%) rotate(-12deg) scale(1); opacity: 1; } }
@keyframes dogJump { 0% { transform: translateX(-50%) translateY(30px); opacity: 0; } 40% { transform: translateX(-50%) translateY(-20px); opacity: 1; } 100% { transform: translateX(-50%) translateY(0); opacity: 1; } }
```

- [ ] **Step 3: JS-Block** – nach `</script>` von `game-russian`:

```html
<script id="game-postman">
/* ================= POST AUSTRAGEN ================= */
const Postman = {
  root: null, streak: 0, timer: null, timeLeft: 0, target: null, tier: null, active: false,
  renderHouses() {
    const box = qs('#houses', this.root);
    box.innerHTML = '';
    for (const hs of [...Rules.POST_HOUSES].sort(() => Math.random() - 0.5)) {
      box.append(h('button', { class: 'house', 'data-n': hs.n, style: `--hc: ${hs.c}`, onclick: () => this.deliver(hs.n) },
        h('div', { class: 'roof' }), h('div', { class: 'wall' }, `#${hs.n}`), h('div', { class: 'mailbox' }, '📫', h('div', { class: 'flag' }))));
    }
  },
  startShift() {
    if (this.active || !this.root) return;
    this.active = true; this.streak = 0;
    qs('#btnShift', this.root).classList.add('hidden');
    qs('#fuseWrap', this.root).classList.remove('hidden');
    qs('#letter', this.root).classList.remove('hidden');
    qs('#jobStatus', this.root).textContent = '';
    this.nextStep();
  },
  nextStep() {
    clearInterval(this.timer);
    if (!this.root) return;
    const prevTier = this.tier;
    this.tier = Rules.postmanTier(this.streak);
    if (prevTier && prevTier.t !== this.tier.t) this.stamp();
    this.timeLeft = this.tier.t;
    this.target = pick(Rules.POST_HOUSES);
    qs('#letter', this.root).innerHTML = `An: <b style="color:${this.target.c}">Haus #${this.target.n}</b><br>${this.tier.r} € Lohn`;
    qs('#streak', this.root).innerHTML = `${this.streak}<span> in Folge</span>`;
    this.renderHouses();
    const fuse = qs('#fuse', this.root), spark = qs('#spark', this.root);
    fuse.style.width = '100%'; spark.style.left = '100%';
    this.timer = setInterval(() => {
      this.timeLeft -= 0.05;
      const pct = Math.max(0, (this.timeLeft / this.tier.t) * 100);
      fuse.style.width = pct + '%'; spark.style.left = pct + '%';
      if (this.timeLeft <= 0) { clearInterval(this.timer); this.fail('Zu langsam!'); }
    }, 50);
  },
  stamp() {
    const st = qs('#stamp', this.root);
    st.classList.remove('hidden'); st.style.animation = 'none'; void st.offsetWidth; st.style.animation = '';
    SFX.play('stamp');
    setTimeout(() => st.classList.add('hidden'), 900);
  },
  async deliver(n) {
    if (!this.active || !this.root) return;
    clearInterval(this.timer);
    const house = qs(`.house[data-n="${n}"]`, this.root);
    if (n === this.target.n) {
      const reward = this.tier.r;
      house.classList.add('delivered');
      const from = qs('#letter', this.root).getBoundingClientRect(), to = qs('.mailbox', house).getBoundingClientRect(), st = qs('#street', this.root).getBoundingClientRect();
      const env = h('span', { class: 'envelope', style: `left:${from.left - st.left}px; top:${from.top - st.top}px` }, '✉️');
      qs('#street', this.root).append(env);
      void env.offsetWidth;
      env.style.transform = `translate(${to.left - from.left}px, ${to.top - from.top}px) scale(.5)`; env.style.opacity = '0';
      setTimeout(() => env.remove(), 400);
      SFX.play('coin');
      Game.applyDelta(reward, { from: house });
      this.streak++;
      if (this.streak > State.s.stats.postStreakBest) { State.s.stats.postStreakBest = this.streak; State.save(); }
      qs('#jobStatus', this.root).innerHTML = `<span class="win">+${UI.fmt(reward)}</span>`;
      await Bus.emit('post:streak', { streak: this.streak });
      await wait(250);
      this.nextStep();
    } else {
      this.fail('Falscher Kasten!', house);
    }
  },
  fail(msg, house) {
    clearInterval(this.timer);
    this.active = false;
    if (!this.root) return;
    const target = house || qs(`.house[data-n="${this.target.n}"]`, this.root);
    if (target) { target.append(h('span', { class: 'dog' }, '🐕')); }
    SFX.play('dog');
    UI.shake(qs('#street', this.root));
    Game.applyDelta(-Rules.POST_PENALTY, { from: target });
    qs('#fuseWrap', this.root).classList.add('hidden');
    qs('#letter', this.root).classList.add('hidden');
    qs('#jobStatus', this.root).innerHTML = `<span class="loss">${msg} 25 € Strafe. Schicht beendet nach ${this.streak} Briefen.</span>`;
    qs('#btnShift', this.root).classList.remove('hidden');
    this.tier = null;
  },
};

UI.register('postman', {
  template: 'tpl-postman',
  mount(root) {
    Postman.root = root;
    Postman.streak = 0; Postman.active = false; Postman.tier = null;
    Postman.renderHouses();
    qs('#btnShift', root).addEventListener('click', () => Postman.startShift());
  },
  unmount() { clearInterval(Postman.timer); Postman.root = null; Postman.active = false; },
});
</script>
```

- [ ] **Step 4: Prüfen**

Run: `tests/screenshot.sh /tmp/k37-post.png "?screen=postman"` → heller Screen mit Himmel, Sonne, vier bunten Häusern mit Briefkästen, Straße unten.

Im Browser: Schicht beginnen → Brief oben links „An: Haus #45", Lunte oben brennt von rechts nach links mit Funken, Streak-Zähler rechts. Richtiges Haus → ✉️ fliegt in den Kasten, Fahne geht hoch, +5 €, nächster Brief; Häuser werden neu gemischt. Nach dem 2. Brief Stempel „TEMPO!" und kürzere Lunte (3 s). Falsches Haus → 🐕 springt heraus, Shake, −25 €, Schicht beendet. Zu langsam → gleicher Ablauf mit „Zu langsam!". Screen mitten in der Schicht verlassen → Lunte stoppt (keine Strafe, kein weiterer Tick; Konsole prüfen: `Postman.timer` läuft nicht weiter, kein Fehler).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat: Post austragen mit Straße, Lunte, Streak-Stempel und Hund

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 18: Achievements & Trophäenwand

**Files:**
- Modify: `keller37.html` (CSS Sektion 6; neuer Block `<script id="achievements">` nach `game-postman`)

**Interfaces:**
- Consumes: `State.meta.achievements`, `State.saveMeta`, `Bus`-Events `win`, `spin:before`, `slots:result`, `roulette:result`, `rr:result`, `beer`, `kidney.sold`, `house.bought`, `divorce`, `mafia.repaid`, `post:streak`, `gameover:restart`; `#trophyGrid` aus Task 11.
- Produces: `Achievements.DEFS`, `Achievements.has(id)`, `Achievements.unlock(id)`, `Achievements.renderWall(gridEl)`; Bus-Event `achievement:unlock {id}`.

- [ ] **Step 1: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Trophäen -- */
.trophy { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border: 1px dashed #4a3a2a; border-radius: 4px; font-family: var(--font-mono); font-size: .8rem; opacity: .35; filter: grayscale(1); }
.trophy.on { opacity: 1; filter: none; border-style: solid; border-color: var(--gold); box-shadow: inset 0 0 12px rgba(201,162,39,.2); }
.trophy .t-ic { font-size: 1.3rem; }
.trophy.fresh { animation: popIn .4s cubic-bezier(.3,1.5,.5,1) both; }
```

- [ ] **Step 2: JS-Block** – nach `</script>` von `game-postman`:

```html
<script id="achievements">
/* ================= ACHIEVEMENTS ================= */
const Achievements = {
  DEFS: [
    { id: 'firstWin', title: 'Erster Gewinn', icon: '🎉', desc: 'Zum ersten Mal gewonnen.' },
    { id: 'highRoller', title: 'Hoch gepokert', icon: '💸', desc: 'Einsatz von mindestens 500 €.' },
    { id: 'jackpot', title: 'Jackpot', icon: '7️⃣', desc: '7-7-7 an den Slots.' },
    { id: 'plein', title: 'Plein', icon: '🎯', desc: 'Roulette-Zahl getroffen.' },
    { id: 'igor', title: 'Igor besiegt', icon: '🐻', desc: 'Das Duell überlebt – Igor nicht.' },
    { id: 'regular', title: 'Stammgast', icon: '🍺', desc: 'Drei Bier gleichzeitig.' },
    { id: 'donor', title: 'Organspender', icon: '🫁', desc: 'Niere verkauft.' },
    { id: 'owner', title: 'Hausbesitzer', icon: '🏰', desc: 'Penthouse gekauft.' },
    { id: 'divorced', title: 'Frisch geschieden', icon: '💔', desc: 'Chantal hat die Papiere geschickt.' },
    { id: 'vitosFriend', title: 'Vitos Freund', icon: '🕶️', desc: 'Mafia-Kredit fristgerecht getilgt.' },
    { id: 'postman', title: 'Fleißiger Bote', icon: '📬', desc: '11 Briefe in Folge.' },
    { id: 'phoenix', title: 'Auferstanden', icon: '🔥', desc: 'Nach dem Game Over weitergespielt.' },
  ],
  has(id) { return State.meta.achievements.includes(id); },
  unlock(id) {
    if (this.has(id)) return;
    const d = this.DEFS.find((x) => x.id === id);
    if (!d) { console.warn('[achievements] unbekannt:', id); return; }
    State.meta.achievements.push(id);
    State.saveMeta();
    SFX.play('unlock');
    UI.toast({ icon: d.icon, title: `Trophäe: ${d.title}`, text: d.desc, tone: 'gold', ms: 4000 });
    const grid = qs('#trophyGrid');
    if (grid) { this.renderWall(grid); const t = qs(`[data-id="${id}"]`, grid); if (t) t.classList.add('fresh'); }
    Bus.emit('achievement:unlock', { id });
  },
  renderWall(grid) {
    grid.innerHTML = '';
    for (const d of this.DEFS) {
      grid.append(h('div', { class: 'trophy' + (this.has(d.id) ? ' on' : ''), 'data-id': d.id, title: d.desc }, h('span', { class: 't-ic' }, d.icon), h('span', {}, d.title)));
    }
  },
};
Bus.on('win', () => Achievements.unlock('firstWin'));
Bus.on('spin:before', ({ bet }) => { if (bet >= 500) Achievements.unlock('highRoller'); });
Bus.on('slots:result', ({ res }) => { if (res.every((s) => s === '7️⃣')) Achievements.unlock('jackpot'); });
Bus.on('roulette:result', ({ type, win }) => { if (type === 'number' && win) Achievements.unlock('plein'); });
Bus.on('rr:result', ({ victim }) => { if (victim === 'igor') Achievements.unlock('igor'); });
Bus.on('beer', ({ beers }) => { if (beers >= 3) Achievements.unlock('regular'); });
Bus.on('kidney.sold', () => Achievements.unlock('donor'));
Bus.on('house.bought', () => Achievements.unlock('owner'));
Bus.on('divorce', () => Achievements.unlock('divorced'));
Bus.on('mafia.repaid', () => Achievements.unlock('vitosFriend'));
Bus.on('post:streak', ({ streak }) => { if (streak >= 11) Achievements.unlock('postman'); });
Bus.on('gameover:restart', () => Achievements.unlock('phoenix'));
</script>
```

- [ ] **Step 3: Prüfen**

Im Browser (`?screen=life&fresh`): Trophäenwand zeigt 12 graue Einträge. Konsole: `Achievements.unlock('plein')` → Toast „Trophäe: Plein" mit Unlock-Klang, Eintrag wird gold und poppt. Reload → bleibt gold. Konsole: `localStorage.removeItem('keller37.state'); location.reload()` → Spielstand frisch, Trophäe bleibt (meta getrennt). Drei Bier kaufen (Konsole vorher `Game.applyDelta(200)`) → „Stammgast".

Run: `tests/dom-selftest.sh` → `passed=56 failed=0`.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat: Achievements mit Trophäenwand

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 19: Game Over & Neues Spiel

**Files:**
- Modify: `keller37.html` (neuer Block `<script id="gameover">` nach `achievements`)

**Interfaces:**
- Consumes: Core-Event `gameover` (aus `afterSpin`, Bedingung `Rules.isGameOver`), `newgame.request` (aus dem ↺-Button), Szene `newgame.confirm` (Task 7), `State.reset`, `Cutscene`, `UI`.
- Produces: Szene `gameover`; Bus-Event `gameover:restart`; `State.meta.gameOvers` wird hochgezählt.

- [ ] **Step 1: JS-Block** – nach `</script>` von `achievements`:

```html
<script id="gameover">
/* ================= GAME OVER & NEUES SPIEL ================= */
Cutscene.define('gameover', [
  { bg: 'hafen-morgen', who: 'vito', mood: 'calm', text: 'Schöner Sonnenaufgang, oder? Ich komme gern hierher, wenn ich nachdenken muss. Über Freunde. Über Schulden.' },
  { bg: 'hafen-morgen', who: 'vito', mood: 'calm', text: 'Die Bank will nichts mehr von dir, ich habe schon etwas von dir, und dein Konto steht bei {{balance}}. Das nennt man ein Ende.' },
  { bg: 'hafen-morgen', who: 'vito', mood: 'happy', fx: 'stats', text: 'Aber ich bin kein Unmensch. Fünfzig Euro und ein neuer Anfang. Wir sehen uns unten.',
    choices: [{ label: 'Nochmal', value: 'again', cls: 'red' }] },
]);

async function restartGame({ playIntro }) {
  State.reset();
  State.s.flags.intro = true;
  State.save();
  UI.setBalance(State.s.balance, { animate: false });
  UI.renderWallet();
  UI.renderSide();
  await UI.show('hub');
  if (playIntro) await Cutscene.play('intro');
}

Bus.on('gameover', async () => {
  const s = State.s;
  const stats = {
    Spins: s.stats.spins,
    'Höchster Kontostand': UI.fmt(s.stats.maxBalance),
    'Größter Gewinn': UI.fmt(s.stats.biggestWin),
    'Verkaufte Nieren': s.stats.kidneys,
    'Beste Post-Serie': s.stats.postStreakBest,
    'Game Overs': State.meta.gameOvers + 1,
  };
  State.meta.gameOvers++;
  State.saveMeta();
  SFX.stopAll();
  await Cutscene.play('gameover', { balance: UI.fmt(s.balance), stats });
  await restartGame({ playIntro: false });
  UI.toast({ icon: '🌅', title: 'Neuer Anfang', text: '50 € und ein Kater. Auf geht’s.', tone: 'gold' });
  await Bus.emit('gameover:restart', {});
});

Bus.on('newgame.request', async () => {
  if (Cutscene.active) return;
  const c = await Cutscene.play('newgame.confirm', {});
  if (c !== 'yes') return;
  await restartGame({ playIntro: true });
});
</script>
```

- [ ] **Step 2: Prüfen**

Im Browser (`?fresh`): Konsole `State.s.balance = -10; State.s.bankDebt = 3000; State.s.mafiaDebt = 300; State.s.mafiaSpins = 3; State.save(); await Game.afterSpin()` → Vito-Szene am Morgenhafen (3 Panels), Panel 3 mit Statistik-Tabelle und Button „Nochmal"; danach Hub, Kontostand `50 €`, keine Zettel, Toast „Neuer Anfang", Trophäe „Auferstanden". Reload → Kontostand `50 €`, kein Intro (Flag gesetzt). `State.meta.gameOvers` ist 1.

Gegenprobe: `State.s.balance = -10; State.s.bankDebt = 2000; State.s.mafiaDebt = 0; State.save(); await Game.afterSpin()` → **kein** Game Over.

↺-Button klicken → Wirt fragt; „Doch nicht" → nichts passiert; nochmal, „Ja, alles weg" → Reset, Intro läuft, Trophäen bleiben.

Run: `tests/dom-selftest.sh` → grün.

- [ ] **Step 3: Commit**

```bash
git add keller37.html
git commit -m "feat: Game Over mit Vito am Hafen und Neues Spiel

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 20: Mobile-Layout, Reduced Motion, Feinschliff

**Files:**
- Modify: `keller37.html` (CSS Sektion 3 (Media Queries am Ende von Sektion 6), `ui` (`renderSide` Tabs), `boot`)

**Interfaces:**
- Consumes: alles Bisherige.
- Produces: Bottom-Bar mit drei Tabs unter 760 px (`.side-tabs`, `.side.open`, `.side-sec.active`); Reduced-Motion-Regeln; Google-Fonts-Fallback-Verhalten geprüft.

- [ ] **Step 1: Media Queries** – am Ende von Sektion 6 (direkt vor `/* ==== 7. ANIMATIONEN ==== */`):

```css
/* -- Mobile (< 760px): Seitenleiste wird Bottom-Bar mit Tabs -- */
.side-tabs { display: none; }
@media (max-width: 760px) {
  .body { grid-template-columns: 1fr; padding: 12px 12px 110px; gap: 12px; }
  .wallet { padding: 8px 12px; gap: 8px; }
  .brand { font-size: 1.5rem; }
  .balance { font-size: 1.15rem; min-width: 110px; padding: 4px 10px; }
  .wallet-mid { order: 3; width: 100%; }
  .side { position: fixed; left: 0; right: 0; bottom: 0; z-index: 30; gap: 0; background: rgba(12,14,10,.97); border-top: 1px solid rgba(201,162,39,.25); }
  .side-sec { display: none; border-radius: 0; box-shadow: none; border: 0; padding: 10px 12px 6px; }
  .side.open .side-sec.active { display: block; }
  .side-sec h3 { display: none; }
  .side-btn { padding: 8px 10px; font-size: .85rem; }
  .side-tabs { display: flex; }
  .side-tabs button { flex: 1; background: none; border: 0; border-top: 3px solid transparent; padding: 8px 4px; font-family: var(--font-display); letter-spacing: .1em; font-size: 1rem; color: var(--dim); }
  .side-tabs button.on { color: var(--gold-2); border-top-color: var(--gold); }
  .hub { grid-template-columns: 1fr 1fr; gap: 10px; }
  .door { height: 150px; padding-top: 14px; gap: 6px; }
  .door .sign { font-size: 1.2rem; padding: 2px 8px; }
  .door .glyph { font-size: 2rem; }
  .finance, .invest-grid, .life-grid { grid-template-columns: 1fr; }
  .roulette-top { flex-direction: column; }
  .table-box { transform: scale(.78); transform-origin: top center; margin-bottom: -90px; }
  .slot-machine { --cell: 64px; padding: 12px 56px 16px 14px; }
  .lever { right: 8px; top: 50px; transform: scale(.8); }
  .pcard { width: 46px; height: 66px; }
  .pcard .pip { font-size: 1.4rem; }
  .pcard .corner { font-size: .65rem; }
  .cards { min-height: 70px; }
  .duel { flex-direction: column; }
  .fighter .face { width: 90px; height: 90px; font-size: 3rem; }
  .house { width: 70px; } .house .roof { border-left-width: 35px; border-right-width: 35px; } .house .wall { width: 64px; height: 50px; font-size: 1.1rem; }
  .cs-stage { flex-direction: column; align-items: center; padding: 0 4vw 2vh; gap: 10px; }
  .cs-portrait { width: 110px; height: 110px; font-size: 4rem; margin-bottom: 0; }
  .cs-text { font-size: 1rem; }
  .cs-box { width: 100%; }
  #toasts { right: 10px; left: 10px; bottom: 120px; }
  .toast { max-width: none; }
}
/* -- Reduced Motion -- */
@media (prefers-reduced-motion: reduce) {
  .neon, .cs-portrait, .balance, .cs-money, .note, .toast, .runner .horse, .spark, .cs-next, .trophy.fresh { animation: none !important; }
  .strip.spinning { animation: none !important; filter: none; }
  .stage, .stage.leaving, .stage.entering { transition: none; animation: none; }
  #wheelCanvas { transition-duration: .3s; }
}
```

- [ ] **Step 2: Tabs in `renderSide`** – in `UI.renderSide` nach `side.append(...)` und vor `side.onclick = …` einfügen:

```js
    const tabs = h('div', { class: 'side-tabs' });
    ['Bar', 'Hinterzimmer', 'Zuhause'].forEach((label, i) => {
      tabs.append(h('button', { onclick: () => {
        const secs = qsa('.side-sec', side);
        const wasOpen = side.classList.contains('open') && secs[i].classList.contains('active');
        secs.forEach((sec, j) => sec.classList.toggle('active', j === i && !wasOpen));
        qsa('button', tabs).forEach((b, j) => b.classList.toggle('on', j === i && !wasOpen));
        side.classList.toggle('open', !wasOpen);
        SFX.play('click');
      } }, label));
    });
    side.append(tabs);
```

Damit ein offener Tab nach `renderSide()` (z.B. nach jedem Bierkauf) offen bleibt: direkt nach `const side = qs('#side');` und **vor** `side.innerHTML = '';` den Zustand merken, und ganz am Ende von `renderSide` (nach `side.onclick = …`) wiederherstellen:

```js
    const openIdx = qsa('.side-sec', side).findIndex((sec) => sec.classList.contains('active'));
    // … (bestehender Aufbau) …
    if (openIdx >= 0) { qsa('.side-sec', side)[openIdx].classList.add('active'); qsa('.side-tabs button', side)[openIdx].classList.add('on'); side.classList.add('open'); }
```

- [ ] **Step 3: Prüfen**

Run (Handybreite): `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=400,850 --virtual-time-budget=4000 --screenshot=/tmp/k37-mobile-hub.png "file://$PWD/keller37.html?fresh"` → PNG ansehen: Hub 2 Spalten, Bottom-Bar mit drei Tabs, keine horizontale Scrollleiste. Gleiches für `?screen=roulette`, `?screen=slots`, `?screen=blackjack`, `?scene=divorce` (Portrait über dem Text).

Im Browser mit DevTools-Gerätemodus (iPhone-Breite): Tab „Bar" öffnet die Bier/Brownie-Buttons, nochmal tippen schließt; Bier kaufen lässt den Tab offen. Desktop: Tabs unsichtbar, Seitenleiste wie vorher.

Reduced Motion: In DevTools Rendering → „Emulate CSS prefers-reduced-motion: reduce" → Neon flackert nicht, Cutscene-Text erscheint sofort, Slots stoppen ohne Blur, kein Shake, keine Partikel.

Fonts-Fallback: DevTools → Network → Offline, Reload → Seite lädt mit Impact/Courier New, nichts bricht.

Run: `tests/dom-selftest.sh` → grün.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat: Mobile-Layout mit Tabs, Reduced Motion, Feinschliff

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 21: Manuelle Checkliste, Screenshots, Abschluss

**Files:**
- Create: `docs/superpowers/screenshots/*.png`
- Create: `docs/superpowers/checklist-2026-09-15.md`
- Modify: `keller37.html` nur bei gefundenen Fehlern

**Interfaces:** keine neuen.

- [ ] **Step 1: Screenshots erzeugen**

```bash
mkdir -p docs/superpowers/screenshots
for s in hub roulette slots horses russian blackjack postman finance invest life; do
  q="?screen=$s&fresh"; [ "$s" = hub ] && q="?fresh"
  tests/screenshot.sh "docs/superpowers/screenshots/$s.png" "$q"
done
for sc in intro divorce mafia.legbreak gameover kidney.offer; do
  tests/screenshot.sh "docs/superpowers/screenshots/scene-$sc.png" "?scene=$sc&fresh"
done
```

Jede PNG mit Read ansehen. Hub-Screenshot mit `?fresh` zeigt das Intro-Overlay – für den reinen Hub zusätzlich `tests/screenshot.sh docs/superpowers/screenshots/hub.png "?screen=hub"` nach einem Lauf ohne `fresh` (Intro-Flag gesetzt) – oder in der Konsole vorher `State.s.flags.intro = true; State.save()`.

- [ ] **Step 2: Checkliste aus Spec 10.2 abarbeiten** – Datei `docs/superpowers/checklist-2026-09-15.md` anlegen und jeden Punkt im Browser durchspielen, Ergebnis eintragen (✅ / ❌ mit Notiz):

```markdown
# KELLER 37 – Abnahme-Checkliste (2026-09-15)

## Szenen (je einmal ausgelöst)
- [ ] intro (erster Start)
- [ ] house.bought
- [ ] tinder.match
- [ ] divorce (Kontostand halbiert sich sichtbar im Panel 3)
- [ ] heartbreak.collapse
- [ ] therapy.done
- [ ] dealer.hired
- [ ] kidney.offer → Nein (nichts passiert) / Ja → kidney.sold
- [ ] mafia.loan (nur beim ersten Kredit)
- [ ] mafia.lastcall (bei 1 Spin Rest)
- [ ] mafia.legbreak (Blackout, Shake, Rechnung)
- [ ] bank.loan (nur beim ersten Kredit)
- [ ] bank.limit (beim ersten abgelehnten Kredit)
- [ ] brownie.first
- [ ] igor.first
- [ ] rr.headshot
- [ ] newgame.confirm (beide Antworten)
- [ ] gameover (Statistik + Nochmal)
- [ ] Überspringen in einer Szene mit drain-Effekt (divorce): Kontostand am Ende korrekt

## Spiele (gewinnen und verlieren)
- [ ] Roulette: Farbe, Gerade/Ungerade, Zahl; Null-Fall (Konsole: Glück 0, viele Spins)
- [ ] Slots: Niete, Paar, Drilling, Jackpot (mit 60 % Glück)
- [ ] Pferde: Sieg und Niederlage, Kommentar läuft
- [ ] Russisches Roulette: Spieler trifft (Doc-Szene), Igor trifft
- [ ] Blackjack: Win, Bust, Dealer, Push
- [ ] Post: Streak bis Stufe 3 (TEMPO! zweimal), falscher Kasten, zu langsam

## Zustand
- [ ] Nach jedem Spin: Bier-Timer, Brownie-Timer, Ehe-Countdown, Mafia-Frist, Anlagen-Countdown stimmen
- [ ] Zinsen + Meds werden vor dem Einsatz abgezogen (Toast „Abzüge")
- [ ] Max-Chip = Guthaben − Zinsen − Meds (mind. 1)
- [ ] Speichern → Reload → Kontostand, Besitz, Schulden, Ehe-Status, Glück identisch
- [ ] Neues Spiel: Reset, Intro, Trophäen bleiben
- [ ] Game Over erreichbar (Konsole), danach 50 €, Trophäe „Auferstanden"
- [ ] Mute an/aus, überlebt Reload

## Technik
- [ ] `tests/run-selftest.mjs` und `tests/dom-selftest.sh` grün
- [ ] Keine Konsolenfehler während eines 10-Minuten-Spiels durch alle Räume
- [ ] Postbote-Timer stoppt beim Verlassen; Herzschlag stoppt beim Verlassen; Galopp stoppt beim Verlassen
- [ ] Esc und Neonschild führen zum Hub; Esc während Cutscene tut nichts
- [ ] Mobile 400 px: alle Screens ohne horizontales Scrollen; Tabs funktionieren
- [ ] Reduced Motion: keine Shakes/Partikel/Flackern, Text sofort da
- [ ] Offline (ohne Google Fonts): Fallback-Fonts, nichts bricht
- [ ] `grep -c "alert(\|confirm(\|prompt(\|onclick=\"" keller37.html` → 0
```

Jeden Punkt tatsächlich ausführen. Gefundene Fehler direkt beheben, Selbsttest erneut laufen lassen, Punkt erst dann abhaken.

- [ ] **Step 3: Grep-Kontrollen**

Run: `grep -c 'alert(\|confirm(\|prompt(' keller37.html` → `0`
Run: `grep -c 'onclick="' keller37.html` → `0`
Run: `node tests/run-selftest.mjs` → `56 bestanden, 0 fehlgeschlagen`
Run: `tests/dom-selftest.sh` → `passed=56 failed=0`

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/screenshots docs/superpowers/checklist-2026-09-15.md keller37.html
git commit -m "docs: Abnahme-Checkliste und Screenshots für KELLER 37

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Selbst-Review des Plans (durchgeführt beim Schreiben)

**Spec-Abdeckung:** Architektur/Blöcke → T1, T4–T8; Look/Tokens/Textur/Shell/Hub/Übergänge → T6; Komponenten → T6; Cutscene-Engine/Cast/Orte/Szenen → T7 (Engine, intro, newgame.confirm), T8 (brownie.first, kidney.*), T9 (bank.*, mafia.*), T11 (house/tinder/divorce/heartbreak/therapy/dealer), T16 (igor.first, rr.headshot), T19 (gameover); Toasts → T6/T8; Spiele → T12–T17; Räume → T9–T11; Game Over + Bank-Limit → T1 (Rules), T9 (Limit-UI), T19; Sound → T5; Achievements → T18; Mobile/Reduced Motion → T20; Verifikation (`?selftest`, Checkliste, Screenshots) → T1, T21. Mechanik-Referenz (Spec 9) → T1–T3 als Tests, T8 (`afterSpin`-Reihenfolge, Kosten), T12–T17 (Timings).

**Bewusste Abweichungen von der Spec:** Blackjack-Austeilreihenfolge ist Spieler/Dealer/Spieler/Dealer (Original: Spieler-Spieler-Dealer-Dealer) – ergebnisneutral, da das Deck zufällig ist. Anlagen erzwingen Mindesteinsatz 10 € auch per JS (Original nur per `min`-Attribut). Bus-Handler laufen parallel (`Promise.all`), daher kann ein Achievement-Toast während einer Szene erscheinen – gewollt.

**Typ-Konsistenz geprüft:** `Game.settle(delta, {from, game})`, `Game.beginSpin(bet)`, `Game.readBet(id)`, `Game.bindBet(root, id)`, `UI.toast({icon,title,text,tone,ms})`, `UI.setBalance(n, {animate, duration})`, `Cutscene.play(id, ctx)`, `Cutscene.define/bind`, `Rules.*`-Signaturen aus T1–T3, Bus-Event-Namen (`slots:result`, `roulette:result`, `rr:result`, `post:streak`, `mafia.repaid`, `gameover:restart` …) stimmen zwischen Emittern (T8–T17, T19) und Listenern (T18) überein.
