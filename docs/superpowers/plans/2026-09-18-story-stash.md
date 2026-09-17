# Story 3 „Die Wäsche" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die dritte Story: vier Wäsche-Wochen für Anabi Stash, Zorn als Todesuhr, nächtliche Überfälle und Hinterhalte, Bahnhof-Jungs, Igor, Kommissar Brandt, Sylvies Hausverbot, sechs Enden – als Daten (`STORY_STASH`) auf der Engine 3, mit der Wochenlogik als reine Regeln in `GangRules`.

**Architecture:** `GangRules` (Block `gang-rules`, aus Plan 3) bekommt die reinen Story-Rechnungen: Wochenwerte, Abrechnung, Nachtkasse, Überfall-/Hinterhalt-Würfel, Raub, Schwellen. `STORY_STASH` (neuer Block `story-stash` nach `story-kater`) ist eine `Stories.define`-Definition: Start, HUD, Kapitel, Events, Aktionen, `fns` (Effekt `call`), Szenen, Enden, Trophäen. Rechnende Nacht-Ereignisse laufen als `fns`, die Vars/Flags setzen und eine Szene zurückgeben; die Szenen sind Funktionen von `ctx` und erzählen den Ausgang aus `ctx.raw.vars/flags`. Kein Story-3-Sonderfall in der Engine – bis auf die kleine, generische Bedingung `{ weapon: { gte: 1 } }` (Task 1).

**Tech Stack:** Vanilla JS in `keller37.html`, Node-Selftest (`story-stash` in die Blockliste), DOM-Selftest, CDP-Playtest `tests/playtest-story.py`, Screenshots.

**Spec:** `docs/superpowers/specs/2026-09-18-story-stash-design.md` (alle Abschnitte; §10 Engine ist mit Plan 1–3 umgesetzt).

## Global Constraints

- Voraussetzung: Pläne „Story-Engine 3", „Baccarat", „Schießerei & Pfandleihe" sind umgesetzt (`recordStake`, `broken`/`repair`, `call`/`fns`, `show`, `fight:after`/`job:after`, `prevEndings`/`lockText`, `jobOverrides`, `hud.max`-Funktion, Tür `hinterzimmer`, `Shootout`/`forceFight`, Pfandleihe, Kurierfahrt, Figuren).
- Zahlen exakt wie in der Spec: Start 5.000 €; Kredit 0/30.000/30.000/50.000/50.000 je Vorgängerende (wirt/nuechtern/taxi/stammgast/brownie); Wochen: Lieferung 10/20/30/40 k, Ziel 20/40/60/80 k, Rückgabe 11/22/33/44 k; `bahnhof` → Ziel × 1,5 ab der nächsten Lieferung (auf 1.000 gerundet); Abrechnung: ✅✅ Zorn −1, Kredit −5.000, Beleg +1; ❌✅ Zorn +1; ✅❌ Rest × 1,5 → Kredit, Zorn +1; ❌❌ Zorn +2; Zorn 0–3, ≥ 3 → Ende `kanal` sofort. Nachtkasse 250 €/intaktes Keller-Spiel. Überfall 25 % (Igor 15 %, Bahnhof 0 %), Reparatur Roulette 6.000/Blackjack 5.000/Slots 4.000/Pferde 3.000/Russisch 2.000 (Igor: halb, auf 100 gerundet). Hinterhalt 15 % (Goldene 7,5 %), 1–3 Gegner, Raub 20 % max 5.000, `blauesAuge` = Glück −15 am Folgetag. Royal-Warnung 10.000, Hausverbot 15.000 (Wochen-Umsatz im Royal). Ablöse 100.000 + Kredit, Zorn ≤ 1, ab Tag 22. Flucht ≥ 30.000 ab Tag 20. Razzia ab Tag 26 mit 3 übergebenen Belegen. Finale ab Tag 25 mit `bahnhof` und Waffe. Igor: 3 Biere à 100 € (1/Tag) → Flag `igor`. Beleg-Übergabe 20 % Risiko (0 % mit `igor`). Eintreiber 1.000 €, Zorn −1, max 2/Woche.
- Lieferungen Tag 1/8/15/22, Abrechnungen Tag 7/14/21/28, jeweils `at: 'night'`; die Abrechnung steht in `events` **vor** allen anderen Nacht-Events.
- Alle Szenen-IDs beginnen mit `stash.`; Erzählpanels ohne Sprecher nutzen `who: 'du'`. Sprache Deutsch, Ton wie Story 1/2 (trocken, kurz).
- Bestehende Stories unverändert: Playtest 140/140 bleibt; neue Szenarien kommen dazu.
- Nach jeder Task Node- und DOM-Selftest grün; Commit-Trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## Dateistruktur

| Ort | Inhalt |
|---|---|
| `story-rules` | Bedingung `weapon` |
| `gang-rules` | Story-Rechnungen (Task 2) |
| `<script id="story-stash">` (nach `story-kater`) | `STORY_STASH` – Task 3 (Gerüst, Events, fns, Aktionen, Enden), Task 4 (Szenen) |
| `achievements` | Trophäen |
| `selftest` | Tests |
| `tests/run-selftest.mjs` | `'story-kater', 'story-stash'` |
| `tests/playtest-story.py` | `scenario_stash` |
| `README.md`, `docs/superpowers/screenshots/stash-*.png` | Doku |

---

### Task 1: Bedingung `weapon`

**Files:**
- Modify: `story-rules` (`check`)
- Test: `selftest`

**Interfaces:**
- Produces: `{ weapon: { gte: 1 } }` vergleicht `s.weapon || 0` wie `strength`.

- [ ] **Step 1: Failing Test**

```js
T.test('StoryRules.check: weapon', () => {
  T.eq(StoryRules.check({ weapon: { gte: 1 } }, base({ story: { vars: {}, flags: {} } })), false);
  T.eq(StoryRules.check({ weapon: { gte: 1 } }, base({ weapon: 2, story: { vars: {}, flags: {} } })), true);
});
```

- [ ] **Step 2: Fehlschlag prüfen** – Run: `node tests/run-selftest.mjs` → `Ungültige Bedingung`.

- [ ] **Step 3: Implementieren** – in `StoryRules.check` hinter der `strength`-Zeile: `if ('weapon' in cond) return StoryRules._ops(cond.weapon, s.weapon || 0);`

- [ ] **Step 4: Tests grün, Commit**

```bash
git add keller37.html
git commit -m "feat(story): Bedingung weapon"
```

---

### Task 2: `GangRules` – Wochen, Abrechnung, Nachtkasse, Überfall, Hinterhalt, Raub, Schwellen

**Files:**
- Modify: Block `gang-rules` (Konstanten und Methoden anhängen)
- Test: `selftest` (Abschnitt `/* ---- Gang: Story-Rechnungen ---- */`)

**Interfaces:**
- Produces:
  - `GangRules.WEEKS` (4 Einträge `{ lieferung, ziel, rueckgabe }`), `week(n, bahnhof)` → `{ lieferung, ziel, rueckgabe }` (n 1–4, darüber Woche 4; `bahnhof` → `ziel = round(ziel·1,5 / 1000)·1000`).
  - `abrechnung({ umsatz, ziel, balance, rueckgabe })` → `{ ausgang: 'ok'|'umsatz'|'geld'|'beides', pay, kreditDelta, zornDelta, belegDelta }`.
  - `zorn(v, d)` → auf 0–3 gekappt.
  - `KELLER_DOORS`, `KASSE_PRO_SPIEL = 250`, `nachtkasse(broken)` → `{ sum, kaputt: [doorIds] }`.
  - `REPAIR`, `repairPrice(door, igor)`; `RAID = { base: 0.25, igor: 0.15 }`, `raidChance(flags)`, `raid(broken, flags, rng)` → door | null (rng 1: Chance, rng 2: Auswahl unter intakten Türen in `KELLER_DOORS`-Reihenfolge).
  - `AMBUSH = { base: 0.15, max: 3 }`, `ambushChance(flags, weapon)`, `ambushCount(rng)` → 1–3; `ROB = { pct: 0.2, max: 5000 }`, `robbery(balance)`.
  - `ROYAL = { warn: 10000, bann: 15000 }`, `ABLOESE = 100000`, `FLUCHT_MIN = 30000`, `KREDIT_SCHRITT = 5000`, `KREDIT_NACHLASS = 5000`, `KREDIT_AUFSCHLAG = 1.5`, `IGOR_BIERE = 3`, `BELEG_RISIKO = 0.2`, `BELEGE_NOETIG = 3`.

- [ ] **Step 1: Failing Tests**

```js
/* ---- Gang: Story-Rechnungen ---- */
T.test('GangRules.week: vier Wochen, danach Woche 4, Bahnhof ×1,5 auf Tausender', () => {
  T.eq(GangRules.week(1, false), { lieferung: 10000, ziel: 20000, rueckgabe: 11000 });
  T.eq(GangRules.week(4, false), { lieferung: 40000, ziel: 80000, rueckgabe: 44000 });
  T.eq(GangRules.week(9, false), GangRules.week(4, false));
  T.eq(GangRules.week(2, true), { lieferung: 20000, ziel: 60000, rueckgabe: 22000 });
  T.eq(GangRules.week(1, true).ziel, 30000);
});
T.test('GangRules.abrechnung: vier Ausgänge', () => {
  const A = GangRules.abrechnung;
  T.eq(A({ umsatz: 20000, ziel: 20000, balance: 15000, rueckgabe: 11000 }), { ausgang: 'ok', pay: 11000, kreditDelta: -5000, zornDelta: -1, belegDelta: 1 });
  T.eq(A({ umsatz: 19999, ziel: 20000, balance: 15000, rueckgabe: 11000 }), { ausgang: 'umsatz', pay: 11000, kreditDelta: 0, zornDelta: 1, belegDelta: 0 });
  T.eq(A({ umsatz: 25000, ziel: 20000, balance: 5000, rueckgabe: 11000 }), { ausgang: 'geld', pay: 5000, kreditDelta: 9000, zornDelta: 1, belegDelta: 0 }, '(11.000 − 5.000) × 1,5');
  T.eq(A({ umsatz: 0, ziel: 20000, balance: 0, rueckgabe: 11000 }), { ausgang: 'beides', pay: 0, kreditDelta: 16500, zornDelta: 2, belegDelta: 0 });
  T.eq(GangRules.zorn(0, -1), 0); T.eq(GangRules.zorn(2, 2), 3); T.eq(GangRules.zorn(1, 1), 2);
});
T.test('GangRules.nachtkasse: 250 € je intaktem Keller-Spiel', () => {
  T.eq(GangRules.nachtkasse({}), { sum: 1250, kaputt: [] });
  T.eq(GangRules.nachtkasse({ slots: 4000, horses: 3000 }), { sum: 750, kaputt: ['slots', 'horses'] });
  T.eq(GangRules.nachtkasse({ roulette: 1, slots: 1, horses: 1, russian: 1, blackjack: 1 }).sum, 0);
  T.eq(GangRules.nachtkasse({ hinterzimmer: 1 }).sum, 1250, 'Hinterzimmer zählt nicht');
});
T.test('GangRules: Reparaturpreise, Igor halbiert auf 100', () => {
  T.eq(GangRules.REPAIR, { roulette: 6000, blackjack: 5000, slots: 4000, horses: 3000, russian: 2000 });
  T.eq(GangRules.repairPrice('roulette', false), 6000); T.eq(GangRules.repairPrice('roulette', true), 3000);
  T.eq(GangRules.repairPrice('horses', true), 1500); T.eq(GangRules.repairPrice('russian', true), 1000);
});
T.test('GangRules.raid: 25/15/0 %, zufällige intakte Tür, nichts bei fünf kaputten', () => {
  T.eq(GangRules.raidChance({}), 0.25); T.eq(GangRules.raidChance({ igor: true }), 0.15); T.eq(GangRules.raidChance({ bahnhof: true, igor: true }), 0);
  T.eq(GangRules.raid({}, {}, seq(0.24, 0)), 'roulette');
  T.eq(GangRules.raid({}, {}, seq(0.24, 0.99)), 'blackjack');
  T.eq(GangRules.raid({}, {}, seq(0.25, 0)), null, 'Würfel ≥ Chance');
  T.eq(GangRules.raid({}, { igor: true }, seq(0.2, 0)), null);
  T.eq(GangRules.raid({ roulette: 1 }, {}, seq(0.1, 0)), 'slots', 'nur intakte Türen');
  T.eq(GangRules.raid({ roulette: 1, slots: 1, horses: 1, russian: 1, blackjack: 1 }, {}, seq(0, 0)), null);
  let calls = 0; GangRules.raid({}, { bahnhof: true }, () => { calls++; return 0; }); T.eq(calls, 0, 'Chance 0: kein Würfel');
});
T.test('GangRules: Hinterhalt-Chance, Anzahl, Raub', () => {
  const W = GangRules.WEAPONS;
  T.eq(GangRules.ambushChance({}, W[0]), 0.15); T.eq(GangRules.ambushChance({}, W[2]), 0.15); T.eq(GangRules.ambushChance({}, W[3]), 0.075);
  T.eq(GangRules.ambushChance({ bahnhof: true }, W[0]), 0);
  T.eq([0, 0.34, 0.67, 0.99].map((r) => GangRules.ambushCount(seq(r))), [1, 2, 3, 3]);
  T.eq(GangRules.robbery(1000), 200); T.eq(GangRules.robbery(100000), 5000); T.eq(GangRules.robbery(0), 0);
});
T.test('GangRules: Schwellen', () => {
  T.eq([GangRules.ROYAL.warn, GangRules.ROYAL.bann, GangRules.ABLOESE, GangRules.FLUCHT_MIN, GangRules.KREDIT_SCHRITT, GangRules.IGOR_BIERE, GangRules.BELEG_RISIKO, GangRules.BELEGE_NOETIG], [10000, 15000, 100000, 30000, 5000, 3, 0.2, 3]);
});
```

- [ ] **Step 2: Fehlschlag prüfen** – Run: `node tests/run-selftest.mjs` → `week is not a function`.

- [ ] **Step 3: Implementieren** – in `GangRules` (vor der schließenden `};`) anhängen:

```js
  /* ---- Story 3: Wäsche-Wochen ---- */
  WEEKS: [
    { lieferung: 10000, ziel: 20000, rueckgabe: 11000 },
    { lieferung: 20000, ziel: 40000, rueckgabe: 22000 },
    { lieferung: 30000, ziel: 60000, rueckgabe: 33000 },
    { lieferung: 40000, ziel: 80000, rueckgabe: 44000 },
  ],
  BAHNHOF_MULT: 1.5,
  week(n, bahnhof) {
    const W = GangRules.WEEKS, w = W[Math.min(W.length, Math.max(1, n)) - 1];
    return { lieferung: w.lieferung, ziel: bahnhof ? Math.round(w.ziel * GangRules.BAHNHOF_MULT / 1000) * 1000 : w.ziel, rueckgabe: w.rueckgabe };
  },
  KREDIT_NACHLASS: 5000, KREDIT_AUFSCHLAG: 1.5, KREDIT_SCHRITT: 5000,
  /* Vier Ausgänge: Umsatz erreicht? Zahlen möglich? – pay ist, was der Abholer mitnimmt (höchstens den Kontostand) */
  abrechnung({ umsatz, ziel, balance, rueckgabe }) {
    const umsatzOk = umsatz >= ziel, kannZahlen = balance >= rueckgabe;
    if (umsatzOk && kannZahlen) return { ausgang: 'ok', pay: rueckgabe, kreditDelta: -GangRules.KREDIT_NACHLASS, zornDelta: -1, belegDelta: 1 };
    if (!umsatzOk && kannZahlen) return { ausgang: 'umsatz', pay: rueckgabe, kreditDelta: 0, zornDelta: 1, belegDelta: 0 };
    const pay = Math.max(0, balance), rest = Math.round((rueckgabe - pay) * GangRules.KREDIT_AUFSCHLAG);
    return { ausgang: umsatzOk ? 'geld' : 'beides', pay, kreditDelta: rest, zornDelta: umsatzOk ? 1 : 2, belegDelta: 0 };
  },
  ZORN_MAX: 3,
  zorn(v, d) { return Math.max(0, Math.min(GangRules.ZORN_MAX, (v || 0) + d)); },
  /* ---- Dein Keller ---- */
  KELLER_DOORS: ['roulette', 'slots', 'horses', 'russian', 'blackjack'],
  KASSE_PRO_SPIEL: 250,
  nachtkasse(broken = {}) {
    const kaputt = GangRules.KELLER_DOORS.filter((d) => broken[d] != null);
    return { sum: (GangRules.KELLER_DOORS.length - kaputt.length) * GangRules.KASSE_PRO_SPIEL, kaputt };
  },
  REPAIR: { roulette: 6000, blackjack: 5000, slots: 4000, horses: 3000, russian: 2000 },
  repairPrice(door, igor) { const p = GangRules.REPAIR[door]; return igor ? Math.round(p / 2 / 100) * 100 : p; },
  RAID: { base: 0.25, igor: 0.15 },
  raidChance(flags) { return flags.bahnhof ? 0 : flags.igor ? GangRules.RAID.igor : GangRules.RAID.base; },
  /* rng 1: Chance; rng 2: Wahl unter den intakten Türen (KELLER_DOORS-Reihenfolge) */
  raid(broken = {}, flags = {}, rng = Math.random) {
    const chance = GangRules.raidChance(flags);
    const intact = GangRules.KELLER_DOORS.filter((d) => broken[d] == null);
    if (!chance || !intact.length) return null;
    if (rng() >= chance) return null;
    return intact[Math.min(intact.length - 1, Math.floor(rng() * intact.length))];
  },
  AMBUSH: { base: 0.15, max: 3 },
  ambushChance(flags, weapon) { return flags.bahnhof ? 0 : GangRules.AMBUSH.base * (weapon && weapon.ambushMult ? weapon.ambushMult : 1); },
  ambushCount(rng) { return 1 + Math.min(GangRules.AMBUSH.max - 1, Math.floor(rng() * GangRules.AMBUSH.max)); },
  ROB: { pct: 0.2, max: 5000 },
  robbery(balance) { return Math.max(0, Math.min(GangRules.ROB.max, Math.round(balance * GangRules.ROB.pct))); },
  /* ---- Schwellen ---- */
  ROYAL: { warn: 10000, bann: 15000 },
  ABLOESE: 100000, FLUCHT_MIN: 30000, IGOR_BIERE: 3, BELEG_RISIKO: 0.2, BELEGE_NOETIG: 3,
```

- [ ] **Step 4: Tests grün** – Run: `node tests/run-selftest.mjs`

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(gang): Wochen, Abrechnung, Nachtkasse, Überfall, Hinterhalt, Raub, Schwellen (rein)"
```

---

### Task 3: `STORY_STASH` – Gerüst, Events, `fns`, Aktionen, Enden (ohne Szenentexte)

**Files:**
- Create: Block `<script id="story-stash">` direkt nach `</script>` von `story-kater`
- Modify: `tests/run-selftest.mjs` (`'story-kater', 'story-stash'`), `achievements` (DEFS)
- Test: `selftest` (Abschnitt `/* ---- Story 3: Die Wäsche ---- */`)

**Interfaces:**
- Consumes: `GangRules` (Task 2), Engine 3, Jobs `eintreiber`/`kurierfahrt`, Tür `hinterzimmer`, Schaufenster `pfandleihe`, `Shootout`.
- Produces: `STORY_STASH` mit allen Feldern; Szenen in dieser Task nur als **Stubs** (`'stash.x': [{ bg: 'bar', who: 'du', text: 'stash.x' }]` bzw. Funktionen mit einem Panel), damit `validate` grün ist – Task 4 ersetzt sie durch die Texte. Szenen mit Wahl (Angebot, Igor, Beleg, Razzia, Ablöse, Kredit, Flucht, Finale) müssen schon in dieser Task ihre `choices` mit `effects` tragen, denn die Tests prüfen die Effekte.

- [ ] **Step 1: Failing Tests**

```js
/* ---- Story 3: Die Wäsche ---- */
const STASH_JOBS = ['spueler', 'post', 'taxi', 'tuersteher', 'croupier', 'eintreiber', 'kurier', 'praktikant', 'docassi', 'filialleiter', 'kurierfahrt'];
const stashState = (o = {}, prev = 'wirt') => Object.assign(base({ balance: 5000, car: 'mercC', weapon: 0, flags: {} }), { story: StoryRules.freshStoryPart(STORY_STASH, { kater: { lastPlayed: 1, endings: [prev], last: prev } }) }, o);
/* Events eines Hooks wie die Engine anwenden; gibt [eventIds, outs] zurück – outs = Rückgaben der Effekte (scene/force/toast) */
const stashHook = (s, at, rng = seq(0.99)) => {
  const ids = [], outs = [];
  for (const e of StoryRules.dueEvents(STORY_STASH, s, at)) {
    ids.push(e.id);
    for (const eff of e.effects || []) outs.push(StoryRules.applyEffect(s, eff, STORY_STASH, rng));
    if (e.once) s.story.seen.push(e.id);
    if (e.daily) (s.story.seenDay || (s.story.seenDay = {}))[e.id] = s.story.day;
  }
  return [ids, outs];
};
/* Wahl in einer Szene anwenden: Effekte der Choice mit value in panels */
const stashChoose = (s, sceneId, value, extra = {}, rng = seq(0.99)) => {
  const def = STORY_STASH.scenes[sceneId];
  const ctx = Object.assign({ raw: { balance: s.balance, day: s.story.day, vars: Object.assign({}, s.story.vars), flags: Object.assign({}, s.story.flags) }, prev: s.story.prev, flags: s.story.flags }, extra);
  const panels = typeof def === 'function' ? def(ctx) : def;
  const outs = [];
  for (const p of panels) for (const ch of p.choices || []) if (ch.value === value) for (const eff of ch.effects || []) outs.push(StoryRules.applyEffect(s, eff, STORY_STASH, rng));
  return outs;
};
T.test('STORY_STASH ist gültig, setzt Der Kater voraus, nicht nach Bett', () => {
  T.eq(StoryRules.validate(STORY_STASH, Object.keys(STORY_STASH.scenes), STASH_JOBS, ['probe', 'schuld', 'kater', 'stash'], { kater: STORY_KATER }), []);
  T.eq([STORY_STASH.requires, STORY_STASH.days, STORY_STASH.prevEndings], ['kater', 30, ['wirt', 'nuechtern', 'taxi', 'stammgast', 'brownie']]);
  T.ok(STORY_STASH.lockText.length > 10);
  T.eq(StoryRules.lockReasonFor(STORY_STASH, { kater: { endings: ['bett'], last: 'bett' } }), 'prevEnding');
  T.eq(StoryRules.lockReasonFor(STORY_STASH, { kater: { endings: ['bett', 'wirt'], last: 'wirt' } }), null);
  T.eq(STORY_STASH.endings.map((e) => e.id), ['kanal', 'krieg', 'kommissar', 'abloese', 'flucht', 'strohmann']);
  T.eq(STORY_STASH.endings.filter((e) => e.immediate).length, 5);
  T.eq(Object.keys(STORY_STASH.trophies).sort(), ['abloese', 'kommissar', 'krieg']);
  T.eq(STORY_STASH.events[0].id, 'abrechnung', 'Abrechnung läuft vor allen anderen Nacht-Events');
});
T.test('STORY_STASH: Start, Tag-1-Morgen je Vorgängerende (Kredit, trocken, Brownie), Auto, Hinterzimmer sichtbar', () => {
  const s = stashState();
  T.eq(s.story.unlocked.jobs, ['eintreiber']);
  T.eq(s.story.unlocked.doors, ['roulette', 'slots', 'horses', 'russian', 'blackjack']);
  T.eq(s.story.unlocked.rooms, ['bar', 'doc', 'bank', 'invest', 'life', 'stadt', 'royal']);
  T.eq(s.story.disabled, ['tinder', 'house', 'dealer', 'brownie']);
  T.eq(s.story.vars.zorn, 0); T.eq(s.story.vars.woche, 0);
  for (const [prev, kredit, trocken, brownie] of [['wirt', 0, false, false], ['nuechtern', 30000, true, false], ['taxi', 30000, false, false], ['stammgast', 50000, false, false], ['brownie', 50000, false, true]]) {
    const t = stashState({ car: null }, prev);
    stashHook(t, 'morning');
    T.eq(t.story.vars.kredit, kredit, `${prev}: Kredit`);
    T.eq(!!t.story.flags.trocken, trocken, `${prev}: trocken`);
    T.eq(!!(t.story.enabled && t.story.enabled.brownie), brownie, `${prev}: Brownie`);
    T.eq(StoryRules.purchaseAllowed(t, 'beer'), trocken ? false : null, `${prev}: Bier`);
    T.eq(t.car, 'mercC'); T.eq(t.story.enabled.hinterzimmer, true); T.eq(t.story.unlocked.doors.includes('hinterzimmer'), false, 'Tisch kommt Tag 2');
  }
  const d2 = stashState(); d2.story.day = 2; d2.story.seen.push('einrichten');
  T.ok(stashHook(d2, 'morning')[0].includes('tisch')); T.ok(d2.story.unlocked.doors.includes('hinterzimmer'));
  const d8 = stashState(); d8.story.day = 8;
  stashHook(d8, 'morning'); T.eq(d8.story.enabled.pfandleihe, true);
});
T.test('STORY_STASH: Kapitel 1/8/15/22, Kurierfahrt ab Kapitel 2', () => {
  const s = stashState();
  for (const [day, id] of [[1, 'k1'], [7, 'k1'], [8, 'k2'], [15, 'k3'], [22, 'k4'], [30, 'k4']]) { s.story.day = day; T.eq(StoryRules.chapterFor(STORY_STASH, s).id, id, `Tag ${day}`); }
  T.eq(STORY_STASH.chapters[1].unlock.jobs, ['kurierfahrt']);
});
T.test('STORY_STASH: Lieferung Tag 1/8/15/22 – Geld, Woche, Ziel, Umsatz-Reset, Bahnhof ×1,5, nur einmal pro Tag', () => {
  const s = stashState({ balance: 5000 });
  const [ids, outs] = stashHook(s, 'night');
  T.ok(ids.includes('lieferung')); T.eq(outs.find((o) => o.scene).scene, 'stash.lieferung');
  T.eq([s.balance, s.story.vars.woche, s.story.vars.ziel, s.story.vars.rueckgabe, s.story.vars.umsatz], [15000, 1, 20000, 11000, 0]);
  T.eq(stashHook(s, 'night')[0].includes('lieferung'), false, 'daily');
  s.story.day = 8; s.story.vars.umsatz = 12345; s.story.vars.umsatzRoyal = 4000; s.story.vars.eintreiberWoche = 2; s.story.flags.royalWarn = true; s.story.flags.bahnhof = true;
  stashHook(s, 'night');
  T.eq([s.balance, s.story.vars.woche, s.story.vars.ziel, s.story.vars.umsatz, s.story.vars.umsatzRoyal, s.story.vars.eintreiberWoche, s.story.flags.royalWarn], [35000, 2, 60000, 0, 0, 0, undefined]);
  s.story.day = 9; T.eq(stashHook(s, 'night')[0].includes('lieferung'), false, 'Tag 9 keine Lieferung');
});
T.test('STORY_STASH: Abrechnung – vier Ausgänge, Beleg, Kredit, Zorn, Anabi erfährt vom Bahnhof', () => {
  const mk = (umsatz, balance, extra = {}) => { const s = stashState({ balance }); s.story.day = 7; Object.assign(s.story.vars, { woche: 1, ziel: 20000, rueckgabe: 11000, umsatz, kredit: 30000 }); Object.assign(s.story.flags, extra); return s; };
  let s = mk(20000, 15000);
  let [ids, outs] = stashHook(s, 'night');
  T.eq(ids[0], 'abrechnung'); T.eq(outs[0].scene, 'stash.abrechnung');
  T.eq([s.balance, s.story.vars.zorn, s.story.vars.kredit, s.story.vars.belege, s.story.vars.belegeOffen, s.story.vars.abrechnungenOk, s.story.vars.ausgang], [4000, 0, 25000, 1, 1, 1, 0]);
  s = mk(10000, 15000); stashHook(s, 'night');
  T.eq([s.balance, s.story.vars.zorn, s.story.vars.kredit, s.story.vars.belege, s.story.vars.ausgang], [4000, 1, 30000, 0, 1]);
  s = mk(20000, 5000); stashHook(s, 'night');
  T.eq([s.balance, s.story.vars.zorn, s.story.vars.kredit, s.story.vars.ausgang], [0, 1, 39000, 2]);
  s = mk(0, 0); stashHook(s, 'night');
  T.eq([s.story.vars.zorn, s.story.vars.kredit, s.story.vars.ausgang], [2, 46500, 3]);
  s = mk(0, 0, { bahnhof: true }); stashHook(s, 'night');
  T.eq([s.story.vars.zorn, s.story.flags.anabiWeiss], [3, true], 'Bahnhof-Deal: einmalig +1');
  T.eq(StoryRules.ending(STORY_STASH, s, { immediateOnly: true }).id, 'kanal', 'Zorn 3 → Kanal sofort');
  s = mk(20000, 15000, { bahnhof: true, anabiWeiss: true }); s.story.vars.zorn = 1; stashHook(s, 'night');
  T.eq(s.story.vars.zorn, 0, 'nicht zweimal');
  s = mk(20000, 15000); s.story.vars.zorn = 0; s.story.vars.abrechnungenOk = 3; [ids, outs] = stashHook(s, 'night');
  T.ok(outs.some((o) => o.achievement === 'waschmaschine'), '4/4 → Waschmaschine');
});
T.test('STORY_STASH: Nachtkasse morgens ab Tag 2 (daily), kaputte Spiele fehlen', () => {
  const s = stashState({ balance: 0 }); s.story.day = 3; s.story.seen.push('einrichten', 'tisch');
  const [ids, outs] = stashHook(s, 'morning');
  T.ok(ids.includes('nachtkasse')); T.eq(s.balance, 1250); T.ok(outs.some((o) => o.toast && o.toast.text.includes('1.250')));
  T.eq(stashHook(s, 'morning')[0].includes('nachtkasse'), false, 'daily');
  s.story.day = 4; s.story.broken = { slots: 4000, roulette: 6000 };
  stashHook(s, 'morning'); T.eq(s.balance, 2000);
});
T.test('STORY_STASH: Überfall ab Tag 8 – zertrümmert eine Tür, Igor halbiert, Bahnhof stoppt, Flag ueberfallHeute', () => {
  const s = stashState(); s.story.day = 8;
  let [, outs] = stashHook(s, 'night', seq(0.1, 0, 0.99));            // Lieferung (kein rng); Überfall: rng 0.1 < 0.25, Auswahl 0 → roulette; Hinterhalt entfällt (ueberfallHeute, kein rng)
  T.eq(s.story.broken, { roulette: 6000 }); T.eq(s.story.flags.ueberfallHeute, true); T.ok(outs.some((o) => o.scene === 'stash.ueberfall'));
  const t = stashState({ balance: 50000 }); t.story.day = 9; t.story.flags.igor = true;
  stashHook(t, 'night', seq(0.1, 0.5, 0.99));                          // Überfall 0.1 < 0.15, Auswahl 0.5 → 3. intakte (horses); Hinterhalt entfällt (ueberfallHeute)
  T.eq(t.story.broken, { horses: 1500 });
  const u = stashState(); u.story.day = 9; u.story.flags.bahnhof = true;
  stashHook(u, 'night', seq(0, 0, 0)); T.eq(u.story.broken, {}, 'Bahnhof-Deal: keine Überfälle');
  const v = stashState(); v.story.day = 7; stashHook(v, 'night', seq(0, 0, 0)); T.eq(v.story.broken, {}, 'vor Tag 8 nichts');
  s.story.day = 9; stashHook(s, 'morning'); T.eq(s.story.flags.ueberfallHeute, false, 'morgens gelöscht');
});
T.test('STORY_STASH: Hinterhalt – ohne Waffe Raub + blaues Auge, mit Waffe Schießerei, nicht nach Überfall/Bahnhof', () => {
  const s = stashState({ balance: 10000 }); s.story.day = 9;
  let [, outs] = stashHook(s, 'night', seq(0.99, 0.1, 0.5));           // Überfall 0.99 nein; Hinterhalt 0.1 < 0.15; Anzahl 0.5 → 2
  T.eq([s.balance, s.story.flags.blauesAuge, s.story.luckMod, s.story.vars.hinterhaltN], [8000, true, -15, 2]);
  T.ok(outs.some((o) => o.scene === 'stash.hinterhalt.raub'));
  s.story.day = 10; stashHook(s, 'sleep'); T.eq([s.story.flags.blauesAuge, s.story.luckMod], [false, 0], 'nächste Nacht: blaues Auge weg');
  const w = stashState({ balance: 10000, weapon: 1 }); w.story.day = 9;
  [, outs] = stashHook(w, 'night', seq(0.99, 0.1, 0.99));
  const f = outs.find((o) => o.force === 'shootout');
  T.eq([w.balance, f.fight.kind, f.fight.foes], [10000, 'hinterhalt', ['junge', 'junge', 'junge']]);
  T.ok(outs.some((o) => o.scene === 'stash.hinterhalt'));
  const g = stashState({ weapon: 3 }); g.story.day = 9; stashHook(g, 'night', seq(0.99, 0.1, 0)); T.eq(g.story.vars.hinterhaltN, undefined, 'Goldene: 0.1 ≥ 0.075');
  const b = stashState(); b.story.day = 9; b.story.flags.bahnhof = true; stashHook(b, 'night', seq(0, 0, 0)); T.eq(b.story.flags.blauesAuge, undefined);
});
T.test('STORY_STASH: fight:after – Hinterhalt gewonnen Ruf +1, verloren Raub; Tutorial; Finale setzt anabiTot/kanal', () => {
  const s = stashState({ balance: 10000 }); s.story.day = 9;
  Object.assign(s.story.flags, { fight_hinterhalt: true, fightWon: true, fightLost: false });
  stashHook(s, 'fight:after'); T.eq([s.story.vars.ruf, s.balance], [1, 10000]);
  Object.assign(s.story.flags, { fightWon: false, fightLost: true });
  const [, outs] = stashHook(s, 'fight:after'); T.eq([s.balance, s.story.flags.blauesAuge], [8000, true]); T.ok(outs.some((o) => o.scene === 'stash.hinterhalt.lost'));
  const t = stashState(); t.story.day = 10;
  const [ids, o2] = stashHook(t, 'night', seq(0.99, 0.99, 0.99));
  T.ok(ids.includes('tutorial')); const f = o2.find((o) => o.force === 'shootout'); T.eq([f.fight.kind, f.fight.foes, f.fight.bonus], ['tutorial', ['laeufer'], 100]);
  Object.assign(t.story.flags, { fight_tutorial: true, fightWon: true, fightLost: false }); stashHook(t, 'fight:after'); T.eq(t.story.vars.ruf, 1);
  const fi = stashState(); Object.assign(fi.story.flags, { fight_finale: true, fightWon: true, fightLost: false }); stashHook(fi, 'fight:after');
  T.eq(fi.story.flags.anabiTot, true); T.eq(StoryRules.ending(STORY_STASH, fi, { immediateOnly: true }).id, 'krieg');
  const fl = stashState(); Object.assign(fl.story.flags, { fight_finale: true, fightWon: false, fightLost: true }); stashHook(fl, 'fight:after');
  T.eq(StoryRules.ending(STORY_STASH, fl, { immediateOnly: true }).id, 'kanal');
});
T.test('STORY_STASH: Angebot der Bahnhof-Jungs ab Tag 15 mit Ruf 2, Annehmen/Ablehnen', () => {
  const s = stashState(); s.story.day = 15; s.story.vars.ruf = 1;
  T.eq(stashHook(s, 'night', seq(0.99, 0.99, 0.99))[0].includes('angebot'), false);
  s.story.day = 16; s.story.vars.ruf = 2;
  T.ok(stashHook(s, 'night', seq(0.99, 0.99, 0.99))[0].includes('angebot'));
  stashChoose(s, 'stash.angebot', 'ja'); T.eq(s.story.flags.bahnhof, true);
  const n = stashState(); n.story.day = 16; n.story.vars.ruf = 2; stashChoose(n, 'stash.angebot', 'nein'); T.eq(n.story.flags.bahnhofNein, true);
  n.story.seen.push('angebot'); T.eq(stashHook(n, 'night', seq(0.99, 0.99, 0.99))[0].includes('angebot'), false, 'once');
});
T.test('STORY_STASH: Igor – Bar-Aktion ab Tag 8, 100 €, einmal pro Tag, drittes Bier → igor + Trophäe; trocken → Cola', () => {
  const s = stashState({ balance: 1000 }); s.story.day = 8;
  const acts = () => StoryRules.actionsFor(STORY_STASH, s, 'bar').map((a) => a.id);
  T.ok(acts().includes('igorBier')); T.eq(acts().includes('igorCola'), false);
  stashChoose(s, 'stash.igor', 'prost'); T.eq([s.balance, s.story.vars.igorBiere, s.story.flags.igorHeute], [900, 1, true]);
  T.eq(acts().includes('igorBier'), false, 'heute schon');
  s.story.day = 9; stashHook(s, 'morning'); T.eq(s.story.flags.igorHeute, false);
  stashChoose(s, 'stash.igor', 'prost'); s.story.flags.igorHeute = false;
  const outs = stashChoose(s, 'stash.igor', 'prost');
  T.eq([s.story.vars.igorBiere, s.story.flags.igor], [3, true]); T.ok(outs.some((o) => o.achievement === 'igorsFreund'));
  T.eq(acts().includes('igorBier'), false, 'Igor ist deiner');
  const t = stashState({ balance: 1000 }); t.story.day = 8; t.story.flags.trocken = true;
  T.ok(StoryRules.actionsFor(STORY_STASH, t, 'bar').map((a) => a.id).includes('igorCola'));
});
T.test('STORY_STASH: Brandt ab Tag 15, Belege übergeben mit Risiko, Razzia ab Tag 26 mit 3 Belegen', () => {
  const s = stashState(); s.story.day = 15; s.story.vars.belege = 2; s.story.vars.belegeOffen = 2;
  const acts = () => StoryRules.actionsFor(STORY_STASH, s, 'bar').map((a) => a.id);
  T.ok(acts().includes('brandt')); T.eq(acts().includes('beleg'), false, 'erst mit Brandt reden');
  stashChoose(s, 'stash.brandt', 'ok'); T.eq(s.story.flags.brandtKennt, true); T.ok(acts().includes('beleg'));
  let outs = stashChoose(s, 'stash.beleg', 'geben', {}, seq(0.5));    // 0.5 ≥ 0.2: unbemerkt
  T.eq([s.story.vars.uebergeben, s.story.vars.belegeOffen, s.story.vars.zorn], [1, 1, 0]); T.ok(outs.some((o) => o.toast));
  outs = stashChoose(s, 'stash.beleg', 'geben', {}, seq(0.1));        // 0.1 < 0.2: Igor sieht es
  T.eq([s.story.vars.uebergeben, s.story.vars.belegeOffen, s.story.vars.zorn], [2, 0, 1]); T.ok(outs.some((o) => o.scene === 'stash.beleg.gesehen'));
  T.eq(acts().includes('beleg'), false, 'keine offenen Belege');
  s.story.flags.igor = true; s.story.vars.belegeOffen = 1; let calls = 0;
  stashChoose(s, 'stash.beleg', 'geben', {}, () => { calls++; return 0; }); T.eq([s.story.vars.zorn, calls], [1, 0], 'mit Igor kein Risiko, kein Würfel');
  T.eq(acts().includes('razzia'), false, 'Tag 15');
  s.story.day = 26; T.ok(acts().includes('razzia'));
  stashChoose(s, 'stash.razzia', 'ja'); T.eq(StoryRules.ending(STORY_STASH, s, { immediateOnly: true }).id, 'kommissar');
  const u = stashState(); u.story.day = 26; u.story.vars.uebergeben = 2; T.eq(StoryRules.actionsFor(STORY_STASH, u, 'bar').map((a) => a.id).includes('razzia'), false);
});
T.test('STORY_STASH: Kurier-Kontrolle (job:after) – Zorn +1, Beleg +1', () => {
  const s = stashState(); s.story.flags.kontrolle = true;
  const [ids, outs] = stashHook(s, 'job:after');
  T.eq(ids, ['kontrolle']); T.eq([s.story.vars.zorn, s.story.vars.belege, s.story.vars.belegeOffen, s.story.flags.kontrolle], [1, 1, 1, false]);
  T.ok(outs.some((o) => o.scene === 'stash.kontrolle') || STORY_STASH.events.find((e) => e.id === 'kontrolle').scene === 'stash.kontrolle');
});
T.test('STORY_STASH: Eintreiber – 1.000 €, keine Stärke nötig, Zorn −1, max 2/Woche', () => {
  const s = stashState({ strength: 0 }); s.story.vars.zorn = 2;
  const job = StoryRules.jobDef({ id: 'eintreiber', requires: { strength: { gte: 4 } }, base: 150 }, STORY_STASH);
  T.eq([job.base, StoryRules.jobAvailable(job, s).ok], [1000, true]);
  for (const sc of STORY_STASH.jobScenes.eintreiber) for (const eff of STORY_STASH.jobEffects[sc]) StoryRules.applyEffect(s, eff, STORY_STASH);
  T.eq([s.story.vars.zorn, s.story.vars.eintreiberWoche], [0, 2]);
  T.eq(StoryRules.jobAvailable(job, s).ok, false, 'zwei pro Woche');
});
T.test('STORY_STASH: Sylvie – Warnung ab 10.000 einmal pro Woche, Hausverbot ab 15.000 (Betreten und mitten im Spiel)', () => {
  const s = stashState(); s.story.vars.umsatzRoyal = 10000;
  T.eq(stashHook(s, 'royal:enter')[0], ['sylvieWarn']); T.eq(s.story.flags.royalWarn, true);
  T.eq(stashHook(s, 'royal:enter')[0], [], 'einmal');
  s.story.vars.umsatzRoyal = 15000;
  const [ids, outs] = stashHook(s, 'spin:after');
  T.ok(ids.includes('royalBannSpin')); T.eq(s.story.flags.royalBann, true); T.eq(s.story.unlocked.rooms.includes('royal'), false); T.ok(outs.some((o) => o.show === 'stadt'));
  T.eq(stashHook(s, 'royal:enter')[0].includes('royalBannEnter'), false, 'nicht doppelt');
  T.eq(STORY_STASH.lockReason.royal, 'Hausverbot');
});
T.test('STORY_STASH: Aktionen Ablöse, Kredit abzahlen, Flucht, Anabi stellen', () => {
  const s = stashState({ balance: 140000 }); s.story.day = 22; s.story.vars.kredit = 30000; s.story.vars.zorn = 1;
  const bank = () => StoryRules.actionsFor(STORY_STASH, s, 'bank').map((a) => a.id);
  T.ok(bank().includes('abloese')); T.ok(bank().includes('kredit'));
  stashChoose(s, 'stash.kredit', 'zahlen'); T.eq([s.balance, s.story.vars.kredit], [135000, 25000]);
  s.story.vars.zorn = 2; T.eq(bank().includes('abloese'), false, 'Zorn ≤ 1'); s.story.vars.zorn = 1;
  s.balance = 100000; let outs = stashChoose(s, 'stash.abloese', 'zahlen'); T.ok(outs.some((o) => o.toast), 'zu wenig: 125.000 nötig'); T.eq(s.story.flags.frei, undefined);
  s.balance = 125000; stashChoose(s, 'stash.abloese', 'zahlen'); T.eq([s.balance, s.story.flags.frei, s.story.vars.kredit], [0, true, 0]);
  T.eq(StoryRules.ending(STORY_STASH, s, { immediateOnly: true }).id, 'abloese');
  const f = stashState({ balance: 30000 }); f.story.day = 20;
  T.ok(StoryRules.actionsFor(STORY_STASH, f, 'stadt').map((a) => a.id).includes('flucht'));
  f.balance = 29999; T.eq(StoryRules.actionsFor(STORY_STASH, f, 'stadt').length, 0);
  f.balance = 30000; stashChoose(f, 'stash.flucht', 'ja'); T.eq(StoryRules.ending(STORY_STASH, f, { immediateOnly: true }).id, 'flucht');
  const a = stashState({ weapon: 0 }); a.story.day = 25; a.story.flags.bahnhof = true;
  const bar = (st) => StoryRules.actionsFor(STORY_STASH, st, 'bar').map((x) => x.id);
  T.eq(bar(a).includes('anabiStellen'), false, 'ohne Waffe kein Knopf');
  a.weapon = 1; T.ok(bar(a).includes('anabiStellen'));
  outs = stashChoose(a, 'stash.finale', 'los'); T.eq(outs.find((o) => o.force).fight.foes, ['igor', 'anabi']);
  a.story.flags.igor = true; outs = stashChoose(a, 'stash.finale', 'los'); T.eq(outs.find((o) => o.force).fight.foes, ['anabi']);
});
T.test('STORY_STASH: Enden-Priorität und Fallback', () => {
  const s = stashState(); s.story.day = 31;
  T.eq(StoryRules.ending(STORY_STASH, s).id, 'strohmann');
  Object.assign(s.story.flags, { flucht: true, frei: true, razzia: true, anabiTot: true }); s.story.vars.zorn = 3;
  T.eq(StoryRules.ending(STORY_STASH, s).id, 'kanal');
  s.story.vars.zorn = 0; T.eq(StoryRules.ending(STORY_STASH, s).id, 'krieg');
  delete s.story.flags.anabiTot; T.eq(StoryRules.ending(STORY_STASH, s).id, 'kommissar');
  delete s.story.flags.razzia; T.eq(StoryRules.ending(STORY_STASH, s).id, 'abloese');
  delete s.story.flags.frei; T.eq(StoryRules.ending(STORY_STASH, s).id, 'flucht');
});
T.test('STORY_STASH: Hausmeister (alle fünf repariert) und Der Stumme nickt', () => {
  const s = stashState(); s.story.day = 5;
  for (const d of GangRules.KELLER_DOORS) s.story.vars[`repariert_${d}`] = 1;
  const [, outs] = stashHook(s, 'morning'); T.ok(outs.some((o) => o.achievement === 'hausmeister'));
  s.story.vars.umsatzHinterzimmer = 100000;
  T.ok(stashHook(s, 'spin:after')[1].some((o) => o.achievement === 'stummeNickt'));
  T.eq(stashHook(s, 'spin:after')[0].includes('stummeNickt'), false, 'einmal');
});
```

- [ ] **Step 2: Fehlschlag prüfen** – Run: `node tests/run-selftest.mjs` → `STORY_STASH is not defined`.

- [ ] **Step 3: Achievements** (in `Achievements.DEFS`, Story-Gruppe hinter `stummeNickt`)

```js
    { id: 'schnellsteHand', title: 'Schnellste Hand', icon: '🔫', desc: 'Anabi Stash im Duell erledigt.', group: 'story' },
    { id: 'kronzeuge', title: 'Kronzeuge', icon: '👮', desc: 'Brandt hat seine Razzia bekommen.', group: 'story' },
    { id: 'sauber', title: 'Sauber', icon: '💰', desc: 'Die Ablöse gezahlt. Der Keller ist wirklich deiner.', group: 'story' },
    { id: 'waschmaschine', title: 'Waschmaschine', icon: '🧺', desc: 'Alle vier Abrechnungen geschafft.', group: 'story' },
    { id: 'hausmeister', title: 'Hausmeister', icon: '🔧', desc: 'Alle fünf Spiele mindestens einmal repariert.', group: 'story' },
    { id: 'igorsFreund', title: 'Igors Freund', icon: '🍺', desc: 'Drei Abende mit Igor. Er steht jetzt neben dir.', group: 'story' },
```

- [ ] **Step 4: Block `story-stash` anlegen**

```html
<script id="story-stash">
/* ================= STORY 3: DIE WÄSCHE – Anabi Stash, vier Wochen, sechs Auswege ================= */
const STORY_STASH = {
  id: 'stash', title: 'Die Wäsche', days: 30, requires: 'kater',
  prevEndings: ['wirt', 'nuechtern', 'taxi', 'stammgast', 'brownie'],
  lockText: '„Der Kater“ endete im Bett beim Doc. Wer tot ist, wäscht nichts mehr.',
  start: {
    balance: 5000,
    unlocked: { jobs: ['eintreiber'], doors: ['roulette', 'slots', 'horses', 'russian', 'blackjack'], rooms: ['bar', 'doc', 'bank', 'invest', 'life', 'stadt', 'royal'] },
    vars: { woche: 0, umsatz: 0, umsatzRoyal: 0, umsatzHinterzimmer: 0, umsatzTotal: 0, ziel: 0, rueckgabe: 0, lieferung: 0, zorn: 0, kredit: 0, belege: 0, belegeOffen: 0, uebergeben: 0, ruf: 0, igorBiere: 0, eintreiberWoche: 0, abrechnungenOk: 0, ausgang: 0, anabiErfaehrt: 0 },
  },
  varMax: { zorn: 3 },
  prices: { brownie: 1000 },
  disabled: ['tinder', 'house', 'dealer', 'brownie'],
  turnoverGroups: { umsatzRoyal: ['megaslots', 'craps', 'wheel'], umsatzHinterzimmer: ['baccarat'] },
  jobOverrides: {
    eintreiber: { base: 1000, requires: { var: 'eintreiberWoche', lt: 2 }, requireText: 'Anabi hat nicht jeden Tag Schuldner', pay: '1.000 €', desc: 'Anabi hat eine Liste. Wer sie abarbeitet, macht ihn ruhiger.' },
  },
  lockReason: { royal: 'Hausverbot', hinterzimmer: 'Anabis Tisch kommt morgen' },
  N: { abloese: GangRules.ABLOESE, fluchtMin: GangRules.FLUCHT_MIN, kreditSchritt: GangRules.KREDIT_SCHRITT },
  hud: [
    { var: 'umsatz', label: '🧺 Umsatz', fmt: 'money', max: (s) => s.story.vars.ziel || 0 },
    { var: 'zorn', label: '😡 Zorn', max: 3, tone: 'danger' },
    { var: 'kredit', label: '🧾 Kredit', fmt: 'money' },
  ],
  goal: (s) => {
    const v = s.story.vars, f = s.story.flags, fmt = StoryRules.fmtMoney;
    if (f.frei) return 'Der Keller ist deiner. Wirklich.';
    if (!v.woche) return 'Der Keller gehört dir. Auf dem Papier.';
    const heute = [7, 14, 21, 28].includes(s.story.day);
    return `Woche ${v.woche}: Umsatz ${fmt(v.umsatz)} / ${fmt(v.ziel)} · ${heute ? 'HEUTE ABEND' : `Tag ${v.woche * 7}`}: ${fmt(v.rueckgabe)} fällig`;
  },
  intro: 'stash.intro',
  /* ---- Story-Funktionen (Effekt call) – rechnen, setzen Vars/Flags, geben Szene/Toast/Force zurück ---- */
  fns: {
    lieferung(s) {
      const st = s.story, v = st.vars;
      const w = GangRules.week(v.woche + 1, !!st.flags.bahnhof);
      v.woche++; v.umsatz = 0; v.umsatzRoyal = 0; v.eintreiberWoche = 0;
      v.ziel = w.ziel; v.rueckgabe = w.rueckgabe; v.lieferung = w.lieferung;
      s.balance += w.lieferung;
      delete st.flags.royalWarn;
      return { scene: 'stash.lieferung' };
    },
    abrechnung(s) {
      const st = s.story, v = st.vars, f = st.flags;
      const r = GangRules.abrechnung({ umsatz: v.umsatz, ziel: v.ziel, balance: s.balance, rueckgabe: v.rueckgabe });
      s.balance -= r.pay;
      v.kredit = Math.max(0, (v.kredit || 0) + r.kreditDelta);
      v.zorn = GangRules.zorn(v.zorn, r.zornDelta);
      v.belege += r.belegDelta; v.belegeOffen += r.belegDelta;
      if (r.ausgang === 'ok') v.abrechnungenOk++;
      v.anabiErfaehrt = 0;
      if (f.bahnhof && !f.anabiWeiss) { f.anabiWeiss = true; v.zorn = GangRules.zorn(v.zorn, 1); v.anabiErfaehrt = 1; }
      v.ausgang = { ok: 0, umsatz: 1, geld: 2, beides: 3 }[r.ausgang];
      v.letztePay = r.pay;
      return { scene: 'stash.abrechnung' };
    },
    nachtkasse(s) {
      const r = GangRules.nachtkasse(s.story.broken);
      s.balance += r.sum;
      const namen = { roulette: 'Roulette', slots: 'Slots', horses: 'Pferde', russian: 'Russisch', blackjack: 'Blackjack' };
      return { toast: { icon: '🧾', title: 'Nachtkasse', text: `+${StoryRules.fmtMoney(r.sum)}${r.kaputt.length ? ` (${r.kaputt.map((d) => namen[d]).join(', ')} kaputt)` : ''}`, tone: r.sum > 0 ? 'win' : 'loss' } };
    },
    ueberfall(s, rng) {
      const st = s.story;
      const door = GangRules.raid(st.broken, st.flags, rng);
      if (!door) return {};
      st.broken = st.broken || {};
      st.broken[door] = GangRules.repairPrice(door, !!st.flags.igor);
      st.flags.ueberfallHeute = true;
      st.vars.letzterUeberfall = door;
      return { scene: 'stash.ueberfall' };
    },
    raub(s) {
      const st = s.story, loot = GangRules.robbery(s.balance);
      s.balance -= loot; st.vars.letzterRaub = loot;
      st.flags.blauesAuge = true; st.luckMod = -15;
      return {};
    },
    hinterhalt(s, rng) {
      const st = s.story;
      if (st.flags.ueberfallHeute || st.flags.bahnhof) return {};
      const w = GangRules.weapon(s);
      if (rng() >= GangRules.ambushChance(st.flags, w)) return {};
      const n = GangRules.ambushCount(rng);
      st.vars.hinterhaltN = n;
      if (!w.tier) { STORY_STASH.fns.raub(s); return { scene: 'stash.hinterhalt.raub' }; }
      return { scene: 'stash.hinterhalt', force: 'shootout', fight: { kind: 'hinterhalt', foes: Array(n).fill('junge') } };
    },
    hinterhaltVerloren(s) { STORY_STASH.fns.raub(s); return { scene: 'stash.hinterhalt.lost' }; },
    tutorial() { return { force: 'shootout', fight: { kind: 'tutorial', foes: ['laeufer'], bonus: 100 } }; },
    finale(s) { return { force: 'shootout', fight: { kind: 'finale', foes: s.story.flags.igor ? ['anabi'] : ['igor', 'anabi'] } }; },
    belegRisiko(s, rng) {
      const st = s.story, v = st.vars;
      v.uebergeben++; v.belegeOffen = Math.max(0, v.belegeOffen - 1);
      if (!st.flags.igor && rng() < GangRules.BELEG_RISIKO) { v.zorn = GangRules.zorn(v.zorn, 1); return { scene: 'stash.beleg.gesehen' }; }
      return { toast: { icon: '🧾', title: 'Beleg übergeben', text: `Brandt steckt den Zettel ein. ${v.uebergeben} von ${GangRules.BELEGE_NOETIG}.`, tone: 'info' } };
    },
    abloese(s) {
      const v = s.story.vars, price = GangRules.ABLOESE + (v.kredit || 0);
      if (s.balance < price) return { toast: { icon: '💰', title: `Ablöse: ${StoryRules.fmtMoney(price)}`, text: 'So viel liegt nicht auf dem Tisch.', tone: 'loss' } };
      s.balance -= price; v.kredit = 0; s.story.flags.frei = true;
      return {};
    },
    kreditZahlen(s) {
      const v = s.story.vars, amt = Math.min(GangRules.KREDIT_SCHRITT, v.kredit || 0, s.balance);
      if (amt <= 0) return {};
      s.balance -= amt; v.kredit -= amt;
      return { toast: { icon: '🧾', title: `−${StoryRules.fmtMoney(amt)}`, text: `Kredit noch ${StoryRules.fmtMoney(v.kredit)}.`, tone: 'info' } };
    },
  },
  chapters: [
    { id: 'k1', title: 'Der Hausherr', when: { day: { gte: 1 } } },
    { id: 'k2', title: 'Die Bahnhof-Jungs', when: { day: { gte: 8 } }, intro: 'stash.k2', unlock: { jobs: ['kurierfahrt'] } },
    { id: 'k3', title: 'Der Kommissar', when: { day: { gte: 15 } }, intro: 'stash.k3' },
    { id: 'k4', title: 'Abrechnung', when: { day: { gte: 22 } }, intro: 'stash.k4' },
  ],
  events: [
    /* ---- Nacht: Abrechnung zuerst ---- */
    { id: 'abrechnung', when: { any: [{ day: { eq: 7 } }, { day: { eq: 14 } }, { day: { eq: 21 } }, { day: { eq: 28 } }] }, daily: true, at: 'night', effects: [{ call: 'abrechnung' }] },
    { id: 'waschmaschine', when: { all: [{ var: 'abrechnungenOk', gte: 4 }, { notFlag: 'waschmaschine' }] }, once: true, at: 'night', effects: [{ flag: 'waschmaschine' }, { achievement: 'waschmaschine' }] },
    { id: 'lieferung', when: { any: [{ day: { eq: 1 } }, { day: { eq: 8 } }, { day: { eq: 15 } }, { day: { eq: 22 } }] }, daily: true, at: 'night', effects: [{ call: 'lieferung' }] },
    { id: 'tutorial', when: { day: { eq: 10 } }, once: true, at: 'night', scene: 'stash.tutorial', effects: [{ call: 'tutorial' }] },
    { id: 'ueberfall', when: { day: { gte: 8 } }, daily: true, at: 'night', effects: [{ call: 'ueberfall' }] },
    { id: 'hinterhalt', when: { day: { gte: 8 } }, daily: true, at: 'night', effects: [{ call: 'hinterhalt' }] },
    { id: 'angebot', when: { all: [{ day: { gte: 15 } }, { var: 'ruf', gte: 2 }, { notFlag: 'bahnhof' }, { notFlag: 'bahnhofNein' }] }, once: true, at: 'night', scene: 'stash.angebot' },
    /* ---- Morgen ---- */
    { id: 'einrichten', when: { day: { eq: 1 } }, once: true, at: 'morning', effects: [{ set: { car: 'mercC', weapon: 0 } }, { enable: ['hinterzimmer'] }] },
    { id: 'startKredit30', when: { all: [{ day: { eq: 1 } }, { any: [{ prevEnding: { story: 'kater', id: 'nuechtern' } }, { prevEnding: { story: 'kater', id: 'taxi' } }] }] }, once: true, at: 'morning', effects: [{ var: 'kredit', set: 30000 }] },
    { id: 'startKredit50', when: { all: [{ day: { eq: 1 } }, { any: [{ prevEnding: { story: 'kater', id: 'stammgast' } }, { prevEnding: { story: 'kater', id: 'brownie' } }] }] }, once: true, at: 'morning', effects: [{ var: 'kredit', set: 50000 }] },
    { id: 'startTrocken', when: { all: [{ day: { eq: 1 } }, { prevEnding: { story: 'kater', id: 'nuechtern' } }] }, once: true, at: 'morning', effects: [{ flag: 'trocken' }, { disable: ['beer'] }] },
    { id: 'startBrownie', when: { all: [{ day: { eq: 1 } }, { prevEnding: { story: 'kater', id: 'brownie' } }] }, once: true, at: 'morning', effects: [{ enable: ['brownie'] }] },
    { id: 'tisch', when: { day: { eq: 2 } }, once: true, at: 'morning', scene: 'stash.tisch', effects: [{ unlock: { doors: ['hinterzimmer'] } }] },
    { id: 'tagesstart', when: { day: { gte: 1 } }, daily: true, at: 'morning', effects: [{ unflag: 'ueberfallHeute' }, { unflag: 'igorHeute' }] },
    { id: 'nachtkasse', when: { day: { gte: 2 } }, daily: true, at: 'morning', effects: [{ call: 'nachtkasse' }] },
    { id: 'pfandleihe', when: { day: { gte: 8 } }, once: true, at: 'morning', effects: [{ enable: ['pfandleihe'] }] },
    { id: 'hausmeister', when: { all: [{ var: 'repariert_roulette', gte: 1 }, { var: 'repariert_slots', gte: 1 }, { var: 'repariert_horses', gte: 1 }, { var: 'repariert_russian', gte: 1 }, { var: 'repariert_blackjack', gte: 1 }] }, once: true, at: 'morning', effects: [{ achievement: 'hausmeister' }] },
    /* ---- Schlaf: blaues Auge heilt ---- */
    { id: 'blauesAugeEnde', when: { flag: 'blauesAuge' }, at: 'sleep', effects: [{ unflag: 'blauesAuge' }, { luckMod: 0 }] },
    /* ---- Schießerei-Ausgänge ---- */
    { id: 'tutorialWon', when: { all: [{ flag: 'fight_tutorial' }, { flag: 'fightWon' }] }, at: 'fight:after', scene: 'stash.tutorial.won', effects: [{ var: 'ruf', add: 1 }] },
    { id: 'tutorialLost', when: { all: [{ flag: 'fight_tutorial' }, { flag: 'fightLost' }] }, at: 'fight:after', scene: 'stash.tutorial.lost' },
    { id: 'hinterhaltWon', when: { all: [{ flag: 'fight_hinterhalt' }, { flag: 'fightWon' }] }, at: 'fight:after', effects: [{ var: 'ruf', add: 1 }, { toast: { icon: '🔫', title: 'Sie rennen', text: 'Ruf +1. Der Bahnhof redet.', tone: 'win' } }] },
    { id: 'hinterhaltLost', when: { all: [{ flag: 'fight_hinterhalt' }, { flag: 'fightLost' }] }, at: 'fight:after', effects: [{ call: 'hinterhaltVerloren' }] },
    { id: 'finaleWon', when: { all: [{ flag: 'fight_finale' }, { flag: 'fightWon' }] }, at: 'fight:after', effects: [{ flag: 'anabiTot' }] },
    { id: 'finaleLost', when: { all: [{ flag: 'fight_finale' }, { flag: 'fightLost' }] }, at: 'fight:after', effects: [{ flag: 'kanal' }] },
    /* ---- Kurierfahrt: Kontrolle ---- */
    { id: 'kontrolle', when: { flag: 'kontrolle' }, at: 'job:after', scene: 'stash.kontrolle', effects: [{ unflag: 'kontrolle' }, { var: 'zorn', add: 1 }, { var: 'belege', add: 1 }, { var: 'belegeOffen', add: 1 }] },
    /* ---- Royal: Sylvie ---- */
    { id: 'sylvieWarn', when: { all: [{ var: 'umsatzRoyal', gte: 10000 }, { var: 'umsatzRoyal', lt: 15000 }, { notFlag: 'royalWarn' }, { notFlag: 'royalBann' }] }, at: 'royal:enter', scene: 'stash.sylvie.warn', effects: [{ flag: 'royalWarn' }] },
    { id: 'royalBannEnter', when: { all: [{ var: 'umsatzRoyal', gte: 15000 }, { notFlag: 'royalBann' }] }, at: 'royal:enter', scene: 'stash.sylvie.bann', effects: [{ flag: 'royalBann' }, { lock: { rooms: ['royal'] } }, { show: 'stadt' }] },
    { id: 'royalBannSpin', when: { all: [{ var: 'umsatzRoyal', gte: 15000 }, { notFlag: 'royalBann' }] }, at: 'spin:after', scene: 'stash.sylvie.bann', effects: [{ flag: 'royalBann' }, { lock: { rooms: ['royal'] } }, { show: 'stadt' }] },
    /* ---- Hinterzimmer ---- */
    { id: 'stummeNickt', when: { all: [{ var: 'umsatzHinterzimmer', gte: 100000 }, { notFlag: 'stummeNickt' }] }, once: true, at: 'spin:after', effects: [{ flag: 'stummeNickt' }, { achievement: 'stummeNickt' }] },
  ],
  actions: [
    { id: 'igorBier', room: 'bar', label: '🍺 Bier mit Igor · 100 €', when: { all: [{ day: { gte: 8 } }, { notFlag: 'trocken' }, { notFlag: 'igor' }, { notFlag: 'igorHeute' }, { balance: { gte: 100 } }] }, scene: 'stash.igor' },
    { id: 'igorCola', room: 'bar', label: '🥤 Cola mit Igor · 100 €', when: { all: [{ day: { gte: 8 } }, { flag: 'trocken' }, { notFlag: 'igor' }, { notFlag: 'igorHeute' }, { balance: { gte: 100 } }] }, scene: 'stash.igor' },
    { id: 'brandt', room: 'bar', label: '👮 Mit Brandt reden', when: { all: [{ day: { gte: 15 } }, { notFlag: 'razzia' }] }, scene: 'stash.brandt' },
    { id: 'beleg', room: 'bar', label: '🧾 Beleg übergeben', when: { all: [{ day: { gte: 15 } }, { flag: 'brandtKennt' }, { var: 'belegeOffen', gte: 1 }, { notFlag: 'razzia' }] }, scene: 'stash.beleg' },
    { id: 'razzia', room: 'bar', label: '👮 Razzia auslösen', when: { all: [{ day: { gte: 26 } }, { var: 'uebergeben', gte: 3 }, { notFlag: 'razzia' }] }, scene: 'stash.razzia' },
    { id: 'anabiStellen', room: 'bar', label: '🔫 Anabi stellen', when: { all: [{ day: { gte: 25 } }, { flag: 'bahnhof' }, { weapon: { gte: 1 } }, { notFlag: 'anabiTot' }, { notFlag: 'kanal' }] }, scene: 'stash.finale' },
    { id: 'abloese', room: 'bank', label: '💰 Ablöse zahlen', when: { all: [{ day: { gte: 22 } }, { var: 'zorn', lte: 1 }, { notFlag: 'frei' }] }, scene: 'stash.abloese' },
    { id: 'kredit', room: 'bank', label: '🧾 Kredit abzahlen · 5.000 €', when: { all: [{ var: 'kredit', gte: 1 }, { balance: { gte: 5000 } }] }, scene: 'stash.kredit' },
    { id: 'flucht', room: 'stadt', label: '🌍 Abhauen', when: { all: [{ day: { gte: 20 } }, { balance: { gte: 30000 } }, { notFlag: 'flucht' }] }, scene: 'stash.flucht' },
  ],
  jobScenes: { eintreiber: ['stash.eintr.kiosk', 'stash.eintr.friseur'] },
  jobEffects: {
    'stash.eintr.kiosk': [{ var: 'eintreiberWoche', add: 1 }, { var: 'zorn', add: -1 }],
    'stash.eintr.friseur': [{ var: 'eintreiberWoche', add: 1 }, { var: 'zorn', add: -1 }],
  },
  endings: [
    { id: 'kanal', title: 'Der Kanal', priority: 70, immediate: true, when: { any: [{ var: 'zorn', gte: 3 }, { flag: 'kanal' }] }, scene: 'stash.ende.kanal' },
    { id: 'krieg', title: 'Der Krieg', priority: 60, immediate: true, when: { flag: 'anabiTot' }, scene: 'stash.ende.krieg' },
    { id: 'kommissar', title: 'Der Kommissar', priority: 50, immediate: true, when: { flag: 'razzia' }, scene: 'stash.ende.kommissar' },
    { id: 'abloese', title: 'Die Ablöse', priority: 40, immediate: true, when: { flag: 'frei' }, scene: 'stash.ende.abloese' },
    { id: 'flucht', title: 'Die Flucht', priority: 30, immediate: true, when: { flag: 'flucht' }, scene: 'stash.ende.flucht' },
    { id: 'strohmann', title: 'Der Strohmann', priority: 0, scene: 'stash.ende.strohmann', fallback: true },
  ],
  trophies: { krieg: 'schnellsteHand', kommissar: 'kronzeuge', abloese: 'sauber' },
  scenes: {
    /* Task 4 ersetzt die Stubs durch Texte; die Wahl-Szenen tragen ihre Effekte schon hier */
    'stash.intro': [{ bg: 'bar', who: 'du', text: 'stash.intro' }],
    'stash.tisch': [{ bg: 'keller', who: 'du', text: 'stash.tisch' }],
    'stash.k2': [{ bg: 'bahnhof', who: 'du', text: 'stash.k2' }], 'stash.k3': [{ bg: 'bar', who: 'du', text: 'stash.k3' }], 'stash.k4': [{ bg: 'bar', who: 'du', text: 'stash.k4' }],
    'stash.lieferung': [{ bg: 'keller', who: 'anabi', text: 'stash.lieferung' }],
    'stash.abrechnung': [{ bg: 'keller', who: 'anabi', text: 'stash.abrechnung' }],
    'stash.ueberfall': [{ bg: 'keller', who: 'igor', text: 'stash.ueberfall' }],
    'stash.hinterhalt': [{ bg: 'gasse', who: 'du', text: 'stash.hinterhalt' }],
    'stash.hinterhalt.raub': [{ bg: 'gasse', who: 'du', text: 'stash.hinterhalt.raub' }],
    'stash.hinterhalt.lost': [{ bg: 'gasse', who: 'du', text: 'stash.hinterhalt.lost' }],
    'stash.tutorial': [{ bg: 'keller', who: 'anabi', text: 'stash.tutorial' }],
    'stash.tutorial.won': [{ bg: 'bahnhof', who: 'anabi', text: 'stash.tutorial.won' }],
    'stash.tutorial.lost': [{ bg: 'bahnhof', who: 'anabi', text: 'stash.tutorial.lost' }],
    'stash.angebot': [{ bg: 'bahnhof', who: 'kessler', text: 'stash.angebot',
      choices: [{ label: 'Annehmen', value: 'ja', cls: 'red', effects: [{ flag: 'bahnhof' }] }, { label: 'Ablehnen', value: 'nein', cls: 'ghost', effects: [{ flag: 'bahnhofNein' }] }] }],
    'stash.igor': (ctx) => [{ bg: 'bar', who: 'igor', text: 'stash.igor',
      choices: [{ label: 'Prost', value: 'prost', cls: 'green', effects: [{ balance: -100 }, { var: 'igorBiere', add: 1 }, { flag: 'igorHeute' }, ...(ctx.raw.vars.igorBiere >= GangRules.IGOR_BIERE - 1 ? [{ flag: 'igor' }, { achievement: 'igorsFreund' }] : [])] }] }],
    'stash.brandt': (ctx) => [{ bg: 'bar', who: 'brandt', text: 'stash.brandt', choices: [{ label: 'Verstanden', value: 'ok', cls: 'ghost', effects: ctx.raw.flags.brandtKennt ? [] : [{ flag: 'brandtKennt' }] }] }],
    'stash.beleg': [{ bg: 'bar', who: 'brandt', text: 'stash.beleg', choices: [{ label: 'Übergeben', value: 'geben', cls: 'blue', effects: [{ call: 'belegRisiko' }] }, { label: 'Doch nicht', value: 'nein', cls: 'ghost' }] }],
    'stash.beleg.gesehen': [{ bg: 'bar', who: 'igor', text: 'stash.beleg.gesehen' }],
    'stash.razzia': [{ bg: 'bar', who: 'brandt', text: 'stash.razzia', choices: [{ label: 'Heute Nacht', value: 'ja', cls: 'red', effects: [{ flag: 'razzia' }] }, { label: 'Noch nicht', value: 'nein', cls: 'ghost' }] }],
    'stash.abloese': [{ bg: 'keller', who: 'anabi', text: 'stash.abloese', choices: [{ label: 'Zahlen', value: 'zahlen', cls: 'red', effects: [{ call: 'abloese' }] }, { label: 'Noch nicht', value: 'nein', cls: 'ghost' }] }],
    'stash.kredit': [{ bg: 'keller', who: 'stumme', text: 'stash.kredit', choices: [{ label: 'Zahlen', value: 'zahlen', cls: 'blue', effects: [{ call: 'kreditZahlen' }] }, { label: 'Doch nicht', value: 'nein', cls: 'ghost' }] }],
    'stash.flucht': [{ bg: 'strasse', who: 'du', text: 'stash.flucht', choices: [{ label: 'Abhauen', value: 'ja', cls: 'red', effects: [{ flag: 'flucht' }] }, { label: 'Bleiben', value: 'nein', cls: 'ghost' }] }],
    'stash.finale': [{ bg: 'keller', who: 'du', text: 'stash.finale', choices: [{ label: 'Los', value: 'los', cls: 'red', effects: [{ call: 'finale' }] }, { label: 'Nicht heute', value: 'nein', cls: 'ghost' }] }],
    'stash.kontrolle': [{ bg: 'strasse', who: 'brandt', text: 'stash.kontrolle' }],
    'stash.sylvie.warn': [{ bg: 'royal', who: 'sylvie', text: 'stash.sylvie.warn' }],
    'stash.sylvie.bann': [{ bg: 'royal', who: 'sylvie', text: 'stash.sylvie.bann' }],
    'stash.eintr.kiosk': [{ bg: 'strasse', who: 'du', text: 'stash.eintr.kiosk' }],
    'stash.eintr.friseur': [{ bg: 'strasse', who: 'du', text: 'stash.eintr.friseur' }],
    'stash.ende.kanal': [{ bg: 'hafen', who: 'du', text: 'stash.ende.kanal' }],
    'stash.ende.krieg': [{ bg: 'keller', who: 'kessler', text: 'stash.ende.krieg' }],
    'stash.ende.kommissar': [{ bg: 'keller', who: 'brandt', text: 'stash.ende.kommissar' }],
    'stash.ende.abloese': [{ bg: 'keller', who: 'anabi', text: 'stash.ende.abloese' }],
    'stash.ende.flucht': [{ bg: 'strasse', who: 'du', text: 'stash.ende.flucht' }],
    'stash.ende.strohmann': [{ bg: 'keller', who: 'anabi', text: 'stash.ende.strohmann' }],
  },
};
if (typeof Stories !== 'undefined') Stories.define(STORY_STASH);
</script>
```

Hinweis zu `hud[].max` mit `fmt: 'money'`: Engine 3 formatiert beide Seiten – „🧺 Umsatz 12.400 € / 20.000 €".

Hinweis `gasse` als Hintergrund: existiert in `PROPS` (Mugging), CSS `.cs-bg.gasse` prüfen (`grep -n "cs-bg.gasse"`); fehlt sie, `strasse` verwenden.

`tests/run-selftest.mjs`: `'story-kater'` → `'story-kater', 'story-stash'`.

- [ ] **Step 5: Tests grün** – Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`. Der DOM-Selftest ruft `Stories.validateAll()` beim Story-Start – die Stub-Szenen halten ihn grün.

- [ ] **Step 6: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(story): Die Wäsche – Gerüst: Start, Wochen, Abrechnung, Überfälle, Aktionen, Enden (Szenen als Stubs)"
```

---

### Task 4: Szenen – die Texte

**Files:**
- Modify: Block `story-stash` (`scenes` – Stubs ersetzen; Wahl-Szenen behalten ihre `choices`/`effects` exakt)
- Test: `selftest` (Intro je Vorgängerende, Abrechnungs-Szene je Ausgang, Ende-Szenen enden mit einem Panel ohne Wahl)

**Interfaces:**
- Consumes: `ctx.prev.kater`, `ctx.raw.vars` (`woche`, `lieferung`, `ziel`, `rueckgabe`, `ausgang`, `letztePay`, `kredit`, `zorn`, `letzterUeberfall`, `letzterRaub`, `hinterhaltN`, `igorBiere`, `belege`, `belegeOffen`, `uebergeben`), `ctx.raw.flags` (`igor`, `trocken`, `bahnhof`, `anabiWeiss`, `brandtKennt`), `StoryRules.fmtMoney`.

- [ ] **Step 1: Failing Tests**

```js
T.test('STORY_STASH: Intro je Vorgängerende – Variante + gemeinsamer Schluss mit Anabi', () => {
  for (const prev of ['wirt', 'nuechtern', 'taxi', 'stammgast', 'brownie']) {
    const panels = STORY_STASH.scenes['stash.intro']({ raw: { flags: {}, vars: {} }, prev: { kater: prev } });
    T.ok(panels.length >= 4, `${prev}: mindestens vier Panels`);
    T.eq(panels[panels.length - 1].who, 'anabi', `${prev}: Anabi hat das letzte Wort`);
    T.ok(panels.every((p) => p.text && !p.text.startsWith('stash.')), `${prev}: keine Stubs`);
  }
});
T.test('STORY_STASH: Abrechnungs-Szene je Ausgang, Lieferung je Woche, keine Stubs mehr', () => {
  const ctx = (vars, flags = {}) => ({ raw: { vars: Object.assign({ woche: 1, lieferung: 10000, ziel: 20000, rueckgabe: 11000, letztePay: 11000, kredit: 0, zorn: 0 }, vars), flags }, prev: {}, flags });
  const texts = new Set();
  for (const ausgang of [0, 1, 2, 3]) { const p = STORY_STASH.scenes['stash.abrechnung'](ctx({ ausgang })); T.ok(p.length >= 2, `Ausgang ${ausgang}`); texts.add(p[1].text); }
  T.eq(texts.size, 4, 'vier verschiedene Texte');
  T.ok(STORY_STASH.scenes['stash.abrechnung'](ctx({ ausgang: 0, anabiErfaehrt: 1 }, { bahnhof: true, anabiWeiss: true })).some((p) => p.text.includes('Bahnhof')));
  T.eq(STORY_STASH.scenes['stash.abrechnung'](ctx({ ausgang: 0, anabiErfaehrt: 0 }, { bahnhof: true, anabiWeiss: true })).some((p) => p.text.includes('Bahnhof')), false, 'nur einmal');
  for (const woche of [1, 2, 3, 4]) T.ok(STORY_STASH.scenes['stash.lieferung'](ctx({ woche })).length >= 2, `Woche ${woche}`);
  for (const [id, def] of Object.entries(STORY_STASH.scenes)) {
    const panels = typeof def === 'function' ? def(ctx({ ausgang: 0, letzterUeberfall: 'slots', letzterRaub: 500, hinterhaltN: 2, igorBiere: 0, belege: 1, belegeOffen: 1, uebergeben: 0 })) : def;
    T.ok(panels.length > 0 && panels.every((p) => p.text && !p.text.startsWith('stash.')), `${id}: Text statt Stub`);
    T.ok(panels.every((p) => p.who && (typeof Cutscene !== 'undefined' ? Cutscene.CAST[p.who] : true)), `${id}: Sprecher bekannt`);
  }
  for (const e of STORY_STASH.endings) { const p = STORY_STASH.scenes[e.scene]; const panels = typeof p === 'function' ? p(ctx({})) : p; T.eq(panels[panels.length - 1].choices, undefined, `${e.id}: Ende ohne Wahl`); }
});
```

(`Cutscene` gibt es unter Node nicht – der Sprecher-Check läuft nur im Browser.)

- [ ] **Step 2: Fehlschlag prüfen** – Run: `node tests/run-selftest.mjs` → „keine Stubs".

- [ ] **Step 3: Szenen schreiben** – `scenes` komplett ersetzen:

```js
  scenes: {
    'stash.intro': (ctx) => {
      const prev = (ctx.prev || {}).kater || 'wirt';
      const start = {
        wirt: [
          { bg: 'keller', who: 'du', mood: 'happy', text: 'Dein Name über der Tür. Kreide, aber immerhin. Der Wirt sitzt am Tresen und trinkt sein Freibier – jetzt von dir.' },
          { bg: 'keller', who: 'wirt', mood: 'calm', text: 'Ein Rat vom Vorbesitzer: Wenn einer kommt und „bittet“, guck erst, wer hinter ihm steht.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Schöner Laden. Klein. Unauffällig. Genau richtig für Geld, das nicht auffallen soll. Ich bitte höflich – Igor bittet anders.' },
        ],
        nuechtern: [
          { bg: 'strasse', who: 'du', mood: 'calm', text: 'Neun Monate trocken. Der Keller steht wieder zum Verkauf – der Käufer hat sich in den Kanal gelegt, sagt man. Dir fehlen dreißigtausend.' },
          { bg: 'bank', who: 'krause', mood: 'calm', text: 'Kein Kredit für Spielhallen, tut mir leid. Aber da wäre ein Herr, der Ihnen gern hilft. Er wartet draußen.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Dreißigtausend, kein Zins. Ich will keinen Zins. Ich will einen Freund mit einem Casino. Den hab ich jetzt.' },
        ],
        taxi: [
          { bg: 'strasse', who: 'du', mood: 'angry', text: 'Der Kaufvertrag war unterschrieben. Das Geld war im Taxi. Chantal auch. Der Notar wollte trotzdem sein Geld.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Ich hab den Notar bezahlt. Dreißigtausend. Sieh es als Hochzeitsgeschenk – nachträglich.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Dafür wäscht du. Nicht Wäsche. Geld. Man nennt es so, weil es danach sauber ist.' },
        ],
        stammgast: [
          { bg: 'keller', who: 'du', mood: 'calm', text: 'Der Wirt hat verkauft. An einen Mann mit Sonnenbrille, nachts. Am nächsten Morgen stand dein Name im Grundbuch.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Strohmann. Ein hässliches Wort für einen schönen Beruf. Du hast ein Casino, ich hab einen Namen, der nicht meiner ist.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Fünfzigtausend hat mich der Laden gekostet. Das steht jetzt auf deinem Zettel. Ich bin nicht der Wirt – bei mir gibt es kein Freibier.' },
        ],
        brownie: [
          { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Mein Lieferant will dich kennenlernen. Er hat gehört, du kannst mit Geld umgehen. Ich hab nicht widersprochen.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Der Doc verkauft Brownies. Ich verkaufe, was in den Brownies ist. Und du bekommst dafür einen Keller. Auf Pump. Fünfzigtausend.' },
          { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Du bist schon drin. Tiefer als die anderen. Das ist keine Drohung, das ist eine Bilanz.' },
        ],
      }[prev];
      return [
        ...start,
        { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Jeden Montag bringt jemand eine Tasche. Du spielst das Geld durch die Tische – nicht verstecken, spielen. Sonntag zahlst du zurück, mit zehn Prozent obendrauf. Was du gewinnst, gehört dir.' },
        { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Und der Umsatz muss stimmen. Geld, das nur rumliegt, ist nicht gewaschen. Geld, das gesetzt wurde, schon. Frag nicht, warum. Frag den Finanzbeamten.' },
        { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Dreimal enttäuschst du mich – dann fährt Igor dich an den Kanal. Er ist ein guter Fahrer. Willkommen im Geschäft.' },
      ];
    },
    'stash.tisch': [
      { bg: 'keller', who: 'du', mood: 'calm', text: 'Sieben Uhr morgens. Vier Männer tragen einen Tisch die Treppe runter. Grünes Tuch, Goldrand, ein Schuh für acht Decks.' },
      { bg: 'keller', who: 'stumme', mood: 'calm', text: '…' },
      { bg: 'keller', who: 'du', mood: 'calm', text: 'Der Croupier sagt nichts. Er nickt Richtung Hinterzimmer. Baccarat, fünfhundert Minimum. Anabis Tisch. Deine Umsätze.' },
    ],
    'stash.k2': [
      { bg: 'bahnhof', who: 'du', mood: 'calm', text: 'Seit dem Tisch im Hinterzimmer steht nachts jemand vor deiner Tür. Kapuzen, Bahnhofsviertel, andere Gang. Sie wissen, wem der Keller wirklich gehört.' },
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Bahnhof-Jungs. Kessler ist ihr Boss. Die wollen nicht dein Geld – die wollen Anabis Waschmaschine kaputt machen. Deine.' },
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Kowalski in der Stadt hat eine Pfandleihe. Er verleiht nichts. Er verkauft. Frag nach dem Handschuhfach.' },
    ],
    'stash.k3': [
      { bg: 'bar', who: 'du', mood: 'calm', text: 'Ein Mann im grauen Mantel sitzt seit drei Abenden an deiner Bar und trinkt Wasser. Er spielt nicht. Er guckt.' },
      { bg: 'bar', who: 'brandt', mood: 'calm', text: 'Brandt. Kommissar. Ich sag es gleich, damit Sie nicht raten müssen. Ich will nicht Sie. Ich will den mit der Sonnenbrille.' },
    ],
    'stash.k4': [
      { bg: 'keller', who: 'du', mood: 'calm', text: 'Woche vier. Die Lieferungen werden größer, die Nächte kürzer. Anabi sagt, es läuft gut. Das ist das Schlimmste, was er sagen kann.' },
      { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Freunde reden über alles. Auch über Ablösen. Achtzig, hundert – Zahlen. Wenn du eine hast, komm an den Tisch.' },
    ],
    'stash.lieferung': (ctx) => {
      const v = ctx.raw.vars, fmt = StoryRules.fmtMoney;
      const wer = [
        { who: 'anabi', text: `Die erste Tasche. ${fmt(v.lieferung)}. Bis Sonntag ${fmt(v.ziel)} Umsatz – Roulette, Slots, mein Tisch, egal. Und ${fmt(v.rueckgabe)} liegen dann hier.` },
        { who: 'igor', text: `Anabi schickt Grüße und ${fmt(v.lieferung)}. Ziel diese Woche: ${fmt(v.ziel)} Umsatz, ${fmt(v.rueckgabe)} zurück. Ich schreib es dir auf den Bierdeckel.` },
        { who: 'stumme', text: `Der Stumme stellt die Tasche auf den Tresen. ${fmt(v.lieferung)}. Ein Zettel: „${fmt(v.ziel)} Umsatz. ${fmt(v.rueckgabe)} zurück. Sonntag.“ Er nickt und geht.` },
        { who: 'anabi', text: `Die große Tasche. ${fmt(v.lieferung)}. ${fmt(v.ziel)} Umsatz, ${fmt(v.rueckgabe)} zurück. Danach reden wir über die Zukunft. Deine.` },
      ][Math.min(3, Math.max(0, v.woche - 1))];
      return [
        { bg: 'keller', who: 'du', mood: 'calm', text: 'Nachts klopft es. Zweimal kurz, einmal lang. Die Lieferung.' },
        Object.assign({ bg: 'keller', mood: 'calm' }, wer),
        ...(ctx.raw.flags.bahnhof ? [{ bg: 'keller', who: 'du', mood: 'calm', text: 'Und eine zweite Tasche, kleiner, ohne Zettel. Kessler. Zwei Herren, ein Umsatzziel – und es ist gewachsen.' }] : []),
      ];
    },
    'stash.abrechnung': (ctx) => {
      const v = ctx.raw.vars, f = ctx.raw.flags, fmt = StoryRules.fmtMoney;
      const bahnhof = !!v.anabiErfaehrt; // nur in der Abrechnung, in der Anabi es erfährt
      const ausgang = [
        { who: 'anabi', mood: 'happy', text: `${fmt(v.letztePay)} auf den Tisch, ${fmt(v.ziel)} durch die Tische. Sauber. Ich streich dir was vom Zettel. Und du bekommst den Kassenzettel – heb ihn auf, für deine Buchhaltung.` },
        { who: 'anabi', mood: 'calm', text: `Das Geld ist da. Aber es ist nicht *durch*. Es liegt nur da. Umsatz zu niedrig. Ich zähle mit, weißt du. Einmal.` },
        { who: 'anabi', mood: 'angry', text: `Umsatz stimmt, Geld fehlt. Ich nehm, was da ist – ${fmt(v.letztePay)}. Der Rest kommt auf den Zettel, mit Aufschlag. Ich bin keine Bank. Ich bin schlimmer.` },
        { who: 'anabi', mood: 'angry', text: `Kein Umsatz, kein Geld. Zwei Fehler in einer Woche. Igor, merk dir das Gesicht. Für den Fall, dass wir es noch mal brauchen.` },
      ][v.ausgang || 0];
      return [
        { bg: 'keller', who: 'du', mood: 'calm', text: 'Sonntagabend. Der Keller ist leer, bis auf den Mann, der zählt.' },
        Object.assign({ bg: 'keller' }, ausgang),
        ...(bahnhof ? [{ bg: 'keller', who: 'anabi', mood: 'angry', text: 'Ach – und man erzählt sich, du wäschst auch für den Bahnhof. Zwei Herren. Ich mag keine Gemeinschaftsgüter.' }] : []),
        { bg: 'keller', who: 'igor', mood: 'calm', text: `Zorn: ${v.zorn} von 3. Zettel: ${fmt(v.kredit)}. Ich sag es nur, damit du es weißt.` },
      ];
    },
    'stash.ueberfall': (ctx) => {
      const namen = { roulette: 'der Kessel', slots: 'der Automat', horses: 'das Tableau', russian: 'Igors Revolver', blackjack: 'der Blackjack-Tisch' };
      const was = namen[ctx.raw.vars.letzterUeberfall] || 'ein Spiel';
      return [
        { bg: 'keller', who: 'du', mood: 'shock', text: 'Drei Uhr nachts. Das Telefon. Igor.' },
        { bg: 'keller', who: 'igor', mood: ctx.raw.flags.igor ? 'calm' : 'angry', text: ctx.raw.flags.igor ? `Sie waren da. Ich auch. ${was} hat es trotzdem erwischt – aber nur zur Hälfte. Der Rest war ich.` : `Bahnhof-Jungs. Fenster eingeschlagen, ${was} zertrümmert. Ich war nicht da. Ich bin nie da, wenn ich nicht bezahlt werde.` },
        { bg: 'keller', who: 'du', mood: 'calm', text: 'Morgen steht ein Preis an der Tür. Reparieren kostet. Nicht reparieren kostet mehr: keine Nachtkasse, kein Umsatz.' },
      ];
    },
    'stash.hinterhalt': (ctx) => [
      { bg: 'gasse', who: 'du', mood: 'calm', text: `Heimweg. ${ctx.raw.vars.hinterhaltN === 1 ? 'Einer' : ctx.raw.vars.hinterhaltN === 2 ? 'Zwei' : 'Drei'} von den Bahnhof-Jungs. Kapuzen, Hände in den Taschen. Deine Hand geht ans Handschuhfach.` },
      { bg: 'gasse', who: 'du', mood: 'calm', text: 'Keiner sagt was. So läuft das hier. Wer zuerst zieht, redet danach.' },
    ],
    'stash.hinterhalt.raub': (ctx) => [
      { bg: 'gasse', who: 'du', mood: 'shock', text: `Heimweg. ${ctx.raw.vars.hinterhaltN === 1 ? 'Einer' : 'Ein paar'} von den Bahnhof-Jungs. Du hast Fäuste. Sie haben mehr.` },
      { bg: 'gasse', who: 'raeuber', mood: 'angry', text: 'Grüß den Sonnenbrillen-Mann. Und sag ihm, das hier war umsonst. Das nächste Mal nicht.' },
      { bg: 'gasse', who: 'du', mood: 'calm', text: `${StoryRules.fmtMoney(ctx.raw.vars.letzterRaub)} weg. Ein Auge zu. Morgen wird ein schlechter Tag – das Glück sieht das Veilchen und geht.` },
    ],
    'stash.hinterhalt.lost': (ctx) => [
      { bg: 'gasse', who: 'du', mood: 'shock', text: 'Zu langsam. Der Asphalt ist kalt, das Blut warm, das Portemonnaie leer.' },
      { bg: 'gasse', who: 'raeuber', mood: 'calm', text: `${StoryRules.fmtMoney(ctx.raw.vars.letzterRaub)}. Und die Waffe behältst du – wir haben genug. Grüß den Sonnenbrillen-Mann.` },
    ],
    'stash.tutorial': [
      { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Da läuft ein Junge vom Bahnhof mit meiner Tasche herum. Er glaubt, sie gehört ihm. Erklär ihm das Gegenteil.' },
      { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Hier. Meine Pistole – geliehen, nicht geschenkt. Warte, bis er zieht. Dann sei schneller. Das ist die ganze Kunst.' },
    ],
    'stash.tutorial.won': [
      { bg: 'bahnhof', who: 'anabi', mood: 'happy', text: 'Er liegt, du stehst. Der Bahnhof hat es gesehen. Das ist Ruf. Ruf ist Geld, das man nicht zählen muss.' },
      { bg: 'bahnhof', who: 'anabi', mood: 'calm', text: 'Die Pistole bitte. Du hast eine Pfandleihe in der Stadt, wenn du eine eigene willst. Kowalski. Sag nicht, dass ich dich schicke.' },
    ],
    'stash.tutorial.lost': [
      { bg: 'bahnhof', who: 'anabi', mood: 'calm', text: 'Er ist weg, die Tasche auch, du hast ein Loch in der Jacke. Meine Pistole – danke. Nächstes Mal zieh nicht, bevor er zieht. Oder zieh schneller danach. Eins von beidem.' },
    ],
    'stash.angebot': [
      { bg: 'bahnhof', who: 'du', mood: 'calm', text: 'Kessler wartet an der Unterführung. Allein. Das ist entweder Respekt oder eine Falle. Bei Kessler ist es meistens beides.' },
      { bg: 'bahnhof', who: 'kessler', mood: 'calm', text: 'Du hast meine Jungs hingelegt. Zweimal. Ich könnte sauer sein. Ich bin lieber praktisch: Wasch für uns, dann lassen wir dich in Ruhe.' },
      { bg: 'bahnhof', who: 'kessler', mood: 'calm', text: 'Keine Überfälle mehr, keine Hinterhalte. Dafür wächst dein Umsatzziel – zwei Herren wollen waschen. Und Anabi erfährt es. Irgendwann. Dann brauchst du uns wirklich.',
        choices: [{ label: 'Annehmen', value: 'ja', cls: 'red', effects: [{ flag: 'bahnhof' }] }, { label: 'Ablehnen', value: 'nein', cls: 'ghost', effects: [{ flag: 'bahnhofNein' }] }] },
    ],
    'stash.igor': (ctx) => {
      const n = ctx.raw.vars.igorBiere || 0, getraenk = ctx.raw.flags.trocken ? 'Cola' : 'Bier';
      const text = [
        `Igor sitzt allein. Du stellst ihm ${getraenk === 'Cola' ? 'eine Cola' : 'ein Bier'} hin. Er guckt es an, als wäre es ein Trick. „Anabi bezahlt mich. Der Wirt hat mich gemocht. Das ist nicht dasselbe.“`,
        `Das zweite ${getraenk === 'Cola' ? 'Glas' : 'Bier'}. Igor redet. Über Vito, über den Wirt, über Nächte, in denen er nicht da war, weil ihn keiner gefragt hat. „Anabi fragt nie. Er sagt.“`,
        `Das dritte. Igor stellt das Glas ab, sehr vorsichtig. „Wenn sie kommen, bin ich da. Wenn du redest, hab ich nichts gehört. Und wenn es gegen ihn geht – steh ich nicht dazwischen.“`,
      ][Math.min(2, n)];
      return [{ bg: 'bar', who: 'igor', mood: n >= 2 ? 'happy' : 'calm', text,
        choices: [{ label: 'Prost', value: 'prost', cls: 'green', effects: [{ balance: -100 }, { var: 'igorBiere', add: 1 }, { flag: 'igorHeute' }, ...(n >= GangRules.IGOR_BIERE - 1 ? [{ flag: 'igor' }, { achievement: 'igorsFreund' }] : [])] }] }];
    },
    'stash.brandt': (ctx) => {
      const v = ctx.raw.vars;
      if (!ctx.raw.flags.brandtKennt) return [
        { bg: 'bar', who: 'brandt', mood: 'calm', text: 'Setzen Sie sich. Ich weiß, was hier läuft. Montags Tasche, sonntags Tasche, dazwischen ein Baccarat-Tisch, der niemandem gehört. Ich kann es nur nicht beweisen.' },
        { bg: 'bar', who: 'brandt', mood: 'calm', text: 'Drei Belege und ein Datum. Kassenzettel von seinen Abrechnungen, ein Koffer aus einer Kontrolle – egal. Dann sind Sie Zeuge, kein Täter. Und der Keller? Beweismittel. Man kann nicht alles haben.',
          choices: [{ label: 'Verstanden', value: 'ok', cls: 'ghost', effects: [{ flag: 'brandtKennt' }] }] },
      ];
      return [{ bg: 'bar', who: 'brandt', mood: 'calm', text: `${v.uebergeben} von ${GangRules.BELEGE_NOETIG} Belegen bei mir. ${v.belegeOffen ? `${v.belegeOffen} haben Sie noch in der Tasche.` : 'Nichts Neues in Ihrer Tasche.'} ${v.uebergeben >= GangRules.BELEGE_NOETIG ? 'Ab Tag 26 brauche ich nur noch ein Wort von Ihnen.' : 'Ich trinke Wasser. Ich habe Zeit.'}`,
        choices: [{ label: 'Verstanden', value: 'ok', cls: 'ghost', effects: [] }] }];
    },
    'stash.beleg': [
      { bg: 'bar', who: 'brandt', mood: 'calm', text: 'Unter dem Tresen, bitte. Nicht gucken, ob jemand guckt. Das sieht man.',
        choices: [{ label: 'Übergeben', value: 'geben', cls: 'blue', effects: [{ call: 'belegRisiko' }] }, { label: 'Doch nicht', value: 'nein', cls: 'ghost' }] },
    ],
    'stash.beleg.gesehen': [
      { bg: 'bar', who: 'igor', mood: 'angry', text: 'Ich hab das gesehen. Der Zettel, der Mantel. Ich muss es Anabi sagen – oder er merkt, dass ich es nicht gesagt habe. Tut mir leid. Ehrlich.' },
      { bg: 'keller', who: 'anabi', mood: 'angry', text: 'Ein Zettel an einen Polizisten. Ein Zettel. Ich zähl das als Enttäuschung. Du weißt, wie ich zähle.' },
    ],
    'stash.razzia': [
      { bg: 'bar', who: 'brandt', mood: 'calm', text: 'Drei Belege. Der Rest ist ein Datum. Sagen Sie „heute Nacht“, dann steht in einer Stunde ein Bus vor der Tür – und Sie stehen hinter mir, nicht vor mir.',
        choices: [{ label: 'Heute Nacht', value: 'ja', cls: 'red', effects: [{ flag: 'razzia' }] }, { label: 'Noch nicht', value: 'nein', cls: 'ghost' }] },
    ],
    'stash.abloese': (ctx) => [
      { bg: 'keller', who: 'anabi', mood: 'calm', text: `Ablöse. Hunderttausend für den Keller, dazu dein Zettel: ${StoryRules.fmtMoney(ctx.raw.vars.kredit || 0)}. Macht ${StoryRules.fmtMoney(GangRules.ABLOESE + (ctx.raw.vars.kredit || 0))}. Bar, jetzt, hier. Dann bin ich weg – und der Tisch auch.`,
        choices: [{ label: 'Zahlen', value: 'zahlen', cls: 'red', effects: [{ call: 'abloese' }] }, { label: 'Noch nicht', value: 'nein', cls: 'ghost' }] },
    ],
    'stash.kredit': (ctx) => [
      { bg: 'keller', who: 'stumme', mood: 'calm', text: `Der Stumme schiebt einen Zettel rüber. „${StoryRules.fmtMoney(ctx.raw.vars.kredit || 0)}“. Darunter: „5.000?“ Er hält den Stift.`,
        choices: [{ label: 'Zahlen', value: 'zahlen', cls: 'blue', effects: [{ call: 'kreditZahlen' }] }, { label: 'Doch nicht', value: 'nein', cls: 'ghost' }] },
    ],
    'stash.flucht': [
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Der Wagen ist vollgetankt. Dreißigtausend im Kofferraum reichen für eine Grenze und ein Jahr. Der Keller bleibt hier. Anabi auch. Dein Name im Grundbuch – auch.',
        choices: [{ label: 'Abhauen', value: 'ja', cls: 'red', effects: [{ flag: 'flucht' }] }, { label: 'Bleiben', value: 'nein', cls: 'ghost' }] },
    ],
    'stash.finale': (ctx) => [
      { bg: 'keller', who: 'du', mood: 'calm', text: `Anabi sitzt am Tisch im Hinterzimmer. ${ctx.raw.flags.igor ? 'Igor steht an der Tür und guckt weg.' : 'Igor steht an der Tür und guckt nicht weg.'} Kessler wartet draußen – für danach. Für dich gibt es nur jetzt.`,
        choices: [{ label: 'Los', value: 'los', cls: 'red', effects: [{ call: 'finale' }] }, { label: 'Nicht heute', value: 'nein', cls: 'ghost' }] },
    ],
    'stash.kontrolle': [
      { bg: 'strasse', who: 'brandt', mood: 'calm', text: 'Zwei Strafzettel in einer Nacht – da guckt man in den Kofferraum. Was für ein Koffer. Ich nehm ihn mit. Und ich schreib auf, wo er herkommt. Das ist ein Beleg. Für später.' },
      { bg: 'keller', who: 'anabi', mood: 'angry', text: 'Mein Koffer bei der Polizei. Weil du bei Rot nicht bremsen kannst. Ich zähl das. Du weißt, wie.' },
    ],
    'stash.sylvie.warn': [
      { bg: 'royal', who: 'sylvie', mood: 'calm', text: 'Sie spielen anders als sonst. Größer, schneller, ohne Freude. Ich sehe so etwas. Ich sehe alles. Dies ist ein Casino, keine Waschküche.' },
    ],
    'stash.sylvie.bann': [
      { bg: 'royal', who: 'sylvie', mood: 'angry', text: 'Genug. Das Haus behält sich alles vor – auch die Tür. Der Parkservice bringt Ihnen den Wagen. Kommen Sie nicht wieder. In diesem Leben.' },
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Hausverbot. Der Umsatz muss ab jetzt durch den Keller. Ganz allein.' },
    ],
    'stash.eintr.kiosk': [
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Kiosk am Bahnhof. Der Besitzer schuldet Anabi vierhundert. Er zahlt, bevor du fertig gefragt hast. Du nimmst dir eine Zeitung mit. Er sagt, sie geht aufs Haus.' },
    ],
    'stash.eintr.friseur': [
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Friseur, zweiter Stock. Er will erst nicht, dann doch, dann schneidet er dir umsonst die Haare. Anabi hat seine Liste, du hast eine neue Frisur.' },
    ],
    'stash.ende.kanal': [
      { bg: 'keller', who: 'anabi', mood: 'calm', fx: 'blackout', text: 'Dreimal. Ich hab es dir gesagt. Igor – der Wagen.' },
      { bg: 'hafen', who: 'igor', mood: 'calm', text: 'Er fährt langsam. Anabi sitzt hinten und sagt nichts. Der Kanal ist ruhig um diese Zeit.' },
      { bg: 'hafen', who: 'du', mood: 'calm', text: 'Der Keller bekommt einen neuen Strohmann. Er wird auch nicht rechnen können.' },
    ],
    'stash.ende.krieg': [
      { bg: 'keller', who: 'du', mood: 'calm', fx: 'flash', text: 'Anabi liegt neben seinem Tisch. Die Sonnenbrille ist heil geblieben. Sonst nichts.' },
      { bg: 'keller', who: 'kessler', mood: 'happy', text: 'Schnellste Hand der Stadt. Der Keller gehört dir. Und uns. Aber wir sind bessere Partner – wir klopfen wenigstens.' },
      { bg: 'keller', who: 'du', mood: 'calm', text: 'Neuer Herr, alte Tasche. Die Wäsche läuft weiter. Nur die Hand am Kofferraum ist jetzt deine.' },
    ],
    'stash.ende.kommissar': (ctx) => [
      { bg: 'keller', who: 'du', mood: 'calm', fx: 'flash', text: 'Blaulicht die Treppe runter. Anabi in Handschellen, der Stumme sagt zum ersten Mal ein Wort, und es ist kein schönes.' },
      ...(ctx.raw.flags.igor ? [{ bg: 'keller', who: 'igor', mood: 'calm', text: 'Ich hab gewusst, dass du es bist. Ich hab nichts gesagt.' }] : []),
      { bg: 'keller', who: 'brandt', mood: 'calm', text: 'Der Keller ist Beweismittel. Sie sind frei. Nur nicht hier. Ein Taxi wartet – ich hab es bezahlt. Das erste Mal, dass die Stadt Ihnen etwas schuldet.' },
    ],
    'stash.ende.abloese': [
      { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Er zählt nach. Zweimal. Dann nickt er dem Stummen zu, und vier Männer tragen den Tisch die Treppe hoch.' },
      { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Sauber. Du bist der Erste, der sich freigekauft hat. Ich erzähl das niemandem. Es wäre schlecht fürs Geschäft.' },
      { bg: 'keller', who: 'du', mood: 'happy', text: 'Der Keller gehört dir. Wirklich. Der Wirt trinkt sein Freibier und sagt, er hätte es gewusst.' },
    ],
    'stash.ende.flucht': [
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Nachts über die Grenze. Im Rückspiegel ein Schein über der Stadt – der Keller brennt. Nicht deine Schuld, sagt niemand.' },
      { bg: 'hafen-morgen', who: 'du', mood: 'calm', text: 'Neuer Name, altes Spiel. Irgendwo gibt es immer einen Keller.' },
    ],
    'stash.ende.strohmann': [
      { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Woche fünf. Die Tasche ist größer. Fünfzigtausend. Du weißt, wie es geht.' },
      { bg: 'keller', who: 'du', mood: 'calm', text: 'Dein Name steht im Grundbuch. Seiner steht auf dir. Der Stumme nickt. Die Wäsche läuft.' },
    ],
  },
```

- [ ] **Step 4: Tests grün** – Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Die Wäsche – alle Szenen"
```

---

### Task 5: Playtest-Szenario, Screenshots, README

**Files:**
- Modify: `tests/playtest-story.py` (`scenario_stash`, in `main()` registrieren; Stadt-Check in Story 3: 5 Schaufenster)
- Create: `docs/superpowers/screenshots/stash-intro.png`, `stash-hub-broken.png`, `stash-abrechnung.png`
- Modify: `README.md`

**Interfaces:**
- Consumes: Dev-Params `?fresh&story=stash&prev=wirt`, `?day=`, `?weapon=`, `?ending=`; CDP-Helfer der Datei (`cdp.navigate/eval/click/wait_for/advance_cutscene/inject_helpers`, `record`).

- [ ] **Step 1: Szenario schreiben** (Muster: `scenario_kater`)

```python
async def scenario_stash(cdp):
    """Story 3 „Die Wäsche": Sperre nach Bett, Intro je Vorgängerende, Lieferung, Umsatz per Baccarat,
    Abrechnung ok, Überfall + Reparatur, Waffe, Schießerei, Brandt/Belege, Razzia-Ende; zweiter Lauf Kanal."""
    # Sperre: Kater endete im Bett
    await cdp.navigate(URL_BASE + "?fresh&mode=free")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)
    await cdp.eval("State.meta.storyRuns = { schuld: { lastPlayed: 1, endings: ['ehrlich'], last: 'ehrlich' }, kater: { lastPlayed: 2, endings: ['bett'], last: 'bett' } }; State.saveMeta();", await_promise=False)
    locked = await cdp.eval("Stories.locked().map(l => l.id + ':' + l.text)", await_promise=False)
    record("stash: nach Bett gesperrt mit eigenem Text", any(l.startswith("stash:") and "Bett" in l for l in locked), str(locked))
    # Start nach Wirt
    await cdp.navigate(URL_BASE + "?fresh&story=stash&prev=wirt")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=20)
    await cdp.wait_for("State.mode === 'story' && Story.s && Story.s.day === 1 && UI.current && !UI.busy", timeout=5.0)
    st = await cdp.eval("({ kredit: Story.s.vars.kredit, car: State.s.car, hz: !!Story.s.enabled.hinterzimmer, doorHidden: document.querySelector('[data-screen=\"hinterzimmer\"]') ? document.querySelector('[data-screen=\"hinterzimmer\"]').hidden : null })", await_promise=False)
    record("stash: Tag 1 – Kredit 0, Mercedes, Hinterzimmer sichtbar", st["kredit"] == 0 and st["car"] == "mercC" and st["hz"] is True, str(st))
    # Nacht 1: Lieferung
    await cdp.eval("Story.evening()")
    await asyncio.sleep(0.4)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    await cdp.advance_cutscene(max_steps=10)
    await cdp.wait_for("Story.s.day === 2 && !Story.sleeping && !__pt.cutsceneActive()", timeout=8.0)
    await cdp.advance_cutscene(max_steps=10)  # Tisch-Szene am Morgen
    v = await cdp.eval("({ balance: State.s.balance, woche: Story.s.vars.woche, ziel: Story.s.vars.ziel, hzOpen: Story.s.unlocked.doors.includes('hinterzimmer') })", await_promise=False)
    record("stash: Lieferung Woche 1 – +10.000, Ziel 20.000, Hinterzimmer offen", v["balance"] == 16250 and v["woche"] == 1 and v["ziel"] == 20000 and v["hzOpen"], str(v))
    # Umsatz per Baccarat (Hand gestubbt: Push, damit das Geld bleibt)
    await cdp.eval("Story.evening()")
    await cdp.eval("UI.show('hinterzimmer')")
    await cdp.wait_for("UI.current && UI.current.id === 'hinterzimmer' && !UI.busy", timeout=3.0)
    umsatz = await cdp.eval("""(async function(){
      BaccaratRules.deal = function(){ return { player: [{val:'5',suit:'♠'},{val:'K',suit:'♥'}], banker: [{val:'2',suit:'♦'},{val:'3',suit:'♣'}], p: 5, b: 5, natural: false, winner: 'tie' }; };
      for (let i = 0; i < 2; i++) { document.querySelector('#bacBet').value = '10000'; Baccarat.place('player'); await Baccarat.deal(); }
      return { umsatz: Story.s.vars.umsatz, hz: Story.s.vars.umsatzHinterzimmer, balance: State.s.balance };
    })()""")
    record("stash: zwei Push-Hände à 10.000 → Umsatz 20.000, Geld bleibt", umsatz["umsatz"] == 20000 and umsatz["hz"] == 20000 and umsatz["balance"] == 16250, str(umsatz))
    # Tag 7 Abrechnung ok
    await cdp.eval("Story.s.day = 7; Story.s.phase = 'evening'; State.save(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    await cdp.advance_cutscene(max_steps=12)
    await cdp.wait_for("Story.s.day === 8 && !Story.sleeping", timeout=8.0)
    await cdp.advance_cutscene(max_steps=12)  # Kapitel 2 Intro, Lieferung folgt nachts
    a = await cdp.eval("({ balance: State.s.balance, zorn: Story.s.vars.zorn, belege: Story.s.vars.belege, ok: Story.s.vars.abrechnungenOk, pf: !!Story.s.enabled.pfandleihe })", await_promise=False)
    record("stash: Abrechnung ok – 11.000 weg, Zorn 0, Beleg 1, Pfandleihe offen", a["balance"] == 16250 - 11000 + 1250 and a["zorn"] == 0 and a["belege"] == 1 and a["ok"] == 1 and a["pf"], str(a))
    # Überfall erzwingen: Tür kaputt → 🔧 in der Lobby → reparieren
    await cdp.eval("Story.s.broken = { slots: 4000 }; State.save(); UI.show('hub');", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'hub' && !UI.busy", timeout=3.0)
    b = await cdp.eval("({ btn: !!document.querySelector('[data-screen=\"slots\"] .repair'), locked: Story.isLocked('slots'), reason: Story.lockReason('slots') })", await_promise=False)
    record("stash: kaputte Slots – 🔧-Knopf, gesperrt, Grund Zertrümmert", b["btn"] and b["locked"] and b["reason"] == "Zertrümmert", str(b))
    await cdp.eval("Story.repair('slots')")
    await asyncio.sleep(0.6)
    r = await cdp.eval("({ broken: Story.s.broken, rep: Story.s.vars.repariert_slots, locked: Story.isLocked('slots') })", await_promise=False)
    record("stash: Reparatur – Eintrag weg, Zähler 1, Tür offen", r["broken"] == {} and r["rep"] == 1 and not r["locked"], str(r))
    # Waffe kaufen
    await cdp.eval("State.s.balance = 40000; State.save(); UI.show('stadt');", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=3.0)
    n = await cdp.eval("document.querySelectorAll('#strasse .storefront').length", await_promise=False)
    record("stash: Stadt zeigt fünf Schaufenster (mit Pfandleihe)", n == 5, "n=%s" % n)
    await cdp.eval("Stadt.open('pfandleihe'); Stadt.buyWeapon(1)", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
    await cdp.advance_cutscene(max_steps=6)
    w = await cdp.eval("({ weapon: State.s.weapon, balance: State.s.balance })", await_promise=False)
    record("stash: Makarov gekauft", w["weapon"] == 1 and w["balance"] == 25000, str(w))
    # Schießerei (Hinterhalt) erzwingen: Nacht 9 mit gestubbtem rng über GangRules
    await cdp.eval("GangRules.raid = () => null; GangRules.ambushChance = () => 1; GangRules.ambushCount = () => 1; GangRules.drawWait = () => 40; Story.s.day = 9; Story.s.phase = 'evening'; State.save(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    await cdp.advance_cutscene(max_steps=6)
    await cdp.wait_for("UI.current && UI.current.id === 'shootout' && Shootout.running", timeout=5.0)
    await cdp.eval("Shootout.ready()", await_promise=False)
    await cdp.wait_for("Shootout.phase === 'draw'", timeout=3.0)
    await cdp.eval("Shootout.tap()", await_promise=False)
    await asyncio.sleep(0.3)
    won = await cdp.eval("({ running: Shootout.running, won: Shootout.results[0] && Shootout.results[0].won })", await_promise=False)
    record("stash: Hinterhalt – Duell gewonnen", won["running"] is False and won["won"] is True, str(won))
    await cdp.click("#btnDuelDone")
    await cdp.wait_for("Story.s.day === 10 && !Story.sleeping", timeout=8.0)
    await cdp.advance_cutscene(max_steps=8)
    ruf = await cdp.eval("Story.s.vars.ruf", await_promise=False)
    record("stash: Ruf +1 nach gewonnenem Hinterhalt", ruf == 1, "ruf=%s" % ruf)
    # Brandt, Belege, Razzia → Ende Kommissar
    await cdp.eval("Story.s.day = 26; Story.s.phase = 'evening'; Story.s.vars.belege = 3; Story.s.vars.belegeOffen = 3; Story.s.flags.igor = true; State.save(); UI.renderSide(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.action('brandt')", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
    await cdp.advance_cutscene(max_steps=6)
    for _ in range(3):
        await cdp.eval("Story.action('beleg')", await_promise=False)
        await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
        await cdp.advance_cutscene(max_steps=4)
        await asyncio.sleep(0.3)
    ub = await cdp.eval("({ u: Story.s.vars.uebergeben, zorn: Story.s.vars.zorn, razzia: StoryRules.actionsFor(Story.story, State.s, 'bar').some(a => a.id === 'razzia') })", await_promise=False)
    record("stash: drei Belege übergeben ohne Risiko (Igor), Razzia-Knopf da", ub["u"] == 3 and ub["zorn"] == 0 and ub["razzia"], str(ub))
    await cdp.eval("Story.action('razzia')", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
    await cdp.advance_cutscene(max_steps=12)
    await asyncio.sleep(0.5)
    ende = await cdp.eval("(State.meta.storyRuns.stash || {}).last", await_promise=False)
    record("stash: Ende Der Kommissar", ende == "kommissar", "last=%s" % ende)
    await cdp.advance_cutscene(max_steps=10)  # Insider/„Und jetzt?“ → Titel
    # Zweiter Lauf: Zorn 3 → Kanal sofort, nächste Story sauber
    await cdp.navigate(URL_BASE + "?fresh&story=stash&prev=stammgast&day=7")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)
    await cdp.wait_for("State.mode === 'story' && Story.s && Story.s.day === 7", timeout=5.0)
    await cdp.eval("Story.s.vars.zorn = 2; Story.s.vars.ziel = 20000; Story.s.vars.rueckgabe = 11000; Story.s.vars.woche = 1; State.s.balance = 0; Story.s.phase = 'evening'; State.save(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    await cdp.advance_cutscene(max_steps=14)
    await asyncio.sleep(0.5)
    k = await cdp.eval("({ last: (State.meta.storyRuns.stash || {}).last, ended: Story.s ? Story.s.ended : null })", await_promise=False)
    record("stash: Abrechnung ohne Geld bei Zorn 2 → Kanal sofort", k["last"] == "kanal", str(k))
```

In `main()` das Szenario nach `scenario_kater` aufrufen. Zahlen im Szenario (16.250 = 5.000 + 10.000 + 1.250 Nachtkasse Tag 2) beim ersten Lauf gegen die Konsole prüfen und korrigieren, falls die Reihenfolge Morgen-Event/Lieferung anders ausfällt – die Spec-Regel gilt, nicht die Zahl im Skript.

- [ ] **Step 2: Playtest** – Run: `python3 tests/playtest-story.py` (allein) → alle Checks grün, `ERRORS 0`.

- [ ] **Step 3: Screenshots**

```bash
bash tests/screenshot.sh docs/superpowers/screenshots/stash-intro.png "?fresh&story=stash&prev=wirt"
bash tests/screenshot.sh docs/superpowers/screenshots/stash-shootout.png "?fresh&mode=free&screen=shootout&foe=kessler&weapon=1"
```

Für `stash-hub-broken.png`: `?fresh&story=stash&prev=wirt&day=9` laden, in der Konsole `Story.s.broken = { slots: 4000, roulette: 6000 }; UI.show('hub')` – oder das Szenario-Skript den Screenshot machen lassen (`cdp.screenshot`), wie bei `kater-*.png`.

- [ ] **Step 4: README**

Abschnitt „Story-Modus": Story 3 „Die Wäsche" (Voraussetzung: Kater beendet, nicht im Bett), Ablauf in fünf Sätzen (Lieferung → Umsatz → Abrechnung, Zorn, Überfälle/Reparatur, Bahnhof-Jungs, Brandt), die sechs Enden als Liste, Dev-Parameter `?fresh&story=stash&prev=wirt|nuechtern|taxi|stammgast|brownie`, `?day=`, `?weapon=`, `?ending=abloese`. Zähler (Szenen/Figuren) aktualisieren: `grep -c "^    'stash\." keller37.html` bzw. `Cutscene.CAST`-Länge.

- [ ] **Step 5: Commit**

```bash
git add tests/playtest-story.py docs/superpowers/screenshots/stash-*.png README.md
git commit -m "test(story): Playtest Die Wäsche; Screenshots; README Story 3"
```

---

## Self-Review

- **Spec-Abdeckung:** §2 Voraussetzung/Vorgängerende (T3 Events `startKredit*`, `startTrocken`, `startBrownie`, `lockText`), §3 Start/HUD/Kapitel (T3), §4 Wäsche-Woche (T2 `week/abrechnung`, T3 `fns.lieferung/abrechnung`, Reihenfolge Abrechnung zuerst, Zorn-Kappung, Kanal sofort), §5 Nachtkasse/Überfall/Reparatur (T2, T3 `nachtkasse/ueberfall`, 🔧 aus Engine 3, Hausmeister), §6 Waffe/Hinterhalt/Tutorial/Angebot/Finale (T3 `hinterhalt/tutorial/finale`, Events, Aktion `anabiStellen` mit `weapon`-Bedingung T1), §7 Brandt/Belege/Razzia/Igor/Sylvie (T3), §8 Baccarat-Trophäe `stummeNickt` (T3), §9 Eintreiber-Override + Kurier-Kontrolle (T3), §11 Enden/Trophäen (T3, T4), §12 Dev-Params/Tests (T3 Node, T5 Playtest).
- **Platzhalter:** keine – Szenen sind in T3 Stubs mit klarer Ersetzung in T4 (Test erzwingt es).
- **Typen:** `fns.*(s, rng)` → `{ scene?, toast?, force?, fight?, achievement? }`; `GangRules.abrechnung` → `{ ausgang, pay, kreditDelta, zornDelta, belegDelta }`; Vars-Namen konsistent (`umsatz`, `umsatzRoyal`, `umsatzHinterzimmer`, `ziel`, `rueckgabe`, `lieferung`, `zorn`, `kredit`, `belege`, `belegeOffen`, `uebergeben`, `ruf`, `igorBiere`, `eintreiberWoche`, `abrechnungenOk`, `ausgang`, `letztePay`, `anabiErfaehrt`, `letzterUeberfall`, `letzterRaub`, `hinterhaltN`, `repariert_<door>`); Flags (`trocken`, `bahnhof`, `bahnhofNein`, `anabiWeiss`, `igor`, `igorHeute`, `brandtKennt`, `razzia`, `frei`, `flucht`, `anabiTot`, `kanal`, `royalWarn`, `royalBann`, `ueberfallHeute`, `blauesAuge`, `kontrolle`, `fightWon`/`fightLost`/`fight_<kind>`, `waschmaschine`, `stummeNickt`); Szenen-IDs wie in `events`/`actions`/`endings`.
- **Bekannte Grenzen (bewusst):** Das freie Mugging-System (abendlicher Überfall aus dem Basisspiel) läuft in Story 3 weiter wie in Story 1/2 – zusätzlicher Druck, keine eigene Logik. Bier bleibt in Story 3 das normale Glücks-Bier (kein Pegel).
