# Caribbean Stud im Casino Royal – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein viertes Royal-Spiel „Caribbean Stud" (Ante → 5 Karten → Mitgehen 2× Ante / Passen → Dealer muss sich mit A-K qualifizieren → Bonus-Tabelle bis 100:1), plus Glück beim Geben, Insider „Sylvies Blick" und Achievement „Karibische Nacht".

**Architecture:** Neuer DOM-freier Block `stud-rules` (`StudRules`, nutzt `PokerRules.evaluate/compare` und `Rules.pech`) nach `poker-rules`; neues Screen-Modul `game-stud` (`Stud`, Muster von `Poker`, Karten über `UI.cardEl`) nach `game-poker`. Geld fließt ausschließlich über `Game.beginSpin / applyDelta / settle / forfeit`. Der Screen wird über die bestehenden Royal-Listen (Zone, Lobby-Portal, Dev-Panel, Story-Umsatz) eingehängt.

**Tech Stack:** Vanilla JS in einer Datei (`keller37.html`), Selftests `T.test/T.eq/T.ok` (Node-Runner `tests/run-selftest.mjs` + DOM-Runner `tests/dom-selftest.sh`), Headless-Chrome-Playtest `tests/playtest-story.py`, `tests/mobile-check.py`.

**Spec:** `docs/superpowers/specs/2026-09-20-caribbean-stud-design.md`

## Global Constraints

- Alles in `keller37.html`; keine neuen Dateien außer Screenshots. Deutsch in allen Texten.
- Ante `StudRules.ANTE = { MIN: 100, MAX: 1000 }`, Bet = `2 * ante` fest, Vorprüfung `Rules.checkSpin(State.s, 3 * ante, Perks.mods())`.
- Bonus-Tabelle `BONUS = [1, 1, 2, 3, 4, 5, 7, 20, 50]`, `ROYAL_BONUS = 100`.
- Insider `{ id: 'sylviesblick', name: 'Sylvies Blick', icon: '🎩', text: 'Caribbean Stud: Madame Sylvie lässt dich eine zweite Dealer-Karte sehen, bevor du mitgehst.', capped: true, mods: { studPeek: true } }`; Kappe über `Rules.effectiveInsider(mods.studPeek, ante)` (250 €).
- Achievement `{ id: 'karibik', title: 'Karibische Nacht', icon: '🌴', desc: 'Bei Caribbean Stud mit Flush oder besser gegen einen qualifizierten Dealer gewonnen.' }`, ausgelöst über `Bus 'stud:result'` bei `outcome === 'win' && player.rank >= 5`.
- Event `stud:result`: `{ outcome, player, dealer, ante, net }` bei **jedem** Ergebnis inkl. `'fold'` (`dealer` = `PokerRules.evaluate(dHand)`, `player` = `PokerRules.evaluate(pHand)`).
- `Game.settle(net, { from, game: 'stud', bet, run })` mit `bet = ante` beim Passen, `3 * ante` nach Mitgehen.
- Keine Änderung an `Story.DOORS`, Kapitel-Türlisten, `Mugging.CASINO`, `GangRules`, Poker/Blackjack/Craps-Logik.
- Vor jedem Commit: `node tests/run-selftest.mjs` grün (0 Fehler). Vor Merge zusätzlich `tests/dom-selftest.sh`, Playtest, `tests/mobile-check.py` grün.
- Commit-Messages enden mit `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Eine zweite Claude-Session arbeitet parallel am selben Repo: Änderungen ausschließlich im eigenen Worktree/Branch, keine Commits auf `main`.

---

## Datei-Struktur

Alles in `keller37.html`:

| Bereich | Anker (Textsuche) | Änderung |
|---|---|---|
| Template Lobby | `<template id="tpl-royal">` → `.deco-portals` | 4. Portal `data-screen="stud"` |
| Template Tisch | nach `</template>` von `tpl-poker` | neues `<template id="tpl-stud">` |
| Perks | `pokerPeekDraw: false, pokerTell: false` / `pokerPeekDraw: 'set', pokerTell: 'set'` / Insider `wirtstell` | `studPeek` + Insider |
| Royal-Modul | `const Royal = {` → `GAMES:` | `'stud'` |
| Screen-Modul | nach `</script>` von `game-poker` | neuer Block `game-stud` |
| Achievements | `Achievements.DEFS` nach `fullhouse`; `Bus.on('poker:result'` | `karibik` + Handler |
| Regeln | nach `</script>` von `poker-rules` | neuer Block `stud-rules` |
| Royal-Regeln | `RoyalRules.SCREENS` | `'stud'` |
| Dev | `DevRules.ROYAL_SCREENS` | `'stud'` |
| Story | `Story.ROOM_OF`; `STORY_STASH.turnoverGroups.umsatzRoyal` | `stud` |
| Boot | `['megaslots', 'craps', 'wheel'].includes(params.get('game'))` | `'stud'` |
| Selftests | Block `selftest`: nach `PokerRules.luckOverride`-Test; Katalog-Test `Rules.INSIDER.length, 8`; `mods: Kartenhai und Wirts Tell`; `RoyalRules.zoneFor`-Test; `StoryRules.recordStake`-Fixture; DOM-Chip-Test `Einsatz-Anzeige (Royal + Baccarat)` | neue/erweiterte Tests |

Tests-Ordner: `tests/run-selftest.mjs` (Block-Liste), `tests/playtest-story.py` (`scenario_stud`), `tests/mobile-check.py` (`FREE_SCREENS`, Zonen-Check). Screenshots: `docs/superpowers/screenshots/royal-lobby.png` (erneuern), `royal-stud.png` (neu).

---

### Task 1: `StudRules` – Qualifikation, Bonus, Abrechnung, Geben, Glück

**Files:**
- Modify: `keller37.html` – neuer Block `<script id="stud-rules">` direkt nach dem `</script>` des Blocks `poker-rules` (vor `<script id="gang-rules">`)
- Modify: `keller37.html` – Block `selftest`, direkt nach dem Test `'PokerRules.luckOverride: …'` (vor `T.test('Story 1 Kapitel 2/4 und Dev-Panel enthalten poker'`)
- Modify: `tests/run-selftest.mjs` – Block-Liste

**Interfaces:**
- Consumes: `PokerRules.evaluate(cards) → { rank 0–8, name, tiebreak[] }`, `PokerRules.compare(a, b) → -1|0|1`, `Rules.pech(luck, rng)`; Test-Helfer `P('K♠', '3♣', …)` → Kartenobjekte `{ val, suit }`, `seq(...vals)` → deterministischer RNG.
- Produces: `StudRules.ANTE`, `StudRules.BONUS`, `StudRules.ROYAL_BONUS`, `StudRules.qualifies(hand) → boolean`, `StudRules.bonus(hand) → number`, `StudRules.deal(deck) → { player, dealer, deck }`, `StudRules.settle(player, dealer, ante) → { outcome: 'noqual'|'win'|'push'|'lose', net, bonus }`, `StudRules.luckOverride(hands, luck, rng) → hands` (dasselbe Objekt oder ein neues aus `deal(hands.deck)`).

- [ ] **Step 1: Block in den Node-Runner eintragen**

In `tests/run-selftest.mjs` in der Zeile `for (const id of ['rules', 'gear-rules', … 'poker-rules', 'gang-rules', …])` nach `'poker-rules'` den Eintrag `'stud-rules'` einfügen:

```js
… 'baccarat-rules', 'poker-rules', 'stud-rules', 'gang-rules', …
```

- [ ] **Step 2: Failing Tests schreiben**

Im Block `selftest` direkt nach dem Test `T.test('PokerRules.luckOverride: …')` einfügen:

```js
T.test('StudRules.qualifies: Ass-König oder Paar und besser', () => {
  const Q = StudRules.qualifies;
  T.ok(Q(P('A♠', 'K♥', '9♦', '5♣', '2♠')), 'A-K qualifiziert');
  T.ok(!Q(P('A♠', 'Q♥', 'J♦', '9♣', '2♠')), 'A-Q nicht');
  T.ok(!Q(P('K♠', 'Q♥', 'J♦', '9♣', '2♠')), 'K-Q nicht');
  T.ok(Q(P('2♠', '2♥', '9♦', '5♣', '3♠')), 'Paar 2 qualifiziert');
});
T.test('StudRules.bonus: Tabelle je Rang, Royal Flush 100', () => {
  const B = StudRules.bonus;
  T.eq(StudRules.BONUS, [1, 1, 2, 3, 4, 5, 7, 20, 50]); T.eq(StudRules.ROYAL_BONUS, 100);
  T.eq(B(P('A♠', '9♥', '7♦', '4♣', '2♠')), 1, 'High Card 1:1');
  T.eq(B(P('9♠', '9♥', 'A♦', '4♣', '2♠')), 1, 'Paar');
  T.eq(B(P('9♠', '9♥', '4♦', '4♣', 'A♠')), 2, 'Zwei Paare');
  T.eq(B(P('7♠', '7♥', '7♦', 'K♣', 'K♠')), 7, 'Full House');
  T.eq(B(P('9♥', '10♥', 'J♥', 'Q♥', 'K♥')), 50, 'Straight Flush');
  T.eq(B(P('10♠', 'J♠', 'Q♠', 'K♠', 'A♠')), 100, 'Royal Flush');
});
T.test('StudRules.settle: noqual, win mit Bonus, push, lose, Royal', () => {
  const S = StudRules.settle;
  const paar9 = P('9♦', '9♣', '5♠', '4♦', 'Q♥'), zweiPaare = P('K♠', 'K♥', '7♣', '7♠', '2♥');
  T.eq(S(paar9, P('A♠', 'Q♦', 'J♣', '9♥', '2♠'), 200), { outcome: 'noqual', net: 200, bonus: 0 }, 'Dealer A-Q: Ante 1:1, Bet zurück');
  T.eq(S(zweiPaare, paar9, 200), { outcome: 'win', net: 1000, bonus: 2 }, '200 + 400·2');
  T.eq(S(P('9♠', '9♥', 'K♦', '4♣', '2♠'), P('9♦', '9♣', 'K♥', '4♥', '2♥'), 200), { outcome: 'push', net: 0, bonus: 0 });
  T.eq(S(zweiPaare, P('5♠', '5♥', '5♦', '8♣', '3♠'), 200), { outcome: 'lose', net: -600, bonus: 0 }, 'Drilling schlägt Zwei Paare');
  T.eq(S(P('10♠', 'J♠', 'Q♠', 'K♠', 'A♠'), paar9, 200), { outcome: 'win', net: 40200, bonus: 100 }, 'Royal: 200 + 400·100');
});
T.test('StudRules.deal: abwechselnd Spieler/Dealer von oben, Rest bleibt im Deck', () => {
  const d = StudRules.deal(P('A♠', '2♠', '3♠', '4♠', '5♠', '6♠', '7♠', '8♠', '9♠', '10♠', 'J♠', 'Q♠'));
  T.eq(d.player.map((c) => c.val), ['A', '3', '5', '7', '9']);
  T.eq(d.dealer.map((c) => c.val), ['2', '4', '6', '8', '10']);
  T.eq(d.deck.map((c) => c.val), ['J', 'Q']);
});
T.test('StudRules.luckOverride: Glück gibt Verlust neu, Pech gibt Gewinn neu, sonst unverändert', () => {
  const rest = P('2♣', '3♣', '4♣', '5♣', '6♣', '7♣', '8♣', '9♣', '10♣', 'J♣');
  const lose = { player: P('A♠', '9♥', '7♦', '4♣', '2♠'), dealer: P('9♦', '9♣', '5♠', '4♦', 'Q♥'), deck: rest };
  const win = { player: P('K♠', 'K♥', '7♣', '7♠', '2♥'), dealer: P('9♦', '9♣', '5♠', '4♦', 'Q♥'), deck: rest };
  const neu = StudRules.luckOverride(lose, 50, seq(0.1));
  T.ok(neu !== lose && neu.player[0].val === '2' && neu.dealer[0].val === '3' && neu.deck.length === 0, 'Verlust + Glück → neu vom Restdeck');
  T.ok(StudRules.luckOverride(lose, 50, seq(0.9)) === lose, 'rng über luck → unverändert');
  T.ok(StudRules.luckOverride(win, -50, seq(0.1)) !== win, 'Gewinn + Pech → neu');
  let calls = 0; const rng = () => { calls++; return 0; };
  T.ok(StudRules.luckOverride(win, 50, rng) === win, 'Gewinn + Glück → unverändert'); T.eq(calls, 0, 'kein rng-Aufruf');
  T.ok(StudRules.luckOverride(lose, 0, rng) === lose, 'ohne Glück nie'); T.eq(calls, 0);
  T.ok(StudRules.luckOverride(lose, -50, rng) === lose, 'Verlust + Pech → unverändert'); T.eq(calls, 0);
});
```

- [ ] **Step 3: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | tail -15`
Expected: die fünf `StudRules.*`-Tests fehlgeschlagen mit `ReferenceError: StudRules is not defined`; alle anderen grün.

- [ ] **Step 4: Block `stud-rules` schreiben**

Direkt nach dem `</script>` des Blocks `poker-rules` (also vor `<script id="gang-rules">`) einfügen:

```html
<script id="stud-rules">
/* ================= CARIBBEAN STUD – gegen das Haus (rein, kein DOM) ================= */
const StudRules = {
  ANTE: { MIN: 100, MAX: 1000 },
  /* Bonus auf den Bet (2× Ante) je PokerRules-Rang: High Card … Straight Flush; Royal Flush gesondert */
  BONUS: [1, 1, 2, 3, 4, 5, 7, 20, 50],
  ROYAL_BONUS: 100,
  /* Der Dealer spielt ab Ass-König (oder Paar und besser); sonst nur Ante 1:1 */
  qualifies(hand) {
    const e = PokerRules.evaluate(hand);
    return e.rank >= 1 || (e.tiebreak[0] === 14 && e.tiebreak[1] === 13);
  },
  bonus(hand) {
    const e = PokerRules.evaluate(hand);
    return e.rank === 8 && e.tiebreak[0] === 14 ? StudRules.ROYAL_BONUS : StudRules.BONUS[e.rank];
  },
  /* Abwechselnd von oben: gerade Indizes Spieler, ungerade Dealer; Rest bleibt im Deck (forceDeck im Test lesbar) */
  deal(deck) {
    const player = [], dealer = [];
    for (let i = 0; i < 10; i++) (i % 2 === 0 ? player : dealer).push(deck[i]);
    return { player, dealer, deck: deck.slice(10) };
  },
  /* Nettobetrag für den Spieler nach Mitgehen (Einsatz Ante + Bet = 3× Ante) */
  settle(player, dealer, ante) {
    if (!StudRules.qualifies(dealer)) return { outcome: 'noqual', net: ante, bonus: 0 };
    const c = PokerRules.compare(PokerRules.evaluate(player), PokerRules.evaluate(dealer));
    if (c > 0) { const bonus = StudRules.bonus(player); return { outcome: 'win', net: ante + 2 * ante * bonus, bonus }; }
    if (c < 0) return { outcome: 'lose', net: -3 * ante, bonus: 0 };
    return { outcome: 'push', net: 0, bonus: 0 };
  },
  /* Glück: eine Verlusthand (als würde der Spieler mitgehen) wird mit luck % einmal neu vom Restdeck gegeben.
     Pech: eine Gewinnhand mit |luck| %. Höchstens ein rng-Aufruf, höchstens ein Neugeben. */
  luckOverride(hands, luck, rng) {
    const net = StudRules.settle(hands.player, hands.dealer, 1).net;
    if (luck > 0 && net < 0 && rng() * 100 < luck) return StudRules.deal(hands.deck);
    if (luck < 0 && net > 0 && Rules.pech(luck, rng)) return StudRules.deal(hands.deck);
    return hands;
  },
};
</script>
```

- [ ] **Step 5: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -5`
Expected: 0 Fehler, Anzahl Tests um 5 gestiegen.

- [ ] **Step 6: Commit**

```bash
git add keller37.html tests/run-selftest.mjs
git commit -m "feat(stud): StudRules – Qualifikation, Bonus-Tabelle, Abrechnung, Geben, Glück

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Insider „Sylvies Blick" und Achievement „Karibische Nacht"

**Files:**
- Modify: `keller37.html` – Block `perk-rules`: `Rules.NEUTRAL_MODS` (Zeile mit `pokerPeekDraw: false, pokerTell: false, bjDealerStand: 17`), `Rules.MOD_STACK` (Zeile mit `pokerPeekDraw: 'set', pokerTell: 'set', bjDealerStand: 'max'`), `Rules.INSIDER` (nach dem Eintrag `wirtstell`)
- Modify: `keller37.html` – Block `achievements`: `Achievements.DEFS` nach dem Eintrag `fullhouse`; nach der Zeile `Bus.on('poker:result', …)`
- Modify: `keller37.html` – Block `selftest`: Test `'Kataloge: Skills mit Licht/Schatten, mods-Schlüssel bekannt'`, Test `'mods: Kartenhai und Wirts Tell; neutral aus'`, neuer DOM-Test

**Interfaces:**
- Consumes: `Rules.mods(s, meta)`, `Rules.effectiveInsider(value, bet)` (boolean → `value && bet <= 250`), `Achievements.has/unlock`, `Bus.on/emit`, Test-Helfer `base(...)`.
- Produces: `Perks.mods().studPeek` (boolean), Insider-Id `'sylviesblick'`, Achievement-Id `'karibik'`, Bus-Handler auf `'stud:result'`.

- [ ] **Step 1: Failing Tests schreiben**

Im Test `'Kataloge: Skills mit Licht/Schatten, mods-Schlüssel bekannt'` die Zeile `T.eq(Rules.SKILLS.length, 9); T.eq(Rules.INSIDER.length, 8);` ändern zu:

```js
  T.eq(Rules.SKILLS.length, 9); T.eq(Rules.INSIDER.length, 9);
```

Den Test `'mods: Kartenhai und Wirts Tell; neutral aus'` komplett ersetzen durch:

```js
T.test('mods: Kartenhai, Wirts Tell und Sylvies Blick; neutral aus', () => {
  const n = Rules.mods(base(), { insider: [] });
  T.eq([n.pokerPeekDraw, n.pokerTell, n.bjDealerStand, n.studPeek], [false, false, 17, false]);
  const m = Rules.mods(base({ skills: ['kartenhai'] }), { insider: ['wirtstell', 'sylviesblick'] });
  T.eq([m.pokerPeekDraw, m.pokerTell, m.bjDealerStand, m.studPeek], [true, true, 18, true]);
  T.ok(Rules.SKILLS.some((k) => k.id === 'kartenhai') && Rules.INSIDER.some((i) => i.id === 'wirtstell' && i.capped));
  T.ok(Rules.INSIDER.some((i) => i.id === 'sylviesblick' && i.capped && i.icon === '🎩'), 'Sylvies Blick gedeckelt');
  T.eq(Rules.MOD_STACK.studPeek, 'set');
  T.eq(Rules.effectiveInsider(m.studPeek, 250), true); T.eq(Rules.effectiveInsider(m.studPeek, 500), false, 'über der Kappe aus');
});
```

Direkt danach den DOM-Test anfügen (der Block `achievements` wird in Node nicht geladen):

```js
if (typeof document !== 'undefined') T.test('Erfolg karibik: Flush oder besser gewinnt bei Stud, Straße nicht, Passen nicht', async () => {
  const keep = State.meta.achievements.slice(), saveMeta = State.saveMeta;
  State.saveMeta = () => {};
  try {
    State.meta.achievements = State.meta.achievements.filter((id) => id !== 'karibik');
    T.ok(Achievements.DEFS.some((a) => a.id === 'karibik' && a.icon === '🌴'), 'im Katalog');
    await Bus.emit('stud:result', { outcome: 'win', player: { rank: 4 }, dealer: { rank: 1 }, ante: 100, net: 900 });
    T.ok(!Achievements.has('karibik'), 'Straße reicht nicht');
    await Bus.emit('stud:result', { outcome: 'fold', player: { rank: 5 }, dealer: { rank: 1 }, ante: 100, net: -100 });
    T.ok(!Achievements.has('karibik'), 'Passen zählt nicht');
    await Bus.emit('stud:result', { outcome: 'win', player: { rank: 5 }, dealer: { rank: 1 }, ante: 100, net: 1100 });
    T.ok(Achievements.has('karibik'), 'Flush gewinnt → Trophäe');
  } finally { State.meta.achievements = keep; State.saveMeta = saveMeta; }
});
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|Fehler|✗" | head`
Expected: Katalog-Test fehlgeschlagen (`INSIDER.length` 8 ≠ 9), mods-Test fehlgeschlagen (`studPeek` undefined statt false).

- [ ] **Step 3: Perks ergänzen**

In `Rules.NEUTRAL_MODS` die Zeile

```js
    pokerPeekDraw: false, pokerTell: false, bjDealerStand: 17,
```
ändern zu
```js
    pokerPeekDraw: false, pokerTell: false, bjDealerStand: 17, studPeek: false,
```

In `Rules.MOD_STACK` die Zeile
```js
    pokerPeekDraw: 'set', pokerTell: 'set', bjDealerStand: 'max',
```
ändern zu
```js
    pokerPeekDraw: 'set', pokerTell: 'set', bjDealerStand: 'max', studPeek: 'set',
```

In `Rules.INSIDER` nach der Zeile mit `id: 'wirtstell'` einfügen:

```js
    { id: 'sylviesblick', name: 'Sylvies Blick', icon: '🎩', text: 'Caribbean Stud: Madame Sylvie lässt dich eine zweite Dealer-Karte sehen, bevor du mitgehst.', capped: true, mods: { studPeek: true } },
```

- [ ] **Step 4: Achievement ergänzen**

In `Achievements.DEFS` nach der Zeile mit `id: 'fullhouse'` einfügen:

```js
    { id: 'karibik', title: 'Karibische Nacht', icon: '🌴', desc: 'Bei Caribbean Stud mit Flush oder besser gegen einen qualifizierten Dealer gewonnen.' },
```

Nach der Zeile `Bus.on('poker:result', …)` einfügen:

```js
Bus.on('stud:result', ({ outcome, player }) => { if (outcome === 'win' && player.rank >= 5) Achievements.unlock('karibik'); });
```

- [ ] **Step 5: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3` → 0 Fehler.
Run: `tests/dom-selftest.sh 2>&1 | tail -3` → 0 Fehler (enthält den neuen `karibik`-Test und den Test `insiderDraw` mit dem 9er-Katalog).

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(stud): Insider Sylvies Blick (studPeek) und Erfolg Karibische Nacht

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Screen `stud` – Template und Modul `Stud`

**Files:**
- Modify: `keller37.html` – neues `<template id="tpl-stud">` direkt nach dem `</template>` von `tpl-poker`
- Modify: `keller37.html` – neuer Block `<script id="game-stud">` direkt nach dem `</script>` des Blocks `game-poker` (vor `<script id="game-roulette">`)
- Test: Browser (manuell per `?screen=stud` noch **nicht** erreichbar – Listen kommen in Task 4; hier über `UI.show('stud')` in der Konsole bzw. DOM-Selftest)

**Interfaces:**
- Consumes: `StudRules.*` (Task 1), `Perks.mods().studPeek` (Task 2), `UI.cardEl(card, hidden)`, `UI.register(id, {template, mount, unmount})`, `Game.bindBet(root, inputId)`, `Game.readBet(id)`, `Game.beginSpin(bet)`, `Game.applyDelta(delta, {quiet})`, `Game.settle(net, {from, game, bet, run})`, `Game.forfeit()`, `Game.run`, `Rules.checkSpin`, `Rules.effectiveLuck`, `Rules.luck`, `Rules.effectiveInsider`, `Rules.INSIDER_CAP`, `Rules.newDeck`, `PokerRules.evaluate`, `UI.fmt`, `UI.toast`, `UI.show`, `SFX.play`, `wait`, `qs/qsa`.
- Produces: Screen-Id `'stud'`, `Stud.forceDeck` (Array; wird per `StudRules.deal` von **oben** verteilt: Index 0,2,4,6,8 Spieler, 1,3,5,7,9 Dealer), `Stud.round` (`null` außerhalb einer Hand), `Stud.inRound`, Bus-Event `'stud:result'`.

- [ ] **Step 1: Template einfügen**

Direkt nach dem `</template>` von `tpl-poker`:

```html
<template id="tpl-stud">
  <div class="panel bj-panel felt">
    <div class="bj-table">
      <div class="bj-hand dealer">
        <div class="hand-label">Madame Sylvie <span class="hand-val" id="studDealerName">–</span> <span class="insider-hint hidden" id="studPeek"></span></div>
        <div class="cards" id="studDealerCards"></div>
      </div>
      <div class="bj-arc" id="studArc">Ante · –</div>
      <div class="bj-hand player">
        <div class="cards" id="studPlayerCards"></div>
        <div class="hand-label">Du <span class="hand-val" id="studHandName">–</span></div>
      </div>
    </div>
    <div class="status" id="studStatus">Ante setzen</div>
    <div class="bet-bar" id="studBetControls">
      <div class="bet-field bet-view"><input type="number" id="studBet" value="100" min="100" readonly></div>
      <button class="chip" data-chip="100" data-v="100">100</button>
      <button class="chip" data-chip="250" data-v="25">250</button>
      <button class="chip" data-chip="500" data-v="500">500</button>
      <button class="chip" data-chip="1000" data-v="max">1000</button>
      <button class="btn solid" id="btnStudDeal">Geben</button>
    </div>
    <div class="bet-bar hidden" id="studCallControls">
      <button class="btn green" id="btnStudCall">Mitgehen</button>
      <button class="btn ghost" id="btnStudFold">Passen</button>
    </div>
    <div class="bet-bar"><button class="btn ghost sm" id="studBack">← Lobby</button></div>
  </div>
</template>
```

- [ ] **Step 2: Block `game-stud` schreiben**

Direkt nach dem `</script>` des Blocks `game-poker`:

```html
<script id="game-stud">
/* ================= CARIBBEAN STUD – Ante, fünf Karten, Mitgehen oder Passen gegen das Haus ================= */
const Stud = {
  root: null, gen: 0, round: null, inRound: false, busy: false,
  forceDeck: null, // Dev/Test: festes Deck für die nächste Hand (StudRules.deal verteilt von oben, abwechselnd Spieler/Dealer)
  GROUPS: ['studBetControls', 'studCallControls'],
  alive(gen) { return !!this.root && this.gen === gen; },
  /* Hand ohne Abrechnung fallen lassen (Screen verlassen) – Einsätze sind bereits abgezogen */
  drop(round) { if (round && !round.done) { round.done = true; Game.forfeit(); } },
  show(group) { for (const g of this.GROUPS) qs('#' + g, this.root).classList.toggle('hidden', g !== group); },
  status(html) { qs('#studStatus', this.root).innerHTML = html; },
  renderArc(round) { qs('#studArc', this.root).textContent = round.called ? `Ante ${UI.fmt(round.ante)} · Bet ${UI.fmt(2 * round.ante)}` : `Ante ${UI.fmt(round.ante)}`; },
  async deal() {
    if (this.inRound || !this.root) return;
    const ante = Game.readBet('studBet');
    if (!(ante >= StudRules.ANTE.MIN && ante <= StudRules.ANTE.MAX)) { UI.toast({ icon: '🃏', title: 'Einsatz', text: `Zwischen ${UI.fmt(StudRules.ANTE.MIN)} und ${UI.fmt(StudRules.ANTE.MAX)}.`, tone: 'loss' }); SFX.play('lose'); return; }
    const mods = Perks.mods();
    const chk = Rules.checkSpin(State.s, 3 * ante, mods);
    if (!chk.ok && chk.reason === 'funds') { UI.toast({ icon: '🃏', title: 'Zu wenig für diesen Tisch', text: `Du brauchst 3× Ante (${UI.fmt(3 * ante)}).`, tone: 'loss' }); SFX.play('lose'); return; }
    if (!Game.beginSpin(ante)) return;
    const gen = this.gen;
    this.inRound = true; this.busy = true;
    const deck = this.forceDeck ? this.forceDeck.slice() : Rules.newDeck(Math.random);
    this.forceDeck = null;
    let hands = StudRules.deal(deck);
    hands = StudRules.luckOverride(hands, Rules.effectiveLuck(Rules.luck(State.s, mods), ante), Math.random);
    const peek = Rules.effectiveInsider(mods.studPeek, ante);
    const round = { pHand: hands.player, dHand: hands.dealer, ante, called: false, phase: 'deal', gen, run: Game.run, done: false };
    this.round = round;
    try {
      qs('#studPlayerCards', this.root).innerHTML = ''; qs('#studDealerCards', this.root).innerHTML = '';
      qs('#studHandName', this.root).textContent = '–'; qs('#studDealerName', this.root).textContent = '–';
      qsa('.hand-val', this.root).forEach((v) => v.classList.remove('push'));
      const hint = qs('#studPeek', this.root);
      hint.classList.toggle('hidden', !mods.studPeek);
      hint.textContent = mods.studPeek && !peek ? `🎩 Sylvies Blick: wirkt bis ${UI.fmt(Rules.INSIDER_CAP)}` : mods.studPeek ? '🎩 Sylvies Blick' : '';
      qs('#btnStudCall', this.root).textContent = `Mitgehen (${UI.fmt(2 * ante)})`;
      this.show('studCallControls');
      this.renderArc(round);
      this.status(`Mitgehen (${UI.fmt(2 * ante)}) oder passen?`);
      for (let i = 0; i < 5; i++) {
        if (!this.alive(gen)) break;
        qs('#studPlayerCards', this.root).append(UI.cardEl(round.pHand[i]));
        qs('#studDealerCards', this.root).append(UI.cardEl(round.dHand[i], !(i === 0 || (i === 1 && peek))));
        SFX.play('cardSlide');
        await wait(180);
      }
      if (this.alive(gen)) qs('#studHandName', this.root).textContent = PokerRules.evaluate(round.pHand).name;
      round.phase = 'decide';
    } finally {
      if (this.gen === gen) this.busy = false;
      else this.drop(round);
    }
  },
  async call() {
    const round = this.round;
    if (!round || round.phase !== 'decide' || this.busy) return;
    const gen = this.gen;
    this.busy = true; round.phase = 'showdown';
    try {
      Game.applyDelta(-2 * round.ante, { quiet: true }); round.called = true;
      if (this.alive(gen)) { this.renderArc(round); this.show(null); this.status('Showdown'); }
      await this.showdown(round);
    } finally {
      if (this.gen === gen) this.busy = false;
      else this.drop(round);
    }
  },
  async fold() {
    const round = this.round;
    if (!round || round.phase !== 'decide' || this.busy) return;
    const gen = this.gen;
    this.busy = true; round.phase = 'end';
    try { await this.finish(round, 'fold', -round.ante); }
    finally { if (this.gen === gen) this.busy = false; else this.drop(round); }
  },
  async showdown(round) {
    if (this.alive(round.gen)) {
      const cards = qsa('#studDealerCards .pcard.hidden-card', this.root);
      for (const c of cards) { c.classList.remove('hidden-card'); SFX.play('cardSlide'); await wait(160); }
      qs('#studDealerName', this.root).textContent = StudRules.qualifies(round.dHand) ? PokerRules.evaluate(round.dHand).name : 'qualifiziert sich nicht';
      await wait(400);
    }
    const r = StudRules.settle(round.pHand, round.dHand, round.ante);
    await this.finish(round, r.outcome, r.net, r.bonus);
  },
  async finish(round, outcome, net, bonus = 0) {
    if (round.done) return;
    round.done = true;
    const pe = PokerRules.evaluate(round.pHand), de = PokerRules.evaluate(round.dHand);
    const stake = round.called ? 3 * round.ante : round.ante;
    if (this.alive(round.gen)) {
      const msg = outcome === 'fold' ? `<span class="loss">Gepasst · −${UI.fmt(round.ante)}</span>`
        : outcome === 'noqual' ? `<span class="win">Dealer nicht qualifiziert (A-K nötig) · +${UI.fmt(net)}</span>`
        : outcome === 'win' ? `<span class="win">${pe.name} schlägt ${de.name} · Bonus ${bonus}:1 · +${UI.fmt(net)}</span>`
        : outcome === 'lose' ? `<span class="loss">${de.name} schlägt ${pe.name} · −${UI.fmt(-net)}</span>`
        : 'Gleichstand · Push';
      this.status(msg);
      if (outcome === 'push') qsa('.hand-val', this.root).forEach((v) => v.classList.add('push'));
      this.show('studBetControls');
    }
    if (this.gen === round.gen) { this.inRound = false; this.busy = false; }
    await Bus.emit('stud:result', { outcome, player: pe, dealer: de, ante: round.ante, net });
    await Game.settle(net, { from: this.alive(round.gen) ? qs('#studPlayerCards', this.root) : null, game: 'stud', bet: stake, run: round.run });
  },
  /* Leertaste wie an den anderen Royal-Tischen: Geben bzw. Mitgehen */
  onKey(e) {
    if (e.code !== 'Space' || !qs('#cutscene').hidden || e.repeat || !Stud.root) return;
    e.preventDefault();
    if (Stud.round && Stud.round.phase === 'decide') Stud.call(); else Stud.deal();
  },
};

UI.register('stud', {
  template: 'tpl-stud',
  mount(root) {
    Stud.gen++;
    Stud.root = root;
    Game.bindBet(root, 'studBet');
    qs('#btnStudDeal', root).addEventListener('click', () => Stud.deal());
    qs('#btnStudCall', root).addEventListener('click', () => Stud.call());
    qs('#btnStudFold', root).addEventListener('click', () => Stud.fold());
    qs('#studBack', root).addEventListener('click', () => { SFX.play('click'); UI.show('royal'); });
    document.addEventListener('keydown', Stud.onKey);
  },
  unmount() {
    Stud.gen++;
    document.removeEventListener('keydown', Stud.onKey);
    if (Stud.inRound) {
      /* Zwischen zwei Aktionen verlassen: Hand sofort fallen lassen. Läuft noch eine Kette (busy), räumt die selbst auf. */
      if (!Stud.busy) Stud.drop(Stud.round);
      UI.toast({ icon: '🃏', title: 'Hand aufgegeben', text: 'Einsatz verfallen.', tone: 'loss' });
    }
    Stud.root = null; Stud.inRound = false; Stud.busy = false; Stud.round = null;
  },
});
</script>
```

Hinweise zum Geldfluss (nicht ändern): `Game.beginSpin(ante)` bucht die Ante ab und hält sie als Escrow; `applyDelta(-2·ante)` bucht den Bet ab; `Game.settle(net, { bet: stake })` schreibt `net + stake` gut. Beim Passen ist `stake = ante`, `net = -ante` → Gutschrift 0. Beim Mitgehen `stake = 3·ante`.

- [ ] **Step 3: DOM-Selftest schreiben (Geldfluss über den echten Screen, festes Deck)**

Im Block `selftest`, direkt nach dem in Task 2 angelegten DOM-Test `'Erfolg karibik: …'`:

```js
if (typeof document !== 'undefined') T.test('Stud: Geben bucht Ante, Mitgehen Bet, Showdown zahlt net + Einsatz; Passen verliert Ante', async () => {
  const keep = { s: State.s, mode: State.mode, save: State.save, saveMeta: State.saveMeta, cur: UI.current };
  State.save = () => {}; State.saveMeta = () => {};
  const C = (val, suit) => ({ val, suit });
  const deck = () => [C('K', '♠'), C('9', '♦'), C('K', '♥'), C('9', '♣'), C('7', '♣'), C('5', '♠'), C('7', '♠'), C('4', '♦'), C('2', '♥'), C('Q', '♥'), ...Rules.newDeck(Math.random)];
  try {
    State.mode = 'free'; State.s = State.fresh(); State.s.balance = 1000; State.s.car = 'audiA3';
    await UI.show('stud');
    const root = qs('#stage');
    qs('.chip[data-chip="250"]', root).click(); qs('.chip[data-chip="100"]', root).click();
    Stud.forceDeck = deck();
    await Stud.deal();
    T.eq(State.s.balance, 900, 'Ante 100 abgebucht');
    T.eq(qsa('#studDealerCards .pcard.hidden-card', root).length, 4, 'vier Dealer-Karten verdeckt');
    T.eq(qs('#studHandName', root).textContent, 'Zwei Paare');
    await Stud.call();
    T.eq(State.s.balance, 1500, '900 − 200 Bet + (500 net + 300 Einsatz)');
    T.eq(qsa('#studDealerCards .pcard.hidden-card', root).length, 0, 'alles aufgedeckt');
    T.ok(qs('#studStatus', root).textContent.includes('Bonus 2:1'), qs('#studStatus', root).textContent);
    T.ok(Stud.round === null || Stud.round.done, 'Hand beendet'); T.ok(!Stud.inRound);
    Stud.forceDeck = deck();
    await Stud.deal();
    await Stud.fold();
    T.eq(State.s.balance, 1400, 'Passen: Ante weg');
    T.ok(qs('#studStatus', root).textContent.includes('Gepasst'));
  } finally {
    State.s = keep.s; State.mode = keep.mode; State.save = keep.save; State.saveMeta = keep.saveMeta;
    await UI.show(keep.cur ? keep.cur.id : 'hub');
  }
});
```

- [ ] **Step 4: DOM-Selftest laufen lassen**

Run: `tests/dom-selftest.sh 2>&1 | tail -5`
Expected: 0 Fehler, der neue Stud-Test grün. Falls `UI.show('stud')` in der DOM-Umgebung die Zone setzt: das ist gewollt (`RoyalRules.zoneFor` kennt `stud` erst ab Task 4; solange gilt Zone `keller`, was den Test nicht berührt).

- [ ] **Step 5: Node-Selftest weiterhin grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3` → 0 Fehler.

- [ ] **Step 6: Commit**

```bash
git add keller37.html
git commit -m "feat(stud): Tisch-Screen Caribbean Stud – Geben, Mitgehen/Passen, Showdown, Insider-Blick

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Einhängen – Lobby-Portal, Royal-Listen, Story-Umsatz, Boot, Dev, Mobile-Check

**Files:**
- Modify: `keller37.html` – `tpl-royal` (`.deco-portals`), `Royal.GAMES`, `RoyalRules.SCREENS`, `DevRules.ROYAL_SCREENS`, `Story.ROOM_OF`, `STORY_STASH.turnoverGroups`, Boot-Parameter, Selftests (`RoyalRules.zoneFor`, `StoryRules.recordStake`, DOM-Chip-Test)
- Modify: `tests/mobile-check.py` – `FREE_SCREENS`, Zonen-Check

**Interfaces:**
- Consumes: Screen `'stud'` (Task 3).
- Produces: `stud` in allen Royal-Listen; `?screen=royal&game=stud` bootet direkt an den Tisch.

- [ ] **Step 1: Failing Tests schreiben**

Test `'RoyalRules.zoneFor: Royal-Screens sind Zone royal, alles andere keller'`: die Zeile `T.eq(RoyalRules.SCREENS, ['royal', 'megaslots', 'craps', 'wheel']);` ändern zu

```js
  T.eq(RoyalRules.SCREENS, ['royal', 'megaslots', 'craps', 'wheel', 'stud']);
```

Direkt nach diesem Test neuen Test einfügen:

```js
T.test('stud hängt in allen Royal-Listen', () => {
  T.ok(DevRules.ROYAL_SCREENS.includes('stud'), 'Dev-Panel');
  T.ok(STORY_STASH.turnoverGroups.umsatzRoyal.includes('stud'), 'Story 3 Royal-Umsatz');
});
if (typeof document !== 'undefined') T.test('stud: Royal.GAMES, ROOM_OF und Lobby-Portal', () => {
  T.ok(Royal.GAMES.includes('stud'), 'Royal.GAMES');
  T.eq(Story.ROOM_OF.stud, ['royal'], 'ROOM_OF');
  const tpl = qs('#tpl-royal').content;
  T.ok(!!tpl.querySelector('.portal[data-screen="stud"] .plaque') && tpl.querySelector('.portal[data-screen="stud"] .plaque').textContent === 'Caribbean Stud', 'Portal in der Lobby');
});
```

Im Test `'StoryRules.recordStake: Umsatz gesamt, Gruppen je Spiel, bet ≤ 0 zählt nicht'` die Fixture-Zeile `const story = { turnoverGroups: { umsatzRoyal: ['megaslots', 'craps', 'wheel'], umsatzHinterzimmer: ['baccarat'] } };` ändern zu:

```js
  const story = { turnoverGroups: { umsatzRoyal: ['megaslots', 'craps', 'wheel', 'stud'], umsatzHinterzimmer: ['baccarat'] } };
```

Im DOM-Test `'Einsatz-Anzeige (Royal + Baccarat): …'` die Schleifenliste erweitern:

```js
      for (const [screen, id, start, chip] of [['megaslots', 'megaBet', '100', '500'], ['craps', 'crapsBet', '50', '200'], ['wheel', 'wheelBet', '100', '1000'], ['stud', 'studBet', '100', '500'], ['hinterzimmer', 'bacBet', '500', '5000']]) {
```

- [ ] **Step 2: Tests laufen lassen – müssen fehlschlagen**

Run: `node tests/run-selftest.mjs 2>&1 | grep -E "FAIL|✗" | head`
Expected: `zoneFor`-Test und `'stud hängt in allen Royal-Listen'` fehlgeschlagen.

- [ ] **Step 3: Listen ergänzen**

`tpl-royal`, nach dem `<button class="portal" data-screen="wheel">…</button>` einfügen:

```html
      <button class="portal" data-screen="stud"><span class="portal-crown"></span><span class="plaque">Caribbean Stud</span><span class="glyph">🃏</span><span class="engraved">Ante · Bonus bis 100:1</span></button>
```

`const Royal = {` → `GAMES: ['megaslots', 'craps', 'wheel'],` → `GAMES: ['megaslots', 'craps', 'wheel', 'stud'],`

`RoyalRules` → `SCREENS: ['royal', 'megaslots', 'craps', 'wheel'],` → `SCREENS: ['royal', 'megaslots', 'craps', 'wheel', 'stud'],`

`DevRules` → `ROYAL_SCREENS: ['royal', 'megaslots', 'craps', 'wheel'],` → `ROYAL_SCREENS: ['royal', 'megaslots', 'craps', 'wheel', 'stud'],`

`Story.ROOM_OF`: `… craps: ['royal'], wheel: ['royal'] },` → `… craps: ['royal'], wheel: ['royal'], stud: ['royal'] },`

`STORY_STASH`: `turnoverGroups: { umsatzRoyal: ['megaslots', 'craps', 'wheel'], umsatzHinterzimmer: ['baccarat'] },` → `turnoverGroups: { umsatzRoyal: ['megaslots', 'craps', 'wheel', 'stud'], umsatzHinterzimmer: ['baccarat'] },`

Boot (Block `boot`): `['megaslots', 'craps', 'wheel'].includes(params.get('game'))` → `['megaslots', 'craps', 'wheel', 'stud'].includes(params.get('game'))`

`tests/mobile-check.py`:
- `FREE_SCREENS = [… "royal", "craps", "megaslots", "wheel"]` → am Ende `, "stud"` anhängen.
- Zonen-Schleife `for sc in ["hub", "royal", "craps", "megaslots", "wheel", "stadt"]:` → `["hub", "royal", "craps", "megaslots", "wheel", "stud", "stadt"]`, und in der `record(...)`-Zeile `all(zones[k] == "royal" for k in ["royal", "craps", "megaslots", "wheel"])` → `["royal", "craps", "megaslots", "wheel", "stud"]`.

- [ ] **Step 4: Tests laufen lassen – grün**

Run: `node tests/run-selftest.mjs 2>&1 | tail -3` → 0 Fehler.
Run: `tests/dom-selftest.sh 2>&1 | tail -3` → 0 Fehler (Chip-Test mit `stud`, Portal-Test).
Run: `python3 tests/mobile-check.py 2>&1 | tail -5` → 0 Fehler (Screen `stud` auf 400 px: keine Überbreite, Tap-Ziele ≥ 40 px, Zone `royal`).

- [ ] **Step 5: Commit**

```bash
git add keller37.html tests/mobile-check.py
git commit -m "feat(stud): Lobby-Portal, Royal-Zone, Dev-Panel, Story-3-Umsatz, Boot-Parameter, Mobile-Check

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Browser-Playtest `scenario_stud` und Screenshots

**Files:**
- Modify: `tests/playtest-story.py` – neue Funktion `scenario_stud(cdp)` direkt nach `scenario_poker`, Aufruf in `main()` nach `await scenario_poker(cdp)`
- Modify: `docs/superpowers/screenshots/royal-lobby.png` (erneuern), Create: `docs/superpowers/screenshots/royal-stud.png`

**Interfaces:**
- Consumes: `Stud.forceDeck`, `Stud.round`, `Stud.inRound`, DOM-Ids aus Task 3, `Achievements.has('karibik')`, `State.meta.insider` (Array von Insider-Ids), Playtest-Helfer `record`, `cdp.eval/click/wait_for/screenshot`, `URL_BASE`.

- [ ] **Step 1: Szenario schreiben**

Nach `scenario_poker` einfügen:

```python
async def scenario_stud(cdp):
    """Caribbean Stud im Royal: Portal, festes Deck (Zwei Paare gegen Paar), Mitgehen -> Bonus 2:1, Dealer nicht
    qualifiziert -> Ante 1:1, Passen, Flush -> Achievement, Screen verlassen laesst die Hand fallen, Insider-Blick mit Kappe."""
    await cdp.navigate(URL_BASE + "?fresh&mode=free&screen=royal")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    portal = await cdp.eval("!!document.querySelector('.portal[data-screen=\"stud\"]')", await_promise=False)
    record("stud: Portal in der Royal-Lobby", portal is True)
    await cdp.screenshot("royal-lobby.png")
    await cdp.eval("State.s.car = 'audiA3'; State.s.balance = 1000; State.save(); UI.renderWallet(); 0", await_promise=False)
    await cdp.eval("UI.show('stud'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    zone = await cdp.eval("document.body.dataset.zone", await_promise=False)
    record("stud: Zone royal", zone == "royal", zone)
    # forceDeck wird von oben abwechselnd verteilt: Index 0,2,4,6,8 Spieler, 1,3,5,7,9 Dealer
    def deck_js(player, dealer):
        cards = []
        for p, d in zip(player, dealer):
            cards.append(p); cards.append(d)
        arr = ", ".join("C('%s','%s')" % (c[:-1], c[-1]) for c in cards)
        return ("(function(){ const C = (val, suit) => ({ val, suit }); const top = [%s];"
                " const rest = Rules.newDeck(Math.random).filter(c => !top.some(x => x.val === c.val && x.suit === c.suit));"
                " Stud.forceDeck = [...top, ...rest]; })(); 0") % arr

    async def play(player, dealer, ante, action):
        await cdp.eval(deck_js(player, dealer), await_promise=False)
        await cdp.eval("document.querySelector('.chip[data-chip=\"%d\"]').click(); 0" % ante, await_promise=False)
        before = await cdp.eval("State.s.balance", await_promise=False)
        await cdp.click("#btnStudDeal")
        await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
        after_deal = await cdp.eval("State.s.balance", await_promise=False)
        hidden = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
        if action == "shot":
            await cdp.screenshot("royal-stud.png")
            action = "call"
        await cdp.click("#btnStudCall" if action == "call" else "#btnStudFold")
        await cdp.wait_for("!Stud.inRound", timeout=8.0)
        await asyncio.sleep(0.5)
        after = await cdp.eval("State.s.balance", await_promise=False)
        status = await cdp.eval("document.querySelector('#studStatus').textContent", await_promise=False)
        return before, after_deal, hidden, after, status

    # Trophaeen liegen im Meta-Speicher und ueberleben ?fresh und fruehere Laeufe im selben Chrome-Profil: hier zuruecksetzen
    await cdp.eval("State.meta.achievements = State.meta.achievements.filter(id => id !== 'karibik'); State.saveMeta(); 0", await_promise=False)
    # 1) Zwei Paare gegen Paar 9, Ante 100: Bet 200, Bonus 2:1 -> net +500
    b0, bd, hidden, b1, status = await play(["K♠", "K♥", "7♣", "7♠", "2♥"], ["9♦", "9♣", "5♠", "4♦", "Q♥"], 100, "shot")
    ach = await cdp.eval("Achievements.has('karibik')", await_promise=False)
    record("stud: Geben bucht Ante ab, 4 Dealer-Karten verdeckt, Mitgehen gewinnt Bonus 2:1 (+500)",
           bd == b0 - 100 and hidden == 4 and b1 == b0 + 500 and "Bonus 2:1" in status and ach is False,
           "b0=%s deal=%s hidden=%s b1=%s status=%s ach=%s" % (b0, bd, hidden, b1, status, ach))
    # 2) Dealer A-Q nicht qualifiziert: Ante 1:1, Bet zurueck -> net +100
    b0, bd, hidden, b1, status = await play(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"], 100, "call")
    record("stud: Dealer nicht qualifiziert zahlt Ante 1:1 (+100)", b1 == b0 + 100 and "nicht qualifiziert" in status, "b0=%s b1=%s status=%s" % (b0, b1, status))
    # 3) Passen: Ante weg
    b0, bd, hidden, b1, status = await play(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "K♦", "J♣", "9♥", "2♠"], 100, "fold")
    hidden_after = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
    record("stud: Passen verliert die Ante, Dealer bleibt verdeckt", b1 == b0 - 100 and hidden_after == 4 and "Gepasst" in status, "b0=%s b1=%s hidden=%s status=%s" % (b0, b1, hidden_after, status))
    # 4) Flush gegen Paar -> Achievement
    b0, bd, hidden, b1, status = await play(["2♥", "5♥", "8♥", "J♥", "K♥"], ["9♦", "9♣", "5♠", "4♦", "Q♠"], 100, "call")
    ach = await cdp.eval("Achievements.has('karibik')", await_promise=False)
    record("stud: Flush gewinnt Bonus 5:1 (+1100) und Trophaee Karibische Nacht", b1 == b0 + 1100 and ach is True, "b0=%s b1=%s ach=%s status=%s" % (b0, b1, ach, status))
    # 5) Screen verlassen mitten in der Hand -> Ante verfallen
    await cdp.eval(deck_js(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"]), await_promise=False)
    await cdp.click("#btnStudDeal")
    await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
    before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("UI.show('royal'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    after = await cdp.eval("State.s.balance", await_promise=False)
    in_round = await cdp.eval("Stud.inRound", await_promise=False)
    rnd = await cdp.eval("Stud.round === null", await_promise=False)
    toast = await cdp.eval("document.querySelector('#toasts').textContent.includes('Hand aufgegeben')", await_promise=False)
    record("stud: Screen verlassen laesst die Hand fallen (Ante weg, Toast)", after == before and in_round is False and rnd is True and toast is True,
           "before=%s after=%s inRound=%s round=null:%s toast=%s" % (before, after, in_round, rnd, toast))
    # 6) Insider Sylvies Blick: Ante 100 -> zweite Dealer-Karte offen; Ante 500 -> verdeckt + Hinweis
    await cdp.eval("State.meta.insider = ['sylviesblick']; State.saveMeta(); 0", await_promise=False)
    await cdp.eval("UI.show('stud'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.eval(deck_js(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"]), await_promise=False)
    await cdp.eval("document.querySelector('.chip[data-chip=\"100\"]').click(); 0", await_promise=False)
    await cdp.click("#btnStudDeal")
    await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
    hidden_peek = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
    hint_peek = await cdp.eval("document.querySelector('#studPeek').textContent", await_promise=False)
    await cdp.click("#btnStudFold")
    await cdp.wait_for("!Stud.inRound", timeout=5.0)
    await cdp.eval("State.s.balance = 5000; State.save(); UI.renderWallet(); 0", await_promise=False)
    await cdp.eval(deck_js(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"]), await_promise=False)
    await cdp.eval("document.querySelector('.chip[data-chip=\"500\"]').click(); 0", await_promise=False)
    await cdp.click("#btnStudDeal")
    await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
    hidden_cap = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
    hint_cap = await cdp.eval("document.querySelector('#studPeek').textContent", await_promise=False)
    await cdp.click("#btnStudFold")
    await cdp.wait_for("!Stud.inRound", timeout=5.0)
    record("stud: Sylvies Blick zeigt bei Ante 100 die zweite Dealer-Karte, bei 500 verdeckt mit Kappen-Hinweis",
           hidden_peek == 3 and hint_peek == "🎩 Sylvies Blick" and hidden_cap == 4 and "wirkt bis 250" in hint_cap,
           "hidden100=%s hint100=%s hidden500=%s hint500=%s" % (hidden_peek, hint_peek, hidden_cap, hint_cap))
    await cdp.eval("State.meta.insider = []; State.saveMeta(); 0", await_promise=False)
    # 7) Ante ausserhalb 100-1000: Toast, keine Karten
    await cdp.eval("document.querySelector('#studBet').value = '50'; 0", await_promise=False)
    await cdp.click("#btnStudDeal")
    await asyncio.sleep(0.4)
    cards = await cdp.eval("document.querySelectorAll('#studPlayerCards .pcard').length", await_promise=False)
    toast = await cdp.eval("document.querySelector('#toasts').textContent.includes('Zwischen 100')", await_promise=False)
    in_round = await cdp.eval("Stud.inRound", await_promise=False)
    record("stud: Ante 50 wird abgelehnt", in_round is False and toast is True, "cards=%s toast=%s inRound=%s" % (cards, toast, in_round))
```

Der Insider-Speicher ist `State.meta.insider` (Array von Ids; `Perks.mods()` ruft `Rules.mods(State.s, State.meta)`).

In `main()` nach `await scenario_poker(cdp)` einfügen: `await scenario_stud(cdp)`.

- [ ] **Step 2: Playtest laufen lassen (eigener Port/Profil, die zweite Session könnte parallel testen)**

Run:
```bash
K37_PORT=9372 K37_PROFILE="$TMPDIR/k37-stud-profile" K37_SHOTS="$TMPDIR/k37-stud-shots" python3 tests/playtest-story.py 2>&1 | tail -20
```
(`K37_SHOTS`-Verzeichnis vorher anlegen: `mkdir -p "$TMPDIR/k37-stud-shots"`.)
Expected: alle `stud:`-Checks OK, keine Regression, `ERRORS 0`. Schlägt Check 1 wegen des Kontostands fehl, zuerst die Reihenfolge im `forceDeck` prüfen (Spieler = gerade Indizes).

- [ ] **Step 3: Screenshots übernehmen**

```bash
python3 -c "import shutil,os; d=os.environ['TMPDIR']+'/k37-stud-shots'; shutil.copyfile(d+'/royal-lobby.png','docs/superpowers/screenshots/royal-lobby.png'); shutil.copyfile(d+'/royal-stud.png','docs/superpowers/screenshots/royal-stud.png')"
```

Beide Bilder mit dem Read-Tool ansehen: Lobby zeigt vier Portale (3 + 1), Stud-Tisch zeigt fünf Spielerkarten, eine offene und vier verdeckte Dealer-Karten, Bogen „Ante 100 €", Buttons „Mitgehen (200 €)" / „Passen" in Royal-Gold.

- [ ] **Step 4: Komplettlauf**

```bash
node tests/run-selftest.mjs 2>&1 | tail -3
tests/dom-selftest.sh 2>&1 | tail -3
python3 tests/mobile-check.py 2>&1 | tail -3
```
Expected: überall 0 Fehler.

- [ ] **Step 5: Commit**

```bash
git add tests/playtest-story.py docs/superpowers/screenshots/royal-lobby.png docs/superpowers/screenshots/royal-stud.png
git commit -m "test(stud): Playtest-Szenario Caribbean Stud, Screenshots Lobby und Tisch

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review (durchgeführt beim Schreiben)

- **Spec-Abdeckung:** 2.1 Einsätze → T3 `deal()` + Template; 2.2 Ablauf → T3; 2.3/2.4 → T1; 3.1 Glück → T1 + T3 (`luckOverride` im `deal()`); 3.2 Insider → T2 + T3 (`peek`, `#studPeek`); 3.3 Achievement → T2; 3.4 Royal-Mechanik → T3 (`Game.settle` mit `game: 'stud'`), Royal-Sperre über Lobby unverändert; 4.1 Portal → T4; 4.2/4.3/4.4 → T3; 5 Listen → T4; 6.1 Selftests → T1/T2/T4 (+ DOM-Geldfluss T3); 6.2 Playtest → T5; 6.3 Lauf → T5 Schritt 4.
- **Platzhalter:** keine.
- **Typ-Konsistenz:** `StudRules.settle` liefert `{ outcome, net, bonus }` und wird in T3 so gelesen; `luckOverride(hands, luck, rng)` nimmt/gibt `{ player, dealer, deck }`; `stud:result`-Payload in T2-Test und T3 identisch (`outcome, player, dealer, ante, net`); DOM-Ids in Template, Modul, DOM-Test und Playtest identisch (`studBet`, `btnStudDeal`, `btnStudCall`, `btnStudFold`, `studDealerCards`, `studPlayerCards`, `studHandName`, `studDealerName`, `studPeek`, `studStatus`, `studArc`, `studBack`).
- **Bekannte Abweichung von der Spec (dort schon nachgezogen):** feste Chips 100/250/500/1000 mit nur lesbarem Feld statt „MAX", Leertaste statt Enter/Esc – beides Royal-Konvention.
