# Cutscene-Bühne (Stufe 1) – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Cutscenes von KELLER 37 bekommen eine Bühne mit SVG-Comic-Figuren (inkl. Protagonist mit Ausrüstung und Zustand), lebenden Kulissen, Sprechblasen und einer Auto-Regie plus optionalen Regie-Schlüsseln – ohne dass Story-Texte, Wahl-Buttons oder die `Cutscene.play/define/bind`-Schnittstelle sich ändern.

**Architecture:** Drei neue DOM-freie Script-Blöcke in `keller37.html` liefern reine Daten/Strings: `cutscene-director` (`CsDirector.stagePlan` = Auto-Regie als reine Funktion, `validatePanels`), `cutscene-cast` (`CsCast.CAST` mit Looks, `figureHtml` = Figur aus acht gestapelten Teil-SVGs, `duParts`), `cutscene-sets` (`CsSets.SETS` = 16 Kulissen als SVG-Strings). Der bestehende Block `cutscene-engine` wird zur Bühnen-Engine umgebaut (Ebenen, Figuren per `transform`, eine Sprechblase am Sprecher, Kamera, Skip-Endzustand). CSS-Abschnitt 5 wird ersetzt. Alle Bewegung nur `transform`/`opacity`; jedes bewegliche Figurenteil ist ein eigenes HTML-Element (`<svg>`), weil CSS-Transforms auf SVG-*Kindknoten* nicht vom Compositor übernommen werden (im Prototyp: 38 Repaints/s der Figur → 0).

**Tech Stack:** Vanilla JS/CSS/Inline-SVG in einer Datei, Node-Selbsttest (`node tests/run-selftest.mjs`), Headless-Chrome-Selbsttest (`tests/dom-selftest.sh`), CDP-Playtest (`python3 tests/playtest-story.py`), Trace (`python3 tests/perf-trace.py`).

**Spec:** `docs/superpowers/specs/2026-09-20-cutscene-buehne-design.md`

Die Code-Blöcke dieses Plans wurden in einem Wegwerf-Prototyp gegen den aktuellen Stand verifiziert (Node 291/291, DOM 322/322, Playtest grün außer Pixel-Diff-Checks ohne Referenzbilder). Sie sind wörtlich zu übernehmen; wo der Plan „ersetzen" sagt, ist der alte Code vollständig zu entfernen.

## Global Constraints

- Eine Datei `keller37.html`, keine Bilddateien, keine externen Abhängigkeiten. Grafik ausschließlich Inline-SVG oder CSS.
- `Cutscene.play(id, ctx)`, `Cutscene.define(id, panels)`, `Cutscene.bind(event, sceneId)`, Rückgabewerte (Wahl-`value`, `Cutscene.SKIP`) und `Cutscene.active` bleiben unverändert. Story-Texte, Wahl-Buttons, Klick-/Tasten-Bedienung (Klick/Leertaste/Enter = weiter, Klick ins Tippen = Text komplett), Überspringen bleiben wie heute.
- Bewegung ausschließlich über `transform` und `opacity`. Kein Layout- oder Paint-Trigger pro Frame außer der Schreibmaschine. Jedes `@keyframes cs*` darf nur `transform`/`opacity` animieren (DOM-Test).
- `prefers-reduced-motion: reduce` und `Cutscene.instant = true` verhalten sich gleich: keine Laufwege, keine Kulissen-Animation, keine Kamera-Fahrt, Text sofort komplett.
- Deutsche Spieltexte; Kommentare im Code auf Deutsch wie im Rest der Datei.
- Commit-Trailer: `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`. Kein Push, kein Merge nach main ohne ausdrückliche Freigabe des Auftraggebers.
- `main` bewegt sich parallel (andere Instanz). Vor Task 1 auf den aktuellen `main` aufsetzen; falls `_fx` in `cutscene-engine` inzwischen weitere `case`-Zweige hat als die im Plan genannten (`flash, shake, blackout, hearts, coins, drain, gain, stats, insiderCards`), diese in die neue Engine übernehmen **und** in `CsDirector.FX` eintragen.

---

## Dateistruktur

Alles in `keller37.html`; die Reihenfolge der Script-Blöcke ist wichtig, weil `cutscene-engine` die drei neuen Blöcke referenziert:

| Stelle | Inhalt | Verantwortung |
|---|---|---|
| CSS `/* ==== 5. CUTSCENE ==== */` … bis vor `/* ==== 6. SPIELE & RÄUME ==== */` | wird komplett ersetzt | Bühne, Figuren, Posen, Blase, Streifen, Kulissen-Leben, Mobil, reduced-motion |
| `<script id="cutscene-director">` (neu, direkt vor `cutscene-engine`) | `CsDirector` | Auto-Regie (`stagePlan`) und Regie-Validierung (`validatePanels`) – DOM-frei |
| `<script id="cutscene-cast">` (neu, danach) | `CsCast` | Cast-Register mit Looks, `figureHtml`, `duParts` – DOM-frei |
| `<script id="cutscene-sets">` (neu, danach) | `CsSets` | 16 Kulissen als SVG-Strings – DOM-frei |
| `<script id="cutscene-engine">` | `Cutscene` (Objekt bis zur Zeile `/* ---- Szenen: Intro & Neues Spiel ---- */`) | Bühnen-Engine; die Szenen-Definitionen darunter bleiben |
| `<script id="selftest">` | neue Tests | Node-Tests hinter den Story-Rules-Tests, DOM-Tests im Block `if (typeof Story !== 'undefined' && typeof document !== 'undefined')` |
| `tests/run-selftest.mjs` | Blockliste | lädt die drei neuen Blöcke |
| `tests/playtest-story.py` | Selektoren | `.cs-bg` → `.cs-sky`, `.cs-box` → `.cs-bubble` |
| `README.md`, `docs/superpowers/specs/2026-09-20-cutscene-buehne-design.md` | Doku | Regie-Schlüssel, Tests, Abweichung „Teil-SVGs" |

Hilfreiche Fundstellen (Zeilennummern Stand Plan, per `grep` prüfen): CSS-Abschnitt 5 `grep -n "==== 5. CUTSCENE"`; Engine `grep -n '<script id="cutscene-engine">'`; Ende des Engine-Objekts `grep -n "Szenen: Intro & Neues Spiel"`; Node-Tests-Einfügepunkt `grep -n "Story-Engine (nur im Browser"`; DOM-Tests-Einfügepunkt `grep -n "const pseudoAnim = "`; alter Props-Test `grep -n "Cutscene.PROPS.bahnhof"`; reduced-motion-Liste `grep -n "\.neon, \.cs-portrait"`; `royal-frame` `grep -n "cs-portrait.royal-frame"`.

---

### Task 1: Regie-Planer `CsDirector` (DOM-frei) + Test-Runner

**Files:**
- Modify: `keller37.html` – neuer Block `<script id="cutscene-director">` direkt vor `<script id="cutscene-engine">`
- Modify: `keller37.html` – Node-Tests im Block `selftest`, eingefügt direkt vor der Zeile `/* ---- Story-Engine (nur im Browser – Block story-engine wird in Node nicht geladen) ---- */`
- Modify: `tests/run-selftest.mjs` – Blockliste

**Interfaces:**
- Produces: `CsDirector.stagePlan(panels) → Plan[]` mit `Plan = { bg, bgChange, speaker, cast: [{ who, slot: 'left'|'mid'|'right'|'far', facing: 1|-1, pose, mood }], enter: [{ who, from: 'left'|'right' }], exit: [who], cam: 'close'|'wide'|'shake'|null, shout: string|null, pause: number, sfx: string|null, look: object|null }`; `CsDirector.validatePanels(id, panels, { castIds, sfxIds }) → string[]`; `CsDirector.side(who)`; Konstanten `SLOTS, POSES, CAMS, MOODS, HURTS, KEYS, FX, MAX_ON_STAGE`.

- [ ] **Step 1: Blockliste des Node-Runners erweitern**

In `tests/run-selftest.mjs` die Zeile mit der Blockliste ändern – `'cutscene-director', 'cutscene-cast', 'cutscene-sets'` hinter `'dev-rules'` einfügen:

```js
for (const id of ['rules', 'gear-rules', 'perk-rules', 'util', 'state', 'bus', 'story-rules', 'royal-rules', 'baccarat-rules', 'gang-rules', 'dev-rules', 'cutscene-director', 'cutscene-cast', 'cutscene-sets', 'story-probe', 'story-schuld', 'story-kater', 'story-stash', 'selftest']) {
```

(Der Runner überspringt fehlende Blöcke, daher darf die Liste schon vor Task 2/3 alle drei nennen.)

- [ ] **Step 2: Fehlschlagende Tests schreiben**

Im Block `selftest` direkt vor `/* ---- Story-Engine (nur im Browser – Block story-engine wird in Node nicht geladen) ---- */` einfügen – nur den `CsDirector`-Teil (die `CsCast`-/`CsSets`-Teile kommen in Task 2/3 an dieselbe Stelle):

```js
/* ---- Cutscene-Bühne: Regie-Planer, Figuren, Kulissen (DOM-frei) ---- */
if (typeof CsDirector !== 'undefined') {
  T.test('stagePlan: du links, Sprecher rechts, Auftritt von der eigenen Seite, Stimmung → Pose', () => {
    const plan = CsDirector.stagePlan([
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'a' },
      { bg: 'bar', who: 'du', mood: 'happy', text: 'b' },
      { bg: 'bar', who: 'vito', mood: 'angry', text: 'c' },
    ]);
    T.eq(plan[0].cast.map((c) => `${c.who}@${c.slot}`), ['du@left', 'wirt@right']);
    T.eq(plan[0].enter, [{ who: 'du', from: 'left' }, { who: 'wirt', from: 'right' }]);
    T.eq(plan[0].cast[1].pose, 'talk'); T.eq(plan[0].cast[0].pose, 'idle');
    T.eq(plan[0].cast[0].facing, 1); T.eq(plan[0].cast[1].facing, -1);
    T.eq(plan[0].speaker, 'wirt'); T.eq(plan[0].bg, 'bar'); T.eq(plan[0].cam, null);
    T.eq(plan[1].enter, []); T.eq(plan[1].cast[0].pose, 'talk'); T.eq(plan[1].cast[0].mood, 'happy');
    T.eq(plan[2].enter, [{ who: 'vito', from: 'right' }]); T.eq(plan[2].cast[2].slot, 'mid'); T.eq(plan[2].cast[2].pose, 'point');
    T.eq(plan[2].cast[1].mood, 'calm', 'Nicht-Sprecher neutral'); T.eq(plan[2].cast[1].pose, 'idle');
  });
  T.test('stagePlan: vierte Figur → die am längsten stumme Nebenfigur geht', () => {
    const plan = CsDirector.stagePlan([
      { bg: 'bar', who: 'wirt', text: 'a' }, { bg: 'bar', who: 'vito', text: 'b' }, { bg: 'bar', who: 'igor', text: 'c' },
    ]);
    T.eq(plan[2].exit, ['wirt']);
    T.eq(plan[2].cast.map((c) => c.who).sort(), ['du', 'igor', 'vito']);
    T.eq(plan[2].cast.find((c) => c.who === 'igor').slot, 'right', 'freier Platz rechts');
  });
  T.test('stagePlan: Kulissenwechsel → alle treten neu auf, Kamera zurück; cast: [] leert die Bühne; enter/exit/walk/pose/look', () => {
    const plan = CsDirector.stagePlan([
      { bg: 'bar', who: 'wirt', text: 'a' },
      { bg: 'keller', who: 'vito', mood: 'shock', text: 'b', cam: 'close' },
      { bg: 'keller', who: 'vito', text: 'c', enter: { who: 'igor', from: 'left' }, walk: { who: 'igor', to: 'far' }, pose: { who: 'du', pose: 'arms-crossed' }, look: { du: { hurt: 'pflaster' } }, shout: 'HEY', pause: 300, sfx: 'gunshot' },
      { bg: 'keller', who: 'vito', text: 'd', exit: 'igor' },
      { bg: 'strasse', who: 'du', text: 'e', cast: [] },
    ]);
    T.eq(plan[1].bgChange, true); T.eq(plan[1].exit.sort(), ['du', 'wirt']); T.eq(plan[1].enter.map((e) => e.who), ['du', 'vito']); T.eq(plan[1].cam, 'close'); T.eq(plan[1].cast[1].pose, 'flinch');
    T.eq(plan[2].enter, [{ who: 'igor', from: 'left' }]);
    T.eq(plan[2].cast.find((c) => c.who === 'igor').slot, 'far');
    T.eq(plan[2].cast.find((c) => c.who === 'du').pose, 'arms-crossed'); T.eq(plan[2].look, { du: { hurt: 'pflaster' } });
    T.eq([plan[2].shout, plan[2].pause, plan[2].sfx], ['HEY', 300, 'gunshot']);
    T.eq(plan[3].exit, ['igor']); T.eq(plan[3].cast.length, 2);
    T.eq(plan[4].cast, []); T.eq(plan[4].exit.sort(), ['du', 'vito']); T.eq(plan[4].cam, 'wide'); T.eq(plan[4].speaker, 'du');
  });
  T.test('stagePlan: dead bleibt liegen, Sprecher-Pose überschreibbar, unbekannter Sprecher = du', () => {
    const plan = CsDirector.stagePlan([{ bg: 'gasse', who: 'du', mood: 'dead', text: 'a' }, { bg: 'gasse', who: 'raeuber', text: 'b' }, { bg: 'gasse', who: 'du', pose: 'hands-up', text: 'c' }, { bg: 'gasse', text: 'd' }]);
    T.eq(plan[0].cast[0].pose, 'down'); T.eq(plan[1].cast[0].pose, 'down'); T.eq(plan[1].cast[0].mood, 'dead'); T.eq(plan[2].cast[0].pose, 'hands-up');
    T.eq(plan[3].speaker, 'du');
  });
  T.test('validatePanels: gültige Panels ohne Fehler; unbekannte Schlüssel, Figuren, Posen, Kameras, Sounds, look.hurt sind Fehler', () => {
    const ok = [{ bg: 'bar', who: 'du', mood: 'calm', text: 'x', fx: 'flash', cast: ['du'], enter: { who: 'vito', from: 'right' }, exit: 'igor', walk: { who: 'du', to: 'mid' }, pose: 'point', cam: 'close', shout: 'PÄNG!', pause: 300, sfx: 'gunshot', look: { du: { hurt: 'pflaster' } }, choices: [{ label: 'a', value: 1 }] }];
    T.eq(CsDirector.validatePanels('ok', ok, { castIds: ['du', 'vito', 'igor'], sfxIds: ['gunshot'] }), []);
    T.eq(CsDirector.validatePanels('ok', ok), [], 'ohne Listen: nur Struktur');
    const errs = CsDirector.validatePanels('t', [{ bg: 'bar', who: 'nix', foo: 1, mood: 'sad', fx: 'boom', cam: 'zoom', pose: { who: 'du', pose: 'fly' }, walk: { who: 'du', to: 'oben' }, look: { du: { hurt: 'x' } }, sfx: 'boom', pause: -1, enter: { who: 'du', from: 'oben' } }], { castIds: ['du'], sfxIds: ['gunshot'] });
    for (const needle of ['"foo"', '"nix"', 'mood "sad"', 'fx "boom"', 'cam "zoom"', 'pose "fly"', 'walk.to "oben"', 'look.hurt "x"', 'sfx "boom"', 'pause', 'enter.from "oben"']) T.ok(errs.some((e) => e.includes(needle)), needle);
    T.ok(errs.every((e) => e.startsWith('t[0]: ')), 'Szene und Panel-Index im Fehler');
  });
}
```

- [ ] **Step 3: Tests laufen lassen – sie müssen (noch) still übersprungen werden**

Run: `node tests/run-selftest.mjs`
Expected: gleiche Anzahl bestanden wie vor der Änderung (der `if (typeof CsDirector !== 'undefined')`-Wächter überspringt die Tests, solange der Block fehlt). Dann kurz den Wächter auf `if (true)` setzen, laufen lassen: FAIL mit `CsDirector is not defined`; Wächter zurücksetzen.

- [ ] **Step 4: Block `cutscene-director` einfügen**

Direkt vor `<script id="cutscene-engine">`:

```html
<script id="cutscene-director">
/* ================= CUTSCENE DIRECTOR – Auto-Regie als reine Funktion (DOM-frei, testbar) ================= */
const CsDirector = {
  SLOTS: ['left', 'mid', 'right', 'far'],
  POSES: ['idle', 'talk', 'point', 'arms-crossed', 'hands-up', 'walk', 'down', 'flinch'],
  CAMS: ['close', 'wide', 'shake'],
  MOODS: ['calm', 'angry', 'happy', 'shock', 'dead'],
  HURTS: ['pflaster', 'kruecke'],
  SIDES: ['left', 'right'],
  KEYS: ['bg', 'who', 'mood', 'text', 'fx', 'choices', 'cast', 'enter', 'exit', 'walk', 'pose', 'cam', 'shout', 'pause', 'sfx', 'look'],
  FX: ['flash', 'shake', 'blackout', 'hearts', 'coins', 'drain', 'gain', 'stats', 'insiderCards'],
  MAX_ON_STAGE: 3,
  /* Stimmung des Sprechers → Körperhaltung */
  moodPose(mood) { return { angry: 'point', shock: 'flinch', dead: 'down' }[mood] || 'talk'; },
  /* Von welcher Seite eine Figur kommt/geht: du von links, alle anderen von rechts */
  side(who) { return who === 'du' ? 'left' : 'right'; },
  /* Platz nach Reihenfolge: du links, erstes Gegenüber rechts, drittes mittig */
  slotFor(who, on) {
    if (who === 'du') return 'left';
    const taken = on.filter((f) => f.who !== who).map((f) => f.slot);
    return taken.includes('right') ? 'mid' : 'right';
  },
  facing(slot, speakerSlot) {
    if (slot === 'left') return 1;
    if (slot === 'right') return -1;
    return speakerSlot === 'right' ? 1 : -1;
  },
  /* panels → je Panel ein Plan: { bg, bgChange, speaker, cast: [{ who, slot, facing, pose, mood }], enter: [{ who, from }], exit: [who], cam, shout, pause, sfx, look } */
  stagePlan(panels) {
    let on = [];            // Figuren auf der Bühne, in Auftrittsreihenfolge: { who, slot, pose, lastSpoke }
    let prevBg = null;
    return panels.map((p, i) => {
      const who = p.who || 'du', bg = p.bg || 'bar';
      const bgChange = i === 0 || bg !== prevBg;
      prevBg = bg;
      const enter = [], exit = [];
      const add = (id, from) => { if (on.some((f) => f.who === id)) return; on.push({ who: id, slot: null, pose: 'idle', lastSpoke: -1 }); enter.push({ who: id, from: from || this.side(id) }); };
      const remove = (id) => { if (!on.some((f) => f.who === id)) return; on = on.filter((f) => f.who !== id); exit.push(id); };
      if (bgChange) { for (const f of on) exit.push(f.who); on = []; }   // Kulissenwechsel: alle gehen ab und treten neu auf
      if (p.cast) {                                                 // explizite Besetzung
        for (const f of on.map((f) => f.who)) if (!p.cast.includes(f)) remove(f);
        for (const id of p.cast) add(id);
      } else {
        add('du');
        add(who);
      }
      for (const e of [].concat(p.enter || [])) add(typeof e === 'string' ? e : e.who, typeof e === 'string' ? null : e.from);
      for (const id of [].concat(p.exit || [])) remove(id);
      if (!p.cast && !on.some((f) => f.who === who)) add(who);
      while (on.length > this.MAX_ON_STAGE) {                       // die am längsten stumme Nebenfigur geht
        const cand = on.filter((f) => f.who !== 'du' && f.who !== who).sort((a, b) => a.lastSpoke - b.lastSpoke)[0];
        if (!cand) break;
        remove(cand.who);
      }
      for (const f of on) if (!f.slot) f.slot = this.slotFor(f.who, on);
      if (p.walk) { const f = on.find((f) => f.who === p.walk.who); if (f) f.slot = p.walk.to; }
      const speaker = on.find((f) => f.who === who);
      if (speaker) speaker.lastSpoke = i;
      const poseOverride = p.pose && typeof p.pose === 'object' ? p.pose : null;
      for (const f of on) {
        const isSpeaker = f.who === who;
        if (isSpeaker) f.pose = typeof p.pose === 'string' ? p.pose : this.moodPose(p.mood || 'calm');
        else if (f.pose !== 'down') f.pose = 'idle';
        if (poseOverride && poseOverride.who === f.who) f.pose = poseOverride.pose;
        f.mood = isSpeaker ? (p.mood || 'calm') : (f.mood === 'dead' ? 'dead' : 'calm');
      }
      const speakerSlot = speaker ? speaker.slot : 'right';
      return {
        bg, bgChange, speaker: who,
        cast: on.map((f) => ({ who: f.who, slot: f.slot, facing: this.facing(f.slot, speakerSlot), pose: f.pose, mood: f.mood })),
        enter, exit,
        cam: p.cam || (bgChange && i > 0 ? 'wide' : null),
        shout: p.shout || null, pause: p.pause || 0, sfx: p.sfx || null, look: p.look || null,
      };
    });
  },
  /* Regie-Schlüssel prüfen: unbekannte Schlüssel, Figuren, Posen, Kameras, Sounds sind Fehler */
  validatePanels(id, panels, { castIds = null, sfxIds = null } = {}) {
    const errs = [];
    const err = (i, msg) => errs.push(`${id}[${i}]: ${msg}`);
    const cast = (i, who, where) => { if (typeof who !== 'string' || (castIds && !castIds.includes(who))) err(i, `Figur "${who}" unbekannt (${where})`); };
    panels.forEach((p, i) => {
      for (const k of Object.keys(p)) if (!this.KEYS.includes(k)) err(i, `Schlüssel "${k}" unbekannt`);
      if (p.who != null) cast(i, p.who, 'who');
      if (p.mood != null && !this.MOODS.includes(p.mood)) err(i, `mood "${p.mood}" unbekannt`);
      if (p.fx != null && !this.FX.includes(p.fx)) err(i, `fx "${p.fx}" unbekannt`);
      if (p.cast != null) { if (!Array.isArray(p.cast)) err(i, 'cast muss ein Array sein'); else p.cast.forEach((w) => cast(i, w, 'cast')); }
      for (const e of [].concat(p.enter || [])) {
        if (typeof e === 'string') cast(i, e, 'enter');
        else { cast(i, e && e.who, 'enter'); if (e && e.from != null && !this.SIDES.includes(e.from)) err(i, `enter.from "${e.from}" unbekannt`); }
      }
      for (const e of [].concat(p.exit || [])) cast(i, e, 'exit');
      if (p.walk != null) { cast(i, p.walk.who, 'walk'); if (!this.SLOTS.includes(p.walk.to)) err(i, `walk.to "${p.walk.to}" unbekannt`); }
      if (p.pose != null) {
        const pose = typeof p.pose === 'string' ? p.pose : p.pose.pose;
        if (typeof p.pose === 'object') cast(i, p.pose.who, 'pose');
        if (!this.POSES.includes(pose)) err(i, `pose "${pose}" unbekannt`);
      }
      if (p.cam != null && !this.CAMS.includes(p.cam)) err(i, `cam "${p.cam}" unbekannt`);
      if (p.shout != null && typeof p.shout !== 'string') err(i, 'shout muss Text sein');
      if (p.pause != null && !(typeof p.pause === 'number' && p.pause >= 0)) err(i, 'pause muss eine Zahl ≥ 0 sein');
      if (p.sfx != null && sfxIds && !sfxIds.includes(p.sfx)) err(i, `sfx "${p.sfx}" unbekannt`);
      if (p.look != null) {
        if (typeof p.look !== 'object') err(i, 'look muss ein Objekt sein');
        else for (const [w, l] of Object.entries(p.look)) { cast(i, w, 'look'); if (l && l.hurt != null && !this.HURTS.includes(l.hurt)) err(i, `look.hurt "${l.hurt}" unbekannt`); }
      }
    });
    return errs;
  },
};
</script>

```

- [ ] **Step 5: Tests laufen lassen**

Run: `node tests/run-selftest.mjs`
Expected: `… bestanden, 0 fehlgeschlagen`, fünf Tests mehr als vorher.

- [ ] **Step 6: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(cutscene): Regie-Planer CsDirector – Auto-Regie als reine Funktion, Validierung der Regie-Schlüssel

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Figuren-Baukasten `CsCast` (DOM-frei)

**Files:**
- Modify: `keller37.html` – neuer Block `<script id="cutscene-cast">` direkt hinter `</script>` von `cutscene-director`
- Modify: `keller37.html` – Node-Tests (gleiche Einfügestelle wie Task 1, hinter den `CsDirector`-Tests)

**Interfaces:**
- Consumes: nichts (reine Strings).
- Produces: `CsCast.CAST` (20 Einträge mit `name, emoji, color, look`), `CsCast.MOODS`, `CsCast.SHOES`, `CsCast.duParts(s) → { shoes, weapon, suit, cheeks, sway, blackEye, rings }` (leeres Objekt bei `null`), `CsCast.figureHtml(who, { mood, parts, hurt }) → string` (`<div class="cs-fig-inner mood-<mood>[ sway][ klein]"><div class="cs-body">` + acht `<svg class="part …">` + `</div></div>`). Rig: viewBox `0 0 100 180`, Schultern (21,82)/(79,82), Kopfmitte (50,46), Mundmitte (50,61), Standlinie y = 172.

- [ ] **Step 1: Fehlschlagende Tests schreiben**

Hinter den `CsDirector`-Tests aus Task 1 einfügen:

```js
if (typeof CsCast !== 'undefined') {
  T.test('CsCast: alle Figuren haben einen Look; figureHtml liefert acht Teil-SVGs mit Rig-Klassen und allen Stimmungen', () => {
    for (const [id, c] of Object.entries(CsCast.CAST)) {
      T.ok(c.look && c.look.skin && c.look.cloth && ['normal', 'breit', 'schmal', 'klein'].includes(c.look.build), `Look ${id}`);
      const html = CsCast.figureHtml(id, { mood: 'angry' });
      T.ok(html.startsWith('<div class="cs-fig-inner mood-angry'), `${id}: Stimmungsklasse`);
      for (const part of ['legL', 'legR', 'body', 'armL', 'armR', 'head', 'eyes', 'mouth']) T.ok(html.includes(`<svg class="part ${part}" viewBox="0 0 100 180"`), `${id}: Teil ${part}`);
      T.eq((html.match(/<svg /g) || []).length, 8, `${id}: acht Teile`);
      for (const m of CsCast.MOODS) T.eq((html.match(new RegExp(`class="m m-${m}"`, 'g')) || []).length, 3, `${id}: Stimmung ${m} in Kopf, Augen, Mund`);
    }
  });
  T.test('CsCast: Hut, Extras, Statur und Fallback-Emoji landen im HTML', () => {
    const vito = CsCast.figureHtml('vito');
    T.ok(vito.includes('<rect x="32" y="42"'), 'Sonnenbrille'); T.ok(vito.includes('class="ember"'), 'Zigarre'); T.ok(vito.includes('fill="#b0202a"'), 'Krawatte');
    T.ok(CsCast.figureHtml('igor').includes('scale(1.22 1)'), 'breit'); T.ok(CsCast.figureHtml('chantal').includes('scale(0.86 1)'), 'schmal');
    T.ok(CsCast.figureHtml('kevin').includes('cs-fig-inner mood-calm klein'), 'klein');
    T.ok(CsCast.figureHtml('sylvie').includes('<rect x="32" y="2" width="36" height="30"'), 'Zylinder');
    T.ok(CsCast.figureHtml('doc').includes('cx="50" cy="100" r="4"'), 'Stethoskop');
    CsCast.CAST.testfig = { name: 'Test', emoji: '🦆', color: '#fff' };
    try { T.ok(CsCast.figureHtml('testfig').includes('🦆'), 'Emoji-Fallback ohne Look'); } finally { delete CsCast.CAST.testfig; }
    T.ok(CsCast.figureHtml('gibtsnicht').includes('fill="#8b1e1e"'), 'unbekannte ID → Look von du (rote Mütze)');
  });
  T.test('CsCast.duParts: Ausrüstung und Zustand aus dem Spielstand', () => {
    T.eq(CsCast.duParts({ beers: 0, beerTimer: 0, mafiaDebt: 0 }), { shoes: null, weapon: 0, suit: false, cheeks: false, sway: false, blackEye: false, rings: false });
    T.eq(CsCast.duParts({ shoes: 'trail', weapon: 2, beers: 3, beerTimer: 2, mafiaDebt: 500, story: { id: 'stash', flags: { blauesAuge: true } } }), { shoes: 'trail', weapon: 2, suit: true, cheeks: true, sway: true, blackEye: true, rings: true });
    T.eq(CsCast.duParts({ beers: 2, beerTimer: 0, mafiaDebt: 0 }).cheeks, false, 'Bier ohne Timer wirkt nicht');
    T.eq(CsCast.duParts({ beers: 2, beerTimer: 1, mafiaDebt: 0 }).sway, false, 'erst ab drei Bier');
    T.eq(CsCast.duParts({ shoes: 'unbekannt', beers: 0, beerTimer: 0, mafiaDebt: 0 }).shoes, null);
    T.eq(CsCast.duParts({ beers: 0, beerTimer: 0, mafiaDebt: 0, story: { id: 'kater', flags: {} } }).suit, false, 'Anzug nur in Story 3');
    T.eq(CsCast.duParts(null), {});
  });
  T.test('CsCast.figureHtml(du): Teile nach parts und hurt', () => {
    const html = CsCast.figureHtml('du', { mood: 'calm', parts: { shoes: 'trail', suit: true, cheeks: true, sway: true, blackEye: true, rings: true }, hurt: 'kruecke' });
    T.ok(html.includes('fill="#ff7a1a"'), 'Trail-Schuhe'); T.ok(html.includes('fill="#1e1e22"'), 'Anzug'); T.ok(html.includes('fill="#ff6b6b"'), 'Wangen');
    T.ok(html.startsWith('<div class="cs-fig-inner mood-calm sway"'), 'Schwanken'); T.ok(html.includes('fill="#3a2a6a"'), 'blaues Auge'); T.ok(html.includes('stroke="#4a3a5a"'), 'Augenringe'); T.ok(html.includes('stroke="#8a6a3a"'), 'Krücke');
    T.ok(CsCast.figureHtml('du', { hurt: 'pflaster' }).includes('fill="#e8c8a0"'), 'Pflaster');
    const plain = CsCast.figureHtml('du');
    T.ok(!plain.includes('#ff6b6b') && !plain.includes('#8a6a3a') && !plain.includes('#e8c8a0') && !plain.includes(' sway'), 'nüchtern, unverletzt: keine Zustandsteile');
  });
}
```

- [ ] **Step 2: Block einfügen**

Direkt hinter dem `</script>` von `cutscene-director`:

```html
<script id="cutscene-cast">
/* ================= CUTSCENE CAST – Figuren-Register und SVG-Baukasten (DOM-frei: liefert Strings) =================
   Rig: viewBox 0 0 100 180. Schultern (21,82)/(79,82), Kopfmitte (50,46), Mundmitte (50,61), Standlinie y=172. */
const CsCast = {
  CAST: {
    wirt:        { name: 'Der Wirt',         emoji: '🍺', color: 'var(--neon-amber)', look: { skin: '#e0b08a', cloth: '#3b2a1e', accent: '#c9a227', hair: 'glatze', hairColor: '#555', hat: null,      extra: ['schuerze', 'bart'],               build: 'breit' } },
    chantal:     { name: 'Chantal-Monique',  emoji: '💅', color: 'var(--neon-pink)',  look: { skin: '#f0c8a8', cloth: '#ff2d95', accent: '#ffd6ea', hair: 'lang',   hairColor: '#f2d16b', hat: null,   extra: ['lippenstift', 'kette'],           build: 'schmal' } },
    vito:        { name: 'Don Vito',         emoji: '🕶️', color: 'var(--neon-red)',   look: { skin: '#e8b48a', cloth: '#1e1e22', accent: '#b0202a', hair: 'kurz',   hairColor: '#111',    hat: 'fedora', hatColor: '#151515', extra: ['sonnenbrille', 'zigarre', 'krawatte'], build: 'normal' } },
    igor:        { name: 'Igor',             emoji: '🐻', color: 'var(--neon-blue)',  look: { skin: '#d8a888', cloth: '#2f3a4a', accent: '#1a222c', hair: 'igel',   hairColor: '#222',    hat: null,   extra: ['narbe'],                          build: 'breit' } },
    doc:         { name: 'Der Doc',          emoji: '🥼', color: '#5fe0d0',           look: { skin: '#e8c8a8', cloth: '#f2f2f2', accent: '#5fe0d0', hair: 'grau',   hairColor: '#b8b8b8', hat: null,   extra: ['brille', 'stethoskop'],           build: 'normal' } },
    krause:      { name: 'Herr Krause',      emoji: '👔', color: 'var(--neon-blue)',  look: { skin: '#e8c8a8', cloth: '#2a3a5c', accent: '#4cc9f0', hair: 'kurz',   hairColor: '#6a5040', hat: null,   extra: ['brille', 'krawatte'],             build: 'normal' } },
    makler:      { name: 'Der Makler',       emoji: '🧑‍💼', color: 'var(--gold-2)',    look: { skin: '#e8b48a', cloth: '#6a6a70', accent: '#c9a227', hair: 'kurz',   hairColor: '#3a2414', hat: null,   extra: ['krawatte'],                       build: 'normal' } },
    schmalz:     { name: 'Dr. Schmalz',      emoji: '⚖️', color: '#c0c0c0',           look: { skin: '#e0b898', cloth: '#111111', accent: '#c0c0c0', hair: 'grau',   hairColor: '#9a9a9a', hat: null,   extra: ['brille'],                         build: 'normal' } },
    kevin:       { name: 'Kevin',            emoji: '🧢', color: 'var(--neon-purple)', look: { skin: '#e8c8a8', cloth: '#7b2cbf', accent: '#3a1a5c', hair: 'kurz',  hairColor: '#3a2414', hat: 'cap', hatColor: '#111', extra: [],               build: 'klein' } },
    postmeister: { name: 'Der Postmeister',  emoji: '📬', color: 'var(--day)',        look: { skin: '#e0b08a', cloth: '#f3c623', accent: '#1a1a1a', hair: 'grau',   hairColor: '#b8b8b8', hat: 'kappe', hatColor: '#1a1a1a', extra: ['schnurrbart'], build: 'normal' } },
    verkaeufer:  { name: 'Der Verkäufer',    emoji: '🤵', color: '#cfd8e3',           look: { skin: '#e8c8a8', cloth: '#cfd8e3', accent: '#1a1a1a', hair: 'kurz',   hairColor: '#111',    hat: null,   extra: ['krawatte'],                       build: 'normal' } },
    du:          { name: 'Du',               emoji: '🤠', color: '#ffffff',           look: { skin: '#e8b48a', cloth: '#6b4a2a', accent: '#e6e0d0', hair: 'kurz',   hairColor: '#3a2414', hat: 'cap', hatColor: '#8b1e1e', extra: [],            build: 'normal' } },
    raeuber:     { name: 'Der Räuber',       emoji: '🥷', color: 'var(--neon-red)',   look: { skin: '#e8b48a', cloth: '#111111', accent: '#222',    hair: 'kurz',   hairColor: '#111',    hat: 'muetze', hatColor: '#111', extra: ['maske'],      build: 'normal' } },
    sylvie:      { name: 'Madame Sylvie',    emoji: '🎩', color: '#e8d5a3',           look: { skin: '#e8c8a8', cloth: '#0b0a0c', accent: '#c9a961', hair: 'lang',   hairColor: '#3a1a1a', hat: 'zylinder', hatColor: '#0b0a0c', extra: ['lippenstift'], build: 'schmal' } },
    insider:     { name: 'Der Insider',      emoji: '🕵️', color: 'var(--neon-blue)',  look: { skin: '#e8b48a', cloth: '#4a4a52', accent: '#2a2a30', hair: 'kurz',   hairColor: '#222',    hat: 'fedora', hatColor: '#3a3a40', extra: ['sonnenbrille'], build: 'normal' } },
    anabi:       { name: 'Anabi Stash',      emoji: '🕶️', color: '#d4af37',           look: { skin: '#c89068', cloth: '#111111', accent: '#d4af37', hair: 'kurz',   hairColor: '#111',    hat: null,   extra: ['sonnenbrille', 'kette', 'krawatte'], build: 'normal' } },
    stumme:      { name: 'Der Stumme',       emoji: '🃏', color: '#8a8a8a',           look: { skin: '#e8c8a8', cloth: '#8a8a8a', accent: '#5a5a5a', hair: 'glatze', hairColor: '#333',    hat: null,   extra: [],                                 build: 'schmal' } },
    kessler:     { name: 'Kessler',          emoji: '🚬', color: 'var(--neon-red)',   look: { skin: '#e8b48a', cloth: '#5a1a1a', accent: '#2a0a0a', hair: 'kurz',   hairColor: '#111',    hat: null,   extra: ['zigarette', 'narbe'],             build: 'normal' } },
    brandt:      { name: 'Kommissar Brandt', emoji: '👮', color: 'var(--neon-blue)',  look: { skin: '#e8c8a8', cloth: '#1e3a5c', accent: '#4cc9f0', hair: 'kurz',   hairColor: '#6a5040', hat: 'kappe', hatColor: '#1e3a5c', extra: ['schnurrbart'], build: 'normal' } },
    kowalski:    { name: 'Kowalski',         emoji: '🔧', color: '#b8a070',           look: { skin: '#e0b08a', cloth: '#3a4a5a', accent: '#b8a070', hair: 'kurz',   hairColor: '#3a2414', hat: null,   extra: ['schnurrbart'],                    build: 'breit' } },
  },
  SHOES: { basic: '#f2f2f2', trail: '#ff7a1a', carbon: '#111' },
  MOODS: ['calm', 'angry', 'happy', 'shock', 'dead'],
  /* Ausrüstung und Zustand des Protagonisten aus dem Spielstand (einmal pro Szene gelesen) */
  duParts(s) {
    if (!s) return {};
    const inStash = !!(s.story && s.story.id === 'stash');
    return {
      shoes: s.shoes && this.SHOES[s.shoes] ? s.shoes : null,
      weapon: s.weapon || 0,
      suit: inStash,
      cheeks: s.beers >= 1 && s.beerTimer > 0,
      sway: s.beers >= 3 && s.beerTimer > 0,
      blackEye: !!(s.story && s.story.flags && s.story.flags.blauesAuge),
      rings: s.mafiaDebt > 0,
    };
  },
  /* opts: { mood, parts (nur du), hurt: 'pflaster'|'kruecke' } → HTML-String.
     Jedes bewegliche Teil ist ein eigenes <svg> (gleiche viewBox, übereinander gestapelt): CSS-Transforms auf HTML-Elementen laufen
     auf dem Compositor, Transforms auf SVG-Kindknoten würden die ganze Figur pro Frame neu malen. */
  figureHtml(who, opts = {}) {
    const c = this.CAST[who] || this.CAST.du;
    const look = Object.assign({}, c.look || this.CAST.du.look);
    if (!c.look) { look.extra = ['emoji']; look.emoji = c.emoji; }
    const parts = opts.parts || {};
    if (parts.suit) { look.cloth = '#1e1e22'; look.accent = '#b0202a'; look.extra = [...look.extra, 'krawatte']; }
    const mood = opts.mood || 'calm';
    const P = look;
    const build = { breit: 'translate(50 0) scale(1.22 1) translate(-50 0)', schmal: 'translate(50 0) scale(0.86 1) translate(-50 0)' }[P.build] || '';
    const armShift = P.build === 'breit' ? 8 : P.build === 'schmal' ? -4 : 0;
    const shoe = parts.shoes ? this.SHOES[parts.shoes] : '#1c1c1c';
    const legFill = P.cloth === '#f2f2f2' ? '#cfd8e3' : this.dark(P.cloth);
    const part = (cls, inner) => `<svg class="part ${cls}" viewBox="0 0 100 180" overflow="visible">${inner}</svg>`;
    const legL = part('legL', `<rect x="30" y="118" width="17" height="48" rx="4" fill="${legFill}"/><path d="M26 164h24a4 4 0 0 1 0 8H26z" fill="${shoe}"/>`);
    const legR = part('legR', `<rect x="53" y="118" width="17" height="48" rx="4" fill="${legFill}"/><path d="M50 164h24a4 4 0 0 1 0 8H50z" fill="${shoe}"/>`);
    const body = part('body', `<g transform="${build}">
      <path d="M24 74 L76 74 L82 124 L18 124 Z" fill="${P.cloth}"/>
      <path d="M42 74 L58 74 L52 118 L48 118 Z" fill="${P.accent}"/>
      ${P.extra.includes('krawatte') ? `<path d="M40 74 L60 74 L54 112 L46 112 Z" fill="#f2f2f2"/><path d="M47 74 L53 74 L55 108 L50 114 L45 108 Z" fill="${P.accent}"/><path d="M40 74 L50 100 L60 74" fill="none" stroke="${this.dark(P.cloth)}" stroke-width="3"/>` : ''}
      ${P.extra.includes('schuerze') ? `<path d="M30 92 L70 92 L72 124 L28 124 Z" fill="#e6e0d0"/><path d="M30 92 L70 92" stroke="#c9a227" stroke-width="2"/>` : ''}
      ${P.extra.includes('kette') ? `<path d="M36 76 Q50 96 64 76" fill="none" stroke="#d4af37" stroke-width="3"/>` : ''}
      ${P.extra.includes('stethoskop') ? `<path d="M38 76 Q50 100 62 76" fill="none" stroke="#333" stroke-width="2.5"/><circle cx="50" cy="100" r="4" fill="#333"/>` : ''}
    </g><rect x="44" y="62" width="12" height="14" fill="${P.skin}"/>`);
    const arm = (side) => {
      const x = side === 'L' ? 14 - armShift : 72 + armShift, cx = side === 'L' ? 21 - armShift : 79 + armShift;
      return part(`arm${side}`, `<rect x="${x}" y="76" width="14" height="52" rx="7" fill="${P.cloth}"/><circle cx="${cx}" cy="130" r="6" fill="${P.skin}"/>
        ${side === 'L' && opts.hurt === 'kruecke' ? `<path d="M${cx - 14} 118 L${cx - 14} 172" stroke="#8a6a3a" stroke-width="4"/><path d="M${cx - 22} 118 L${cx - 6} 118" stroke="#8a6a3a" stroke-width="4"/>` : ''}`);
    };
    const face = this.face(mood, P, parts, opts.hurt);
    const hair = this.hair(P);
    const head = part('head', `${hair.back}<path d="M28 46 a22 24 0 0 1 44 0 v10 a22 20 0 0 1 -44 0z" fill="${P.skin}"/>${face.head}${hair.front}${this.extras(P, parts)}${this.hat(P)}`);
    const eyes = part('eyes', face.eyes);
    const mouth = part('mouth', face.mouth);
    const klein = P.build === 'klein' ? ' klein' : '';
    return `<div class="cs-fig-inner mood-${mood}${parts.sway ? ' sway' : ''}${klein}"><div class="cs-body">${legL}${legR}${body}${arm('L')}${arm('R')}${head}${eyes}${mouth}</div></div>`;
  },
  dark(hex) {
    const n = parseInt(hex.slice(1), 16); if (Number.isNaN(n) || hex.length !== 7) return '#222';
    const f = (v) => Math.max(0, Math.round(v * 0.7)).toString(16).padStart(2, '0');
    return `#${f(n >> 16)}${f((n >> 8) & 255)}${f(n & 255)}`;
  },
  /* Mimik: alle fünf Stimmungen liegen in den Teilen, CSS zeigt nur .m-<mood>. Liefert { head, eyes, mouth } (Brauen gehören zum Kopf,
     Augen und Mund sind eigene Teile, damit Blinzeln und Sprechen ohne Neuzeichnen des Kopfes laufen) */
  face(mood, P, parts, hurt) {
    const browColor = P.hairColor === '#b8b8b8' || P.hairColor === '#9a9a9a' ? '#777' : P.hairColor;
    const brow = (d) => `<path d="${d}" fill="none" stroke="${browColor}" stroke-width="2.2" stroke-linecap="round"/>`;
    const dots = '<circle cx="41" cy="48" r="3.2" fill="#111"/><circle cx="59" cy="48" r="3.2" fill="#111"/>';
    const mouthColor = P.extra.includes('lippenstift') ? '#c8102e' : '#5a3020';
    const brows = {
      calm: brow('M36 41 L46 40') + brow('M54 40 L64 41'),
      angry: brow('M35 37 L47 43') + brow('M65 37 L53 43'),
      happy: brow('M35 40 Q41 36 47 39') + brow('M53 39 Q59 36 65 40'),
      shock: brow('M35 38 Q41 34 47 37') + brow('M53 37 Q59 34 65 38'),
      dead: brow('M36 40 L46 42') + brow('M54 42 L64 40'),
    };
    const eyes = {
      calm: dots, angry: dots,
      happy: '<path d="M37 49 Q41 44 45 49" fill="none" stroke="#111" stroke-width="2.4"/><path d="M55 49 Q59 44 63 49" fill="none" stroke="#111" stroke-width="2.4"/>',
      shock: '<circle cx="41" cy="48" r="5" fill="#fff" stroke="#111" stroke-width="1.5"/><circle cx="59" cy="48" r="5" fill="#fff" stroke="#111" stroke-width="1.5"/><circle cx="41" cy="48" r="2.4" fill="#111"/><circle cx="59" cy="48" r="2.4" fill="#111"/>',
      dead: '<g fill="none" stroke="#111" stroke-width="2.2"><path d="M37 44 L45 52 M45 44 L37 52"/><path d="M55 44 L63 52 M63 44 L55 52"/></g>',
    };
    const mouths = {
      calm: `<path d="M44 61 Q50 65 56 61" fill="${mouthColor}" stroke="${mouthColor}" stroke-width="2" stroke-linecap="round"/>`,
      angry: `<path d="M43 63 Q50 58 57 63" fill="none" stroke="${mouthColor}" stroke-width="2.5" stroke-linecap="round"/>`,
      happy: `<path d="M41 59 Q50 70 59 59z" fill="${mouthColor}"/><path d="M44 60 Q50 63 56 60z" fill="#fff"/>`,
      shock: '<ellipse cx="50" cy="63" rx="5" ry="6" fill="#3a1a10"/>',
      dead: `<path d="M44 63 L56 63" stroke="${mouthColor}" stroke-width="2.5" stroke-linecap="round"/>`,
    };
    const state = `${parts.cheeks ? '<circle cx="36" cy="56" r="4" fill="#ff6b6b" opacity=".55"/><circle cx="64" cy="56" r="4" fill="#ff6b6b" opacity=".55"/>' : ''}
      ${parts.rings ? '<path d="M36 53 Q41 56 46 53" fill="none" stroke="#4a3a5a" stroke-width="2" opacity=".7"/><path d="M54 53 Q59 56 64 53" fill="none" stroke="#4a3a5a" stroke-width="2" opacity=".7"/>' : ''}
      ${parts.blackEye ? '<circle cx="41" cy="48" r="7" fill="#3a2a6a" opacity=".55"/>' : ''}
      ${hurt === 'pflaster' ? '<rect x="52" y="30" width="16" height="7" rx="2" fill="#e8c8a0" transform="rotate(-20 60 33)"/><rect x="58" y="24" width="7" height="16" rx="2" fill="#e8c8a0" transform="rotate(-20 60 33)"/>' : ''}`;
    const moodGroups = (map) => this.MOODS.map((m) => `<g class="m m-${m}">${map[m]}</g>`).join('');
    return { head: moodGroups(brows) + state, eyes: moodGroups(eyes), mouth: moodGroups(mouths) };
  },
  hair(P) {
    const h = P.hairColor || '#3a2414';
    const front = {
      kurz: `<path d="M26 44 Q28 18 50 18 Q72 18 74 44 Q68 32 50 30 Q32 32 26 44z" fill="${h}"/>`,
      grau: `<path d="M26 44 Q28 18 50 18 Q72 18 74 44 Q68 32 50 30 Q32 32 26 44z" fill="${h}"/>`,
      lang: `<path d="M26 44 Q28 16 50 16 Q72 16 74 44 Q68 30 50 28 Q32 30 26 44z" fill="${h}"/>`,
      igel: `<path d="M26 44 L30 22 L36 34 L42 18 L48 32 L54 18 L60 32 L66 22 L74 44 Q50 34 26 44z" fill="${h}"/>`,
      glatze: `<path d="M27 42 Q27 30 33 26 L33 42z" fill="${h}"/><path d="M73 42 Q73 30 67 26 L67 42z" fill="${h}"/>`,
    }[P.hair] || '';
    const back = P.hair === 'lang' ? `<path d="M24 40 Q22 90 30 96 L70 96 Q78 90 76 40z" fill="${h}"/>` : '';
    return { front, back };
  },
  hat(P) {
    const c = P.hatColor || '#111';
    return {
      cap: `<path d="M24 30 Q26 8 50 8 Q74 8 76 30z" fill="${c}"/><path d="M20 29 L55 29 Q58 32 55 35 L22 35 Q18 32 20 29z" fill="${this.dark(c)}"/>`,
      fedora: `<path d="M30 34 Q34 8 50 8 Q66 8 70 34z" fill="${c}"/><path d="M14 34 Q50 26 86 34 L84 40 Q50 34 16 40z" fill="${this.dark(c)}"/><path d="M30 30 L70 30 L70 35 L30 35z" fill="${P.accent}"/>`,
      zylinder: `<rect x="32" y="2" width="36" height="30" fill="${c}"/><rect x="22" y="30" width="56" height="6" rx="3" fill="${this.dark(c)}"/><rect x="32" y="24" width="36" height="5" fill="${P.accent}"/>`,
      muetze: `<path d="M26 36 Q26 10 50 10 Q74 10 74 36z" fill="${c}"/><rect x="25" y="30" width="50" height="8" rx="3" fill="${this.dark(c)}"/>`,
      kappe: `<path d="M26 32 Q26 14 50 14 Q74 14 74 32z" fill="${c}"/><rect x="24" y="30" width="52" height="6" rx="2" fill="${this.dark(c)}"/><path d="M22 35 L56 35 Q58 38 55 41 L24 41 Q20 38 22 35z" fill="#111"/><circle cx="50" cy="24" r="4" fill="${P.accent}"/>`,
    }[P.hat] || '';
  },
  extras(P, parts) {
    const out = [];
    for (const e of P.extra) {
      if (e === 'sonnenbrille') out.push('<rect x="32" y="42" width="14" height="9" rx="2" fill="#050505"/><rect x="54" y="42" width="14" height="9" rx="2" fill="#050505"/><path d="M46 45 L54 45" stroke="#050505" stroke-width="2"/>');
      if (e === 'brille') out.push('<circle cx="41" cy="48" r="7" fill="none" stroke="#333" stroke-width="1.8"/><circle cx="59" cy="48" r="7" fill="none" stroke="#333" stroke-width="1.8"/><path d="M48 48 L52 48" stroke="#333" stroke-width="1.8"/>');
      if (e === 'zigarre') out.push('<rect x="58" y="60" width="20" height="4" rx="2" fill="#3a2a1a"/><circle class="ember" cx="79" cy="62" r="3" fill="#ff7a1a"/>');
      if (e === 'zigarette') out.push('<rect x="57" y="61" width="18" height="2.5" rx="1" fill="#f2f2f2"/><circle class="ember" cx="76" cy="62" r="2" fill="#ff7a1a"/>');
      if (e === 'narbe') out.push('<path d="M64 40 L68 54" stroke="#a04040" stroke-width="2" stroke-linecap="round"/>');
      if (e === 'bart') out.push(`<path d="M30 56 Q50 84 70 56 Q66 66 50 68 Q34 66 30 56z" fill="${P.hairColor}"/>`);
      if (e === 'schnurrbart') out.push(`<path d="M40 57 Q50 53 60 57 Q50 61 40 57z" fill="${P.hairColor}"/>`);
      if (e === 'maske') out.push('<path d="M28 54 L72 54 L70 68 Q50 76 30 68z" fill="#111"/>');
      if (e === 'emoji') out.push(`<text x="50" y="58" font-size="40" text-anchor="middle">${P.emoji}</text>`);
    }
    return out.join('');
  },
};
</script>

```

- [ ] **Step 3: Tests laufen lassen**

Run: `node tests/run-selftest.mjs`
Expected: `0 fehlgeschlagen`, vier Tests mehr.

- [ ] **Step 4: Sichtprüfung der Figuren (einmalig, kein Testcode)**

Eine Wegwerf-Seite im Scratchpad erzeugen, die für jede Cast-ID `CsCast.figureHtml(id)` in ein 120×216-px-Div mit folgendem Minimal-CSS rendert, und per `Chrome --headless=new --screenshot` anschauen:

```css
.f { position: relative; width: 120px; height: 216px; display: inline-block; margin: 6px; }
.cs-fig-inner, .cs-body { position: absolute; inset: 0; } .part { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.m { opacity: 0; } .mood-calm .m-calm { opacity: 1; }
```

Erwartung: 20 unterscheidbare Figuren (Vito Fedora/Sonnenbrille/Zigarre, Chantal blond/pink, Igor breit, Kevin klein, Doc weißer Kittel …), keine Teile außerhalb der Figur, Mütze über den Brauen.

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(cutscene): Figuren-Baukasten CsCast – 20 Looks, acht Teil-SVGs je Figur, Protagonist mit Ausrüstung und Zustand

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Kulissen-Register `CsSets` (DOM-frei)

**Files:**
- Modify: `keller37.html` – neuer Block `<script id="cutscene-sets">` direkt hinter `</script>` von `cutscene-cast`
- Modify: `keller37.html` – Node-Test (hinter den `CsCast`-Tests)

**Interfaces:**
- Produces: `CsSets.SETS[id] = { back(): string, front(): string, life: string[] }` für die 16 IDs `bar, keller, hinterzimmer, strasse, gasse, hafen, hafen-morgen, klinik, bank, standesamt, villa, bahnhof, pfandleihe, autohaus, intersport, royal`; `CsSets.svg/rect/windows` Helfer; `CsSets.define(id, def)`.

- [ ] **Step 1: Fehlschlagenden Test schreiben**

Hinter den `CsCast`-Tests einfügen:

```js
if (typeof CsSets !== 'undefined') {
  T.test('CsSets: alle 16 Kulissen mit back/front/life; jedes lebende Element ist gezeichnet', () => {
    const ids = ['bar', 'keller', 'hinterzimmer', 'strasse', 'gasse', 'hafen', 'hafen-morgen', 'klinik', 'bank', 'standesamt', 'villa', 'bahnhof', 'pfandleihe', 'autohaus', 'intersport', 'royal'];
    T.eq(Object.keys(CsSets.SETS).sort(), [...ids].sort());
    for (const id of ids) {
      const s = CsSets.SETS[id];
      T.ok(Array.isArray(s.life) && s.life.length >= 1 && s.life.every((l) => l.startsWith('life-')), `${id}: life`);
      const back = s.back(), front = s.front();
      T.ok(back.startsWith('<svg class="cs-set') && back.includes('preserveAspectRatio="xMidYMax meet"'), `${id}: back`);
      T.eq(typeof front, 'string', `${id}: front`);
      for (const l of s.life) T.ok(back.includes(`class="${l}"`) || front.includes(`class="${l}"`), `${id}: ${l} gezeichnet`);
    }
    T.ok(CsSets.SETS.gasse.front().includes('life-rain'), 'Regen im Vordergrund');
    T.ok(CsSets.SETS['hafen-morgen'].back().includes('life-sun') && !CsSets.SETS.hafen.back().includes('life-sun'), 'Sonne nur am Morgen');
  });
}
```

- [ ] **Step 2: Block einfügen**

Direkt hinter dem `</script>` von `cutscene-cast`:

```html
<script id="cutscene-sets">
/* ================= CUTSCENE SETS – Kulissen-Register (DOM-frei: liefert SVG-Strings) =================
   Jede Kulisse: { back(): SVG hinter den Figuren, front(): SVG vor den Figuren ('' = keins), life: [Klassen der lebenden Elemente] }
   Zeichenfläche 1000×400, unten bündig und auf Bühnenbreite skaliert (preserveAspectRatio xMidYMax meet) – hochkant bleibt oben Himmel frei. Die Standlinie der Figuren liegt bei y≈352. */
const CsSets = {
  svg(inner, cls = '') { return `<svg class="cs-set ${cls}" viewBox="0 0 1000 400" preserveAspectRatio="xMidYMax meet">${inner}</svg>`; },
  rect(x, y, w, h, fill, extra = '') { return `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" ${extra}/>`; },
  windows(x0, y0, cols, rows, dx, dy, fill, cls = '') { let s = ''; for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) s += `<rect class="${cls}" x="${x0 + c * dx}" y="${y0 + r * dy}" width="10" height="14" fill="${fill}" style="animation-delay:${((r * cols + c) * 0.37) % 3}s"/>`; return s; },
  SETS: {},
  define(id, def) { this.SETS[id] = def; },
};
CsSets.define('bar', {
  life: ['life-neon', 'life-smoke'],
  back() { const S = CsSets; let bottles = ''; for (let i = 0; i < 12; i++) bottles += S.rect(230 + i * 46, 120 - (i % 3) * 8, 18, 46 + (i % 3) * 8, ['#7a5a2a', '#3a6a3a', '#6a2a2a', '#c9a227'][i % 4], 'rx="5"');
    return S.svg(`${S.rect(200, 60, 600, 8, '#5a3a1a')}${S.rect(200, 166, 600, 8, '#5a3a1a')}${bottles}
      ${S.rect(0, 280, 1000, 60, '#4a2e12')}${S.rect(0, 274, 1000, 8, '#7a5a2a')}
      <text class="life-neon" x="880" y="60" font-family="monospace" font-size="26" font-weight="700" fill="#ff5c7a" text-anchor="middle" letter-spacing="4">KELLER 37</text>
      <path class="life-smoke" d="M120 250 Q130 230 120 210 Q110 190 120 170" fill="none" stroke="#fff" stroke-width="3" opacity=".25"/>`); },
  front() { return ''; },
});
CsSets.define('keller', {
  life: ['life-blink', 'life-swing'],
  back() { const S = CsSets; let m = ''; for (let i = 0; i < 4; i++) m += `${S.rect(80 + i * 240, 170, 110, 170, '#1e1e1a', 'rx="6"')}<rect class="life-blink" x="${95 + i * 240}" y="185" width="80" height="50" fill="#2a4a3a" style="animation-delay:${i * .5}s"/>${S.rect(95 + i * 240, 250, 80, 20, '#3a3a30')}`;
    return S.svg(`${m}<g class="life-swing" style="transform-origin:500px 0px"><path d="M500 0 L500 70" stroke="#666" stroke-width="3"/><path d="M470 70 L530 70 L545 100 L455 100z" fill="#8a8a70"/><ellipse cx="500" cy="100" rx="45" ry="6" fill="#fff8d0" opacity=".9"/></g>`); },
  front() { return ''; },
});
CsSets.define('hinterzimmer', {
  life: ['life-candle', 'life-smoke'],
  back() { const S = CsSets; return S.svg(`${S.rect(300, 250, 400, 14, '#3a2410')}${S.rect(320, 264, 20, 90, '#2a1a0a')}${S.rect(660, 264, 20, 90, '#2a1a0a')}
      ${S.rect(560, 214, 12, 36, '#e8e0c0')}<ellipse class="life-candle" cx="566" cy="206" rx="7" ry="14" fill="#ffb347" style="transform-origin:566px 220px"/>
      <ellipse cx="430" cy="252" rx="26" ry="6" fill="#555"/><path class="life-smoke" d="M430 246 Q440 226 430 206 Q420 186 430 166" fill="none" stroke="#fff" stroke-width="3" opacity=".25"/>`); },
  front() { return ''; },
});
CsSets.define('strasse', {
  life: ['life-car'],
  back() { const S = CsSets; let houses = ''; for (let i = 0; i < 5; i++) houses += `${S.rect(i * 210, 60 + (i % 2) * 40, 190, 280 - (i % 2) * 40, ['#2a2a34', '#33333f'][i % 2])}${S.windows(i * 210 + 20, 90 + (i % 2) * 40, 5, 4, 34, 44, '#8a8a60')}`;
    return S.svg(`${houses}${S.rect(0, 338, 1000, 14, '#555')}${S.rect(760, 120, 6, 220, '#777')}<path d="M740 120 L786 120 L780 100 L746 100z" fill="#999"/><ellipse cx="763" cy="128" rx="70" ry="40" fill="#fff4c0" opacity=".12"/>
      <g class="life-car"><rect x="-260" y="300" width="160" height="44" rx="10" fill="#111"/><rect x="-230" y="278" width="90" height="30" rx="8" fill="#222"/><circle cx="-230" cy="346" r="12" fill="#333"/><circle cx="-130" cy="346" r="12" fill="#333"/><path d="M-100 314 L60 290 L60 340z" fill="#fff8c0" opacity=".25"/></g>`); },
  front() { return ''; },
});
CsSets.define('gasse', {
  life: ['life-rain', 'life-cat'],
  back() { const S = CsSets; return S.svg(`${S.rect(0, 0, 1000, 340, '#14161c')}<circle cx="820" cy="70" r="30" fill="#e8e6d0" opacity=".85"/>
      ${S.rect(60, 250, 70, 90, '#3a3a40', 'rx="6"')}${S.rect(140, 262, 70, 78, '#3a3a40', 'rx="6"')}${S.rect(55, 244, 80, 10, '#555', 'rx="3"')}
      <path d="M700 60 L700 340 M760 60 L760 340 M700 120 L760 120 M700 200 L760 200 M700 280 L760 280 M760 120 L820 60" stroke="#444" stroke-width="5" fill="none"/>
      <g class="life-cat"><path d="M0 340 q10 -20 20 0 l4 -14 l6 12 h20 l6 -12 l4 14 q10 -14 8 0z" fill="#0a0a0a"/></g>`); },
  front() { let r = ''; for (let i = 0; i < 40; i++) r += `<path d="M${i * 26 + (i % 3) * 7} ${-400 + (i * 53) % 400} l-6 30" stroke="#9ab" stroke-width="1.5" opacity=".35"/>`;
    return CsSets.svg(`<g class="life-rain">${r}<g transform="translate(0 400)">${r}</g></g>`); },
});
const hafen = (morgen) => ({
  life: morgen ? ['life-wave', 'life-sun'] : ['life-wave', 'life-gull'],
  back() { const S = CsSets; return S.svg(`${morgen ? '<circle class="life-sun" cx="820" cy="200" r="46" fill="#ffb060" opacity=".9"/>' : '<circle cx="840" cy="70" r="28" fill="#e8e6d0" opacity=".8"/>'}
      <path d="M120 300 L120 60 L260 60 M120 100 L200 60 M120 140 L200 60 M120 180 L200 60" stroke="#333" stroke-width="8" fill="none"/>
      <path d="M560 300 L560 90 L700 90 M560 130 L640 90 M560 170 L640 90" stroke="#333" stroke-width="8" fill="none"/>
      ${S.rect(300, 240, 120, 60, '#5a2a2a')}${S.rect(420, 240, 120, 60, '#2a4a5a')}${S.rect(360, 180, 120, 60, '#5a5a2a')}
      ${S.rect(0, 300, 1000, 100, morgen ? '#c46a3a' : '#0a1a33')}<g class="life-wave"><path d="M-100 320 q25 -6 50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0" fill="none" stroke="${morgen ? '#ffd090' : '#5aa0d0'}" stroke-width="2" opacity=".6"/></g>
      ${morgen ? '' : '<path class="life-gull" d="M0 0 q8 -8 16 0 q8 -8 16 0" fill="none" stroke="#ddd" stroke-width="2" style="transform:translate(200px,120px)"/>'}`); },
  front() { return ''; },
});
CsSets.define('hafen', hafen(false));
CsSets.define('hafen-morgen', hafen(true));
CsSets.define('klinik', {
  life: ['life-ekg', 'life-flicker'],
  back() { const S = CsSets; return S.svg(`<rect class="life-flicker" x="380" y="20" width="240" height="14" rx="4" fill="#f4fff8"/>
      ${S.rect(600, 240, 300, 20, '#cfd8e3')}${S.rect(600, 260, 14, 90, '#889')}${S.rect(886, 260, 14, 90, '#889')}${S.rect(620, 220, 80, 20, '#eef')}
      ${S.rect(120, 120, 150, 100, '#111', 'rx="6"')}${S.rect(180, 220, 30, 130, '#889')}<polyline class="life-ekg" points="130,170 160,170 170,150 180,195 190,160 200,170 260,170" fill="none" stroke="#5fe0d0" stroke-width="3"/>`); },
  front() { return ''; },
});
CsSets.define('bank', {
  life: ['life-ticker'],
  back() { const S = CsSets; let rows = ''; for (let i = 0; i < 4; i++) rows += `<text class="life-ticker" x="720" y="${150 + i * 22}" font-family="monospace" font-size="16" fill="${i % 2 ? '#ff6b6b' : '#5fe0a0'}" style="animation-delay:${i * .7}s">${['DAX  −0,8 %', 'GOLD +1,2 %', 'BTC  −4,1 %', 'K37  +37 %'][i]}</text>`;
    return S.svg(`${S.rect(0, 230, 1000, 20, '#1a3a5c')}${S.rect(0, 250, 1000, 100, '#123a5c')}${S.rect(700, 120, 220, 110, '#0a1a2a', 'rx="6"')}${rows}
      ${S.rect(930, 300, 30, 50, '#5a3a1a')}<circle cx="945" cy="280" r="34" fill="#2a6a3a"/><circle cx="920" cy="300" r="22" fill="#2a6a3a"/><circle cx="970" cy="300" r="22" fill="#2a6a3a"/>`); },
  front() { return ''; },
});
CsSets.define('standesamt', {
  life: ['life-dust'],
  back() { const S = CsSets; return S.svg(`${S.rect(380, 40, 240, 200, '#f8f4e8')}<path d="M500 40 L500 240 M380 140 L620 140" stroke="#b8a888" stroke-width="8"/>
      ${S.rect(660, 240, 200, 110, '#8a7050')}<circle cx="710" cy="230" r="22" fill="#ff9ab0"/><circle cx="750" cy="222" r="24" fill="#ffd0a0"/><circle cx="790" cy="230" r="22" fill="#ff9ab0"/>
      ${S.rect(120, 60, 6, 290, '#777')}<path d="M126 60 L200 80 L126 100z" fill="#c0392b"/><path d="M126 100 L200 120 L126 140z" fill="#f1c40f"/>`); },
  front() { let d = ''; for (let i = 0; i < 18; i++) d += `<circle class="life-dust" cx="${400 + (i * 61) % 220}" cy="${60 + (i * 37) % 200}" r="2" fill="#fff" style="animation-delay:${(i * .4) % 4}s"/>`; return CsSets.svg(d); },
});
CsSets.define('villa', {
  life: ['life-city', 'life-shimmer'],
  back() { const S = CsSets; let sky = ''; for (let i = 0; i < 12; i++) sky += `${S.rect(i * 84, 120 + (i * 37) % 90, 70, 300, '#0a1030')}${S.windows(i * 84 + 8, 130 + (i * 37) % 90, 3, 6, 22, 24, '#ffe08a', 'life-city')}`;
    return S.svg(`<circle cx="880" cy="60" r="26" fill="#f4f0d0"/>${sky}${S.rect(0, 300, 1000, 60, '#1a5a8a')}<g class="life-shimmer"><path d="M0 320 h1000 M0 340 h1000" stroke="#8ad0ff" stroke-width="2" stroke-dasharray="30 40" opacity=".6"/></g>`); },
  front() { return ''; },
});
CsSets.define('bahnhof', {
  life: ['life-train', 'life-tick'],
  back() { const S = CsSets; return S.svg(`${S.rect(0, 0, 1000, 340, '#0d1220')}<path d="M0 330 h1000 M0 346 h1000" stroke="#666" stroke-width="4"/>
      <g class="life-train"><rect x="-1100" y="230" width="1000" height="100" rx="12" fill="#2a2a3a"/>${S.windows(-1080, 250, 20, 1, 50, 0, '#ffd88a')}</g>
      ${S.rect(120, 60, 8, 280, '#777')}<circle cx="124" cy="60" r="30" fill="#f4f0e0"/><path d="M124 60 L124 40" stroke="#111" stroke-width="3"/><path class="life-tick" d="M124 60 L140 60" stroke="#111" stroke-width="3" style="transform-origin:124px 60px"/>
      ${S.rect(700, 290, 200, 14, '#5a3a1a')}${S.rect(710, 304, 12, 46, '#333')}${S.rect(878, 304, 12, 46, '#333')}`); },
  front() { return ''; },
});
CsSets.define('pfandleihe', {
  life: ['life-neon'],
  back() { const S = CsSets; return S.svg(`${S.rect(200, 200, 600, 140, '#2a2418')}${S.rect(210, 210, 580, 90, '#1a160c')}
      ${S.rect(240, 250, 60, 40, '#c9a227')}${S.rect(340, 240, 40, 50, '#8a8a8a')}<path d="M440 270 h60 v-14 h-20 v-10 h-24z" fill="#444"/>${S.rect(560, 246, 80, 44, '#5a3a1a')}${S.rect(680, 236, 60, 54, '#333')}
      <text class="life-neon" x="500" y="80" font-family="monospace" font-size="30" fill="#ffd166" text-anchor="middle" letter-spacing="6">PFAND · GOLD · BARGELD</text>`); },
  front() { return ''; },
});
CsSets.define('autohaus', {
  life: ['life-sway'],
  back() { const S = CsSets; return S.svg(`${S.rect(0, 0, 1000, 340, '#1a1e26')}<ellipse cx="500" cy="330" rx="260" ry="26" fill="#2a2e38"/>
      <g class="life-sway" style="transform-origin:500px 330px"><path d="M300 320 L320 270 L400 240 L600 240 L680 270 L700 320z" fill="#c0392b"/><path d="M400 240 L420 260 L580 260 L600 240z" fill="#8ad"/><circle cx="360" cy="320" r="24" fill="#111"/><circle cx="640" cy="320" r="24" fill="#111"/></g>`); },
  front() { return ''; },
});
CsSets.define('intersport', {
  life: ['life-spot'],
  back() { const S = CsSets; let shoes = ''; for (let i = 0; i < 8; i++) shoes += `<path d="M${140 + i * 100} 220 q30 -30 60 -10 l20 10 v14 h-80z" fill="${['#f2f2f2', '#ff7a1a', '#111', '#4cc9f0'][i % 4]}"/>`;
    return S.svg(`${S.rect(100, 140, 800, 8, '#cfd8e3')}${S.rect(100, 236, 800, 8, '#cfd8e3')}${shoes}<path class="life-spot" d="M500 0 L380 300 L620 300z" fill="#fff" opacity=".08" style="transform-origin:500px 0px"/>`); },
  front() { return ''; },
});
CsSets.define('royal', {
  life: ['life-glitter'],
  back() { const S = CsSets; let g = ''; for (let i = 0; i < 9; i++) g += `<circle class="life-glitter" cx="${420 + i * 20}" cy="${110 + Math.abs(i - 4) * 12}" r="5" fill="#fff7d0" style="animation-delay:${i * .2}s"/>`;
    return S.svg(`${S.rect(0, 0, 220, 340, '#6a0f1a')}${S.rect(780, 0, 220, 340, '#6a0f1a')}${S.rect(240, 0, 40, 340, '#e8dcc0')}${S.rect(720, 0, 40, 340, '#e8dcc0')}
      <path d="M500 0 L500 60" stroke="#c9a961" stroke-width="4"/><path d="M420 110 Q500 60 580 110" fill="none" stroke="#c9a961" stroke-width="4"/>${g}`); },
  front() { return ''; },
});
</script>

```

- [ ] **Step 3: Tests laufen lassen**

Run: `node tests/run-selftest.mjs`
Expected: `0 fehlgeschlagen`, ein Test mehr.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat(cutscene): Kulissen-Register CsSets – 16 Kulissen als SVG mit lebenden Elementen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Bühnen-Engine, CSS, DOM-Tests, Playtest-Selektoren

**Files:**
- Modify: `keller37.html` – CSS-Abschnitt 5 (von `/* ==== 5. CUTSCENE ==== */` bis vor `/* ==== 6. SPIELE & RÄUME ==== */`) komplett ersetzen
- Modify: `keller37.html` – Zeile `.cs-portrait.royal-frame { … }` (bei ca. Z. 770, `grep -n "cs-portrait.royal-frame"`) löschen; in der reduced-motion-Liste (`grep -n "\.neon, \.cs-portrait"`) `.cs-portrait, ` entfernen
- Modify: `keller37.html` – Block `cutscene-engine`: das `Cutscene`-Objekt (von `/* ================= CUTSCENE – Visual-Novel-Engine` bis zur schließenden `};` vor `/* ---- Szenen: Intro & Neues Spiel ---- */`) ersetzen
- Modify: `keller37.html` – bestehender DOM-Test `Cutscene.CAST: Story-3-Figuren und Hintergründe` (zwei Zeilen)
- Modify: `keller37.html` – neue DOM-Tests vor `const pseudoAnim = (el, pseudo) => getComputedStyle(el, pseudo).animationName;`
- Modify: `tests/playtest-story.py` – zwei Selektoren

**Interfaces:**
- Consumes: `CsDirector.stagePlan/side`, `CsCast.CAST/figureHtml/duParts`, `CsSets.SETS`, bestehende `UI.fmt/shownBalance/setBalance/pulseBalance/renderWallet/shake`, `SFX.play/stopAll`, `h/qs/qsa/wait/rand/pick`, `State.s`, `Bus.on`, `Rules.insiderCapText`.
- Produces: `Cutscene.instant` (bool, Test-/Dev-Schalter), `Cutscene.CAST === CsCast.CAST`, `Cutscene.SETS === CsSets.SETS`, DOM-Klassen `cs-world, cs-sky, cs-back, cs-floor, cs-actors, cs-front, cs-fig[data-pose].speaking.talking.walking.far, cs-fig-inner.mood-*, cs-body, part, cs-bubble(.narrator), cs-name, cs-text, cs-next, cs-shout, cs-bar, cs-bar-mid, cs-money, cs-skip, cs-choices, cs-extra, cs-stats, cs-flash, cs-black, cs-particle`; `#cutscene.cs-instant`.

- [ ] **Step 1: Fehlschlagende DOM-Tests schreiben**

Vor der Zeile `  const pseudoAnim = (el, pseudo) => getComputedStyle(el, pseudo).animationName;` einfügen (der Block liegt bereits in `if (typeof Story !== 'undefined' && typeof document !== 'undefined') {`; `animatedProps` ist dort schon definiert):

```js
  T.test('Cutscene-Bühne: Figuren, eine Blase am Sprecher, Regie, Skip-Endzustand', async () => {
    const keep = { s: State.s, save: State.save, instant: Cutscene.instant };
    State.save = () => {}; State.s = State.fresh(); State.s.beers = 3; State.s.beerTimer = 2;
    Cutscene.instant = true;
    Cutscene.define('test.buehne', [
      { bg: 'bar', who: 'wirt', mood: 'calm', text: 'Eins.' },
      { bg: 'bar', who: 'vito', mood: 'angry', text: 'Zwei.', cam: 'close', shout: 'HEY!' },
      { bg: 'keller', who: 'du', mood: 'happy', text: 'Drei.', enter: 'igor', pose: { who: 'igor', pose: 'arms-crossed' }, look: { du: { hurt: 'pflaster' } } },
      { bg: 'keller', who: 'du', mood: 'calm', text: 'Vier.', cast: [], choices: [{ label: 'Ok', value: 'ok' }] },
    ]);
    try {
      const done = Cutscene.play('test.buehne', {});
      await wait(40);
      const root = qs('#cutscene');
      T.eq(qsa('.cs-fig', root).length, 2, 'du + wirt');
      T.eq(qsa('.cs-bubble:not([hidden])', root).length, 1, 'genau eine Blase');
      T.ok(qs('.cs-fig.speaking .cs-fig-inner.mood-calm', root), 'Sprecher wirt mit Stimmung');
      T.eq(qsa('.cs-fig.speaking svg.part', root).length, 8, 'acht Teil-SVGs');
      T.eq(qs('.cs-name', root).textContent, 'Der Wirt');
      T.ok(qs('.cs-sky', root).classList.contains('bar'), 'Kulisse bar');
      T.ok(qs('.cs-back svg.cs-set', root), 'Kulissen-SVG');
      T.ok(qs('.cs-fig:not(.speaking) circle[fill="#ff6b6b"]', root), 'Bier → rote Wangen bei du');
      T.ok(qs('.cs-fig:not(.speaking) .cs-fig-inner.sway', root), '3 Bier → Schwanken');
      T.ok(parseFloat(qs('.cs-bubble', root).style.top) >= 0 && qs('.cs-bubble', root).style.width, 'Blase platziert');
      root.click(); await wait(40);
      T.eq(qsa('.cs-fig', root).length, 3, 'vito dazu');
      T.eq(qs('.cs-fig.speaking', root).dataset.pose, 'point', 'angry → point');
      T.ok(/scale/.test(qs('.cs-world', root).style.transform), 'Kamera close');
      T.eq(qs('.cs-shout', root).textContent, 'HEY!');
      qs('.cs-skip', root).click(); await wait(40);
      T.ok(qs('.cs-sky', root).classList.contains('keller'), 'Skip → letzte Kulisse');
      T.eq(qsa('.cs-fig', root).length, 0, 'cast: [] → leere Bühne');
      T.ok(qs('.cs-bubble', root).classList.contains('narrator'), 'Erzähler-Blase');
      T.eq(qs('.cs-world', root).style.transform, '', 'Kamera zurück');
      T.eq(qsa('.cs-choices .btn', root).length, 1, 'Wahl im Streifen');
      T.ok(document.documentElement.scrollWidth <= window.innerWidth, 'keine Überbreite');
      qs('.cs-choices .btn', root).click();
      T.eq(await done, 'ok', 'Wahlwert');
      T.ok(root.hidden, 'Overlay zu');
      /* Regie-Ausführung ohne Skip: Kulissenwechsel, Auftritt, Pflaster, Pose-Override */
      const done2 = Cutscene.play('test.buehne', {});
      await wait(40); root.click(); await wait(40); root.click(); await wait(40);
      T.eq(qsa('.cs-fig', root).length, 2, 'Kulissenwechsel: du + igor');
      T.eq(qs('.cs-fig:not(.speaking)', root).dataset.pose, 'arms-crossed', 'pose-Override');
      T.ok(qs('.cs-fig.speaking rect[fill="#e8c8a0"]', root), 'look.hurt → Pflaster');
      qs('.cs-skip', root).click(); await wait(40); qs('.cs-choices .btn', root).click(); await done2;
      T.ok(!Cutscene.active && !document.body.classList.contains('cs-open'), 'Szene sauber beendet');
    } finally { Cutscene.instant = keep.instant; State.s = keep.s; State.save = keep.save; delete Cutscene.SCENES['test.buehne']; }
  });
  T.test('Cutscene-Keyframes (cs*) animieren nur transform oder opacity', () => {
    let n = 0;
    for (const sheet of document.styleSheets) {
      let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
      for (const r of rules) if (r.type === CSSRule.KEYFRAMES_RULE && /^cs[A-Z]/.test(r.name)) { n++; for (const p of animatedProps(r)) T.ok(p === 'transform' || p === 'opacity', `${r.name}: ${p}`); }
    }
    T.ok(n >= 25, `${n} cs-Keyframes gefunden`);
  });
```

Außerdem im bestehenden Test `Cutscene.CAST: Story-3-Figuren und Hintergründe` ändern:

```js
    T.ok(Cutscene.SETS.bahnhof && Cutscene.SETS.pfandleihe, 'Kulissen');
    const probe = document.createElement('div'); probe.className = 'cs-sky bahnhof'; document.body.append(probe);
```

(statt `Cutscene.PROPS…` und `'cs-bg bahnhof'`).

- [ ] **Step 2: DOM-Tests laufen lassen – müssen fehlschlagen**

Run: `tests/dom-selftest.sh`
Expected: `failed=` ≥ 2 (Bühnen-Test und Kulissen-Test scheitern, weil `Cutscene.SETS`, `.cs-sky`, `.cs-fig` fehlen; weil der Bühnen-Test die alte Engine mitten in einer Szene stehen lässt, können Folgetests wie „Royal verlassen“ ebenfalls rot sein – das verschwindet mit Step 3/4).

- [ ] **Step 3: CSS-Abschnitt 5 ersetzen**

Alles von `/* ==== 5. CUTSCENE ==== */` bis (ausschließlich) `/* ==== 6. SPIELE & RÄUME ==== */` durch folgenden Block ersetzen:

```css
/* ==== 5. CUTSCENE – Bühne ==== */
#cutscene { position: fixed; inset: 0; z-index: 80; background: #000; overflow: hidden; animation: fadeIn .3s ease both; }
#cutscene[hidden] { display: none; }
/* Welt = alles, was die Kamera zoomt: Himmel, Kulisse, Boden, Figuren, Vordergrund */
.cs-world { position: absolute; inset: 0; contain: paint; transform-origin: 50% 50%; transition: transform .6s ease; }
.cs-world.cs-fade { animation: csFade .5s ease both; }
.cs-sky, .cs-back, .cs-actors, .cs-front { position: absolute; inset: 0; }
.cs-front { pointer-events: none; }
.cs-sky::after { content: ""; position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 40%, transparent 30%, rgba(0,0,0,.7) 100%); }
.cs-sky.bar { background: linear-gradient(180deg, #3a1f0c 0%, #1a0d05 60%, #000 100%); }
.cs-sky.hinterzimmer { background: radial-gradient(circle at 50% 20%, #5a3a12 0%, #1e1207 40%, #000 100%); }
.cs-sky.standesamt { background: linear-gradient(180deg, #f3e6c8 0%, #c9b58f 60%, #6b5b3f 100%); }
.cs-sky.villa { background: linear-gradient(180deg, #0a1636 0%, #16244d 50%, #0a0f1f 100%); }
.cs-sky.hafen { background: linear-gradient(180deg, #02050f 0%, #0a1a33 55%, #041020 100%); }
.cs-sky.hafen-morgen { background: linear-gradient(180deg, #2c2a4a 0%, #c4573b 45%, #f0a35a 70%, #3b2a2a 100%); }
.cs-sky.klinik { background: linear-gradient(180deg, #0d3b3f 0%, #0a2224 60%, #020a0b 100%); }
.cs-sky.bank { background: linear-gradient(180deg, #0c1f33 0%, #123a5c 50%, #06131f 100%); }
.cs-sky.strasse { background: linear-gradient(180deg, #7fb2e5 0%, #c7d7e3 50%, #5b5b4d 100%); }
.cs-sky.keller { background: radial-gradient(circle at 50% 10%, #4a4a3a 0%, #151512 40%, #000 100%); }
.cs-sky.bahnhof { background: linear-gradient(180deg, #05070d 0%, #1a2233 45%, #3b3a2a 100%); }
.cs-sky.pfandleihe { background: linear-gradient(180deg, #2a2418 0%, #14110a 60%, #000 100%); }
.cs-sky.gasse { background: linear-gradient(180deg, #05070d 0%, #1a1e2a 60%, #2a2a26 100%); }
.cs-sky.autohaus { background: linear-gradient(180deg, #1a1e26 0%, #2a2e38 100%); }
.cs-sky.intersport { background: linear-gradient(180deg, #dfe6ee 0%, #b8c4d0 100%); }
.cs-sky.royal { background: radial-gradient(circle at 50% 0%, #3a0a10 0%, #12060a 60%, #000 100%); }
.cs-set { position: absolute; inset: 0; width: 100%; height: 100%; }
.cs-floor { position: absolute; left: 0; right: 0; bottom: 0; height: 12%; background: linear-gradient(#1a1610, #0a0806); border-top: 1px solid rgba(255,255,255,.08); }
/* Figuren: Position nur per transform (--x in px, von der Engine gesetzt). Aufbau: .cs-fig (Platz) > .cs-fig-inner (Blickrichtung --face,
   Schwanken) > .cs-body (Atmen, Umfallen, Zucken) > acht gestapelte Teil-SVGs (Beine, Rumpf, Arme, Kopf, Augen, Mund) mit derselben viewBox.
   Drehpunkte in Prozent der Figur (100×180 Einheiten): Schulter (21|79 %, 45.6 %), Hüfte (38|61 %, 65.6 %), Hals (50 %, 34.4 %), Standlinie (50 %, 95.6 %). */
.cs-fig { position: absolute; left: 0; bottom: 12%; height: min(42vh, 380px); aspect-ratio: 5 / 9; --x: 0px; --face: 1; transform: translateX(calc(var(--x) - 50%)); transition: transform .6s ease; filter: drop-shadow(0 8px 8px rgba(0,0,0,.7)); z-index: 1; }
.cs-fig.walking { will-change: transform; }
.cs-fig.far { transform: translateX(calc(var(--x) - 50%)) translateY(-25%) scale(.6); z-index: 0; }
.cs-fig::after { content: ""; position: absolute; left: 50%; bottom: -6px; width: 120%; height: 24px; transform: translateX(-50%); background: radial-gradient(ellipse, rgba(201,162,39,.35), transparent 70%); opacity: 0; transition: opacity .4s; z-index: -1; }
.cs-fig.speaking::after { opacity: 1; }
.cs-fig-inner { position: absolute; inset: 0; transform: scaleX(var(--face)); transform-origin: 50% 50%; }
.cs-fig-inner.klein { top: 15%; }
.cs-fig-inner.sway { animation: csSway 2.4s ease-in-out infinite; transform-origin: 50% 100%; }
.cs-body { position: absolute; inset: 0; transform-origin: 50% 95.6%; }
.cs-fig .part { position: absolute; inset: 0; width: 100%; height: 100%; display: block; overflow: visible; }
.cs-fig .m { opacity: 0; }
.mood-calm .m-calm, .mood-angry .m-angry, .mood-happy .m-happy, .mood-shock .m-shock, .mood-dead .m-dead { opacity: 1; }
.cs-fig .eyes { animation: csBlink 4s infinite; transform-origin: 50% 26.7%; }
.cs-fig .ember { animation: csGlow 1.4s infinite; }
.cs-fig.talking .mouth { animation: csMouth .25s steps(2) infinite; transform-origin: 50% 33.9%; }
/* Posen */
.cs-fig[data-pose="idle"] .cs-body { animation: csBreathe 3s ease-in-out infinite; }
.cs-fig[data-pose="talk"] .cs-body { animation: csNod .5s ease-in-out infinite; }
.cs-fig[data-pose="talk"] .armR { animation: csTalkArm 1.2s ease-in-out infinite; }
.cs-fig .armL, .cs-fig .armR, .cs-fig .legL, .cs-fig .legR { transition: transform .3s ease; }
.cs-fig .armL { transform-origin: 21% 45.6%; } .cs-fig .armR { transform-origin: 79% 45.6%; }
.cs-fig .legL { transform-origin: 38% 65.6%; } .cs-fig .legR { transform-origin: 61% 65.6%; }
.cs-fig.speaking .mood-happy .cs-body { animation: bounce .7s infinite; }   /* nach talk: froher Sprecher wippt statt zu nicken */
.cs-fig[data-pose="point"] .armR { transform: rotate(-70deg); }
.cs-fig[data-pose="arms-crossed"] .armL { transform: rotate(-75deg); }
.cs-fig[data-pose="arms-crossed"] .armR { transform: rotate(75deg); }
.cs-fig[data-pose="hands-up"] .armL { transform: rotate(160deg); }
.cs-fig[data-pose="hands-up"] .armR { transform: rotate(-160deg); }
.cs-fig[data-pose="walk"] .legL, .cs-fig[data-pose="walk"] .armR { animation: csStepA .4s ease-in-out infinite alternate; }
.cs-fig[data-pose="walk"] .legR, .cs-fig[data-pose="walk"] .armL { animation: csStepB .4s ease-in-out infinite alternate; }
.cs-fig[data-pose="down"] .cs-body { transform: rotate(85deg); transition: transform .5s ease-in; }
.cs-fig[data-pose="flinch"] .cs-body { animation: csFlinch .4s ease both; }
@keyframes csFade { from { opacity: 0; } to { opacity: 1; } }
@keyframes csBlink { 0%, 94%, 100% { transform: scaleY(1); } 97% { transform: scaleY(.1); } }
@keyframes csGlow { 50% { opacity: .4; } }
@keyframes csSway { 0%, 100% { transform: scaleX(var(--face)) rotate(-2deg); } 50% { transform: scaleX(var(--face)) rotate(2deg); } }
@keyframes csMouth { from { transform: scaleY(1); } to { transform: scaleY(2.2); } }
@keyframes csBreathe { 0%, 100% { transform: scaleY(1); } 50% { transform: scaleY(1.02); } }
@keyframes csNod { 0%, 100% { transform: rotate(0); } 50% { transform: rotate(-1.5deg); } }
@keyframes csTalkArm { 0%, 100% { transform: rotate(0); } 50% { transform: rotate(-35deg); } }
@keyframes csStepA { from { transform: rotate(-20deg); } to { transform: rotate(20deg); } }
@keyframes csStepB { from { transform: rotate(20deg); } to { transform: rotate(-20deg); } }
@keyframes csFlinch { 0% { transform: translateX(0) rotate(0); } 30% { transform: translateX(-12px) rotate(-8deg); } 100% { transform: translateX(-4px) rotate(-3deg); } }
/* Sprechblase, Ausruf, Streifen */
.cs-bubble { position: absolute; z-index: 5; max-width: min(460px, 70%); background: #f4efe2; color: #1a1208; border-radius: 14px; border-left: 5px solid var(--c, #8b1e1e); padding: 10px 14px 18px; box-shadow: 0 6px 18px rgba(0,0,0,.6); animation: popIn .18s ease both; --tail: 40px; }
.cs-bubble[hidden] { display: none; }
.cs-bubble::after { content: ""; position: absolute; left: var(--tail); bottom: -12px; margin-left: -10px; border: 10px solid transparent; border-top-color: #f4efe2; border-bottom: 0; }
.cs-bubble.narrator { background: rgba(12,12,10,.92); color: var(--text); border: 1px solid var(--gold); }
.cs-bubble.narrator::after { display: none; }
.cs-name { font-family: var(--font-display); letter-spacing: .14em; font-size: .8rem; color: #5a3020; margin-bottom: 4px; }
.cs-bubble.narrator .cs-name { color: var(--gold-2); }
.cs-text { font-size: 1.05rem; line-height: 1.5; }
.cs-next { position: absolute; right: 12px; bottom: 4px; color: #8b1e1e; animation: bob 1s infinite; font-size: .9rem; }
.cs-shout { position: absolute; z-index: 6; font-family: var(--font-display); font-size: 2.6rem; letter-spacing: .06em; color: #fff; text-shadow: 0 0 14px var(--neon-red), 0 0 30px var(--neon-red); opacity: 0; pointer-events: none; transform: translate(-50%, -110%) rotate(-8deg); }
.cs-shout.on { animation: csShout .9s ease both; }
@keyframes csShout { 0% { opacity: 0; transform: translate(-50%, -110%) rotate(-8deg) scale(.4); } 15% { opacity: 1; transform: translate(-50%, -110%) rotate(-8deg) scale(1.15); } 25% { transform: translate(-50%, -110%) rotate(-8deg) scale(1); } 80% { opacity: 1; } 100% { opacity: 0; transform: translate(-50%, -130%) rotate(-8deg) scale(1); } }
.cs-bar { position: absolute; left: 0; right: 0; bottom: 0; z-index: 5; display: flex; align-items: flex-end; gap: 12px; padding: 12px 16px; pointer-events: none; }
.cs-bar > * { pointer-events: auto; }
.cs-bar-mid { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.cs-money { font-family: var(--font-mono); font-size: 1.3rem; font-weight: 700; color: var(--gold-2); background: rgba(0,0,0,.5); padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(201,162,39,.4); }
.cs-money.up { animation: pulseGold .6s ease both; }
.cs-money.down { animation: pulseRed .6s ease both; }
.cs-skip { background: rgba(0,0,0,.4); border: 1px solid rgba(255,255,255,.2); color: var(--dim); font-family: var(--font-display); letter-spacing: .1em; padding: 6px 12px; border-radius: 4px; }
.cs-skip:hover { color: var(--text); border-color: var(--text); }
.cs-choices { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
.cs-choices:empty { display: none; }
.cs-extra:empty { display: none; }
.cs-stats { display: grid; grid-template-columns: 1fr auto; gap: 4px 20px; font-family: var(--font-mono); background: rgba(12,12,10,.92); border: 1px solid var(--gold); border-radius: 8px; padding: 10px 14px; }
.cs-stats span:nth-child(even) { text-align: right; color: var(--gold-2); }
.cs-flash { position: absolute; inset: 0; background: #fff; z-index: 4; pointer-events: none; opacity: 0; }
.cs-flash.on { animation: flash .18s ease both; }
.cs-black { position: absolute; inset: 0; background: #000; z-index: 4; pointer-events: none; opacity: 0; transition: opacity .5s; }
.cs-black.on { opacity: 1; }
.cs-particle { position: absolute; z-index: 3; pointer-events: none; animation: particleUp 1.6s ease-out both; }
/* Sofort-Modus (Tests, Skip, reduced-motion): keine Wege, keine Überblendung */
.cs-instant .cs-fig, .cs-instant .cs-world { transition: none !important; }
.cs-instant .cs-world.cs-fade { animation: none; }
/* Kulissen-Leben – ausschließlich transform/opacity */
.life-neon { animation: csFlicker 3s infinite; }
.life-flicker { animation: csFlicker 4s infinite; }
.life-smoke { animation: csSmoke 4s ease-in-out infinite; }
.life-blink { animation: csBlinkLight 2s steps(2) infinite; }
.life-swing { animation: csSwing 5s ease-in-out infinite; }
.life-candle { animation: csCandle .8s ease-in-out infinite alternate; }
.life-car { animation: csCar 9s linear infinite; }
.life-rain { animation: csRain .7s linear infinite; }
.life-cat { animation: csCat 14s linear infinite; }
.life-wave { animation: csWave 3s ease-in-out infinite; }
.life-gull { animation: csGull 12s linear infinite; }
.life-sun { animation: csSun 30s linear both; }
.life-ekg { animation: csPulse 1.2s ease-in-out infinite; }
.life-ticker { animation: csTicker 3s steps(1) infinite; }
.life-dust { animation: csDust 4s linear infinite; }
.life-city { animation: csTicker 3s steps(1) infinite; }
.life-shimmer { animation: csShimmer 2s linear infinite; }
.life-train { animation: csTrain 12s linear infinite; }
.life-tick { animation: csTick 60s steps(60) infinite; }
.life-sway { animation: csLean 4s ease-in-out infinite; }
.life-spot { animation: csSpot 6s ease-in-out infinite; }
.life-glitter { animation: csGlitter 1.6s ease-in-out infinite; }
@keyframes csFlicker { 0%, 92%, 100% { opacity: 1; } 94% { opacity: .3; } 96% { opacity: 1; } 98% { opacity: .5; } }
@keyframes csSmoke { 0% { transform: translateY(0); opacity: .25; } 100% { transform: translateY(-40px); opacity: 0; } }
@keyframes csBlinkLight { 50% { opacity: .4; } }
@keyframes csSwing { 0%, 100% { transform: rotate(-3deg); } 50% { transform: rotate(3deg); } }
@keyframes csCandle { from { transform: scale(1); } to { transform: scale(.85, 1.1); } }
@keyframes csCar { 0%, 55% { transform: translateX(0); } 100% { transform: translateX(1300px); } }
@keyframes csRain { from { transform: translateY(0); } to { transform: translateY(400px); } }
@keyframes csCat { 0%, 70% { transform: translateX(-60px); } 90%, 100% { transform: translateX(1100px); } }
@keyframes csWave { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(50px); } }
@keyframes csGull { from { transform: translate(200px, 120px); } to { transform: translate(900px, 80px); } }
@keyframes csSun { from { transform: translateY(80px); } to { transform: translateY(0); } }
@keyframes csPulse { 50% { opacity: .4; } }
@keyframes csTicker { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
@keyframes csDust { 0% { transform: translate(0, 0); opacity: 0; } 50% { opacity: .8; } 100% { transform: translate(-20px, 40px); opacity: 0; } }
@keyframes csShimmer { from { transform: translateX(0); } to { transform: translateX(70px); } }
@keyframes csTrain { 0%, 60% { transform: translateX(0); } 100% { transform: translateX(2200px); } }
@keyframes csTick { to { transform: rotate(360deg); } }
@keyframes csLean { 0%, 100% { transform: rotate(-1.5deg); } 50% { transform: rotate(1.5deg); } }
@keyframes csSpot { 0%, 100% { transform: rotate(-12deg); } 50% { transform: rotate(12deg); } }
@keyframes csGlitter { 50% { opacity: .2; } }
/* Hochkant: Kulisse doppelt so breit wie die Bühne zeichnen (zeigt die Mitte), sonst wäre sie nur ein schmaler Streifen am Boden */
@media (max-aspect-ratio: 4/5) { .cs-set { width: 200%; left: -50%; } }
@media (max-width: 760px) {
  .cs-fig { height: min(30vh, 240px); }
  .cs-bubble { max-width: 70%; padding: 8px 10px 16px; }
  .cs-text { font-size: .95rem; }
  .cs-bar { padding: 8px 10px; gap: 8px; }
  .cs-money { font-size: 1rem; padding: 4px 8px; }
}
@media (prefers-reduced-motion: reduce) {
  #cutscene .cs-set *, .cs-fig, .cs-fig *, .cs-world, .cs-bubble, .cs-shout, .cs-next { animation: none !important; transition: none !important; }
  .cs-fig-inner { transform: scaleX(var(--face)) !important; }
}
```

Dann die Zeile `.cs-portrait.royal-frame { … }` löschen und in der reduced-motion-Liste `.cs-portrait, ` entfernen (`grep -n "cs-portrait" keller37.html` muss danach nichts mehr finden).

- [ ] **Step 4: Engine ersetzen**

Im Block `cutscene-engine` das gesamte `Cutscene`-Objekt (vom Kommentar `/* ================= CUTSCENE – Visual-Novel-Engine ================= */` bis einschließlich der schließenden `};` unmittelbar vor `/* ---- Szenen: Intro & Neues Spiel ---- */`) ersetzen durch:

```js
/* ================= CUTSCENE – Bühnen-Engine: Kulissen, Figuren, Sprechblase, Regie ================= */
const Cutscene = {
  active: false,
  instant: false,           // Dev/Tests: keine Laufwege, kein Tippen, keine Wartezeiten (wie prefers-reduced-motion)
  SKIP: Symbol('skip'),
  CAST: CsCast.CAST,
  SETS: CsSets.SETS,
  SCENES: {},
  WALK_MS: 600,
  SLOT_X: { left: 0.18, mid: 0.5, right: 0.82, far: 0.5 },
  define(id, panels) { this.SCENES[id] = panels; },
  bind(eventName, sceneId) { Bus.on(eventName, (ctx) => this.play(sceneId, ctx)); },
  fill(text, ctx) { return text.replace(/\{\{(\w+)\}\}/g, (_, k) => (k in ctx ? String(ctx[k]) : `{{${k}}}`)); },
  quick() { return this.instant || matchMedia('(prefers-reduced-motion: reduce)').matches; },
  async play(id, ctx = {}) {
    const def = this.SCENES[id];
    if (!def) { console.warn('[cutscene] Szene fehlt:', id); return undefined; }
    while (this.active) await wait(50);
    const panels = typeof def === 'function' ? def(ctx) : def;
    this.active = true;
    document.body.classList.add('cs-open');
    SFX.stopAll();
    const root = qs('#cutscene');
    root.innerHTML = '';
    const els = {
      root,
      world: h('div', { class: 'cs-world' }),
      sky: h('div', { class: 'cs-sky' }), back: h('div', { class: 'cs-back' }), floor: h('div', { class: 'cs-floor' }),
      actors: h('div', { class: 'cs-actors' }), front: h('div', { class: 'cs-front' }),
      flash: h('div', { class: 'cs-flash' }), black: h('div', { class: 'cs-black' }),
      shout: h('div', { class: 'cs-shout' }),
      bubble: h('div', { class: 'cs-bubble' }),
      name: h('div', { class: 'cs-name' }), text: h('div', { class: 'cs-text' }), next: h('div', { class: 'cs-next' }, '▼'),
      money: h('div', { class: 'cs-money money-live' }, UI.fmt(UI.shownBalance)),
      extra: h('div', { class: 'cs-extra' }), choices: h('div', { class: 'cs-choices' }),
      skip: h('button', { class: 'cs-skip' }, 'Überspringen ⏭'),
      figs: new Map(), bg: null, look: {}, parts: CsCast.duParts(State.s), skipping: false,
    };
    els.bubble.append(els.name, els.text, els.next); els.bubble.hidden = true;
    els.world.append(els.sky, els.back, els.floor, els.actors, els.front);
    els.bar = h('div', { class: 'cs-bar' }, els.money, h('div', { class: 'cs-bar-mid' }, els.extra, els.choices), els.skip);
    root.append(els.world, els.flash, els.black, els.shout, els.bubble, els.bar);
    root.classList.toggle('cs-instant', this.quick());
    root.hidden = false;
    const plan = CsDirector.stagePlan(panels);
    let result;
    for (let i = 0; i < panels.length; i++) {
      const isLast = i === panels.length - 1;
      const r = await this._panel(els, panels[i], plan[i], ctx, isLast);
      if (r === this.SKIP) {
        for (let j = i + 1; j < panels.length - 1; j++) this._fx(els, panels[j].fx, ctx, true);
        els.skipping = true; root.classList.add('cs-instant'); els.world.style.transform = ''; // letztes Panel ohne Laufwege in den Endzustand, Kamera zurück
        i = panels.length - 2;
        continue;
      }
      if (r !== undefined) result = r;
    }
    root.hidden = true;
    root.innerHTML = '';
    this.active = false;
    document.body.classList.remove('cs-open');
    UI.setBalance(State.s.balance, { animate: false });
    UI.renderWallet();
    return result;
  },
  offX(side, W) { return side === 'left' ? -0.3 * W : 1.3 * W; },
  /* Kulisse, Figuren und Kamera eines Panels setzen; liefert die Sprecher-Figur oder null (leere Bühne / Erzähler) */
  _stage(els, p, plan, instant) {
    const W = els.actors.clientWidth, H = els.actors.clientHeight;
    if (plan.bg !== els.bg) {
      const known = !!this.SETS[plan.bg], set = this.SETS[known ? plan.bg : 'bar'];
      els.sky.className = `cs-sky ${known ? plan.bg : 'bar'}`;
      els.back.innerHTML = set.back(); els.front.innerHTML = set.front();
      if (els.bg !== null && !instant) { els.world.classList.remove('cs-fade'); void els.world.offsetWidth; els.world.classList.add('cs-fade'); }
      els.bg = plan.bg;
    }
    if (p.look) for (const [who, l] of Object.entries(p.look)) els.look[who] = Object.assign({}, els.look[who], l);
    for (const who of plan.exit) {
      const f = els.figs.get(who); if (!f) continue;
      els.figs.delete(who);
      f.el.classList.add('walking'); f.el.classList.remove('speaking'); f.el.dataset.pose = 'walk';
      f.el.style.setProperty('--x', `${this.offX(CsDirector.side(who), W)}px`);
      if (instant || plan.bgChange) f.el.remove(); else setTimeout(() => f.el.remove(), this.WALK_MS); // beim Kulissenwechsel deckt die Überblendung den Abgang
    }
    for (const [who, f] of [...els.figs]) if (!plan.cast.some((c) => c.who === who)) { els.figs.delete(who); f.el.remove(); } // nach Skip/Kulissenwechsel: nur die geplante Besetzung bleibt
    let speaker = null;
    for (const c of plan.cast) {
      let f = els.figs.get(c.who);
      const entering = plan.enter.find((e) => e.who === c.who);
      if (!f) {
        f = { who: c.who, el: h('div', { class: 'cs-fig' }), key: null };
        els.figs.set(c.who, f); els.actors.append(f.el);
        f.el.style.setProperty('--x', `${this.offX(entering ? entering.from : CsDirector.side(c.who), W)}px`);
        if (!instant) void f.el.offsetWidth; // Startposition festschreiben, sonst gibt es keinen Weg zu animieren
      }
      const look = els.look[c.who] || {};
      const key = `${c.mood}|${look.hurt || ''}`;
      if (f.key !== key) { f.el.innerHTML = CsCast.figureHtml(c.who, { mood: c.mood, parts: c.who === 'du' ? els.parts : null, hurt: look.hurt }); f.key = key; }
      f.el.style.setProperty('--x', `${this.SLOT_X[c.slot] * W}px`);
      f.el.style.setProperty('--face', String(c.facing));
      f.el.classList.toggle('far', c.slot === 'far');
      const walking = !!entering && !instant;
      f.el.classList.toggle('walking', walking);
      if (walking) setTimeout(() => f.el.classList.remove('walking'), this.WALK_MS);
      f.el.dataset.pose = walking ? 'walk' : c.pose;
      if (walking) setTimeout(() => { if (f.el.isConnected) f.el.dataset.pose = c.pose; }, this.WALK_MS);
      f.el.classList.toggle('speaking', c.who === plan.speaker);
      if (c.who === plan.speaker) speaker = f;
    }
    if (plan.cam === 'shake') UI.shake(els.world);
    else if (plan.cam === 'wide') els.world.style.transform = '';
    else if (plan.cam === 'close' && speaker) {
      const slot = plan.cast.find((c) => c.who === speaker.who).slot;
      els.world.style.transformOrigin = `${this.SLOT_X[slot] * W}px ${H * (slot === 'far' ? 0.35 : 0.45)}px`;
      els.world.style.transform = 'scale(1.8)';
    }
    return speaker;
  },
  /* Kopfposition einer Figur relativ zur Bühne – einmal pro Panel gemessen, nie pro Frame */
  _headAt(els, fig) {
    const R = els.root.getBoundingClientRect(), head = qs('.head', fig.el).getBoundingClientRect();
    return { x: head.left + head.width / 2 - R.left, y: head.top - R.top, W: R.width };
  },
  /* Blase über dem Sprecher; ohne Sprecher (leere Bühne) als Erzähler-Blase oben mittig */
  _placeBubble(els, speaker, full) {
    const b = els.bubble;
    b.hidden = false; b.style.width = ''; b.style.minHeight = '';
    b.classList.toggle('narrator', !speaker);
    els.text.textContent = full;                       // volle Größe messen, dann wieder leeren und tippen
    const bw = b.offsetWidth, bh = b.offsetHeight;
    b.style.width = `${bw}px`; b.style.minHeight = `${bh}px`;
    if (!speaker) { b.style.left = `${Math.round((els.root.clientWidth - bw) / 2)}px`; b.style.top = '12%'; return; }
    const hd = this._headAt(els, speaker);
    const left = Math.max(8, Math.min(hd.W - bw - 8, Math.round(hd.x - bw / 2)));
    b.style.left = `${left}px`; b.style.top = `${Math.max(8, Math.round(hd.y - bh - 18))}px`;
    b.style.setProperty('--tail', `${Math.round(Math.max(18, Math.min(bw - 18, hd.x - left)))}px`);
  },
  _shout(els, speaker, text) {
    const s = els.shout; s.textContent = text;
    if (speaker) { const hd = this._headAt(els, speaker); s.style.left = `${Math.round(hd.x)}px`; s.style.top = `${Math.round(hd.y)}px`; }
    else { s.style.left = '50%'; s.style.top = '40%'; }
    s.classList.remove('on'); void s.offsetWidth; s.classList.add('on');
  },
  _panel(els, p, plan, ctx, isLast) {
    return new Promise((resolve) => {
      const who = this.CAST[p.who] || this.CAST.du;
      const instant = this.quick() || els.skipping;
      els.bubble.hidden = true; els.choices.innerHTML = ''; els.extra.innerHTML = ''; els.next.style.visibility = 'hidden';
      els.skip.style.display = isLast ? 'none' : '';
      els.name.textContent = who.name; els.bubble.style.setProperty('--c', who.color); // Sprecher sofort bekannt (Blase erscheint nach dem Auftritt)
      const speaker = this._stage(els, p, plan, instant);
      const moving = plan.enter.length > 0 || plan.exit.length > 0 || plan.cam === 'close' || plan.cam === 'wide';
      this._fx(els, p.fx, ctx, false);
      if (p.sfx) SFX.play(p.sfx);
      const full = this.fill(p.text || '', ctx);
      let typing = false, started = false, finished = false, showAll = false, pos = 0, timer = null, skipWait = null;
      const waitOr = (ms) => new Promise((r) => { if (!ms || instant) return r(); skipWait = r; setTimeout(r, ms); });
      const renderChoices = () => {
        for (const c of p.choices) els.choices.append(h('button', { class: 'btn ' + (c.cls || ''), onclick: (e) => { e.stopPropagation(); SFX.play('click'); done(c.value); } }, c.label));
      };
      const finish = () => {
        typing = false; clearTimeout(timer); els.text.textContent = full;
        if (speaker) speaker.el.classList.remove('talking');
        if (p.choices) renderChoices(); else els.next.style.visibility = 'visible';
      };
      const tick = () => {
        if (!typing) return;
        pos++;
        els.text.textContent = full.slice(0, pos);
        if (pos % 3 === 0) SFX.play('typewriter');
        if (pos >= full.length) { finish(); return; }
        const ch = full[pos - 1];
        timer = setTimeout(tick, /[.!?…]/.test(ch) ? 120 : /[,;:]/.test(ch) ? 60 : 30);
      };
      const onClick = (e) => {
        if (e.target.closest('.cs-choices') || e.target.closest('.cs-skip')) return;
        if (!started) { showAll = true; if (skipWait) skipWait(); return; }   // Klick während Auftritt/Pause: Weg abkürzen, Text komplett zeigen (wie Klick ins Tippen)
        if (typing) finish(); else if (!p.choices) done(undefined);
      };
      const onKey = (e) => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); onClick({ target: els.text }); } };
      const onSkip = (e) => { e.stopPropagation(); done(this.SKIP); };
      const cleanup = () => { typing = false; clearTimeout(timer); els.root.removeEventListener('click', onClick); document.removeEventListener('keydown', onKey); els.skip.removeEventListener('click', onSkip); };
      const done = (v) => { if (finished) return; finished = true; cleanup(); resolve(v); };
      els.root.addEventListener('click', onClick);
      document.addEventListener('keydown', onKey);
      els.skip.addEventListener('click', onSkip);
      (async () => {
        await waitOr(moving ? this.WALK_MS : 0);
        if (finished) return;
        await waitOr(p.pause || 0);
        if (finished) return;
        if (p.shout) this._shout(els, speaker, p.shout);
        this._placeBubble(els, speaker, full);
        started = true;
        if (instant || showAll) { finish(); return; }
        typing = true; els.text.textContent = '';
        if (speaker) speaker.el.classList.add('talking');
        tick();
      })();
    });
  },
  _fx(els, fx, ctx, instant) {
    if (!fx) return;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    switch (fx) {
      case 'flash': if (!instant) { els.flash.classList.remove('on'); void els.flash.offsetWidth; els.flash.classList.add('on'); } break;
      case 'shake': if (!instant) UI.shake(els.root); break;
      case 'blackout': if (!instant && !reduced) { els.black.classList.add('on'); SFX.play('blackout'); setTimeout(() => els.black.classList.remove('on'), 900); } break;
      case 'hearts': if (!instant && !reduced) this._particles(els, ['❤️', '💕', '💖'], 14); break;
      case 'coins': if (!instant && !reduced) { this._particles(els, ['🪙', '💶', '💰'], 24); SFX.play('cash'); } break;
      case 'drain': UI.setBalance(State.s.balance, { animate: !instant, duration: 1800 }); if (!instant) { UI.pulseBalance(-1); SFX.play('lose'); } break;
      case 'gain': UI.setBalance(State.s.balance, { animate: !instant, duration: 1200 }); if (!instant) { UI.pulseBalance(1); SFX.play('cash'); } break;
      case 'stats': {
        const grid = h('div', { class: 'cs-stats' });
        for (const [k, v] of Object.entries(ctx.stats || {})) grid.append(h('span', {}, k), h('span', {}, String(v)));
        els.extra.append(grid);
        break;
      }
      case 'insiderCards': {
        const grid = h('div', { class: 'cs-insider-cards' });
        for (const d of ctx.insiders || []) grid.append(h('div', { class: 'insider-chip' }, h('b', {}, `${d.icon} ${d.name}`), d.text, h('small', {}, Rules.insiderCapText(d))));
        els.extra.append(grid);
        break;
      }
      default: console.warn('[cutscene] fx unbekannt:', fx);
    }
  },
  _particles(els, glyphs, n) {
    for (let i = 0; i < n; i++) {
      const p = h('span', { class: 'cs-particle', style: `left:${rand(5, 95)}%; top:${rand(40, 90)}%; animation-delay:${rand(0, 0.6)}s; font-size:${rand(1.2, 2.4)}rem` }, pick(glyphs));
      els.root.append(p);
      setTimeout(() => p.remove(), 2400);
    }
  },
};
```

Falls das alte `_fx` weitere `case`-Zweige hatte als `flash, shake, blackout, hearts, coins, drain, gain, stats, insiderCards`: übernehmen und in `CsDirector.FX` ergänzen.

- [ ] **Step 5: Playtest-Selektoren anpassen**

In `tests/playtest-story.py`:
- `document.querySelector('#cutscene .cs-bg')` → `document.querySelector('#cutscene .cs-sky')`
- `document.querySelector('.cs-box').textContent` → `document.querySelector('.cs-bubble').textContent`

Sonst nichts – die Klick-Semantik (Klick 1 = Text komplett, Klick 2 = weiter) ist unverändert, weil ein Klick während des Auftritts den Weg abkürzt **und** den Text komplett zeigt (`showAll`).

- [ ] **Step 6: Alle Tests laufen lassen**

Run: `node tests/run-selftest.mjs && tests/dom-selftest.sh`
Expected: Node `0 fehlgeschlagen`; DOM `failed=0` (zwei Tests mehr als vor Task 4).

Run: `python3 tests/playtest-story.py 2>&1 | grep -E "FEHLGESCHLAGEN|ERRORS"`
Expected: `ERRORS 0`; keine Fehlschläge außer ggf. `freie sandbox: … (Pixel-Diff)` – die brauchen Referenzbilder unter `/tmp/k37story/` und schlagen ohne sie auch auf `main` fehl (vorher auf `main` prüfen und im Ledger notieren).

- [ ] **Step 7: Sichtprüfung**

`?screen=hub&fresh&scene=mafia.legbreak` und `?screen=hub&fresh&scene=intro` im Browser öffnen (Desktop und Handy-Emulation 412×915): Figuren laufen ein, Blase am Kopf des Sprechers, Kulisse mit Leben, Mobil keine Überbreite, Klick während des Auftritts zeigt den Text sofort, Überspringen springt in den Endzustand.

- [ ] **Step 8: Commit**

```bash
git add keller37.html tests/playtest-story.py
git commit -m "feat(cutscene): Bühnen-Engine – Kulissen-Ebenen, Figuren per transform, Sprechblase am Sprecher, Kamera, Regie-Schlüssel

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Regie-Validierung aller Szenen

**Files:**
- Modify: `keller37.html` – Node-Test hinter den `CsSets`-Tests (Task 3)
- Modify: `keller37.html` – DOM-Test vor `const pseudoAnim = …`
- Modify: `keller37.html` – `Stories.validateAll()` im Block `story-engine`

**Interfaces:**
- Consumes: `CsDirector.validatePanels`, `CsCast.CAST`, `SFX.LIB`, `STORY_PROBE/SCHULD/KATER/STASH`, `Cutscene.SCENES`.

- [ ] **Step 1: Node-Test schreiben**

Hinter den `CsSets`-Tests einfügen:

```js
/* ---- Regie-Validierung: jede Szene, jeder Schlüssel ---- */
if (typeof CsDirector !== 'undefined' && typeof STORY_SCHULD !== 'undefined') {
  T.test('Regie: alle Story-Szenen (Probe, Schuld, Kater, Wäsche) bestehen validatePanels', () => {
    const ctx = { raw: { vars: { woche: 1, lieferung: 10000, ziel: 20000, rueckgabe: 11000, letztePay: 11000, kredit: 0, zorn: 0, ausgang: 0, letzterUeberfall: 'slots', letzterRaub: 500, hinterhaltN: 2, igorBiere: 0, belege: 1, belegeOffen: 1, uebergeben: 0 }, flags: {} }, prev: {}, flags: {} };
    const castIds = Object.keys(CsCast.CAST);
    const errs = []; let n = 0;
    for (const story of [STORY_PROBE, STORY_SCHULD, STORY_KATER, STORY_STASH]) {
      for (const [id, def] of Object.entries(story.scenes || {})) {
        const panels = typeof def === 'function' ? def(ctx) : def;
        n += panels.length;
        errs.push(...CsDirector.validatePanels(id, panels, { castIds }));
      }
    }
    T.eq(errs, []);
    T.ok(n > 200, `${n} Panels geprüft`);
  });
}
```

- [ ] **Step 2: DOM-Test schreiben**

Vor `  const pseudoAnim = …` (hinter den Tests aus Task 4) einfügen:

```js
  T.test('Regie: alle Keller-Szenen (Cutscene.SCENES) bestehen validatePanels, Sounds im SFX-Register', () => {
    const ctx = { type: { intro: ['a', 'b'], fightWon: 'a', fightLost: 'a', fled: 'a', caught: 'a', paid: 'a' }, loot: '1 €', fight: 50, flee: 50, wallet: '1 €', strength: 1, extra: '0 €',
      choices: [{ label: 'x', value: 'x' }], texts: '', old: 'a', tradeIn: '1 €', neu: 'b', cost: '1 €', name: 'n', price: '1 €', amount: '1 €', fee: '1 €', limit: '1 €', rate: 1, debt: '1 €', bill: '1 €', before: '1 €', after: '1 €', balance: '1 €', stats: {},
      raw: { vars: {}, flags: {} }, prev: {}, flags: {} };
    const castIds = Object.keys(Cutscene.CAST), sfxIds = Object.keys(SFX.LIB);
    const errs = []; let n = 0, skipped = [];
    for (const [id, def] of Object.entries(Cutscene.SCENES)) {
      let panels;
      try { panels = typeof def === 'function' ? def(ctx) : def; } catch (e) { skipped.push(id); continue; }
      n++;
      errs.push(...CsDirector.validatePanels(id, panels, { castIds, sfxIds }));
    }
    T.eq(errs, []);
    T.eq(skipped, [], 'jede Szene lässt sich mit dem Test-Kontext erzeugen');
    T.ok(n >= 60, `${n} Szenen geprüft`);
  });
```

- [ ] **Step 3: Beide laufen lassen**

Run: `node tests/run-selftest.mjs && tests/dom-selftest.sh`
Expected: beide grün – die bestehenden Szenen enthalten noch keine Regie-Schlüssel und nur bekannte `fx`. (Schlägt der DOM-Test mit `skipped` ≠ `[]` fehl, fehlt dem Test-Kontext ein Feld, das eine Funktions-Szene liest: das Feld mit einem Platzhalterwert in `ctx` ergänzen – nicht die Szene ändern.)

- [ ] **Step 4: Validierung in `Stories.validateAll()` einbauen**

In `Stories.validateAll()` (Block `story-engine`) nach der `for (const st of Object.values(this.all)) errs.push(…)`-Zeile ergänzen, damit Tippfehler in Regie-Schlüsseln auch beim Start (Konsole + Toast) auffallen – nur für Szenen ohne Kontext-Funktion, Funktions-Szenen prüft der Selbsttest:

```js
    const castIds = Object.keys(Cutscene.CAST), sfxIds = typeof SFX !== 'undefined' && SFX.LIB ? Object.keys(SFX.LIB) : null;
    for (const [id, def] of Object.entries(Cutscene.SCENES)) if (typeof def !== 'function') errs.push(...CsDirector.validatePanels(id, def, { castIds, sfxIds }));
```

- [ ] **Step 5: Gegenprobe**

Vorübergehend in `Cutscene.define('intro', …)` ein `cam: 'zoom'` einfügen, `tests/dom-selftest.sh` laufen lassen → der DOM-Test aus Step 2 muss `intro[0]: cam "zoom" unbekannt` melden; Änderung zurücknehmen, Tests grün.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "test(cutscene): Regie-Schlüssel aller Szenen validiert (Selbsttest + validateAll)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Hand-Regie – Grundszenen (Keller, Kredite, Überfall, Klinik, Leben)

**Files:**
- Modify: `keller37.html` – Szenen-Definitionen (`Cutscene.define(...)`) in den Blöcken `cutscene-engine`, `rooms`, `game-russian`, `gameover`, `mugging`

**Interfaces:**
- Consumes: Regie-Schlüssel aus `CsDirector.KEYS` (`cast, enter, exit, walk, pose, cam, shout, pause, sfx, look`).

Regel: Nur Schlüssel **ergänzen** – Texte, `bg`, `who`, `mood`, `fx`, `choices` bleiben wörtlich. Panel-Nummern zählen ab 1 in der Reihenfolge der Definition. Fundstelle jeweils `grep -n "Cutscene.define('<id>'"`.

- [ ] **Step 1: Schlüssel eintragen**

| Szene | Panel (Textanfang) | ergänzen |
|---|---|---|
| `intro` | 2 „Hier unten gibt es keine Regeln" | `pose: 'point'` |
| `intro` | 3 „Die Türen sind da drüben" | `cam: 'close'` |
| `gameover` | 1 „Schöner Sonnenaufgang" | `cast: ['du', 'vito']` |
| `gameover` | 2 „Die Bank will nichts mehr" | `cam: 'close'` |
| `gameover` | 3 „Aber ich bin kein Unmensch" | `cam: 'wide', pose: 'point'` |
| `mafia.loan` | 2 „Fünf Spins." | `pose: 'point'` |
| `mafia.loan` | 3 „Ich mag dich." | `cam: 'close', pause: 500` |
| `mafia.lastcall` | 1 | `cam: 'close', pause: 600` |
| `mafia.legbreak` | 1 „Die Frist ist um." | `pose: 'point'` |
| `mafia.legbreak` | 2 „KNACK." | `shout: 'KNACK!', cam: 'shake', look: { du: { hurt: 'kruecke' } }, pose: { who: 'du', pose: 'down' }` |
| `mafia.legbreak` | 3 „Not-OP" | `pose: { who: 'du', pose: 'idle' }` |
| `mug.intro` | 1 „Der kurze Weg" | `cast: ['du'], walk: { who: 'du', to: 'mid' }` |
| `mug.intro` | 2 (`ctx.type.intro[0]`) | `enter: { who: 'raeuber', from: 'right' }, pose: 'point', cam: 'shake', shout: 'HEY!'` |
| `mug.intro` | 3 (`ctx.type.intro[1]`) | `cam: 'close'` |
| `mug.fightWon` | 1 | `pose: { who: 'raeuber', pose: 'down' }, shout: 'ZACK!', cam: 'shake'` |
| `mug.fightWon` | 2 | `cam: 'close'` |
| `mug.fightLost` | 1 | `pose: 'point', cam: 'shake', shout: 'ZACK!'` |
| `mug.fightLost` | 2 | `look: { du: { hurt: 'pflaster' } }` |
| `mug.fled` | 1 | `pose: 'walk', cam: 'shake'` |
| `mug.caught` | 1 | `pose: 'point', cam: 'shake'` |
| `mug.caught` | 2 | `look: { du: { hurt: 'pflaster' } }` |
| `mug.paid` | 1 | `pose: 'point'` |
| `mug.paid` | 2 | `exit: 'raeuber'` |
| `kidney.offer` | 2 „Zweitausend Euro" | `pose: 'point'` |
| `kidney.sold` | 1 „Zähl rückwärts" | `pose: { who: 'du', pose: 'down' }` |
| `kidney.sold` | 2 „Wach? Gut." | `pose: { who: 'du', pose: 'idle' }` |
| `rr.headshot` | 1 | `look: { du: { hurt: 'pflaster' } }, cam: 'shake', shout: 'PÄNG!', sfx: 'gunshot'` |
| `igor.first` | 1 „…" | `pause: 900, cam: 'close'` |
| `igor.first` | letztes „Eine Kugel." | `pose: 'point'` |
| `house.bought` | 1 „Traumlage!" | `pose: 'hands-up'` |
| `house.bought` | 2 „Dreißig Euro die Minute" | `pose: 'point'` |
| `tinder.match` | 1 „Ehrlich jetzt – ein Penthouse?!" | `cam: 'close'` |
| `tinder.match` | 3 „Ja, ich will." | `walk: { who: 'chantal', to: 'mid' }, cam: 'wide'` |
| `divorce` | 1 „Ehrlich jetzt, Schatz" | `pose: 'point'` |
| `divorce` | 2 „Dr. Schmalz" | `walk: { who: 'chantal', to: 'far' }` |
| `divorce` | 3 „{{before}} durch zwei" | `cam: 'close'` |
| `heartbreak.collapse` | 1 „Kreislauf!" | `pose: { who: 'du', pose: 'down' }, cam: 'shake'` |
| `heartbreak.collapse` | 2 „Notarzt" | `pose: { who: 'du', pose: 'idle' }` |

Beispiel (so sieht ein ergänztes Panel aus):

```js
  { bg: 'klinik', who: 'doc', mood: 'shock', fx: 'flash', look: { du: { hurt: 'pflaster' } }, cam: 'shake', shout: 'PÄNG!', sfx: 'gunshot', text: 'Streifschuss! Du Glückspilz. Hundert Euro fürs Pflaster – und für meine Nerven.' },
```

- [ ] **Step 2: Tests**

Run: `node tests/run-selftest.mjs && tests/dom-selftest.sh`
Expected: grün – insbesondere der DOM-Test `Regie: alle Keller-Szenen …` (er würde jeden Tippfehler in den Schlüsseln melden).

- [ ] **Step 3: Sichtprüfung**

`?screen=hub&fresh&scene=mug.intro`, `…scene=mafia.legbreak`, `…scene=rr.headshot`, `…scene=divorce` durchklicken: Räuber kommt von rechts mit „HEY!", du gehst nach dem KNACK zu Boden und hast danach eine Krücke, Pflaster nach dem Streifschuss, Chantal tritt bei Schmalz in den Hintergrund.

- [ ] **Step 4: Commit**

```bash
git add keller37.html
git commit -m "feat(cutscene): Hand-Regie für Intro, Game-over, Kredite, Überfall, Klinik und Leben

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Hand-Regie – Story-Szenen (Schuld, Kater, Wäsche)

**Files:**
- Modify: `keller37.html` – Blöcke `story-schuld`, `story-kater`, `story-stash` (`scenes: { … }`)

Regel wie Task 6. Funktions-Szenen (`(ctx) => { … }`) enthalten ihre Panels als Objektliterale im `return`/`push` – dort ergänzen. Fundstelle `grep -n "'<id>':"`.

- [ ] **Step 1: Story 1 „Die Schuld"**

| Szene | Panel | ergänzen |
|---|---|---|
| `schuld.intro` | 1 „Beton. Kalt." | `cast: ['du'], pose: 'down', cam: 'close'` |
| `schuld.intro` | 2 „Gestern Nacht" | `pose: 'point'` |
| `schuld.intro` | 3 „Dreißig Tage." | `cam: 'close'` |
| `schuld.intro` | 4 „Hier. Fünfzig Euro" | `pose: 'point'` |
| `schuld.k4` | 1 „Letzte Woche." | `cam: 'close'` |
| `schuld.fluchtFrage` | 1 „Heute Nacht?" | `cam: 'close'` |
| `schuld.croup.safe2` | 1 „Neben dem Geld: Fotos." | `cast: ['du'], cam: 'close'` |
| `schuld.sturzFrage` | 1 „Du hast das Buch." | `enter: 'igor'` |
| `schuld.duelWon` | 1 | `cam: 'close'` |
| `schuld.duelLost` | 1 | `look: { du: { hurt: 'pflaster' } }` |
| `schuld.ende.ehrlich` | 1 „Fünfzigtausend." | `cam: 'close'` |
| `schuld.ende.ehrlich` | 3 „Verschwinde" | `pose: 'point'` |
| `schuld.ende.doc` | 2 „Zwei Nieren, ein Hobby." | `pose: { who: 'du', pose: 'down' }` |
| `schuld.ende.doc` | 3 „Er wacht wieder auf." | `cam: 'close'` |
| `schuld.ende.sturz` | 1 „Tag der Abrechnung." | `cast: ['du', 'vito', 'igor']` |
| `schuld.ende.sturz` | 2 „Nein. Heute nicht." | `pose: 'point'` |
| `schuld.ende.sturz` | 3 „Du… weißt nicht" | `cam: 'close'` |
| `schuld.ende.sturz` | 4 „Vito ist durch die Hintertür." | `pose: 'hands-up'` |
| `schuld.ende.taxi` (Funktion) | erstes Panel `panels = [ { … kevin … 'Vier Uhr.' } ]` | `cam: 'close'` |
| `schuld.ende.taxi` (Funktion) | letztes `panels.push({ … 'Die Fähre legt ab.' })` | `cast: ['du']` |

- [ ] **Step 2: Story 2 „Der Kater"**

| Szene | Panel | ergänzen |
|---|---|---|
| `kater.intro` (Funktion) | im `start.concat([ … ])`: 1 „Ja. Natürlich ja." | `cam: 'close'` |
| `kater.intro` (Funktion) | im `concat`: 3 „Villa mit Hafenblick" | `cast: ['du'], pose: 'hands-up'` |
| `kater.absturz` | 1 „Der Wecker ist weg." | `cast: ['du'], cam: 'close'` |
| `kater.absturz` | 2 „Ihre Frau hat die Vollmacht" | `pose: 'point'` |
| `kater.k2` | 1 „Tag vier." | `cast: ['du']` |
| `kater.doc.angebot` | 2 „Dreihundert das Stück" | `pose: 'point'` |
| `kater.chantal` | 1 „Sie steht vor dem Keller." | `cast: ['du']` |
| `kater.chantal` | 2 „Lass mich rein." | `cam: 'close'` |
| `kater.sylvie` | 1 | `cam: 'close'` |
| `kater.ende.bett` | 1 „Zähl rückwärts" | `pose: { who: 'du', pose: 'down' }` |
| `kater.ende.bett` | 2 „Der Wirt bringt Blumen." | `cast: ['wirt'], cam: 'wide'` |
| `kater.ende.wirt` (Funktion) | erstes Panel „Der Schlüssel." | `pose: 'hands-up'` |
| `kater.ende.wirt` (Funktion) | letztes `panels.push({ … 'Der Ort, an dem ich alles verloren habe.' })` | `cam: 'close'` |
| `kater.ende.nuechtern` | 2 „Kein Keller, kein Bier" | `cast: ['du'], walk: { who: 'du', to: 'mid' }` |
| `kater.ende.brownie` | 1 „Partner." | `pose: 'point'` |
| `kater.ende.taxi` | 1 „Vier Uhr. Das Taxi wartet." | `cam: 'close'` |
| `kater.ende.taxi` | 2 „Die Fähre legt ab." | `cast: ['du']` |
| `kater.ende.stammgast` | 2 „Das erste Bier geht aufs Haus." | `cam: 'close'` |

- [ ] **Step 3: Story 3 „Die Wäsche"**

| Szene | Panel | ergänzen |
|---|---|---|
| `stash.intro` (Funktion) | im gemeinsamen `return [ … ]`: 1 „Jeden Montag" | `pose: 'point'` |
| `stash.intro` (Funktion) | im `return`: 3 „Dreimal enttäuschst du mich" | `cam: 'close', pause: 500` |
| `stash.tisch` | 2 „…" (stumme) | `pause: 800` |
| `stash.tisch` | 3 „Der Croupier sagt nichts." | `pose: { who: 'stumme', pose: 'point' }` |
| `stash.hinterhalt` (Funktion) | 1 „Heimweg." | `cast: ['du'], cam: 'close'` |
| `stash.hinterhalt` (Funktion) | 2 „Keiner sagt was." | `cam: 'shake'` |
| `stash.tutorial` | 2 „Hier. Meine Pistole" | `pose: 'point'` |
| `stash.angebot` | 1 „Kessler wartet" | `cast: ['du']` |
| `stash.angebot` | 3 „Keine Überfälle mehr" | `cam: 'close'` |
| `stash.razzia` | 1 „Drei Belege." | `cam: 'close'` |
| `stash.finale` (Funktion) | 1 „Anabi sitzt am Tisch" | `cast: ['du', 'anabi'], pause: 600` |
| `stash.flucht` | 1 „Der Wagen ist vollgetankt." | `cast: ['du']` |
| `stash.ende.kanal` | 1 „Dreimal." | `pose: 'point', enter: 'igor'` |
| `stash.ende.kanal` | 2 „Er fährt langsam." | `cast: ['igor', 'anabi', 'du']` |
| `stash.ende.kanal` | 3 „Der Keller bekommt einen neuen Strohmann." | `cast: []` |
| `stash.ende.krieg` | 1 „Anabi liegt neben seinem Tisch." | `cast: ['du', 'anabi'], pose: { who: 'anabi', pose: 'down' }, sfx: 'gunshot', cam: 'shake'` |
| `stash.ende.krieg` | 2 „Schnellste Hand der Stadt." | `pose: 'point'` |
| `stash.ende.kommissar` (Funktion) | 1 „Blaulicht die Treppe runter." | `cast: ['du', 'anabi', 'brandt'], pose: { who: 'anabi', pose: 'hands-up' }` |
| `stash.ende.kommissar` (Funktion) | 3 „Der Keller ist Beweismittel." | `pose: 'point'` |
| `stash.ende.abloese` | 3 „Der Keller gehört dir." | `cam: 'close'` |
| `stash.ende.flucht` | 1 „Nachts über die Grenze." | `cast: ['du']` |
| `stash.ende.flucht` | 2 „Neuer Name, altes Spiel." | `walk: { who: 'du', to: 'mid' }` |
| `stash.ende.strohmann` | 2 „Dein Name steht im Grundbuch." | `cam: 'close'` |

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs && tests/dom-selftest.sh`
Expected: grün – der Node-Test `Regie: alle Story-Szenen …` meldet jeden Tippfehler mit Szene und Panel-Index.

Run: `python3 tests/playtest-story.py 2>&1 | grep -E "FEHLGESCHLAGEN|ERRORS"`
Expected: wie nach Task 4.

- [ ] **Step 5: Sichtprüfung**

`?fresh&story=schuld` (Intro: du liegst am Boden, Kamera nah), `?fresh&story=stash&day=30` bis zu einem Ende, `?screen=hub&fresh&scene=kater.ende.bett` (Erzähler-Blase, nur der Wirt auf der Bühne).

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(story): Hand-Regie für Eröffnungen, Enden und Wendepunkte von Schuld, Kater und Wäsche

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Performance-Nachweis, Doku, Abschluss

**Files:**
- Modify: `README.md` – Abschnitt zur Cutscene-Bühne (Regie-Schlüssel), Tests-Abschnitt (neue Tests, Trace-Referenz)
- Modify: `docs/superpowers/specs/2026-09-20-cutscene-buehne-design.md` – Abweichungs-Notiz
- Modify: `tests/perf-trace.py` – Szenario-Liste (eine Zeile)

- [ ] **Step 1: Trace-Szenario ergänzen**

In `tests/perf-trace.py` in der Szenario-Liste hinter `("Cutscene idle", "?screen=hub&scene=intro", 4, None, None),` eine Zeile ergänzen, die eine Szene mit Auftritt, Kamera und Schreibmaschine misst:

```python
    ("Cutscene Regie", "?screen=hub&scene=mug.intro", 4, None, None),
```

- [ ] **Step 2: Messen**

Run (auf dem Feature-Branch): `python3 tests/perf-trace.py --mobile "Cutscene"` und `python3 tests/perf-trace.py "Cutscene"`.
Zum Vergleich dieselben Befehle einmal auf `main` (`git stash` ist nicht nötig: `git worktree add /tmp/k37main main` und dort ausführen, danach `git worktree remove /tmp/k37main`).
Expected: Unter „meistgemalte Elemente" erscheinen **keine** `.cs-fig`/`.cs-body`/`.part`-Knoten und keine `.cs-set`-Knoten – nur `.cs-bubble`/`.cs-text` (Schreibmaschine). Raster-ms pro Sekunde im Bereich von `main` (Prototyp mobil: 3,3 ms vs. 2,6 ms bei gleichem Text-Tippen; Layouts nur durch die Schreibmaschine). Tauchen Figuren- oder Kulissenteile als meistgemalte Elemente auf, ist eine Animation auf einen SVG-Kindknoten geraten – die betroffene Regel auf das `.part`-/HTML-Element heben.

- [ ] **Step 3: README**

Im Abschnitt „Was drin ist" (oder dem Absatz über Cutscenes/Story) einen Absatz „Cutscene-Bühne" ergänzen:

```markdown
### Cutscene-Bühne

Cutscenes spielen auf einer Bühne aus Ebenen (Himmel, Kulisse, Boden, Figuren, Vordergrund): Comic-Figuren als Inline-SVG (20 Figuren, Protagonist mit Schuhen, Anzug in Story 3, roten Wangen nach Bier, blauem Auge, Augenringen bei Mafia-Schulden), 16 Kulissen mit einem lebenden Element (Neon, Regen, vorbeifahrendes Auto, Zug …), eine Sprechblase am Kopf des Sprechers. Die Auto-Regie (`CsDirector.stagePlan`) inszeniert jedes Panel aus `who/mood/bg`: du links, Gegenüber rechts, Sprecher tritt auf, Stimmung bestimmt Pose (`angry` zeigt, `shock` zuckt, `dead` kippt). Optionale Regie-Schlüssel pro Panel: `cast` (Besetzung, `[]` = Erzähler), `enter`/`exit`, `walk: { who, to: left|mid|right|far }`, `pose` (`idle, talk, point, arms-crossed, hands-up, walk, down, flinch`), `cam` (`close|wide|shake`), `shout: 'PÄNG!'`, `pause` (ms), `sfx`, `look: { du: { hurt: 'pflaster'|'kruecke' } }`. Unbekannte Schlüssel sind Testfehler. `Cutscene.instant = true` (Tests/Dev) und `prefers-reduced-motion` schalten Laufwege und Tippen ab.
```

Im Tests-Abschnitt ergänzen: Node-Tests für `stagePlan`/`validatePanels`/`figureHtml`/`duParts`/`CsSets`, DOM-Tests „Cutscene-Bühne", „cs-Keyframes nur transform/opacity", „Regie: alle Keller-Szenen", Node-Test „Regie: alle Story-Szenen"; Trace-Szenario „Cutscene Regie" mit den in Step 2 gemessenen Werten (vorher/nachher, Desktop und mobil).

- [ ] **Step 4: Spec-Notiz**

In `docs/superpowers/specs/2026-09-20-cutscene-buehne-design.md` unter „2. Figuren › Rig" einen Absatz anfügen:

```markdown
**Umsetzungsnotiz (Plan):** Eine Figur ist kein einzelnes SVG, sondern acht gestapelte `<svg class="part …">` (Beine ×2, Rumpf, Arme ×2, Kopf, Augen, Mund) mit derselben viewBox in `.cs-fig-inner > .cs-body`. Grund: CSS-Transforms auf SVG-Kindknoten werden nicht vom Compositor übernommen und malen die ganze Figur pro Frame neu; auf HTML-Elementen laufen Posen, Blinzeln und Mundbewegung als Compositor-Animationen. Die Anker gelten unverändert, als Prozent der Figur: Schultern (21 %|79 %, 45,6 %), Hüften (38 %|61 %, 65,6 %), Hals (50 %, 34,4 %), Standlinie (50 %, 95,6 %). Der Effekt `muzzle` wird nicht in Stufe 1 vordefiniert, sondern kommt mit der Schießerei (Stufe 2) – kein toter Code.
```

- [ ] **Step 5: Abschluss-Checks**

```bash
grep -n "cs-portrait\|cs-box\|Cutscene.PROPS\|figureSvg" keller37.html tests/*.py tests/*.mjs   # muss leer sein
node tests/run-selftest.mjs && tests/dom-selftest.sh
python3 tests/playtest-story.py 2>&1 | grep -E "FEHLGESCHLAGEN|ERRORS"
```

Expected: grep leer; Node/DOM grün; Playtest `ERRORS 0`, nur ggf. Pixel-Diff-Zeilen wie auf `main`.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/superpowers/specs/2026-09-20-cutscene-buehne-design.md tests/perf-trace.py
git commit -m "docs(cutscene): Bühne, Regie-Schlüssel und Trace-Referenz dokumentiert; Trace-Szenario Cutscene Regie

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

Danach: Branch nicht mergen, nicht pushen – Freigabe des Auftraggebers einholen (siehe Global Constraints).
