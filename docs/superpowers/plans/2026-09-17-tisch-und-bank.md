# Tisch & Bank – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Roulette mit mehreren Chips pro Dreh, Bank auf 8 % Zinsen mit nur einem offenen Kredit, Anlagen mit je einer laufenden Anlage pro Sorte (Festgeld 6 Spins, Trickbetrug +50 %).

**Architecture:** Alle Zahlen und die Auswertung bleiben rein in `Rules` (`rouletteSettle`, `rouletteLuckTarget`, `canInvest`, `bankLoanReason`); der Roulette-Screen hält nur ein Chip-Array und bezahlt die Summe einmal über den bestehenden Escrow (`Game.beginSpin` / `Game.settle`). Finanz- und Anlagen-Raum lesen die Regeln und sperren Knöpfe mit Hinweistext.

**Tech Stack:** Vanilla HTML/CSS/JS in `keller37.html` (Ein-Datei-Vorgabe), Node-Selftest (`node tests/run-selftest.mjs`), Browser-Selftest (`tests/dom-selftest.sh`), headless-Chrome-Playtest (`python3 tests/playtest-story.py`).

**Spec:** `docs/superpowers/specs/2026-09-17-tisch-und-bank-design.md`

## Global Constraints

- Alles bleibt in der einen Datei `keller37.html`; keine neuen Script-Blöcke nötig (Änderungen in `rules`, `rooms`, `game-roulette`, `achievements`, Templates, CSS).
- `State.VERSION` bleibt `1`; keine neuen Pflichtfelder. Laufende Anlagen bekommen ein optionales Feld `type`; alte ohne `type` werden über `name` erkannt.
- Zahlen exakt: `BANK_RATE = 0.08`; Mercedes `bankRate` C/S/G = `0.07 / 0.06 / 0.05`; `INVEST.bank.spins = 6`; `INVEST.scam.rate = 0.5`; sonst unverändert (Limits 3.000 / 4.000 / 6.000 / 10.000; Festgeld 10 % Risiko; Aktien +100 % / 2 Spins / 85 %; Trickbetrug 10 Spins / 55 %; Mindestbetrag 10 €).
- Ein offener Bank-Kredit: `bankLoanAllowed(s, amt)` ist nur wahr bei `s.bankDebt === 0` und innerhalb des Limits. Game-Over-Regel (Ruling, siehe Task 1): beide Kreditquellen zu (`bankDebt > 0 ∧ mafiaDebt > 0`) und kein 1-€-Spin bezahlbar.
- Roulette: Auszahlung Zahl 35:1, Außenfelder 1:1, Null lässt Außenfelder verlieren; Escrow genau einmal pro Dreh mit der Chip-Summe; Glücks-Override wirkt auf genau einen Chip (`rouletteLuckTarget`).
- Deutsch, typografische Anführungszeichen „…" (schließend gerades `"` wie im Rest der Datei).
- Vor jedem Commit: `node tests/run-selftest.mjs` und `tests/dom-selftest.sh` grün. Commits enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## Orientierung im Code (für alle Tasks)

- Helfer (Block `util`): `qs`, `qsa`, `h(tag, attrs, ...children)`, `wait(ms)`, `pick`, `rand`.
- `Rules` (Block `rules`): `BANK_RATE`, `BANK_LIMIT`, `bankInterest(debt, s?)`, `spinCosts(s)`, `maxBet(s)`, `checkSpin(s, bet)`, `bankLoanAllowed(s, amt)`, `isGameOver(s)`, `INVEST`, `investmentResolve`, `WHEEL`, `RED`, `isRed`, `rouletteRoll(rng)`, `rouletteLuckOverride(type, chosen, rolled, luck, rng)`, `roulettePayout(type, chosen, rolled, bet)` (liefert Delta: `+bet`, `+35·bet` oder `−bet`). Katalog `Rules.GEAR` im Block `gear-rules`.
- `Game` (Block `core`): `readBet(inputId)`, `bindBet(root, inputId)` (Stepper + `[data-chip]`-Schnellwahl, `max` → `Rules.maxBet`), `beginSpin(bet)` (prüft `checkSpin`, zieht Einsatz + Zinsen + Meds ab, `inFlight++`, setzt `Game.run`), `settle(delta, { from, game, bet, run })` (zahlt brutto zurück, `afterSpin`, Bus `win`/`loss`), `applyDelta(delta, { from, quiet })`.
- Roulette (Block `game-roulette`, Template `tpl-roulette`): `buildTable()` baut `.rcell`-Buttons (Zahlen + Außenfelder), `flyChip(cell, label, gen)`, `animateBall(dur, gen)`, `play(type, chosen, cell)` (ein Einsatz), `drawWheel(highlight)`; CSS `.rtable`, `.rcell`, `.chip`, `.chip.placed`, `.bet-bar`, `.table-box`, Keyframes `chipWin`/`chipLost`/`popIn`.
- Finanz (Block `rooms`, `const Finance`): `render()` (Schuldscheine, `[data-loan]`-Knöpfe, `#bankTerms`), `loanBank(amt)`, `repayBank()`; Szenen `bank.loan`, `bank.limit` (Block `rooms`, `Cutscene.define`). Template `tpl-finance`.
- Anlagen (Block `rooms`, `const Invest`): `render()` (Ticket-Liste `#tickets`), `invest(type)`; Template `tpl-invest` mit drei `.chalk.inv[data-type]`-Karten; Auflösung in `Game.afterSpin` (Bus `invest.resolved`).
- Achievements: `Bus.on('roulette:result', ({ type, win }) => …)` für „Plein".
- Selftests: Block `selftest`, `T.test/T.eq/T.ok`, `base(o)`, `seq(...values)` (rng-Sequenz), Fälle vor `/* --- SELFTEST CASES END --- */`.
- Playtest: `tests/playtest-story.py` (`cdp.navigate`, `cdp.eval(js, await_promise=False)`, `cdp.click(sel)`, `cdp.screenshot(name)` → `/tmp/k37story/`, `record(name, ok, detail)`, `main()`); Referenzbilder `docs/superpowers/screenshots/`.

---

### Task 1: Regeln – Bank 8 %, ein Kredit, Anlagen-Werte, `canInvest`, Roulette-Auswertung

**Files:**
- Modify: `keller37.html` – Block `rules` (`BANK_RATE`, `bankLoanAllowed`, `isGameOver`, `INVEST`, neue Funktionen), Block `gear-rules` (Mercedes `bankRate`), Block `selftest` (Tests anpassen/ergänzen)

**Interfaces:**
- Produces: `Rules.bankLoanReason(s, amt) → null | 'open' | 'limit'`; `Rules.bankLoanAllowed(s, amt) → boolean` (= `bankLoanReason === null`); `Rules.canInvest(s, kind, amount) → { ok, reason?: 'running' | 'min' | 'funds' }`; `Rules.investRunning(s, kind) → inv | null`; `Rules.rouletteTotal(bets) → number`; `Rules.rouletteSettle(bets, rolled) → { payout, hits: [{ bet, win, payout }] }` (Chip-`payout` = Einsatz + Gewinn bei Treffer, sonst 0); `Rules.rouletteLuckTarget(bets) → index | -1`.

- [ ] **Step 1: Bestehende Tests auf die neuen Zahlen umstellen und neue Tests schreiben**

Im Block `selftest`:

`T.test('bankInterest: 30% gerundet', …)` ersetzen durch

```js
T.test('bankInterest: 8 % gerundet', () => {
  T.eq(Rules.bankInterest(0), 0);
  T.eq(Rules.bankInterest(200), 16);
  T.eq(Rules.bankInterest(1000), 80);
  T.eq(Rules.bankInterest(333), 27);
});
```

`T.test('bankInterest: Mercedes-Zinssatz', …)` ersetzen durch

```js
T.test('bankInterest: Mercedes-Zinssatz', () => {
  T.eq(Rules.bankInterest(1000), 80);
  T.eq(Rules.bankInterest(1000, base()), 80);
  T.eq(Rules.bankInterest(1000, base({ car: 'mercC' })), 70);
  T.eq(Rules.bankInterest(1000, base({ car: 'mercG' })), 50);
  T.eq(Rules.spinCosts(base({ bankDebt: 1000, car: 'mercS' })).interest, 60);
});
```

`T.test('bankLoanAllowed: Limit 3000', …)` ersetzen durch

```js
T.test('bankLoanAllowed: ein Kredit, Limit 3000', () => {
  T.eq(Rules.bankLoanReason(base({ bankDebt: 0 }), 3000), null);
  T.eq(Rules.bankLoanReason(base({ bankDebt: 0 }), 3001), 'limit');
  T.eq(Rules.bankLoanReason(base({ bankDebt: 500 }), 500), 'open');
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 0 }), 1000), true);
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 2000 }), 1000), false);
});
```

`T.test('bankLoanAllowed / isGameOver: Mercedes-Limit', …)` ersetzen durch

```js
T.test('bankLoanAllowed / isGameOver: Mercedes-Limit, beide Quellen zu', () => {
  T.eq(Rules.bankLoanReason(base({ bankDebt: 0, car: 'mercC' }), 4000), null);
  T.eq(Rules.bankLoanReason(base({ bankDebt: 0, car: 'mercC' }), 4001), 'limit');
  T.eq(Rules.bankLoanReason(base({ bankDebt: 0 }), 4000), 'limit');
  T.eq(Rules.isGameOver(base({ bankDebt: 500, mafiaDebt: 300, balance: 0 })), true);
  T.eq(Rules.isGameOver(base({ bankDebt: 0, mafiaDebt: 300, balance: 0 })), false);
  T.eq(Rules.isGameOver(base({ bankDebt: 500, mafiaDebt: 0, balance: 0 })), false);
  T.eq(Rules.isGameOver(base({ bankDebt: 500, mafiaDebt: 300, balance: 100 })), false);
});
```

Im Test `GEAR: Preise steigen je Linie, Glück ≤ 4, Zinsen sinken` bleibt alles gültig (7 > 6 > 5). Neu vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- Tisch & Bank ---- */
T.test('INVEST: neue Werte', () => {
  T.eq([Rules.INVEST.bank.rate, Rules.INVEST.bank.spins, Rules.INVEST.bank.risk], [0.08, 6, 10]);
  T.eq([Rules.INVEST.scam.rate, Rules.INVEST.scam.spins, Rules.INVEST.scam.risk], [0.5, 10, 55]);
  T.eq([Rules.INVEST.stock.rate, Rules.INVEST.stock.spins, Rules.INVEST.stock.risk], [1.0, 2, 85]);
  T.eq(Rules.BANK_RATE, 0.08);
  T.eq([Rules.GEAR.cars.mercC.bankRate, Rules.GEAR.cars.mercS.bankRate, Rules.GEAR.cars.mercG.bankRate], [0.07, 0.06, 0.05]);
});
T.test('canInvest / investRunning: je Sorte eine, Mindestbetrag, Geld', () => {
  const s = base({ balance: 100, investments: [{ type: 'bank', name: 'Festgeld', amount: 50, rate: 0.08, spins: 3, risk: 10 }] });
  T.eq(Rules.canInvest(s, 'bank', 50), { ok: false, reason: 'running' });
  T.eq(Rules.canInvest(s, 'stock', 50), { ok: true });
  T.eq(Rules.canInvest(s, 'scam', 5), { ok: false, reason: 'min' });
  T.eq(Rules.canInvest(s, 'scam', 101), { ok: false, reason: 'funds' });
  T.eq(Rules.investRunning(s, 'bank').amount, 50);
  T.eq(Rules.investRunning(s, 'scam'), null);
  const alt = base({ balance: 100, investments: [{ name: 'Trickbetrug', amount: 20, rate: 0.3, spins: 2, risk: 55 }] });
  T.eq(Rules.canInvest(alt, 'scam', 20).reason, 'running', 'alte Anlage ohne type über den Namen erkannt');
});
T.test('rouletteTotal / rouletteSettle: Zahl + Rot + Gerade', () => {
  const bets = [{ type: 'number', n: 17, amount: 10 }, { type: 'red', n: null, amount: 50 }, { type: 'even', n: null, amount: 20 }];
  T.eq(Rules.rouletteTotal(bets), 80);
  const r18 = Rules.rouletteSettle(bets, 18);              // 18: rot, gerade
  T.eq(r18.payout, 100 + 40);
  T.eq(r18.hits.map((x) => x.win), [false, true, true]);
  T.eq(r18.hits.map((x) => x.payout), [0, 100, 40]);
  const r17 = Rules.rouletteSettle(bets, 17);              // 17: schwarz, ungerade
  T.eq(r17.payout, 360);
  T.eq(r17.hits.map((x) => x.payout), [360, 0, 0]);
  const r0 = Rules.rouletteSettle(bets, 0);
  T.eq(r0.payout, 0);
  T.eq(Rules.rouletteSettle([], 5), { payout: 0, hits: [] });
});
T.test('rouletteLuckTarget: höchster Einsatz, Zahl vor Außenfeld, dann Reihenfolge', () => {
  T.eq(Rules.rouletteLuckTarget([]), -1);
  T.eq(Rules.rouletteLuckTarget([{ type: 'red', n: null, amount: 50 }, { type: 'number', n: 3, amount: 10 }]), 0);
  T.eq(Rules.rouletteLuckTarget([{ type: 'red', n: null, amount: 50 }, { type: 'number', n: 3, amount: 50 }]), 1);
  T.eq(Rules.rouletteLuckTarget([{ type: 'red', n: null, amount: 50 }, { type: 'black', n: null, amount: 50 }]), 0);
});
```

Außerdem in `T.test('Life.render …')`-ähnlichen Fällen nichts ändern; der Test bei ~Zeile 5026 (`investments.push({ name: 'Festgeld', … spins: 5 …})`) bleibt gültig.

- [ ] **Step 2: Tests laufen lassen – fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: FAIL bei `bankInterest: 8 %`, `bankInterest: Mercedes`, `bankLoanAllowed: ein Kredit`, `isGameOver`, `INVEST: neue Werte`, `canInvest`, `rouletteTotal`, `rouletteLuckTarget` (Funktionen fehlen bzw. alte Zahlen).

- [ ] **Step 3: Konstanten und Funktionen**

Block `rules`: `BANK_RATE: 0.3,` → `BANK_RATE: 0.08,`.

`bankLoanAllowed` und `isGameOver` ersetzen durch:

```js
  /* null = erlaubt; 'open' = es läuft schon ein Kredit; 'limit' = Betrag übersteigt das Limit */
  bankLoanReason(s, amt) {
    if (s.bankDebt > 0) return 'open';
    if (amt > Rules.gear(s).bankLimit) return 'limit';
    return null;
  },
  bankLoanAllowed(s, amt) { return Rules.bankLoanReason(s, amt) === null; },
  /* Game Over: beide Kreditquellen zu (Bank-Kredit offen, Vito-Zettel offen) und nicht mal ein 1-€-Spin (inkl. Zinsen/Meds) bezahlbar */
  isGameOver(s) {
    const c = Rules.spinCosts(s);
    return s.bankDebt > 0 && s.mafiaDebt > 0 && s.balance < 1 + c.interest + c.meds;
  },
```

`INVEST`:

```js
  INVEST: {
    bank: { name: 'Festgeld', rate: 0.08, spins: 6, risk: 10, min: 10 },
    stock: { name: 'Aktien', rate: 1.0, spins: 2, risk: 85, min: 10 },
    scam: { name: 'Trickbetrug', rate: 0.5, spins: 10, risk: 55, min: 10 },
  },
  investRunning(s, kind) {
    const def = Rules.INVEST[kind];
    return (s.investments || []).find((inv) => inv.type === kind || (!inv.type && inv.name === def.name)) || null;
  },
  canInvest(s, kind, amount) {
    const def = Rules.INVEST[kind];
    if (!def) return { ok: false, reason: 'unknown' };
    if (Rules.investRunning(s, kind)) return { ok: false, reason: 'running' };
    if (!Number.isFinite(amount) || amount < def.min) return { ok: false, reason: 'min' };
    if (s.balance < amount) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
```

Roulette – nach `roulettePayout`:

```js
  rouletteTotal(bets) { return bets.reduce((sum, b) => sum + b.amount, 0); },
  /* Auszahlung aller Chips: pro Chip Einsatz + Gewinn bei Treffer, sonst 0 */
  rouletteSettle(bets, rolled) {
    const hits = bets.map((bet) => {
      const d = Rules.roulettePayout(bet.type, bet.n, rolled, bet.amount);
      const win = d > 0;
      return { bet, win, payout: win ? bet.amount + d : 0 };
    });
    return { payout: hits.reduce((sum, x) => sum + x.payout, 0), hits };
  },
  /* Der Chip, auf den das Glück wirkt: höchster Einsatz; bei Gleichstand Zahl vor Außenfeld; dann der zuerst gelegte */
  rouletteLuckTarget(bets) {
    let best = -1;
    bets.forEach((b, i) => {
      if (best < 0) { best = i; return; }
      const cur = bets[best];
      if (b.amount > cur.amount || (b.amount === cur.amount && b.type === 'number' && cur.type !== 'number')) best = i;
    });
    return best;
  },
```

Block `gear-rules`: `bankRate: 0.27` → `0.07`, `0.24` → `0.06`, `0.20` → `0.05`.

- [ ] **Step 4: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs` und `tests/dom-selftest.sh`
Expected: alle bestanden (107 alte, davon 4 umgestellt, + 4 neue = 111).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(rules): Bank 8 %, ein offener Kredit, Anlagen-Werte, canInvest, Roulette-Mehrfachauswertung

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Finanz- und Anlagen-Raum – Kredit-Sperre, laufende Anlage an der Karte, Texte

**Files:**
- Modify: `keller37.html` – Template `tpl-finance` (Hinweis-Zeile), Template `tpl-invest` (Texte, Slot für laufende Anlage), Block `rooms` (`Finance.render`, `Finance.loanBank`, `Invest.render`, `Invest.invest`, Szene `bank.loan`), Seitenleisten-Text „Anlagen"
- Modify: `README.md` (Bank 8 %, Anlagen-Werte)

**Interfaces:**
- Consumes: `Rules.bankLoanReason`, `Rules.canInvest`, `Rules.investRunning` (Task 1).
- Produces: `#bankHint` (Hinweis unter den Kredit-Knöpfen), Anlagen-Karten mit `.inv-running` bzw. Eingabe, Anlagen mit `type`.

- [ ] **Step 1: Finanz-Raum**

Template `tpl-finance`: direkt nach der Zeile mit den `[data-loan]`-Knöpfen (suche `data-loan="500"`) eine Hinweiszeile einfügen:

```html
      <p class="dim hidden" id="bankHint"></p>
```

`Finance.render()`: die Zeile

```js
    qsa('[data-loan]', this.root).forEach((b) => { b.disabled = !Rules.bankLoanAllowed(s, parseInt(b.dataset.loan, 10)); });
```

ersetzen durch

```js
    qsa('[data-loan]', this.root).forEach((b) => { b.disabled = !Rules.bankLoanAllowed(s, parseInt(b.dataset.loan, 10)); });
    const hint = qs('#bankHint', this.root);
    hint.classList.toggle('hidden', s.bankDebt === 0);
    hint.textContent = s.bankDebt > 0 ? 'Erst den Schuldschein tilgen – Herr Krause gibt nur einen Kredit auf einmal.' : '';
```

`Finance.loanBank(amt)`: den Anfang

```js
    if (!Rules.bankLoanAllowed(s, amt)) {
      if (!s.flags.bankLimit) { … }
      else UI.toast({ … });
      return;
    }
```

ersetzen durch

```js
    const why = Rules.bankLoanReason(s, amt);
    if (why === 'open') { UI.toast({ icon: '👔', title: 'Ein Kredit reicht', text: 'Erst den Schuldschein tilgen.', tone: 'loss' }); SFX.play('lose'); return; }
    if (why === 'limit') {
      if (!s.flags.bankLimit) { s.flags.bankLimit = true; State.save(); await Cutscene.play('bank.limit', { limit: UI.fmt(Rules.gear(s).bankLimit) }); }
      else UI.toast({ icon: '👔', title: 'Kreditlimit erreicht', text: `Herr Krause bedauert. ${UI.fmt(Rules.gear(s).bankLimit)} sind das Ende.`, tone: 'loss' });
      return;
    }
```

Szene `bank.loan` (Block `rooms`): den Text „Dreißig Prozent Zinsen – pro Spin, versteht sich. …" ersetzen durch `{{rate}} Prozent Zinsen – pro Spin, versteht sich. Marktüblich. Hier unten. Unterschreiben Sie bitte da, da und da.` und den Aufruf `Cutscene.play('bank.loan', {})` in `loanBank` ändern in `Cutscene.play('bank.loan', { rate: Math.round(Rules.gear(s).bankRate * 100) })`.

Template `tpl-finance`: `Herr Krause · 30 % Zinsen pro Spin · Limit 3.000 €` → `Herr Krause · 8 % Zinsen pro Spin · Limit 3.000 €` (wird ohnehin von `render()` überschrieben).

- [ ] **Step 2: Anlagen-Raum**

Template `tpl-invest`: in jeder Karte den Text anpassen und einen Slot für die laufende Anlage ergänzen – Beispiel Festgeld:

```html
      <div class="chalk inv" data-type="bank">
        <h4>🏦 Festgeld</h4>
        <p class="dim">+8 % · 6 Spins · 10 % Risiko</p>
        <div class="inv-running hidden"></div>
        <div class="inv-form">
          <div class="bet-field"><button data-step="-10">−</button><input type="number" id="invBank" value="50" min="10"><button data-step="10">+</button></div>
          <button class="btn blue sm" data-invest="bank">Anlegen</button>
        </div>
      </div>
```

Gleiches Muster für Aktien (`+100 % · 2 Spins · <strong>85 % Risiko</strong>`) und Trickbetrug (`+50 % · 10 Spins · <strong>55 % Risiko</strong>` und darunter `<p class="dim">Vito legt es für dich an. Frag nicht, wo.</p>`); Eingabe + Knopf jeweils in `.inv-form`.

CSS (im Abschnitt der `.chalk.inv`-Regeln, suche `.invest-grid`):

```css
.inv-running { font-family: var(--font-mono); font-size: .85rem; color: var(--gold-2); border: 1px dashed rgba(201,162,39,.5); border-radius: 6px; padding: 8px 10px; text-align: center; }
```

`Invest.render()` ersetzen durch:

```js
  render() {
    if (!this.root) return;
    const s = State.s;
    const box = qs('#tickets', this.root);
    box.innerHTML = '';
    if (s.investments.length === 0) box.append(h('span', { class: 'empty' }, 'Keine laufenden Anlagen.'));
    for (const inv of s.investments) {
      box.append(h('div', { class: 'ticket' }, h('b', {}, inv.name), ` · ${UI.fmt(inv.amount)} · noch ${inv.spins} Spin${inv.spins === 1 ? '' : 's'}`));
    }
    for (const card of qsa('.chalk.inv', this.root)) {
      const run = Rules.investRunning(s, card.dataset.type);
      qs('.inv-running', card).classList.toggle('hidden', !run);
      qs('.inv-form', card).classList.toggle('hidden', !!run);
      if (run) qs('.inv-running', card).textContent = `Läuft: ${UI.fmt(run.amount)} · noch ${run.spins} Spin${run.spins === 1 ? '' : 's'}`;
    }
  },
```

`Invest.invest(type)`: die beiden Prüfungen (`amt < def.min`, `s.balance < amt`) ersetzen durch

```js
    const chk = Rules.canInvest(s, type, amt);
    if (!chk.ok) {
      const msg = chk.reason === 'running' ? { title: 'Läuft schon', text: `Erst auszahlen lassen, dann neu anlegen.` }
        : chk.reason === 'min' ? { title: 'Mindestens 10 €' } : { title: 'Zu wenig Geld', text: `Du hast ${UI.fmt(s.balance)}.` };
      UI.toast(Object.assign({ icon: '🚫', tone: 'loss' }, msg)); SFX.play('lose'); return;
    }
```

und beim Push `type` ergänzen: `s.investments.push({ type, name: def.name, amount: amt, rate: def.rate, spins: def.spins, risk: def.risk });`.

- [ ] **Step 3: README**

`README.md`: „Bank (30 % Zinsen pro Spin, Limit 3.000 €)" → „Bank (8 % Zinsen pro Spin, Limit 3.000 €, nur ein Kredit auf einmal)"; im Anlagen-Absatz die Werte „Festgeld +8 % nach 6 Spins (10 % Risiko), Aktien +100 % nach 2 Spins (85 %), Trickbetrug +50 % nach 10 Spins (55 %) – je Sorte eine laufende Anlage".

- [ ] **Step 4: Tests und Sichtprüfung**

Run: `node tests/run-selftest.mjs`, `tests/dom-selftest.sh`; `tests/screenshot.sh /tmp/finance.png "?fresh&screen=finance"` und `tests/screenshot.sh /tmp/invest.png "?fresh&screen=invest"` – Konditionszeile „8 %", Anlagen-Texte neu. In der Konsole (oder per kleinem CDP-Skript): 500 € Kredit nehmen → Knöpfe gesperrt, `#bankHint` sichtbar; Festgeld 20 € anlegen → Karte zeigt „Läuft: 20 € · noch 6 Spins", Eingabe weg.

- [ ] **Step 5: Commit**

```bash
git add keller37.html README.md
git commit -m "feat(bank): ein Kredit auf einmal mit Hinweis, Anlagen-Karten zeigen laufende Anlage, neue Werte in Texten

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Roulette-Tisch – Chips legen, Tischleiste, ein Dreh wertet alles aus

**Files:**
- Modify: `keller37.html` – Template `tpl-roulette`, CSS Roulette (`.table-bar`, `.chip-stack`, Schnellwahl 500), Block `game-roulette` (Chip-Array, `place/undo/clear/repeat/spin`), Block `achievements` (Listener „Plein")

**Interfaces:**
- Consumes: `Rules.rouletteTotal`, `rouletteSettle`, `rouletteLuckTarget` (Task 1), `Game.beginSpin/settle/readBet/bindBet`.
- Produces: `Roulette.bets`, `Roulette.lastBets`, `Roulette.place(type, n, cell)`, `Roulette.undo()`, `Roulette.clear()`, `Roulette.repeat()`, `Roulette.spin()`, Bus-Event `roulette:result { bets, rolled, payout, hits, total }`, DOM `#tableTotal`, `#btnSpin`, `#btnUndo`, `#btnClear`, `#btnRepeat`, `.chip-stack[data-key]`.

- [ ] **Step 1: Template**

`tpl-roulette`: den Block `.table-box` ersetzen durch

```html
      <div class="table-box">
        <div class="rtable" id="rtable"></div>
        <div class="table-bar">
          <span class="table-total" id="tableTotal">Auf dem Tisch: 0 € · 0 Chips</span>
          <button class="btn sm" id="btnSpin" disabled>Drehen</button>
          <button class="btn ghost sm" id="btnUndo" disabled>↶ Chip zurück</button>
          <button class="btn ghost sm" id="btnClear" disabled>Tisch leeren</button>
          <button class="btn ghost sm" id="btnRepeat" disabled>Wie zuletzt</button>
        </div>
        <div class="bet-bar">
          <span class="dim">Chip:</span>
          <div class="bet-field"><button data-step="-5">−</button><input type="number" id="rouletteBet" value="10" min="1"><button data-step="5">+</button></div>
          <button class="chip" data-chip="10" data-v="10">10</button>
          <button class="chip" data-chip="50" data-v="50">50</button>
          <button class="chip" data-chip="100" data-v="100">100</button>
          <button class="chip" data-chip="500" data-v="500">500</button>
          <button class="chip" data-chip="max" data-v="max">MAX</button>
        </div>
        <div class="status" id="rouletteStatus">Chip auf ein Feld legen, dann drehen</div>
      </div>
```

- [ ] **Step 2: CSS**

Neben `.rtable`-Regeln ergänzen:

```css
.table-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; }
.table-bar .btn.sm { font-size: .8rem; padding: 6px 12px; }
.table-total { font-family: var(--font-mono); font-size: .85rem; color: var(--gold-2); margin-right: 6px; }
.chip-stack { position: absolute; right: -4px; top: -6px; min-width: 22px; height: 22px; padding: 0 5px; border-radius: 11px; background: #e8c65a; color: #111; border: 2px solid #fff; font-family: var(--font-mono); font-weight: 700; font-size: .68rem; line-height: 18px; text-align: center; pointer-events: none; box-shadow: 0 2px 4px rgba(0,0,0,.6); z-index: 2; animation: popIn .2s ease both; }
.chip-stack.won { background: var(--neon-green); color: #062; animation: chipWin .5s ease both; }
.chip-stack.lost { background: #555; color: #ccc; animation: chipLost .5s ease both; }
.chip[data-v="500"] { --chip: #6a1b9a; }
```

- [ ] **Step 3: Roulette-Modul**

Im Objekt `Roulette` die Felder ergänzen: `bets: [], lastBets: [],`. In `buildTable()` den `onclick` der Zellen ändern: `onclick: (e) => this.place(type, chosen, e.currentTarget)`. `play(type, chosen, cell)` komplett ersetzen durch:

```js
  key(type, n) { return type === 'number' ? `n${n}` : type; },
  cellFor(type, n) { return qs(`.rcell[data-key="${this.key(type, n)}"]`, this.root); },
  total() { return Rules.rouletteTotal(this.bets); },
  renderTable(result = null) {
    if (!this.root) return;
    qsa('.chip-stack', this.root).forEach((el) => el.remove());
    const sums = new Map();
    for (const b of this.bets) { const k = this.key(b.type, b.n); sums.set(k, (sums.get(k) || 0) + b.amount); }
    for (const [k, sum] of sums) {
      const cell = qs(`.rcell[data-key="${k}"]`, this.root);
      if (!cell) continue;
      const won = result ? result.hits.some((x) => this.key(x.bet.type, x.bet.n) === k && x.win) : null;
      cell.append(h('div', { class: 'chip-stack' + (won === true ? ' won' : won === false ? ' lost' : ''), 'data-key': k }, String(sum)));
    }
    qs('#tableTotal', this.root).textContent = `Auf dem Tisch: ${UI.fmt(this.total())} · ${this.bets.length} Chip${this.bets.length === 1 ? '' : 's'}`;
    const idle = !this.spinning;
    qs('#btnSpin', this.root).disabled = !idle || this.bets.length === 0;
    qs('#btnUndo', this.root).disabled = !idle || this.bets.length === 0;
    qs('#btnClear', this.root).disabled = !idle || this.bets.length === 0;
    qs('#btnRepeat', this.root).disabled = !idle || this.lastBets.length === 0 || !Rules.checkSpin(State.s, Rules.rouletteTotal(this.lastBets)).ok;
  },
  place(type, n, cell) {
    if (this.spinning || !this.root) return;
    const amount = Game.readBet('rouletteBet');
    const chk = Rules.checkSpin(State.s, this.total() + amount);
    if (!chk.ok) {
      if (chk.reason === 'invalid') UI.toast({ icon: '🚫', title: 'Ungültiger Chip', text: 'Mindestens 1 €.', tone: 'loss' });
      else UI.toast({ icon: '🚫', title: 'Zu wenig Geld', tone: 'loss', ms: 4500, text: `Auf dem Tisch wären ${UI.fmt(this.total() + amount)} (+ Zinsen ${UI.fmt(chk.interest)} + Meds ${UI.fmt(chk.meds)}).` });
      SFX.play('lose');
      return;
    }
    this.bets.push({ type, n, amount });
    SFX.play('chip');
    this.flyChip(cell, String(amount), this.gen);
    this.renderTable();
    qs('#rouletteStatus', this.root).textContent = 'Chip liegt. Weitere legen oder drehen.';
  },
  undo() { if (this.spinning || !this.bets.length) return; this.bets.pop(); SFX.play('click'); this.renderTable(); },
  clear() { if (this.spinning || !this.bets.length) return; this.bets = []; SFX.play('click'); this.renderTable(); },
  repeat() {
    if (this.spinning || !this.lastBets.length) return;
    if (!Rules.checkSpin(State.s, Rules.rouletteTotal(this.lastBets)).ok) return;
    this.bets = this.lastBets.map((b) => Object.assign({}, b));
    SFX.play('chip');
    this.renderTable();
  },
  async spin() {
    if (this.spinning || !this.root || !this.bets.length) return;
    const bets = this.bets.map((b) => Object.assign({}, b));
    const total = Rules.rouletteTotal(bets);
    if (!Game.beginSpin(total)) return;
    const run = Game.run;
    const gen = this.gen;
    this.spinning = true;
    this.renderTable();
    try {
      qs('#rtable', this.root).classList.add('locked');
      qsa('.chip.placed', this.root).forEach((c) => c.remove());
      qs('#rouletteStatus', this.root).textContent = 'Kugel rollt…';
      qs('#resultNum', this.root).className = 'result-num';
      let rolled = Rules.rouletteRoll(Math.random);
      const ti = Rules.rouletteLuckTarget(bets);
      if (ti >= 0) rolled = Rules.rouletteLuckOverride(bets[ti].type, bets[ti].n, rolled, Rules.luck(State.s), Math.random);
      const targetIdx = Rules.WHEEL.indexOf(rolled);
      const sliceDeg = 360 / 37;
      const targetDeg = (360 - targetIdx * sliceDeg) % 360;
      const currentMod = this.wheelDeg % 360;
      let diff = targetDeg - currentMod;
      if (diff <= 0) diff += 360;
      this.wheelDeg += 5 * 360 + diff;
      this.drawWheel(-1);
      qs('#wheelCanvas', this.root).style.transform = `rotate(${this.wheelDeg}deg)`;
      this.animateBall(4000, gen);
      await wait(4100);
      const result = Rules.rouletteSettle(bets, rolled);
      const delta = result.payout - total;
      this.lastBets = bets;
      this.bets = [];
      if (this.alive(gen)) {
        this.drawWheel(targetIdx);
        const res = qs('#resultNum', this.root);
        res.textContent = rolled;
        res.className = `result-num show ${rolled === 0 ? 'green' : Rules.isRed(rolled) ? 'red' : 'black'}`;
        const colName = rolled === 0 ? '🟢 0' : Rules.isRed(rolled) ? `🔴 ${rolled}` : `⚫ ${rolled}`;
        const label = (b) => b.type === 'number' ? String(b.n) : { red: 'Rot', black: 'Schwarz', even: 'Gerade', odd: 'Ungerade' }[b.type];
        const parts = result.hits.map((x) => x.win ? `${label(x.bet)} ✓ +${UI.fmt(x.payout - x.bet.amount)}` : `${label(x.bet)} ✗`);
        qs('#rouletteStatus', this.root).innerHTML = delta > 0
          ? `<span class="win">${colName} · ${parts.join(' · ')} → +${UI.fmt(delta)}</span>`
          : delta === 0 ? `<span>${colName} · ${parts.join(' · ')} → ±0</span>`
          : `<span class="loss">${colName} · ${parts.join(' · ')} → −${UI.fmt(-delta)}</span>`;
        this.bets = bets; this.renderTable(result); this.bets = [];   // Marker mit Gewinn/Verlust-Farbe stehen lassen
        setTimeout(() => { if (this.alive(gen) && !this.spinning) this.renderTable(); }, 1400);
      }
      await Bus.emit('roulette:result', { bets, rolled, payout: result.payout, hits: result.hits, total, win: delta > 0 });
      await Game.settle(delta, { from: this.alive(gen) ? qs('.wheel-box', this.root) : null, game: 'roulette', bet: total, run });
    } finally {
      if (this.gen === gen) {
        this.spinning = false;
        qs('#rtable', this.root).classList.remove('locked');
        this.renderTable();
      }
    }
  },
```

In `buildTable()` jede Zelle mit `'data-key': type === 'number' ? \`n${chosen}\` : type` versehen (im `cell(...)`-Helfer: `h('button', { class: …, style, 'data-key': type === 'number' ? \`n${chosen}\` : type, onclick: … }, label)`).

`UI.register('roulette', …)` – `mount`: nach `Game.bindBet(root, 'rouletteBet');` ergänzen:

```js
    Roulette.bets = [];
    qs('#btnSpin', root).addEventListener('click', () => Roulette.spin());
    qs('#btnUndo', root).addEventListener('click', () => Roulette.undo());
    qs('#btnClear', root).addEventListener('click', () => Roulette.clear());
    qs('#btnRepeat', root).addEventListener('click', () => Roulette.repeat());
    Roulette.renderTable();
```

`unmount`: zusätzlich `Roulette.bets = [];` (liegende, unbezahlte Chips verfallen ohne Buchung – es wurde nichts abgezogen).

Hinweis zu `flyChip`: der Chip landet weiterhin als `.chip.placed` auf der Zelle; `renderTable()` zeichnet zusätzlich den Summen-Marker. Beim Dreh werden die `.chip.placed` entfernt (wie bisher), die Marker bleiben und färben sich.

- [ ] **Step 4: Trophäe „Plein"**

Block `achievements`: `Bus.on('roulette:result', ({ type, win }) => { if (type === 'number' && win) Achievements.unlock('plein'); });` → `Bus.on('roulette:result', ({ hits }) => { if ((hits || []).some((x) => x.win && x.bet.type === 'number')) Achievements.unlock('plein'); });`

Suche außerdem nach weiteren Konsumenten von `roulette:result` (`grep -n "roulette:result" keller37.html`) – Story-Events nutzen `spin:after`, nicht dieses Event; falls doch etwas `type`/`chosen` liest, auf `hits` umstellen.

- [ ] **Step 5: Tests und Sichtprüfung**

Run: `node tests/run-selftest.mjs`, `tests/dom-selftest.sh`. Browser (CDP-Skript im Scratchpad oder Konsole): `?fresh&screen=roulette`, `Game.applyDelta(1000)`, Chip 10 auf 17, Chip 50 auf Rot, Chip 20 auf Gerade → Leiste „Auf dem Tisch: 80 € · 3 Chips", Marker „10"/„50"/„20"; „Chip zurück" entfernt den 20er; `Math.random`-Stub so, dass 18 fällt (`Rules.rouletteRoll` = `floor(rng()*37)` → rng = 18.5/37) → nach dem Dreh Kontostand 1050 − 60 + 100 = +40 netto, Status „🔴 18 · 17 ✗ · Rot ✓ +50 → +40 €"; „Wie zuletzt" legt die zwei Chips wieder. Screenshot `roulette-chips.png` mit liegenden Chips.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(roulette): mehrere Chips pro Dreh – legen, zurück, leeren, wie zuletzt; eine Kugel wertet alles aus

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Playtest-Szenario, Screenshots, Checkliste

**Files:**
- Modify: `tests/playtest-story.py` (neues Szenario `scenario_roulette_chips`, Anpassung „27 %" → „7 %")
- Modify: `docs/superpowers/screenshots/roulette.png`, `finance.png`, `invest.png` (erneuern), Create: `roulette-chips.png`
- Create: `docs/superpowers/checklist-tisch-2026-09-17.md`

**Interfaces:**
- Consumes: alles aus Task 1–3 (`Roulette.place/undo/clear/repeat/spin`, `#tableTotal`, `.chip-stack`, `#bankHint`, `.inv-running`).

- [ ] **Step 1: Szenario schreiben**

Vor `async def main():`:

```python
async def scenario_roulette_chips(cdp):
    """Roulette: Chips legen/zurueck/leeren, ein Dreh wertet alles aus, Wie zuletzt; Bank-Sperre; Anlagen-Sperre."""
    await cdp.navigate(URL_BASE + "?fresh&screen=roulette")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.eval("State.s.balance = 1000; State.save(); UI.setBalance(1000, {animate:false}); 0", await_promise=False)
    await cdp.eval("document.querySelector('#rouletteBet').value = 10; Roulette.place('number', 17, Roulette.cellFor('number', 17)); 0", await_promise=False)
    await cdp.eval("document.querySelector('#rouletteBet').value = 50; Roulette.place('red', null, Roulette.cellFor('red', null)); 0", await_promise=False)
    await cdp.eval("document.querySelector('#rouletteBet').value = 20; Roulette.place('even', null, Roulette.cellFor('even', null)); 0", await_promise=False)
    await asyncio.sleep(0.6)
    total = await cdp.eval("document.querySelector('#tableTotal').textContent", await_promise=False)
    stacks = await cdp.eval("[...document.querySelectorAll('.chip-stack')].map(e=>e.dataset.key+':'+e.textContent).sort().join(',')", await_promise=False)
    record("roulette: drei Chips liegen, Summe 80", total is not None and "80 €" in total and "3 Chips" in total and stacks == "even:20,n17:10,red:50", "total=%s stacks=%s" % (total, stacks))
    await cdp.screenshot("roulette-chips.png")
    await cdp.click("#btnUndo")
    await asyncio.sleep(0.2)
    n = await cdp.eval("Roulette.bets.length", await_promise=False)
    record("roulette: Chip zurueck entfernt den letzten", n == 2, "bets=%s" % n)
    await cdp.click("#btnClear")
    await asyncio.sleep(0.2)
    n = await cdp.eval("Roulette.bets.length", await_promise=False)
    spin_disabled = await cdp.eval("document.querySelector('#btnSpin').disabled", await_promise=False)
    record("roulette: Tisch leeren, Drehen gesperrt", n == 0 and spin_disabled is True, "bets=%s disabled=%s" % (n, spin_disabled))
    # erneut legen, Ergebnis 18 (rot, gerade) erzwingen: rouletteRoll = floor(rng*37) -> rng = 18.5/37; Luck ist 0
    await cdp.eval("document.querySelector('#rouletteBet').value = 10; Roulette.place('number', 17, Roulette.cellFor('number', 17)); document.querySelector('#rouletteBet').value = 50; Roulette.place('red', null, Roulette.cellFor('red', null)); 0", await_promise=False)
    await cdp.eval("window.__origRandom = Math.random; Math.random = () => 18.5/37; 0", await_promise=False)
    await cdp.click("#btnSpin")
    await asyncio.sleep(0.3)
    bal_mid = await cdp.eval("State.s.balance", await_promise=False)
    record("roulette: Einsatz 60 einmal abgezogen (Escrow)", bal_mid == 940, "bal=%s" % bal_mid)
    await asyncio.sleep(4.6)
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    status = await cdp.eval("document.querySelector('#rouletteStatus').textContent", await_promise=False)
    record("roulette: 18 -> 17 verliert, Rot gewinnt, netto +40", bal == 1040 and status is not None and "Rot ✓ +50" in status and "17 ✗" in status, "bal=%s status=%s" % (bal, status))
    last = await cdp.eval("JSON.stringify(Roulette.lastBets)", await_promise=False)
    await cdp.click("#btnRepeat")
    await asyncio.sleep(0.3)
    again = await cdp.eval("JSON.stringify(Roulette.bets)", await_promise=False)
    record("roulette: Wie zuletzt legt dieselben Chips", last is not None and again == last, "last=%s again=%s" % (last, again))
    # Bank: ein Kredit auf einmal
    await cdp.eval("UI.show('finance'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.eval("Finance.loanBank(500); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.3)
    disabled = await cdp.eval("[...document.querySelectorAll('[data-loan]')].every(b=>b.disabled)", await_promise=False)
    hint = await cdp.eval("document.querySelector('#bankHint').textContent", await_promise=False)
    debt = await cdp.eval("State.s.bankDebt", await_promise=False)
    record("bank: bei offenem Kredit alle Kredit-Knoepfe gesperrt, Hinweis sichtbar", debt == 500 and disabled is True and hint is not None and "tilgen" in hint, "debt=%s disabled=%s hint=%s" % (debt, disabled, hint))
    terms = await cdp.eval("document.querySelector('#bankTerms').textContent", await_promise=False)
    record("bank: Konditionen 8 %", terms is not None and "8 %" in terms, "terms=%s" % terms)
    await cdp.screenshot("story-free-finance.png")
    # Anlagen: je Sorte eine
    await cdp.eval("UI.show('invest'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.eval("document.querySelector('#invBank').value = 20; Invest.invest('bank'); 0", await_promise=False)
    await asyncio.sleep(0.4)
    running = await cdp.eval("document.querySelector('.chalk.inv[data-type=bank] .inv-running').textContent", await_promise=False)
    form_hidden = await cdp.eval("document.querySelector('.chalk.inv[data-type=bank] .inv-form').classList.contains('hidden')", await_promise=False)
    inv = await cdp.eval("JSON.stringify(State.s.investments)", await_promise=False)
    record("anlagen: Festgeld laeuft, Karte zeigt laufende Anlage, Eingabe weg", form_hidden is True and running is not None and "20 €" in running and "6 Spins" in running and inv is not None and '"type":"bank"' in inv, "running=%s hidden=%s inv=%s" % (running, form_hidden, inv))
    bal_before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("Invest.invest('bank'); 0", await_promise=False)
    await asyncio.sleep(0.3)
    bal_after = await cdp.eval("State.s.balance", await_promise=False)
    n_inv = await cdp.eval("State.s.investments.length", await_promise=False)
    record("anlagen: zweites Festgeld abgelehnt", bal_after == bal_before and n_inv == 1, "before=%s after=%s n=%s" % (bal_before, bal_after, n_inv))
    await cdp.screenshot("story-free-invest.png")
```

Falls `Invest.invest('bank')` ohne sichtbares Formular an `qs('#invBank')` scheitert (Eingabe ist bei laufender Anlage versteckt, aber im DOM): der Wert wird vorher gesetzt; sollte `invest()` bei versteckter Eingabe früher abbrechen, `Rules.canInvest` liefert ohnehin `running` – der Check bleibt gültig.

In `main()` nach `await scenario_story_stadt(cdp)`:

```python
        await scenario_roulette_chips(cdp)
```

In `scenario_stadt_shop`: `"27 %" in terms` → `"7 %" in terms`.

- [ ] **Step 2: Playtest laufen lassen**

Run: `python3 -u tests/playtest-story.py` (zweimal) und `python3 -u tests/playtest-story.py --mobile`
Expected: `fehlgeschlagen: 0`, `ERRORS 0`. Die Pixel-Diff-Referenz `roulette.png` ändert sich durch die neue Tischleiste – bewusst erneuern (`cp /tmp/k37story/story-free-roulette.png docs/superpowers/screenshots/roulette.png`) und in der Checkliste nennen; Diff-Schwelle nicht anheben.

- [ ] **Step 3: Screenshots**

`roulette-chips.png`, `story-free-finance.png` → `finance.png`, `story-free-invest.png` → `invest.png` nach `docs/superpowers/screenshots/` kopieren und mit dem Read-Tool prüfen (Marker auf den Feldern, Tischleiste, Hinweis unter den Kredit-Knöpfen, „Läuft: …" an der Festgeld-Karte).

- [ ] **Step 4: Checkliste**

`docs/superpowers/checklist-tisch-2026-09-17.md`: eine Zeile je Spec-Anforderung (§2.1–2.4, §3, §4) mit Nachweis (Selftest-Name, Playtest-Check, Screenshot).

- [ ] **Step 5: Commit**

```bash
git add tests/playtest-story.py docs/superpowers/screenshots docs/superpowers/checklist-tisch-2026-09-17.md
git commit -m "test: Playtest für Roulette-Chips, Kredit-Sperre, Anlagen-Sperre; Screenshots; Checkliste

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec-Abdeckung:** §2.1 Datenmodell → T3; §2.2 Bedienung (Chip-Wert, Schnellwahl 10/50/100/500/Max, Leiste, Buttons, `checkSpin` beim Legen, Sperre während Kugel) → T3; §2.3 Auswertung (Escrow einmal, Luck-Target, Anzeige, `lastBets`, Bus-Event, Plein, „Verzockt" über `loss`) → T1/T3; §2.4 reine Regeln → T1; §3 Bank (8 %, Mercedes, ein Kredit, Hinweis, Szene dynamisch, Game-Over-Ruling) → T1/T2; §4 Anlagen (Werte, je Sorte eine, Karte, Text, alte Anlagen) → T1/T2; §5 Technik → T1–T3; §6 Tests → T1 (Node), T4 (Browser); README → T2.

**Rulings im Plan:** (a) `isGameOver` prüft `bankDebt > 0` statt `bankDebt >= limit`, weil mit „ein Kredit" jede offene Schuld die Bank schließt – Spec §3 sagt „unverändert", die Absicht (beide Quellen zu) bleibt; (b) Schnellwahl-Chips 10/50/100/500/Max wie in der Spec (heute 10/25/50/Max).

**Platzhalter:** keine. **Typ-Konsistenz:** `rouletteSettle → { payout, hits: [{ bet, win, payout }] }` in T1 und T3 identisch; `bankLoanReason` `'open' | 'limit' | null` in T1/T2; `investRunning`/`canInvest` in T1/T2/T4; DOM-IDs `#tableTotal/#btnSpin/#btnUndo/#btnClear/#btnRepeat/#bankHint/.inv-running/.inv-form/.chip-stack[data-key]` in T2/T3/T4 identisch; `Roulette.cellFor(type, n)` in T3 definiert und in T4 genutzt.
