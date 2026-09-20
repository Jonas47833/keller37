# KELLER 37 – Caribbean Stud im Casino Royal

Datum: 2026-09-20 · Status: abgestimmt · Basis: `keller37.html` @ `2824e7e` (main)

## 1. Ziel

Ein viertes Spiel im **Casino Royal**: **Caribbean Stud Poker** gegen das Haus (Madame Sylvie). Ante setzen, fünf Karten, eine Dealer-Karte offen, dann Mitgehen (2× Ante) oder Passen. Der Dealer muss sich mit Ass-König qualifizieren; gewinnt der Spieler gegen einen qualifizierten Dealer, zahlt der Einsatz nach Bonus-Tabelle bis 100:1.

Dazu zwei Anbindungen an bestehende Systeme: Glück wirkt beim Geben (Baccarat-Muster), ein neunter Insider („Sylvies Blick"), und ein Achievement.

Erstes von drei geplanten Royal-Spielen (danach Sic Bo, Three Card Poker – jeweils eigene Spec).

Nicht Teil dieser Spec: Jackpot-Nebenwette, neuer Skill, Story-Szenen am Stud-Tisch, Änderungen an Poker/Blackjack/Craps, Änderungen an der Royal-Optik.

## 2. Regeln

### 2.1 Einsätze

- **Ante** = Wert des Einsatzfelds, **100 € bis 1.000 €** (`StudRules.ANTE = { MIN: 100, MAX: 1000 }`). Außerhalb des Bereichs: Toast „Einsatz – Zwischen 100 € und 1.000 €." (Craps-Konvention), keine Hand.
- **Bet = 2 × Ante**, fest. Maximales Risiko pro Hand: 3× Ante.
- Vor dem Geben: `Rules.checkSpin(State.s, 3 * ante, Perks.mods())` (Ante + Bet inkl. Zinsen/Medikamente). Bei `reason === 'funds'` Toast „Zu wenig für diesen Tisch – du brauchst 3× Ante."; andere Gründe wie überall über `Game.beginSpin`.
- Einsatzfeld: `Game.bindBet(root, 'studBet', () => Math.min(StudRules.ANTE.MAX, Math.floor(Rules.maxBet(State.s, Perks.mods()) / 3)))`, Chips 100 / 250 / 500 / MAX, Startwert 100.

### 2.2 Ablauf einer Hand

1. **Geben.** Frisches 52er-Deck (`Rules.newDeck(Math.random)`, in Tests `Stud.forceDeck`). Ante wird abgebucht (`Game.beginSpin(ante)`). Spieler 5 Karten offen, Dealer 5 Karten – nur die erste offen (mit Insider und Ante ≤ 250 €: die ersten zwei). Glücks-Eingriff siehe 3.1 – passiert vor der Anzeige.
2. **Entscheidung.** **Mitgehen** (`Game.applyDelta(-2 * ante)`, sofort abgebucht) oder **Passen** (Ante verloren, Hand beendet ohne Aufdecken).
3. **Showdown.** Dealer-Karten werden nacheinander aufgedeckt. Abrechnung nach 2.4.

### 2.3 Handbewertung und Qualifikation

Handbewertung ist `PokerRules.evaluate(cards)` → `{ rank 0–8, name, tiebreak }` (unverändert). Stud-Rang in der Bonus-Tabelle: `rank`, Royal Flush = `rank 8 && tiebreak[0] === 14`.

`StudRules.qualifies(hand)` → `true`, wenn `evaluate(hand).rank >= 1` **oder** (`rank === 0` und `tiebreak[0] === 14 && tiebreak[1] === 13`). A-K-x-x-x qualifiziert, A-Q-J-10-8 nicht.

### 2.4 Abrechnung `StudRules.settle(player, dealer, ante)` → `{ outcome, net, bonus }`

`player`/`dealer` sind Kartenarrays. `net` ist der Nettobetrag für den Spieler (bezogen auf Ante + Bet = 3× Ante Einsatz):

| Fall | `outcome` | `bonus` | `net` |
|---|---|---|---|
| Dealer nicht qualifiziert | `'noqual'` | 0 | `+ante` (Ante 1:1, Bet zurück) |
| Dealer qualifiziert, Spieler besser | `'win'` | Tabelle | `ante + 2 * ante * bonus` |
| Dealer qualifiziert, gleich | `'push'` | 0 | `0` |
| Dealer qualifiziert, Dealer besser | `'lose'` | 0 | `-3 * ante` |

Passen wird nicht über `settle` abgerechnet: `net = -ante`, `outcome = 'fold'`.

**Bonus-Tabelle** `StudRules.BONUS = [1, 1, 2, 3, 4, 5, 7, 20, 50]` (Index = `rank`: High Card, Paar, Zwei Paare, Drilling, Straße, Flush, Full House, Vierling, Straight Flush), `StudRules.ROYAL_BONUS = 100`. `StudRules.bonus(hand)` liefert den Faktor (Royal Flush → 100).

Beispiel Ante 200: Zwei Paare gegen Paar → `net = 200 + 400 · 2 = 1.000 €`; Dealer nicht qualifiziert → `+200 €`; verloren → `−600 €`.

## 3. Systeme

### 3.1 Glück (`StudRules.luckOverride(hands, luck, rng)`)

Baccarat-Muster, ein einziger Eingriff beim Geben, bevor der Spieler etwas sieht:

- `hands = { player, dealer, deck }` (Zustand nach dem Geben). Bewertet wird `settle(player, dealer, ante).net` mit Ante 1 (nur das Vorzeichen zählt – „als würde der Spieler mitgehen").
- `luck > 0` und `net < 0`: mit `luck` % (`rng() * 100 < luck`) werden **beide** Hände einmal neu vom restlichen Deck gegeben (`StudRules.deal(deck)` erneut, Deck wird nicht neu gemischt).
- `luck < 0` und `net > 0`: mit `|luck|` % (`Rules.pech(luck, rng)`) einmal neu gegeben.
- Sonst unverändert. Höchstens ein RNG-Aufruf, höchstens ein Neugeben.
- Wirksames Glück: `Rules.effectiveLuck(Rules.luck(State.s, mods), ante)`. `LUCK_CAP` ist 1.000 €, im Ante-Bereich wirkt Glück also voll.

`StudRules.deal(deck)` → `{ player: 5 Karten, dealer: 5 Karten, deck: Rest }`; gibt abwechselnd Spieler/Dealer von oben (`deck[0]`, `deck[1]`, …), damit `forceDeck` im Test lesbar bleibt: Karten 0,2,4,6,8 Spieler, 1,3,5,7,9 Dealer.

### 3.2 Insider „Sylvies Blick" 🎩

`Rules.INSIDER` bekommt als neunten Eintrag:

```js
{ id: 'sylviesblick', name: 'Sylvies Blick', icon: '🎩',
  text: 'Caribbean Stud: Madame Sylvie lässt dich eine zweite Dealer-Karte sehen, bevor du mitgehst.',
  capped: true, mods: { studPeek: true } }
```

- `Rules.NEUTRAL_MODS.studPeek = false`, `MOD_STACK.studPeek = 'set'`.
- Wirkung: `Rules.effectiveInsider(mods.studPeek, ante)` wahr → Dealer-Karte 2 wird beim Geben offen gelegt (kein `hidden-card`).
- Ante > 250 € (`Rules.INSIDER_CAP`): Karte bleibt verdeckt; im Dealer-Label steht „🎩 Sylvies Blick: wirkt bis 250 €" (Element `#studPeek`, Klasse `insider-hint`, Konvention wie `#pkTell`).
- Ohne Insider: kein Hinweis-Element sichtbar.
- Insider-Katalog: 9 Einträge; Angebot bleibt „Eins pro Kapitel" (Selftest `insiderDraw` und Katalog-Zählungen werden angepasst).

### 3.3 Achievement

```js
{ id: 'karibik', title: 'Karibische Nacht', icon: '🌴', desc: 'Bei Caribbean Stud mit Flush oder besser gegen einen qualifizierten Dealer gewonnen.' }
```

`Bus.on('stud:result', ({ outcome, player }) => { if (outcome === 'win' && player.rank >= 5) Achievements.unlock('karibik'); })`. Event-Payload: `{ outcome, player: evaluate(pHand), dealer: evaluate(dHand), ante, net }` – wird bei jedem Ergebnis inkl. `'fold'` gesendet.

### 3.4 Royal-Mechanik

- `Game.settle(net, { from, game: 'stud', bet: eingesetzt, run })` – `bet` = `ante` beim Passen, `3 * ante` nach Mitgehen. Damit laufen Gewinn-Flash, `Bus 'win'` (→ `Royal.onWin`, „Gast des Hauses" ab 5.000 € Nettogewinn, Erfolg `royalHigh`) und Story-Umsatz mit.
- Eintritt, Auto-Pflicht und Story-Sperre laufen über die Royal-Tür (`Royal.enter`); der Stud-Screen ist nur aus der Lobby erreichbar. Keine Änderung an `Story.DOORS`, Kapitel-Türlisten oder `Mugging.CASINO`.

## 4. Tisch (UI)

### 4.1 Lobby-Portal (`tpl-royal`)

Vierte Kachel nach dem Glücksrad:

```html
<button class="portal" data-screen="stud"><span class="portal-crown"></span><span class="plaque">Caribbean Stud</span><span class="glyph">🃏</span><span class="engraved">Ante · Bonus bis 100:1</span></button>
```

Das bestehende Raster (`.deco-portals`, 3 Spalten, Handy 2) bricht in eine zweite Reihe um – kein neues CSS.

### 4.2 Screen `stud` (Template `tpl-stud`)

Aufbau wie `tpl-poker` (Filz-Tisch, `bj-panel`), Royal-Zone färbt über `body[data-zone="royal"]`:

- Dealer-Reihe: Label „Madame Sylvie" + `<span class="hand-val" id="studDealerName"></span>` + `<span class="insider-hint hidden" id="studPeek"></span>`, Karten `#studDealerCards`.
- Bogen `#studArc`: „Ante · –" / „Ante 200 €" / „Ante 200 € · Bet 400 €".
- Spieler-Reihe: Karten `#studPlayerCards`, Label „Du" + `<span class="hand-val" id="studHandName">–</span>`.
- Status `#studStatus`.
- `#studBetControls`: `bet-field` mit `#studBet` (value 100, min 100), Chips 100/250/500/MAX, `#btnStudDeal` „Geben".
- `#studCallControls` (hidden): `#btnStudCall` „Mitgehen (400 €)" (Betrag wird gesetzt), `#btnStudFold` „Passen".
- `#studBack` „← Lobby" (`btn ghost sm`, wie `#crapsBack`).

Karten über `UI.cardEl(c, hidden)` mit Deal-Animation; Dealer-Karten 2–5 `hidden-card` (Karte 2 offen bei wirksamem Insider). Aufdecken im Showdown: `hidden-card` nacheinander entfernen, `SFX.play('cardSlide')`, 160 ms Abstand (Konvention Poker-Showdown). Dealer-Handname erscheint nach dem Aufdecken: `PokerRules.NAMES[rank]` oder „qualifiziert sich nicht".

### 4.3 Statustexte

| Situation | `#studStatus` |
|---|---|
| Leer | „Ante setzen" |
| Nach Geben | „Mitgehen (400 €) oder passen?" |
| Gepasst | „Gepasst · −200 €" |
| Nicht qualifiziert | „Dealer nicht qualifiziert (A-K nötig) · +200 €" |
| Gewonnen | „Zwei Paare schlägt Paar · Bonus 2:1 · +1.000 €" |
| Push | „Gleichstand · Push" |
| Verloren | „Drilling schlägt Zwei Paare · −600 €" |

Beträge über `UI.fmt`. Gewinn-Status mit Klasse `win`, Verlust `loss` (bestehende Status-Konvention aus Poker).

### 4.4 Modul `Stud`

Nach dem Muster von `Poker`: `root, gen, round, busy, forceDeck, alive(gen), drop(round)`, Methoden `deal()`, `call()`, `fold()`, `showdown(round)`, `finish(round, outcome, net)`, `onKey(e)` (Enter = Geben bzw. Mitgehen, Esc = Passen bei laufender Hand, sonst Lobby), `show(group)` für die Button-Leisten.

`UI.register('stud', { template: 'tpl-stud', mount, unmount })`: `unmount` bricht eine laufende Hand ab (`drop` → `Game.forfeit()`, Toast „Hand aufgegeben · Einsatz verfallen"), außer während `busy` (Showdown läuft zu Ende, Auszahlung erfolgt ohne Screen). `Stud.round = null` danach.

Verlassen über Seitenleiste/Logo/Esc läuft durch `Royal.confirmLeave` wie bei den anderen Royal-Spielen (Eintritt-Nachfrage), zusätzlich der Forfeit aus `unmount`.

## 5. Listen und Einbindung

Alle bekommen `'stud'`:

- `Royal.GAMES` → `['megaslots', 'craps', 'wheel', 'stud']`
- `RoyalRules.SCREENS` → `['royal', 'megaslots', 'craps', 'wheel', 'stud']` (Zone, Gold-Vorhang)
- `DevRules.ROYAL_SCREENS` (Dev-Panel Screen-Sprung)
- `ROOM_OF.stud = ['royal']`
- `STORY_STASH.turnoverGroups.umsatzRoyal` (Story 3) und die gleichnamige Selftest-Fixture
- Boot-Parameter `?screen=royal&game=stud`
- `tests/run-selftest.mjs`: Block `'stud-rules'` nach `'poker-rules'`
- `tests/mobile-check.py`: `FREE_SCREENS` + Zonen-Check (`zones['stud'] === 'royal'`), `TAP_SELECTORS` unverändert (keine tippbaren Karten)

Neue Script-Blöcke: `<script id="stud-rules">` nach `poker-rules` (DOM-frei, nutzt `PokerRules` und `Rules`), `<script id="game-stud">` nach `game-poker`.

## 6. Tests

### 6.1 Selftests (Block `selftest`)

- `qualifies`: A-K-9-5-2 ja; A-Q-J-9-2 nein; K-Q-J-9-2 nein; Paar 2-2 ja.
- `bonus`: Paar → 1, Zwei Paare → 2, Full House → 7, Straight Flush 9-K → 50, Royal → 100.
- `settle` Ante 200: noqual → `+200`; Zwei Paare vs. Paar → `outcome 'win', bonus 2, net 1000`; Paar vs. gleiches Paar mit gleichen Kickern → `push, 0`; Paar vs. Drilling → `lose, −600`; Royal vs. Paar → `net = 200 + 400·100 = 40200`.
- `deal(deck)`: 10 Karten abwechselnd, Rest im Deck.
- `luckOverride`: Verlusthand, `luck 50`, `seq(0.1)` → neu gegeben (andere Karten); `seq(0.9)` → unverändert; Gewinnhand mit `luck −50`, `seq(0.1)` → neu gegeben; Gewinnhand mit `luck 50` → unverändert, kein RNG-Aufruf.
- Katalog: `Rules.INSIDER.length === 9`, `sylviesblick` vorhanden, `NEUTRAL_MODS.studPeek === false`, `MOD_STACK.studPeek === 'set'`, `insiderDraw` liefert weiterhin 3 ungezogene (Test mit 9er-Katalog).
- Listen: `Royal.GAMES`, `RoyalRules.SCREENS`, `DevRules.ROYAL_SCREENS`, `turnoverGroups.umsatzRoyal` enthalten `stud`; `zoneFor('stud') === 'royal'`.
- Achievement `karibik` im Katalog; `stud:result` mit `win` + `rank 5` schaltet frei, mit `rank 4` nicht.
- DOM-Selftest: Chip-Leiste `['stud', 'studBet', '100', '500']` in der bestehenden Royal-Chip-Prüfung.

### 6.2 Browser-Playtest (`tests/playtest-story.py`, `scenario_stud(cdp)`)

Freies Spiel, Auto vorhanden, Royal betreten, `Stud.forceDeck` gesetzt (Reihenfolge nach 3.1: gerade Indizes Spieler, ungerade Dealer):

1. Ante 200, Spieler K♠ K♥ 7♣ 7♠ 2♥, Dealer 9♦ 9♣ 5♠ 4♦ Q♥ → nach Geben Konto −200, vier Dealer-Karten `hidden-card`; Mitgehen → Konto −600, Auszahlung +1.600 (`net` + Einsatz) → Konto +1.000 gegenüber Start; Status „Zwei Paare schlägt Paar · Bonus 2:1 · +1.000 €"; Erfolg `karibik` nicht freigeschaltet.
2. Dealer A♠ Q♦ J♣ 9♥ 2♠ (nicht qualifiziert), Spieler Paar → Mitgehen → netto +200, Status enthält „nicht qualifiziert".
3. Passen → netto −200, Dealer-Karten bleiben verdeckt.
4. Spieler Flush (♥ 2-5-8-J-K) vs. Dealer Paar → Mitgehen → Erfolg `karibik` freigeschaltet.
5. Hand geben, dann `UI.show('royal')` → Toast „Hand aufgegeben", Konto −Ante, `Stud.round === null`.
6. Insider `sylviesblick` per Dev/State setzen: Ante 100 → zweite Dealer-Karte ohne `hidden-card`; Ante 500 → mit `hidden-card`, `#studPeek` sichtbar mit „wirkt bis 250 €".
7. Ante 50 → Toast „Zwischen 100 € und 1.000 €", keine Karten.

Screenshots: `royal-lobby.png` (Referenz erneuern, 4 Portale), neu `royal-stud.png` (nach Geben, vor Entscheidung), `mobile-royal.png` erneuern falls Diff > 2 %.

### 6.3 Lauf

`node tests/run-selftest.mjs`, `tests/dom-selftest.sh`, `python3 tests/playtest-story.py` (mit eigenem `K37_PORT`/`K37_PROFILE`), `python3 tests/mobile-check.py`. Alles grün vor Merge.
