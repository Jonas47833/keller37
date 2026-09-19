# Admin-Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein verstecktes, per `?dev` + Login erreichbares Admin-Panel in `keller37.html`, mit dem sich Werte, Screens, Storys (Tag/Flags/Vars/Jobs/Enden) und einzelne Szenen sofort prüfen lassen.

**Architecture:** Zwei neue Script-Blöcke: `dev-rules` (rein, Node-getestet: Hash, Login, Zahlenprüfung, Flag-Namen, Gruppierungen) und `dev` (Panel-DOM und Aktionen, datengetrieben aus `UI.screens`, `Cutscene.SCENES`, `Stories.all`, `Jobs.POOL`, `Rules.GEAR`). Der Story-Einstieg bekommt ein Options-Objekt (`StoryRules.optsFromParams`), damit URL und Panel denselben Startpfad benutzen. CSS nur unter `#devFab/#devPanel/#devLogin`; ohne `?dev` bzw. Login existiert kein Panel-DOM.

**Tech Stack:** Vanilla JS/CSS in einer HTML-Datei, Node-Selftest (`tests/run-selftest.mjs`), CDP-Playtests in Python (`tests/playtest-story.py`-Infrastruktur, Headless Chrome, `websockets`).

**Spec:** `docs/superpowers/specs/2026-09-18-admin-panel-design.md`

## Global Constraints

- Eine einzige HTML-Datei (`keller37.html`); Tests liegen unter `tests/`.
- Alle Texte Deutsch.
- Ohne `?dev` bzw. ohne Anmeldung: kein Panel-DOM, keine Listener; `python3 tests/desktop-diff.py` bleibt 0 px.
- `dev` wird **nicht** in `Story.consumeDevParams` entfernt und zählt **nicht** zu `skipTitle` im Boot.
- Login: `DevRules.hash(user + ':' + pass) === DEV_LOGIN_HASH`; `DEV_LOGIN_HASH = '6222687456220819'` (cyrb53 von `Admin:<Passwort>`). Kein Klartext im Repo.
- Anmeldung in `sessionStorage['keller37.dev'] = '1'`, Reiter in `sessionStorage['keller37.devTab']`; alle Storage-Zugriffe in try/catch.
- Alle Tap-Ziele im Panel ≥ 44 px; Panel-Breite Desktop 380 px, ≤ 760 px 100 %; z-Index Panel/Knopf 97, Login 98.
- Panel-Look: Hintergrund `#1b1d22`, Text `#e6e6e6`, Akzent `#7dd3fc`, `font-family: var(--font-mono)`; keine Regel reagiert auf `body[data-zone]`.
- Aktionen benutzen bestehende Wege (`UI.show`, `Modes.enter`, `Story.finish`, `Jobs.take`, `Cutscene.play`) – keine kopierten Engine-Pfade.
- Szenen-Vorschau: `Cutscene.play(id, ctx)` direkt, nie `Story.playScene` (keine Effekte auf den Spielstand).
- Vor jedem Commit: `node tests/run-selftest.mjs` grün. Tests, die Chrome brauchen, laufen mit eigenem Port (`K37_PORT=9371`, Profil `/tmp/k37dev-profile`), weil eine andere Session Port 9335 nutzt.
- Deutsche Texte mit geraden Anführungszeichen (`„…"`) brechen `"…"`-Strings in Shell-Heredocs: Python-Skripte mit `'''…'''` oder das Edit-Tool benutzen.
- Commits enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## Dateistruktur

- `keller37.html`
  - CSS: neuer Block `/* -- Admin-Panel -- */` direkt vor `/* -- Reduced Motion -- */` (Zeile ≈ 586).
  - `<script id="dev-rules">` neu, direkt vor `<script id="title">` (nach `gang-rules`).
  - `<script id="dev">` neu, direkt vor `<script id="selftest">` (nach `story-stash`).
  - `story-rules`: `StoryRules.optsFromParams(params)`.
  - `story-engine`: `Story.enter(choice, opts)` liest `opts` statt `params`.
  - `title`: `Modes.enter(choice, opts)` reicht `opts` durch.
  - `jobs`: `Jobs.take(id, { force })`.
  - `ui`: `UI.show` ruft am Ende `Dev.render()` (guarded).
  - `boot`: `Dev.init()` nach `UI.mountShell()`.
  - `selftest`: neue Tests für `DevRules` und `StoryRules.optsFromParams`.
- `tests/run-selftest.mjs`: `dev-rules` in die Block-Liste.
- `tests/playtest-dev.py` (neu): CDP-Playtest des Panels, nutzt `tests/playtest-story.py` wie `mobile-check.py`.
- `tests/mobile-check.py`: ein Check „Panel ≥ 44 px, kein Overflow" bei 400 px.
- `README.md`: Abschnitt „Admin-Panel", Test-Zeile.
- `docs/superpowers/screenshots/dev-*.png`.

## Vorab-Entscheidungen (Abweichungen von der Spec, hier verbindlich)

1. `DevRules.parseNumber(raw, { min, max })` – nur Ganzzahlen, Punkte/Leerzeichen als Tausendertrenner erlaubt; die Spec-Option `int` entfällt.
2. „Alle Achievements" schreibt die IDs direkt in `State.meta.achievements` (kein `Achievements.unlock` je ID – das wären 20+ Toasts und Sounds).
3. `UI.show` ruft `Dev.render()` direkt (guarded) statt über ein Bus-Event – kein Abo-Bookkeeping bei Logout/Login.
4. „Job starten" listet alle Jobs aus `Jobs.POOL` (nicht nur die der Story) und ruft `Jobs.take(id, { force: true })`, das die Verfügbarkeitsprüfung überspringt.
5. Screen-Knopf auf gesperrtem Screen in der Story: das Panel trägt Tür/Raum in `Story.s.unlocked` ein und setzt `Story.allowOnce = id` (für Gates), dann `UI.show(id)` – statt eines 🔒-Toasts.
6. Starttag 1 spielt das Intro, Starttag > 1 überspringt es (wie `?day`).
7. Der Playtest ist eine eigene Datei `tests/playtest-dev.py` (wie `mobile-check.py` importiert sie `playtest-story.py`), Port 9371.

---

### Task 1: `dev-rules` – reine Helfer mit Selftests

**Files:**
- Modify: `keller37.html` (neuer Block vor `<script id="title">`; Tests im Block `selftest` vor `/* ---- StoryRules ---- */`)
- Modify: `tests/run-selftest.mjs` (Block-Liste)

**Interfaces:**
- Produces: `DEV_LOGIN_HASH` (String), `DevRules.hash(str) → String`, `DevRules.login(user, pass) → boolean`, `DevRules.parseNumber(raw, { min, max }) → number | null`, `DevRules.flagNamesIn(story) → string[]` (sortiert, ohne Duplikate), `DevRules.groupScreens(ids) → { keller, royal, stadt, story, sonst }`, `DevRules.sceneGroups(sceneIds, stories) → [{ id, title, ids }]` (erste Gruppe `{ id: null, title: 'Keller' }`).

- [ ] **Step 1: Block-Liste im Node-Runner erweitern**

In `tests/run-selftest.mjs` in der `for (const id of [...])`-Liste `'gang-rules'` um `'dev-rules'` ergänzen:

```js
for (const id of ['rules', 'gear-rules', 'perk-rules', 'util', 'state', 'bus', 'story-rules', 'royal-rules', 'baccarat-rules', 'gang-rules', 'dev-rules', 'story-probe', 'story-schuld', 'story-kater', 'story-stash', 'selftest']) {
```

- [ ] **Step 2: Fehlschlagende Tests schreiben**

In `keller37.html` im Block `selftest`, direkt vor der Zeile `/* ---- StoryRules ---- */`, einfügen:

```js
/* ---- DevRules (Admin-Panel) ---- */
T.test('DevRules.hash: deterministisch, nahe Eingaben verschieden', () => {
  T.eq(DevRules.hash('a:b'), '5416304911849898');
  T.eq(DevRules.hash('a:c'), '2267616075222599');
  T.eq(DevRules.hash(''), '3338908027751811');
  T.eq(DevRules.hash('a:b'), DevRules.hash('a:b'));
});
T.test('DevRules.login: nur exakte Zugangsdaten', () => {
  const ok = DevRules.hash('Admin:<Passwort>') === DEV_LOGIN_HASH;
  T.ok(ok, 'Hash der Zugangsdaten stimmt nicht mit DEV_LOGIN_HASH überein');
  T.eq(DevRules.login('Admin', '<Passwort>'), true);
  T.eq(DevRules.login('admin', '<Passwort>'), false, 'Groß/Klein');
  T.eq(DevRules.login('Admin', 'falsch'), false);
  T.eq(DevRules.login(' Admin', '<Passwort>'), false, 'Leerzeichen');
  T.eq(DevRules.login('', ''), false);
});
T.test('DevRules.parseNumber: Ganzzahlen mit Grenzen, Müll → null', () => {
  T.eq(DevRules.parseNumber('5000'), 5000);
  T.eq(DevRules.parseNumber(' 5.000 '), 5000, 'Tausenderpunkt');
  T.eq(DevRules.parseNumber('-20', { min: -100 }), -20);
  T.eq(DevRules.parseNumber('4', { min: 0, max: 3 }), null, 'über max');
  T.eq(DevRules.parseNumber('-1', { min: 0 }), null, 'unter min');
  T.eq(DevRules.parseNumber(''), null);
  T.eq(DevRules.parseNumber('abc'), null);
  T.eq(DevRules.parseNumber('1e3'), null);
  T.eq(DevRules.parseNumber('1,5'), null, 'keine Dezimalzahlen');
  T.eq(DevRules.parseNumber(null), null);
  T.eq(DevRules.parseNumber(42), 42, 'Zahl statt String');
});
T.test('DevRules.flagNamesIn: Flags aus Effekten, Bedingungen, Gates, Kapiteln, Enden', () => {
  const st = {
    scenes: {
      a: [{ choices: [{ value: 'x', effects: [{ flag: 'f1' }, { unflag: 'f2' }], when: { notFlag: 'f3' } }] }],
      b: () => [{ choices: [{ value: 'y', effects: [{ flag: 'f4' }] }] }],
    },
    events: [{ when: { all: [{ flag: 'f5' }, { not: { flag: 'f6' } }] }, effects: [{ unflag: 'f1' }] }],
    gates: { royal: [{ when: { any: [{ flag: 'f7' }] }, text: 't' }] },
    chapters: [{ when: { flag: 'f8' } }],
    endings: [{ id: 'e', when: { flag: 'f9' } }],
  };
  T.eq(DevRules.flagNamesIn(st), ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9']);
  T.eq(DevRules.flagNamesIn({}), []);
  T.ok(DevRules.flagNamesIn(STORY_KATER).includes('abgestuerzt'), 'Kater: abgestuerzt');
  T.ok(DevRules.flagNamesIn(STORY_KATER).includes('zitter'), 'Kater: zitter');
  const probe = DevRules.flagNamesIn(STORY_PROBE);
  T.eq(probe, [...new Set(probe)].sort(), 'sortiert, ohne Duplikate');
});
T.test('DevRules.groupScreens: Keller/Royal/Stadt/Story/Sonst', () => {
  const g = DevRules.groupScreens(['hub', 'roulette', 'royal', 'craps', 'stadt', 'jobs', 'vito', 'job-spueler', 'shootout', 'skills']);
  T.eq(g.keller, ['hub', 'roulette', 'skills']);
  T.eq(g.royal, ['royal', 'craps']);
  T.eq(g.stadt, ['stadt']);
  T.eq(g.story, ['jobs', 'vito', 'job-spueler']);
  T.eq(g.sonst, ['shootout']);
  T.eq(DevRules.groupScreens([]), { keller: [], royal: [], stadt: [], story: [], sonst: [] });
});
T.test('DevRules.sceneGroups: Story-Szenen der Story, Rest ist Keller', () => {
  const stories = { kater: { id: 'kater', title: 'Der Kater', scenes: { 'kater.intro': [], 'kater.k2': [] } }, probe: { id: 'probe', title: 'Probe', scenes: { 'probe.n1': [] } } };
  const g = DevRules.sceneGroups(['intro', 'kater.k2', 'probe.n1', 'divorce', 'kater.intro'], stories);
  T.eq(g[0], { id: null, title: 'Keller', ids: ['intro', 'divorce'] });
  T.eq(g[1], { id: 'kater', title: 'Der Kater', ids: ['kater.k2', 'kater.intro'] });
  T.eq(g[2], { id: 'probe', title: 'Probe', ids: ['probe.n1'] });
});
```

- [ ] **Step 3: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: Abbruch mit `Script-Block "dev-rules" fehlt` (der Runner wirft, bevor Tests laufen).

- [ ] **Step 4: Block `dev-rules` anlegen**

In `keller37.html` direkt vor `<script id="title">` einfügen:

```html
<script id="dev-rules">
/* ================= ADMIN-PANEL – reine Helfer (Login-Hash, Zahlen, Flag-Namen, Gruppierung) ================= */
/* Hash von "Benutzer:Passwort" (cyrb53). Ändern: in der Browser-Konsole DevRules.hash('Name:Passwort') ausführen und das Ergebnis hier eintragen. */
const DEV_LOGIN_HASH = '6222687456220819';
const DevRules = {
  hash(str) {
    let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
    for (let i = 0; i < str.length; i++) {
      const ch = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761); h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507); h1 ^= Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507); h2 ^= Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return String(4294967296 * (2097151 & h2) + (h1 >>> 0));
  },
  login(user, pass) { return DevRules.hash(`${user}:${pass}`) === DEV_LOGIN_HASH; },
  /* Ganzzahl aus einem Eingabefeld (Punkte/Leerzeichen als Tausendertrenner erlaubt); null bei Müll oder außerhalb der Grenzen */
  parseNumber(raw, { min = -Infinity, max = Infinity } = {}) {
    const s = String(raw == null ? '' : raw).replace(/[\s.]/g, '');
    if (!/^-?\d+$/.test(s)) return null;
    const n = Number(s);
    if (n < min || n > max) return null;
    return n;
  },
  /* Flag-Namen einer Story: Effekte (flag/unflag) und Bedingungen (flag/notFlag, rekursiv not/all/any) in Szenen, Events, Gates, Kapiteln, Enden */
  flagNamesIn(story) {
    const out = new Set();
    const cond = (c) => {
      if (!c || typeof c !== 'object') return;
      if (c.flag) out.add(c.flag);
      if (c.notFlag) out.add(c.notFlag);
      if (c.not) cond(c.not);
      (c.all || []).forEach(cond); (c.any || []).forEach(cond);
    };
    const effs = (list) => (list || []).forEach((e) => { if (e && e.flag) out.add(e.flag); if (e && e.unflag) out.add(e.unflag); });
    const panels = (def) => {
      let p = def;
      if (typeof def === 'function') { try { p = def({ raw: { flags: {}, vars: {} }, prev: {}, flags: {} }); } catch (e) { p = []; } }
      for (const panel of p || []) for (const ch of panel.choices || []) { effs(ch.effects); cond(ch.when); }
    };
    for (const def of Object.values(story.scenes || {})) panels(def);
    for (const ev of story.events || []) { cond(ev.when); effs(ev.effects); }
    for (const list of Object.values(story.gates || {})) for (const g of list || []) cond(g.when);
    for (const ch of story.chapters || []) cond(ch.when);
    for (const end of story.endings || []) cond(end.when);
    return [...out].sort();
  },
  KELLER_SCREENS: ['hub', 'roulette', 'slots', 'horses', 'russian', 'blackjack', 'hinterzimmer', 'postman', 'finance', 'invest', 'life', 'skills'],
  ROYAL_SCREENS: ['royal', 'megaslots', 'craps', 'wheel'],
  STORY_SCREENS: ['jobs', 'vito'],
  groupScreens(ids) {
    const g = { keller: [], royal: [], stadt: [], story: [], sonst: [] };
    for (const id of ids) {
      if (DevRules.KELLER_SCREENS.includes(id)) g.keller.push(id);
      else if (DevRules.ROYAL_SCREENS.includes(id)) g.royal.push(id);
      else if (id === 'stadt') g.stadt.push(id);
      else if (DevRules.STORY_SCREENS.includes(id) || id.startsWith('job-')) g.story.push(id);
      else g.sonst.push(id);
    }
    return g;
  },
  /* Szenen-IDs nach Story gruppieren (Reihenfolge wie sceneIds); alles ohne Story ist „Keller" */
  sceneGroups(sceneIds, stories) {
    const taken = new Set();
    const groups = [];
    for (const st of Object.values(stories || {})) {
      const ids = sceneIds.filter((id) => st.scenes && Object.prototype.hasOwnProperty.call(st.scenes, id));
      ids.forEach((id) => taken.add(id));
      groups.push({ id: st.id, title: st.title || st.id, ids });
    }
    groups.unshift({ id: null, title: 'Keller', ids: sceneIds.filter((id) => !taken.has(id)) });
    return groups;
  },
};
</script>

```

- [ ] **Step 5: Tests laufen lassen – müssen bestehen**

Run: `node tests/run-selftest.mjs`
Expected: `N bestanden, 0 fehlgeschlagen` (N = bisherige Zahl + 6).

- [ ] **Step 6: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(dev): DevRules – Login-Hash, Zahlenprüfung, Flag-Namen, Gruppierungen (Node-getestet)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Story-Einstieg über Options-Objekt, `Jobs.take(force)`

**Files:**
- Modify: `keller37.html` – Block `story-rules` (neue Funktion `optsFromParams` in `StoryRules`, z. B. direkt vor `freshStoryPart`), Block `story-engine` (`Story.enter`), Block `title` (`Modes.enter`), Block `jobs` (`Jobs.take`), Block `selftest`.

**Interfaces:**
- Produces: `StoryRules.optsFromParams(params: URLSearchParams) → { fresh: boolean, story: string|null, prev: string|null, day: number|null, weapon: number|null, ending: string|null, job: string|null }`; `Story.enter(choice, opts = null)`; `Modes.enter(choice, opts = null)`; `Jobs.take(id, { force = false } = {})`.
- Consumes: nichts aus Task 1.

- [ ] **Step 1: Fehlschlagenden Test schreiben**

Im Block `selftest`, direkt vor `/* ---- DevRules (Admin-Panel) ---- */`:

```js
T.test('StoryRules.optsFromParams: URL-Parameter → Options-Objekt', () => {
  T.eq(StoryRules.optsFromParams(new URLSearchParams('')), { fresh: false, story: null, prev: null, day: null, weapon: null, ending: null, job: null });
  T.eq(StoryRules.optsFromParams(new URLSearchParams('fresh&story=kater&prev=doc&day=5&weapon=2&ending=wirt&job=spueler')),
    { fresh: true, story: 'kater', prev: 'doc', day: 5, weapon: 2, ending: 'wirt', job: 'spueler' });
  T.eq(StoryRules.optsFromParams(new URLSearchParams('day=abc&weapon=')).day, 1, 'Müll bei day → 1 (wie bisher parseInt||1)');
  T.eq(StoryRules.optsFromParams(new URLSearchParams('day=abc&weapon=')).weapon, 0, 'Müll bei weapon → 0');
  T.eq(StoryRules.optsFromParams(new URLSearchParams('day=0')).day, 1, 'day mindestens 1');
  T.eq(StoryRules.optsFromParams(new URLSearchParams('weapon=9')).weapon, 3, 'weapon höchstens 3');
});
```

- [ ] **Step 2: Test laufen lassen – muss fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: `FAIL StoryRules.optsFromParams: … StoryRules.optsFromParams is not a function`.

- [ ] **Step 3: `optsFromParams` in `StoryRules` ergänzen**

Im Block `story-rules`, direkt vor `  freshStoryPart(story, storyRuns = {}) {`:

```js
  /* Dev-Parameter des Story-Einstiegs als Options-Objekt – URL (?fresh&story=…) und Admin-Panel füllen dieselbe Form */
  optsFromParams(params) {
    const int = (k, lo, hi, dflt) => (params.has(k) ? Math.max(lo, Math.min(hi, parseInt(params.get(k), 10) || dflt)) : null);
    return {
      fresh: params.has('fresh'),
      story: params.get('story'),
      prev: params.get('prev'),
      day: int('day', 1, Infinity, 1),
      weapon: int('weapon', 0, 3, 0),
      ending: params.get('ending'),
      job: params.get('job'),
    };
  },
```

- [ ] **Step 4: `Story.enter` auf `opts` umstellen**

Im Block `story-engine` die Methode `async enter(choice) {` komplett ersetzen durch:

```js
  async enter(choice, opts = null) {
    Stories.validateAll();
    const o = opts || StoryRules.optsFromParams(new URLSearchParams(location.search));
    this.consumeDevParams(); // `o` ist eine Kopie – gilt für diesen Einstieg, danach nicht mehr
    if (choice === 'newstory' && State.hasStoryRun() && !o.fresh) {
      State.setMode('story');
      this.story = Stories.get(State.s.story.id);
      this.setup();
      const c = await Cutscene.play('story.newConfirm', {});
      if (c !== 'yes') return this.enter('story');
    }
    if (choice === 'newstory' || !State.hasStoryRun()) {
      const forced = o.story;
      const forcedNext = this.forcedNext; this.forcedNext = null;
      const id = forced && Stories.get(forced) ? forced : (forcedNext || StoryRules.pickStory(Stories.list(), State.meta.storyRuns, Math.random));
      const story = Stories.get(id);
      State.startStory(story);
      if (o.prev != null && o.fresh && story.requires) State.s.story.prev[story.requires] = o.prev;
      if (typeof Perks !== 'undefined') Perks.refreshExcluded(true);
      if (typeof Roulette !== 'undefined') Roulette.lastBets = [];
      if (o.day != null && o.fresh) State.s.story.day = o.day;
      if (o.weapon != null && o.fresh) State.s.weapon = o.weapon;
      this.story = story;
      this.setup();
      State.save();
      const st = this.s;
      if (o.day == null) { await this.playScene(story.intro); if (this.stale(st)) return; }
      await this.applyChapter();
      if (this.stale(st)) return;
      if (o.ending) { const end = story.endings.find((e) => e.id === o.ending); if (end) return this.finish(end); }
      await this.morning();
      if (o.job && this.s.phase === 'morning') await Jobs.take(o.job);
      return;
    }
    State.setMode('story');
    this.story = Stories.get(State.s.story.id);
    if (!this.story) { UI.toast({ icon: '🐛', title: 'Story unbekannt', text: State.s.story.id, tone: 'loss' }); return Modes.enter('free'); }
    this.setup();
    const st = this.s;
    await this.applyChapter();
    if (this.stale(st)) return;
    if (st.phase === 'morning') await this.morning(); else await this.evening();
    if (this.stale(st)) return; // ein sofortiges Ende im Morgen-Event darf Jobs.take/Toast nicht mehr auf einer toten Story ausführen
    if (o.job && this.s.phase === 'morning') await Jobs.take(o.job);
    UI.toast({ icon: '📖', title: this.story.title, text: `Tag ${this.s.day} von ${this.story.days}.` });
  },
```

Prüfen, dass die alte Fassung keine weiteren `params.`-Zugriffe hatte, die hier fehlen: `grep -n "params\." keller37.html | sed -n '/story-engine/,$p'` – innerhalb von `Story.enter` darf kein `params` mehr vorkommen.

- [ ] **Step 5: `Modes.enter` reicht `opts` durch**

Im Block `title`, in `const Modes = {`: Signatur `async enter(choice) {` → `async enter(choice, opts = null) {` und die Zeile `if (typeof Story !== 'undefined') await Story.enter(choice);` → `if (typeof Story !== 'undefined') await Story.enter(choice, opts);`.

- [ ] **Step 6: `Jobs.take` mit `force`**

Im Block `jobs`: `async take(id) {` → `async take(id, { force = false } = {}) {` und die Zeile
`if (!job || !StoryRules.jobAvailable(job, State.s).ok) return;` →
`if (!job || (!force && !StoryRules.jobAvailable(job, State.s).ok)) return; // force: Admin-Panel überspringt die Verfügbarkeitsprüfung`

- [ ] **Step 7: Node-Selftest + DOM-Selftest**

Run: `node tests/run-selftest.mjs && sh tests/dom-selftest.sh`
Expected: beide grün (Node: +1 Test).

- [ ] **Step 8: Story-Playtest (URL-Pfad unverändert)**

Run: `K37_PORT=9371 K37_PROFILE=/tmp/k37dev-profile K37_SHOTS=/tmp/k37dev-story python3 tests/playtest-story.py`
Expected: `ERRORS 0`, keine `FAIL`-Zeile. (Dauert einige Minuten. Läuft in `main()` alles über `?fresh&story=…&day=…&prev=…&job=…&ending=…`, deckt also genau den umgestellten Pfad ab.)

- [ ] **Step 9: Commit**

```bash
git add keller37.html
git commit -m "refactor(story): Einstieg über Options-Objekt (StoryRules.optsFromParams), Jobs.take(force)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Panel-Gerüst – Login, Knopf, Schublade, Reiter, CSS, Boot; Playtest-Datei

**Files:**
- Modify: `keller37.html` – CSS-Block vor `/* -- Reduced Motion -- */`, neuer `<script id="dev">` vor `<script id="selftest">`, `UI.show` (Block `ui`), Boot.
- Create: `tests/playtest-dev.py`

**Interfaces:**
- Consumes: `DevRules.login` (Task 1).
- Produces: `Dev.active`, `Dev.init()`, `Dev.loggedIn()`, `Dev.login(user, pass) → boolean`, `Dev.logout()`, `Dev.toggle(on?)`, `Dev.render()`, Helfer `Dev.numRow(label, get, set, opts)`, `Dev.boolRow(label, get, set)`, `Dev.selectRow(label, options, get, set)`, `Dev.btn(label, fn, cls)`, `Dev.sec(title, ...kids)`, `Dev.toast(text)`, `Dev.refreshGame()`; Reiter-Renderer `renderWerte/renderScreens/renderStory/renderSzenen` (in diesem Task Platzhalter, die einen leeren `div` liefern – Tasks 4–7 füllen sie).
- DOM: `#devLogin` (`form.dev-login`, Inputs `#devUser`, `#devPass`), `#devFab`, `#devPanel[.open]`, `.dev-tab[data-tab]`, `#devBody`, `#devInfo`.

- [ ] **Step 1: Playtest-Datei anlegen (Login-Szenario, schlägt fehl)**

`tests/playtest-dev.py`:

```python
#!/usr/bin/env python3
'''
CDP-Playtest des Admin-Panels (?dev + Login) in keller37.html.

Nutzt den CDP-Helfer aus tests/playtest-story.py (wie mobile-check.py). Aufruf:
    python3 tests/playtest-dev.py
Env: K37_PORT (Standard 9371), K37_PROFILE, K37_SHOTS (Screenshots, Standard /tmp/k37dev).
Am Ende: "FAILS n" und Exit-Code 1 bei Fehlern.
'''
import asyncio
import importlib.util
import json
import os
import sys

sys.argv = [sys.argv[0]]
os.environ.setdefault("K37_PORT", "9371")
os.environ.setdefault("K37_PROFILE", "/tmp/k37dev-profile")
os.environ.setdefault("K37_SHOTS", "/tmp/k37dev")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("pt", os.path.join(ROOT, "tests", "playtest-story.py"))
pt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pt)
URL = "file://" + os.path.join(ROOT, "keller37.html")
USER, PASS = "Admin", "<Passwort>"

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("%s %s%s" % ("OK  " if ok else "FAIL", name, (" - " + str(detail)) if detail else ""))


async def login(cdp):
    '''Login-Formular ausfüllen und absenden; wartet auf den Knopf.'''
    await cdp.eval("document.querySelector('#devUser').value = %s; document.querySelector('#devPass').value = %s; document.querySelector('#devLogin').requestSubmit();"
                   % (json.dumps(USER), json.dumps(PASS)), await_promise=False)
    return await cdp.wait_for("!!document.querySelector('#devFab')", timeout=2.0)


async def open_tab(cdp, tab):
    await cdp.eval("(function(){ const p = document.querySelector('#devPanel'); if (!p.classList.contains('open')) Dev.toggle(true); document.querySelector('.dev-tab[data-tab=%s]').click(); })()" % json.dumps(tab), await_promise=False)
    await asyncio.sleep(0.15)


async def scenario_login(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub", wait=1.4)
    present = await cdp.eval("!!(document.querySelector('#devLogin') || document.querySelector('#devFab') || document.querySelector('#devPanel'))", await_promise=False)
    record("ohne ?dev: kein Panel-DOM", present is False, present)

    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    login_visible = await cdp.eval("!!document.querySelector('#devLogin') && !document.querySelector('#devFab')", await_promise=False)
    record("?dev: Login sichtbar, noch kein Knopf", login_visible is True)
    await cdp.eval("document.querySelector('#devUser').value = 'Admin'; document.querySelector('#devPass').value = 'falsch'; document.querySelector('#devLogin').requestSubmit();", await_promise=False)
    await asyncio.sleep(0.1)
    wrong = await cdp.eval("(function(){ const b = document.querySelector('#devLogin'); return { there: !!b, shake: b && b.classList.contains('shake'), fab: !!document.querySelector('#devFab'), pass: b && document.querySelector('#devPass').value }; })()", await_promise=False) or {}
    record("falsches Passwort: bleibt zu, wackelt, Feld geleert", wrong.get("there") and wrong.get("shake") and not wrong.get("fab") and wrong.get("pass") == "", wrong)
    ok = await login(cdp)
    gone = await cdp.eval("!document.querySelector('#devLogin')", await_promise=False)
    record("richtiges Passwort: Knopf da, Login weg", bool(ok) and gone is True)
    ss = await cdp.eval("sessionStorage.getItem('keller37.dev')", await_promise=False)
    record("sessionStorage merkt Anmeldung", ss == "1", ss)

    await cdp.navigate(URL + "?mode=free&screen=hub", wait=1.4)
    fab = await cdp.eval("!!document.querySelector('#devFab') && !document.querySelector('#devLogin')", await_promise=False)
    record("Reload ohne ?dev: Knopf bleibt", fab is True)
    await cdp.eval("document.querySelector('#devFab').click()", await_promise=False)
    await asyncio.sleep(0.3)
    panel = await cdp.eval("(function(){ const p = document.querySelector('#devPanel'); const tabs = [...document.querySelectorAll('.dev-tab')].map(t => t.dataset.tab); return { open: p.classList.contains('open'), tabs, info: document.querySelector('#devInfo').textContent, width: p.getBoundingClientRect().width }; })()", await_promise=False) or {}
    record("Knopf öffnet Schublade mit vier Reitern, 380 px", panel.get("open") and panel.get("tabs") == ["werte", "screens", "story", "szenen"] and abs(panel.get("width", 0) - 380) < 1, panel)
    record("Kopfzeile zeigt Modus, Screen, Kontostand", "frei" in (panel.get("info") or "") and "hub" in (panel.get("info") or "") and "€" in (panel.get("info") or ""), panel.get("info"))
    await cdp.screenshot("dev-panel.png")
    await cdp.eval("document.querySelector('.dev-tab[data-tab=story]').click()", await_promise=False)
    await asyncio.sleep(0.1)
    tab = await cdp.eval("sessionStorage.getItem('keller37.devTab')", await_promise=False)
    record("Reiter wird gemerkt", tab == "story", tab)

    await cdp.eval("Dev.logout()", await_promise=False)
    await asyncio.sleep(0.1)
    after = await cdp.eval("(function(){ return { fab: !!document.querySelector('#devFab'), panel: !!document.querySelector('#devPanel'), ss: sessionStorage.getItem('keller37.dev') }; })()", await_promise=False) or {}
    record("Abmelden: Knopf und Panel weg, sessionStorage leer", not after.get("fab") and not after.get("panel") and after.get("ss") is None, after)


async def main():
    cdp = pt.CDP()
    cdp.launch()
    try:
        await cdp.connect()
        await scenario_login(cdp)
    finally:
        errs = [e for e in cdp.console_errors]
        record("keine Konsolenfehler", not errs, errs[:3])
        await cdp.close()
    fails = [n for n, ok in RESULTS if not ok]
    print("FAILS", len(fails))
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Playtest laufen lassen – muss fehlschlagen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAIL ?dev: Login sichtbar …` und weitere FAILs, `FAILS ≥ 5`.

- [ ] **Step 3: CSS einfügen**

In `keller37.html` direkt vor `/* -- Reduced Motion -- */`:

```css
/* -- Admin-Panel (nur mit ?dev + Login im DOM; bewusst weder Keller- noch Royal-Look) -- */
#devFab { position: fixed; right: 14px; bottom: 14px; width: 44px; height: 44px; border-radius: 50%; border: 1px solid #3a3f4a; background: #1b1d22; color: #e6e6e6; font-size: 20px; line-height: 1; z-index: 97; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,.5); }
#devPanel { position: fixed; top: 0; right: 0; bottom: 0; width: 380px; max-width: 100%; background: #1b1d22; color: #e6e6e6; font-family: var(--font-mono); font-size: 13px; z-index: 97; transform: translateX(100%); transition: transform .2s ease; display: flex; flex-direction: column; box-shadow: -6px 0 18px rgba(0,0,0,.5); }
#devPanel.open { transform: none; }
.dev-head { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-bottom: 1px solid #2c3038; flex-wrap: wrap; }
.dev-head strong { font-size: 14px; }
.dev-info { color: #9aa3b2; font-size: 12px; flex: 1 1 100%; margin: 0; }
.dev-tabs { display: grid; grid-template-columns: repeat(4, 1fr); border-bottom: 1px solid #2c3038; }
.dev-tab { min-height: 44px; background: none; border: 0; border-bottom: 2px solid transparent; color: #9aa3b2; font: inherit; cursor: pointer; }
.dev-tab.on { color: #7dd3fc; border-bottom-color: #7dd3fc; }
.dev-body { flex: 1; overflow: auto; -webkit-overflow-scrolling: touch; padding: 10px 12px 70px; }
.dev-sec { margin-bottom: 14px; }
.dev-sec h4 { margin: 0 0 6px; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: #7dd3fc; }
.dev-sec h5 { margin: 8px 0 4px; font-size: 12px; color: #9aa3b2; }
.dev-row { display: grid; grid-template-columns: 110px 1fr auto; gap: 6px; align-items: center; min-height: 44px; margin-bottom: 4px; }
.dev-row > span { color: #c7ccd6; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dev-row.dev-check { grid-template-columns: 44px 1fr; }
.dev-check input { width: 22px; height: 22px; margin: 0 auto; accent-color: #7dd3fc; }
.dev-in { min-height: 44px; background: #0f1114; border: 1px solid #3a3f4a; border-radius: 6px; color: #e6e6e6; font: inherit; padding: 0 10px; width: 100%; min-width: 0; }
.dev-btn { min-height: 44px; padding: 0 12px; background: #2a2f38; border: 1px solid #3a3f4a; border-radius: 6px; color: #e6e6e6; font: inherit; cursor: pointer; }
.dev-btn.ghost { background: none; }
.dev-btn.warn { border-color: #f59e0b; color: #fbbf24; }
.dev-btn.dim { opacity: .5; }
.dev-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.dev-list { display: grid; gap: 6px; }
.dev-list .dev-btn { text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dev-login { position: fixed; left: 50%; top: 20%; transform: translateX(-50%); z-index: 98; background: #1b1d22; border: 1px solid #3a3f4a; border-radius: 10px; padding: 16px; display: grid; gap: 8px; width: min(320px, calc(100% - 32px)); font-family: var(--font-mono); color: #e6e6e6; box-shadow: 0 10px 30px rgba(0,0,0,.6); margin: 0; }
.dev-login-title { font-size: 14px; font-weight: 700; }
.dev-login.shake { animation: devShake .3s ease; }
@keyframes devShake { 0%, 100% { transform: translateX(-50%); } 25% { transform: translateX(calc(-50% - 8px)); } 75% { transform: translateX(calc(-50% + 8px)); } }
.dev-login-row { display: flex; gap: 8px; }
.dev-login-row .dev-btn { flex: 1; }
@media (max-width: 760px) { #devPanel { width: 100%; } #devFab { right: 12px; bottom: 12px; } }
@media (prefers-reduced-motion: reduce) { #devPanel { transition: none; } .dev-login.shake { animation: none; } }
```

- [ ] **Step 4: Block `dev` anlegen**

Direkt vor `<script id="selftest">`:

```html
<script id="dev">
/* ================= ADMIN-PANEL – verstecktes Dev-Werkzeug (?dev + Login, sessionStorage) ================= */
const Dev = {
  active: false,
  KEY: 'keller37.dev',
  TAB_KEY: 'keller37.devTab',
  TABS: [['werte', 'Werte'], ['screens', 'Screens'], ['story', 'Story'], ['szenen', 'Szenen']],
  tab: 'werte',
  /* sessionStorage lesen (v undefined), schreiben (String) oder löschen (null) – privater Modus o. ä. wirft, dann gilt die Anmeldung nur bis zum Reload */
  ss(k, v) {
    try {
      if (v === undefined) return sessionStorage.getItem(k);
      if (v === null) sessionStorage.removeItem(k); else sessionStorage.setItem(k, v);
    } catch (e) { return null; }
    return v;
  },
  loggedIn() { return this.ss(this.KEY) === '1'; },
  init() { if (this.loggedIn()) this.mount(); else this.showLogin(); },
  showLogin() {
    if (qs('#devLogin')) return;
    const user = h('input', { id: 'devUser', class: 'dev-in', type: 'text', placeholder: 'Benutzer', autocomplete: 'off', autocapitalize: 'off' });
    const pass = h('input', { id: 'devPass', class: 'dev-in', type: 'password', placeholder: 'Passwort' });
    const box = h('form', { id: 'devLogin', class: 'dev-login', onsubmit: (e) => { e.preventDefault(); this.login(user.value, pass.value); } },
      h('div', { class: 'dev-login-title' }, '🛠 Admin'), user, pass,
      h('div', { class: 'dev-login-row' },
        h('button', { type: 'submit', class: 'dev-btn' }, 'Anmelden'),
        h('button', { type: 'button', class: 'dev-btn ghost', onclick: () => box.remove() }, 'Abbrechen')));
    document.body.appendChild(box);
    user.focus();
  },
  login(user, pass) {
    const box = qs('#devLogin');
    if (!DevRules.login(user, pass)) {
      if (box) { box.classList.remove('shake'); void box.offsetWidth; box.classList.add('shake'); qs('#devPass', box).value = ''; }
      return false;
    }
    this.ss(this.KEY, '1');
    if (box) box.remove();
    this.mount();
    return true;
  },
  logout() {
    this.ss(this.KEY, null);
    this.active = false;
    const fab = qs('#devFab'); if (fab) fab.remove();
    const panel = qs('#devPanel'); if (panel) panel.remove();
    UI.toast({ icon: '🛠', title: 'Abgemeldet' });
  },
  mount() {
    if (this.active) return;
    this.active = true;
    const saved = this.ss(this.TAB_KEY);
    this.tab = this.TABS.some(([id]) => id === saved) ? saved : 'werte';
    document.body.appendChild(h('button', { id: 'devFab', type: 'button', title: 'Admin-Panel', onclick: () => this.toggle() }, '🛠'));
    const panel = h('aside', { id: 'devPanel' },
      h('div', { class: 'dev-head' },
        h('strong', {}, '🛠 Admin'),
        h('button', { type: 'button', class: 'dev-btn ghost', onclick: () => this.logout() }, 'Abmelden'),
        h('button', { type: 'button', class: 'dev-btn ghost', onclick: () => this.toggle(false) }, '✕'),
        h('p', { id: 'devInfo', class: 'dev-info' })),
      h('div', { class: 'dev-tabs' }, this.TABS.map(([id, label]) => h('button', { type: 'button', class: 'dev-tab', 'data-tab': id, onclick: () => { this.tab = id; this.ss(this.TAB_KEY, id); this.render(); } }, label))),
      h('div', { id: 'devBody', class: 'dev-body' }));
    document.body.appendChild(panel);
    this.render();
  },
  toggle(on) {
    const p = qs('#devPanel'); if (!p) return;
    const open = on == null ? !p.classList.contains('open') : !!on;
    p.classList.toggle('open', open);
    if (open) this.render();
  },
  /* Reiter neu zeichnen – nur wenn das Panel offen ist (UI.show ruft das nach jedem Screen-Wechsel) */
  render() {
    if (!this.active) return;
    const panel = qs('#devPanel'); if (!panel || !panel.classList.contains('open')) return;
    qsa('.dev-tab', panel).forEach((b) => b.classList.toggle('on', b.dataset.tab === this.tab));
    qs('#devInfo', panel).textContent = `${State.mode === 'story' ? 'Story' : 'frei'} · ${UI.current ? UI.current.id : '–'} · ${UI.fmt(State.s.balance)}`;
    const body = qs('#devBody', panel); body.innerHTML = '';
    const fn = { werte: this.renderWerte, screens: this.renderScreens, story: this.renderStory, szenen: this.renderSzenen }[this.tab];
    try { body.appendChild(fn.call(this)); } catch (e) { console.error('[dev]', e); body.appendChild(h('p', { class: 'dev-info' }, `Fehler: ${e.message}`)); }
  },
  toast(text) { UI.toast({ icon: '🛠', title: text, ms: 2000 }); },
  /* nach Änderungen an State.s: speichern und alles neu zeichnen, was Werte zeigt */
  refreshGame() {
    State.save();
    UI.setBalance(State.s.balance); UI.renderWallet(); UI.renderSide();
    if (State.mode === 'story' && typeof Story !== 'undefined' && Story.story) Story.renderDaybar();
  },
  /* ---- Bausteine ---- */
  numRow(label, get, set, opts = {}) {
    const inp = h('input', { type: 'text', inputmode: 'numeric', class: 'dev-in', value: String(get()) });
    const apply = () => {
      const n = DevRules.parseNumber(inp.value, opts);
      if (n == null) { this.toast(`Ungültig: ${label}`); return; }
      set(n); this.toast(`${label} → ${n.toLocaleString('de-DE')}`); this.render();
    };
    inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); apply(); } });
    return h('label', { class: 'dev-row', title: label }, h('span', {}, label), inp, h('button', { type: 'button', class: 'dev-btn', onclick: apply }, 'Setzen'));
  },
  boolRow(label, get, set) {
    return h('label', { class: 'dev-row dev-check', title: label },
      h('input', { type: 'checkbox', checked: get() ? 'checked' : null, onchange: (e) => { set(e.target.checked); this.toast(`${label} → ${e.target.checked ? 'an' : 'aus'}`); } }),
      h('span', {}, label));
  },
  /* options: [[value, label], …]; value '' steht für „keins" (null) */
  selectRow(label, options, get, set) {
    const cur = get(); const curVal = cur == null ? '' : String(cur);
    const sel = h('select', { class: 'dev-in', onchange: (e) => { set(e.target.value === '' ? null : e.target.value); this.toast(`${label} → ${e.target.value || 'keins'}`); } },
      options.map(([v, l]) => h('option', { value: v, selected: String(v) === curVal ? 'selected' : null }, l)));
    return h('label', { class: 'dev-row', title: label }, h('span', {}, label), sel);
  },
  btn(label, fn, cls = '') { return h('button', { type: 'button', class: `dev-btn ${cls}`.trim(), onclick: fn }, label); },
  sec(title, ...kids) { return h('section', { class: 'dev-sec' }, h('h4', {}, title), ...kids); },
  /* ---- Reiter (werden in den Folge-Tasks gefüllt) ---- */
  renderWerte() { return h('div', {}); },
  renderScreens() { return h('div', {}); },
  renderStory() { return h('div', {}); },
  renderSzenen() { return h('div', {}); },
};
</script>

```

- [ ] **Step 5: `UI.show` und Boot anbinden**

Im Block `ui`, Methode `async show(id)`: die letzte Zeile `this.busy = false;` ersetzen durch:

```js
    this.busy = false;
    if (typeof Dev !== 'undefined' && Dev.active) Dev.render(); // Admin-Panel: Kopfzeile/Reiter nach Screen-Wechsel aktualisieren
```

Im Block `boot`, direkt nach `UI.mountShell();` (vor dem `if (discarded) …`):

```js
  if (typeof Dev !== 'undefined' && (params.has('dev') || Dev.loggedIn())) Dev.init(); // Admin-Panel: ?dev zeigt das Login, angemeldet bleibt es bis Tab-Schluss
```

`skipTitle` bleibt unverändert (kein `dev`).

- [ ] **Step 6: Tests**

Run: `python3 tests/playtest-dev.py`
Expected: alle `OK`, `FAILS 0`.

Run: `node tests/run-selftest.mjs && sh tests/dom-selftest.sh`
Expected: grün.

Run: `python3 tests/desktop-diff.py`
Expected: alle Screens 0 px (ohne `?dev` kein DOM).

- [ ] **Step 7: Commit**

```bash
git add keller37.html tests/playtest-dev.py
git commit -m "feat(dev): Admin-Panel-Gerüst – ?dev-Login, Knopf, Schublade mit vier Reitern, Playtest

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Reiter „Werte"

**Files:**
- Modify: `keller37.html` – Block `dev` (`renderWerte`), `tests/playtest-dev.py` (neues Szenario).

**Interfaces:**
- Consumes: `Dev.numRow/boolRow/selectRow/btn/sec/refreshGame/toast` (Task 3), `DevRules.parseNumber` (Task 1), `Rules.GEAR.cars/shoes`, `Rules.XP_LEVELS`, `Rules.INSIDER`, `Achievements.DEFS`, `State.KEY/STORY_KEY/META_KEY`, `Perks.refreshExcluded(true)`.

- [ ] **Step 1: Szenario schreiben (schlägt fehl)**

In `tests/playtest-dev.py` nach `scenario_login` einfügen und in `main()` nach `await scenario_login(cdp)` aufrufen:

```python
async def scenario_werte(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await login(cdp)
    await open_tab(cdp, "werte")
    rows = await cdp.eval("[...document.querySelectorAll('#devBody .dev-row')].map(r => r.title)", await_promise=False) or []
    record("werte: Felder für Kontostand, XP, Stärke, Waffe, Auto, Royal-Gast", all(x in rows for x in ["Kontostand", "XP", "Stärke", "Waffenstufe", "Auto", "Royal-Gast"]), rows)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Kontostand'); r.querySelector('input').value = '5.000'; r.querySelector('button').click(); })()", await_promise=False)
    await cdp.wait_for("State.s.balance === 5000", timeout=1.0)
    bal = await cdp.eval("({ s: State.s.balance, saved: JSON.parse(localStorage.getItem('keller37.state')).balance })", await_promise=False) or {}
    await asyncio.sleep(1.2)  # Money-Counter tweent
    shown = await cdp.eval("document.querySelector('#balance').textContent", await_promise=False)
    record("werte: Kontostand 5.000 gesetzt, gespeichert, Wallet zeigt ihn", bal.get("s") == 5000 and bal.get("saved") == 5000 and "5.000" in (shown or ""), (bal, shown))
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Waffenstufe'); r.querySelector('input').value = '7'; r.querySelector('button').click(); })()", await_promise=False)
    await asyncio.sleep(0.1)
    w = await cdp.eval("State.s.weapon", await_promise=False)
    record("werte: Waffenstufe 7 abgelehnt (max 3)", w == 0, w)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Royal-Gast'); r.querySelector('input').click(); })()", await_promise=False)
    await asyncio.sleep(0.1)
    guest = await cdp.eval("State.s.flags.royalGuest === true", await_promise=False)
    record("werte: Royal-Gast per Schalter", guest is True)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Auto'); const s = r.querySelector('select'); s.value = 'audiA3'; s.dispatchEvent(new Event('change')); })()", await_promise=False)
    await asyncio.sleep(0.1)
    car = await cdp.eval("State.s.car", await_promise=False)
    record("werte: Auto per Auswahl", car == "audiA3", car)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'Alle Achievements').click()", await_promise=False)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'Alle Insider-Skills').click()", await_promise=False)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'Level max').click()", await_promise=False)
    await asyncio.sleep(0.1)
    all_ = await cdp.eval("({ ach: State.meta.achievements.length === Achievements.DEFS.length, ins: State.meta.insider.length === Rules.INSIDER.length, xp: State.s.xp === Rules.XP_LEVELS[Rules.XP_LEVELS.length - 1] })", await_promise=False) or {}
    record("werte: Alle Achievements / Insider / Level max", all_.get("ach") and all_.get("ins") and all_.get("xp"), all_)
    await cdp.screenshot("dev-werte.png")
```

- [ ] **Step 2: Laufen lassen – muss fehlschlagen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAIL werte: Felder …`.

- [ ] **Step 3: `renderWerte` implementieren**

Im Block `dev` die Zeile `renderWerte() { return h('div', {}); },` ersetzen durch:

```js
  renderWerte() {
    const s = State.s;
    const W = h('div', {});
    const num = (label, key, opts) => this.numRow(label, () => s[key] || 0, (n) => { s[key] = n; this.refreshGame(); }, opts);
    W.append(this.sec('Zahlen',
      num('Kontostand', 'balance', { min: -1e9, max: 1e9 }),
      num('XP', 'xp', { min: 0, max: 1e6 }),
      num('Stärke', 'strength', { min: 0, max: 99 }),
      num('Bier-Pegel', 'beers', { min: 0, max: 9 }),
      num('Bankschulden', 'bankDebt', { min: 0, max: 1e9 }),
      num('Mafiaschulden', 'mafiaDebt', { min: 0, max: 1e9 }),
      num('Waffenstufe', 'weapon', { min: 0, max: 3 })));
    const flag = (label, key) => this.boolRow(label, () => !!s.flags[key], (v) => { s.flags[key] = v; this.refreshGame(); });
    const bool = (label, key) => this.boolRow(label, () => !!s[key], (v) => { s[key] = v; this.refreshGame(); });
    W.append(this.sec('Schalter',
      flag('Royal-Gast', 'royalGuest'), flag('Igor', 'igor'), flag('Brownie', 'brownie'),
      bool('Haus', 'hasHouse'), bool('Verheiratet', 'isMarried'), bool('Dealer', 'hasDealer'), bool('Niere verkauft', 'kidneySold')));
    const opts = (obj) => [['', 'keins'], ...Object.entries(obj).map(([k, v]) => [k, v.name || k])];
    W.append(this.sec('Ausrüstung',
      this.selectRow('Auto', opts(Rules.GEAR.cars), () => s.car, (v) => { s.car = v; this.refreshGame(); }),
      this.selectRow('Schuhe', opts(Rules.GEAR.shoes), () => s.shoes, (v) => { s.shoes = v; this.refreshGame(); })));
    const reload = (q) => { location.href = location.pathname + q; };
    W.append(this.sec('Knöpfe', h('div', { class: 'dev-list' },
      this.btn('Alle Achievements', () => { State.meta.achievements = Achievements.DEFS.map((d) => d.id); State.saveMeta(); this.toast('Alle Trophäen'); }),
      this.btn('Alle Insider-Skills', () => { State.meta.insider = Rules.INSIDER.map((i) => i.id); State.saveMeta(); if (typeof Perks !== 'undefined') Perks.refreshExcluded(true); this.refreshGame(); this.toast('Alle Insider'); }),
      this.btn('Level max', () => { s.xp = Rules.XP_LEVELS[Rules.XP_LEVELS.length - 1]; this.refreshGame(); this.toast('Level max'); }),
      this.btn('Spielstand löschen (frei) ⟲', () => { try { State.storage.removeItem(State.KEY); } catch (e) { /* egal */ } reload('?dev&mode=free'); }, 'warn'),
      this.btn('Alles löschen ⟲', () => { try { State.storage.removeItem(State.KEY); State.storage.removeItem(State.STORY_KEY); State.storage.removeItem(State.META_KEY); } catch (e) { /* egal */ } reload('?dev'); }, 'warn'))));
    return W;
  },
```

- [ ] **Step 4: Laufen lassen – muss bestehen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAILS 0`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/playtest-dev.py
git commit -m "feat(dev): Reiter Werte – Zahlen, Schalter, Ausrüstung, Sammel-Knöpfe

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Reiter „Screens"

**Files:**
- Modify: `keller37.html` – Block `dev` (`renderScreens`, `showScreen`), `tests/playtest-dev.py`.

**Interfaces:**
- Consumes: `DevRules.groupScreens` (Task 1), `UI.screens`, `UI.show`, `UI.mobile()`, `Stadt.SHOPS`/`Stadt.shop`, `Shootout.pending` (wird beim Mount des Screens `shootout` konsumiert), `GangRules.FOES`, `GangRules.weapon(s).bonus`, `Mugging.force`, `Story.isLocked/DOORS/ROOM_OF/allowOnce`.
- Produces: `Dev.showScreen(id) → Promise`.

- [ ] **Step 1: Szenario schreiben (schlägt fehl)**

In `tests/playtest-dev.py` nach `scenario_werte` einfügen und in `main()` aufrufen:

```python
async def scenario_screens(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await login(cdp)
    await open_tab(cdp, "screens")
    secs = await cdp.eval("[...document.querySelectorAll('#devBody .dev-sec h4')].map(h => h.textContent)", await_promise=False) or []
    record("screens: Gruppen Keller, Casino Royal, Stadt, Story, Schießerei, Überfall", all(any(x in s for s in secs) for x in ["Keller", "Casino Royal", "Stadt", "Story", "Schießerei", "Überfall"]), secs)
    n = await cdp.eval("document.querySelectorAll('#devBody .dev-btn').length", await_promise=False)
    total = await cdp.eval("UI.screens.size", await_promise=False)
    record("screens: mindestens ein Knopf pro registriertem Screen", (n or 0) >= (total or 99), (n, total))
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'craps').click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'craps' && !UI.busy", timeout=4.0)
    zone = await cdp.eval("document.body.dataset.zone", await_promise=False)
    still_open = await cdp.eval("document.querySelector('#devPanel').classList.contains('open')", await_promise=False)
    info = await cdp.eval("document.querySelector('#devInfo').textContent", await_promise=False)
    record("screens: craps öffnet mit Zone royal; Panel bleibt am Desktop offen, Kopfzeile aktuell", zone == "royal" and still_open is True and "craps" in (info or ""), (zone, still_open, info))
    await cdp.screenshot("dev-screens.png")
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent.endsWith(' merc')).click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=4.0)
    shop = await cdp.eval("Stadt.shop", await_promise=False)
    record("screens: Laden merc direkt", shop == "merc", shop)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'kessler').click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'shootout' && !UI.busy", timeout=4.0)
    foe = await cdp.eval("({ screen: document.body.dataset.screen, pending: Shootout.pending })", await_promise=False) or {}
    record("screens: Schießerei öffnet, pending konsumiert", foe.get("screen") == "shootout" and foe.get("pending") is None, foe)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'junkie').click()", await_promise=False)
    force = await cdp.eval("Mugging.force", await_promise=False)
    record("screens: Überfall junkie vorgemerkt", force == "junkie", force)
    # Story: gesperrte Tür wird beim Klick freigeschaltet
    await cdp.navigate(URL + "?fresh&story=schuld&day=1&dev", wait=2.0)
    await cdp.inject_helpers()
    await cdp.advance_cutscene()
    await login(cdp)
    await open_tab(cdp, "screens")
    locked_before = await cdp.eval("Story.isLocked('roulette')", await_promise=False)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'roulette').click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'roulette' && !UI.busy", timeout=4.0)
    unlocked = await cdp.eval("State.s.story.unlocked.doors.includes('roulette')", await_promise=False)
    record("screens: gesperrte Story-Tür wird beim Sprung freigeschaltet", locked_before is True and unlocked is True, (locked_before, unlocked))
```

- [ ] **Step 2: Laufen lassen – muss fehlschlagen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAIL screens: Gruppen …`.

- [ ] **Step 3: `renderScreens` und `showScreen` implementieren**

Im Block `dev` die Zeile `renderScreens() { return h('div', {}); },` ersetzen durch:

```js
  renderScreens() {
    const W = h('div', {});
    const g = DevRules.groupScreens([...UI.screens.keys()]);
    const inStory = State.mode === 'story';
    const grid = (ids, dimIf = () => false) => h('div', { class: 'dev-grid' }, ids.map((id) => this.btn(id, () => this.showScreen(id), dimIf(id) ? 'dim' : '')));
    W.append(this.sec('Keller', grid(g.keller)));
    W.append(this.sec('Casino Royal', grid(g.royal)));
    if (typeof Stadt !== 'undefined') {
      W.append(this.sec('Stadt', h('div', { class: 'dev-grid' },
        this.btn('stadt', () => { Stadt.shop = null; this.showScreen('stadt'); }),
        Object.entries(Stadt.SHOPS).map(([id, sh]) => this.btn(`${sh.icon} ${id}`, () => { Stadt.shop = id; this.showScreen('stadt'); })))));
    }
    W.append(this.sec('Story', grid(g.story, () => !inStory)));
    if (g.sonst.length) W.append(this.sec('Sonstiges', grid(g.sonst)));
    if (typeof Shootout !== 'undefined' && typeof GangRules !== 'undefined') {
      W.append(this.sec('Schießerei', h('div', { class: 'dev-grid' }, Object.keys(GangRules.FOES).map((foe) => this.btn(foe, () => {
        Shootout.pending = { kind: 'dev', foes: [foe], bonus: GangRules.weapon(State.s).bonus }; // der Screen konsumiert pending beim Mount
        this.showScreen('shootout');
      })))));
    }
    if (typeof Mugging !== 'undefined') {
      W.append(this.sec('Überfall (nächster Spin)', h('div', { class: 'dev-grid' },
        [['zufällig', true], ['junkie', 'junkie'], ['jugend', 'jugend'], ['cousin', 'cousin']].map(([label, v]) => this.btn(label, () => { Mugging.force = v; this.toast(`Nächster Spin: Überfall (${label})`); })))));
    }
    return W;
  },
  /* Screen öffnen; in der Story gesperrte Türen/Räume vorher freischalten, Gates einmal durchlassen. Auf dem Handy schließt sich das Panel. */
  async showScreen(id) {
    if (State.mode === 'story' && typeof Story !== 'undefined' && Story.story && Story.s && Story.isLocked(id)) {
      const st = Story.s;
      if (Story.DOORS.includes(id) && !st.unlocked.doors.includes(id)) st.unlocked.doors.push(id);
      for (const r of Story.ROOM_OF[id] || []) if (!st.unlocked.rooms.includes(r)) st.unlocked.rooms.push(r);
      Story.allowOnce = id;
      State.save();
      this.toast(`${id} freigeschaltet`);
    }
    if (UI.mobile()) this.toggle(false);
    await UI.show(id);
  },
```

Hinweis: `Story.isLocked(id)` konsumiert `allowOnce`, wenn es gleich `id` ist – deshalb wird `allowOnce` erst **nach** der Prüfung gesetzt.

- [ ] **Step 4: Laufen lassen – muss bestehen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAILS 0`. Falls „Schießerei"-Check scheitert, weil `shootout` in der Story-Sperre hängt: Szenario läuft im freien Modus, `UI.show('shootout')` ist dort erlaubt – dann den Selektor prüfen, nicht die Engine ändern.

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/playtest-dev.py
git commit -m "feat(dev): Reiter Screens – alle Screens, Läden, Schießerei, Überfall; Story-Sperren beim Sprung lösen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Reiter „Story"

**Files:**
- Modify: `keller37.html` – Block `dev` (`renderStory`, `startStory`, `refreshStory`), `tests/playtest-dev.py`.

**Interfaces:**
- Consumes: `Modes.enter(choice, opts)` und `Jobs.take(id, { force })` (Task 2), `DevRules.flagNamesIn/parseNumber` (Task 1), `Stories.all/get`, `Story.story/s/finish/renderDaybar/DOORS/ROOM_OF`, `Jobs.POOL`, `State.STORY_KEY`.
- Produces: `Dev.startStory(id, prev, dayRaw, weaponRaw) → Promise`, `Dev.refreshStory()`.

- [ ] **Step 1: Szenario schreiben (schlägt fehl)**

In `tests/playtest-dev.py` nach `scenario_screens` einfügen und in `main()` aufrufen:

```python
async def scenario_story(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await cdp.inject_helpers()
    await login(cdp)
    await open_tab(cdp, "story")
    head = await cdp.eval("document.querySelector('#devBody .dev-info') && document.querySelector('#devBody .dev-info').textContent", await_promise=False)
    record("story: ohne Story steht 'Keine Story aktiv'", "Keine Story" in (head or ""), head)
    # Kater ab Tag 5 mit vorigem Ende doc starten
    await cdp.eval("(function(){ const sel = document.querySelector('#devStorySel'); sel.value = 'kater'; sel.dispatchEvent(new Event('change')); const prev = document.querySelector('#devPrevSel'); prev.value = 'doc'; document.querySelector('#devDayIn').value = '5'; document.querySelector('#devStartBtn').click(); })()", await_promise=False)
    await cdp.wait_for("State.mode === 'story' && State.s.story && State.s.story.id === 'kater' && UI.current && !UI.busy && !Cutscene.active", timeout=8.0)
    st = await cdp.eval("({ id: State.s.story.id, day: State.s.story.day, prev: State.s.story.prev.schuld, leber: !!document.querySelector('.hud-leber') })", await_promise=False) or {}
    record("story: Kater ab Tag 5, prev=doc, Leber-HUD sichtbar", st.get("id") == "kater" and st.get("day") == 5 and st.get("prev") == "doc" and st.get("leber"), st)
    await open_tab(cdp, "story")
    await cdp.screenshot("dev-story.png")
    rows = await cdp.eval("[...document.querySelectorAll('#devBody .dev-row')].map(r => r.title)", await_promise=False) or []
    record("story: Vars (pegel, leber) und Flags (abgestuerzt, zitter) als Felder", all(x in rows for x in ["pegel", "leber", "abgestuerzt", "zitter"]), rows[:30])
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'leber'); r.querySelector('input').value = '40'; r.querySelector('button').click(); })()", await_promise=False)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'abgestuerzt'); r.querySelector('input').click(); })()", await_promise=False)
    await asyncio.sleep(0.2)
    v = await cdp.eval("({ leber: State.s.story.vars.leber, ab: State.s.story.flags.abgestuerzt, saved: JSON.parse(localStorage.getItem('keller37.story')).story.vars.leber, hud: document.querySelector('.hud-leber .val') && document.querySelector('.hud-leber .val').textContent })", await_promise=False) or {}
    record("story: leber=40 und abgestuerzt=true gesetzt, gespeichert, HUD aktuell", v.get("leber") == 40 and v.get("ab") is True and v.get("saved") == 40 and "40" in (v.get("hud") or ""), v)
    # Tag/Phase
    await cdp.eval("(function(){ document.querySelector('#devDaySet').value = '12'; document.querySelector('#devPhaseSel').value = 'evening'; document.querySelector('#devDayBtn').click(); })()", await_promise=False)
    await cdp.wait_for("State.s.story.day === 12 && State.s.story.phase === 'evening' && UI.current && UI.current.id === 'hub' && !UI.busy", timeout=8.0)
    d = await cdp.eval("({ day: State.s.story.day, phase: State.s.story.phase, screen: UI.current.id })", await_promise=False) or {}
    record("story: Tag 12 abends → Hub", d.get("day") == 12 and d.get("phase") == "evening" and d.get("screen") == "hub", d)
    # Job erzwingen (taxi braucht 200 € Kaution – force)
    await cdp.eval("State.s.balance = 0; State.save();", await_promise=False)
    await open_tab(cdp, "story")
    await cdp.eval("(function(){ document.querySelector('#devJobSel').value = 'taxi'; document.querySelector('#devJobBtn').click(); })()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'job-taxi' && !UI.busy", timeout=6.0)
    j = await cdp.eval("({ screen: UI.current.id, unlocked: State.s.story.unlocked.jobs.includes('taxi'), phase: State.s.story.phase })", await_promise=False) or {}
    record("story: Job taxi trotz fehlender Kaution gestartet", j.get("screen") == "job-taxi" and j.get("unlocked") and j.get("phase") == "morning", j)
    # Freischalten: Raum royal
    await open_tab(cdp, "story")
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'raum:royal'); r.querySelector('input').click(); })()", await_promise=False)
    await asyncio.sleep(0.1)
    room = await cdp.eval("State.s.story.unlocked.rooms.includes('royal')", await_promise=False)
    record("story: Raum royal freigeschaltet", room is True, room)
    # Ende abspielen
    await cdp.eval("(function(){ document.querySelector('#devEndSel').value = 'wirt'; document.querySelector('#devEndBtn').click(); })()", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene(max_steps=40)
    ended = await cdp.eval("(function(){ const p = JSON.parse(localStorage.getItem('keller37.story') || 'null'); const run = JSON.parse(localStorage.getItem('keller37.meta')).storyRuns.kater; return { ended: !!(p && p.story && p.story.ended) || !!(run && run.endings.includes('wirt')), endScreen: !!document.querySelector('.cs-choices, .ending, #cutscene') }; })()", await_promise=False) or {}
    record("story: Ende wirt abgespielt", ended.get("ended") is True, ended)
```

- [ ] **Step 2: Laufen lassen – muss fehlschlagen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAIL story: ohne Story …`.

- [ ] **Step 3: `renderStory`, `startStory`, `refreshStory` implementieren**

Im Block `dev` die Zeile `renderStory() { return h('div', {}); },` ersetzen durch:

```js
  renderStory() {
    const W = h('div', {});
    const stories = Object.values(Stories.all);
    const running = State.mode === 'story' && typeof Story !== 'undefined' && Story.story && Story.s && !Story.s.ended;
    W.append(h('p', { class: 'dev-info' }, running
      ? `${Story.story.title} · Tag ${Story.s.day} · ${Story.s.phase === 'morning' ? 'morgens' : 'abends'} · vorher: ${Object.entries(Story.s.prev || {}).map(([k, v]) => `${k}=${v}`).join(', ') || '–'}`
      : 'Keine Story aktiv'));
    /* Starten */
    const selStory = h('select', { id: 'devStorySel', class: 'dev-in' }, stories.map((st) => h('option', { value: st.id }, `${st.title || st.id}${st.dev ? ' (dev)' : ''}`)));
    const selPrev = h('select', { id: 'devPrevSel', class: 'dev-in' });
    const fillPrev = () => {
      const st = Stories.get(selStory.value);
      const req = st && st.requires ? Stories.get(st.requires) : null;
      selPrev.innerHTML = ''; selPrev.disabled = !req;
      selPrev.append(h('option', { value: '' }, req ? `voriges Ende von „${req.title}"` : '– keine Voraussetzung –'));
      if (req) req.endings.forEach((e) => selPrev.append(h('option', { value: e.id }, e.id)));
    };
    selStory.addEventListener('change', fillPrev); fillPrev();
    const dayIn = h('input', { id: 'devDayIn', type: 'text', inputmode: 'numeric', class: 'dev-in', value: '1' });
    const weaponIn = h('input', { id: 'devWeaponIn', type: 'text', inputmode: 'numeric', class: 'dev-in', value: String(State.s.weapon || 0) });
    W.append(this.sec('Story starten ⟲',
      h('label', { class: 'dev-row', title: 'Story' }, h('span', {}, 'Story'), selStory),
      h('label', { class: 'dev-row', title: 'Vorher' }, h('span', {}, 'Vorher'), selPrev),
      h('label', { class: 'dev-row', title: 'Starttag' }, h('span', {}, 'Starttag (1 = mit Intro)'), dayIn),
      h('label', { class: 'dev-row', title: 'Waffe' }, h('span', {}, 'Waffe (0–3)'), weaponIn),
      h('button', { id: 'devStartBtn', type: 'button', class: 'dev-btn warn', onclick: () => this.startStory(selStory.value, selPrev.value || null, dayIn.value, weaponIn.value) }, 'Story starten ⟲')));
    if (!running) return W;
    const st = Story.s; const story = Story.story;
    /* Vars */
    W.append(this.sec('Vars', Object.keys(st.vars).map((k) => this.numRow(k, () => st.vars[k] || 0, (n) => { st.vars[k] = n; this.refreshStory(); }, { min: -1e9, max: 1e9 }))));
    /* Flags: gesetzte + alle, die in der Story vorkommen */
    const names = [...new Set([...Object.keys(st.flags), ...DevRules.flagNamesIn(story)])].sort();
    W.append(this.sec('Flags', names.map((k) => this.boolRow(k, () => !!st.flags[k], (v) => { st.flags[k] = v; this.refreshStory(); }))));
    /* Tag/Phase */
    const daySet = h('input', { id: 'devDaySet', type: 'text', inputmode: 'numeric', class: 'dev-in', value: String(st.day) });
    const phaseSel = h('select', { id: 'devPhaseSel', class: 'dev-in' },
      h('option', { value: 'morning', selected: st.phase === 'morning' ? 'selected' : null }, 'morgens'),
      h('option', { value: 'evening', selected: st.phase === 'evening' ? 'selected' : null }, 'abends'));
    W.append(this.sec('Tag / Phase',
      h('label', { class: 'dev-row', title: 'Tag' }, h('span', {}, 'Tag'), daySet, phaseSel),
      h('button', { id: 'devDayBtn', type: 'button', class: 'dev-btn', onclick: async () => {
        const d = DevRules.parseNumber(daySet.value, { min: 1, max: story.days || 999 });
        if (d == null) { this.toast('Ungültig: Tag'); return; }
        st.day = d; st.phase = phaseSel.value; st.jobToday = null; State.save();
        this.toast(`Tag ${d}, ${phaseSel.value === 'morning' ? 'morgens' : 'abends'}`);
        if (UI.mobile()) this.toggle(false);
        await Modes.enter('story'); // bestehender Fortsetzungspfad: setup → applyChapter → morning/evening
        this.render();
      } }, 'Setzen & fortsetzen')));
    /* Job */
    const jobs = typeof Jobs !== 'undefined' ? Object.values(Jobs.POOL) : [];
    const selJob = h('select', { id: 'devJobSel', class: 'dev-in' }, jobs.map((j) => h('option', { value: j.id }, `${j.icon} ${j.name} (${j.id})`)));
    W.append(this.sec('Job starten',
      h('label', { class: 'dev-row', title: 'Job' }, h('span', {}, 'Job'), selJob),
      h('button', { id: 'devJobBtn', type: 'button', class: 'dev-btn', onclick: async () => {
        const id = selJob.value; const job = Jobs.POOL[id];
        if (!st.unlocked.jobs.includes(id)) st.unlocked.jobs.push(id);
        st.phase = 'morning'; st.jobToday = null; State.save(); Story.renderDaybar();
        this.toast(job && job.requires ? `Job ${id} (Voraussetzung übergangen)` : `Job ${id}`);
        if (UI.mobile()) this.toggle(false);
        await Jobs.take(id, { force: true });
      } }, 'Starten')));
    /* Ende */
    const selEnd = h('select', { id: 'devEndSel', class: 'dev-in' }, story.endings.map((e) => h('option', { value: e.id }, e.id)));
    W.append(this.sec('Ende abspielen',
      h('label', { class: 'dev-row', title: 'Ende' }, h('span', {}, 'Ende'), selEnd),
      h('button', { id: 'devEndBtn', type: 'button', class: 'dev-btn warn', onclick: async () => {
        const end = story.endings.find((e) => e.id === selEnd.value); if (!end) return;
        this.toggle(false);
        await Story.finish(end);
      } }, 'Abspielen')));
    /* Freischalten */
    const rooms = [...new Set(Object.values(Story.ROOM_OF).flat())];
    const unl = (list, id) => (v) => {
      const i = list.indexOf(id);
      if (v && i < 0) list.push(id); if (!v && i >= 0) list.splice(i, 1);
      State.save(); UI.renderSide();
      if (UI.current && UI.current.id === 'hub') UI.show('hub'); // Türen im Gang neu zeichnen
    };
    W.append(this.sec('Freischalten',
      h('h5', {}, 'Türen'), Story.DOORS.map((d) => this.boolRow(`tuer:${d}`, () => st.unlocked.doors.includes(d), unl(st.unlocked.doors, d))),
      h('h5', {}, 'Räume'), rooms.map((r) => this.boolRow(`raum:${r}`, () => st.unlocked.rooms.includes(r), unl(st.unlocked.rooms, r))),
      h('h5', {}, 'Jobs'), jobs.map((j) => this.boolRow(`job:${j.id}`, () => st.unlocked.jobs.includes(j.id), unl(st.unlocked.jobs, j.id)))));
    return W;
  },
  refreshStory() { State.save(); Story.renderDaybar(); UI.renderWallet(); UI.renderSide(); },
  /* Story neu starten: Story-Spielstand löschen, dann derselbe Pfad wie ?fresh&story=…&prev=…&day=…&weapon=… */
  async startStory(id, prev, dayRaw, weaponRaw) {
    const story = Stories.get(id); if (!story) return;
    const day = DevRules.parseNumber(dayRaw, { min: 1, max: story.days || 999 });
    const weapon = DevRules.parseNumber(weaponRaw, { min: 0, max: 3 });
    if (day == null || weapon == null) { this.toast('Ungültig: Tag/Waffe'); return; }
    try { State.storage.removeItem(State.STORY_KEY); } catch (e) { /* egal */ }
    if (typeof Story !== 'undefined') Story.forcedNext = null;
    this.toggle(false);
    this.toast(`${story.title} ab Tag ${day}`);
    await Modes.enter('newstory', { fresh: true, story: id, prev, day: day > 1 ? day : null, weapon, ending: null, job: null });
    this.render();
  },
```

`boolRow`-Labels für Freischalten tragen Präfixe (`tuer:`, `raum:`, `job:`), damit die `title`-Attribute eindeutig bleiben (`roulette` ist sonst Tür **und** Screen-Knopf).

- [ ] **Step 4: Laufen lassen – muss bestehen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAILS 0`. Falls „Ende wirt" scheitert: prüfen, ob `Story.finish` die Ende-Szene per Cutscene abspielt (dann `advance_cutscene` länger laufen lassen) – nicht das Ende-Kriterium aufweichen.

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/playtest-dev.py
git commit -m "feat(dev): Reiter Story – Start mit Vorgeschichte/Tag/Waffe, Vars, Flags, Tag/Phase, Job, Ende, Freischalten

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Reiter „Szenen"

**Files:**
- Modify: `keller37.html` – Block `dev` (`renderSzenen`, `previewCtx`, `preview`), `tests/playtest-dev.py`.

**Interfaces:**
- Consumes: `DevRules.sceneGroups` (Task 1), `Cutscene.SCENES/active/play`, `Stories.all`, `Story.ctx()`, `Story.finish`.
- Produces: `Dev.preview(id) → Promise`, `Dev.previewCtx() → object`, `Dev.sceneQuery` (String, letzter Suchtext).

- [ ] **Step 1: Szenario schreiben (schlägt fehl)**

In `tests/playtest-dev.py` nach `scenario_story` einfügen und in `main()` aufrufen:

```python
async def scenario_szenen(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await cdp.inject_helpers()
    await login(cdp)
    await open_tab(cdp, "szenen")
    groups = await cdp.eval("[...document.querySelectorAll('#devBody .dev-sec h4')].map(h => h.textContent)", await_promise=False) or []
    n = await cdp.eval("document.querySelectorAll('#devBody .dev-list .dev-btn').length", await_promise=False)
    total = await cdp.eval("Object.keys(Cutscene.SCENES).length", await_promise=False)
    record("szenen: Gruppen Keller + Storys, ein Knopf je Szene", groups[:1] == ["Keller"] and any("Kater" in g for g in groups) and n == total, (groups, n, total))
    await cdp.eval("(function(){ const s = document.querySelector('#devSceneSearch'); s.value = 'kater.k'; s.dispatchEvent(new Event('input')); })()", await_promise=False)
    await asyncio.sleep(0.1)
    ids = await cdp.eval("[...document.querySelectorAll('#devBody .dev-list .dev-btn')].map(b => b.textContent)", await_promise=False) or []
    record("szenen: Suche filtert", ids and all("kater.k" in i for i in ids), ids)
    await cdp.screenshot("dev-szenen.png")
    # Vorschau einer Story-Szene mit Entscheidung: Spielstand bleibt unverändert
    before = await cdp.eval("JSON.stringify([State.s.balance, State.s.flags, localStorage.getItem('keller37.state')])", await_promise=False)
    await cdp.eval("(function(){ const s = document.querySelector('#devSceneSearch'); s.value = 'schuld.intro'; s.dispatchEvent(new Event('input')); })()", await_promise=False)
    await asyncio.sleep(0.1)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-list .dev-btn')].find(b => b.textContent === 'schuld.intro').click()", await_promise=False)
    await asyncio.sleep(0.5)
    active = await cdp.eval("Cutscene.active && !document.querySelector('#devPanel').classList.contains('open')", await_promise=False)
    record("szenen: Vorschau läuft, Panel zu", active is True, active)
    await cdp.advance_cutscene(max_steps=40)
    after = await cdp.eval("JSON.stringify([State.s.balance, State.s.flags, localStorage.getItem('keller37.state')])", await_promise=False)
    mode = await cdp.eval("State.mode", await_promise=False)
    record("szenen: Vorschau ändert Spielstand nicht (frei bleibt frei)", before == after and mode == "free", (before, after, mode))
    # Platzhalter bleiben sichtbar, wenn der Kontext sie nicht kennt (Tippfehler fallen auf)
    await cdp.eval("Cutscene.define('dev.probe', [{ bg: 'bar', who: 'wirt', mood: 'calm', text: 'Kontostand {{balance}}, unbekannt {{gibtsnicht}}' }]); Dev.preview('dev.probe');", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.eval("__pt.advance()", await_promise=False)  # erster Klick beendet die Tipp-Animation, Text steht komplett
    await asyncio.sleep(0.2)
    txt = await cdp.eval("document.querySelector('#cutscene .cs-text') && document.querySelector('#cutscene .cs-text').textContent", await_promise=False)
    record("szenen: bekannte Platzhalter gefüllt, unbekannte sichtbar", "€" in (txt or "") and "{{gibtsnicht}}" in (txt or ""), txt)
    await cdp.advance_cutscene(max_steps=5)
```

Der Text wird per Tipp-Animation aufgebaut; der erste `__pt.advance()` schreibt ihn komplett (Engine-Verhalten `typing = false … els.text.textContent = full`), erst der zweite Klick blättert weiter.

- [ ] **Step 2: Laufen lassen – muss fehlschlagen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAIL szenen: Gruppen …`.

- [ ] **Step 3: `renderSzenen`, `previewCtx`, `preview` implementieren**

Im Block `dev` die Zeile `renderSzenen() { return h('div', {}); },` ersetzen durch:

```js
  sceneQuery: '',
  renderSzenen() {
    const W = h('div', {});
    const search = h('input', { id: 'devSceneSearch', type: 'search', class: 'dev-in', placeholder: 'Szene suchen …', value: this.sceneQuery });
    const list = h('div', {});
    const running = State.mode === 'story' && typeof Story !== 'undefined' && Story.story && Story.s && !Story.s.ended;
    const build = () => {
      list.innerHTML = '';
      const q = (this.sceneQuery = search.value.trim().toLowerCase());
      const ids = Object.keys(Cutscene.SCENES).filter((id) => !q || id.toLowerCase().includes(q));
      for (const g of DevRules.sceneGroups(ids, Stories.all)) {
        const kids = g.ids.map((id) => this.btn(id, () => this.preview(id), Cutscene.active ? 'dim' : ''));
        const st = g.id ? Stories.get(g.id) : null;
        if (st && running && Story.story.id === st.id) {
          for (const end of st.endings) if (!q || `ende: ${end.id}`.includes(q)) kids.push(this.btn(`Ende: ${end.id}`, async () => { this.toggle(false); await Story.finish(end); }, 'warn'));
        }
        if (kids.length) list.append(this.sec(g.title, h('div', { class: 'dev-list' }, kids)));
      }
    };
    search.addEventListener('input', build); build();
    W.append(h('div', { class: 'dev-sec' }, search), list);
    return W;
  },
  /* Kontext für die Vorschau: laufende Story → echter Story-Kontext; sonst Beispielwerte (wie ?scene=) plus Startwerte aller Storys */
  previewCtx() {
    if (State.mode === 'story' && typeof Story !== 'undefined' && Story.story && Story.s) return Story.ctx();
    const ctx = { bill: 900, before: 1000, after: 500, price: '1.000 €', debt: 300, day: 1, balance: UI.fmt(State.s.balance), stats: { Spins: 12, 'Höchster Kontostand': '1.234 €' }, raw: { balance: State.s.balance, day: 1, vars: {}, flags: {} }, prev: {}, flags: {} };
    for (const st of Object.values(Stories.all)) for (const [k, v] of Object.entries(st.start.vars || {})) { if (!(k in ctx)) ctx[k] = String(v); if (!(k in ctx.raw.vars)) ctx.raw.vars[k] = v; }
    return ctx;
  },
  /* Vorschau: Cutscene.play direkt – Entscheidungen laufen durch, Effekte greifen nicht */
  async preview(id) {
    if (Cutscene.active) { this.toast('Erst die laufende Szene beenden'); return; }
    this.toggle(false);
    await Cutscene.play(id, this.previewCtx());
    this.toast(`Szene ${id} fertig`);
  },
```

- [ ] **Step 4: Laufen lassen – muss bestehen**

Run: `python3 tests/playtest-dev.py`
Expected: `FAILS 0`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/playtest-dev.py
git commit -m "feat(dev): Reiter Szenen – Katalog mit Suche, Vorschau ohne Effekte, Enden der laufenden Story

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Handy-Check, README, Screenshots, Gesamtlauf

**Files:**
- Modify: `tests/mobile-check.py`, `README.md`, `docs/superpowers/specs/2026-09-18-admin-panel-design.md` (Abschnitt „Vorab-Entscheidungen" nachziehen), `docs/superpowers/screenshots/dev-*.png`.

- [ ] **Step 1: Handy-Check ergänzen**

In `tests/mobile-check.py`, in `main()` direkt vor dem Kommentar `# Desktop-Gegenprobe: Roulette-Tisch bleibt 13 Spalten breit` einfügen:

```python
        # Admin-Panel: bei 400 px volle Breite, Tap-Ziele >= 44 px, kein Overflow
        await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
        await cdp.eval("document.querySelector('#devUser').value = 'Admin'; document.querySelector('#devPass').value = '<Passwort>'; document.querySelector('#devLogin').requestSubmit();", await_promise=False)
        await cdp.wait_for("!!document.querySelector('#devFab')", timeout=2.0)
        for tab in ["werte", "screens", "story", "szenen"]:
            await cdp.eval("Dev.toggle(true); document.querySelector('.dev-tab[data-tab=%s]').click();" % json.dumps(tab), await_promise=False)
            await asyncio.sleep(0.3)
            res = await cdp.eval(CHECK_JS % (json.dumps(["#devFab", ".dev-tab", ".dev-btn", ".dev-in", ".dev-row.dev-check"]), 44), await_promise=False) or {}
            width = await cdp.eval("document.querySelector('#devPanel').getBoundingClientRect().width === window.innerWidth", await_promise=False)
            record("dev-panel %s: volle Breite, Tap-Ziele >= 44 px, kein Overflow" % tab, width is True and res.get("overflow", 1) <= 0 and not res.get("small"), (width, res))
            if tab == "werte":
                await cdp.screenshot("mobile-dev-panel.png")
        await cdp.eval("Dev.logout()", await_promise=False)
```

Run: `python3 tests/mobile-check.py`
Expected: alle `OK`, inklusive der vier neuen `dev-panel …`-Zeilen. Fällt ein Tap-Ziel unter 44 px, CSS im Block `/* -- Admin-Panel -- */` nachziehen (nicht den Schwellwert).

- [ ] **Step 2: README**

In `README.md` nach der Tabelle „Dev-Parameter" und dem Absatz über einmalig gültige Parameter (endet mit „… dieselbe erzwungene Story starten.") einfügen:

```markdown
### Admin-Panel

`keller37.html?dev` zeigt ein Login (Benutzer + Passwort). Nach der Anmeldung erscheint unten rechts ein
🛠-Knopf, der auf jedem Screen – auch im Casino Royal und in Cutscenes – eine Schublade mit vier Reitern
öffnet. Die Anmeldung hält, bis der Tab geschlossen wird (`sessionStorage`), auch ohne `?dev` in der URL.

| Reiter | Was geht |
|---|---|
| **Werte** | Kontostand, XP, Stärke, Bier-Pegel, Schulden, Waffenstufe setzen; Royal-Gast, Igor, Brownie, Haus, Ehe, Dealer, Niere schalten; Auto/Schuhe wählen; alle Trophäen, alle Insider, Level max; Spielstand oder alles löschen |
| **Screens** | jeden registrierten Screen öffnen (Keller, Casino Royal, Stadt samt Läden, Story-Screens); Schießerei mit Gegnerwahl; Überfall beim nächsten Spin erzwingen. In der Story werden gesperrte Türen/Räume beim Sprung freigeschaltet |
| **Story** | Story mit vorigem Ende, Starttag (1 = mit Intro) und Waffenstufe neu starten; laufende Story: alle Vars und Flags editieren (auch noch nie gesetzte, z. B. `abgestuerzt`), Tag/Phase setzen, jeden Job erzwingen, jedes Ende abspielen, Türen/Räume/Jobs freischalten |
| **Szenen** | alle Cutscenes (Keller und je Story) mit Suche; Klick spielt eine Vorschau **ohne** Effekte auf den Spielstand; unbekannte Platzhalter bleiben als `{{name}}` sichtbar |

Das Panel ist eine Tür mit Schild, kein Tresor: Die Prüfung steht in der Datei (als Hash, nicht im Klartext);
wer die Browser-Konsole öffnet, kommt daran vorbei. Ohne `?dev` bzw. Anmeldung wird nichts davon ins DOM
gelegt – normale Spieler sehen keinen Unterschied (`tests/desktop-diff.py` bleibt 0 px).

Zugangsdaten ändern: in der Browser-Konsole `DevRules.hash('Name:Passwort')` ausführen und das Ergebnis in
`keller37.html` in `DEV_LOGIN_HASH` (Block `dev-rules`) eintragen.
```

In der Tabelle „Dev-Parameter" eine Zeile ergänzen:

```markdown
| `?dev` | Admin-Panel-Login einblenden (siehe unten); bleibt in der URL stehen, ist kein Einmal-Parameter |
```

Im Abschnitt „Tests" nach der Zeile `python3 tests/mobile-check.py …` ergänzen:

```
python3 tests/playtest-dev.py       # CDP-Playtest Admin-Panel: Login, Werte, Screens, Story, Szenen (Port 9371)
```

- [ ] **Step 3: Spec nachziehen**

In `docs/superpowers/specs/2026-09-18-admin-panel-design.md` am Ende einen Abschnitt anfügen:

```markdown
## Umsetzungsentscheidungen (Plan 2026-09-18-admin-panel.md)

- `parseNumber` nur Ganzzahlen (Option `int` entfällt); Tausenderpunkte erlaubt.
- „Alle Achievements" schreibt die IDs direkt in `State.meta.achievements` (keine 20 Toasts).
- `UI.show` ruft `Dev.render()` direkt (guarded) statt über ein Bus-Event.
- „Job starten" listet alle Jobs aus `Jobs.POOL`; `Jobs.take(id, { force: true })` überspringt die Verfügbarkeitsprüfung.
- Screen-Sprung auf gesperrten Story-Screen schaltet Tür/Raum frei und lässt Gates einmal durch (`Story.allowOnce`).
- Starttag 1 spielt das Intro, > 1 überspringt es.
- Playtest als eigene Datei `tests/playtest-dev.py` (Port 9371), importiert `playtest-story.py` wie `mobile-check.py`.
```

- [ ] **Step 4: Screenshots ablegen**

Run: `K37_SHOTS=docs/superpowers/screenshots python3 tests/playtest-dev.py && K37_SHOTS=docs/superpowers/screenshots python3 tests/mobile-check.py`
Expected: `FAILS 0`; Dateien `docs/superpowers/screenshots/dev-panel.png`, `dev-werte.png`, `dev-screens.png`, `dev-story.png`, `dev-szenen.png`, `mobile-dev-panel.png` (plus die bestehenden `mobile-*.png`, die dabei neu geschrieben werden – per `git diff --stat` prüfen, dass sie sich nicht sichtbar ändern; falls doch, nur die `dev-`/`mobile-dev-`-Dateien stagen).

Die Screenshots kurz ansehen (Read-Tool): Schublade rechts, dunkles Grau, Reiter, Felder – kein Keller-Gold, kein Royal-Cinzel.

- [ ] **Step 5: Gesamtlauf**

```bash
node tests/run-selftest.mjs && sh tests/dom-selftest.sh && python3 tests/desktop-diff.py && python3 tests/mobile-check.py && python3 tests/playtest-dev.py && K37_PORT=9371 K37_PROFILE=/tmp/k37dev-profile K37_SHOTS=/tmp/k37dev-story python3 tests/playtest-story.py
```
Expected: alles grün, `desktop-diff` 0 px auf allen Screens (Roulette kann einmalig 33 px flaken – dann nur diesen Screen wiederholen), `playtest-story` `ERRORS 0`.

- [ ] **Step 6: Commit**

```bash
git add README.md tests/mobile-check.py docs/superpowers/specs/2026-09-18-admin-panel-design.md docs/superpowers/screenshots/dev-panel.png docs/superpowers/screenshots/dev-werte.png docs/superpowers/screenshots/dev-screens.png docs/superpowers/screenshots/dev-story.png docs/superpowers/screenshots/dev-szenen.png docs/superpowers/screenshots/mobile-dev-panel.png
git commit -m "test+docs(dev): Handy-Check fürs Admin-Panel, README-Abschnitt, Screenshots

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec-Abdeckung:** Zugang/Login (Task 3), Panel-Aufbau inkl. Reiter-Merken und Handy-Layout (Task 3, 8), Reiter Werte (4), Screens inkl. Schießerei/Überfall/Läden (5), Story inkl. Start/Vars/Flags/Tag/Job/Ende/Freischalten (6), Szenen inkl. Suche/Vorschau/Platzhalter/Enden (7), Technik: `dev-rules` + Node-Liste (1), `optsFromParams`/`Story.enter(opts)`/`Modes.enter`/`Jobs.take(force)` (2), Boot + `UI.show`-Hook (3), Fehlerfälle: Ungültig-Toast (`numRow`), Tag-Begrenzung auf `story.days` (6), Job ohne Voraussetzung mit Hinweis (6), Vorschau bei aktiver Cutscene blockiert (7), sessionStorage-Fehler (`ss`, 3). Tests: Node (1, 2), Playtest (3–7), Handy-Check, desktop-diff, README (8).

**Typen/Namen:** `DevRules.parseNumber(raw, {min,max})` überall ohne `int`; `Dev.toggle(on)`, `Dev.render()`, `Dev.showScreen(id)`, `Dev.startStory(id, prev, dayRaw, weaponRaw)`, `Dev.preview(id)`; DOM-IDs `devStorySel/devPrevSel/devDayIn/devWeaponIn/devStartBtn/devDaySet/devPhaseSel/devDayBtn/devJobSel/devJobBtn/devEndSel/devEndBtn/devSceneSearch` stimmen zwischen Task 6/7 und den Playtests überein; `sceneGroups` liefert `{ id, title, ids }` (Task 1 Test und Task 7 Nutzung).
