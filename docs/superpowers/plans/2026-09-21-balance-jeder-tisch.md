# Balancing „Jeder Tisch ein Weg" – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jeder simulierte Tisch (Rot, Craps, Baccarat, Rad, Slots, Mega Seven) wird für den disziplinierten Spieler ein gangbarer Weg zum Story-Ziel (Story 1 ≥ 75 %, Story 2 ≥ 65 %), nüchtern leicht im Plus; Igors Duell zahlt 5:1.

**Architecture:** Alle Änderungen sind Konstanten und kleine Funktionen in den DOM-freien Regelblöcken (`<script id="rules">`, `<script id="royal-rules">`, `<script id="baccarat-rules">`) in `keller37.html`, plus Tafeln im Markup, Selftests im Block `selftest` und die Balance-Sim. Jede Aufgabe ändert einen Tisch, hält die Testsuite grün und wird einzeln committet; die Sim belegt am Ende die Zielwerte.

**Tech Stack:** Eine HTML-Datei (`keller37.html`, ~1 MB, Vanilla JS), Node ≥ 18 für `tests/run-selftest.mjs` und `tests/balance-sim.mjs` (Node liegt unter `~/.local/opt/node/bin` – `export PATH=~/.local/opt/node/bin:$PATH`), Chrome unter `~/.local/opt/chrome-linux64/chrome` für `tests/dom-selftest.sh`.

**Spec:** `docs/superpowers/specs/2026-09-21-balance-jeder-tisch-design.md`

## Global Constraints

- Nur `keller37.html`, `README.md`, `tests/balance-sim.mjs` anfassen. Kein neues Modul, keine neuen Dateien außer Screenshots.
- Regelblöcke bleiben DOM-frei (sie laufen unter Node im `vm`-Kontext ohne `document`).
- Jede Regelfunktion, die `rng` nimmt, bleibt deterministisch bei gegebener `rng`-Folge (Tests nutzen `seq(...)` und `seeded(n)`).
- Vor jedem Commit: `node tests/run-selftest.mjs` → `… bestanden, 0 fehlgeschlagen`.
- Kommentare im Stil des Codes: kurz, deutsch, mit „Balancing 2026-09-21 (Jeder Tisch)" dort, wo Zahlen geändert werden.
- Toleranzen laut Spec §4: ±3 Punkte Quote, ±5 Punkte Story gegenüber der Tabelle.
- Commit-Nachrichten enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

## Review Focus

1. **Pech bleibt Pech:** Zitter-Tag (`luckMod −15`) muss mit Grundglück netto −10 ergeben, die Kopfzeile „−10%" zeigen und die Pech-Zweige (`luck < 0`) weiter greifen – Test in Task 1.
2. **Freispiel-Rest aus altem Spielstand:** Ein gespeicherter Spielstand mit `freeLeft` bis 15 muss nach dem Deckel 9 weiter abspielbar sein (kein Absturz, kein Verfall) – `FREE_MAX` deckelt nur das Aufaddieren. Test in Task 6.
3. **Feld 22 am Rad:** Das 0,5-Feld an Index 22 hat kein Feld ≥ 1 in Reichweite 2; Glück darf es nicht verändern und nicht auf Index 0 (Bankrott) schieben – Test in Task 4.
4. **Zwei Kirschen zählen nur ab Walze 1:** `🔔 🍒 🍒` auf einer Linie zahlt nichts, `🍒 🍒 🔔` zahlt 2 – Test in Task 6.
5. **Hohe Einsätze:** `effectiveLuck` skaliert auch das Grundglück ab 1.000 € herunter (5 × 1000/bet); die Tafel „🍀 +5 %" bleibt, die Wirkung sinkt – Test in Task 1.

---

### Task 1: Grundglück +5 (`Rules.BASE_LUCK`)

**Files:**
- Modify: `keller37.html` – Block `rules` (`Rules.luck`, ca. Zeile 1795), Selftests ca. Zeile 10613–10625, DOM-Test ca. Zeile 13384
- Modify: `tests/balance-sim.mjs` (`disciplined`, `wild`, `rtpTable`-Aufrufe)

**Interfaces:**
- Produces: `Rules.BASE_LUCK` (Number, 5); `Rules.luck(s, mods)` liefert nüchtern `Rules.BASE_LUCK`.

- [ ] **Step 1: Bestehende luck-Tests auf das Grundglück umschreiben**

Suche im Block `selftest` den Test `T.test('luck: nichts aktiv = 0', …)` und die vier folgenden luck-Tests (Bier, Bier ohne Timer, Brownie, Story-Modifikator). Ersetze sie durch:

```js
T.test('luck: nichts aktiv = Grundglück 5 (Balancing 2026-09-21, Jeder Tisch)', () => { T.eq(Rules.BASE_LUCK, 5); T.eq(Rules.luck(base()), 5); });
T.test('luck: Bier addiert auf das Grundglück', () => {
  T.eq(Rules.luck(base({ beers: 1, beerTimer: 2 })), 15);
  T.eq(Rules.luck(base({ beers: 2, beerTimer: 1 })), 20);
  T.eq(Rules.luck(base({ beers: 3, beerTimer: 2 })), 25);
});
T.test('luck: Bier ohne Timer zählt nicht', () => T.eq(Rules.luck(base({ beers: 2, beerTimer: 0 })), 5));
T.test('luck: Brownie', () => {
  T.eq(Rules.luck(base({ brownieTimer: 1 })), 45);
  T.eq(Rules.luck(base({ beers: 3, beerTimer: 2, brownieTimer: 1 })), 65);
});
T.test('luck: Story-Modifikator – Zitter-Tag −15 ist netto Pech (−10), mit 3 Bier +10', () => {
  T.eq(Rules.luck(base({ story: { luckMod: -15 } })), -10);
  T.ok(Rules.luck(base({ story: { luckMod: -15 } })) < 0, 'Pech-Zweige greifen weiter');
  T.eq(Rules.luck(base({ beers: 3, beerTimer: 2, story: { luckMod: -15 } })), 10);
});
T.test('effectiveLuck skaliert auch das Grundglück ab LUCK_CAP herunter', () => {
  T.eq(Rules.effectiveLuck(Rules.BASE_LUCK, 1000), 5);
  T.eq(Rules.effectiveLuck(Rules.BASE_LUCK, 5000), 1);
});
```

(Die genauen Erwartungswerte der bisherigen Brownie-/Story-Tests: vorher 40 / 60 / 5 – jetzt jeweils +5.)

- [ ] **Step 2: Test laufen lassen – muss fehlschlagen**

Run: `export PATH=~/.local/opt/node/bin:$PATH && node tests/run-selftest.mjs 2>&1 | tail -8`
Expected: `FAIL luck: nichts aktiv = Grundglück 5 …` (und die anderen luck-Tests), Summe `… 5 fehlgeschlagen` o. ä.

- [ ] **Step 3: `Rules.BASE_LUCK` einführen**

Im Block `rules`, direkt vor `LUCK_CAP: 1000,`:

```js
  BASE_LUCK: 5,        // Grundglück nüchtern: jeder Tisch leicht im Plus (~102–105 %), Bier ist Turbo statt Pflicht (Balancing 2026-09-21, Jeder Tisch)
```

In `Rules.luck` die erste Zeile `let l = 0;` ersetzen durch `let l = Rules.BASE_LUCK;`.

Den Kommentarblock über `effectiveLuck` (beginnt mit `/* Glück ist ein echter, aber teurer Vorteil …`) ersetzen durch:

```js
  /* Glück ist ein echter, aber teurer Vorteil: voll bis LUCK_CAP, darüber im Verhältnis kleiner (Pech genauso).
     Balancing 2026-09-21 (Jeder Tisch): Grundglück BASE_LUCK hebt jeden Tisch nüchtern auf ~102–105 %, mit 3 Bier auf ~117–138 %
     (Rot 122, Craps 120, Mega 122, Baccarat 117, Rad 121, Slots 138 – Slots streuen am stärksten und brauchen den größten Vorteil).
     Ziel: der disziplinierte Spieler (tests/balance-sim.mjs) schafft die Story an jedem Tisch zu ≥ 75 % (Story 1) / ≥ 65 % (Story 2);
     wer alles setzt, fällt trotzdem. */
```

- [ ] **Step 4: DOM-Test für die Kopfzeile anpassen**

Suche im Block `selftest` die Zeile `T.eq(qs('#luck .luck-val').textContent, '+0%');` (ca. Zeile 13384) und ersetze `'+0%'` durch `'+5%'`. In derselben Testfunktion: `'+20%'` → `'+25%'` und `T.eq(qsa('#luck .seg.on').length, 3)` bleibt 3 (25 ≥ 20). Die Zeilen mit `'−15%'` (Zitter-Tag): prüfen, wie der Zustand aufgebaut ist – setzt der Test `luckMod: -15` ohne Bier, wird daraus `'−10%'` und `'Glück −10 %'`; passe beide Strings an.

- [ ] **Step 5: Node-Tests laufen lassen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `… bestanden, 0 fehlgeschlagen`

- [ ] **Step 6: Balance-Sim auf Grundglück umstellen**

In `tests/balance-sim.mjs`:

In `disciplined(rng, P)` die Zeile
`bal += games[P.game](bet, Rules.effectiveLuck(20, bet), rng); timer--;`
ersetzen durch
`bal += games[P.game](bet, Rules.effectiveLuck(Rules.BASE_LUCK + 20, bet), rng); timer--;`

In `wild(rng, P)` die Zeile mit `bal += games[P.game](bet, 0, rng);` ersetzen durch `bal += games[P.game](bet, Rules.effectiveLuck(Rules.BASE_LUCK, bet), rng);`.

`edgeAt20(game)` ersetzen durch den **Bier-Vorteil** (Quote mit 3 Bier minus Quote nüchtern, beides mit Grundglück):

```js
/* Vorteil von 3 Bier = Quote bei BASE_LUCK+20 minus Quote bei BASE_LUCK (in Einsätzen) */
function beerEdge(game) {
  const N = 100000; let with3 = 0, sober = 0;
  let rng = seeded(3); for (let i = 0; i < N; i++) with3 += games[game](100, Rules.BASE_LUCK + 20, rng);
  rng = seeded(3); for (let i = 0; i < N; i++) sober += games[game](100, Rules.BASE_LUCK, rng);
  return (with3 - sober) / N / 100;
}
```

und alle Aufrufe `edgeAt20('rouletteRot')` / `edgeAt20('slots')` durch `beerEdge(...)` ersetzen. Die Ausgabezeile `Vorteil bei +20 Glück: …` in `Vorteil von 3 Bier (Grundglück ${Rules.BASE_LUCK}): …` umbenennen.

In `rtpTable()` bleibt die Tabelle mit Glück 0 / 20 / 60 (sie zeigt die Rohquote je Glück; nüchtern = Spalte L0 + Grundglück wird in Task 7 als eigene Tabelle ergänzt).

- [ ] **Step 7: Sim laufen lassen (Sanity)**

Run: `node tests/balance-sim.mjs 2>&1 | tail -20`
Expected: läuft ohne Fehler durch; Story-1-Rot-Wert steigt gegenüber 76 % (Grundglück wirkt), Slots bleiben unter 30 %.

- [ ] **Step 8: DOM-Selftest**

Run: `sh tests/dom-selftest.sh`
Expected: `data-selftest="passed=N failed=0"`

- [ ] **Step 9: Commit**

```bash
git add keller37.html tests/balance-sim.mjs
git commit -m "balance: Grundglück +5 – nüchtern leicht im Plus, Bier ist Turbo statt Pflicht

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Craps – Glück gewinnt den Verlustwurf

**Files:**
- Modify: `keller37.html` – Block `royal-rules` (`RoyalRules.crapsLuckOverride`, ca. Zeile 7360; Konstante daneben), Selftests ca. Zeile 11339 (`crapsLuckOverride: verlierender Wurf wird verschoben …`)

**Interfaces:**
- Produces: `RoyalRules.CRAPS_WIN_SHARE` (Number, 0.3); `RoyalRules.crapsLuckOverride(dice, point, hasPass, luck, rng, hasField)` unverändert in Signatur.

- [ ] **Step 1: Failing Tests schreiben**

Direkt vor dem Test `T.test('crapsLuckOverride: Pech würfelt einen Gewinn neu …')` einfügen:

```js
T.test('crapsLuckOverride: Glück macht mit CRAPS_WIN_SHARE der Glückschance aus dem Verlustwurf einen Gewinnwurf (Balancing 2026-09-21, Jeder Tisch)', () => {
  T.eq(RoyalRules.CRAPS_WIN_SHARE, 0.3);
  /* Punktphase, Punkt 6, Wurf 3+4 = 7 verliert. luck 100 → Gewinnchance 30 %: rng 0.2 < 0.3 → Summe 6, erstes Paar [1, 5] */
  T.eq(RoyalRules.crapsLuckOverride([3, 4], 6, true, 100, seq(0.2)), [1, 5], 'Verlustwurf → Punkt getroffen');
  /* rng 0.4 ≥ 0.3 → kein Gewinnwurf; dann wie bisher: rng 0 < luck → Schub um ±1 auf einen nicht verlierenden Wurf */
  const o = RoyalRules.crapsLuckOverride([3, 4], 6, true, 100, seq(0.4, 0));
  T.ok(o[0] + o[1] !== 7 && Math.abs(o[0] - 3) + Math.abs(o[1] - 4) === 1, 'Fallback: Schub wie bisher');
  /* Come-out: 1+2 = 3 verliert; rng 0.1 < 0.3 → Gewinnwurf, zweites rng 0.7 ≥ 0.5 → 11 = [5, 6] */
  T.eq(RoyalRules.crapsLuckOverride([1, 2], null, true, 100, seq(0.1, 0.7)), [5, 6], 'Come-out → 11');
  T.eq(RoyalRules.crapsLuckOverride([1, 2], null, true, 100, seq(0.1, 0.2)), [1, 6], 'Come-out → 7 (rng < 0.5)');
  T.eq(RoyalRules.crapsLuckOverride([4, 4], 8, true, 100, seq(0)), [4, 4], 'Gewinner bleibt');
  T.eq(RoyalRules.crapsLuckOverride([1, 2], null, false, 100, seq(0)), [1, 2], 'ohne Pass-Einsatz nichts');
  /* luck 20 (kein Bier, nur Grundglück ×4): Gewinnchance 6 %: rng 0.05 → Gewinn, rng 0.07 → kein Gewinn, Schub-Zweig prüft dann rng 0.5 ≥ 0.2 → bleibt */
  T.eq(RoyalRules.crapsLuckOverride([3, 4], 6, true, 20, seq(0.05)), [1, 5]);
  T.eq(RoyalRules.crapsLuckOverride([3, 4], 6, true, 20, seq(0.07, 0.5)), [3, 4]);
});
```

- [ ] **Step 2: Test laufen lassen – muss fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -A2 "CRAPS_WIN_SHARE" | head -5`
Expected: `FAIL crapsLuckOverride: Glück macht … : expected 0.3, got undefined` (o. ä.)

- [ ] **Step 3: Implementieren**

Im Block `royal-rules` direkt über `crapsLuckOverride(` einfügen:

```js
  CRAPS_WIN_SHARE: 0.3, // Anteil der Glückschance, mit dem ein Verlustwurf zum Gewinnwurf wird (Balancing 2026-09-21, Jeder Tisch: Craps 88/81 % Story statt 22/19)
```

`crapsLuckOverride` so ändern, dass der Glück-Zweig (nach `if (!hasPass) return dice;` und der `losing`-Definition) lautet:

```js
    if (!losing(dice)) return dice;
    /* Erst die Gewinnchance (CRAPS_WIN_SHARE × luck): 7/11 im Come-out, sonst der Punkt – Paar [a, want − a] mit dem kleinsten a */
    if (rng() * 100 < luck * RoyalRules.CRAPS_WIN_SHARE) {
      const want = point != null ? point : (rng() < 0.5 ? 7 : 11);
      for (let a = 1; a <= 6; a++) { const b = want - a; if (b >= 1 && b <= 6) return [a, b]; }
    }
    /* sonst wie bisher: mit luck % ein Würfel um ±1 auf einen nicht verlierenden Wurf */
    if (!(rng() * 100 < luck)) return dice;
    for (const [i, dir] of [[0, 1], [0, -1], [1, 1], [1, -1]]) {
      const d = dice.slice(); d[i] += dir;
      if (d[i] >= 1 && d[i] <= 6 && !losing(d)) return d;
    }
    return dice;
```

- [ ] **Step 4: Bestehenden Craps-Test anpassen**

Der bestehende Test `crapsLuckOverride: verlierender Wurf wird verschoben, Gewinner nie` ruft mit `seq(0)` auf – `rng 0` löst jetzt zuerst den Gewinnwurf aus. Ändere dort jeden Aufruf mit Glück 100 auf `seq(0.5, 0)` (erster Wert 0.5 ≥ 0.3 → kein Gewinnwurf, zweiter Wert 0 → Schub). Konkret: `[3, 4], 8, true, 100, seq(0)` → `seq(0.5, 0)`; `[1, 2], null, true, 100, seq(0)` → `seq(0.5, 0)`; `[1, 1], null, true, 100, seq(0)` → `seq(0.5, 0)`; `[4, 4], 8, …` und `[6, 6], 6, …` bleiben (Gewinner/neutral rufen `rng` nicht auf).

- [ ] **Step 5: Tests laufen lassen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `… 0 fehlgeschlagen`

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "balance(craps): Glück gewinnt den Verlustwurf mit 30 % der Glückschance – Story 88/81 % statt 22/19

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Baccarat – bis zu drei neue Hände

**Files:**
- Modify: `keller37.html` – Block `baccarat-rules` (`BaccaratRules.luckOverride`, letzte Funktion des Blocks), Selftest ca. Zeile 12223 (`BaccaratRules.luckOverride: Pech würfelt Gewinn einmal neu …`)

**Interfaces:**
- Produces: `BaccaratRules.LUCK_REDEALS` (Number, 3); `BaccaratRules.luckOverride(hand, bets, luck, rng)` unverändert in Signatur.

- [ ] **Step 1: Failing Test schreiben**

Direkt nach dem bestehenden Test `BaccaratRules.luckOverride: Pech würfelt …` einfügen:

```js
T.test('BaccaratRules.luckOverride: Glück gibt bei Verlust bis zu LUCK_REDEALS-mal neu, bis die Hand nicht verliert (Balancing 2026-09-21, Jeder Tisch)', () => {
  const R = BaccaratRules; T.eq(R.LUCK_REDEALS, 3);
  const bets = { player: 1000 }, lost = { winner: 'banker' };
  const keep = R.deal;
  try {
    /* Stub: die ersten zwei neuen Hände verlieren, die dritte gewinnt */
    let n = 0; R.deal = () => (++n < 3 ? { winner: 'banker', n } : { winner: 'player', n });
    T.eq(R.luckOverride(lost, bets, 100, seq(0)), { winner: 'player', n: 3 }, 'dritte Hand gewinnt → drei Deals');
    n = 0; R.deal = () => ({ winner: 'banker', n: ++n });
    T.eq(R.luckOverride(lost, bets, 100, seq(0)), { winner: 'banker', n: 3 }, 'alle drei verlieren → die letzte bleibt, kein vierter Deal');
    n = 0; R.deal = () => ({ winner: 'tie', n: ++n });
    T.eq(R.luckOverride(lost, bets, 100, seq(0)), { winner: 'tie', n: 1 }, 'Push zählt als nicht verloren → ein Deal');
    n = 0; R.deal = () => ({ winner: 'player', n: ++n });
    T.eq(R.luckOverride(lost, bets, 30, seq(0.5)), lost, 'rng 0.5 ≥ 0.3 → kein Deal'); T.eq(n, 0);
  } finally { R.deal = keep; }
});
```

- [ ] **Step 2: Test laufen lassen – muss fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep "LUCK_REDEALS" | head -3`
Expected: `FAIL … expected 3, got undefined`

- [ ] **Step 3: Implementieren**

Im Block `baccarat-rules` direkt über `luckOverride(hand, bets, luck, rng) {` einfügen:

```js
  LUCK_REDEALS: 3, // Glück gibt eine verlorene Hand bis zu so oft neu (vorher 1×; Balancing 2026-09-21, Jeder Tisch: Story 82/75 % statt 13/11)
```

`luckOverride` ersetzen durch:

```js
  luckOverride(hand, bets, luck, rng) {
    let delta = BaccaratRules.settle(bets, hand);
    if (luck < 0) return delta > 0 && Rules.pech(luck, rng) ? BaccaratRules.deal(rng) : hand;
    if (!(luck > 0 && delta < 0 && rng() * 100 < luck)) return hand;
    let h = hand;
    for (let i = 0; i < BaccaratRules.LUCK_REDEALS && delta < 0; i++) { h = BaccaratRules.deal(rng); delta = BaccaratRules.settle(bets, h); }
    return h;
  },
```

- [ ] **Step 4: Bestehenden Test umbenennen und laufen lassen**

Den Titel des bestehenden Tests `BaccaratRules.luckOverride: Pech würfelt Gewinn einmal neu, Glück gibt Verlust einmal neu, sonst unverändert` ändern in `… Glück gibt Verlust neu (Details im nächsten Test), sonst unverändert`. Die Assertions dort bleiben gültig (die neue Hand mit `bacCard(3), bacCard(1), bacCard(4), bacCard(2)` ist eine echte Hand; ob sie verliert, ändert am `T.ok(rg !== lost && rg.player)` nichts – falls die Hand verliert, folgt ein zweiter Deal mit den zyklischen `seq`-Werten, `rg.player` bleibt gesetzt).

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `… 0 fehlgeschlagen`

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "balance(baccarat): Glück gibt eine verlorene Hand bis zu dreimal neu – Story 82/75 % statt 13/11

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Glücksrad – neue Felder, Glück hebt aufs nächste Feld ≥ 1

**Files:**
- Modify: `keller37.html` – Block `royal-rules` (`RoyalRules.WHEEL.SEGMENTS` ca. Zeile 7230, `WHEEL_COLORS`, `wheelTone`, `wheelLuckOverride`), CSS ca. Zeile 1076 (`.wheel .seg.x10, .wheel .seg.x5`), Tafel im Template `tpl-wheel` ca. Zeile 1741–1746, Selftests ca. Zeile 10793 (`'Rad 97,9 % ohne Glück'`), 11361 (`wheelTone`), 11365 (`WHEEL: 24 Segmente …`), `wheelLuckOverride`-Tests (grep `wheelLuckOverride` im Block `selftest`)
- Modify: `README.md` – Absatz Casino Royal (Glücksrad-Felder)

**Interfaces:**
- Produces: `RoyalRules.WHEEL.SEGMENTS` (24 Zahlen, Summe 24); `RoyalRules.WHEEL_COLORS` mit Schlüsseln `0, 0.5, 1, 2, 3, 5`; `RoyalRules.wheelTone(3) === 'x3'`.

- [ ] **Step 1: Failing Tests schreiben**

Den bestehenden Test `WHEEL: 24 Segmente, Verteilung, Erwartungswert 97,9 %` komplett ersetzen durch:

```js
T.test('WHEEL: 24 Felder ×5 ×3 ×2 ×2 · 8× Einsatz zurück · 8× Hälfte · 4× Bankrott = 100 % (Balancing 2026-09-21, Jeder Tisch)', () => {
  const S = RoyalRules.WHEEL.SEGMENTS;
  T.eq(S, [0, 5, 0.5, 1, 0.5, 2, 0, 1, 1, 1, 0.5, 3, 0, 1, 0.5, 1, 0.5, 2, 0, 1, 0.5, 1, 0.5, 0.5], 'Reihenfolge ist balancerelevant (Reichweite 2 des Glücks)');
  const count = (v) => S.filter((x) => x === v).length;
  T.eq([count(0), count(0.5), count(1), count(2), count(3), count(5), count(10)], [4, 8, 8, 2, 1, 1, 0]);
  T.eq(S.reduce((a, b) => a + b, 0), 24, 'Summe 24 → 100 % ohne Glück');
  /* Glück: jedes Feld < 1 außer Index 22 erreicht binnen 2 Schritten ein Feld ≥ 1 */
  S.forEach((v, i) => { if (v < 1 && i !== 22) T.ok(S[(i + 1) % 24] >= 1 || S[(i + 2) % 24] >= 1, `Feld ${i} (${v}) hat binnen 2 Schritten ein Feld ≥ 1`); });
  T.ok(S[23] < 1 && S[0] < 1, 'Index 22 ist die dokumentierte Ausnahme');
});
T.test('wheelLuckOverride: Glück hebt ein Feld < 1 aufs nächste Feld ≥ 1 (bis 2 weiter), Pech drückt ein Feld > 0 auf einen Bankrott in Reichweite', () => {
  const S = RoyalRules.WHEEL.SEGMENTS;
  T.eq(RoyalRules.wheelLuckOverride(2, 100, seq(0)), 3, '0,5 an 2 → ×1 an 3');
  T.eq(RoyalRules.wheelLuckOverride(0, 100, seq(0)), 1, 'Bankrott an 0 → ×5 an 1');
  T.eq(RoyalRules.wheelLuckOverride(10, 100, seq(0)), 11, '0,5 an 10 → ×3 an 11');
  T.eq(RoyalRules.wheelLuckOverride(4, 100, seq(0)), 5, '0,5 an 4 → ×2 an 5');
  T.eq(RoyalRules.wheelLuckOverride(22, 100, seq(0)), 22, 'Index 22: kein Feld ≥ 1 in Reichweite → bleibt (nicht auf den Bankrott an 0)');
  T.eq(RoyalRules.wheelLuckOverride(3, 100, seq(0)), 3, 'Feld ≥ 1 bleibt');
  T.eq(RoyalRules.wheelLuckOverride(2, 30, seq(0.5)), 2, 'rng 0.5 ≥ 0.3 → bleibt');
  T.eq(RoyalRules.wheelLuckOverride(2, 0, seq(0)), 2, 'ohne Glück');
  /* Pech wie bisher */
  T.eq(RoyalRules.wheelLuckOverride(5, -100, seq(0)), 6, '×2 an 5 → Bankrott an 6');
  T.eq(RoyalRules.wheelLuckOverride(3, -100, seq(0)), 3, '×1 an 3: kein Bankrott in Reichweite 2 (4, 5) → bleibt');
  T.eq(RoyalRules.wheelLuckOverride(0, -100, seq(0)), 0, 'Bankrott bleibt Bankrott');
  T.ok(S[6] === 0 && S[4] !== 0 && S[5] !== 0, 'Voraussetzungen der Pech-Fälle');
});
```

Im Test `RoyalRules.wheelTone: Segmentklasse je Multiplikator`: `[10, 5, 2, 1, 0.5, 0].map(…)` → `[5, 3, 2, 1, 0.5, 0].map(…)` mit Erwartung `['x5', 'x3', 'x2', 'x1', 'half', 'bust']`; `Object.keys(RoyalRules.WHEEL_COLORS).sort()` → `['0', '0.5', '1', '2', '3', '5']`.

Im Test `Glücks-Ökonomie: …` (ca. Zeile 10793) die Zeile `T.ok(Math.abs(RoyalRules.WHEEL.SEGMENTS.reduce(…) / 24 - 23.5 / 24) < 1e-9, 'Rad 97,9 % ohne Glück');` ersetzen durch `T.eq(RoyalRules.WHEEL.SEGMENTS.reduce((a, b) => a + b, 0), 24, 'Rad 100 % ohne Glück');`.

Falls ein weiterer bestehender `wheelLuckOverride`-Test existiert (grep `T.test('wheelLuckOverride` / `wheelLuckOverride(`): löschen, der neue oben ersetzt ihn.

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep "FAIL" | grep -i "wheel\|Rad" | head`
Expected: mindestens `FAIL WHEEL: 24 Felder …` und `FAIL wheelLuckOverride: …`

- [ ] **Step 3: Regeln ändern**

In `RoyalRules.WHEEL`:

```js
    SEGMENTS: [0, 5, 0.5, 1, 0.5, 2, 0, 1, 1, 1, 0.5, 3, 0, 1, 0.5, 1, 0.5, 2, 0, 1, 0.5, 1, 0.5, 0.5], // ×5 ×3 ×2 ×2 · 8× Einsatz zurück · 8× Hälfte · 4× Bankrott = 24 → 100 %; Reihenfolge balancerelevant (Balancing 2026-09-21, Jeder Tisch: Story 81/74 % statt 21/17; vorher ×10/×5/×2, 13× Hälfte, 8× Bankrott)
```

`WHEEL_COLORS`: Schlüssel `10` entfernen, `3: '#c9a961'` ergänzen (das bisherige ×10-Gold), also `{ 5: '#f1dfa8', 3: '#c9a961', 2: '#1d6b4a', 1: '#2a262e', 0.5: '#5a1a24', 0: '#141216' }`.

Den Kommentar über `wheelLuckOverride` (beginnt `/* ---- Glücksrad: 24 Segmente …`) auf die neue Verteilung umschreiben: `Summe 24 → 100 % ohne Glück. Balancing 2026-09-21 (Jeder Tisch): ×5 ×3 ×2 ×2, 8× Einsatz zurück, 8× Hälfte, 4× Bankrott; Glück hebt ein Feld < 1 aufs nächste Feld ≥ 1 (bis 2 weiter).`

`wheelLuckOverride` – den Glück-Zweig ändern:

```js
    if (S[index] >= 1 || !(rng() * 100 < luck)) return index;
    for (let k = 1; k <= 2; k++) { const j = (index + k) % S.length; if (S[j] >= 1) return j; }
    return index;
```

(Pech-Zweig unverändert.)

- [ ] **Step 4: CSS und Tafel**

CSS ca. Zeile 1076: `.wheel .seg.x10, .wheel .seg.x5 { color: #141216; }` → `.wheel .seg.x5, .wheel .seg.x3 { color: #141216; }`.

Tafel im Template (Zeilen mit `<tr><td>×10</td>…`):

```html
        <tr><td>×5</td><td>1 Feld</td></tr><tr><td>×3</td><td>1 Feld</td></tr><tr><td>×2</td><td>2 Felder</td></tr>
        <tr><td>Einsatz zurück</td><td>8 Felder</td></tr><tr><td>Hälfte</td><td>8 Felder</td></tr><tr><td>Bankrott</td><td>4 Felder</td></tr>
```

- [ ] **Step 5: Tests laufen lassen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `… 0 fehlgeschlagen`

- [ ] **Step 6: README**

In `README.md` den Klammertext `(24 Felder: ×10, ×5, ×2, 13× Hälfte zurück, 8× Bankrott – ~98 %, wie Roulette Rot, nur streuender)` ersetzen durch `(24 Felder: ×5, ×3, 2× ×2, 8× Einsatz zurück, 8× Hälfte, 4× Bankrott – 100 % ohne Glück; Glück hebt ein schlechtes Feld aufs nächste gute)`.

- [ ] **Step 7: Screenshot und Commit**

Run: `sh tests/screenshot.sh /tmp/claude-1000/wheel.png "?screen=royal&game=wheel"` und das Bild ansehen: Rad zeigt ×5/×3/×2-Felder mit dunkler Schrift, Tafel mit sechs Zeilen.

```bash
git add keller37.html README.md
git commit -m "balance(rad): ×5 ×3 ×2 ×2, 8× Einsatz zurück, 4× Bankrott; Glück hebt aufs nächste Feld ≥ 1 – Story 81/74 % statt 21/17

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Slots – Paar 1,4×, Drillinge 5/10/19/40, Glücks-Drilling 60 %

**Files:**
- Modify: `keller37.html` – Block `rules` (`SLOT_LUCK_TRIPLE` ca. Zeile 1914, `slotMultiplier` ca. Zeile 1927, Kommentar davor), Block `perk-rules` (`NEUTRAL_MODS.slotPairMult` ca. Zeile 2181, Skill `zockerhaende` ca. Zeile 2203), Template `tpl-slots` Tafel ca. Zeile 1307–1311, Selftests ca. Zeile 10764–10775 (SLOT_LUCK_TRIPLE, Slots-Korridor), 10808–10815 (`slotMultiplier`), 14693 (Zockerhände mods), 14886/14890–14900 (Slots-EV)
- Modify: `README.md` – Skill-Tabelle Zockerhände, Absatz Bier/Drilling

**Interfaces:**
- Produces: `Rules.SLOT_LUCK_TRIPLE = 0.6`; `Rules.slotMultiplier(a, b, c, mods)` Drillinge 5/10/19/40; `Rules.NEUTRAL_MODS.slotPairMult = 1.4`; Zockerhände `slotPairMult: 1.5`.

- [ ] **Step 1: Bestehende Tests auf die neuen Werte umschreiben (sie werden dadurch zu Failing Tests)**

Im Test mit `T.eq(Rules.SLOT_LUCK_TRIPLE, 0.12);` (ca. Zeile 10764): `0.12` → `0.6`; die zwei Zeilen danach: `seq(0.1, 0.11)` → `seq(0.1, 0.59)` mit Kommentar `'rng 0.59 < 0.6 → Kirsch-Drilling'`, `seq(0.1, 0.12)` → `seq(0.1, 0.6)` mit `'rng 0.6 ≥ 0.6 → nur Paar'`.

Im Test `Glücks-Ökonomie …` die Slots-Zeile: `T.ok(slots > 111 && slots < 120, …)` → `T.ok(slots > 125 && slots < 133, \`Slots bei +20 Glück: RTP ${slots.toFixed(1)} % (erwartet 125–133; Slots streuen 3× so stark wie Rot und brauchen den größten Bier-Vorteil)\`);`

Test `slotMultiplier` (ca. Zeile 10808): `'💎' → 19`, `'🔔' → 10`, `'🍒' → 5`, Paare `1.2` → `1.4` (drei Zeilen), `'7️⃣'` bleibt 40.

Zeile 14693 `T.eq(m.slotPairMult, 1.3);` → `1.5`.

Zeile 14886 `T.eq(Rules.slotMultiplier('🍒', '🍒', '🍒', M({ slotPairMult: 0 })), 6, 'Drilling unberührt');` → `5`.

Test `Slots: Erwartungswert neutral ~97,7 %, Zockerhände 1,3× …` ersetzen durch:

```js
T.test('Slots: Erwartungswert neutral 210/216 = 97,2 %, Zockerhände 1,5× ~101 % (Balancing 2026-09-21, Jeder Tisch)', () => {
  const evFor = (mods) => {
    let sum = 0, n = 0;
    for (const a of Rules.SYMBOLS) for (const b of Rules.SYMBOLS) for (const c of Rules.SYMBOLS) { sum += Rules.slotMultiplier(a, b, c, mods); n++; }
    return { sum, n, avg: sum / n };
  };
  const zocker = evFor(M({ slotPairMult: 1.5 }));
  T.eq(zocker.n, 216, 'alle Walzen-Kombinationen');
  T.ok(zocker.avg > 1 && zocker.avg < 1.03, `Zockerhände 1,5× ist nüchtern leicht +EV, ~101 % (avg=${zocker.avg}) – der Perk kostet dafür 2 % Bank-Zinsen`);
  const neutral = evFor(Rules.NEUTRAL_MODS);
  T.ok(Math.abs(neutral.avg - 210 / 216) < 1e-9, `neutral 210/216 = 97,2 % ohne Glück (avg=${neutral.avg}); mit Grundglück ~105 %`);
});
```

(Rechnung: Drillinge 3×5 + 10 + 19 + 40 = 84; Paare 6 Symbole × 15 Kombinationen × 1,4 = 126; Summe 210. Zockerhände: 84 + 90 × 1,5 = 219 → 101,4 %.)

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep FAIL | grep -i "slot\|Zocker" | head`
Expected: `FAIL slotMultiplier …`, `FAIL Slots: Erwartungswert …`, `FAIL … SLOT_LUCK_TRIPLE …`

- [ ] **Step 3: Regeln ändern**

Block `rules`:
- `SLOT_LUCK_TRIPLE: 0.12,` → `SLOT_LUCK_TRIPLE: 0.6, // Glück: ein erzwungenes Paar aus 🍒🍋🍇 wird so oft zum Drilling (Balancing 2026-09-21, Jeder Tisch: 0,6 statt 0,12 – Slots streuen stark, Bier muss dort mehr bringen)`
- Kommentar über `slotMultiplier`: `/* Drillinge 5/10/19/40 + Paar 1,4× → 210/216 = 97,2 % ohne Glück, ~105 % mit Grundglück (Balancing 2026-09-21, Jeder Tisch; vorher 6/20/25/40 + 1,2× = 97,7 %: flachere Drillinge, öfter Paar – Story 80/70 % statt 16/13) */`
- `slotMultiplier`: `return a === '7️⃣' ? 40 : a === '💎' ? 19 : a === '🔔' ? 10 : 5;`

Block `perk-rules`:
- `NEUTRAL_MODS`: `slotPairMult: 1.2,` → `slotPairMult: 1.4,`
- Skill `zockerhaende`: `light: 'Slots: Paar zahlt 1,5×'`, `mods: { slotPairMult: 1.5, bankRateAdd: 0.02 }`

Template `tpl-slots` Tafel:

```html
          <tr><td>7️⃣ 7️⃣ 7️⃣</td><td>40×</td></tr>
          <tr><td>💎 💎 💎</td><td>19×</td></tr>
          <tr><td>🔔 🔔 🔔</td><td>10×</td></tr>
          <tr><td>Drilling</td><td>5×</td></tr>
          <tr><td>Paar</td><td id="payPair">1,4×</td></tr>
```

(`#payPair` wird zur Laufzeit aus `mods.slotPairMult` gesetzt – der Startwert im Markup ist nur die Anzeige vor dem ersten Render.)

- [ ] **Step 4: Tests laufen lassen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `… 0 fehlgeschlagen`. Falls der Slots-Korridor (125–133) knapp verfehlt wird: Wert mit `node tests/balance-sim.mjs --rtp` prüfen (Zeile `slots`, Spalte L20) und den Korridor um den gemessenen Wert ±4 legen – nicht die Regel ändern.

- [ ] **Step 5: README**

- Skill-Tabelle: `| 🎰 Zockerhände | Slots: Paar zahlt 1,3× | Bank-Zinsen +2 % |` → `1,5×`.
- Im Absatz „Leben": `(Slots: Glück erzwingt ein Paar, aus 🍒🍋🍇 wird es zu 12 % ein Drilling)` → `zu 60 %`. Der Rest des Quoten-Satzes wird in Task 7 neu geschrieben.

- [ ] **Step 6: Commit**

```bash
git add keller37.html README.md
git commit -m "balance(slots): Paar 1,4×, Drillinge 5/10/19/40, Glücks-Paar wird zu 60 % Drilling – Story 80/70 % statt 16/13

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Mega Seven abflachen

**Files:**
- Modify: `keller37.html` – Block `royal-rules` (`RoyalRules.MEGA` ca. Zeile 7240: `WEIGHTS`, `PAY`, `FREE_SPINS/FREE_MULT/FREE_MAX`; `megaLineWins` ca. 7266; `megaLuckOverride` ca. 7295), Template `tpl-megaslots` Tafel ca. Zeile 1652–1662, Statustext ca. Zeile 4558 (`(Freispiel ×2)`), Selftests: `megaLuckOverride`-Tests ca. Zeile 11257–11280, `Mega Seven: RTP-Korridor` ca. 11282, Mega-Zeile im Test `Glücks-Ökonomie` ca. 10787, `megaLineWins`-Tests (grep `megaLineWins` im Block `selftest`)
- Modify: `README.md` – Mega-Seven-Text im Absatz Casino Royal

**Interfaces:**
- Produces: `RoyalRules.MEGA.PAY['🍒'] = [0, 0, 2, 5, 8, 12]` usw.; `RoyalRules.MEGA.LUCK_GAIN = 1.5`, `RoyalRules.MEGA.LUCK_REROLLS = 3`; `megaLineWins(grid)` zählt ab `PAY[sym][count] > 0`; `megaLuckOverride(grid, luck, rng)` dreht bei Niete neu.

- [ ] **Step 1: Failing Tests schreiben**

Den bestehenden Test `megaLuckOverride: kein Glück / Pech-Wurf / kleinster Ein-Schritt-Gewinn / bestehender Gewinn` ersetzen durch:

```js
T.test('megaLuckOverride: Glück dreht bei Niete mit LUCK_GAIN × luck bis zu LUCK_REROLLS-mal neu, bis eine Linie zahlt (Balancing 2026-09-21, Jeder Tisch)', () => {
  const M = RoyalRules.MEGA; T.eq([M.LUCK_GAIN, M.LUCK_REROLLS], [1.5, 3]);
  const niete = G(['🔔 7️⃣ 💎', '7️⃣ BAR 💎', '💎 7️⃣ 🔔', '🔔 7️⃣ BAR', 'BAR 7️⃣ 💎']);
  const win = G(['🍒 🍒 🍒', '🍒 🍒 🍒', '🍒 🍒 🍒', '🔔 🔔 🔔', '🔔 🔔 🔔']);
  T.eq(RoyalRules.megaLineWins(niete), [], 'Ausgangsgitter gewinnt nichts');
  T.eq(RoyalRules.megaLuckOverride(niete, 0, seq(0.5)), niete, 'ohne Glück unverändert');
  T.eq(RoyalRules.megaLuckOverride(win, 100, seq(0)), win, 'bestehender Gewinn bleibt');
  T.eq(RoyalRules.megaLuckOverride(niete, 20, seq(0.31)), niete, 'luck 20 × 1,5 = 30 %: rng 0.31 → bleibt');
  const keep = RoyalRules.megaRoll;
  try {
    let n = 0; RoyalRules.megaRoll = () => (++n < 3 ? niete : win);
    T.eq(RoyalRules.megaLuckOverride(niete, 20, seq(0.29)), win, 'rng 0.29 < 0.30 → neu drehen; dritter Wurf trifft'); T.eq(n, 3);
    n = 0; RoyalRules.megaRoll = () => { n++; return niete; };
    T.eq(RoyalRules.megaLuckOverride(niete, 100, seq(0)), niete, 'drei Nieten → letzte Niete, kein vierter Wurf'); T.eq(n, 3);
    n = 0; RoyalRules.megaRoll = () => { n++; return win; };
    T.eq(RoyalRules.megaLuckOverride(niete, 100, seq(0)), win, 'erster neuer Wurf trifft → ein Wurf'); T.eq(n, 1);
  } finally { RoyalRules.megaRoll = keep; }
});
```

Der bestehende Test `megaLuckOverride: Pech würfelt ein gewinnendes Gitter neu, Niete bleibt` bleibt unverändert.

Direkt vor `T.test('Mega Seven: RTP-Korridor …')` einfügen:

```js
T.test('MEGA: flache Tafel, Kirschen ab 2, Freispiele 3×1 (Balancing 2026-09-21, Jeder Tisch)', () => {
  const M = RoyalRules.MEGA;
  T.eq(M.WEIGHTS, [36, 18, 14, 6, 4, 3]);
  T.eq(M.PAY, { '🍒': [0, 0, 2, 5, 8, 12], '🔔': [0, 0, 0, 5, 10, 20], BAR: [0, 0, 0, 6, 12, 25], '💎': [0, 0, 0, 8, 20, 50], '7️⃣': [0, 0, 0, 10, 30, 100] });
  T.eq([M.FREE_SPINS, M.FREE_MULT, M.FREE_MAX], [3, 1, 9]);
  /* zwei Kirschen ab Walze 1 zahlen (Mittellinie = Reihe 1), zwei Glocken nicht, Kirschen ab Walze 2 nicht */
  const row = (a, b, c, d, e) => G([`x ${a} x`, `x ${b} x`, `x ${c} x`, `x ${d} x`, `x ${e} x`]);
  T.eq(RoyalRules.megaLineWins(row('🍒', '🍒', '🔔', 'BAR', '💎')).filter((w) => w.line === 0), [{ line: 0, sym: '🍒', count: 2, mult: 2 }], '🍒🍒 → 2');
  T.eq(RoyalRules.megaLineWins(row('🔔', '🔔', '🍒', 'BAR', '💎')).filter((w) => w.line === 0), [], '🔔🔔 zahlt nichts');
  T.eq(RoyalRules.megaLineWins(row('🔔', '🍒', '🍒', 'BAR', '💎')).filter((w) => w.line === 0), [], 'Kirschen erst ab Walze 2 zählen nicht');
  T.eq(RoyalRules.megaLineWins(row('🍒', '🍒', '🍒', 'BAR', '💎')).filter((w) => w.line === 0), [{ line: 0, sym: '🍒', count: 3, mult: 5 }], '🍒🍒🍒 → 5');
  /* Auszahlung: Linieneinsatz = Einsatz/5; 2 Kirschen auf einer Linie bei 500 € = 200 € */
  T.eq(RoyalRules.megaWin(row('🍒', '🍒', '🔔', 'BAR', '💎'), 500, false).payout, 200);
  T.eq(RoyalRules.megaWin(row('🍒', '🍒', '🔔', 'BAR', '💎'), 500, true).payout, 200, 'Freispiel ohne Verdopplung');
  /* Freispiele: Deckel 9 beim Aufaddieren; ein alter Rest > 9 wird nur nicht weiter erhöht */
  T.eq(Math.min(M.FREE_MAX, 8 + M.FREE_SPINS), 9);
  T.eq(Math.min(M.FREE_MAX, 15 + M.FREE_SPINS), 9, 'Rest 15 aus altem Spielstand: kein Fehler, Deckel greift');
});
```

Im Test `Mega Seven: RTP-Korridor (60.000 Spins, Seed 7)`: `T.ok(rtp > 0.88 && rtp < 0.98, …)` → `T.ok(rtp > 0.98 && rtp < 1.06, \`RTP ${rtp.toFixed(3)} außerhalb 0,98–1,06 (Balancing 2026-09-21, Jeder Tisch: ~102 % ohne Glück)\`);`

Im Test `Glücks-Ökonomie …` die Mega-Zeile: `T.ok(mega > 111 && mega < 122, …)` → `T.ok(mega > 114 && mega < 122, \`Mega Seven bei +20 Glück: RTP ${mega.toFixed(1)} % (erwartet 114–122)\`);`

Bestehende `megaLineWins`-Tests prüfen (grep): Erwartungen mit `mult` aus der alten Tafel (z. B. `🍒×3 → 2`, `7️⃣×5 → 500`) auf die neue Tafel umrechnen (🍒 3/4/5 = 5/8/12, 🔔 5/10/20, BAR 6/12/25, 💎 8/20/50, 7️⃣ 10/30/100). `megaWinTier`- und `megaAnticipation`-Tests bleiben (sie hängen nicht an der Tafel).

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep FAIL | grep -i mega | head`
Expected: `FAIL MEGA: flache Tafel …`, `FAIL megaLuckOverride: Glück dreht …`

- [ ] **Step 3: Regeln ändern**

In `RoyalRules.MEGA`:

```js
    WEIGHTS: [36, 18, 14, 6, 4, 3], // 🍒 🔔 BAR 💎 7️⃣ ⭐ – Balancing 2026-09-21 (Jeder Tisch): Trefferquote 40 % statt 16 %, Streuung 1,3 statt 3,9 (vorher 30/25/18/12/7/8)
    LINES: …unverändert…
    /* Auszahlung × Linieneinsatz je Anzahl in Folge ab Walze 1 (Index 2–5). Ein 3er zahlt mindestens den Einsatz zurück, Kirschen zahlen ab 2.
       Vorher 2/5/10 · 3/12/30 · 5/20/50 · 10/40/100 · 20/100/500 mit 70 % der Quote aus Freispielen. */
    PAY: { '🍒': [0, 0, 2, 5, 8, 12], '🔔': [0, 0, 0, 5, 10, 20], BAR: [0, 0, 0, 6, 12, 25], '💎': [0, 0, 0, 8, 20, 50], '7️⃣': [0, 0, 0, 10, 30, 100] },
    BETS: [100, 250, 500, 1000],
    FREE_SPINS: 3, FREE_MULT: 1, FREE_MAX: 9, SCATTER: '⭐', // Freispiele sind Bonus, nicht mehr das Hauptgeschäft (vorher 5, ×2, Deckel 15)
    LUCK_GAIN: 1.5, LUCK_REROLLS: 3, // Glück: bei Niete mit LUCK_GAIN × luck % bis zu LUCK_REROLLS-mal neu drehen, bis eine Linie zahlt
```

`megaLineWins`: die Zeile `if (count >= 3) out.push({ line, sym, count, mult: M.PAY[sym][count] });` → `if (M.PAY[sym][count] > 0) out.push({ line, sym, count, mult: M.PAY[sym][count] });`

`megaLuckOverride` ersetzen durch:

```js
  /* Glück: bei Niete mit LUCK_GAIN × luck % bis zu LUCK_REROLLS-mal neu drehen, bis eine Linie zahlt – das Spiegelbild von Pech (Gewinn wird neu gedreht).
     Der frühere Walzen-Schub (megaShift) lief bei den meisten Nieten ins Leere; Bier brachte an Mega nur +6 Punkte. (Balancing 2026-09-21, Jeder Tisch) */
  megaLuckOverride(grid, luck, rng) {
    if (luck < 0) return RoyalRules.megaLineWins(grid).length && Rules.pech(luck, rng) ? RoyalRules.megaRoll(rng) : grid;
    if (RoyalRules.megaLineWins(grid).length) return grid;
    if (!(rng() * 100 < luck * RoyalRules.MEGA.LUCK_GAIN)) return grid;
    let g = grid;
    for (let i = 0; i < RoyalRules.MEGA.LUCK_REROLLS && !RoyalRules.megaLineWins(g).length; i++) g = RoyalRules.megaRoll(rng);
    return g;
  },
```

`megaShift` bleibt (eigener Test `megaShift: Spalte rotieren`); prüfen mit `grep -n "megaShift" keller37.html`, dass es außer Definition und Test keine Aufrufer mehr gibt.

- [ ] **Step 4: Tafel und Statustext**

Tafel im Template (`<h4>Auszahlung × Linieneinsatz</h4>` und die Tabelle):

```html
      <h4>Auszahlung × Linieneinsatz (3 / 4 / 5 in Folge)</h4>
      <table>
        <tr><td>7️⃣</td><td>10 / 30 / 100</td></tr>
        <tr><td>💎</td><td>8 / 20 / 50</td></tr>
        <tr><td>BAR</td><td>6 / 12 / 25</td></tr>
        <tr><td>🔔</td><td>5 / 10 / 20</td></tr>
        <tr><td>🍒</td><td>5 / 8 / 12 · schon 2 in Folge: 2</td></tr>
        <tr><td>⭐ ×3+</td><td>3 Freispiele</td></tr>
      </table>
```

Statustext ca. Zeile 4558: `${free ? ' (Freispiel ×2)' : ''}` → `${free ? ' (Freispiel)' : ''}`.

- [ ] **Step 5: Tests laufen lassen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `… 0 fehlgeschlagen`. Falls der Mega-Korridor knapp verfehlt wird: `node tests/balance-sim.mjs --rtp` (Zeile `mega`) prüfen, Korridor um den Messwert ±4 legen – nicht die Regel ändern.

- [ ] **Step 6: README**

Im Absatz Casino Royal: `**Mega Seven** (5 Walzen, 5 Linien, Freispiele ×2)` → `**Mega Seven** (5 Walzen, 5 Linien, Kirschen zahlen ab 2, 3 Freispiele)`. Weiter unten im selben Absatz die Stellen `klappt bei Freispielen ein Banner aus` (bleibt) und `feiert BIG WIN ab 10× und MEGA WIN ab 50× Einsatz` (bleibt) – nur das `Freispiele ×2` entfernen, falls es dort erneut vorkommt (grep `×2` in README).

- [ ] **Step 7: Screenshot und Commit**

Run: `sh tests/screenshot.sh /tmp/claude-1000/mega.png "?screen=royal&game=megaslots"` – Tafel zeigt die neue Tabelle mit sechs Zeilen.

```bash
git add keller37.html README.md
git commit -m "balance(mega): flache Tafel, Kirschen ab 2, Freispiele 3×1, Glück dreht Nieten neu – Story 84/77 % statt 13/11

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Bier-Schwelle, Sim-Tabelle für alle Tische, README, Abschluss

**Files:**
- Modify: `keller37.html` – `Rules.BEER_WORTH_FROM` ca. Zeile 1788, Test `Glücks-Ökonomie …` ca. Zeile 10771–10793, Kommentar `BEER_SPINS`
- Modify: `tests/balance-sim.mjs` – neue Tabelle „diszipliniert je Tisch"
- Modify: `README.md` – Quoten-Absatz, Bier-Schwelle
- Modify: `docs/superpowers/specs/2026-09-21-balance-jeder-tisch-design.md` – Abschnitt 4 mit den gemessenen Werten, falls sie von der Tabelle abweichen

**Interfaces:**
- Consumes: `Rules.BASE_LUCK`, alle Tischregeln aus Task 1–6.
- Produces: `Rules.BEER_WORTH_FROM = 100`; `node tests/balance-sim.mjs` druckt die Tabelle je Tisch.

- [ ] **Step 1: Test der Bier-Schwelle auf Grundglück umstellen (Failing Test)**

Im Test `Glücks-Ökonomie: Bier 8 Spins, Brownie 4 Spins, Cap 1.000 – 3 Bier lohnen sich ab ~110 € …`:

Titel → `'Glücks-Ökonomie: Bier 8 Spins, Brownie 4 Spins, Cap 1.000 – 3 Bier lohnen sich ab ~100 € an jedem Tisch (Balancing 2026-09-21, Jeder Tisch)'`.

Die Rot-Messung erweitern: nach der bestehenden Schleife (Rot bei Glück 20 → `rot`) eine zweite mit `Rules.BASE_LUCK + 20` und eine mit `Rules.BASE_LUCK`:

```js
  const rotAt = (luck) => { const r = seeded(5); let s = 0; for (let i = 0; i < N; i++) { const rolled = Rules.rouletteLuckOverride('red', null, Rules.rouletteRoll(r), luck, r); s += Rules.roulettePayout('red', null, rolled, 100, mods); } return 100 + s / N; };
  const rot3 = rotAt(Rules.BASE_LUCK + 20), rot0 = rotAt(Rules.BASE_LUCK);
  T.ok(rot0 > 100 && rot0 < 106, `Rot nüchtern mit Grundglück ${rot0.toFixed(1)} % (erwartet 100–106)`);
  /* 3 Bier = 150 € für BEER_SPINS Spins: Gewinnschwelle am Roulette = 150 / (BEER_SPINS × Bier-Vorteil), Vorteil = Quote mit 3 Bier − Quote nüchtern */
  const schwelle = 150 / (Rules.BEER_SPINS * (rot3 - rot0) / 100);
  T.ok(schwelle > 85 && schwelle < 120, `Bier rechnet sich ab ${schwelle.toFixed(0)} € Einsatz`);
  T.ok(Math.abs(Rules.BEER_WORTH_FROM - schwelle) < 15, `Bar-Hinweis BEER_WORTH_FROM ${Rules.BEER_WORTH_FROM} passt zur Schwelle ${schwelle.toFixed(0)}`);
```

und die alten Zeilen `const schwelle = 150 / (Rules.BEER_SPINS * (rot - 100) / 100);` sowie die zwei `T.ok(schwelle …)` / `T.ok(Math.abs(Rules.BEER_WORTH_FROM …))` entfernen. Die Rot-Korridor-Zeile `T.ok(rot > 113 && rot < 121, …)` bleibt.

- [ ] **Step 2: Test laufen lassen – muss fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep "BEER_WORTH_FROM"`
Expected: `FAIL … Bar-Hinweis BEER_WORTH_FROM 110 passt zur Schwelle ~101`

- [ ] **Step 3: Konstante und Kommentar**

`BEER_WORTH_FROM: 110,` → `BEER_WORTH_FROM: 100, // Einsatz, ab dem sich 3 Bier rechnen (Bar-Hinweis; der Selftest prüft ihn gegen 150 / (BEER_SPINS × Bier-Vorteil)); Balancing 2026-09-21 (Jeder Tisch): Vorteil 19 Punkte am Roulette → ~100 €`

Kommentar an `BEER_SPINS`: `… lohnt sich ab ~110 € Einsatz` → `~100 €`.

- [ ] **Step 4: Tests laufen lassen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3`
Expected: `… 0 fehlgeschlagen`

- [ ] **Step 5: Sim-Tabelle für alle Tische**

In `tests/balance-sim.mjs` nach `rtpTable();` und vor `if (!process.argv.includes('--rtp'))` eine Funktion einfügen und aufrufen (innerhalb des `if`-Blocks, nach der Zeile `Vorteil von 3 Bier …`):

```js
/* Je Tisch: Quote nüchtern / mit 3 Bier (beides mit Grundglück), Trefferquote, Streuung in Einsätzen, Story 1/2 diszipliniert (1.500 Läufe) */
function tableByGame(s1, s2) {
  console.log(`\nJe Tisch, diszipliniert (Grundglück ${Rules.BASE_LUCK}; Ziel Story 1 ≥ 75 %, Story 2 ≥ 65 % – Balancing 2026-09-21, Jeder Tisch):`);
  console.log('  Tisch          nüchtern   3 Bier   Treffer   Streuung   Story 1   Story 2');
  for (const g of Object.keys(games)) {
    if (g === 'rouletteZahl') continue;
    const N = 40000, rng = seeded(3); let sum = 0, sq = 0, hits = 0, sober = 0;
    for (let i = 0; i < N; i++) { const d = games[g](100, Rules.BASE_LUCK + 20, rng); sum += d; sq += d * d; if (d > 0) hits++; sober += games[g](100, Rules.BASE_LUCK, rng); }
    const mean = sum / N, sd = Math.sqrt(sq / N - mean * mean) / 100, edge = beerEdge(g);
    const pct = (P) => { const r = seeded(21); let won = 0; for (let i = 0; i < 1500; i++) if (disciplined(r, { ...P, game: g, edge }).won) won++; return (won / 15).toFixed(1).padStart(5) + ' %'; };
    console.log(`  ${g.padEnd(13)} ${(100 + sober / N).toFixed(1).padStart(7)} %  ${(100 + mean).toFixed(1).padStart(5)} %  ${(hits / N * 100).toFixed(1).padStart(6)} %   ${sd.toFixed(2).padStart(6)}   ${pct({ ...s1, gameFrom: 0 })}   ${pct(s2)}`);
  }
}
```

Aufruf: `tableByGame(s1, s2);` direkt nach der Definition von `s2` im `if`-Block. (`disciplined` erwartet `P.edge` = Bier-Vorteil in Einsätzen – `beerEdge(g)` liefert genau das; `gameFrom: 0`, damit alle Tische ab Tag 1 spielbar sind wie in der Kalibrierung.)

- [ ] **Step 6: Sim laufen lassen und gegen die Spec prüfen**

Run: `node tests/balance-sim.mjs 2>&1 | tail -30`
Expected (Spec §4, Toleranz ±3 Quote / ±5 Story):

```
  slots           ~104.7 %  ~137.8 %   ~58 %   ~2.9   ~80 %   ~70 %
  rouletteRot     ~103.2 %  ~121.8 %   ~61 %   ~1.0   ~93 %   ~89 %
  wheel           ~104.2 %  ~120.7 %   ~22 %   ~1.2   ~81 %   ~74 %
  mega            ~105.2 %  ~122.3 %   ~41 %   ~1.3   ~84 %   ~77 %
  crapsPass       ~102.0 %  ~120.0 %   ~60 %   ~1.0   ~88 %   ~81 %
  baccaratBank    ~103.4 %  ~117.3 %   ~54 %   ~0.9   ~82 %   ~75 %
```

Weicht ein Tisch stärker ab, ist eine Regel falsch umgesetzt (Task 2–6 mit der Spec vergleichen), nicht die Sim. Der wilde Spieler (`run('wild …')`, falls vorhanden) bleibt ≤ 10 %.

- [ ] **Step 7: README-Quotenabsatz**

Im Absatz „Leben" den Satz von `Nüchtern liegen alle Tische bei ~97 % …` bis `… (Balancing 2026-09-21: vorher 4 Spins, Bier lohnte sich erst ab 220 € und nur am Roulette);` ersetzen durch:

`Nüchtern hast du 🍀 +5 % Grundglück und jeder Tisch liegt leicht im Plus (~102–105 %); mit drei Bier bei 117–138 % (Rot 122, Craps 120, Mega Seven 122, Baccarat 117, Rad 121, Slots 138 – Slots streuen am stärksten; Glück erzwingt dort ein Paar, aus 🍒🍋🍇 wird es zu 60 % ein Drilling) – 150 € Bier rechnen sich ab ~100 € Einsatz an jedem Tisch. Wer die Bankroll hält, schafft die Story an jedem Tisch zu 75–90 %, wer alles setzt, fällt trotzdem (`tests/balance-sim.mjs`; Balancing 2026-09-21 „Jeder Tisch": vorher war Rot der einzige Weg – Slots/Mega/Rad/Craps/Baccarat schafften die Story nur zu 11–22 %);`

Der Rest des Satzes (`negatives Glück ist Pech …`) bleibt.

- [ ] **Step 8: Spec-Abschnitt 4 mit Messwerten abgleichen**

Falls die Sim-Werte aus Step 6 von der Tabelle in Spec §4 um mehr als 1 Punkt abweichen: Tabelle in der Spec auf die gemessenen Werte setzen (Status bleibt „abgestimmt").

- [ ] **Step 9: DOM-Selftest, Playtest, Screenshots**

Run: `sh tests/dom-selftest.sh` → `failed=0`.
Run: `python3 tests/playtest-story.py 2>&1 | tail -15` → keine `FAIL`-Zeile (Laufzeit mehrere Minuten; bei Fehlern im Bereich Bier-Hinweis/Rad/Mega die Tafeltexte prüfen, sonst ist der Fehler vorbestehend – `git stash` und erneut laufen lassen, um das zu belegen).
Run: `sh tests/screenshot.sh /tmp/claude-1000/slots.png "?screen=slots"` – Tafel 40/19/10/5, Paar 1,4×; Kopfzeile 🍀 +5 %.

- [ ] **Step 10: Commit und Push**

```bash
git add keller37.html tests/balance-sim.mjs README.md docs/superpowers/specs/2026-09-21-balance-jeder-tisch-design.md
git commit -m "balance: Bier lohnt sich ab ~100 €, Sim-Tabelle je Tisch, README – jeder Tisch ein Weg zur Story

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Russisches Roulette – Igor zahlt 5:1

**Files:**
- Modify: `keller37.html` – Block `rules` (`HOSPITAL_RR` ca. Zeile 1780, `rrDelta` ca. Zeile 1960), Block `game-russian` (`Russian.start` ca. Zeile 6156, Statuszeilen in `pull` ca. Zeile 6195/6210, `Game.bindBet(root, 'rrBet')` ca. Zeile 6260), Template `tpl-russian` ca. Zeile 1500, Tür-Tag ca. Zeile 1202, Selftest `rrDelta` ca. Zeile 10854, DOM-Test `Russisch Roulette in Ego-Sicht …` ca. Zeile 14395–14462
- Modify: `README.md` – Satz zu Russischem Roulette im Absatz „Sechs Spiele"

**Interfaces:**
- Produces: `Rules.RR_MULT = 5`; `Rules.rrStake(bet)` → `bet * RR_MULT`; `Rules.rrDelta(victim, bet)` → `victim === 'player' ? -(bet * RR_MULT + HOSPITAL_RR) : bet * RR_MULT`.

- [ ] **Step 1: Failing Test schreiben**

Test `rrDelta` (ca. Zeile 10854) ersetzen durch:

```js
T.test('rrDelta/rrStake: Igor zahlt 5:1, Streifschuss kostet 5× Einsatz + Spital (Balancing 2026-09-21, Jeder Tisch)', () => {
  T.eq(Rules.RR_MULT, 5); T.eq(Rules.HOSPITAL_RR, 100);
  T.eq(Rules.rrStake(10), 50); T.eq(Rules.rrStake(1000), 5000);
  T.eq(Rules.rrDelta('player', 10), -150); T.eq(Rules.rrDelta('igor', 10), 50);
  T.eq(Rules.rrDelta('player', 1000), -5100); T.eq(Rules.rrDelta('igor', 1000), 5000);
});
```

- [ ] **Step 2: Test laufen lassen – muss fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep "rrDelta" | head -2`
Expected: `FAIL rrDelta/rrStake: … expected 5, got undefined`

- [ ] **Step 3: Regeln ändern**

Block `rules`: unter `HOSPITAL_RR: 100,` einfügen `RR_MULT: 5, // Igor zahlt 5:1, ein Streifschuss kostet 5× Einsatz + Spital (Balancing 2026-09-21, Jeder Tisch; vorher 1:1 – bei 10 € riskierte man 110 für 10)`.

`rrDelta` ersetzen durch:

```js
  rrStake(bet) { return bet * Rules.RR_MULT; }, // liegt auf dem Tisch (Escrow bei Duellstart, MAX-Chip = maxBet / RR_MULT)
  rrDelta(victim, bet) { return victim === 'player' ? -(bet * Rules.RR_MULT + Rules.HOSPITAL_RR) : bet * Rules.RR_MULT; },
```

- [ ] **Step 4: Spielablauf anpassen**

In `Russian.start`: `if (!forced && !Game.beginSpin(bet)) return;` → `if (!forced && !Game.beginSpin(Rules.rrStake(bet))) return;`

In `Russian.end` (ca. Zeile 6250): `await Game.settle(delta, { from: …, game: 'russian', bet: duel.bet, run: duel.run });` → `bet: Rules.rrStake(duel.bet)` (Escrow wird brutto zurückgebucht, `delta` ist das Netto aus `rrDelta`). Die Zeile `await Bus.emit('rr:result', { victim, bet: duel.bet });` bleibt (Einsatz, nicht Tischeinsatz).

Statuszeilen in `pull`: `−${UI.fmt(duel.bet)}` → `−${UI.fmt(-Rules.rrDelta('player', duel.bet))}` und `+${UI.fmt(duel.bet)}` → `+${UI.fmt(Rules.rrDelta('igor', duel.bet))}`.

`Game.bindBet(root, 'rrBet');` → `Game.bindBet(root, 'rrBet', () => Math.max(1, Math.floor(Rules.maxBet(State.s, Perks.mods()) / Rules.RR_MULT)));`

Template `tpl-russian`: Statuszeile → `Duell gegen Igor. Igor zahlt 5:1 – ein Streifschuss kostet 5× Einsatz und 100 € Spital.`

Tür-Tag (ca. Zeile 1202): `<div class="chalk-tag">Duell · 1 Kugel</div>` → `<div class="chalk-tag">Duell · 5:1</div>`.

- [ ] **Step 5: DOM-Test anpassen**

Im Test `Russisch Roulette in Ego-Sicht …` (Startguthaben 1000, Einsatz 10): Escrow ist jetzt 50, Verlust 150.
- `[true, 990, false, 'revolverMuzzle', …]` → `950`
- Kommentar `Abrechnung −(10 + 100)` → `Abrechnung −(5 × 10 + 100)`; Erwartung `890` (Streifschuss abgerechnet) → `850`
- forced: beide `890` → `850`
- drop: `880` (nach Start) → `800`; `880` (nach drop) → `800`
- `[['result', 'player', 10]]` bleibt (Event meldet den Einsatz).

- [ ] **Step 6: Tests laufen lassen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh`
Expected: `… 0 fehlgeschlagen` und `failed=0`

- [ ] **Step 7: README und Commit**

README, Absatz „Sechs Spiele": `Russisches Roulette gegen Igor` → `Russisches Roulette gegen Igor (5:1 – ein Streifschuss kostet 5× Einsatz und 100 € Spital)`.

```bash
git add keller37.html README.md
git commit -m "balance(igor): Russisches Roulette zahlt 5:1, Streifschuss kostet 5× Einsatz + Spital – bei 10 € nicht mehr 110 riskieren für 10

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git pull --rebase origin main && node tests/run-selftest.mjs 2>&1 | tail -1 && git push origin main
```
