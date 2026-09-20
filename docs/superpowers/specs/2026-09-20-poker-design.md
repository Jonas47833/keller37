# KELLER 37 – Poker gegen den Wirt

Datum: 2026-09-20 · Status: abgestimmt · Basis: `keller37.html` @ `95b70ce` (main)

## 1. Ziel

Ein neues Spiel im Keller-Hub: **Five-Card Draw, Heads-up gegen den Wirt**, mit einer einzigen Setzrunde nach dem Tausch. Der Wirt ist ein echter Gegner (tauscht, setzt, blufft, steigt aus), aber die Regeln bleiben so knapp, dass der Spieler nie mehr als zwei Buttons gleichzeitig sieht.

Dazu drei Anbindungen an bestehende Systeme: Glück wirkt beim Tausch, ein neunter XP-Skill („Kartenhai"), ein achter Insider („Wirts Tell"), und ein Achievement.

Nicht Teil dieser Spec: Poker im Casino Royal oder Hinterzimmer, Story-Szenen am Pokertisch, Überfall-/Nachtkasse-Anbindung in Story 3, mehrere Gegner.

## 2. Regeln

### 2.1 Einsätze

- **Ante** = Wert des Einsatzfelds (Standard 10 €, Minimum 1 €). Beide Seiten zahlen das Ante in den Pot.
- Jeder weitere Einsatz (Setzen, Erhöhen, Mitgehen) ist **genau 1× Ante**.
- Pot-Maximum: 2 Antes + Setzen + Erhöhen + Mitgehen = **6× Ante** (Spieler-Risiko: 3× Ante).
- Vor dem Geben: `balance ≥ 3 × Ante` (Ante + Setzen + Mitgehen), sonst Toast „Zu wenig für diesen Tisch – du brauchst 3× Ante." Das Einsatzfeld wird wie bei Blackjack per `Game.bindBet(root, 'pokerBet', maxFn)` gebunden, `maxFn = () => Math.floor(Rules.maxBet(State.s, mods) / 3)`.

### 2.2 Ablauf einer Runde

1. **Geben.** Frisches 52er-Deck (`Rules.newDeck(Math.random)`). Spieler 5 offen, Wirt 5 verdeckt. Ante wird abgebucht (`Game.beginSpin(ante)`; Wirt-Ante ist virtuell, nur im Pot).
2. **Tausch.** Spieler markiert 0–3 Karten (Antippen), Button „Tauschen" (bei 0 markierten „Behalten"). Neue Karten vom Deck. Danach tauscht der Wirt verdeckt nach `PokerRules.wirtDraw`; Anzeige „Der Wirt tauscht N" (N = 0–3).
3. **Setzrunde.** Spieler beginnt: **Setzen** (1× Ante, wird sofort abgebucht) oder **Checken**.
   - Spieler hat gesetzt → Wirt: *mitgehen* (→ Showdown), *erhöhen* (1× Ante mehr) oder *aussteigen* (→ Spieler gewinnt Pot).
   - Spieler hat gecheckt → Wirt: *setzen* oder *checken* (→ Showdown).
   - Hat der Wirt gesetzt oder erhöht → Spieler: **Mitgehen** (1× Ante, sofort abgebucht → Showdown) oder **Aussteigen** (Pot an Wirt).
   - Keine weitere Erhöhung. Nach der Spieler-Antwort ist die Setzrunde vorbei.
4. **Showdown.** Wirt deckt auf. Bessere Hand nimmt den Pot; Gleichstand teilt (halber Pot zurück, ungerader Cent an den Spieler gerundet: `Math.ceil(pot / 2)`).

### 2.3 Handbewertung

`PokerRules.evaluate(cards)` → `{ rank, name, tiebreak }`:

| rank | name | tiebreak |
|---|---|---|
| 0 | High Card | Kartenwerte absteigend |
| 1 | Paar | Paarwert, dann Kicker absteigend |
| 2 | Zwei Paare | hohes Paar, niedriges Paar, Kicker |
| 3 | Drilling | Drillingswert, Kicker |
| 4 | Straße | höchste Karte (A-2-3-4-5 → 5) |
| 5 | Flush | Kartenwerte absteigend |
| 6 | Full House | Drillingswert, Paarwert |
| 7 | Vierling | Vierlingswert, Kicker |
| 8 | Straight Flush | höchste Karte (Royal = 14) |

Kartenwerte: 2–10 numerisch, J 11, Q 12, K 13, A 14. Straße A-2-3-4-5 zählt als Straße mit Höchstwert 5.

`PokerRules.compare(a, b)` → −1 / 0 / 1: erst `rank`, dann `tiebreak` elementweise.

## 3. Der Wirt

Alle Funktionen in `PokerRules`, DOM-frei, `rng` als Parameter.

### 3.1 Tausch `wirtDraw(hand)` → Array der Indizes, die getauscht werden (max. 3)

Feste Reihenfolge, erste zutreffende Regel gilt:

1. Straße, Flush, Full House, Vierling, Straight Flush → `[]`.
2. Drilling → die zwei anderen. Zwei Paare → die eine. Paar → die drei anderen.
3. Vier Karten einer Farbe → die fünfte. Vier aufeinanderfolgende Werte (offen, z. B. 5-6-7-8) → die fünfte.
4. Sonst → die drei niedrigsten.

### 3.2 Setzen `wirtAct(hand, situation, rng)` → `'call' | 'raise' | 'fold' | 'bet' | 'check'`

`situation` ist `'facingBet'` (Spieler hat gesetzt) oder `'checked'` (Spieler hat gecheckt). Klassen nach `evaluate(hand).rank`:

| Klasse | facingBet | checked |
|---|---|---|
| stark (rank ≥ 2) | raise | bet |
| mittel (rank = 1) | call | bet |
| schwach (rank = 0) | `rng() < BLUFF_RAISE` → raise, sonst fold | `rng() < BLUFF_BET` → bet, sonst check |

Konstanten `PokerRules.WIRT = { BLUFF_RAISE: 0.2, BLUFF_BET: 0.3 }`. Genau ein `rng`-Aufruf nur in der schwachen Klasse.

### 3.3 Abrechnung `payout(pot, outcome)` → Bruttobetrag aus dem Pot für den Spieler

`outcome` ∈ `'win' | 'lose' | 'split'`: `win → pot`, `lose → 0`, `split → Math.ceil(pot / 2)`.

Konvention wie bei Blackjack: Die Einsätze des Spielers sind bereits abgebucht (`Game.beginSpin` fürs Ante, `Game.applyDelta` für Setzen/Mitgehen). `Game.settle(delta, { bet })` bucht `delta + bet` zurück – das Modul ruft `Game.settle(payout − playerIn, { bet: playerIn, … })`, wobei `playerIn` die Summe der Spieler-Einsätze in dieser Runde ist. Das Netto `payout − playerIn` ist zugleich der Wert für Toast und Statistik.

## 4. Systeme

### 4.1 Glück

`PokerRules.luckOverride(before, after, drawFn, luck, rng)`:
- `before`/`after` sind `evaluate`-Ergebnisse vor und nach dem Tausch, `drawFn()` zieht die Ersatzkarten erneut und gibt die neue Hand zurück.
- `luck > 0` und `compare(after, before) <= 0` (keine Verbesserung) → mit `luck` % (ein `rng`-Aufruf) einmal `drawFn()`.
- `luck < 0` und `compare(after, before) > 0` (Verbesserung) → mit `Rules.pech(luck, rng)` einmal `drawFn()`.
- Sonst unverändert. Es gibt nur einen Neuzug, kein zweites Würfeln.
- `luck` = `Rules.effectiveLuck(Rules.luck(State.s, mods), ante)`.

Die Ersatzkarten für den Neuzug kommen vom selben Deck (weiter oben abgehoben); die zuerst gezogenen gehen nicht zurück ins Deck.

### 4.2 Skill „Kartenhai" 🦈

```js
{ id: 'kartenhai', name: 'Kartenhai', icon: '🦈',
  light: 'Poker: du siehst, wie viele Karten der Wirt tauschen wird, bevor du tauschst',
  shadow: 'Blackjack: Dealer zieht bis 18',
  mods: { pokerPeekDraw: true, bjDealerStand: 18 } }
```

- `NEUTRAL_MODS`: `pokerPeekDraw: false`, `bjDealerStand: 17`. `MOD_STACK`: `pokerPeekDraw: 'set'`, `bjDealerStand: 'max'`.
- `Rules.dealerShouldHit(hand, stand = 17)` bekommt den Stand-Wert als zweiten Parameter; Blackjack ruft `Rules.dealerShouldHit(round.dHand, mods.bjDealerStand)`. Der Blackjack-Bogen (`#bjArc`) zeigt „Dealer zieht bis 18", wenn aktiv.
- Kein `excludes`.

### 4.3 Insider „Wirts Tell" 🧔

```js
{ id: 'wirtstell', name: 'Wirts Tell', icon: '🧔',
  text: 'Poker: der Wirt kratzt sich am Bart, wenn er nichts auf der Hand hat.',
  capped: true, mods: { pokerTell: true } }
```

- `NEUTRAL_MODS`: `pokerTell: false`; `MOD_STACK`: `'set'`.
- Anzeige im `insider-hint` neben dem Wirt-Label, nach dem Wirt-Tausch und vor der Spieler-Entscheidung: `Rules.effectiveInsider(mods.pokerTell, ante)` → wahr: rank 0 → „🧔 Der Wirt kratzt sich am Bart", sonst „🧔 Der Wirt trinkt einen Schluck". Bei Ante > 250 €: „🧔 Wirts Tell: wirkt bis 250 €".
- Der Tell bezieht sich auf die Hand **nach** dem Wirt-Tausch.
- `insiderDraw`-Pool wächst auf 8. Der bestehende Test `insiderDraw: 3 ungezogene, weniger wenn Pool kleiner` zieht mit `all.slice(0, 5)` und erwartet 2 – er wird auf `all.slice(0, 6)` angepasst. Der Playtest-Check „8 Skills wählbar" wird auf 9 angepasst.

### 4.4 Achievement

`{ id: 'fullhouse', title: 'Full House', icon: '🏠', desc: 'Mit Full House oder besser den Showdown gewonnen.' }` – über `Bus.on('poker:result', ({ outcome, showdown, player }) => …)` mit `showdown && outcome === 'win' && player.rank >= 6`.

`Bus.emit('poker:result', { outcome, showdown, player, wirt, pot, ante })` nach jeder Runde (`outcome` ∈ win/lose/split, `showdown` boolean, `player`/`wirt` = `evaluate`-Ergebnisse, `wirt` null ohne Showdown).

## 5. Tisch (UI)

### 5.1 Tür

Im Hub-Template nach der Blackjack-Tür:

```html
<div class="door" data-screen="poker" style="--neon: var(--neon-green)"><div class="sign">Poker</div><div class="glyph">♠️</div><div class="chalk-tag">Draw · gegen den Wirt</div><div class="knob"></div></div>
```

### 5.2 Screen `poker` (Template `tpl-poker`)

Aufbau wie `tpl-blackjack` (`.panel.felt`), Klassen `pk-*`:

- **Wirt-Hand** oben: `#pkWirtCards` (5 `pcard` mit `hidden-card`, beim Showdown umgedreht wie die Blackjack-Hole-Card), Label „Der Wirt", darin `#pkWirtDraw` („tauscht 2") und `#pkTell` (`insider-hint hidden`).
- **Mitte**: `#pkPot` („Pot · 20 €"), `#pkStatus` (Statuszeile).
- **Spieler-Hand** unten: `#pkPlayerCards`; Karten antippbar, Klasse `picked` hebt die Karte 12 px und gibt gelben Rand; Label „Du" mit `#pkHandName` (Handname nach `evaluate`, live beim Geben und nach dem Tausch).
- **Leiste**: `#pkBetControls` (Einsatzfeld `#pkBet` + „Geben" `#btnPkDeal`), `#pkDrawControls` („Tauschen/Behalten" `#btnPkDraw`), `#pkBetRound` („Setzen" `#btnPkBet`, „Checken" `#btnPkCheck`), `#pkCallRound` („Mitgehen" `#btnPkCall`, „Aussteigen" `#btnPkFold`). Immer nur eine Gruppe sichtbar.
- Kartenelemente: `Blackjack.cardEl` wird zu `UI.cardEl(c, hidden)` (Blackjack ruft die neue Stelle auf; keine Kopie).
- Kartenhai: sobald der Spieler seine Karten sieht, steht bei aktivem `pokerPeekDraw` im Wirt-Label „wird 2 tauschen" (aus `wirtDraw(wirtHand).length`) – das ist die Lichtseite.

### 5.3 Statustexte

| Phase | `#pkStatus` |
|---|---|
| vor dem Geben | „Ante setzen" |
| Tausch | „Welche Karten tauschen? (bis zu 3)" |
| Setzrunde | „Setzen oder checken?" |
| Wirt hat gesetzt | „Der Wirt setzt {ante}. Mitgehen?" |
| Wirt hat erhöht | „Der Wirt erhöht auf {2×ante}. Mitgehen?" |
| Wirt steigt aus | „Der Wirt wirft hin · +{netto}" (win-Klasse) |
| Spieler steigt aus | „Aufgegeben · −{playerIn}" (loss-Klasse) |
| Showdown gewonnen | „{Handname} schlägt {Wirt-Handname} · +{netto}" |
| Showdown verloren | „{Wirt-Handname} schlägt {Handname} · −{playerIn}" |
| Split | „Geteilt · {Handname} gegen {Handname}" |

Wirt-Aktionen werden mit `wait(500)` verzögert, damit man sie als Zug wahrnimmt; Karten-Ausgabe mit `SFX.play('cardSlide')` und `wait(180)` je Karte.

### 5.4 Modul `Poker`

Script-Block `game-poker` nach `game-blackjack`. Struktur wie `Blackjack`: `root, gen, round, inRound, busy`, `alive(gen)`, `drop(round)` (→ `Game.forfeit()`), `UI.register('poker', { template: 'tpl-poker', mount, unmount })`. Beim `unmount` mitten in der Runde: Toast „Hand aufgegeben · Einsatz verfallen" (wie Blackjack). `round` hält `deck, pHand, wHand, ante, pot, playerIn, picked (Set), phase, gen, run`.

Geldfluss:
- Geben: `Game.beginSpin(ante)` (bucht Ante ab). `pot = 2 × ante`, `playerIn = ante`.
- Setzen / Mitgehen: `Game.applyDelta(-ante, { quiet: true })`, `pot += ante`, `playerIn += ante`. Der Wirt-Einsatz erhöht nur `pot`.
- Ende: `Game.settle(PokerRules.payout(pot, outcome) − playerIn, { from: #pkPlayerCards, game: 'poker', bet: playerIn, run })`.

## 6. Story-Anbindung

- `Story.DOORS` um `'poker'` ergänzen (Reihenfolge: nach `'blackjack'`).
- Story 1 „Die Schuld": Kapitel 2 `unlock.doors` → `['roulette', 'blackjack', 'russian', 'poker']`; Kapitel 4 → alle sechs.
- Story 2 „Der Kater" und Story 3 „Die Wäsche": `start.unlocked.doors` → alle sechs.
- Story-Probe (`STORY_PROBE`) bleibt unverändert.
- `DevRules.KELLER_SCREENS` (Gruppierung im Admin-Panel) bekommt `'poker'` nach `'blackjack'`.
- **Nicht** in `GangRules.KELLER_DOORS`/`GangRules.REPAIR` (Story 3: kein Überfallziel, keine Nachtkasse, nicht zertrümmerbar), **aber** in `Mugging.CASINO`, weil diese Liste die Überfälle im freien Spiel beim Betreten einer Keller-Tür steuert und Poker nicht die einzige sichere Tür sein soll.
- Die zwei Selftests, die `unlocked.doors` exakt vergleichen (Story 2/3 Start), werden um `'poker'` ergänzt.

## 7. Tests

### 7.1 Selftests (`T.test`, Block `selftest`)

- `evaluate`: je ein Fall pro Rang inkl. Rad-Straße (A-2-3-4-5 → rank 4, tiebreak [5]) und Royal (rank 8, tiebreak [14]); Kicker-Reihenfolge bei Paar/Zwei Paaren.
- `compare`: höherer Rang gewinnt; gleicher Rang → Kicker; identische Hände → 0.
- `wirtDraw`: Paar → 3 Indizes der Nicht-Paar-Karten; Zwei Paare → 1; Flush-Draw → die eine falsche Farbe; Müll → drei niedrigste; Straße → `[]`.
- `wirtAct`: stark/facingBet → raise; mittel/checked → bet; schwach/facingBet mit `seq(0.1)` → raise, `seq(0.5)` → fold; schwach/checked `seq(0.2)` → bet, `seq(0.9)` → check.
- `payout`: win → pot, lose → 0, split → ceil(pot/2).
- `luckOverride`: keine Verbesserung + luck 100 → drawFn aufgerufen; Verbesserung + luck 100 → nicht; Verbesserung + luck −100 → aufgerufen; luck 0 → nie.
- `dealerShouldHit(hand, 18)`: 17 zieht, 18 steht; ohne Parameter wie bisher.
- `mods`: Kartenhai liefert `pokerPeekDraw: true, bjDealerStand: 18`; Wirts Tell `pokerTell: true`; neutral `false`/`17`/`false`.

### 7.2 Browser-Playtest (`tests/playtest-story.py`)

- Freies Spiel: Tür `poker` im Hub sichtbar, Screen mountet, „Geben" bei Ante 10 bucht 10 ab, 5 Spielerkarten sichtbar, Wirt-Karten verdeckt.
- Deck erzwingen über `Poker.round.deck` ist zu spät (schon gegeben) → Modul bietet `Poker.forceDeck = [...]` (nur gesetzt, wenn vorhanden; Dev-Hilfe wie `Mugging.force`). Test legt Full House für Spieler, Paar für Wirt, tauscht 0, setzt, Wirt geht mit (rank 1 → call), Showdown: Kontostand +20 gegenüber vor der Runde, Achievement `fullhouse` freigeschaltet.
- Screenshot `poker.png`; Mobile-Check (`tests/mobile-check.py`, Screen `poker` in `FREE_SCREENS`): keine Überbreite, Karten ≥ 40 px Tap-Ziel.

### 7.3 Lauf

`node tests/run-selftest.mjs`, `sh tests/dom-selftest.sh`, `python3 tests/playtest-story.py`, `python3 tests/mobile-check.py`.
