# KELLER 37 – Story 3 „Die Wäsche"

Datum: 2026-09-18 · Status: abgestimmt · Basis: `keller37.html` @ `6d4b29e` (main)

## 1. Ziel

Dritte Story für den Story-Modus, als **Fortsetzung** von „Der Kater": Der Spieler besitzt den Keller und gerät an den Gangster **Anabi Stash**, der das Casino als Waschmaschine benutzt. Ziel der Story: aus der Gang herauskommen.

1. **Story „Die Wäsche"** (30 Tage, ID `stash`): vier Wäsche-Wochen mit Lieferung, Umsatzziel und Abrechnung; Anabis Zorn als Todesuhr; nächtliche Überfälle, die Automaten zerstören; eine rivalisierende Gang (die Bahnhof-Jungs); Waffe und Schießerei; Kommissar Brandt als Ausweg; sechs Enden.
2. **Baccarat** (Punto Banco) im Hinterzimmer des Kellers – Anabis Tisch, die Umsatzmaschine mit den höchsten Limits im Spiel.
3. **Schießerei „Zieh!"** – Reaktionsduell als eigenes Minispiel (kein Glücksspiel), Waffe als Gear-Stufe.
4. **Engine-Erweiterungen**, generisch: Umsatzzähler, kaputte Türen mit Reparatur, Gear-Slot Waffe, Effekt `call`, Hook `fight:after`, Job-Varianten.

Gambling bleibt der Kern: Die Wäsche zwingt den Spieler, jede Woche große Summen *durch die Tische* zu schleusen – viel setzen, wenig verlieren – und selbst Überfälle werden mit Spielgewinnen repariert.

Nicht Teil dieser Spec: Kauf des Casino Royal (mögliche Story 4), Türsteher anstellen und Chantal als Abholerin (beides als optionale Kleinigkeiten geparkt), Änderungen an bestehenden Spielen jenseits des Umsatz-Hooks.

**Parallelarbeit:** Wie bei Story 2 stehen alle Story-Zahlen im Story-Objekt (`STORY_STASH.N`), alle neuen Spiele und Regeln in eigenen `<script>`-Blöcken, und Änderungen an bestehenden Objekten sind auf die in Abschnitt 8 genannten Hooks beschränkt.

## 2. Voraussetzung und Vorgängerende

- `requires: 'kater'`, `prevEndings: ['wirt', 'nuechtern', 'taxi', 'stammgast', 'brownie']` – nach dem Kater-Ende *Bett* (Tod) ist Story 3 **nicht** erreichbar; die Titel-Tür sagt „🔒 *Der Kater* endete im Bett beim Doc". Tod muss etwas bedeuten.
- Gemeinsame Ausgangslage für alle: **Tag 1 gehört der Keller dir auf dem Papier, und Anabi Stash hat einen Haken in dir.** Je Vorgängerende unterscheiden sich nur Intro-Szene, Startwert `kredit` und ein Flag:

| Kater-Ende | Überleitung (Intro) | `kredit` | Extra |
|---|---|---|---|
| `wirt` | Du bist Hausherr. Anabi kommt von selbst – ein kleines Casino ist die perfekte Waschmaschine. Er „bittet", mit Igor hinter sich. | 0 € | – |
| `nuechtern` | Der Keller steht wieder zum Verkauf, dir fehlt das Geld. Anabi finanziert. | 30.000 € | Flag `trocken`: Bier an der Bar gesperrt („Du trinkst nicht mehr."), Igor-Aktion heißt „Cola mit Igor". |
| `taxi` | Chantal ist mit dem Geld weg, der Kaufvertrag war schon unterschrieben. Anabi springt ein. | 30.000 € | – |
| `stammgast` | Der Käufer war Anabi. Er setzt dich als Strohmann ein: dein Name im Grundbuch, sein Geld. | 50.000 € | – |
| `brownie` | Der Doc stellt dich seinem Lieferanten vor: Anabi. Der Keller ist dein „Gehalt". | 50.000 € | Brownies beim Doc kaufbar (Preis 1.000 €, nur Glück wie im freien Spiel, keine Sucht-Schleife). |

- Der Kredit tut nichts aktiv: Er erhöht die Ablöse (Abschnitt 9) und lässt sich jederzeit per Sidebar-Aktion **„🧾 Kredit abzahlen"** in Schritten von 5.000 € tilgen. Er ist der Haken, nicht die Uhr.
- Dev: `?story=stash` umgeht die Sperre; `?prev=wirt|nuechtern|taxi|stammgast|brownie` (mit `?fresh`).

## 3. Start, HUD, Kapitel

**Start:** 5.000 € Bargeld. Auto und Schuhe aus dem Vorgänger bleiben (`car`, `shoes` werden übernommen), `hasHouse` nein, `weapon: 0`. Offen: alle fünf Keller-Spiele (`roulette`, `slots`, `horses`, `russian`, `blackjack`), Räume `bar`, `doc`, `bank`, `invest`, `life`, `stadt`, `royal`. Das Hinterzimmer (`hinterzimmer`) öffnet Tag 2, die Pfandleihe Tag 8. `disabled: ['tinder', 'house', 'dealer', 'kidney']`. Kein Alkohol-System (Pegel/Leber gibt es in dieser Story nicht); Bier wirkt wie im freien Spiel.

**HUD:** `🧺 Umsatz` (Woche, `fmt: 'money'`, Label-Funktion „12.400 / 20.000"), `😡 Zorn` (0–3, `tone: 'danger'`), `🧾 Kredit` (Geld). Ziel-Text (`goal`) zeigt Woche, Fälligkeit und am Abrechnungstag die Warnung: „Heute Abend: 11.000 € fällig · Umsatz 14.200 / 20.000".

**Kapitel:**

| Kapitel | Tage | Inhalt |
|---|---|---|
| **1 · Der Hausherr** | 1–7 | Intro je Vorgängerende. Tag 1 Nacht: Anabi bringt die erste Lieferung (Abschnitt 4). Tag 2 Morgen: Anabis Leute tragen den Baccarat-Tisch ins Hinterzimmer → Tür `hinterzimmer` offen. Job `eintreiber` (Anabis Schuldner, zwei neue Szenen). Tag 7: erste Abrechnung. |
| **2 · Die Bahnhof-Jungs** | 8–14 | Ab Tag 8 nächtliche Überfälle und Hinterhalte (Abschnitte 5, 6). Stadt: Schaufenster **Pfandleihe Kowalski** (Waffen). Job `kurierfahrt`. Tag 10 Nacht (erzwungen): Anabis Leihpistole, Tutorial-Duell gegen einen Bahnhof-Läufer. |
| **3 · Der Kommissar** | 15–21 | Brandt abends an der Bar (Abschnitt 7). Angebot der Bahnhof-Jungs ab Ruf 2. Igor-Biere laufen (ab Tag 8 möglich). |
| **4 · Abrechnung** | 22–30 | Ablöse-Aktion ab Tag 22, Krieg-Finale ab Tag 25, Razzia ab Tag 26, Flucht ab Tag 20. Letzte Abrechnung Tag 28; Tag 30 Fallback-Ende. |

Lieferungen Tag 1/8/15/22 und Abrechnungen Tag 7/14/21/28 sind `once`-Events `at: 'night'`.

## 4. Die Wäsche-Woche

**Lieferung** (Nacht, nicht ablehnbar): Bargeld → `balance`. `turnover.week` und `turnover.royal` werden auf 0 gesetzt, `woche` +1.

| Woche | Lieferung | Umsatzziel | Rückgabe (110 %) |
|---|---|---|---|
| 1 | 10.000 € | 20.000 € | 11.000 € |
| 2 | 20.000 € | 40.000 € | 22.000 € |
| 3 | 30.000 € | 60.000 € | 33.000 € |
| 4 | 40.000 € | 80.000 € | 44.000 € |

Mit Flag `bahnhof` (Abschnitt 6) gilt ab der **nächsten** Lieferung Umsatzziel × 1,5 (gerundet auf 1.000 €); Lieferung und Rückgabe bleiben.

**Umsatz** = Summe aller Einsätze (`bet`) aus `Game.settle` seit der Lieferung – alle Spiele, Keller, Hinterzimmer und Royal, gewonnen oder verloren. Wieder gesetzte Gewinne zählen. Craps zählt den riskierten Einsatz pro Wurf (die Pass-Linie steht jede Runde erneut im Risiko); Freispiele zählen 0. Eigenes Geld zählt genauso – der Spieler gambelt automatisch selbst mit. Bank und Anlagen bleiben offen, zählen aber nicht als Umsatz: Wer die Lieferung parkt, kassiert Zorn.

**Abrechnung** (Nacht): Der Abholer kommt. `GangRules.abrechnung({ umsatz, ziel, balance, rueckgabe, zorn, kredit })` liefert einen der vier Ausgänge; die Szene erzählt ihn.

| Umsatz ≥ Ziel | Zahlen möglich | Folge |
|---|---|---|
| ✅ | ✅ | `balance −rueckgabe`, **Zorn −1**, **Kredit −5.000** (min 0), **`belege` +1**, `abrechnungenOk` +1. „Ich streich dir was." |
| ❌ | ✅ | `balance −rueckgabe`, **Zorn +1**. „Das Geld ist nicht *durch*, es ist nur *da*." |
| ✅ | ❌ | `balance → 0`, Rest × 1,5 → **Kredit**, **Zorn +1**. |
| ❌ | ❌ | wie oben, **Zorn +2**. |

Zorn ist auf 0–3 gekappt (`varMax`). **Zorn ≥ 3 → Ende `kanal`**, `immediate`. Die Abrechnung läuft vor allen anderen Nacht-Events desselben Tages.

## 5. Dein Keller: Nachtkasse, Überfall, Reparatur

**Nachtkasse** (Morgen-Event täglich, Effekt `call: 'nachtkasse'`): `N.kasseProSpiel` = **250 €** pro intaktem Keller-Spiel (max. 1.250 €/Tag). Hinterzimmer und Royal zählen nicht. Toast: „Nachtkasse: +1.000 € (Slots kaputt)".

**Überfall** (Nacht-Event ab Tag 8, `call: 'ueberfall'`, vor dem Hinterhalt): Chance **25 %**, mit Flag `igor` **15 %**, mit Flag `bahnhof` **0 %** (die Bahnhof-Jungs waren es). Ein zufälliges intaktes Keller-Spiel wird zertrümmert: `broken[door] = preis` (mit `igor` halber Preis, gerundet auf 100 €). Sind alle fünf kaputt, kein Überfall. Morgen-Szene: Igor vor den Scherben. Es gibt höchstens einen Überfall pro Nacht; kaputte Spiele bleiben kaputt, bis der Spieler zahlt – sie können sich stapeln.

| Spiel | Reparatur (`N.reparatur`) |
|---|---|
| Roulette (Kessel) | 6.000 € |
| Blackjack (Tisch) | 5.000 € |
| Slots (Automat) | 4.000 € |
| Pferde (Tableau) | 3.000 € |
| Russisch (Revolver) | 2.000 € |

**Reparatur:** Kaputte Tür ist gesperrt (grau, Grund „Zertrümmert"). In der Lobby ersetzt ein Knopf **„🔧 Reparieren 4.000 €"** die Tür; Klick → `StoryRules.repair(s, door)` zieht den Preis ab, löscht `broken[door]`, Tür sofort offen. Nicht genug Geld: Knopf ausgegraut mit Preis. Var `repariert` zählt reparierte Spiele je Sorte (Trophäe *Hausmeister*).

## 6. Bahnhof-Jungs, Waffe, Schießerei

**Waffe** – Gear-Slot `weapon` (0–3), Kauf im Stadt-Schaufenster **Pfandleihe Kowalski** (nur Story 3, ab Tag 8, Figur *Kowalski*):

| Stufe | Waffe | Preis | Reaktionsbonus | Extra |
|---|---|---|---|---|
| 0 | keine | – | – | Kein Duell möglich: Hinterhalt = Raub. |
| 1 | Gebrauchte Makarov | 15.000 € | 100 ms | |
| 2 | Glock 17 | 35.000 € | 200 ms | |
| 3 | „Die Goldene" (Desert Eagle) | 75.000 € | 300 ms | Hinterhalt-Chance halbiert. |

Nur Aufstieg, kein Verkauf. `weapon` wandert wie `car` nicht in die nächste Story (Story-Start setzt ihn auf 0).

**Schießerei „Zieh!"** (Screen `shootout`, Block `game-shootout`, Regeln in `GangRules`): Straße bei Nacht, zwei Silhouetten. „Warte…" **1,5–4 s** zufällig, dann blitzt **ZIEH!**. Tippen/Klick/Leertaste vor dem Blitz = Fehlschuss, Runde verloren. Sonst `GangRules.duel({ reaction, bonus, foe, rng })`: Spieler gewinnt, wenn `reaction − bonus < foe.base + noise`, `noise` gleichverteilt in ±`foe.spread`. Mehrere Gegner = Runden nacheinander; eine verlorene Runde beendet den Kampf als Niederlage. Ergebnis → `Story.hook('fight:after', { kind, won })`.

| Gegner | Basis | Streuung |
|---|---|---|
| Bahnhof-Läufer (Tutorial) | 380 ms | ± 60 |
| Bahnhof-Junge | 320 ms | ± 60 |
| Kessler (Bahnhof-Boss) | 260 ms | ± 40 |
| Igor | 280 ms | ± 40 |
| Anabi Stash | 220 ms | ± 30 |

**Hinterhalt** (Nacht-Event ab Tag 8, `call: 'hinterhalt'`, nur wenn in dieser Nacht kein Überfall lief, nicht mit `bahnhof`): Chance **15 %** (Waffe 3: 7,5 %). 1–3 Bahnhof-Jungen. Ohne Waffe oder verloren: **20 % Bargeld weg (max. 5.000 €)** und Flag `blauesAuge` → nächster Tag `luckMod −15` (Morgen-Event löscht es abends). Gewonnen: sie rennen, **`ruf` +1**.

**Tag 10 (erzwungen, Nacht):** Anabi drückt dir seine Leihpistole in die Hand (Bonus 100 ms nur für dieses Duell) und schickt dich zu einem Bahnhof-Läufer. Gewonnen: `ruf` +1. Verloren: nur Text. Pistole danach zurück.

**Das Angebot** (K3, `once`, Nacht, `day ≥ 15`, `ruf ≥ 2`, nicht `bahnhof`, Szene mit Wahl): Kessler: „Wasch für uns, dann lassen wir dich in Ruhe."
- **Annehmen:** Flag `bahnhof`. Keine Überfälle und Hinterhalte mehr. Ab der nächsten Lieferung Umsatzziel × 1,5. Bei der nächsten Abrechnung erfährt es Anabi: einmalig **Zorn +1** (Flag `anabiWeiss`). Sidebar-Aktion **„🔫 Anabi stellen"** ab Tag 25 (braucht `weapon ≥ 1`).
- **Ablehnen:** Flag `bahnhofNein`, alles bleibt wie es ist; das Angebot kommt nicht wieder.

**Krieg-Finale** (Aktion `anabiStellen`): Schießerei mit den Gegnern Igor (entfällt mit Flag `igor`) → Anabi. Gewonnen: Flag `anabiTot` → Ende `krieg`. Verloren: Flag `kanal` → Ende `kanal`.

## 7. Kommissar, Igor, Sylvie

**Kommissar Brandt** (Figur, ab Tag 15 abends): Bar-Aktion **„Mit Brandt reden"** (einmalig Einstiegsszene, danach Statusdialog: übergebene Belege, was fehlt). „Drei Belege und ein Datum, dann bist du Zeuge, kein Täter."

**Belege** (`belege`, gesammelt; `uebergeben`, übergeben): +1 pro geschaffter Abrechnung, +1 pro Kurierfahrt-Kontrolle. Bar-Aktion **„Beleg übergeben"** (braucht `belege > uebergeben`, ab Tag 15): `uebergeben` +1; mit **20 %** sieht Igor es → **Zorn +1** (mit `igor` 0 %). Ab **`uebergeben ≥ 3` und Tag ≥ 26**: Sidebar-Aktion **„👮 Razzia auslösen"** → Flag `razzia` → Ende `kommissar`.

**Igor** (ab Tag 8): Bar-Aktion **„Bier mit Igor"** (100 €, einmal pro Tag; `trocken` → „Cola mit Igor"). `igorBiere` +1; beim dritten Flag `igor`: Überfälle 15 %, halbe Reparatur, Belege sicher, Krieg-Finale ohne Igor. Trophäe *Igors Freund*. Bei der Razzia: „Ich hab gewusst, dass du's bist. Ich hab nichts gesagt."

**Sylvie & das Royal:** `turnover.royal` zählt je Woche. `royal:enter`-Events: bei **≥ 10.000 €** einmalig pro Woche die Warnung („Sie spielen anders als sonst. Ich sehe so etwas."), bei **≥ 15.000 €** die Hausverbot-Szene: Flag `royalBann`, Raum `royal` gesperrt (`lockReason.royal` „Hausverbot") bis Story-Ende. Die Prüfung läuft auch in `spin:after` innerhalb des Royal, damit die Grenze nicht erst beim nächsten Betreten greift: Beim Überschreiten wird die aktuelle Sitzung mit der Szene beendet und zur Stadt zurückgeführt.

## 8. Baccarat – Das Hinterzimmer

**Zugang:** Tür **„🂡 Hinterzimmer"** in der Keller-Lobby, existiert nur, wenn die Story sie `enabled` hat (Story 3 ab Tag 2). Nie in `broken`, keine Nachtkasse. Croupier **„Der Stumme"** (Figur, spricht nie – Szenen mit ihm sind Beschreibungen `who: 'du'`).

**Regeln (`BaccaratRules`, rein):** Punto Banco, unendlicher Schuh (jede Karte unabhängig gezogen, wie Blackjack). Wetten **Spieler** 1:1, **Bank** 0,95:1, **Unentschieden** 8:1; Spieler-/Bank-Wette bei Unentschieden zurück. Punktwert = Summe modulo 10, Bildkarten/10 = 0, Ass = 1. Natural (8/9 mit zwei Karten) beendet die Hand. Drittkarte: Spieler zieht bei ≤ 5, steht bei 6–7. Bank: zieht bei ≤ 2 immer; 3: außer Spieler-Drittkarte 8; 4: bei Spieler-Drittkarte 2–7; 5: bei 4–7; 6: bei 6–7; 7: steht; zieht ohne Spieler-Drittkarte bei ≤ 5. RTP: Spieler ≈ 98,8 %, Bank ≈ 98,9 %, Unentschieden ≈ 85,6 %.

**Limits:** `N.baccarat = { min: 500, max: 10000, chips: [500, 1000, 5000, 10000] }` pro Hand über alle Felder. Mehrere Felder gleichzeitig erlaubt (wie Roulette-Mehrfacheinsatz).

**Glück:** wie Craps. `Rules.pech(luck, rng)` würfelt einen Gewinn einmal neu; bei positivem `effectiveLuck` wird eine verlorene Hand mit `luck` % einmal neu gegeben. Beides höchstens einmal pro Hand.

**Ablauf:** Chips setzen → „Geben" → Karten nacheinander aufgedeckt (Spieler 1, Bank 1, Spieler 2, Bank 2, ggf. Drittkarten), Naturals leuchten → Abrechnung über `Game.beginSpin`/`Game.settle` (`game: 'baccarat'`). Zustand an `State.s` gebunden wie bei Craps.

**Trophäen:** 🂡 **Natural** (fünf Naturals in einer Sitzung), 🀄 **Der Stumme nickt** (100.000 € Umsatz im Hinterzimmer über die Story, Var `umsatzHinterzimmer`).

## 9. Jobs

Nur diese zwei Jobs sind in Story 3 freigeschaltet, beide von Anabi.

| Job | Art | Lohn | Regel |
|---|---|---|---|
| 🥊 **Eintreiber** (`eintreiber`, bestehend; neue Szenen `stash.eintr.*` mit Anabis Schuldnern) | Schicht | 1.000 € (Story-`jobOverrides.eintreiber = { base: 1000, requires: null }` – die Stärke-Voraussetzung aus dem Basisspiel entfällt, Anabi fragt nicht) | Pro Schicht **Zorn −1**. Max. **2× pro Woche** (`eintreiberWoche`, Reset bei der Lieferung); danach Job gesperrt mit Text „Anabi hat nicht jeden Tag Schuldner." |
| 💼 **Kurierfahrt** (`kurierfahrt`, neu, ab Tag 8) | Minispiel = Taxi-Screen mit `variant: 'kurier'` | 0 Strafzettel: 3.000 €, 1: 1.500 € | **≥ 2 Strafzettel = Kontrolle**: kein Lohn, **Zorn +1**, **`belege` +1**. Skin: Koffer statt Fahrgäste, „Übergabepunkte" statt Fahrgast-Zähler. |

## 10. Engine-Änderungen

Alle generisch, keine Story-3-Sonderfälle in der Engine.

**Game / Story-Statistik**
- `Game.settle` emittiert zusätzlich `Bus.emit('stake', { bet, game })` vor `win`/`loss`. `Story` hört darauf und ruft `StoryRules.recordStake(s.story, bet, game)`: `turnover.week += bet`, `turnover.royal += bet` für die Royal-Spiele (`megaslots`, `craps`, `wheel`; Liste als Konstante `StoryRules.ROYAL_GAMES`), `turnover.total += bet`. Story-Objekt kann `turnoverGroups` definieren (`{ hinterzimmer: ['baccarat'] }`) → zusätzliche Zähler.

**Kaputte Türen**
- `s.story.broken = { [door]: preis }`. Die bestehende Tür-Prüfung der Story (dieselbe Stelle, an der `unlocked.doors` und `gates` geprüft werden) liefert „gesperrt", solange `broken[door]` gesetzt ist; Sperrgrund „Zertrümmert". `StoryRules.repair(s, door)` → `{ ok, price }`. Lobby rendert für kaputte Türen den 🔧-Knopf.
- Neuer Effekt `{ break: 'slots', price: 4000 }` und `{ repair: 'slots' }` (für Dev/Tests); im Spiel setzt `call: 'ueberfall'` den Zustand.

**Gear**
- `SET_KEYS` + `'weapon'`; `Rules.gear(s).weapon` (0–3). Stadt-Schaufenster `pfandleihe` registriert sich wie `royal` als Story-aktivierbares Element (`story.enabled` enthält `'pfandleihe'`).

**Türen/Räume**
- Keller-Tür `hinterzimmer` (Screen `baccarat`) wird in der Tür-Liste der Lobby definiert, aber nur gerendert/öffnbar, wenn `story.enabled` sie enthält (analog Raum `royal`). Im freien Spiel nicht vorhanden.

**Story-Definition / Effekte / Hooks**
- Neues Feld `fns: { name: (s, ctx) => {...} }` und Effekt `{ call: 'name' }`; die Funktion darf `vars`, `flags`, `balance`, `broken`, `luckMod` ändern und einen Ergebnis-String in `ctx.result` legen, den die folgende Szene liest. `validate` prüft, dass jedes `call` auf eine definierte Funktion zeigt.
- Neuer Hook `fight:after` mit `ctx.fight = { kind, won }`.
- `story.turnoverGroups` (s. o.), `story.varMax.zorn = 3`.
- `prevEndings: [...]` zusätzlich zu `requires`: Story nur wählbar, wenn das zuletzt erreichte Ende der Voraussetzung in der Liste steht; Titel-Tür zeigt sonst den Sperrtext `lockText`.

**Jobs**
- Story-Feld `jobOverrides: { [jobId]: { base, requires, pay } }` überlagert Job-Definitionen nur in dieser Story (`Jobs.def(id)` liest es).
- Job-Definition darf `variant` tragen; `Jobs.start` reicht es an den Screen (`Taxi.start({ variant })`). Taxi-Screen: Variante `kurier` ändert Skin, Zähler-Text und Auszahlungsregel (`GangRules.kurierPay(tickets)` → `{ pay, kontrolle }`), und ruft danach `Story.hook('job:after', { job, tickets, kontrolle })`.

**Figuren:** `anabi` (🕶️), `stumme` (🃏), `kessler` (🚬), `brandt` (👮), `kowalski` (🔧). Vorhanden: `igor`, `sylvie`, `doc`, `wirt`, `chantal`.

**Neue Blöcke:** `gang-rules`, `baccarat-rules` (beide DOM-frei, im Node-Selftest), `game-baccarat`, `game-shootout`, `story-stash`.

## 11. Enden

Priorität von oben; erste erfüllte zählt.

| id | Ende | Prio | Bedingung | Szene |
|---|---|---|---|---|
| `kanal` | ⚰️ Der Kanal | 70, `immediate` | `var zorn ≥ 3` oder Flag `kanal` (Finale verloren) | Igor fährt. Anabi sitzt hinten und sagt nichts. Der Kanal ist ruhig um diese Zeit. |
| `krieg` | 🔫 Der Krieg | 60, `immediate` | Flag `anabiTot` | Kessler klopft dir auf die Schulter. Der Keller gehört dir – und den Bahnhof-Jungs. Trophäe **Schnellste Hand**. |
| `kommissar` | 👮 Der Kommissar | 50, `immediate` | Flag `razzia` (Aktion, `uebergeben ≥ 3`, Tag ≥ 26) | Blaulicht im Keller. Anabi in Handschellen. Brandt: „Der Keller ist Beweismittel. Sie sind frei. Nur nicht hier." Mit `igor` seine Zeile. Trophäe **Kronzeuge**. |
| `abloese` | 💰 Die Ablöse | 40, `immediate` | Flag `frei` (Aktion „Ablöse zahlen": `balance ≥ N.abloese + kredit`, `zorn ≤ 1`, Tag ≥ 22) | Anabi zählt nach, zweimal. Der Stumme nimmt den Tisch mit. Der Keller ist wirklich deiner. Trophäe **Sauber**. |
| `flucht` | 🌍 Die Flucht | 30, `immediate` | Flag `flucht` (Aktion „Abhauen": `car`, `balance ≥ 30.000`, Tag ≥ 20) | Nachts über die Grenze. Der Keller brennt hinter dir – nicht deine Schuld, sagt niemand. |
| `strohmann` | 🧹 Der Strohmann | 0, `fallback` | Tag 30 | Woche 5 kommt. Lieferung 50.000 €. Dein Name steht im Grundbuch, seiner auf dir. |

`N.abloese = 100000`. Enden landen in `storyRuns.stash.endings`. Für eine spätere Story 4 bleibt der Spieler bei `abloese`, `krieg`, `strohmann` Besitzer, bei `kommissar` und `flucht` ohne Keller.

**Trophäen** (`story.trophies`): 🧺 **Waschmaschine** (`abrechnungenOk ≥ 4`), 🔧 **Hausmeister** (alle fünf Spiele mindestens einmal repariert), 🍺 **Igors Freund** (`igor`), dazu die Enden-Trophäen oben und die beiden Baccarat-Trophäen.

## 12. Dev-Parameter und Tests

| URL-Zusatz | Wirkung |
|---|---|
| `?story=stash` | Story erzwingen, Sperre umgehen |
| `?prev=wirt` | voriges Kater-Ende für diesen Lauf (mit `?fresh`) |
| `?day=N` | Starttag (mit `?fresh`) |
| `?weapon=2` | Waffenstufe setzen (Story-Modus) |
| `?ending=abloese` | Ende direkt abspielen |
| `?screen=baccarat` | Hinterzimmer direkt öffnen (im Story-Modus) |
| `?screen=shootout&foe=anabi` | Schießerei gegen einen Gegner (`laeufer`, `junge`, `kessler`, `igor`, `anabi`) |

**Node-Selftest:**
- `GangRules`: Wochenwerte für Woche 1–4 und mit `bahnhof` × 1,5; `abrechnung` alle vier Ausgänge inkl. Kredit × 1,5 und Zorn +2, Kappung 0–3; `nachtkasse` mit 0/2/5 kaputten Spielen; `ueberfall` 25/15/0 % mit festem rng, kein Überfall bei fünf kaputten, halber Preis mit `igor`; `hinterhalt` nur ohne Überfall, 15/7,5 %, Raub 20 % max 5.000; `duel` Fehlschuss vor Blitz, Waffenbonus, Streuung; `kurierPay` 0/1/2 Strafzettel; Royal-Schwellen 10.000/15.000; `WEAPONS` Preise/Boni.
- `BaccaratRules`: Punktwert modulo 10, alle Zeilen der Bank-Drittkarten-Tabelle, Naturals, Auszahlung 1:1 / 0,95:1 / 8:1 und Rückgabe bei Unentschieden, RTP-Simulation 100.000 Hände in Toleranz ± 0,5 Punkte, Pech- und Glück-Redeal höchstens einmal.
- `STORY_STASH`: `validate` leer (Szenen, Jobs, Enden, `call`-Ziele); Intro je Vorgängerende und Sperre nach `bett`; Enden-Priorität `kanal` > `krieg` > `kommissar` > `abloese` > `flucht`; `immediate` bei Zorn 3 mitten in der Nacht → nächste Story sauber; `recordStake` füllt `week/royal/total` und Gruppen; `broken` sperrt Tür, `repair` öffnet und zieht Geld ab; Eintreiber-Limit 2/Woche; Angebot nur mit `ruf ≥ 2`; Razzia-Aktion nur mit `uebergeben ≥ 3` und Tag ≥ 26; Ablöse-Aktion nur mit `zorn ≤ 1`.

**DOM-Selftest:** Hinterzimmer-Tür nur in Story 3; 🔧-Knopf statt Tür bei `broken`, ausgegraut ohne Geld; Stadt zeigt fünf Schaufenster in Story 3; Baccarat-Screen setzt und zahlt aus; Shootout Fehlschuss-Pfad; Taxi-Variante `kurier` zeigt Koffer-Skin.

**CDP-Playtest `scenario_stash`:** Tag 1 Lieferung → Umsatz per Baccarat auf Ziel → Tag 7 Abrechnung ✅/✅ (Zorn 0, Beleg 1) → Tag 8 Überfall per Seed erzwingen → reparieren → Waffe kaufen → Schießerei gewinnen (Reaktion per CDP-Timing) → Tag 15 Brandt, drei Belege übergeben → Tag 26 Razzia → Ende `kommissar`. Zweiter Lauf: zwei Abrechnungen ohne Zahlung → Zorn 3 → Ende `kanal`, sofort, nächste Story sauber.

Screenshots nach `docs/superpowers/screenshots/stash-*.png`.

## 13. Umsetzungsreihenfolge

1. **Engine 3**: `stake`-Event + `recordStake`, `broken`/`repair`, Gear `weapon`, Effekt `call`, Hook `fight:after`/`job:after`, `prevEndings`, Job-`variant`, Figuren – mit Tests.
2. **Baccarat**: `BaccaratRules` (rein, getestet), Screen, Tür `hinterzimmer`, Trophäen.
3. **Schießerei & Pfandleihe**: `GangRules.duel`/`WEAPONS`, Screen `shootout`, Schaufenster, Kurier-Variante des Taxis.
4. **Story „Die Wäsche"**: `GangRules` (Woche, Abrechnung, Nachtkasse, Überfall, Hinterhalt), Story-Objekt, Szenen, Aktionen, Enden; Selbsttest und Playtest.
5. README, Screenshots.

Schritte 2 und 3 hängen nur von 1 ab und können parallel laufen; 4 braucht 1–3.
