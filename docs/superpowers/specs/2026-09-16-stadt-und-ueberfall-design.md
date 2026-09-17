# KELLER 37 – Stadt (Autos & Schuhe) und Überfälle

Datum: 2026-09-16 · Status: abgestimmt · Basis: `keller37.html` @ `d13841e`

## 1. Ziel

Zwei neue Systeme, die das Spiel über lange Zeit „einfacher und besser" machen, ohne die Casino-Mechanik zu kippen:

1. **Stadt** – ein Laden mit Autos (Audi-Linie, Mercedes-Linie) und Schuhen (INTERSPORT). Käufe sind dauerhafte Upgrades pro Spielstand.
2. **Überfälle** – auf dem Weg in den Keller wird man gelegentlich überfallen. Kämpfen gibt **Stärke**, ein neues Attribut mit eigenen Vorteilen.

Beides gilt im freien Spiel **und** im Story-Modus. Ausrüstung und Stärke leben im jeweiligen Spielstand (`keller37.state` bzw. `keller37.story`); ein Story-Neustart beginnt ohne Auto.

Nicht Teil dieser Spec: Meta-Progression über Story-Runden hinweg, Sammeln mehrerer Autos, Kauf auf Kredit.

## 2. Daten

### 2.1 Neue Felder in `State.fresh()`

```js
car: null,            // id aus Rules.GEAR.cars oder null
shoes: null,          // id aus Rules.GEAR.shoes oder null
strength: 0,          // 💪, nie sinkend
mugCooldown: 0,       // freies Spiel: Spins bis zum nächsten möglichen Überfall; Story: Tage
stats: { …, muggings: 0, fightsWon: 0 },
```

`State.VERSION` bleibt `1`. Alte Spielstände werden per `Object.assign(fresh, saved)` aufgefüllt (wie heute bei `flags`/`stats`). Ein bestehender Spielstand läuft ohne Reset weiter.

### 2.2 Katalog `Rules.GEAR`

Alle Zahlen liegen ausschließlich hier; kein Spiel liest `s.car`/`s.shoes` direkt, sondern nur `Rules.gear(s)`.

```js
GEAR: {
  cars: {
    audiA3:  { brand: 'audi', tier: 1, name: 'Audi A3 (gebraucht)',   icon: '🚗', price: 1500,  mugMult: 0.7,  flee: 10, luck: 0 },
    audiRS4: { brand: 'audi', tier: 2, name: 'Audi RS 4 quattro',     icon: '🏎️', price: 8000,  mugMult: 0.45, flee: 20, luck: 2 },
    audiR8:  { brand: 'audi', tier: 3, name: 'Audi R8',               icon: '🏎️', price: 30000, mugMult: 0.2,  flee: 35, luck: 4 },
    mercC:   { brand: 'merc', tier: 1, name: 'Mercedes C-Klasse',     icon: '🚙', price: 2000,  bankLimit: 4000,  bankRate: 0.27, luck: 0 },
    mercS:   { brand: 'merc', tier: 2, name: 'Mercedes S-Klasse',     icon: '🚘', price: 10000, bankLimit: 6000,  bankRate: 0.24, luck: 2 },
    mercG:   { brand: 'merc', tier: 3, name: 'Mercedes AMG G 63',     icon: '🚐', price: 40000, bankLimit: 10000, bankRate: 0.20, luck: 4 },
  },
  shoes: {
    basic:  { tier: 1, name: 'Laufschuh Basic',   icon: '👟', price: 300,  flee: 15, postTime: 1, postPay: 0,  spuelerBand: 0,   taxiTip: 0 },
    trail:  { tier: 2, name: 'Trail-Runner Pro',  icon: '👟', price: 2000, flee: 30, postTime: 1, postPay: 5,  spuelerBand: 0.2, taxiTip: 0 },
    carbon: { tier: 3, name: 'Carbon-Sprinter',   icon: '👟', price: 7500, flee: 45, postTime: 2, postPay: 10, spuelerBand: 0.2, taxiTip: 5 },
  },
  TRADE_IN: 0.5,   // Anteil des alten Kaufpreises, der beim Autokauf angerechnet wird
},
```

Nicht gesetzte Boni gelten als neutral (`mugMult: 1`, `flee: 0`, `luck: 0`, `bankLimit: Rules.BANK_LIMIT`, `bankRate: Rules.BANK_RATE`, `postTime/postPay/spuelerBand/taxiTip: 0`).

### 2.3 Abgeleitete Werte `Rules.gear(s)`

Pure Funktion, liefert immer alle Schlüssel:

```js
{ luck, mugMult, flee, bankLimit, bankRate, postTime, postPay, spuelerBand, taxiTip }
```

- `luck` = Auto-Glück (max 4). Schuhe geben kein Glück.
- `flee` = Auto-Flucht + Schuh-Flucht.
- `mugMult` = Auto-Multiplikator × (Stärke ≥ 10 ? 0,5 : 1).

Kaufregeln (pure):

- `Rules.carUpgradeCost(s, id)` = max(0, Preis − `TRADE_IN` × Preis des aktuellen Autos) (0 Anrechnung, wenn keins). Gilt innerhalb der Linie **und** beim Markenwechsel; es gibt nie Geld zurück. Ein Rückschritt (niedrigere Stufe derselben Marke) ist nicht kaufbar.
- `Rules.canBuyCar(s, id)` → `{ok, reason: 'owned' | 'downgrade' | 'funds', cost}`.
- `Rules.canBuyShoes(s, id)` → `{ok, reason: 'owned' | 'downgrade' | 'funds'}`; Schuhe kosten immer den vollen Preis, nur Aufstieg.

### 2.4 Hooks in bestehenden Regeln

| Regel | Änderung |
|---|---|
| `Rules.luck(s)` | `+ Rules.gear(s).luck` |
| `Rules.bankInterest(debt, s)` | Zinssatz `gear.bankRate` statt Konstante (Signatur bekommt `s`; alle Aufrufer angepasst) |
| `Rules.bankLoanAllowed(s, amt)` | Limit `gear.bankLimit` |
| `Rules.postmanTier(streak, s)` | `t + gear.postTime`, `r + gear.postPay` |
| Spüler-Minispiel | Timing-Band um `gear.spuelerBand` (Anteil) breiter |
| Taxi-Minispiel | `+ gear.taxiTip` pro Fahrgast (Anzeige und `StoryRules.taxiPay(passengers, tickets, tip)`) |
| Türsteher-Schicht (`Jobs.runShift`) | `+ min(50, 10 × strength)` auf den Grundlohn, Toast nennt den Bonus |
| Finanz-Raum | Limit-Anzeige liest `gear.bankLimit`, Zinshinweis `gear.bankRate` |

## 3. Screen „Stadt"

### 3.1 Zugang

- Hub: zweite Tag-Tür neben „Ausgang · Post austragen": **„Stadt" 🏙️**, Chalk-Tag „Autohaus · INTERSPORT", `data-screen="stadt"`.
- Story: `stadt` ist ein Raum in `unlocked.rooms`; die Tür ist verdeckt, solange er gesperrt ist (wie `bank`/`vito` in der Seitenleiste). Offen morgens **und** abends; ein Kauf verbraucht keinen Tag.
- Story 1 „Die Schuld": neues Morgen-Event `stadtOffen` an Tag 4 (`once`), Szene `schuld.stadt` (2–3 Panels: Kevin schleppt dich mit ins Autohaus – „Guck mal, was man hier alles nicht bezahlen kann"), Effekt `{ unlock: { rooms: ['stadt'] } }`. `StoryRules.validate` prüft `stadt` als gültigen Raum.

### 3.2 Aufbau

Drei Schaufenster nebeneinander (`grid`, unter 760 px untereinander):

1. **Audi Zentrum** – drei Karten A3 / RS 4 / R8.
2. **Mercedes-Benz Niederlassung** – drei Karten C / S / G 63.
3. **INTERSPORT** – drei Karten Basic / Trail / Carbon.

Karte: Icon, Name, Preis, Boni als Stichpunkte in Spielerworten („Überfälle −30 %", „Flucht +10 %", „Bank-Limit 4.000 €", „Zinsen 27 %", „Post: +1 s pro Brief", „Spüler: leichteres Timing"), Button:

- „Kaufen · 1.500 €" (kein Auto / anderes Auto ohne Inzahlungnahme-Anteil)
- „Upgrade · 7.250 €" (Preis minus Inzahlungnahme; auch beim Markenwechsel)
- „Deins" (aktuell, deaktiviert)
- deaktiviert mit Tooltip bei `downgrade` oder `funds`

Verkäufer-Zeile je Schaufenster (statischer Text nach Zustand): ohne Auto „Zu Fuß gekommen? Mutig.", mit Auto der Marke „Schön, dass du wieder da bist.", mit Auto der anderen Marke „Der Wechsel lohnt sich. Sagen alle." INTERSPORT: „Für Leute, die es eilig haben."

### 3.3 Kaufablauf

1. Bei Auto mit Inzahlungnahme oder Markenwechsel: Bestätigungspanel „Dein Audi A3 geht mit 750 € in Zahlung. Weiter?" (Ja/Nein).
2. Cutscene, 2 Panels, Hintergrund `autohaus` bzw. `intersport` (neue Hintergründe im Cutscene-BG-Katalog), Figur `verkaeufer` (neu, neutrales Gesicht): Schlüssel- bzw. Schuhkarton-Übergabe.
3. Geld über `Game.applyDelta(-cost, { from: card })`, Feld setzen, `State.save()`, Toast, Karten neu rendern.
4. Kein Kauf, wenn `Cutscene.active` oder `Game.inFlight > 0`.

### 3.4 Seitenleiste

Unter dem Kontostand eine Besitz-Zeile: `🚗 Audi RS 4 · 👟 Trail-Runner · 💪 3`. Fehlende Teile werden weggelassen; ohne alles: „Zu Fuß · 💪 0". In beiden Modi.

## 4. Überfall

### 4.1 Auslöser

`Mugging.maybe(where)` wird an genau zwei Stellen gerufen:

- freies Spiel: in `UI.show(screen)`, wenn von `hub` auf eine Casino-Tür gewechselt wird (`roulette`, `slots`, `horses`, `russian`, `blackjack`), vor dem eigentlichen Wechsel;
- Story: am Anfang von `Story.evening()`, vor `UI.show('hub')`.

Der Überfall läuft nie, wenn `Cutscene.active`, `Game.inFlight > 0`, `Game.gameOverPending` oder (Story) `Story.sleeping`.

### 4.2 Chance `Rules.mugChance(s, where)` (pure)

```
base    = where === 'evening' ? 0.12 : 0.06
0,      wenn s.balance < 100
0,      wenn s.mugCooldown > 0
0,      wenn freies Spiel und s.stats.spins < 10
0,      wenn Story und story.day < 4
×2,     wenn s.balance >= 2000
× gear.mugMult
```

Nach jedem Überfall (egal wie er ausgeht): `mugCooldown = 15` (freies Spiel, in `Game.afterSpin` um 1 verringert – nur bei `State.mode === 'free'`) bzw. `3` (Story, ausschließlich in `StoryRules.advanceDay` um 1 verringert; Spins zählen dort nicht). Beim Start eines neuen freien Spiels ist `mugCooldown` 0, die Spin-Schwelle deckt die Anfangszeit ab.

### 4.3 Beute `Rules.mugLoot(balance)`

`clamp(round(balance × 0.2), 50, 1500)`, nie mehr als `balance`.

### 4.4 Ablauf (Cutscene `mugging`, Hintergrund `gasse`)

Räubertyp zufällig aus drei (`junkie`, `jugend`, `cousin` – „Igors Cousin"), jeweils eigene Anrede- und Ergebnistexte; Figuren neu im Cutscene-Katalog (`raeuber`, drei Stimmungen genügen).

1. Panel: Räuber tritt aus dem Schatten, fordert `{{loot}}`.
2. Panel mit drei Choices:
   - **💪 Kämpfen** – `Rules.fightChance(strength) = min(0.9, 0.35 + 0.08 × strength)`. Sieg: nichts verloren, `strength += 1`, `stats.fightsWon += 1`; ab `strength >= 5` (vor dem Inkrement) zusätzlich Brieftasche `Rules.mugWallet(rng)` = 50–150 € (`+`). Niederlage: `−loot`, `strength += 1`.
   - **👟 Wegrennen** – `Rules.fleeChance(gear) = min(0.9, 0.3 + gear.flee / 100)`. Erfolg: nichts verloren. Misserfolg: `−loot − round(balance × 0.1)` (Deckel: nie unter 0). Keine Stärke.
   - **💸 Zahlen** – `−loot`. Keine Stärke.
3. Ergebnis-Panel mit `fx` (`shake` bei Kampf, `swipe` bei Flucht, `stats` nicht nötig), Geld animiert über `Game.applyDelta`.

Immer: `stats.muggings += 1`, Cooldown setzen, `State.save()`. Danach der ursprüngliche Raumwechsel bzw. der Abend. Wird das Fenster während der Szene neu geladen, ist nichts passiert (Geld wird erst nach der Wahl gebucht). Der Skip-Knopf springt nur zum Wahl-Panel, das immer das letzte Panel der ersten Szene ist.

Dev-Parameter `?mug=1` erzwingt beim nächsten Auslöser einen Überfall (Chance 1), `?mug=junkie|jugend|cousin` zusätzlich den Typ.

### 4.5 Stärke außerhalb des Kampfs

- Türsteher-Bonus (siehe 2.4).
- Story 1: neue Schicht-Karte **„Eintreiber"** bei Vito: `{ id: 'eintreiber', kind: 'shift', base: 150, requires: { strength: { gte: 4 } }, requireText: 'Stärke 4', desc: 'Vito hat eine Liste. Du hast Fäuste.', pay: '150 €' }`, freigeschaltet zusammen mit dem Türsteher-Event (`unlock.jobs: ['tuersteher', 'eintreiber']`); zwei eigene Szenen (`schuld.eintreiber.kiosk`, `schuld.eintreiber.zahnarzt`) mit `jobEffects` `{ var: 'ruf', add: 1 }`. `StoryRules.check` bekommt die Bedingung `strength` (liest `s.strength`).
- Freies Spiel: ab Stärke 8 grüßt Igor in seiner Begrüßungsszene mit einer zusätzlichen Zeile („Respekt. Man hört Dinge.") – nur Text.
- Trophäen: `strassenkaempfer` „Straßenkämpfer" (5 Kämpfe gewonnen), `vollausgestattet` „Vollausgestattet" (Auto Stufe 3 + Carbon-Sprinter).

## 5. Technik

### 5.1 Neue Script-Blöcke (Reihenfolge)

- `gear-rules` (nach `rules`): `Rules.GEAR`, `Rules.gear`, `carUpgradeCost`, `canBuyCar`, `canBuyShoes`, `mugChance`, `mugLoot`, `mugWallet`, `fightChance`, `fleeChance`, `Rules.MUG` (Konstanten: Basischancen, Cooldowns, Schwellen, Deckel).
- `room-stadt` (nach `rooms`): Screen-Template `tpl-stadt`, Rendering, Kauf, Verkäufer-Texte.
- `mugging` (nach `gameover`, vor `story-rules`): `Mugging.maybe(where)`, Szenen, Räubertexte.
- Story-Inhalte (`schuld.stadt`, Eintreiber-Szenen, Event) in `story-schuld`.

### 5.2 Eingriffe (jeweils wenige Zeilen)

`State.fresh`, `Rules.luck`/`bankInterest`/`bankLoanAllowed`/`postmanTier`, `Game.afterSpin` (Cooldown), `UI.show` (Hook), `Story.evening` (Hook), `StoryRules.advanceDay` (Cooldown), `StoryRules.check` (`strength`), `StoryRules.validate` (Raum `stadt`), `Jobs.POOL` (Eintreiber), `Jobs.runShift` (Türsteher-Bonus), Spüler/Taxi (Band/Trinkgeld), Finanz-Raum (Anzeige), Seitenleiste (Besitz-Zeile), Hub (Tür), Cutscene-Katalog (Hintergründe `autohaus`, `intersport`, `gasse`; Figuren `verkaeufer`, `raeuber`), Achievements (2 neue), Titel-Trophäenliste, README.

### 5.3 Balance-Leitplanken

- Glück aus Ausrüstung: max +4 %.
- Bargeldverlust je Überfall: max 1.500 € (+10 % bei missglückter Flucht).
- Überfälle im freien Spiel: grob alle 20–40 Raumwechsel ohne Auto, deutlich seltener mit Audi.
- Alle Werte nur in `Rules.GEAR`/`Rules.MUG`.

## 6. Tests

### 6.1 Node-Selftest (`node tests/run-selftest.mjs`)

- Katalog: Preise steigen je Linie, `luck ≤ 4`, `flee`-Summe Auto+Schuh ≤ 80, `bankRate` sinkt mit Stufe.
- `Rules.gear`: ohne alles neutral; Audi R8 + Carbon; Mercedes G; Stärke 10 halbiert `mugMult`.
- `carUpgradeCost`: kein Auto → Preis; A3 → RS 4 = 8000 − 750; A3 → C-Klasse = 2000 − 750; RS 4 → A3 = `downgrade`.
- `canBuyShoes`: Basic → Carbon erlaubt (Sprung), Carbon → Trail = `downgrade`.
- `luck`, `bankLoanAllowed`, `bankInterest`, `postmanTier` mit und ohne Ausrüstung.
- `mugChance`: unter 100 € = 0; Cooldown = 0; Spins < 10 = 0; Story Tag < 4 = 0; ≥ 2000 € verdoppelt; Audi-Multiplikator; Abend-Basis 0,12.
- `mugLoot`: 100 € → 50; 10.000 € → 1.500; 60 € → 50; 30 € → 30.
- `fightChance(0) = 0.35`, `fightChance(7) = 0.9`, `fleeChance` Deckel 0,9.
- `StoryRules.check` mit `strength`; `validate` akzeptiert Raum `stadt` und Job `eintreiber`; `jobAvailable` Eintreiber bei Stärke 3 = nicht ok, 4 = ok.
- Tick-Regeln: `afterSpin` senkt `mugCooldown`; `advanceDay` senkt ihn in der Story.

### 6.2 Browser-Playtest (`tests/playtest-story.py` + neue Fälle, headless Chrome, 1280 und 400 px)

- Stadt öffnen, Kauf mit zu wenig Geld: Button deaktiviert, Kontostand unverändert.
- A3 kaufen → Upgrade RS 4 (Kosten mit Inzahlungnahme) → Markenwechsel C-Klasse mit Bestätigung → Abbruch lässt Auto unverändert.
- Seitenleiste zeigt Besitz und Stärke.
- `?mug=1`: alle drei Ausgänge je einmal (Kampf mit Stärke 20 = sicherer Sieg, Zahlen, Flucht), Kontostand und Stärke wie erwartet, danach landet man im gewählten Raum.
- Story: Tag 4 Morgen-Event schaltet Stadt frei; Eintreiber-Karte erscheint erst ab Stärke 4; Türsteher-Toast nennt Bonus.
- Screenshots `docs/superpowers/screenshots/stadt-*.png`, `mug-*.png`.

## 7. Ablauf

Branch `feature/stadt-ueberfall` von `main`, Umsetzung per Plan (`writing-plans` → `subagent-driven-development`), Merge nach `main` und Push nur nach Rückfrage.

## 8. Abweichungen in der Umsetzung

- `gameOverPending` ist ein modulweites `let` im Block `gameover` (nicht `Game.gameOverPending`); alle Prüfstellen (u. a. `Mugging.maybe`) lesen die freie Variable direkt.
- Das Ergebnis-Panel bei Flucht nutzt `fx: 'flash'` statt `swipe` – ein `swipe`-Effekt existiert im Cutscene-Katalog nicht.
- Nicht kaufbare Karten (Stadt) zeigen wie im Leben-Raum einen Grund-Span statt eines deaktivierten Buttons mit Tooltip; bei `funds` **mit** vorhandenem Auto steht dort zusätzlich der wirksame Preis (nach Inzahlungnahme), z. B. „Zu wenig Bargeld · 7.250 €".
- `stadtOffen` prüft `day ≥ 4` statt `day === 4` (weiterhin `once`), damit auch Saves, die Tag 4 bereits hinter sich haben, die Stadt bei nächster Gelegenheit freigeschaltet bekommen.
- **Stadt als Straße (Nutzerwunsch nach dem ersten Spielen):** Der Screen zeigt zuerst drei Schaufenster (Audi Zentrum, Mercedes-Benz Niederlassung, INTERSPORT) mit Verkäufer-Spruch und aktuellem Besitz; ein Klick öffnet den Laden mit seinen drei Karten nebeneinander und „← Zurück auf die Straße". Dev-Parameter `?screen=stadt&shop=audi|merc|sport`.
