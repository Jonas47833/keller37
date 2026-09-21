# KELLER 37 – Balancing „Jeder Tisch ein Weg"

Datum: 2026-09-21 · Status: abgestimmt · Basis: `keller37.html` @ `529c41b` (main, nach Sic Bo und Ego-Bühne)

## 1. Ziel

Die Story soll leichter werden – nicht durch höhere Quoten allein, sondern dadurch, dass **jeder Tisch ein gangbarer Weg zum Story-Ziel** ist. Heute schafft nur Roulette Rot die Story zuverlässig; wer Slots, Mega Seven, Rad, Craps oder Baccarat mag, verliert die Story fast sicher und erfährt nie, warum.

Vorgaben (Jonas, 2026-09-21):

- Disziplinierter Spieler (Sim-Modell in `tests/balance-sim.mjs`: Bankroll halten, Bier wenn es sich rechnet, 40 Spins/Abend) erreicht an **jedem** simulierten Tisch **Story 1 ≥ 75 %** und **Story 2 ≥ 65 %** – Rot heute (76/69) ist der Maßstab.
- **Auch nüchtern leicht im Plus** (~102–105 %); Bier wird Turbo statt Pflicht.
- Wild spielen (halbe Bankroll pro Spin) darf weiter scheitern.
- Mega Seven wird **abgeflacht** (nicht als Risiko-Spiel belassen); das ×10-Feld am Rad darf entfallen.

Nicht Teil dieser Spec: Story-Texte, neue Skills/Insider, Blackjack/Pferde/Stud/Poker/Sic Bo (sie bekommen nur das Grundglück, weil die Sim sie nicht modelliert), Story 3 in der Sim.

## 2. Befund (Sim, Stand heute, diszipliniert)

| Tisch | nüchtern | 3 Bier | Streuung (× Einsatz) | Story 1 | Story 2 |
|---|---|---|---|---|---|
| Roulette Rot | 98 % | 117 % | 1,0 | 76 % | 69 % |
| Slots | 95 % | 115 % | 3,2 | 16 % | 13 % |
| Glücksrad | 99 % | 114 % | 2,3 | 21 % | 17 % |
| Mega Seven | 98 % | 116 % | 3,9 | 13 % | 11 % |
| Craps (Pass) | 98 % | 110 % | 1,0 | 22 % | 19 % |
| Baccarat (Bank) | 98 % | 108 % | 0,9 | 13 % | 11 % |

Zwei Ursachen: **Streuung** (Slots/Mega/Rad: 2–4× so hoch wie Rot – ein Treffer bringt selten +1, Verlustserien gehen tiefer) und ein **zu schwacher Bier-Vorteil** (Craps/Baccarat: +8–10 Punkte statt +19). Gleiche Auszahlungsquote ergibt nicht gleichen Story-Erfolg; deshalb wird je Tisch anders gedreht.

Mega Seven im Detail: 70 der 98 Prozentpunkte kommen aus Freispielen, das Basisspiel zahlt 27 %; 70 % der Drehs verlieren den ganzen Einsatz.

## 3. Regeländerungen

### 3.1 Grundglück (`Rules.BASE_LUCK = 5`)

`Rules.luck(s, mods)` startet bei `Rules.BASE_LUCK` statt 0. Alles andere (Bier, Brownie, Ausrüstung, Story-Modifikator, `effectiveLuck`-Deckel bei 1.000 €) bleibt. Damit liegt jeder Tisch nüchtern bei 102–105 %.

- Kopfzeile zeigt 🍀 +5 %.
- Zitter-Tag (Story 2, `luckMod −15`) ergibt netto −10; der rote Zettel zeigt weiter den Story-Wert −15.
- Tests, die nüchtern `Rules.luck(s) === 0` erwarten, prüfen auf `Rules.BASE_LUCK`.

### 3.2 Craps – Glück gewinnt den Verlustwurf (`RoyalRules.crapsLuckOverride`)

Bei positivem Glück und Pass-Line-Einsatz, wenn der Wurf verliert (Come-out 2/3/12 bzw. 7 bei Punkt):

1. Mit `luck × CRAPS_WIN_SHARE` % (`RoyalRules.CRAPS_WIN_SHARE = 0.3`) wird der Wurf zum **Gewinnwurf**: bei Punkt ein Wurf mit Summe = Punkt, im Come-out 7 oder 11 (je 50 %). Würfelpaar: das erste `[a, want − a]` mit `1 ≤ a, want − a ≤ 6`.
2. Sonst wie heute: mit `luck` % wird ein Würfel um ±1 auf einen nicht verlierenden Wurf geschoben.

Pech und Field-Wette unverändert. Ein zusätzlicher `rng`-Aufruf nur im Verlustfall bei Glück > 0.

### 3.3 Baccarat – bis zu drei neue Hände (`BaccaratRules.luckOverride`)

Bei positivem Glück und verlierender Hand: mit `luck` % wird neu gegeben, **bis zu `BaccaratRules.LUCK_REDEALS = 3`-mal**, bis die Hand nicht mehr verliert (heute: genau einmal). Pech unverändert.

### 3.4 Glücksrad – neue Felder, Glück hebt aufs nächste Feld ≥ 1

`RoyalRules.WHEEL.SEGMENTS` (24 Felder, Zeigerreihenfolge):

```
[0, 5, 0.5, 1, 0.5, 2, 0, 1, 1, 1, 0.5, 3, 0, 1, 0.5, 1, 0.5, 2, 0, 1, 0.5, 1, 0.5, 0.5]
```

Zusammensetzung: ×5, ×3, ×2, ×2 · **8× Einsatz zurück (×1)** · 8× Hälfte (×0,5) · **4× Bankrott (×0)**. Summe 24,0 → 100 % ohne Glück (heute: ×10/×5/×2, 13× Hälfte, 8× Bankrott, Summe 23,5). Das ×10-Feld entfällt, höchstes Feld ist ×5.

`RoyalRules.wheelLuckOverride`: Bei positivem Glück und einem Feld **< 1** (heute: nur = 0) wird mit `luck` % das nächste Feld **≥ 1** im Uhrzeigersinn genommen, bis 2 Felder weiter; gibt es keines, bleibt das Feld. Pech: wie heute, ein Feld > 0 fällt mit `|luck|` % auf ein Bankrott-Feld in Reichweite 2. Die Reihenfolge der Segmente ist balancerelevant (Sim-Werte gelten für genau diese Liste), weil die Reichweite 2 entscheidet, welche Felder Glück erreicht.

Tafel/Legende zeigt ×5 ×3 ×2 · Einsatz zurück · Hälfte · Bankrott; Zahnkranz/Lauflicht/Bankrott-Blackout unverändert.

### 3.5 Slots – Paar 1,4×, flachere Drillinge, öfter Drilling aus Glück

- `Rules.NEUTRAL_MODS.slotPairMult = 1.4` (heute 1,2). Skill „Zockerhände" (`slotPairMult 1.3`) wird auf **1,5** angehoben, damit er weiter ein Plus ist; „Briefträgerherz" (Paare zahlen nichts) bleibt 0.
- `Rules.slotMultiplier`: Drillinge **5 / 10 / 19 / 40** für 🍒🍋🍇 / 🔔 / 💎 / 7️⃣ (heute 6/20/25/40).
- `Rules.SLOT_LUCK_TRIPLE = 0.6` (heute 0,12): ein vom Glück erzwungenes Paar aus 🍒🍋🍇 wird zu 60 % ein Drilling.

### 3.6 Mega Seven – abflachen

Ziel: Geld aus den Freispielen ins Basisspiel; Trefferquote 40 % statt 16 %, Streuung 1,3 statt 3,9.

**Auszahlung je Linie** (`RoyalRules.MEGA.PAY`, Index = Anzahl in Folge ab Walze 1; Linieneinsatz = Einsatz/5):

| Symbol | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| 🍒 | **2** | 5 | 8 | 12 |
| 🔔 | – | 5 | 10 | 20 |
| BAR | – | 6 | 12 | 25 |
| 💎 | – | 8 | 20 | 50 |
| 7️⃣ | – | 10 | 30 | 100 |

Ein 3er zahlt damit mindestens den Einsatz zurück (heute 0,4×). **Kirschen zahlen ab 2 in Folge** (0,4× Einsatz): `megaLineWins` nimmt eine Linie, sobald `PAY[sym][count] > 0` (statt `count >= 3`). 5er 7️⃣ = 20× Einsatz (heute 100×).

**Gewichte** `RoyalRules.MEGA.WEIGHTS = [36, 18, 14, 6, 4, 3]` für 🍒 🔔 BAR 💎 7️⃣ ⭐ (heute 30/25/18/12/7/8).

**Freispiele:** `FREE_SPINS = 3` (heute 5), `FREE_MULT = 1` (heute 2), `FREE_MAX = 9` (heute 15). Scatter-Auslösung (≥ 3 ⭐ im Raster) unverändert. Freispiel-Banner und Tafel nennen „3 Freispiele" ohne „×2"; `megaWin` multipliziert in Freispielen mit `FREE_MULT` (jetzt 1).

**Glück** (`RoyalRules.megaLuckOverride`): Bei positivem Glück und Niete wird mit `luck × MEGA_LUCK_GAIN` % (`RoyalRules.MEGA.LUCK_GAIN = 1.5`) **bis zu `MEGA.LUCK_REROLLS = 3`-mal neu gedreht**, bis das Raster eine Gewinnlinie hat. Der heutige Walzen-Schub (`megaShift`) entfällt als Glücks-Eingriff (bleibt als Funktion, falls anderswo genutzt – sonst löschen). Pech unverändert (Gewinn wird mit `|luck|` % neu gedreht). Präsentation (Spannungs-Walzen, BIG/MEGA WIN ab 10×/50×, Auto ×10) unverändert.

### 3.7 Roulette

Keine Regeländerung; profitiert nur vom Grundglück.

### 3.8 Russisches Roulette – Igor zahlt 5:1 (Nachtrag, Jonas 2026-09-21)

Heute: du ziehst zuerst, sechs Kammern, abwechselnd → 50/50; Igor liegt → +Einsatz, du → −Einsatz −100 € Spital. Bei 10 € Einsatz riskiert man 110 für 10.

Neu: `Rules.RR_MULT = 5`.
- `Rules.rrStake(bet) = bet × RR_MULT` – das liegt auf dem Tisch und wird bei Duellstart treuhänderisch abgezogen (`Game.beginSpin(Rules.rrStake(bet))`); der MAX-Chip setzt `floor(maxBet / RR_MULT)`.
- `Rules.rrDelta('igor', bet) = +bet × RR_MULT`; `Rules.rrDelta('player', bet) = −(bet × RR_MULT + HOSPITAL_RR)`.
- 10 €: +50 / −150 (67 %) · 100 €: +500 / −600 (91 %) · 1.000 €: +5.000 / −5.100 (99 %). Hohe Einsätze fast fair, kleine bestraft das Spital – Nervenkitzel mit Preis in beide Richtungen. Kein Glückseingriff (die Kugel bleibt Zufall).
- `rr:result` meldet weiter `{ victim, bet }` mit dem Einsatz (nicht dem Fünffachen); `stake` (Umsatz Story 3) zählt den Tischeinsatz `rrStake(bet)`.
- Texte: Tafel „Igor zahlt 5:1 · Streifschuss kostet 5× Einsatz + 100 € Spital", Tür-Tag „Duell · 5:1", Statuszeilen mit den echten Beträgen aus `rrDelta`. Vitos Prüfung (`forced`) bleibt ohne Geld.

## 4. Erwartete Werte (Sim, diszipliniert, Grundglück 5)

| Tisch | nüchtern | 3 Bier | Treffer % | Streuung | Story 1 | Story 2 |
|---|---|---|---|---|---|---|
| Roulette Rot | 103 % | 122 % | 61 | 1,0 | 93 % | 89 % |
| Craps (Pass) | 102 % | 120 % | 60 | 1,0 | 88 % | 81 % |
| Mega Seven | 105 % | 122 % | 41 | 1,3 | 84 % | 77 % |
| Baccarat (Bank) | 103 % | 117 % | 54 | 0,9 | 82 % | 75 % |
| Glücksrad | 104 % | 121 % | 22 | 1,2 | 81 % | 74 % |
| Slots | 105 % | 138 % | 58 | 2,9 | 80 % | 70 % |

Alle über der Marke, keiner klar der beste; Rot bleibt der ruhigste Weg, Slots der wildeste (deshalb dort 138 % mit Bier). Der wilde Spieler bleibt bei ~5 %. Toleranz bei der Umsetzung: ±3 Punkte Quote, ±5 Punkte Story – die Sim ist mit Seed deterministisch, Abweichungen darüber sind ein Umsetzungsfehler, kein Rauschen.

## 5. Was mit anhängt

- **Tafeln im Markup:** Slots-Tafel (Drillinge 5/10/19/40, Paar 1,4×), Rad-Legende (×5 ×3 ×2, Einsatz zurück, Hälfte, Bankrott), Mega-Tafel (2er 🍒, neue Zahlen, „3 Freispiele").
- **Bar-Hinweis** „Bier lohnt sich ab X €": `Rules.BEER_WORTH_FROM` neu aus `150 / (BEER_SPINS × Vorteil)` mit dem neuen Rot-Vorteil (122 − 103 = 19 Punkte → ~100 €); der Selftest prüft ihn weiter gegen die Rechnung.
- **Selftests:** RTP-Korridore je Tisch auf die neuen Werte. Ohne Glück (Sim, Seed): Slots 95 %, Rot 98 %, Rad 100 %, Mega 102 %, Craps 98 %, Baccarat 98 %; mit Glück 20: Slots 129 %, Rot 117 %, Rad 117 %, Mega 118 %, Craps 116 %, Baccarat 114 % – Korridore je ±4 Punkte um diese Werte. Mega-RTP-Korridor 0,88–0,98 → 0,98–1,06 ohne Glück; Rad-Test „Summe 23,5" → 24,0 und 24 Felder; `Rules.luck` nüchtern = `BASE_LUCK`.
- **`tests/balance-sim.mjs`:** gibt die Tabelle aus Abschnitt 4 (disziplinierter Lauf für **alle** modellierten Tische, Quote nüchtern/+3 Bier, Treffer, Streuung, Story 1/2) standardmäßig aus – sie ist der Beleg für jede künftige Regeländerung.
- **README:** Absätze zu Quoten („nüchtern ~97 %… mit drei Bier ~115 %"), Bier-Schwelle, Glücksrad-Felder, Mega Seven (Freispiele ×2, 500×), Kommentare in den Regelblöcken („Balancing 2026-09-21") auf den neuen Stand.
- **Dev-Panel:** falls es Glück/Quoten anzeigt, Werte prüfen; keine neuen Schalter.

## 6. Tests

### 6.1 Selftests (Block `selftest`, laufen unter Node)

- `Rules.luck` nüchtern = 5; mit 3 Bier 25; Zitter-Tag −10.
- Craps: Seed-Lauf, Verlustwurf bei Punkt 6 wird mit Glück 100 zu Summe 6; mit `CRAPS_WIN_SHARE = 0` greift nur der Schub; Field unverändert.
- Baccarat: bei Glück 100 und Verlust wird bis zu 3× neu gegeben (Stub-`deal`, der erst beim dritten Mal gewinnt).
- Rad: 24 Felder, Summe 24,0, Anzahl 0/0,5/1/2/3/5 = 4/8/8/2/1/1; Glück hebt ein 0,5-Feld aufs nächste ≥ 1 in Reichweite 2, nicht weiter; Pech wie heute.
- Slots: Paar 1,4×, Drillinge 5/10/19/40, `SLOT_LUCK_TRIPLE` 0,6; Zockerhände 1,5.
- Mega: 2 🍒 ab Walze 1 zahlt 2 je Linie, 2 🔔 zahlt nichts; `FREE_SPINS/FREE_MULT/FREE_MAX` = 3/1/9; Glück dreht bei Niete bis 3× neu (Stub-`megaRoll`: 2 Nieten, dann Treffer → Ergebnis ist der Treffer; 3 Nieten → letzte Niete); Pech unverändert.
- RTP-Korridore (Seed, 60.000 Spins) je Tisch laut Abschnitt 4.
- `BEER_WORTH_FROM` gegen Rechnung.

### 6.2 Balance-Sim

`node tests/balance-sim.mjs` vor und nach der Umsetzung; die Nachher-Tabelle steht im Commit.

### 6.3 Browser

`tests/dom-selftest.sh` grün; `tests/playtest-story.py` einmal durch (Story 1 und 2 spielbar, Jobs, Bier-Hinweis sichtbar); Screenshots der drei geänderten Tafeln (Slots, Rad, Mega) für den Commit.
