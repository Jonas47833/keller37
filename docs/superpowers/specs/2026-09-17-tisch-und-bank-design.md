# KELLER 37 – Tisch & Bank: Roulette-Mehrfacheinsatz, Bank- und Anlagen-Rebalance

Datum: 2026-09-17 · Status: abgestimmt · Basis: `keller37.html` @ `57ef394`

## 1. Ziel

Paket 1 von zwei („Tisch & Bank", danach „Insider & Skills"):

1. **Roulette:** mehrere Einsätze pro Dreh – Chips auf Zahlen und Außenfelder legen, ein Dreh wertet alles aus.
2. **Bank:** 8 % Zinsen pro Spin statt 30 %, nur ein offener Kredit.
3. **Anlagen:** Festgeld nach 6 Spins, Trickbetrug +50 %, je Sorte nur eine laufende Anlage.

Balance-Ziel: Bank ist keine Dauerfalle mehr, aber weiter teuer; Anlagen haben negativen Erwartungswert und sind Parkplatz bzw. Zock, keine Geldmaschine; Roulette wird schneller und variabler bei gleicher Hausquote.

Nicht Teil dieser Spec: Insider-Upgrades, Skill-System, Änderungen an Slots/Blackjack/Pferden/Igor, Story-Inhalte.

## 2. Roulette-Mehrfacheinsatz

### 2.1 Datenmodell

```js
Roulette.bets = [{ type: 'number'|'red'|'black'|'even'|'odd', n: 0..36|null, amount: number }]
Roulette.lastBets = []   // Chip-Verteilung des letzten Drehs, für „Wie zuletzt"
```

Chips gleichen Typs und gleicher Zahl werden **nicht** zusammengelegt – jeder Klick ist ein Chip; die Anzeige summiert pro Feld. `undo()` entfernt den zuletzt gelegten Chip, `clear()` alle.

### 2.2 Bedienung

- Das Einsatzfeld heißt **„Chip"**; Schnellwahl 10 / 50 / 100 / 500 / Max bleibt („Max" = `Rules.maxBet(s)` minus bereits liegender Chips).
- Klick auf ein Feld legt einen Chip mit dem aktuellen Chip-Wert; erneuter Klick stapelt. Marker `.chip-stack` zeigt die Summe des Felds (z. B. „150").
- Kopfzeile über dem Tisch: „Auf dem Tisch: 260 € · 3 Chips", Buttons **Drehen**, **↶ Chip zurück**, **Tisch leeren**, **Wie zuletzt** (nur wenn `lastBets` vorhanden und bezahlbar; legt exakt die letzte Verteilung).
- Ein Chip darf nur gelegt werden, wenn `Rules.checkSpin(s, total + chip).ok` – sonst Toast wie heute („Zu wenig Geld …" mit Zinsen/Meds). **Drehen** ist deaktiviert ohne Chips.
- Während der Kugel läuft: Tisch gesperrt (wie heute).

### 2.3 Auswertung

- `Game.beginSpin(total)` einmal (Escrow: Summe aller Chips + Zinsen + Meds), Kugel wie bisher, `Game.settle(payout − total, { bet: total, run })`.
- Auszahlung je Chip: Zahl 35:1 (+ Einsatz zurück), Außenfelder 1:1 (+ Einsatz zurück); Null lässt alle Außenfelder verlieren.
- **Glück (Bier/Brownie/Auto):** `Rules.rouletteLuckOverride` wirkt auf genau einen Chip – `Rules.rouletteLuckTarget(bets)`: höchster Einsatz; bei Gleichstand Zahl vor Außenfeld; bei weiterem Gleichstand der zuerst gelegte.
- Anzeige: gewinnende Chips leuchten gold und fliegen zur Kasse, verlierende werden abgeräumt; Statuszeile „Rot ✓ +50 · 17 ✗ · Gerade ✓ +50 → +100 €" bzw. „Alles weg: −260 €".
- Nach dem Dreh wird der Tisch geleert, `lastBets` gespeichert.
- Bus-Event `roulette:result { bets, rolled, payout, hits }`; Trophäe „Plein" feuert, wenn ein Zahl-Chip trifft. Story-Statistik „Verzockt" bekommt weiter den Netto-Verlust (über `loss`).

### 2.4 Reine Regeln

```js
Rules.rouletteSettle(bets, rolled) → { payout, hits: [{ bet, win, payout }] }   // payout inkl. zurückgezahlter Einsätze
Rules.rouletteLuckTarget(bets) → index                                           // −1 bei leerem Tisch
Rules.rouletteTotal(bets) → number
```

`rouletteLuckOverride(type, chosen, rolled, luck, rng)` bleibt unverändert und wird mit dem Ziel-Chip aufgerufen.

## 3. Bank und Vito

- `Rules.BANK_RATE = 0.08`; Mercedes `bankRate` C/S/G = 0.07 / 0.06 / 0.05. Limits unverändert (3.000; Mercedes 4.000 / 6.000 / 10.000).
- **Ein offener Kredit:** `Rules.bankLoanAllowed(s, amt)` verlangt zusätzlich `s.bankDebt === 0`. Finanz-Raum: Kredit-Knöpfe gesperrt bei offenem Kredit, Hinweis „Erst den Schuldschein tilgen." Tilgen bleibt wie heute (Gesamtsumme).
- Vito unverändert (ein Zettel, 5 Spins, ×3). Game-Over-Regel unverändert.
- Alle Texte mit „30 %" werden dynamisch oder auf 8 % gesetzt (Finanz-Raum liest bereits `gear.bankRate`; Bank-Szenen/Toasts prüfen).

## 4. Anlagen

```js
INVEST: {
  bank:  { name: 'Festgeld',    rate: 0.08, spins: 6,  risk: 10, min: 10 },
  stock: { name: 'Aktien',      rate: 1.0,  spins: 2,  risk: 85, min: 10 },
  scam:  { name: 'Trickbetrug', rate: 0.5,  spins: 10, risk: 55, min: 10 },
}
```

- **Je Sorte eine laufende Anlage:** `Rules.canInvest(s, kind, amount)` → `{ ok, reason: 'running' | 'min' | 'funds' }`. Die Anlagen-Karte zeigt bei laufender Anlage statt Eingabe und Knopf die laufende Anlage („Festgeld · 2.000 € · noch 4 Spins"); nach Auszahlung/Verlust wieder die Eingabe.
- Trickbetrug-Text: „Vito legt es für dich an. Frag nicht, wo."
- Bestehende Spielstände mit mehreren laufenden Anlagen derselben Sorte laufen aus; neu anlegen erst, wenn keine mehr läuft.

## 5. Technik

- Block `rules`: Konstanten, `canInvest`, `bankLoanAllowed`, `rouletteSettle`, `rouletteLuckTarget`, `rouletteTotal`.
- Block `game-roulette`: `bets`/`lastBets`, `place/undo/clear/repeat/spin`, Chip-Marker, Statuszeile, Animationen (CSS im Abschnitt Roulette).
- Block `rooms`: Finanz (Kredit-Sperre, Hinweis), Anlagen (Karte mit laufender Anlage, `canInvest`).
- Templates `tpl-roulette` (Kopfzeile/Buttons), `tpl-invest` (Karten), `tpl-finance` (Hinweis).
- Keine neuen State-Felder; `State.VERSION` bleibt 1.
- README: Roulette-Bedienung, neue Bank-/Anlagen-Werte.

## 6. Tests

- Node: `rouletteSettle` (Zahl + Rot, Null, nur Außenfelder, leerer Tisch), `rouletteLuckTarget` (höchster Einsatz, Gleichstand Zahl vor Außen, Reihenfolge), `rouletteTotal`, `bankInterest` 8 % und Mercedes, `bankLoanAllowed` mit offenem Kredit, `canInvest` (laufend / min / funds), Katalog-Werte, bestehende Tests angepasst (30 % → 8 %).
- Browser-Playtest, neues Szenario `scenario_roulette_chips` (freies Spiel): 3 Chips legen (Zahl 17, Rot, Gerade), Anzeige „Auf dem Tisch", Chip zurück, Tisch leeren, erneut legen, Drehen mit RNG-Stub auf Ergebnis 18 (Rot, Gerade) → Delta +… stimmt, Kontostand einmal belastet; „Wie zuletzt" legt dieselben Chips; Kredit-Sperre bei offenem Kredit; Anlagen-Sperre bei laufendem Festgeld. Screenshots `roulette-chips.png`, `finance.png`, `invest.png` erneuert.

## 7. Ablauf

Branch `feature/tisch-und-bank` von `main`, Plan per `writing-plans`, Umsetzung per Subagenten, Merge nach `main` und Push nur nach Rückfrage.

## 8. Abweichungen in der Umsetzung

Drei Punkte weichen vom Stand dieser Spec ab (Ruling nach dem Whole-Branch-Review, Fix-Pass):

1. **Game-Over-Regel geändert.** §3 sagte „Game-Over-Regel unverändert" – tatsächlich musste `Rules.isGameOver` angepasst werden: `bankDebt > 0 && mafiaDebt > 0 &&` kein 1-€-Spin mehr bezahlbar (inkl. Zinsen/Meds), statt vorher `bankDebt >= limit`. Grund: Mit „nur ein Kredit auf einmal" (§3) lässt sich die Bank praktisch nie mehr bis ans Limit ausreizen, solange noch ein alter (kleinerer) Kredit offen ist – die alte Regel „Game Over ab `bankDebt >= limit`" wäre dadurch kaum noch erreichbar geworden. Die neue Regel bindet Game Over stattdessen daran, dass beide Kreditquellen (Bank offen, Vito offen) zu sind und selbst ein Mindesteinsatz nicht mehr drin ist. Siehe Node-Selftest `isGameOver: beide Quellen zu und kein Spin mehr bezahlbar` (`keller37.html`).
2. **Vierter Kredit-Knopf „Limit".** §3/Technik (§5, `tpl-finance`) nannten nur 200/500/1.000 als Kredit-Beträge. Mit nur einem offenen Kredit und diesen drei Beträgen war das Bank-Limit (3.000 bzw. Mercedes 4.000–10.000) faktisch unerreichbar – die Szene `bank.limit` und der Mercedes-Limit-Perk wären damit toter Code. Ergänzt: ein vierter Button `data-loan="limit"` in `tpl-finance`, der auf `Rules.gear(s).bankLimit` leiht (Text „Limit · <Betrag>" über `UI.fmt`, gesperrt wie die anderen über `Rules.bankLoanAllowed`). Node-Selftest `bankLoanReason(base({ bankDebt: 0, car: 'mercS' }), 6000) === null` / `6001 === 'limit'`.
3. **„Max"-Chip zieht bereits liegende Chips ab.** §2.2 nannte das schon als Sollverhalten („Max" = `Rules.maxBet(s)` minus bereits liegender Chips), das war in der ersten Umsetzung aber noch nicht verdrahtet – `Game.bindBet` hatte keinen Hebel dafür. Ergänzt: dritter, optionaler Parameter `maxFn` an `Game.bindBet(root, inputId, maxFn = () => Rules.maxBet(State.s))`; die Roulette-Mount ruft `Game.bindBet(root, 'rouletteBet', () => Math.max(1, Rules.maxBet(State.s) - Roulette.total()))`. Playtest-Check direkt nach den drei Chips (Summe 80, Kontostand 1.000): Klick auf `.chip[data-chip=max]` → `#rouletteBet` zeigt „920".
