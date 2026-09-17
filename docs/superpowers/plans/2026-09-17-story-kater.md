# Story 2 „Der Kater" – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die zweite Story „Der Kater" (Fortsetzung von „Die Schuld", 30 Tage, Alkohol-Schleife, Drogen-Schalter, Kauf des Kellers, sechs Enden) als Datenobjekt `STORY_KATER` plus die wenigen generischen Engine-Ergänzungen, die dafür noch fehlen.

**Architecture:** `STORY_KATER` lebt in einem eigenen Block `<script id="story-kater">` nach `story-schuld`, im selben Format. Alle Mechanik (Pegel, Leber, Deckel, Zitter-Tag, Sucht, Therapie, Kauf) ist als Events/Effekte auf den Hooks aus Plan 1 formuliert; die Engine bekommt nur noch vier generische Effekte (`set`, `lock`, `achievement`, `unlockJobs` ist bereits `unlock`), Story-Aktionen in der Seitenleiste (`story.actions`), Rohwerte im Szenen-Kontext (`ctx.raw`) und Story-Trophäen (`story.trophies`). Reine Logik in `StoryRules`, testbar in Node.

**Tech Stack:** Vanilla JS in `keller37.html`; Selbsttest (Node + Chrome); `tests/playtest-story.py` (CDP).

**Spec:** `docs/superpowers/specs/2026-09-17-story-kater-design.md` (alle Abschnitte außer 7).

**Voraussetzungen:** Plan 1 (`2026-09-17-story-engine-2.md`) und Plan 2 (`2026-09-17-casino-royal.md`) sind umgesetzt. Verwendete Namen daraus: `requires`, `prevEnding`, `s.story.prev`, Hooks `sleep`/`buy:beer`/`buy:brownie`/`buy:kidney`/`buy:therapy`/`royal:enter`/`royal:guest`, Effekte `luckMod`/`jobMod`/`price`/`enable`/`disable`, `hud[].label` als Funktion, `immediate`-Enden, `gates`, Raum `royal`, `StoryRules.price`, `Story.hook`, Stats `beers`/`brownies`/`biggestWin`.

## Global Constraints

- Ein-Datei-Vorgabe; neuer Block `story-kater` (Node-Testliste in `tests/run-selftest.mjs` um `'story-kater'` nach `'story-schuld'` erweitern).
- Alle Zahlen im Story-Objekt (`prices`, Leber-Raten, Kaufpreis) – keine neuen `Rules`-Konstanten.
- Keine Story-2-Bezeichner in der Engine; alle Engine-Ergänzungen generisch und einzeln getestet.
- Szenen-IDs mit Präfix `kater.`; Charaktere nur aus `CAST` (wirt, chantal, vito, igor, doc, krause, kevin, sylvie, du, makler, schmalz); Hintergründe nur aus den vorhandenen (`bar, hinterzimmer, standesamt, villa, hafen, hafen-morgen, klinik, bank, strasse, keller, autohaus, intersport, gasse, royal`).
- Vor jedem Commit `node tests/run-selftest.mjs` grün; vor dem letzten Commit `tests/dom-selftest.sh` und `python3 tests/playtest-story.py` (Playtest nur ohne parallele Chrome-/Agent-Last laufen lassen – die Taxi-Schicht ist lastempfindlich; ein TIMEOUT bei `taxi: Schicht abgeschlossen` ist ein bekannter Flake → einmal wiederholen).
- Commit-Messages enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## Dateistruktur

| Ort | Inhalt |
|---|---|
| Block `story-rules` | Effekte `set` (Whitelist), `lock`, `achievement`; `validate` (actions, trophies, set-Keys) |
| Block `story-engine` | `Story.ctx` mit `raw`, `Story.action(id)`, `applyEffects` verarbeitet `achievement`; `story:ended` → `story.trophies`, `alleEnden` generisch |
| Block `ui` (`renderSide`) | Story-Aktionen als Buttons in der Sektion ihres Raums |
| Block `jobs` | `Jobs.POOL.filialleiter` |
| Block `achievements` | DEFS `endeWirt`, `endeNuechtern`, `endeBrownie`, `endeBett`, `standhaft`, `hausherr` |
| Block `story-kater` (neu) | `STORY_KATER` (Definition, Szenen, Events, Enden) |
| Block `selftest` | Tests für Effekte/Aktionen und für die Story-Logik |
| `tests/run-selftest.mjs`, `tests/playtest-story.py` | Blockliste; Szenario `scenario_kater` |
| `README.md` | Story-2-Absatz, Dev-Parameter |

---

### Task 1: Engine – Effekte `set`/`lock`/`achievement`, `story.actions`, `ctx.raw`, `story.trophies`

**Files:**
- Modify: Block `story-rules` (`applyEffect`, `validate`, neu `SET_KEYS`, `actionsFor`), Block `story-engine` (`ctx`, `action`, `applyEffects`, `story:ended`-Listener → verschieben aus `achievements`), Block `ui` (`renderSide`), Block `achievements` (`Bus.on('story:ended')` anpassen)
- Test: Block `selftest`

**Interfaces (Produces):**
```js
// Effekte
{ set: { car: 'mercC', hasHouse: true } }      // nur Keys aus StoryRules.SET_KEYS
{ lock: { jobs: ['filialleiter'], rooms: ['royal'], doors: [] } }
{ achievement: 'standhaft' }                   // Story.applyEffects → Achievements.unlock
// Story-Felder
actions: [{ id: 'kauf', room: 'bar', label: '🔑 Über den Keller reden', when: cond, scene: 'kater.kauf' }]
trophies: { wirt: 'endeWirt', … }             // endingId → achievementId
// Engine
StoryRules.SET_KEYS = ['car', 'shoes', 'hasHouse', 'hasDealer', 'kidneySold']
StoryRules.actionsFor(story, s, room) → [action]     // nur mit erfüllter Bedingung
Story.action(id) → Promise                            // spielt action.scene, wendet Choice-Effekte an, prüft immediate-Enden
Story.ctx(extra) enthält raw: { balance, day, vars: {…}, flags: {…} } und prev (= s.story.prev)
```

- [ ] **Step 1: Failing Tests**

```js
T.test('StoryRules.applyEffect: set (Whitelist), lock, achievement', () => {
  const s = Object.assign(base({ car: 'audiA3', hasHouse: true }), { story: StoryRules.freshStoryPart(STORY_PROBE) });
  StoryRules.applyEffect(s, { set: { car: null, hasHouse: false } }, STORY_PROBE);
  T.eq([s.car, s.hasHouse], [null, false]);
  T.throws(() => StoryRules.applyEffect(s, { set: { balance: 9 } }, STORY_PROBE), 'balance ist nicht erlaubt');
  s.story.unlocked = { jobs: ['spueler', 'post'], doors: ['slots'], rooms: ['bar', 'royal'] };
  StoryRules.applyEffect(s, { lock: { jobs: ['post'], rooms: ['royal'] } }, STORY_PROBE);
  T.eq(s.story.unlocked, { jobs: ['spueler'], doors: ['slots'], rooms: ['bar'] });
  T.eq(StoryRules.applyEffect(s, { achievement: 'x' }, STORY_PROBE), { achievement: 'x' }, 'wird an die Engine gemeldet');
});
T.test('StoryRules.actionsFor: Aktionen je Raum mit Bedingung', () => {
  const st = Object.assign({}, STORY_PROBE, { actions: [
    { id: 'a', room: 'bar', label: 'A', when: { var: 'mut', gte: 1 }, scene: 'probe.n1' },
    { id: 'b', room: 'bar', label: 'B', scene: 'probe.n1' },
    { id: 'c', room: 'doc', label: 'C', scene: 'probe.n1' },
  ] });
  const s = Object.assign(base(), { story: StoryRules.freshStoryPart(st) });
  T.eq(StoryRules.actionsFor(st, s, 'bar').map((a) => a.id), ['b']);
  s.story.vars.mut = 1;
  T.eq(StoryRules.actionsFor(st, s, 'bar').map((a) => a.id), ['a', 'b']);
  T.eq(StoryRules.actionsFor(st, s, 'doc').map((a) => a.id), ['c']);
  T.eq(StoryRules.actionsFor(STORY_PROBE, s, 'bar'), []);
});
T.test('StoryRules.validate: actions und trophies und set-Keys', () => {
  const bad = Object.assign({}, STORY_PROBE, { id: 'x',
    actions: [{ id: 'a', room: 'nirgends', label: 'A', scene: 'fehlt' }],
    trophies: { gibtsnicht: 'endeX' },
    events: [{ id: 'e', at: 'night', effects: [{ set: { balance: 1 } }] }] });
  T.eq(StoryRules.validate(bad, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']), [
    'x: Szene "fehlt" fehlt (action a)', 'x: Raum "nirgends" unbekannt (action a)', 'x: set-Key "balance" nicht erlaubt (e)', 'x: Trophäe für unbekanntes Ende "gibtsnicht"',
  ]);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL (`Ungültiger Effekt`, `actionsFor` undefined).

- [ ] **Step 3: Implementieren**

`StoryRules`:

```js
  SET_KEYS: ['car', 'shoes', 'hasHouse', 'hasDealer', 'kidneySold'],
  actionsFor(story, s, room) { return (story.actions || []).filter((a) => a.room === room && StoryRules.check(a.when, s)); },
```

In `applyEffect`, vor dem abschließenden `throw`:

```js
    if ('set' in eff) { for (const [k, v] of Object.entries(eff.set)) { if (!StoryRules.SET_KEYS.includes(k)) throw new Error(`set-Key "${k}" nicht erlaubt`); s[k] = v; } return {}; }
    if ('lock' in eff) { for (const k of ['jobs', 'doors', 'rooms']) if (eff.lock[k]) st.unlocked[k] = st.unlocked[k].filter((x) => !eff.lock[k].includes(x)); return {}; }
    if ('achievement' in eff) return { achievement: eff.achievement };
```

In `validate` (vor `return errs`):

```js
    for (const a of story.actions || []) { scene(a.scene, `action ${a.id}`); if (!StoryRules.ROOMS.includes(a.room)) errs.push(`${story.id}: Raum "${a.room}" unbekannt (action ${a.id})`); }
    const setKeys = (list, where) => (list || []).forEach((eff) => { if (eff.set) for (const k of Object.keys(eff.set)) if (!StoryRules.SET_KEYS.includes(k)) errs.push(`${story.id}: set-Key "${k}" nicht erlaubt (${where})`); });
    for (const e of story.events || []) setKeys(e.effects, e.id);
    for (const [end] of Object.entries(story.trophies || {})) if (!(story.endings || []).some((e) => e.id === end)) errs.push(`${story.id}: Trophäe für unbekanntes Ende "${end}"`);
```

Reihenfolge der Fehlermeldungen wie im Test: Szene vor Raum (beide in der `actions`-Schleife), dann `set`, dann Trophäen – die `actions`-Schleife also **vor** der Trophäen-Prüfung und nach den bestehenden Event-Prüfungen platzieren, und die `setKeys`-Prüfung direkt dahinter.

`Story` (Block `story-engine`):
- `ctx(extra)`: vor `return Object.assign(c, extra);` → `c.raw = { balance: s.balance, day: this.s.day, vars: Object.assign({}, this.s.vars), flags: Object.assign({}, this.s.flags) }; c.prev = this.s.prev || {};`
- `applyEffects`: nach `const out = …` → `if (out.achievement && typeof Achievements !== 'undefined') Achievements.unlock(out.achievement);`
- `Story.enter`, Fortsetzungspfad (der Zweig nach `State.setMode('story')` mit `if (st.phase === 'morning') await this.morning(); else await this.evening();`): vor dem abschließenden `UI.toast({ icon: '📖', … Tag ${this.s.day} … })` und vor dem `?job=`-Zweig `if (this.stale(st)) return;` einfügen – ein sofortiges Ende in einem Morgen-Event darf den Toast/`Jobs.take` nicht mehr auf `undefined` laufen lassen (Residuum der Plan-1-Review). Ebenso in `forceDuel` nach dem Duell-Await: `const st = this.s;` vorher merken und `if (this.stale(st)) return victim;` vor dem Flag-Schreiben.
- Gate-Szene (Spec §7 „Türsteher-Panel“ statt nur Toast): Gate-Einträge dürfen `scene: '<sceneId>'` tragen. `StoryRules.gateEntry(story, s, screen)` liefert den ersten zutreffenden Eintrag (oder null); `gate()` bleibt die Text-Variante darauf aufgebaut. In `Royal.enter` (Block `casino-royal`) den Zweig `if (this.inStory() && Story.isLocked('royal'))` so erweitern: `const g = StoryRules.gateEntry(Story.story, State.s, 'royal'); if (g && g.scene) { await Story.playScene(g.scene); return; }` vor dem Toast. `validate` prüft `scene` von Gates wie andere Szenen-Referenzen (`scene(g.scene, \`gate ${screen}[${i}]\`)`). Test: `StoryRules.gateEntry` liefert den Eintrag mit `scene`, `validate` meldet fehlende Gate-Szene.
- Neu:

```js
  async action(id) {
    const a = (this.story.actions || []).find((x) => x.id === id);
    if (!a || !StoryRules.check(a.when, State.s) || Cutscene.active || Game.inFlight > 0) return;
    await this.playScene(a.scene);
    await this.checkImmediate();
    UI.renderSide(); this.renderDaybar();
  },
```

Block `ui`, `renderSide`: nach der Definition von `secs` eine Helferfunktion und in jeder Raum-Sektion die Aktionen anhängen. Konkret: `const acts = (r) => inStory ? StoryRules.actionsFor(Story.story, s, r).map((a) => h('button', { class: 'side-btn story-action', 'data-story-action': a.id }, h('span', {}, a.label))) : [];` und in der Bar-Sektion `secs.push(sec('Die Bar', btn(…Bier…), btn(…Brownie…), ...acts('bar'), h('p', …)))`; für `doc`/`bank`/`life`/`stadt` analog `...acts('doc')` usw. in die jeweilige Sektion (bei `hz` → `hz.push(...acts('doc'), ...acts('bank'))`). Klick-Handler (dort, wo `data-action` ausgewertet wird): `const sa = e.target.closest('[data-story-action]'); if (sa) { SFX.play('click'); return Story.action(sa.dataset.storyAction); }`.

Block `achievements`, den Listener ersetzen:

```js
Bus.on('story:ended', ({ id, ending }) => {
  const st = typeof Stories !== 'undefined' ? Stories.get(id) : null;
  const map = Object.assign({ ehrlich: 'endeEhrlich', taxi: 'endeTaxi', sturz: 'endeSturz' }, st && st.trophies);
  if (map[ending]) Achievements.unlock(map[ending]);
  const run = State.meta.storyRuns[id];
  const total = st ? st.endings.length : 4;
  if (run && run.endings.length >= total) Achievements.unlock('alleEnden');
});
```

(`alleEnden`-Beschreibung in DEFS auf „Alle Enden einer Story gesehen." ändern.)

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen. Run: `tests/dom-selftest.sh` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Effekte set/lock/achievement, Story-Aktionen in der Seitenleiste, ctx.raw, Story-Trophäen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Job „Filialleiter", Trophäen-DEFS, Story-Skelett `STORY_KATER` (Definition ohne Szenentexte), Validierung

**Files:**
- Modify: Block `jobs` (`POOL`), Block `achievements` (`DEFS`), `tests/run-selftest.mjs`
- Create: Block `<script id="story-kater">` nach `story-schuld`
- Test: Block `selftest`

**Interfaces (Produces):** `STORY_KATER` mit allen Feldern außer Szenentexten (die kommen in Task 3–8; bis dahin Platzhalter-Szenen mit einem Panel, damit `validate` grün ist – **jede** Szene wird in den Folgetasks ersetzt, die Liste in Task 9 prüft das).

- [ ] **Step 1: Failing Test**

```js
/* ---- Story 2: Der Kater ---- */
const KATER_JOBS = ['spueler', 'post', 'taxi', 'tuersteher', 'croupier', 'eintreiber', 'filialleiter'];
const katerState = (o = {}, prev = { schuld: 'ehrlich' }) => {
  const s = Object.assign(base({ balance: 2000, car: 'mercC', hasHouse: true, flags: {} }), { story: StoryRules.freshStoryPart(STORY_KATER, { schuld: { lastPlayed: 1, endings: [prev.schuld], last: prev.schuld } }) }, o);
  return s;
};
/* Events eines Hooks wie die Engine anwenden (Szenen ohne Wahl), gibt die Event-IDs zurück */
const runHook = (s, at) => {
  const ids = [];
  for (const e of StoryRules.dueEvents(STORY_KATER, s, at)) {
    ids.push(e.id);
    for (const eff of e.effects || []) StoryRules.applyEffect(s, eff, STORY_KATER);
    if (e.once) s.story.seen.push(e.id);
  }
  return ids;
};
T.test('STORY_KATER ist gültig und setzt Die Schuld voraus', () => {
  T.eq(StoryRules.validate(STORY_KATER, Object.keys(STORY_KATER.scenes), KATER_JOBS, ['probe', 'schuld', 'kater']), []);
  T.eq(STORY_KATER.requires, 'schuld'); T.eq(STORY_KATER.days, 30);
  T.eq(STORY_KATER.endings.length, 6);
  T.eq(STORY_KATER.endings.filter((e) => e.fallback).map((e) => e.id), ['stammgast']);
  T.eq(STORY_KATER.endings.find((e) => e.id === 'bett').immediate, true);
  T.eq(STORY_KATER.endings.find((e) => e.id === 'wirt').immediate, true);
  T.eq(Object.keys(STORY_KATER.trophies).sort(), ['bett', 'brownie', 'nuechtern', 'wirt']);
});
T.test('STORY_KATER: Start – Flitterwochen', () => {
  const s = katerState();
  T.eq(s.story.vars, { pegel: 0, leber: 100, deckel: 0, bierHeute: 0, brownieHeute: 0, docNein: 0 });
  T.eq(s.story.unlocked.jobs, ['filialleiter']);
  T.eq(s.story.unlocked.doors, ['roulette', 'slots', 'horses', 'russian', 'blackjack']);
  T.eq(s.story.unlocked.rooms, ['bar', 'doc', 'bank', 'invest', 'life', 'stadt', 'royal']);
  T.eq(s.story.prices, { brownie: 1000, therapy: 5000 });
  T.eq(s.story.disabled, ['tinder', 'house', 'dealer']);
  T.eq(StoryRules.chapterFor(STORY_KATER, s).id, 'k1');
});
T.test('STORY_KATER: Kapitelgrenzen 4/11/21', () => {
  const s = katerState();
  for (const [day, id] of [[3, 'k1'], [4, 'k2'], [10, 'k2'], [11, 'k3'], [20, 'k3'], [21, 'k4'], [30, 'k4']]) { s.story.day = day; T.eq(StoryRules.chapterFor(STORY_KATER, s).id, id, `Tag ${day}`); }
});
T.test('Jobs: filialleiter im Pool', () => {
  T.eq(typeof Jobs === 'undefined' || (Jobs.POOL.filialleiter && Jobs.POOL.filialleiter.base), typeof Jobs === 'undefined' ? true : 400);
});
```

(`Jobs` ist im Node-Test nicht geladen – der letzte Test ist nur im Browser scharf.)

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → `STORY_KATER is not defined`.

- [ ] **Step 3: Implementieren**

`tests/run-selftest.mjs`: `'story-kater'` nach `'story-schuld'`.

Block `jobs`, `POOL`:

```js
    filialleiter: { id: 'filialleiter', name: 'Filialleiter bei Krause', icon: '🏦', kind: 'shift', base: 400, desc: 'Anzug, Schlüssel, Unterschriftenmappe. Ihre Frau ruft öfter an.', pay: '400 €' },
```

Block `achievements`, `DEFS`:

```js
    { id: 'endeWirt', title: 'Hausherr', icon: '🔑', desc: 'Den Keller vom Wirt gekauft.', group: 'story' },
    { id: 'endeNuechtern', title: 'Nüchtern', icon: '🌅', desc: 'Am Keller vorbeigegangen.', group: 'story' },
    { id: 'endeBrownie', title: 'Der Brownie', icon: '💊', desc: 'Der Doc hat einen Partner.', group: 'story' },
    { id: 'endeBett', title: 'Das Bett beim Doc', icon: '🛏️', desc: 'Die Niere war ein Vorschuss.', group: 'story' },
    { id: 'standhaft', title: 'Standhaft', icon: '🙅', desc: 'Dem Doc dreimal Nein gesagt.', group: 'story' },
```

Neuer Block (Skelett; Szenen-Objekte hier zunächst mit `[{ bg: 'bar', who: 'wirt', mood: 'calm', text: 'TODO' }]` – werden in Task 3–8 ersetzt; Task 9 prüft, dass kein `TODO` mehr existiert):

```html
<script id="story-kater">
/* ================= STORY 2: DER KATER – Fortsetzung von „Die Schuld" ================= */
const STORY_KATER = {
  id: 'kater', title: 'Der Kater', days: 30, requires: 'schuld',
  start: {
    balance: 2000,
    unlocked: { jobs: ['filialleiter'], doors: ['roulette', 'slots', 'horses', 'russian', 'blackjack'], rooms: ['bar', 'doc', 'bank', 'invest', 'life', 'stadt', 'royal'] },
    vars: { pegel: 0, leber: 100, deckel: 0, bierHeute: 0, brownieHeute: 0, docNein: 0 },
  },
  varMax: { pegel: 3, leber: 100 },
  prices: { brownie: 1000, therapy: 5000 },
  disabled: ['tinder', 'house', 'dealer'],
  /* Zahlen der Schleife – an einer Stelle */
  N: { kaufpreis: 40000, buecherRabatt: 5000, freibier: 50, bedarf: 3, leberBier: 1, leberBrownie: 4, leberEntzug: 2, leberEntzugSucht: 4, leberNiere: 20, leberWarnung: 30, brownieSucht: 300, therapieSucht: 8000, chantalGeld: 15000, leberDoc: 70, luckZitter: -15, jobZitter: { spuelerZone: 0.7, taxiBrakeDelay: 150, postTime: 0.75, shiftPay: 0.5 } },
  hud: [
    { var: 'leber', label: '🫀 Leber', max: 100, tone: 'danger' },
    { var: 'pegel', label: (s) => (s.story.flags.sucht ? '💊 Pegel' : '🍺 Pegel'), max: 3 },
    { var: 'deckel', label: '🧾 Deckel', fmt: 'money' },
  ],
  goal: (s) => (s.story.flags.gekauft ? 'Der Keller gehört dir.' : s.story.flags.abgestuerzt ? `Ziel: Keller ${UI.fmt(STORY_KATER.N.kaufpreis + (s.story.vars.deckel || 0))} bis Tag 30` : 'Flitterwochen. Genieß es.'),
  lockReason: { royal: 'Parkservice only' },
  gates: { royal: [{ when: { flag: 'zitter' }, text: 'Sie zittern. Wir haben eine Hausordnung.', scene: 'kater.royal.zitter' }] },
  intro: 'kater.intro',
  scenes: { /* Task 3–8 */ },
  chapters: [
    { id: 'k1', title: 'Flitterwochen', when: { day: { gte: 1 } } },
    { id: 'k2', title: 'Der Morgen danach', when: { day: { gte: 4 } }, intro: 'kater.k2', unlock: { jobs: ['spueler', 'post', 'taxi'] } },
    { id: 'k3', title: 'Der Wagen', when: { day: { gte: 11 } }, intro: 'kater.k3', unlock: { jobs: ['tuersteher', 'croupier'], rooms: ['royal'] } },
    { id: 'k4', title: 'Letzte Runde', when: { day: { gte: 21 } }, intro: 'kater.k4' },
  ],
  events: [ /* Task 4–8 */ ],
  actions: [ /* Task 7 */ ],
  jobScenes: { /* Task 6 */ },
  jobEffects: { /* Task 6 */ },
  endings: [
    { id: 'bett', title: 'Das Bett beim Doc', priority: 60, immediate: true, when: { var: 'leber', lte: 0 }, scene: 'kater.ende.bett' },
    { id: 'wirt', title: 'Der Wirt', priority: 50, immediate: true, when: { flag: 'gekauft' }, scene: 'kater.ende.wirt' },
    { id: 'nuechtern', title: 'Nüchtern', priority: 40, when: { all: [{ flag: 'nuechtern' }, { day: { gte: 30 } }] }, scene: 'kater.ende.nuechtern' },
    { id: 'brownie', title: 'Der Brownie', priority: 30, when: { all: [{ flag: 'sucht' }, { var: 'leber', lte: 15 }, { day: { gte: 30 } }] }, scene: 'kater.ende.brownie' },
    { id: 'taxi', title: 'Chantals Taxi', priority: 20, when: { all: [{ flag: 'chantalZurueck' }, { balance: { gte: 15000 } }, { day: { gte: 30 } }] }, scene: 'kater.ende.taxi' },
    { id: 'stammgast', title: 'Der Stammgast', priority: 0, scene: 'kater.ende.stammgast', fallback: true },
  ],
  trophies: { wirt: 'endeWirt', nuechtern: 'endeNuechtern', brownie: 'endeBrownie', bett: 'endeBett' },
};
if (typeof Stories !== 'undefined') Stories.define(STORY_KATER);
</script>
```

Hinweis zu `day: { gte: 30 }` in den Tag-30-Enden: Die Engine prüft Enden nachts **vor** `advanceDay` (Tag 30 → Nacht 30) und danach (Tag 31). Nacht 30 mit `day = 30` erfüllt `gte: 30` → das Ende spielt in der Nacht des 30. Tages; das Fallback greift bei `day > days`. Beides passt zur Spec „Tag 30: Abrechnung".

`leber` mit `varMax: 100` – `applyEffect` klemmt `add` nach oben auf 100 und nach unten auf 0 ✓ (Story-1-Verhalten). `pegel` klemmt auf 3.

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs` → alle grün außer evtl. Szenen-Validierung (Skelett-Szenen müssen für `intro`, Kapitel-Intros und Enden existieren – im Skelett anlegen: `kater.intro`, `kater.k2`, `kater.k3`, `kater.k4`, `kater.ende.bett`, `kater.ende.wirt`, `kater.ende.nuechtern`, `kater.ende.brownie`, `kater.ende.taxi`, `kater.ende.stammgast` mit `TODO`-Panel; zusätzlich `kater.royal.zitter`, weil das Gate darauf zeigt).

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(story): Skelett Story 2 „Der Kater", Job Filialleiter, Enden-Trophäen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Intro-Varianten, Hochzeit, Flitterwochen (Kapitel 1), Absturz (Nacht 3)

**Files:** Block `story-kater` (`scenes`, `events`) · Test: Block `selftest`

- [ ] **Step 1: Failing Tests**

```js
T.test('STORY_KATER: Tag-1-Morgen richtet Villa, Auto ein; Doc-Ende startet mit Leber 70', () => {
  const s = katerState({ car: null, hasHouse: false });
  T.eq(runHook(s, 'morning'), ['einrichten']);
  T.eq([s.car, s.hasHouse, s.story.vars.leber], ['mercC', true, 100]);
  const d = katerState({ car: null, hasHouse: false }, { schuld: 'doc' });
  T.eq(runHook(d, 'morning'), ['einrichten', 'niereWeg']);
  T.eq(d.story.vars.leber, 70);
});
T.test('STORY_KATER: Absturz in Nacht 3', () => {
  const s = katerState({ balance: 3500 });
  s.story.day = 3; s.story.seen.push('einrichten');
  T.eq(runHook(s, 'night'), ['absturz']);
  T.eq([s.balance, s.car, s.hasHouse], [0, null, false]);
  T.eq(s.story.flags.abgestuerzt, true);
  T.eq(s.story.unlocked.jobs, []);
  T.eq(s.story.unlocked.rooms, ['bar', 'doc', 'bank', 'invest', 'life', 'stadt'], 'Royal gesperrt bis Kapitel 3');
  s.story.day = 4;
  T.eq(runHook(s, 'night').includes('absturz'), false, 'einmalig');
});
T.test('STORY_KATER: Intro-Szene je vorigem Ende', () => {
  for (const prev of ['ehrlich', 'sturz', 'taxi', 'doc']) {
    const s = katerState({}, { schuld: prev });
    const panels = STORY_KATER.scenes['kater.intro']({ raw: { flags: {}, vars: {} }, prev: s.story.prev });
    T.ok(panels.length >= 4, `${prev}: Variante + Hochzeit`);
    T.eq(panels[panels.length - 1].bg, 'standesamt', `${prev}: endet im Standesamt`);
  }
});
```

Die Intro-Funktion liest `ctx.prev` (Task 1).

- [ ] **Step 2: Fehlschlag sehen** – Run: `node tests/run-selftest.mjs`.

- [ ] **Step 3: Implementieren**

`scenes` (ersetzen der Skelett-Einträge `kater.intro`, `kater.k2` bleibt für Task 4):

```js
    'kater.intro': (ctx) => {
      const prev = (ctx.prev || {}).schuld || 'ehrlich';
      const start = {
        ehrlich: [
          { bg: 'bank', who: 'krause', mood: 'happy', text: 'Fünfzigtausend zurückgezahlt, auf den Cent. Ein Mann, der das kann, kann eine Filiale führen. Willkommen im Team.' },
          { bg: 'strasse', who: 'chantal', mood: 'happy', text: 'Ich hab vor der Bank gewartet. Zwei Stunden. Für dich wäre ich auch drei geblieben. Fast.' },
        ],
        sturz: [
          { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Der Keller läuft. Igor an der Tür, du am Kessel. Vito? Irgendwo, wo es keine Auslieferung gibt.' },
          { bg: 'bar', who: 'wirt', mood: 'happy', text: 'Krause sucht einen Filialleiter. Ich hab dich empfohlen. Heirate, kauf ein Auto, werd langweilig. Ich hab\'s auch überlebt.' },
        ],
        taxi: [
          { bg: 'hafen-morgen', who: 'du', mood: 'calm', text: 'Ein Jahr. Neuer Name, Zahnarztpapiere, kein Zahnarzt. Die Fähre legt an. Das Handy vibriert: „Ich habe Zeit. – V."' },
          { bg: 'strasse', who: 'chantal', mood: 'happy', text: 'Rutsch rüber. Ich bin dieselbe Fähre gefahren, du hast nur nicht nach hinten geguckt. Krause hat einen Job für dich.' },
        ],
        doc: [
          { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Wach? Eine Niere weniger, ein Zettel weniger. Vito ist zufrieden. Die Naht hält, meistens.' },
          { bg: 'klinik', who: 'chantal', mood: 'calm', text: 'Sie ist die ganze Nacht geblieben. Das hat noch keine. Krause war auch da – er hat einen Job für dich.' },
        ],
      }[prev];
      return start.concat([
        { bg: 'standesamt', who: 'chantal', mood: 'happy', text: 'Ja. Natürlich ja. Ich hab die Vollmacht schon vorbereitet – für die Flitterwochen, Schatz. Man muss ja an alles denken.' },
        { bg: 'standesamt', who: 'schmalz', mood: 'calm', text: 'Kraft des mir verliehenen Amtes. Gütertrennung? Nein? Wie Sie meinen. Unterschreiben Sie da, da und da.' },
        { bg: 'villa', who: 'du', mood: 'happy', text: 'Villa mit Hafenblick, Mercedes vor der Tür, Filialleiter bei Krause. Dreißig Tage. Was soll schon passieren.' },
      ]);
    },
    'kater.absturz': [
      { bg: 'villa', who: 'du', mood: 'shock', text: 'Der Wecker ist weg. Das Bett ist weg. Der Zettel auf dem Boden: „Danke für alles. Wirklich alles. – C.-M."' },
      { bg: 'bank', who: 'krause', mood: 'calm', text: 'Ihre Frau hat die Vollmacht genutzt. Konto, Wagen, Villa – alles rechtens. Und die Filiale… Sie verstehen, das Vertrauen.' },
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Setz dich. Das erste geht aufs Haus. Das zweite auch, ich schreib\'s an. Du siehst aus, als bräuchtest du drei.' },
    ],
```

`events` (Anfang der Liste):

```js
    { id: 'einrichten', when: { day: { eq: 1 } }, once: true, at: 'morning', effects: [{ set: { car: 'mercC', hasHouse: true } }] },
    { id: 'niereWeg', when: { all: [{ day: { eq: 1 } }, { prevEnding: { story: 'schuld', id: 'doc' } }] }, once: true, at: 'morning', effects: [{ var: 'leber', set: 70 }, { set: { kidneySold: true } }] },
    { id: 'absturz', when: { day: { eq: 3 } }, once: true, at: 'night', scene: 'kater.absturz',
      effects: [{ balancePct: -100, min: 0 }, { set: { car: null, hasHouse: false } }, { lock: { jobs: ['filialleiter'], rooms: ['royal'] } }, { flag: 'abgestuerzt' }, { price: { beer: 0 } }] },
```

`kidneySold: true` nach dem Doc-Ende bringt die bestehenden Meds-Kosten pro Spin (20 €) mit – konsistent mit Story 1.

`{ balancePct: -100, min: 0 }`: laut `applyEffect` „Abzug mindestens `min`, nie mehr als der Kontostand" → Konto 0 ✓ (Test in Story 1: `balancePct −20, min 100`).

- [ ] **Step 4: Tests** – Run: `node tests/run-selftest.mjs` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(kater): Intro-Varianten je Story-1-Ende, Hochzeit, Absturz in Nacht 3

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Alkohol-Schleife – Freibier/Deckel, Pegel, Entzugsnacht, Zitter-Tag, Leber, Warnung, Kapitel-2-Intro

**Files:** Block `story-kater` · Test: Block `selftest`

- [ ] **Step 1: Failing Tests**

```js
const katerDay = (day, extra = {}) => { const s = katerState({ balance: 200, car: null, hasHouse: false }); s.story.day = day; s.story.flags.abgestuerzt = true; s.story.seen.push('einrichten', 'absturz'); s.story.unlocked.rooms = ['bar', 'doc', 'bank', 'invest', 'life', 'stadt']; Object.assign(s.story.flags, extra); return s; };
T.test('STORY_KATER: Freibier morgens, Deckel beim ersten Bier, danach 50 €', () => {
  const s = katerDay(5);
  runHook(s, 'morning');
  T.eq(StoryRules.price(s, 'beer'), 0, 'erstes Bier des Tages umsonst');
  runHook(s, 'buy:beer');
  T.eq([s.story.vars.deckel, s.story.vars.bierHeute, s.story.vars.pegel, s.story.vars.leber], [50, 1, 1, 99]);
  T.eq(StoryRules.price(s, 'beer'), 50);
  runHook(s, 'buy:beer'); runHook(s, 'buy:beer'); runHook(s, 'buy:beer');
  T.eq([s.story.vars.deckel, s.story.vars.bierHeute, s.story.vars.pegel, s.story.vars.leber], [50, 4, 3, 96], 'Bier 4: Pegel bleibt 3, Leber zahlt');
});
T.test('STORY_KATER: Entzugsnacht → Zitter-Tag → erstes Bier hebt ihn auf', () => {
  const s = katerDay(5);
  runHook(s, 'morning'); runHook(s, 'buy:beer'); runHook(s, 'buy:beer');
  const ids = runHook(s, 'sleep');
  T.ok(ids.includes('entzug') && ids.includes('entzugSzene'), ids.join());
  T.eq(s.story.vars.leber, 96, '98 − 2 Entzug');
  T.eq(s.story.flags.zitter, true); T.eq(s.story.luckMod, -15); T.eq(StoryRules.jobMod(s).shiftPay, 0.5);
  T.eq(s.story.vars.pegel, 0, 'Pegel nachts zurückgesetzt'); T.eq(s.story.vars.bierHeute, 0);
  T.eq(StoryRules.gate(STORY_KATER, s, 'royal'), 'Sie zittern. Wir haben eine Hausordnung.');
  s.story.day = 6; runHook(s, 'morning');
  T.eq(runHook(s, 'buy:beer').includes('zitterEnde'), true);
  T.eq([s.story.flags.zitter, s.story.luckMod, StoryRules.jobMod(s)], [false, 0, {}]);
  T.eq(StoryRules.gate(STORY_KATER, s, 'royal'), null);
  runHook(s, 'buy:beer'); runHook(s, 'buy:beer');
  const n2 = runHook(s, 'sleep');
  T.ok(!n2.includes('entzug'), 'drei Bier → kein Entzug');
  T.ok(!n2.includes('entzugSzene'), 'Szene nur beim ersten Mal');
});
T.test('STORY_KATER: Leber-Rechnung 27 Tage Minimum = 19; Warnung bei ≤ 30; Niere −20', () => {
  const s = katerDay(4);
  for (let d = 4; d <= 30; d++) { s.story.day = d; runHook(s, 'morning'); runHook(s, 'buy:beer'); runHook(s, 'buy:beer'); runHook(s, 'buy:beer'); runHook(s, 'night'); runHook(s, 'sleep'); }
  T.eq(s.story.vars.leber, 19);
  T.ok(s.story.seen.includes('leberWarnung'), 'Warnszene kam');
  const k = katerDay(5); runHook(k, 'buy:kidney'); T.eq(k.story.vars.leber, 80);
});
T.test('STORY_KATER: Ende „Bett" ist sofort, wenn Leber 0', () => {
  const s = katerDay(12); s.story.vars.leber = 1; runHook(s, 'morning'); runHook(s, 'buy:beer');
  T.eq(s.story.vars.leber, 0);
  T.eq(StoryRules.ending(STORY_KATER, s, { immediateOnly: true }).id, 'bett');
});
```

- [ ] **Step 2: Fehlschlag sehen** – Run: `node tests/run-selftest.mjs`.

- [ ] **Step 3: Implementieren**

`events` (hinter `absturz`; Reihenfolge ist relevant – `dueEvents` liefert in Definitionsreihenfolge):

```js
    /* ---- Tagesbeginn: erstes Bier umsonst ---- */
    { id: 'freibier', when: { all: [{ flag: 'abgestuerzt' }, { notFlag: 'nuechtern' }] }, at: 'morning', effects: [{ price: { beer: 0 } }, { var: 'bierHeute', set: 0 }, { var: 'brownieHeute', set: 0 }] },
    /* ---- Bierkauf ---- */
    { id: 'deckel', when: { all: [{ flag: 'abgestuerzt' }, { var: 'bierHeute', eq: 0 }] }, at: 'buy:beer', effects: [{ var: 'deckel', add: 50 }, { price: { beer: 50 } }] },
    { id: 'bier', when: { flag: 'abgestuerzt' }, at: 'buy:beer', effects: [{ var: 'bierHeute', add: 1 }, { var: 'pegel', add: 1 }, { var: 'leber', add: -1 }] },
    { id: 'zitterEnde', when: { flag: 'zitter' }, at: 'buy:beer', effects: [{ unflag: 'zitter' }, { luckMod: 0 }, { jobMod: null }] },
    /* ---- Niere ---- */
    { id: 'niere', when: { flag: 'abgestuerzt' }, at: 'buy:kidney', effects: [{ var: 'leber', add: -20 }] },
    /* ---- Nacht: Entzug, Pegel-Reset, Warnung ---- */
    { id: 'entzugSzene', when: { all: [{ flag: 'abgestuerzt' }, { notFlag: 'nuechtern' }, { notFlag: 'entzugGesehen' }, { var: 'pegel', lt: 3 }, { not: { all: [{ flag: 'sucht' }, { var: 'brownieHeute', gte: 1 }] } }] }, once: true, at: 'sleep', scene: 'kater.entzug', effects: [{ flag: 'entzugGesehen' }] },
    { id: 'entzug', when: { all: [{ flag: 'abgestuerzt' }, { notFlag: 'nuechtern' }, { notFlag: 'sucht' }, { var: 'pegel', lt: 3 }] }, at: 'sleep', effects: [{ var: 'leber', add: -2 }, { flag: 'zitter' }, { luckMod: -15 }, { jobMod: { spuelerZone: 0.7, taxiBrakeDelay: 150, postTime: 0.75, shiftPay: 0.5 } }] },
    { id: 'entzugSucht', when: { all: [{ flag: 'abgestuerzt' }, { notFlag: 'nuechtern' }, { flag: 'sucht' }, { var: 'pegel', lt: 3 }, { var: 'brownieHeute', lt: 1 }] }, at: 'sleep', effects: [{ var: 'leber', add: -4 }, { flag: 'zitter' }, { luckMod: -15 }, { jobMod: { spuelerZone: 0.7, taxiBrakeDelay: 150, postTime: 0.75, shiftPay: 0.5 } }] },
    { id: 'pegelReset', when: { flag: 'abgestuerzt' }, at: 'sleep', effects: [{ var: 'pegel', set: 0 }] },
    { id: 'leberWarnung', when: { all: [{ flag: 'abgestuerzt' }, { var: 'leber', lte: 30 }, { var: 'leber', gt: 0 }] }, once: true, at: 'night', scene: 'kater.leber' },
```

Die Zahlen aus `STORY_KATER.N` hier bewusst **ausgeschrieben** (Event-Objekte sind statisch); `N` dient als Referenz für Szenentexte und Kaufgespräch. Alternativ die Event-Liste per Funktion mit `N` bauen – dann `events: (() => { const N = …; return [...]; })()` – erlaubt, wenn der Ausführende es sauberer findet; die Tests bleiben gleich.

`scenes`:

```js
    'kater.k2': [
      { bg: 'strasse', who: 'du', mood: 'shock', text: 'Tag vier. Null auf dem Konto, kein Auto, kein Schlüssel. Der Wirt hat einen Deckel für mich angelegt. Ich hab ihn nicht drum gebeten.' },
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Pinnwand ist da hinten. Spülen, Post, Taxi. Und drei Bier am Tag – nicht meine Regel, deine Hände haben das entschieden.' },
    ],
    'kater.entzug': [
      { bg: 'keller', who: 'wirt', mood: 'calm', text: 'Du hast gestern nur zwei gehabt. Ich seh das. Deine Hände sehen das auch.' },
      { bg: 'keller', who: 'du', mood: 'shock', text: 'Das Glas klirrt, bevor ich es anfasse. Heute wird kein guter Tag. Bis zum ersten Bier.' },
    ],
    'kater.leber': [
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Deine Leber und ich haben gesprochen. Sie war kurz angebunden. Dreißig Prozent, sagt sie. Ich sage: Ich hab ein Bett frei.' },
    ],
    'kater.royal.zitter': [
      { bg: 'royal', who: 'sylvie', mood: 'calm', text: 'Der Türsteher hebt die Hand. Sie zittern. Wir haben eine Hausordnung – kommen Sie wieder, wenn die Hände still sind.' },
    ],
```

- [ ] **Step 4: Tests** – Run: `node tests/run-selftest.mjs` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(kater): Alkohol-Schleife – Freibier/Deckel, Pegel, Entzug, Zitter-Tag, Leber, Warnung

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Drogen (Doc-Angebot, Sucht), Therapie (Kapitel 3), Kapitel-3-Intro

**Files:** Block `story-kater` · Test: Block `selftest`

- [ ] **Step 1: Failing Tests**

```js
T.test('STORY_KATER: Doc-Angebot Tag 6/12/18, dreimal Nein → Standhaft', () => {
  const s = katerDay(6);
  T.eq(runHook(s, 'night'), ['docAngebot']);
  StoryRules.applyEffect(s, { var: 'docNein', add: 1 }, STORY_KATER); s.story.seen.push('docAngebot');
  s.story.day = 12; T.eq(runHook(s, 'night'), ['docAngebot2']); StoryRules.applyEffect(s, { var: 'docNein', add: 1 }, STORY_KATER);
  s.story.day = 18; T.eq(runHook(s, 'night'), ['docAngebot3']);
  StoryRules.applyEffect(s, { var: 'docNein', add: 1 }, STORY_KATER);
  T.eq(runHook(s, 'night'), ['standhaft'], 'dritter Nein-Abend: Trophäe');
  T.eq(s.story.flags.docAbgelehnt, true);
});
T.test('STORY_KATER: Sucht – Brownie 300 €, Therapie 8.000 €, Brownie deckt den Pegel, Entzug −4', () => {
  const s = katerDay(6);
  const panels = STORY_KATER.scenes['kater.doc.angebot'];
  const ja = panels[panels.length - 1].choices.find((c) => c.value === 'ja');
  for (const eff of ja.effects) StoryRules.applyEffect(s, eff, STORY_KATER);
  T.eq(s.story.flags.sucht, true);
  T.eq(StoryRules.price(s, 'brownie'), 300); T.eq(StoryRules.price(s, 'therapy'), 8000);
  s.story.day = 7; runHook(s, 'morning');
  runHook(s, 'buy:brownie');
  T.eq([s.story.vars.brownieHeute, s.story.vars.leber], [1, 96]);
  T.ok(!runHook(s, 'sleep').includes('entzugSucht'), 'Brownie deckt den Bedarf');
  s.story.day = 8; runHook(s, 'morning');
  const ids = runHook(s, 'sleep');
  T.ok(ids.includes('entzugSucht') && !ids.includes('entzug'), ids.join());
  T.eq(s.story.vars.leber, 92, '96 − 4');
});
T.test('STORY_KATER: Therapie – ab Kapitel 3 erlaubt, danach kein Bier, kein Entzug, Leber stabil', () => {
  const s = katerDay(11);
  T.eq(StoryRules.purchaseAllowed(s, 'therapy'), null, 'vor dem Kapitel-3-Effekt nicht freigegeben');
  StoryRules.applyEffect(s, { enable: ['therapy'] }, STORY_KATER); // macht Kapitel 3 per chapters[].unlock nicht – daher als Event, siehe Implementierung
  runHook(s, 'buy:therapy');
  T.eq(s.story.flags.nuechtern, true);
  T.eq(StoryRules.purchaseAllowed(s, 'beer'), false); T.eq(StoryRules.purchaseAllowed(s, 'brownie'), false);
  T.eq(StoryRules.purchaseAllowed(s, 'therapy'), false, 'Therapie ist einmalig – sperrt sich selbst');
  T.eq(runHook(s, 'sleep').filter((id) => id.startsWith('entzug')), []);
  s.story.day = 12; T.eq(runHook(s, 'morning').includes('freibier'), false);
});
T.test('STORY_KATER: Kapitel-3-Morgen gibt Therapie frei', () => {
  const s = katerDay(11);
  T.ok(runHook(s, 'morning').includes('therapieFrei'));
  T.eq(StoryRules.purchaseAllowed(s, 'therapy'), true);
});
```

- [ ] **Step 2: Fehlschlag sehen** – Run: `node tests/run-selftest.mjs`.

- [ ] **Step 3: Implementieren**

`events` (anhängen):

```js
    /* ---- Drogen ---- */
    { id: 'docAngebot', when: { all: [{ day: { eq: 6 } }, { notFlag: 'sucht' }] }, once: true, at: 'night', scene: 'kater.doc.angebot' },
    { id: 'docAngebot2', when: { all: [{ day: { eq: 12 } }, { notFlag: 'sucht' }, { notFlag: 'nuechtern' }] }, once: true, at: 'night', scene: 'kater.doc.angebot2' },
    { id: 'docAngebot3', when: { all: [{ day: { eq: 18 } }, { notFlag: 'sucht' }, { notFlag: 'nuechtern' }] }, once: true, at: 'night', scene: 'kater.doc.angebot3' },
    { id: 'standhaft', when: { all: [{ var: 'docNein', gte: 3 }, { notFlag: 'sucht' }] }, once: true, at: 'night', effects: [{ flag: 'docAbgelehnt' }, { achievement: 'standhaft' }] },
    { id: 'brownie', when: { all: [{ flag: 'abgestuerzt' }] }, at: 'buy:brownie', effects: [{ var: 'brownieHeute', add: 1 }, { var: 'leber', add: -4 }] },
    { id: 'zitterEndeBrownie', when: { flag: 'zitter' }, at: 'buy:brownie', effects: [{ unflag: 'zitter' }, { luckMod: 0 }, { jobMod: null }] },
    /* ---- Therapie ---- */
    { id: 'therapieFrei', when: { all: [{ day: { gte: 11 } }, { flag: 'abgestuerzt' }, { notFlag: 'nuechtern' }] }, once: true, at: 'morning', effects: [{ enable: ['therapy'] }] },
    { id: 'therapie', when: { flag: 'abgestuerzt' }, at: 'buy:therapy', scene: 'kater.therapie', effects: [{ flag: 'nuechtern' }, { disable: ['beer', 'brownie', 'therapy'] }, { unflag: 'zitter' }, { luckMod: 0 }, { jobMod: null }, { price: { beer: 50 } }] },
```

Die Sucht-Variante von `entzug`/`entzugSucht` und `freibier` (Bedingung `notFlag: 'nuechtern'`) ist in Task 4 bereits berücksichtigt.

`scenes`:

```js
    'kater.k3': [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Ich werd\'s verkaufen. Den Keller. Vierzigtausend, plus was auf deinem Deckel steht. Nicht an dich – an wen auch immer zuerst kommt.' },
      { bg: 'bar', who: 'wirt', mood: 'happy', text: 'Außer du kommst zuerst. Bis Tag dreißig. Und der Doc hat ein Programm, falls du die Hände brauchst. Kostet, hilft, macht nüchtern. Nüchtern spielt sich schlecht.' },
    ],
    'kater.doc.angebot': [
      { bg: 'bar', who: 'doc', mood: 'calm', text: 'Drei Bier für zwanzig Prozent Glück. Ein Brownie für vierzig. Rechne selbst, du warst Filialleiter.' },
      { bg: 'bar', who: 'doc', mood: 'calm', text: 'Dreihundert das Stück, für dich. Deine Leber bezahlt den Rest.',
        choices: [{ label: 'Nein, danke', value: 'nein', cls: 'ghost', effects: [{ var: 'docNein', add: 1 }] }, { label: 'Was kostet das?', value: 'ja', cls: 'red', effects: [{ flag: 'sucht' }, { price: { brownie: 300, therapy: 8000 } }] }] },
    ],
    'kater.doc.angebot2': [
      { bg: 'bar', who: 'doc', mood: 'calm', text: 'Deine Leber weiß, was du gestern gemacht hast. Ich auch. Der Brownie wäre schneller gewesen.',
        choices: [{ label: 'Nein', value: 'nein', cls: 'ghost', effects: [{ var: 'docNein', add: 1 }] }, { label: 'Gib her', value: 'ja', cls: 'red', effects: [{ flag: 'sucht' }, { price: { brownie: 300, therapy: 8000 } }] }] },
    ],
    'kater.doc.angebot3': [
      { bg: 'gasse', who: 'doc', mood: 'angry', text: 'Letztes Angebot. Danach frag ich nicht mehr, ich warte nur noch.',
        choices: [{ label: 'Nein.', value: 'nein', cls: 'ghost', effects: [{ var: 'docNein', add: 1 }] }, { label: 'Okay.', value: 'ja', cls: 'red', effects: [{ flag: 'sucht' }, { price: { brownie: 300, therapy: 8000 } }] }] },
    ],
    'kater.therapie': (ctx) => ctx.raw.flags.sucht ? [
      { bg: 'klinik', who: 'doc', mood: 'angry', text: 'Achttausend. Du kaufst dich bei mir raus. Ich muss dich gehen lassen – das Programm ist echt, leider.' },
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Kein Bier, kein Brownie, kein Glück aus der Flasche. Du wirst am Tisch merken, wie ehrlich der Kessel ist.' },
    ] : [
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Fünftausend. Vier Wochen Programm in drei Tagen, ich hab Beziehungen. Ab morgen zittert nichts mehr.' },
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Der Wirt schenkt dir nichts mehr ein, ich hab\'s ihm gesagt. Und das Glück im Glas? Gibt\'s nicht mehr. Nüchtern spielt sich anders.' },
    ],
```

- [ ] **Step 4: Tests** – Run: `node tests/run-selftest.mjs` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(kater): Doc-Angebot dreimal, Sucht-Schalter, Therapie ab Kapitel 3

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Jobs und Schicht-Szenen (Filialleiter, Türsteher, Croupier, Eintreiber), Sylvie-Szene

**Files:** Block `story-kater` (`jobScenes`, `jobEffects`, `scenes`, `events`) · Test: Block `selftest`

- [ ] **Step 1: Failing Tests**

```js
T.test('STORY_KATER: Schicht-Szenen vorhanden, Eintreiber nur ohne Sturz', () => {
  T.eq(STORY_KATER.jobScenes.filialleiter.length, 3);
  T.eq(STORY_KATER.jobScenes.tuersteher.length, 3);
  T.eq(STORY_KATER.jobScenes.croupier.length, 3);
  T.eq(STORY_KATER.jobScenes.eintreiber.length, 2);
  const a = katerDay(21, {}); T.eq(runHook(a, 'morning').includes('eintreiberJob'), true);
  T.eq(a.story.unlocked.jobs.includes('eintreiber'), true);
  const b = katerState({}, { schuld: 'sturz' }); b.story.day = 21; b.story.flags.abgestuerzt = true;
  T.eq(runHook(b, 'morning').includes('eintreiberJob'), false);
  T.eq(runHook(b, 'morning').includes('igorPartner') || b.story.seen.includes('igorPartner'), true, 'nach Sturz stattdessen Igor-Szene');
});
T.test('STORY_KATER: Croupier sieht die Bücher → Rabatt-Flag', () => {
  const s = katerDay(15);
  T.eq(STORY_KATER.jobEffects['kater.croup.buecher'], [{ flag: 'buecher' }]);
});
T.test('STORY_KATER: Sylvie nach dem ersten großen Gewinn', () => {
  const s = katerDay(15);
  T.eq(runHook(s, 'royal:guest'), ['sylvieGast']);
  T.eq(runHook(s, 'royal:guest'), [], 'einmalig');
});
```

- [ ] **Step 2: Fehlschlag sehen** – Run: `node tests/run-selftest.mjs`.

- [ ] **Step 3: Implementieren**

```js
  jobScenes: {
    filialleiter: ['kater.fil.anruf', 'kater.fil.vollmacht', 'kater.fil.lob'],
    tuersteher: ['kater.tuer.chantal', 'kater.tuer.sylvie', 'kater.tuer.kevin'],
    croupier: ['kater.croup.buecher', 'kater.croup.wirt', 'kater.croup.hand'],
    eintreiber: ['kater.eintr.vito', 'kater.eintr.kiosk'],
  },
  jobEffects: {
    'kater.croup.buecher': [{ flag: 'buecher' }],
    'kater.tuer.kevin': [{ balance: 50 }],
    'kater.eintr.kiosk': [{ balance: 100 }],
  },
```

`events` (anhängen):

```js
    /* ---- Kapitel 4: Eintreiber nur, wenn Vito noch da ist ---- */
    { id: 'eintreiberJob', when: { all: [{ day: { gte: 21 } }, { flag: 'abgestuerzt' }, { not: { prevEnding: { story: 'schuld', id: 'sturz' } } }] }, once: true, at: 'morning', scene: 'kater.vito.zurueck', effects: [{ unlock: { jobs: ['eintreiber'] } }] },
    { id: 'igorPartner', when: { all: [{ day: { gte: 21 } }, { flag: 'abgestuerzt' }, { prevEnding: { story: 'schuld', id: 'sturz' } }] }, once: true, at: 'morning', scene: 'kater.igor.partner' },
    /* ---- Casino Royal ---- */
    { id: 'sylvieGast', when: { flag: 'abgestuerzt' }, once: true, at: 'royal:guest', scene: 'kater.sylvie' },
```

`scenes`:

```js
    /* Filialleiter (Kapitel 1) – keine Wahl, nur Vorahnung */
    'kater.fil.anruf': [{ bg: 'bank', who: 'krause', mood: 'calm', text: 'Ihre Frau hat angerufen. Wollte die Kontonummer der Filiale wissen – für eine Überraschung, sagt sie. Reizend.' }],
    'kater.fil.vollmacht': [{ bg: 'bank', who: 'chantal', mood: 'happy', text: 'Ich hol nur die Vollmacht ab, Schatz. Für die Flitterwochen. Herr Krause war so nett, sie gleich zu beglaubigen.' }],
    'kater.fil.lob': [{ bg: 'bank', who: 'krause', mood: 'happy', text: 'Eine bemerkenswerte Frau. Sie fragt nach Dingen, die sonst niemand fragt. Sie können stolz sein.' }],
    /* Türsteher (Kapitel 3) */
    'kater.tuer.chantal': [
      { bg: 'keller', who: 'chantal', mood: 'calm', text: 'Sie steht in der Schlange. Mit einem anderen. Er trägt meinen Mantel. Sie tut, als würde sie mich nicht kennen. Sie kann das gut.',
        choices: [{ label: 'Reinlassen', value: 'rein', cls: 'ghost' }, { label: 'Nicht heute', value: 'raus', cls: 'red', effects: [{ flag: 'chantalAbgewiesen' }] }] },
    ],
    'kater.tuer.sylvie': [
      { bg: 'keller', who: 'sylvie', mood: 'calm', text: 'Madame Sylvie, im Keller. Sie sieht sich um wie jemand, der Quadratmeter zählt. „Ihr Wirt will verkaufen. Ich kaufe gern."' },
      { bg: 'keller', who: 'sylvie', mood: 'calm', text: '„Sie wollen auch? Dann beeilen Sie sich. Ich habe Zeit, Sie haben eine Leber."' },
    ],
    'kater.tuer.kevin': [
      { bg: 'keller', who: 'kevin', mood: 'happy', text: 'Kevin drückt mir fünfzig in die Hand. „Für nichts. Du hast mich nicht gesehen." Ich hab ihn nicht gesehen.' },
    ],
    /* Croupier (Kapitel 3, 3 Türsteher-Nächte) */
    'kater.croup.buecher': [
      { bg: 'hinterzimmer', who: 'du', mood: 'shock', text: 'Der Wirt hat die Bücher offen liegen lassen. Der Keller macht das Doppelte von dem, was er sagt. Vierzigtausend ist ein Freundschaftspreis – oder ein Test.' },
    ],
    'kater.croup.wirt': [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Du gibst gut Karten. Ruhige Hände heute. Wie viele waren\'s? Drei? Merkt man. Merken die Gäste auch.' },
    ],
    'kater.croup.hand': [
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Igor legt einen Chip auf den Tisch. „Für dich. Nicht setzen. Halten." Ich halte ihn. Er ist warm.' },
    ],
    /* Eintreiber (Kapitel 4, nur wenn Vito noch da ist) */
    'kater.vito.zurueck': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Ich bin kein Unmensch. Aber du trinkst. Trinkende Männer haben Listen im Kopf, die sie vergessen. Ich habe eine auf Papier. Willst du sie abarbeiten?' },
    ],
    'kater.eintr.vito': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: '„Deine Frau steht auch drauf. Zeile vier." Er lässt mich die Zeile lesen. Ich lese sie zweimal.' },
    ],
    'kater.eintr.kiosk': [
      { bg: 'gasse', who: 'du', mood: 'calm', text: 'Der Kioskbesitzer zahlt, bevor ich die Hand hebe. Hundert extra „für den Weg". Ich nehme sie. Meine Hände zittern nicht, wenn sie Geld halten.' },
    ],
    'kater.igor.partner': [
      { bg: 'bar', who: 'igor', mood: 'calm', text: 'Igor sitzt neben mir. „Der Wirt verkauft. Ich bleibe an der Tür, wer auch kauft. Kauf du. Ich mag deine Hände, wenn sie ruhig sind."' },
    ],
    /* Casino Royal */
    'kater.sylvie': [
      { bg: 'royal', who: 'sylvie', mood: 'calm', text: 'Gast des Hauses. Ich weiß, was Sie vorhaben. Vierzigtausend für einen Keller – ich zahle mehr, wenn Sie es nicht schaffen.' },
    ],
```

- [ ] **Step 4: Tests** – Run: `node tests/run-selftest.mjs` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(kater): Schicht-Szenen Filialleiter/Türsteher/Croupier/Eintreiber, Igor nach dem Sturz, Sylvie

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Kaufgespräch (Story-Aktion), Chantal-Rückkehr, Kapitel-4-Intro

**Files:** Block `story-kater` (`actions`, `events`, `scenes`) · Test: Block `selftest`

- [ ] **Step 1: Failing Tests**

```js
T.test('STORY_KATER: Kaufgespräch ab Tag 20, Preis = 40.000 + Deckel, Bücher −5.000', () => {
  const s = katerDay(19); s.story.vars.deckel = 1250;
  T.eq(StoryRules.actionsFor(STORY_KATER, s, 'bar'), []);
  s.story.day = 20;
  T.eq(StoryRules.actionsFor(STORY_KATER, s, 'bar').map((a) => a.id), ['kauf']);
  const ctx = (bal) => ({ raw: { balance: bal, day: 20, vars: s.story.vars, flags: s.story.flags }, balance: UI_FMT(bal) });
  const panels = STORY_KATER.scenes['kater.kauf'](ctx(41000));
  const last = panels[panels.length - 1];
  T.eq(last.choices.map((c) => c.value), ['nein'], 'zu wenig Geld: nur Absage');
  const p2 = STORY_KATER.scenes['kater.kauf'](ctx(41250));
  const ja = p2[p2.length - 1].choices.find((c) => c.value === 'ja');
  T.eq(ja.effects, [{ balance: -41250 }, { flag: 'gekauft' }]);
  s.story.flags.buecher = true;
  const p3 = STORY_KATER.scenes['kater.kauf'](ctx(36250));
  const ja3 = p3[p3.length - 1].choices.find((c) => c.value === 'ja');
  T.eq(ja3.effects, [{ balance: -36250 }, { flag: 'gekauft' }]);
  s.story.flags.gekauft = true;
  T.eq(StoryRules.actionsFor(STORY_KATER, s, 'bar'), [], 'nach dem Kauf keine Aktion mehr');
});
T.test('STORY_KATER: Chantal kommt ab Tag 21 mit 15.000 zurück, nicht mit Sucht', () => {
  const s = katerDay(21); s.balance = 15000;
  T.ok(runHook(s, 'night').includes('chantal'));
  const t = katerDay(21, { sucht: true }); t.balance = 15000;
  const ids = runHook(t, 'night');
  T.ok(!ids.includes('chantal') && ids.includes('chantalSucht'));
  const u = katerDay(21); u.balance = 14999;
  T.ok(!runHook(u, 'night').includes('chantal'));
});
```

`UI_FMT` im Node-Test: `UI` existiert dort nicht – im Test-Block oben `const UI_FMT = (n) => typeof UI !== 'undefined' ? UI.fmt(n) : \`${n} €\`;` anlegen. Die Szene benutzt `ctx.raw.balance` (Zahl) und formatiert selbst mit `fmtMoney` – eine kleine reine Hilfsfunktion in `StoryRules`: `fmtMoney(n) { return n.toLocaleString('de-DE') + ' €'; }` (im Browser identisch zu `UI.fmt`? – **prüfen** `grep -n "fmt(" keller37.html` im Block `ui`; wenn `UI.fmt` etwas anderes tut, in der Szene `typeof UI !== 'undefined' ? UI.fmt : StoryRules.fmtMoney` verwenden).

- [ ] **Step 2: Fehlschlag sehen** – Run: `node tests/run-selftest.mjs`.

- [ ] **Step 3: Implementieren**

```js
  actions: [
    { id: 'kauf', room: 'bar', label: '🔑 Über den Keller reden', when: { all: [{ day: { gte: 20 } }, { flag: 'abgestuerzt' }, { notFlag: 'gekauft' }] }, scene: 'kater.kauf' },
  ],
```

`events` (anhängen):

```js
    /* ---- Kapitel 4: Chantal ---- */
    { id: 'chantal', when: { all: [{ day: { gte: 21 } }, { balance: { gte: 15000 } }, { notFlag: 'sucht' }, { notFlag: 'chantalZurueck' }, { notFlag: 'chantalWeg' }] }, once: true, at: 'night', scene: 'kater.chantal' },
    { id: 'chantalSucht', when: { all: [{ day: { gte: 21 } }, { balance: { gte: 15000 } }, { flag: 'sucht' }] }, once: true, at: 'night', scene: 'kater.chantal.sucht' },
```

`scenes`:

```js
    'kater.k4': [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Letzte Runde. Zehn Tage. Sylvie hat ein Angebot gemacht, ich hab noch nicht Ja gesagt. Ich hab auch noch nicht Nein gesagt.' },
    ],
    'kater.kauf': (ctx) => {
      const fmt = typeof UI !== 'undefined' ? UI.fmt : StoryRules.fmtMoney;
      const deckel = ctx.raw.vars.deckel || 0;
      const rabatt = ctx.raw.flags.buecher ? STORY_KATER.N.buecherRabatt : 0;
      const preis = STORY_KATER.N.kaufpreis + deckel - rabatt;
      const kann = ctx.raw.balance >= preis;
      const choices = [{ label: 'Noch nicht', value: 'nein', cls: 'ghost' }];
      if (kann) choices.unshift({ label: `Kaufen · ${fmt(preis)}`, value: 'ja', cls: 'red', effects: [{ balance: -preis }, { flag: 'gekauft' }] });
      return [
        { bg: 'bar', who: 'wirt', mood: 'calm', text: `Vierzigtausend. Plus dein Deckel: ${fmt(deckel)}.${rabatt ? ' Du hast die Bücher gesehen, ich seh\'s dir an – fünftausend weniger, dafür hältst du den Mund.' : ''} Macht ${fmt(preis)}.` },
        { bg: 'bar', who: 'wirt', mood: kann ? 'happy' : 'calm', text: kann ? 'Du hast es. Ich seh\'s. Schlüssel liegt unter dem Tresen, wo er immer lag.' : `Du hast ${fmt(ctx.raw.balance)}. Der Kessel läuft noch, die Tische auch. Beeil dich.`, choices },
      ];
    },
    'kater.chantal': [
      { bg: 'strasse', who: 'chantal', mood: 'calm', text: 'Sie steht vor dem Keller. Ohne Mantel, ohne den anderen. „Ich hab gehört, du hast wieder Geld. Ich hab gehört, du kaufst was."' },
      { bg: 'strasse', who: 'chantal', mood: 'happy', text: '„Lass mich rein. Ich kann Kasse. Ich kann alles, was mit Kasse zu tun hat, das weißt du."',
        choices: [{ label: 'Reinlassen', value: 'rein', cls: 'pink', effects: [{ flag: 'chantalZurueck' }] }, { label: 'Rauswerfen', value: 'raus', cls: 'red', effects: [{ flag: 'chantalWeg' }] }] },
    ],
    'kater.chantal.sucht': [
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Sie hat mich an der Bar gesehen. Mit dem Doc. Sie hat nichts gesagt. Sie ist weitergegangen. Das war das Netteste, was sie je getan hat.' },
    ],
```

`StoryRules.fmtMoney(n) { return `${Math.round(n).toLocaleString('de-DE')} €`; }` ergänzen.

- [ ] **Step 4: Tests** – Run: `node tests/run-selftest.mjs` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(kater): Kaufgespräch als Story-Aktion, Chantal-Rückkehr, Kapitel 4

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Sechs Enden

**Files:** Block `story-kater` (`scenes`) · Test: Block `selftest`

- [ ] **Step 1: Failing Tests**

```js
T.test('STORY_KATER: sechs Enden per Zustand, Prioritäten', () => {
  const at = (setup) => { const s = katerDay(30); setup(s); return StoryRules.ending(STORY_KATER, s); };
  T.eq(at((s) => { s.story.vars.leber = 0; }).id, 'bett');
  T.eq(at((s) => { s.story.flags.gekauft = true; s.story.vars.leber = 0; }).id, 'bett', 'Bett vor Wirt');
  T.eq(at((s) => { s.story.flags.gekauft = true; }).id, 'wirt');
  T.eq(at((s) => { s.story.flags.nuechtern = true; }).id, 'nuechtern');
  T.eq(at((s) => { s.story.flags.sucht = true; s.story.vars.leber = 15; }).id, 'brownie');
  T.eq(at((s) => { s.story.flags.sucht = true; s.story.vars.leber = 16; }).id, null, 'Leber 16 → kein Brownie-Ende');
  T.eq(at((s) => { s.story.flags.chantalZurueck = true; s.balance = 15000; }).id, 'taxi');
  T.eq(at((s) => { s.story.flags.chantalZurueck = true; s.balance = 14999; }), null);
  const fb = katerDay(31); T.eq(StoryRules.ending(STORY_KATER, fb).id, 'stammgast');
  const early = katerDay(12); early.story.flags.nuechtern = true; T.eq(StoryRules.ending(STORY_KATER, early), null, 'Nüchtern erst an Tag 30');
  const wirt = katerDay(22); wirt.story.flags.gekauft = true; T.eq(StoryRules.ending(STORY_KATER, wirt, { immediateOnly: true }).id, 'wirt', 'Kauf beendet sofort');
});
T.test('STORY_KATER: Ende Wirt mit Chantal-Variante', () => {
  const p1 = STORY_KATER.scenes['kater.ende.wirt']({ raw: { flags: { chantalZurueck: true }, vars: {} } });
  const p2 = STORY_KATER.scenes['kater.ende.wirt']({ raw: { flags: {}, vars: {} } });
  T.eq(p1.length, p2.length + 1);
  T.eq(p1.some((p) => p.who === 'chantal'), true); T.eq(p2.some((p) => p.who === 'chantal'), false);
});
```

- [ ] **Step 2: Fehlschlag sehen** – Run: `node tests/run-selftest.mjs`.

- [ ] **Step 3: Implementieren**

```js
    'kater.ende.bett': [
      { bg: 'klinik', who: 'doc', mood: 'calm', fx: 'blackout', text: 'Zähl rückwärts von zehn. Du kommst nicht bis sieben. Das ist in Ordnung. Die Niere war ein Vorschuss – das hier ist die Rate.' },
      { bg: 'klinik', who: 'wirt', mood: 'calm', text: 'Der Wirt bringt Blumen. Er stellt sie neben das Bett, in dem niemand mehr liegt. Der Deckel? „Ich hab ihn zerrissen. Er hätte eh nicht gezahlt."' },
    ],
    'kater.ende.wirt': (ctx) => {
      const panels = [
        { bg: 'bar', who: 'wirt', mood: 'happy', text: 'Der Schlüssel. Unter dem Tresen, wo er immer lag. Ich bleib Gast – der Hocker am Ende ist meiner, das steht im Vertrag, den du nicht gelesen hast.' },
        { bg: 'keller', who: 'igor', mood: 'calm', text: 'Igor nickt. Einmal. Das ist bei Igor ein Handschlag.' },
      ];
      if (ctx.raw.flags.chantalZurueck) panels.push({ bg: 'bar', who: 'chantal', mood: 'happy', text: 'Sie steht hinter dem Tresen. Sie hat die Kasse schon geöffnet. „Nur gucken, Schatz. Vorerst."' });
      panels.push({ bg: 'royal', who: 'sylvie', mood: 'calm', text: 'Blumen von Madame Sylvie. Karte: „Herzlichen Glückwunsch. Ich habe Zeit." Dieselbe Handschrift wie auf einem anderen Zettel.' });
      panels.push({ bg: 'bar', who: 'du', mood: 'happy', text: 'Der Ort, an dem ich alles verloren habe. Er gehört mir. Der Kessel läuft, wie er läuft. Erstes Bier geht aufs Haus. Mein Haus.' });
      return panels;
    },
    'kater.ende.nuechtern': [
      { bg: 'strasse', who: 'du', mood: 'calm', text: 'Tag dreißig. Ich gehe am Keller vorbei. Die Tür steht offen, der Wirt winkt. Ich winke zurück. Ich bleibe nicht stehen.' },
      { bg: 'hafen-morgen', who: 'du', mood: 'happy', text: 'Kein Keller, kein Bier, kein Glück im Glas. Nur Hände, die nicht zittern. Es ist weniger, als ich wollte. Es ist mehr, als ich hatte.' },
    ],
    'kater.ende.brownie': [
      { bg: 'bar', who: 'doc', mood: 'happy', text: 'Partner. Du sitzt an der Bar und wartest. Auf den Nächsten, der gerade seine Frau verloren hat. Du erkennst sie am Zettel in der Hand.' },
      { bg: 'bar', who: 'du', mood: 'calm', text: 'Dreihundert das Stück. Für ihn. Die Leber bezahlt den Rest, das weiß ich besser als jeder. Ich sage es ihm nicht.' },
    ],
    'kater.ende.taxi': [
      { bg: 'strasse', who: 'chantal', mood: 'happy', text: 'Vier Uhr. Das Taxi wartet. Sie hat die Kasse, den Deckel-Zettel und die Vollmacht – die alte gilt noch, hat Dr. Schmalz gesagt.' },
      { bg: 'hafen', who: 'du', mood: 'shock', text: 'Die Fähre legt ab. Das Handy vibriert. Unbekannte Nummer: „Danke für alles. Wirklich alles. Wieder. – C.-M."' },
    ],
    'kater.ende.stammgast': [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Verkauft. An Sylvie. Sie lässt alles, wie es ist – nur die Preise nicht. Dein Hocker bleibt, sagt sie. Sie mag Stammgäste. Die sind berechenbar.' },
      { bg: 'bar', who: 'du', mood: 'calm', text: 'Das erste Bier geht aufs Haus. Es ist nicht mehr mein Haus. Es war nie meins. Der Kessel läuft, wie er läuft.' },
    ],
```

- [ ] **Step 4: Tests** – Run: `node tests/run-selftest.mjs` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(kater): sechs Enden

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Browser-Verdrahtung prüfen, Playtest-Szenario, README, Screenshots

**Files:**
- Modify: `tests/playtest-story.py` (neues `scenario_kater`), `README.md`, `docs/superpowers/screenshots/`
- Prüfen: Block `story-kater` enthält kein `TODO` mehr (`grep -n "TODO" keller37.html` → leer)

- [ ] **Step 1: Manuelle Runde im Browser**

`?fresh&story=kater&prev=doc` → Intro-Variante Doc, Hochzeit, Tag 1: Villa/Auto im HUD (`Stadt.line`), Filialleiter an der Pinnwand, Casino Royal erreichbar (Auto da), Leber 70. Drei Tage schlafen → Absturz-Szene, Konto 0, kein Auto; Seitenleiste: Bier „0 €", danach „50 €"; Deckel im HUD; Schlafen mit 2 Bier → Zitter-Toast, Royal-Schaufenster „Sie zittern…"; erstes Bier hebt auf. Tag 6 Nacht: Doc-Angebot. Konsole `Story.s.day = 19; State.save()` → schlafen → Tag 20: Seitenleiste zeigt „🔑 Über den Keller reden"; Konsole `State.s.balance = 50000` → kaufen → Ende Wirt sofort, Trophäe „Hausherr", Titel zeigt „Neue Story · Die Schuld" (kater gespielt, schuld älter).

- [ ] **Step 2: Playtest-Szenario**

In `tests/playtest-story.py` vor `async def main()`:

```python
async def scenario_kater(cdp):
    """Story 2: Sperre ohne Story-1-Ende, Intro-Variante, Absturz, Zitter-Tag, Kauf-Ende."""
    # Ohne Story-1-Ende ist Der Kater gesperrt: Titel zeigt Die Schuld als naechste Story
    await cdp.navigate(URL_BASE + "?fresh")
    await asyncio.sleep(0.7)
    tag = await cdp.eval("document.querySelector('#titleStoryTag').textContent", await_promise=False)
    record("kater: ohne Story-1-Ende startet Die Schuld", "Die Schuld" in (tag or ""), tag)
    lock = await cdp.eval("document.querySelector('#titleStoryLock').textContent", await_promise=False)
    record("kater: Titel nennt die Sperre", "Der Kater" in (lock or ""), lock)
    # Erzwungen mit vorigem Ende doc
    await cdp.navigate(URL_BASE + "?fresh&story=kater&prev=doc")
    await asyncio.sleep(0.7)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=20)
    leber = await cdp.eval("State.s.story.vars.leber", await_promise=False)
    record("kater: Doc-Ende → Leber 70", leber == 70, "leber=%s" % leber)
    car = await cdp.eval("State.s.car", await_promise=False)
    record("kater: Mercedes am Tag 1", car == "mercC", "car=%s" % car)
    # Drei Naechte schlafen (Job ueberspringen: 'Kein Job heute')
    for d in (1, 2, 3):
        await cdp.eval("Story.evening()", await_promise=False)
        await asyncio.sleep(0.4)
        await cdp.eval("Story.night()", await_promise=False)
        for _ in range(40):
            if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                await cdp.advance_cutscene(max_steps=4)
            if await cdp.eval("State.s.story.day", await_promise=False) == d + 1 and not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                break
            await asyncio.sleep(0.15)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    flag = await cdp.eval("State.s.story.flags.abgestuerzt", await_promise=False)
    record("kater: Absturz Nacht 3", bal == 0 and flag is True, "balance=%s abgestuerzt=%s" % (bal, flag))
    price = await cdp.eval("StoryRules.price(State.s, 'beer')", await_promise=False)
    record("kater: erstes Bier umsonst", price == 0, "price=%s" % price)
    await cdp.eval("Story.evening()", await_promise=False)
    await asyncio.sleep(0.3)
    await cdp.eval("Actions.beer()")
    deckel = await cdp.eval("State.s.story.vars.deckel", await_promise=False)
    record("kater: Deckel 50 nach Freibier", deckel == 50, "deckel=%s" % deckel)
    await cdp.eval("Story.night()", await_promise=False)
    for _ in range(40):
        if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            await cdp.advance_cutscene(max_steps=4)
        if await cdp.eval("State.s.story.flags.zitter", await_promise=False):
            break
        await asyncio.sleep(0.15)
    zitter = await cdp.eval("State.s.story.flags.zitter", await_promise=False)
    record("kater: Zitter-Tag nach Entzugsnacht", zitter is True, "zitter=%s" % zitter)
    await cdp.screenshot("kater-zitter.png")
    # Sofortiges Ende aus dem sleep-Hook heraus (Plan-1-Review, Critical #1): Leber 1 → Entzugsnacht −2 → „Bett" mitten in Story.night();
    # danach „Nächste Story" → Die Schuld muss unberührt an Tag 1/morning starten (kein Tag-2-Sprung, keine fremden seen-IDs).
    await cdp.eval("State.s.story.vars.leber = 1; State.s.story.vars.pegel = 0; State.s.story.phase = 'evening'; State.save();")
    await cdp.eval("Story.night()", await_promise=False)
    ended = None
    for _ in range(80):
        if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            await cdp.advance_cutscene(max_steps=3, label_hint="Nächste Story")
        ended = await cdp.eval("(State.meta.storyRuns.kater || {}).last", await_promise=False)
        nxt = await cdp.eval("State.s.story && State.s.story.id", await_promise=False)
        if ended == "bett" and nxt == "schuld" and not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            break
        await asyncio.sleep(0.15)
    record("kater: Ende Bett aus der Entzugsnacht", ended == "bett", "last=%s" % ended)
    nxt_state = await cdp.eval("State.s.story ? [State.s.story.id, State.s.story.day, State.s.story.phase, State.s.story.seen.length, Story.finishing, Story.sleeping] : null", await_promise=False)
    record("kater: Folgestory startet sauber an Tag 1", nxt_state == ["schuld", 1, "morning", 0, False, False], "state=%s" % nxt_state)
    # zurueck in eine frische Kater-Story fuer den Kauf-Test
    await cdp.navigate(URL_BASE + "?fresh&story=kater&prev=doc&day=22")
    await asyncio.sleep(0.7)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)
    # Kauf-Ende
    await cdp.eval("State.s.story.phase = 'evening'; State.s.balance = 60000; State.save(); UI.renderSide();")
    await asyncio.sleep(0.3)
    has_action = await cdp.eval("!!document.querySelector('[data-story-action=\"kauf\"]')", await_promise=False)
    record("kater: Kauf-Aktion in der Seitenleiste", has_action is True, "")
    await cdp.eval("Story.action('kauf')", await_promise=False)
    await asyncio.sleep(0.4)
    await cdp.advance_cutscene(max_steps=6, label_hint="Kaufen")
    ended = None
    for _ in range(80):
        if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
        ended = await cdp.eval("State.s.story.ended", await_promise=False)
        if ended:
            break
        await asyncio.sleep(0.15)
    record("kater: Ende Wirt sofort nach Kauf", ended == "wirt", "ended=%s" % ended)
    # Reentrancy-/Guard-Abdeckung fuer Story.checkImmediate (Plan 1, Task 6): das Ende kam aus einer
    # Szenen-Wahl (Story.action -> playScene -> applyEffects -> checkImmediate), nicht aus Story.night().
    finishing = await cdp.eval("Story.finishing", await_promise=False)
    record("kater: finishing-Flag nach dem Ende zurueckgesetzt", finishing is False, "finishing=%s" % finishing)
    phase = await cdp.eval("State.s.story && State.s.story.phase", await_promise=False)
    record("kater: keine Phasenaenderung nach sofortigem Ende", phase == "evening", "phase=%s" % phase)
    await cdp.screenshot("kater-ende-wirt.png")
```

In `main()` nach `scenario_story_stadt(cdp)`: `await scenario_kater(cdp)`.

`advance_cutscene(label_hint=…)` klickt bevorzugt den Button mit diesem Text – prüfen, wie `label_hint` implementiert ist (Zeile ~249), und ggf. den exakten Button-Text „Kaufen · 41.250 €" per Präfix matchen.

- [ ] **Step 3: README**

Abschnitt „Story-Modus", Unterpunkt „Enden" erweitern:

```
- **Story 2 „Der Kater":** Fortsetzung – erst spielbar, wenn „Die Schuld" ein Ende hat, und der Einstieg hängt davon ab, welches. Hochzeit, Absturz, drei Bier am Tag als Pflicht und als Glücksquelle, eine Leber als Countdown, der Doc mit einem Angebot, und der Keller, der zu kaufen ist. Sechs Enden.
```

Dev-Parameter: `?story=kater`, `?prev=doc` sind aus Plan 1/2 bereits dokumentiert – prüfen, `?ending=wirt` als Beispiel ergänzen.

- [ ] **Step 4: Screenshots und Gesamtverifikation**

```bash
tests/screenshot.sh docs/superpowers/screenshots/kater-intro.png "?fresh&story=kater&prev=doc"
```

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen. Run: `tests/dom-selftest.sh` → grün. Run: `python3 tests/playtest-story.py` → alle Szenarien grün, `ERRORS 0`. `grep -n "TODO" keller37.html` → leer.

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/playtest-story.py README.md docs/superpowers/screenshots/kater-*.png
git commit -m "test(kater): Playtest-Szenario Story 2; docs: README

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec-Abdeckung:**
- §2 Voraussetzung/Reihenfolge: `requires`, `prevEnding` in Intro/Events (Task 2, 3, 6) ✔
- §3 Kapitel 1–4, Intro-Varianten, Leber 70 nach Doc, Chantal-Rückkehr (Task 2, 3, 7) ✔; „Auto weg/Villa weg/Job weg" per `set`/`lock` (Task 1, 3) ✔
- §4 Pegel/Freibier/Deckel/Entzug/Zitter/Leber/Warnung/Therapie (Task 4, 5) ✔; Zitter-Casino-Sperre über `gates` (Task 2) ✔; Zitter-Minigame/Lohn über `jobMod` aus Plan 1 ✔
- §5 Drogen dreifach, Standhaft, Sucht-Folgen inkl. Chantal-Sperre und Therapie 8.000 (Task 5, 7) ✔
- §6 Jobs je Kapitel, Filialleiter, Eintreiber nur ohne Sturz, Igor-Alternative, Croupier-Bücher-Rabatt (Task 2, 6, 7) ✔; Zitter-Lohn −50 % (Plan 1) ✔
- §7 Sylvie-Szene in der Story (Task 6) ✔ (Casino selbst: Plan 2)
- §9 sechs Enden mit Prioritäten, `immediate` für Bett und Wirt, Chantal-Variante (Task 2, 8) ✔; Trophäen (Task 1, 2) ✔
- §10 Dev-Parameter (Plan 1/2), Tests, Playtest (Task 9) ✔

**Typ-Konsistenz:** Variablen `pegel, leber, deckel, bierHeute, brownieHeute, docNein`; Flags `abgestuerzt, zitter, entzugGesehen, sucht, docAbgelehnt, nuechtern, buecher, chantalZurueck, chantalWeg, chantalAbgewiesen, gekauft`; Effekte/Hooks wie in Plan 1/2 benannt. `StoryRules.fmtMoney` nur in Szenenfunktionen als Node-Fallback.

**Bewusste Vereinfachung:** „Drei Bier am Tag" stößt im Spiel an `Rules.MAX_BEERS` (drei gleichzeitig aktive Bier, Timer läuft pro Spin ab) – man muss zwischen den Bieren spielen. Das ist gewollt (Gambling-Kern), wird aber in der Entzug-Szene nicht erklärt; der Wirt-Text in `kater.k2` deutet es an. Falls die Balancing-Instanz `MAX_BEERS` ändert, bleibt die Story korrekt.
