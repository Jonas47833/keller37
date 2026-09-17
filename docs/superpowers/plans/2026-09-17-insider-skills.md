# Insider & Skills – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** XP durch Spielen, bis zu drei Skills mit Licht- und Schattenseite pro Spielstand, und dauerhafte Insider-Upgrades (eins pro abgeschlossenem Story-Teil) – alles über ein zentrales Modifikator-Register, das die bestehenden Regeln lesen.

**Architecture:** Neuer reiner Block `perk-rules` (Kataloge, XP-Level, `Rules.mods(s, meta)`); bestehende reine Regeln bekommen einen optionalen `mods`-Parameter (Default neutral, alte Tests bleiben gültig). Ein Modul `Perks` vergibt XP über Bus-Events, verwaltet Skill-Wahl/Umskillen, bietet beim Story-Ende die Insider-Wahl an und liefert `Perks.mods()` = `Rules.mods(State.s, State.meta)` für alle Aufrufstellen. Die Spiele lesen `Perks.mods()` und zeigen die Insider-Effekte (ausgegraute Zahlen, lahmes Pferd, Deck-Hitze, Festhalten).

**Tech Stack:** Vanilla HTML/CSS/JS in `keller37.html` (Ein-Datei-Vorgabe), Node-Selftest, Browser-Selftest, CDP-Playtest.

**Spec:** `docs/superpowers/specs/2026-09-17-insider-skills-design.md`

## Global Constraints

- Alles bleibt in `keller37.html`; neue Blöcke: `perk-rules` (direkt nach `gear-rules`), `perks` (direkt nach `mugging`, vor `story-rules`). `tests/run-selftest.mjs` lädt `perk-rules` nach `gear-rules`.
- `State.VERSION` bleibt 1. Neue Felder: Spielstand `xp: 0, skills: [], skillRespecs: 0, insiderExcluded: [], mechRespins: 0`; Meta `insider: [], insiderClaimed: {}` (`insiderClaimed` wird wie `storyRuns` als Objekt gemerged).
- Zahlen exakt wie Spec §2.3–2.5: `XP_LEVELS = [0, 25, 60, 110, 180, 270]`, Punkte bei Level 2/4/6, max. 3 Skills, Umskillen 2.000 €, `INSIDER_CAP = 250`, XP-Quellen +1 Spin / +2 Sieg / +5 Job / +5 Story-Tag / +10 Trophäe, Skill- und Insider-Kataloge mit genau den `mods`-Werten der Spec.
- `Rules.mods(s, meta)` liefert immer alle Schlüssel aus Spec §2.6 mit Neutralwerten; reine Regeln bekommen `mods` als letzten optionalen Parameter mit Default `Rules.NEUTRAL_MODS`; kein Spiel liest `s.skills`/`meta.insider` direkt, nur über `Perks.mods()` (Ausnahme: Anzeige im Skill-Screen/Titel).
- Deckel: `stallbursche`, `croupierauge`, `kartenzaehler`, `mechaniker` wirken nur bei Einsatz ≤ `INSIDER_CAP`; Hinweis im Screen, wenn der Einsatz darüber liegt.
- Deutsch mit „…"-Anführungszeichen (schließend gerades `"` wie im Rest der Datei).
- Vor jedem Commit: `node tests/run-selftest.mjs` und `tests/dom-selftest.sh` grün. Commits enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Arbeit nur im Worktree `.worktrees/insider-skills` (Branch `feature/insider-skills`); Merge/Push nur nach Freigabe.

---

## Orientierung im Code (für alle Tasks)

- Helfer (Block `util`): `qs`, `qsa`, `h(tag, attrs, ...children)`, `wait`, `pick`, `rand`.
- `Rules` (Block `rules`): `BEER_LUCK`, `MAX_BEERS`, `MAFIA_SPINS`, `luck(s)`, `effectiveLuck`, `canBeer(s)`, `bankInterest(debt, s)`, `bankLoanReason(s, amt)`, `mafiaBill(debt)`, `rouletteRoll(rng)`, `roulettePayout(type, chosen, rolled, bet)`, `rouletteSettle(bets, rolled)`, `slotMultiplier(a, b, c)`, `horseStep(isSelected, luck, rng)`, `horseDelta(won, bet)`, `newDeck`, `handSum`, `bjOutcome`, `bjDelta(outcome, bet)`, `investmentResolve(inv, rng)`, `postmanTier(streak, s)`, `mugChance(s, where)`, `mugWallet(rng)`, `fightChance(strength)`. `Rules.gear(s)` (Block `gear-rules`) liefert `bankRate`/`bankLimit` u. a.
- `State.s` / `State.meta`, `State.save()`, `State.saveMeta()`, `State.fresh()`, `State.freshMeta()`, `State._read` (Merge alter Spielstände).
- `Game` (Block `core`): `readBet`, `bindBet`, `beginSpin`, `settle`, `applyDelta`, `afterSpin` (emittiert `spin:after`), Bus `win`.
- `Achievements.unlock(id)` emittiert `achievement:unlock`; `Jobs` emittiert `job:done`; `StoryRules.advanceDay(s)` (rein) – der Story-Tag-XP kommt an der Aufrufstelle in `Story.night()`.
- `Story.finish(end)` (Block `story-engine`): Statistik-Panel, dann Wahl „Nächste Story / Zum Titel".
- Screens: `UI.register(id, { template, mount, unmount })`, Templates vor `<!-- /TEMPLATES -->`, Seitenleiste in `UI.renderSide` (Block `ui`), Kopfzeile in `UI.mountShell`/`renderWallet`, `Actions.<name>`.
- Cutscene: `Cutscene.define(id, panels | (ctx) => panels)`, `Cutscene.play(id, ctx)` → Wert der Wahl, `CAST`, `PROPS`.
- Selftests: Block `selftest`, `T.test/T.eq/T.ok`, `base(o)`, `seq(...)`, `near(a, b)`; neue Fälle vor `/* --- SELFTEST CASES END --- */`.
- Playtest: `tests/playtest-story.py` (`cdp.navigate/eval/click/screenshot/advance_cutscene`, `record`), Referenzbilder `docs/superpowers/screenshots/`. Chrome-Port 9335 kann von einer parallelen Session belegt sein – dann warten, nicht killen.

---

### Task 1: Block `perk-rules` – Kataloge, XP-Level, `mods`, Ziehungen; State-Felder

**Files:**
- Modify: `keller37.html` – neuer Block nach `</script>` von `gear-rules`; `State.fresh()`, `State.freshMeta()`, `State._read` (Block `state`); Selftests
- Modify: `tests/run-selftest.mjs` – Blockliste

**Interfaces:**
- Produces: `Rules.XP_LEVELS`, `Rules.INSIDER_CAP`, `Rules.MAX_SKILLS = 3`, `Rules.RESPEC_PRICE = 2000`, `Rules.XP_GAIN = { spin: 1, win: 2, job: 5, day: 5, achievement: 10 }`, `Rules.SKILLS` (Array), `Rules.INSIDER` (Array), `Rules.NEUTRAL_MODS`, `Rules.xpLevel(xp) → { level, next, points }` (`next` = XP-Schwelle des nächsten Levels oder `null` ab Level 6), `Rules.skillPointsFree(s)`, `Rules.canPickSkill(s, id) → { ok, reason?: 'unknown'|'active'|'full'|'points'|'conflict' }`, `Rules.mods(s, meta) → Objekt mit allen NEUTRAL_MODS-Schlüsseln`, `Rules.insiderDraw(meta, rng) → string[]` (≤ 3), `Rules.effectiveInsider(value, bet)` (Zahl: proportional; Boolean: nur bei `bet ≤ CAP`), `Rules.deckHot(deck) → boolean`, `Rules.pickExcluded(rng) → number[]` (12 aus 1–36), `Rules.pickLoser(selectedId, rng) → id ≠ selected`.

- [ ] **Step 1: Runner-Liste**

`tests/run-selftest.mjs`: `['rules', 'gear-rules', 'util', …]` → `['rules', 'gear-rules', 'perk-rules', 'util', …]`.

- [ ] **Step 2: Fehlschlagende Tests**

Vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- Perks: XP, Skills, Insider ---- */
T.test('xpLevel: Schwellen und Punkte', () => {
  T.eq(Rules.XP_LEVELS, [0, 25, 60, 110, 180, 270]);
  T.eq(Rules.xpLevel(0), { level: 1, next: 25, points: 0 });
  T.eq(Rules.xpLevel(24), { level: 1, next: 25, points: 0 });
  T.eq(Rules.xpLevel(25), { level: 2, next: 60, points: 1 });
  T.eq(Rules.xpLevel(110), { level: 4, next: 180, points: 2 });
  T.eq(Rules.xpLevel(270), { level: 6, next: null, points: 3 });
  T.eq(Rules.xpLevel(9999), { level: 6, next: null, points: 3 });
});
T.test('Kataloge: Skills mit Licht/Schatten, mods-Schlüssel bekannt', () => {
  T.eq(Rules.SKILLS.length, 8); T.eq(Rules.INSIDER.length, 7);
  for (const sk of Rules.SKILLS) { T.ok(sk.light && sk.shadow, sk.id); for (const k of Object.keys(sk.mods)) T.ok(k in Rules.NEUTRAL_MODS, `${sk.id}.${k}`); }
  for (const ins of Rules.INSIDER) { T.ok(ins.text && typeof ins.capped === 'boolean', ins.id); for (const k of Object.keys(ins.mods)) T.ok(k in Rules.NEUTRAL_MODS, `${ins.id}.${k}`); }
  T.eq(Rules.INSIDER_CAP, 250); T.eq(Rules.MAX_SKILLS, 3); T.eq(Rules.RESPEC_PRICE, 2000);
  T.eq(Rules.XP_GAIN, { spin: 1, win: 2, job: 5, day: 5, achievement: 10 });
});
T.test('mods: neutral ohne Skills/Insider', () => {
  T.eq(Rules.mods(base(), { insider: [] }), Rules.NEUTRAL_MODS);
  T.eq(Rules.mods(base()), Rules.NEUTRAL_MODS, 'ohne meta');
});
T.test('mods: Skills und Insider stapeln', () => {
  const m = Rules.mods(base({ skills: ['pokerface', 'zockerhaende', 'verhandler'] }), { insider: ['bankinsider', 'vitosneffe'] });
  T.eq(m.bjNatural, 1.5); T.eq(m.bjPushBonus, 0.1); T.eq(m.beerLuckMult, 0);
  T.eq(m.slotPairMult, 1.5);
  near(m.bankRateAdd, 0.02 - 0.02 - 0.03, 'Zinsen addieren');
  T.eq(m.mafiaSpins, 8, 'Maximum von 7 und 8'); T.eq(m.mafiaMult, 2);
  T.eq(m.bankLimitAdd, 2000); near(m.investRateMult, 0.9); near(m.mugChanceMult, 0.5);
  T.eq(m.postLetters, 15); T.eq(m.horsePayout, 3);
  const k = Rules.mods(base({ skills: ['pferdefluesterer', 'strassenkoeter', 'eisenmagen'] }), { insider: ['postmeister', 'vitosneffe'] });
  T.eq(k.horsePayout, 3.3); near(k.mugChanceMult, 1.5 * 0.5); T.eq(k.fightAdd, 0.15); T.eq(k.walletMult, 2); T.eq(k.bankLimitAdd, -1000);
  T.eq(k.maxBeers, 4); T.eq(k.brownieSpins, 2); T.eq(k.postTimeAdd, -1); T.eq(k.postPayAdd, 5); T.eq(k.postLetters, 20);
  T.eq(Rules.mods(base({ skills: ['unbekannt'] })), Rules.NEUTRAL_MODS, 'unbekannte IDs ignoriert');
});
T.test('canPickSkill / skillPointsFree', () => {
  T.eq(Rules.skillPointsFree(base({ xp: 0, skills: [] })), 0);
  T.eq(Rules.skillPointsFree(base({ xp: 60, skills: [] })), 1);
  T.eq(Rules.skillPointsFree(base({ xp: 110, skills: ['pokerface'] })), 1);
  T.eq(Rules.canPickSkill(base({ xp: 0, skills: [] }), 'pokerface').reason, 'points');
  T.eq(Rules.canPickSkill(base({ xp: 25, skills: [] }), 'pokerface'), { ok: true });
  T.eq(Rules.canPickSkill(base({ xp: 25, skills: [] }), 'gibtsnicht').reason, 'unknown');
  T.eq(Rules.canPickSkill(base({ xp: 110, skills: ['pokerface'] }), 'pokerface').reason, 'active');
  T.eq(Rules.canPickSkill(base({ xp: 110, skills: ['zockerhaende'] }), 'brieftraeger').reason, 'conflict');
  T.eq(Rules.canPickSkill(base({ xp: 999, skills: ['pokerface', 'kalterkopf', 'verhandler'] }), 'eisenmagen').reason, 'full');
});
T.test('insiderDraw: 3 ungezogene, weniger wenn Pool kleiner', () => {
  const all = Rules.INSIDER.map((i) => i.id);
  const d = Rules.insiderDraw({ insider: [] }, seq(0, 0, 0));
  T.eq(d.length, 3); T.ok(new Set(d).size === 3, 'verschieden'); d.forEach((id) => T.ok(all.includes(id)));
  const d2 = Rules.insiderDraw({ insider: all.slice(0, 5) }, seq(0, 0));
  T.eq(d2.length, 2); d2.forEach((id) => T.ok(!all.slice(0, 5).includes(id), 'nie gewählte'));
  T.eq(Rules.insiderDraw({ insider: all }, seq(0)), []);
});
T.test('effectiveInsider: Deckel 250', () => {
  T.eq(Rules.effectiveInsider(1.2, 250), 1.2);
  near(Rules.effectiveInsider(1.2, 500), 1.1, 'Bonusanteil halbiert');
  T.eq(Rules.effectiveInsider(true, 250), true); T.eq(Rules.effectiveInsider(true, 251), false);
  T.eq(Rules.effectiveInsider(false, 10), false);
});
T.test('deckHot / pickExcluded / pickLoser', () => {
  const hot = [...Array(20)].map(() => ({ val: '10' })).concat([{ val: '3' }]);
  T.eq(Rules.deckHot(hot), true);
  const cold = [...Array(20)].map(() => ({ val: '3' })).concat([{ val: 'A' }]);
  T.eq(Rules.deckHot(cold), false);
  const ex = Rules.pickExcluded(Math.random);
  T.eq(ex.length, 12); T.eq(new Set(ex).size, 12); ex.forEach((n) => T.ok(n >= 1 && n <= 36));
  for (let i = 0; i < 50; i++) T.ok(Rules.pickLoser(2, Math.random) !== 2);
  T.ok([1, 3, 4].includes(Rules.pickLoser(2, seq(0))));
});
T.test('State.fresh/freshMeta: Perk-Felder', () => {
  const f = State.fresh(); T.eq([f.xp, f.skills, f.skillRespecs, f.insiderExcluded, f.mechRespins], [0, [], 0, [], 0]);
  const m = State.freshMeta(); T.eq([m.insider, m.insiderClaimed], [[], {}]);
});
```

- [ ] **Step 3: Tests laufen lassen – fehlschlagen**

Run: `node tests/run-selftest.mjs` → Abbruch `Script-Block "perk-rules" fehlt`.

- [ ] **Step 4: State-Felder**

`State.fresh()`: nach `car: null, shoes: null, strength: 0, mugCooldown: 0,` ergänzen: `xp: 0, skills: [], skillRespecs: 0, insiderExcluded: [], mechRespins: 0,`.
`State.freshMeta()`: `{ v: 1, achievements: [], muted: false, gameOvers: 0, storyRuns: {}, insider: [], insiderClaimed: {} }`.
`State._read`: nach der `storyRuns`-Merge-Zeile: `if (f.insiderClaimed) merged.insiderClaimed = Object.assign({}, p.insiderClaimed || {});`.

- [ ] **Step 5: Block `perk-rules`**

Nach `</script>` des Blocks `gear-rules`:

```html
<script id="perk-rules">
/* ================= PERKS – XP, Skills (Licht/Schatten), Insider-Upgrades (rein, kein DOM, kein State) ================= */
Object.assign(Rules, {
  XP_LEVELS: [0, 25, 60, 110, 180, 270],
  XP_GAIN: { spin: 1, win: 2, job: 5, day: 5, achievement: 10 },
  MAX_SKILLS: 3,
  RESPEC_PRICE: 2000,
  INSIDER_CAP: 250,
  NEUTRAL_MODS: {
    beerLuckMult: 1, brownieLuckMult: 1, maxBeers: 3, brownieSpins: 1,
    bjNatural: 1, bjPushBonus: 0, bjHotDeck: 1,
    rouletteNumberPayout: 35, rouletteExclude: 0,
    slotPairMult: 1.2, slotHoldEvery: 0,
    horsePayout: 3, horseLoserMarked: false,
    bankRateAdd: 0, bankLimitAdd: 0, mafiaSpins: 5, mafiaMult: 3, investRateMult: 1,
    mugChanceMult: 1, fightAdd: 0, walletMult: 1,
    postTimeAdd: 0, postPayAdd: 0, postLetters: 15,
  },
  /* Wie ein Schlüssel gestapelt wird: add = Summe, mult = Produkt, max = Maximum, set = letzter Wert */
  MOD_STACK: {
    beerLuckMult: 'mult', brownieLuckMult: 'mult', maxBeers: 'max', brownieSpins: 'max',
    bjNatural: 'max', bjPushBonus: 'max', bjHotDeck: 'max',
    rouletteNumberPayout: 'max', rouletteExclude: 'max',
    slotPairMult: 'set', slotHoldEvery: 'max',
    horsePayout: 'max', horseLoserMarked: 'set',
    bankRateAdd: 'add', bankLimitAdd: 'add', mafiaSpins: 'max', mafiaMult: 'set', investRateMult: 'mult',
    mugChanceMult: 'mult', fightAdd: 'add', walletMult: 'mult',
    postTimeAdd: 'add', postPayAdd: 'add', postLetters: 'max',
  },
  SKILLS: [
    { id: 'pokerface', name: 'Pokerface', icon: '🃏', light: 'Blackjack: natürlicher Blackjack zahlt 3:2, Push bringt +10 %', shadow: 'Bier gibt kein Glück', mods: { bjNatural: 1.5, bjPushBonus: 0.1, beerLuckMult: 0 } },
    { id: 'kalterkopf', name: 'Kalter Kopf', icon: '🧊', light: 'Roulette-Zahlen zahlen 36:1', shadow: 'Brownie wirkt nur halb', mods: { rouletteNumberPayout: 36, brownieLuckMult: 0.5 } },
    { id: 'zockerhaende', name: 'Zockerhände', icon: '🎰', light: 'Slots: Paar zahlt 1,5×', shadow: 'Bank-Zinsen +2 %', mods: { slotPairMult: 1.5, bankRateAdd: 0.02 }, excludes: ['brieftraeger'] },
    { id: 'pferdefluesterer', name: 'Pferdeflüsterer', icon: '🐎', light: 'Pferde zahlen 3,3:1', shadow: 'Überfälle 50 % häufiger', mods: { horsePayout: 3.3, mugChanceMult: 1.5 } },
    { id: 'eisenmagen', name: 'Eisenmagen', icon: '🍺', light: '4 Bier möglich (+25 %), Brownie hält 2 Spins', shadow: 'Postbote: −1 s pro Brief', mods: { maxBeers: 4, brownieSpins: 2, postTimeAdd: -1 } },
    { id: 'verhandler', name: 'Verhandler', icon: '🤝', light: 'Bank-Zinsen −2 %, Vito-Frist 7 Spins', shadow: 'Anlagen zahlen 10 % weniger', mods: { bankRateAdd: -0.02, mafiaSpins: 7, investRateMult: 0.9 } },
    { id: 'strassenkoeter', name: 'Straßenköter', icon: '🐕', light: 'Kampfchance +15 %, Brieftasche ×2', shadow: 'Bank-Limit −1.000 €', mods: { fightAdd: 0.15, walletMult: 2, bankLimitAdd: -1000 } },
    { id: 'brieftraeger', name: 'Briefträgerherz', icon: '📬', light: 'Postbote +1 s und +5 € pro Brief', shadow: 'Slots: Paare zahlen nichts', mods: { postTimeAdd: 1, postPayAdd: 5, slotPairMult: 0 }, excludes: ['zockerhaende'] },
  ],
  INSIDER: [
    { id: 'stallbursche', name: 'Stallbursche', icon: '🐴', text: 'Vor jedem Rennen ist ein Pferd markiert, das sicher nicht gewinnt.', capped: true, mods: { horseLoserMarked: true } },
    { id: 'croupierauge', name: 'Croupier-Auge', icon: '👁️', text: '12 Roulette-Zahlen sind ausgegraut und fallen nicht.', capped: true, mods: { rouletteExclude: 12 } },
    { id: 'kartenzaehler', name: 'Kartenzähler', icon: '🧮', text: 'Blackjack zeigt, ob das Deck heiß ist – dann zahlt ein Sieg 1,2:1.', capped: true, mods: { bjHotDeck: 1.2 } },
    { id: 'mechaniker', name: 'Mechaniker', icon: '🔧', text: 'Slots: nach einer Niete darfst du jede 5. Runde eine Walze festhalten und neu drehen.', capped: true, mods: { slotHoldEvery: 5 } },
    { id: 'bankinsider', name: 'Bankinsider', icon: '🏦', text: 'Zinsen −3 %, Limit +2.000 €.', capped: false, mods: { bankRateAdd: -0.03, bankLimitAdd: 2000 } },
    { id: 'vitosneffe', name: 'Vitos Neffe', icon: '🕶️', text: 'Vito-Frist 8 Spins, Rechnung ×2 statt ×3, Überfälle halb so oft.', capped: false, mods: { mafiaSpins: 8, mafiaMult: 2, mugChanceMult: 0.5 } },
    { id: 'postmeister', name: 'Postmeister', icon: '📮', text: 'Postbote: 20 Briefe pro Schicht, +5 € pro Brief.', capped: false, mods: { postLetters: 20, postPayAdd: 5 } },
  ],
  xpLevel(xp) {
    let level = 1;
    for (let i = 1; i < Rules.XP_LEVELS.length; i++) if (xp >= Rules.XP_LEVELS[i]) level = i + 1;
    const next = level < Rules.XP_LEVELS.length ? Rules.XP_LEVELS[level] : null;
    return { level, next, points: Math.min(Rules.MAX_SKILLS, Math.floor(level / 2)) };
  },
  skillPointsFree(s) { return Math.max(0, Rules.xpLevel(s.xp || 0).points - (s.skills || []).length); },
  canPickSkill(s, id) {
    const def = Rules.SKILLS.find((k) => k.id === id);
    if (!def) return { ok: false, reason: 'unknown' };
    const skills = s.skills || [];
    if (skills.includes(id)) return { ok: false, reason: 'active' };
    if (skills.length >= Rules.MAX_SKILLS) return { ok: false, reason: 'full' };
    if (Rules.skillPointsFree(s) <= 0) return { ok: false, reason: 'points' };
    const conflict = skills.some((k) => { const d = Rules.SKILLS.find((x) => x.id === k); return (d && d.excludes || []).includes(id) || (def.excludes || []).includes(k); });
    if (conflict) return { ok: false, reason: 'conflict' };
    return { ok: true };
  },
  /* Alle aktiven Modifikatoren: Skills aus dem Spielstand, Insider aus dem Meta-Speicher; unbekannte IDs ignoriert */
  mods(s, meta) {
    const out = Object.assign({}, Rules.NEUTRAL_MODS);
    const apply = (m) => {
      for (const [k, v] of Object.entries(m)) {
        const how = Rules.MOD_STACK[k];
        if (how === 'add') out[k] += v;
        else if (how === 'mult') out[k] *= v;
        else if (how === 'max') out[k] = Math.max(out[k], v);
        else out[k] = v;
      }
    };
    for (const id of (s && s.skills) || []) { const d = Rules.SKILLS.find((k) => k.id === id); if (d) apply(d.mods); }
    for (const id of (meta && meta.insider) || []) { const d = Rules.INSIDER.find((k) => k.id === id); if (d) apply(d.mods); }
    return out;
  },
  insiderDraw(meta, rng = Math.random) {
    const pool = Rules.INSIDER.map((i) => i.id).filter((id) => !((meta && meta.insider) || []).includes(id));
    const out = [];
    while (pool.length && out.length < 3) out.push(pool.splice(Math.floor(rng() * pool.length), 1)[0]);
    return out;
  },
  /* Insider-Wissen wirkt voll bis INSIDER_CAP; Zahlen verlieren darüber anteilig ihren Bonus, Schalter gelten nur darunter */
  effectiveInsider(value, bet) {
    if (typeof value === 'boolean') return value && bet <= Rules.INSIDER_CAP;
    if (!bet || bet <= Rules.INSIDER_CAP) return value;
    return 1 + (value - 1) * Rules.INSIDER_CAP / bet;
  },
  deckHot(deck) {
    if (!deck.length) return false;
    const strong = deck.filter((c) => ['10', 'J', 'Q', 'K', 'A'].includes(c.val)).length;
    return strong / deck.length > 0.4;
  },
  pickExcluded(rng = Math.random) {
    const nums = Array.from({ length: 36 }, (_, i) => i + 1);
    const out = [];
    while (out.length < 12) out.push(nums.splice(Math.floor(rng() * nums.length), 1)[0]);
    return out.sort((a, b) => a - b);
  },
  pickLoser(selectedId, rng = Math.random) {
    const others = Rules.HORSES.map((h) => h.id).filter((id) => id !== selectedId);
    return others[Math.floor(rng() * others.length)];
  },
});
</script>
```

- [ ] **Step 6: Tests – grün**

Run: `node tests/run-selftest.mjs`, `tests/dom-selftest.sh`. Expected: alle bestanden (111 + 10).

- [ ] **Step 7: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(perks): Kataloge für Skills und Insider, XP-Level, Rules.mods, Ziehungen, State-Felder

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Regel-Hooks – bestehende Regeln lesen `mods`

**Files:**
- Modify: `keller37.html` – Block `rules` (`BEER_LUCK`, `luck`, `canBeer`, `bankInterest`, `bankLoanReason`, `mafiaBill`, neue `mafiaSpins`, `rouletteRoll`, `roulettePayout`, `rouletteSettle`, `slotMultiplier`, `horseStep`, `horseDelta`, `bjDelta`, `investmentResolve`, `postmanTier`), Block `gear-rules` (`mugChance`, `mugWallet`, `fightChance`); Selftests

**Interfaces:**
- Consumes: `Rules.NEUTRAL_MODS`, `Rules.mods` (Task 1).
- Produces (alle mit `mods = Rules.NEUTRAL_MODS` als Default, alte Aufrufe bleiben gültig): `luck(s, mods)`, `canBeer(s, mods)`, `bankInterest(debt, s, mods)`, `bankLoanReason(s, amt, mods)`, `bankLimitFor(s, mods)`, `bankRateFor(s, mods)`, `mafiaSpins(mods)`, `mafiaBill(debt, mods)`, `rouletteRoll(rng, excluded = [])`, `roulettePayout(type, chosen, rolled, bet, mods)`, `rouletteSettle(bets, rolled, mods)`, `slotMultiplier(a, b, c, mods)`, `horseStep(isSelected, luck, rng, handicap = 1)`, `horseDelta(won, bet, mods)`, `bjDelta(outcome, bet, mods, ctx = {})` mit `ctx.natural`/`ctx.hot`, `investmentResolve(inv, rng, mods)`, `postmanTier(streak, s, mods)`, `mugChance(s, where, mods)`, `mugWallet(rng, mods)`, `fightChance(strength, mods)`.

- [ ] **Step 1: Fehlschlagende Tests**

```js
/* ---- Regel-Hooks mit mods ---- */
const M = (o) => Object.assign({}, Rules.NEUTRAL_MODS, o);
T.test('luck mit mods: Bier/Brownie-Multiplikatoren, 4. Bier', () => {
  T.eq(Rules.BEER_LUCK, [0, 10, 15, 20, 25]);
  T.eq(Rules.luck(base({ beers: 3, beerTimer: 1 }), M({ beerLuckMult: 0 })), 0);
  T.eq(Rules.luck(base({ beers: 4, beerTimer: 1 })), 25);
  T.eq(Rules.luck(base({ brownieTimer: 1 }), M({ brownieLuckMult: 0.5 })), 20);
  T.eq(Rules.canBeer(base({ beers: 3, balance: 100 })).reason, 'max');
  T.eq(Rules.canBeer(base({ beers: 3, balance: 100 }), M({ maxBeers: 4})), { ok: true });
});
T.test('Bank/Vito mit mods', () => {
  near(Rules.bankRateFor(base(), M({ bankRateAdd: -0.03 })), 0.05);
  near(Rules.bankRateFor(base({ car: 'mercG' }), M({ bankRateAdd: -0.05 })), 0.01, 'Untergrenze 1 %');
  T.eq(Rules.bankLimitFor(base(), M({ bankLimitAdd: 2000 })), 5000);
  T.eq(Rules.bankLimitFor(base(), M({ bankLimitAdd: -9000 })), 500, 'Untergrenze 500');
  T.eq(Rules.bankInterest(1000, base(), M({ bankRateAdd: -0.03 })), 50);
  T.eq(Rules.bankLoanReason(base(), 4000, M({ bankLimitAdd: 2000 })), null);
  T.eq(Rules.bankLoanReason(base(), 5001, M({ bankLimitAdd: 2000 })), 'limit');
  T.eq(Rules.mafiaSpins(), 5); T.eq(Rules.mafiaSpins(M({ mafiaSpins: 8 })), 8);
  T.eq(Rules.mafiaBill(300), 900); T.eq(Rules.mafiaBill(300, M({ mafiaMult: 2 })), 600);
});
T.test('Roulette mit mods: 36:1, Ausschlussliste', () => {
  T.eq(Rules.roulettePayout('number', 17, 17, 10), 350);
  T.eq(Rules.roulettePayout('number', 17, 17, 10, M({ rouletteNumberPayout: 36 })), 360);
  T.eq(Rules.rouletteSettle([{ type: 'number', n: 17, amount: 10 }], 17, M({ rouletteNumberPayout: 36 })).payout, 370);
  const ex = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
  for (let i = 0; i < 1000; i++) T.ok(!ex.includes(Rules.rouletteRoll(Math.random, ex)), 'nie ausgeschlossen');
  T.eq(Rules.rouletteRoll(seq(0.05, 0.99), ex), 36, 'zweiter Wurf nach Ausschluss');
  T.eq(Rules.rouletteRoll(seq(0), []), 0);
});
T.test('Slots/Pferde mit mods', () => {
  T.eq(Rules.slotMultiplier('🍒', '🍒', '🍋', M({ slotPairMult: 1.5 })), 1.5);
  T.eq(Rules.slotMultiplier('🍒', '🍒', '🍋', M({ slotPairMult: 0 })), 0);
  T.eq(Rules.slotMultiplier('🍒', '🍒', '🍒', M({ slotPairMult: 0 })), 5, 'Drilling unberührt');
  T.eq(Rules.horseDelta(true, 100), 300); T.eq(Rules.horseDelta(true, 100, M({ horsePayout: 3.3 })), 330); T.eq(Rules.horseDelta(false, 100, M({ horsePayout: 3.3 })), -100);
  near(Rules.horseStep(false, 0, seq(0), 0.85), 1.5 * 0.85, 'Handicap');
});
T.test('Blackjack mit mods: Natural 3:2, Push +10 %, heißes Deck 1,2:1', () => {
  T.eq(Rules.bjDelta('win', 100), 100);
  T.eq(Rules.bjDelta('win', 100, M({ bjNatural: 1.5 }), { natural: true }), 150);
  T.eq(Rules.bjDelta('push', 100, M({ bjPushBonus: 0.1 })), 10);
  T.eq(Rules.bjDelta('win', 100, M({ bjHotDeck: 1.2 }), { hot: true }), 120);
  T.eq(Rules.bjDelta('win', 100, M({ bjHotDeck: 1.2, bjNatural: 1.5 }), { hot: true, natural: true }), 150, 'Natural schlägt heiß');
  T.eq(Rules.bjDelta('dealer', 100, M({ bjNatural: 1.5 }), { natural: true }), -100);
});
T.test('Anlagen/Post/Überfall mit mods', () => {
  T.eq(Rules.investmentResolve({ amount: 100, rate: 0.5, risk: 0 }, seq(0.99)).payout, 150);
  T.eq(Rules.investmentResolve({ amount: 100, rate: 0.5, risk: 0 }, seq(0.99), M({ investRateMult: 0.9 })).payout, 145);
  T.eq(Rules.postmanTier(0, base(), M({ postTimeAdd: 1, postPayAdd: 5 })), { t: 6, r: 10 });
  T.eq(Rules.postmanTier(11, base(), M({ postTimeAdd: -1 })), { t: 0.5, r: 50 }, 'Untergrenze 0,5 s');
  T.eq(Rules.postmanTier(11, base({ shoes: 'carbon' }), M({ postTimeAdd: 1 })), { t: 1.5, r: 60 }, 'Schuh-Deckel bleibt');
  near(Rules.mugChance(mugBase(), 'door', M({ mugChanceMult: 0.5 })), 0.03);
  near(Rules.fightChance(0, M({ fightAdd: 0.15 })), 0.5); near(Rules.fightChance(50, M({ fightAdd: 0.15 })), 0.9);
  T.eq(Rules.mugWallet(() => 0, M({ walletMult: 2 })), 100);
});
```

- [ ] **Step 2: Tests laufen lassen – fehlschlagen** (`node tests/run-selftest.mjs`, 6 FAIL).

- [ ] **Step 3: Regeln umstellen**

Block `rules`:

```js
  BEER_LUCK: [0, 10, 15, 20, 25],
```

```js
  luck(s, mods = Rules.NEUTRAL_MODS) {
    let l = 0;
    if (s.beerTimer > 0) l += Rules.BEER_LUCK[Math.min(s.beers, 4)] * mods.beerLuckMult;
    if (s.brownieTimer > 0) l += Rules.BROWNIE_LUCK * mods.brownieLuckMult;
    l += Rules.gear(s).luck;
    return l;
  },
```

```js
  bankRateFor(s, mods = Rules.NEUTRAL_MODS) { return Math.max(0.01, Rules.gear(s).bankRate + mods.bankRateAdd); },
  bankLimitFor(s, mods = Rules.NEUTRAL_MODS) { return Math.max(500, Rules.gear(s).bankLimit + mods.bankLimitAdd); },
  bankInterest(debt, s, mods = Rules.NEUTRAL_MODS) {
    const rate = s ? Rules.bankRateFor(s, mods) : Rules.BANK_RATE;
    return debt > 0 ? Math.round(debt * rate) : 0;
  },
```

`spinCosts(s)` bleibt, ruft aber `Rules.bankInterest(s.bankDebt, s, s.__mods || Rules.NEUTRAL_MODS)` **nicht** – stattdessen bekommt `spinCosts(s, mods = Rules.NEUTRAL_MODS)` den Parameter und reicht ihn durch; ebenso `maxBet(s, mods)`, `checkSpin(s, bet, mods)`, `isGameOver(s, mods)`. (Aufrufstellen in Task 7.)

```js
  bankLoanReason(s, amt, mods = Rules.NEUTRAL_MODS) {
    if (s.bankDebt > 0) return 'open';
    if (amt > Rules.bankLimitFor(s, mods)) return 'limit';
    return null;
  },
  bankLoanAllowed(s, amt, mods = Rules.NEUTRAL_MODS) { return Rules.bankLoanReason(s, amt, mods) === null; },
  mafiaSpins(mods = Rules.NEUTRAL_MODS) { return mods.mafiaSpins; },
  mafiaBill(debt, mods = Rules.NEUTRAL_MODS) { return debt * mods.mafiaMult; },
```

```js
  canBeer(s, mods = Rules.NEUTRAL_MODS) {
    if (s.beers >= mods.maxBeers) return { ok: false, reason: 'max' };
    …(Rest unverändert)
```

```js
  /* würfelt so lange, bis eine nicht ausgeschlossene Zahl fällt (max. 37 Versuche, dann erste erlaubte) */
  rouletteRoll(rng, excluded = []) {
    for (let i = 0; i < 37; i++) { const n = Math.floor(rng() * 37); if (!excluded.includes(n)) return n; }
    for (let n = 0; n < 37; n++) if (!excluded.includes(n)) return n;
    return 0;
  },
  roulettePayout(type, chosen, rolled, bet, mods = Rules.NEUTRAL_MODS) {
    const red = Rules.isRed(rolled);
    if (type === 'red' && red) return bet;
    if (type === 'black' && !red && rolled !== 0) return bet;
    if (type === 'even' && rolled !== 0 && rolled % 2 === 0) return bet;
    if (type === 'odd' && rolled % 2 !== 0) return bet;
    if (type === 'number' && rolled === chosen) return bet * mods.rouletteNumberPayout;
    return -bet;
  },
```

`rouletteSettle(bets, rolled, mods = Rules.NEUTRAL_MODS)` reicht `mods` an `roulettePayout` durch.

```js
  slotMultiplier(a, b, c, mods = Rules.NEUTRAL_MODS) {
    if (a === b && b === c) return a === '7️⃣' ? 40 : a === '💎' ? 25 : a === '🔔' ? 15 : 5;
    if (a === b || b === c || a === c) return mods.slotPairMult;
    return 0;
  },
```

```js
  horseStep(isSelected, luck, rng, handicap = 1) {
    let step = rng() * 3 + 1;
    if (isSelected && luck > 0) step += luck * 0.001;
    return step * 1.5 * handicap;
  },
  horseDelta(won, bet, mods = Rules.NEUTRAL_MODS) { return won ? Math.round(bet * mods.horsePayout) : -bet; },
```

```js
  /* ctx.natural = Blackjack mit zwei Karten (nur bei Sieg), ctx.hot = heißes Deck (Kartenzähler) */
  bjDelta(outcome, bet, mods = Rules.NEUTRAL_MODS, ctx = {}) {
    if (outcome === 'win') return Math.round(bet * (ctx.natural ? mods.bjNatural : ctx.hot ? mods.bjHotDeck : 1));
    if (outcome === 'push') return Math.round(bet * mods.bjPushBonus);
    return -bet;
  },
```

```js
  investmentResolve(inv, rng, mods = Rules.NEUTRAL_MODS) {
    const won = rng() * 100 >= inv.risk;
    return { won, payout: won ? Math.round(inv.amount * (1 + inv.rate * mods.investRateMult)) : 0 };
  },
```

```js
  postmanTier(streak, s, mods = Rules.NEUTRAL_MODS) {
    const g = s ? Rules.gear(s) : { postTime: 0, postPay: 0 };
    const t = streak < 2 ? { t: 5, r: 5 } : streak < 6 ? { t: 3, r: 10 } : streak < 11 ? { t: 1.5, r: 25 } : { t: 0.5, r: 50 };
    /* Schuhe geben Zeit – die schnellste Stufe wird aber nie langsamer als 1,5 s; Skills addieren danach, Untergrenze 0,5 s */
    const shoeTime = t.t < 1.5 ? Math.min(t.t + g.postTime, 1.5) : t.t + g.postTime;
    return { t: Math.max(0.5, shoeTime + mods.postTimeAdd), r: t.r + g.postPay + mods.postPayAdd };
  },
```

Block `gear-rules`: `mugChance(s, where, mods = Rules.NEUTRAL_MODS)` → letzte Zeile `return c * Rules.gear(s).mugMult * mods.mugChanceMult;`; `mugWallet(rng = Math.random, mods = Rules.NEUTRAL_MODS)` → `return Math.round((M.WALLET_MIN + Math.floor(rng() * (M.WALLET_MAX - M.WALLET_MIN + 1))) * mods.walletMult);`; `fightChance(strength, mods = Rules.NEUTRAL_MODS)` → `Math.min(M.CHANCE_CAP, M.FIGHT_BASE + M.FIGHT_PER_STR * (strength || 0) + mods.fightAdd)`.

Hinweis: `Rules.NEUTRAL_MODS` wird im Block `perk-rules` definiert, der nach `rules` geladen wird – Default-Parameter werden erst beim Aufruf ausgewertet, das ist in Ordnung. Der bestehende Test `postmanTier: Schuhe geben Zeit und Lohn` (`postmanTier(11, carbon) = {t:1.5, r:60}`) bleibt gültig.

- [ ] **Step 4: Tests – grün** (`node tests/run-selftest.mjs`, `tests/dom-selftest.sh`).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(rules): Regeln lesen mods – Glück, Bank, Vito, Roulette (36:1, Ausschluss), Slots, Pferde, Blackjack, Anlagen, Post, Überfall

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Modul `Perks` – XP, Level-Badge, Skill-Screen, Umskillen

**Files:**
- Modify: `keller37.html` – CSS (vor `/* ==== 7. ANIMATIONEN ==== */`), Template `tpl-skills` (vor `<!-- /TEMPLATES -->`), neuer Block `perks` (nach `mugging`), Block `ui` (`Actions.skills`, `renderSide`, `mountShell`/`renderWallet`), Block `story-engine` (`Story.night()` XP pro Tag), `README.md`

**Interfaces:**
- Consumes: Task 1/2.
- Produces: `Perks.mods()`, `Perks.addXp(n, why)`, `Perks.pick(id)`, `Perks.respec()`, `Perks.renderBadge()`, `Perks.render()`, Screen `skills`, `Actions.skills`, DOM `#lvBadge`, `#xpBar`, `#skillSlots`, `#skillCards`, `#btnRespec`, `#insiderList`, Bus-Event `perks:levelup { level }`.

- [ ] **Step 1: CSS**

```css
/* ==== Perks – Level-Badge, Skill-Screen ==== */
.lv-badge { display: inline-flex; align-items: center; gap: 6px; font-family: var(--font-mono); font-size: .8rem; color: var(--gold-2); border: 1px solid rgba(201,162,39,.35); border-radius: 6px; padding: 2px 8px; background: rgba(0,0,0,.3); cursor: pointer; }
.lv-badge .bar { width: 44px; height: 6px; border-radius: 3px; background: #2a2e26; overflow: hidden; }
.lv-badge .bar i { display: block; height: 100%; background: var(--neon-green); }
.lv-badge.point { animation: pulse 1.2s ease-in-out infinite; border-color: var(--neon-green); }
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 rgba(61,220,132,0); } 50% { box-shadow: 0 0 12px rgba(61,220,132,.8); } }
.skills-head { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; justify-content: space-between; }
.xp-bar { flex: 1; min-width: 200px; height: 12px; border-radius: 6px; background: #2a2e26; overflow: hidden; }
.xp-bar i { display: block; height: 100%; background: var(--neon-green); }
.skill-slots { display: flex; gap: 10px; }
.skill-slot { min-width: 110px; padding: 8px 12px; border: 1px dashed rgba(201,162,39,.4); border-radius: 8px; font-family: var(--font-mono); font-size: .8rem; text-align: center; color: var(--dim); }
.skill-slot.filled { border-style: solid; color: var(--gold-2); }
.skill-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.skill-card { background: var(--panel-2); border: 1px solid rgba(255,255,255,.06); border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 6px; }
.skill-card.active { border-color: var(--gold); box-shadow: 0 0 14px rgba(201,162,39,.25); }
.skill-card h4 { font-family: var(--font-display); letter-spacing: .08em; }
.skill-card .light { color: var(--neon-green); font-family: var(--font-mono); font-size: .8rem; }
.skill-card .shadow { color: #ff8a80; font-family: var(--font-mono); font-size: .8rem; }
.skill-card .reason { color: var(--dim); font-family: var(--font-mono); font-size: .75rem; margin-top: auto; }
.skill-card .btn { margin-top: auto; align-self: flex-start; font-size: .85rem; padding: 6px 14px; }
.insider-list { display: flex; flex-wrap: wrap; gap: 10px; }
.insider-chip { border: 1px solid rgba(76,201,240,.4); border-radius: 8px; padding: 8px 12px; background: rgba(0,0,0,.3); font-family: var(--font-mono); font-size: .8rem; max-width: 280px; }
.insider-chip b { display: block; color: var(--neon-blue); }
```

- [ ] **Step 2: Template**

```html
<template id="tpl-skills">
  <div class="panel stretch">
    <h2>🧠 Kopf</h2>
    <div class="skills-head">
      <div class="xp-bar"><i id="xpBar"></i></div>
      <span class="side-hint" id="xpText"></span>
      <div class="skill-slots" id="skillSlots"></div>
      <button class="btn ghost sm" id="btnRespec">Umskillen · 2.000 €</button>
    </div>
    <div class="skill-cards" id="skillCards"></div>
    <div class="chalk"><h4>🕵️ Insider</h4><div class="insider-list" id="insiderList"></div></div>
  </div>
</template>
```

- [ ] **Step 3: Block `perks`**

Nach `</script>` des Blocks `mugging`:

```html
<script id="perks">
/* ================= PERKS – XP, Skills, Insider-Anzeige ================= */
const Perks = {
  root: null,
  mods() { return Rules.mods(State.s, State.meta); },
  addXp(n, why) {
    const s = State.s;
    const before = Rules.xpLevel(s.xp || 0);
    s.xp = (s.xp || 0) + n;
    const after = Rules.xpLevel(s.xp);
    State.save();
    this.renderBadge();
    if (after.level > before.level) {
      const free = Rules.skillPointsFree(s);
      UI.toast({ icon: '🧠', title: `Level ${after.level}`, text: free > 0 ? 'Ein Skill-Punkt wartet – klick auf das Level.' : (after.level >= 6 ? 'Mehr geht nicht. Respekt.' : 'Weiter so.'), tone: 'gold', ms: 4000 });
      SFX.play('unlock');
      Bus.emit('perks:levelup', { level: after.level });
    }
    if (this.root) this.render();
  },
  renderBadge() {
    const el = qs('#lvBadge');
    if (!el) return;
    const s = State.s;
    const lv = Rules.xpLevel(s.xp || 0);
    const pct = lv.next ? Math.round(((s.xp - Rules.XP_LEVELS[lv.level - 1]) / (lv.next - Rules.XP_LEVELS[lv.level - 1])) * 100) : 100;
    el.innerHTML = '';
    el.append(`Lv ${lv.level}`, h('span', { class: 'bar' }, h('i', { style: `width:${pct}%` })));
    el.classList.toggle('point', Rules.skillPointsFree(s) > 0);
    el.title = lv.next ? `${s.xp} / ${lv.next} XP` : `${s.xp} XP · max`;
  },
  REASON: { points: 'Kein Punkt frei', full: 'Alle Slots belegt', conflict: 'Passt nicht zu einem aktiven Skill', active: 'Aktiv', unknown: '' },
  render() {
    if (!this.root) return;
    const s = State.s;
    const lv = Rules.xpLevel(s.xp || 0);
    const from = Rules.XP_LEVELS[lv.level - 1];
    qs('#xpBar', this.root).style.width = lv.next ? `${Math.round(((s.xp - from) / (lv.next - from)) * 100)}%` : '100%';
    qs('#xpText', this.root).textContent = lv.next ? `Lv ${lv.level} · ${s.xp} / ${lv.next} XP` : `Lv ${lv.level} · ${s.xp} XP · max`;
    const slots = qs('#skillSlots', this.root); slots.innerHTML = '';
    for (let i = 0; i < Rules.MAX_SKILLS; i++) {
      const id = s.skills[i];
      const def = id && Rules.SKILLS.find((k) => k.id === id);
      const unlockLv = (i + 1) * 2;
      slots.append(h('div', { class: 'skill-slot' + (def ? ' filled' : '') }, def ? `${def.icon} ${def.name}` : (lv.points > i ? 'frei' : `ab Lv ${unlockLv}`)));
    }
    const cards = qs('#skillCards', this.root); cards.innerHTML = '';
    for (const def of Rules.SKILLS) {
      const chk = Rules.canPickSkill(s, def.id);
      const card = h('div', { class: 'skill-card' + (chk.reason === 'active' ? ' active' : '') },
        h('h4', {}, `${def.icon} ${def.name}`),
        h('div', { class: 'light' }, `＋ ${def.light}`),
        h('div', { class: 'shadow' }, `－ ${def.shadow}`));
      if (chk.ok) card.append(h('button', { class: 'btn', onclick: () => this.pick(def.id) }, 'Wählen'));
      else card.append(h('div', { class: 'reason' }, this.REASON[chk.reason] || ''));
      cards.append(card);
    }
    qs('#btnRespec', this.root).disabled = s.skills.length === 0;
    const list = qs('#insiderList', this.root); list.innerHTML = '';
    const ins = (State.meta.insider || []).map((id) => Rules.INSIDER.find((i) => i.id === id)).filter(Boolean);
    if (!ins.length) list.append(h('span', { class: 'empty' }, 'Noch keins – schließe ein Story-Teil ab.'));
    for (const i of ins) list.append(h('div', { class: 'insider-chip' }, h('b', {}, `${i.icon} ${i.name}`), i.text));
  },
  pick(id) {
    const s = State.s;
    const chk = Rules.canPickSkill(s, id);
    if (!chk.ok) return;
    s.skills.push(id);
    State.save();
    SFX.play('unlock');
    const def = Rules.SKILLS.find((k) => k.id === id);
    UI.toast({ icon: def.icon, title: def.name, text: def.light, tone: 'gold' });
    this.render(); this.renderBadge(); UI.renderWallet(); UI.renderSide();
  },
  async respec() {
    const s = State.s;
    if (!s.skills.length) return;
    if (s.balance < Rules.RESPEC_PRICE) { UI.toast({ icon: '🧠', title: 'Zu wenig Geld', text: `Umskillen kostet ${UI.fmt(Rules.RESPEC_PRICE)}.`, tone: 'loss' }); SFX.play('lose'); return; }
    const choice = await Cutscene.play('perks.respec', { price: UI.fmt(Rules.RESPEC_PRICE) });
    if (choice !== 'yes' || !s.skills.length || s.balance < Rules.RESPEC_PRICE) return;
    Game.applyDelta(-Rules.RESPEC_PRICE, { from: this.root ? qs('#skillSlots', this.root) : null });
    s.skills = []; s.skillRespecs++;
    State.save();
    UI.toast({ icon: '🧠', title: 'Kopf frei', text: 'Alle Skill-Punkte sind wieder verfügbar.', tone: 'info' });
    this.render(); this.renderBadge(); UI.renderWallet(); UI.renderSide();
  },
};
UI.register('skills', {
  template: 'tpl-skills',
  mount(root) { Perks.root = root; qs('#btnRespec', root).addEventListener('click', () => Perks.respec()); Perks.render(); },
  unmount() { Perks.root = null; },
});
Cutscene.define('perks.respec', (ctx) => [
  { bg: 'bar', who: 'wirt', mood: 'calm', text: `Alles vergessen für ${ctx.price}? Der Doc hat da so ein Pulver. Danach bist du wieder ein unbeschriebenes Blatt.`,
    choices: [{ label: 'Ja, alles vergessen', value: 'yes', cls: 'red' }, { label: 'Doch nicht', value: 'no', cls: 'ghost' }] },
]);
/* XP-Quellen */
Bus.on('spin:after', () => Perks.addXp(Rules.XP_GAIN.spin, 'spin'));
Bus.on('win', () => Perks.addXp(Rules.XP_GAIN.win, 'win'));
Bus.on('job:done', () => Perks.addXp(Rules.XP_GAIN.job, 'job'));
Bus.on('achievement:unlock', () => Perks.addXp(Rules.XP_GAIN.achievement, 'achievement'));
Bus.on('story:day', () => Perks.addXp(Rules.XP_GAIN.day, 'day'));
</script>
```

- [ ] **Step 4: Kopfzeile, Seitenleiste, Story-Tag**

Block `ui`, `mountShell()`: in `wallet-mid` nach dem Glück-Element: `h('button', { class: 'lv-badge', id: 'lvBadge', title: 'Skills', onclick: () => UI.show('skills') })`; am Ende von `renderWallet()`: `if (typeof Perks !== 'undefined') Perks.renderBadge();`.

`Actions`: `skills: () => UI.show('skills'),`. `renderSide()`: vor der Stadt-Sektion: `secs.push(sec('Kopf', btn('🧠 Skills', Rules.skillPointsFree(s) > 0 ? `${Rules.skillPointsFree(s)} Punkt frei` : `Lv ${Rules.xpLevel(s.xp || 0).level}`, 'skills')));` (in beiden Modi).

Block `story-engine`, `Story.night()`: direkt nach `StoryRules.advanceDay(State.s);` → `await Bus.emit('story:day', { day: State.s.story.day });`.

`Story.isLocked`: `skills` in die Liste der nie gesperrten Screens (`['jobs', 'vito', 'skills']`).

- [ ] **Step 5: README** – Abschnitt „Skills & Insider": XP-Quellen, Level 2/4/6, 8 Skills mit Licht/Schatten (Tabelle), Umskillen 2.000 €, Insider pro Story-Teil, Deckel 250 €.

- [ ] **Step 6: Tests und Sichtprüfung** – `node tests/run-selftest.mjs`, `tests/dom-selftest.sh`; `tests/screenshot.sh out.png "?fresh&screen=skills"`; Konsole/CDP: `Perks.addXp(25)` → Toast, Badge pulsiert; Karte „Wählen" → aktiv; `Perks.respec()` mit 2.000 €.

- [ ] **Step 7: Commit** – `feat(perks): XP durch Spielen, Level-Badge, Skill-Screen mit Wahl und Umskillen`.

---

### Task 4: Insider-Wahl beim Story-Ende, Titel-Panel, Ausschlussliste

**Files:**
- Modify: `keller37.html` – Block `perks` (`Perks.offerInsider`, `Perks.refreshExcluded`), Block `story-engine` (`Story.finish`), Block `cutscene-engine` (`CAST.insider`), Titel-Trophäen-Panel (Block `title`, `renderWall` oder Panel-Aufbau), Block `gameover` (`restartGame`)

**Interfaces:**
- Consumes: `Rules.insiderDraw`, `Rules.pickExcluded`, `Perks.mods()`.
- Produces: `Perks.offerInsider(storyId) → Promise<string|null>`, `Perks.refreshExcluded()` (setzt `State.s.insiderExcluded` = 12 Zahlen, wenn `mods.rouletteExclude > 0`, sonst `[]`), Szene `insider.offer`, Bus `insider:granted { id }`.

- [ ] **Step 1: Fehlschlagender Test** (Node, reine Logik ist in Task 1 – hier nur der Wahl-Ablauf per Browser; kein Node-Test nötig). Stattdessen DOM-Selftest-Fall im Block `selftest`, der nur im Browser läuft:

```js
if (typeof Perks !== 'undefined') T.test('Perks.refreshExcluded: 12 Zahlen nur mit Croupier-Auge', () => {
  const s = State.s, m = State.meta; const bakS = s.insiderExcluded, bakM = m.insider;
  m.insider = ['croupierauge']; Perks.refreshExcluded(); T.eq(s.insiderExcluded.length, 12);
  m.insider = []; Perks.refreshExcluded(); T.eq(s.insiderExcluded, []);
  s.insiderExcluded = bakS; m.insider = bakM;
});
```

- [ ] **Step 2: Implementierung**

Block `perks`, im Objekt `Perks`:

```js
  refreshExcluded() {
    const s = State.s;
    s.insiderExcluded = this.mods().rouletteExclude > 0 ? Rules.pickExcluded(Math.random) : [];
    State.save();
  },
  async offerInsider(storyId) {
    const meta = State.meta;
    if (meta.insiderClaimed[storyId]) return null;
    const draw = Rules.insiderDraw(meta, Math.random);
    if (!draw.length) { UI.toast({ icon: '🕵️', title: 'Der Insider', text: 'Er hat nichts Neues für dich.', tone: 'info' }); return null; }
    const defs = draw.map((id) => Rules.INSIDER.find((i) => i.id === id));
    const choice = await Cutscene.play('insider.offer', { choices: defs.map((d) => ({ label: `${d.icon} ${d.name}`, value: d.id, cls: 'blue' })), texts: defs.map((d) => `${d.name}: ${d.text}`).join(' · ') });
    if (!choice || !draw.includes(choice)) return null;
    meta.insider.push(choice); meta.insiderClaimed[storyId] = true;
    State.saveMeta();
    this.refreshExcluded();
    const def = Rules.INSIDER.find((i) => i.id === choice);
    UI.toast({ icon: def.icon, title: `Insider: ${def.name}`, text: def.text, tone: 'gold', ms: 4500 });
    SFX.play('unlock');
    await Bus.emit('insider:granted', { id: choice });
    return choice;
  },
```

Szene (nach `perks.respec`):

```js
Cutscene.define('insider.offer', (ctx) => [
  { bg: 'hinterzimmer', who: 'insider', mood: 'calm', text: 'Du hast ein Kapitel überlebt. Das sehen nicht viele. Ich habe da ein paar Dinge, die man nicht kaufen kann – nur wissen.' },
  { bg: 'hinterzimmer', who: 'insider', mood: 'happy', text: `Such dir eins aus. ${ctx.texts}`, choices: ctx.choices },
]);
```

`Cutscene.CAST`: `insider: { name: 'Der Insider', emoji: '🕵️', color: 'var(--neon-blue)' },`.

`Story.finish(end)`: nach `await Cutscene.play('story.ending.tmp', …)` und vor `await Bus.emit('story:ended', …)`: `if (typeof Perks !== 'undefined') await Perks.offerInsider(this.story.id);`.

`restartGame` (Block `gameover`): nach dem Reset `Perks.refreshExcluded();` (damit ein neues freies Spiel mit Croupier-Auge sofort 12 Zahlen hat). Ebenso in `Modes.enter('newstory')`/Story-Start (dort, wo `freshStoryPart` in den neuen Spielstand geschrieben wird): `Perks.refreshExcluded()`.

Titel: im Trophäen-Panel (`#titleTrophiesPanel`, Aufbau in Block `title`) unter der Wand einen Abschnitt `h('div', { class: 'trophy-sep' }, 'Insider')` gefolgt von `.insider-chip`-Elementen der gewonnenen Upgrades (oder „Noch keins").

- [ ] **Step 3: Tests/Sichtprüfung** – `node`/`dom` grün; Browser: `?fresh&story=schuld&ending=ehrlich` (Dev-Parameter `?ending` existiert) → nach dem Statistik-Panel erscheint der Insider mit 3 Optionen; Wahl → Toast, `State.meta.insider` enthält die ID; zweiter Durchlauf desselben Endes → keine Szene.

- [ ] **Step 4: Commit** – `feat(perks): Insider-Wahl beim Story-Ende, Titel-Panel, Ausschlussliste fürs Croupier-Auge`.

---

### Task 5: Spiele I – Roulette (Ausschluss) und Pferde (lahmes Pferd)

**Files:**
- Modify: `keller37.html` – Block `game-roulette` (`buildTable`, `place`, `spin`, Hinweis), Block `game-horses` (Start des Rennens, Runner-Markierung, `horseDelta`-Aufruf), CSS, Templates `tpl-roulette`/`tpl-horses` (Hinweiszeile)

**Interfaces:**
- Consumes: `Perks.mods()`, `Rules.effectiveInsider`, `Rules.rouletteRoll(rng, excluded)`, `Rules.rouletteSettle(bets, rolled, mods)`, `Rules.pickLoser`, `Rules.horseStep(…, handicap)`, `Rules.horseDelta(won, bet, mods)`, `State.s.insiderExcluded`.
- Produces: `.rcell.excluded`, `#rouletteInsider` (Hinweis), `.runner.lame` + `#horseInsider`, `Horses.loser`.

- [ ] **Step 1: Roulette**

CSS: `.rcell.excluded { opacity: .28; filter: grayscale(1); pointer-events: none; }` `.insider-hint { font-family: var(--font-mono); font-size: .75rem; color: var(--neon-blue); }`.

Template `tpl-roulette`: unter `.table-bar` eine Zeile `<div class="insider-hint hidden" id="rouletteInsider"></div>`.

`buildTable()`: nach dem Bau der Zellen: `this.applyExcluded()`:

```js
  excluded() { return Perks.mods().rouletteExclude > 0 ? (State.s.insiderExcluded || []) : []; },
  applyExcluded() {
    const ex = this.excluded();
    qsa('.rcell', this.root).forEach((c) => { const n = c.dataset.key.startsWith('n') ? parseInt(c.dataset.key.slice(1), 10) : null; c.classList.toggle('excluded', n !== null && ex.includes(n)); });
    const hint = qs('#rouletteInsider', this.root);
    hint.classList.toggle('hidden', !ex.length);
    hint.textContent = ex.length ? `👁️ Croupier-Auge: ${ex.length} Zahlen fallen nicht (wirkt bis ${UI.fmt(Rules.INSIDER_CAP)} Gesamteinsatz)` : '';
  },
```

`place()`: `if (type === 'number' && this.excluded().includes(n)) return;`.
`spin()`: `const mods = Perks.mods(); const ex = Rules.effectiveInsider(this.excluded().length > 0, total) ? this.excluded() : []; let rolled = Rules.rouletteRoll(Math.random, ex);` und `Rules.rouletteSettle(bets, rolled, mods)`. Wenn `this.excluded().length && !ex.length` (Einsatz über dem Deckel): Statuszeile vor dem Dreh „Über 250 € schaut der Croupier genauer hin – keine Hilfe."; Kesselfelder (`drawWheel`): ausgeschlossene Zahlen mit `#3a3a3a` Füllung zeichnen (Parameter `excluded` aus `this.excluded()`).

- [ ] **Step 2: Pferde**

CSS: `.runner.lame .horse { filter: grayscale(.8); opacity: .7; } .runner .lame-tag { position: absolute; left: 6px; top: -10px; font-family: var(--font-mono); font-size: .7rem; color: #ff8a80; }`.

`Horses.start()` (vor dem Rennen, nach `const bet = …`/`beginSpin`): 

```js
      const mods = Perks.mods();
      const marked = Rules.effectiveInsider(mods.horseLoserMarked, bet) ? this.loser : null;
```

`Horses` bekommt `loser: null` und in `mount` sowie nach jedem Rennen: `Horses.pickLoser()`:

```js
  pickLoser() {
    this.loser = Perks.mods().horseLoserMarked ? Rules.pickLoser(State.s.selectedHorse, Math.random) : null;
    qsa('.runner', this.root).forEach((r) => { const id = parseInt(r.id.slice(2), 10); const lame = id === this.loser; r.classList.toggle('lame', lame); qsa('.lame-tag', r).forEach((t) => t.remove()); if (lame) r.append(h('span', { class: 'lame-tag' }, '🚫 lahmt')); });
    const hint = qs('#horseInsider', this.root);
    if (hint) { hint.classList.toggle('hidden', this.loser === null); hint.textContent = this.loser !== null ? `🐴 Stallbursche: ${Rules.HORSES.find((x) => x.id === this.loser).name} gewinnt heute nicht (wirkt bis ${UI.fmt(Rules.INSIDER_CAP)} Einsatz)` : ''; }
  },
```

Wird das gewählte Pferd geändert (`selectedHorse`), erneut `pickLoser()` aufrufen (nie das gewählte). Im Rennen: `pos[i] += Rules.horseStep(hrs.id === selected, luck, Math.random, hrs.id === marked ? 0.85 : 1);` und `Rules.horseDelta(won, bet, mods)`. Template `tpl-horses`: `<div class="insider-hint hidden" id="horseInsider"></div>` unter der Bahn. Status bei Einsatz über dem Deckel: „Über 250 € hält der Stallbursche den Mund."

- [ ] **Step 3: Tests/Sichtprüfung** – `node`/`dom` grün; CDP: `State.meta.insider=['croupierauge','stallbursche']; Perks.refreshExcluded(); UI.show('roulette')` → 12 `.rcell.excluded`; 200 Stub-Würfe nie in der Liste; `UI.show('horses')` → ein `.runner.lame` ≠ gewähltes Pferd. Screenshots `roulette-croupierauge.png`, `horses-stallbursche.png` im Scratchpad ansehen.

- [ ] **Step 4: Commit** – `feat(insider): Croupier-Auge graut 12 Zahlen aus, Stallbursche markiert ein lahmes Pferd`.

---

### Task 6: Spiele II – Blackjack (Natural, heißes Deck) und Slots (Festhalten)

**Files:**
- Modify: `keller37.html` – Block `game-blackjack` (`start`, `finish`, Deck-Anzeige), Template `tpl-blackjack`; Block `game-slots` (`spin`, `respin`, Hold-Buttons), Template `tpl-slots`, CSS

**Interfaces:**
- Consumes: `Perks.mods()`, `Rules.effectiveInsider`, `Rules.deckHot`, `Rules.bjDelta(outcome, bet, mods, ctx)`, `Rules.slotMultiplier(a, b, c, mods)`, `State.s.mechRespins`.
- Produces: `#bjDeckHeat`, `round.natural`, `round.hot`; `Slots.lastRes`, `Slots.holdIndex`, `Slots.respin()`, `.hold-btn`, `#slotInsider`.

- [ ] **Step 1: Blackjack**

Template: neben dem Dealer-Label `<span class="insider-hint hidden" id="bjDeckHeat"></span>`.
`start()`: nach dem Austeilen: `round.natural = round.pHand.length === 2 && Rules.handSum(round.pHand) === 21; const mods = Perks.mods(); round.hot = Rules.effectiveInsider(mods.bjHotDeck, bet) > 1 && Rules.deckHot(round.deck);` Anzeige: wenn `mods.bjHotDeck > 1`: `#bjDeckHeat` sichtbar mit `Rules.deckHot(round.deck) ? '🔥 Deck heiß' : '❄️ Deck kalt'` (+ „(wirkt bis 250 €)" wenn `bet > INSIDER_CAP`). Bei Natural: Status „Blackjack! Stand, um zu kassieren." (Hit bleibt erlaubt; `natural` gilt nur, solange `pHand.length === 2`).
`finish(outcome, round)`: `const mods = Perks.mods(); const ctx = { natural: round.natural && round.pHand.length === 2 && outcome === 'win', hot: !!round.hot }; const delta = Rules.bjDelta(outcome, round.bet, mods, ctx);` Statusmeldungen: `win` → `Gewonnen · +${UI.fmt(delta)}` mit Zusatz „(Blackjack 3:2)" bzw. „(heißes Deck 1,2:1)"; `push` → `Push · Unentschieden` + (`delta > 0` ? ` · +${UI.fmt(delta)} Trinkgeld` : ''). `Game.settle(delta, …)` unverändert.

- [ ] **Step 2: Slots**

`Slots`: Felder `lastRes: null, holdIndex: -1`. Nach einem Spin mit `m === 0` (Niete) und `Perks.mods().slotHoldEvery > 0`: `State.s.mechRespins++` (bei Gewinn ebenfalls `++`, der Zähler zählt Runden); `State.save()`. Wenn `mechRespins >= slotHoldEvery` **und** `Rules.effectiveInsider(true, bet)` **und** Niete: `this.lastRes = res; this.lastBet = bet;` und über jeder Walze einen Button `.hold-btn` „Festhalten" einblenden (`#holds` Container im Template, drei Buttons `data-reel="0|1|2"`). Klick → `Slots.respin(k)`:

```js
  async respin(k) {
    if (this.spinning || !this.root || !this.lastRes) return;
    const bet = this.lastBet, gen = this.gen, held = this.lastRes[k];
    this.lastRes = null; State.s.mechRespins = 0; State.save();
    this.spinning = true;
    try {
      qsa('.hold-btn', this.root).forEach((b) => b.classList.add('hidden'));
      qs('#slotStatus', this.root).textContent = `Walze ${k + 1} festgehalten – Gratisdreh…`;
      const fresh = Rules.slotRoll(Math.random);
      const res = fresh.map((sym, i) => (i === k ? held : sym));
      [0, 1, 2].filter((i) => i !== k).forEach((i, j) => { const s = qs(`#reel${i + 1} .strip`, this.root); s.style.transition = 'none'; s.style.transform = 'translateY(0)'; void s.offsetHeight; s.classList.add('spinning'); setTimeout(() => { if (this.alive(gen)) { this.setReel(i + 1, res[i], true); qs(`#reel${i + 1}`, this.root).classList.add('locked'); SFX.play('reelStop'); } }, 800 + j * 600); });
      SFX.loop('reelSpin', 120);
      await wait(1900);
      SFX.stop('reelSpin');
      const m = Rules.slotMultiplier(...res, Perks.mods());
      const payout = m > 0 ? Math.round(bet * m) : 0;
      if (this.alive(gen)) qs('#slotStatus', this.root).innerHTML = payout > 0 ? `<span class="win">Gratisdreh: ${String(m).replace('.', ',')}× · +${UI.fmt(payout)}</span>` : `<span class="loss">Gratisdreh: Niete. Der Mechaniker zuckt mit den Schultern.</span>`;
      if (payout > 0) { Game.applyDelta(payout, { from: this.alive(gen) ? qs('.slot-machine', this.root) : null }); SFX.play('cash'); await Bus.emit('win', { amount: payout, game: 'slots' }); }
      State.save();
    } finally {
      SFX.stop('reelSpin');
      if (this.gen === gen) this.spinning = false;
    }
  },
```

Der Gratisdreh ist kein Spin (kein `beginSpin`/`afterSpin`, keine Zinsen/Meds, kein XP über `spin:after`; `win` gibt XP). Template `tpl-slots`: über den Walzen `<div class="holds" id="holds"><button class="btn ghost sm hold-btn hidden" data-reel="0">Festhalten</button>…</div>`, darunter `<div class="insider-hint hidden" id="slotInsider"></div>` („🔧 Mechaniker: nächster Gratisdreh in N Runden" / „bereit" / „wirkt bis 250 €"). `spin()` benutzt `Rules.slotMultiplier(...res, Perks.mods())`; Paar-Anzeige im Paytable (`Paar 1,2×`) wird beim Mount aus `mods.slotPairMult` gesetzt (`#payPair`).

- [ ] **Step 3: Tests/Sichtprüfung** – `node`/`dom` grün; CDP: `State.meta.insider=['kartenzaehler','mechaniker']`, Blackjack-Deal zeigt Deck-Hitze; `State.s.skills=['pokerface']` und gestubbtes Deck mit A+K → Natural → +150 auf 100 €; Slots: nach 5 Nieten (Stub) erscheinen Festhalten-Buttons, Klick → Gratisdreh ohne Kontoabzug.

- [ ] **Step 4: Commit** – `feat(insider): Blackjack Natural 3:2/Push-Bonus/heißes Deck, Slots-Mechaniker mit Gratisdreh`.

---

### Task 7: Aufrufstellen verdrahten – Bar, Bank/Vito, Überfall, Postbote, Kosten

**Files:**
- Modify: `keller37.html` – Block `core` (`Game.beginSpin`, `spinCosts`-Aufrufer, `afterSpin` Brownie/Investments, `isGameOver`-Aufruf), Block `rooms` (`Actions.beer/brownie`, `Finance.render/loanBank/loanMafia`, Vito-Rechnung, Bar-Text), Block `mugging` (`mugChance`, `fightChance`, `mugWallet`, Anzeige der Prozente), Block `game-postman` (`postmanTier`, Schichtende `postLetters`), Block `ui` (`renderWallet` Zinsen, Bier-Knopf „(3/4)"), Block `story-engine` (`StoryRules`-nahe Aufrufe von `bankInterest`), Selftests (Tick-Regeln falls nötig)

**Interfaces:**
- Consumes: alles aus Task 2/3 (`Perks.mods()`, Regeln mit `mods`).
- Produces: alle Aufrufstellen übergeben `Perks.mods()`; `Game.beginSpin` nutzt `Rules.checkSpin(State.s, bet, Perks.mods())`; `Rules.spinCosts(s, mods)` überall mit `mods`.

- [ ] **Step 1: Aufrufstellen**

- `Game.beginSpin(bet)`: `const chk = Rules.checkSpin(State.s, bet, Perks.mods());` (und `maxBet`-Aufrufe in `bindBet`/Roulette: `Rules.maxBet(State.s, Perks.mods())`).
- `Game.afterSpin`: `Rules.investmentResolve(inv, Math.random, Perks.mods())`; Game-Over-Prüfung `Rules.isGameOver(s, Perks.mods())` (wo sie steht, `grep -n "isGameOver("`).
- `Actions.beer`: `Rules.canBeer(s, Perks.mods())`, Toast-Text „Maximal N Bier" mit `mods.maxBeers`; Toast `+${Rules.BEER_LUCK[s.beers] * mods.beerLuckMult} % Glück` (bei 0: „Bier schmeckt, wirkt aber nicht – Pokerface."). Seitenleiste: `🍺 Bier (${s.beers}/${mods.maxBeers})`.
- `Actions.brownie`: `s.brownieTimer = Perks.mods().brownieSpins;`.
- `Finance.render`: `bankTerms` liest `Rules.bankRateFor(s, mods)`/`Rules.bankLimitFor(s, mods)`; Limit-Knopf `loanAmount('limit')` → `Rules.bankLimitFor(State.s, Perks.mods())`; `loanBank`: `Rules.bankLoanReason(s, amt, Perks.mods())`, Szene `bank.limit` mit `limit: UI.fmt(Rules.bankLimitFor(…))`; `loanMafia`: `s.mafiaSpins = Rules.mafiaSpins(Perks.mods());`; Vito-Rechnung: `Rules.mafiaBill(s.mafiaDebt, Perks.mods())` (alle Aufrufstellen per `grep -n "mafiaBill("`); Vito-Zettel-Text „Noch N Spins" unverändert.
- `UI.renderWallet`: `Rules.bankInterest(s.bankDebt, s, Perks.mods())`, `Rules.luck(s, Perks.mods())`; alle weiteren `Rules.luck(State.s)`-Aufrufe (Slots/Roulette/Pferde) → `Rules.luck(State.s, Perks.mods())`.
- `Mugging.maybe`: `Rules.mugChance(s, where, Perks.mods())`; `Mugging.run`: `Rules.fightChance(s.strength, mods)` (Anzeige und Wurf), `Rules.mugWallet(Math.random, mods)`.
- Postbote: `Rules.postmanTier(this.streak, State.s, Perks.mods())`; Schichtende `if (this.streak >= Perks.mods().postLetters)` mit Text `Feierabend! ${n} Briefe ausgetragen.`; Pinnwand-Text („endet nach 15 Briefen") dynamisch aus `mods.postLetters` in `Jobs.render`.
- Story-`StoryRules`-Aufrufe von `bankInterest`/`spinCosts` (falls vorhanden, `grep -n "spinCosts(\|bankInterest("`): `Perks.mods()` übergeben.

- [ ] **Step 2: Tests** – `node`/`dom` grün. Browser-Kurzcheck per CDP: `State.s.skills=['eisenmagen']` → 4 Bier möglich, Seitenleiste „(3/4)"; `['verhandler']` → `#bankTerms` 6 %; `State.meta.insider=['vitosneffe']` → Vito-Kredit zeigt 8 Spins; `['postmeister']` → Schicht endet nach 20 Briefen (Stub).

- [ ] **Step 3: Commit** – `feat(perks): Aufrufstellen lesen Perks.mods – Bar, Bank, Vito, Überfall, Postbote, Spin-Kosten`.

---

### Task 8: Playtest, Screenshots, Checkliste

**Files:**
- Modify: `tests/playtest-story.py` (Szenario `scenario_perks`), `docs/superpowers/screenshots/` (neu: `skills.png`, `insider-offer.png`, `roulette-croupierauge.png`; erneuern, was sich durch das Level-Badge in der Kopfzeile ändert – alle vier Sandbox-Referenzen `slots/roulette/blackjack/hub.png`), Create: `docs/superpowers/checklist-insider-2026-09-17.md`

- [ ] **Step 1: Szenario**

```python
async def scenario_perks(cdp):
    """XP -> Level 2 -> Skill; Umskillen; Insider-Wahl am Story-Ende; Croupier-Auge; Stallbursche; Mechaniker."""
    await cdp.navigate(URL_BASE + "?fresh&screen=skills")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.eval("localStorage.removeItem('keller37.meta'); State.meta.insider = []; State.meta.insiderClaimed = {}; State.saveMeta(); 0", await_promise=False)
    n = await cdp.eval("document.querySelectorAll('#skillCards .btn').length", await_promise=False)
    record("perks: ohne Punkt kein Waehlen-Button", n == 0, "buttons=%s" % n)
    await cdp.eval("Perks.addXp(25, 'test'); 0", await_promise=False)
    await asyncio.sleep(0.4)
    pulsing = await cdp.eval("document.querySelector('#lvBadge').classList.contains('point')", await_promise=False)
    n = await cdp.eval("document.querySelectorAll('#skillCards .btn').length", await_promise=False)
    record("perks: Level 2 -> Badge pulsiert, 8 Skills waehlbar", pulsing is True and n == 8, "pulsing=%s buttons=%s" % (pulsing, n))
    await cdp.screenshot("skills.png")
    await cdp.eval("Perks.pick('zockerhaende'); 0", await_promise=False)
    await asyncio.sleep(0.3)
    skills = await cdp.eval("JSON.stringify(State.s.skills)", await_promise=False)
    conflict = await cdp.eval("[...document.querySelectorAll('#skillCards .skill-card')].find(c=>c.textContent.includes('Brieftr')).querySelector('.reason').textContent", await_promise=False)
    record("perks: Skill aktiv, Konflikt-Grund sichtbar", skills == '["zockerhaende"]' and conflict is not None and "Passt nicht" in conflict, "skills=%s conflict=%s" % (skills, conflict))
    await cdp.eval("State.s.balance = 5000; State.save(); UI.setBalance(5000, {animate:false}); Perks.respec(); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene(label_hint="Ja, alles vergessen")
    await asyncio.sleep(0.4)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    skills = await cdp.eval("JSON.stringify(State.s.skills)", await_promise=False)
    record("perks: Umskillen kostet 2000 und leert die Skills", bal == 3000 and skills == "[]", "bal=%s skills=%s" % (bal, skills))
    # Insider-Wahl am Story-Ende
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&ending=ehrlich")
    await asyncio.sleep(1.5)
    await cdp.inject_helpers()
    await cdp.eval("State.meta.insider = []; State.meta.insiderClaimed = {}; State.saveMeta(); 0", await_promise=False)
    for _ in range(40):
        labels = await cdp.eval("[...document.querySelectorAll('.cs-choices button')].map(b=>b.textContent).join('|')", await_promise=False)
        if labels and ("Nächste Story" in labels):
            break
        await cdp.eval("__pt.advance(null)", await_promise=False)
        await asyncio.sleep(0.15)
    await cdp.eval("__pt.advance('Nächste Story')", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene(max_steps=3)
    n_choices = await cdp.eval("document.querySelectorAll('.cs-choices button').length", await_promise=False)
    record("insider: Story-Ende bietet 3 Upgrades", n_choices == 3, "choices=%s" % n_choices)
    await cdp.screenshot("insider-offer.png")
    await cdp.eval("__pt.advance(null)", await_promise=False)
    await asyncio.sleep(0.5)
    ins = await cdp.eval("JSON.stringify(State.meta.insider)", await_promise=False)
    claimed = await cdp.eval("JSON.stringify(State.meta.insiderClaimed)", await_promise=False)
    record("insider: Wahl in Meta gespeichert, Story-Teil abgehakt", ins is not None and ins != "[]" and claimed is not None and "schuld" in claimed, "insider=%s claimed=%s" % (ins, claimed))
    # Croupier-Auge + Stallbursche im freien Spiel
    await cdp.navigate(URL_BASE + "?fresh&screen=roulette")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.eval("State.meta.insider = ['croupierauge', 'stallbursche', 'mechaniker']; State.saveMeta(); Perks.refreshExcluded(); Roulette.applyExcluded(); 0", await_promise=False)
    await asyncio.sleep(0.3)
    n_ex = await cdp.eval("document.querySelectorAll('.rcell.excluded').length", await_promise=False)
    never = await cdp.eval("(()=>{const ex=State.s.insiderExcluded; for(let i=0;i<200;i++){ if(ex.includes(Rules.rouletteRoll(Math.random, ex))) return false; } return true; })()", await_promise=False)
    record("insider: Croupier-Auge graut 12 Zahlen aus, Kugel faellt nie dorthin", n_ex == 12 and never is True, "excluded=%s never=%s" % (n_ex, never))
    await cdp.screenshot("roulette-croupierauge.png")
    await cdp.eval("UI.show('horses'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    lame = await cdp.eval("(()=>{const r=document.querySelector('.runner.lame'); return r ? parseInt(r.id.slice(2),10) : null})()", await_promise=False)
    sel = await cdp.eval("State.s.selectedHorse", await_promise=False)
    record("insider: Stallbursche markiert ein lahmes Pferd (nicht das gewaehlte)", lame is not None and lame != sel, "lame=%s selected=%s" % (lame, sel))
    await cdp.eval("UI.show('slots'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.eval("State.s.balance = 1000; State.s.mechRespins = 5; State.save(); window.__origRandom = Math.random; Math.random = () => 0.0; 0", await_promise=False)
    # Math.random -> 0 liefert drei 🍒 (Drilling) – für eine Niete andere Werte: 0.05 / 0.4 / 0.8 -> 🍒 🍇 💎
    await cdp.eval("let q=[0.05,0.4,0.8,0.99,0.99]; Math.random = () => q.length ? q.shift() : 0.99; 0", await_promise=False)
    await cdp.click("#btnSpin")
    await asyncio.sleep(2.8)
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    holds = await cdp.eval("[...document.querySelectorAll('.hold-btn')].filter(b=>!b.classList.contains('hidden')).length", await_promise=False)
    record("insider: Mechaniker zeigt nach Niete Festhalten-Buttons", holds == 3, "holds=%s" % holds)
```

`main()`: nach `scenario_roulette_chips(cdp)` → `await scenario_perks(cdp)`.

Hinweise: Der Dev-Parameter `?ending=<id>` startet die Story und springt ans Ende (prüfen: `grep -n "params.get('ending')"`); die Choice-Labels des Endes sind „Nächste Story"/„Zum Titel". Die Slots-Stub-Sequenz prüft `Rules.slotRoll` (`Math.floor(rng()*6)` je Walze) – ggf. Werte anpassen, damit eine Niete entsteht; `slotLuckOverride` zieht bei Glück 0 keinen weiteren Wert.

- [ ] **Step 2: Läufe** – Desktop zweimal, Mobile einmal; Sandbox-Referenzen wegen des Level-Badges erneuern (bewusst, Schwelle unverändert); Screenshots ansehen.

- [ ] **Step 3: Checkliste** – `docs/superpowers/checklist-insider-2026-09-17.md`: je Spec-Zeile (§2.3–2.7, §3.1–3.4) Nachweis.

- [ ] **Step 4: Commit** – `test: Playtest für Skills, Insider-Wahl, Croupier-Auge, Stallbursche, Mechaniker; Screenshots; Checkliste`.

---

## Self-Review

**Spec-Abdeckung:** §2.1/2.2 Felder → T1; §2.3 XP-Quellen/Level → T1 (Regeln), T3 (Vergabe, `story:day` in `Story.night`); §2.4/2.5 Kataloge → T1; §2.6 `mods` → T1; §2.7 Hooks → T2 (Regeln) + T5/T6/T7 (Aufrufstellen); Deckel → T5/T6; §3.1 Badge → T3; §3.2 Screen → T3; §3.3 Insider-Wahl + Titel → T4; §3.4 Spiele → T5/T6, Bar/Post → T7; §4 Blöcke → T1/T3; README → T3; §5 Tests → T1/T2 (Node), T4 (DOM-Fall), T8 (Browser).

**Rulings im Plan:** (a) Gratisdreh des Mechanikers ist kein Spin (kein Escrow/afterSpin/Zinsen); (b) `MOD_STACK` legt Stapelregeln fest (Zinsen add, Frist max, Paar-Multiplikator set – Konflikt Zockerhände/Briefträgerherz ist ohnehin ausgeschlossen); (c) Natural gilt nur bei Sieg mit genau zwei Karten; (d) `skills`-Screen in der Story nie gesperrt.

**Typ-Konsistenz:** `Rules.mods(s, meta)` ↔ `Perks.mods()`; `effectiveInsider(value, bet)` boolean/number in T1/T5/T6; `bjDelta(outcome, bet, mods, ctx)` T2/T6; `rouletteRoll(rng, excluded)` T2/T5/T8; `postmanTier(streak, s, mods)` T2/T7; `Perks.refreshExcluded`, `Roulette.applyExcluded`, `.runner.lame`, `.hold-btn`, `#lvBadge`, `#skillCards .btn`, `.skill-card .reason` in T3–T8 identisch.
