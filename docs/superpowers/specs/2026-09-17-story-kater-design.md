# KELLER 37 – Story 2 „Der Kater" und Casino Royal

Datum: 2026-09-17 · Status: abgestimmt · Basis: `keller37.html` @ `57ef394` (main)

## 1. Ziel

Zweite Story für den Story-Modus, als **Fortsetzung** von „Die Schuld", plus ein zweites Spielhaus mit drei neuen Spielen, das auch dem freien Spiel zugutekommt.

1. **Story „Der Kater"** (30 Tage): Hochzeit, Absturz, Alkohol als Glücksquelle und Todesuhr, optional Drogen, Ziel: den Keller vom Wirt kaufen.
2. **Casino Royal**: neues Zimmer in der Stadt, nur mit Auto erreichbar. Drei Spiele: Mega Seven (5-Walzen-Slot), Craps, Glücksrad. Neuer Charakter Madame Sylvie.
3. **Engine-Erweiterungen**, generisch: Story-Reihenfolge/Voraussetzungen, Spielergebnisse als Story-Bedingungen, Story-Glücksmodifikator, Story-Preise, sofortige Enden.

Gambling bleibt der Kern: Die Alkohol-Schleife ist so gebaut, dass das, was den Spieler umbringt (Bier, Brownies), gleichzeitig das ist, was ihn am Tisch gewinnen lässt.

Nicht Teil dieser Spec: Poker, Kauf des Casino Royal (Story 3), Änderungen an bestehenden Keller-Spielen, Bank-/Anlagen-Balance (läuft parallel in „Tisch & Bank").

**Parallelarbeit:** Eine zweite Instanz balanciert gleichzeitig `Rules`-Konstanten (Roulette-Mehrfacheinsatz, Bank, Anlagen). Deshalb: alle Story-Zahlen stehen im Story-Objekt, alle neuen Spiele in eigenen `<script>`-Blöcken, Änderungen an bestehenden Objekten (`Rules`, `Story`, `Life`) auf wenige, klar benannte Hooks beschränkt (Abschnitt 8).

## 2. Voraussetzung und Reihenfolge

- Story-Definition bekommt `requires: 'schuld'`. Die Titel-Tür „Story" zeigt „Der Kater" erst, wenn `State.meta.storyRuns.schuld.endings` mindestens ein Ende enthält; vorher steht an der Tür „🔒 Erst *Die Schuld* beenden".
- `StoryRules.pickStory` überspringt Stories, deren `requires` nicht erfüllt ist. „Nächste Story" nach einem Ende nimmt die **nächste in Definitionsreihenfolge**, deren Voraussetzung erfüllt ist; ist keine mehr übrig, greift wie bisher „am längsten nicht gespielt".
- Neue Bedingung `{ prevEnding: { story: 'schuld', id: 'doc' } }` – wahr, wenn dieses Ende in `storyRuns` der genannten Story erreicht wurde. Mehrere erreichte Enden: das **zuletzt** erreichte gilt für Intro-Varianten (`storyRuns[id].endings` wird chronologisch geführt, `last` = letzter Eintrag).
- Dev: `?story=kater` umgeht die Sperre; `?prev=doc|ehrlich|sturz|taxi` setzt für diesen Lauf das „vorige Ende" (nur mit `?fresh`).

## 3. Kapitel

| Kapitel | Tage | Inhalt |
|---|---|---|
| **1 · Flitterwochen** | 1–3 | Intro (Abschnitt 3.1), Hochzeit im Standesamt ohne Wahl. Start: 2.000 €, Villa (`hasHouse`), Mercedes C-Klasse, Job **Filialleiter** (Abschnitt 6). Alle Keller-Türen und Räume offen, Stadt offen, Casino Royal erreichbar (Auto vorhanden). Chantal in jeder Abend-Szene. Bier kaufbar wie im freien Spiel; Pegel/Leber/Deckel greifen erst ab Flag `abgestuerzt` (alle `buy:*`-, `sleep`- und Zitter-Events tragen `when: { flag: 'abgestuerzt' }`). |
| **2 · Der Morgen danach** | 4–10 | Nacht 3 (Event `absturz`, `at: 'night'`, Tag 3, setzt `flag: abgestuerzt`): Chantal weg, Konto 0, Auto, Villa, Job weg. Krause-Szene: „Ihre Frau hat die Vollmacht genutzt." Wirt-Szene: erstes Bier umsonst. Ab jetzt HUD 🍺 Pegel, 🫀 Leber, Deckel. Jobs: Spüler, Post, Taxi. Tag 6: Doc-Angebot (Abschnitt 5). |
| **3 · Der Wagen** | 11–20 | Kapitel-Intro: Wirt will verkaufen, 40.000 € + Deckel; Ziel im HUD. Therapie kaufbar. Türsteher freigeschaltet; Croupier nach 3 Türsteher-Nächten. Autohaus verkauft wieder → mit Auto öffnet das Casino Royal. |
| **4 · Letzte Runde** | 21–30 | Kauf-Gespräch beim Wirt (Raum `bar`, Knopf „Über den Keller reden", ab Tag 20 jederzeit). Chantal-Rückkehr (Abschnitt 3.2). Eintreiber, falls Vito noch da ist. Leber-Warnung, Enden. |

### 3.1 Intro-Varianten (je 2–3 Panels, dann gemeinsame Hochzeitsszene)

| voriges Ende | Panels |
|---|---|
| `ehrlich` | Vito ist bezahlt, Krause bietet dir die Filiale an („Ein Mann, der 50.000 zurückzahlt, kann eine Filiale führen."). Chantal wartet vor der Bank. |
| `sturz` | Der Wirt hat den Keller, Igor die Tür, du warst Croupier. Der Wirt: „Heirate. Ich hab's auch überlebt." |
| `taxi` | Ein Jahr später, zurück in der Stadt, Papiere auf einen Zahnarzt. Handy: „Ich habe Zeit. – V." Chantal steigt aus demselben Taxi. |
| `doc` | Aufwachen in der Klinik, eine Niere weniger, der Doc: „Sie ist die ganze Nacht geblieben." Start-Leber **70 statt 100**. |

### 3.2 Chantal-Rückkehr

Event, einmalig, `at: 'night'`, ab Tag 21, wenn `balance ≥ 15.000` und `notFlag: 'sucht'`. Wahl: **reinlassen** (`flag: chantalZurueck`) / **rauswerfen** (`flag: chantalWeg`). Mit `sucht` gibt es stattdessen ein kurzes Panel ohne Wahl („Sie hat dich an der Bar gesehen. Sie hat nichts gesagt.").

## 4. Alkohol-Schleife

Story-Variablen, alle im HUD:

```js
vars: { pegel: 0, leber: 100, deckel: 0 }
varMax: { pegel: 3 }   // Bier 4+ erhöht den Pegel nicht mehr, gibt Glück wie Bier 3, kostet trotzdem Leber
```

**Pegel** (Bedarf: 3 Bier pro Tag; mit `sucht`: 3 Bier *oder* 1 Brownie):
- Jeder Bierkauf: `pegel + 1`, Leber −1, Glück wie bisher (`Rules.BEER_LUCK`, `BEER_SPINS`).
- **Erstes Bier des Tages ist ab Kapitel 2 umsonst** – der Wirt schreibt an: `deckel + 50`. Bei 0 € gibt es also genau ein Bier, nicht drei.
- **Schlafen mit ungedecktem Bedarf → Entzugsnacht:** Leber −2 (mit `sucht`: −4), Flag `zitter` für den nächsten Tag. Erste Entzugsnacht spielt eine Wirt-Szene, danach nur Toast.
- Pegel wird jede Nacht auf 0 gesetzt.

**Zitter-Tag** (`flag: zitter`, endet mit dem ersten Bier bzw. Brownie des Tages):
- Story-Glücksmodifikator −15 an allen Tischen. Der Modifikator wird in `Rules.luck` addiert, das Ergebnis darf negativ werden – negatives Glück = Pech: mit |x| % wird ein Gewinn einmal neu ausgewürfelt (kann wieder gewinnen; Roulette-Zahlen wie beim Glück ausgenommen, Einsatzdeckel gilt genauso; `Rules.pech`). Bier-/Brownie-/Auto-Glück rechnen dagegen an. Blackjack und Igor bleiben unberührt.
- Minispiele schwerer: Spüler-Trefferzone −30 %, Taxi-Bremse reagiert 150 ms verzögert, Postbote-Zeit −25 %. Umsetzung über einen Story-Job-Modifikator, den die drei Spiele abfragen (`Story.jobMod()` → `{ spuelerZone: 0.7, taxiBrakeDelay: 150, postTime: 0.75 }`, Standard `{}`).
- Schicht-Jobs zahlen −50 % („Du hast die Gläser fallen lassen").
- Casino Royal verweigert den Einlass (Abschnitt 7).

**Leber** (100 → 0, sinkt nie unter 0, steigt nie):
- Bier −1, Brownie −4, Entzugsnacht −2/−4, Nierenverkauf −20 (der bestehende Kauf bleibt erlaubt – Satire).
- `leber ≤ 30` → einmalige Doc-Warnszene, danach bei jedem Bier ein Toast.
- `leber = 0` → Ende **Das Bett beim Doc**, sofort (Abschnitt 9, `immediate`).
- Rechnung: 3 Bier × 27 Tage = 81 → wer nur das Minimum trinkt, überlebt mit 19 (bzw. stirbt an Tag 27 nach dem `doc`-Ende ohne Therapie – gewollt: dort ist Therapie Pflicht).

**Therapie** (ab Kapitel 3, Preis aus `story.prices.therapy`: 5.000 €, mit `sucht` 8.000 €), einmalig:
- Flag `nuechtern`: kein Pegel-Bedarf, keine Zitter-Tage, Leber sinkt nicht mehr.
- Bier und Brownies sind nicht mehr kaufbar (Bar: „Der Wirt schenkt dir nichts mehr ein."); Bier-/Brownie-Glück entfällt damit von selbst.
- Eigene Szene beim Doc; mit `sucht` muss der Doc dich gehen lassen.

## 5. Drogen

Event `docAngebot`, `at: 'night'`, Tag 6, einmalig, Wahl:
- **„Nein, danke"** → `flag: docAbgelehnt`, Zähler `docNein + 1`. Wiederholung an Tag 12 und 18 mit mehr Druck. Nach dem dritten Nein: Trophäe **Standhaft**, kein weiteres Angebot.
- **„Was kostet das?"** → `flag: sucht`. Ab dann:
  - Brownie 300 € (`story.prices.brownie`), kein Preisanstieg (`brownieNext` ignoriert).
  - Pegel-Bedarf: 3 Bier *oder* 1 Brownie. Entzugsnacht −4 Leber.
  - HUD zeigt 💊 statt 🍺 vor dem Pegel.
  - Chantal kommt nicht zurück; Therapie 8.000 €; eigenes Ende **Der Brownie**.

Sucht ist ein Schalter, kein Zähler, nicht rückgängig.

## 6. Jobs

Kein neuer Job-Typ; ein neuer Schicht-Job und bestehende mit Story-Szenen.

| Kapitel | Jobs | Szenen |
|---|---|---|
| 1 | **Filialleiter bei Krause** (`filialleiter`, Schicht, 400 €, nur in Story 2) | 3 Szenen: Chantal ruft an und fragt nach Kontonummern; Chantal holt „eine Vollmacht" ab; Krause lobt deine Frau. Keine Effekte außer Geld – der Spieler *könnte* es ahnen, kann aber nichts tun. |
| 2 | Spüler, Post, Taxi | – |
| 3 | + Türsteher (100 €), + Croupier (150 €, `jobDone tuersteher ≥ 3`) | Croupier: du siehst die Bücher (Flag `buecher`: der Keller läuft besser, als der Wirt sagt – Kaufpreis-Gespräch bekommt eine dritte Option „Ich kenne die Zahlen": Preis −5.000); Türsteher: Chantal steht mit einem anderen an der Tür; Sylvie kommt in den Keller schauen. |
| 4 | + Eintreiber (150 €, Stärke 4) **nur wenn** `not: { prevEnding: { story: 'schuld', id: 'sturz' } }` | Zwei Szenen mit Vito („Ich bin kein Unmensch. Aber du trinkst.") |

Zitter-Tag-Regeln aus Abschnitt 4 gelten für alle Jobs.

## 7. Casino Royal

**Zugang:** viertes Schaufenster am Ende der Stadt-Straße. Bedingung: `Rules.gear(s).car` vorhanden (jede Klasse). Ohne Auto: Kreideschild „Parkservice only – zu Fuß kommt hier keiner rein." Mit `zitter`: Türsteher-Panel „Sie zittern. Wir haben eine Hausordnung.", kein Einlass.

**Eintritt:** 100 € pro Betreten (Story: einmal pro Tag). Entfällt dauerhaft nach Flag `gastDesHauses` (erster Einzelgewinn ≥ 5.000 € in einem der drei Spiele → Sylvie-Szene).

**Charakter:** `sylvie: { name: 'Madame Sylvie', emoji: '🎩', color: '#e8d5a3' }` – kühl, Direktorin. Story 2: Gast-des-Hauses-Szene, ein Croupier-Szenenauftritt im Keller, ein Panel im Ende „Der Wirt". Story 3 (nicht hier): Verkäuferin des Casinos.

**Hintergrund:** neues `bg: 'royal'` (Samt, Kronleuchter, Gold) im Stil der bestehenden CSS-Hintergründe.

**Freies Spiel:** identischer Zugang (Auto), Eintritt 100 € pro Betreten, `gastDesHauses` als normales Flag in `State.s`. Hub-Sidebar bekommt den Raum „Casino Royal" mit Schloss, solange kein Auto.

### 7.1 Mega Seven (🎰)

- 5 Walzen × 3 Reihen, **5 feste Linien**: drei Waagerechte, V, umgekehrtes V.
- Symbole und Gewichte je Walze: 🍒 Kirsche 30, 🔔 Glocke 25, BAR 18, 💎 Diamant 12, 7️⃣ Sieben 7, ⭐ Scatter 8 (Summe 100).
- Einsatz pro Spin 100 / 250 / 500 / 1.000 € (= 20 / 50 / 100 / 200 € pro Linie). Gewinn pro Linie × Linieneinsatz, von links, 3+ gleiche:

| Symbol | 3 | 4 | 5 |
|---|---|---|---|
| 🍒 | 2 | 5 | 10 |
| 🔔 | 3 | 10 | 25 |
| BAR | 5 | 20 | 50 |
| 💎 | 10 | 40 | 100 |
| 7️⃣ | 20 | 100 | 500 |

- **Freispiele:** 3+ ⭐ irgendwo → 5 Freispiele, alle Gewinne ×2, Nachtriggern erlaubt, max. 15 offene Freispiele. Freispiele kosten nichts, zählen aber als Spins (Zinsen, Timer, `spin:after`).
- Ziel-RTP 90–94 %; der Selbsttest simuliert 200.000 Spins mit festem Seed und prüft den Korridor. Gewichte/Tabelle dürfen zum Treffen des Korridors angepasst werden, nicht die Struktur.
- Glück-Override (`Rules.megaLuckOverride`): mit Wahrscheinlichkeit `luck / 100` wird, wenn keine Linie gewinnt, die Walze gewählt, deren Verschiebung um eine Position die höchste Linie vollendet; gibt es keine, bleibt das Ergebnis.
- UI: Walzen laufen nacheinander aus (wie Lucky Seven), Gewinnlinien leuchten, Gewinntabelle aufklappbar, Freispiel-Zähler.

### 7.2 Craps (🎲)

- Zwei Wetten, beide gleichzeitig möglich:
  - **Pass Line:** Come-out: 7/11 gewinnt 1:1, 2/3/12 verliert, sonst Punkt. Danach: Punkt gewinnt 1:1, 7 verliert, alles andere weiter. Der Einsatz bleibt liegen, bis entschieden ist (nicht abziehbar).
  - **Field:** ein Wurf. 3/4/9/10/11 gewinnt 1:1, 2 und 12 gewinnen 2:1, 5/6/7/8 verliert.
- Einsatz 50–2.000 € je Wette; jeder Wurf ist ein Spin (`spin:before`/`spin:after`, Einsatz = Summe der in diesem Wurf neu riskierten Beträge; ein liegender Pass-Einsatz wird nicht erneut belastet).
- Reine Regeln: `Rules.crapsRoll(rng)`, `Rules.crapsPass(state, dice)`, `Rules.crapsField(dice)`, `Rules.crapsSettle(bets, point, dice)`.
- Glück-Override: mit Wahrscheinlichkeit `luck / 100` wird ein verlierender Wurf (7 in der Punktphase; 2/3/12 im Come-out mit Pass-Einsatz) um ±1 auf einem Würfel verschoben, sofern der Wurf dadurch nicht verliert.
- UI: Filztisch, zwei Würfel rollen (CSS-Animation, Reduced-Motion: Schnitt), „Punkt: 6"-Puck, letzte Würfe als Leiste.

### 7.3 Glücksrad (🎡)

- 24 Segmente: **13 × Bankrott (×0)**, **5 × Hälfte (×0,5)**, **3 × ×1**, **1 × ×2**, **1 × ×5**, **1 × ×10**. Erwartungswert 22,5/24 = 93,75 % RTP.
- Einsatz 100 / 500 / 1.000 / 5.000 €. Auszahlung = Einsatz × Segment (×1 = Einsatz zurück).
- `Rules.wheelSpin(rng)` → Segmentindex; `Rules.wheelPayout(index, bet)`.
- Glück-Override: mit Wahrscheinlichkeit `luck / 100` läuft das Rad bei Bankrott ein Segment weiter (Reihenfolge fest, jedes Bankrott-Segment hat ein Nicht-Bankrott-Segment als Nachbarn – Anordnung im Code so festgelegt).
- UI: Rad dreht 4–6 Umdrehungen mit Ausrollen, Zeiger klackert (SFX), Segment leuchtet; Reduced-Motion: kurzer Schnitt aufs Ergebnis.

### 7.4 Ergebnis-Events

Alle drei melden `Bus.emit('<spiel>:result', { delta, bet, detail })` mit `<spiel>` ∈ `megaslots | craps | wheel`. `Game.settle` wird wie bei den Keller-Spielen verwendet; Trophäen: **High Roller** (Einzelgewinn ≥ 5.000 € im Royal), **Sieben Siebener** (5 × 7️⃣ auf einer Linie), **Gegen die Wand** (Bankrott bei 5.000 € Einsatz).

## 8. Engine-Änderungen

Alle generisch, keine Story-2-Sonderfälle in der Engine.

**StoryRules**
- Bedingung `prevEnding` (Abschnitt 2); `requires` in der Definition; `pickStory(stories, storyRuns, rng)` filtert `requires`; neue `nextStory(stories, storyRuns, currentId)`.
- `validate` prüft zusätzlich: `requires` zeigt auf definierte Story, `prices` nur bekannte Schlüssel, `immediate`-Enden haben keine `fallback`-Markierung.

**Stats** (`story.stats`, gefüllt aus Bus-Events in `Story`): bestehend `earned, gambled, jobs`; neu `wins, streak, bestStreak, biggestWin, beers, brownies, royalVisits`. `streak` zählt Gewinne in Folge über alle Spiele, Verlust setzt auf 0. Ergebnis-Events der Keller-Spiele liefern `{ delta, bet }`; wo das heute fehlt, wird es ergänzt.

**Hooks** (`at:`): neu `sleep` (vor den `night`-Events, für die Pegel-Prüfung), `buy:beer`, `buy:brownie`, `buy:kidney`, `buy:therapy`, `royal:enter`. Events mit `at: 'buy:*'` laufen synchron nach dem Kauf.

**Effekte**: neu `{ luckMod: -15 }` (setzt `story.luckMod`; `Rules.luck(s)` addiert `s.story?.luckMod || 0`), `{ jobMod: {...} }` / `{ jobMod: null }`, `{ price: { brownie: 300 } }`, `{ disable: ['tinder', 'house', 'dealer'] }` / `{ enable: [...] }`.

**Story-Definition**: neue Felder `requires`, `prices` (Startpreise, überschreiben `Rules.PRICES` nur im Story-Modus dieser Story), `disabled` (Käufe, die in dieser Story nicht angeboten werden), `hud[].label` als String oder Funktion `(s) => '💊 Bedarf'|'🍺 Bedarf'` (umgesetzt statt eines separaten `hud[].icon`-Felds; die Funktion bekommt den ganzen Spielzustand `s`).

**Enden**: `immediate: true` → wird nach jeder Effektanwendung und nach jedem `buy:*`-Hook geprüft, nicht nur nachts.

**Rooms**: Zimmer `royal` registriert sich wie `stadt` (Screen, Sidebar-Eintrag, Sperrgrund-Funktion). `Story.unlocked.rooms` steuert es im Story-Modus, im freien Spiel `Rules.gear(s).car`.

## 9. Enden

Priorität von oben; erste erfüllte zählt.

| id | Ende | Prio | Bedingung | Szene |
|---|---|---|---|---|
| `bett` | 🛏️ Das Bett beim Doc | 60, `immediate` | `var leber ≤ 0` | Blackout. Der Doc: „Die Niere war ein Vorschuss." |
| `wirt` | 🍺 Der Wirt | 50 | `flag: gekauft` (Kaufgespräch bestätigt: `balance ≥ 40.000 + deckel`, ab Tag 20; mit `buecher` −5.000) | Schlüsselübergabe; der Wirt bleibt Gast. Mit `chantalZurueck`: sie steht hinter dem Tresen. Sylvie schickt Blumen. Trophäe **Hausherr**. |
| `nuechtern` | 🌅 Nüchtern | 40 | `flag: nuechtern` und Tag 30 | Du gehst am Keller vorbei und bleibst nicht stehen. |
| `brownie` | 💊 Der Brownie | 30 | `flag: sucht`, `leber ≤ 15`, Tag 30 | Der Doc hat dich zum Partner gemacht. Du sitzt an der Bar und wartest auf den Nächsten. |
| `taxi` | 🚕 Chantals Taxi | 20 | `flag: chantalZurueck`, `balance ≥ 15.000`, Tag 30 | Sie fährt mit deinem Geld weg. Wieder. |
| `stammgast` | 🪑 Der Stammgast | 0, `fallback` | Tag 30 | Der Wirt verkauft an jemand anderen. Du trinkst dein Freibier. |

Ende-Erfolge landen wie bisher in `storyRuns.kater.endings` und auf der Trophäenwand.

## 10. Dev-Parameter und Tests

| URL-Zusatz | Wirkung |
|---|---|
| `?story=kater` | Story erzwingen, Sperre umgehen |
| `?prev=doc` | voriges Story-1-Ende für diesen Lauf setzen (mit `?fresh`) |
| `?ending=wirt` | Ende direkt abspielen |
| `?screen=royal&game=craps` | freies Spiel: Casino Royal öffnen, optional direkt ein Spiel (`megaslots`, `craps`, `wheel`) |

**Selbsttest (Node + Browser), nach vorhandenem Muster:**
- Regeln pur: Craps-Auszahlung für alle 36 Kombinationen in Come-out und Punktphase, Field-Tabelle; Mega-Seven-Linienauswertung (3/4/5 gleiche, gemischte Linie, Scatter-Zählung, Nachtriggern-Deckel), RTP-Korridor per Seed; Glücksrad-Segmentsumme = 24, Erwartungswert 93,75 %, Override läuft nie auf Bankrott; alle drei Overrides deterministisch mit `seq()`.
- Story: `validate(STORY_KATER)` leer; `pickStory`/`nextStory` mit `requires`; `prevEnding` mit leerem, einem, mehreren Enden; Pegel-Rechnung (3 Bier decken, 2 nicht, Brownie deckt nur mit `sucht`); Entzugsnacht setzt `zitter`, erstes Bier löscht es; Leber-Verlauf 27 Tage Minimum = 19; `immediate`-Ende bei Leber 0 mitten am Tag; jedes der sechs Enden per konstruiertem Zustand; Eintreiber nur ohne `sturz`; Therapie schaltet Bier ab; Chantal-Event nicht mit `sucht`.
- Fast-Forward-Szenario Tag 1 → 30 wie beim bestehenden Story-Test (`tests/playtest-story.py` bekommt einen Kater-Durchlauf).

## 11. Umsetzungsreihenfolge

1. Engine: `requires`/`prevEnding`/`nextStory`, Stats, Hooks, Effekte, `immediate`, Titel-Sperre – mit Tests.
2. Casino Royal: Regeln der drei Spiele (pur, getestet), dann Screens, Zimmer, Sylvie, Trophäen; im freien Spiel verifizieren.
3. Story „Der Kater": Objekt, Szenen, Filialleiter, Kaufgespräch, Enden; Selbsttest und Playtest.
4. README (Story-Abschnitt, Casino Royal, Dev-Parameter), Screenshots.

Jeder Schritt ist für sich mergefähig; Schritt 2 hat keine Abhängigkeit zu Schritt 1 und kann parallel laufen.
