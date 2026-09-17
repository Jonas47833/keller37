# Casino Royal (Mega Seven, Craps, Glücksrad, Madame Sylvie) – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein zweites Spielhaus („Casino Royal") mit drei neuen Spielen, erreichbar über die Stadt nur mit Auto, im freien Spiel und im Story-Modus.

**Architecture:** Reine Spielregeln in einem neuen DOM-freien Block `royal-rules` (`const RoyalRules = {…}`), damit sie im Node-Selbsttest laufen. Screens, Lobby, Eintritt, Sylvie und Trophäen in einem Block `casino-royal`. Die Story-Engine bekommt drei kleine generische Erweiterungen: Raum `royal`, bedingte Sperren (`story.gates`), Hooks `royal:enter`/`royal:guest`. Alle drei Spiele nutzen `Game.beginSpin`/`Game.settle` wie die Keller-Spiele, damit Zinsen, Meds, Glück, `spin:after`, Trophäen und Story-Stats automatisch greifen.

**Tech Stack:** Vanilla JS/CSS in `keller37.html`; Selbsttest-Block `selftest`; `tests/run-selftest.mjs` (Blockliste erweitern).

**Spec:** `docs/superpowers/specs/2026-09-17-story-kater-design.md`, Abschnitt 7 (Casino Royal) und 8 (Rooms).

## Global Constraints

- Ein-Datei-Vorgabe; neue Blöcke `<script id="royal-rules">` (vor `selftest`, nach `story-rules`) und `<script id="casino-royal">` (nach `room-stadt`).
- `tests/run-selftest.mjs`: `'royal-rules'` in die Blockliste aufnehmen (zwischen `'story-rules'` und `'story-probe'`).
- Block `rules` **nicht** anfassen (Parallelarbeit); Glück kommt über `Rules.luck(State.s)` rein.
- Alle Auszahlungen/Gewichte aus der Spec: Mega-Seven-Gewichte `30/25/18/12/7/8`, Tabelle 🍒 2/5/10 · 🔔 3/10/25 · BAR 5/20/50 · 💎 10/40/100 · 7️⃣ 20/100/500, Scatter ≥3 → 5 Freispiele ×2, max. 15; Craps Pass Line 1:1, Field 1:1 (2/12 → 2:1); Rad 13× 0, 5× 0,5, 3× 1, 1× 2, 1× 5, 1× 10; Eintritt 100 €.
- Ergebnis-Events: `megaslots:result`, `craps:result`, `wheel:result` mit `{ delta, bet, detail }`.
- Deterministische Tests mit `seq(...)` oder `seeded(n)` (Mulberry32, in Task 1 angelegt).
- Vor jedem Commit `node tests/run-selftest.mjs` grün; vor dem letzten Commit `tests/dom-selftest.sh` und Screenshots.
- Commit-Messages enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## Dateistruktur

| Ort | Inhalt |
|---|---|
| `<script id="royal-rules">` (neu) | `RoyalRules`: `MEGA`, `megaSymbol`, `megaRoll`, `megaLineWins`, `megaScatters`, `megaWin`, `megaShift`, `megaLuckOverride`, `megaDelta`; `crapsRoll`, `crapsPass`, `crapsField`, `crapsSettle`, `crapsLuckOverride`; `WHEEL`, `wheelSpin`, `wheelPayout`, `wheelLuckOverride`; `ENTRY_FEE`, `GUEST_WIN`, `canEnter` |
| `<script id="casino-royal">` (neu) | `Royal` (Lobby, Eintritt, Gast-Status), `MegaSlots`, `Craps`, `Wheel` (Screens), Sylvie-Szenen, Trophäen-Listener, `UI.register` für `royal`, `megaslots`, `craps`, `wheel` |
| Templates | `tpl-royal`, `tpl-megaslots`, `tpl-craps`, `tpl-wheel` |
| CSS | `.royal-*`, `.mega-*`, `.craps-*`, `.wheel-*`, `.cs-bg.royal`, `.storefront.royal` |
| Block `cutscene-engine` | `CAST.sylvie` |
| Block `room-stadt` | vierter Storefront `royal` |
| Block `ui` (`renderSide`) | Sektion „Casino Royal“ |
| Block `story-rules` | `ROOMS` + `'royal'`, `HOOKS` + `'royal:guest'`, `gate()`, `validate` (gates) |
| Block `story-engine` | `ROOM_OF` + royal/megaslots/craps/wheel, `isLocked`/`lockReason` mit `gate` |
| Block `achievements` | 3 neue DEFS |
| Block `boot` | `?screen=royal&game=…` |
| `tests/run-selftest.mjs` | Blockliste |
| `README.md` | Casino Royal, Dev-Parameter |

---

### Task 1: `RoyalRules` – Mega Seven (reine Regeln, RTP-Simulation)

**Files:**
- Create: Block `<script id="royal-rules">` in `keller37.html`, direkt vor `<script id="title">` (also nach `story-rules`)
- Modify: `tests/run-selftest.mjs` (Blockliste)
- Test: Block `selftest`, neuer Abschnitt `/* ---- RoyalRules: Mega Seven ---- */` vor `/* ---- StoryRules ---- */` (o. ä. – hinter den Slot-Tests)

**Interfaces (Produces):**
```js
RoyalRules.MEGA = { SYMBOLS, WEIGHTS, LINES, PAY, BETS: [100, 250, 500, 1000], FREE_SPINS: 5, FREE_MULT: 2, FREE_MAX: 15, SCATTER: '⭐' }
RoyalRules.megaSymbol(rng) → symbol                       // gewichtet
RoyalRules.megaRoll(rng) → grid   // grid[reel][row], 5×3
RoyalRules.megaLineWins(grid) → [{ line, sym, count, mult }]   // nur Linien mit count ≥ 3, mult aus PAY (× Linieneinsatz)
RoyalRules.megaScatters(grid) → number
RoyalRules.megaWin(grid, bet, free) → { lines, scatters, payout, freeSpins }  // payout in €, freeSpins = 5 wenn scatters ≥ 3 sonst 0
RoyalRules.megaShift(grid, reel, dir) → grid  // dir ±1: Spalte rotieren
RoyalRules.megaLuckOverride(grid, luck, rng) → grid
RoyalRules.megaDelta(bet, payout, free) → number  // free: payout, sonst payout − bet
seeded(n) → rng   // Testhelfer (Mulberry32), im selftest-Block neben seq()
```

- [ ] **Step 1: Failing Tests schreiben**

Im Block `selftest` neben `seq` den Helfer anlegen:

```js
/* deterministischer rng mit Seed (Mulberry32) – für Simulationen */
const seeded = (a) => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
```

Tests (hinter den `slotDelta`-Tests):

```js
/* ---- RoyalRules: Mega Seven ---- */
const G = (cols) => cols.map((c) => c.split(' ')); // 'a b c' je Walze, oben→unten
T.test('megaSymbol: gewichtete Ziehung', () => {
  T.eq(RoyalRules.megaSymbol(seq(0)), '🍒');
  T.eq(RoyalRules.megaSymbol(seq(0.299)), '🍒');
  T.eq(RoyalRules.megaSymbol(seq(0.30)), '🔔');
  T.eq(RoyalRules.megaSymbol(seq(0.92)), '⭐');
  T.eq(RoyalRules.megaSymbol(seq(0.999)), '⭐');
});
T.test('megaRoll: 5 Walzen × 3 Reihen', () => {
  const g = RoyalRules.megaRoll(seeded(1));
  T.eq(g.length, 5); g.forEach((r) => T.eq(r.length, 3));
  g.flat().forEach((s) => T.ok(RoyalRules.MEGA.SYMBOLS.includes(s)));
});
T.test('megaLineWins: Mitte, oben, unten, V, umgekehrtes V', () => {
  T.eq(RoyalRules.megaLineWins(G(['🔔 🍒 🔔', '🔔 🍒 🔔', '🔔 🍒 🔔', '🔔 🔔 🔔', '🔔 🔔 🔔'])).map((w) => [w.line, w.sym, w.count, w.mult]),
    [[0, '🍒', 3, 2], [1, '🔔', 5, 25], [2, '🔔', 5, 25]]);
  T.eq(RoyalRules.megaLineWins(G(['BAR 🍒 🍒', '🍒 BAR 🍒', '🍒 🍒 BAR', '🍒 BAR 🍒', 'BAR 🍒 🍒'])).map((w) => [w.line, w.sym, w.count, w.mult]), [[3, 'BAR', 5, 50]]);
  T.eq(RoyalRules.megaLineWins(G(['🍒 🍒 💎', '🍒 💎 🍒', '💎 🍒 🍒', '🍒 💎 🍒', '🍒 🍒 💎'])).map((w) => [w.line, w.sym, w.count, w.mult]), [[4, '💎', 5, 100]]);
});
T.test('megaLineWins: nur von links, zwei gleiche zählen nicht, Scatter bildet keine Linie', () => {
  const g = G(['🍒 7️⃣ 🍒', '🍒 7️⃣ 🍒', '🍒 🍒 🍒', '🍒 7️⃣ 🍒', '🍒 7️⃣ 🍒']); // Mitte: 7️⃣ 7️⃣ 🍒 7️⃣ 7️⃣ → 2 von links → nichts; oben/unten 🍒×5; V und ΛV brechen nach 1
  T.eq(RoyalRules.megaLineWins(g).map((w) => [w.line, w.sym, w.count]), [[1, '🍒', 5], [2, '🍒', 5]]);
  T.eq(RoyalRules.megaLineWins(G(['⭐ 🍒 🍒', '⭐ 🍒 🍒', '⭐ 🍒 🍒', '🍒 🍒 🍒', '🍒 🍒 🍒'])).filter((w) => w.sym === '⭐'), []);
});
T.test('megaScatters / megaWin / megaDelta', () => {
  const g = G(['⭐ 🍒 🍒', '🍒 ⭐ 🍒', '🍒 🍒 ⭐', '🔔 🔔 🔔', '🔔 🔔 🔔']);
  T.eq(RoyalRules.megaScatters(g), 3);
  const w = RoyalRules.megaWin(g, 500, false);
  T.eq(w.scatters, 3); T.eq(w.freeSpins, 5);
  T.eq(w.payout, 0, 'keine Linie: Mitte 🍒 ⭐ 🍒 🔔 🔔 → 1 von links');
  const g2 = G(['🍒 🍒 🍒', '🍒 🍒 🍒', '🍒 🍒 🍒', '🔔 🔔 🔔', '🔔 🔔 🔔']);
  const w2 = RoyalRules.megaWin(g2, 500, false);
  T.eq(w2.payout, 5 * 2 * 100, 'einheitliche Spalten: alle fünf Linien 🍒×3 → 5 × 2 × Linieneinsatz 100');
  T.eq(RoyalRules.megaWin(g2, 500, true).payout, 2000, 'Freispiel ×2');
  T.eq(RoyalRules.megaDelta(500, 600, false), 100);
  T.eq(RoyalRules.megaDelta(500, 0, false), -500);
  T.eq(RoyalRules.megaDelta(500, 1200, true), 1200, 'Freispiel kostet nichts');
});
T.test('megaShift: Spalte rotieren', () => {
  const g = G(['a b c', 'd e f', 'g h i', 'j k l', 'm n o']);
  T.eq(RoyalRules.megaShift(g, 1, 1)[1], ['e', 'f', 'd']);
  T.eq(RoyalRules.megaShift(g, 1, -1)[1], ['f', 'd', 'e']);
  T.eq(RoyalRules.megaShift(g, 1, 1)[0], ['a', 'b', 'c'], 'andere Walzen unverändert');
  T.eq(g[1], ['d', 'e', 'f'], 'Original unverändert');
});
T.test('megaLuckOverride: kein Glück / Pech-Wurf / bester Ein-Schritt-Gewinn / bestehender Gewinn', () => {
  // keine Linie trifft; Walze 1 um −1 → Mitte 7️⃣×5 (500) schlägt die beiden 💎×3-Alternativen (10)
  const g = G(['🔔 7️⃣ 💎', '7️⃣ BAR 💎', '💎 7️⃣ 🔔', '🔔 7️⃣ BAR', 'BAR 7️⃣ 💎']);
  T.eq(RoyalRules.megaLineWins(g), [], 'Ausgangsgitter gewinnt nichts');
  T.eq(RoyalRules.megaLuckOverride(g, 0, seq(0.5)), g, 'ohne Glück unverändert');
  T.eq(RoyalRules.megaLuckOverride(g, 50, seq(0.6)), g, 'rng ≥ luck/100 → unverändert');
  const o = RoyalRules.megaLuckOverride(g, 100, seq(0));
  T.eq(o[1], ['💎', '7️⃣', 'BAR'], 'Walze 1 um −1 rotiert');
  T.eq(RoyalRules.megaLineWins(o).map((w) => [w.line, w.sym, w.count, w.mult]), [[0, '7️⃣', 5, 500]], 'Mittellinie 7️⃣×5');
  T.eq(g[1], ['7️⃣', 'BAR', '💎'], 'Original unverändert');
  const win = G(['🍒 🍒 🍒', '🍒 🍒 🍒', '🍒 🍒 🍒', '🔔 🔔 🔔', '🔔 🔔 🔔']);
  T.eq(RoyalRules.megaLuckOverride(win, 100, seq(0)), win, 'bestehender Gewinn bleibt');
});
T.test('Mega Seven: RTP-Korridor (60.000 Spins, Seed 7)', () => {
  const rng = seeded(7); let paid = 0, ret = 0, free = 0;
  for (let i = 0; i < 60000; i++) {
    const isFree = free > 0; if (isFree) free--; else paid += 500;
    const w = RoyalRules.megaWin(RoyalRules.megaRoll(rng), 500, isFree);
    ret += w.payout; if (w.freeSpins) free = Math.min(RoyalRules.MEGA.FREE_MAX, free + w.freeSpins);
  }
  const rtp = ret / paid;
  T.ok(rtp > 0.88 && rtp < 0.98, `RTP ${rtp.toFixed(3)} außerhalb 0,88–0,98`);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs`
Expected: `Script-Block "royal-rules" fehlt` (nach Erweiterung der Blockliste) bzw. `RoyalRules is not defined`.

Blockliste in `tests/run-selftest.mjs`: `['rules', 'gear-rules', 'util', 'state', 'bus', 'story-rules', 'royal-rules', 'story-probe', 'story-schuld', 'selftest']`.

- [ ] **Step 3: Implementieren**

Neuer Block vor `<script id="title">`:

```html
<script id="royal-rules">
/* ================= CASINO ROYAL – reine Spielregeln (Mega Seven, Craps, Glücksrad) ================= */
const RoyalRules = {
  ENTRY_FEE: 100,
  GUEST_WIN: 5000,
  /* ---- Mega Seven: 5 Walzen × 3 Reihen, 5 feste Linien ---- */
  MEGA: {
    SYMBOLS: ['🍒', '🔔', 'BAR', '💎', '7️⃣', '⭐'],
    WEIGHTS: [30, 25, 18, 12, 7, 8],
    LINES: [[1, 1, 1, 1, 1], [0, 0, 0, 0, 0], [2, 2, 2, 2, 2], [0, 1, 2, 1, 0], [2, 1, 0, 1, 2]], // Reihe je Walze
    PAY: { '🍒': [0, 0, 0, 2, 5, 10], '🔔': [0, 0, 0, 3, 10, 25], BAR: [0, 0, 0, 5, 20, 50], '💎': [0, 0, 0, 10, 40, 100], '7️⃣': [0, 0, 0, 20, 100, 500] },
    BETS: [100, 250, 500, 1000],
    FREE_SPINS: 5, FREE_MULT: 2, FREE_MAX: 15, SCATTER: '⭐',
  },
  megaSymbol(rng) {
    const M = RoyalRules.MEGA;
    const total = M.WEIGHTS.reduce((a, b) => a + b, 0);
    let r = rng() * total;
    for (let i = 0; i < M.SYMBOLS.length; i++) { r -= M.WEIGHTS[i]; if (r < 0) return M.SYMBOLS[i]; }
    return M.SYMBOLS[M.SYMBOLS.length - 1];
  },
  megaRoll(rng) { return [0, 1, 2, 3, 4].map(() => [0, 1, 2].map(() => RoyalRules.megaSymbol(rng))); },
  megaLineWins(grid) {
    const M = RoyalRules.MEGA, out = [];
    M.LINES.forEach((rows, line) => {
      const sym = grid[0][rows[0]];
      if (sym === M.SCATTER || !M.PAY[sym]) return;
      let count = 1;
      for (let r = 1; r < 5; r++) { if (grid[r][rows[r]] === sym) count++; else break; }
      if (count >= 3) out.push({ line, sym, count, mult: M.PAY[sym][count] });
    });
    return out;
  },
  megaScatters(grid) { return grid.flat().filter((s) => s === RoyalRules.MEGA.SCATTER).length; },
  megaWin(grid, bet, free) {
    const M = RoyalRules.MEGA;
    const lines = RoyalRules.megaLineWins(grid);
    const lineBet = bet / M.LINES.length;
    const payout = Math.round(lines.reduce((a, w) => a + w.mult * lineBet, 0) * (free ? M.FREE_MULT : 1));
    const scatters = RoyalRules.megaScatters(grid);
    return { lines, scatters, payout, freeSpins: scatters >= 3 ? M.FREE_SPINS : 0 };
  },
  megaShift(grid, reel, dir) {
    const g = grid.map((c) => c.slice());
    const c = g[reel];
    g[reel] = dir > 0 ? [c[1], c[2], c[0]] : [c[2], c[0], c[1]];
    return g;
  },
  /* Glück: gewinnt keine Linie, wird die Walze/Richtung gewählt, deren Ein-Schritt-Verschiebung am meisten zahlt */
  megaLuckOverride(grid, luck, rng) {
    if (RoyalRules.megaLineWins(grid).length) return grid;
    if (!(rng() * 100 < luck)) return grid;
    let best = null, bestPay = 0;
    for (let reel = 0; reel < 5; reel++) for (const dir of [1, -1]) {
      const g = RoyalRules.megaShift(grid, reel, dir);
      const pay = RoyalRules.megaLineWins(g).reduce((a, w) => a + w.mult, 0);
      if (pay > bestPay) { best = g; bestPay = pay; }
    }
    return best || grid;
  },
  megaDelta(bet, payout, free) { return free ? payout : payout - bet; },
};
</script>
```

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen (RTP-Test gibt bei Fehlschlag den Wert aus – dann Gewichte laut Spec anpassen, nicht die Struktur). Hinweis: `SelfTest.run` ist seit Plan 1 async; `tests/dom-selftest.sh` hat ein 4-s-Budget – bleibt die Simulation darunter (Node-Laufzeit des Tests < 1 s), ist alles gut.

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(royal): Mega-Seven-Regeln (5×3, 5 Linien, Freispiele, Glück) mit RTP-Simulation

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `RoyalRules` – Craps

**Files:**
- Modify: Block `royal-rules`
- Test: Block `selftest`

**Interfaces (Produces):**
```js
RoyalRules.CRAPS = { MIN: 50, MAX: 2000, FIELD: { 2: 2, 3: 1, 4: 1, 9: 1, 10: 1, 11: 1, 12: 2 } }
RoyalRules.crapsRoll(rng) → [d1, d2]
RoyalRules.crapsPass(point, sum) → { result: 'win'|'lose'|'point'|'none', point: number|null }
RoyalRules.crapsField(sum) → 0 | 1 | 2
RoyalRules.crapsSettle({ pass, field }, point, dice) → { delta, pass: 'win'|'lose'|'point'|'none'|null, field: 'win'|'lose'|null, point, sum }
RoyalRules.crapsLuckOverride(dice, point, hasPass, luck, rng) → dice
```

- [ ] **Step 1: Failing Tests**

```js
/* ---- RoyalRules: Craps ---- */
T.test('crapsRoll: zwei Würfel 1–6', () => {
  T.eq(RoyalRules.crapsRoll(seq(0, 0.99)), [1, 6]);
  T.eq(RoyalRules.crapsRoll(seq(0.5, 0.17)), [4, 2]);
});
T.test('crapsPass: Come-out und Punktphase', () => {
  T.eq(RoyalRules.crapsPass(null, 7), { result: 'win', point: null });
  T.eq(RoyalRules.crapsPass(null, 11), { result: 'win', point: null });
  for (const s of [2, 3, 12]) T.eq(RoyalRules.crapsPass(null, s), { result: 'lose', point: null }, `Craps ${s}`);
  for (const s of [4, 5, 6, 8, 9, 10]) T.eq(RoyalRules.crapsPass(null, s), { result: 'point', point: s });
  T.eq(RoyalRules.crapsPass(6, 6), { result: 'win', point: null });
  T.eq(RoyalRules.crapsPass(6, 7), { result: 'lose', point: null });
  T.eq(RoyalRules.crapsPass(6, 11), { result: 'none', point: 6 }, '11 in der Punktphase ist nichts');
  T.eq(RoyalRules.crapsPass(6, 2), { result: 'none', point: 6 });
});
T.test('crapsField: Tabelle', () => {
  const exp = { 2: 2, 3: 1, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0, 9: 1, 10: 1, 11: 1, 12: 2 };
  for (const [s, m] of Object.entries(exp)) T.eq(RoyalRules.crapsField(+s), m, `Summe ${s}`);
});
T.test('crapsSettle: alle 36 Kombinationen im Come-out mit Pass 100 + Field 50', () => {
  for (let a = 1; a <= 6; a++) for (let b = 1; b <= 6; b++) {
    const sum = a + b;
    const r = RoyalRules.crapsSettle({ pass: 100, field: 50 }, null, [a, b]);
    const passDelta = [7, 11].includes(sum) ? 100 : [2, 3, 12].includes(sum) ? -100 : 0;
    const fm = RoyalRules.crapsField(sum);
    const fieldDelta = fm ? 50 * fm : -50;
    T.eq(r.delta, passDelta + fieldDelta, `${a}+${b}`);
    T.eq(r.sum, sum);
    T.eq(r.point, [7, 11, 2, 3, 12].includes(sum) ? null : sum);
  }
});
T.test('crapsSettle: Punktphase, nur Pass', () => {
  T.eq(RoyalRules.crapsSettle({ pass: 100, field: 0 }, 8, [4, 4]), { delta: 100, pass: 'win', field: null, point: null, sum: 8 });
  T.eq(RoyalRules.crapsSettle({ pass: 100, field: 0 }, 8, [3, 4]), { delta: -100, pass: 'lose', field: null, point: null, sum: 7 });
  T.eq(RoyalRules.crapsSettle({ pass: 100, field: 0 }, 8, [1, 1]), { delta: 0, pass: 'none', field: null, point: 8, sum: 2 });
  T.eq(RoyalRules.crapsSettle({ pass: 0, field: 100 }, null, [6, 6]), { delta: 200, pass: null, field: 'win', point: null, sum: 12 }, 'Field ohne Pass, 12 zahlt doppelt');
});
T.test('crapsLuckOverride: verlierender Wurf wird verschoben, Gewinner nie', () => {
  T.eq(RoyalRules.crapsLuckOverride([3, 4], 8, true, 0, seq(0)), [3, 4], 'ohne Glück');
  const o = RoyalRules.crapsLuckOverride([3, 4], 8, true, 100, seq(0));
  T.ok(o[0] + o[1] !== 7, 'Sieben in der Punktphase wird vermieden');
  T.ok(Math.abs(o[0] - 3) + Math.abs(o[1] - 4) === 1, 'genau ein Würfel um 1');
  const c = RoyalRules.crapsLuckOverride([1, 2], null, true, 100, seq(0));
  T.eq(c, [2, 2], 'Craps 3 im Come-out → erster Würfel +1 → 4');
  T.eq(RoyalRules.crapsLuckOverride([1, 1], null, true, 100, seq(0)), [1, 1], 'Craps 2: kein ±1-Schritt entkommt (3 bleibt Craps) → unverändert');
  T.eq(RoyalRules.crapsLuckOverride([1, 2], null, false, 100, seq(0)), [1, 2], 'ohne Pass-Einsatz gibt es nichts zu retten');
  T.eq(RoyalRules.crapsLuckOverride([4, 4], 8, true, 100, seq(0)), [4, 4], 'Gewinner bleibt');
  T.eq(RoyalRules.crapsLuckOverride([6, 6], 6, true, 100, seq(0)), [6, 6], 'neutraler Wurf (12 in Punktphase) bleibt');
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL `crapsRoll is not a function`.

- [ ] **Step 3: Implementieren** (in `RoyalRules` ergänzen)

```js
  /* ---- Craps: Pass Line + Field ---- */
  CRAPS: { MIN: 50, MAX: 2000, FIELD: { 2: 2, 3: 1, 4: 1, 9: 1, 10: 1, 11: 1, 12: 2 } },
  crapsRoll(rng) { return [Math.floor(rng() * 6) + 1, Math.floor(rng() * 6) + 1]; },
  crapsPass(point, sum) {
    if (point == null) {
      if (sum === 7 || sum === 11) return { result: 'win', point: null };
      if (sum === 2 || sum === 3 || sum === 12) return { result: 'lose', point: null };
      return { result: 'point', point: sum };
    }
    if (sum === point) return { result: 'win', point: null };
    if (sum === 7) return { result: 'lose', point: null };
    return { result: 'none', point };
  },
  crapsField(sum) { return RoyalRules.CRAPS.FIELD[sum] || 0; },
  crapsSettle(bets, point, dice) {
    const sum = dice[0] + dice[1];
    let delta = 0, pass = null, field = null, newPoint = point;
    if (bets.pass > 0) {
      const p = RoyalRules.crapsPass(point, sum);
      pass = p.result; newPoint = p.point;
      if (p.result === 'win') delta += bets.pass; else if (p.result === 'lose') delta -= bets.pass;
    }
    if (bets.field > 0) {
      const m = RoyalRules.crapsField(sum);
      field = m ? 'win' : 'lose';
      delta += m ? bets.field * m : -bets.field;
    }
    return { delta, pass, field, point: newPoint, sum };
  },
  /* Glück: ein verlierender Pass-Wurf (7 in der Punktphase, 2/3/12 im Come-out) wird um ±1 auf einem Würfel verschoben */
  crapsLuckOverride(dice, point, hasPass, luck, rng) {
    if (!hasPass) return dice;
    const losing = (d) => { const s = d[0] + d[1]; return point != null ? s === 7 : (s === 2 || s === 3 || s === 12); };
    if (!losing(dice) || !(rng() * 100 < luck)) return dice;
    for (const [i, dir] of [[0, 1], [0, -1], [1, 1], [1, -1]]) {
      const d = dice.slice(); d[i] += dir;
      if (d[i] >= 1 && d[i] <= 6 && !losing(d)) return d;
    }
    return dice;
  },
```

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(royal): Craps-Regeln (Pass Line, Field, Punktphase, Glück)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `RoyalRules` – Glücksrad

**Files:**
- Modify: Block `royal-rules`
- Test: Block `selftest`

**Interfaces (Produces):**
```js
RoyalRules.WHEEL = { SEGMENTS: [24 Multiplikatoren], BETS: [100, 500, 1000, 5000] }
RoyalRules.wheelSpin(rng) → index 0..23
RoyalRules.wheelPayout(index, bet) → number   // Einsatz × Multiplikator, gerundet
RoyalRules.wheelDelta(index, bet) → number    // payout − bet
RoyalRules.wheelLuckOverride(index, luck, rng) → index  // Bankrott → nächstes Nicht-Bankrott-Segment
```

- [ ] **Step 1: Failing Tests**

```js
/* ---- RoyalRules: Glücksrad ---- */
T.test('WHEEL: 24 Segmente, Verteilung, Erwartungswert 93,75 %', () => {
  const S = RoyalRules.WHEEL.SEGMENTS;
  T.eq(S.length, 24);
  const count = (v) => S.filter((x) => x === v).length;
  T.eq([count(0), count(0.5), count(1), count(2), count(5), count(10)], [13, 5, 3, 1, 1, 1]);
  T.eq(S.reduce((a, b) => a + b, 0) / 24, 0.9375);
  S.forEach((v, i) => { if (v === 0) T.ok(S[(i + 1) % 24] !== 0 || S[(i + 2) % 24] !== 0, `Bankrott ${i} hat binnen 2 Schritten ein Nicht-Bankrott-Segment`); });
});
T.test('wheelSpin / wheelPayout / wheelDelta', () => {
  T.eq(RoyalRules.wheelSpin(seq(0)), 0);
  T.eq(RoyalRules.wheelSpin(seq(0.999)), 23);
  T.eq(RoyalRules.wheelSpin(seq(0.5)), 12);
  const S = RoyalRules.WHEEL.SEGMENTS;
  const i10 = S.indexOf(10), iH = S.indexOf(0.5), i0 = S.indexOf(0);
  T.eq(RoyalRules.wheelPayout(i10, 500), 5000);
  T.eq(RoyalRules.wheelPayout(iH, 500), 250);
  T.eq(RoyalRules.wheelPayout(i0, 500), 0);
  T.eq(RoyalRules.wheelDelta(i10, 500), 4500);
  T.eq(RoyalRules.wheelDelta(iH, 500), -250);
  T.eq(RoyalRules.wheelDelta(S.indexOf(1), 500), 0);
});
T.test('wheelLuckOverride: Bankrott rückt auf das nächste Nicht-Bankrott-Segment', () => {
  const S = RoyalRules.WHEEL.SEGMENTS;
  const i0 = S.indexOf(0);
  T.eq(RoyalRules.wheelLuckOverride(i0, 0, seq(0)), i0, 'ohne Glück');
  const o = RoyalRules.wheelLuckOverride(i0, 100, seq(0));
  T.ok(S[o] !== 0 && (o === (i0 + 1) % 24 || o === (i0 + 2) % 24), 'nächstes Nicht-Bankrott, 1–2 Schritte weiter');
  T.eq(RoyalRules.wheelLuckOverride(S.indexOf(10), 100, seq(0)), S.indexOf(10), 'Gewinn bleibt');
  T.eq(RoyalRules.wheelLuckOverride(i0, 50, seq(0.999)), i0, 'Glück greift nicht (rng ≥ luck/100)');
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL.

- [ ] **Step 3: Implementieren**

```js
  /* ---- Glücksrad: 24 Segmente, Multiplikator auf den Einsatz (0 = Bankrott, 0,5 = Hälfte zurück) ---- */
  WHEEL: {
    SEGMENTS: [0, 0, 0.5, 0, 0, 1, 0, 1, 0, 2, 0, 0.5, 0, 1, 0, 5, 0, 0.5, 0, 10, 0, 0.5, 0, 0.5],
    BETS: [100, 500, 1000, 5000],
  },
  wheelSpin(rng) { return Math.floor(rng() * RoyalRules.WHEEL.SEGMENTS.length); },
  wheelPayout(index, bet) { return Math.round(bet * RoyalRules.WHEEL.SEGMENTS[index]); },
  wheelDelta(index, bet) { return RoyalRules.wheelPayout(index, bet) - bet; },
  wheelLuckOverride(index, luck, rng) {
    const S = RoyalRules.WHEEL.SEGMENTS;
    if (S[index] !== 0 || !(rng() * 100 < luck)) return index;
    for (let k = 1; k <= 2; k++) { const j = (index + k) % S.length; if (S[j] !== 0) return j; }
    return index;
  },
```

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(royal): Glücksrad-Regeln (24 Segmente, 93,75 % RTP, Glück)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Lobby, Eintritt, Gast-Status, Sylvie, Stadt-Schaufenster, Story-Anbindung, Trophäen

**Files:**
- Create: Block `<script id="casino-royal">` direkt nach `</script>` von `room-stadt`; Template `tpl-royal` nach `tpl-stadt`; CSS
- Modify: Block `cutscene-engine` (`CAST`), Block `room-stadt` (`SHOPS`-Rendering), Block `ui` (`renderSide`), Block `story-rules` (`ROOMS`, `HOOKS`, `gate`, `validate`), Block `story-engine` (`ROOM_OF`, `isLocked`, `lockReason`), Block `achievements` (`DEFS`), Block `boot`
- Test: Block `selftest` (`canEnter`, `gate`)

**Interfaces:**
- Consumes: Plan 1 – `Story.hook(at)`, `s.story.stats.royalVisits`, `StoryRules.HOOKS`
- Produces:
  - `RoyalRules.canEnter(s) → { ok: true } | { ok: false, reason: 'car' | 'gate', text }` (reine Prüfung ohne Story-Gate; Gate-Text kommt von `StoryRules.gate`)
  - `RoyalRules.entryFee(s) → 0 | 100` (0 wenn `s.flags.royalGuest`, oder im Story-Modus wenn `s.story.royalPaidDay === s.story.day`)
  - `Royal.enter() → Promise` (von Stadt-Schaufenster und Seitenleiste aufgerufen: prüft, kassiert, `royalVisits++`, `Story.hook('royal:enter')`, `UI.show('royal')`)
  - `s.flags.royalGuest` (beide Modi), gesetzt bei `win` ≥ 5.000 in einem Royal-Spiel → Trophäe `royalHigh`, `Story.hook('royal:guest')`
  - Story-Definition: `gates: { royal: [{ when: cond, text: '…' }] }`; `StoryRules.gate(story, s, screen) → text | null`
  - `StoryRules.ROOMS` enthält `'royal'`; `StoryRules.HOOKS` enthält `'royal:guest'`
  - `Story.ROOM_OF`: `royal: ['royal'], megaslots: ['royal'], craps: ['royal'], wheel: ['royal']`
  - `CAST.sylvie`, `bg 'royal'`
  - Trophäen `royalHigh`, `fuenfSiebener`, `gegenDieWand`
  - Dev: `?screen=royal&game=megaslots|craps|wheel`

- [ ] **Step 1: Failing Tests**

```js
/* ---- RoyalRules: Eintritt ---- */
T.test('RoyalRules.canEnter / entryFee', () => {
  T.eq(RoyalRules.canEnter(base()), { ok: false, reason: 'car', text: 'Parkservice only – zu Fuß kommt hier keiner rein.' });
  T.eq(RoyalRules.canEnter(base({ car: 'audiA3' })), { ok: true });
  T.eq(RoyalRules.entryFee(base({ car: 'audiA3' })), 100);
  T.eq(RoyalRules.entryFee(base({ car: 'audiA3', flags: { royalGuest: true } })), 0);
  const st = { day: 4, royalPaidDay: 4 };
  T.eq(RoyalRules.entryFee(base({ car: 'audiA3', story: st })), 0, 'Story: heute schon bezahlt');
  T.eq(RoyalRules.entryFee(base({ car: 'audiA3', story: { day: 5, royalPaidDay: 4 } })), 100);
});
T.test('StoryRules.gate: bedingte Sperre mit Text', () => {
  const st = Object.assign({}, STORY_PROBE, { gates: { royal: [{ when: { flag: 'zitter' }, text: 'Sie zittern.' }, { when: { var: 'mut', lte: 0 }, text: 'Zu wenig Mut.' }] } });
  const s = Object.assign(base(), { story: StoryRules.freshStoryPart(st) });
  T.eq(StoryRules.gate(st, s, 'royal'), 'Zu wenig Mut.', 'erste zutreffende Sperre');
  s.story.flags.zitter = true;
  T.eq(StoryRules.gate(st, s, 'royal'), 'Sie zittern.');
  s.story.flags.zitter = false; s.story.vars.mut = 1;
  T.eq(StoryRules.gate(st, s, 'royal'), null);
  T.eq(StoryRules.gate(st, s, 'slots'), null, 'ohne Gate offen');
  T.eq(StoryRules.gate(STORY_PROBE, s, 'royal'), null, 'Story ohne gates');
});
T.test('StoryRules.validate: gates brauchen when und text, Raum royal bekannt', () => {
  const st = Object.assign({}, STORY_PROBE, { id: 'x', gates: { royal: [{ text: 'ohne when' }] }, start: Object.assign({}, STORY_PROBE.start, { unlocked: { jobs: ['spueler'], doors: [], rooms: ['royal'] } }) });
  T.eq(StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']), ['x: Gate royal[0] braucht when und text']);
});
```

`base()` im Selbsttest hat kein `flags`/`car` – `base({ car: … })` setzt es; `flags` fehlt → `entryFee` muss `s.flags && s.flags.royalGuest` prüfen.

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL.

- [ ] **Step 3: Implementieren**

**`RoyalRules`** (Block `royal-rules`):

```js
  /* ---- Eintritt ---- */
  canEnter(s) {
    if (!s.car) return { ok: false, reason: 'car', text: 'Parkservice only – zu Fuß kommt hier keiner rein.' };
    return { ok: true };
  },
  entryFee(s) {
    if (s.flags && s.flags.royalGuest) return 0;
    if (s.story && s.story.royalPaidDay != null && s.story.royalPaidDay === s.story.day) return 0;
    return RoyalRules.ENTRY_FEE;
  },
```

**`StoryRules`** (Block `story-rules`):
- `ROOMS: ['bar', 'doc', 'bank', 'mafia', 'invest', 'life', 'vito', 'stadt', 'royal'],`
- `HOOKS`: `'royal:guest'` anhängen.
- Neu:

```js
  /* Bedingte Sperre eines Screens: erste zutreffende Regel liefert den Kreidetext, sonst null */
  gate(story, s, screen) {
    for (const g of ((story.gates || {})[screen] || [])) if (StoryRules.check(g.when, s)) return g.text;
    return null;
  },
```

- `validate`, vor `return errs;`:

```js
    for (const [screen, list] of Object.entries(story.gates || {})) list.forEach((g, i) => { if (!g.when || !g.text) errs.push(`${story.id}: Gate ${screen}[${i}] braucht when und text`); });
```

**`Story`** (Block `story-engine`):
- `ROOM_OF: { finance: ['bank', 'mafia'], invest: ['invest'], life: ['life'], vito: ['vito'], stadt: ['stadt'], royal: ['royal'], megaslots: ['royal'], craps: ['royal'], wheel: ['royal'] },`
- `isLocked(screen)`: vor `if (this.DOORS.includes(screen))` einfügen `if (StoryRules.gate(this.story, State.s, screen)) return true;`
- `lockReason(screen)`: als erste Zeile `const g = StoryRules.gate(this.story, State.s, screen); if (g) return g;`

**Cast + Hintergrund:** in `CAST` (Block `cutscene-engine`): `sylvie: { name: 'Madame Sylvie', emoji: '🎩', color: '#e8d5a3' },`. CSS neben `.cs-bg.autohaus`:

```css
.cs-bg.royal { background: radial-gradient(ellipse at 50% 0%, #6b1f2a 0%, #2a0a12 45%, #0d0508 100%); }
.cs-bg.royal::after { content: ""; position: absolute; inset: 0; background: repeating-linear-gradient(90deg, transparent 0 60px, rgba(232,213,163,.05) 60px 62px); pointer-events: none; }
```

**Template `tpl-royal`** (nach `tpl-stadt`):

```html
<template id="tpl-royal">
  <div class="panel stretch royal">
    <div class="royal-head"><h2>🎩 Casino Royal</h2><p class="royal-sylvie" id="royalLine"></p></div>
    <div class="hub royal-hub">
      <div class="door" data-screen="megaslots" style="--neon: var(--gold-2)"><div class="sign">Mega Seven</div><div class="glyph">🎰</div><div class="chalk-tag">5 Walzen · Freispiele</div><div class="knob"></div></div>
      <div class="door" data-screen="craps" style="--neon: var(--neon-green)"><div class="sign">Craps</div><div class="glyph">🎲</div><div class="chalk-tag">Pass Line · Field</div><div class="knob"></div></div>
      <div class="door" data-screen="wheel" style="--neon: var(--neon-red)"><div class="sign">Glücksrad</div><div class="glyph">🎡</div><div class="chalk-tag">bis 10×</div><div class="knob"></div></div>
    </div>
    <div class="bet-bar"><button class="btn ghost sm" id="royalLeave">← Zurück in die Stadt</button></div>
  </div>
</template>
```

CSS:

```css
.royal { background: radial-gradient(ellipse at 50% 0%, rgba(107,31,42,.6), transparent 60%); }
.royal-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 14px; justify-content: space-between; }
.royal-head h2 { font-family: var(--font-display); color: var(--gold-2); letter-spacing: .1em; margin: 0; }
.royal-sylvie { font-family: var(--font-mono); font-style: italic; color: var(--dim); margin: 0; }
.royal-hub { grid-template-columns: repeat(3, 1fr); }
.storefront.royal { --neon: var(--gold-2); border-color: #5a3a12; background: linear-gradient(180deg, #3a1a22, #14080b); }
.storefront.royal.locked { opacity: .7; }
.storefront.royal.locked .sign { text-shadow: none; color: var(--dim); }
```

**Block `casino-royal`** (nach `room-stadt`):

```html
<script id="casino-royal">
/* ================= CASINO ROYAL – Lobby, Eintritt, Madame Sylvie ================= */
const Royal = {
  GAMES: ['megaslots', 'craps', 'wheel'],
  SYLVIE: {
    first: 'Madame Sylvie sieht kurz von ihren Zahlen auf. Sie sieht alles. Sie sagt nichts.',
    guest: 'Madame Sylvie nickt. „Gast des Hauses. Der Eintritt entfällt. Das Haus behält sich alles andere vor.“',
    paid: 'Hundert Euro. Die Garderobe ist links, die Ausgänge sind egal.',
  },
  inStory() { return State.mode === 'story' && typeof Story !== 'undefined' && Story.story; },
  async enter() {
    const s = State.s;
    if (Cutscene.active || Game.inFlight > 0) return;
    const chk = RoyalRules.canEnter(s);
    if (!chk.ok) { UI.toast({ icon: '🎩', title: 'Casino Royal', text: chk.text, tone: 'loss' }); SFX.play('lose'); return; }
    if (this.inStory() && Story.isLocked('royal')) { UI.toast({ icon: '🔒', title: Story.lockReason('royal'), tone: 'loss' }); SFX.play('lose'); return; }
    const fee = RoyalRules.entryFee(s);
    if (fee > 0 && s.balance < fee) { UI.toast({ icon: '🎩', title: 'Eintritt 100 €', text: 'So viel hast du nicht dabei.', tone: 'loss' }); SFX.play('lose'); return; }
    if (fee > 0) {
      Game.applyDelta(-fee, { quiet: true });
      if (this.inStory()) s.story.royalPaidDay = s.story.day;
      UI.toast({ icon: '🎩', title: 'Eintritt −100 €', text: this.SYLVIE.paid, tone: 'info' });
    }
    if (this.inStory()) s.story.stats.royalVisits++;
    if (!s.flags.royalSeen) { s.flags.royalSeen = true; State.save(); await Cutscene.play('royal.first', {}); }
    State.save(); UI.renderWallet(); UI.renderSide();
    await UI.show('royal');
    if (typeof Story !== 'undefined') await Story.hook('royal:enter');
  },
  async onWin(amount, game) {
    if (!this.GAMES.includes(game) || amount < RoyalRules.GUEST_WIN) return;
    Achievements.unlock('royalHigh');
    const s = State.s;
    if (s.flags.royalGuest) return;
    s.flags.royalGuest = true; State.save();
    await Cutscene.play('royal.guest', { amount: UI.fmt(amount) });
    if (typeof Story !== 'undefined') await Story.hook('royal:guest');
  },
  line() { return State.s.flags.royalGuest ? 'Gast des Hauses. Madame Sylvie grüßt nicht, aber sie sieht her.' : 'Madame Sylvie steht am Ende des Saals. Sie zählt. Nicht Geld – Leute.'; },
};
UI.register('royal', {
  template: 'tpl-royal',
  mount(root) {
    qs('#royalLine', root).textContent = Royal.line();
    qsa('.door', root).forEach((d) => d.addEventListener('click', () => { SFX.play('click'); UI.show(d.dataset.screen); }));
    qs('#royalLeave', root).addEventListener('click', () => { SFX.play('click'); UI.show('stadt'); });
    if (typeof Story !== 'undefined') Story.decorateHub(root);
  },
});
Cutscene.define('royal.first', [
  { bg: 'royal', who: 'sylvie', mood: 'calm', text: 'Willkommen. Sie sind neu. Man sieht es an den Schuhen, nicht am Auto.' },
  { bg: 'royal', who: 'sylvie', mood: 'calm', text: 'Drei Tische. Höhere Einsätze, bessere Beleuchtung, dieselbe Mathematik. Viel Vergnügen.' },
]);
Cutscene.define('royal.guest', [
  { bg: 'royal', who: 'sylvie', mood: 'happy', text: '{{amount}} in einer Runde. Sie sind ab jetzt Gast des Hauses – der Eintritt entfällt.' },
  { bg: 'royal', who: 'sylvie', mood: 'calm', text: 'Das Haus schenkt nichts. Es investiert.' },
]);
Bus.on('win', ({ amount, game }) => Royal.onWin(amount, game));
</script>
```

`Story.decorateHub(root)` markiert Türen mit `.door[data-screen]` als gesperrt – im Royal-Hub greift das für die drei Spiele über `ROOM_OF` (sie sind offen, sobald `royal` offen ist).

**Stadt** (Block `room-stadt`, `render()`, im `if (!shop)`-Zweig nach der Schleife):

```js
      const chk = RoyalRules.canEnter(State.s);
      const gate = Royal.inStory() ? StoryRules.gate(Story.story, State.s, 'royal') : null;
      const roomOpen = !Royal.inStory() || Story.roomUnlocked('royal');
      if (roomOpen) street.append(h('div', { class: 'storefront royal' + (chk.ok && !gate ? '' : ' locked'), 'data-shop': 'royal', onclick: () => Royal.enter() },
        h('div', { class: 'sign' }, 'Casino Royal'),
        h('div', { class: 'glyph' }, '🎩'),
        h('p', { class: 'seller' }, gate || (chk.ok ? 'Der Parkservice nimmt den Schlüssel.' : chk.text)),
        h('div', { class: 'owned' }, State.s.flags.royalGuest ? 'Gast des Hauses' : `Eintritt ${UI.fmt(RoyalRules.ENTRY_FEE)}`)));
```

CSS: `.strasse` bleibt 3 Spalten; ergänzen `.strasse .storefront.royal { grid-column: 1 / -1; min-height: 200px; }` (das Casino liegt quer am Ende der Straße).

**Seitenleiste** (Block `ui`, `renderSide`, nach der `stadt`-Sektion):

```js
    if (room('royal') && typeof Royal !== 'undefined') secs.push(sec('Casino Royal',
      btn('🎩 Casino Royal', s.flags.royalGuest ? 'Gast' : (s.car ? this.fmt(RoyalRules.ENTRY_FEE) : '🚗 nötig'), 'royal', !s.car)));
```

Und im Klick-Handler der Seitenleiste (`data-action`), wo `finance`/`invest`/`stadt` per `UI.show(action)` behandelt werden: `royal` → `Royal.enter()` (Suche nach `dataset.action` in Block `ui`/`core` und dort `if (a === 'royal') return Royal.enter();` ergänzen).

**Trophäen** (Block `achievements`, `DEFS`):

```js
    { id: 'royalHigh', title: 'High Roller', icon: '🎩', desc: 'Einzelgewinn von 5.000 € im Casino Royal.' },
    { id: 'fuenfSiebener', title: 'Fünf Siebener', icon: '7️⃣', desc: 'Fünf 7️⃣ auf einer Linie bei Mega Seven.' },
    { id: 'gegenDieWand', title: 'Gegen die Wand', icon: '🎡', desc: 'Bankrott am Glücksrad mit 5.000 € Einsatz.' },
```

**Boot** (Block `boot`, nach der `shop`-Zeile):

```js
  if (params.get('screen') === 'royal' && params.has('game') && ['megaslots', 'craps', 'wheel'].includes(params.get('game'))) { await UI.show(params.get('game')); }
  else await UI.show(params.get('screen') || 'hub');
```

(ersetzt die bestehende Zeile `await UI.show(params.get('screen') || 'hub');`).

- [ ] **Step 4: Tests + Browser**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.
Run: `tests/dom-selftest.sh` → grün.
Run: `tests/screenshot.sh /tmp/stadt.png "?screen=stadt"` → viertes Schaufenster „Casino Royal“ quer unten, gesperrt (kein Auto).
Run: `tests/screenshot.sh /tmp/royal.png "?screen=royal"` → Lobby mit drei Türen (Türen führen noch auf „Screen fehlt“ – kommt in Task 5–7).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(royal): Lobby, Eintritt, Gast des Hauses, Madame Sylvie, Stadt-Schaufenster, Story-Gates

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Screen Mega Seven

**Files:**
- Create: Template `tpl-megaslots`, CSS `.mega-*`, `MegaSlots` im Block `casino-royal`
- Test: manuell + DOM-Selbsttest

**Interfaces:**
- Consumes: `RoyalRules.mega*`, `Game.beginSpin/readBet/bindBet/settle`, `Rules.luck`
- Produces: `Bus.emit('megaslots:result', { delta, bet, detail: { grid, lines, scatters, free, freeLeft } })`; Trophäe `fuenfSiebener`

- [ ] **Step 1: Template**

```html
<template id="tpl-megaslots">
  <div class="panel mega-panel">
    <div class="mega-machine">
      <div class="slot-head neon" style="--neon: var(--gold-2)">Mega Seven</div>
      <div class="mega-grid" id="megaGrid"></div>
      <div class="mega-lines" id="megaLines"></div>
      <div class="mega-free hidden" id="megaFree">FREISPIELE <span id="megaFreeLeft">0</span> · ×2</div>
    </div>
    <div class="chalk paytable">
      <h4>Auszahlung × Linieneinsatz</h4>
      <table>
        <tr><td>7️⃣</td><td>20 / 100 / 500</td></tr>
        <tr><td>💎</td><td>10 / 40 / 100</td></tr>
        <tr><td>BAR</td><td>5 / 20 / 50</td></tr>
        <tr><td>🔔</td><td>3 / 10 / 25</td></tr>
        <tr><td>🍒</td><td>2 / 5 / 10</td></tr>
        <tr><td>⭐ ×3+</td><td>5 Freispiele, ×2</td></tr>
      </table>
      <p class="side-hint">5 Linien · Linieneinsatz = Einsatz ÷ 5</p>
    </div>
    <div class="status" id="megaStatus">Einsatz wählen und drehen</div>
    <div class="bet-bar">
      <input type="number" id="megaBet" value="100" min="100" hidden>
      <button class="chip" data-chip="100" data-v="100">100</button>
      <button class="chip" data-chip="250" data-v="25">250</button>
      <button class="chip" data-chip="500" data-v="50">500</button>
      <button class="chip" data-chip="1000" data-v="max">1000</button>
      <button class="btn solid" id="btnMega">Drehen</button>
      <button class="btn ghost sm" id="megaBack">← Lobby</button>
    </div>
  </div>
</template>
```

CSS:

```css
.mega-panel { display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: start; }
.mega-panel .status, .mega-panel .bet-bar { grid-column: 1 / -1; }
.mega-machine { --cell: 64px; position: relative; background: linear-gradient(180deg, #3a1020, #150409); border: 4px solid var(--gold-2); border-radius: 18px; padding: 14px 18px 18px; box-shadow: var(--shadow), inset 0 0 40px rgba(0,0,0,.6); }
.mega-grid { display: grid; grid-template-columns: repeat(5, var(--cell)); gap: 6px; background: #0a0a0a; padding: 10px; border-radius: 10px; border: 3px solid #5a3a12; justify-content: center; }
.mega-grid .cell { width: var(--cell); height: var(--cell); display: flex; align-items: center; justify-content: center; font-size: calc(var(--cell) * .5); background: linear-gradient(180deg, #fff, #e0d8c0); border-radius: 6px; font-family: var(--font-display); color: #222; }
.mega-grid .cell.bar { font-size: calc(var(--cell) * .3); letter-spacing: .05em; }
.mega-grid .cell.spin { filter: blur(2px); animation: megaFlicker .12s linear infinite; }
.mega-grid .cell.hit { box-shadow: 0 0 0 3px var(--gold-2), 0 0 18px var(--gold-2); animation: hitGlow .6s ease 3; }
.mega-lines { font-family: var(--font-mono); font-size: .8rem; color: var(--gold-2); min-height: 1.2em; margin-top: 8px; text-align: center; }
.mega-free { margin-top: 6px; text-align: center; font-family: var(--font-display); color: var(--neon-amber); letter-spacing: .15em; }
@keyframes megaFlicker { 0% { opacity: .6; } 100% { opacity: 1; } }
@media (max-width: 720px) { .mega-panel { grid-template-columns: 1fr; } .mega-machine { --cell: 50px; } }
```

Prüfen, dass `hitGlow` existiert (`grep -n "@keyframes hitGlow"`), sonst aus `.reel-win.hit` übernehmen. In `.mode-reduced`/`prefers-reduced-motion`-Regel (Zeile mit `animation: none !important`) `.mega-grid .cell.spin` ergänzen.

- [ ] **Step 2: `MegaSlots` implementieren** (im Block `casino-royal` unter `Royal`)

```js
/* ---- Mega Seven ---- */
const MegaSlots = {
  root: null, spinning: false, gen: 0, freeLeft: 0, lastBet: 0,
  alive(gen) { return !!this.root && this.gen === gen; },
  cellText(sym) { return sym === 'BAR' ? 'BAR' : sym; },
  render(grid, opts = {}) {
    const g = qs('#megaGrid', this.root); if (!g) return;
    g.innerHTML = '';
    for (let row = 0; row < 3; row++) for (let reel = 0; reel < 5; reel++) {
      const sym = grid[reel][row];
      g.append(h('div', { class: 'cell' + (sym === 'BAR' ? ' bar' : '') + (opts.spin && opts.spin.includes(reel) ? ' spin' : ''), 'data-reel': reel, 'data-row': row }, this.cellText(sym)));
    }
  },
  markHits(lines) {
    for (const w of lines) for (let r = 0; r < w.count; r++) {
      const row = RoyalRules.MEGA.LINES[w.line][r];
      const el = qs(`.cell[data-reel="${r}"][data-row="${row}"]`, this.root); if (el) el.classList.add('hit');
    }
  },
  async spin() {
    if (this.spinning || !this.root) return;
    const free = this.freeLeft > 0;
    const bet = free ? this.lastBet : Game.readBet('megaBet');
    if (!free && !RoyalRules.MEGA.BETS.includes(bet)) { UI.toast({ icon: '🎰', title: 'Einsatz', text: 'Hier gilt 100, 250, 500 oder 1.000 €.', tone: 'loss' }); return; }
    if (!Game.beginSpin(free ? 0 : bet)) return;
    const run = Game.run, gen = this.gen;
    this.spinning = true;
    try {
      qs('#btnMega', this.root).disabled = true;
      if (free) this.freeLeft--;
      this.lastBet = bet;
      let grid = RoyalRules.megaRoll(Math.random);
      grid = RoyalRules.megaLuckOverride(grid, Rules.luck(State.s), Math.random);
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      const shown = RoyalRules.megaRoll(Math.random);
      this.render(shown, { spin: [0, 1, 2, 3, 4] });
      SFX.loop('reelSpin', 120);
      const stops = reduced ? [100, 150, 200, 250, 300] : [700, 1050, 1400, 1750, 2100];
      for (let i = 0; i < 5; i++) {
        await wait(stops[i] - (i ? stops[i - 1] : 0));
        if (!this.alive(gen)) return;
        shown[i] = grid[i];
        this.render(shown, { spin: [1, 2, 3, 4].filter((k) => k > i) });
        SFX.play('reelStop');
      }
      SFX.stop('reelSpin');
      const w = RoyalRules.megaWin(grid, bet, free);
      const delta = RoyalRules.megaDelta(bet, w.payout, free);
      if (w.freeSpins) this.freeLeft = Math.min(RoyalRules.MEGA.FREE_MAX, this.freeLeft + w.freeSpins);
      if (this.alive(gen)) {
        this.markHits(w.lines);
        qs('#megaLines', this.root).textContent = w.lines.map((l) => `Linie ${l.line + 1}: ${this.cellText(l.sym)} ×${l.count} → ${l.mult}×`).join(' · ') + (w.scatters >= 3 ? ` · ⭐×${w.scatters}: +${w.freeSpins} Freispiele` : '');
        const st = qs('#megaStatus', this.root);
        st.innerHTML = w.payout > 0 ? `<span class="win">Auszahlung ${UI.fmt(w.payout)}${free ? ' (Freispiel ×2)' : ''}</span>` : `<span class="loss">${free ? 'Freispiel · nichts' : `Niete · −${UI.fmt(bet)}`}</span>`;
        qs('#megaFree', this.root).classList.toggle('hidden', this.freeLeft === 0);
        qs('#megaFreeLeft', this.root).textContent = this.freeLeft;
        if (w.lines.some((l) => l.sym === '7️⃣' && l.count === 5)) Achievements.unlock('fuenfSiebener');
      }
      await Bus.emit('megaslots:result', { delta, bet: free ? 0 : bet, detail: { grid, lines: w.lines, scatters: w.scatters, free, freeLeft: this.freeLeft } });
      await Game.settle(delta, { from: this.alive(gen) ? qs('.mega-machine', this.root) : null, game: 'megaslots', bet: free ? 0 : bet, run });
    } finally {
      SFX.stop('reelSpin');
      if (this.gen === gen) { this.spinning = false; const b = qs('#btnMega', this.root); if (b) { b.disabled = false; b.textContent = this.freeLeft > 0 ? `Freispiel (${this.freeLeft})` : 'Drehen'; } }
    }
  },
  onKey(e) { if (e.code === 'Space' && qs('#cutscene').hidden && !e.repeat) { e.preventDefault(); MegaSlots.spin(); } },
};
UI.register('megaslots', {
  template: 'tpl-megaslots',
  mount(root) {
    MegaSlots.gen++; MegaSlots.root = root;
    MegaSlots.render([['🍒', '7️⃣', '💎'], ['🔔', '7️⃣', 'BAR'], ['💎', '7️⃣', '🍒'], ['BAR', '7️⃣', '🔔'], ['🍒', '7️⃣', '💎']]);
    Game.bindBet(root, 'megaBet');
    qs('#btnMega', root).addEventListener('click', () => MegaSlots.spin());
    qs('#megaBack', root).addEventListener('click', () => { SFX.play('click'); UI.show('royal'); });
    document.addEventListener('keydown', MegaSlots.onKey);
    if (MegaSlots.freeLeft > 0) { qs('#megaFree', root).classList.remove('hidden'); qs('#megaFreeLeft', root).textContent = MegaSlots.freeLeft; qs('#btnMega', root).textContent = `Freispiel (${MegaSlots.freeLeft})`; }
  },
  unmount() { MegaSlots.gen++; document.removeEventListener('keydown', MegaSlots.onKey); SFX.stop('reelSpin'); MegaSlots.root = null; MegaSlots.spinning = false; },
});
```

`Game.beginSpin(0)`: `Rules.checkSpin` verlangt `bet > 0` → für Freispiele scheitert das. Deshalb in `MegaSlots.spin` für `free` **nicht** `beginSpin` aufrufen, sondern nur `Game.inFlight++` und `Game.run` lesen; `Game.settle(delta, { bet: 0, run })` verbucht dann die Auszahlung und ruft `afterSpin` (Zinsen/Meds werden bei Freispielen nicht extra fällig – Escrow-Logik prüfen: `settle` ruft `applyDelta(delta + bet)`; mit `bet: 0` stimmt das). Konkret: `if (free) { Game.inFlight++; } else if (!Game.beginSpin(bet)) return;`. Prüfen, dass `Game.run` bei `inFlight++` ohne `beginSpin` noch auf `State.s` zeigt (`grep -n "run:" keller37.html` im Block `core`); sonst `const run = State.s`.

`data-v` der Chips steuert nur die Farbe (`.chip[data-v="…"]`), daher die Zuordnung 100→`100`, 250→`25`, 500→`50`, 1000→`max`.

- [ ] **Step 3: Verifikation**

Run: `tests/dom-selftest.sh` → grün.
Run: `tests/screenshot.sh /tmp/mega.png "?screen=royal&game=megaslots"` → 5×3-Gitter, Tabelle, Chips 100/250/500/1000.
Manuell im Browser (`?fresh&screen=royal&game=megaslots`, vorher per Konsole `State.s.balance = 20000; State.save()`): 10 Spins, Freispiele auslösen (Konsole: `MegaSlots.freeLeft = 5`), prüfen: Freispiel kostet nichts, Button zeigt „Freispiel (n)“.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat(royal): Mega-Seven-Screen (5×3, Linien leuchten, Freispiele)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Screen Craps

**Files:**
- Create: Template `tpl-craps`, CSS `.craps-*`, `Craps` im Block `casino-royal`

**Interfaces:**
- Produces: `Bus.emit('craps:result', { delta, bet, detail: { dice, sum, pass, field, point } })`
- Wirtschaft: Pro Wurf `Game.beginSpin(riskiert)` mit `riskiert = pass + field`; der Pass-Einsatz wird pro Wurf neu treuhänderisch abgezogen und bei `none` zurückgezahlt (`delta 0` für den Pass-Anteil). So gilt „jeder Wurf ist ein Spin“ inklusive Zinsen/Meds.

- [ ] **Step 1: Template + CSS**

```html
<template id="tpl-craps">
  <div class="panel craps-panel">
    <div class="craps-table">
      <div class="craps-head"><span class="neon" style="--neon: var(--neon-green)">CRAPS</span><span class="craps-point" id="crapsPoint">Come-out</span></div>
      <div class="craps-dice"><div class="die" id="die1">⚄</div><div class="die" id="die2">⚂</div></div>
      <div class="craps-bets">
        <div class="craps-bet" id="passBox"><h4>PASS LINE</h4><div class="amt" id="passAmt">0 €</div><p>7/11 gewinnt · 2/3/12 verliert · sonst Punkt</p></div>
        <div class="craps-bet" id="fieldBox"><h4>FIELD</h4><div class="amt" id="fieldAmt">0 €</div><p>3 4 9 10 11 zahlen 1:1 · 2 und 12 zahlen 2:1</p></div>
      </div>
      <div class="craps-history" id="crapsHistory"></div>
    </div>
    <div class="status" id="crapsStatus">Einsatz wählen, auf Pass Line oder Field legen, würfeln</div>
    <div class="bet-bar">
      <input type="number" id="crapsBet" value="50" min="50" hidden>
      <button class="chip" data-chip="50" data-v="50">50</button>
      <button class="chip" data-chip="200" data-v="25">200</button>
      <button class="chip" data-chip="500" data-v="100">500</button>
      <button class="chip" data-chip="2000" data-v="max">2000</button>
      <button class="btn green sm" id="btnPass">auf Pass</button>
      <button class="btn blue sm" id="btnField">auf Field</button>
      <button class="btn ghost sm" id="btnClearCraps">Leeren</button>
      <button class="btn solid" id="btnRoll">Würfeln</button>
      <button class="btn ghost sm" id="crapsBack">← Lobby</button>
    </div>
  </div>
</template>
```

```css
.craps-table { background: radial-gradient(ellipse at 50% 30%, #1f6b3a, #0d3a20 70%, #082414); border: 6px solid #4a2a12; border-radius: 120px / 40px; padding: 18px 26px; box-shadow: var(--shadow), inset 0 0 60px rgba(0,0,0,.5); }
.craps-head { display: flex; justify-content: space-between; align-items: center; font-family: var(--font-display); font-size: 1.4rem; }
.craps-point { font-family: var(--font-mono); font-size: .9rem; background: #fff; color: #222; border-radius: 50%; padding: 6px 10px; }
.craps-point.on { background: var(--gold); }
.craps-dice { display: flex; gap: 18px; justify-content: center; margin: 16px 0; }
.die { width: 70px; height: 70px; border-radius: 12px; background: #fff; color: #222; font-size: 3.2rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 6px 14px rgba(0,0,0,.6); }
.die.rolling { animation: dieRoll .5s linear infinite; }
@keyframes dieRoll { 0% { transform: rotate(0) translateY(0); } 50% { transform: rotate(180deg) translateY(-14px); } 100% { transform: rotate(360deg) translateY(0); } }
.craps-bets { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.craps-bet { border: 2px dashed rgba(255,255,255,.5); border-radius: 10px; padding: 10px; text-align: center; color: #fff; }
.craps-bet h4 { margin: 0; font-family: var(--font-display); letter-spacing: .15em; }
.craps-bet .amt { font-family: var(--font-mono); font-size: 1.2rem; color: var(--gold-2); }
.craps-bet p { font-size: .75rem; color: rgba(255,255,255,.7); margin: 4px 0 0; }
.craps-bet.won { box-shadow: 0 0 0 3px var(--neon-green); } .craps-bet.lost { opacity: .5; }
.craps-history { font-family: var(--font-mono); font-size: .8rem; color: rgba(255,255,255,.7); text-align: center; margin-top: 10px; min-height: 1.2em; }
```

Reduced-Motion-Regel um `.die.rolling` ergänzen.

- [ ] **Step 2: `Craps` implementieren**

```js
/* ---- Craps ---- */
const Craps = {
  root: null, rolling: false, gen: 0, point: null, bets: { pass: 0, field: 0 }, history: [],
  FACES: ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅'],
  alive(gen) { return !!this.root && this.gen === gen; },
  place(kind) {
    if (this.rolling || !this.root) return;
    const v = Game.readBet('crapsBet');
    if (!(v >= RoyalRules.CRAPS.MIN && v <= RoyalRules.CRAPS.MAX)) { UI.toast({ icon: '🎲', title: 'Einsatz', text: `Zwischen ${UI.fmt(RoyalRules.CRAPS.MIN)} und ${UI.fmt(RoyalRules.CRAPS.MAX)}.`, tone: 'loss' }); return; }
    if (kind === 'pass' && this.point != null) { UI.toast({ icon: '🎲', title: 'Punkt läuft', text: 'Pass Line erst nach der Entscheidung.', tone: 'loss' }); return; }
    this.bets[kind] = Math.min(RoyalRules.CRAPS.MAX, this.bets[kind] + v);
    SFX.play('chip'); this.render();
  },
  clear() { if (this.rolling) return; if (this.point != null) { this.bets.field = 0; } else this.bets = { pass: 0, field: 0 }; this.render(); },
  render() {
    if (!this.root) return;
    qs('#passAmt', this.root).textContent = UI.fmt(this.bets.pass);
    qs('#fieldAmt', this.root).textContent = UI.fmt(this.bets.field);
    const p = qs('#crapsPoint', this.root); p.textContent = this.point == null ? 'Come-out' : `Punkt ${this.point}`; p.classList.toggle('on', this.point != null);
    qs('#crapsHistory', this.root).textContent = this.history.slice(-10).join(' · ');
    qs('#btnPass', this.root).disabled = this.point != null;
    qs('#btnRoll', this.root).disabled = this.rolling || (this.bets.pass + this.bets.field) === 0;
  },
  async roll() {
    if (this.rolling || !this.root) return;
    const risk = this.bets.pass + this.bets.field;
    if (risk === 0) return;
    if (!Game.beginSpin(risk)) return;
    const run = Game.run, gen = this.gen;
    this.rolling = true; this.render();
    try {
      qsa('.craps-bet', this.root).forEach((b) => b.classList.remove('won', 'lost'));
      qsa('.die', this.root).forEach((d) => d.classList.add('rolling'));
      SFX.loop('reelSpin', 100);
      let dice = RoyalRules.crapsRoll(Math.random);
      dice = RoyalRules.crapsLuckOverride(dice, this.point, this.bets.pass > 0, Rules.luck(State.s), Math.random);
      await wait(matchMedia('(prefers-reduced-motion: reduce)').matches ? 150 : 900);
      SFX.stop('reelSpin');
      if (!this.alive(gen)) return;
      qsa('.die', this.root).forEach((d) => d.classList.remove('rolling'));
      qs('#die1', this.root).textContent = this.FACES[dice[0]]; qs('#die2', this.root).textContent = this.FACES[dice[1]];
      SFX.play('reelStop');
      const r = RoyalRules.crapsSettle(this.bets, this.point, dice);
      const bets = Object.assign({}, this.bets);
      this.history.push(`${dice[0]}+${dice[1]}=${r.sum}`);
      if (r.pass === 'win') qs('#passBox', this.root).classList.add('won'); if (r.pass === 'lose') qs('#passBox', this.root).classList.add('lost');
      if (r.field === 'win') qs('#fieldBox', this.root).classList.add('won'); if (r.field === 'lose') qs('#fieldBox', this.root).classList.add('lost');
      this.point = r.point;
      if (r.pass === 'win' || r.pass === 'lose') this.bets.pass = 0;
      this.bets.field = 0;
      const st = qs('#crapsStatus', this.root);
      const txt = [];
      if (r.pass === 'point') txt.push(`Punkt ist ${r.point}`); if (r.pass === 'win') txt.push('Pass gewinnt'); if (r.pass === 'lose') txt.push(r.sum === 7 ? 'Seven out' : 'Craps');
      if (r.field === 'win') txt.push(`Field ${RoyalRules.crapsField(r.sum) === 2 ? 'doppelt' : 'gewinnt'}`); if (r.field === 'lose') txt.push('Field verliert');
      st.innerHTML = `<span class="${r.delta > 0 ? 'win' : r.delta < 0 ? 'loss' : ''}">${txt.join(' · ') || 'Weiter'} (${r.delta >= 0 ? '+' : '−'}${UI.fmt(Math.abs(r.delta))})</span>`;
      this.render();
      await Bus.emit('craps:result', { delta: r.delta, bet: risk, detail: { dice, sum: r.sum, pass: r.pass, field: r.field, point: r.point, bets } });
      await Game.settle(r.delta, { from: this.alive(gen) ? qs('.craps-table', this.root) : null, game: 'craps', bet: risk, run });
    } finally {
      SFX.stop('reelSpin');
      if (this.gen === gen) { this.rolling = false; this.render(); }
    }
  },
  onKey(e) { if (e.code === 'Space' && qs('#cutscene').hidden && !e.repeat) { e.preventDefault(); Craps.roll(); } },
};
UI.register('craps', {
  template: 'tpl-craps',
  mount(root) {
    Craps.gen++; Craps.root = root;
    Game.bindBet(root, 'crapsBet');
    qs('#btnPass', root).addEventListener('click', () => Craps.place('pass'));
    qs('#btnField', root).addEventListener('click', () => Craps.place('field'));
    qs('#btnClearCraps', root).addEventListener('click', () => Craps.clear());
    qs('#btnRoll', root).addEventListener('click', () => Craps.roll());
    qs('#crapsBack', root).addEventListener('click', () => { SFX.play('click'); UI.show('royal'); });
    document.addEventListener('keydown', Craps.onKey);
    Craps.render();
  },
  unmount() { Craps.gen++; document.removeEventListener('keydown', Craps.onKey); SFX.stop('reelSpin'); Craps.root = null; Craps.rolling = false; },
});
```

Hinweis zur Wirtschaft: `Game.settle(delta, { bet: risk })` zahlt `delta + risk` aus – bei `pass: 'none'` (Punkt läuft weiter) ist der Pass-Anteil von `delta` 0, der Einsatz kommt zurück aufs Konto und wird beim nächsten Wurf erneut riskiert. Der Pass-Einsatz bleibt logisch auf dem Tisch (`this.bets.pass`), ökonomisch aber jede Runde neu abgezogen – so bleiben Zinsen/Meds pro Wurf korrekt.

Wenn der Spieler die Lobby verlässt, während ein Punkt läuft: `unmount` lässt `point`/`bets.pass` stehen; beim nächsten Mount wird weitergespielt. Bei Modus-Wechsel/Neustart (`gameover:restart`, `story:day`): `Bus.on('gameover:restart', () => { Craps.point = null; Craps.bets = { pass: 0, field: 0 }; Craps.history = []; MegaSlots.freeLeft = 0; })` ergänzen und dasselbe bei `Bus.on('story:day', …)` (der Tag endet, die Tische werden geräumt).

- [ ] **Step 3: Verifikation**

Run: `tests/dom-selftest.sh` → grün. Run: `tests/screenshot.sh /tmp/craps.png "?screen=royal&game=craps"`.
Manuell: Pass 50 legen → würfeln → bei Punkt: Pass-Button gesperrt, Field weiterhin belegbar; bei 7: „Seven out“, Pass geleert.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat(royal): Craps-Screen (Pass Line, Field, Punkt-Puck, Würfelanimation)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Screen Glücksrad

**Files:**
- Create: Template `tpl-wheel`, CSS `.wheel-*`, `Wheel` im Block `casino-royal`

**Interfaces:**
- Produces: `Bus.emit('wheel:result', { delta, bet, detail: { index, mult } })`; Trophäe `gegenDieWand`

- [ ] **Step 1: Template + CSS**

```html
<template id="tpl-wheel">
  <div class="panel wheel-panel">
    <div class="wheel-stage">
      <div class="wheel-pointer">▼</div>
      <div class="wheel" id="wheel"></div>
      <div class="wheel-hub">🎩</div>
    </div>
    <div class="chalk paytable">
      <h4>24 Felder</h4>
      <table>
        <tr><td>×10</td><td>1 Feld</td></tr><tr><td>×5</td><td>1 Feld</td></tr><tr><td>×2</td><td>1 Feld</td></tr>
        <tr><td>×1</td><td>3 Felder</td></tr><tr><td>Hälfte</td><td>5 Felder</td></tr><tr><td>Bankrott</td><td>13 Felder</td></tr>
      </table>
    </div>
    <div class="status" id="wheelStatus">Einsatz wählen und drehen</div>
    <div class="bet-bar">
      <input type="number" id="wheelBet" value="100" min="100" hidden>
      <button class="chip" data-chip="100" data-v="100">100</button>
      <button class="chip" data-chip="500" data-v="50">500</button>
      <button class="chip" data-chip="1000" data-v="25">1000</button>
      <button class="chip" data-chip="5000" data-v="max">5000</button>
      <button class="btn solid" id="btnWheel">Drehen</button>
      <button class="btn ghost sm" id="wheelBack">← Lobby</button>
    </div>
  </div>
</template>
```

```css
.wheel-panel { display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: center; }
.wheel-panel .status, .wheel-panel .bet-bar { grid-column: 1 / -1; }
.wheel-stage { position: relative; width: min(360px, 80vw); aspect-ratio: 1; margin: 0 auto; }
.wheel { position: absolute; inset: 0; border-radius: 50%; border: 8px solid var(--gold); box-shadow: var(--shadow), inset 0 0 30px rgba(0,0,0,.6); transition: transform 4.5s cubic-bezier(.15,.85,.25,1); }
.wheel.snap { transition: none; }
.wheel .seg { position: absolute; left: 50%; top: 50%; width: 50%; transform-origin: 0 50%; font-family: var(--font-mono); font-size: .8rem; color: #fff; text-align: right; padding-right: 12px; box-sizing: border-box; }
.wheel-pointer { position: absolute; left: 50%; top: -18px; transform: translateX(-50%); font-size: 1.6rem; color: var(--gold-2); z-index: 2; text-shadow: 0 0 8px var(--gold-2); }
.wheel-hub { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 64px; height: 64px; border-radius: 50%; background: #1a0a0d; border: 4px solid var(--gold); display: flex; align-items: center; justify-content: center; font-size: 1.6rem; z-index: 1; }
.wheel.hit { animation: hitGlow .6s ease 3; }
@media (max-width: 720px) { .wheel-panel { grid-template-columns: 1fr; } }
```

- [ ] **Step 2: `Wheel` implementieren**

```js
/* ---- Glücksrad ---- */
const Wheel = {
  root: null, spinning: false, gen: 0, turns: 0,
  COLORS: { 0: '#2a2a2e', 0.5: '#5a3a12', 1: '#1f8a4c', 2: '#1e6fb3', 5: '#b066ff', 10: '#b3261e' },
  label(m) { return m === 0 ? 'BANKROTT' : m === 0.5 ? 'HÄLFTE' : `×${m}`; },
  build() {
    const el = qs('#wheel', this.root); if (!el) return;
    const S = RoyalRules.WHEEL.SEGMENTS, n = S.length, step = 360 / n;
    el.style.background = `conic-gradient(${S.map((m, i) => `${this.COLORS[m]} ${i * step}deg ${(i + 1) * step}deg`).join(', ')})`;
    el.innerHTML = '';
    S.forEach((m, i) => el.append(h('div', { class: 'seg', style: `transform: rotate(${i * step + step / 2 - 90}deg)` }, this.label(m))));
  },
  /* Zeiger steht oben (−90°); Segment i liegt bei i*step … (i+1)*step im conic-gradient (0° = oben). Ziel: Segmentmitte unter dem Zeiger. */
  angleFor(index) { const step = 360 / RoyalRules.WHEEL.SEGMENTS.length; return -(index * step + step / 2); },
  async spin() {
    if (this.spinning || !this.root) return;
    const bet = Game.readBet('wheelBet');
    if (!RoyalRules.WHEEL.BETS.includes(bet)) { UI.toast({ icon: '🎡', title: 'Einsatz', text: 'Hier gilt 100, 500, 1.000 oder 5.000 €.', tone: 'loss' }); return; }
    if (!Game.beginSpin(bet)) return;
    const run = Game.run, gen = this.gen;
    this.spinning = true;
    try {
      qs('#btnWheel', this.root).disabled = true;
      let index = RoyalRules.wheelSpin(Math.random);
      index = RoyalRules.wheelLuckOverride(index, Rules.luck(State.s), Math.random);
      const el = qs('#wheel', this.root);
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      this.turns += reduced ? 1 : 5;
      el.classList.toggle('snap', reduced);
      el.style.transform = `rotate(${this.turns * 360 + this.angleFor(index)}deg)`;
      if (!reduced) { let n = 0; const t = setInterval(() => { if (!this.alive(gen) || ++n > 28) return clearInterval(t); SFX.play('click'); }, 150); }
      await wait(reduced ? 200 : 4600);
      if (!this.alive(gen)) return;
      const mult = RoyalRules.WHEEL.SEGMENTS[index];
      const delta = RoyalRules.wheelDelta(index, bet);
      el.classList.remove('hit'); void el.offsetWidth; if (mult >= 1) el.classList.add('hit');
      qs('#wheelStatus', this.root).innerHTML = mult === 0 ? `<span class="loss">BANKROTT · −${UI.fmt(bet)}</span>` : mult === 0.5 ? `<span class="loss">Hälfte zurück · −${UI.fmt(bet - RoyalRules.wheelPayout(index, bet))}</span>` : mult === 1 ? 'Einsatz zurück' : `<span class="win">×${mult} · +${UI.fmt(delta)}</span>`;
      if (mult === 0 && bet === 5000) Achievements.unlock('gegenDieWand');
      SFX.play(mult >= 2 ? 'cash' : mult === 0 ? 'lose' : 'reelStop');
      await Bus.emit('wheel:result', { delta, bet, detail: { index, mult } });
      await Game.settle(delta, { from: this.alive(gen) ? qs('.wheel-stage', this.root) : null, game: 'wheel', bet, run });
    } finally {
      if (this.gen === gen) { this.spinning = false; const b = qs('#btnWheel', this.root); if (b) b.disabled = false; }
    }
  },
  alive(gen) { return !!this.root && this.gen === gen; },
  onKey(e) { if (e.code === 'Space' && qs('#cutscene').hidden && !e.repeat) { e.preventDefault(); Wheel.spin(); } },
};
UI.register('wheel', {
  template: 'tpl-wheel',
  mount(root) {
    Wheel.gen++; Wheel.root = root; Wheel.turns = 0; Wheel.build();
    Game.bindBet(root, 'wheelBet');
    qs('#btnWheel', root).addEventListener('click', () => Wheel.spin());
    qs('#wheelBack', root).addEventListener('click', () => { SFX.play('click'); UI.show('royal'); });
    document.addEventListener('keydown', Wheel.onKey);
  },
  unmount() { Wheel.gen++; document.removeEventListener('keydown', Wheel.onKey); Wheel.root = null; Wheel.spinning = false; },
});
```

Die Zeiger-Geometrie **im Browser prüfen**: Nach einem Spin muss das Segment unter dem Zeiger dem `index` entsprechen (Konsole: `RoyalRules.WHEEL.SEGMENTS[index]` gegen die Beschriftung unter dem Zeiger). Falls um ein Segment versetzt: `angleFor` um `± step/2` korrigieren.

- [ ] **Step 3: Verifikation**

Run: `tests/dom-selftest.sh` → grün. Run: `tests/screenshot.sh /tmp/wheel.png "?screen=royal&game=wheel"` → Rad mit 24 Segmenten, Zeiger oben.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat(royal): Glücksrad-Screen (conic-gradient, Ausrollen, Klackern)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Story-Sperre der Royal-Spiele im Story-Modus, README, Screenshots, Gesamtverifikation

**Files:**
- Modify: Block `story-engine` (`decorateHub` – Türen der Royal-Lobby), `README.md`, `docs/superpowers/screenshots/` (neue Bilder)

- [ ] **Step 1: Story-Modus prüfen**

`?fresh&story=probe` → Stadt öffnen: Casino Royal erscheint nur, wenn die Story Raum `royal` freischaltet (Probe tut das nicht → kein Schaufenster). Für den Test in der Konsole: `Story.s.unlocked.rooms.push('royal'); State.s.car = 'audiA3'; State.save(); UI.show('stadt')` → Schaufenster da, Eintritt 100 €, `Story.s.stats.royalVisits` steigt, `Story.s.royalPaidDay` = Tag, zweiter Besuch am selben Tag kostenlos.

- [ ] **Step 2: README**

Abschnitt „Was drin ist“ – neuer Punkt nach „Stadt“:

```
- **Casino Royal:** am Ende der Straße, nur mit Auto (Parkservice). Eintritt 100 € – bis zum ersten Einzelgewinn ab 5.000 €, dann bist du Gast des Hauses. Drei Tische mit höheren Einsätzen: **Mega Seven** (5 Walzen, 5 Linien, Freispiele ×2), **Craps** (Pass Line und Field, jeder Wurf ein Spin) und das **Glücksrad** (24 Felder, ×10 bis Bankrott). Madame Sylvie sieht alles.
```

Dev-Parameter-Tabelle, `?screen=`-Zeile ergänzen: „… bei `royal` öffnet `&game=megaslots|craps|wheel` direkt einen Tisch“.

- [ ] **Step 3: Screenshots**

```bash
tests/screenshot.sh docs/superpowers/screenshots/royal-lobby.png "?screen=royal"
tests/screenshot.sh docs/superpowers/screenshots/royal-mega.png "?screen=royal&game=megaslots"
tests/screenshot.sh docs/superpowers/screenshots/royal-craps.png "?screen=royal&game=craps"
tests/screenshot.sh docs/superpowers/screenshots/royal-wheel.png "?screen=royal&game=wheel"
```

Jedes Bild ansehen (Read) und auf Layoutfehler prüfen (Überlappung, abgeschnittene Tabellen, Mobile-Breite: `tests/screenshot.sh` mit schmaler Breite, falls das Script das unterstützt – sonst im Browser DevTools).

- [ ] **Step 4: Gesamtverifikation**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen. Run: `tests/dom-selftest.sh` → grün. Run: `python3 tests/playtest-story.py` → Story 1 unverändert grün.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/screenshots/royal-*.png keller37.html
git commit -m "docs: Casino Royal im README, Screenshots

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec-Abdeckung (Abschnitt 7):** Zugang per Auto ✔ (Task 4), Zitter-Sperre generisch über `gates` ✔ (Task 4; die Story liefert Bedingung und Text), Eintritt 100 €/Story einmal pro Tag/Gast des Hauses ✔ (Task 4), Sylvie + `bg royal` ✔, freies Spiel ✔ (gleicher Weg), Mega Seven inkl. Freispiele/Nachtriggern/RTP-Test ✔ (Task 1, 5), Craps zwei Wetten/jeder Wurf ein Spin/Override ✔ (Task 2, 6), Glücksrad Segmente/Override/Reduced-Motion ✔ (Task 3, 7), Ergebnis-Events und drei Trophäen ✔ (Task 4–7), Rooms `royal` in `StoryRules.ROOMS` ✔, Dev-Parameter ✔ (Task 4, 8).

**Typ-Konsistenz:** `RoyalRules.canEnter(s)`, `entryFee(s)`, `megaWin(grid, bet, free)`, `crapsSettle(bets, point, dice)`, `wheelLuckOverride(index, luck, rng)`, `StoryRules.gate(story, s, screen)`, `Story.hook(at)` – in Tests und Screens identisch verwendet. Event-Payload überall `{ delta, bet, detail }`.

**Offene Prüfpunkte im Code (im Plan markiert):** `Game.run` ohne `beginSpin` bei Freispielen (Task 5), Zeiger-Geometrie des Rads (Task 7), Seitenleisten-Klick-Handler für `royal` (Task 4).
