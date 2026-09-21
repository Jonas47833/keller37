# Ruf-Stufen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ruf (0–10) bekommt vier benannte Stufen, ein Angebot je Stufe in Story 1 und 3, neue Ruf-Quellen in Story 3 und einen Stufentitel im HUD beider Stories.

**Architecture:** Ein reiner Helfer `StoryRules.rufStufe` liefert die Stufe; Stories nutzen weiterhin `{ var: 'ruf', gte: N }`-Bedingungen und `once`/`daily`-Events der bestehenden Engine. Alle Logik mit Seiteneffekten liegt in Story-Funktionen (`fns`, per `call`-Effekt) und ist damit in Node ohne DOM testbar; Szenen sind Daten in `scenes`. Die einzige Regeländerung außerhalb der Stories ist `GangRules.raidChance` (kennt `flags.wache`).

**Tech Stack:** Eine HTML-Datei (`keller37.html`, Vanilla JS), Node-Selftest (`tests/run-selftest.mjs`), Browser-Selftest (`tests/dom-selftest.sh`), CDP-Playtest (`tests/playtest-story.py`), Handy-Check (`tests/mobile-check.py`).

**Spec:** `docs/superpowers/specs/2026-09-21-ruf-stufen-design.md`

## Global Constraints

- Eine Datei `keller37.html`, Deutsch, Story-Texte in der Tonlage der jeweiligen Story (Story 1: Vito/Igor/Bahnhof, Story 3: Anabi/Kessler/Bahnhof-Jungs).
- Keine neuen Enden, keine Änderung an Vertrauens-Schwellen, Job-Freischaltungen, Story 2 oder freiem Spiel. Ruf wirkt nur über die Angebote – kein Überfall-Multiplikator, keine Preise, keine Zinsen.
- Schwellen sind genau 2 / 5 / 8 (`RUF_STUFEN[i].ab`); Story-Events mit `ruf`-Bedingung verwenden ausschließlich diese Werte.
- Ruf klemmt bei `varMax.ruf = 10` in beiden Stories (`applyEffect` klemmt `add` an `varMax` und auf ≥ 0; `fns` nutzen `Math.min(10, …)`).
- Neue Szenen bestehen `StoryRules.validatePanels` (bestehender Test „Regie: alle Story-Szenen"); erlaubte Regie-Schlüssel siehe README „Cutscene-Bühne". Figuren: `vito`, `igor`, `junge`, `anabi`, `du`; Kulissen: `hinterzimmer`, `bar`, `strasse`, `keller`, `bahnhof`.
- Tests vor jedem Commit: `node tests/run-selftest.mjs` und `sh tests/dom-selftest.sh` grün (Node lädt die Blöcke `story-rules`, `gang-rules`, `story-schuld`, `story-stash`, `selftest`; alles in diesem Plan ist dort testbar).
- Commit-Nachrichten Deutsch, Format `feat(ruf): …` / `test(ruf): …` / `docs(ruf): …`, jeweils mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Für Shell-Kommandos mit Umlauten/typografischen Zeichen Python-Skripte mit dreifachen Anführungszeichen (`'''…'''`) verwenden – die geraden Anführungszeichen `"` in deutschen Texten (`„…"`) brechen `"…"`-Strings. Einfügen in `keller37.html` per Python `str.replace` mit eindeutigem Anker (`assert s.count(anker) == 1`).
- Node-Tests im Block `<script id="selftest">` stehen hinter den bestehenden Tests derselben Story (Suche: `T.test('STORY_SCHULD: Flucht braucht Ruf` für Story 1, `T.test('STORY_STASH: Eintreiber` für Story 3, `T.test('StoryRules.validate` für `story-rules`). Die Helfer `base`, `seq`, `stashState`, `stashHook`, `stashChoose` existieren dort bereits.

## Review Focus

1. **Alter Spielstand ohne `vars.rufStufe`** (Story 1/3 vor diesem Plan gespeichert): `fns.rufStufe` liest `v.rufStufe || 0`; ein Spieler mit Ruf 6 sieht beim nächsten Schlafen genau einen Toast „Respektiert", nicht zwei. → Test in Task 2.
2. **Vito-Nachlass bei `schuld < 10.000`**: `schuld` wird 0, das Ende „Der Ehrliche" (`schuld lte 0`) feuert am Ende derselben Nacht – gewollt, aber nicht immediate. → Test in Task 3 (schuld 4.000 → 0, `StoryRules.ending` liefert `ehrlich`).
3. **Wache und Kesslers Deal gleichzeitig**: Wache angenommen, danach `bahnhof` gesetzt – `wacheNacht` zieht weiter 200 € ab (Entscheidung des Spielers), das Wache-Angebot kommt nie mehr (`once`). → Test in Task 5.
4. **Ruf fällt nach einem Angebot unter die Schwelle** (z. B. Ruf 5 → „Igor holen" −2 → 3): `vitoRespekt` ist `once` und bleibt gesehen; es kommt nicht erneut, wenn Ruf wieder 5 erreicht. → Test in Task 3.
5. **Reparatur-Ruf einmal pro Woche, auch bei zwei Reparaturen in einer Nacht**: zweite Reparatur derselben Woche gibt nichts; nach `lieferung` (Wochenwechsel) wieder +1. → Test in Task 4.

---

## Dateistruktur

- `keller37.html` – alle Änderungen:
  - Block `story-rules` (`const StoryRules = {`): `RUF_STUFEN`, `rufStufe()`.
  - Block `gang-rules`: `WACHE_PREIS`, `raidChance` mit `flags.wache`.
  - Block `story-schuld` (`const STORY_SCHULD = {`): `start.vars.rufStufe`, HUD-Label, Events `rufStufeNacht`/`rufStufeMorgen`/`vitoRespekt`/`igorHoert`, `igorZweifel` mit `notFlag`, neuer Block `fns`, Szenen `schuld.vitoRespekt`/`schuld.igorHoert`.
  - Block `story-stash` (`const STORY_STASH = {`): `start.vars.rufStufe`, `varMax.ruf`, HUD-Eintrag, Events `rufStufeNacht`/`rufStufeMorgen`/`eintreiberRuf`/`wache`/`wacheNacht`/`anabiHoert`, `fns` (`rufStufe`, `reparaturRuf`, `wacheNacht`, `anabiNachlass`, Änderungen an `abrechnung`, `kreditZahlen`, `lieferung`), `goal`-Suffix, Szenen `stash.wache`/`stash.anabiHoert`, Kessler-Satz in `stash.angebot`, Ruf-Zeile in `stash.abrechnung`, `Bus.on('story:repair')` nach `Stories.define(STORY_STASH)`.
  - Block `selftest`: neue Tests je Task.
- `tests/playtest-story.py` – `scenario_ruf(cdp)`, Aufruf in `main()` nach `scenario_sicbo`.
- `docs/superpowers/screenshots/ruf-wache.png`, `ruf-anabi.png`, `ruf-vito.png`.
- `README.md` – Story-1- und Story-3-Absätze.

---

### Task 1: Stufen-Helfer `StoryRules.rufStufe` und Schwellen-Konsistenz

**Files:**
- Modify: `keller37.html` Block `story-rules` (Suche `  validate(story, sceneIds, jobIds` – der Helfer kommt davor), Block `selftest` (hinter `T.test('StoryRules.validate`-Tests)
- Test: Block `selftest`

**Interfaces:**
- Produces: `StoryRules.RUF_STUFEN: Array<{ id, ab, titel }>`; `StoryRules.rufStufe(ruf: number) → { id, ab, titel }` (letzte Stufe mit `ab <= (ruf || 0)`; negative Werte → Stufe 0).
- Consumes: nichts Neues.

- [ ] **Step 1: Failing Tests schreiben**

Hinter dem letzten `T.test('StoryRules.validate…`-Block im Block `selftest` einfügen:

```js
T.test('StoryRules.rufStufe: vier Stufen 0/2/5/8, negative Werte sind Niemand', () => {
  T.eq(StoryRules.RUF_STUFEN.map((s) => s.ab), [0, 2, 5, 8]);
  T.eq(StoryRules.RUF_STUFEN.map((s) => s.titel), ['Niemand', 'Bekannt', 'Respektiert', 'Legende']);
  for (const [ruf, id] of [[0, 'niemand'], [1, 'niemand'], [2, 'bekannt'], [4, 'bekannt'], [5, 'respektiert'], [7, 'respektiert'], [8, 'legende'], [10, 'legende'], [-1, 'niemand'], [undefined, 'niemand']]) {
    T.eq(StoryRules.rufStufe(ruf).id, id, `Ruf ${ruf}`);
  }
});
T.test('Ruf-Events beider Stories nutzen nur die Stufen-Schwellen 2/5/8', () => {
  const schwellen = StoryRules.RUF_STUFEN.map((s) => s.ab).filter((x) => x > 0);
  const rufConds = (cond, out = []) => {
    if (!cond || typeof cond !== 'object') return out;
    if (cond.var === 'ruf' && 'gte' in cond) out.push(cond.gte);
    for (const k of ['all', 'any']) for (const c of cond[k] || []) rufConds(c, out);
    return out;
  };
  for (const story of [STORY_SCHULD, STORY_STASH]) for (const e of story.events) for (const g of rufConds(e.when)) {
    T.ok(schwellen.includes(g), `${story.id}/${e.id}: Ruf-Schwelle ${g} ist keine Stufe`);
  }
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|fehlgeschlagen"`
Expected: `FAIL StoryRules.rufStufe …` (TypeError: `RUF_STUFEN` undefined); der Schwellen-Test besteht bereits (heute nur `gte: 2`) – das ist in Ordnung, er sichert die späteren Tasks ab.

- [ ] **Step 3: Helfer einfügen**

In `const StoryRules = {` direkt vor `  validate(story, sceneIds, jobIds` einfügen:

```js
  /* Ruf-Stufen: Titel im HUD und Schwellen der Angebote (Story 1 und 3). Events nutzen weiterhin { var: 'ruf', gte: ab }. */
  RUF_STUFEN: [{ id: 'niemand', ab: 0, titel: 'Niemand' }, { id: 'bekannt', ab: 2, titel: 'Bekannt' }, { id: 'respektiert', ab: 5, titel: 'Respektiert' }, { id: 'legende', ab: 8, titel: 'Legende' }],
  rufStufe(ruf) { const r = ruf || 0; let cur = StoryRules.RUF_STUFEN[0]; for (const s of StoryRules.RUF_STUFEN) if (r >= s.ab) cur = s; return cur; },
```

- [ ] **Step 4: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1`
Expected: `… 0 fehlgeschlagen`

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(ruf): StoryRules.rufStufe – vier Stufen, Schwellen-Konsistenz-Test

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: HUD-Titel und Stufen-Toast in beiden Stories

**Files:**
- Modify: `keller37.html` Block `story-schuld` (`start.vars`, `hud`, `events`, neuer Block `fns`), Block `story-stash` (`start.vars`, `varMax`, `hud`, `events`, `fns`), Block `selftest`
- Test: Block `selftest`

**Interfaces:**
- Consumes: `StoryRules.rufStufe` (Task 1).
- Produces: `vars.rufStufe` (Index 0–3) in beiden Stories; `STORY_SCHULD.fns.rufStufe(s)` und `STORY_STASH.fns.rufStufe(s)` → `{}` oder `{ toast }`; Events `rufStufeNacht` (`at: 'night'`) und `rufStufeMorgen` (`at: 'morning'`), beide `daily: true`, `effects: [{ call: 'rufStufe' }]`.

- [ ] **Step 1: Failing Tests schreiben**

Hinter `T.test('STORY_SCHULD: Flucht braucht Ruf…` einfügen:

```js
T.test('Ruf-Stufen: HUD zeigt Titel, Stufen-Toast genau beim Wechsel (Story 1 und 3, auch ohne rufStufe im alten Spielstand)', () => {
  for (const [story, mk] of [[STORY_SCHULD, () => Object.assign(base({ balance: 500 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) })], [STORY_STASH, () => stashState()]]) {
    const s = mk(); const v = s.story.vars;
    T.eq(v.rufStufe, 0, `${story.id}: Start Stufe 0`);
    T.eq(story.varMax.ruf, 10, `${story.id}: varMax.ruf`);
    const hud = story.hud.find((h) => h.var === 'ruf');
    T.ok(hud && typeof hud.label === 'function' && hud.max === 10, `${story.id}: HUD-Eintrag ruf`);
    T.eq(hud.label(s), '🔥 Niemand'); v.ruf = 5; T.eq(hud.label(s), '🔥 Respektiert');
    const nightIds = StoryRules.dueEvents(story, s, 'night').map((e) => e.id);
    T.ok(nightIds.includes('rufStufeNacht'), `${story.id}: rufStufeNacht fällig`);
    T.ok(StoryRules.dueEvents(story, s, 'morning').map((e) => e.id).includes('rufStufeMorgen'), `${story.id}: rufStufeMorgen fällig`);
    const out1 = story.fns.rufStufe(s);
    T.eq(out1.toast && out1.toast.tone, 'win', `${story.id}: Aufstieg → win-Toast`); T.ok(out1.toast.title.includes('Respektiert')); T.eq(v.rufStufe, 2);
    T.eq(story.fns.rufStufe(s), {}, `${story.id}: unverändert → kein Toast`);
    v.ruf = 4; const out2 = story.fns.rufStufe(s);
    T.eq(out2.toast && out2.toast.tone, 'loss', `${story.id}: Abstieg → loss-Toast`); T.eq(v.rufStufe, 1);
    /* alter Spielstand: rufStufe fehlt, Ruf 6 → genau ein Toast Respektiert */
    const alt = mk(); delete alt.story.vars.rufStufe; alt.story.vars.ruf = 6;
    const o = story.fns.rufStufe(alt); T.ok(o.toast && o.toast.title.includes('Respektiert')); T.eq(alt.story.vars.rufStufe, 2); T.eq(story.fns.rufStufe(alt), {});
  }
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|fehlgeschlagen"`
Expected: `FAIL Ruf-Stufen: HUD zeigt Titel … schuld: Start Stufe 0` (rufStufe undefined).

- [ ] **Step 3: Story 1 anpassen**

In `const STORY_SCHULD = {`:

`vars: { schuld: 50000, vertrauen: 0, ruf: 0, gezahlt: 0, duellSiege: 0, tuerSauber: 0 }` → `vars: { schuld: 50000, vertrauen: 0, ruf: 0, rufStufe: 0, gezahlt: 0, duellSiege: 0, tuerSauber: 0 }`

HUD: `{ var: 'ruf', label: '🔥 Ruf', max: 10 }` → `{ var: 'ruf', label: (s) => '🔥 ' + StoryRules.rufStufe(s.story.vars.ruf).titel, max: 10 }`

In `events: [` von STORY_SCHULD als erste Einträge (vor `{ id: 'chantal3'`):

```js
    /* Ruf-Stufen: Toast beim Wechsel (Spec 2026-09-21 Ruf-Stufen §2.2) */
    { id: 'rufStufeNacht', daily: true, at: 'night', effects: [{ call: 'rufStufe' }] },
    { id: 'rufStufeMorgen', daily: true, at: 'morning', effects: [{ call: 'rufStufe' }] },
```

Direkt vor `  endings: [` von STORY_SCHULD einen `fns`-Block einfügen:

```js
  /* ---- Story-Funktionen (Effekt call) ---- */
  fns: {
    rufStufe(s) { return StoryRules.rufStufeToast(s.story.vars); },
  },
```

- [ ] **Step 4: Gemeinsamen Toast-Helfer in `story-rules` ergänzen**

Beide Stories brauchen dieselbe Logik – sie liegt neben `rufStufe` in `StoryRules` (hinter `rufStufe(ruf) {…},`):

```js
  /* Stufen-Toast: vergleicht die Stufe aus vars.ruf mit vars.rufStufe (Index), setzt sie nach und liefert bei Wechsel einen Toast */
  RUF_SAETZE: { bekannt: 'Man hat deinen Namen gehört.', respektiert: 'Man kennt deinen Namen.', legende: 'Man erzählt sich Geschichten.' },
  rufStufeToast(vars) {
    const stufe = StoryRules.rufStufe(vars.ruf), idx = StoryRules.RUF_STUFEN.indexOf(stufe), alt = vars.rufStufe || 0;
    if (idx === alt) return {};
    vars.rufStufe = idx;
    const auf = idx > alt;
    return { toast: { icon: '🔥', title: auf ? stufe.titel : `${stufe.titel} – Ruf sinkt`, text: auf ? StoryRules.RUF_SAETZE[stufe.id] : 'Der Bahnhof redet weniger über dich.', tone: auf ? 'win' : 'loss' } };
  },
```

- [ ] **Step 5: Story 3 anpassen**

In `const STORY_STASH = {`:

`vars: { woche: 0, …, ruf: 0, igorBiere: 0, …` → hinter `ruf: 0,` ein `rufStufe: 0,` einfügen (Anker: `uebergeben: 0, ruf: 0,` → `uebergeben: 0, ruf: 0, rufStufe: 0,`).

`  varMax: { zorn: 3 },` → `  varMax: { zorn: 3, ruf: 10 },`

HUD (Anker `    { var: 'kredit', label: '🧾 Kredit', fmt: 'money' },`) – dahinter:

```js
    { var: 'ruf', label: (s) => '🔥 ' + StoryRules.rufStufe(s.story.vars.ruf).titel, max: 10 },
```

Events von STORY_STASH: vor `{ id: 'abrechnung', when` einfügen:

```js
    /* Ruf-Stufen: Toast beim Wechsel (Spec 2026-09-21 Ruf-Stufen §2.2) */
    { id: 'rufStufeNacht', daily: true, at: 'night', effects: [{ call: 'rufStufe' }] },
    { id: 'rufStufeMorgen', daily: true, at: 'morning', effects: [{ call: 'rufStufe' }] },
```

In `fns: {` von STORY_STASH als erste Funktion (vor `lieferung(s) {`):

```js
    rufStufe(s) { return StoryRules.rufStufeToast(s.story.vars); },
```

- [ ] **Step 6: Tests laufen lassen – grün, auch der Browser-Selftest (HUD rendert `label` als Funktion)**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh`
Expected: `… 0 fehlgeschlagen` und `data-selftest="passed=N failed=0"`

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(ruf): Stufentitel im HUD (Story 1 und 3), Stufen-Toast per fns.rufStufe

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Story 1 – „Vitos Respekt" (5) und „Igor hört zu" (8)

**Files:**
- Modify: `keller37.html` Block `story-schuld` (`events`, `scenes`), Block `selftest`
- Test: Block `selftest`

**Interfaces:**
- Consumes: Events-Format der Engine, `StoryRules.dueEvents`, `StoryRules.ending`.
- Produces: Events `vitoRespekt`, `igorHoert`; Szenen `schuld.vitoRespekt`, `schuld.igorHoert`; Flags `vitosMann`, `igorZweifelt` (bestehend).

- [ ] **Step 1: Failing Tests schreiben**

Hinter dem Test aus Task 2 einfügen:

```js
/* Wahl in einer Story-1-Szene anwenden (Szenen sind Arrays ohne ctx) */
const schuldChoose = (s, sceneId, value) => {
  const panels = STORY_SCHULD.scenes[sceneId];
  for (const p of panels) for (const c of p.choices || []) if (c.value === value) for (const eff of c.effects || []) StoryRules.applyEffect(s, eff, STORY_SCHULD);
};
T.test('STORY_SCHULD: Vitos Respekt ab Ruf 5 (once), Annehmen −10.000/Vertrauen +2, nicht unter 0, Ablehnen Ruf +1', () => {
  const s = Object.assign(base({ balance: 500 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) });
  s.story.day = 12; s.story.seen.push('chantal3', 'wirt5', 'stadtOffen');
  const night = () => StoryRules.dueEvents(STORY_SCHULD, s, 'night').map((e) => e.id).filter((id) => !id.startsWith('rufStufe'));
  s.story.vars.ruf = 4; T.eq(night().includes('vitoRespekt'), false, 'Ruf 4: kein Angebot');
  s.story.vars.ruf = 5; T.ok(night().includes('vitoRespekt'));
  schuldChoose(s, 'schuld.vitoRespekt', 'ja');
  T.eq(s.story.vars.schuld, 40000); T.eq(s.story.vars.vertrauen, 2); T.eq(s.story.flags.vitosMann, true);
  s.story.seen.push('vitoRespekt'); s.story.vars.ruf = 3; s.story.vars.ruf = 5;
  T.eq(night().includes('vitoRespekt'), false, 'once: kommt nicht wieder, auch wenn Ruf erneut 5 erreicht');
  const n = Object.assign(base({ balance: 500 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) }); n.story.vars.ruf = 5;
  schuldChoose(n, 'schuld.vitoRespekt', 'nein'); T.eq(n.story.vars.ruf, 6); T.eq(n.story.vars.schuld, 50000);
  const k = Object.assign(base({ balance: 500 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) }); k.story.vars.schuld = 4000; k.story.vars.vertrauen = 9;
  schuldChoose(k, 'schuld.vitoRespekt', 'ja'); T.eq(k.story.vars.schuld, 0, 'nicht unter 0'); T.eq(k.story.vars.vertrauen, 10, 'varMax');
  const end = StoryRules.ending(STORY_SCHULD, k); T.ok(end && end.id === 'ehrlich', 'Schuld 0 → Der Ehrliche am Nachtende');
});
T.test('STORY_SCHULD: Igor hört zu ab Ruf 8 nur ohne igorZweifelt; Zuhören setzt das Flag; igorZweifel dann nicht mehr', () => {
  const s = Object.assign(base({ balance: 500 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) });
  s.story.day = 20; s.story.seen.push('chantal3', 'wirt5', 'stadtOffen', 'vitoRespekt');
  const night = () => StoryRules.dueEvents(STORY_SCHULD, s, 'night').map((e) => e.id).filter((id) => !id.startsWith('rufStufe'));
  s.story.vars.ruf = 7; T.eq(night().includes('igorHoert'), false);
  s.story.vars.ruf = 8; T.ok(night().includes('igorHoert'));
  schuldChoose(s, 'schuld.igorHoert', 'nein'); T.eq(!!s.story.flags.igorZweifelt, false, 'Abwinken: nichts');
  schuldChoose(s, 'schuld.igorHoert', 'ja'); T.eq(s.story.flags.igorZweifelt, true);
  T.eq(night().includes('igorHoert'), false, 'mit Flag kein igorHoert mehr');
  s.story.vars.duellSiege = 3;
  T.eq(StoryRules.dueEvents(STORY_SCHULD, s, 'spin:after').map((e) => e.id), [], 'igorZweifel feuert nicht mehr, wenn das Flag steht');
  const z = Object.assign(base({ balance: 500 }), { story: StoryRules.freshStoryPart(STORY_SCHULD) }); z.story.vars.duellSiege = 3;
  T.eq(StoryRules.dueEvents(STORY_SCHULD, z, 'spin:after').map((e) => e.id), ['igorZweifel'], 'ohne Flag wie bisher');
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|fehlgeschlagen"`
Expected: `FAIL STORY_SCHULD: Vitos Respekt … Ruf 5` (erwartet `['vitoRespekt']`, ist `[]`) und `FAIL STORY_SCHULD: Igor hört zu …`.

- [ ] **Step 3: Events einfügen**

In `events: [` von STORY_SCHULD direkt hinter der Zeile `{ id: 'igorZweifel', when: { var: 'duellSiege', gte: 3 }, once: true, at: 'spin:after', scene: 'schuld.igorZweifel', effects: [{ flag: 'igorZweifelt' }] },` – zuerst diese Zeile ersetzen durch:

```js
    { id: 'igorZweifel', when: { all: [{ var: 'duellSiege', gte: 3 }, { notFlag: 'igorZweifelt' }] }, once: true, at: 'spin:after', scene: 'schuld.igorZweifel', effects: [{ flag: 'igorZweifelt' }] },
    /* Ruf-Angebote (Spec 2026-09-21 Ruf-Stufen §3): Respektiert → Vito, Legende → Igor */
    { id: 'vitoRespekt', when: { var: 'ruf', gte: 5 }, once: true, at: 'night', scene: 'schuld.vitoRespekt' },
    { id: 'igorHoert', when: { all: [{ var: 'ruf', gte: 8 }, { notFlag: 'igorZweifelt' }] }, once: true, at: 'night', scene: 'schuld.igorHoert' },
```

(Die exakte bestehende `igorZweifel`-Zeile per `grep -n "id: 'igorZweifel'" keller37.html` prüfen und vollständig ersetzen.)

- [ ] **Step 4: Szenen einfügen**

In `scenes: {` von STORY_SCHULD direkt hinter dem Eintrag `'schuld.tuer.kevin': [ … ],` (Anker: die Zeile `        ] },` + `    ],` die den Eintrag schließt – sicherer: vor `    'schuld.buero': [` einfügen, falls vorhanden, sonst vor dem ersten `'schuld.ende.`-Eintrag):

```js
    /* ---- Ruf-Angebote ---- */
    'schuld.vitoRespekt': [
      { bg: 'hinterzimmer', who: 'du', mood: 'calm', cast: ['du'], text: 'Igor holt dich von der Bar. Kein Wort. Hinterzimmer, Vito, ein Glas, das er nicht anrührt.' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', text: 'Man redet über dich. Am Bahnhof, im Taxi, an meiner Tür. Ich höre viel. Meistens Unsinn. Diesmal nicht.' },
      { bg: 'hinterzimmer', who: 'vito', mood: 'calm', cam: 'close', text: 'Zehntausend weniger auf dem Zettel. Dafür trägst du ab heute meinen Namen, wenn jemand fragt, für wen du arbeitest. Das ist kein Geschenk. Das ist ein Preis.',
        choices: [
          { label: 'Annehmen', value: 'ja', cls: 'red', effects: [{ var: 'schuld', add: -10000 }, { var: 'vertrauen', add: 2 }, { flag: 'vitosMann' }] },
          { label: 'Ablehnen', value: 'nein', cls: 'ghost', effects: [{ var: 'ruf', add: 1 }] },
        ] },
      { bg: 'hinterzimmer', who: 'igor', mood: 'calm', text: 'Igor bringt dich zurück. An der Tür sagt er, ohne dich anzusehen: „Am Bahnhof sagen sie, du zahlst selbst. Egal, was du eben gesagt hast.“' },
    ],
    'schuld.igorHoert': [
      { bg: 'bar', who: 'du', mood: 'calm', cast: ['du'], text: 'Kurz vor Schluss. Der Wirt wischt. Igor setzt sich neben dich. Igor setzt sich nie.' },
      { bg: 'bar', who: 'igor', mood: 'calm', enter: 'igor', text: 'Ich stehe seit elf Jahren an dieser Tür. Ich weiß, wer reinkommt und wer nicht mehr rauskommt. Und ich weiß, wie man am Bahnhof über Vito redet. Und wie über dich.' },
      { bg: 'bar', who: 'igor', mood: 'calm', cam: 'close', text: 'Sie haben mehr Respekt vor dir als vor ihm. Das hat er noch nicht gemerkt. Ich schon. Willst du wissen, was ich sonst noch gemerkt habe?',
        choices: [
          { label: 'Zuhören', value: 'ja', cls: 'blue', effects: [{ flag: 'igorZweifelt' }] },
          { label: 'Abwinken', value: 'nein', cls: 'ghost' },
        ] },
      { bg: 'bar', who: 'igor', mood: 'calm', text: 'Er steht auf, legt einen Schein auf den Tresen. „Für das Bier. Und für das Gespräch, das wir nicht hatten.“' },
    ],
```

Hinweis: `enter: 'igor'` ist ein Regie-Schlüssel (README „Cutscene-Bühne"); wenn `validatePanels` ihn in dieser Form nicht akzeptiert (Test „Regie: alle Story-Szenen" schlägt fehl), den Schlüssel weglassen – die Auto-Regie lässt den Sprecher ohnehin auftreten.

- [ ] **Step 5: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh`
Expected: `… 0 fehlgeschlagen`, `failed=0` (der Browser-Test „Regie: alle Story-Szenen" prüft die neuen Szenen).

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(ruf): Story 1 – Vitos Respekt (Ruf 5) und Igor hört zu (Ruf 8)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Story 3 – neue Ruf-Quellen

**Files:**
- Modify: `keller37.html` Block `story-stash` (`events`, `fns.abrechnung`, `fns.kreditZahlen`, `fns.lieferung`, neue `fns.reparaturRuf`, Szene `stash.abrechnung`, `Bus.on('story:repair')`), Block `selftest`
- Test: Block `selftest`

**Interfaces:**
- Consumes: `Story.repair` emittiert bereits `Bus.emit('story:repair', { door, price })`; `fns.lieferung` erhöht `v.woche`.
- Produces: `STORY_STASH.fns.reparaturRuf(s) → {} | { toast }` (setzt `flags.rufReparaturWoche`); Event `eintreiberRuf` (`at: 'job:after'`, `when: { jobToday: 'eintreiber' }`, `daily`); `fns.abrechnung` und `fns.kreditZahlen` erhöhen Ruf.

- [ ] **Step 1: Failing Tests schreiben**

Hinter `T.test('STORY_STASH: Eintreiber – …` einfügen:

```js
T.test('STORY_STASH: Ruf-Quellen – Abrechnung ok, Eintreiber-Schicht, Kredit-Rate, Reparatur einmal je Woche; alle klemmen bei 10', () => {
  /* Abrechnung: nur Ausgang ok gibt Ruf */
  const a = stashState({ balance: 50000 }); a.story.day = 7; a.story.vars.woche = 1; a.story.vars.ziel = 20000; a.story.vars.rueckgabe = 11000; a.story.vars.lieferung = 10000;
  a.story.vars.umsatz = 20000; STORY_STASH.fns.abrechnung(a); T.eq(a.story.vars.ruf, 1, 'sauber → +1');
  const b = stashState({ balance: 50000 }); b.story.vars.woche = 1; b.story.vars.ziel = 20000; b.story.vars.rueckgabe = 11000; b.story.vars.umsatz = 5000;
  STORY_STASH.fns.abrechnung(b); T.eq(b.story.vars.ruf, 0, 'Umsatz zu niedrig → nichts');
  /* Eintreiber-Schicht */
  const e = stashState(); e.story.day = 3; e.story.jobToday = 'eintreiber';
  const [ids] = stashHook(e, 'job:after'); T.ok(ids.includes('eintreiberRuf')); T.eq(e.story.vars.ruf, 1);
  T.eq(stashHook(e, 'job:after')[0].includes('eintreiberRuf'), false, 'daily: nur einmal am Tag');
  e.story.jobToday = 'kurierfahrt'; e.story.day = 4; T.eq(stashHook(e, 'job:after')[0].includes('eintreiberRuf'), false, 'anderer Job: nichts');
  /* Kredit-Rate */
  const k = stashState({ balance: 9000 }); k.story.vars.kredit = 12000;
  const out = STORY_STASH.fns.kreditZahlen(k); T.eq(k.story.vars.kredit, 7000); T.eq(k.story.vars.ruf, 1); T.ok(out.toast && /Ruf \+1/.test(out.toast.text), 'Toast nennt Ruf');
  const k0 = stashState({ balance: 0 }); k0.story.vars.kredit = 5000; STORY_STASH.fns.kreditZahlen(k0); T.eq(k0.story.vars.ruf, 0, 'ohne Zahlung kein Ruf');
  /* Reparatur: einmal je Woche, nach lieferung wieder */
  const r = stashState(); r.story.vars.woche = 1;
  T.ok(STORY_STASH.fns.reparaturRuf(r).toast); T.eq(r.story.vars.ruf, 1); T.eq(r.story.flags.rufReparaturWoche, true);
  T.eq(STORY_STASH.fns.reparaturRuf(r), {}); T.eq(r.story.vars.ruf, 1, 'zweite Reparatur derselben Woche: nichts');
  r.story.day = 8; STORY_STASH.fns.lieferung(r); T.eq(!!r.story.flags.rufReparaturWoche, false, 'Wochenwechsel setzt zurück');
  T.ok(STORY_STASH.fns.reparaturRuf(r).toast); T.eq(r.story.vars.ruf, 2);
  /* Klemmen bei 10 */
  const m = stashState({ balance: 50000 }); m.story.vars.ruf = 10; m.story.vars.woche = 1; m.story.vars.ziel = 1; m.story.vars.rueckgabe = 1; m.story.vars.umsatz = 1;
  STORY_STASH.fns.abrechnung(m); STORY_STASH.fns.reparaturRuf(m); m.story.vars.kredit = 5000; STORY_STASH.fns.kreditZahlen(m);
  m.story.jobToday = 'eintreiber'; m.story.day = 5; stashHook(m, 'job:after');
  T.eq(m.story.vars.ruf, 10);
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|fehlgeschlagen"`
Expected: `FAIL STORY_STASH: Ruf-Quellen … sauber → +1` (Ruf bleibt 0).

- [ ] **Step 3: `fns` erweitern**

In `fns.abrechnung` von STORY_STASH: die Zeile `      if (r.ausgang === 'ok') v.abrechnungenOk++;` ersetzen durch:

```js
      if (r.ausgang === 'ok') { v.abrechnungenOk++; v.ruf = Math.min(10, (v.ruf || 0) + 1); v.rufAbrechnung = 1; } else v.rufAbrechnung = 0;
```

In `fns.kreditZahlen`: die Zeilen

```js
      s.balance -= amt; v.kredit -= amt;
      return { toast: { icon: '🧾', title: `−${StoryRules.fmtMoney(amt)}`, text: `Kredit noch ${StoryRules.fmtMoney(v.kredit)}.`, tone: 'info' } };
```

ersetzen durch:

```js
      s.balance -= amt; v.kredit -= amt; v.ruf = Math.min(10, (v.ruf || 0) + 1);
      return { toast: { icon: '🧾', title: `−${StoryRules.fmtMoney(amt)}`, text: `Kredit noch ${StoryRules.fmtMoney(v.kredit)}. Ruf +1 – Anabi merkt sich, wer zahlt.`, tone: 'info' } };
```

In `fns.lieferung`: `      v.woche++; v.umsatz = 0; v.umsatzRoyal = 0; v.eintreiberWoche = 0;` → dahinter ` delete st.flags.rufReparaturWoche;` anhängen (dieselbe Zeile).

Neue Funktion in `fns` (hinter `kreditZahlen`):

```js
    /* Reparatur nach Überfall: Ruf +1, einmal je Woche (Flag fällt bei der Lieferung) – aufgerufen vom Bus-Hook story:repair */
    reparaturRuf(s) {
      const st = s.story;
      if (st.flags.rufReparaturWoche) return {};
      st.flags.rufReparaturWoche = true; st.vars.ruf = Math.min(10, (st.vars.ruf || 0) + 1);
      return { toast: { icon: '🔥', title: 'Ruf +1', text: 'Er lässt sich nicht kleinkriegen, sagen sie am Bahnhof.', tone: 'win' } };
    },
```

- [ ] **Step 4: Event, Bus-Hook, Abrechnungs-Zeile**

Events von STORY_STASH: hinter `{ id: 'kontrolle', when: { flag: 'kontrolle' }, at: 'job:after', …` einfügen:

```js
    { id: 'eintreiberRuf', when: { jobToday: 'eintreiber' }, daily: true, at: 'job:after', effects: [{ var: 'ruf', add: 1 }, { toast: { icon: '🥊', title: 'Ruf +1', text: 'Die Liste ist kürzer. Der Bahnhof hat es gesehen.', tone: 'win' } }] },
```

Hinter `if (typeof Stories !== 'undefined') Stories.define(STORY_STASH);` einfügen:

```js
/* Ruf: +1 je Woche für die erste Reparatur nach einem Überfall (Spec 2026-09-21 Ruf-Stufen §4.1) */
if (typeof Bus !== 'undefined') Bus.on('story:repair', () => {
  if (State.mode !== 'story' || !State.s.story || State.s.story.id !== 'stash') return;
  const out = STORY_STASH.fns.reparaturRuf(State.s);
  if (out.toast) UI.toast(out.toast);
  State.save(); UI.renderWallet();
});
```

In der Szene `'stash.abrechnung'`: den Igor-Panel-Text `` text: `Zorn: ${v.zorn} von 3. Zettel: ${fmt(v.kredit)}. Ich sag es nur, damit du es weißt.` `` ersetzen durch `` text: `Zorn: ${v.zorn} von 3. Zettel: ${fmt(v.kredit)}.${v.rufAbrechnung ? ' Und am Bahnhof wissen sie, dass du sauber abgeliefert hast – Ruf +1.' : ''} Ich sag es nur, damit du es weißt.` ``.

- [ ] **Step 5: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh`
Expected: `… 0 fehlgeschlagen`, `failed=0`. Falls der bestehende Abrechnungs-Test (`STORY_STASH: Abrechnung – vier Ausgänge…`) exakte `vars` vergleicht, `rufAbrechnung`/`ruf` dort ergänzen.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(ruf): Story 3 – Ruf-Quellen: saubere Abrechnung, Eintreiber, Kredit-Rate, Reparatur je Woche

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Story 3 – „Die Wache" (Ruf 5)

**Files:**
- Modify: `keller37.html` Block `gang-rules` (`WACHE_PREIS`, `raidChance`), Block `story-stash` (`events`, `fns.wacheNacht`, `goal`, Szenen `stash.wache`, `stash.angebot`), Block `selftest`
- Test: Block `selftest`

**Interfaces:**
- Consumes: `GangRules.raid(broken, flags, rng)` ruft `raidChance(flags)`; `fns.ueberfall` nutzt `raid`.
- Produces: `GangRules.WACHE_PREIS = 200`; `raidChance({ wache: true }) === 0`; Events `wache` (once, night) und `wacheNacht` (daily, night, vor `ueberfall`); `fns.wacheNacht(s) → {} | { toast }`; Flags `wache`, `wacheNein`, `wacheWeg`.

- [ ] **Step 1: Failing Tests schreiben**

Hinter dem Test aus Task 4 einfügen:

```js
T.test('GangRules.raidChance: Wache stoppt Überfälle wie der Bahnhof-Deal; Hinterhalt-Chance bleibt', () => {
  T.eq(GangRules.WACHE_PREIS, 200);
  T.eq(GangRules.raidChance({ wache: true }), 0);
  T.eq(GangRules.raidChance({ bahnhof: true }), 0);
  T.eq(GangRules.raidChance({}), GangRules.RAID.base);
  T.eq(GangRules.ambushChance({ wache: true }, null), GangRules.AMBUSH.base, 'Wache steht vor dem Keller, nicht in der Gasse');
  T.eq(GangRules.raid({}, { wache: true }, seq(0.0, 0.0)), null, 'raid liefert mit Wache keine Tür');
});
T.test('STORY_STASH: Die Wache ab Ruf 5 ohne Bahnhof-Deal (once); 200 €/Nacht; geht bei leerer Kasse; goal zeigt Wache', () => {
  const nightIds = (s, rng = seq(0.99, 0.99, 0.99)) => stashHook(s, 'night', rng)[0];
  /* Tage ohne eigene Nacht-Events wählen: 10 = Tutorial, 14 = Abrechnung, 15 = Lieferung + Kessler-Angebot */
  const s = stashState({ balance: 5000 }); s.story.day = 9; s.story.vars.woche = 2; s.story.vars.ruf = 4;
  T.eq(nightIds(s).includes('wache'), false, 'Ruf 4: nichts');
  s.story.day = 11; s.story.vars.ruf = 5; s.story.flags.bahnhof = true;
  T.eq(nightIds(s).includes('wache'), false, 'mit Bahnhof-Deal kein Angebot');
  delete s.story.flags.bahnhof; s.story.day = 12;
  T.ok(nightIds(s).includes('wache'), 'Ruf 5, Tag 12: Angebot');   // stashHook markiert once-Events als gesehen
  stashChoose(s, 'stash.wache', 'ja'); T.eq(s.story.flags.wache, true);
  /* Nacht mit Wache: 200 € weg, kein Überfall (raid fragt den rng mit Wache gar nicht); rng 0.99 → kein Hinterhalt */
  s.story.day = 13; const bal = s.balance;
  const [ids] = stashHook(s, 'night', seq(0.99, 0.99, 0.99));
  T.ok(ids.indexOf('wacheNacht') < ids.indexOf('ueberfall'), 'wacheNacht läuft vor ueberfall');
  T.eq(s.balance, bal - 200); T.eq(Object.keys(s.story.broken || {}).length, 0, 'keine Tür kaputt');
  T.ok(STORY_STASH.goal(s).includes('Wache 200'), 'goal nennt die Wache');
  /* leere Kasse: Wache geht, Flag fällt, Toast; Überfall in derselben Nacht: rng 0.0 (Überfall ja), 0.0 (erste Tür); Hinterhalt entfällt wegen ueberfallHeute */
  s.balance = 150; s.story.day = 16;
  const [ids2, outs2] = stashHook(s, 'night', seq(0.0, 0.0, 0.99));
  T.eq(!!s.story.flags.wache, false); T.eq(s.story.flags.wacheWeg, true); T.eq(s.balance, 150, 'nichts abgezogen');
  T.ok(outs2.some((o) => o.toast && o.toast.title === 'Die Wache geht'));
  T.ok(Object.keys(s.story.broken || {}).length > 0, 'ohne Wache: Überfall trifft eine Tür');
  T.eq(STORY_STASH.goal(s).includes('Wache'), false);
  s.story.day = 17; s.story.vars.ruf = 6; T.eq(nightIds(s).includes('wache'), false, 'once: kein zweites Angebot');
  /* Ablehnen */
  const n = stashState(); n.story.day = 12; n.story.vars.ruf = 5; stashChoose(n, 'stash.wache', 'nein'); T.eq(n.story.flags.wacheNein, true);
  n.story.seen.push('wache'); n.story.day = 13; T.eq(nightIds(n).includes('wacheNacht'), false, 'ohne Flag keine Kosten');
  /* Wache + später Bahnhof-Deal: kostet weiter */
  const w = stashState({ balance: 5000 }); w.story.day = 16; w.story.flags.wache = true; w.story.flags.bahnhof = true;
  stashHook(w, 'night', seq(0.99, 0.99, 0.99)); T.eq(w.balance, 4800);
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|fehlgeschlagen"`
Expected: `FAIL GangRules.raidChance: Wache …` (WACHE_PREIS undefined) und `FAIL STORY_STASH: Die Wache …`.

- [ ] **Step 3: GangRules anpassen**

Im Block `gang-rules`: `  raidChance(flags) { return flags.bahnhof ? 0 : flags.igor ? GangRules.RAID.igor : GangRules.RAID.base; },` ersetzen durch:

```js
  WACHE_PREIS: 200, // Bahnhof-Jungs vor der Tür (Ruf-Angebot „Die Wache“): je Nacht, Türen bleiben ganz
  raidChance(flags) { return flags.bahnhof || flags.wache ? 0 : flags.igor ? GangRules.RAID.igor : GangRules.RAID.base; },
```

- [ ] **Step 4: Story 3 – Events, fns, goal, Szenen**

Events von STORY_STASH: die Zeile `{ id: 'ueberfall', when: { day: { gte: 8 } }, daily: true, at: 'night', effects: [{ call: 'ueberfall' }] },` ersetzen durch:

```js
    /* Die Wache (Ruf-Angebot): Kosten vor dem Überfall abrechnen – eine gegangene Wache schützt in derselben Nacht nicht mehr */
    { id: 'wacheNacht', when: { flag: 'wache' }, daily: true, at: 'night', effects: [{ call: 'wacheNacht' }] },
    { id: 'ueberfall', when: { day: { gte: 8 } }, daily: true, at: 'night', effects: [{ call: 'ueberfall' }] },
```

Hinter der `angebot`-Zeile (`{ id: 'angebot', when: { all: [{ day: { gte: 15 } }, { var: 'ruf', gte: 2 }, …`) einfügen:

```js
    { id: 'wache', when: { all: [{ var: 'ruf', gte: 5 }, { notFlag: 'bahnhof' }, { notFlag: 'wache' }, { notFlag: 'wacheNein' }] }, once: true, at: 'night', scene: 'stash.wache' },
```

In `fns` (hinter `reparaturRuf`):

```js
    /* Die Wache: 200 € je Nacht; reicht die Kasse nicht, gehen die Jungs (Flag fällt, kommt nicht wieder) */
    wacheNacht(s) {
      const f = s.story.flags;
      if (s.balance >= GangRules.WACHE_PREIS) { s.balance -= GangRules.WACHE_PREIS; return {}; }
      delete f.wache; f.wacheWeg = true;
      return { toast: { icon: '🚪', title: 'Die Wache geht', text: 'Kein Geld, keine Jungs. Die Tür ist wieder deine Sache.', tone: 'loss' } };
    },
```

`goal` von STORY_STASH: die letzte `return`-Zeile

```js
    return `Woche ${v.woche}: Umsatz ${fmt(v.umsatz)} / ${fmt(v.ziel)} · ${heute ? 'HEUTE ABEND' : `Tag ${v.woche * 7}`}: ${fmt(v.rueckgabe)} fällig`;
```

ersetzen durch:

```js
    return `Woche ${v.woche}: Umsatz ${fmt(v.umsatz)} / ${fmt(v.ziel)} · ${heute ? 'HEUTE ABEND' : `Tag ${v.woche * 7}`}: ${fmt(v.rueckgabe)} fällig${f.wache ? ` · Wache ${GangRules.WACHE_PREIS} €/Nacht` : ''}`;
```

(Die drei früheren `return`-Zeilen in `goal` bleiben ohne Wache-Suffix; der Test setzt `woche = 2`, `day = 12`, also die letzte Zeile.)

Szenen: vor `'stash.angebot': [` einfügen:

```js
    'stash.wache': [
      { bg: 'strasse', who: 'du', mood: 'calm', cast: ['du'], text: 'Vor dem Keller stehen zwei. Kapuzen, Bahnhof. Sie stehen nicht so, wie man steht, wenn man etwas kaputt machen will.' },
      { bg: 'strasse', who: 'junge', mood: 'calm', text: 'Kessler sagt, du bist keiner, den man beklaut. Dann sind wir eben keine, die klauen. Zweihundert die Nacht, und keiner fasst deine Tür an. Keiner.' },
      { bg: 'strasse', who: 'junge', mood: 'calm', cam: 'close', text: 'Wenn das Geld nicht da ist, sind wir es auch nicht. So läuft das. Deal?',
        choices: [
          { label: 'Annehmen', value: 'ja', cls: 'blue', effects: [{ flag: 'wache' }] },
          { label: 'Ablehnen', value: 'nein', cls: 'ghost', effects: [{ flag: 'wacheNein' }] },
        ] },
    ],
```

Kessler-Szene `'stash.angebot'` von Array zu Funktion machen – den kompletten Eintrag ersetzen durch:

```js
    'stash.angebot': (ctx) => [
      { bg: 'bahnhof', who: 'du', mood: 'calm', cast: ['du'], text: 'Kessler wartet an der Unterführung. Allein. Das ist entweder Respekt oder eine Falle. Bei Kessler ist es meistens beides.' },
      { bg: 'bahnhof', who: 'kessler', mood: 'calm', text: 'Du hast meine Jungs hingelegt. Zweimal. Ich könnte sauer sein. Ich bin lieber praktisch: Wasch für uns, dann lassen wir dich in Ruhe.' },
      ...(ctx.raw.flags.wache ? [{ bg: 'bahnhof', who: 'kessler', mood: 'calm', text: 'Deine zwei vor der Tür kannst du behalten. Oder heimschicken. Mir egal – sie kriegen ihr Geld so oder so von dir.' }] : []),
      { bg: 'bahnhof', who: 'kessler', mood: 'calm', cam: 'close', text: 'Keine Überfälle mehr, keine Hinterhalte. Dafür wächst dein Umsatzziel – zwei Herren wollen waschen. Und Anabi erfährt es. Irgendwann. Dann brauchst du uns wirklich.',
        choices: [{ label: 'Annehmen', value: 'ja', cls: 'red', effects: [{ flag: 'bahnhof' }] }, { label: 'Ablehnen', value: 'nein', cls: 'ghost', effects: [{ flag: 'bahnhofNein' }] }] },
    ],
```

- [ ] **Step 5: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh`
Expected: `… 0 fehlgeschlagen`, `failed=0`. Der bestehende Test „STORY_STASH: Angebot der Bahnhof-Jungs…" nutzt `stashChoose`, das Funktions-Szenen unterstützt – bleibt grün.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(ruf): Story 3 – Die Wache (Ruf 5): 200 €/Nacht, Türen bleiben ganz, geht bei leerer Kasse

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Story 3 – „Anabi hört zu" (Ruf 8)

**Files:**
- Modify: `keller37.html` Block `story-stash` (`events`, `fns.anabiNachlass`, Szene `stash.anabiHoert`), Block `selftest`
- Test: Block `selftest`

**Interfaces:**
- Produces: Event `anabiHoert` (once, night, `{ var: 'ruf', gte: 8 }`); `fns.anabiNachlass(s) → { toast }` (Kredit auf volle Tausend halbiert, Zorn 0); Szene `stash.anabiHoert`.

- [ ] **Step 1: Failing Tests schreiben**

Hinter dem Wache-Test einfügen:

```js
T.test('STORY_STASH: Anabi hört zu ab Ruf 8 (once) – Annehmen halbiert Kredit auf volle Tausend und setzt Zorn 0; Ablehnen Ruf +1', () => {
  const nightIds = (s) => stashHook(s, 'night', seq(0.99, 0.99, 0.99))[0];
  const s = stashState({ balance: 5000 }); s.story.day = 18; s.story.vars.woche = 3; s.story.vars.ruf = 7; s.story.vars.kredit = 7000; s.story.vars.zorn = 2; s.story.flags.bahnhofNein = true;
  T.eq(nightIds(s).includes('anabiHoert'), false);
  s.story.vars.ruf = 8; s.story.day = 19; T.ok(nightIds(s).includes('anabiHoert'));   // stashHook markiert once
  stashChoose(s, 'stash.anabiHoert', 'ja'); T.eq(s.story.vars.kredit, 4000, '7.000 → 4.000 (auf volle Tausend)'); T.eq(s.story.vars.zorn, 0);
  s.story.day = 20; T.eq(nightIds(s).includes('anabiHoert'), false, 'once');
  const t = stashState(); t.story.vars.kredit = 10000; STORY_STASH.fns.anabiNachlass(t); T.eq(t.story.vars.kredit, 5000);
  const z = stashState(); z.story.vars.kredit = 0; T.ok(STORY_STASH.fns.anabiNachlass(z).toast); T.eq(z.story.vars.kredit, 0, 'ohne Kredit bleibt 0');
  const n = stashState(); n.story.vars.ruf = 8; n.story.vars.kredit = 7000; stashChoose(n, 'stash.anabiHoert', 'nein'); T.eq(n.story.vars.ruf, 9); T.eq(n.story.vars.kredit, 7000);
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|fehlgeschlagen"`
Expected: `FAIL STORY_STASH: Anabi hört zu …` (Event fehlt).

- [ ] **Step 3: Event, fns, Szene**

Events: hinter der `wache`-Zeile aus Task 5 einfügen:

```js
    { id: 'anabiHoert', when: { var: 'ruf', gte: 8 }, once: true, at: 'night', scene: 'stash.anabiHoert' },
```

`fns` (hinter `wacheNacht`):

```js
    /* Anabi hört zu (Legende): Kredit auf volle Tausend halbiert, Zorn 0 */
    anabiNachlass(s) {
      const v = s.story.vars;
      v.kredit = Math.round((v.kredit || 0) / 2 / 1000) * 1000; v.zorn = 0;
      return { toast: { icon: '🤝', title: 'Kredit halbiert', text: `Zettel jetzt ${StoryRules.fmtMoney(v.kredit)}. Zorn: null.`, tone: 'win' } };
    },
```

Szene: vor `'stash.angebot': (ctx) => [` einfügen:

```js
    'stash.anabiHoert': [
      { bg: 'keller', who: 'du', mood: 'calm', cast: ['du'], text: 'Kein Igor, kein Anruf. Anabi kommt selbst. Er setzt sich an den Tisch, an dem sonst gezählt wird, und zählt nichts.' },
      { bg: 'keller', who: 'anabi', mood: 'calm', enter: 'anabi', text: 'Am Bahnhof sagen sie deinen Namen, bevor sie meinen sagen. Ich habe das lange nicht gehört. Bei niemandem.' },
      { bg: 'keller', who: 'anabi', mood: 'calm', cam: 'close', text: 'So einen Namen kauft man nicht. Man hält ihn. Ich streiche die Hälfte vom Zettel und vergesse, worüber ich mich geärgert habe. Einmal.',
        choices: [
          { label: 'Annehmen', value: 'ja', cls: 'red', effects: [{ call: 'anabiNachlass' }] },
          { label: 'Ablehnen', value: 'nein', cls: 'ghost', effects: [{ var: 'ruf', add: 1 }] },
        ] },
      { bg: 'keller', who: 'anabi', mood: 'calm', text: 'Er steht auf. An der Treppe dreht er sich nicht um. Wer sich nicht umdreht, hat verstanden, was er gesehen hat.' },
    ],
```

(Wie in Task 3: `enter: 'anabi'` weglassen, falls `validatePanels` es ablehnt.)

- [ ] **Step 4: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh`
Expected: `… 0 fehlgeschlagen`, `failed=0`.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(ruf): Story 3 – Anabi hört zu (Ruf 8): Kredit halbiert, Zorn 0

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Playtest-Szenario, Screenshots, README

**Files:**
- Modify: `tests/playtest-story.py` (neues `scenario_ruf`, Aufruf in `main()` hinter `await scenario_sicbo(cdp)`), `README.md` (Story-1-Absatz „Enden", Story-3-Absatz)
- Create: `docs/superpowers/screenshots/ruf-wache.png`, `ruf-anabi.png`, `ruf-vito.png`

**Interfaces:**
- Consumes: CDP-Helfer `cdp.navigate`, `cdp.inject_helpers`, `cdp.eval`, `cdp.wait_for`, `cdp.advance_cutscene`, `cdp.screenshot`, `record`; die Muster `settle()` und `click_choice()` aus `scenario_stash`/`scenario_kater` (lokale Hilfsfunktionen – im neuen Szenario erneut definieren, sie sind dort verschachtelt).

- [ ] **Step 1: Szenario schreiben**

Vor `async def scenario_roulette_chips(cdp):` einfügen:

```python
async def scenario_ruf(cdp):
    """Ruf-Stufen: Wache (Ruf 5) und Anabi (Ruf 8) in Story 3, Vitos Respekt (Ruf 5) in Story 1, HUD-Titel."""

    async def settle(max_rounds=60):
        for _ in range(max_rounds):
            if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                await cdp.advance_cutscene(max_steps=4)
            sleeping = await cdp.eval("Story.sleeping", await_promise=False)
            cs = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            busy = await cdp.eval("UI.busy", await_promise=False)
            if not sleeping and not cs and not busy:
                return True
            await asyncio.sleep(0.15)
        return False

    async def click_choice(hint, max_steps=8):
        for _ in range(max_steps):
            if not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                return False
            found = await cdp.eval(
                "(function(){var b=[...document.querySelectorAll('.cs-choices button')].find(function(x){return x.textContent.includes(%s)}); if(!b) return false; b.click(); return true;})()" % json.dumps(hint),
                await_promise=False)
            if found:
                return True
            await cdp.eval("__pt.advance(null)", await_promise=False)
            await asyncio.sleep(0.15)
        return False

    async def night_and_choose(label, shot=None, max_steps=20):
        """Schlafen, warten bis eine Cutscene läuft, bis zum Choice-Button mit label vorklicken (Screenshot, sobald er da ist), klicken, Nacht zu Ende bringen."""
        await cdp.eval("Story.evening()")
        await asyncio.sleep(0.3)
        await cdp.eval("Story.night()", await_promise=False)
        await cdp.wait_for("__pt.cutsceneActive()", timeout=6.0)
        for _ in range(max_steps):
            if not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                return False
            there = await cdp.eval("[...document.querySelectorAll('.cs-choices button')].some(b => b.textContent.includes(%s))" % json.dumps(label), await_promise=False)
            if there:
                break
            await cdp.eval("__pt.advance(null)", await_promise=False)
            await asyncio.sleep(0.15)
        if shot:
            await asyncio.sleep(0.3)
            await cdp.screenshot(shot)
        ok = await click_choice(label, max_steps=2)
        await settle()
        return ok

    # Story 3, Tag 16 (keine Lieferung, kein Kessler-Angebot dank bahnhofNein), Ruf 5 → Wache.
    # Überfall/Hinterhalt vor der Annahme ausschalten, damit die Nacht deterministisch ist.
    await cdp.navigate(URL_BASE + "?fresh&story=stash&prev=wirt&day=16")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=20)
    await cdp.wait_for("State.mode === 'story' && Story.s && Story.s.day === 16 && UI.current && !UI.busy", timeout=6.0)
    await cdp.eval("Story.s.vars.ruf = 5; Story.s.flags.bahnhofNein = true; State.s.balance = 3000; GangRules.RAID.base = 0; GangRules.AMBUSH.base = 0; State.save(); UI.renderWallet();", await_promise=False)
    hud = await cdp.eval("[...document.querySelectorAll('#notes .note')].map(n => n.textContent)", await_promise=False) or []
    record("ruf: HUD zeigt Respektiert 5/10", any("Respektiert 5/10" in t for t in hud), str(hud))
    ok = await night_and_choose("Annehmen", shot="ruf-wache")
    v = await cdp.eval("({ wache: !!Story.s.flags.wache, balance: State.s.balance, day: Story.s.day, goal: (document.querySelector('#daybarSlot') || {}).textContent || '' })", await_promise=False)
    record("ruf: Wache-Szene bei Ruf 5, angenommen; Tagesleiste nennt Wache", ok and v["wache"] and v["day"] == 17 and "Wache" in v["goal"], str(v))
    # Ruf 8 → Anabi; in derselben Nacht kostet die Wache erstmals 200 €
    await cdp.eval("Story.s.vars.ruf = 8; Story.s.vars.kredit = 7000; Story.s.vars.zorn = 2; State.save(); UI.renderWallet();", await_promise=False)
    ok = await night_and_choose("Annehmen", shot="ruf-anabi")
    v = await cdp.eval("({ kredit: Story.s.vars.kredit, zorn: Story.s.vars.zorn, balance: State.s.balance, hud: [...document.querySelectorAll('#notes .note')].map(n => n.textContent).join(' | ') })", await_promise=False)
    record("ruf: Anabi bei Ruf 8 – Kredit 4.000, Zorn 0, Wache 200 € abgezogen, HUD Legende", ok and v["kredit"] == 4000 and v["zorn"] == 0 and v["balance"] == 2800 and "Legende" in v["hud"], str(v))
    # Story 1, Tag 12, Ruf 5 → Vito, ablehnen
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=12")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=20)
    await cdp.wait_for("State.mode === 'story' && Story.s && Story.s.day === 12 && UI.current && !UI.busy", timeout=6.0)
    await cdp.eval("Story.s.vars.ruf = 5; State.save(); UI.renderWallet();", await_promise=False)
    ok = await night_and_choose("Ablehnen", shot="ruf-vito")
    v = await cdp.eval("({ ruf: Story.s.vars.ruf, schuld: Story.s.vars.schuld, hud: [...document.querySelectorAll('#notes .note')].map(n => n.textContent).join(' | ') })", await_promise=False)
    record("ruf: Vito bei Ruf 5 abgelehnt → Ruf 6, Schuld unverändert, HUD Respektiert", ok and v["ruf"] == 6 and v["schuld"] == 50000 and "Respektiert 6/10" in v["hud"], str(v))
```

Hinweise für die Umsetzung: Die Cutscene-Engine merkt sich keine Szenen-ID, darum wird die Szene über ihre Wirkung geprüft (Flag/Var nach der Wahl). Der Selektor `#notes .note` folgt `Story.hudNotes` (`qs('#notes')`, Klasse `note`); die Tagesleiste wird in `#daybarSlot` gerendert. `?day=16` bei `stash` richtet die Woche über `devWoche` ein; `bahnhofNein` verhindert das Kessler-Angebot (das dieselben Button-Labels hat). `GangRules.RAID.base = 0` / `AMBUSH.base = 0` gelten nur für diesen Seitenaufruf. Die Screenshots entstehen in `night_and_choose`, sobald der Wahl-Button sichtbar ist – also mitten in der Szene.

In `main()` hinter `        await scenario_sicbo(cdp)` einfügen: `        await scenario_ruf(cdp)`.

- [ ] **Step 2: Playtest nur mit diesem Szenario laufen lassen**

Der Playtest kennt keinen Szenario-Filter; für den Lauf temporär alle anderen Aufrufe in `main()` auskommentieren ist fehleranfällig. Stattdessen den kompletten Playtest laufen lassen:

Run: `python3 tests/playtest-story.py 2>&1 | tail -15`
Expected: `Checks: N, davon fehlgeschlagen: 0` und `ERRORS 0`; Screenshots in `/tmp/k37shots` (bzw. `K37_SHOTS`).

- [ ] **Step 3: Screenshots ins Repo, Handy-Check**

```bash
cp /tmp/k37shots/ruf-wache.png /tmp/k37shots/ruf-anabi.png /tmp/k37shots/ruf-vito.png docs/superpowers/screenshots/
python3 tests/mobile-check.py 2>&1 | tail -3
```

Expected: `… 0 fehlgeschlagen`. Falls die HUD-Zeile in Story 3 (vier Notes) auf dem Handy Überbreite meldet: `.note` im Story-HUD bekommt in der `≤ 760 px`-Media-Query `white-space: normal` bzw. die Zeile `flex-wrap: wrap` – erst dann ist der Task fertig.

- [ ] **Step 4: README**

Im Absatz `- **Enden:** Story 1 „Die Schuld" …` hinter dem Satz, der bei „mehr wird hier nicht verraten." endet, ergänzen:

```
  Ruf hat vier Stufen (Niemand · Bekannt ab 2 · Respektiert ab 5 · Legende ab 8, Titel im HUD, Toast beim Wechsel). Ab
  „Respektiert" macht Vito ein Angebot (10.000 € vom Zettel gegen seinen Namen – oder ablehnen und Ruf +1), ab „Legende"
  setzt sich Igor abends zu dir und zweifelt an seinem Chef – ein zweiter Weg zum „Sturz" neben den drei Duellsiegen.
```

Im Absatz `- **Story 3 „Die Wäsche":** …` hinter „… alles generisch für spätere Stories nutzbar." ergänzen:

```
  Ruf (🔥 im HUD, dieselben vier Stufen wie in Story 1) wächst hier durch saubere Wochenabrechnungen, Eintreiber-Schichten,
  Kredit-Raten und die erste Reparatur je Woche – nicht nur durch Duelle. Ab „Respektiert" bieten zwei Bahnhof-Jungs die
  Wache an (200 € je Nacht, keine Tür geht mehr kaputt; ist die Kasse leer, gehen sie), ab „Legende" kommt Anabi selbst
  und halbiert den Zettel (Zorn auf null) – die Ablöse wird bezahlbar.
```

- [ ] **Step 5: Alle Tests, Commit**

```bash
node tests/run-selftest.mjs 2>&1 | tail -1 && sh tests/dom-selftest.sh
git add tests/playtest-story.py docs/superpowers/screenshots/ruf-wache.png docs/superpowers/screenshots/ruf-anabi.png docs/superpowers/screenshots/ruf-vito.png README.md keller37.html
git commit -m "test(ruf): Playtest-Szenario Ruf-Stufen, Screenshots; docs(ruf): README Story 1 und 3

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

`keller37.html` steht im `git add` nur für den Fall der Handy-CSS-Anpassung aus Step 3; ohne Änderung ist das harmlos.
