# Story-Engine 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die generischen Engine-Erweiterungen, die Story 3 „Die Wäsche" braucht: Umsatzzähler, kaputte Türen mit Reparatur, Gear-Slot Waffe, Story-Funktionen (`call`), neue Hooks, `prevEndings`, Job-Overrides und -Varianten, neue Figuren.

**Architecture:** Alles bleibt im Muster von Story 2: reine Regeln in `StoryRules` (DOM-frei, Node-Selftest), DOM-Seite in `Story`/`Jobs`/`UI`. Keine Story-3-Sonderfälle in der Engine – jede Erweiterung ist ein generisches Feld/Effekt/Hook, das eine Story-Definition benutzt. Zahlen kommen in diesem Plan nicht vor; sie gehören in Plan 2–4.

**Tech Stack:** Vanilla JS in einer HTML-Datei (`keller37.html`, `<script id="…">`-Blöcke), Node-Selftest `node tests/run-selftest.mjs`, DOM-Selftest `tests/dom-selftest.sh`.

**Spec:** `docs/superpowers/specs/2026-09-18-story-stash-design.md` (Abschnitt 10 „Engine-Änderungen", Abschnitt 2 „Voraussetzung", Abschnitt 9 „Jobs").

## Global Constraints

- Eine Datei: alles in `keller37.html`; neue Logik in bestehende Blöcke oder neue `<script id="…">`-Blöcke. Keine externen Dateien außer Tests/Docs.
- DOM-freie Blöcke (`rules`, `gear-rules`, `perk-rules`, `util`, `state`, `bus`, `story-rules`, `royal-rules`, `story-*`) dürfen kein `document`, `UI`, `qs` benutzen – sie laufen unter Node.
- Jede Änderung an `StoryRules` bekommt einen Test im Block `selftest` (Muster: `T.test('…', () => { … })`, Helfer `seq(...)`, `base(...)`).
- Nach jeder Task: `node tests/run-selftest.mjs` grün (aktuell 209 Tests) und `bash tests/dom-selftest.sh` grün (aktuell 215) – Zahlen steigen mit neuen Tests.
- Bestehende Stories (`schuld`, `kater`) dürfen sich nicht verändern: `python3 tests/playtest-story.py` bleibt 140/140 (allein laufen lassen, Taxi-Timeout ist lastabhängig).
- Commits einzeln pro Task, Trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Sprache in Spiel und Kommentaren: Deutsch; Code-Bezeichner wie im Bestand (englisch/deutsch gemischt, z. B. `jobsDone`, `umsatz`).

---

## Dateistruktur

Alles in `keller37.html`:

| Block | Änderung |
|---|---|
| `state` | `State.fresh()` bekommt `weapon: 0` |
| `core` | `Game.settle` emittiert `stake` |
| `story-rules` | `recordStake`, `repair`, `SET_KEYS` + `weapon`, Effekte `call`/`break`/`repair`/`show`, `HOOKS` + `fight:after`/`job:after`, `requirementMet` mit `prevEndings`, `lockReason`, `validate`-Erweiterungen, `freshStoryPart` mit `broken` |
| `story-engine` | `Bus.on('stake')`, `isLocked`/`lockReason`/`decorateHub` für `broken`, `Story.repair`, `applyEffects` für `show`, `Stories.locked()` mit `text`, `hudNotes` mit `max` als Funktion, `Story.DOORS` + `hinterzimmer` |
| `title` | Sperrtext aus `Stories.locked()` |
| `jobs` | `Jobs.def(id)` mit `jobOverrides`, `variant` an den Screen, `Jobs.collect(id, flags)` + Hook `job:after` |
| `cutscene-engine` | Figuren `anabi`, `stumme`, `kessler`, `brandt`, `kowalski`; Hintergrund `bahnhof` |
| CSS | `.cs-bg.bahnhof`, `.door.broken`, `.door .repair` |
| `selftest` | Tests je Task |
| `tests/run-selftest.mjs` | keine Änderung in diesem Plan (neue Blöcke kommen in Plan 2–4) |

---

### Task 1: Umsatzzähler – `stake`-Event und `StoryRules.recordStake`

**Files:**
- Modify: `keller37.html` Block `core` (`Game.settle`, ~Zeile 2387)
- Modify: `keller37.html` Block `story-rules` (neue Methode nach `recordSpin`, ~Zeile 5011)
- Modify: `keller37.html` Block `story-engine` (neben `Bus.on('win', …)`, ~Zeile 5638)
- Test: `keller37.html` Block `selftest` (nach dem Test `StoryRules.recordSpin: …`, ~Zeile 7505)

**Interfaces:**
- Produces: `Bus.emit('stake', { bet, game })` in `Game.settle` vor `win`/`loss`; `StoryRules.recordStake(st, bet, game, story)` – `st` = `s.story`; erhöht `st.vars.umsatz` und `st.vars.umsatzTotal` um `bet` und für jede Gruppe in `story.turnoverGroups` (`{ [varName]: [gameIds] }`) `st.vars[varName]`, wenn `game` in der Liste steht. `bet ≤ 0` ändert nichts.

- [ ] **Step 1: Failing Test schreiben**

Im Block `selftest` direkt nach dem Test `'StoryRules.recordSpin: Serie, Siege, größter Gewinn'` einfügen:

```js
T.test('StoryRules.recordStake: Umsatz gesamt, Gruppen je Spiel, bet ≤ 0 zählt nicht', () => {
  const story = { turnoverGroups: { umsatzRoyal: ['megaslots', 'craps', 'wheel'], umsatzHinterzimmer: ['baccarat'] } };
  const st = { vars: {} };
  StoryRules.recordStake(st, 500, 'roulette', story);
  T.eq(st.vars, { umsatz: 500, umsatzTotal: 500 });
  StoryRules.recordStake(st, 1000, 'craps', story);
  T.eq(st.vars, { umsatz: 1500, umsatzTotal: 1500, umsatzRoyal: 1000 });
  StoryRules.recordStake(st, 10000, 'baccarat', story);
  T.eq(st.vars.umsatzHinterzimmer, 10000); T.eq(st.vars.umsatz, 11500);
  StoryRules.recordStake(st, 0, 'slots', story); StoryRules.recordStake(st, -5, 'slots', story);
  T.eq(st.vars.umsatz, 11500, 'Freispiel (0) und Unsinn (<0) zählen nicht');
  const plain = { vars: { umsatz: 7 } };
  StoryRules.recordStake(plain, 3, 'slots', {});
  T.eq(plain.vars, { umsatz: 10, umsatzTotal: 3 }, 'ohne turnoverGroups nur umsatz/umsatzTotal');
});
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: `FAIL StoryRules.recordStake: … StoryRules.recordStake is not a function`

- [ ] **Step 3: `recordStake` implementieren**

In `StoryRules` nach `recordSpin(stats, delta) { … },` einfügen:

```js
  /* Umsatz (Summe der Einsätze) – jede Story zählt umsatz/umsatzTotal, optional Gruppen je Spiel-ID (story.turnoverGroups) */
  recordStake(st, bet, game, story = {}) {
    if (!(bet > 0)) return;
    st.vars.umsatz = (st.vars.umsatz || 0) + bet;
    st.vars.umsatzTotal = (st.vars.umsatzTotal || 0) + bet;
    for (const [name, games] of Object.entries(story.turnoverGroups || {})) if (games.includes(game)) st.vars[name] = (st.vars[name] || 0) + bet;
  },
```

- [ ] **Step 4: `stake`-Event in `Game.settle`**

In `Game.settle` die Zeile `this.applyDelta(delta + bet, { from, net: delta });` so ergänzen:

```js
      this.applyDelta(delta + bet, { from, net: delta });
      if (bet > 0) await Bus.emit('stake', { bet, game }); // Umsatz – jeder Einsatz, gewonnen oder verloren (Freispiele: bet 0)
```

- [ ] **Step 5: Story hört zu**

Im Block `story-engine` nach `Bus.on('loss', …);` einfügen:

```js
Bus.on('stake', ({ bet, game }) => { if (State.mode === 'story' && Story.story && Story.s && !Story.s.ended) { StoryRules.recordStake(Story.s, bet, game, Story.story); State.save(); } });
```

- [ ] **Step 6: Tests laufen lassen**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Expected: alle bestanden (Node 210).

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Umsatzzähler – stake-Event in Game.settle, StoryRules.recordStake mit turnoverGroups"
```

---

### Task 2: Kaputte Türen – `broken`, `repair`, Effekte `break`/`repair`, Lobby-Knopf

**Files:**
- Modify: `keller37.html` Block `story-rules` (`applyEffect`, `freshStoryPart`, neue `repair`)
- Modify: `keller37.html` Block `story-engine` (`isLocked`, `lockReason`, `decorateHub`, neue `Story.repair`)
- Modify: `keller37.html` CSS (bei `.door.locked`, ~Zeile 760–790 – Suche nach `.door.locked`)
- Test: Block `selftest`

**Interfaces:**
- Produces: `s.story.broken = { [door]: price }` (in `freshStoryPart` als `{}`); Effekt `{ break: 'slots', price: 4000 }` setzt `broken.slots = 4000`; Effekt `{ repair: 'slots' }` löscht den Eintrag ohne Geld; `StoryRules.repair(s, door)` → `{ ok: true, price }` (zieht `price` von `s.balance` ab, löscht Eintrag, `s.story.vars.repariert_<door>` +1) oder `{ ok: false, reason: 'intact' | 'funds', price }`. `Story.repair(door)` (DOM) ruft das und rendert die Lobby neu. `Story.isLocked(door)` ist wahr für kaputte Türen, `lockReason` = `'Zertrümmert'`.

- [ ] **Step 1: Failing Tests**

Nach dem `recordStake`-Test einfügen:

```js
T.test('StoryRules: broken – Effekt break/repair, repair() zieht Geld ab, zählt, verweigert bei zu wenig Geld', () => {
  const s = base({ balance: 5000, story: StoryRules.freshStoryPart(STORY_PROBE) });
  T.eq(s.story.broken, {});
  StoryRules.applyEffect(s, { break: 'slots', price: 4000 }, STORY_PROBE);
  T.eq(s.story.broken, { slots: 4000 });
  T.eq(StoryRules.repair(s, 'roulette'), { ok: false, reason: 'intact', price: 0 });
  s.balance = 3999;
  T.eq(StoryRules.repair(s, 'slots'), { ok: false, reason: 'funds', price: 4000 });
  s.balance = 4000;
  T.eq(StoryRules.repair(s, 'slots'), { ok: true, price: 4000 });
  T.eq([s.balance, s.story.broken, s.story.vars.repariert_slots], [0, {}, 1]);
  StoryRules.applyEffect(s, { break: 'horses', price: 3000 }, STORY_PROBE);
  StoryRules.applyEffect(s, { repair: 'horses' }, STORY_PROBE);
  T.eq(s.story.broken, {}, 'repair-Effekt ohne Geld (Dev/Story)');
  T.eq(s.story.vars.repariert_horses, undefined, 'Effekt zählt nicht als bezahlte Reparatur');
});
T.test('StoryRules.validate: break braucht price', () => {
  const st = Object.assign({}, STORY_PROBE, { events: [{ id: 'x', at: 'night', effects: [{ break: 'slots' }] }] });
  T.ok(StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']).some((e) => e.includes('break')));
});
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: FAIL (`broken` undefined / `repair is not a function`).

- [ ] **Step 3: `StoryRules` erweitern**

In `applyEffect` vor `if ('achievement' in eff)` einfügen:

```js
    if ('break' in eff) { st.broken = st.broken || {}; st.broken[eff.break] = eff.price; return {}; }
    if ('repair' in eff) { if (st.broken) delete st.broken[eff.repair]; return {}; }
```

In `freshStoryPart` im zurückgegebenen Objekt hinter `luckMod: 0, jobMod: {},` ergänzen: `broken: {},`.

Neue Methode nach `recordStake`:

```js
  /* Kaputte Tür bezahlen: Preis aus broken[door], Zähler repariert_<door> für Trophäen */
  repair(s, door) {
    const st = s.story;
    const price = (st.broken || {})[door];
    if (price == null) return { ok: false, reason: 'intact', price: 0 };
    if (s.balance < price) return { ok: false, reason: 'funds', price };
    s.balance -= price;
    delete st.broken[door];
    st.vars[`repariert_${door}`] = (st.vars[`repariert_${door}`] || 0) + 1;
    return { ok: true, price };
  },
```

In `validate` in der Schleife über `story.events` (die Zeile `scene(e.scene, e.id); for (const eff of e.effects || []) { … }`) ergänzen:

```js
      for (const eff of e.effects || []) if ('break' in eff && !(eff.price > 0)) errs.push(`${story.id}: break "${eff.break}" ohne price (${e.id})`);
```

- [ ] **Step 4: `Story` (DOM) – Sperre, Grund, Knopf**

In `Story.isLocked` nach `if (screen === this.allowOnce) { … }` einfügen:

```js
    if (this.s.broken && this.s.broken[screen] != null) return true;
```

In `Story.lockReason` als erste Zeile:

```js
    if (this.s.broken && this.s.broken[screen] != null) return 'Zertrümmert';
```

`decorateHub` ersetzen durch:

```js
  decorateHub(root) {
    qsa('.door', root).forEach((d) => {
      const id = d.dataset.screen;
      const price = this.s.broken ? this.s.broken[id] : null;
      if (price != null) {
        d.classList.add('locked', 'broken');
        qs('.chalk-tag', d).textContent = 'Zertrümmert';
        const can = State.s.balance >= price;
        const b = h('button', { class: 'btn sm repair' + (can ? '' : ' ghost'), disabled: can ? null : '', title: can ? 'Reparieren' : 'Zu wenig Geld' }, `🔧 ${UI.fmt(price)}`);
        b.addEventListener('click', (e) => { e.stopPropagation(); SFX.play('click'); Story.repair(id); });
        d.append(b);
        return;
      }
      if (!this.isLocked(id)) return;
      d.classList.add('locked');
      d.append(h('div', { class: 'boards' }, h('span'), h('span')));
      qs('.chalk-tag', d).textContent = this.lockReason(id);
    });
  },
  /* 🔧 in der Lobby: bezahlen, Eintrag löschen, Lobby neu zeichnen */
  async repair(door) {
    if (Cutscene.active || Game.inFlight > 0 || UI.busy) return;
    const r = StoryRules.repair(State.s, door);
    if (!r.ok) { UI.toast({ icon: '🔧', title: r.reason === 'funds' ? `Reparatur kostet ${UI.fmt(r.price)}` : 'Nichts kaputt', text: r.reason === 'funds' ? 'Zu wenig Geld.' : '', tone: 'loss' }); SFX.play('lose'); return; }
    State.save();
    UI.setBalance(State.s.balance); UI.renderWallet(); UI.renderSide();
    SFX.play('stamp');
    UI.toast({ icon: '🔧', title: 'Repariert', text: `−${UI.fmt(r.price)}. Läuft wieder.`, tone: 'info' });
    await Bus.emit('story:repair', { door, price: r.price });
    if (UI.current && UI.current.id === 'hub') await UI.show('hub');
  },
```

- [ ] **Step 5: CSS**

Direkt nach der bestehenden Regel `.door.locked .boards span …` (Suche `.boards`) einfügen:

```css
.door.broken { filter: saturate(.3); }
.door.broken .glyph { transform: rotate(-12deg) translateY(6px); opacity: .55; }
.door .repair { position: absolute; left: 50%; bottom: 14px; transform: translateX(-50%); z-index: 3; white-space: nowrap; }
```

- [ ] **Step 6: Tests**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Expected: grün (Node 212).

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(story): kaputte Türen – broken/repair in StoryRules, 🔧-Knopf in der Lobby"
```

---

### Task 3: Gear-Slot `weapon`, Effekt `call` mit `story.fns`, Effekt `show`, Hooks `fight:after`/`job:after`

**Files:**
- Modify: `keller37.html` Block `state` (`fresh()`), `story-rules` (`SET_KEYS`, `HOOKS`, `applyEffect`, `validate`), `story-engine` (`applyEffects`)
- Test: Block `selftest`

**Interfaces:**
- Produces: `State.fresh().weapon === 0`; `StoryRules.SET_KEYS` enthält `'weapon'`; Effekt `{ call: 'name' }` ruft `story.fns[name](s, rng)` auf und gibt dessen Rückgabe (`{}` wenn nichts) als `out` zurück – `out` darf `scene`, `toast`, `achievement`, `force`, `fight`, `show` enthalten; Effekt `{ show: 'stadt' }` → `out.show`; `StoryRules.HOOKS` enthält `'fight:after'` und `'job:after'`; `validate` meldet `call` auf unbekannte Funktion. `Story.applyEffects` behandelt `out.show` (→ `UI.show`) und `out.force === 'shootout'` (→ `this.forceFight(out.fight)` – die Methode kommt in Plan 3; hier nur der Aufruf mit `typeof this.forceFight === 'function'`-Guard).

- [ ] **Step 1: Failing Tests**

```js
T.test('State.fresh: weapon 0; SET_KEYS erlaubt weapon', () => {
  T.eq(State.fresh().weapon, 0);
  const s = base({ story: StoryRules.freshStoryPart(STORY_PROBE) });
  StoryRules.applyEffect(s, { set: { weapon: 2 } }, STORY_PROBE);
  T.eq(s.weapon, 2);
});
T.test('StoryRules: Effekt call ruft story.fns auf, reicht rng durch, gibt out zurück', () => {
  const story = Object.assign({}, STORY_PROBE, { fns: {
    kasse: (s) => { s.balance += 250; return { toast: { title: 'Kasse' } }; },
    wurf: (s, rng) => ({ scene: rng() < 0.5 ? 'p.gut' : 'p.aus' }),
    nix: () => undefined,
  } });
  const s = base({ balance: 0, story: StoryRules.freshStoryPart(story) });
  T.eq(StoryRules.applyEffect(s, { call: 'kasse' }, story), { toast: { title: 'Kasse' } });
  T.eq(s.balance, 250);
  T.eq(StoryRules.applyEffect(s, { call: 'wurf' }, story, seq(0.1)), { scene: 'p.gut' });
  T.eq(StoryRules.applyEffect(s, { call: 'wurf' }, story, seq(0.9)), { scene: 'p.aus' });
  T.eq(StoryRules.applyEffect(s, { call: 'nix' }, story), {});
  T.throws(() => StoryRules.applyEffect(s, { call: 'fehlt' }, story), 'unbekannte Funktion');
  T.eq(StoryRules.applyEffect(s, { show: 'stadt' }, story), { show: 'stadt' });
});
T.test('StoryRules.validate: call auf unbekannte Funktion, neue Hooks erlaubt', () => {
  const st = Object.assign({}, STORY_PROBE, { fns: { a: () => ({}) }, events: [
    { id: 'ok', at: 'fight:after', effects: [{ call: 'a' }] },
    { id: 'ok2', at: 'job:after', effects: [] },
    { id: 'bad', at: 'night', effects: [{ call: 'b' }] },
  ] });
  const errs = StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post']);
  T.eq(errs.length, 1); T.ok(errs[0].includes('call "b"'));
});
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: FAIL (weapon undefined, set-Key nicht erlaubt, call ignoriert).

- [ ] **Step 3: Implementieren**

`State.fresh()`: hinter `car: null, shoes: null, strength: 0, mugCooldown: 0,` → `car: null, shoes: null, weapon: 0, strength: 0, mugCooldown: 0,`.

`StoryRules`:
- `HOOKS: […, 'royal:enter', 'royal:guest', 'fight:after', 'job:after'],`
- `SET_KEYS: ['car', 'shoes', 'weapon', 'hasHouse', 'hasDealer', 'kidneySold'],`
- In `applyEffect` **vor** `if ('chance' in eff)` einfügen:

```js
    if ('call' in eff) {
      const fn = (story.fns || {})[eff.call];
      if (typeof fn !== 'function') throw new Error(`Story-Funktion "${eff.call}" fehlt`);
      return fn(s, rng) || {};
    }
```

- In `applyEffect` am Ende vor `return out;`: `if ('show' in eff) out.show = eff.show;`
- In `validate`, in der Events-Schleife hinter der `break`-Prüfung:

```js
      for (const eff of e.effects || []) if ('call' in eff && typeof (story.fns || {})[eff.call] !== 'function') errs.push(`${story.id}: call "${eff.call}" ohne Funktion (${e.id})`);
```

Auch Choice-Effekte in Szenen können `call` tragen – die werden nicht validiert (Szenen sind Funktionen); das ist wie bisher bei `scene`-Effekten in Choices.

`Story.applyEffects` – im `for`-Body hinter `if (out.force === 'duel') { … }` ergänzen:

```js
      if (out.force === 'shootout' && typeof this.forceFight === 'function') { await this.forceFight(out.fight || {}); if (this.stale(st)) return; }
      if (out.show) { await UI.show(out.show); if (this.stale(st)) return; }
```

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Expected: grün (Node 215).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Gear-Slot weapon, Effekt call/show, Hooks fight:after und job:after"
```

---

### Task 4: `prevEndings` – Story nur nach bestimmten Vorgängerenden, Sperrtext im Titel

**Files:**
- Modify: `keller37.html` Block `story-rules` (`requirementMet`, neue `lockReasonFor`, `validate`), `story-engine` (`Stories.locked`), `title` (Sperrtext)
- Test: Block `selftest`

**Interfaces:**
- Produces: Story-Felder `prevEndings: ['id', …]` und `lockText: 'Text'`. `StoryRules.lockReasonFor(story, storyRuns)` → `null` (frei) | `'requires'` | `'prevEnding'`; `requirementMet` = `lockReasonFor(...) === null`. `Stories.locked()` liefert `{ id, title, requires, text }`, `text` = fertiger Sperrtext.

- [ ] **Step 1: Failing Tests**

```js
T.test('StoryRules.prevEndings: Story nur nach erlaubtem letzten Ende der Voraussetzung', () => {
  const st = { id: 'x', requires: 'kater', prevEndings: ['wirt', 'nuechtern'] };
  T.eq(StoryRules.lockReasonFor(st, {}), 'requires');
  T.eq(StoryRules.lockReasonFor(st, { kater: { endings: ['bett'], last: 'bett' } }), 'prevEnding');
  T.eq(StoryRules.lockReasonFor(st, { kater: { endings: ['bett', 'wirt'], last: 'wirt' } }), null);
  T.eq(StoryRules.lockReasonFor(st, { kater: { endings: ['wirt', 'bett'] } }), 'prevEnding', 'ohne last zählt das letzte in endings');
  T.eq(StoryRules.requirementMet(st, { kater: { endings: ['nuechtern'], last: 'nuechtern' } }), true);
  T.eq(StoryRules.requirementMet({ id: 'y' }, {}), true);
  T.eq(StoryRules.requirementMet({ id: 'y', requires: 'kater' }, { kater: { endings: ['bett'], last: 'bett' } }), true, 'ohne prevEndings reicht irgendein Ende');
});
T.test('StoryRules.validate: prevEndings müssen Enden der Voraussetzung sein', () => {
  const kater = { id: 'k', endings: [{ id: 'a', fallback: true }, { id: 'b' }] };
  const st = Object.assign({}, STORY_PROBE, { id: 'x', requires: 'k', prevEndings: ['a', 'zzz'] });
  const errs = StoryRules.validate(st, Object.keys(STORY_PROBE.scenes), ['spueler', 'post'], ['k', 'x'], { k: kater });
  T.eq(errs.length, 1); T.ok(errs[0].includes('zzz'));
});
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: FAIL (`lockReasonFor is not a function`).

- [ ] **Step 3: Implementieren**

`requirementMet` ersetzen durch:

```js
  /* null = spielbar; 'requires' = Vorgänger nie beendet; 'prevEnding' = letztes Vorgänger-Ende nicht in prevEndings */
  lockReasonFor(story, storyRuns) {
    if (!story.requires) return null;
    const run = storyRuns[story.requires];
    if (!(run && run.endings && run.endings.length)) return 'requires';
    if (story.prevEndings) {
      const last = run.last || run.endings[run.endings.length - 1];
      if (!story.prevEndings.includes(last)) return 'prevEnding';
    }
    return null;
  },
  requirementMet(story, storyRuns) { return StoryRules.lockReasonFor(story, storyRuns) === null; },
```

`validate` bekommt einen fünften Parameter `stories = {}` (Map id → Story) und prüft am Ende vor `return errs;`:

```js
    if (story.prevEndings && stories[story.requires]) {
      const ids = (stories[story.requires].endings || []).map((e) => e.id);
      for (const p of story.prevEndings) if (!ids.includes(p)) errs.push(`${story.id}: prevEnding "${p}" ist kein Ende von ${story.requires}`);
    }
```

`Stories.validateAll` ruft `StoryRules.validate(st, sceneIds, jobIds || …, storyIds, this.all)`.

`Stories.locked()` ersetzen:

```js
  locked() {
    return this.list().filter((st) => !StoryRules.requirementMet(st, State.meta.storyRuns)).map((st) => {
      const why = StoryRules.lockReasonFor(st, State.meta.storyRuns);
      const reqTitle = this.get(st.requires) ? this.get(st.requires).title : st.requires;
      const text = why === 'prevEnding' && st.lockText ? `🔒 ${st.title} – ${st.lockText}` : `🔒 ${st.title} – erst „${reqTitle}“ beenden`;
      return { id: st.id, title: st.title, requires: reqTitle, text };
    });
  },
```

`Title.show`: `lockEl.textContent = locked.map((l) => l.text).join(' · ');`

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Expected: grün (Node 217).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): prevEndings – Story nur nach bestimmten Vorgängerenden, eigener Sperrtext im Titel"
```

---

### Task 5: Jobs – `jobOverrides`, `Jobs.def`, `variant`, `Jobs.collect(id, flags)` + Hook `job:after`

**Files:**
- Modify: `keller37.html` Block `jobs` (`Jobs.render`, `take`, `runShift`, `collect`, `finishGame`, neue `def`)
- Modify: `keller37.html` Block `job-taxi` (`Taxi.finish` benutzt die Job-ID aus `Story.jobStart`), `job-spueler` unverändert
- Test: Block `selftest` (reine Logik: `StoryRules.jobDef`)

**Interfaces:**
- Produces: `StoryRules.jobDef(job, story)` → Kopie des Jobs überlagert mit `story.jobOverrides[job.id]` (rein, testbar); `Jobs.def(id)` (DOM) = `StoryRules.jobDef(Jobs.POOL[id], Story.story)`; `Jobs.render/take/runShift` benutzen `def`; `Jobs.take` reicht `job.variant` an den Screen durch, indem `Story.jobStart = { id, balance, variant }` gesetzt wird; `Jobs.collect(id, flags = {})` setzt `Object.assign(Story.s.flags, flags)` und ruft nach `job:done` `await Story.hook('job:after')`. `Taxi.finish` ruft `Jobs.collect(this.jobId)` mit `this.jobId = Story.jobStart ? Story.jobStart.id : 'taxi'` (in Plan 3 kommt die Kurier-Variante dazu).

- [ ] **Step 1: Failing Test**

```js
T.test('StoryRules.jobDef: Story-Overrides überlagern Job-Definition, requires: null löscht Voraussetzung', () => {
  const job = { id: 'eintreiber', name: 'Eintreiber', kind: 'shift', base: 150, requires: { strength: { gte: 4 } }, requireText: 'Stärke 4', pay: '150 €' };
  T.eq(StoryRules.jobDef(job, {}), job);
  const d = StoryRules.jobDef(job, { jobOverrides: { eintreiber: { base: 1000, requires: null, pay: '1.000 €' } } });
  T.eq([d.base, d.requires, d.pay, d.name], [1000, null, '1.000 €', 'Eintreiber']);
  T.eq(job.base, 150, 'Original unverändert');
  const s = base({ strength: 0, story: StoryRules.freshStoryPart(STORY_PROBE) });
  s.story.unlocked.jobs.push('eintreiber');
  T.eq(StoryRules.jobAvailable(job, s).ok, false);
  T.eq(StoryRules.jobAvailable(d, s).ok, true);
});
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: FAIL (`jobDef is not a function`).

- [ ] **Step 3: `StoryRules.jobDef`**

Nach `jobAvailable` einfügen:

```js
  /* Job-Definition für diese Story: story.jobOverrides[id] überlagert Felder (requires: null hebt eine Voraussetzung auf) */
  jobDef(job, story) {
    const o = story && story.jobOverrides && story.jobOverrides[job.id];
    return o ? Object.assign({}, job, o) : job;
  },
```

- [ ] **Step 4: `Jobs` umstellen**

In `Jobs` nach `POOL: { … },` einfügen:

```js
  def(id) { const j = this.POOL[id]; return j ? StoryRules.jobDef(j, Story.story) : null; },
```

`render`: `for (const job of Object.values(this.POOL)) {` → `for (const job of Object.keys(this.POOL).map((id) => this.def(id))) {`.

`take`: `const job = this.POOL[id];` → `const job = this.def(id);` und `Story.jobStart = { id, balance: State.s.balance };` → `Story.jobStart = { id, balance: State.s.balance, variant: job.variant || null };`.

`collect` ersetzen:

```js
  async collect(id, flags = {}) {
    const start = Story.jobStart;
    if (!start || start.id !== id) return false;
    Story.jobStart = null;
    const earned = State.s.balance - start.balance;
    Object.assign(Story.s.flags, flags); // Ergebnis-Flags des Minispiels (z. B. kontrolle) für job:after-Events
    Story.jobDone(id, earned);
    await Bus.emit('job:done', { id, earned });
    await Story.hook('job:after');
    return true;
  },
```

`runShift`: vor `await Story.evening();` einfügen `await Story.hook('job:after'); if (State.s !== run || run.story.ended) return;`.

`Taxi.finish`: `await Jobs.collect('taxi');` → `await Jobs.collect(Story.jobStart ? Story.jobStart.id : 'taxi');` und in `UI.register('job-taxi', …)` mount: `Jobs.finishGame('taxi')` → `Jobs.finishGame(Taxi.jobId)`, wobei `Taxi.start()` als erste Zeile nach dem Guard setzt `this.jobId = Story.jobStart ? Story.jobStart.id : 'taxi';` (Feld `jobId: 'taxi'` in das `Taxi`-Objekt aufnehmen). Achtung: `Jobs.collect` setzt `Story.jobStart = null` – deshalb die ID in `start()` merken, nicht in `finish()` lesen.

- [ ] **Step 5: Tests + Playtest-Stichprobe**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Expected: grün (Node 218).
Run: `python3 tests/playtest-story.py`
Expected: `140/140`, `ERRORS 0` (Taxi-Job in Story 1 läuft weiter über `Jobs.collect('taxi')`).

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(jobs): jobOverrides je Story, Jobs.def, Job-Variante an den Screen, job:after-Hook nach collect/runShift"
```

---

### Task 6: HUD `max` als Funktion, Tür `hinterzimmer` in `Story.DOORS`, Figuren und Hintergrund

**Files:**
- Modify: `keller37.html` Block `story-engine` (`hudNotes`, `Story.DOORS`), `cutscene-engine` (`CAST`, `PROPS`), CSS (`.cs-bg.bahnhof`, `.cs-bg.pfandleihe`)
- Test: Block `selftest` (nur Cast-Existenz im DOM-Test)

**Interfaces:**
- Produces: `hud[].max` darf Funktion `(s) => number` sein; mit `fmt: 'money'` werden Wert und Max als Geld formatiert („12.400 € / 20.000 €"). `Story.DOORS` enthält `'hinterzimmer'` (Screen-ID des Baccarat-Tischs, Plan 2). Figuren `anabi`, `stumme`, `kessler`, `brandt`, `kowalski`; Hintergründe `bahnhof`, `pfandleihe`.

- [ ] **Step 1: Failing DOM-Test**

Im Block `selftest` (Browser-Teil, Suche nach `typeof document !== 'undefined'` – die DOM-Tests stehen hinter dieser Prüfung) einfügen:

```js
if (typeof document !== 'undefined') T.test('Cutscene.CAST: Story-3-Figuren und Hintergründe', () => {
  for (const id of ['anabi', 'stumme', 'kessler', 'brandt', 'kowalski']) T.ok(Cutscene.CAST[id] && Cutscene.CAST[id].name, `Figur ${id}`);
  T.ok(Cutscene.PROPS.bahnhof && Cutscene.PROPS.pfandleihe, 'Props');
  const probe = document.createElement('div'); probe.className = 'cs-bg bahnhof'; document.body.append(probe);
  T.ok(getComputedStyle(probe).backgroundImage !== 'none', 'Hintergrund bahnhof hat CSS'); probe.remove();
});
```

- [ ] **Step 2: DOM-Test laufen lassen, muss fehlschlagen**

Run: `bash tests/dom-selftest.sh`
Expected: 1 FAIL (`Figur anabi`).

- [ ] **Step 3: Implementieren**

`Cutscene.CAST` ergänzen (hinter `insider`):

```js
    anabi: { name: 'Anabi Stash', emoji: '🕶️', color: '#d4af37' },
    stumme: { name: 'Der Stumme', emoji: '🃏', color: '#8a8a8a' },
    kessler: { name: 'Kessler', emoji: '🚬', color: 'var(--neon-red)' },
    brandt: { name: 'Kommissar Brandt', emoji: '👮', color: 'var(--neon-blue)' },
    kowalski: { name: 'Kowalski', emoji: '🔧', color: '#b8a070' },
```

`Cutscene.PROPS` ergänzen: `bahnhof: ['🚉', '🌙'], pfandleihe: ['🔫', '🏷️'],`

CSS hinter `.cs-bg.keller { … }`:

```css
.cs-bg.bahnhof { background: linear-gradient(180deg, #05070d 0%, #1a2233 45%, #3b3a2a 100%); }
.cs-bg.pfandleihe { background: linear-gradient(180deg, #2a2418 0%, #14110a 60%, #000 100%); }
```

`Story.DOORS: ['roulette', 'slots', 'horses', 'russian', 'blackjack', 'postman', 'hinterzimmer'],`

`Story.hudNotes` ersetzen:

```js
  hudNotes() {
    return (this.story.hud || []).map((hd) => {
      const v = this.s.vars[hd.var] || 0;
      const max = typeof hd.max === 'function' ? hd.max(State.s) : hd.max;
      const f = (n) => (hd.fmt === 'money' ? UI.fmt(n) : String(n));
      const txt = max != null ? (hd.fmt === 'money' ? `${f(v)} / ${f(max)}` : `${v}/${max}`) : f(v); // Zahlen wie bisher „0/3“, Geld „12.400 € / 20.000 €“
      const label = typeof hd.label === 'function' ? hd.label(State.s) : hd.label;
      return h('span', { class: `note ${hd.tone || 'gold'}` }, `${label} ${txt}`);
    });
  },
```

(Zahlen-HUDs bleiben exakt „Pegel 0/3" – der Playtest prüft diesen String.)

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Expected: grün.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(story): HUD-Maximum als Funktion, Tür hinterzimmer, Figuren Anabi/Stumme/Kessler/Brandt/Kowalski"
```

---

### Task 7: Spec-Abgleich und README-Notiz

**Files:**
- Modify: `docs/superpowers/specs/2026-09-16-story-mode-design.md` (Engine-Felder ergänzen)
- Modify: `README.md` (Abschnitt „Story-Engine" – neue Felder in einer Zeile je Feld)

- [ ] **Step 1: Story-Mode-Spec ergänzen**

Im Abschnitt „Engine-Änderungen"/Felderliste der Story-Mode-Spec (Suche nach `hud[].label`) diese Zeilen anhängen:

```markdown
- `turnoverGroups: { varName: [gameIds] }` – Umsatz-Gruppen; `umsatz`/`umsatzTotal` zählen immer (Bus `stake`).
- `broken: { door: price }` im Story-Zustand; Effekte `{ break, price }`, `{ repair }`; `StoryRules.repair(s, door)`; Lobby zeigt 🔧.
- `fns: { name: (s, rng) => out }` mit Effekt `{ call: 'name' }`; `out` wie ein Effekt-Ergebnis (`scene`, `toast`, `achievement`, `force`, `fight`, `show`).
- Effekt `{ show: 'screen' }`; Hooks `fight:after`, `job:after`; Gear-Slot `weapon` in `SET_KEYS`.
- `prevEndings: [ids]` + `lockText`; `jobOverrides: { jobId: { base, requires, pay, … } }`; Job-Feld `variant` (an den Screen über `Story.jobStart.variant`).
- `hud[].max` darf Funktion sein.
```

- [ ] **Step 2: README**

Im README-Abschnitt zur Story-Engine (Suche `luckMod`) einen Satz ergänzen: „Story 3 bringt Umsatzzähler (`stake`), kaputte Türen (`broken`/🔧), Story-Funktionen (`call`), Waffen-Slot, `prevEndings` und Job-Overrides – alles generisch."

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-09-16-story-mode-design.md README.md
git commit -m "docs: Story-Engine 3 – neue Felder in Spec und README"
```

---

## Self-Review

- **Spec-Abdeckung (§10):** stake/recordStake (T1), broken/repair/🔧 (T2), weapon/SET_KEYS (T3), call/fns + validate (T3), fight:after/job:after (T3, T5), show (T3), prevEndings + lockText (T4), jobOverrides + variant + collect-Flags (T5), Figuren (T6), hud max (T6), Tür hinterzimmer (T6; Screen selbst in Plan 2), Pfandleihe-Schaufenster (Plan 3), `forceFight` (Plan 3, Aufruf hier vorbereitet).
- **Platzhalter:** keine.
- **Typkonsistenz:** `recordStake(st, bet, game, story)` überall mit `st = s.story`; `repair(s, door)` → `{ ok, price, reason? }`; `lockReasonFor(story, storyRuns)`; `jobDef(job, story)`; `Jobs.collect(id, flags)`; `Story.jobStart.variant`; `Taxi.jobId`.
