# Schießerei & Pfandleihe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das Reaktionsduell „Zieh!" als eigenes Minispiel, die Waffe als kaufbare Gear-Stufe in der Pfandleihe Kowalski, die Story-Anbindung (`Story.forceFight`, Hook `fight:after`) und die Kurier-Variante des Taxi-Jobs.

**Architecture:** Neuer DOM-freier Block `gang-rules` (`GangRules`: Waffen, Gegner, Rundenlogik, Kurier-Lohn – Story-Wochenlogik kommt in Plan 4 in denselben Block). Neuer Screen-Block `game-shootout` (Screen-ID `shootout`) nach dem Muster der Job-Minispiele (Generation `gen`, `alive(gen)`, Tastatur + Tippen). `Story.forceFight(cfg)` zeigt den Screen, wartet auf „Weiter", setzt Ergebnis-Flags und läuft den Hook `fight:after` (Engine 3 hat den Aufruf über `out.force === 'shootout'` vorbereitet). Die Pfandleihe ist ein Schaufenster in `Stadt`, das nur erscheint, wenn `Story.s.enabled.pfandleihe` gesetzt ist.

**Tech Stack:** Vanilla JS in `keller37.html`, Node-Selftest, DOM-Selftest, Screenshots.

**Spec:** `docs/superpowers/specs/2026-09-18-story-stash-design.md` Abschnitt 6 (Waffe, Schießerei), Abschnitt 9 (Kurierfahrt), Abschnitt 10 (Engine: Gear, Job-Variante, `fight:after`).

## Global Constraints

- Eine Datei `keller37.html`; neue Blöcke `<script id="gang-rules">` (direkt nach `baccarat-rules`, DOM-frei, in `tests/run-selftest.mjs` nach `'baccarat-rules'` laden) und `<script id="game-shootout">` (direkt nach `job-taxi`).
- Waffen exakt: Stufe 1 „Gebrauchte Makarov" 15.000 € Bonus 100 ms; Stufe 2 „Glock 17" 35.000 € Bonus 200 ms; Stufe 3 „Die Goldene" (Desert Eagle) 75.000 € Bonus 300 ms + Hinterhalt-Chance halbiert. Nur Aufstieg, kein Verkauf.
- Gegner exakt (Basis ± Streuung, ms): Läufer 380 ± 60, Junge 320 ± 60, Kessler 260 ± 40, Igor 280 ± 40, Anabi 220 ± 30. Wartezeit vor „ZIEH!" 1,5–4 s zufällig. Tippen vor dem Blitz = Fehlschuss = Runde verloren. Eine verlorene Runde = Kampf verloren.
- Kurierfahrt: 0 Strafzettel 3.000 €, 1 Strafzettel 1.500 €, ≥ 2 Strafzettel Kontrolle (0 €, Flag `kontrolle` für den `job:after`-Hook).
- Voraussetzung: Plan „Story-Engine 3" ist umgesetzt (`State.fresh().weapon`, `Story.jobStart.variant`, `Jobs.collect(id, flags)`, `Taxi.jobId`, Hook `fight:after`, Figuren `kessler`/`kowalski`, Hintergrund `pfandleihe`).
- Nach jeder Task Node- und DOM-Selftest grün; Commit-Trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## Dateistruktur

| Ort | Inhalt |
|---|---|
| `<script id="gang-rules">` | `GangRules.WEAPONS`, `FOES`, `weapon(s)`, `canBuyWeapon`, `DRAW_WAIT`, `drawWait`, `duelRound`, `kurierPay` |
| `<template id="tpl-shootout">` + CSS `.duel-*` | Bühne: zwei Silhouetten, Signal, Status, Buttons |
| `<script id="game-shootout">` | `Shootout`, `UI.register('shootout', …)` |
| `story-engine` | `Story.forceFight(cfg)`; Dev-Param `weapon` |
| `ui` | `UI.show`-Guard während eines erzwungenen Duells; Escape-Guard |
| `title` | `Title.open`-Guard |
| `room-stadt` | Schaufenster `pfandleihe`, `buyWeapon`, `line()` mit Waffe; Szene `stadt.waffe` |
| `jobs` | `Jobs.POOL.kurierfahrt` |
| `job-taxi` | Variante `kurier` (Skin, Zähler, Lohn, Kontrolle) |
| `selftest` | Tests |
| `tests/run-selftest.mjs` | Block laden |

---

### Task 1: `GangRules` – Waffen, Gegner, Rundenlogik, Kurier-Lohn

**Files:**
- Create: Block `<script id="gang-rules">` nach `baccarat-rules`
- Modify: `tests/run-selftest.mjs`
- Test: Block `selftest` (neuer Abschnitt `/* ---- Gang: Waffen, Duell, Kurier ---- */` nach den Baccarat-Tests)

**Interfaces:**
- Produces: `GangRules.WEAPONS[tier]` `{ tier, name, icon, price, bonus, ambushMult?, desc }`; `GangRules.FOES[id]` `{ name, emoji, base, spread }` für `laeufer|junge|kessler|igor|anabi`; `weapon(s)` → Waffe der Stufe `s.weapon || 0`; `canBuyWeapon(s, tier)` → `{ ok: true }` | `{ ok: false, reason: 'unknown'|'owned'|'downgrade'|'funds' }`; `drawWait(rng)` → ms in [1500, 4000]; `duelRound({ reaction, bonus, foe, rng })` → `{ won, misfire, foeTime, you }` (`reaction == null` = Fehlschuss; `you = max(0, reaction − bonus)`; `foeTime = round(base + (rng()·2 − 1)·spread)`; ein rng-Aufruf); `kurierPay(tickets)` → `{ pay, kontrolle }`.

- [ ] **Step 1: Failing Tests**

```js
/* ---- Gang: Waffen, Duell, Kurier ---- */
T.test('GangRules.WEAPONS: vier Stufen, Preise und Boni laut Spec, Goldene halbiert Hinterhalte', () => {
  const W = GangRules.WEAPONS;
  T.eq(W.map((w) => [w.tier, w.price, w.bonus]), [[0, 0, 0], [1, 15000, 100], [2, 35000, 200], [3, 75000, 300]]);
  T.eq(W[3].ambushMult, 0.5); T.eq(W[1].ambushMult, undefined);
  T.eq(GangRules.weapon(base()).tier, 0); T.eq(GangRules.weapon(base({ weapon: 2 })).name, 'Glock 17');
});
T.test('GangRules.canBuyWeapon: nur Aufstieg, Sprung erlaubt, Geld nötig', () => {
  T.eq(GangRules.canBuyWeapon(base({ balance: 15000 }), 1), { ok: true });
  T.eq(GangRules.canBuyWeapon(base({ balance: 14999 }), 1), { ok: false, reason: 'funds' });
  T.eq(GangRules.canBuyWeapon(base({ balance: 80000, weapon: 0 }), 3), { ok: true }, 'Sprung auf 3');
  T.eq(GangRules.canBuyWeapon(base({ balance: 80000, weapon: 2 }), 2), { ok: false, reason: 'owned' });
  T.eq(GangRules.canBuyWeapon(base({ balance: 80000, weapon: 2 }), 1), { ok: false, reason: 'downgrade' });
  T.eq(GangRules.canBuyWeapon(base({ balance: 80000 }), 0), { ok: false, reason: 'unknown' });
  T.eq(GangRules.canBuyWeapon(base({ balance: 80000 }), 7), { ok: false, reason: 'unknown' });
});
T.test('GangRules.FOES und drawWait', () => {
  const F = GangRules.FOES;
  T.eq([F.laeufer, F.junge, F.kessler, F.igor, F.anabi].map((f) => [f.base, f.spread]), [[380, 60], [320, 60], [260, 40], [280, 40], [220, 30]]);
  T.eq(GangRules.drawWait(seq(0)), 1500); T.eq(GangRules.drawWait(seq(1)), 4000); T.eq(GangRules.drawWait(seq(0.5)), 2750);
});
T.test('GangRules.duelRound: Fehlschuss verliert, Bonus zieht ab, Streuung ±spread, ein rng-Aufruf', () => {
  const foe = GangRules.FOES.junge;
  let calls = 0; const counting = () => { calls++; return 0.5; };
  T.eq(GangRules.duelRound({ reaction: null, bonus: 300, foe, rng: counting }), { won: false, misfire: true, foeTime: 320, you: null });
  T.eq(calls, 1);
  T.eq(GangRules.duelRound({ reaction: 300, bonus: 0, foe, rng: seq(0.5) }), { won: true, misfire: false, foeTime: 320, you: 300 });
  T.eq(GangRules.duelRound({ reaction: 320, bonus: 0, foe, rng: seq(0.5) }).won, false, 'gleich schnell = verloren');
  T.eq(GangRules.duelRound({ reaction: 400, bonus: 100, foe, rng: seq(0.5) }), { won: true, misfire: false, foeTime: 320, you: 300 });
  T.eq(GangRules.duelRound({ reaction: 50, bonus: 100, foe, rng: seq(0.5) }).you, 0, 'nie negativ');
  T.eq(GangRules.duelRound({ reaction: 300, bonus: 0, foe, rng: seq(0) }).foeTime, 260, 'rng 0 → base − spread');
  T.eq(GangRules.duelRound({ reaction: 300, bonus: 0, foe, rng: seq(1) }).foeTime, 380, 'rng 1 → base + spread');
  T.eq(GangRules.duelRound({ reaction: 250, bonus: 0, foe: GangRules.FOES.anabi, rng: seq(0.5) }).won, false, 'Anabi 220');
});
T.test('GangRules.kurierPay: 0 → 3.000, 1 → 1.500, ≥ 2 → Kontrolle', () => {
  T.eq(GangRules.kurierPay(0), { pay: 3000, kontrolle: false });
  T.eq(GangRules.kurierPay(1), { pay: 1500, kontrolle: false });
  T.eq(GangRules.kurierPay(2), { pay: 0, kontrolle: true });
  T.eq(GangRules.kurierPay(5), { pay: 0, kontrolle: true });
});
```

- [ ] **Step 2: Tests laufen lassen, muss fehlschlagen**

Run: `node tests/run-selftest.mjs`
Expected: `GangRules is not defined`.

- [ ] **Step 3: Block anlegen**

```html
<script id="gang-rules">
/* ================= GANG – Waffen, Duell, Kurier (rein, kein DOM); Wochen-/Wäsche-Logik der Story 3 folgt unten ================= */
const GangRules = {
  WEAPONS: [
    { tier: 0, name: 'Keine Waffe', icon: '✋', price: 0, bonus: 0, desc: 'Nur Fäuste. Die reichen hier nicht.' },
    { tier: 1, name: 'Gebrauchte Makarov', icon: '🔫', price: 15000, bonus: 100, desc: 'Ostblock, Seriennummer weggefeilt. Geht meistens los.' },
    { tier: 2, name: 'Glock 17', icon: '🔫', price: 35000, bonus: 200, desc: 'Polizeiausführung. Frag nicht, welcher Polizist.' },
    { tier: 3, name: '„Die Goldene“', icon: '✨', price: 75000, bonus: 300, ambushMult: 0.5, desc: 'Desert Eagle, vergoldet. Die Bahnhof-Jungs kennen das Ding – und gehen lieber woanders hin.' },
  ],
  FOES: {
    laeufer: { name: 'Bahnhof-Läufer', emoji: '🏃', base: 380, spread: 60 },
    junge: { name: 'Bahnhof-Junge', emoji: '🧢', base: 320, spread: 60 },
    kessler: { name: 'Kessler', emoji: '🚬', base: 260, spread: 40 },
    igor: { name: 'Igor', emoji: '🐻', base: 280, spread: 40 },
    anabi: { name: 'Anabi Stash', emoji: '🕶️', base: 220, spread: 30 },
  },
  weapon(s) { const W = GangRules.WEAPONS; return W[Math.min(W.length - 1, Math.max(0, s.weapon || 0))]; },
  canBuyWeapon(s, tier) {
    const w = GangRules.WEAPONS[tier];
    if (!w || tier === 0) return { ok: false, reason: 'unknown' };
    const cur = s.weapon || 0;
    if (cur === tier) return { ok: false, reason: 'owned' };
    if (cur > tier) return { ok: false, reason: 'downgrade' };
    if (s.balance < w.price) return { ok: false, reason: 'funds' };
    return { ok: true };
  },
  DRAW_WAIT: [1500, 4000],
  drawWait(rng) { const [a, b] = GangRules.DRAW_WAIT; return Math.round(a + rng() * (b - a)); },
  /* reaction: ms nach dem Blitz, null = vor dem Blitz getippt (Fehlschuss). Gegnerzeit streut gleichverteilt ±spread. */
  duelRound({ reaction, bonus = 0, foe, rng }) {
    const foeTime = Math.round(foe.base + (rng() * 2 - 1) * foe.spread);
    if (reaction == null) return { won: false, misfire: true, foeTime, you: null };
    const you = Math.max(0, reaction - bonus);
    return { won: you < foeTime, misfire: false, foeTime, you };
  },
  /* Kurierfahrt: Lohn nach Strafzetteln; ab zwei guckt die Polizei in den Kofferraum */
  kurierPay(tickets) {
    if (tickets >= 2) return { pay: 0, kontrolle: true };
    return { pay: tickets === 0 ? 3000 : 1500, kontrolle: false };
  },
};
</script>
```

`tests/run-selftest.mjs`: `'baccarat-rules'` → `'baccarat-rules', 'gang-rules'`.

- [ ] **Step 4: Tests**

Run: `node tests/run-selftest.mjs`
Expected: grün (+5).

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(gang): GangRules – Waffen, Gegner, Duell-Runde, Kurier-Lohn"
```

---

### Task 2: Screen `shootout` – Template, CSS, `Shootout`

**Files:**
- Modify: `keller37.html` – `<template id="tpl-shootout">` direkt nach `tpl-job-taxi`; CSS hinter `.ticket-pop { … }`; Block `<script id="game-shootout">` nach `job-taxi`
- Test: DOM-Selftest

**Interfaces:**
- Produces: `Shootout.start({ kind, foes: [foeIds], bonus, forced })`, `ready()` (Runde scharf machen), `tap()`, `finish(won)`, Felder `running`, `phase: 'idle'|'wait'|'draw'|'result'|'done'`, `signalAt`, `forced`, `pending` (Konfiguration, die `mount` sofort startet), Events `Bus.emit('fight:done', { kind, won, rounds })` beim Ende und `Bus.emit('fight:leave', { kind, won })` beim Klick auf „Weiter". `UI.register('shootout', …)`; Dev: `?screen=shootout&foe=anabi` startet einen Kampf gegen diesen Gegner mit `?weapon=N` als Bonus-Quelle.

- [ ] **Step 1: Template**

```html
<template id="tpl-shootout">
  <div class="panel duel-panel">
    <div class="duel-stage" id="duelStage">
      <div class="duel-moon">🌙</div>
      <div class="duel-fighter you" id="duelYou">🤠</div>
      <div class="duel-signal" id="duelSignal">…</div>
      <div class="duel-fighter foe" id="duelFoe">🧢</div>
      <div class="duel-name" id="duelFoeName"></div>
      <div class="duel-count" id="duelCount"></div>
    </div>
    <div class="status" id="duelStatus">Warte auf ZIEH! – dann tippen oder Leertaste. Zu früh ist ein Fehlschuss.</div>
    <div class="bet-bar">
      <button class="btn solid" id="btnDuelStart">Bereit</button>
      <button class="btn ghost hidden" id="btnDuelDone">Weiter</button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: CSS**

```css
.duel-panel { align-items: stretch; }
.duel-stage { position: relative; height: 300px; border-radius: 10px; background: linear-gradient(180deg, #05070d 0%, #141a28 55%, #2a2820 100%); overflow: hidden; touch-action: none; user-select: none; cursor: crosshair; }
.duel-stage::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 70px; background: #1a1812; border-top: 2px dashed rgba(255,255,255,.15); }
.duel-moon { position: absolute; right: 8%; top: 8%; font-size: 2rem; opacity: .7; }
.duel-fighter { position: absolute; bottom: 58px; font-size: 4rem; z-index: 2; filter: drop-shadow(0 0 10px rgba(0,0,0,.8)); transition: transform .3s; }
.duel-fighter.you { left: 14%; }
.duel-fighter.foe { right: 14%; transform: scaleX(-1); }
.duel-fighter.down { transform: rotate(80deg) translateY(30px); opacity: .6; }
.duel-fighter.foe.down { transform: scaleX(-1) rotate(80deg) translateY(30px); }
.duel-fighter.hit { animation: shake .4s; }
.duel-signal { position: absolute; left: 50%; top: 34%; transform: translate(-50%, -50%); font-family: var(--font-display); font-size: 1.6rem; letter-spacing: .2em; color: rgba(255,255,255,.5); z-index: 3; }
.duel-signal.wait { color: rgba(255,255,255,.35); }
.duel-signal.draw { font-size: 3.4rem; color: #fff; text-shadow: 0 0 20px var(--neon-red), 0 0 40px var(--neon-red); animation: stampIn .15s both; }
.duel-name { position: absolute; right: 10%; top: 12%; font-family: var(--font-mono); font-size: .8rem; color: rgba(255,255,255,.7); }
.duel-count { position: absolute; left: 10%; top: 12%; font-family: var(--font-mono); font-size: .8rem; color: rgba(255,255,255,.7); }
@media (max-width: 760px) { .duel-stage { height: 240px; } .duel-fighter { font-size: 3rem; } }
```

- [ ] **Step 3: Screen-Block**

```html
<script id="game-shootout">
/* ================= SCHIESSEREI „ZIEH!“ – Reaktionsduell, ein Gegner nach dem anderen ================= */
const Shootout = {
  root: null, gen: 0, running: false, forced: false, pending: null, cfg: null, foes: [], idx: 0, phase: 'idle', signalAt: 0, timer: null, nextTimer: null, results: [],
  alive(gen) { return !!this.root && this.gen === gen; },
  /* cfg: { kind, foes: ['junge', …], bonus (ms), forced } */
  start(cfg) {
    if (!this.root || this.running) return;
    this.cfg = cfg; this.foes = cfg.foes.map((id) => GangRules.FOES[id]).filter(Boolean); this.idx = 0; this.results = [];
    this.running = true; this.forced = !!cfg.forced; this.phase = 'idle';
    qs('#btnDuelStart', this.root).classList.remove('hidden'); qs('#btnDuelDone', this.root).classList.add('hidden');
    qs('#btnDuelStart', this.root).textContent = 'Bereit';
    qs('#duelStatus', this.root).textContent = `${this.foes.length} Gegner. ${cfg.bonus ? `Waffe: ${cfg.bonus} ms Vorsprung.` : 'Ohne Vorsprung.'} „Bereit“ – dann warten, bis ZIEH! aufblitzt.`;
    this.renderFoe();
  },
  renderFoe() {
    if (!this.root) return;
    const foe = this.foes[this.idx];
    qs('#duelFoe', this.root).textContent = foe ? foe.emoji : ''; qs('#duelFoe', this.root).className = 'duel-fighter foe';
    qs('#duelYou', this.root).className = 'duel-fighter you';
    qs('#duelFoeName', this.root).textContent = foe ? foe.name : '';
    qs('#duelCount', this.root).textContent = `${Math.min(this.idx + 1, this.foes.length)} / ${this.foes.length}`;
    const sig = qs('#duelSignal', this.root); sig.textContent = '…'; sig.className = 'duel-signal';
  },
  ready() {
    if (!this.running || this.phase !== 'idle' || !this.root) return;
    const gen = this.gen;
    this.phase = 'wait';
    qs('#btnDuelStart', this.root).classList.add('hidden');
    const sig = qs('#duelSignal', this.root); sig.textContent = 'Warte…'; sig.className = 'duel-signal wait';
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.timer = setTimeout(() => {
      if (!this.alive(gen) || this.phase !== 'wait') return;
      this.phase = 'draw'; this.signalAt = performance.now();
      sig.textContent = 'ZIEH!'; sig.className = 'duel-signal draw';
      SFX.play('reelStop');
    }, reduced ? 800 : GangRules.drawWait(Math.random));
  },
  tap() {
    if (!this.running) return;
    if (this.phase === 'wait') { clearTimeout(this.timer); this.resolve(null); }
    else if (this.phase === 'draw') this.resolve(Math.round(performance.now() - this.signalAt));
  },
  resolve(reaction) {
    const gen = this.gen;
    this.phase = 'result';
    const foe = this.foes[this.idx];
    const r = GangRules.duelRound({ reaction, bonus: this.cfg.bonus || 0, foe, rng: Math.random });
    this.results.push(r);
    if (this.root) {
      qs(r.won ? '#duelFoe' : '#duelYou', this.root).classList.add(r.won ? 'down' : 'hit');
      qs('#duelStatus', this.root).innerHTML = r.misfire ? `<span class="loss">Zu früh! Der Schuss geht in den Asphalt. ${foe.name} nicht.</span>`
        : r.won ? `<span class="win">${foe.name}: ${r.foeTime} ms. Du: ${r.you} ms. Er liegt.</span>` : `<span class="loss">${foe.name}: ${r.foeTime} ms. Du: ${r.you} ms. Zu langsam.</span>`;
    }
    SFX.play(r.won ? 'cash' : 'lose');
    if (!r.won) return this.finish(false);
    this.idx++;
    if (this.idx >= this.foes.length) return this.finish(true);
    this.nextTimer = setTimeout(() => { if (!this.alive(gen)) return; this.phase = 'idle'; this.renderFoe(); const b = qs('#btnDuelStart', this.root); b.textContent = 'Nächster'; b.classList.remove('hidden'); }, 900);
  },
  finish(won) {
    this.running = false; this.phase = 'done';
    if (this.root) {
      qs('#btnDuelStart', this.root).classList.add('hidden'); qs('#btnDuelDone', this.root).classList.remove('hidden');
      const line = won ? 'Alle liegen. Du gehst.' : 'Du liegst. Sie gehen.';
      qs('#duelStatus', this.root).innerHTML += ` <b>${line}</b>`;
    }
    Bus.emit('fight:done', { kind: this.cfg.kind, won, rounds: this.results });
  },
  async leave() {
    if (this.running) return;
    const kind = this.cfg ? this.cfg.kind : null, won = this.results.length > 0 && this.results.every((r) => r.won) && this.idx >= this.foes.length;
    const forced = this.forced; this.forced = false;
    await Bus.emit('fight:leave', { kind, won });
    if (!forced) await UI.show('hub'); // Story/Dev: die Story entscheidet, wohin es geht (Nacht läuft weiter, Ende, …)
  },
  onKey(e) {
    if (!qs('#cutscene').hidden || e.repeat) return;
    if (e.code === 'Space') { e.preventDefault(); if (Shootout.phase === 'idle') Shootout.ready(); else Shootout.tap(); }
  },
};
UI.register('shootout', {
  template: 'tpl-shootout',
  mount(root) {
    Shootout.gen++; Shootout.root = root; Shootout.running = false; Shootout.phase = 'idle';
    qs('#btnDuelStart', root).addEventListener('click', () => { SFX.play('click'); Shootout.ready(); });
    qs('#btnDuelDone', root).addEventListener('click', (e) => { e.currentTarget.disabled = true; SFX.play('click'); Shootout.leave(); });
    qs('#duelStage', root).addEventListener('pointerdown', () => Shootout.tap());
    document.addEventListener('keydown', Shootout.onKey);
    if (Shootout.pending) { const c = Shootout.pending; Shootout.pending = null; Shootout.start(c); return; }
    const params = new URLSearchParams(location.search);
    const foe = params.get('foe');
    if (foe && GangRules.FOES[foe]) {
      if (params.has('weapon')) State.s.weapon = Math.max(0, Math.min(3, parseInt(params.get('weapon'), 10) || 0));
      Shootout.start({ kind: 'dev', foes: [foe], bonus: GangRules.weapon(State.s).bonus });
    } else {
      qs('#duelStatus', root).textContent = 'Kein Gegner. (Dev: ?screen=shootout&foe=junge)';
      qs('#btnDuelStart', root).classList.add('hidden');
    }
  },
  unmount() {
    document.removeEventListener('keydown', Shootout.onKey);
    clearTimeout(Shootout.timer); clearTimeout(Shootout.nextTimer);
    const wasRunning = Shootout.running;
    Shootout.gen++; Shootout.root = null; Shootout.running = false; Shootout.phase = 'idle';
    /* Screen mitten im Kampf verlassen (Brand-Knopf, Reload-Schutz greift nicht): zählt als verloren, damit ein wartendes forceFight nicht hängt */
    if (wasRunning) { const kind = Shootout.cfg ? Shootout.cfg.kind : null; Shootout.forced = false; Bus.emit('fight:done', { kind, won: false, rounds: Shootout.results, aborted: true }); Bus.emit('fight:leave', { kind, won: false, aborted: true }); }
  },
});
</script>
```

- [ ] **Step 4: DOM-Tests** (im Bereich `if (typeof Story !== 'undefined' && typeof document !== 'undefined') { … }`)

```js
  T.test('Shootout: Fehlschuss vor dem Blitz verliert, Treffer nach dem Blitz gewinnt, fight:done/leave', async () => {
    const keep = { cur: UI.current, wait: GangRules.drawWait, s: State.s, mode: State.mode, save: State.save };
    State.save = () => {}; State.mode = 'free'; State.s = State.fresh();
    const events = [];
    const off1 = Bus.on('fight:done', (e) => events.push(['done', e.kind, e.won]));
    const off2 = Bus.on('fight:leave', (e) => events.push(['leave', e.kind, e.won]));
    try {
      GangRules.drawWait = () => 30;
      await UI.show('shootout');
      Shootout.start({ kind: 't1', foes: ['laeufer', 'laeufer'], bonus: 0 });
      T.eq([Shootout.running, Shootout.phase, qs('#duelCount').textContent], [true, 'idle', '1 / 2']);
      Shootout.ready(); T.eq(Shootout.phase, 'wait');
      Shootout.tap(); // zu früh
      T.eq([Shootout.running, Shootout.phase, Shootout.results[0].misfire], [false, 'done', true]);
      T.eq(events, [['done', 't1', false]]);
      await Shootout.leave();
      T.eq(events[1], ['leave', 't1', false]); T.eq(UI.current.id, 'hub', 'nicht erzwungen: zurück in den Gang');
      events.length = 0;
      await UI.show('shootout');
      Shootout.start({ kind: 't2', foes: ['laeufer'], bonus: 300, forced: true });
      Shootout.ready();
      await wait(120); // Blitz nach 30 ms (gestubbt)
      T.eq(Shootout.phase, 'draw');
      Shootout.tap(); // ≈ 90 ms − 300 Bonus → 0 < Läufer (≥ 320)
      T.eq([Shootout.running, Shootout.results[0].won], [false, true]);
      T.eq(events, [['done', 't2', true]]);
      await Shootout.leave();
      T.eq(events[1], ['leave', 't2', true]); T.eq(UI.current.id, 'shootout', 'erzwungen: Screen bleibt, die Story navigiert');
    } finally {
      off1(); off2(); GangRules.drawWait = keep.wait; State.save = keep.save; State.s = keep.s; State.mode = keep.mode;
      await UI.show(keep.cur ? keep.cur.id : 'hub');
    }
  });
```

`Bus.on` gibt (wie in `Story.forceDuel` benutzt) eine Abmeldefunktion zurück – prüfen im Block `bus`.

- [ ] **Step 5: Tests + Screenshot**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Run: `bash tests/screenshot.sh docs/superpowers/screenshots/shootout.png "?fresh&mode=free&screen=shootout&foe=anabi&weapon=2"`

- [ ] **Step 6: Commit**

```bash
git add keller37.html docs/superpowers/screenshots/shootout.png
git commit -m "feat(shootout): Reaktionsduell Zieh! – Screen, Runden, fight:done/leave"
```

---

### Task 3: `Story.forceFight`, Guards, Dev-Param `weapon`

**Files:**
- Modify: `story-engine` (`Story.forceFight`, `consumeDevParams`, `enter`), `ui` (`UI.show`, Escape-Handler), `title` (`Title.open`)
- Test: DOM-Selftest

**Interfaces:**
- Consumes: `Shootout.pending/start/running/forced`, Events `fight:leave`, `GangRules.weapon(s)`.
- Produces: `Story.forceFight({ kind, foes, bonus? })` → `{ kind, won }`; setzt vor dem Hook `st.flags.fightWon = won`, `st.flags.fightLost = !won`, `st.flags['fight_' + kind] = true`, läuft `runEvents('fight:after')`, löscht danach `fight_<kind>`, prüft `checkImmediate`. Bonus = `cfg.bonus` wenn gesetzt (Leihpistole), sonst Waffe des Spielers. `?weapon=N` (mit `?fresh`) setzt `State.s.weapon` beim Story-Start.

- [ ] **Step 1: Failing DOM-Test**

```js
  T.test('Story.forceFight: Screen, Ergebnis-Flags, fight:after-Events, Aufräumen', async () => {
    const keep = { s: State.s, mode: State.mode, story: Story.story, cur: UI.current, save: State.save, wait: GangRules.drawWait };
    State.save = () => {}; GangRules.drawWait = () => 30;
    const story = { id: 't.fight', title: 'T', days: 3, start: { balance: 100, vars: {}, unlocked: { jobs: [], doors: [], rooms: [] } }, chapters: [], scenes: {},
      events: [{ id: 'gewonnen', at: 'fight:after', when: { all: [{ flag: 'fight_probe' }, { flag: 'fightWon' }] }, effects: [{ var: 'ruf', add: 1 }] }],
      endings: [{ id: 'aus', title: 'Aus', scene: 'x', priority: 0, fallback: true }] };
    try {
      State.mode = 'story'; State.s = State.freshStory(story); State.s.weapon = 2; Story.story = story;
      const p = Story.forceFight({ kind: 'probe', foes: ['laeufer'] });
      await wait(400); // UI.show + mount + start
      T.eq([UI.current.id, Shootout.running, Shootout.forced, Shootout.cfg.bonus], ['shootout', true, true, 200], 'Waffe 2 → 200 ms');
      Shootout.ready(); await wait(120); Shootout.tap();
      T.eq(Shootout.running, false);
      qs('#btnDuelDone').click();
      const res = await p;
      T.eq(res.won, true);
      T.eq([State.s.story.flags.fightWon, State.s.story.flags.fightLost, State.s.story.flags.fight_probe], [true, false, undefined]);
      T.eq(State.s.story.vars.ruf, 1, 'fight:after-Event lief');
    } finally {
      GangRules.drawWait = keep.wait; State.save = keep.save; State.s = keep.s; State.mode = keep.mode; Story.story = keep.story;
      await UI.show(keep.cur ? keep.cur.id : 'hub');
    }
  });
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `bash tests/dom-selftest.sh`
Expected: `forceFight is not a function`.

- [ ] **Step 3: `Story.forceFight`** (hinter `forceDuel`)

```js
  /* ---- Erzwungene Schießerei ---- */
  async forceFight(cfg) {
    const st = this.s;
    const bonus = cfg.bonus != null ? cfg.bonus : GangRules.weapon(State.s).bonus;
    Shootout.pending = { kind: cfg.kind, foes: cfg.foes || [], bonus, forced: true };
    this.allowOnce = 'shootout';
    await UI.show('shootout');
    const res = await new Promise((resolve) => {
      const off = Bus.on('fight:leave', (r) => { off(); resolve(r); });
      if (!Shootout.running) { off(); resolve({ kind: cfg.kind, won: false, aborted: true }); } // Screen nicht bereit – nicht ewig warten
    });
    if (this.stale(st)) return res;
    st.flags.fightWon = !!res.won; st.flags.fightLost = !res.won; st.flags[`fight_${cfg.kind}`] = true;
    State.save();
    await this.runEvents('fight:after');
    if (!this.stale(st)) { delete st.flags[`fight_${cfg.kind}`]; State.save(); }
    if (this.stale(st)) return res;
    await this.checkImmediate();
    return res;
  },
```

- [ ] **Step 4: Guards**

`UI.show`, direkt nach `if (this.busy) return;`:

```js
    if (typeof Shootout !== 'undefined' && Shootout.running && Shootout.forced && id !== 'shootout') { UI.toast({ icon: '🔫', title: 'Erst das Duell beenden' }); return; }
```

Escape-Handler in `mountShell` (Zeile `if (typeof Russian !== 'undefined' && Russian.inDuel …) return;`) ergänzen um: `if (typeof Shootout !== 'undefined' && Shootout.running && Shootout.forced) return;`

`Title.open`: nach dem Russian-Guard: `if (typeof Shootout !== 'undefined' && Shootout.running && Shootout.forced) { UI.toast({ icon: '⏳', title: 'Erst das Duell beenden' }); return; }`

- [ ] **Step 5: Dev-Param `weapon`**

`Story.consumeDevParams`: `const dev = ['story', 'day', 'job', 'ending', 'fresh', 'prev', 'weapon'];`
`Story.enter` hinter der `?day`-Zeile: `if (params.has('weapon') && params.has('fresh')) State.s.weapon = Math.max(0, Math.min(3, parseInt(params.get('weapon'), 10) || 0));`

- [ ] **Step 6: Tests**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh`
Expected: grün.

- [ ] **Step 7: Commit**

```bash
git add keller37.html
git commit -m "feat(story): forceFight – erzwungene Schießerei mit Ergebnis-Flags und fight:after, Guards, ?weapon="
```

---

### Task 4: Pfandleihe Kowalski – Schaufenster, Waffenkauf, Gear-Zeile

**Files:**
- Modify: `room-stadt` (`SHOPS`, `SELLER`, `render`, `seller`, `ownedLine`, `buyWeapon`, `line`), Szene `stadt.waffe`, `ui` (Seitenleisten-Label Stadt)
- Test: DOM-Selftest

**Interfaces:**
- Consumes: `GangRules.WEAPONS/canBuyWeapon/weapon`, `Story.s.enabled.pfandleihe` (Story setzt `{ enable: ['pfandleihe'] }`).
- Produces: `Stadt.SHOPS.pfandleihe`, `Stadt.storyShop(id)` → bool (Schaufenster sichtbar), `Stadt.buyWeapon(tier)`, `Bus.emit('gear:weapon', { tier })`, Szene `stadt.waffe`.

- [ ] **Step 1: Failing DOM-Test**

```js
  T.test('Stadt: Pfandleihe nur mit Story-Freigabe, Waffenkauf setzt weapon', async () => {
    const keep = { s: State.s, mode: State.mode, story: Story.story, cur: UI.current, save: State.save, play: Cutscene.play };
    State.save = () => {}; Cutscene.play = async () => undefined;
    try {
      State.mode = 'free'; State.s = State.fresh();
      await UI.show('stadt');
      T.eq(qs('.storefront.pfandleihe', qs('#stage')), null, 'freies Spiel: kein Schaufenster');
      State.mode = 'story'; State.s = State.freshStory(STORY_PROBE); Story.story = STORY_PROBE; State.s.balance = 40000;
      State.s.story.unlocked.rooms.push('stadt'); State.s.story.enabled.pfandleihe = true;
      await UI.show('stadt');
      T.ok(qs('.storefront.pfandleihe', qs('#stage')), 'Story mit enabled: Schaufenster da');
      Stadt.open('pfandleihe');
      const cards = qsa('#laden .gear-card', qs('#stage'));
      T.eq(cards.length, 3, 'drei Waffen');
      await Stadt.buyWeapon(2);
      T.eq([State.s.weapon, State.s.balance], [2, 5000]);
      T.eq(GangRules.canBuyWeapon(State.s, 1).reason, 'downgrade');
      T.ok(Stadt.line(State.s).includes('Glock'), 'Gear-Zeile nennt die Waffe');
    } finally {
      Cutscene.play = keep.play; State.save = keep.save; State.s = keep.s; State.mode = keep.mode; Story.story = keep.story;
      await UI.show(keep.cur ? keep.cur.id : 'hub');
    }
  });
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `bash tests/dom-selftest.sh`
Expected: FAIL („Story mit enabled: Schaufenster da").

- [ ] **Step 3: Implementieren**

`Stadt.SHOPS`: `pfandleihe: { name: 'Pfandleihe Kowalski', icon: '🔫', kind: 'weapon', story: true },`
`Stadt.SELLER`: `pfandleihe: 'Ich frag nicht, wofür. Du fragst nicht, woher.',`

Neue Methoden in `Stadt`:

```js
  /* Schaufenster, die nur eine Story öffnet (story: true) – sichtbar mit Story.s.enabled[id] */
  storyShop(id) { return !this.SHOPS[id].story || (State.mode === 'story' && typeof Story !== 'undefined' && Story.s && Story.s.enabled && !!Story.s.enabled[id]); },
  weaponPerks(w) { const out = [`Reaktion +${w.bonus} ms`]; if (w.ambushMult) out.push(`Hinterhalte −${Math.round((1 - w.ambushMult) * 100)} %`); out.push(w.desc); return out; },
  async buyWeapon(tier) {
    const s = State.s;
    if (this.busy()) return;
    if (!GangRules.canBuyWeapon(s, tier).ok) return;
    const w = GangRules.WEAPONS[tier];
    SFX.play('cash');
    Game.applyDelta(-w.price, { from: this.root ? qs('#laden', this.root) : null });
    s.weapon = tier;
    State.save();
    await Cutscene.play('stadt.waffe', { name: w.name });
    UI.toast({ icon: w.icon, title: w.name, text: 'Liegt im Handschuhfach. Deins.', tone: 'gold' });
    UI.renderWallet(); UI.renderSide(); this.render();
    await Bus.emit('gear:weapon', { tier });
  },
```

`seller(id)`: erste Zeile `if (id === 'sport' || id === 'pfandleihe') return this.SELLER[id];`
`ownedLine(id)`: `if (id === 'pfandleihe') return \`Deine Waffe: ${s.weapon ? GangRules.WEAPONS[s.weapon].name : '–'}\`;`
`open(id)`: `if (!this.SHOPS[id] || !this.storyShop(id)) return;`
`render()`, Straße: `for (const [id, sh] of Object.entries(this.SHOPS)) { if (!this.storyShop(id)) continue; … }`
`render()`, Laden: vor `if (shop.kind === 'car')` einfügen:

```js
    if (shop.kind === 'weapon') {
      GangRules.WEAPONS.filter((w) => w.tier > 0).forEach((w) => {
        const check = GangRules.canBuyWeapon(s, w.tier);
        laden.append(this.card(w, this.weaponPerks(w), check, `Kaufen · ${UI.fmt(w.price)}`, () => this.buyWeapon(w.tier)));
      });
      return;
    }
```

`line(s)`: hinter der Schuhe-Zeile `if (s.weapon) parts.push(\`${GangRules.WEAPONS[s.weapon].icon} ${GangRules.WEAPONS[s.weapon].name}\`);`

Szene (hinter `stadt.shoes`):

```js
Cutscene.define('stadt.waffe', [
  { bg: 'pfandleihe', who: 'kowalski', mood: 'calm', text: 'Bar, keine Quittung, kein Name. {{name}}. Läuft.' },
  { bg: 'pfandleihe', who: 'kowalski', mood: 'calm', text: 'Ein Tipp umsonst: Wer zu früh zieht, hat schon verloren. Wer zu spät zieht, auch. Dazwischen ist wenig Platz.' },
]);
```

Seitenleiste (`UI.renderSide`, Sektion Stadt): Label `'🏙️ Autohaus · INTERSPORT'` → `` `🏙️ Autohaus · INTERSPORT${inStory && Story.s.enabled && Story.s.enabled.pfandleihe ? ' · Pfandleihe' : ''}` ``.

Hub-Tür Stadt (`tpl-hub`, `chalk-tag` „Autohaus · INTERSPORT") bleibt.

- [ ] **Step 4: Tests + Playtest**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh && python3 tests/playtest-story.py`
Expected: grün; Playtest 140/140 (Stadt zählt in Story 1 weiter 4 Schaufenster).

- [ ] **Step 5: Commit**

```bash
git add keller37.html
git commit -m "feat(stadt): Pfandleihe Kowalski – Waffen kaufen (story-enabled), Gear-Zeile mit Waffe"
```

---

### Task 5: Kurierfahrt – Job und Taxi-Variante

**Files:**
- Modify: `jobs` (`POOL.kurierfahrt`), `job-taxi` (`Taxi.start/spawn/score/floatText/finish`), CSS `.taxi-road.kurier`
- Test: DOM-Selftest

**Interfaces:**
- Consumes: `Story.jobStart.variant` (Engine 3), `GangRules.kurierPay`, `Jobs.collect(id, flags)`.
- Produces: Job `kurierfahrt` `{ kind: 'game', screen: 'job-taxi', variant: 'kurier' }`; `Taxi.variant` (`null | 'kurier'`); bei Kontrolle `Jobs.collect('kurierfahrt', { kontrolle: true })`.

- [ ] **Step 1: Failing DOM-Test**

```js
  T.test('Taxi-Variante kurier: Skin, Zähler, Lohn nach Strafzetteln, Kontrolle setzt Flag', async () => {
    const keep = { s: State.s, mode: State.mode, story: Story.story, cur: UI.current, save: State.save };
    State.save = () => {};
    const story = { id: 't.kurier', title: 'T', days: 3, start: { balance: 1000, vars: {}, unlocked: { jobs: ['kurierfahrt'], doors: [], rooms: [] } }, chapters: [], events: [], scenes: {},
      endings: [{ id: 'aus', title: 'Aus', scene: 'x', priority: 0, fallback: true }] };
    try {
      State.mode = 'story'; State.s = State.freshStory(story); Story.story = story;
      Story.jobStart = { id: 'kurierfahrt', balance: 1000, variant: 'kurier' };
      Story.allowOnce = 'job-taxi';
      await UI.show('job-taxi');
      Taxi.start();
      T.eq([Taxi.variant, Taxi.jobId, qs('#taxiRoad').classList.contains('kurier')], ['kurier', 'kurierfahrt', true]);
      T.ok(qs('#taxiScore').textContent.startsWith('Übergaben'));
      Taxi.tickets = 2; Taxi.timeLeft = 0;
      await Taxi.finish();
      T.eq(State.s.balance, 1000, 'Kontrolle: kein Lohn');
      T.eq(State.s.story.flags.kontrolle, true);
      T.eq(State.s.story.jobToday, 'kurierfahrt');
      /* zweiter Lauf: 1 Strafzettel → 1.500 € */
      State.s.story.jobToday = null; delete State.s.story.flags.kontrolle;
      Story.jobStart = { id: 'kurierfahrt', balance: State.s.balance, variant: 'kurier' };
      Story.allowOnce = 'job-taxi'; await UI.show('job-taxi'); Taxi.start(); Taxi.tickets = 1; Taxi.timeLeft = 0; await Taxi.finish();
      T.eq(State.s.balance, 2500); T.eq(State.s.story.flags.kontrolle, undefined);
    } finally {
      Story.jobStart = null; State.save = keep.save; State.s = keep.s; State.mode = keep.mode; Story.story = keep.story;
      await UI.show(keep.cur ? keep.cur.id : 'hub');
    }
  });
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `bash tests/dom-selftest.sh`
Expected: FAIL (`variant` undefined / kein `kurier`).

- [ ] **Step 3: Job-Definition** (`Jobs.POOL`, hinter `filialleiter`)

```js
    kurierfahrt: { id: 'kurierfahrt', name: 'Kurierfahrt', icon: '💼', kind: 'game', screen: 'job-taxi', variant: 'kurier', desc: 'Anabis Koffer im Kofferraum. 60 Sekunden, drei Spuren, Übergabepunkte statt Fahrgäste. Zwei Strafzettel, und die Polizei guckt in den Kofferraum.', pay: 'bis 3.000 €', requires: { balance: { gte: 200 } }, requireText: 'Kaution 200 €' },
```

- [ ] **Step 4: Taxi-Variante**

`Taxi`-Objekt: Felder `variant: null, jobId: 'taxi'` ergänzen.

`start()`, nach `const gen = this.gen;`:

```js
    this.jobId = Story.jobStart ? Story.jobStart.id : 'taxi';
    this.variant = Story.jobStart ? Story.jobStart.variant || null : null;
    qs('#taxiRoad', this.root).classList.toggle('kurier', this.variant === 'kurier');
    qs('#taxiCar', this.root).textContent = this.variant === 'kurier' ? '🚗' : '🚕';
```

`spawn()`: `pick(['🙋', '🙋‍♀️', '🧑‍🦳', '🕺'])` → `this.variant === 'kurier' ? '📦' : pick(['🙋', '🙋‍♀️', '🧑‍🦳', '🕺'])`.

Im `step` (Rider getroffen): `this.floatText(\`+${15 + this.tip} €\`, 'win')` → `this.floatText(this.variant === 'kurier' ? 'Übergabe ✓' : \`+${15 + this.tip} €\`, 'win')`.

`score()`: `` `${this.variant === 'kurier' ? 'Übergaben' : 'Fahrgäste'} ${this.passengers} · Strafzettel ${this.tickets}` ``.

`finish()` ersetzen:

```js
  async finish() {
    this.running = false;
    clearInterval(this.spawnTimer);
    const kurier = this.variant === 'kurier' ? GangRules.kurierPay(this.tickets) : null;
    const pay = kurier ? kurier.pay : Math.max(StoryRules.taxiPay(this.passengers, this.tickets, this.tip), -Math.max(0, State.s.balance));
    if (this.root) {
      qs('#taxiRoad', this.root).classList.remove('running');
      this.entities.forEach((e) => e.el.remove()); this.entities = [];
      qs('#btnTaxiDone', this.root).classList.remove('hidden');
      const st = qs('#taxiStatus', this.root);
      if (kurier) st.innerHTML = kurier.kontrolle ? '<span class="loss">Kontrolle! Blaulicht, Kofferraum auf, Koffer weg. Kein Lohn.</span>' : `<span class="win">Koffer abgeliefert · ${this.tickets} Strafzettel · ${UI.fmt(pay)}</span>`;
      else st.innerHTML = pay >= 0 ? `<span class="win">Feierabend · ${this.passengers} Fahrgäste · ${UI.fmt(pay)}</span>` : `<span class="loss">Feierabend · ${this.tickets} Strafzettel · Abzug ${UI.fmt(-pay)}</span>`;
    }
    if (pay !== 0) Game.applyDelta(pay, { from: this.root ? qs('#taxiRoad', this.root) : null });
    if (pay > 0) SFX.play('cash'); else if (kurier && kurier.kontrolle) SFX.play('lose');
    await Bus.emit('taxi:result', { passengers: this.passengers, tickets: this.tickets, pay, variant: this.variant });
    await Jobs.collect(this.jobId, kurier && kurier.kontrolle ? { kontrolle: true } : {});
  },
```

CSS (hinter `.taxi-road.running { … }`):

```css
.taxi-road.kurier { background-color: #1e1e28; border-color: #8a7a4a; }
.taxi-road.kurier .rider { filter: drop-shadow(0 0 8px rgba(212,175,55,.8)); }
```

- [ ] **Step 5: Tests + Playtest**

Run: `node tests/run-selftest.mjs && bash tests/dom-selftest.sh && python3 tests/playtest-story.py`
Expected: grün; 140/140 (Story-1-Taxi unverändert: `variant` null).

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(jobs): Kurierfahrt – Taxi-Variante mit Koffer, Lohn nach Strafzetteln, Kontrolle-Flag"
```

---

### Task 6: README

**Files:**
- Modify: `README.md` – Minispiel „Zieh!" (Steuerung: Bereit → warten → tippen/Leertaste), Pfandleihe (Waffen 15.000/35.000/75.000 €), Job Kurierfahrt, Dev-Parameter `?screen=shootout&foe=…&weapon=N`, `?fresh&story=…&weapon=N`.

- [ ] **Step 1: README ergänzen** (Jobs-Liste, Minispiele, Dev-Parameter je eine Zeile)
- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(README): Schießerei, Pfandleihe, Kurierfahrt"
```

---

## Self-Review

- **Spec §6:** Waffen-Tabelle (T1), Zieh!-Ablauf mit Wartezeit/Fehlschuss/Runden (T2), Gegner-Tabelle (T1), `fight:after` mit Ergebnis (T3), Bonus-Override für die Leihpistole (T3 `cfg.bonus`), Pfandleihe ab Story-Freigabe (T4), Dev-Params (T2/T3). Hinterhalt/Angebot/Finale sind Story-Events – Plan 4.
- **Spec §9 Kurierfahrt:** Job + Variante + Lohnregel + Kontrolle-Flag (T5); `job:after`-Event mit Zorn/Beleg – Plan 4.
- **Platzhalter:** keine.
- **Typen:** `duelRound({ reaction, bonus, foe, rng })`; `Shootout.start({ kind, foes, bonus, forced })`; `fight:done/leave { kind, won }`; `forceFight(cfg)` → `{ kind, won }`; Flags `fightWon`/`fightLost`/`fight_<kind>`; `kurierPay(tickets)` → `{ pay, kontrolle }`; `Jobs.collect(id, { kontrolle })`; `Stadt.buyWeapon(tier)`; `s.weapon` 0–3.
