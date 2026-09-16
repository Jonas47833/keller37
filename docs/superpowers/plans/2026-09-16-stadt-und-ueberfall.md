# Stadt (Autos & Schuhe) und Überfälle – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein Laden „Stadt" mit Autos (Audi-/Mercedes-Linie) und INTERSPORT-Schuhen als dauerhafte Upgrades, plus Überfälle auf dem Weg in den Keller, die das Attribut Stärke aufbauen – in beiden Modi von KELLER 37.

**Architecture:** Alle Zahlen und Regeln leben in einem neuen reinen Block `gear-rules` (`Rules.GEAR`, `Rules.MUG`, `Rules.gear(s)` …). Bestehende Regeln (`luck`, Bank, Postbote, Spüler, Taxi, Türsteher) lesen nur `Rules.gear(s)`. Ein Screen `stadt` verkauft, ein Modul `Mugging` hängt an genau zwei Stellen (Hub → Casino-Tür im freien Spiel, Morgen → Abend in der Story). Story 1 bekommt ein Freischalt-Event und den Job „Eintreiber".

**Tech Stack:** Vanilla HTML/CSS/JS in `keller37.html` (Ein-Datei-Vorgabe), Node-Selftest (`node tests/run-selftest.mjs`), headless-Chrome-Playtest (`python3 tests/playtest-story.py`).

**Spec:** `docs/superpowers/specs/2026-09-16-stadt-und-ueberfall-design.md`

## Global Constraints

- Alles bleibt in der einen Datei `keller37.html`; neue Logik als `<script id="…">`-Blöcke: `gear-rules` (direkt nach `rules`), `room-stadt` (direkt nach `rooms`), `mugging` (direkt nach `gameover`, vor `story-rules`).
- `State.VERSION` bleibt `1`; neue Felder werden durch `Object.assign(fresh, saved)` aufgefüllt – kein Reset bestehender Spielstände.
- Alle Zahlen ausschließlich in `Rules.GEAR` / `Rules.MUG`; kein Spiel liest `s.car`/`s.shoes`/`s.strength` direkt, nur `Rules.gear(s)` bzw. die Mug-Funktionen (Ausnahme: Anzeige-Code und Kauf-Code im Screen `stadt`).
- Glück aus Ausrüstung max +4 %; Beute pro Überfall 50–1.500 € (+10 % bei missglückter Flucht); Kontostand fällt nie unter 0; Stärke sinkt nie.
- Katalog exakt wie Spec §2.2 (Namen, Preise, Boni); Kosten beim Autokauf `max(0, Preis − 0,5 × Preis des alten Autos)`.
- Überfall nie bei `Cutscene.active`, `Game.inFlight > 0`, `Game.gameOverPending`, `Story.sleeping`; Cooldown 15 Spins (nur `State.mode === 'free'`) bzw. 3 Story-Tage (nur `advanceDay`).
- Deutsch, Ton „Seedy Underground", typografische Anführungszeichen „…" in Spieltexten.
- Vor jedem Commit: `node tests/run-selftest.mjs` grün; Browser-Selftest `tests/dom-selftest.sh` grün.
- Commits enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## Orientierung im Code (für alle Tasks)

- Hilfsfunktionen (Block `util`): `qs(sel, root)`, `qsa(sel, root)`, `h(tag, attrs, ...children)` (Attribut `onclick` = Handler, `class` = Klassen, `null`-Kinder werden ignoriert), `wait(ms)`, `pick(arr)`, `rand(a, b)`.
- `State.s` = aktueller Spielstand (beide Modi), `State.mode` = `'free' | 'story'`, `State.save()`. Im Story-Modus liegt der Story-Teil unter `State.s.story` (`day`, `phase`, `unlocked.rooms`, `vars`, `flags`, `jobsDone`, `stats`).
- `Game.applyDelta(delta, { from, quiet })` bucht Geld mit Animation; `Game.inFlight`, `Game.gameOverPending`.
- `UI.show(id)` wechselt Screens (Templates `tpl-<id>`, `UI.register(id, { template, mount(root), unmount() })`); `UI.toast({ icon, title, text, tone })`; `UI.fmt(n)` formatiert Euro; `UI.renderSide()` / `UI.renderWallet()` zeichnen Seitenleiste / Kopfzeile neu; `Actions.<name>` = Handler für Seitenleisten-Buttons (`data-action`).
- `Cutscene.define(id, panels | (ctx) => panels)`, `Cutscene.play(id, ctx)` → Promise mit dem Wert der zuletzt getroffenen Wahl (`choices: [{ label, value, cls }]`); Panel-Felder `bg`, `who`, `mood` (`calm|happy|angry|shock|dead`), `text` (mit `{{platzhalter}}`), `fx` (`flash|shake|drain|gain|blackout|stats|hearts`). Hintergründe brauchen eine CSS-Regel `.cs-bg.<name>` und optional Props in `Cutscene.PROPS`; Figuren stehen in `Cutscene.CAST`.
- Story: `Story.s` = `State.s.story`, `Story.story` = aktive Story-Definition, `Story.roomUnlocked(r)`, `Story.isLocked(screen)`, `Story.ROOM_OF`, `Story.evening()`, `Story.playScene(id)`, `Jobs.POOL`, `Jobs.runShift(job)`, `StoryRules.check(cond, s)`, `StoryRules.applyEffect`, `StoryRules.validate(story, sceneIds, jobIds)`, `StoryRules.advanceDay(s)`.
- Selftests: Block `selftest`, Helfer `T.test(name, fn)`, `T.eq(a, b)` (JSON-Vergleich), `T.ok(v)`, `base(o)` (freier Spielstand), `storyBase(o)` (Story-Spielstand); neue Fälle vor der Zeile `/* --- SELFTEST CASES END --- */` einfügen. Der Node-Runner `tests/run-selftest.mjs` lädt nur die Blöcke aus seiner Liste – **`gear-rules` muss dort eingetragen werden (Task 1)**.
- Dev-Parameter (Block `boot`): `?fresh`, `?screen=<id>`, `?scene=<id>`, `?mode=story`, `?story=<id>`, `?day=<n>`, `?job=<id>`, `?selftest`.
- Playtest: `tests/playtest-story.py` (CDP-Helfer `cdp.navigate(url)`, `cdp.eval(js, await_promise=False)`, `cdp.click(sel)`, `cdp.screenshot(name)`, `cdp.advance_cutscene(label_hint=…)` klickt Panels weiter und wählt die Choice mit passendem Label, `record(name, ok, detail)`); Screenshots landen in `docs/superpowers/screenshots/`.

---

### Task 1: Regeln – Katalog, `Rules.gear`, Kaufregeln, Überfall-Rechnung, State-Felder

**Files:**
- Modify: `keller37.html` – `State.fresh()` (Block `state`, ~Zeile 1096), neuer Block `gear-rules` direkt nach `</script>` des Blocks `rules` (~Zeile 1085), Selftests vor `/* --- SELFTEST CASES END --- */`
- Modify: `tests/run-selftest.mjs` – Blockliste

**Interfaces:**
- Produces: `Rules.GEAR`, `Rules.MUG`, `Rules.gear(s) → { luck, mugMult, flee, bankLimit, bankRate, postTime, postPay, spuelerBand, taxiTip }`, `Rules.carUpgradeCost(s, id) → number`, `Rules.canBuyCar(s, id) → { ok, reason?, cost }`, `Rules.canBuyShoes(s, id) → { ok, reason? }`, `Rules.mugChance(s, where) → 0..1`, `Rules.mugLoot(balance) → number`, `Rules.mugWallet(rng) → 50..150`, `Rules.fightChance(strength) → 0..0.9`, `Rules.fleeChance(gear) → 0..0.9`, `Rules.fleeFailExtra(balance) → number`; State-Felder `car`, `shoes`, `strength`, `mugCooldown`, `stats.muggings`, `stats.fightsWon`.

- [ ] **Step 1: Runner-Liste erweitern**

In `tests/run-selftest.mjs` die Zeile

```js
for (const id of ['rules', 'util', 'state', 'bus', 'story-rules', 'story-probe', 'story-schuld', 'selftest']) {
```

ersetzen durch

```js
for (const id of ['rules', 'gear-rules', 'util', 'state', 'bus', 'story-rules', 'story-probe', 'story-schuld', 'selftest']) {
```

- [ ] **Step 2: Fehlschlagende Tests schreiben**

Vor `/* --- SELFTEST CASES END --- */` einfügen:

```js
/* ---- Gear: Katalog, Boni, Kauf ---- */
const near = (a, b, msg = '') => T.ok(Math.abs(a - b) < 1e-9, `${msg} erwartet ${b}, bekommen ${a}`);
T.test('GEAR: Preise steigen je Linie, Glück ≤ 4, Zinsen sinken', () => {
  const cars = Rules.GEAR.cars;
  for (const brand of ['audi', 'merc']) {
    const line = Object.values(cars).filter((c) => c.brand === brand).sort((a, b) => a.tier - b.tier);
    T.eq(line.length, 3, brand);
    for (let i = 1; i < line.length; i++) T.ok(line[i].price > line[i - 1].price, `${brand} Preis Stufe ${i + 1}`);
  }
  for (const c of Object.values(cars)) T.ok((c.luck || 0) <= 4, c.name);
  const merc = Object.values(cars).filter((c) => c.brand === 'merc').sort((a, b) => a.tier - b.tier);
  T.ok(merc[0].bankRate > merc[1].bankRate && merc[1].bankRate > merc[2].bankRate, 'Zinsen sinken');
  const shoes = Object.values(Rules.GEAR.shoes).sort((a, b) => a.tier - b.tier);
  T.eq(shoes.map((s) => s.price), [300, 2000, 7500]);
  T.ok(cars.audiR8.flee + shoes[2].flee <= 80, 'Flucht-Summe ≤ 80');
});
T.test('gear: ohne Ausrüstung neutral', () => {
  T.eq(Rules.gear(base()), { luck: 0, mugMult: 1, flee: 0, bankLimit: 3000, bankRate: 0.3, postTime: 0, postPay: 0, spuelerBand: 0, taxiTip: 0 });
});
T.test('gear: Audi R8 + Carbon', () => {
  const g = Rules.gear(base({ car: 'audiR8', shoes: 'carbon' }));
  T.eq([g.luck, g.mugMult, g.flee, g.bankLimit, g.bankRate, g.postTime, g.postPay, g.spuelerBand, g.taxiTip], [4, 0.2, 80, 3000, 0.3, 2, 10, 0.2, 5]);
});
T.test('gear: Mercedes G', () => {
  const g = Rules.gear(base({ car: 'mercG' }));
  T.eq([g.luck, g.mugMult, g.flee, g.bankLimit, g.bankRate], [4, 1, 0, 10000, 0.2]);
});
T.test('gear: Stärke 10 halbiert mugMult', () => {
  near(Rules.gear(base({ strength: 10 })).mugMult, 0.5);
  near(Rules.gear(base({ strength: 10, car: 'audiA3' })).mugMult, 0.35);
  near(Rules.gear(base({ strength: 9 })).mugMult, 1);
});
T.test('carUpgradeCost / canBuyCar', () => {
  T.eq(Rules.carUpgradeCost(base(), 'audiA3'), 1500);
  T.eq(Rules.carUpgradeCost(base({ car: 'audiA3' }), 'audiRS4'), 8000 - 750);
  T.eq(Rules.carUpgradeCost(base({ car: 'audiA3' }), 'mercC'), 2000 - 750);
  T.eq(Rules.carUpgradeCost(base({ car: 'audiR8' }), 'mercC'), 0, 'nie Geld zurück');
  T.eq(Rules.canBuyCar(base({ car: 'audiRS4', balance: 99999 }), 'audiA3').reason, 'downgrade');
  T.eq(Rules.canBuyCar(base({ car: 'audiA3', balance: 99999 }), 'audiA3').reason, 'owned');
  T.eq(Rules.canBuyCar(base({ balance: 1499 }), 'audiA3').reason, 'funds');
  T.eq(Rules.canBuyCar(base({ balance: 1500 }), 'audiA3'), { ok: true, cost: 1500 });
  T.eq(Rules.canBuyCar(base({ car: 'audiA3', balance: 7250 }), 'audiRS4'), { ok: true, cost: 7250 });
  T.eq(Rules.canBuyCar(base({ car: 'audiR8', balance: 25000 }), 'mercG'), { ok: true, cost: 25000 });
});
T.test('canBuyShoes: nur Aufstieg, Sprung erlaubt, voller Preis', () => {
  T.eq(Rules.canBuyShoes(base({ balance: 7500 }), 'carbon'), { ok: true });
  T.eq(Rules.canBuyShoes(base({ shoes: 'basic', balance: 7500 }), 'carbon'), { ok: true });
  T.eq(Rules.canBuyShoes(base({ shoes: 'carbon', balance: 99999 }), 'trail').reason, 'downgrade');
  T.eq(Rules.canBuyShoes(base({ shoes: 'trail', balance: 99999 }), 'trail').reason, 'owned');
  T.eq(Rules.canBuyShoes(base({ balance: 299 }), 'basic').reason, 'funds');
});
/* ---- Überfall-Rechnung ---- */
const mugBase = (o = {}) => base(Object.assign({ balance: 500, mugCooldown: 0, strength: 0, stats: { spins: 20 } }, o));
T.test('mugChance: Schwellen', () => {
  T.eq(Rules.mugChance(mugBase({ balance: 99 }), 'door'), 0);
  T.eq(Rules.mugChance(mugBase({ mugCooldown: 1 }), 'door'), 0);
  T.eq(Rules.mugChance(mugBase({ stats: { spins: 9 } }), 'door'), 0);
  near(Rules.mugChance(mugBase(), 'door'), 0.06);
  near(Rules.mugChance(mugBase({ balance: 2000 }), 'door'), 0.12);
  near(Rules.mugChance(mugBase({ car: 'audiA3' }), 'door'), 0.042);
});
T.test('mugChance: Abend in der Story', () => {
  const s3 = storyBase({ day: 3 }); s3.balance = 500; s3.mugCooldown = 0; s3.stats = { spins: 0 };
  T.eq(Rules.mugChance(s3, 'evening'), 0);
  const s4 = storyBase({ day: 4 }); s4.balance = 500; s4.mugCooldown = 0; s4.stats = { spins: 0 };
  near(Rules.mugChance(s4, 'evening'), 0.12);
});
T.test('mugLoot: 20 %, 50–1500, nie mehr als Bargeld', () => {
  T.eq(Rules.mugLoot(100), 50); T.eq(Rules.mugLoot(1000), 200); T.eq(Rules.mugLoot(10000), 1500);
  T.eq(Rules.mugLoot(60), 50); T.eq(Rules.mugLoot(30), 30);
});
T.test('fightChance / fleeChance / Deckel', () => {
  near(Rules.fightChance(0), 0.35); near(Rules.fightChance(3), 0.59); near(Rules.fightChance(7), 0.9); near(Rules.fightChance(50), 0.9);
  near(Rules.fleeChance({ flee: 0 }), 0.3); near(Rules.fleeChance({ flee: 45 }), 0.75); near(Rules.fleeChance({ flee: 80 }), 0.9);
  T.eq(Rules.fleeFailExtra(1000), 100);
});
T.test('mugWallet: 50–150', () => {
  T.eq(Rules.mugWallet(() => 0), 50); T.eq(Rules.mugWallet(() => 0.999), 150);
});
T.test('State.fresh: Gear-Felder', () => {
  const f = State.fresh();
  T.eq([f.car, f.shoes, f.strength, f.mugCooldown, f.stats.muggings, f.stats.fightsWon], [null, null, 0, 0, 0, 0]);
});
```

- [ ] **Step 3: Tests laufen lassen – sie müssen fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: Abbruch mit `Script-Block "gear-rules" fehlt` (der Runner wirft, weil der Block noch nicht existiert).

- [ ] **Step 4: State-Felder ergänzen**

In `State.fresh()` (Block `state`) die Zeilen

```js
      hasHouse: false, isMarried: false, marriageSpins: 0, isHeartbroken: false, hasDealer: false,
      flags: { intro: false, mafiaLoan: false, bankLoan: false, bankLimit: false, brownie: false, igor: false },
      stats: { spins: 0, maxBalance: 50, biggestWin: 0, kidneys: 0, postStreakBest: 0 },
```

ersetzen durch

```js
      hasHouse: false, isMarried: false, marriageSpins: 0, isHeartbroken: false, hasDealer: false,
      car: null, shoes: null, strength: 0, mugCooldown: 0,
      flags: { intro: false, mafiaLoan: false, bankLoan: false, bankLimit: false, brownie: false, igor: false },
      stats: { spins: 0, maxBalance: 50, biggestWin: 0, kidneys: 0, postStreakBest: 0, muggings: 0, fightsWon: 0 },
```

- [ ] **Step 5: Block `gear-rules` anlegen**

Direkt nach dem `</script>` des Blocks `<script id="rules">` einfügen:

```html
<script id="gear-rules">
/* ================= GEAR – Autos, Schuhe, Stärke, Überfall-Rechnung (rein, kein DOM, kein State) ================= */
Object.assign(Rules, {
  GEAR: {
    cars: {
      audiA3:  { brand: 'audi', tier: 1, name: 'Audi A3 (gebraucht)', icon: '🚗', price: 1500,  mugMult: 0.7,  flee: 10, luck: 0 },
      audiRS4: { brand: 'audi', tier: 2, name: 'Audi RS 4 quattro',   icon: '🏎️', price: 8000,  mugMult: 0.45, flee: 20, luck: 2 },
      audiR8:  { brand: 'audi', tier: 3, name: 'Audi R8',             icon: '🏎️', price: 30000, mugMult: 0.2,  flee: 35, luck: 4 },
      mercC:   { brand: 'merc', tier: 1, name: 'Mercedes C-Klasse',   icon: '🚙', price: 2000,  bankLimit: 4000,  bankRate: 0.27, luck: 0 },
      mercS:   { brand: 'merc', tier: 2, name: 'Mercedes S-Klasse',   icon: '🚘', price: 10000, bankLimit: 6000,  bankRate: 0.24, luck: 2 },
      mercG:   { brand: 'merc', tier: 3, name: 'Mercedes AMG G 63',   icon: '🚐', price: 40000, bankLimit: 10000, bankRate: 0.20, luck: 4 },
    },
    shoes: {
      basic:  { tier: 1, name: 'Laufschuh Basic',  icon: '👟', price: 300,  flee: 15, postTime: 1, postPay: 0,  spuelerBand: 0,   taxiTip: 0 },
      trail:  { tier: 2, name: 'Trail-Runner Pro', icon: '👟', price: 2000, flee: 30, postTime: 1, postPay: 5,  spuelerBand: 0.2, taxiTip: 0 },
      carbon: { tier: 3, name: 'Carbon-Sprinter',  icon: '👟', price: 7500, flee: 45, postTime: 2, postPay: 10, spuelerBand: 0.2, taxiTip: 5 },
    },
    TRADE_IN: 0.5,
    BRANDS: { audi: 'Audi Zentrum', merc: 'Mercedes-Benz Niederlassung' },
  },
  MUG: {
    BASE_DOOR: 0.06, BASE_EVENING: 0.12,
    MIN_CASH: 100, RICH_CASH: 2000, RICH_MULT: 2,
    MIN_SPINS: 10, MIN_DAY: 4,
    COOLDOWN_SPINS: 15, COOLDOWN_DAYS: 3,
    LOOT_PCT: 0.2, LOOT_MIN: 50, LOOT_MAX: 1500, FLEE_FAIL_PCT: 0.1,
    FIGHT_BASE: 0.35, FIGHT_PER_STR: 0.08, FLEE_BASE: 0.3, CHANCE_CAP: 0.9,
    STR_WALLET: 5, WALLET_MIN: 50, WALLET_MAX: 150,
    STR_FEARED: 10, FEARED_MULT: 0.5,
    STR_RESPECT: 8,
  },
  /* Alle Boni der aktuellen Ausrüstung – immer alle Schlüssel, neutral = ohne Ausrüstung */
  gear(s) {
    const car = s.car ? Rules.GEAR.cars[s.car] : null;
    const sh = s.shoes ? Rules.GEAR.shoes[s.shoes] : null;
    const feared = (s.strength || 0) >= Rules.MUG.STR_FEARED ? Rules.MUG.FEARED_MULT : 1;
    return {
      luck: car ? car.luck || 0 : 0,
      mugMult: (car && car.mugMult != null ? car.mugMult : 1) * feared,
      flee: (car ? car.flee || 0 : 0) + (sh ? sh.flee || 0 : 0),
      bankLimit: car && car.bankLimit ? car.bankLimit : Rules.BANK_LIMIT,
      bankRate: car && car.bankRate ? car.bankRate : Rules.BANK_RATE,
      postTime: sh ? sh.postTime || 0 : 0,
      postPay: sh ? sh.postPay || 0 : 0,
      spuelerBand: sh ? sh.spuelerBand || 0 : 0,
      taxiTip: sh ? sh.taxiTip || 0 : 0,
    };
  },
  carUpgradeCost(s, id) {
    const car = Rules.GEAR.cars[id];
    const old = s.car ? Rules.GEAR.cars[s.car] : null;
    return Math.max(0, car.price - (old ? Math.round(old.price * Rules.GEAR.TRADE_IN) : 0));
  },
  canBuyCar(s, id) {
    const car = Rules.GEAR.cars[id];
    if (!car) return { ok: false, reason: 'unknown', cost: 0 };
    const cost = Rules.carUpgradeCost(s, id);
    if (s.car === id) return { ok: false, reason: 'owned', cost };
    const old = s.car ? Rules.GEAR.cars[s.car] : null;
    if (old && old.brand === car.brand && car.tier < old.tier) return { ok: false, reason: 'downgrade', cost };
    if (s.balance < cost) return { ok: false, reason: 'funds', cost };
    return { ok: true, cost };
  },
  canBuyShoes(s, id) {
    const sh = Rules.GEAR.shoes[id];
    if (!sh) return { ok: false, reason: 'unknown' };
    if (s.shoes === id) return { ok: false, reason: 'owned' };
    const old = s.shoes ? Rules.GEAR.shoes[s.shoes] : null;
    if (old && sh.tier < old.tier) return { ok: false, reason: 'downgrade' };
    if (s.balance < sh.price) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
  /* where: 'door' (freies Spiel, Hub → Casino-Tür) oder 'evening' (Story, Morgen → Abend) */
  mugChance(s, where) {
    const M = Rules.MUG;
    if (s.balance < M.MIN_CASH) return 0;
    if ((s.mugCooldown || 0) > 0) return 0;
    if (where === 'evening') { if (!s.story || s.story.day < M.MIN_DAY) return 0; }
    else if (((s.stats && s.stats.spins) || 0) < M.MIN_SPINS) return 0;
    let c = where === 'evening' ? M.BASE_EVENING : M.BASE_DOOR;
    if (s.balance >= M.RICH_CASH) c *= M.RICH_MULT;
    return c * Rules.gear(s).mugMult;
  },
  mugLoot(balance) {
    const M = Rules.MUG;
    return Math.min(balance, Math.max(M.LOOT_MIN, Math.min(M.LOOT_MAX, Math.round(balance * M.LOOT_PCT))));
  },
  mugWallet(rng = Math.random) {
    const M = Rules.MUG;
    return M.WALLET_MIN + Math.floor(rng() * (M.WALLET_MAX - M.WALLET_MIN + 1));
  },
  fightChance(strength) { const M = Rules.MUG; return Math.min(M.CHANCE_CAP, M.FIGHT_BASE + M.FIGHT_PER_STR * (strength || 0)); },
  fleeChance(gear) { const M = Rules.MUG; return Math.min(M.CHANCE_CAP, M.FLEE_BASE + (gear.flee || 0) / 100); },
  fleeFailExtra(balance) { return Math.round(balance * Rules.MUG.FLEE_FAIL_PCT); },
});
</script>
```

- [ ] **Step 6: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs`
Expected: alle bestanden (84 alte + 14 neue), `0 fehlgeschlagen`.

- [ ] **Step 7: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(gear): Katalog Autos/Schuhe, Rules.gear, Kauf- und Überfall-Rechnung, State-Felder

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Ausrüstung wirkt – Glück, Bank, Postbote, Cooldown, Finanz-Anzeige

**Files:**
- Modify: `keller37.html` – Block `rules`: `luck`, `bankInterest`, `bankLoanAllowed`, `isGameOver`, `postmanTier`; Block `core`: `Game.afterSpin`; Block `ui`: `renderWallet`; Block `rooms`: `Finance.render`; Template `tpl-finance`; Block `game-postman`: Aufruf `postmanTier`; Selftests

**Interfaces:**
- Consumes: `Rules.gear(s)` (Task 1).
- Produces: `Rules.bankInterest(debt, s?)` (ohne `s` → 30 %), `Rules.postmanTier(streak, s?)` (ohne `s` → wie bisher), `Rules.bankLoanAllowed(s, amt)` mit Auto-Limit, `Rules.isGameOver(s)` mit Auto-Limit; `Game.afterSpin` zählt `mugCooldown` im freien Spiel herunter.

- [ ] **Step 1: Fehlschlagende Tests schreiben**

Vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- Ausrüstung wirkt ---- */
T.test('luck: Auto-Glück addiert sich', () => {
  T.eq(Rules.luck(base({ car: 'audiRS4' })), 2);
  T.eq(Rules.luck(base({ car: 'mercG', beers: 3, beerTimer: 1, brownieTimer: 1 })), 64);
});
T.test('bankInterest: Mercedes-Zinssatz', () => {
  T.eq(Rules.bankInterest(1000), 300);
  T.eq(Rules.bankInterest(1000, base()), 300);
  T.eq(Rules.bankInterest(1000, base({ car: 'mercC' })), 270);
  T.eq(Rules.bankInterest(1000, base({ car: 'mercG' })), 200);
  T.eq(Rules.spinCosts(base({ bankDebt: 1000, car: 'mercS' })).interest, 240);
});
T.test('bankLoanAllowed / isGameOver: Mercedes-Limit', () => {
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 3000, car: 'mercC' }), 1000), true);
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 3000, car: 'mercC' }), 1001), false);
  T.eq(Rules.bankLoanAllowed(base({ bankDebt: 3000 }), 1), false);
  T.eq(Rules.isGameOver(base({ bankDebt: 3000, mafiaDebt: 300, balance: 0 })), true);
  T.eq(Rules.isGameOver(base({ bankDebt: 3000, mafiaDebt: 300, balance: 0, car: 'mercC' })), false);
});
T.test('postmanTier: Schuhe geben Zeit und Lohn', () => {
  T.eq(Rules.postmanTier(0), { t: 5, r: 5 });
  T.eq(Rules.postmanTier(0, base({ shoes: 'basic' })), { t: 6, r: 5 });
  T.eq(Rules.postmanTier(11, base({ shoes: 'carbon' })), { t: 2.5, r: 60 });
  T.eq(Rules.postmanTier(2, base({ shoes: 'trail' })), { t: 4, r: 15 });
});
```

- [ ] **Step 2: Tests laufen lassen – fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: 4 FAIL (`luck`, `bankInterest`, `bankLoanAllowed`, `postmanTier`).

- [ ] **Step 3: Regeln umstellen**

Im Block `rules`:

```js
  luck(s) {
    let l = 0;
    if (s.beerTimer > 0) l += Rules.BEER_LUCK[Math.min(s.beers, 3)];
    if (s.brownieTimer > 0) l += Rules.BROWNIE_LUCK;
    l += Rules.gear(s).luck;
    return l;
  },
  bankInterest(debt, s) {
    const rate = s ? Rules.gear(s).bankRate : Rules.BANK_RATE;
    return debt > 0 ? Math.round(debt * rate) : 0;
  },
  spinCosts(s) {
    return { interest: Rules.bankInterest(s.bankDebt, s), meds: s.kidneySold ? Rules.MEDS_PER_SPIN : 0 };
  },
```

```js
  bankLoanAllowed(s, amt) { return s.bankDebt + amt <= Rules.gear(s).bankLimit; },
  /* Game Over: beide Kreditquellen zu und nicht mal ein 1-€-Spin (inkl. Zinsen/Meds) mehr bezahlbar */
  isGameOver(s) {
    const c = Rules.spinCosts(s);
    return s.bankDebt >= Rules.gear(s).bankLimit && s.mafiaDebt > 0 && s.balance < 1 + c.interest + c.meds;
  },
```

```js
  postmanTier(streak, s) {
    const g = s ? Rules.gear(s) : { postTime: 0, postPay: 0 };
    const t = streak < 2 ? { t: 5, r: 5 } : streak < 6 ? { t: 3, r: 10 } : streak < 11 ? { t: 1.5, r: 25 } : { t: 0.5, r: 50 };
    return { t: t.t + g.postTime, r: t.r + g.postPay };
  },
```

- [ ] **Step 4: Aufrufer anpassen**

- Block `game-postman`: `this.tier = Rules.postmanTier(this.streak);` → `this.tier = Rules.postmanTier(this.streak, State.s);`
- Block `ui`, `renderWallet`: `Rules.bankInterest(s.bankDebt)` → `Rules.bankInterest(s.bankDebt, s)`.
- Block `rooms`, `Finance.render`: `Rules.bankInterest(s.bankDebt)` → `Rules.bankInterest(s.bankDebt, s)`, und am Ende von `render()` die Konditionszeile setzen:

```js
    const g = Rules.gear(s);
    qs('#bankTerms', this.root).textContent = `Herr Krause · ${Math.round(g.bankRate * 100)} % Zinsen pro Spin · Limit ${UI.fmt(g.bankLimit)}`;
```

- Template `tpl-finance`: `<p class="dim">Herr Krause · 30 % Zinsen pro Spin · Limit 3.000 €</p>` → `<p class="dim" id="bankTerms">Herr Krause · 30 % Zinsen pro Spin · Limit 3.000 €</p>`.
- Block `core`, `Game.afterSpin`, direkt nach `s.stats.spins++;`:

```js
    if (State.mode === 'free' && s.mugCooldown > 0) s.mugCooldown--;
```

- [ ] **Step 5: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs` und `tests/dom-selftest.sh`
Expected: alle bestanden, keine Konsolenfehler.

- [ ] **Step 6: Sichtprüfung**

Run: `tests/screenshot.sh "?screen=finance" /tmp/finance.png` (oder das Muster aus `tests/screenshot.sh`) – Konditionszeile zeigt „30 % … Limit 3.000 €"; in der Konsole `State.s.car='mercC'; Finance.render()` → „27 % … Limit 4.000 €".

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(gear): Auto-Glück, Mercedes-Bank-Limit/Zinsen, Schuh-Bonus beim Postboten, Überfall-Cooldown pro Spin

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Story-Regeln – Stärke-Bedingung, Raum `stadt`, Tages-Cooldown, Spüler/Taxi/Türsteher-Boni

**Files:**
- Modify: `keller37.html` – Block `story-rules`: `check`, `validate`, `advanceDay`, `taxiPay`, neue Konstante `ROOMS`; Block `story-engine`: `ROOM_OF`; Block `jobs`: `runShift`; Block `job-spueler`: Zonenbreite; Block `job-taxi`: Fahrgast-Gutschrift, `finish`; Selftests

**Interfaces:**
- Consumes: `Rules.gear(s)` (Task 1).
- Produces: Bedingung `{ strength: { gte: n } }` in `StoryRules.check`; `StoryRules.ROOMS`; `StoryRules.validate` meldet unbekannte Räume; `StoryRules.taxiPay(passengers, tickets, tip = 0)`; `StoryRules.tuerBonus(strength) → 0..50`; `Story.ROOM_OF.stadt`.

- [ ] **Step 1: Fehlschlagende Tests schreiben**

Vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- Story: Stärke, Räume, Cooldown ---- */
T.test('StoryRules.check: strength', () => {
  const s = storyBase(); s.strength = 4;
  T.ok(StoryRules.check({ strength: { gte: 4 } }, s));
  T.ok(!StoryRules.check({ strength: { gte: 5 } }, s));
  T.ok(!StoryRules.check({ strength: { gte: 1 } }, storyBase()));
});
T.test('StoryRules.validate: Räume', () => {
  T.ok(StoryRules.ROOMS.includes('stadt'));
  const st = probeStory();
  st.start.unlocked.rooms = ['bar', 'stadt'];
  T.eq(StoryRules.validate(st, ['p.k2', 'p.e1', 'p.gut', 'p.mid', 'p.aus'], ['spueler']), []);
  st.start.unlocked.rooms = ['bar', 'garage'];
  T.ok(StoryRules.validate(st, ['p.k2', 'p.e1', 'p.gut', 'p.mid', 'p.aus'], ['spueler']).some((e) => e.includes('garage')));
  st.start.unlocked.rooms = ['bar'];
  st.events = [{ id: 'x', when: { day: { gte: 1 } }, at: 'morning', scene: 'p.e1', effects: [{ unlock: { rooms: ['keller'] } }] }];
  T.ok(StoryRules.validate(st, ['p.k2', 'p.e1', 'p.gut', 'p.mid', 'p.aus'], ['spueler']).some((e) => e.includes('keller')));
});
T.test('advanceDay: Überfall-Cooldown sinkt pro Tag', () => {
  const s = storyBase(); s.mugCooldown = 3;
  StoryRules.advanceDay(s); T.eq(s.mugCooldown, 2);
  StoryRules.advanceDay(s); StoryRules.advanceDay(s); StoryRules.advanceDay(s); T.eq(s.mugCooldown, 0);
});
T.test('taxiPay mit Trinkgeld, tuerBonus-Deckel', () => {
  T.eq(StoryRules.taxiPay(12, 1), 130);
  T.eq(StoryRules.taxiPay(12, 1, 5), 190);
  T.eq(StoryRules.tuerBonus(0), 0); T.eq(StoryRules.tuerBonus(3), 30); T.eq(StoryRules.tuerBonus(9), 50);
});
T.test('jobAvailable: Eintreiber braucht Stärke 4', () => {
  const job = { id: 'eintreiber', requires: { strength: { gte: 4 } }, requireText: 'Stärke 4' };
  const s = storyBase({ unlocked: { jobs: ['eintreiber'], doors: [], rooms: [] } });
  s.strength = 3; T.eq(StoryRules.jobAvailable(job, s).ok, false);
  s.strength = 4; T.eq(StoryRules.jobAvailable(job, s).ok, true);
});
```

- [ ] **Step 2: Tests laufen lassen – fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: 5 FAIL.

- [ ] **Step 3: `StoryRules` erweitern**

In `check` vor `throw new Error(...)`:

```js
    if ('strength' in cond) return StoryRules._ops(cond.strength, s.strength || 0);
```

Neue Konstante und Helfer im `StoryRules`-Objekt (neben `spuelerPay`/`taxiPay`):

```js
  ROOMS: ['bar', 'doc', 'bank', 'mafia', 'invest', 'life', 'vito', 'stadt'],
  spuelerPay(hits, breaks) { return hits * 5 - breaks * 10; },
  taxiPay(passengers, tickets, tip = 0) { return passengers * (15 + tip) - tickets * 50; },
  tuerBonus(strength) { return Math.min(50, 10 * (strength || 0)); },
```

`advanceDay`:

```js
  advanceDay(s) { s.story.day++; s.story.phase = 'morning'; s.story.jobToday = null; if ((s.mugCooldown || 0) > 0) s.mugCooldown--; },
```

`validate`: nach der `jobs`-Hilfsfunktion eine `rooms`-Hilfsfunktion, und sie an denselben Stellen wie `jobs` aufrufen:

```js
    const rooms = (list, where) => (list || []).forEach((r) => { if (!StoryRules.ROOMS.includes(r)) errs.push(`${story.id}: Raum "${r}" unbekannt (${where})`); });
    scene(story.intro, 'intro');
    jobs(story.start && story.start.unlocked && story.start.unlocked.jobs, 'start');
    rooms(story.start && story.start.unlocked && story.start.unlocked.rooms, 'start');
    for (const ch of story.chapters || []) { scene(ch.intro, ch.id); jobs(ch.unlock && ch.unlock.jobs, ch.id); rooms(ch.unlock && ch.unlock.rooms, ch.id); }
    for (const e of story.events || []) { scene(e.scene, e.id); for (const eff of e.effects || []) { scene(eff.scene, e.id); jobs(eff.unlock && eff.unlock.jobs, e.id); rooms(eff.unlock && eff.unlock.rooms, e.id); } }
```

- [ ] **Step 4: Story-Engine und Jobs**

Block `story-engine`: `ROOM_OF: { finance: ['bank', 'mafia'], invest: ['invest'], life: ['life'], vito: ['vito'], stadt: ['stadt'] },`

Block `jobs`, `runShift`: die Zeilen

```js
    const before = State.s.balance;
    Game.applyDelta(job.base, { quiet: true });
    UI.toast({ icon: job.icon, title: `${job.name}: Schicht`, text: `+${UI.fmt(job.base)} Lohn.`, tone: 'win' });
```

ersetzen durch

```js
    const before = State.s.balance;
    const bonus = job.id === 'tuersteher' ? StoryRules.tuerBonus(State.s.strength) : 0;
    Game.applyDelta(job.base + bonus, { quiet: true });
    UI.toast({ icon: job.icon, title: `${job.name}: Schicht`, text: bonus > 0 ? `+${UI.fmt(job.base)} Lohn, +${UI.fmt(bonus)} weil keiner mit dir diskutiert.` : `+${UI.fmt(job.base)} Lohn.`, tone: 'win' });
```

Block `job-spueler`: die Zeile

```js
    this.zone = { c: rand(0.35, 0.75), w: reduced ? 0.3 : 0.3 - k * 0.18 }; // 30 % → 12 %
```

ersetzen durch

```js
    const band = 1 + Rules.gear(State.s).spuelerBand; // Trail-Runner/Carbon: Band 20 % breiter
    this.zone = { c: rand(0.35, 0.75), w: (reduced ? 0.3 : 0.3 - k * 0.18) * band }; // 30 % → 12 %
```

Block `job-taxi`: im Objekt ein Feld `tip: 0` ergänzen (neben `passengers`), beim Start der Schicht (dort, wo `this.passengers = 0` gesetzt wird) `this.tip = Rules.gear(State.s).taxiTip;` setzen; die Fahrgast-Zeile

```js
          if (e.kind === 'rider') { if (e.lane === this.laneIdx) { this.passengers++; SFX.play('coin'); e.el.textContent = '💨'; this.floatText('+15 €', 'win'); } }
```

zu

```js
          if (e.kind === 'rider') { if (e.lane === this.laneIdx) { this.passengers++; SFX.play('coin'); e.el.textContent = '💨'; this.floatText(`+${15 + this.tip} €`, 'win'); } }
```

und in `finish`: `StoryRules.taxiPay(this.passengers, this.tickets)` → `StoryRules.taxiPay(this.passengers, this.tickets, this.tip)`.

- [ ] **Step 5: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs` und `tests/dom-selftest.sh`
Expected: alle bestanden.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Stärke-Bedingung, Raum stadt, Tages-Cooldown, Schuh-Boni bei Spüler/Taxi, Türsteher-Bonus

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Screen „Stadt" – Schaufenster, Kauf, Hub-Tür, Seitenleiste, Trophäe

**Files:**
- Modify: `keller37.html` – CSS (vor `/* ==== 7. ANIMATIONEN ==== */`), Template `tpl-stadt` (vor `<!-- /TEMPLATES -->`), `tpl-hub` (neue Tür), Block `ui`: `Actions`, `renderSide`; neuer Block `room-stadt` nach Block `rooms`; Block `cutscene-engine`: `CAST`, `PROPS`; Block `achievements`: `DEFS` + Listener; `README.md`

**Interfaces:**
- Consumes: `Rules.GEAR`, `Rules.gear`, `Rules.canBuyCar`, `Rules.canBuyShoes`, `Rules.carUpgradeCost` (Task 1).
- Produces: Screen `stadt` (`UI.show('stadt')`), `Stadt.render()`, `Stadt.buyCar(id)`, `Stadt.buyShoes(id)`, `Actions.stadt`, Bus-Events `gear:car {id}` und `gear:shoes {id}`, Trophäe `vollausgestattet`, Seitenleisten-Sektion „Stadt" mit Besitz-Zeile (`#gearLine`), Hub-Tür `data-screen="stadt"`, Cutscene-Hintergründe `autohaus`, `intersport`, Figur `verkaeufer`.

- [ ] **Step 1: CSS**

Vor `/* ==== 7. ANIMATIONEN ==== */` einfügen:

```css
/* ==== Stadt – Autohaus & INTERSPORT ==== */
.stadt { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; align-items: start; }
.shop { background: var(--panel-2); border: 1px solid rgba(255,255,255,.06); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 12px; box-shadow: var(--shadow); }
.shop h3 { font-family: var(--font-display); letter-spacing: .12em; font-size: 1.25rem; text-align: center; }
.shop.audi h3 { color: #d8d8d8; text-shadow: 0 0 10px rgba(255,255,255,.35); }
.shop.merc h3 { color: #cfd8e3; text-shadow: 0 0 10px rgba(76,201,240,.45); }
.shop.sport h3 { color: #ff6a3d; text-shadow: 0 0 10px rgba(255,106,61,.5); }
.shop .seller { font-family: var(--font-mono); font-size: .8rem; color: var(--dim); text-align: center; font-style: italic; min-height: 2.2em; }
.gear-card { background: rgba(0,0,0,.25); border: 1px solid rgba(255,255,255,.06); border-radius: 10px; padding: 12px; display: grid; grid-template-columns: 52px 1fr; gap: 6px 12px; align-items: center; }
.gear-card.owned { border-color: var(--gold); box-shadow: 0 0 14px rgba(201,162,39,.25); }
.gear-card .pic { font-size: 2.2rem; grid-row: span 3; text-align: center; filter: drop-shadow(0 4px 8px rgba(0,0,0,.6)); }
.gear-card .name { font-weight: 700; }
.gear-card .price { font-family: var(--font-mono); color: var(--gold-2); font-size: .85rem; }
.gear-card ul { list-style: none; font-family: var(--font-mono); font-size: .75rem; color: var(--dim); display: flex; flex-wrap: wrap; gap: 4px 10px; }
.gear-card .btn { grid-column: 2; justify-self: start; font-size: .9rem; padding: 6px 14px; }
.gear-card .reason { grid-column: 2; font-family: var(--font-mono); font-size: .75rem; color: var(--dim); }
.gear-line { font-family: var(--font-mono); font-size: .78rem; color: var(--gold-2); }
.cs-bg.autohaus { background: linear-gradient(180deg, #e8eef3 0%, #b9c4cf 45%, #3c4249 46%, #1b1f23 100%); }
.cs-bg.intersport { background: linear-gradient(180deg, #1a1a1a 0%, #2b2b2b 50%, #ff6a3d 51%, #b03d1c 100%); }
@media (max-width: 1100px) { .stadt { grid-template-columns: 1fr 1fr; } }
@media (max-width: 760px) { .stadt { grid-template-columns: 1fr; } }
```

- [ ] **Step 2: Templates und Hub-Tür**

Vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-stadt">
  <div class="panel stretch">
    <h2>🏙️ Stadt</h2>
    <div class="stadt">
      <section class="shop audi"><h3>Audi Zentrum</h3><p class="seller" id="sellerAudi"></p><div id="shopAudi"></div></section>
      <section class="shop merc"><h3>Mercedes-Benz Niederlassung</h3><p class="seller" id="sellerMerc"></p><div id="shopMerc"></div></section>
      <section class="shop sport"><h3>INTERSPORT</h3><p class="seller" id="sellerSport"></p><div id="shopSport"></div></section>
    </div>
  </div>
</template>
```

In `tpl-hub` nach der Postboten-Tür:

```html
    <div class="door day" data-screen="stadt" style="--neon: var(--day)"><div class="sign">Stadt</div><div class="glyph">🏙️</div><div class="chalk-tag">Autohaus · INTERSPORT</div><div class="knob"></div></div>
```

- [ ] **Step 3: Cutscene-Katalog**

In `Cutscene.CAST` ergänzen: `verkaeufer: { name: 'Der Verkäufer', emoji: '🤵', color: '#cfd8e3' },`
In `Cutscene.PROPS` ergänzen: `autohaus: ['🚗', '🪴'], intersport: ['👟', '🏷️'],`

- [ ] **Step 4: Block `room-stadt`**

Direkt nach dem `</script>` des Blocks `<script id="rooms">`:

```html
<script id="room-stadt">
/* ================= STADT – Autohaus (Audi / Mercedes) und INTERSPORT ================= */
const Stadt = {
  root: null,
  SELLER: {
    none: 'Zu Fuß gekommen? Mutig.',
    same: 'Schön, dass du wieder da bist.',
    other: 'Der Wechsel lohnt sich. Sagen alle.',
    sport: 'Für Leute, die es eilig haben.',
  },
  REASON: { funds: 'Zu wenig Bargeld', downgrade: 'Kein Rückschritt', owned: 'Deins' },
  carPerks(c) {
    const out = [];
    if (c.mugMult != null) out.push(`Überfälle −${Math.round((1 - c.mugMult) * 100)} %`);
    if (c.flee) out.push(`Flucht +${c.flee} %`);
    if (c.bankLimit) out.push(`Bank-Limit ${UI.fmt(c.bankLimit)}`);
    if (c.bankRate) out.push(`Zinsen ${Math.round(c.bankRate * 100)} %`);
    if (c.luck) out.push(`Glück +${c.luck} %`);
    return out;
  },
  shoePerks(sh) {
    const out = [`Flucht +${sh.flee} %`];
    if (sh.postTime) out.push(`Post: +${sh.postTime} s pro Brief`);
    if (sh.postPay) out.push(`Post: +${sh.postPay} € pro Brief`);
    if (sh.spuelerBand) out.push('Spüler: leichteres Timing');
    if (sh.taxiTip) out.push(`Taxi: +${sh.taxiTip} € Trinkgeld`);
    return out;
  },
  card(item, perks, check, label, onBuy) {
    const owned = check.reason === 'owned';
    const el = h('div', { class: 'gear-card' + (owned ? ' owned' : '') },
      h('div', { class: 'pic' }, item.icon),
      h('div', { class: 'name' }, item.name),
      h('div', { class: 'price' }, UI.fmt(item.price)),
      h('ul', {}, ...perks.map((p) => h('li', {}, p))));
    if (check.ok) el.append(h('button', { class: 'btn', onclick: onBuy }, label));
    else el.append(h('span', { class: 'reason' }, this.REASON[check.reason] || check.reason));
    return el;
  },
  render() {
    if (!this.root) return;
    const s = State.s;
    const cur = s.car ? Rules.GEAR.cars[s.car] : null;
    for (const [brand, boxId, sellerId] of [['audi', '#shopAudi', '#sellerAudi'], ['merc', '#shopMerc', '#sellerMerc']]) {
      const box = qs(boxId, this.root); box.innerHTML = '';
      qs(sellerId, this.root).textContent = !cur ? this.SELLER.none : cur.brand === brand ? this.SELLER.same : this.SELLER.other;
      Object.entries(Rules.GEAR.cars).filter(([, c]) => c.brand === brand).sort((a, b) => a[1].tier - b[1].tier).forEach(([id, c]) => {
        const check = Rules.canBuyCar(s, id);
        const label = cur ? `Upgrade · ${UI.fmt(check.cost)}` : `Kaufen · ${UI.fmt(check.cost)}`;
        box.append(this.card(c, this.carPerks(c), check, label, () => this.buyCar(id)));
      });
    }
    const box = qs('#shopSport', this.root); box.innerHTML = '';
    qs('#sellerSport', this.root).textContent = this.SELLER.sport;
    Object.entries(Rules.GEAR.shoes).sort((a, b) => a[1].tier - b[1].tier).forEach(([id, sh]) => {
      box.append(this.card(sh, this.shoePerks(sh), Rules.canBuyShoes(s, id), `Kaufen · ${UI.fmt(sh.price)}`, () => this.buyShoes(id)));
    });
  },
  busy() { return Cutscene.active || Game.inFlight > 0; },
  async buyCar(id) {
    const s = State.s;
    if (this.busy()) return;
    const check = Rules.canBuyCar(s, id);
    if (!check.ok) return;
    const car = Rules.GEAR.cars[id];
    const old = s.car ? Rules.GEAR.cars[s.car] : null;
    if (old) {
      const tradeIn = Math.round(old.price * Rules.GEAR.TRADE_IN);
      const choice = await Cutscene.play('stadt.tradein', { old: old.name, tradeIn: UI.fmt(tradeIn), neu: car.name, cost: UI.fmt(check.cost) });
      if (choice !== 'yes' || this.busy() || !Rules.canBuyCar(s, id).ok) return; // Zustand kann sich während der Szene geändert haben
    }
    SFX.play('cash');
    Game.applyDelta(-Rules.canBuyCar(s, id).cost, { from: this.root ? qs(car.brand === 'audi' ? '#shopAudi' : '#shopMerc', this.root) : null });
    s.car = id;
    State.save();
    await Cutscene.play('stadt.car', { name: car.name });
    UI.toast({ icon: car.icon, title: car.name, text: 'Steht vor der Tür. Deins.', tone: 'gold' });
    UI.renderWallet(); UI.renderSide(); this.render();
    await Bus.emit('gear:car', { id });
  },
  async buyShoes(id) {
    const s = State.s;
    if (this.busy()) return;
    if (!Rules.canBuyShoes(s, id).ok) return;
    const sh = Rules.GEAR.shoes[id];
    SFX.play('cash');
    Game.applyDelta(-sh.price, { from: this.root ? qs('#shopSport', this.root) : null });
    s.shoes = id;
    State.save();
    await Cutscene.play('stadt.shoes', { name: sh.name });
    UI.toast({ icon: '👟', title: sh.name, text: 'Passt. Lauf.', tone: 'gold' });
    UI.renderWallet(); UI.renderSide(); this.render();
    await Bus.emit('gear:shoes', { id });
  },
  /* Kurze Zeile für Seitenleiste und Kopfzeile: „🚗 Audi RS 4 quattro · 👟 Trail-Runner Pro · 💪 3" */
  line(s) {
    const parts = [];
    if (s.car) parts.push(`${Rules.GEAR.cars[s.car].icon} ${Rules.GEAR.cars[s.car].name}`);
    if (s.shoes) parts.push(`${Rules.GEAR.shoes[s.shoes].icon} ${Rules.GEAR.shoes[s.shoes].name}`);
    if (!parts.length) parts.push('Zu Fuß');
    parts.push(`💪 ${s.strength || 0}`);
    return parts.join(' · ');
  },
};
UI.register('stadt', {
  template: 'tpl-stadt',
  mount(root) { Stadt.root = root; Stadt.render(); },
  unmount() { Stadt.root = null; },
});
Cutscene.define('stadt.tradein', (ctx) => [
  { bg: 'autohaus', who: 'verkaeufer', mood: 'calm', text: `Dein ${ctx.old} geht mit ${ctx.tradeIn} in Zahlung. Bleiben ${ctx.cost} für den ${ctx.neu}. Weiter?`,
    choices: [{ label: 'Ja, tauschen', value: 'yes', cls: 'green' }, { label: 'Doch nicht', value: 'no', cls: 'ghost' }] },
]);
Cutscene.define('stadt.car', [
  { bg: 'autohaus', who: 'verkaeufer', mood: 'happy', text: 'Bar. Ich frag nicht, woher. Das ist Teil des Service.' },
  { bg: 'autohaus', who: 'verkaeufer', mood: 'calm', fx: 'flash', text: 'Der Schlüssel. Der {{name}} steht vorne. Fahren Sie vorsichtig – oder wenigstens schnell.' },
]);
Cutscene.define('stadt.shoes', [
  { bg: 'intersport', who: 'verkaeufer', mood: 'happy', text: '{{name}}. Dämpfung, Grip, und man hört Sie nicht kommen. Oder gehen.' },
  { bg: 'intersport', who: 'verkaeufer', mood: 'calm', text: 'Karton bleibt hier. Sie sehen aus, als würden Sie ihn gleich brauchen.' },
]);
Bus.on('gear:car', () => { const s = State.s; if (s.car && Rules.GEAR.cars[s.car].tier === 3 && s.shoes === 'carbon') Achievements.unlock('vollausgestattet'); });
Bus.on('gear:shoes', () => { const s = State.s; if (s.car && Rules.GEAR.cars[s.car].tier === 3 && s.shoes === 'carbon') Achievements.unlock('vollausgestattet'); });
</script>
```

Hinweis: `Achievements` wird erst im Block `achievements` (später in der Datei) definiert; die `Bus.on`-Handler laufen erst zur Laufzeit, das ist in Ordnung (gleiches Muster wie `Bus.on('house.bought', …)`).

- [ ] **Step 5: Seitenleiste, Actions, Trophäe**

Block `ui`, `Actions`: `stadt: () => UI.show('stadt'),` ergänzen.

`renderSide`: nach der Zeile `if (room('life')) secs.push(sec('Zuhause', …));`:

```js
    if (room('stadt')) secs.push(sec('Stadt',
      btn('🏙️ Autohaus · INTERSPORT', s.car || s.shoes ? '✓' : '', 'stadt'),
      h('p', { class: 'side-hint gear-line', id: 'gearLine' }, Stadt.line(s))));
```

Block `achievements`, `DEFS` – nach `phoenix` und vor den `group: 'story'`-Einträgen:

```js
    { id: 'strassenkaempfer', title: 'Straßenkämpfer', icon: '🥊', desc: 'Fünf Räuber verprügelt.' },
    { id: 'vollausgestattet', title: 'Vollausgestattet', icon: '🏁', desc: 'Top-Auto und Carbon-Sprinter.' },
```

(`strassenkaempfer` wird in Task 5 ausgelöst.)

- [ ] **Step 6: Sichtprüfung und Browser-Selftest**

Run: `tests/dom-selftest.sh`; dann `tests/screenshot.sh "?screen=stadt"` bei 1280 px und 400 px (Mobil per `Emulation.setDeviceMetricsOverride` wie im Playtest). Kaufpfad in der Konsole: `State.s.balance = 20000; Stadt.render()` → A3 kaufen → Karte RS 4 zeigt „Upgrade · 7.250 €", C-Klasse „Upgrade · 1.250 €", A3 „Deins"; Seitenleiste zeigt „🚗 Audi A3 (gebraucht) · 💪 0".

- [ ] **Step 7: README**

In `README.md` im Abschnitt zu den Räumen einen Absatz „Stadt" ergänzen (Autos: Audi-Linie sicher unterwegs, Mercedes-Linie Bank; INTERSPORT-Schuhe: Flucht, Postbote, Job-Minispiele; Inzahlungnahme 50 %) und `?screen=stadt` bei den Dev-Parametern erwähnen.

- [ ] **Step 8: Commit**

```bash
git add keller37.html README.md
git commit -m "feat(stadt): Screen mit Audi/Mercedes/INTERSPORT, Kauf mit Inzahlungnahme, Hub-Tür, Seitenleiste, Trophäe Vollausgestattet

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Überfall – Modul `Mugging`, Szenen, Hooks, Dev-Parameter, Trophäe, Igor-Respekt

**Files:**
- Modify: `keller37.html` – CSS (`.cs-bg.gasse`), Block `cutscene-engine` (`CAST.raeuber`, `PROPS.gasse`), neuer Block `mugging` nach Block `gameover`, Block `ui`: `UI.show`, Block `story-engine`: `Story.evening`, Block `boot`: `?mug`, Block `game-russian`: Szene `igor.first`, Block `achievements`: Listener

**Interfaces:**
- Consumes: `Rules.mugChance`, `mugLoot`, `mugWallet`, `fightChance`, `fleeChance`, `fleeFailExtra`, `Rules.MUG`, `Rules.gear` (Task 1); `Stadt.line` (Task 4) nur indirekt über `UI.renderSide`.
- Produces: `Mugging.maybe(where) → Promise<boolean>` (true = Überfall lief), `Mugging.force` (`null | true | 'junkie' | 'jugend' | 'cousin'`), Bus-Event `mug:done { outcome, loot, strength }` mit `outcome ∈ 'fightWon' | 'fightLost' | 'fled' | 'caught' | 'paid'`, Szenen `mug.intro`, `mug.fightWon`, `mug.fightLost`, `mug.fled`, `mug.caught`, `mug.paid`.

- [ ] **Step 1: CSS und Katalog**

CSS vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
.cs-bg.gasse { background: linear-gradient(180deg, #05060a 0%, #14161e 55%, #2a2418 56%, #0d0b07 100%); }
```

`Cutscene.CAST`: `raeuber: { name: 'Der Räuber', emoji: '🥷', color: 'var(--neon-red)' },`
`Cutscene.PROPS`: `gasse: ['🗑️', '🌙'],`

- [ ] **Step 2: Block `mugging`**

Direkt nach dem `</script>` des Blocks `<script id="gameover">`:

```html
<script id="mugging">
/* ================= ÜBERFALL – auf dem Weg in den Keller ================= */
const Mugging = {
  force: null,     // Dev-Parameter ?mug=1|junkie|jugend|cousin – erzwingt den nächsten Überfall
  running: false,
  CASINO: ['roulette', 'slots', 'horses', 'russian', 'blackjack'],
  TYPES: {
    junkie: {
      name: 'Der Junkie', emoji: '🧟',
      intro: ['Ey. EY. Hast du mal… {{loot}}? Ich hab ein Messer. Glaub ich. Irgendwo.', 'Seine Hand zittert. Das Messer nicht. Doch, das auch.'],
      fightWon: 'Ein Schubser. Er sitzt im Müll und weint. Du fühlst dich nicht gut dabei, aber stärker.',
      fightLost: 'Er trifft dich mit irgendwas Hartem. Als du hochkommst, ist er weg. Dein Geld auch.',
      fled: 'Du rennst. Er rennt auch – in die andere Richtung. Keiner weiß warum.',
      caught: 'Du stolperst. Er nicht. Er nimmt {{loot}} und, weil er sauer ist, noch {{extra}} dazu.',
      paid: 'Er nimmt die Scheine, murmelt „danke, Bruder" und ist weg.',
    },
    jugend: {
      name: 'Zwei Jugendliche', emoji: '🧢',
      intro: ['„Handy, Geld, Jacke. Los." Der Kleinere filmt.', 'Der Größere hat einen Schlagring. Der Kleinere hat 40.000 Follower.'],
      fightWon: 'Der Schlagring landet im Gully, der Größere auf dem Boden, das Video im Netz. Du siehst gut aus darauf.',
      fightLost: 'Zu zweit. Du kommst nicht mal zum Schwingen. {{loot}} weg – und das Video hat schon 200 Likes.',
      fled: 'Du bist schneller als beide. Der Kleinere filmt noch deinen Rücken.',
      caught: 'Der Kleinere stellt dir ein Bein. {{loot}} und {{extra}} extra, „fürs Wegrennen".',
      paid: '„Klug." Sie nehmen {{loot}} und machen ein Selfie mit dir.',
    },
    cousin: {
      name: 'Igors Cousin', emoji: '🐻',
      intro: ['„Igor sagt, du hast Geld. Igor sagt auch, du bist Freund. Ich bin nicht Igor."', 'Er ist größer als Igor. Das sollte nicht möglich sein.'],
      fightWon: 'Du triffst ihn genau einmal. Es reicht. Er nickt anerkennend, bevor er umfällt.',
      fightLost: 'Er hebt dich hoch wie einen Sack Mehl und schüttelt {{loot}} aus dir raus.',
      fled: 'Er kommt nicht mal aus dem Stand. „Nächstes Mal", ruft er. Klingt fast freundlich.',
      caught: 'Zwei Schritte. Er hat dich am Kragen. {{loot}} plus {{extra}} „für Laufen".',
      paid: '„Igor hatte recht. Du bist vernünftig." {{loot}} wechseln den Besitzer.',
    },
  },
  blocked() {
    if (Cutscene.active || Game.inFlight > 0 || Game.gameOverPending || this.running) return true;
    if (typeof Story !== 'undefined' && Story.sleeping) return true;
    return false;
  },
  /* Gibt true zurück, wenn ein Überfall gelaufen ist. Aufrufer wartet, bevor er weitermacht. */
  async maybe(where) {
    if (this.blocked()) return false;
    const s = State.s;
    const forced = this.force;
    const chance = forced ? 1 : Rules.mugChance(s, where);
    if (Math.random() >= chance) return false;
    this.force = null;
    this.running = true;
    try {
      const typeId = typeof forced === 'string' && this.TYPES[forced] ? forced : pick(Object.keys(this.TYPES));
      await this.run(typeId);
    } finally { this.running = false; }
    return true;
  },
  async run(typeId) {
    const s = State.s;
    const T = this.TYPES[typeId];
    const loot = Rules.mugLoot(s.balance);
    const gear = Rules.gear(s);
    const ctx = { loot: UI.fmt(loot), type: T, fight: Math.round(Rules.fightChance(s.strength) * 100), flee: Math.round(Rules.fleeChance(gear) * 100) };
    const choice = await Cutscene.play('mug.intro', ctx);
    let outcome, delta = 0, wallet = 0;
    if (choice === 'fight') {
      const won = Math.random() < Rules.fightChance(s.strength);
      if (won) {
        outcome = 'fightWon';
        if (s.strength >= Rules.MUG.STR_WALLET) wallet = Rules.mugWallet();
        delta = wallet;
        s.stats.fightsWon++;
      } else { outcome = 'fightLost'; delta = -loot; }
      s.strength++;
    } else if (choice === 'flee') {
      if (Math.random() < Rules.fleeChance(gear)) outcome = 'fled';
      else { outcome = 'caught'; delta = -Math.min(s.balance, loot + Rules.fleeFailExtra(s.balance)); }
    } else { outcome = 'paid'; delta = -loot; }
    s.stats.muggings++;
    s.mugCooldown = State.mode === 'story' ? Rules.MUG.COOLDOWN_DAYS : Rules.MUG.COOLDOWN_SPINS;
    if (delta !== 0) Game.applyDelta(delta, { quiet: true });
    State.save();
    await Cutscene.play('mug.' + outcome, Object.assign({}, ctx, { extra: UI.fmt(Math.max(0, -delta - loot)), wallet: UI.fmt(wallet), strength: s.strength }));
    if (outcome === 'fightWon' || outcome === 'fightLost') UI.toast({ icon: '💪', title: `Stärke ${s.strength}`, text: outcome === 'fightWon' ? 'Gewonnen. Du wirst härter.' : 'Verloren. Du wirst trotzdem härter.', tone: outcome === 'fightWon' ? 'win' : 'loss' });
    UI.renderWallet(); UI.renderSide();
    await Bus.emit('mug:done', { outcome, loot, strength: s.strength });
  },
};
Cutscene.define('mug.intro', (ctx) => [
  { bg: 'gasse', who: 'du', mood: 'calm', text: 'Der kurze Weg zum Keller. Durch die Gasse. Immer durch die Gasse.' },
  { bg: 'gasse', who: 'raeuber', mood: 'angry', fx: 'flash', text: ctx.type.intro[0] },
  { bg: 'gasse', who: 'raeuber', mood: 'calm', text: ctx.type.intro[1] + ` Er will ${ctx.loot}.`,
    choices: [
      { label: `💪 Kämpfen (${ctx.fight} %)`, value: 'fight', cls: 'red' },
      { label: `👟 Wegrennen (${ctx.flee} %)`, value: 'flee', cls: 'blue' },
      { label: `💸 Zahlen (${ctx.loot})`, value: 'pay', cls: 'ghost' },
    ] },
]);
Cutscene.define('mug.fightWon', (ctx) => [
  { bg: 'gasse', who: 'du', mood: 'angry', fx: 'shake', text: ctx.type.fightWon },
  { bg: 'gasse', who: 'du', mood: 'happy', fx: ctx.wallet !== '0 €' ? 'gain' : undefined, text: ctx.wallet !== '0 €' ? `Seine Brieftasche: ${ctx.wallet}. Finderlohn. Stärke ${ctx.strength}.` : `Nichts verloren. Stärke ${ctx.strength}.` },
]);
Cutscene.define('mug.fightLost', (ctx) => [
  { bg: 'gasse', who: 'raeuber', mood: 'angry', fx: 'shake', text: ctx.type.fightLost },
  { bg: 'gasse', who: 'du', mood: 'dead', fx: 'drain', text: `Du hast eingesteckt. Du hast gelernt. Stärke ${ctx.strength}.` },
]);
Cutscene.define('mug.fled', (ctx) => [
  { bg: 'gasse', who: 'du', mood: 'shock', fx: 'flash', text: ctx.type.fled },
  { bg: 'keller', who: 'du', mood: 'happy', text: 'Unten. Alles noch da. Die Beine zittern, das Geld nicht.' },
]);
Cutscene.define('mug.caught', (ctx) => [
  { bg: 'gasse', who: 'raeuber', mood: 'angry', fx: 'shake', text: ctx.type.caught },
  { bg: 'gasse', who: 'du', mood: 'dead', fx: 'drain', text: 'Hätte ich mal bezahlt.' },
]);
Cutscene.define('mug.paid', (ctx) => [
  { bg: 'gasse', who: 'raeuber', mood: 'calm', fx: 'drain', text: ctx.type.paid },
  { bg: 'gasse', who: 'du', mood: 'calm', text: 'Kein Kratzer. Kein Stolz. Weiter.' },
]);
Bus.on('mug:done', () => { if (State.s.stats.fightsWon >= 5) Achievements.unlock('strassenkaempfer'); });
</script>
```

Ergänzung in `mug.fightWon`: das Feld `fx: undefined` ist erlaubt (`_fx` ignoriert unbekannte/leere Effekte) – falls nicht, `fx` nur setzen, wenn Brieftasche > 0 (`Object.assign({...}, ctx.wallet !== '0 €' ? { fx: 'gain' } : {})`).

- [ ] **Step 3: Hooks**

Block `ui`, `UI.show(id)` – nach der `Story.isLocked`-Zeile und vor `this.busy = true;`:

```js
    if (State.mode === 'free' && this.current && this.current.id === 'hub' && typeof Mugging !== 'undefined' && Mugging.CASINO.includes(id)) {
      await Mugging.maybe('door');
      if (this.busy) return;
    }
```

Block `story-engine`, `Story.evening()`:

```js
  async evening() {
    const fromMorning = this.s.phase === 'morning';
    this.s.phase = 'evening';
    State.save(); this.renderDaybar();
    if (fromMorning && typeof Mugging !== 'undefined') await Mugging.maybe('evening');
    await UI.show('hub');
  },
```

Block `boot`: neben den anderen `params`-Auswertungen (vor dem ersten `UI.show`):

```js
  if (params.has('mug')) Mugging.force = params.get('mug') === '1' || params.get('mug') === '' ? true : params.get('mug');
```

- [ ] **Step 4: Igor grüßt ab Stärke 8**

Block `game-russian`: `Cutscene.define('igor.first', [...])` in eine Funktion umwandeln:

```js
Cutscene.define('igor.first', () => [
  { bg: 'keller', who: 'igor', mood: 'calm', text: '…' },
  ...(State.s.strength >= Rules.MUG.STR_RESPECT ? [{ bg: 'keller', who: 'igor', mood: 'happy', text: 'Respekt. Man hört Dinge. Mein Cousin humpelt noch.' }] : []),
  { bg: 'keller', who: 'igor', mood: 'calm', text: 'Eine Kugel. Sechs Kammern. Du zuerst. Ich habe Zeit.' },
]);
```

- [ ] **Step 5: Browser-Prüfung**

Run: `tests/dom-selftest.sh` (grün, keine Konsolenfehler). Dann per Screenshot-Skript oder Konsole: `?fresh&screen=hub&mug=1` → Klick auf Slots-Tür → Überfall-Szene erscheint, nach Wahl „Zahlen" landet man an den Slots, Kontostand um 50 € gesunken (Start 50 € → unter 100 €: dafür vorher `State.s.balance = 500` setzen, oder `Game.applyDelta(450)`). `?mug=cousin` zeigt Igors Cousin. Story: `?fresh&story=schuld&day=5&mug=1` → nach dem ersten Job der Abend beginnt mit der Gasse.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(mugging): Überfall auf dem Weg in den Keller – Kämpfen/Wegrennen/Zahlen, Stärke, drei Räubertypen, Hooks, ?mug

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Story 1 – Stadt-Freischaltung (Tag 4) und Job „Eintreiber"

**Files:**
- Modify: `keller37.html` – Block `jobs`: `POOL`; Block `story-schuld`: `events`, `jobScenes`, `jobEffects`, `scenes`; Selftests

**Interfaces:**
- Consumes: Bedingung `strength` und `StoryRules.ROOMS` (Task 3), Raum `stadt` (Task 4).
- Produces: Job `eintreiber` in `Jobs.POOL`; Event `stadtOffen`; Szenen `schuld.stadt`, `schuld.eintreiber.kiosk`, `schuld.eintreiber.zahnarzt`.

- [ ] **Step 1: Fehlschlagender Test**

Vor `/* --- SELFTEST CASES END --- */`:

```js
T.test('Story Schuld: stadtOffen an Tag 4, Eintreiber mit Türsteher freigeschaltet', () => {
  const st = Stories.all.schuld;
  const ev = st.events.find((e) => e.id === 'stadtOffen');
  T.ok(ev, 'Event stadtOffen');
  T.eq(ev.at, 'morning'); T.eq(ev.scene, 'schuld.stadt');
  T.ok(ev.effects.some((e) => e.unlock && e.unlock.rooms && e.unlock.rooms.includes('stadt')));
  const s4 = storyBase({ id: 'schuld', day: 4 });
  T.ok(StoryRules.dueEvents(st, s4, 'morning').some((e) => e.id === 'stadtOffen'));
  const s3 = storyBase({ id: 'schuld', day: 3 });
  T.ok(!StoryRules.dueEvents(st, s3, 'morning').some((e) => e.id === 'stadtOffen'));
  const tuer = st.events.find((e) => e.id === 'tuerJob');
  T.ok(tuer.effects.some((e) => e.unlock && e.unlock.jobs && e.unlock.jobs.includes('eintreiber')));
  T.eq(st.jobScenes.eintreiber, ['schuld.eintreiber.kiosk', 'schuld.eintreiber.zahnarzt']);
  T.eq(st.jobEffects['schuld.eintreiber.kiosk'], [{ var: 'ruf', add: 1 }]);
  T.eq(st.jobEffects['schuld.eintreiber.zahnarzt'], [{ var: 'ruf', add: 1 }]);
  for (const id of ['schuld.stadt', 'schuld.eintreiber.kiosk', 'schuld.eintreiber.zahnarzt']) T.ok(Array.isArray(st.scenes[id]) && st.scenes[id].length >= 2, id);
});
```

Falls `Stories.all` in der Node-Umgebung anders heißt, den Zugriff so wählen, wie der bestehende Test `Stories.validateAll`/`Stories.all` ihn nutzt (siehe Block `story-rules`, Zeile mit `for (const st of Object.values(this.all))`).

- [ ] **Step 2: Test laufen lassen – fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: 1 FAIL (`Event stadtOffen`).

- [ ] **Step 3: Job-Pool**

Block `jobs`, `POOL`, nach `croupier`:

```js
    eintreiber: { id: 'eintreiber', name: 'Eintreiber', icon: '🥊', kind: 'shift', base: 150, requires: { strength: { gte: 4 } }, requireText: 'Stärke 4', desc: 'Vito hat eine Liste. Du hast Fäuste.', pay: '150 €' },
```

- [ ] **Step 4: Story-Inhalt**

Block `story-schuld`, `events` – nach `wirt5`:

```js
    { id: 'stadtOffen', when: { day: { eq: 4 } }, once: true, at: 'morning', scene: 'schuld.stadt', effects: [{ unlock: { rooms: ['stadt'] } }] },
```

`tuerJob`-Event: `effects: [{ unlock: { jobs: ['tuersteher'] } }]` → `effects: [{ unlock: { jobs: ['tuersteher', 'eintreiber'] } }]`.

`jobScenes`: `eintreiber: ['schuld.eintreiber.kiosk', 'schuld.eintreiber.zahnarzt'],`

`jobEffects`: `'schuld.eintreiber.kiosk': [{ var: 'ruf', add: 1 }], 'schuld.eintreiber.zahnarzt': [{ var: 'ruf', add: 1 }],`

`scenes`:

```js
    'schuld.stadt': [
      { bg: 'strasse', who: 'kevin', mood: 'happy', text: 'Komm mit. Ich zeig dir was. Nein, nicht das. Was Legales.' },
      { bg: 'autohaus', who: 'kevin', mood: 'happy', text: 'Guck mal, was man hier alles nicht bezahlen kann. Audi links, Mercedes rechts, und gegenüber verkaufen sie Schuhe, mit denen man vor beiden wegrennen kann.' },
      { bg: 'autohaus', who: 'kevin', mood: 'calm', text: 'Vito fährt Mercedes. Igor fährt gar nicht. Denk mal drüber nach, was das über die Gasse sagt.' },
    ],
    'schuld.eintreiber.kiosk': [
      { bg: 'strasse', who: 'vito', mood: 'calm', text: 'Der Kiosk an der Ecke. Zweihundert, seit drei Wochen. Sei höflich. Einmal.' },
      { bg: 'strasse', who: 'du', mood: 'angry', text: 'Du musst nicht mal die Stimme heben. Er sieht deine Hände und zählt. Vito nickt, als du zurückkommst.' },
    ],
    'schuld.eintreiber.zahnarzt': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Ein Zahnarzt. Spielt bei uns, verliert bei uns, zahlt nicht bei uns. Erste Etage, Praxis Dr. Leuchtenberg.' },
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Er zahlt, bevor du das Wartezimmer verlässt. Und bietet dir eine Prophylaxe an. Umsonst. Du sagst ja.' },
    ],
```

- [ ] **Step 5: Tests – grün, Validierung**

Run: `node tests/run-selftest.mjs` (enthält `Stories`-Validierung – Räume/Jobs/Szenen müssen bekannt sein) und `tests/dom-selftest.sh`.
Expected: alle bestanden.

- [ ] **Step 6: Sichtprüfung**

Run: `?fresh&story=schuld&day=4` → Morgen-Szene mit Kevin läuft, danach zeigt die Seitenleiste „Stadt"; `?fresh&story=schuld&day=13` mit `State.s.strength = 4; Story.s.vars.vertrauen = 4` vor dem Morgen → Pinnwand zeigt „Eintreiber"; bei Stärke 3 ist die Karte mit „Stärke 4" gesperrt.

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Stadt-Freischaltung an Tag 4 mit Kevin, Job Eintreiber ab Stärke 4

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Playtest-Szenarien, Screenshots, Checkliste

**Files:**
- Modify: `tests/playtest-story.py` – neue Szenarien und Aufrufe in `main()`
- Create: `docs/superpowers/screenshots/stadt-*.png`, `docs/superpowers/screenshots/mug-*.png`
- Create: `docs/superpowers/checklist-stadt-2026-09-16.md`

**Interfaces:**
- Consumes: alles aus Task 1–6; Dev-Parameter `?mug`, `?screen=stadt`.

- [ ] **Step 1: Szenarien schreiben**

In `tests/playtest-story.py` vor `async def main():` einfügen:

```python
async def scenario_stadt_shop(cdp):
    """Stadt: Kauf abgelehnt ohne Geld, Kauf, Upgrade, Markenwechsel mit Bestaetigung, Abbruch."""
    await cdp.navigate(URL_BASE + "?fresh&screen=stadt")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    n_buttons = await cdp.eval("document.querySelectorAll('#shopAudi .btn').length", await_promise=False)
    record("stadt: ohne Geld kein Kaufen-Button", n_buttons == 0, "buttons=%s" % n_buttons)
    await cdp.screenshot("stadt-arm.png")
    await cdp.eval("State.s.balance = 20000; State.save(); UI.setBalance(20000, {animate:false}); Stadt.render(); 0", await_promise=False)
    await asyncio.sleep(0.2)
    await cdp.eval("Stadt.buyCar('audiA3'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.4)
    car = await cdp.eval("State.s.car", await_promise=False)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    record("stadt: A3 gekauft", car == "audiA3" and bal == 18500, "car=%s bal=%s" % (car, bal))
    label = await cdp.eval("[...document.querySelectorAll('#shopAudi .gear-card')][1].querySelector('.btn').textContent", await_promise=False)
    record("stadt: RS 4 zeigt Upgrade-Preis mit Inzahlungnahme", label is not None and "7.250" in label, "label=%s" % label)
    await cdp.screenshot("stadt-a3.png")
    # Markenwechsel mit Bestaetigung: erst abbrechen, dann zustimmen
    await cdp.eval("Stadt.buyCar('mercC'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene(label_hint="Doch nicht")
    await asyncio.sleep(0.3)
    car = await cdp.eval("State.s.car", await_promise=False)
    record("stadt: Abbruch laesst Auto unveraendert", car == "audiA3", "car=%s" % car)
    await cdp.eval("Stadt.buyCar('mercC'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene(label_hint="Ja, tauschen")
    await asyncio.sleep(0.4)
    car = await cdp.eval("State.s.car", await_promise=False)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    record("stadt: Markenwechsel A3 -> C-Klasse kostet 1.250", car == "mercC" and bal == 18500 - 1250, "car=%s bal=%s" % (car, bal))
    await cdp.eval("Stadt.buyShoes('trail'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.3)
    shoes = await cdp.eval("State.s.shoes", await_promise=False)
    record("stadt: Trail-Runner gekauft", shoes == "trail", "shoes=%s" % shoes)
    line = await cdp.eval("document.querySelector('#gearLine') && document.querySelector('#gearLine').textContent", await_promise=False)
    record("stadt: Seitenleiste zeigt Besitz", line is not None and "Mercedes C-Klasse" in line and "Trail-Runner" in line and "💪 0" in line, "line=%s" % line)
    terms = await cdp.eval("UI.show('finance').then(()=>document.querySelector('#bankTerms').textContent)")
    record("stadt: Bank zeigt Mercedes-Konditionen", terms is not None and "27 %" in terms and "4.000" in terms, "terms=%s" % terms)


async def scenario_mugging(cdp):
    """Ueberfall im freien Spiel: alle drei Ausgaenge per ?mug."""
    async def setup(mug):
        await cdp.navigate(URL_BASE + "?fresh&screen=hub&mug=" + mug)
        await asyncio.sleep(1.0)
        await cdp.inject_helpers()
        await cdp.eval("State.s.balance = 1000; State.s.stats.spins = 20; State.save(); UI.setBalance(1000, {animate:false}); 0", await_promise=False)
    # Zahlen
    await setup("junkie")
    await cdp.click(".door[data-screen=slots]")
    await asyncio.sleep(0.6)
    active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("mug: Szene erscheint beim Tuerwechsel", active is True, "active=%s" % active)
    await cdp.screenshot("mug-intro.png")
    await cdp.advance_cutscene(label_hint="Zahlen")
    await asyncio.sleep(0.6)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    cd = await cdp.eval("State.s.mugCooldown", await_promise=False)
    record("mug: Zahlen kostet 200 und fuehrt zu den Slots", bal == 800 and screen == "slots" and cd == 15, "bal=%s screen=%s cd=%s" % (bal, screen, cd))
    # Kaempfen mit Staerke 20 (sicherer Sieg, Brieftasche)
    await setup("cousin")
    await cdp.eval("State.s.strength = 20; State.save(); 0", await_promise=False)
    await cdp.click(".door[data-screen=roulette]")
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene(label_hint="Kämpfen")
    await asyncio.sleep(0.6)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    won = await cdp.eval("State.s.stats.fightsWon", await_promise=False)
    record("mug: Kampf mit Staerke 20 gewonnen, Brieftasche 50-150, Staerke 21", 1050 <= (bal or 0) <= 1150 and st == 21 and won == 1, "bal=%s st=%s won=%s" % (bal, st, won))
    await cdp.screenshot("mug-fight.png")
    # Wegrennen mit R8 + Carbon (90 %) - Ergebnis ist zufaellig, nur Konsistenz pruefen
    await setup("jugend")
    await cdp.eval("State.s.car = 'audiR8'; State.s.shoes = 'carbon'; State.save(); 0", await_promise=False)
    await cdp.click(".door[data-screen=blackjack]")
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene(label_hint="Wegrennen")
    await asyncio.sleep(0.6)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    record("mug: Flucht laesst Staerke unveraendert, Kontostand 1000 (gelungen) oder 700 (erwischt)", bal in (1000, 700) and st == 0, "bal=%s st=%s" % (bal, st))
    # Kein Ueberfall bei Cooldown
    await cdp.eval("Mugging.force = true; State.s.mugCooldown = 5; 0", await_promise=False)
    await cdp.eval("UI.show('hub'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.click(".door[data-screen=slots]")
    await asyncio.sleep(0.6)
    active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("mug: ?mug erzwingt auch im Cooldown (Dev), Szene laeuft", active is True, "active=%s" % active)
    await cdp.advance_cutscene(label_hint="Zahlen")


async def scenario_story_stadt(cdp):
    """Story: Tag 4 schaltet die Stadt frei, Abend-Ueberfall, Eintreiber ab Staerke 4."""
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=4")
    await asyncio.sleep(1.2)
    await cdp.inject_helpers()
    await cdp.advance_cutscene()
    await asyncio.sleep(0.4)
    rooms = await cdp.eval("JSON.stringify(State.s.story.unlocked.rooms)", await_promise=False)
    record("story: Tag 4 schaltet stadt frei", rooms is not None and "stadt" in rooms, "rooms=%s" % rooms)
    has_btn = await cdp.eval("!!document.querySelector('#side [data-action=stadt]')", await_promise=False)
    record("story: Seitenleiste zeigt Stadt-Knopf", has_btn is True, "has=%s" % has_btn)
    await cdp.screenshot("stadt-story-tag4.png")
    # Abend-Ueberfall erzwingen
    await cdp.eval("Mugging.force = 'cousin'; State.s.balance = 500; State.save(); 0", await_promise=False)
    await cdp.eval("Jobs.take('spueler'); 0", await_promise=False)
    await asyncio.sleep(0.8)
    await cdp.eval("Spueler.finish && Spueler.finish(); 0", await_promise=False)
    await asyncio.sleep(0.8)
    await cdp.eval("Story.evening(); 0", await_promise=False)
    await asyncio.sleep(0.8)
    active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("story: Ueberfall am Abend", active is True, "active=%s" % active)
    await cdp.advance_cutscene(label_hint="Zahlen")
    await asyncio.sleep(0.5)
    cd = await cdp.eval("State.s.mugCooldown", await_promise=False)
    phase = await cdp.eval("State.s.story.phase", await_promise=False)
    record("story: Cooldown 3 Tage, Abend erreicht", cd == 3 and phase == "evening", "cd=%s phase=%s" % (cd, phase))
    # Eintreiber
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=13")
    await asyncio.sleep(1.2)
    await cdp.inject_helpers()
    await cdp.advance_cutscene()
    await cdp.eval("Story.s.unlocked.jobs.push('eintreiber'); State.s.strength = 3; State.save(); UI.show('jobs'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    locked = await cdp.eval("(()=>{const c=[...document.querySelectorAll('#pinboard .job-card')].find(e=>e.textContent.includes('Eintreiber')); return c ? c.textContent.includes('Stärke 4') : 'missing'})()", await_promise=False)
    record("story: Eintreiber bei Staerke 3 gesperrt", locked is True, "locked=%s" % locked)
    await cdp.eval("State.s.strength = 4; State.save(); UI.show('jobs'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    locked = await cdp.eval("(()=>{const c=[...document.querySelectorAll('#pinboard .job-card')].find(e=>e.textContent.includes('Eintreiber')); return c ? c.textContent.includes('Stärke 4') : 'missing'})()", await_promise=False)
    record("story: Eintreiber bei Staerke 4 offen", locked is False, "locked=%s" % locked)
    await cdp.screenshot("stadt-story-eintreiber.png")
```

Die Selektoren für Pinnwand-Karten (`#pinboard .job-card`) und die Spüler-Abschlussfunktion (`Spueler.finish`) sind gegen den Code zu prüfen (`grep -n "class: 'job-card'\|async finish()" keller37.html`) und ggf. anzupassen; die Prüfung „gesperrt" muss auf den tatsächlich gerenderten Sperrtext (`requireText`) treffen.

In `main()` nach `await scenario_free_sandbox_unchanged(cdp)`:

```python
        await scenario_stadt_shop(cdp)
        await scenario_mugging(cdp)
        await scenario_story_stadt(cdp)
```

- [ ] **Step 2: Playtest laufen lassen**

Run: `python3 tests/playtest-story.py` und `python3 tests/playtest-story.py --mobile`
Expected: `fehlgeschlagen: 0`, `ERRORS 0`. Bei Pixel-Diff-Fehlern gegen Referenz-Screenshots (Hub hat jetzt eine Tür mehr): betroffene Referenzen in `docs/superpowers/screenshots/` bewusst erneuern und in der Checkliste nennen.

- [ ] **Step 3: Screenshots sichten**

`docs/superpowers/screenshots/stadt-arm.png`, `stadt-a3.png`, `mug-intro.png`, `mug-fight.png`, `stadt-story-tag4.png`, `stadt-story-eintreiber.png` öffnen (Read-Tool) und prüfen: drei Schaufenster nebeneinander bei 1280 px, untereinander bei 400 px; Karten lesbar; Gasse-Hintergrund dunkel mit Räuber-Portrait; Choice-Buttons zeigen Prozentwerte.

- [ ] **Step 4: Checkliste**

`docs/superpowers/checklist-stadt-2026-09-16.md` anlegen mit je einer Zeile pro Spec-Anforderung (§2.2 Katalog, §2.4 Hooks, §3 Screen, §4 Überfall, §4.5 Stärke, §6 Tests) und dem Nachweis (Testname oder Screenshot).

- [ ] **Step 5: Commit**

```bash
git add tests/playtest-story.py docs/superpowers/screenshots docs/superpowers/checklist-stadt-2026-09-16.md
git commit -m "test: Playtest-Szenarien für Stadt, Überfall und Story-Freischaltung, Screenshots, Checkliste

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec-Abdeckung:** §2.1 Felder → T1; §2.2 Katalog → T1; §2.3 `gear`/Kaufregeln → T1; §2.4 Hooks: luck/Bank/Post → T2, Spüler/Taxi/Türsteher → T3, Finanz-Anzeige → T2; §3.1 Tür/Raum/Story-Event → T4/T6; §3.2–3.4 Screen, Kauf, Seitenleiste → T4; §4.1–4.4 Überfall → T5 (Cooldown-Ticks T2/T3); §4.5 Türsteher-Bonus T3, Eintreiber T6, Igor-Respekt T5, Trophäen T4/T5; §5 Blöcke → T1/T4/T5; §6 Tests → T1–T3 (Node), T7 (Browser); README → T4.

**Platzhalter:** keine – jeder Code-Schritt enthält den Code; T7 nennt explizit, welche Selektoren gegen den Code zu prüfen sind.

**Typ-Konsistenz:** `Rules.gear(s)` liefert überall dieselben neun Schlüssel; `Rules.bankInterest(debt, s)` optional `s` (T2-Tests und alte Tests ohne `s`); `StoryRules.taxiPay(p, t, tip = 0)`; `Mugging.maybe(where)` mit `'door' | 'evening'` passt zu `Rules.mugChance(s, where)`; `Stadt.line(s)` wird in `renderSide` (T4) genutzt; Achievement-IDs `strassenkaempfer`/`vollausgestattet` in T4 definiert, in T4/T5 ausgelöst.
