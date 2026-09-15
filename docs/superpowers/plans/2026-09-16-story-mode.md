# Story-Modus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein Story-Modus für `keller37.html`: Titelscreen mit Modus-Wahl, datengetriebene Story-Engine (Tage, Bedingungen, Effekte, Enden), Jobbörse mit zwei neuen Mini-Spielen und Schicht-Karten, und die komplette Story 1 „Die Schuld" (30 Tage, 4 Enden).

**Architecture:** Die Engine ist in einen puren Teil (`StoryRules`, Node-testbar) und einen DOM-Teil (`Story`, `Jobs`, Screens) getrennt. Storys sind Datenpakete (`Stories.define({...})`) mit Szenen, Kapiteln, Ereignissen, Job-Szenen und Enden; die Engine kennt keine konkrete Story. `State` bekommt einen Modus (`free`/`story`) mit getrenntem Spielstand; Rules, Spiele, Wallet und Cutscene-Engine bleiben unverändert und sehen nur `State.s`.

**Tech Stack:** Vanilla HTML/CSS/JS in `keller37.html`, Node 20 (`tests/run-selftest.mjs`), Headless Chrome + CDP (python3 `websockets`) für Playtests.

**Spec:** `docs/superpowers/specs/2026-09-16-story-mode-design.md` (Redesign-Spec für die Sandbox: `docs/superpowers/specs/2026-09-15-keller37-redesign.md`, §9 bleibt 1:1).

## Global Constraints

- Branch `story-mode`; `main` bleibt unberührt.
- Eine Datei `keller37.html`; neue Blöcke als `<script id="…">` nach `gameover` und vor `selftest`, in dieser Reihenfolge: `story-rules`, `title`, `story-engine`, `jobs`, `job-spueler`, `job-taxi`, `story-probe`, `story-schuld`. Templates vor `<!-- /TEMPLATES -->`, CSS vor `/* ==== 7. ANIMATIONEN ==== */`, Keyframes ans Ende von Sektion 7. Tests vor `/* --- SELFTEST CASES END --- */`.
- Node-Runner lädt zusätzlich `story-rules` und `story-probe` (beide DOM-frei); `tests/run-selftest.mjs` wird in Task 1 entsprechend erweitert.
- Freies Spiel bleibt im Verhalten identisch; der bestehende Selbsttest (57) bleibt grün; `?screen=`-Screenshots des freien Spiels unverändert.
- Spielstände: `keller37.state` (frei), `keller37.story` (Story, Version 1), `keller37.meta` mit neuem Feld `storyRuns: { [storyId]: { lastPlayed: ms, endings: [ids] } }`.
- Kein `alert/confirm/prompt`, kein `onclick=""`, UI-Sprache Deutsch, Mobile ≥ 400 px ohne horizontales Scrollen, Reduced-Motion respektiert.
- Bedingungs-Sprache exakt wie Spec §6; Effekte exakt wie Spec §7; Platzhalter in Story-Szenen: `{{day}}`, `{{balance}}` (formatiert) und jede Story-Variable direkt per Namen (`{{schuld}}` formatiert als Geld wenn `hud.fmt === 'money'`, sonst Zahl).
- Job-Lohn läuft über `Game.applyDelta` (kein Spin, kein `afterSpin`); Lohnformeln: Spüler `hits*5 − breaks*10`, Taxi `passengers*15 − tickets*50` (kann negativ sein, wird dann abgezogen).
- Story 1 schaltet den Raum `life` **nicht** frei (Abweichung von Spec §9, Ruling: ohne Tinder gibt es keinen Liebeskummer, der Raum wäre leer).
- Commit-Nachrichten Deutsch (`feat:`/`fix:`/`docs:`), Trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` (bzw. das Modell des Subagents).
- Verifikationswerkzeuge: `node tests/run-selftest.mjs`, `tests/dom-selftest.sh`, `tests/screenshot.sh out.png "?mode=story&story=schuld&fresh"`, CDP-Skripte nach dem Muster von `docs/superpowers/checklist-2026-09-15.md` (python3 + websockets, `--remote-debugging-port`).
- Dev-Query-Parameter (Task 2/3): `?mode=free|story` (Titel überspringen), `?story=<id>` (Story erzwingen, impliziert `mode=story`), `?day=<n>` (nur mit `fresh`), `?job=<id>` (Jobbörse überspringen, Job direkt), `?ending=<id>` (Ende abspielen), `?scene=`, `?screen=`, `?selftest`, `?fresh` (löscht **beide** Spielstände).

---

### Task 1: StoryRules – pure Engine-Regeln (TDD)

**Files:**
- Modify: `keller37.html` (neuer Block `<script id="story-rules">` nach `gameover`; Tests in `selftest`)
- Modify: `tests/run-selftest.mjs` (lädt `story-rules` und `story-probe`, wenn vorhanden)

**Interfaces:**
- Produces: `StoryRules.cmp(op, a, b)`, `StoryRules.check(cond, s)` → boolean (wirft `Error('Ungültige Bedingung: …')` bei unbekannter Form), `StoryRules.applyEffect(s, eff)` → `{ force?: string, loseDay?: boolean, scene?: string }` (pure Effekte werden direkt auf `s` angewendet, nicht-pure zurückgemeldet), `StoryRules.pickStory(ids, storyRuns, rng)` → id, `StoryRules.chapterFor(story, s)` → chapter | null, `StoryRules.dueEvents(story, s, at)` → events[], `StoryRules.ending(story, s)` → ending | null, `StoryRules.advanceDay(s)`, `StoryRules.jobAvailable(job, s)` → `{ ok, reason }`, `StoryRules.spuelerPay(hits, breaks)`, `StoryRules.taxiPay(passengers, tickets)`, `StoryRules.validate(story, sceneIds, jobIds)` → `[]` oder Liste von Fehlertexten, `StoryRules.freshStoryPart(story)` → das `story`-Teilobjekt des Spielstands.
- Story-Objekt-Form (für alle späteren Tasks verbindlich):
```js
{
  id, title, days, dev?,                       // dev: true → nie zufällig gezogen
  start: { balance, unlocked: { jobs: [], doors: [], rooms: [] }, vars: {} },
  varMax: { vertrauen: 10 },                   // optional, Clamp für add
  hud: [ { var, label, fmt?: 'money', max?, tone? } ],
  goal: (s) => 'Text',                         // Text rechts in der Tagesleiste
  lockReason: { roulette: 'Vito sagt nein' },  // optional, Default 'Noch geschlossen'
  intro: sceneId,
  scenes: { [sceneId]: panels },               // werden von der Engine in Cutscene registriert
  chapters: [ { id, title, when, intro?, unlock?: { jobs, doors, rooms } } ],
  events: [ { id, when, once?: true, at: 'night'|'morning'|'spin:after', scene?, effects?: [] } ],
  jobScenes: { [jobId]: [sceneIds] },
  endings: [ { id, title, priority, when?, scene, fallback?: true } ],
}
```
- Spielstand-Teil `s.story`: `{ id, day, phase, vars, flags, unlocked: {jobs, doors, rooms}, jobsDone: {}, jobToday: null, seen: [], seenJobScenes: {}, ended: null, stats: { earned: 0, gambled: 0, jobs: 0 } }`.

- [ ] **Step 1: Node-Runner erweitern**

In `tests/run-selftest.mjs` die Zeile `for (const id of ['rules', 'util', 'state', 'bus', 'selftest']) {` ersetzen durch:

```js
for (const id of ['rules', 'util', 'state', 'bus', 'story-rules', 'story-probe', 'selftest']) {
```

- [ ] **Step 2: Failing Tests schreiben** – vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- StoryRules ---- */
const storyBase = (o = {}) => Object.assign(base({ balance: 500 }), {
  story: Object.assign({
    id: 'probe', day: 1, phase: 'morning', vars: { schuld: 50000, vertrauen: 2 }, flags: { a: true },
    unlocked: { jobs: ['spueler'], doors: ['slots'], rooms: ['bar'] }, jobsDone: { tuersteher: 3 }, jobToday: null,
    seen: [], seenJobScenes: {}, ended: null, stats: { earned: 0, gambled: 0, jobs: 0 },
  }, o),
});
T.test('StoryRules.cmp', () => {
  T.ok(StoryRules.cmp('gte', 5, 5)); T.ok(!StoryRules.cmp('gt', 5, 5)); T.ok(StoryRules.cmp('lte', 4, 5));
  T.ok(StoryRules.cmp('lt', 4, 5)); T.ok(StoryRules.cmp('eq', 5, 5)); T.ok(StoryRules.cmp('ne', 4, 5));
});
T.test('StoryRules.check: day/balance/var', () => {
  const s = storyBase({ day: 10 });
  T.ok(StoryRules.check({ day: { gte: 10 } }, s)); T.ok(!StoryRules.check({ day: { gt: 10 } }, s));
  T.ok(StoryRules.check({ balance: { gte: 500 } }, s)); T.ok(!StoryRules.check({ balance: { lt: 500 } }, s));
  T.ok(StoryRules.check({ var: 'vertrauen', gte: 2 }, s)); T.ok(!StoryRules.check({ var: 'vertrauen', gt: 2 }, s));
  T.ok(StoryRules.check({ var: 'unbekannt', lte: 0 }, s), 'fehlende Variable zählt als 0');
});
T.test('StoryRules.check: flag/jobDone/unlocked/all/any/not', () => {
  const s = storyBase();
  T.ok(StoryRules.check({ flag: 'a' }, s)); T.ok(!StoryRules.check({ flag: 'b' }, s));
  T.ok(StoryRules.check({ notFlag: 'b' }, s)); T.ok(!StoryRules.check({ notFlag: 'a' }, s));
  T.ok(StoryRules.check({ jobDone: 'tuersteher', gte: 3 }, s)); T.ok(!StoryRules.check({ jobDone: 'croupier', gte: 1 }, s));
  T.ok(StoryRules.check({ unlocked: 'spueler' }, s)); T.ok(StoryRules.check({ unlocked: 'slots' }, s)); T.ok(!StoryRules.check({ unlocked: 'taxi' }, s));
  T.ok(StoryRules.check({ all: [{ flag: 'a' }, { day: { gte: 1 } }] }, s));
  T.ok(!StoryRules.check({ all: [{ flag: 'a' }, { flag: 'b' }] }, s));
  T.ok(StoryRules.check({ any: [{ flag: 'b' }, { flag: 'a' }] }, s));
  T.ok(StoryRules.check({ not: { flag: 'b' } }, s));
  T.ok(StoryRules.check(undefined, s), 'keine Bedingung = wahr');
});
T.test('StoryRules.check: ungültig wirft', () => {
  let threw = false;
  try { StoryRules.check({ foo: 1 }, storyBase()); } catch (e) { threw = /Ungültige Bedingung/.test(e.message); }
  T.ok(threw);
});
T.test('StoryRules.applyEffect: var add/set mit Clamp, flag, balance, unlock', () => {
  const s = storyBase();
  const story = { varMax: { vertrauen: 10 } };
  T.eq(StoryRules.applyEffect(s, { var: 'vertrauen', add: 20 }, story), {});
  T.eq(s.story.vars.vertrauen, 10);
  StoryRules.applyEffect(s, { var: 'vertrauen', add: -30 }, story); T.eq(s.story.vars.vertrauen, 0);
  StoryRules.applyEffect(s, { var: 'schuld', set: 0 }, story); T.eq(s.story.vars.schuld, 0);
  StoryRules.applyEffect(s, { var: 'neu', add: 2 }, story); T.eq(s.story.vars.neu, 2);
  StoryRules.applyEffect(s, { flag: 'x' }, story); T.eq(s.story.flags.x, true);
  StoryRules.applyEffect(s, { unflag: 'x' }, story); T.eq(s.story.flags.x, false);
  StoryRules.applyEffect(s, { balance: -250 }, story); T.eq(s.balance, 250);
  StoryRules.applyEffect(s, { balancePct: -20, min: 100 }, story); T.eq(s.balance, 200);
  StoryRules.applyEffect(s, { unlock: { jobs: ['taxi', 'spueler'], doors: ['roulette'] } }, story);
  T.eq(s.story.unlocked.jobs, ['spueler', 'taxi']); T.eq(s.story.unlocked.doors, ['slots', 'roulette']);
});
T.test('StoryRules.applyEffect: nicht-pure Effekte werden gemeldet', () => {
  const s = storyBase();
  T.eq(StoryRules.applyEffect(s, { force: 'duel' }, {}), { force: 'duel' });
  T.eq(StoryRules.applyEffect(s, { loseDay: true }, {}), { loseDay: true });
  T.eq(StoryRules.applyEffect(s, { scene: 'x.y' }, {}), { scene: 'x.y' });
});
T.test('StoryRules.pickStory: am längsten nicht gespielt, dev nie', () => {
  const stories = [{ id: 'a' }, { id: 'b' }, { id: 'c', dev: true }];
  T.eq(StoryRules.pickStory(stories, { a: { lastPlayed: 5 }, b: { lastPlayed: 3 } }, seq(0)), 'b');
  T.eq(StoryRules.pickStory(stories, { a: { lastPlayed: 5 } }, seq(0)), 'b', 'nie gespielt zählt als ältestes');
  T.eq(StoryRules.pickStory(stories, {}, seq(0)), 'a');
  T.eq(StoryRules.pickStory(stories, {}, seq(0.99)), 'b', 'Gleichstand → rng');
  T.eq(StoryRules.pickStory([{ id: 'a' }], {}, seq(0.99)), 'a');
});
const probeStory = () => ({
  id: 'p', title: 'P', days: 3,
  start: { balance: 50, unlocked: { jobs: [], doors: [], rooms: [] }, vars: { x: 0 } },
  chapters: [
    { id: 'k1', title: 'Eins', when: { day: { gte: 1 } }, unlock: { jobs: ['spueler'] } },
    { id: 'k2', title: 'Zwei', when: { day: { gte: 2 } }, intro: 'p.k2', unlock: { doors: ['slots'] } },
  ],
  events: [
    { id: 'e1', when: { day: { eq: 2 } }, once: true, at: 'night', scene: 'p.e1' },
    { id: 'e2', when: { var: 'x', gte: 1 }, at: 'morning', effects: [{ flag: 'y' }] },
  ],
  jobScenes: {},
  endings: [
    { id: 'gut', title: 'Gut', priority: 2, when: { var: 'x', gte: 5 }, scene: 'p.gut' },
    { id: 'mid', title: 'Mittel', priority: 1, when: { flag: 'y' }, scene: 'p.mid' },
    { id: 'aus', title: 'Aus', priority: 0, scene: 'p.aus', fallback: true },
  ],
  scenes: { 'p.k2': [], 'p.e1': [], 'p.gut': [], 'p.mid': [], 'p.aus': [] },
});
T.test('StoryRules.chapterFor: höchstes passendes Kapitel', () => {
  const st = probeStory();
  T.eq(StoryRules.chapterFor(st, storyBase({ day: 1 })).id, 'k1');
  T.eq(StoryRules.chapterFor(st, storyBase({ day: 2 })).id, 'k2');
  T.eq(StoryRules.chapterFor(st, storyBase({ day: 0 })), null);
});
T.test('StoryRules.dueEvents: at, when, once/seen', () => {
  const st = probeStory();
  T.eq(StoryRules.dueEvents(st, storyBase({ day: 2 }), 'night').map((e) => e.id), ['e1']);
  T.eq(StoryRules.dueEvents(st, storyBase({ day: 2, seen: ['e1'] }), 'night'), []);
  T.eq(StoryRules.dueEvents(st, storyBase({ day: 2 }), 'morning'), []);
  T.eq(StoryRules.dueEvents(st, storyBase({ day: 2, vars: { x: 1 } }), 'morning').map((e) => e.id), ['e2']);
});
T.test('StoryRules.ending: Priorität, Fallback nur nach Ablauf', () => {
  const st = probeStory();
  T.eq(StoryRules.ending(st, storyBase({ day: 2 })), null);
  T.eq(StoryRules.ending(st, storyBase({ day: 2, flags: { y: true } })).id, 'mid');
  T.eq(StoryRules.ending(st, storyBase({ day: 2, flags: { y: true }, vars: { x: 5 } })).id, 'gut');
  T.eq(StoryRules.ending(st, storyBase({ day: 4 })).id, 'aus', 'Tag > days → Fallback');
});
T.test('StoryRules.advanceDay', () => {
  const s = storyBase({ day: 3, phase: 'evening', jobToday: 'spueler' });
  StoryRules.advanceDay(s);
  T.eq([s.story.day, s.story.phase, s.story.jobToday], [4, 'morning', null]);
});
T.test('StoryRules.jobAvailable', () => {
  const s = storyBase({ jobToday: null });
  T.eq(StoryRules.jobAvailable({ id: 'spueler' }, s), { ok: true });
  T.eq(StoryRules.jobAvailable({ id: 'taxi' }, s), { ok: false, reason: 'locked' });
  s.story.unlocked.jobs.push('taxi', 'croupier');
  T.eq(StoryRules.jobAvailable({ id: 'taxi', requires: { balance: { gte: 200 } }, requireText: 'Kaution 200 €' }, s), { ok: true });
  s.balance = 100;
  T.eq(StoryRules.jobAvailable({ id: 'taxi', requires: { balance: { gte: 200 } }, requireText: 'Kaution 200 €' }, s), { ok: false, reason: 'Kaution 200 €' });
  s.story.jobToday = 'spueler';
  T.eq(StoryRules.jobAvailable({ id: 'spueler' }, s), { ok: false, reason: 'done' });
});
T.test('StoryRules Lohn', () => {
  T.eq(StoryRules.spuelerPay(10, 0), 50); T.eq(StoryRules.spuelerPay(7, 3), 5); T.eq(StoryRules.spuelerPay(0, 10), -100);
  T.eq(StoryRules.taxiPay(12, 1), 130); T.eq(StoryRules.taxiPay(0, 3), -150);
});
T.test('StoryRules.validate: Referenzen und Fallback', () => {
  T.eq(StoryRules.validate(probeStory(), ['p.k2', 'p.e1', 'p.gut', 'p.mid', 'p.aus'], ['spueler']), []);
  const bad = probeStory(); bad.endings.pop(); bad.chapters[1].intro = 'fehlt'; bad.chapters[0].unlock.jobs = ['nix'];
  const errs = StoryRules.validate(bad, ['p.e1', 'p.gut', 'p.mid'], ['spueler']);
  T.ok(errs.some((e) => /fehlt/.test(e))); T.ok(errs.some((e) => /nix/.test(e))); T.ok(errs.some((e) => /Fallback/.test(e)));
});
T.test('StoryRules.freshStoryPart', () => {
  const p = StoryRules.freshStoryPart(probeStory());
  T.eq(p.day, 1); T.eq(p.phase, 'morning'); T.eq(p.vars, { x: 0 }); T.eq(p.unlocked, { jobs: [], doors: [], rooms: [] });
  T.eq(p.stats, { earned: 0, gambled: 0, jobs: 0 });
});
```

- [ ] **Step 3: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs` → FAIL-Zeilen `StoryRules is not defined`, Exit 1.

- [ ] **Step 4: Block einfügen** – nach `</script>` von `gameover`:

```html
<script id="story-rules">
/* ================= STORY RULES – pure Engine-Regeln, kein DOM ================= */
const StoryRules = {
  OPS: ['eq', 'ne', 'gte', 'lte', 'gt', 'lt'],
  cmp(op, a, b) {
    switch (op) {
      case 'eq': return a === b; case 'ne': return a !== b;
      case 'gte': return a >= b; case 'lte': return a <= b;
      case 'gt': return a > b; case 'lt': return a < b;
      default: throw new Error(`Ungültige Bedingung: Operator ${op}`);
    }
  },
  _ops(obj, value) {
    const keys = Object.keys(obj).filter((k) => StoryRules.OPS.includes(k));
    if (!keys.length) throw new Error(`Ungültige Bedingung: ${JSON.stringify(obj)}`);
    return keys.every((k) => StoryRules.cmp(k, value, obj[k]));
  },
  check(cond, s) {
    if (cond == null) return true;
    const st = s.story;
    if ('all' in cond) return cond.all.every((c) => StoryRules.check(c, s));
    if ('any' in cond) return cond.any.some((c) => StoryRules.check(c, s));
    if ('not' in cond) return !StoryRules.check(cond.not, s);
    if ('day' in cond) return StoryRules._ops(cond.day, st.day);
    if ('balance' in cond) return StoryRules._ops(cond.balance, s.balance);
    if ('var' in cond) return StoryRules._ops(cond, st.vars[cond.var] || 0);
    if ('jobDone' in cond) return StoryRules._ops(cond, st.jobsDone[cond.jobDone] || 0);
    if ('flag' in cond) return !!st.flags[cond.flag];
    if ('notFlag' in cond) return !st.flags[cond.notFlag];
    if ('unlocked' in cond) return ['jobs', 'doors', 'rooms'].some((k) => st.unlocked[k].includes(cond.unlocked));
    throw new Error(`Ungültige Bedingung: ${JSON.stringify(cond)}`);
  },
  applyEffect(s, eff, story = {}) {
    const st = s.story;
    if ('var' in eff) {
      const max = (story.varMax || {})[eff.var];
      let v = 'set' in eff ? eff.set : (st.vars[eff.var] || 0) + (eff.add || 0);
      if (max != null) v = Math.min(max, v);
      if ('add' in eff) v = Math.max(0, v);
      st.vars[eff.var] = v;
      return {};
    }
    if ('flag' in eff) { st.flags[eff.flag] = true; return {}; }
    if ('unflag' in eff) { st.flags[eff.unflag] = false; return {}; }
    if ('balance' in eff) { s.balance += eff.balance; return {}; }
    if ('balancePct' in eff) { s.balance += Math.round(s.balance * eff.balancePct / 100); if (eff.min != null) s.balance = Math.max(eff.min, s.balance); return {}; }
    if ('unlock' in eff) {
      for (const k of ['jobs', 'doors', 'rooms']) for (const id of eff.unlock[k] || []) if (!st.unlocked[k].includes(id)) st.unlocked[k].push(id);
      return {};
    }
    const out = {};
    if ('force' in eff) out.force = eff.force;
    if ('loseDay' in eff) out.loseDay = true;
    if ('scene' in eff) out.scene = eff.scene;
    return out;
  },
  pickStory(stories, storyRuns, rng) {
    const cands = stories.filter((st) => !st.dev);
    const last = (st) => (storyRuns[st.id] && storyRuns[st.id].lastPlayed) || 0;
    const min = Math.min(...cands.map(last));
    const oldest = cands.filter((st) => last(st) === min);
    return oldest[Math.floor(rng() * oldest.length)].id;
  },
  chapterFor(story, s) {
    let found = null;
    for (const ch of story.chapters) if (StoryRules.check(ch.when, s)) found = ch;
    return found;
  },
  dueEvents(story, s, at) {
    return story.events.filter((e) => e.at === at && !(e.once && s.story.seen.includes(e.id)) && StoryRules.check(e.when, s));
  },
  ending(story, s) {
    const sorted = story.endings.filter((e) => !e.fallback).slice().sort((a, b) => b.priority - a.priority);
    for (const e of sorted) if (StoryRules.check(e.when, s)) return e;
    if (s.story.day > story.days) return story.endings.find((e) => e.fallback) || null;
    return null;
  },
  advanceDay(s) { s.story.day++; s.story.phase = 'morning'; s.story.jobToday = null; },
  jobAvailable(job, s) {
    const st = s.story;
    if (!st.unlocked.jobs.includes(job.id)) return { ok: false, reason: 'locked' };
    if (st.jobToday) return { ok: false, reason: 'done' };
    if (job.requires && !StoryRules.check(job.requires, s)) return { ok: false, reason: job.requireText || 'Voraussetzung fehlt' };
    return { ok: true };
  },
  spuelerPay(hits, breaks) { return hits * 5 - breaks * 10; },
  taxiPay(passengers, tickets) { return passengers * 15 - tickets * 50; },
  validate(story, sceneIds, jobIds) {
    const errs = [];
    const scene = (id, where) => { if (id && !sceneIds.includes(id)) errs.push(`${story.id}: Szene "${id}" fehlt (${where})`); };
    const jobs = (list, where) => (list || []).forEach((j) => { if (!jobIds.includes(j)) errs.push(`${story.id}: Job "${j}" unbekannt (${where})`); });
    scene(story.intro, 'intro');
    jobs(story.start && story.start.unlocked && story.start.unlocked.jobs, 'start');
    for (const ch of story.chapters || []) { scene(ch.intro, ch.id); jobs(ch.unlock && ch.unlock.jobs, ch.id); }
    for (const e of story.events || []) { scene(e.scene, e.id); for (const eff of e.effects || []) { scene(eff.scene, e.id); jobs(eff.unlock && eff.unlock.jobs, e.id); } }
    for (const [job, list] of Object.entries(story.jobScenes || {})) { jobs([job], 'jobScenes'); list.forEach((id) => scene(id, `jobScenes.${job}`)); }
    for (const e of story.endings || []) scene(e.scene, e.id);
    if ((story.endings || []).filter((e) => e.fallback).length !== 1) errs.push(`${story.id}: genau ein Fallback-Ende nötig`);
    return errs;
  },
  freshStoryPart(story) {
    return {
      id: story.id, day: 1, phase: 'morning',
      vars: Object.assign({}, story.start.vars), flags: {},
      unlocked: { jobs: [...story.start.unlocked.jobs], doors: [...story.start.unlocked.doors], rooms: [...story.start.unlocked.rooms] },
      jobsDone: {}, jobToday: null, seen: [], seenJobScenes: {}, ended: null,
      stats: { earned: 0, gambled: 0, jobs: 0 },
    };
  },
};
</script>
```

- [ ] **Step 5: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs` → `72 bestanden, 0 fehlgeschlagen` (57 + 15).
Run: `tests/dom-selftest.sh` → `passed=72 failed=0`.

- [ ] **Step 6: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(story): StoryRules – Bedingungen, Effekte, Enden, Lohn (pure)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: State-Modi, Titelscreen, Boot

**Files:**
- Modify: `keller37.html` (`state`-Block; `ui`-Block `mountShell`; neuer Block `<script id="title">` nach `story-rules`; Template `tpl-title`; CSS Sektion 6; `boot`; Tests)

**Interfaces:**
- Produces: `State.mode` (`'free'|'story'`), `State.STORY_KEY = 'keller37.story'`, `State.keyFor(mode)`, `State.setMode(mode)` → `{loaded}` (lädt den Spielstand des Modus in `State.s`), `State.freshStory(story)` (Sandbox-`fresh()` + `story.start.balance` + `story: StoryRules.freshStoryPart(story)`), `State.startStory(story)` (setzt Modus story, frischen Story-Stand, speichert), `State.meta.storyRuns`, `State.hasStoryRun()`; `Title.show()` (Overlay `#title`, gibt Promise auf `'free' | 'story' | 'newstory'`), `Title.hide()`; `UI.mountShell()` idempotent (Escape-Listener nur einmal), Wallet-Button 🚪 → `Title.open()` (Titel anzeigen, Modus wechseln); Body-Klasse `mode-story` / `mode-free`.
- Consumes: `StoryRules.freshStoryPart`, `Stories.list()` (Task 3 – in Task 2 existiert `Stories` noch nicht; Title zeigt bis dahin „Story" ohne Fortsetzen-Text: Guard `typeof Stories !== 'undefined'`).

- [ ] **Step 1: Failing Tests** – vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- State: Modi ---- */
T.test('State.setMode lädt getrennte Spielstände', () => {
  const st = memStorage();
  State.init(st);
  T.eq(State.mode, 'free');
  State.s.balance = 777; State.save();
  const story = { id: 'p', start: { balance: 50, unlocked: { jobs: [], doors: [], rooms: [] }, vars: { x: 1 } }, chapters: [], events: [], endings: [] };
  State.startStory(story);
  T.eq(State.mode, 'story'); T.eq(State.s.balance, 50); T.eq(State.s.story.id, 'p'); T.eq(State.s.story.vars, { x: 1 });
  T.ok(st.getItem('keller37.story').includes('"id":"p"'));
  T.eq(State.meta.storyRuns.p.endings, []);
  T.ok(State.meta.storyRuns.p.lastPlayed > 0);
  State.setMode('free');
  T.eq(State.s.balance, 777);
  T.eq(State.setMode('story'), { loaded: true }); T.eq(State.s.story.id, 'p');
  T.ok(State.hasStoryRun());
});
T.test('State.init: meta.storyRuns wird aufgefüllt, Story-Save fehlt → hasStoryRun false', () => {
  const st = memStorage();
  st.setItem('keller37.meta', JSON.stringify({ v: 1, achievements: [], muted: false, gameOvers: 0 }));
  State.init(st);
  T.eq(State.meta.storyRuns, {});
  T.ok(!State.hasStoryRun());
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs` → FAIL `State.startStory is not a function` u.ä.

- [ ] **Step 3: State erweitern** – im `state`-Block:

`freshMeta()` ersetzen durch:
```js
  freshMeta() { return { v: 1, achievements: [], muted: false, gameOvers: 0, storyRuns: {} }; },
```
Nach `META_KEY: 'keller37.meta',` einfügen:
```js
  STORY_KEY: 'keller37.story',
  mode: 'free',
  keyFor(mode) { return mode === 'story' ? this.STORY_KEY : this.KEY; },
```
`_read` bleibt; in `_read` nach `if (f.stats) …` ergänzen:
```js
      if (f.storyRuns) merged.storyRuns = Object.assign({}, p.storyRuns || {});
```
`init` ersetzen durch:
```js
  init(storage) {
    this.storage = storage;
    this.mode = 'free';
    const s = this._read(this.KEY, () => this.fresh());
    const m = this._read(this.META_KEY, () => this.freshMeta());
    this.s = s.value;
    this.meta = m.value;
    if (!this.meta.storyRuns) this.meta.storyRuns = {};
    return { loaded: s.loaded, discarded: s.discarded || m.discarded };
  },
  setMode(mode) {
    this.mode = mode;
    const r = this._read(this.keyFor(mode), () => this.fresh());
    this.s = r.value;
    if (mode === 'story' && !this.s.story) return { loaded: false };
    return { loaded: r.loaded };
  },
  hasStoryRun() {
    try { const raw = this.storage.getItem(this.STORY_KEY); if (!raw) return false; const p = JSON.parse(raw); return !!(p && p.v === this.VERSION && p.story && !p.story.ended); } catch (e) { return false; }
  },
  freshStory(story) {
    const s = this.fresh();
    s.balance = story.start.balance;
    s.flags.intro = true;
    s.story = StoryRules.freshStoryPart(story);
    return s;
  },
  startStory(story) {
    this.mode = 'story';
    this.s = this.freshStory(story);
    if (!this.meta.storyRuns[story.id]) this.meta.storyRuns[story.id] = { lastPlayed: 0, endings: [] };
    this.meta.storyRuns[story.id].lastPlayed = Date.now();
    this.saveMeta();
    this.save();
  },
```
`save()` ersetzen durch:
```js
  save() { try { this.storage.setItem(this.keyFor(this.mode), JSON.stringify(this.s)); } catch (e) { /* privater Modus o.ä. */ } },
```

- [ ] **Step 4: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs` → `74 bestanden, 0 fehlgeschlagen`.

- [ ] **Step 5: Titelscreen** – Template vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-title">
  <div class="title-inner">
    <div class="title-neon neon" style="--neon: var(--neon-amber)">Keller 37</div>
    <p class="title-sub">Fünfzig Euro. Sechs Türen. Kein Ausweg.</p>
    <div class="title-doors">
      <div class="door title-door" data-choice="story" style="--neon: var(--neon-red)"><div class="sign">Story</div><div class="glyph">📖</div><div class="chalk-tag" id="titleStoryTag">Neue Story</div><div class="knob"></div></div>
      <div class="door title-door" data-choice="free" style="--neon: var(--neon-green)"><div class="sign">Freies Spiel</div><div class="glyph">🎰</div><div class="chalk-tag" id="titleFreeTag">Der Keller wie er ist</div><div class="knob"></div></div>
    </div>
    <button class="btn ghost sm hidden" id="titleNewStory">Neue Story beginnen</button>
    <div class="title-foot"><button class="icon-btn" id="titleMute">🔊</button></div>
  </div>
</template>
```

CSS vor `/* ==== 7. ANIMATIONEN ==== */`:
```css
/* -- Titelscreen -- */
#title { position: fixed; inset: 0; z-index: 75; background: radial-gradient(ellipse at 50% 20%, #1b1a12 0%, var(--bg) 60%); display: flex; align-items: center; justify-content: center; overflow: auto; animation: fadeIn .3s ease both; }
#title[hidden] { display: none; }
.title-inner { display: flex; flex-direction: column; align-items: center; gap: 18px; padding: 24px 16px; width: 100%; max-width: 760px; }
.title-neon { font-size: 4.5rem; line-height: 1; }
.title-sub { color: var(--dim); font-family: var(--font-mono); font-size: .95rem; }
.title-doors { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; width: 100%; }
.title-door { height: 240px; }
.title-foot { display: flex; gap: 8px; }
@media (max-width: 760px) { .title-neon { font-size: 3rem; } .title-doors { grid-template-columns: 1fr; } .title-door { height: 170px; } }
```

HTML-Element nach `<div id="cutscene" hidden></div>`:
```html
<div id="title" hidden></div>
```

Block `<script id="title">` nach `story-rules`:
```html
<script id="title">
/* ================= TITELSCREEN – Modus-Wahl ================= */
const Title = {
  root: null,
  show() {
    return new Promise((resolve) => {
      const root = qs('#title');
      root.innerHTML = '';
      root.appendChild(qs('#tpl-title').content.cloneNode(true));
      root.hidden = false;
      document.body.classList.add('title-open');
      const hasRun = State.hasStoryRun();
      const tag = qs('#titleStoryTag', root);
      if (hasRun && typeof Stories !== 'undefined') {
        const info = Stories.runInfo();
        tag.textContent = `Fortsetzen · ${info.title} · Tag ${info.day}/${info.days}`;
        qs('#titleNewStory', root).classList.remove('hidden');
      } else {
        tag.textContent = 'Neue Story';
      }
      qs('#titleMute', root).textContent = State.meta.muted ? '🔇' : '🔊';
      qs('#titleMute', root).addEventListener('click', (e) => { SFX.setMuted(!State.meta.muted); e.currentTarget.textContent = State.meta.muted ? '🔇' : '🔊'; });
      const done = (v) => { Title.hide(); resolve(v); };
      qsa('.title-door', root).forEach((d) => {
        d.addEventListener('mouseenter', () => SFX.play('neonBuzz'));
        d.addEventListener('click', () => { SFX.play('click'); done(d.dataset.choice === 'story' ? (hasRun ? 'story' : 'newstory') : 'free'); });
      });
      qs('#titleNewStory', root).addEventListener('click', () => { SFX.play('click'); done('newstory'); });
    });
  },
  hide() { const root = qs('#title'); root.hidden = true; root.innerHTML = ''; document.body.classList.remove('title-open'); },
  /* Vom Wallet-Knopf: zurück zum Titel, dann Modus wechseln */
  async open() {
    if (Cutscene.active || Game.inFlight > 0) { UI.toast({ icon: '⏳', title: 'Erst die Runde beenden' }); return; }
    State.save();
    const choice = await Title.show();
    await Modes.enter(choice);
  },
};
/* Modus betreten – Story-Teil kommt in Task 3 (Story.enter); hier nur das freie Spiel */
const Modes = {
  async enter(choice) {
    if (choice === 'free') {
      State.setMode('free');
      document.body.classList.remove('mode-story'); document.body.classList.add('mode-free');
      UI.mountShell();
      await UI.show('hub');
      if (Rules.isGameOver(State.s)) await Bus.emit('gameover', {});
      else if (!State.s.flags.intro) { await Cutscene.play('intro'); State.s.flags.intro = true; State.save(); }
      return;
    }
    if (typeof Story !== 'undefined') await Story.enter(choice);
    else { UI.toast({ icon: '🚧', title: 'Story kommt noch', tone: 'info' }); await Modes.enter('free'); }
  },
};
</script>
```

- [ ] **Step 6: `UI.mountShell` idempotent + Titel-Knopf** – im `ui`-Block `mountShell` ersetzen:

```js
  mountShell() {
    const w = qs('#wallet');
    w.innerHTML = '';
    w.append(
      h('button', { class: 'brand neon', id: 'brand', style: '--neon: var(--neon-amber)', title: 'Zurück in den Gang', onclick: () => UI.show('hub') }, 'Keller 37'),
      h('div', { class: 'wallet-mid' }, h('div', { class: 'luck', id: 'luck' }), h('div', { class: 'notes', id: 'notes' })),
      h('div', { class: 'wallet-right' },
        h('button', { class: 'icon-btn', id: 'mute', title: 'Ton an/aus', onclick: () => { SFX.setMuted(!State.meta.muted); UI.renderWallet(); } }, '🔊'),
        h('button', { class: 'icon-btn', id: 'newgame', title: 'Neues Spiel', onclick: () => Bus.emit('newgame.request', {}) }, '↺'),
        h('button', { class: 'icon-btn', id: 'toTitle', title: 'Zum Titel', onclick: () => Title.open() }, '🚪'),
        h('div', { class: 'balance money-live', id: 'balance' }, '0 €')),
    );
    this.shownBalance = State.s.balance;
    this.setBalance(State.s.balance, { animate: false });
    this.renderWallet();
    this.renderSide();
    if (!this._shellKeys) {
      this._shellKeys = true;
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && qs('#cutscene').hidden && qs('#title').hidden && UI.current && UI.current.id !== 'hub') UI.show('hub');
      });
    }
  },
```

- [ ] **Step 7: Boot umbauen** – Inhalt von `<script id="boot">` ersetzen:

```js
/* ================= BOOT ================= */
(async function boot() {
  const params = new URLSearchParams(location.search);
  let storage;
  try { storage = window.localStorage; storage.getItem('x'); } catch (e) {
    storage = { data: {}, getItem(k) { return k in this.data ? this.data[k] : null; }, setItem(k, v) { this.data[k] = String(v); }, removeItem(k) { delete this.data[k]; } };
  }
  if (params.has('fresh')) { try { storage.removeItem('keller37.state'); storage.removeItem('keller37.story'); } catch (e) { /* egal */ } }
  const { loaded, discarded } = State.init(storage);
  UI.mountShell();
  if (discarded) UI.toast({ icon: '🗑️', title: 'Alter Spielstand verworfen', text: 'Unlesbar oder falsche Version – neues Spiel.', tone: 'loss', ms: 5000 });
  if (params.has('selftest')) {
    const r = SelfTest.run();
    document.documentElement.dataset.selftest = `passed=${r.passed} failed=${r.failed}`;
    console.log('[selftest]', r);
    r.failures.forEach((f) => console.error('[selftest] FAIL', f));
    UI.toast({ icon: r.failed ? '❌' : '✅', title: 'Selbsttest', text: `${r.passed} bestanden, ${r.failed} fehlgeschlagen`, tone: r.failed ? 'loss' : 'win', ms: 6000 });
  }
  const wantsStory = params.has('story') || params.get('mode') === 'story';
  const skipTitle = params.has('mode') || params.has('story') || params.has('screen') || params.has('scene') || params.has('selftest');
  if (wantsStory) { await Modes.enter(State.hasStoryRun() && !params.has('fresh') ? 'story' : 'newstory'); return; }
  if (!skipTitle) { const choice = await Title.show(); await Modes.enter(choice); return; }
  /* Dev-Pfad freies Spiel: wie bisher */
  document.body.classList.add('mode-free');
  await UI.show(params.get('screen') || 'hub');
  let gameOverAtBoot = false;
  if (Rules.isGameOver(State.s)) { gameOverAtBoot = true; await Bus.emit('gameover', {}); }
  if (params.has('scene')) {
    await Cutscene.play(params.get('scene'), { bill: 900, before: 1000, after: 500, price: '1.000 €', debt: 300, stats: { Spins: 12, 'Höchster Kontostand': '1.234 €' } });
  } else if (!State.s.flags.intro && !params.has('screen')) {
    await Cutscene.play('intro');
    State.s.flags.intro = true;
    State.save();
  }
  if (loaded && !gameOverAtBoot && !params.has('screen')) UI.toast({ icon: '💾', title: 'Spielstand geladen', text: `Willkommen zurück. ${UI.fmt(State.s.balance)} in der Tasche.` });
})();
```

Außerdem in `Modes.enter('free')`: nach `await UI.show('hub')` den Willkommens-Toast wie bisher (`if (loaded) …`) – dazu merkt sich `Modes.freeLoaded = loaded` in boot vor dem Aufruf: `Modes.freeLoaded = loaded;` und in `enter('free')`: `if (Modes.freeLoaded && !Rules.isGameOver(State.s)) UI.toast({ icon: '💾', title: 'Spielstand geladen', text: … }); Modes.freeLoaded = false;`.

- [ ] **Step 8: Prüfen**

Run: `node tests/run-selftest.mjs` → 74; `tests/dom-selftest.sh` → `passed=74 failed=0` (der `?selftest`-Pfad überspringt den Titel).
Run: `tests/screenshot.sh /tmp/st-title.png "?fresh"` → Titelscreen: Neonschild, zwei Türen „Story" (rot, Kreide „Neue Story") und „Freies Spiel" (grün), Mute-Knopf.
Run: `tests/screenshot.sh /tmp/st-hub.png "?screen=hub"` → Hub wie bisher (Dev-Pfad ohne Titel), Wallet hat jetzt ein 🚪-Icon.
CDP: Titel → „Freies Spiel" klicken → Hub + Intro-Szene (bei fresh); 🚪 → Titel wieder da, „Freies Spiel" → Hub, Kontostand erhalten. „Story" klicken → Toast „Story kommt noch" und freies Spiel (bis Task 3).

- [ ] **Step 9: Commit**

```bash
git add keller37.html
git commit -m "feat(story): State-Modi, Titelscreen, Boot mit Modus-Wahl

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Story-Engine (Tagesschleife, Sperren, Szenen mit Effekten, erzwungenes Duell) + Probe-Story

**Files:**
- Modify: `keller37.html` (neue Blöcke `<script id="story-engine">` nach `title` und `<script id="story-probe">` nach `job-taxi` – solange `jobs`/`job-*` noch fehlen direkt nach `story-engine`; Template `tpl-daybar`; CSS Sektion 6 + Keyframes; `ui` (`UI.show`, `renderSide`, `renderWallet`, hub-mount); `game-russian` (`start(opts)`, `end`); `gameover` (Story-Guard, ↺); `state` (`peekStory`); Tests)

**Interfaces:**
- Produces: `Stories.define(story)` (registriert `story.scenes` via `Cutscene.define`, speichert), `Stories.get(id)`, `Stories.list()` (ohne `dev`), `Stories.runInfo()` → `{title, day, days}` des gespeicherten Laufs, `Stories.validateAll()` → Fehlerliste (Konsole + Toast bei Fehlern); `Story.story` (aktives Story-Objekt), `Story.enter('story'|'newstory')`, `Story.playScene(id, extra?)` (Ctx-Füllung + Choice-Effekte), `Story.applyEffects(list)`, `Story.morning()`, `Story.evening()`, `Story.night()`, `Story.finish(ending)`, `Story.isLocked(screenId)` → boolean, `Story.lockReason(screenId)`, `Story.roomUnlocked(room)`, `Story.renderDaybar()`, `Story.forceDuel()` → `'player'|'igor'`, `Story.jobDone(jobId, earned)` (setzt `jobToday`, zählt `jobsDone`, `stats.earned/jobs`, geht in den Abend), `Story.allowOnce` (Screen-Id, die trotz Sperre einmal geöffnet werden darf); Bus-Events `story:day {day}`, `story:ended {id, ending}`; `State.peekStory()` → gespeicherter Story-Stand oder null; `Russian.start({forced:true})` → Duell ohne Einsatz, Ergebnis über `Bus.emit('rr:forced', {victim})`, kein `settle`, keine Spital-Szene; Body-Klasse `mode-story`; Screens-Konstanten `Story.DOORS = ['roulette','slots','horses','russian','blackjack','postman']`, `Story.ROOM_OF = { finance: ['bank','mafia'], invest: ['invest'], life: ['life'], vito: ['vito'] }`.
- Story-Probe: `const STORY_PROBE = {…}` (DOM-frei, `dev: true`), registriert, nur per `?story=probe` erreichbar.

- [ ] **Step 1: Failing Tests** – vor `/* --- SELFTEST CASES END --- */`:

```js
/* ---- Story-Probe validiert ---- */
T.test('STORY_PROBE ist gültig', () => {
  T.eq(StoryRules.validate(STORY_PROBE, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']), []);
  T.eq(STORY_PROBE.dev, true);
  T.eq(StoryRules.pickStory([STORY_PROBE, { id: 'x' }], {}, seq(0)), 'x', 'dev-Story wird nie gezogen');
});
T.test('STORY_PROBE: Tagesablauf mit StoryRules', () => {
  const s = Object.assign(base({ balance: 500 }), { story: StoryRules.freshStoryPart(STORY_PROBE) });
  T.eq(StoryRules.chapterFor(STORY_PROBE, s).id, 'k1');
  T.eq(StoryRules.dueEvents(STORY_PROBE, s, 'night').map((e) => e.id), ['n1']);
  StoryRules.applyEffect(s, { var: 'mut', add: 5 }, STORY_PROBE);
  T.eq(s.story.vars.mut, 3, 'varMax clamp');
  T.eq(StoryRules.ending(STORY_PROBE, s).id, 'mutig');
  s.story.vars.mut = 0; s.story.day = 4;
  T.eq(StoryRules.ending(STORY_PROBE, s).id, 'aus');
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen** (`STORY_PROBE is not defined`).

- [ ] **Step 3: `State.peekStory`** – im `state`-Block nach `hasStoryRun()` einfügen:

```js
  peekStory() {
    try { const raw = this.storage.getItem(this.STORY_KEY); if (!raw) return null; const p = JSON.parse(raw); return p && p.v === this.VERSION && p.story ? p : null; } catch (e) { return null; }
  },
```

- [ ] **Step 4: Template, CSS**

Template vor `<!-- /TEMPLATES -->`:
```html
<template id="tpl-daybar">
  <div class="daybar">
    <div class="day-count"><span class="day-label">Tag</span> <span id="dayNum">1</span><span class="day-of">/<span id="dayMax">30</span></span></div>
    <div class="day-phase"><span id="phaseMorning">☀️ Morgen</span><span class="arrow">→</span><span id="phaseEvening">🌙 Abend</span></div>
    <button class="btn solid sm" id="btnSleep">💤 Schlafen</button>
    <div class="day-goal" id="dayGoal"></div>
    <button class="icon-btn" id="btnTitleBack" title="Zum Titel">🚪</button>
  </div>
</template>
```

CSS vor `/* ==== 7. ANIMATIONEN ==== */`:
```css
/* -- Story: Tagesleiste, Sperren, Nacht -- */
body.mode-story #brand { pointer-events: none; }
body.mode-story #newgame, body.mode-story #toTitle { display: none; }
.daybar { position: sticky; top: 58px; z-index: 19; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; padding: 6px 20px; background: rgba(20,17,12,.95); border-bottom: 1px solid rgba(201,162,39,.25); font-family: var(--font-display); letter-spacing: .08em; }
.day-count { font-size: 1.6rem; color: var(--gold-2); }
.day-count .day-label, .day-count .day-of { font-size: 1rem; color: var(--dim); }
.day-phase { display: flex; gap: 8px; align-items: center; font-size: 1rem; color: var(--dim); }
.day-phase .on { color: #fff; text-shadow: 0 0 8px var(--neon-amber); }
.day-phase .arrow { opacity: .5; }
.day-goal { margin-left: auto; font-family: var(--font-mono); font-size: .85rem; color: var(--text); letter-spacing: 0; }
.door.locked { cursor: not-allowed; filter: brightness(.55) saturate(.4); }
.door.locked:hover { transform: none; }
.door.locked:hover::after { opacity: 0; }
.door .boards { position: absolute; inset: 0; pointer-events: none; }
.door .boards span { position: absolute; left: -10%; right: -10%; top: 45%; height: 16px; background: linear-gradient(180deg, #7a5a34, #4a3520); border: 1px solid #2a1c10; box-shadow: 0 3px 6px rgba(0,0,0,.6); transform: rotate(-18deg); }
.door .boards span:last-child { transform: rotate(16deg); top: 55%; }
.door.locked .chalk-tag { color: #ffb3b3; }
#nightfade { position: fixed; inset: 0; z-index: 85; background: #000; display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-size: 4rem; letter-spacing: .2em; color: #fff; text-shadow: 0 0 20px var(--neon-amber); opacity: 0; pointer-events: none; transition: opacity .35s; }
#nightfade.on { opacity: 1; pointer-events: auto; }
@media (max-width: 760px) { .daybar { top: 0; position: static; padding: 6px 12px; gap: 8px; } .day-count { font-size: 1.3rem; } .day-goal { width: 100%; margin-left: 0; } }
```

HTML nach `<div id="title" hidden></div>`: `<div id="nightfade" aria-hidden="true"></div>` und ein leerer Container für die Tagesleiste direkt nach `</header>` (dem `#wallet`): `<div id="daybarSlot"></div>`.

- [ ] **Step 5: Engine-Block** – `<script id="story-engine">` nach `title`:

```html
<script id="story-engine">
/* ================= STORY ENGINE – Tage, Sperren, Szenen, Enden ================= */
const Stories = {
  all: {},
  define(story) {
    for (const [id, panels] of Object.entries(story.scenes || {})) Cutscene.define(id, panels);
    this.all[story.id] = story;
  },
  get(id) { return this.all[id]; },
  list() { return Object.values(this.all).filter((s) => !s.dev); },
  runInfo() {
    const p = State.peekStory();
    if (!p) return null;
    const st = this.get(p.story.id);
    return { id: p.story.id, title: st ? st.title : p.story.id, day: p.story.day, days: st ? st.days : '?' };
  },
  validateAll() {
    const sceneIds = Object.keys(Cutscene.SCENES);
    const jobIds = typeof Jobs !== 'undefined' ? Object.keys(Jobs.POOL) : null;
    const errs = [];
    for (const st of Object.values(this.all)) errs.push(...StoryRules.validate(st, sceneIds, jobIds || (st.start.unlocked.jobs)));
    if (errs.length) { errs.forEach((e) => console.error('[story]', e)); UI.toast({ icon: '🐛', title: 'Story-Daten fehlerhaft', text: errs[0], tone: 'loss', ms: 8000 }); }
    return errs;
  },
};

const Story = {
  DOORS: ['roulette', 'slots', 'horses', 'russian', 'blackjack', 'postman'],
  ROOM_OF: { finance: ['bank', 'mafia'], invest: ['invest'], life: ['life'], vito: ['vito'] },
  story: null,
  allowOnce: null,
  lostDay: false,
  get s() { return State.s.story; },

  /* ---- Einstieg ---- */
  async enter(choice) {
    Stories.validateAll();
    const params = new URLSearchParams(location.search);
    if (choice === 'newstory' && State.hasStoryRun() && !params.has('fresh')) {
      State.setMode('story');
      this.story = Stories.get(State.s.story.id);
      this.setup();
      const c = await Cutscene.play('story.newConfirm', {});
      if (c !== 'yes') return this.enter('story');
    }
    if (choice === 'newstory' || !State.hasStoryRun()) {
      const forced = params.get('story');
      const id = forced && Stories.get(forced) ? forced : StoryRules.pickStory(Stories.list(), State.meta.storyRuns, Math.random);
      const story = Stories.get(id);
      State.startStory(story);
      if (params.has('day') && params.has('fresh')) State.s.story.day = Math.max(1, parseInt(params.get('day'), 10) || 1);
      this.story = story;
      this.setup();
      State.save();
      if (!params.has('day')) await this.playScene(story.intro);
      await this.applyChapter();
      if (params.has('ending')) { const end = story.endings.find((e) => e.id === params.get('ending')); if (end) return this.finish(end); }
      await this.morning();
      return;
    }
    State.setMode('story');
    this.story = Stories.get(State.s.story.id);
    if (!this.story) { UI.toast({ icon: '🐛', title: 'Story unbekannt', text: State.s.story.id, tone: 'loss' }); return Modes.enter('free'); }
    this.setup();
    if (this.s.phase === 'morning') await this.morning(); else await this.evening();
    UI.toast({ icon: '📖', title: this.story.title, text: `Tag ${this.s.day} von ${this.story.days}.` });
  },
  setup() {
    document.body.classList.remove('mode-free'); document.body.classList.add('mode-story');
    UI.mountShell();
    this.renderDaybar();
  },

  /* ---- Kontext & Szenen ---- */
  ctx(extra = {}) {
    const s = State.s;
    const c = { day: this.s.day, balance: UI.fmt(s.balance) };
    for (const [k, v] of Object.entries(this.s.vars)) {
      const hud = (this.story.hud || []).find((h) => h.var === k);
      c[k] = hud && hud.fmt === 'money' ? UI.fmt(v) : String(v);
    }
    return Object.assign(c, extra);
  },
  async playScene(id, extra = {}) {
    if (!id) return undefined;
    const result = await Cutscene.play(id, this.ctx(extra));
    const panels = this.story.scenes[id] || [];
    if (result !== undefined) {
      for (const p of panels) for (const ch of p.choices || []) if (ch.value === result && ch.effects) await this.applyEffects(ch.effects);
    }
    return result;
  },
  async applyEffects(list) {
    for (const eff of list || []) {
      const out = StoryRules.applyEffect(State.s, eff, this.story);
      if (out.scene) await this.playScene(out.scene);
      if (out.force === 'duel') await this.forceDuel();
      if (out.loseDay) this.lostDay = true;
    }
    State.save();
    UI.setBalance(State.s.balance);
    UI.renderWallet(); UI.renderSide();
    this.renderDaybar();
  },
  async runEvents(at) {
    for (const e of StoryRules.dueEvents(this.story, State.s, at)) {
      if (e.once) this.s.seen.push(e.id);
      if (e.scene) await this.playScene(e.scene);
      await this.applyEffects(e.effects || []);
    }
  },
  async applyChapter() {
    const ch = StoryRules.chapterFor(this.story, State.s);
    if (!ch || ch.id === this.s.chapter) return;
    this.s.chapter = ch.id;
    const before = JSON.stringify(this.s.unlocked);
    if (ch.unlock) StoryRules.applyEffect(State.s, { unlock: ch.unlock }, this.story);
    State.save();
    UI.toast({ icon: '📖', title: `Kapitel: ${ch.title}`, tone: 'gold', ms: 4000 });
    if (ch.intro) await this.playScene(ch.intro);
    if (JSON.stringify(this.s.unlocked) !== before) {
      const names = [...(ch.unlock.jobs || []).map((j) => (typeof Jobs !== 'undefined' && Jobs.POOL[j] ? Jobs.POOL[j].name : j)), ...(ch.unlock.doors || []), ...(ch.unlock.rooms || [])];
      UI.toast({ icon: '🔓', title: 'Neu freigeschaltet', text: names.join(' · '), tone: 'info', ms: 5000 });
    }
    UI.renderSide(); this.renderDaybar();
  },

  /* ---- Tagesphasen ---- */
  async morning() {
    this.s.phase = 'morning'; this.lostDay = false;
    State.save(); this.renderDaybar();
    await this.runEvents('morning');
    if (this.lostDay) return this.evening();
    await UI.show(UI.screens.has('jobs') ? 'jobs' : 'hub');
  },
  async evening() {
    this.s.phase = 'evening';
    State.save(); this.renderDaybar();
    await UI.show('hub');
  },
  async night() {
    if (this.s.phase !== 'evening' || Cutscene.active || Game.inFlight > 0) { if (Game.inFlight > 0) UI.toast({ icon: '⏳', title: 'Erst die Runde beenden' }); return; }
    await this.fade(`Nacht ${this.s.day}`);
    await this.runEvents('night');
    let end = StoryRules.ending(this.story, State.s);
    if (end) return this.finish(end);
    StoryRules.advanceDay(State.s);
    State.save();
    await Bus.emit('story:day', { day: this.s.day });
    end = StoryRules.ending(this.story, State.s);
    if (end) return this.finish(end);
    await this.fade(`Tag ${this.s.day}`);
    await this.applyChapter();
    await this.morning();
  },
  async finish(end) {
    this.s.ended = end.id;
    const run = State.meta.storyRuns[this.story.id] || (State.meta.storyRuns[this.story.id] = { lastPlayed: 0, endings: [] });
    if (!run.endings.includes(end.id)) run.endings.push(end.id);
    run.lastPlayed = Date.now();
    State.saveMeta(); State.save();
    const st = this.s.stats;
    const stats = { Tage: this.s.day, Verdient: UI.fmt(st.earned), Verzockt: UI.fmt(st.gambled), Jobs: st.jobs, Ende: end.title };
    const panels = (this.story.scenes[end.scene] || []).map((p) => Object.assign({}, p));
    const last = panels[panels.length - 1];
    last.fx = 'stats';
    last.choices = [{ label: 'Nächste Story', value: 'next', cls: 'red' }, { label: 'Zum Titel', value: 'title', cls: 'ghost' }];
    Cutscene.define('story.ending.tmp', panels);
    const choice = await Cutscene.play('story.ending.tmp', this.ctx({ stats }));
    await Bus.emit('story:ended', { id: this.story.id, ending: end.id });
    if (choice === 'next') return this.enter('newstory');
    const c = await Title.show();
    await Modes.enter(c);
  },
  jobDone(jobId, earned) {
    this.s.jobToday = jobId;
    this.s.jobsDone[jobId] = (this.s.jobsDone[jobId] || 0) + 1;
    this.s.stats.jobs++;
    this.s.stats.earned += Math.max(0, earned);
    State.save();
    return this.evening();
  },

  /* ---- Sperren ---- */
  isLocked(screen) {
    if (State.mode !== 'story' || !this.story) return false;
    if (screen === this.allowOnce) { this.allowOnce = null; return false; }
    if (this.DOORS.includes(screen)) {
      if (screen === 'postman') return true; // Post ist ein Job (morgens)
      return !this.s.unlocked.doors.includes(screen);
    }
    if (this.ROOM_OF[screen]) return !this.ROOM_OF[screen].some((r) => this.s.unlocked.rooms.includes(r));
    return false;
  },
  lockReason(screen) {
    if (screen === 'postman') return 'Morgens, an der Pinnwand';
    return (this.story.lockReason || {})[screen] || 'Noch geschlossen';
  },
  roomUnlocked(room) { return State.mode !== 'story' || this.s.unlocked.rooms.includes(room); },
  decorateHub(root) {
    qsa('.door', root).forEach((d) => {
      const id = d.dataset.screen;
      if (!this.isLocked(id)) return;
      d.classList.add('locked');
      d.append(h('div', { class: 'boards' }, h('span'), h('span')));
      qs('.chalk-tag', d).textContent = this.lockReason(id);
    });
  },

  /* ---- HUD ---- */
  hudNotes() {
    return (this.story.hud || []).map((hd) => {
      const v = this.s.vars[hd.var] || 0;
      const txt = hd.fmt === 'money' ? UI.fmt(v) : (hd.max ? `${v}/${hd.max}` : String(v));
      return h('span', { class: `note ${hd.tone || 'gold'}` }, `${hd.label} ${txt}`);
    });
  },
  renderDaybar() {
    const slot = qs('#daybarSlot');
    if (State.mode !== 'story' || !this.story) { slot.innerHTML = ''; return; }
    if (!qs('.daybar', slot)) {
      slot.appendChild(qs('#tpl-daybar').content.cloneNode(true));
      qs('#btnSleep', slot).addEventListener('click', () => { SFX.play('click'); Story.night(); });
      qs('#btnTitleBack', slot).addEventListener('click', () => Title.open());
    }
    qs('#dayNum', slot).textContent = this.s.day;
    qs('#dayMax', slot).textContent = this.story.days;
    qs('#phaseMorning', slot).classList.toggle('on', this.s.phase === 'morning');
    qs('#phaseEvening', slot).classList.toggle('on', this.s.phase === 'evening');
    qs('#btnSleep', slot).disabled = this.s.phase !== 'evening';
    qs('#dayGoal', slot).textContent = this.story.goal ? this.story.goal(State.s) : '';
  },
  fade(text) {
    const el = qs('#nightfade');
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.textContent = text;
    el.classList.add('on');
    return wait(reduced ? 300 : 1100).then(() => { el.classList.remove('on'); return wait(reduced ? 50 : 350); });
  },

  /* ---- Erzwungenes Duell ---- */
  async forceDuel() {
    this.allowOnce = 'russian';
    await UI.show('russian');
    const victim = await new Promise((resolve) => {
      const off = Bus.on('rr:forced', ({ victim: v }) => { off(); resolve(v); });
      Russian.start({ forced: true });
    });
    this.s.flags[victim === 'igor' ? 'duelWon' : 'duelLost'] = true;
    State.save();
    await wait(800);
    return victim;
  },
};

/* Story-weite Szenen */
Cutscene.define('story.newConfirm', [
  { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Eine neue Geschichte? Die alte ist dann weg – Tag, Geld, alles. Sicher?',
    choices: [{ label: 'Ja, neu anfangen', value: 'yes', cls: 'red' }, { label: 'Weiterspielen', value: 'no', cls: 'ghost' }] },
]);

Bus.on('spin:after', () => { if (State.mode === 'story' && Story.story) return Story.runEvents('spin:after'); });
Bus.on('loss', ({ amount }) => { if (State.mode === 'story' && Story.story) { Story.s.stats.gambled += amount; State.save(); } });
</script>
```

- [ ] **Step 6: UI-Anpassungen** im `ui`-Block:

In `UI.show(id)` nach `if (!def) { … return; }` einfügen:
```js
    if (typeof Story !== 'undefined' && Story.isLocked(id)) { UI.toast({ icon: '🔒', title: Story.lockReason(id), tone: 'loss' }); SFX.play('lose'); return; }
```
In `UI.register('hub', …)` `mount(root)` am Ende: `if (typeof Story !== 'undefined' && State.mode === 'story') Story.decorateHub(root);`

In `renderWallet()` nach der letzten `notes.append(...)`-Zeile: `if (State.mode === 'story' && typeof Story !== 'undefined' && Story.story) notes.append(...Story.hudNotes());`

`renderSide()`: die `side.append(…)`-Anweisung ersetzen durch:
```js
    const inStory = State.mode === 'story' && typeof Story !== 'undefined' && Story.story;
    const room = (r) => !inStory || Story.roomUnlocked(r);
    const secs = [];
    if (room('bar')) secs.push(sec('Die Bar',
      btn(`🍺 Bier${s.beers > 0 ? ` (${s.beers}/3)` : ''}`, '50 €', 'beer', !Rules.canBeer(s).ok),
      btn('🍪 Brownie', s.brownieCost >= 10000 ? '10.000 €' : '1.000 €', 'brownie', !Rules.canBrownie(s).ok),
      h('p', { class: 'side-hint' }, 'Bier hält 2 Spins, Brownie 1 Spin.')));
    const hz = [];
    if (room('doc') || !inStory) hz.push(btn(s.kidneySold ? '🫁 Niere verkauft' : '🫁 Niere verkaufen', s.kidneySold ? '' : '+2.000 €', 'kidney', s.kidneySold));
    if (room('bank') || room('mafia')) hz.push(btn('🏦 Kredite', s.bankDebt + s.mafiaDebt > 0 ? `−${this.fmt(s.bankDebt + s.mafiaDebt)}` : '', 'finance'));
    if (room('invest')) hz.push(btn('📈 Anlagen', s.investments.length ? `${s.investments.length} aktiv` : '', 'invest'));
    if (inStory && room('vito')) hz.push(btn('🕶️ Vitos Tisch', s.story.vars.schuld != null ? this.fmt(s.story.vars.schuld) : '', 'vito'));
    if (hz.length) secs.push(sec('Hinterzimmer', ...hz));
    if (room('life')) secs.push(sec('Zuhause', btn('🏡 Leben', s.hasHouse ? '🏰' : '', 'life')));
    side.append(...secs);
```
und die Tab-Beschriftungen bleiben `['Bar', 'Hinterzimmer', 'Zuhause']` – bei weniger Sektionen: `tabs` nur für vorhandene Sektionen erzeugen: die Schleife über `secs.map((_, i) => ['Bar', 'Hinterzimmer', 'Zuhause'][…])` ist unsauber; stattdessen die Labels aus den `h3` der erzeugten Sektionen lesen: `qsa('.side-sec h3', side).map((el) => el.textContent).forEach((label, i) => …)` (gleicher Handler wie bisher). `Actions.vito = () => UI.show('vito');` zu `Actions` ergänzen (Screen kommt in Task 4; bis dahin Konsolen-Warnung).

- [ ] **Step 7: Russisches Roulette erzwingbar** – im `game-russian`-Block:

`async start() {` → `async start(opts = {}) {`; die Zeilen
```js
    const bet = Game.readBet('rrBet');
    if (!Game.beginSpin(bet)) return;
    const gen = this.gen;
    const duel = { cylinder: Rules.rrCylinder(Math.random), idx: 0, bet, gen, run: Game.run, done: false };
```
ersetzen durch
```js
    const forced = !!opts.forced;
    const bet = forced ? 0 : Game.readBet('rrBet');
    if (!forced && !Game.beginSpin(bet)) return;
    const gen = this.gen;
    const duel = { cylinder: Rules.rrCylinder(Math.random), idx: 0, bet, gen, run: forced ? null : Game.run, done: false, forced };
```
In `pull()` die beiden Status-Zeilen: bei `duel.forced` kürzer: `duel.forced ? 'PÄNG · Streifschuss' : \`PÄNG · Streifschuss · −${…} & 100 € Spital\`` bzw. `duel.forced ? 'PÄNG · Igor liegt' : \`PÄNG · Igor liegt · +${…}\``.
In `end(victim, duel)` nach dem `finally`-Block und **vor** `const delta = …` einfügen:
```js
    if (duel.forced) { await Bus.emit('rr:forced', { victim }); return; }
```
In `mount` (Status-Text) unverändert; bei `forced` Start setzt `start()` den Status: nach `qs('#rrStatus', this.root).textContent = 'Du bist dran. Drück ab.';` → `= forced ? 'Vitos Prüfung. Kein Einsatz – nur dein Kopf. Drück ab.' : 'Du bist dran. Drück ab.';`

- [ ] **Step 7b: Freies Spiel räumt die Tagesleiste** – im `title`-Block in `Modes.enter`, Zweig `choice === 'free'`, nach `UI.mountShell();` einfügen: `if (typeof Story !== 'undefined') Story.renderDaybar();` (leert `#daybarSlot`, weil `State.mode` jetzt `free` ist).

- [ ] **Step 8: Game Over & ↺ im Story-Modus** – im `gameover`-Block: am Anfang des `Bus.on('gameover', …)`-Handlers `if (State.mode === 'story') return;`; im `Bus.on('newgame.request', …)`-Handler am Anfang: `if (State.mode === 'story') return Story.enter('newstory');`.

- [ ] **Step 9: Probe-Story** – `<script id="story-probe">` (vorerst direkt nach `story-engine`; Task 4–6 fügen ihre Blöcke davor ein):

```html
<script id="story-probe">
/* ================= STORY PROBE – Dev-Story für Engine-Tests (?story=probe) ================= */
const STORY_PROBE = {
  id: 'probe', title: 'Probelauf', days: 3, dev: true,
  start: { balance: 500, unlocked: { jobs: ['spueler', 'post'], doors: ['slots'], rooms: ['bar'] }, vars: { mut: 0 } },
  varMax: { mut: 3 },
  hud: [{ var: 'mut', label: '💪 Mut', max: 3 }],
  goal: (s) => `Probelauf · Mut ${s.story.vars.mut}/3`,
  lockReason: { roulette: 'Erst ab Tag 2' },
  intro: 'probe.intro',
  scenes: {
    'probe.intro': [{ bg: 'bar', who: 'wirt', mood: 'calm', text: 'Probelauf. Drei Tage, ein Ziel: Mut sammeln. Tag {{day}}, {{balance}} in der Tasche.' }],
    'probe.k2': [{ bg: 'bar', who: 'wirt', mood: 'happy', text: 'Tag zwei. Roulette ist offen.' }],
    'probe.n1': [{ bg: 'keller', who: 'igor', mood: 'calm', text: 'Nacht eins. Mutig?', choices: [{ label: 'Ja', value: 'ja', effects: [{ var: 'mut', add: 1 }] }, { label: 'Nein', value: 'nein', cls: 'ghost' }] }],
    'probe.spin': [{ bg: 'bar', who: 'wirt', mood: 'calm', text: 'Du hast gespielt und Mut. Igor will dich testen.', choices: [{ label: 'Los', value: 'los', effects: [{ force: 'duel' }] }] }],
    'probe.mutig': [{ bg: 'hafen-morgen', who: 'vito', mood: 'happy', text: 'Mutig. Das war der Probelauf.' }],
    'probe.aus': [{ bg: 'klinik', who: 'doc', mood: 'calm', text: 'Drei Tage rum. Nichts passiert. Das war der Probelauf.' }],
  },
  chapters: [
    { id: 'k1', title: 'Eins', when: { day: { gte: 1 } } },
    { id: 'k2', title: 'Zwei', when: { day: { gte: 2 } }, intro: 'probe.k2', unlock: { doors: ['roulette'] } },
  ],
  events: [
    { id: 'n1', when: { day: { eq: 1 } }, once: true, at: 'night', scene: 'probe.n1' },
    { id: 'sp', when: { var: 'mut', gte: 1 }, once: true, at: 'spin:after', scene: 'probe.spin' },
    { id: 'dw', when: { flag: 'duelWon' }, once: true, at: 'night', effects: [{ var: 'mut', add: 1 }] },
  ],
  jobScenes: {},
  endings: [
    { id: 'mutig', title: 'Mutig', priority: 1, when: { var: 'mut', gte: 2 }, scene: 'probe.mutig' },
    { id: 'aus', title: 'Aus', priority: 0, scene: 'probe.aus', fallback: true },
  ],
};
if (typeof Stories !== 'undefined') Stories.define(STORY_PROBE);
</script>
```

- [ ] **Step 10: Prüfen**

Run: `node tests/run-selftest.mjs` → `76 bestanden, 0 fehlgeschlagen`; `tests/dom-selftest.sh` → `passed=76 failed=0`.
Run: `tests/screenshot.sh /tmp/st-probe.png "?story=probe&fresh"` → Intro-Szene des Wirts mit „Tag 1, 500 € in der Tasche".
CDP (`?story=probe&fresh`): Intro wegklicken → Hub (kein `jobs`-Screen noch) mit Tagesleiste „Tag 1/3", Morgen aktiv, Schlafen deaktiviert, Wallet-Zettel „💪 Mut 0/3"; Türen außer Slots verrammelt (Bretter, Kreide „Erst ab Tag 2" bei Roulette, „Noch geschlossen" sonst, Post: „Morgens, an der Pinnwand"); Klick auf Roulette → Toast 🔒; Seitenleiste nur „Die Bar". Konsole: `Story.evening()` → Schlafen aktiv; Slots spielen (Escrow, Wallet) → nach dem Spin (mut 0) keine Szene. Schlafen → Blende „Nacht 1", Igor-Szene, „Ja" → Mut 1/3; Blende „Tag 2", Toast „Kapitel: Zwei", Wirt-Szene, Roulette-Tür offen. `Story.evening()`; Slots spielen → Szene „probe.spin" → „Los" → Russisch-Roulette-Screen mit „Vitos Prüfung…", Abzug drücken bis Entscheidung → zurück; `State.s.story.flags` hat duelWon oder duelLost, Kontostand unverändert. Schlafen → Nacht 2 (bei duelWon Mut 2 → Ende „Mutig" mit Statistik-Panel und zwei Knöpfen) sonst Tag 3 → Schlafen → Fallback „Aus". „Zum Titel" → Titelscreen zeigt „Neue Story" (Lauf beendet). `?story=probe` ohne fresh nach Reload mitten im Lauf → „Fortsetzen · Probelauf · Tag N/3" auf dem Titel; Titel → Story → gleicher Tag/Phase. 🚪 aus der Story zum Titel und „Freies Spiel" → Sandbox-Stand unverändert (`State.s.story` undefined, kein Daybar, alle Türen offen).

- [ ] **Step 11: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Story-Engine mit Tagesschleife, Sperren, Effekten, erzwungenem Duell und Probe-Story

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Jobbörse, Schicht-Karten, Raum „Vitos Tisch", Post als Job

**Files:**
- Modify: `keller37.html` (neuer Block `<script id="jobs">` nach `story-engine` (vor `story-probe`); Templates `tpl-jobs`, `tpl-vito`; CSS Sektion 6; `game-postman` (Story-Deckel 15 Briefe, `job:done`); `story-engine` (Daybar-Knopf „Pinnwand"); `ui` (`Actions.vito`))

**Interfaces:**
- Produces: `Jobs.POOL` (`{ [id]: { id, name, icon, kind: 'game'|'shift', screen?, base?, requires?, requireText?, desc, pay } }`), `Jobs.take(id)`, `Jobs.runShift(job)`, `Jobs.finishGame(id)` (von Job-Screens am Ende gerufen: berechnet `earned` aus Kontostand-Differenz seit `take`, dann `Story.jobDone`), `Jobs.abort()` (Job-Screen ohne Ergebnis verlassen → `jobToday` bleibt null); Screens `jobs`, `vito`; `Story.jobStart = { id, balance }`; Bus-Event `job:done {id, earned}`; Postman: im Story-Modus endet die Schicht nach 15 Briefen („Feierabend") oder beim Fehler und ruft `Jobs.finishGame('post')`.
- Consumes: `Story.*`, `StoryRules.jobAvailable`, `Game.applyDelta`, `Cutscene`.

- [ ] **Step 1: Templates** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-jobs">
  <div class="panel stretch jobs-panel">
    <div class="pinboard" id="pinboard"></div>
    <div class="bet-bar"><button class="btn ghost" id="btnNoJob">Kein Job heute → Abend</button></div>
  </div>
</template>
<template id="tpl-vito">
  <div class="panel vito-panel">
    <h2 class="neon" style="--neon: var(--neon-red)">Vitos Tisch</h2>
    <p class="dim" id="vitoLine">Er sitzt da. Er wartet. Er hat Zeit.</p>
    <div class="paper iou" id="vitoIou"></div>
    <div class="bet-bar">
      <div class="bet-field"><button data-step="-100">−</button><input type="number" id="vitoPay" value="500" min="100" step="100"><button data-step="100">+</button></div>
      <button class="chip" data-chip="500" data-v="50">500</button>
      <button class="chip" data-chip="1000" data-v="100">1k</button>
      <button class="chip" data-chip="max" data-v="max">MAX</button>
      <button class="btn red" id="btnVitoPay">Rate zahlen</button>
    </div>
    <div class="status" id="vitoStatus"></div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Jobbörse -- */
.pinboard { position: relative; background: radial-gradient(circle at 20% 30%, #a8783f 0, #8a5e2e 40%, #6e4a22 100%); background-image: radial-gradient(rgba(0,0,0,.18) 1px, transparent 1.5px); background-size: 6px 6px; border: 10px solid #4a3520; border-radius: 6px; padding: 22px; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 18px; min-height: 260px; box-shadow: inset 0 0 40px rgba(0,0,0,.5); }
.jobnote { position: relative; background: var(--paper); color: var(--paper-ink); padding: 26px 14px 14px; font-family: var(--font-mono); box-shadow: 3px 4px 10px rgba(0,0,0,.6); transform: rotate(-1.5deg); display: flex; flex-direction: column; gap: 6px; cursor: pointer; transition: transform .15s; }
.jobnote:nth-child(even) { transform: rotate(1.2deg); background: #f6e6b3; }
.jobnote:hover { transform: rotate(0) translateY(-3px); }
.jobnote::before { content: ""; position: absolute; top: 8px; left: 50%; width: 14px; height: 14px; margin-left: -7px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #ff6b6b, #8a1010); box-shadow: 0 2px 3px rgba(0,0,0,.6); }
.jobnote h4 { font-family: var(--font-display); letter-spacing: .1em; font-size: 1.3rem; display: flex; align-items: center; gap: 8px; }
.jobnote .pay { color: #7a4a10; font-weight: 700; }
.jobnote p { font-size: .8rem; }
.jobnote.locked { opacity: .55; filter: grayscale(.8); cursor: not-allowed; }
.jobnote.locked:hover { transform: rotate(-1.5deg); }
.jobnote .why { font-size: .75rem; color: #b3261e; font-weight: 700; }
.jobnote.done { opacity: .7; }
.jobnote .done-stamp { position: absolute; right: 10px; top: 30px; transform: rotate(-14deg); font-family: var(--font-display); color: #2f7a1f; border: 3px solid #2f7a1f; padding: 2px 8px; letter-spacing: .1em; }
/* -- Vitos Tisch -- */
.vito-panel { background: radial-gradient(circle at 50% 10%, #3a2210, #150a03 70%); border-color: rgba(255,59,59,.3); }
.vito-panel .dim { color: var(--dim); }
```

- [ ] **Step 3: Jobs-Block** – `<script id="jobs">` nach `story-engine`:

```html
<script id="jobs">
/* ================= JOBS – Pinnwand, Schicht-Karten ================= */
const Jobs = {
  POOL: {
    spueler: { id: 'spueler', name: 'Spüler', icon: '🍽️', kind: 'game', screen: 'job-spueler', desc: 'Teller im Takt vom Band. 5 € pro Teller, Bruch kostet 10 €.', pay: '0–50 €' },
    post: { id: 'post', name: 'Postbote', icon: '📬', kind: 'game', screen: 'postman', desc: 'Briefe in den richtigen Kasten. Schicht endet nach 15 Briefen oder beim ersten Fehler.', pay: '5–50 € pro Brief' },
    taxi: { id: 'taxi', name: 'Nachttaxi', icon: '🚕', kind: 'game', screen: 'job-taxi', desc: '60 Sekunden, drei Spuren. Fahrgäste einsammeln, bei Rot bremsen.', pay: 'bis 300 €', requires: { balance: { gte: 200 } }, requireText: 'Kaution 200 €' },
    tuersteher: { id: 'tuersteher', name: 'Türsteher', icon: '🚪', kind: 'shift', base: 100, desc: 'Wer kommt rein, wer nicht. Vito guckt zu.', pay: '100 € + Trinkgeld' },
    croupier: { id: 'croupier', name: 'Croupier', icon: '🃏', kind: 'shift', base: 150, requires: { jobDone: 'tuersteher', gte: 3 }, requireText: '3 Nächte als Türsteher', desc: 'Karten geben, Kessel drehen, Mund halten.', pay: '150 €' },
    kurier: { id: 'kurier', name: 'Kevins Kurier', icon: '💊', kind: 'shift', base: 300, desc: 'Päckchen von A nach B. Frag nicht, was drin ist.', pay: '300 €' },
    praktikant: { id: 'praktikant', name: 'Praktikant bei Krause', icon: '👔', kind: 'shift', base: 120, desc: 'Kaffee kochen, Akten lesen. Manche Akten sind interessant.', pay: '120 €' },
    docassi: { id: 'docassi', name: 'Assistent beim Doc', icon: '🩺', kind: 'shift', base: 250, desc: 'Handschuhe an. Nicht hinsehen.', pay: '250 €' },
  },
  render(root) {
    const board = qs('#pinboard', root);
    board.innerHTML = '';
    const s = State.s;
    for (const job of Object.values(this.POOL)) {
      if (!s.story.unlocked.jobs.includes(job.id)) continue;
      const av = StoryRules.jobAvailable(job, s);
      const note = h('div', { class: 'jobnote' + (av.ok ? '' : av.reason === 'done' ? ' done' : ' locked') },
        h('h4', {}, job.icon, job.name), h('p', {}, job.desc), h('div', { class: 'pay' }, job.pay));
      if (!av.ok && av.reason !== 'done') note.append(h('div', { class: 'why' }, av.reason === 'locked' ? 'Gesperrt' : av.reason));
      if (av.reason === 'done') note.append(h('div', { class: 'done-stamp' }, 'Heute erledigt'));
      if (av.ok) note.addEventListener('click', () => { SFX.play('stamp'); Jobs.take(job.id); });
      board.append(note);
    }
    if (!board.children.length) board.append(h('p', { class: 'paper' }, 'Nichts an der Pinnwand. Komm morgen wieder.'));
  },
  async take(id) {
    const job = this.POOL[id];
    if (!job || !StoryRules.jobAvailable(job, State.s).ok) return;
    if (job.kind === 'game') {
      Story.jobStart = { id, balance: State.s.balance };
      Story.allowOnce = job.screen;
      await UI.show(job.screen);
      return;
    }
    await this.runShift(job);
  },
  async runShift(job) {
    const list = (Story.story.jobScenes || {})[job.id] || [];
    const seen = Story.s.seenJobScenes[job.id] || (Story.s.seenJobScenes[job.id] = []);
    let cands = list.filter((sid) => !seen.includes(sid));
    if (!cands.length && list.length) { seen.length = 0; cands = list.slice(); }
    const sceneId = cands.length ? pick(cands) : null;
    if (sceneId) seen.push(sceneId);
    const before = State.s.balance;
    Game.applyDelta(job.base, { quiet: true });
    UI.toast({ icon: job.icon, title: `${job.name}: Schicht`, text: `+${UI.fmt(job.base)} Lohn.`, tone: 'win' });
    if (sceneId) await Story.playScene(sceneId);
    const earned = State.s.balance - before;
    await Bus.emit('job:done', { id: job.id, earned });
    await Story.jobDone(job.id, earned);
    if (Story.lostDay) { Story.lostDay = false; UI.toast({ icon: '🚔', title: 'Tag verloren', text: 'Der Abend fällt aus.', tone: 'loss' }); await Story.night(); }
  },
  async finishGame(id) {
    const start = Story.jobStart;
    Story.jobStart = null;
    const earned = start ? State.s.balance - start.balance : 0;
    await Bus.emit('job:done', { id, earned });
    await Story.jobDone(id, earned);
  },
  abort() { Story.jobStart = null; },
};

UI.register('jobs', {
  template: 'tpl-jobs',
  mount(root) {
    Jobs.render(root);
    qs('#btnNoJob', root).addEventListener('click', () => { SFX.play('click'); Story.evening(); });
  },
});

/* ---- Raum: Vitos Tisch (Story 1) ---- */
const VitoRoom = {
  root: null,
  render() {
    if (!this.root) return;
    const st = State.s.story;
    const left = Story.story.days - st.day + 1;
    qs('#vitoIou', this.root).innerHTML = `<h4>Vitos Zettel</h4><div class="amt">${UI.fmt(st.vars.schuld || 0)}</div><div class="deadline">Noch ${left} Tag${left === 1 ? '' : 'e'}</div><div>Bisher gezahlt: ${UI.fmt(st.vars.gezahlt || 0)}</div>`;
    qs('#btnVitoPay', this.root).disabled = (st.vars.schuld || 0) <= 0;
  },
  pay() {
    const s = State.s; const st = s.story;
    let amt = parseInt(qs('#vitoPay', this.root).value, 10);
    if (!Number.isFinite(amt) || amt < 100) { UI.toast({ icon: '🕶️', title: 'Mindestens 100 €', tone: 'loss' }); return; }
    amt = Math.min(amt, st.vars.schuld || 0);
    if (s.balance < amt) { UI.toast({ icon: '🕶️', title: 'Zu wenig Geld', text: `Du hast ${UI.fmt(s.balance)}.`, tone: 'loss' }); SFX.play('lose'); return; }
    Game.applyDelta(-amt, { from: qs('#vitoIou', this.root) });
    const beforeSteps = Math.floor((st.vars.gezahlt || 0) / 5000);
    st.vars.gezahlt = (st.vars.gezahlt || 0) + amt;
    st.vars.schuld = Math.max(0, (st.vars.schuld || 0) - amt);
    const steps = Math.floor(st.vars.gezahlt / 5000) - beforeSteps;
    if (steps > 0) StoryRules.applyEffect(s, { var: 'vertrauen', add: steps }, Story.story);
    State.save();
    SFX.play('stamp');
    qs('#vitoStatus', this.root).innerHTML = `<span class="win">${UI.fmt(amt)} auf den Tisch. Vito nickt${steps > 0 ? ' anerkennend' : ''}.</span>`;
    this.render(); UI.renderWallet(); UI.renderSide(); Story.renderDaybar();
  },
};
UI.register('vito', {
  template: 'tpl-vito',
  mount(root) {
    VitoRoom.root = root;
    Game.bindBet(root, 'vitoPay');
    qsa('[data-chip="max"]', root).forEach((c) => c.addEventListener('click', () => { qs('#vitoPay', root).value = Math.max(100, Math.min(State.s.balance, State.s.story.vars.schuld || 0)); }));
    qs('#btnVitoPay', root).addEventListener('click', () => VitoRoom.pay());
    VitoRoom.render();
  },
  unmount() { VitoRoom.root = null; },
});
Actions.vito = () => UI.show('vito');
</script>
```

Hinweis: `Game.bindBet` setzt beim MAX-Chip `Rules.maxBet(State.s)`; der zusätzliche Listener oben überschreibt den Wert danach mit dem Vito-Maximum (Listener-Reihenfolge: `bindBet` zuerst registriert, also zuerst ausgeführt).

- [ ] **Step 4: Daybar-Knopf „Pinnwand"** – in `tpl-daybar` nach `#btnSleep` einfügen: `<button class="btn ghost sm" id="btnBoard">📌 Pinnwand</button>`; in `Story.renderDaybar()` beim ersten Aufbau: `qs('#btnBoard', slot).addEventListener('click', () => { SFX.play('click'); UI.show('jobs'); });` und bei jedem Render: `qs('#btnBoard', slot).classList.toggle('hidden', this.s.phase !== 'morning');`. In `Story.isLocked`: Screens `jobs`, `vito`, `job-spueler`, `job-taxi` sind nie gesperrt, außer Job-Screens am Abend: `if (['job-spueler', 'job-taxi'].includes(screen)) return this.s.phase !== 'morning';` (vor der DOORS-Prüfung; `postman` bleibt über `allowOnce` erreichbar).

- [ ] **Step 5: Postbote im Story-Modus** – im `game-postman`-Block:

In `nextStep(gen)` ganz am Anfang (nach `clearInterval(this.timer); if (!this.root) return;`):
```js
    if (State.mode === 'story' && this.streak >= 15) { this.endShift('Feierabend! 15 Briefe ausgetragen.'); return; }
```
Neue Methode nach `fail(msg, house)`:
```js
  endShift(msg) {
    clearInterval(this.timer);
    this.active = false;
    if (this.root) {
      qs('#fuseWrap', this.root).classList.add('hidden');
      qs('#letter', this.root).classList.add('hidden');
      qs('#jobStatus', this.root).innerHTML = `<span class="win">${msg}</span>`;
      qs('#btnShift', this.root).classList.remove('hidden');
    }
    this.tier = null;
    if (State.mode === 'story') Jobs.finishGame('post');
  },
```
Am Ende von `fail(msg, house)` (nach `this.tier = null;`): `if (State.mode === 'story') Jobs.finishGame('post');`
In `unmount`: `if (State.mode === 'story' && Postman.active) Jobs.abort();` vor dem Timer-Clear (Job nicht gezählt, kann erneut genommen werden).

- [ ] **Step 6: Prüfen**

Run: `node tests/run-selftest.mjs` → 76; `tests/dom-selftest.sh` → 76.
Run: `tests/screenshot.sh /tmp/st-jobs.png "?story=probe&fresh"` → nach dem Intro (Screenshot zeigt Intro; für die Pinnwand: `?story=probe&fresh&day=1` überspringt das Intro) → Korkwand mit zwei Zetteln „Spüler" und „Postbote" (Spüler-Screen fehlt noch → Klick auf Spüler loggt „Screen fehlt", Post öffnet den Postboten).
CDP (`?story=probe&fresh&day=1`): Post klicken → Postboten-Screen; Schicht: 15 Briefe korrekt (per `Postman.deliver(Postman.target.n)` in Schleife mit Wartezeit) → Status „Feierabend", zurück im Hub, Tagesleiste zeigt Abend, `State.s.story.jobToday === 'post'`, `jobsDone.post === 1`, `stats.earned` = Summe der Belohnungen; Pinnwand-Knopf verschwindet, Schlafen aktiv. Falscher Kasten → −25, ebenfalls `jobDone`. Probe hat keine Schicht-Karten – `Jobs.runShift` per Konsole prüfen: `State.s.story.unlocked.jobs.push('tuersteher'); Story.story.jobScenes.tuersteher = ['probe.n1']; await Jobs.runShift(Jobs.POOL.tuersteher)` → +100 €, Igor-Szene, danach Abend. Vito-Raum: `State.s.story.unlocked.rooms.push('vito'); State.s.story.vars.schuld = 50000; UI.renderSide()` → „🕶️ Vitos Tisch" in der Seitenleiste; öffnen, `Game.applyDelta(6000)`, 5.000 zahlen → Zettel 45.000 €, Vertrauen-Zettel +1 (`vars.vertrauen` 1), Kontostand −5.000.

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Pinnwand, Schicht-Karten, Vitos Tisch, Post als Job

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Mini-Spiel Spüler

**Files:**
- Modify: `keller37.html` (Template `tpl-job-spueler`; CSS Sektion 6 + Keyframes; neuer Block `<script id="job-spueler">` nach `jobs`)

**Interfaces:**
- Consumes: `StoryRules.spuelerPay`, `Jobs.finishGame('spueler')`, `Jobs.abort()`, `Game.applyDelta`, `SFX`, `UI`.
- Produces: Screen `job-spueler`; `Spueler.start()`, `Spueler.tap()`; Bus-Event `spueler:result {hits, breaks, pay}`.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-job-spueler">
  <div class="panel kitchen">
    <h2 class="neon" style="--neon: var(--neon-blue)">Spülküche</h2>
    <div class="dish-counter"><span id="dishNum">Teller 0/10</span><span id="dishScore">Sauber 0 · Bruch 0</span></div>
    <div class="belt" id="belt">
      <div class="zone" id="dishZone"></div>
      <div class="plate" id="dishPlate">🍽️</div>
    </div>
    <div class="status" id="dishStatus">Klick oder Leertaste, wenn der Teller in der Zone ist.</div>
    <div class="bet-bar">
      <button class="btn solid" id="btnDishStart">Schicht beginnen</button>
      <button class="btn blue hidden" id="btnDishTap">Abwaschen!</button>
      <button class="btn ghost hidden" id="btnDishDone">Feierabend</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Spüler -- */
.kitchen { background: linear-gradient(180deg, #17202a, #0d1319); border-color: rgba(76,201,240,.25); }
.dish-counter { display: flex; gap: 20px; font-family: var(--font-mono); color: var(--dim); }
.belt { position: relative; width: 100%; max-width: 640px; height: 90px; background: repeating-linear-gradient(90deg, #2a2f36 0 30px, #22262c 30px 60px); border: 4px solid #3a3f46; border-radius: 10px; overflow: hidden; box-shadow: inset 0 8px 16px rgba(0,0,0,.6); }
.belt.running { animation: beltMove .6s linear infinite; }
.zone { position: absolute; top: 0; bottom: 0; background: rgba(61,220,132,.25); border-left: 2px solid var(--neon-green); border-right: 2px solid var(--neon-green); box-shadow: inset 0 0 20px rgba(61,220,132,.3); }
.plate { position: absolute; top: 50%; left: 0; transform: translate(-50%, -50%); font-size: 3rem; filter: drop-shadow(0 4px 6px rgba(0,0,0,.7)); }
.plate.hit { animation: plateHit .35s ease both; }
.plate.broken { animation: plateBreak .5s ease both; }
@media (max-width: 760px) { .belt { height: 70px; } .plate { font-size: 2.3rem; } }
```
Keyframes (Sektion 7): 
```css
@keyframes beltMove { from { background-position: 0 0; } to { background-position: 60px 0; } }
@keyframes plateHit { 0% { transform: translate(-50%, -50%) scale(1); } 50% { transform: translate(-50%, -80%) scale(1.2); } 100% { transform: translate(-50%, -50%) scale(0); opacity: 0; } }
@keyframes plateBreak { 0% { transform: translate(-50%, -50%) rotate(0); } 100% { transform: translate(-50%, 40%) rotate(60deg); opacity: 0; } }
```

- [ ] **Step 3: Block** – `<script id="job-spueler">` nach `jobs`:

```html
<script id="job-spueler">
/* ================= JOB: SPÜLER – Timing am Band ================= */
const Spueler = {
  root: null, gen: 0, running: false, raf: null, plate: 0, hits: 0, breaks: 0, pos: 0, t0: 0, dur: 1600, zone: { c: 0.5, w: 0.3 }, resolved: false,
  TOTAL: 10,
  alive(gen) { return !!this.root && this.gen === gen; },
  start() {
    if (this.running || !this.root) return;
    this.running = true; this.plate = 0; this.hits = 0; this.breaks = 0;
    qs('#btnDishStart', this.root).classList.add('hidden');
    qs('#btnDishTap', this.root).classList.remove('hidden');
    qs('#belt', this.root).classList.add('running');
    qs('#dishStatus', this.root).textContent = 'Los!';
    this.nextPlate();
  },
  nextPlate() {
    const gen = this.gen;
    if (!this.alive(gen) || !this.running) return;
    if (this.plate >= this.TOTAL) return this.finish();
    this.plate++;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const k = (this.plate - 1) / (this.TOTAL - 1);
    this.dur = reduced ? 1800 : Math.round(1600 - k * 700);          // 1600 → 900 ms
    this.zone = { c: rand(0.35, 0.75), w: reduced ? 0.3 : 0.3 - k * 0.18 }; // 30 % → 12 %
    this.resolved = false;
    const zone = qs('#dishZone', this.root), plate = qs('#dishPlate', this.root);
    zone.style.left = `${(this.zone.c - this.zone.w / 2) * 100}%`; zone.style.width = `${this.zone.w * 100}%`;
    plate.className = 'plate'; plate.style.left = '0%';
    qs('#dishNum', this.root).textContent = `Teller ${this.plate}/${this.TOTAL}`;
    this.t0 = performance.now();
    const step = (now) => {
      if (!this.alive(gen) || !this.running || this.resolved) return;
      this.pos = Math.min(1, (now - this.t0) / this.dur);
      plate.style.left = `${this.pos * 100}%`;
      if (this.pos >= 1) { this.miss('Runtergefallen!'); return; }
      this.raf = requestAnimationFrame(step);
    };
    this.raf = requestAnimationFrame(step);
  },
  tap() {
    if (!this.running || this.resolved || !this.root) return;
    const inZone = Math.abs(this.pos - this.zone.c) <= this.zone.w / 2;
    if (inZone) {
      this.resolved = true; this.hits++;
      qs('#dishPlate', this.root).classList.add('hit');
      SFX.play('coin');
      qs('#dishStatus', this.root).innerHTML = '<span class="win">Sauber!</span>';
      this.score();
      setTimeout(() => this.nextPlate(), 380);
    } else {
      this.miss('Daneben – Bruch!');
    }
  },
  miss(msg) {
    this.resolved = true; this.breaks++;
    if (this.root) {
      qs('#dishPlate', this.root).classList.add('broken');
      qs('#dishStatus', this.root).innerHTML = `<span class="loss">${msg}</span>`;
      UI.shake(qs('#belt', this.root));
    }
    SFX.play('lose');
    this.score();
    setTimeout(() => this.nextPlate(), 520);
  },
  score() { if (this.root) qs('#dishScore', this.root).textContent = `Sauber ${this.hits} · Bruch ${this.breaks}`; },
  async finish() {
    this.running = false;
    const pay = Math.max(StoryRules.spuelerPay(this.hits, this.breaks), -State.s.balance);
    if (this.root) {
      qs('#belt', this.root).classList.remove('running');
      qs('#btnDishTap', this.root).classList.add('hidden');
      qs('#btnDishDone', this.root).classList.remove('hidden');
      qs('#dishStatus', this.root).innerHTML = pay >= 0 ? `<span class="win">Schicht vorbei · ${this.hits} sauber · Lohn ${UI.fmt(pay)}</span>` : `<span class="loss">Schicht vorbei · ${this.breaks} Bruch · Abzug ${UI.fmt(-pay)}</span>`;
    }
    if (pay !== 0) Game.applyDelta(pay, { from: this.root ? qs('#belt', this.root) : null });
    if (pay >= 0) SFX.play('cash');
    await Bus.emit('spueler:result', { hits: this.hits, breaks: this.breaks, pay });
  },
  onKey(e) { if (e.code === 'Space' && qs('#cutscene').hidden && !e.repeat) { e.preventDefault(); Spueler.tap(); } },
};
UI.register('job-spueler', {
  template: 'tpl-job-spueler',
  mount(root) {
    Spueler.root = root; Spueler.gen++; Spueler.running = false;
    qs('#btnDishStart', root).addEventListener('click', () => { SFX.play('click'); Spueler.start(); });
    qs('#btnDishTap', root).addEventListener('click', () => Spueler.tap());
    qs('#belt', root).addEventListener('pointerdown', () => Spueler.tap());
    qs('#btnDishDone', root).addEventListener('click', () => { SFX.play('click'); Jobs.finishGame('spueler'); });
    document.addEventListener('keydown', Spueler.onKey);
  },
  unmount() {
    document.removeEventListener('keydown', Spueler.onKey);
    if (Spueler.raf) cancelAnimationFrame(Spueler.raf);
    if (Spueler.running) Jobs.abort();
    Spueler.gen++; Spueler.root = null; Spueler.running = false;
  },
});
</script>
```

- [ ] **Step 4: Prüfen**

Run: `node tests/run-selftest.mjs` → 76; `tests/dom-selftest.sh` → 76.
Run: `tests/screenshot.sh /tmp/st-spueler.png "?story=probe&fresh&day=1&screen=job-spueler"` – Hinweis: `?screen` mit Story: in `boot` wird bei `wantsStory` der `screen`-Parameter ignoriert; für Screenshots stattdessen CDP nutzen (`Jobs.take('spueler')`).
CDP (`?story=probe&fresh&day=1`): Spüler-Zettel klicken → Küche mit Band; „Schicht beginnen" → Teller läuft von links nach rechts, grüne Zone; in der Zone tippen → „Sauber!", Zähler; außerhalb → Bruch mit Shake; nichts tun → „Runtergefallen!"; nach 10 Tellern Lohn (z.B. 7 sauber, 3 Bruch → +5 €), Kontostand ändert sich, „Feierabend" → Hub, Abend, `jobsDone.spueler === 1`, `stats.earned` = Lohn (bei negativem Lohn 0). Screen mid-Schicht verlassen (Esc) → kein Lohn, Pinnwand zeigt Spüler wieder verfügbar. Reduced-Motion: Zone bleibt 30 %.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Mini-Spiel Spüler

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Mini-Spiel Nachttaxi

**Files:**
- Modify: `keller37.html` (Template `tpl-job-taxi`; CSS Sektion 6 + Keyframes; neuer Block `<script id="job-taxi">` nach `job-spueler`)

**Interfaces:**
- Consumes: `StoryRules.taxiPay`, `Jobs.finishGame('taxi')`, `Jobs.abort()`, `Game.applyDelta`, `SFX`, `UI`.
- Produces: Screen `job-taxi`; `Taxi.start()`, `Taxi.lane(dir)`, `Taxi.brake()`; Bus-Event `taxi:result {passengers, tickets, pay}`.

- [ ] **Step 1: Template** – vor `<!-- /TEMPLATES -->`:

```html
<template id="tpl-job-taxi">
  <div class="panel taxi-panel">
    <div class="taxi-hud"><span id="taxiTime">60 s</span><span id="taxiScore">Fahrgäste 0 · Strafzettel 0</span></div>
    <div class="taxi-road" id="taxiRoad">
      <div class="lane-line l1"></div><div class="lane-line l2"></div>
      <div class="taxi" id="taxiCar">🚕</div>
      <div class="brake-flash" id="brakeFlash"></div>
    </div>
    <div class="status" id="taxiStatus">← → Spur wechseln · Leertaste bremsen · oder tippen: links / Mitte / rechts</div>
    <div class="bet-bar">
      <button class="btn solid" id="btnTaxiStart">Schicht beginnen</button>
      <button class="btn ghost hidden" id="btnTaxiDone">Feierabend</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS** – vor `/* ==== 7. ANIMATIONEN ==== */`:

```css
/* -- Nachttaxi -- */
.taxi-panel { background: linear-gradient(180deg, #0b1020, #05070f); border-color: rgba(76,201,240,.25); }
.taxi-hud { display: flex; gap: 20px; font-family: var(--font-mono); color: var(--dim); }
.taxi-road { position: relative; width: 100%; max-width: 420px; height: 420px; background: #2b2b2b; border-left: 8px solid #d8c36b; border-right: 8px solid #d8c36b; border-radius: 6px; overflow: hidden; touch-action: none; user-select: none; }
.taxi-road.running { background-image: repeating-linear-gradient(180deg, transparent 0 40px, rgba(255,255,255,.04) 40px 44px); animation: roadMove .5s linear infinite; }
.lane-line { position: absolute; top: 0; bottom: 0; width: 4px; background: repeating-linear-gradient(180deg, #ddd 0 24px, transparent 24px 48px); }
.lane-line.l1 { left: 33.3%; } .lane-line.l2 { left: 66.6%; }
.taxi { position: absolute; bottom: 20px; width: 33.3%; text-align: center; font-size: 2.6rem; transition: left .12s; filter: drop-shadow(0 0 8px rgba(245,214,122,.6)); }
.taxi.braking { filter: drop-shadow(0 0 12px #ff3b3b); }
.rider { position: absolute; width: 33.3%; text-align: center; font-size: 2rem; top: -60px; }
.light { position: absolute; left: 0; right: 0; height: 26px; top: -40px; background: repeating-linear-gradient(90deg, #ff3b3b 0 20px, #fff 20px 40px); box-shadow: 0 0 16px rgba(255,59,59,.7); display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.brake-flash { position: absolute; inset: 0; background: rgba(255,59,59,.35); opacity: 0; pointer-events: none; }
.brake-flash.on { animation: flash .25s ease both; }
.ticket-pop { position: absolute; left: 50%; top: 40%; transform: translateX(-50%) rotate(-8deg); font-family: var(--font-display); font-size: 2rem; color: #fff; background: #b3261e; padding: 4px 14px; letter-spacing: .1em; animation: stampIn .4s cubic-bezier(.3,1.6,.5,1) both; }
@media (max-width: 760px) { .taxi-road { height: 340px; } }
```
Keyframes: `@keyframes roadMove { from { background-position: 0 0; } to { background-position: 0 44px; } }`

- [ ] **Step 3: Block** – `<script id="job-taxi">` nach `job-spueler`:

```html
<script id="job-taxi">
/* ================= JOB: NACHTTAXI – drei Spuren, 60 Sekunden ================= */
const Taxi = {
  root: null, gen: 0, running: false, raf: null, spawnTimer: null, timeLeft: 60, laneIdx: 1, passengers: 0, tickets: 0, braking: false, brakeUntil: 0, entities: [], speed: 160, lastT: 0,
  DURATION: 60,
  alive(gen) { return !!this.root && this.gen === gen; },
  start() {
    if (this.running || !this.root) return;
    const gen = this.gen;
    this.running = true; this.timeLeft = this.DURATION; this.laneIdx = 1; this.passengers = 0; this.tickets = 0; this.entities = []; this.speed = 160;
    qs('#btnTaxiStart', this.root).classList.add('hidden');
    qs('#taxiRoad', this.root).classList.add('running');
    this.placeCar();
    SFX.play('whinny');
    this.spawnTimer = setInterval(() => this.spawn(), 900);
    this.lastT = performance.now();
    const step = (now) => {
      if (!this.alive(gen) || !this.running) return;
      const dt = Math.min(0.05, (now - this.lastT) / 1000); this.lastT = now;
      this.timeLeft -= dt;
      this.speed = 160 + (this.DURATION - this.timeLeft) * 2; // wird schneller
      qs('#taxiTime', this.root).textContent = `${Math.max(0, Math.ceil(this.timeLeft))} s`;
      const road = qs('#taxiRoad', this.root); const H = road.clientHeight; const carY = H - 20 - 44;
      for (const e of this.entities) {
        e.y += this.speed * dt; e.el.style.top = `${e.y}px`;
        if (!e.done && e.y >= carY - 20 && e.y <= carY + 30) {
          e.done = true;
          if (e.kind === 'rider') { if (e.lane === this.laneIdx) { this.passengers++; SFX.play('coin'); e.el.textContent = '💨'; this.floatText('+15 €', 'win'); } }
          else if (this.braking) { SFX.play('click'); } else { this.tickets++; SFX.play('stamp'); this.ticket(); }
          this.score();
        }
        if (e.y > H + 60) { e.el.remove(); e.dead = true; }
      }
      this.entities = this.entities.filter((e) => !e.dead);
      if (this.braking && now > this.brakeUntil) { this.braking = false; qs('#taxiCar', this.root).classList.remove('braking'); }
      if (this.timeLeft <= 0) { this.finish(); return; }
      this.raf = requestAnimationFrame(step);
    };
    this.raf = requestAnimationFrame(step);
  },
  spawn() {
    if (!this.root || !this.running) return;
    const road = qs('#taxiRoad', this.root);
    const isLight = Math.random() < 0.22;
    if (isLight) {
      const el = h('div', { class: 'light' }, '🚦 ROT');
      road.append(el); this.entities.push({ kind: 'light', el, y: -40, done: false });
    } else {
      const lane = Math.floor(Math.random() * 3);
      const el = h('div', { class: 'rider', style: `left:${lane * 33.3}%` }, pick(['🙋', '🙋‍♀️', '🧑‍🦳', '🕺']));
      road.append(el); this.entities.push({ kind: 'rider', el, y: -60, lane, done: false });
    }
  },
  placeCar() { if (this.root) qs('#taxiCar', this.root).style.left = `${this.laneIdx * 33.3}%`; },
  lane(dir) { if (!this.running) return; this.laneIdx = Math.max(0, Math.min(2, this.laneIdx + dir)); this.placeCar(); SFX.play('click'); },
  brake() { if (!this.running || !this.root) return; this.braking = true; this.brakeUntil = performance.now() + 600; qs('#taxiCar', this.root).classList.add('braking'); const f = qs('#brakeFlash', this.root); f.classList.remove('on'); void f.offsetWidth; f.classList.add('on'); },
  ticket() { if (!this.root) return; const p = h('div', { class: 'ticket-pop' }, 'STRAFZETTEL −50 €'); qs('#taxiRoad', this.root).append(p); UI.shake(qs('#taxiRoad', this.root)); setTimeout(() => p.remove(), 900); },
  floatText(txt, cls) { if (!this.root) return; const el = h('div', { class: 'ticket-pop', style: 'background:#2f7a1f' }, txt); qs('#taxiRoad', this.root).append(el); setTimeout(() => el.remove(), 600); },
  score() { if (this.root) qs('#taxiScore', this.root).textContent = `Fahrgäste ${this.passengers} · Strafzettel ${this.tickets}`; },
  async finish() {
    this.running = false;
    clearInterval(this.spawnTimer);
    const pay = Math.max(StoryRules.taxiPay(this.passengers, this.tickets), -State.s.balance);
    if (this.root) {
      qs('#taxiRoad', this.root).classList.remove('running');
      this.entities.forEach((e) => e.el.remove()); this.entities = [];
      qs('#btnTaxiDone', this.root).classList.remove('hidden');
      qs('#taxiStatus', this.root).innerHTML = pay >= 0 ? `<span class="win">Feierabend · ${this.passengers} Fahrgäste · ${UI.fmt(pay)}</span>` : `<span class="loss">Feierabend · ${this.tickets} Strafzettel · Abzug ${UI.fmt(-pay)}</span>`;
    }
    if (pay !== 0) Game.applyDelta(pay, { from: this.root ? qs('#taxiRoad', this.root) : null });
    if (pay >= 0) SFX.play('cash');
    await Bus.emit('taxi:result', { passengers: this.passengers, tickets: this.tickets, pay });
  },
  onKey(e) {
    if (!qs('#cutscene').hidden) return;
    if (e.code === 'ArrowLeft') { e.preventDefault(); Taxi.lane(-1); }
    else if (e.code === 'ArrowRight') { e.preventDefault(); Taxi.lane(1); }
    else if (e.code === 'Space' && !e.repeat) { e.preventDefault(); Taxi.brake(); }
  },
  onTap(e) {
    const r = e.currentTarget.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width;
    if (x < 0.33) Taxi.lane(-1); else if (x > 0.66) Taxi.lane(1); else Taxi.brake();
  },
};
UI.register('job-taxi', {
  template: 'tpl-job-taxi',
  mount(root) {
    Taxi.root = root; Taxi.gen++; Taxi.running = false;
    qs('#btnTaxiStart', root).addEventListener('click', () => { SFX.play('click'); Taxi.start(); });
    qs('#btnTaxiDone', root).addEventListener('click', () => { SFX.play('click'); Jobs.finishGame('taxi'); });
    qs('#taxiRoad', root).addEventListener('pointerdown', Taxi.onTap);
    document.addEventListener('keydown', Taxi.onKey);
  },
  unmount() {
    document.removeEventListener('keydown', Taxi.onKey);
    clearInterval(Taxi.spawnTimer); if (Taxi.raf) cancelAnimationFrame(Taxi.raf);
    if (Taxi.running) Jobs.abort();
    Taxi.gen++; Taxi.root = null; Taxi.running = false; Taxi.entities = [];
  },
});
</script>
```

- [ ] **Step 4: Prüfen**

Run: Node/DOM-Selbsttest 76.
CDP (`?story=probe&fresh&day=1`, Konsole `State.s.story.unlocked.jobs.push('taxi'); Game.applyDelta(300); UI.show('jobs')`): Taxi-Zettel klicken → Straße mit gelben Rändern, Taxi unten Mitte; „Schicht beginnen" → Fahrgäste und rote Ampeln kommen von oben, werden schneller; ArrowLeft/Right wechseln die Spur, Space bremst (rotes Glühen); Fahrgast in der eigenen Spur → +15-Pop und Zähler; Ampel ohne Bremse → „STRAFZETTEL"-Stempel + Shake; nach 60 s Lohn, Feierabend → Abend. Tap-Zonen per `pointerdown` mit clientX prüfen. Screenshot mitten in der Fahrt ansehen.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Mini-Spiel Nachttaxi

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Story 1 „Die Schuld" – Kapitel 1–2, Kontrolle, Kurier/Praktikant, Enden „ehrlich" + Fallback

**Files:**
- Modify: `keller37.html` (`story-rules`: Effekt `chance` + Test; `story-engine`: Szenen als Funktion, `flags` im Ctx; neuer Block `<script id="story-schuld">` nach `story-probe`; Tests)

**Interfaces:**
- Produces: `const STORY_SCHULD = {…}` (registriert via `Stories.define`), Effekt `{ chance: 0.3, effects: [...] }` (würfelt mit `rng`, Default `Math.random`; `StoryRules.applyEffect(s, eff, story, rng)`), Szenen dürfen Funktionen `(ctx) => panels` sein (`ctx.flags` verfügbar), Story-1-Variablen `schuld, vertrauen, ruf, gezahlt, duellSiege, tuerSauber`, Flags aus Spec §9.
- Consumes: alles aus Task 1–6.

- [ ] **Step 1: Failing Tests** – vor `/* --- SELFTEST CASES END --- */`:

```js
T.test('StoryRules.applyEffect: chance würfelt', () => {
  const s = storyBase();
  StoryRules.applyEffect(s, { chance: 0.3, effects: [{ flag: 'hit' }] }, {}, seq(0.1)); T.eq(!!s.story.flags.hit, true);
  StoryRules.applyEffect(s, { chance: 0.3, effects: [{ flag: 'miss' }] }, {}, seq(0.9)); T.eq(!!s.story.flags.miss, false);
  T.eq(StoryRules.applyEffect(s, { chance: 1, effects: [{ scene: 'x' }] }, {}, seq(0)), { scene: 'x' }, 'verschachtelte nicht-pure Effekte werden gemeldet');
});
T.test('STORY_SCHULD ist gültig', () => {
  const sceneIds = Object.keys(STORY_SCHULD.scenes);
  T.eq(StoryRules.validate(STORY_SCHULD, sceneIds, ['spueler', 'post', 'taxi', 'tuersteher', 'croupier', 'kurier', 'praktikant', 'docassi']), []);
  T.eq(STORY_SCHULD.days, 30);
  T.eq(STORY_SCHULD.start.vars.schuld, 50000);
  T.ok(!STORY_SCHULD.dev);
});
T.test('STORY_SCHULD: Kontrolle Tag 10 und Enden', () => {
  const s = Object.assign(base({ balance: 100 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) });
  s.story.day = 10;
  T.eq(StoryRules.dueEvents(STORY_SCHULD, s, 'night').map((e) => e.id), ['kontrolleFail']);
  s.balance = 5000;
  T.eq(StoryRules.dueEvents(STORY_SCHULD, s, 'night').map((e) => e.id), ['kontrolleOk']);
  s.story.vars.schuld = 0;
  T.eq(StoryRules.ending(STORY_SCHULD, s).id, 'ehrlich');
  s.story.vars.schuld = 1; s.story.day = 31;
  T.eq(StoryRules.ending(STORY_SCHULD, s).id, 'doc');
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen** (`STORY_SCHULD is not defined`; chance-Test schlägt fehl, weil `hit` nicht gesetzt wird).

- [ ] **Step 3: `chance`-Effekt** – in `StoryRules.applyEffect` die Signatur auf `applyEffect(s, eff, story = {}, rng = Math.random)` ändern und **vor** `if ('var' in eff)` einfügen:

```js
    if ('chance' in eff) {
      if (rng() >= eff.chance) return {};
      const out = {};
      for (const e of eff.effects || []) Object.assign(out, StoryRules.applyEffect(s, e, story, rng));
      return out;
    }
```

- [ ] **Step 4: Szenen als Funktion + flags im Ctx** – im `story-engine`-Block:

In `Story.ctx()` nach `const c = { day: …, balance: … };` ergänzen: `c.flags = this.s.flags;`
In `Story.playScene`: `const panels = this.story.scenes[id] || [];` → `const def = this.story.scenes[id]; const panels = typeof def === 'function' ? def(this.ctx(extra)) : (def || []);`
In `Story.finish`: `const panels = (this.story.scenes[end.scene] || []).map(…)` → `const def = this.story.scenes[end.scene]; const panels = (typeof def === 'function' ? def(this.ctx({ stats })) : (def || [])).map((p) => Object.assign({}, p));`
`Cutscene.fill` nutzt nur `\w+`-Platzhalter – Funktions-Szenen greifen direkt auf `ctx.flags` zu.

- [ ] **Step 5: Story-Block** – `<script id="story-schuld">` nach `story-probe`:

```html
<script id="story-schuld">
/* ================= STORY 1: DIE SCHULD ================= */
const STORY_SCHULD = {
  id: 'schuld', title: 'Die Schuld', days: 30,
  start: { balance: 50, unlocked: { jobs: ['spueler', 'post'], doors: ['slots', 'horses'], rooms: ['bar', 'vito'] }, vars: { schuld: 50000, vertrauen: 0, ruf: 0, gezahlt: 0, duellSiege: 0, tuerSauber: 0 } },
  varMax: { vertrauen: 10, ruf: 10 },
  hud: [{ var: 'schuld', label: '🕶️ Vito', fmt: 'money', tone: 'danger' }, { var: 'vertrauen', label: '🤝', max: 10 }, { var: 'ruf', label: '🔥 Ruf', max: 10 }],
  goal: (s) => `Ziel: Vito ${UI.fmt(s.story.vars.schuld)} bis Tag 30`,
  lockReason: { roulette: 'Vito sagt nein', blackjack: 'Vito sagt nein', russian: 'Igor hat keine Zeit' },
  intro: 'schuld.intro',
  scenes: {
    /* ---- Intro ---- */
    'schuld.intro': [
      { bg: 'keller', who: 'du', mood: 'shock', text: 'Beton. Kalt. Ein Zettel vor meinem Gesicht: 50.000 €. Ich erinnere mich an nichts.' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Gestern Nacht hast du an meinem Tisch gesessen. Mit meinem Geld. Du warst sehr mutig. Fünfzigtausend mutig.' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Dreißig Tage. Dann liegt es hier auf dem Tisch – in Raten oder am Stück, mir egal. Ich bin kein Unmensch.' },
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Hier. Fünfzig Euro und eine Schürze. Die Spülküche ist hinten links, der Postmeister sucht Leute. Morgens arbeiten, abends spielen – so läuft das hier.' },
    ],
    /* ---- Kapitel ---- */
    'schuld.k2': [
      { bg: 'strasse', who: 'kevin', mood: 'happy', text: 'Digga! Hab gehört, du hast ein Vito-Problem. Ich hab Jobs: Päckchen fahren. Und Krause sucht einen Praktikanten – der Typ zahlt in Kaffee, aber die Akten…' },
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Vito hat die hinteren Tische aufgemacht. Roulette, Blackjack. Igor auch. Und die Bank redet mit dir – wenn du das brauchst.' },
    ],
    /* ---- Ereignisse ---- */
    'schuld.chantal3': [
      { bg: 'bar', who: 'chantal', mood: 'happy', text: 'Ehrlich jetzt – *du*? Hier? Süß. Du weißt nichts mehr, oder? Wir hatten… einen Abend. Vergiss es. Trink was.' },
    ],
    'schuld.wirt5': [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Ein Wort unter uns: Vito hat noch nie jemanden *bezahlen* lassen. Die Frist ist ein Spiel. Ich weiß nur nicht, welches.' },
    ],
    'schuld.kontrolle.ok': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Tag zehn. Ich wollte nur sehen, ob du arbeitest oder nur spielst. Du arbeitest. Gut.' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'happy', text: 'Igor mag dich. Das passiert selten. Weiter so.' },
    ],
    'schuld.kontrolle.fail': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Tag zehn. Fünftausend wollte ich sehen. Ich sehe {{balance}}. Das ist nicht fünftausend.' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'angry', text: 'Igor. Der Revolver. Kein Einsatz – nur eine Erinnerung daran, wem dein Kopf gehört.' },
    ],
    'schuld.duelLost': [
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Streifschuss. Vito wollte dich nicht tot, nur wach. Fünfhundert fürs Nähen. Ich schreib es dir auf – ach nein, du zahlst jetzt.' },
    ],
    'schuld.duelWon': [
      { bg: 'keller', who: 'igor', mood: 'calm', text: '…Du hast nicht gezittert. Das merke ich mir.' },
    ],
    /* ---- Kurier ---- */
    'schuld.kurier.polizei': [
      { bg: 'strasse', who: 'du', mood: 'shock', text: 'Blaulicht. Ein Streifenwagen rollt neben mir her. Das Päckchen wiegt plötzlich zehn Kilo.',
        choices: [
          { label: 'Laufen', value: 'run', cls: 'red', effects: [{ chance: 0.5, effects: [{ scene: 'schuld.kurier.verhaftet' }] }, { var: 'ruf', add: 1 }] },
          { label: 'Cool bleiben, bluffen', value: 'bluff', effects: [{ chance: 0.3, effects: [{ scene: 'schuld.kurier.verhaftet' }] }, { var: 'ruf', add: 1 }] },
        ] },
    ],
    'schuld.kurier.verhaftet': [
      { bg: 'strasse', who: 'du', mood: 'dead', fx: 'blackout', text: 'Handschellen. Eine Nacht in der Zelle, 200 € Strafe, und Vito weiß es, bevor ich draußen bin.' },
    ],
    'schuld.kurier.doc': [
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Ah, der Kurier. Kevins Ware. Sag ihm, die Qualität lässt nach. Und sag ihm nicht, dass ich das gesagt habe.' },
    ],
    'schuld.kurier.igor': [
      { bg: 'keller', who: 'kevin', mood: 'happy', text: 'Digga, das hier geht in den Keller. An Igor persönlich. Du kennst ihn doch.',
        choices: [
          { label: 'Klar, mach ich', value: 'ja', effects: [{ scene: 'schuld.kurier.igor2' }] },
          { label: 'Nicht in den Keller', value: 'nein', cls: 'ghost', effects: [{ var: 'ruf', add: -1 }] },
        ] },
    ],
    'schuld.kurier.igor2': [
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Kevin ist pünktlich. Du auch. Das ist gut.', },
    ],
    /* ---- Praktikant ---- */
    'schuld.prakt.insider': [
      { bg: 'bank', who: 'krause', mood: 'calm', text: 'Die Akte bleibt zu. Ach – Sie haben schon reingeschaut. Nun. Morgen früh gehen diese Aktien durch die Decke. Nur zwischen uns.',
        choices: [
          { label: 'Vorbörslich kaufen', value: 'kaufen', cls: 'red', effects: [{ balance: 400 }, { flag: 'insider' }] },
          { label: 'Das ist Insiderhandel', value: 'nein', cls: 'ghost', effects: [{ scene: 'schuld.prakt.korrekt' }] },
        ] },
    ],
    'schuld.prakt.korrekt': [{ bg: 'bank', who: 'krause', mood: 'happy', text: 'Sehr korrekt. Das mag ich. Kaffee?' }],
    'schuld.prakt.konto': [
      { bg: 'bank', who: 'krause', mood: 'calm', text: 'Ein Herr Vito hat hier ein Konto. Bemerkenswert leer für einen Mann mit Keller. Sein Laden läuft nicht so, wie er tut.' },
    ],
    'schuld.prakt.praemie': [
      { bg: 'bank', who: 'krause', mood: 'happy', text: 'Sie sind fleißig. Ich kann Ihren Zins nicht senken, das kann niemand. Aber hier: hundert Euro Fleißprämie. Nicht verzocken. Ich weiß, wo Sie abends sind.' },
    ],
    /* ---- Enden ---- */
    'schuld.ende.ehrlich': [
      { bg: 'hafen', who: 'vito', mood: 'calm', text: 'Fünfzigtausend. Auf den Cent. Weißt du, wie viele Leute das je geschafft haben?' },
      { bg: 'hafen', who: 'vito', mood: 'calm', text: 'Keiner. Die Frist war nie zum Zahlen da. Sie war da, um zu sehen, was du tust, wenn du keine Wahl hast.' },
      { bg: 'hafen', who: 'vito', mood: 'happy', text: 'Verschwinde, bevor ich dich mag. Und komm nicht zurück. Ehrlich gemeint – als Kompliment.' },
    ],
    'schuld.ende.doc': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Tag dreißig. {{schuld}} offen. Ich sagte, ich bin kein Unmensch. Ich sagte nicht, dass der Doc keiner ist.' },
      { bg: 'klinik', who: 'doc', mood: 'calm', fx: 'blackout', text: 'Zwei Nieren, ein Hobby. Zähl rückwärts von zehn.' },
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Er wacht wieder auf. Irgendwann. Das war deine Geschichte.' },
    ],
  },
  chapters: [
    { id: 'k1', title: 'Der Zettel', when: { day: { gte: 1 } } },
    { id: 'k2', title: 'Kleine Fische', when: { day: { gte: 6 } }, intro: 'schuld.k2', unlock: { jobs: ['kurier', 'praktikant', 'taxi'], doors: ['roulette', 'blackjack', 'russian'], rooms: ['bank'] } },
  ],
  events: [
    { id: 'chantal3', when: { day: { eq: 3 } }, once: true, at: 'night', scene: 'schuld.chantal3', effects: [{ flag: 'chantalKennt' }] },
    { id: 'wirt5', when: { day: { eq: 5 } }, once: true, at: 'night', scene: 'schuld.wirt5' },
    { id: 'kontrolleOk', when: { all: [{ day: { eq: 10 } }, { any: [{ balance: { gte: 5000 } }, { var: 'schuld', lte: 45000 }] }] }, once: true, at: 'night', scene: 'schuld.kontrolle.ok', effects: [{ var: 'vertrauen', add: 1 }, { flag: 'kontrolle' }] },
    { id: 'kontrolleFail', when: { all: [{ day: { eq: 10 } }, { not: { any: [{ balance: { gte: 5000 } }, { var: 'schuld', lte: 45000 }] } }] }, once: true, at: 'night', scene: 'schuld.kontrolle.fail', effects: [{ force: 'duel' }] },
    { id: 'duelLostBill', when: { all: [{ flag: 'duelLost' }, { notFlag: 'duelLostBilled' }] }, once: true, at: 'night', scene: 'schuld.duelLost', effects: [{ balance: -500 }, { flag: 'duelLostBilled' }] },
    { id: 'duelWonNote', when: { all: [{ flag: 'duelWon' }, { notFlag: 'duelWonNoted' }] }, once: true, at: 'night', scene: 'schuld.duelWon', effects: [{ flag: 'duelWonNoted' }, { var: 'vertrauen', add: 1 }] },
  ],
  jobScenes: {
    kurier: ['schuld.kurier.polizei', 'schuld.kurier.doc', 'schuld.kurier.igor'],
    praktikant: ['schuld.prakt.insider', 'schuld.prakt.konto', 'schuld.prakt.praemie'],
  },
  endings: [
    { id: 'ehrlich', title: 'Der Ehrliche', priority: 30, when: { var: 'schuld', lte: 0 }, scene: 'schuld.ende.ehrlich' },
    { id: 'doc', title: 'Der Doc', priority: 0, scene: 'schuld.ende.doc', fallback: true },
  ],
};
if (typeof Stories !== 'undefined') Stories.define(STORY_SCHULD);
</script>
```

Die Szene `schuld.kurier.verhaftet` wird über den `scene`-Effekt gespielt; der Tag-Verlust und die 200 € hängen an einem eigenen Effekt: in beiden Choices der Polizei-Szene die `chance`-Effekte auf `[{ scene: 'schuld.kurier.verhaftet' }, { balance: -200 }, { flag: 'verhaftet' }, { var: 'vertrauen', add: -1 }, { loseDay: true }]` erweitern (so eintragen, nicht nur die Szene). `praktikant`-Prämie: Szene `schuld.prakt.praemie` bekommt am Ende des Textes den Effekt über ein Event? Nein – Schicht-Karten ohne Choice brauchen trotzdem Effekte: `Story.playScene` wendet nur Choice-Effekte an. Ergänze deshalb in `Jobs.runShift` nach dem Abspielen: `const extra = (Story.story.jobEffects || {})[sceneId]; if (extra) await Story.applyEffects(extra);` und in der Story: `jobEffects: { 'schuld.prakt.praemie': [{ balance: 100 }], 'schuld.kurier.doc': [{ var: 'ruf', add: 1 }], 'schuld.prakt.konto': [{ flag: 'vitoPleite' }] }`.

- [ ] **Step 6: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs` → `79 bestanden, 0 fehlgeschlagen`; `tests/dom-selftest.sh` → 79.

- [ ] **Step 7: Prüfen im Browser**

`?story=schuld&fresh` → Intro (4 Panels) → Pinnwand mit Spüler und Post; Tagesleiste „Tag 1/30", Ziel „Vito 50.000 €", Zettel 🕶️ Vito 50.000 €, 🤝 0/10, 🔥 Ruf 0/10; Hub: Slots und Pferde offen, Rest verrammelt („Vito sagt nein" bei Roulette/Blackjack, „Igor hat keine Zeit"), Seitenleiste: Bar + Vitos Tisch. CDP-Durchlauf: Tag 1–5 per Post/Schlafen; Nacht 3 Chantal-Szene, Nacht 5 Wirt; Tag 6 Kapitel „Kleine Fische" mit Kevin/Wirt-Szenen, neue Jobs Kurier/Praktikant/Taxi (Taxi gesperrt ohne 200 €), Türen offen, Kredite in der Seitenleiste. Kurier-Schicht: +300 €, eine der drei Szenen; Polizei-Szene „Laufen" mehrfach (Konsole `Story.playScene('schuld.kurier.polizei')`) → manchmal Verhaftung (Blackout, −200, Tag verloren → direkt Nacht). Praktikant: alle drei Szenen. Nacht 10 mit < 5.000 €: Vito-Szene → erzwungenes Duell → danach Nacht 11 mit Doc-Rechnung (−500) oder Igor-Lob (+1 Vertrauen). Mit 5.000 € oder 5.000 gezahlt: Kontrolle ok. `State.s.story.vars.schuld = 100; Game.applyDelta(1000)` → Vitos Tisch → 100 zahlen → Schlafen → Ende „Der Ehrliche" mit Statistik; „Zum Titel"; Titel zeigt „Neue Story". `?story=schuld&fresh&day=30` → Pinnwand; Schlafen → Fallback „Der Doc".

- [ ] **Step 8: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Die Schuld – Kapitel 1–2, Kontrolle, Kurier, Praktikant, zwei Enden

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Story 1 – Kapitel 3–4, Türsteher/Croupier/Doc-Assistent, Enden „sturz" + „taxi", Achievements

**Files:**
- Modify: `keller37.html` (`story-schuld`: Kapitel, Ereignisse, Szenen, Job-Szenen, Enden, Bus-Listener; `achievements`: neue DEFS + Listener + Story-Abschnitt der Trophäenwand; Tests)

**Interfaces:**
- Produces: vollständige `STORY_SCHULD`; Achievements `jobFirst, teller10, nachtschicht, endeEhrlich, endeTaxi, endeSturz, alleEnden` (Gruppe `story`); `Achievements.renderWall` zeigt eine Trennzeile „Story".
- Consumes: `rr:result`, `job:done`, `spueler:result`, `taxi:result`, `story:ended`.

- [ ] **Step 1: Failing Tests** – vor `/* --- SELFTEST CASES END --- */`:

```js
T.test('STORY_SCHULD: vier Enden, Prioritäten, Sturz-Bedingung', () => {
  T.eq(STORY_SCHULD.endings.map((e) => e.id).sort(), ['doc', 'ehrlich', 'sturz', 'taxi']);
  const s = Object.assign(base({ balance: 100 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) });
  s.story.day = 28; Object.assign(s.story.flags, { hauptbuch: true, safe: true, igorZweifelt: true });
  T.eq(StoryRules.ending(STORY_SCHULD, s), null, 'Sturz braucht sturzJetzt oder Tag 30');
  s.story.flags.sturzJetzt = true;
  T.eq(StoryRules.ending(STORY_SCHULD, s).id, 'sturz');
  s.story.flags.fluchtHeute = true;
  T.eq(StoryRules.ending(STORY_SCHULD, s).id, 'sturz', 'Sturz vor Taxi');
  s.story.vars.schuld = 0;
  T.eq(StoryRules.ending(STORY_SCHULD, s).id, 'ehrlich', 'Ehrlich vor allem');
  const t = Object.assign(base({ balance: 100 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) });
  t.story.flags.fluchtHeute = true;
  T.eq(StoryRules.ending(STORY_SCHULD, t).id, 'taxi');
});
T.test('STORY_SCHULD: Kapitel 3/4 und Job-Freischaltung per Vertrauen', () => {
  const s = Object.assign(base({ balance: 100 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) });
  s.story.day = 13;
  T.eq(StoryRules.chapterFor(STORY_SCHULD, s).id, 'k3');
  T.eq(StoryRules.dueEvents(STORY_SCHULD, s, 'morning').map((e) => e.id), []);
  s.story.vars.vertrauen = 4;
  T.eq(StoryRules.dueEvents(STORY_SCHULD, s, 'morning').map((e) => e.id), ['tuerJob']);
  s.story.day = 21; s.story.vars.vertrauen = 7; s.story.seen.push('tuerJob');
  T.eq(StoryRules.chapterFor(STORY_SCHULD, s).id, 'k4');
  T.eq(StoryRules.dueEvents(STORY_SCHULD, s, 'morning').map((e) => e.id), ['croupierJob']);
  T.eq(STORY_SCHULD.jobScenes.tuersteher.length, 3); T.eq(STORY_SCHULD.jobScenes.croupier.length, 3); T.eq(STORY_SCHULD.jobScenes.docassi.length, 3);
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**.

- [ ] **Step 3: Story erweitern** – im `story-schuld`-Block:

`lockReason` unverändert. In `scenes` ergänzen:

```js
    /* ---- Kapitel 3/4 ---- */
    'schuld.k3': [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Woche drei. Der Doc sucht einen Assistenten, falls du einen Magen hast. Und Vito redet über dich. Das ist gut. Oder schlecht.' },
    ],
    'schuld.tuerJob': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Du hältst dich. Igor sagt, du zahlst, du spielst, du klaust nicht. Ich brauche jemanden an der Tür. Nachts. Bist du das?' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'happy', text: 'Hundert die Nacht, plus was die Gäste dir zustecken. Und du siehst, wer rein will. Das ist mehr wert als das Geld.' },
    ],
    'schuld.buero': [
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Vito will seinen Mantel. Büro, hinten. Ich bleibe an der Tür.' },
      { bg: 'hinterzimmer', who: 'du', mood: 'shock', text: 'Der Mantel hängt am Haken. Auf dem Schreibtisch liegt das Hauptbuch. Offen. Mein Name steht drin – mit einem Datum, an dem ich nicht hier war.',
        choices: [
          { label: 'Reinschauen', value: 'lesen', cls: 'red', effects: [{ flag: 'hauptbuch' }, { scene: 'schuld.buero2' }] },
          { label: 'Mantel nehmen, gehen', value: 'gehen', cls: 'ghost', effects: [{ var: 'tuerSauber', add: 1 }] },
        ] },
    ],
    'schuld.buero2': [
      { bg: 'hinterzimmer', who: 'du', mood: 'calm', text: 'Zwölf Namen, zwölf Schulden, keiner hat je gezahlt. Neben jedem ein Datum – und ein Vermerk: „Doc". Ich mache ein Foto. Meine Hand zittert nicht mal.' },
    ],
    'schuld.chantalBeichte': [
      { bg: 'hafen', who: 'chantal', mood: 'calm', text: 'Okay. Ehrlich jetzt. Der Abend, an den du dich nicht erinnerst? Vito hat mich geschickt. Ich sollte dich abfüllen und an den Tisch setzen.' },
      { bg: 'hafen', who: 'chantal', mood: 'angry', text: 'Du hast gar nicht gespielt. Er hat die Zahl in sein Buch geschrieben, als du schon unterm Tisch lagst. Das Hauptbuch. Im Büro. Ich hab es gesehen.' },
      { bg: 'hafen', who: 'chantal', mood: 'calm', text: 'Ich sag dir das, weil ich die Nächste auf der Liste bin. Und weil du süß bist. Hauptsächlich das Erste.' },
    ],
    'schuld.igorZweifel': [
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Dreimal. Dreimal hast du den Revolver gehalten und nicht gezittert. Vito zittert, wenn er das Buch aufschlägt.' },
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Ich arbeite für Vito, seit ich zwölf bin. Ich habe nie gefragt, was in dem Buch steht. Vielleicht sollte ich.' },
    ],
    'schuld.k4': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Letzte Woche. Ich zähle mit. Alle Tische sind offen, jede Tür. Nutz sie – oder nutz sie nicht. Am Tag dreißig sitzen wir hier.' },
    ],
    'schuld.croupierJob': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'happy', text: 'Du bist an der Tür der Beste, den ich je hatte. Also nehme ich dich von der Tür. Der Tisch. Karten, Kessel, Tageskasse. Ab morgen.' },
    ],
    'schuld.erinnerung': [
      { bg: 'keller', who: 'igor', mood: 'calm', text: 'Tag fünfundzwanzig. Vito lässt grüßen. Zwanzig Prozent, sagt er. Eine Erinnerung. Es tut mir leid.' },
    ],
    'schuld.fluchtAngebot': [
      { bg: 'strasse', who: 'kevin', mood: 'calm', text: 'Digga, hör zu. Du hast Geld, du hast ein Taxi, du hast noch Beine. Ich kenn einen, der macht Papiere. Neuer Name, Hafen, Fähre um vier Uhr morgens.' },
      { bg: 'strasse', who: 'kevin', mood: 'happy', text: 'Wenn du willst, sag es mir nachts. Ich frag jeden Abend einmal. Nur einmal.' },
    ],
    'schuld.fluchtFrage': [
      { bg: 'strasse', who: 'kevin', mood: 'calm', text: 'Heute Nacht? Fähre um vier. Danach fragt keiner mehr nach {{schuld}}.',
        choices: [
          { label: 'Heute Nacht', value: 'ja', cls: 'red', effects: [{ flag: 'fluchtHeute' }] },
          { label: 'Noch nicht', value: 'nein', cls: 'ghost' },
        ] },
    ],
    'schuld.igorSah': [
      { bg: 'keller', who: 'igor', mood: 'angry', text: 'Kevin redet zu viel. Papiere, Hafen, Fähre. Vito weiß es noch nicht. Ich noch nicht lange. Enttäusch mich nicht.' },
    ],
    'schuld.sturzFrage': [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Du hast das Buch. Du hast den Safe. Igor steht hinter dir. Jetzt oder nie – morgen ist Vito wieder vorsichtig.',
        choices: [
          { label: 'Jetzt', value: 'jetzt', cls: 'red', effects: [{ flag: 'sturzJetzt' }] },
          { label: 'Noch einen Tag', value: 'warten', cls: 'ghost' },
        ] },
    ],
    'schuld.tuerSauber': [{ bg: 'keller', who: 'igor', mood: 'calm', text: 'Drei Nächte, keiner reingelassen, der nicht auf der Liste stand. Vito hat es gesehen.' }],
    /* ---- Türsteher ---- */
    'schuld.tuer.hundert': [
      { bg: 'keller', who: 'makler', mood: 'happy', text: 'Hundert Euro, und Sie haben mich nie gesehen. Ich stehe nicht auf der Liste, aber ich stehe auf Roulette.',
        choices: [
          { label: 'Rein mit dir (+100 €)', value: 'rein', cls: 'red', effects: [{ balance: 100 }, { var: 'vertrauen', add: -1 }, { flag: 'gastRein' }] },
          { label: 'Liste ist Liste', value: 'nein', cls: 'ghost', effects: [{ var: 'tuerSauber', add: 1 }] },
        ] },
    ],
    'schuld.tuer.chantal': [
      { bg: 'keller', who: 'chantal', mood: 'calm', text: 'Lass mich rein. Ich muss mit Vito reden. Bitte – er hört sonst nicht zu.',
        choices: [
          { label: 'Reinlassen', value: 'rein', effects: [{ flag: 'chantalRein' }] },
          { label: 'Nicht heute', value: 'nein', cls: 'ghost', effects: [{ var: 'tuerSauber', add: 1 }, { scene: 'schuld.tuer.chantal2' }] },
        ] },
    ],
    'schuld.tuer.chantal2': [{ bg: 'keller', who: 'chantal', mood: 'angry', text: 'Sie sieht mich an, als hätte ich sie schon einmal enttäuscht. Vielleicht habe ich das.' }],
    'schuld.tuer.kevin': [
      { bg: 'keller', who: 'kevin', mood: 'happy', text: 'Digga, ich bin auf der Liste. Unter „K". Guck nicht so, ich liefere hier nur ab. An Igor. Winke, winke.',
        choices: [
          { label: 'Durchwinken', value: 'ja', effects: [{ var: 'ruf', add: 1 }] },
          { label: 'Igor holen', value: 'igor', cls: 'ghost', effects: [{ var: 'vertrauen', add: 1 }, { var: 'ruf', add: -2 }, { flag: 'kevinVerpfiffen' }] },
        ] },
    ],
    /* ---- Croupier ---- */
    'schuld.croup.kessel': [
      { bg: 'hinterzimmer', who: 'makler', mood: 'happy', text: 'Halten Sie den Kessel ein bisschen. Rot, nur heute. Dreihundert für Sie, und keiner merkt was.',
        choices: [
          { label: 'Halten (+300 €)', value: 'halten', cls: 'red', effects: [{ balance: 300 }, { flag: 'kesselGehalten' }, { chance: 0.3, effects: [{ scene: 'schuld.croup.erwischt' }, { var: 'vertrauen', add: -2 }] }] },
          { label: 'Der Kessel läuft, wie er läuft', value: 'nein', cls: 'ghost', effects: [{ var: 'vertrauen', add: 1 }] },
        ] },
    ],
    'schuld.croup.erwischt': [{ bg: 'hinterzimmer', who: 'vito', mood: 'angry', text: 'Ich habe Augen an jedem Tisch. Rot, dreimal, für den Makler? Ich bin enttäuscht. Igor auch.' }],
    'schuld.croup.vito': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Gib Karten. Und erzähl mir, was der Wirt so redet, wenn ich nicht da bin.',
        choices: [
          { label: 'Nichts. Er wischt Gläser.', value: 'nichts', effects: [{ var: 'vertrauen', add: 1 }] },
          { label: 'Er sagt, du lässt niemanden zahlen', value: 'verrat', cls: 'red', effects: [{ var: 'vertrauen', add: -1 }, { flag: 'wirtVerraten' }] },
        ] },
    ],
    'schuld.croup.safe': [
      { bg: 'hinterzimmer', who: 'igor', mood: 'calm', text: 'Vito ist weg. Die Tageskasse in den Safe. Die Kombination ist drei-sieben. Ich sage das nur einmal.',
        choices: [
          { label: 'Umsehen', value: 'safe', cls: 'red', effects: [{ flag: 'safe' }, { scene: 'schuld.croup.safe2' }] },
          { label: 'Kasse rein, Klappe zu', value: 'zu', cls: 'ghost', effects: [{ var: 'vertrauen', add: 1 }] },
        ] },
    ],
    'schuld.croup.safe2': [{ bg: 'hinterzimmer', who: 'du', mood: 'shock', text: 'Neben dem Geld: Fotos. Zwölf Leute, jeder unterm Tisch, jeder mit einem Datum. Und eine Quittung vom Doc. Ich schließe den Safe. Drei-sieben.' }],
    /* ---- Doc-Assistent ---- */
    'schuld.doc.niere': [
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Ein Patient, zwei Nieren, kein Geld. Er schläft. Halt die Schale.',
        choices: [
          { label: 'Schale halten (+150 €)', value: 'halten', cls: 'red', effects: [{ balance: 150 }, { flag: 'komplize' }, { var: 'ruf', add: 1 }] },
          { label: 'Ich geh', value: 'gehen', cls: 'ghost', effects: [{ scene: 'schuld.doc.gehen' }] },
        ] },
    ],
    'schuld.doc.gehen': [{ bg: 'klinik', who: 'doc', mood: 'calm', text: 'Schade. Du hättest ruhige Hände. Die Tür ist da hinten, schließ sie leise.' }],
    'schuld.doc.vorbesitzer': [
      { bg: 'klinik', who: 'doc', mood: 'calm', text: 'Wusstest du, dass der Keller mal jemand anderem gehörte? Vor drei Jahren. Der Mann lag auf genau diesem Tisch. Vito hat die Rechnung bezahlt. Großzügig.' },
    ],
    'schuld.doc.igor': [
      { bg: 'klinik', who: 'igor', mood: 'shock', text: 'Streifschuss. Ein Duell. Der andere hatte Glück. Halt mich fest, der Doc näht schlecht, wenn ich zucke.' },
      { bg: 'klinik', who: 'igor', mood: 'calm', text: 'Du hast ruhige Hände. Das habe ich schon einmal gesagt. Ich sage es nicht oft.' },
    ],
    /* ---- Enden ---- */
    'schuld.ende.sturz': [
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Tag der Abrechnung. Setz dich. Igor, die Tür.' },
      { bg: 'hinterzimmer', who: 'igor', mood: 'calm', text: 'Nein. Heute nicht. Das Buch, Vito. Der Safe. Zwölf Namen. Ich habe nie gefragt. Jetzt frage ich.' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'shock', fx: 'blackout', text: 'Du… weißt nicht, was du tust. Igor. IGOR.' },
      { bg: 'bar', who: 'wirt', mood: 'happy', text: 'Vito ist durch die Hintertür. Der Keller gehört jetzt dem, der die Schlüssel hat – mir. Und du fängst morgen an. Als Croupier. Der Kessel läuft, wie er läuft.' },
    ],
    'schuld.ende.taxi': (ctx) => {
      const panels = [
        { bg: 'strasse', who: 'kevin', mood: 'calm', text: 'Vier Uhr. Papiere im Handschuhfach. Neuer Name, klingt nach Zahnarzt. Fahr.' },
      ];
      if (ctx.flags.chantalKennt && !ctx.flags.komplize) panels.push({ bg: 'hafen', who: 'chantal', mood: 'happy', text: 'Rutsch rüber. Ehrlich jetzt – dachtest du, ich bleibe hier? Ich bin die Nächste auf der Liste. Fahr.' });
      panels.push({ bg: 'hafen', who: 'du', mood: 'calm', text: 'Die Fähre legt ab. Das Handy vibriert. Eine Nachricht, unbekannte Nummer: „Ich bin kein Unmensch. Aber ich habe Zeit. – V."' });
      return panels;
    },
```

In `chapters` ergänzen:
```js
    { id: 'k3', title: 'Die Tür', when: { day: { gte: 13 } }, intro: 'schuld.k3', unlock: { jobs: ['docassi'], rooms: ['invest'] } },
    { id: 'k4', title: 'Abrechnung', when: { day: { gte: 21 } }, intro: 'schuld.k4', unlock: { doors: ['roulette', 'slots', 'horses', 'russian', 'blackjack'] } },
```

In `events` ergänzen:
```js
    { id: 'tuerJob', when: { all: [{ day: { gte: 13 } }, { var: 'vertrauen', gte: 4 }] }, once: true, at: 'morning', scene: 'schuld.tuerJob', effects: [{ unlock: { jobs: ['tuersteher'] } }] },
    { id: 'buero', when: { all: [{ jobDone: 'tuersteher', gte: 1 }, { notFlag: 'bueroGesehen' }] }, once: true, at: 'morning', scene: 'schuld.buero', effects: [{ flag: 'bueroGesehen' }] },
    { id: 'chantalBeichte', when: { all: [{ day: { gte: 15 } }, { flag: 'chantalKennt' }] }, once: true, at: 'night', scene: 'schuld.chantalBeichte', effects: [{ flag: 'chantalBeichte' }] },
    { id: 'igorZweifel', when: { var: 'duellSiege', gte: 3 }, once: true, at: 'spin:after', scene: 'schuld.igorZweifel', effects: [{ flag: 'igorZweifelt' }] },
    { id: 'tuerSauber', when: { var: 'tuerSauber', gte: 3 }, at: 'night', scene: 'schuld.tuerSauber', effects: [{ var: 'vertrauen', add: 1 }, { var: 'tuerSauber', set: 0 }] },
    { id: 'croupierJob', when: { all: [{ day: { gte: 21 } }, { var: 'vertrauen', gte: 7 }] }, once: true, at: 'morning', scene: 'schuld.croupierJob', effects: [{ unlock: { jobs: ['croupier'] } }] },
    { id: 'erinnerung', when: { day: { eq: 25 } }, once: true, at: 'night', scene: 'schuld.erinnerung', effects: [{ balancePct: -20, min: 100 }] },
    { id: 'fluchtAngebot', when: { all: [{ day: { gte: 20 } }, { jobDone: 'taxi', gte: 1 }, { balance: { gte: 8000 } }, { notFlag: 'fluchtBereit' }] }, once: true, at: 'night', scene: 'schuld.fluchtAngebot', effects: [{ flag: 'fluchtBereit' }] },
    { id: 'fluchtFrage', when: { all: [{ flag: 'fluchtBereit' }, { notFlag: 'fluchtHeute' }] }, at: 'night', scene: 'schuld.fluchtFrage' },
    { id: 'igorSah', when: { all: [{ flag: 'fluchtBereit' }, { notFlag: 'igorSah' }] }, once: true, at: 'morning', scene: 'schuld.igorSah', effects: [{ flag: 'igorSah' }, { var: 'vertrauen', add: -3 }] },
    { id: 'sturzFrage', when: { all: [{ day: { gte: 28 } }, { flag: 'hauptbuch' }, { flag: 'safe' }, { flag: 'igorZweifelt' }, { notFlag: 'sturzJetzt' }] }, at: 'night', scene: 'schuld.sturzFrage' },
```
Reihenfolge der Nacht-Ereignisse ist die Array-Reihenfolge: `fluchtFrage` muss **nach** `fluchtAngebot` stehen (steht so), `sturzFrage` als letztes.

In `jobScenes` ergänzen:
```js
    tuersteher: ['schuld.tuer.hundert', 'schuld.tuer.chantal', 'schuld.tuer.kevin'],
    croupier: ['schuld.croup.kessel', 'schuld.croup.vito', 'schuld.croup.safe'],
    docassi: ['schuld.doc.niere', 'schuld.doc.vorbesitzer', 'schuld.doc.igor'],
```
`jobEffects` ergänzen: `'schuld.doc.vorbesitzer': [{ var: 'ruf', add: 1 }], 'schuld.doc.igor': [{ var: 'vertrauen', add: 1 }, { flag: 'igorDank' }]`.

In `endings` ergänzen (vor `doc`):
```js
    { id: 'sturz', title: 'Der Sturz', priority: 20, when: { all: [{ flag: 'hauptbuch' }, { flag: 'safe' }, { flag: 'igorZweifelt' }, { any: [{ flag: 'sturzJetzt' }, { day: { gte: 30 } }] }] }, scene: 'schuld.ende.sturz' },
    { id: 'taxi', title: 'Das Taxi', priority: 10, when: { flag: 'fluchtHeute' }, scene: 'schuld.ende.taxi' },
```

Am Ende des Blocks (nach `Stories.define`) der Duell-Zähler:
```js
Bus.on('rr:result', ({ victim }) => {
  if (State.mode !== 'story' || !State.s.story || State.s.story.id !== 'schuld' || victim !== 'igor') return;
  const v = State.s.story.vars;
  v.duellSiege = (v.duellSiege || 0) + 1;
  if (v.duellSiege <= 3) StoryRules.applyEffect(State.s, { var: 'vertrauen', add: 1 }, STORY_SCHULD);
  State.save(); UI.renderWallet();
});
```

- [ ] **Step 4: Achievements** – im `achievements`-Block `DEFS` ergänzen:

```js
    { id: 'jobFirst', title: 'Erster Arbeitstag', icon: '🧾', desc: 'Einen Job in der Story beendet.', group: 'story' },
    { id: 'teller10', title: 'Tellerwäscher', icon: '🍽️', desc: '10 von 10 Tellern sauber.', group: 'story' },
    { id: 'nachtschicht', title: 'Nachtschicht', icon: '🚕', desc: 'Taxi-Schicht mit mindestens 200 €.', group: 'story' },
    { id: 'endeEhrlich', title: 'Der Ehrliche', icon: '🤝', desc: 'Vito bis auf den Cent bezahlt.', group: 'story' },
    { id: 'endeTaxi', title: 'Das Taxi', icon: '⛴️', desc: 'Mit der Fähre um vier verschwunden.', group: 'story' },
    { id: 'endeSturz', title: 'Der Sturz', icon: '📕', desc: 'Vito durch die Hintertür geschickt.', group: 'story' },
    { id: 'alleEnden', title: 'Alle Wege', icon: '🗺️', desc: 'Alle vier Enden einer Story gesehen.', group: 'story' },
```
Listener ergänzen:
```js
Bus.on('job:done', () => Achievements.unlock('jobFirst'));
Bus.on('spueler:result', ({ hits }) => { if (hits >= 10) Achievements.unlock('teller10'); });
Bus.on('taxi:result', ({ pay }) => { if (pay >= 200) Achievements.unlock('nachtschicht'); });
Bus.on('story:ended', ({ id, ending }) => {
  const map = { ehrlich: 'endeEhrlich', taxi: 'endeTaxi', sturz: 'endeSturz' };
  if (map[ending]) Achievements.unlock(map[ending]);
  const run = State.meta.storyRuns[id];
  if (run && run.endings.length >= 4) Achievements.unlock('alleEnden');
});
```
`renderWall(grid)` so ändern, dass vor dem ersten `group: 'story'`-Eintrag eine Trennzeile eingefügt wird: `grid.append(h('div', { class: 'trophy-sep' }, 'Story'))` – CSS: `.trophy-sep { grid-column: 1 / -1; font-family: var(--font-display); letter-spacing: .12em; color: var(--dim); margin-top: 6px; }`.

- [ ] **Step 5: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs` → `81 bestanden, 0 fehlgeschlagen`; `tests/dom-selftest.sh` → 81.

- [ ] **Step 6: Prüfen im Browser (CDP, vier Läufe)**

Alle über `?story=schuld&fresh&day=<n>` plus Konsolen-Setup:
1. **Sturz:** `day=13`, Konsole `State.s.story.vars.vertrauen = 4; State.save(); Story.morning()` → Vito-Szene, Türsteher an der Pinnwand; Türsteher-Schicht → Szene; nächster Morgen → Büro-Szene → „Reinschauen" (hauptbuch). `vars.vertrauen = 7; State.s.story.day = 21; Story.night()`-Ablauf bis Kapitel 4 → Croupier-Szene, Croupier-Schicht bis Safe-Szene → „Umsehen" (safe). Russisch Roulette dreimal gewinnen (Konsole: `for (…) Bus.emit('rr:result', {victim:'igor'})`) → Igor-Zweifel-Szene beim nächsten `spin:after` (einen Slot-Spin machen). Tag 28 Nacht → Wirt „Jetzt oder nie" → „Jetzt" → Ende „Der Sturz". Trophäe „Der Sturz".
2. **Taxi:** `day=20`, `Game.applyDelta(9000); State.s.story.jobsDone.taxi = 1; State.save()`; Abend → Schlafen → Kevin-Angebot, dann Frage → „Noch nicht"; nächster Morgen Igor-Szene (Vertrauen −3); Abend → Schlafen → Frage → „Heute Nacht" → Ende „Das Taxi" (mit Chantal-Panel, wenn `chantalKennt` gesetzt und nicht `komplize`).
3. **Erinnerung + Doc-Assistent:** `day=24`, Kontostand 1.000 → Nacht 25: Igor, −200 €. Doc-Assistent: alle drei Szenen (Konsole `Story.playScene(...)`), `komplize` nach Schale halten.
4. **Kessel:** `Story.playScene('schuld.croup.kessel')` mehrfach „Halten" → gelegentlich Vito-Erwischt-Szene, Vertrauen −2.
Mobile 400 px: Pinnwand einspaltig, Tagesleiste umbricht, Spüler/Taxi bedienbar (Tap-Zonen).

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Die Schuld – Kapitel 3–4, Türsteher/Croupier/Doc, Sturz- und Taxi-Ende, Story-Trophäen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Playtest, Checkliste, Screenshots, Spec-Abgleich

**Files:**
- Create: `tests/playtest-story.py` (CDP-Durchlauf, aus dem Scratchpad-Skript `playtest.py` des Sandbox-Playtests abgeleitet – dessen Aufbau ist in `docs/superpowers/checklist-2026-09-15.md` beschrieben)
- Create: `docs/superpowers/checklist-story-2026-09-16.md`, `docs/superpowers/screenshots/story-*.png`
- Modify: `keller37.html` nur bei Fehlern; `README.md` (Abschnitt „Story-Modus" + Dev-Parameter)

- [ ] **Step 1: Playtest-Skript** – `tests/playtest-story.py` fährt mit CDP (Chrome `--headless=new --remote-debugging-port=9335`, `Emulation.setDeviceMetricsOverride` optional per `--mobile`) folgende Sequenz und speichert Screenshots nach `/tmp/k37story/`: Titel → Story → Intro (mid-typing) → Pinnwand → Spüler (mid-Schicht, Ergebnis) → Abend-Hub mit verrammelten Türen → Vitos Tisch → Schlafen (Nachtblende) → Tag 2 → Post-Schicht (mid) → Tag 3 Nacht Chantal → Tag 6 Kapitel-Szene → Taxi (mid) → Nacht 10 Kontrolle fail → erzwungenes Duell → Ende „Doc" via `?day=30` → Titel „Neue Story" → Freies Spiel unverändert (Kontostand, Türen). Konsolenfehler/Exceptions werden gesammelt; am Ende `ERRORS n`.

- [ ] **Step 2: Checkliste** – `docs/superpowers/checklist-story-2026-09-16.md` mit allen Punkten aus Spec §13 (jede Szene von Story 1 einmal, alle vier Enden, alle 15 Schicht-Karten-Szenen, beide Mini-Spiele Gewinn/Verlust, Titel ↔ Modi ohne Datenverlust, Reload mitten im Tag, Mobile 400 px, Reduced Motion, Selbsttests 81, freie Sandbox unverändert: `?screen=`-Screenshots gegen `docs/superpowers/screenshots/*.png` vergleichen). Jeden Punkt ausführen, ✅/❌ mit Beleg; Fehler surgical fixen (eigene Commits).

- [ ] **Step 3: Screenshots** – `docs/superpowers/screenshots/story-title.png`, `story-jobs.png`, `story-spueler.png`, `story-taxi.png`, `story-hub-locked.png`, `story-vito.png`, `story-ending-sturz.png`, `story-mobile-jobs.png`.

- [ ] **Step 4: README** – Abschnitt „Story-Modus" (was es ist, Titelscreen, Jobs, Enden ohne Spoiler) und die neuen Dev-Parameter in der Tabelle.

- [ ] **Step 5: Grep + Tests** – `grep -c 'alert(\|confirm(\|prompt(' keller37.html` → 0; `grep -c 'onclick="' keller37.html` → 0; Node/DOM-Selbsttest 81/81.

- [ ] **Step 6: Commit**

```bash
git add tests/playtest-story.py docs/superpowers/checklist-story-2026-09-16.md docs/superpowers/screenshots/story-*.png README.md keller37.html
git commit -m "docs(story): Playtest-Skript, Abnahme-Checkliste, Screenshots, README

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Selbst-Review des Plans

**Spec-Abdeckung:** §3 Titel/Modi → T2; §4 Modus-Umschaltung → T2; §5 Tagesschleife (Daybar, Morgen/Abend/Nacht, Sperren, Nachtblende) → T3; §6 Bedingungen → T1; §7 Datenformat, Effekte, erzwungenes Duell → T1/T3/T7 (`chance`); §8 Job-Pool (Pinnwand, Schicht-Karten, Spüler, Taxi, Post-Deckel, Kaution) → T4–T6; §9 Story 1 (Variablen, Räume, Intro, Kapitel, Ereignisse, Enden, Vertrauen/Ruf-Regeln) → T7/T8; §11 Achievements/Meta → T2 (`storyRuns`), T3 (`finish`), T8; §12 UI-Details → T2–T6; §13 Verifikation → Tests in T1–T3/T7/T8, Playtest T9; §14 Reihenfolge eingehalten.

**Bewusste Abweichungen (Rulings):** Raum `life` bleibt in Story 1 gesperrt; Platzhalter `{{schuld}}` statt `{{var.schuld}}`; Vertrauen „+1 pro 3 Türsteher-Schichten ohne Gast" über `tuerSauber`-Zähler (Choices „Liste ist Liste"/„Nicht heute"/„Mantel nehmen"); „Igor sieht die Flucht" ist ein deterministisches Morgen-Ereignis nach dem Angebot (−3 Vertrauen) statt an eine Türsteher-Schicht gekoppelt; die Büro-Szene läuft am Morgen nach der ersten Türsteher-Nacht; Schicht-Karten ohne Choice bekommen Effekte über `jobEffects`.

**Typ-Konsistenz:** `StoryRules.applyEffect(s, eff, story, rng)` (T1, erweitert T7), `Story.playScene(id, extra)`, `Story.applyEffects(list)`, `Story.jobDone(id, earned)`, `Jobs.take/runShift/finishGame/abort`, `Russian.start({forced:true})` + `rr:forced`, Bus-Events `job:done {id, earned}`, `spueler:result {hits, breaks, pay}`, `taxi:result {passengers, tickets, pay}`, `story:ended {id, ending}`, `story:day {day}` – in Emittern (T3–T8) und Listenern (T8) gleich benannt. Selbsttest-Zählung: 57 → 72 (T1) → 74 (T2) → 76 (T3) → 79 (T7) → 81 (T8).
