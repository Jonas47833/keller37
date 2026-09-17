# Story-Engine 2 (Voraussetzungen, Stats, Hooks, Effekte, sofortige Enden) – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Story-Engine so erweitern, dass Story 2 „Der Kater" (und das Casino Royal) rein als Daten obendrauf gesetzt werden können – ohne Story-2-Sonderfälle in der Engine.

**Architecture:** Alle neue Logik landet als reine Funktionen in `StoryRules` (Block `story-rules`) bzw. `Rules` (Block `rules`), weil nur diese Blöcke im Node-Selbsttest laufen. `Story` (Block `story-engine`), `Actions`/`Life` (Block `rooms`), die Minispiele und der Titelscreen verdrahten die Funktionen nur. Story-Zustand, der bisher nicht existiert (`prev`, `prices`, `enabled`, `disabled`, `luckMod`, `jobMod`, neue Stats), lebt in `s.story` und wird von `freshStoryPart` angelegt.

**Tech Stack:** Vanilla JS in einer HTML-Datei (`keller37.html`), Selbsttest im Block `selftest` (läuft per `node tests/run-selftest.mjs` in Node und per `tests/dom-selftest.sh` in Chrome).

**Spec:** `docs/superpowers/specs/2026-09-17-story-kater-design.md`, Abschnitte 2, 4 (Zitter-Tag/Job-Modifikator), 8, 10.

## Global Constraints

- Ein-Datei-Vorgabe: alles in `keller37.html`; keine neuen Dateien außer Doku.
- Node-Selbsttest lädt nur `rules, gear-rules, util, state, bus, story-rules, story-probe, story-schuld, selftest` – neue testbare Logik gehört in `rules` oder `story-rules`, nie in `story-engine`.
- Parallelarbeit am Block `rules` (Balancing-Instanz): dort nur die zwei genannten Ein-Zeilen-Änderungen (`luck`, `canTherapy`), sonst nichts anfassen.
- Keine Story-2-Bezeichner in der Engine (kein `kater`, `leber`, `pegel` außerhalb von Tests).
- Testnamen deutsch, Stil wie bestehende `T.test('…', () => …)`.
- Vor jedem Commit: `node tests/run-selftest.mjs` grün. Vor dem letzten Commit zusätzlich `tests/dom-selftest.sh`.
- Commit-Messages enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Abweichung von der Spec (bewusst): `luckMod` wird in `Rules.luck` addiert und das Ergebnis auf ≥ 0 geklemmt. Ein negativer Modifikator neutralisiert Bier-/Brownie-/Auto-Glück, macht Tische aber nicht schlechter als nüchtern.

---

## Dateistruktur

Alle Änderungen in `keller37.html`, nach Block:

| Block | Änderung |
|---|---|
| `rules` | `Rules.luck` addiert `s.story.luckMod` (Klemme ≥ 0); `Rules.canTherapy` akzeptiert `s.story.enabled.therapy` |
| `story-rules` | `HOOKS`, `requirementMet`, `pickStory` (Filter), `nextStory`, `prevEndings`, `check` (`prevEnding`), `recordSpin`, `applyEffect` (`luckMod`, `jobMod`, `price`, `enable`, `disable`), `price`, `purchaseAllowed`, `jobMod`, `ending` (`immediateOnly`), `validate` (neu: `requires`, `at`, `immediate`), `freshStoryPart(story, storyRuns)` |
| `state` | `freshStory` reicht `storyRuns` durch, setzt `brownieCost` aus Story-Preis |
| `story-engine` | `Stories.next()`, `Stories.locked()`; `Story.enter` (`?prev`, `forcedNext`), `Story.hook(at)`, `Story.checkImmediate()`, `night()` mit `sleep`, `finish()` (`last`, `forcedNext`), `hudNotes` (Label als Funktion), `win`/`loss`-Bus → `recordSpin` |
| `title` + `tpl-title` | Tag zeigt nächste Story, Hinweis auf gesperrte |
| `rooms` | `Actions.beer/brownie/kidney`, `Life.therapy/render`: Story-Preise, Hooks, `purchaseAllowed` |
| `ui` (`renderSide`) | Bar-Preise aus `StoryRules.price` |
| `jobs`, `job-spueler`, `job-taxi`, `rules` (`postmanTier`) | `jobMod` konsumieren |
| `selftest` | neue Tests |
| `README.md` | Dev-Parameter `?prev=` |

---

### Task 1: Story-Voraussetzungen (`requires`), `nextStory`, `prevEndings`

**Files:**
- Modify: `keller37.html` Block `story-rules` (`pickStory`, `validate`, `freshStoryPart`), Block `state` (`freshStory`)
- Test: `keller37.html` Block `selftest`, nach dem Test `'StoryRules.pickStory: am längsten nicht gespielt, dev nie'`

**Interfaces:**
- Produces:
  - `StoryRules.requirementMet(story, storyRuns) → boolean`
  - `StoryRules.pickStory(stories, storyRuns, rng) → id` (jetzt mit `requires`-Filter; wirft, wenn keine Story wählbar)
  - `StoryRules.nextStory(stories, storyRuns, currentId) → id`
  - `StoryRules.prevEndings(storyRuns) → { [storyId]: lastEndingId }`
  - `s.story.prev` (Objekt wie `prevEndings`), angelegt in `freshStoryPart(story, storyRuns = {})`
  - `State.freshStory(story)` ruft `StoryRules.freshStoryPart(story, this.meta.storyRuns)`

- [ ] **Step 1: Failing Tests schreiben**

Im Block `selftest`, direkt nach dem bestehenden Test `'StoryRules.pickStory: am längsten nicht gespielt, dev nie'` einfügen:

```js
T.test('StoryRules.requirementMet / pickStory: requires filtert', () => {
  const a = { id: 'a' }, b = { id: 'b', requires: 'a' };
  T.eq(StoryRules.requirementMet(a, {}), true);
  T.eq(StoryRules.requirementMet(b, {}), false);
  T.eq(StoryRules.requirementMet(b, { a: { lastPlayed: 1, endings: [] } }), false, 'gespielt ohne Ende reicht nicht');
  T.eq(StoryRules.requirementMet(b, { a: { lastPlayed: 1, endings: ['x'] } }), true);
  T.eq(StoryRules.pickStory([a, b], {}, seq(0.99)), 'a', 'b ist gesperrt');
  T.eq(StoryRules.pickStory([a, b], { a: { lastPlayed: 5, endings: ['x'] } }, seq(0)), 'b', 'b nie gespielt = ältestes');
  T.throws(() => StoryRules.pickStory([b], {}, seq(0)), 'keine wählbare Story wirft');
});
T.test('StoryRules.nextStory: Reihenfolge, Voraussetzung, sonst pickStory', () => {
  const a = { id: 'a' }, b = { id: 'b', requires: 'a' }, c = { id: 'c' };
  const runs = { a: { lastPlayed: 9, endings: ['x'] } };
  T.eq(StoryRules.nextStory([a, b, c], runs, 'a'), 'b');
  T.eq(StoryRules.nextStory([a, b, c], { a: { lastPlayed: 9, endings: [] } }, 'a'), 'c', 'b gesperrt → nächste in Reihenfolge');
  T.eq(StoryRules.nextStory([a, b, c], Object.assign({ c: { lastPlayed: 1, endings: ['y'] } }, runs), 'c'), 'b', 'nach der letzten: pickStory (b nie gespielt)');
  T.eq(StoryRules.nextStory([a], { a: { lastPlayed: 1, endings: ['x'] } }, 'a'), 'a', 'einzige Story wiederholt sich');
});
T.test('StoryRules.prevEndings: letztes Ende je Story', () => {
  T.eq(StoryRules.prevEndings({}), {});
  T.eq(StoryRules.prevEndings({ a: { lastPlayed: 1, endings: ['x', 'y'] } }), { a: 'y' });
  T.eq(StoryRules.prevEndings({ a: { lastPlayed: 1, endings: ['x', 'y'], last: 'x' } }), { a: 'x' }, 'last hat Vorrang');
  T.eq(StoryRules.prevEndings({ a: { lastPlayed: 1, endings: [] } }), {});
});
T.test('StoryRules.freshStoryPart: prev aus storyRuns', () => {
  const p = StoryRules.freshStoryPart(probeStory(), { schuld: { lastPlayed: 1, endings: ['doc'] } });
  T.eq(p.prev, { schuld: 'doc' });
  T.eq(StoryRules.freshStoryPart(probeStory()).prev, {});
});
T.test('StoryRules.validate: requires muss bekannte Story sein', () => {
  const st = Object.assign({}, STORY_PROBE, { id: 'x', requires: 'gibtsnicht' });
  const errs = StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post'], ['probe']);
  T.eq(errs, ['x: requires "gibtsnicht" unbekannt']);
  T.eq(StoryRules.validate(Object.assign({}, st, { requires: 'probe' }), Object.keys(STORY_PROBE.scenes), ['spueler', 'post'], ['probe']), []);
});
```

`T.throws` gibt es noch nicht – im `SelfTest`-Objekt (Block `selftest`, neben `eq`/`ok`) ergänzen:

```js
  throws(fn, msg = '') { let threw = false; try { fn(); } catch (e) { threw = true; } if (!threw) throw new Error(`${msg} – kein Fehler geworfen`); },
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag sehen**

Run: `node tests/run-selftest.mjs`
Expected: mindestens 5 FAIL, u. a. `StoryRules.requirementMet is not a function`.

- [ ] **Step 3: Implementieren**

In `StoryRules` (Block `story-rules`) `pickStory` ersetzen und die neuen Funktionen daneben einfügen:

```js
  requirementMet(story, storyRuns) {
    if (!story.requires) return true;
    const run = storyRuns[story.requires];
    return !!(run && run.endings && run.endings.length);
  },
  pickStory(stories, storyRuns, rng) {
    const cands = stories.filter((st) => !st.dev && StoryRules.requirementMet(st, storyRuns));
    if (!cands.length) throw new Error('Keine wählbare Story');
    const last = (st) => (storyRuns[st.id] && storyRuns[st.id].lastPlayed) || 0;
    const min = Math.min(...cands.map(last));
    const oldest = cands.filter((st) => last(st) === min);
    return oldest[Math.floor(rng() * oldest.length)].id;
  },
  /* „Nächste Story“ nach einem Ende: die nächste in Definitionsreihenfolge mit erfüllter Voraussetzung, sonst pickStory */
  nextStory(stories, storyRuns, currentId) {
    const list = stories.filter((st) => !st.dev);
    const idx = list.findIndex((st) => st.id === currentId);
    for (let i = idx + 1; i < list.length; i++) if (StoryRules.requirementMet(list[i], storyRuns)) return list[i].id;
    return StoryRules.pickStory(list, storyRuns, Math.random);
  },
  prevEndings(storyRuns) {
    const out = {};
    for (const [id, run] of Object.entries(storyRuns || {})) {
      const last = run.last || (run.endings && run.endings[run.endings.length - 1]);
      if (last) out[id] = last;
    }
    return out;
  },
```

In `validate(story, sceneIds, jobIds)` die Signatur um `storyIds = null` erweitern und vor `return errs;` einfügen:

```js
    if (story.requires && storyIds && !storyIds.includes(story.requires)) errs.push(`${story.id}: requires "${story.requires}" unbekannt`);
```

`freshStoryPart(story)` → `freshStoryPart(story, storyRuns = {})`, im Rückgabeobjekt ergänzen:

```js
      prev: StoryRules.prevEndings(storyRuns),
```

In `State.freshStory(story)` (Block `state`):

```js
    s.story = StoryRules.freshStoryPart(story, this.meta.storyRuns);
```

In `Stories.validateAll()` (Block `story-engine`) `storyIds` mitgeben:

```js
    const storyIds = Object.keys(this.all);
    for (const st of Object.values(this.all)) errs.push(...StoryRules.validate(st, sceneIds, jobIds || (st.start.unlocked.jobs), storyIds));
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node tests/run-selftest.mjs`
Expected: `… bestanden, 0 fehlgeschlagen`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): requires/nextStory/prevEndings in StoryRules, prev im Story-Zustand

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Bedingung `prevEnding`, `finish` merkt `last`, „Nächste Story“ in Reihenfolge, `?prev=`

**Files:**
- Modify: `keller37.html` Block `story-rules` (`check`), Block `story-engine` (`Story.enter`, `Story.finish`, `consumeDevParams`), Block `title` (`Title.show`), Template `tpl-title`, Block `story-engine` (`Stories`)
- Test: Block `selftest`

**Interfaces:**
- Consumes: `StoryRules.nextStory`, `StoryRules.prevEndings`, `s.story.prev` (Task 1)
- Produces:
  - Bedingung `{ prevEnding: { story: 'schuld', id: 'doc' } }`
  - `State.meta.storyRuns[id].last` (id des zuletzt erreichten Endes)
  - `Stories.next() → { id, title } | null` (Story, die „Neue Story“ starten würde), `Stories.locked() → [{ id, title, requires }]`
  - `Story.forcedNext` (interner Übergabewert von `finish` an `enter`)
  - Dev-Parameter `?prev=<endingId>` (mit `?fresh`)

- [ ] **Step 1: Failing Test schreiben**

Nach dem Test aus Task 1 `'StoryRules.freshStoryPart: prev aus storyRuns'`:

```js
T.test('StoryRules.check: prevEnding', () => {
  const s = Object.assign(base(), { story: Object.assign(StoryRules.freshStoryPart(probeStory()), { prev: { schuld: 'doc' } }) });
  T.eq(StoryRules.check({ prevEnding: { story: 'schuld', id: 'doc' } }, s), true);
  T.eq(StoryRules.check({ prevEnding: { story: 'schuld', id: 'taxi' } }, s), false);
  T.eq(StoryRules.check({ prevEnding: { story: 'nie', id: 'doc' } }, s), false);
  T.eq(StoryRules.check({ not: { prevEnding: { story: 'schuld', id: 'sturz' } } }, s), true);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs`
Expected: FAIL `Ungültige Bedingung: {"prevEnding":…}`.

- [ ] **Step 3: Implementieren**

In `StoryRules.check`, vor dem abschließenden `throw`:

```js
    if ('prevEnding' in cond) return (st.prev || {})[cond.prevEnding.story] === cond.prevEnding.id;
```

In `Story.finish(end)` nach `if (!run.endings.includes(end.id)) run.endings.push(end.id);`:

```js
    run.last = end.id;
```

und die Zeile `if (choice === 'next') return this.enter('newstory');` ersetzen durch:

```js
    if (choice === 'next') { this.forcedNext = StoryRules.nextStory(Stories.list(), State.meta.storyRuns, this.story.id); return this.enter('newstory'); }
```

In `Story.enter`, die Zeile mit `const id = forced && …` ersetzen:

```js
      const forcedNext = this.forcedNext; this.forcedNext = null;
      const id = forced && Stories.get(forced) ? forced : (forcedNext || StoryRules.pickStory(Stories.list(), State.meta.storyRuns, Math.random));
      const story = Stories.get(id);
      State.startStory(story);
      if (params.has('prev') && params.has('fresh') && story.requires) State.s.story.prev[story.requires] = params.get('prev');
```

(`State.startStory(story)` steht dort bereits – nur die `prev`-Zeile danach ergänzen.) In `Story` das Feld `forcedNext: null,` neben `allowOnce: null,` anlegen. In `consumeDevParams` die Liste erweitern: `const dev = ['story', 'day', 'job', 'ending', 'fresh', 'prev'];`

In `Stories` (Block `story-engine`) ergänzen:

```js
  next() {
    try { const id = StoryRules.pickStory(this.list(), State.meta.storyRuns, Math.random); const st = this.get(id); return { id, title: st.title }; } catch (e) { return null; }
  },
  locked() {
    return this.list().filter((st) => !StoryRules.requirementMet(st, State.meta.storyRuns)).map((st) => ({ id: st.id, title: st.title, requires: this.get(st.requires) ? this.get(st.requires).title : st.requires }));
  },
```

Titelscreen: in `tpl-title` unter der Zeile mit `id="titleNewStory"` einfügen:

```html
    <p class="title-hint hidden" id="titleStoryLock"></p>
```

CSS (bei den anderen `.title-*`-Regeln, z. B. nach `.title-sub`):

```css
.title-hint { color: var(--dim); font-size: .85rem; margin: 4px 0 0; }
```

In `Title.show`, der `else`-Zweig `tag.textContent = 'Neue Story';` wird:

```js
      } else {
        const nx = typeof Stories !== 'undefined' ? Stories.next() : null;
        tag.textContent = nx ? `Neue Story · ${nx.title}` : 'Neue Story';
      }
      const locked = typeof Stories !== 'undefined' ? Stories.locked() : [];
      const lockEl = qs('#titleStoryLock', root);
      if (locked.length) { lockEl.textContent = locked.map((l) => `🔒 ${l.title} – erst „${l.requires}“ beenden`).join(' · '); lockEl.classList.remove('hidden'); }
```

- [ ] **Step 4: Tests + Browser-Check**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.
Run: `tests/screenshot.sh /tmp/title.png "?fresh"` und Bild ansehen: Tür „Story“ zeigt „Neue Story · Die Schuld“, kein Sperr-Hinweis (es gibt noch keine Story mit `requires`).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): prevEnding-Bedingung, Nächste Story in Reihenfolge, Titel zeigt nächste/gesperrte Story, ?prev=

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Spiel-Stats (`wins`, `streak`, `bestStreak`, `biggestWin`, `beers`, `brownies`, `royalVisits`)

**Files:**
- Modify: Block `story-rules` (`freshStoryPart`, neu `recordSpin`), Block `story-engine` (Bus-Listener am Ende), Block `rooms` (`Actions.beer`, `Actions.brownie`)
- Test: Block `selftest`

**Interfaces:**
- Produces:
  - `s.story.stats = { earned, gambled, jobs, wins, streak, bestStreak, biggestWin, beers, brownies, royalVisits }`
  - `StoryRules.recordSpin(stats, delta)` – mutiert `stats`
  - Bedingungen wie `{ stat: 'biggestWin', gte: 5000 }` funktionieren damit ohne weitere Änderung

- [ ] **Step 1: Failing Test**

```js
T.test('StoryRules.recordSpin: Serie, Siege, größter Gewinn', () => {
  const st = StoryRules.freshStoryPart(probeStory()).stats;
  T.eq([st.wins, st.streak, st.bestStreak, st.biggestWin, st.beers, st.brownies, st.royalVisits], [0, 0, 0, 0, 0, 0, 0]);
  StoryRules.recordSpin(st, 100); StoryRules.recordSpin(st, 700);
  T.eq([st.wins, st.streak, st.bestStreak, st.biggestWin], [2, 2, 2, 700]);
  StoryRules.recordSpin(st, 0);
  T.eq(st.streak, 2, 'Push ändert die Serie nicht');
  StoryRules.recordSpin(st, -50);
  T.eq([st.wins, st.streak, st.bestStreak], [2, 0, 2]);
  StoryRules.recordSpin(st, 5);
  T.eq([st.streak, st.bestStreak, st.biggestWin], [1, 2, 700]);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL `recordSpin is not a function`.

- [ ] **Step 3: Implementieren**

`freshStoryPart`: `stats: { earned: 0, gambled: 0, jobs: 0, wins: 0, streak: 0, bestStreak: 0, biggestWin: 0, beers: 0, brownies: 0, royalVisits: 0 },`

Neue Funktion in `StoryRules`:

```js
  recordSpin(stats, delta) {
    if (delta > 0) { stats.wins++; stats.streak++; stats.bestStreak = Math.max(stats.bestStreak, stats.streak); stats.biggestWin = Math.max(stats.biggestWin, delta); }
    else if (delta < 0) stats.streak = 0;
  },
```

Block `story-engine`, die Zeile `Bus.on('loss', …)` ersetzen durch:

```js
Bus.on('win', ({ amount }) => { if (State.mode === 'story' && Story.story) { StoryRules.recordSpin(Story.s.stats, amount); State.save(); } });
Bus.on('loss', ({ amount }) => { if (State.mode === 'story' && Story.story) { Story.s.stats.gambled += amount; StoryRules.recordSpin(Story.s.stats, -amount); State.save(); } });
```

Alte Spielstände: `s.story.stats` kann die neuen Schlüssel nicht haben. In `Story.setup()` als erste Zeile:

```js
    if (this.s) this.s.stats = Object.assign({ wins: 0, streak: 0, bestStreak: 0, biggestWin: 0, beers: 0, brownies: 0, royalVisits: 0 }, this.s.stats);
```

`beers`/`brownies` werden in Task 4 zusammen mit den Hooks hochgezählt; `royalVisits` im Casino-Royal-Plan.

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Spiel-Stats wins/streak/bestStreak/biggestWin aus win/loss-Events

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Hooks `sleep`, `buy:beer`, `buy:brownie`, `buy:kidney`, `buy:therapy`, `royal:enter` + `HOOKS`-Validierung

**Files:**
- Modify: Block `story-rules` (`HOOKS`, `validate`), Block `story-engine` (`Story.hook`, `Story.night`), Block `rooms` (`Actions.beer`, `Actions.brownie`, `Actions.kidney`, `Life.therapy`)
- Test: Block `selftest`

**Interfaces:**
- Produces:
  - `StoryRules.HOOKS = ['morning', 'night', 'sleep', 'spin:after', 'buy:beer', 'buy:brownie', 'buy:kidney', 'buy:therapy', 'royal:enter']`
  - `Story.hook(at) → Promise` – führt `runEvents(at)` aus, wenn Story-Modus aktiv; sonst no-op. Danach `checkImmediate()` (Task 6; bis dahin nur `runEvents`)
  - `sleep`-Events laufen in `night()` **vor** den `night`-Events
  - `s.story.stats.beers` / `.brownies` zählen Käufe

- [ ] **Step 1: Failing Test**

```js
T.test('StoryRules.validate: unbekannter Hook', () => {
  const st = Object.assign({}, STORY_PROBE, { id: 'x', events: [{ id: 'e', at: 'unbekannt', scene: 'probe.n1' }] });
  T.eq(StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']), ['x: Hook "unbekannt" in Event e']);
  for (const at of StoryRules.HOOKS) {
    const ok = Object.assign({}, STORY_PROBE, { id: 'y', events: [{ id: 'e', at, scene: 'probe.n1' }] });
    T.eq(StoryRules.validate(ok, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']), [], at);
  }
});
T.test('StoryRules.dueEvents: sleep-Hook', () => {
  const st = Object.assign({}, STORY_PROBE, { events: [{ id: 'z', at: 'sleep', when: { var: 'mut', lte: 0 }, scene: 'probe.n1' }] });
  const s = Object.assign(base(), { story: StoryRules.freshStoryPart(st) });
  T.eq(StoryRules.dueEvents(st, s, 'sleep').map((e) => e.id), ['z']);
  T.eq(StoryRules.dueEvents(st, s, 'night'), []);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL (`HOOKS` undefined; validate liefert `[]` statt Fehler).

- [ ] **Step 3: Implementieren**

In `StoryRules`:

```js
  HOOKS: ['morning', 'night', 'sleep', 'spin:after', 'buy:beer', 'buy:brownie', 'buy:kidney', 'buy:therapy', 'royal:enter'],
```

In `validate`, in der Schleife über `story.events`, als erste Zeile im Schleifenkörper:

```js
      if (!StoryRules.HOOKS.includes(e.at)) errs.push(`${story.id}: Hook "${e.at}" in Event ${e.id}`);
```

In `Story` (Block `story-engine`):

```js
  /* Generischer Einstiegspunkt für Käufe/Zimmer: Events des Hooks abarbeiten, dann sofortige Enden prüfen */
  async hook(at) {
    if (State.mode !== 'story' || !this.story || !this.s || this.s.ended) return;
    await this.runEvents(at);
    if (this.checkImmediate) await this.checkImmediate();
  },
```

In `Story.night()` die Zeile `await this.runEvents('night');` ersetzen durch:

```js
      await this.runEvents('sleep');
      await this.runEvents('night');
```

Block `rooms`:

- `Actions.beer`: nach `State.save();` (vor `UI.renderWallet()`) einfügen `if (State.mode === 'story' && State.s.story) State.s.story.stats.beers++;` und die letzte Zeile `await Bus.emit('beer', …)` ergänzen um `await Story.hook('buy:beer');` danach.
- `Actions.brownie`: analog `stats.brownies++` nach dem `State.save()`, das auf `s.brownieCost = …` folgt, und `await Story.hook('buy:brownie');` nach `await Bus.emit('brownie', {});`.
- `Actions.kidney`: nach `await Bus.emit('kidney.sold', {});` → `await Story.hook('buy:kidney');`.
- `Life.therapy`: nach `await Bus.emit('therapy.done', {});` → `if (typeof Story !== 'undefined') await Story.hook('buy:therapy');`.

`Story` ist in Block `rooms` zur Laufzeit definiert (Block `story-engine` wird davor ausgeführt? – **prüfen:** `rooms` steht vor `story-engine` in der Datei, aber die Actions laufen erst nach dem Boot, dann existiert `Story`). Zur Sicherheit überall `if (typeof Story !== 'undefined')` voranstellen.

- [ ] **Step 4: Tests + Browser**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.
Run: `tests/dom-selftest.sh` → grün (prüft, dass Bierkauf im freien Spiel ohne Story nicht bricht – `Story.hook` ist dort no-op).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Hooks sleep/buy:*/royal:enter, HOOKS-Validierung, Bier-/Brownie-Zähler

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Effekte `luckMod`, `jobMod`, `price`, `enable`/`disable`; Story-Felder `prices`, `disabled`; HUD-Label als Funktion

**Files:**
- Modify: Block `rules` (`luck`, `canTherapy` – je eine Zeile), Block `story-rules` (`applyEffect`, `price`, `purchaseAllowed`, `jobMod`, `freshStoryPart`, `validate`), Block `state` (`freshStory`), Block `story-engine` (`hudNotes`), Block `ui` (`renderSide`), Block `rooms` (`Actions.beer/brownie`, `Life.render/therapy`)
- Test: Block `selftest`

**Interfaces:**
- Produces:
  - Effekte: `{ luckMod: -15 }`, `{ jobMod: { spuelerZone: 0.7, taxiBrakeDelay: 150, postTime: 0.75, shiftPay: 0.5 } }`, `{ jobMod: null }`, `{ price: { brownie: 300 } }`, `{ enable: ['therapy'] }`, `{ disable: ['tinder', 'house', 'dealer'] }`
  - Story-Felder: `prices: { brownie: 300, therapy: 5000 }`, `disabled: ['tinder']`, `hud[].label` als String **oder** `(s) => string`
  - `s.story.luckMod` (Zahl), `s.story.jobMod` (Objekt), `s.story.prices` (Objekt), `s.story.enabled` (Objekt `{ therapy: true }`), `s.story.disabled` (Array)
  - `StoryRules.price(s, key) → number` (Story-Preis, sonst `Rules.PRICES[key]`)
  - `StoryRules.purchaseAllowed(s, key) → true | false | null` (`true` = explizit erlaubt, `false` = gesperrt, `null` = Standardregeln)
  - `StoryRules.jobMod(s) → object` (immer ein Objekt)
  - `Rules.luck(s)` addiert `s.story.luckMod`, Ergebnis ≥ 0
  - `Rules.canTherapy(s)`: `ok` auch ohne `isHeartbroken`, wenn `s.story.enabled.therapy`

- [ ] **Step 1: Failing Tests**

```js
T.test('Rules.luck: Story-Modifikator, nie unter 0', () => {
  T.eq(Rules.luck(base({ beers: 3, beerTimer: 2, story: { luckMod: -15 } })), 5);
  T.eq(Rules.luck(base({ beers: 1, beerTimer: 2, story: { luckMod: -15 } })), 0);
  T.eq(Rules.luck(base({ story: { luckMod: 10 } })), 10);
  T.eq(Rules.luck(base({ story: {} })), 0);
});
T.test('Rules.canTherapy: Story kann Therapie freigeben', () => {
  T.eq(Rules.canTherapy(base({ balance: 5000, story: { enabled: { therapy: true } } })), { ok: true });
  T.eq(Rules.canTherapy(base({ balance: 4999, story: { enabled: { therapy: true } } })), { ok: false, reason: 'funds' });
  T.eq(Rules.canTherapy(base({ balance: 5000, story: { enabled: {} } })), { ok: false, reason: 'notNeeded' });
});
T.test('StoryRules: Effekte luckMod/jobMod/price/enable/disable', () => {
  const story = Object.assign({}, STORY_PROBE, { prices: { brownie: 300 }, disabled: ['tinder'] });
  const s = Object.assign(base(), { story: StoryRules.freshStoryPart(story) });
  T.eq(s.story.prices, { brownie: 300 }); T.eq(s.story.disabled, ['tinder']); T.eq(s.story.enabled, {}); T.eq(s.story.luckMod, 0); T.eq(s.story.jobMod, {});
  StoryRules.applyEffect(s, { luckMod: -15 }, story); T.eq(s.story.luckMod, -15);
  StoryRules.applyEffect(s, { luckMod: 0 }, story); T.eq(s.story.luckMod, 0);
  StoryRules.applyEffect(s, { jobMod: { shiftPay: 0.5 } }, story); T.eq(StoryRules.jobMod(s), { shiftPay: 0.5 });
  StoryRules.applyEffect(s, { jobMod: null }, story); T.eq(StoryRules.jobMod(s), {});
  T.eq(StoryRules.jobMod(base()), {}, 'ohne Story leer');
  StoryRules.applyEffect(s, { price: { therapy: 8000 } }, story); T.eq(s.story.prices, { brownie: 300, therapy: 8000 });
  T.eq(StoryRules.price(s, 'therapy'), 8000); T.eq(StoryRules.price(s, 'beer'), Rules.PRICES.beer); T.eq(StoryRules.price(base(), 'brownie'), Rules.PRICES.brownie);
  StoryRules.applyEffect(s, { enable: ['therapy'] }, story); T.eq(s.story.enabled, { therapy: true });
  T.eq(StoryRules.purchaseAllowed(s, 'therapy'), true); T.eq(StoryRules.purchaseAllowed(s, 'tinder'), false); T.eq(StoryRules.purchaseAllowed(s, 'house'), null); T.eq(StoryRules.purchaseAllowed(base(), 'tinder'), null);
  StoryRules.applyEffect(s, { disable: ['beer'] }, story); T.eq(StoryRules.purchaseAllowed(s, 'beer'), false);
  StoryRules.applyEffect(s, { enable: ['beer'] }, story); T.eq(StoryRules.purchaseAllowed(s, 'beer'), true, 'enable hebt disable auf');
});
T.test('StoryRules.validate: prices nur bekannte Schlüssel', () => {
  const st = Object.assign({}, STORY_PROBE, { id: 'x', prices: { kaviar: 1 } });
  T.eq(StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']), ['x: Preis "kaviar" unbekannt']);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAILs (luck ignoriert story, Effekte werfen `Ungültiger Effekt`, `price` undefined …).

- [ ] **Step 3: Implementieren**

Block `rules`:

```js
  luck(s) {
    let l = 0;
    if (s.beerTimer > 0) l += Rules.BEER_LUCK[Math.min(s.beers, 3)];
    if (s.brownieTimer > 0) l += Rules.BROWNIE_LUCK;
    l += Rules.gear(s).luck;
    if (s.story && s.story.luckMod) l += s.story.luckMod; // Story-Modifikator (z. B. Zitter-Tag), kürzt höchstens auf 0
    return Math.max(0, l);
  },
```

`canTherapy`: erste Zeile ersetzen durch

```js
    if (!s.isHeartbroken && !(s.story && s.story.enabled && s.story.enabled.therapy)) return { ok: false, reason: 'notNeeded' };
```

Block `story-rules`, `freshStoryPart` ergänzen:

```js
      prices: Object.assign({}, story.prices || {}), enabled: {}, disabled: [...(story.disabled || [])], luckMod: 0, jobMod: {},
```

`applyEffect`, vor `if ('unlock' in eff)` (bzw. vor dem abschließenden `throw`) einfügen:

```js
    if ('luckMod' in eff) { st.luckMod = eff.luckMod || 0; return {}; }
    if ('jobMod' in eff) { st.jobMod = eff.jobMod ? Object.assign({}, eff.jobMod) : {}; return {}; }
    if ('price' in eff) { st.prices = Object.assign(st.prices || {}, eff.price); return {}; }
    if ('enable' in eff) { st.enabled = st.enabled || {}; st.disabled = (st.disabled || []).filter((k) => !eff.enable.includes(k)); for (const k of eff.enable) st.enabled[k] = true; return {}; }
    if ('disable' in eff) { st.disabled = Array.from(new Set([...(st.disabled || []), ...eff.disable])); st.enabled = st.enabled || {}; for (const k of eff.disable) delete st.enabled[k]; return {}; }
```

Neue Helfer in `StoryRules`:

```js
  price(s, key) {
    const p = s.story && s.story.prices && s.story.prices[key];
    return p != null ? p : Rules.PRICES[key];
  },
  purchaseAllowed(s, key) {
    if (!s.story) return null;
    if ((s.story.disabled || []).includes(key)) return false;
    if (s.story.enabled && s.story.enabled[key]) return true;
    return null;
  },
  jobMod(s) { return (s.story && s.story.jobMod) || {}; },
```

`validate`, vor `return errs;`:

```js
    for (const k of Object.keys(story.prices || {})) if (!(k in Rules.PRICES)) errs.push(`${story.id}: Preis "${k}" unbekannt`);
```

Block `state`, `freshStory(story)`: nach `s.story = …` → `if (s.story.prices.brownie != null) s.brownieCost = s.story.prices.brownie;`

Block `story-engine`, `hudNotes()`: `const label = typeof hd.label === 'function' ? hd.label(State.s) : hd.label;` und im `h('span', …)` `label` statt `hd.label` verwenden.

Block `rooms`:
- `Actions.beer`: `Game.applyDelta(-StoryRules.price(s, 'beer'), { quiet: true });` und in der Toast-/Fehlermeldung `UI.fmt(StoryRules.price(s, 'beer'))` statt „50 €“. Vor dem `canBeer`-Check: `if (StoryRules.purchaseAllowed(s, 'beer') === false) { UI.toast({ icon: '🍺', title: 'Kein Bier mehr', text: 'Der Wirt schenkt dir nichts mehr ein.', tone: 'loss' }); return; }`
- `Actions.brownie`: gleicher `purchaseAllowed`-Check mit Text „Nichts mehr da.“; die Zeile `s.brownieCost = Rules.PRICES.brownieNext;` ersetzen durch `s.brownieCost = s.story && s.story.prices && s.story.prices.brownie != null ? s.story.prices.brownie : Rules.PRICES.brownieNext;`
- `Life.therapy`: `Game.applyDelta(-StoryRules.price(s, 'therapy'), …)`.
- `Life.render`: Karten `lifeHouse`, `lifeLove` (Tinder-Zweig), `lifeDealer` nur befüllen, wenn `StoryRules.purchaseAllowed(s, 'house'|'tinder'|'dealer') !== false`; sonst `this.card(el, { pic: '🚫', empty: true, title: 'Nicht heute', text: 'Gibt es in dieser Geschichte nicht.' })`. Therapie-Karte: wenn `StoryRules.purchaseAllowed(s, 'therapy') === true && !s.isHeartbroken`: `{ pic: '🩺', title: 'Therapie', text: (Story.story.copy && Story.story.copy.therapy) || 'Der Doc hat ein Programm. Kein Bier mehr – und kein Glück daraus.', action: () => Life.therapy(), label: \`Therapie · ${UI.fmt(StoryRules.price(s, 'therapy'))}\`, cls: 'pink', check: Rules.canTherapy(s) }`; im Liebeskummer-Zweig das Label `\`Therapie & Anwalt · ${UI.fmt(StoryRules.price(s, 'therapy'))}\``.

Block `ui`, `renderSide`: Bar-Buttons

```js
      btn(`🍺 Bier${s.beers > 0 ? ` (${s.beers}/3)` : ''}`, this.fmt(StoryRules.price(s, 'beer')), 'beer', !Rules.canBeer(s).ok || StoryRules.purchaseAllowed(s, 'beer') === false),
      btn('🍪 Brownie', this.fmt(s.brownieCost), 'brownie', !Rules.canBrownie(s).ok || StoryRules.purchaseAllowed(s, 'brownie') === false),
```

(`StoryRules` ist im Browser vor `ui` nicht definiert? – **prüfen:** Block `story-rules` steht nach `ui`. `renderSide` läuft aber erst nach dem Boot, dann existiert `StoryRules`. Falls der DOM-Selbsttest meckert, `typeof StoryRules !== 'undefined' ? … : Rules.PRICES.beer` verwenden.)

- [ ] **Step 4: Tests + Browser**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.
Run: `tests/dom-selftest.sh` → grün. Run: `tests/screenshot.sh /tmp/life.png "?screen=life"` – Life-Screen sieht aus wie vorher (kein `purchaseAllowed`-Effekt im freien Spiel).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Effekte luckMod/jobMod/price/enable/disable, Story-Preise, HUD-Label als Funktion

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Sofortige Enden (`immediate: true`)

**Files:**
- Modify: Block `story-rules` (`ending`, `validate`), Block `story-engine` (`Story.checkImmediate`, `applyEffects`, `finish`)
- Test: Block `selftest`

**Interfaces:**
- Consumes: `Story.hook` (Task 4) ruft `checkImmediate` bereits auf
- Produces:
  - `StoryRules.ending(story, s, { immediateOnly = false } = {})`
  - `Story.checkImmediate() → Promise<boolean>` (true, wenn ein Ende gespielt wurde)
  - `Story.finishing` (Reentrancy-Schutz)

- [ ] **Step 1: Failing Test**

```js
T.test('StoryRules.ending: immediate-Enden', () => {
  const st = Object.assign({}, STORY_PROBE, { endings: [
    { id: 'tot', title: 'Tot', priority: 60, immediate: true, when: { var: 'mut', gte: 3 }, scene: 'probe.aus' },
    { id: 'mutig', title: 'Mutig', priority: 1, when: { var: 'mut', gte: 2 }, scene: 'probe.mutig' },
    { id: 'aus', title: 'Aus', priority: 0, scene: 'probe.aus', fallback: true },
  ] });
  const s = Object.assign(base(), { story: StoryRules.freshStoryPart(st) });
  s.story.vars.mut = 2;
  T.eq(StoryRules.ending(st, s, { immediateOnly: true }), null, 'normales Ende nicht sofort');
  T.eq(StoryRules.ending(st, s).id, 'mutig');
  s.story.vars.mut = 3;
  T.eq(StoryRules.ending(st, s, { immediateOnly: true }).id, 'tot');
  T.eq(StoryRules.ending(st, s).id, 'tot', 'nachts greift es ebenfalls');
});
T.test('StoryRules.validate: immediate nicht mit fallback', () => {
  const st = Object.assign({}, STORY_PROBE, { id: 'x', endings: [{ id: 'aus', title: 'Aus', priority: 0, scene: 'probe.aus', fallback: true, immediate: true }] });
  T.eq(StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']), ['x: Ende aus – immediate und fallback schließen sich aus']);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL (`immediateOnly` ignoriert → liefert `mutig` statt `null`).

- [ ] **Step 3: Implementieren**

```js
  ending(story, s, { immediateOnly = false } = {}) {
    const cands = story.endings.filter((e) => !e.fallback && (!immediateOnly || e.immediate));
    const sorted = cands.slice().sort((a, b) => b.priority - a.priority);
    for (const e of sorted) if (StoryRules.check(e.when, s)) return e;
    if (!immediateOnly && s.story.day > story.days) return story.endings.find((e) => e.fallback) || null;
    return null;
  },
```

`validate`, in der Schleife über `story.endings`: `if (e.immediate && e.fallback) errs.push(\`${story.id}: Ende ${e.id} – immediate und fallback schließen sich aus\`);`

`Story` (Block `story-engine`): Feld `finishing: false,` anlegen, dann

```js
  async checkImmediate() {
    if (this.finishing || !this.story || !this.s || this.s.ended) return false;
    const end = StoryRules.ending(this.story, State.s, { immediateOnly: true });
    if (!end) return false;
    this.finishing = true;
    try { await this.finish(end); } finally { this.finishing = false; }
    return true;
  },
```

In `applyEffects(list)` als letzte Zeile: `await this.checkImmediate();`. In `night()`: `if (end) return this.finish(end);` bleibt – `ending()` ohne Option enthält `immediate`-Enden.

Wichtig in `finish`: `finish` ruft am Ende `this.enter('newstory')` oder `Title.show()`. Wenn `checkImmediate` aus `applyEffects` mitten in `runEvents` aufgerufen wird, laufen die restlichen Events nach `finish` weiter. Deshalb in `runEvents` nach jedem Event: `if (this.s.ended) return;` – und in `night()` nach `await this.runEvents('sleep')` sowie nach `runEvents('night')`: `if (this.s.ended) return;`.

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen. Run: `tests/dom-selftest.sh` → grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): sofortige Enden (immediate) nach Effekten und Käufen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: `jobMod` in Spüler, Taxi, Postbote und Schichtlohn

**Files:**
- Modify: Block `rules` (`postmanTier` – Achtung Parallelarbeit: nur diese Funktion), Block `job-spueler` (`next()`-Zone), Block `job-taxi` (`brake()`), Block `jobs` (`runShift`)
- Test: Block `selftest`

**Interfaces:**
- Consumes: `StoryRules.jobMod(s)` (Task 5)
- Produces: Verhalten laut Spec 4 – Zone × `spuelerZone`, Bremse verzögert um `taxiBrakeDelay` ms, Post-Zeit × `postTime`, Schichtlohn × `shiftPay`
- Neue reine Funktion `StoryRules.shiftPay(base, bonus, jobMod) → number`

- [ ] **Step 1: Failing Tests**

```js
T.test('postmanTier: Story-Zeitfaktor', () => {
  const s = base({ story: { jobMod: { postTime: 0.5 } } });
  T.eq(Rules.postmanTier(0, s).t, 2.5);
  T.eq(Rules.postmanTier(0, base({ story: { jobMod: {} } })).t, 5);
  T.eq(Rules.postmanTier(0, base({ shoes: 'basic', story: { jobMod: { postTime: 0.5 } } })).t, 3, 'Schuh-Bonus vor dem Faktor');
});
T.test('StoryRules.shiftPay: Faktor auf Lohn + Bonus, gerundet', () => {
  T.eq(StoryRules.shiftPay(100, 30, {}), 130);
  T.eq(StoryRules.shiftPay(100, 30, { shiftPay: 0.5 }), 65);
  T.eq(StoryRules.shiftPay(150, 0, { shiftPay: 0.5 }), 75);
  T.eq(StoryRules.shiftPay(105, 0, { shiftPay: 0.5 }), 53);
});
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `node tests/run-selftest.mjs` → FAIL.

- [ ] **Step 3: Implementieren**

`Rules.postmanTier`:

```js
  postmanTier(streak, s) {
    const g = s ? Rules.gear(s) : { postTime: 0, postPay: 0 };
    const jm = s && s.story && s.story.jobMod ? s.story.jobMod : {};
    const t = streak < 2 ? { t: 5, r: 5 } : streak < 6 ? { t: 3, r: 10 } : streak < 11 ? { t: 1.5, r: 25 } : { t: 0.5, r: 50 };
    return { t: (t.t + g.postTime) * (jm.postTime != null ? jm.postTime : 1), r: t.r + g.postPay };
  },
```

`StoryRules.shiftPay(base, bonus, jobMod) { return Math.round((base + bonus) * (jobMod.shiftPay != null ? jobMod.shiftPay : 1)); }`

Block `jobs`, `runShift`: die zwei Zeilen `const bonus = …; Game.applyDelta(job.base + bonus, …)` werden

```js
    const bonus = job.id === 'tuersteher' ? StoryRules.tuerBonus(State.s.strength) : 0;
    const jm = StoryRules.jobMod(State.s);
    const pay = StoryRules.shiftPay(job.base, bonus, jm);
    Game.applyDelta(pay, { quiet: true });
    const cut = pay < job.base + bonus ? ' Du hast die Gläser fallen lassen – halber Lohn.' : '';
    UI.toast({ icon: job.icon, title: `${job.name}: Schicht`, text: (bonus > 0 ? `+${UI.fmt(job.base)} Lohn, +${UI.fmt(bonus)} weil keiner mit dir diskutiert.` : `+${UI.fmt(job.base)} Lohn.`) + cut, tone: 'win' });
```

Block `job-spueler`, in `next()`: `const band = (1 + Rules.gear(State.s).spuelerBand) * (StoryRules.jobMod(State.s).spuelerZone != null ? StoryRules.jobMod(State.s).spuelerZone : 1);`

Block `job-taxi`, `brake()`:

```js
  brake() {
    if (!this.running || !this.root) return;
    const delay = StoryRules.jobMod(State.s).taxiBrakeDelay || 0;
    const apply = () => { if (!this.running || !this.root) return; this.braking = true; this.brakeUntil = performance.now() + 600; qs('#taxiCar', this.root).classList.add('braking'); const f = qs('#brakeFlash', this.root); f.classList.remove('on'); void f.offsetWidth; f.classList.add('on'); };
    if (delay > 0) setTimeout(apply, delay); else apply();
  },
```

- [ ] **Step 4: Tests + manueller Check**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen. Run: `tests/dom-selftest.sh` → grün.
Manuell: `?fresh&story=probe&job=spueler` – Spüler läuft wie bisher (jobMod leer).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(jobs): Story-Job-Modifikator in Spüler, Taxi, Post und Schichtlohn

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: README, Doku, Abschluss-Verifikation

**Files:**
- Modify: `README.md` (Dev-Parameter-Tabelle, Story-Modus-Abschnitt)
- Modify: `docs/superpowers/specs/2026-09-16-story-mode-design.md` (Abschnitt 6 Bedingungen, Abschnitt 7 Datenformat – neue Felder kurz nachtragen)

- [ ] **Step 1: README**

In der Dev-Parameter-Tabelle nach der `?ending=`-Zeile:

```
| `?prev=doc` | zusammen mit `?fresh&story=…`: setzt das „vorige Ende" der vorausgesetzten Story (für Fortsetzungen) |
```

Im Abschnitt „Story-Modus“, Unterpunkt „Enden“, einen Satz ergänzen: „Stories können eine Voraussetzung haben (`requires`); der Titelscreen zeigt dann an, welche Story als Nächstes startet und welche noch gesperrt ist.“

- [ ] **Step 2: Story-Mode-Spec nachziehen**

Abschnitt 6: `{ prevEnding: { story: 'schuld', id: 'doc' } }` ergänzen. Abschnitt 7: Felder `requires`, `prices`, `disabled`, `hud[].label` (String oder Funktion), Event-Hooks `sleep`, `buy:beer|brownie|kidney|therapy`, `royal:enter`, Effekte `luckMod`, `jobMod`, `price`, `enable`, `disable`, Enden-Flag `immediate` – je eine Zeile.

- [ ] **Step 3: Gesamtverifikation**

Run: `node tests/run-selftest.mjs` → 0 fehlgeschlagen.
Run: `tests/dom-selftest.sh` → grün.
Run: `python3 tests/playtest-story.py` → bestehender Story-1-Durchlauf grün (Regression: Story 1 verhält sich unverändert).

- [ ] **Step 4: Commit**

```bash
git add README.md docs/superpowers/specs/2026-09-16-story-mode-design.md
git commit -m "docs: Story-Engine 2 – requires/prevEnding, neue Hooks und Effekte, ?prev=

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec-Abdeckung (Abschnitt 8 der Spec):**
- `requires`, `pickStory`-Filter, `nextStory` → Task 1/2 ✔
- `prevEnding`, `storyRuns[].last` → Task 2 ✔
- Stats `wins, streak, bestStreak, biggestWin, beers, brownies, royalVisits` → Task 3/4 (`royalVisits` wird vom Casino-Plan hochgezählt, Feld existiert) ✔
- Hooks `sleep`, `buy:*`, `royal:enter` → Task 4 (`royal:enter` wird vom Casino-Plan aufgerufen, Validierung kennt ihn) ✔
- Effekte `luckMod`, `jobMod`, `price`, `disable`/`enable`; Story-Felder `prices`, `disabled`; HUD-Icon-Funktion (umgesetzt als `label`-Funktion, deckt den Zweck ab) → Task 5 ✔
- `immediate`-Enden → Task 6 ✔
- Rooms `royal` → bewusst im Casino-Plan (dort wird `StoryRules.ROOMS` erweitert).
- Validierung `requires`, `prices`, `immediate`/`fallback`, Hooks → Tasks 1, 4, 5, 6 ✔
- Zitter-Tag-Mechanik (Spec 4): Engine-Seite (`jobMod`-Konsum) → Task 7 ✔; die Story-Events selbst gehören in den Story-Plan.

**Typ-Konsistenz:** `StoryRules.price(s, key)`, `purchaseAllowed(s, key)`, `jobMod(s)`, `shiftPay(base, bonus, jobMod)`, `recordSpin(stats, delta)`, `ending(story, s, { immediateOnly })`, `freshStoryPart(story, storyRuns)`, `validate(story, sceneIds, jobIds, storyIds)` – überall gleich verwendet.

**Bekannte Abweichung:** `luckMod` klemmt auf ≥ 0 (siehe Global Constraints).
