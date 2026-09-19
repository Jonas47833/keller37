# KELLER 37 – Insider & Skills

Datum: 2026-09-17 · Status: abgestimmt · Basis: `keller37.html` @ `906bb81` (main)

## 1. Ziel

Paket 2 von zwei („Tisch & Bank" ist umgesetzt):

1. **Skills** – Erfahrung durch Spielen; alle zwei Level darf man einen von acht Skills wählen (max. 3 aktiv). Jeder Skill hat eine Lichtseite und einen Haken in einer anderen Baustelle.
2. **Insider-Upgrades** – jedes abgeschlossene Story-Teil gibt einmalig eine Wahl aus drei zufällig gezogenen Upgrades; sie bleiben dauerhaft (Meta) und gelten in beiden Modi.

Balance-Leitplanke (wie beim Glück): Alles, was Gewinnchancen direkt anhebt, wirkt nur bis zu einem Einsatzdeckel voll – Skills und Insider machen das Spiel spürbar leichter, aber nie zur Geldmaschine.

Nicht Teil dieser Spec: neue Story-Inhalte (die Fortsetzung entsteht parallel), neue Spiele, Änderungen an Stadt/Überfällen über die genannten Modifikatoren hinaus.

## 2. Daten

### 2.1 Spielstand (`State.fresh()`, beide Modi)

```js
xp: 0,                 // Erfahrungspunkte
skills: [],            // bis zu 3 Skill-IDs
skillRespecs: 0,       // Zähler (nur Statistik)
insiderExcluded: [],   // 12 ausgegraute Roulette-Zahlen, wenn Croupier-Auge aktiv; sonst leer
mechRespins: 0,        // Slots-Runden seit dem letzten Festhalten (Mechaniker)
```

### 2.2 Meta (`State.freshMeta()`)

```js
insider: [],           // gewonnene Insider-IDs, dauerhaft
insiderClaimed: {},    // storyId → true (pro Story-Teil einmal)
```

`State.VERSION` bleibt 1; Felder werden per `Object.assign` aufgefüllt (`insiderClaimed` wie `storyRuns` als Objekt gemerged).

### 2.3 XP und Level

| Quelle | XP |
|---|---|
| Spin (jedes Spiel, `spin:after`) | +1 |
| gewonnener Spin (`win`) | +2 zusätzlich |
| erledigter Job (`job:done`) | +5 |
| Story-Tag beendet (`advanceDay`) | +5 |
| neue Trophäe (`achievement`) | +10 |

`Rules.XP_LEVELS = [0, 25, 60, 110, 180, 270]` (kumulierte XP für Level 1–6). `Rules.xpLevel(xp) → { level, next, points }` – `points` = Skill-Punkte insgesamt (Level 2, 4, 6 → 1, 2, 3). Freie Punkte = `points − skills.length`. Über Level 6 hinaus zählt XP weiter (Anzeige „Lv 6 · max").

### 2.4 Skill-Katalog `Rules.SKILLS`

Jeder Eintrag: `{ id, name, icon, light, shadow, mods }`. `mods` sind Schlüssel für `Rules.mods`.

| ID | Name | Licht (Text) | Schatten (Text) | mods |
|---|---|---|---|---|
| `pokerface` | Pokerface | Blackjack: natürlicher Blackjack zahlt 3:2, Push bringt +10 % | Bier gibt kein Glück | `bjNatural: 1.5, bjPushBonus: 0.1, beerLuckMult: 0` |
| `kalterkopf` | Kalter Kopf | Roulette-Zahlen zahlen 36:1 | Brownie wirkt nur halb | `rouletteNumberPayout: 36, brownieLuckMult: 0.5` |
| `zockerhaende` | Zockerhände | Slots: Paar zahlt 1,3× | Bank-Zinsen +2 % | `slotPairMult: 1.3, bankRateAdd: 0.02` |
| `pferdefluesterer` | Pferdeflüsterer | Pferde zahlen 3,3:1 (bis 250 €) | Überfälle 50 % häufiger | `horsePayout: 3.3, mugChanceMult: 1.5` |
| `eisenmagen` | Eisenmagen | 4 Bier möglich (+25 %), Brownie hält 6 Spins (Basis 4, Balancing 2026-09-20) | Postbote: −1 s pro Brief | `maxBeers: 4, brownieSpins: 6, postTimeAdd: -1` |
| `verhandler` | Verhandler | Bank-Zinsen −2 %, Vito-Frist 7 Spins | Anlagen zahlen 10 % weniger | `bankRateAdd: -0.02, mafiaSpins: 7, investRateMult: 0.9` |
| `strassenkoeter` | Straßenköter | Kampfchance +15 %, Brieftasche ×2 | Bank-Limit −1.000 € | `fightAdd: 0.15, walletMult: 2, bankLimitAdd: -1000` |
| `brieftraeger` | Briefträgerherz | Postbote +1 s und +5 € pro Brief | Slots: Paare zahlen nichts | `postTimeAdd: 1, postPayAdd: 5, slotPairMult: 0` |

Konflikte: `zockerhaende` und `brieftraeger` schließen sich aus (`excludes`), `Rules.canPickSkill` meldet `reason: 'conflict'`. Mehrere `bankRateAdd`/`postTimeAdd` addieren sich; Multiplikatoren multiplizieren sich.

Balance: `slotPairMult: 1.3` bleibt bei jedem Einsatz unter 1,0 Erwartungswert (Kombinatorik über alle 216 Walzen-Ausgänge: `(95 + 90 × 1,3) / 216 ≈ 0,98`); mit dem alten Wert 1,5 wäre Slots bei jedem Einsatz +EV gewesen. Der Pferdeflüsterer-Bonus (`horsePayout: 3.3`) ist wie ein Insider-Deckel gebaut (`Rules.effectiveBonus(value, neutral, bet)`, analog zu `effectiveInsider`, aber mit Neutralwert ≠ 1): er wirkt voll bis `INSIDER_CAP` = 250 € Einsatz, darüber verliert nur der Bonus-Anteil über dem Neutralwert `horsePayout: 3` anteilig (Bonus wirkt voll bis 250 € Einsatz) – ohne Deckel wäre 3,3:1 bei jedem Einsatz +EV gewesen.

### 2.5 Insider-Katalog `Rules.INSIDER`

Jeder Eintrag: `{ id, name, icon, text, capped, mods }`. `capped: true` = wirkt bis `Rules.INSIDER_CAP = 250` € Einsatz voll, darüber anteilig (`Rules.effectiveInsider(value, bet)` wie `effectiveLuck`; bei Wahrheitswerten: wirkt nur, wenn `bet ≤ INSIDER_CAP`).

| ID | Name | Wirkung | capped | mods |
|---|---|---|---|---|
| `stallbursche` | Stallbursche | Vor jedem Rennen ist ein Pferd markiert, das sicher nicht gewinnt (nie das gewählte); es läuft mit 0,85× Schritt | ja | `horseLoserMarked: true` |
| `croupierauge` | Croupier-Auge | 12 Roulette-Zahlen sind ausgegraut und fallen nicht; die Kugel würfelt unter den restlichen 25 | ja | `rouletteExclude: 12` |
| `kartenzaehler` | Kartenzähler | Blackjack: Anzeige „Deck heiß/kalt"; bei heißem Deck zahlt ein Sieg 1,2:1 | ja | `bjHotDeck: 1.2` |
| `mechaniker` | Mechaniker | Slots: nach einer Niete darf man jede 5. Runde eine Walze festhalten und neu drehen | ja | `slotHoldEvery: 5` |
| `bankinsider` | Bankinsider | Zinsen −3 %, Limit +2.000 € | nein | `bankRateAdd: -0.03, bankLimitAdd: 2000` |
| `vitosneffe` | Vitos Neffe | Vito-Frist 8 Spins, Rechnung ×2 statt ×3, Überfälle halb so oft | nein | `mafiaSpins: 8, mafiaMult: 2, mugChanceMult: 0.5` |
| `postmeister` | Postmeister | Postbote: 20 Briefe pro Schicht, +5 € pro Brief | nein | `postLetters: 20, postPayAdd: 5` |

„Heißes Deck": Anteil von 10ern/Assen im Restdeck > 40 % (`Rules.deckHot(deck)`); Anzeige „🔥 heiß" / „❄️ kalt" neben dem Deck.

Bei mehreren `mafiaSpins`-Quellen gilt das Maximum; `bankLimitAdd` addiert sich (Untergrenze 500 €).

### 2.6 `Rules.mods(s, meta)`

Pure Funktion; liefert immer alle Schlüssel mit Neutralwerten:

```js
{ beerLuckMult: 1, brownieLuckMult: 1, maxBeers: 3, brownieSpins: 1,
  bjNatural: 1, bjPushBonus: 0, bjHotDeck: 1,
  rouletteNumberPayout: 35, rouletteExclude: 0,
  slotPairMult: 1.2, slotHoldEvery: 0,
  horsePayout: 3, horseLoserMarked: false,
  bankRateAdd: 0, bankLimitAdd: 0, mafiaSpins: 5, mafiaMult: 3, investRateMult: 1,
  mugChanceMult: 1, fightAdd: 0, walletMult: 1,
  postTimeAdd: 0, postPayAdd: 0, postLetters: 15 }
```

Skills aus `s.skills`, Insider aus `meta.insider`. Unbekannte IDs werden ignoriert.

### 2.7 Regel-Hooks (bestehende Funktionen lesen `mods`)

| Regel | Änderung |
|---|---|
| `Rules.luck(s)` | Bier-Anteil × `beerLuckMult`, Brownie-Anteil × `brownieLuckMult` |
| `Rules.canBeer`, `MAX_BEERS` | Maximum = `maxBeers`; `BEER_LUCK` bekommt Stufe 4 = 25 |
| Brownie-Timer (`Actions.brownie`) | `brownieSpins` |
| `bankInterest(debt, s)` / `gear.bankRate` | Satz + `bankRateAdd` (Untergrenze 0,01) |
| `bankLoanReason` / `gear.bankLimit` | Limit + `bankLimitAdd` (Untergrenze 500) |
| `MAFIA_SPINS`, `mafiaBill` | `mafiaSpins`, `mafiaMult` |
| `roulettePayout(type, chosen, rolled, bet, mods)` | Zahl: `bet × (rouletteNumberPayout)` |
| `rouletteRoll(rng, excluded)` | würfelt so lange, bis eine nicht ausgeschlossene Zahl fällt (max. 37 Versuche; Fallback erste erlaubte) |
| `slotMultiplier(a, b, c, mods)` | Paar = `slotPairMult` (0 = nichts) |
| `horseDelta(won, bet, mods)` | Sieg = `bet × horsePayout` |
| `horseStep(isSelected, luck, rng, handicap)` | `handicap` = 0,85 für das markierte Pferd |
| `bjDelta(outcome, bet, mods, ctx)` | `ctx.natural` → `bet × bjNatural`; `push` → `bet × bjPushBonus`; `ctx.hot` → `bet × bjHotDeck` (nur bei Sieg ohne Natural) |
| `investmentResolve(inv, rng, mods)` | Auszahlung × `investRateMult` auf den Zinsanteil |
| `Rules.mugChance` | × `mugChanceMult` |
| `Rules.fightChance(strength, mods)` | + `fightAdd`, Deckel 0,9 bleibt |
| `Rules.mugWallet(rng, mods)` | × `walletMult` |
| `postmanTier(streak, s, mods)` | Zeit + `postTimeAdd` (Untergrenze 0,5 s; Schuh-Deckel 1,5 s bleibt), Lohn + `postPayAdd` |
| Postbote Schichtende | nach `postLetters` Briefen |

Deckel: In den Spielen werden `stallbursche`, `croupierauge`, `kartenzaehler`, `mechaniker` nur angewandt, wenn `bet ≤ INSIDER_CAP` (Anzeige „Insider-Wissen wirkt bis 250 €" im jeweiligen Screen, wenn der Einsatz darüber liegt).

## 3. Oberfläche

### 3.1 Kopfzeile

Neben dem Glück ein Badge „Lv 3" mit Mini-Balken (Fortschritt zum nächsten Level). Bei freiem Skill-Punkt pulsiert das Badge; Klick öffnet den Skill-Screen. Level-Up: Toast „Level 4 – ein Skill-Punkt wartet."

### 3.2 Screen `skills` („Kopf")

Seitenleiste: neue Sektion „Kopf" mit Button „🧠 Skills" (Preis-Spalte zeigt „1 Punkt frei" / „Lv 3"). Screen:
- oben XP-Balken „Lv 3 · 72 / 110 XP", drei Slots (belegt: Icon + Name, leer: „frei" / „ab Lv 4");
- Karten der 8 Skills: Icon, Name, Licht (grün), Schatten (rot), Button „Wählen" (nur bei freiem Punkt), „Aktiv" bzw. Grund („Kein Punkt frei", „Passt nicht zu Zockerhände");
- „Umskillen · 2.000 €": setzt `skills` auf `[]`, `skillRespecs++`, Punkte bleiben (Bestätigungspanel wie beim Reset);
- Meta-Bereich „Insider" mit den gewonnenen Upgrades (Icon, Name, Text) oder „Noch keins – schließe ein Story-Teil ab."

### 3.3 Insider-Wahl

In `Story.finish(end)` nach dem Statistik-Panel und vor der Wahl „Nächste Story / Zum Titel": wenn `!meta.insiderClaimed[story.id]`, Szene `insider.offer` (Hintergrund `hinterzimmer`, Figur `insider` neu: „Der Insider", 🕵️): ein Panel mit Vorstellung, ein Panel mit drei Choices (Name + Kurztext). Gewählt → `meta.insider.push(id)`, `meta.insiderClaimed[story.id] = true`, `State.save()`, Toast. Sind keine ungezogenen Upgrades mehr übrig, entfällt die Szene (Toast „Der Insider hat nichts Neues.").

Titel-Trophäen-Panel: Abschnitt „Insider" mit den gewonnenen Upgrades.

### 3.4 Spiele

- **Roulette:** ausgegraute Zellen (`.rcell.excluded`, keine Chips möglich) und gedimmte Kesselfelder; Hinweis unter dem Tisch „Croupier-Auge: 12 Zahlen fallen nicht".
- **Pferde:** markierter Runner mit „🚫 lahmt"; Auswahl dieses Pferds bleibt möglich, wird aber im Status gewarnt.
- **Blackjack:** neben dem Kartenschlitten „🔥 Deck heiß" / „❄️ Deck kalt" (nur mit Kartenzähler); Status nennt 3:2 bzw. 1,2:1.
- **Slots:** nach einer Niete erscheint über jeder Walze „Festhalten" (nur wenn `mechRespins ≥ 5`); Klick hält die Walze, dreht die anderen zwei ohne neuen Einsatz; `mechRespins = 0`.
- Bar: Bier-Knopf zeigt „(3/4)" mit Eisenmagen.

## 4. Technik

- Neuer Block `perk-rules` (nach `gear-rules`): Kataloge, `XP_LEVELS`, `INSIDER_CAP`, `xpLevel`, `skillPointsFree`, `canPickSkill`, `mods`, `insiderDraw(meta, rng)`, `effectiveInsider`, `deckHot`, `pickExcluded(rng)` (12 Zahlen aus 1–36), `pickLoser(selected, rng)`.
- Neuer Block `perks` (nach `mugging`): `Perks.addXp(n, why)`, Bus-Listener für XP, Level-Up-Toast, `Perks.pick(id)`, `Perks.respec()`, `Perks.offerInsider(storyId)`, `Perks.renderBadge()`; Screen `skills`.
- Regeln lesen `Rules.mods(State.s, State.meta)` an den Aufrufstellen; reine Funktionen bekommen `mods` als Parameter (Default = neutral), damit alte Tests unverändert laufen.
- `Roulette.buildTable` markiert `insiderExcluded`; `Horses.start` zieht den Verlierer; `Blackjack` berechnet `natural`/`hot`; `Slots` Festhalten-Logik.
- `State.reset` bzw. Neues Spiel: `insiderExcluded` neu ziehen, wenn Croupier-Auge aktiv; beim Erwerb des Upgrades sofort ziehen.
- README: Skills, Insider, XP-Quellen, Deckel.

## 5. Tests

- Node: `xpLevel` (Schwellen, Punkte, über Level 6), `canPickSkill` (kein Punkt, Konflikt, doppelt, voll), `mods` neutral / einzelne Skills / Insider / Stapelung (Zins-Additionen, mafiaSpins-Maximum, Limit-Untergrenze), jeder Hook aus §2.7 mit und ohne `mods`, `rouletteRoll` mit Ausschluss fällt nie in die Liste (1.000 Würfe, Sequenz-rng), `pickExcluded` liefert 12 verschiedene aus 1–36, `pickLoser` nie das gewählte, `deckHot`, `insiderDraw` (3 ungezogene, weniger wenn Pool kleiner, nie gewählte), `effectiveInsider`, Katalog-Validierung (jeder Skill hat genau einen Licht- und einen Schatten-Text, jedes `mods`-Feld ist in der Neutralliste bekannt).
- Browser-Playtest (`scenario_perks`): XP per Spins bis Level 2 → Badge pulsiert → Skill wählen → Karte „Aktiv"; Umskillen kostet 2.000 €; Konflikt-Grund sichtbar; Story-Ende (per `?ending`) zeigt Insider-Wahl, Meta enthält die Wahl, beim zweiten Ende derselben Story keine Wahl; Croupier-Auge: 12 `.rcell.excluded`, Kugel fällt bei 200 Stub-Würfen nie in die Liste; Stallbursche markiert einen Runner ≠ gewähltes Pferd; Mechaniker: Festhalten erscheint nach Niete bei `mechRespins ≥ 5`. Screenshots `skills.png`, `insider-offer.png`, `roulette-croupierauge.png`.

## 6. Ablauf

Branch `feature/insider-skills` im Worktree; Umsetzung per Plan und Subagenten; Merge nach `main` und Push **nur nach ausdrücklicher Freigabe**.
