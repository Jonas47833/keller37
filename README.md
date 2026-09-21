# KELLER 37

Ein satirisches Casino-Lebenssimulations-Spiel in einer einzigen HTML-Datei. Fünfzig Euro in der Tasche, sechs Türen, ein Wirt, der alles schon gesehen hat – und Chantal-Monique, Don Vito und der Doc warten auch schon.

**Spielen:** `keller37.html` doppelklicken. Keine Installation, kein Build. Läuft offline (Google Fonts sind optional).

## Was drin ist

- **Sechs Spiele:** Roulette mit Setztisch und laufender Kugel, Slots mit echten Walzen, Pferderennen mit Live-Kommentar, Russisches Roulette gegen Igor (5:1 – ein Streifschuss kostet 5× Einsatz und 100 € Spital), Blackjack am Filztisch, Post austragen als ehrlicher Ausweg (eine Schicht endet nach 15 Briefen oder beim ersten Fehler). Beim Roulette Chips mit dem gewählten Wert auf Zahlen und Außenfelder legen (mehrere gleichzeitig), „Chip zurück", „Tisch leeren" oder „Wie zuletzt" nutzen; ein Dreh wertet alle liegenden Chips auf einmal aus.
- **Leben:** Villa kaufen, auf Tinder Chantal-Monique heiraten, geschieden werden, Therapie zahlen, einen Dealer anheuern. Bier und Brownies an der Bar geben Glück (1/2/3 Bier = +9/+14/+18 %, Brownie +40 %) – Bier hält 8 Spins, Brownie 4; es wirkt voll bis 1.000 € Einsatz, darüber anteilig, und nie auf Roulette-Zahlen. Nüchtern hast du 🍀 +5 % Grundglück und jeder Tisch liegt leicht im Plus (~102–105 %); mit drei Bier bei 116–133 % (Rot 120, Craps 118, Mega Seven 121, Baccarat 116, Rad 119, Slots 133 – Slots streuen am stärksten; Glück erzwingt dort ein Paar, aus 🍒🍋🍇 wird es zu 60 % ein Drilling) – 150 € Bier rechnen sich ab ~110 € Einsatz an jedem Tisch. Wer die Bankroll hält, schafft die Story an jedem Tisch zu 75–90 %, wer alles setzt, fällt trotzdem (`tests/balance-sim.mjs`; Balancing 2026-09-21 „Jeder Tisch“: vorher war Rot der einzige Weg – Slots/Mega/Rad/Craps/Baccarat schafften die Story nur zu 11–22 %); negatives Glück ist Pech (Zitter-Tag in Story 2): mit |x| % wird ein Gewinn einmal neu ausgewürfelt. Eine Niere fürs Hinterzimmer.
- **Kredite:** Bank (8 % Zinsen pro Spin, Limit 3.000 €, nur ein Kredit auf einmal) oder Don Vito (5 Spins Frist, danach der Doc).
- **Anlagen:** Festgeld +8 % nach 6 Spins (10 % Risiko), Aktien +100 % nach 2 Spins (85 %), Trickbetrug +50 % nach 10 Spins (55 %) – je Sorte eine laufende Anlage.
- **Stadt:** Autohaus (Audi-Linie senkt das Überfallrisiko und erhöht die Fluchtchance, Mercedes-Linie hebt Bank-Limit und senkt die Zinsen) und INTERSPORT (Laufschuhe verbessern die Flucht, bringen mehr Zeit/Lohn beim Postboten und helfen bei den Job-Minispielen). Ein neues Auto nimmt das alte mit 50 % seines Preises in Zahlung, Schuhe gibt es nur zum vollen Preis.
- **Casino Royal:** am Ende der Straße, nur mit Auto (Parkservice). Eintritt 100 € – bis zum ersten Einzelgewinn ab 5.000 €, dann bist du Gast des Hauses. Fünf Tische mit höheren Einsätzen: **Mega Seven** (5 Walzen, 5 Linien, Kirschen zahlen ab 2, 3 Freispiele), **Craps** (Pass Line und Field, jeder Wurf ein Spin), das **Glücksrad** (24 Felder: ×5, ×3, 2× ×2, 8× Einsatz zurück, 8× Hälfte, 4× Bankrott – 100 % ohne Glück; Glück hebt ein schlechtes Feld aufs nächste gute), **Caribbean Stud** (Ante 100–1.000 €, Mitgehen 2× Ante, Dealer braucht Ass-König, Bonus bis 100:1) und **Sic Bo** (drei Würfel, 29 Felder: Klein/Groß 1:1, Summe bis 60:1, Einzelzahl, Triple 180:1). Madame Sylvie sieht alles. Ein anderer Ort: Art déco in Gold und Schwarz – beim Betreten wechselt die ganze Seite (Kopfzeile, Seitenleiste, Chips) hinter einem Gold-Vorhang, die Lobby ist ein Foyer mit fünf Portalen, Mega Seven hat echte Walzenstreifen (Anlauf, Bremsen, Nachwippen, Stopp-Klack mit steigender Tonhöhe), baut Spannung auf, wenn nach drei Walzen Freispiele oder ein großer Treffer in Reichweite sind (die letzten zwei laufen länger, die Maschine glüht, Herzschlag), feiert BIG WIN ab 10× und MEGA WIN ab 50× Einsatz mit Banner, hochzählendem Betrag und Goldregen, zeichnet Gewinnlinien in Gold, klappt bei Freispielen ein Banner aus und dreht auf Wunsch **Auto ×10** Runden am Stück (stoppt bei Big Win oder leerer Kasse), Craps markiert Einsätze mit Chip-Stapeln, das Glücksrad hat Zahnkranz, Lauflichter und beim Bankrott gehen kurz die Lichter aus. In der Stadt steht die Fassade mit Marquee, Messingschild und – am Zitter-Tag – einem Türsteher. An allen Tischen mit festen Einsätzen (Mega Seven, Craps, Glücksrad, Caribbean Stud, Sic Bo, Baccarat) steht der gewählte Betrag wie im Keller im Feld neben den Chips, der passende Chip ist hervorgehoben.
- **Kater-HUD (Story 2):** Leber als Balken (grün → gelb → rot, pulsiert ab 30), Pegel als drei Bierkrüge, Deckel als Bierdeckel mit Strichliste; am Zitter-Tag zittern Kontostand und Krüge, ein roter Zettel zeigt −15 Glück, das erste Bier beendet es („Ruhige Hände.").
- **Hinterzimmer:** 🂡 Baccarat (Punto Banco) · 500–10.000 € · Spieler 1:1, Bank 0,95:1, Unentschieden 8:1 · nur in Story 3.
- **Überfälle & Stärke:** auf dem Weg in den Keller kann es einen Überfall geben – Kämpfen, Wegrennen oder Zahlen. Ein Kampf (gewonnen oder verloren) erhöht 💪 Stärke; Stärke verbessert die Kampfchance und den Türsteher-Bonus, schaltet den Job „Eintreiber" frei und macht ab 10 gefürchtet (seltener Ziel für Überfälle).
- **Schießerei „Zieh!":** Reaktionsduell gegen einen oder mehrere Gegner (Story 3) – „Bereit", dann warten, bis ZIEH! aufblitzt, dann tippen oder Leertaste; wer vor dem Blitz schießt, hat einen Fehlschuss und verliert sofort.
- **Pfandleihe Kowalski:** ab Story-Freigabe im Autohaus/INTERSPORT-Viertel – drei Waffen (15.000 €, 35.000 € und 75.000 €), die im Duell Vorsprung geben und nur aufgerüstet, nie zurückgetauscht werden können.
- **Cutscenes:** 161 Visual-Novel-Szenen mit 20 Charakteren, Typewriter-Text, Entscheidungen und Effekten.
- **Extras:** synthetisierter Sound (Web Audio, keine Dateien), Spielstand in `localStorage`, Game Over mit Statistik, Trophäen, Reduced-Motion.
- **Handy (≤ 760 px):** Roulette-Tisch hochkant (Zero oben, 1-2-3 nebeneinander, Außenfelder unten), Einsatz-Leiste in festen Zeilen (Stepper / Chips / kleine Knöpfe zu dritt / Hauptknopf volle Breite – auch in Casino Royal), Tab-Leiste mit Icons, Header-Knöpfe in Touch-Größe, die Glück/Level-Zeile klappt beim Scrollen ein. Auf dem Handy entfallen Backdrop-Blur, Filmkorn und die Tür-Schatten, der Screen-Wechsel blendet nur über – das spart Mobile-Chrome das Ruckeln beim Wechsel zurück in den Keller. Am Desktop ändert sich nichts.

### Cutscene-Bühne

Cutscenes spielen auf einer Bühne aus Ebenen (Himmel, Kulisse, Boden, Figuren, Vordergrund): Comic-Figuren als Inline-SVG (20 Figuren, Protagonist mit Schuhen, Anzug in Story 3, roten Wangen nach Bier, blauem Auge, Augenringen bei Mafia-Schulden), 16 Kulissen mit einem lebenden Element (Neon, Regen, vorbeifahrendes Auto, Zug …), eine Sprechblase am Kopf des Sprechers. Die Auto-Regie (`CsDirector.stagePlan`) inszeniert jedes Panel aus `who/mood/bg`: du links, Gegenüber rechts, Sprecher tritt auf, Stimmung bestimmt Pose (`angry` zeigt, `shock` zuckt, `dead` kippt). Optionale Regie-Schlüssel pro Panel: `cast` (Besetzung, `[]` = Erzähler), `enter`/`exit`, `walk: { who, to: left|mid|right|far }`, `pose` (`idle, talk, point, arms-crossed, hands-up, walk, down, flinch`), `cam` (`close|wide|shake`), `shout: 'PÄNG!'`, `pause` (ms), `sfx`, `look: { du: { hurt: 'pflaster'|'kruecke' } }`. Unbekannte Schlüssel sind Testfehler. `Cutscene.instant = true` (Tests/Dev) und `prefers-reduced-motion` schalten Laufwege und Tippen ab.

### Schießerei

Duelle (Story 3: Tutorial, Hinterhalte, Finale; Dev: `?screen=shootout&foe=junge&weapon=2`) laufen in Ego-Sicht: Welt-Canvas mit Kulisse (Bahnhof, Gasse, Keller), der Gegner als Comic-Figur aus dem Cutscene-Rig, unten rechts die eigene Waffe (Makarov, Glock, „Die Goldene"). Ablauf: der Gegner kommt aus dem Dunkel, zieht (Arm hoch + „ZIEH!"), dann zählt der erste Tipp, der ihn trifft (Figur plus 24 px Rand, Touch 32 px). Daneben getippt = Schuss ins Leere, die Uhr läuft weiter; der Gegner schießt von sich aus bei seiner Zeit plus Waffenbonus (`GangRules.foeFiresAt`) – das ist exakt der Punkt, an dem die alte Rechnung verloren hätte, die Balance ist unverändert (`GangRules.resolveRound` ≡ `duelRound` bei einem Treffer). Zu früh getippt bleibt ein Fehlschuss. Treffer: Mündungsfeuer, Blutspritzer, Zeitlupe beim Fall; getroffen werden: roter Rand, Tropfen über der Kamera. Leertaste/Enter schießt mit automatischem Treffer. `prefers-reduced-motion`: keine Zeitlupe, kein Ruck, kein Blitz, Partikel als Standbild.

### Überfall und Russisches Roulette auf der Ego-Bühne

Die Ego-Bühne der Schießerei (`EgoStage`, Alias `DuelStage`) trägt auch die beiden anderen Sonderszenen. **Überfall:** nach „Kämpfen" oder „Wegrennen" öffnet sich ein Vollbild-Einschub in der Gasse – beim Kampf holt der Räuber aus und ein Ring zieht sich um ihn zusammen, beim Wegrennen läuft die Kulisse, der Räuber holt auf, bis rechts die Abzweigung auftaucht. Ein Tipp (Bühne, Leertaste, Enter) im goldenen Fenster des Rings (die letzten 250 von 900 ms) gibt +10 Prozentpunkte auf die Kampf- bzw. Fluchtchance (Deckel 95 %, `GangRules.timingBonus`/`chanceWithBonus`); der Ausgang wird wie bisher gewürfelt, nur der erste Tipp zählt, es gibt keinen Malus. Gewonnen: Faust ruckt, Einschlag, Räuber fällt in Zeitlupe; verloren: seine Faust auf die Kamera, roter Rand, „Du liegst"; entkommen: er schrumpft ins Dunkel; erwischt: Kragengriff. Danach die bekannten Text-Panels, „Zahlen" bleibt reiner Text. **Russisches Roulette:** Ego-Sicht im Hinterzimmer, Igor gegenüber am Tisch, Trommel-Nahaufnahme unten links. In deinem Zug hebt sich der Revolver und dreht in die Mündungssicht; Abzug per Knopf, Tipp auf die Bühne oder Leertaste/Enter. Klick: Kammer grau, der Revolver gleitet zu Igor, der ihn an die Schläfe hebt – Klick: Erleichterung, Knall: Mündungsfeuer, Blut, Fall in Zeitlupe. Dein Knall: Blitz, Ruck, roter Rand, Tropfen, dann der Doc wie bisher. Regeln, Einsatz und Abrechnung sind unverändert. `prefers-reduced-motion`: Ring als Leiste mit Marker, Kulisse steht, Trommel springt, Revolver direkt in Mündungssicht, kein Blitz/Ruck.

## Story-Modus

Neben dem freien Spiel gibt es einen zweiten Modus: eine Geschichte über rund 30 Spieltage
mit eigenen Arbeitsstellen, Kapiteln und mehreren Enden. Der Titelscreen (Neon „Keller 37",
zwei Türen) fragt beim Start, welcher Modus es sein soll; unten links lassen sich Ton und
die Trophäenwand öffnen, ohne einen Modus zu betreten.

- **Titelscreen:** Tür „Story" startet oder setzt eine laufende Story fort (Beschriftung
  zeigt Titel und Tag); Tür „Freies Spiel" lädt den bekannten Sandbox-Spielstand. Ein Wechsel
  zwischen den Modi – über die Tagesleiste („🚪 Titel") im Story-Modus bzw. das Wallet-Icon
  🚪 im freien Spiel – verliert in keiner Richtung Spielstand.
- **Tagesschleife:** Jeder Tag hat einen Morgen (Jobbörse an der Pinnwand: ein Job pro Tag,
  wahlweise „Kein Job heute") und einen Abend (der bekannte Hub, in dem Türen und Räume, die
  die Story noch nicht freigegeben hat, mit Brettern vernagelt sind). „Schlafen" löst die
  Nacht aus – Ereignisse, Kapitelwechsel, Freischaltungen, danach der nächste Tag.
- **Jobs:** drei Mini-Spiele (🍽️ Spüler – Teller im Timing-Fenster treffen; 🚕 Nachttaxi –
  Fahrgäste einsammeln und bei Rot bremsen; 💼 Kurierfahrt – dieselbe Fahrt als Taxi mit Anabis
  Koffer im Kofferraum, Übergabepunkte statt Fahrgäste, Lohn nach Strafzetteln: 0 Strafzettel
  3.000 €, 1 Strafzettel 1.500 €, ab 2 durchsucht die Polizei den Kofferraum – Kontrolle, kein
  Lohn) und mehrere Schicht-Karten-Jobs (🚪 Türsteher, 🃏 Croupier, 💊 Kurier, 👔 Praktikant,
  🩺 Arzthelfer, 🏦 Filialleiter, 🥊 Eintreiber), die jeweils kurze Szenen mit echten
  Entscheidungen zeigen und Geld sowie Story-Variablen verändern.
- **Enden:** Story 1 „Die Schuld" hat vier unterschiedliche Enden, je nachdem wie die 30 Tage
  verlaufen – mehr wird hier nicht verraten.
  Ruf hat vier Stufen (Niemand · Bekannt ab 2 · Respektiert ab 5 · Legende ab 8, Titel im HUD, Toast beim Wechsel). Ab
  „Respektiert" macht Vito ein Angebot (10.000 € vom Zettel gegen seinen Namen – oder ablehnen und Ruf +1), ab „Legende"
  setzt sich Igor abends zu dir und zweifelt an seinem Chef – ein zweiter Weg zum „Sturz" neben den drei Duellsiegen. Erreichte Enden werden pro Story gemerkt; die
  Trophäenwand bekommt einen eigenen Abschnitt für Story-Erfolge. Stories können eine
  Voraussetzung haben (`requires`); der Titelscreen zeigt dann an, welche Story als Nächstes
  startet und welche noch gesperrt ist.
- **Story 2 „Der Kater":** Fortsetzung – erst spielbar, wenn „Die Schuld" ein Ende hat, und der
  Einstieg hängt davon ab, welches. Hochzeit, Absturz, drei Bier am Tag als Pflicht und als
  Glücksquelle, eine Leber als Countdown, der Doc mit einem Angebot, und der Keller, der zu
  kaufen ist. Sechs Enden.
- **Story 3 „Die Wäsche":** Fortsetzung – Voraussetzung ist ein Ende von „Der Kater", das nicht
  „Bett" heißt (Tod beim Doc beendet die Reihe). Jeden Montag bringt Anabi eine Tasche Geld, die
  Lieferung. Bis Sonntag muss das Geld durch die Tische gespielt werden – jeder Einsatz zählt als
  Umsatz, getrennt nach Casino Royal und Hinterzimmer. Am Sonntagabend die Abrechnung: Umsatz und
  Rückgabe werden getrennt geprüft und ergeben einen von vier Ausgängen zwischen „sauber" und
  „beides falsch", die Kredit und Zorn (0–3) verschieben – bei Zorn 3 ist sofort Schluss. Ab Tag 8
  zerschlagen die Bahnhof-Jungs nachts zufällig eine Kellertür (Reparatur kostet, mit Igor als
  Partner halb so viel) oder lauern im Hinterhalt, wo eine Waffe aus der Pfandleihe Kowalski beim
  Reaktionsduell Vorsprung gibt. Ab Tag 15 taucht Kommissar Brandt in der Bar auf: unbemerkt
  übergebene Kassenbelege sammeln sich zum Beweismittel, das die Story als Kronzeuge beenden kann.
  Sechs Enden: **Der Kanal** (Zorn 3), **Der Krieg** (Anabi im Finale erschossen), **Der Kommissar**
  (Razzia nach drei Belegen), **Die Ablöse** (100.000 € plus Restkredit auf einmal), **Die Flucht**
  (ab Tag 20 mit mindestens 30.000 €) und **Der Strohmann** als Fallback nach Tag 30. Story 3
  bringt dafür Umsatzzähler (`stake`), kaputte Türen (`broken`/🔧), Story-Funktionen (`call`),
  Waffen-Slot, `prevEndings` und Job-Overrides – alles generisch für spätere Stories nutzbar.
  Ruf (🔥 im HUD, dieselben vier Stufen wie in Story 1) wächst hier durch saubere Wochenabrechnungen, Eintreiber-Schichten,
  Kredit-Raten und die erste Reparatur je Woche – nicht nur durch Duelle. Ab „Respektiert" bieten zwei Bahnhof-Jungs die
  Wache an (200 € je Nacht, keine Tür geht mehr kaputt; ist die Kasse leer, gehen sie), ab „Legende" kommt Anabi selbst
  und halbiert den Zettel (Zorn auf null) – die Ablöse wird bezahlbar.

## Skills & Insider

Erfahrung durch Spielen: pro Dreh +1 XP, pro Gewinn zusätzlich +1 XP, pro erledigtem Job +10 XP,
pro überstandenem Story-Tag +10 XP, pro neuer Trophäe +25 XP. Die Level liegen bei 150 / 400 / 800 /
1.300 / 2.000 XP – ein normaler Abend bringt ~80, der erste Skill kommt also am zweiten Abend, der
dritte gegen Ende einer 30-Tage-Story (Balancing 2026-09-21; vorher war Max-Level am 4. Tag erreicht). Ein Level-Badge neben dem Glück
in der Kopfzeile zeigt den Fortschritt zum nächsten Level und pulsiert, sobald ein Skill-Punkt
frei ist; ein Klick öffnet den Screen „🧠 Kopf" (Seitenleiste, Sektion „Kopf", nie gesperrt).

Auf Level 2, 4 und 6 gibt es je einen Skill-Punkt – maximal drei Skills gleichzeitig aktiv, von
acht möglichen. Jeder Skill hat eine Lichtseite und einen Haken an anderer Stelle:

| Skill | Lichtseite | Schattenseite |
|---|---|---|
| 🃏 Pokerface | Blackjack: natürlicher Blackjack zahlt 3:2, Push bringt +10 % | Bier gibt kein Glück |
| 🧊 Kalter Kopf | Roulette-Zahlen zahlen 36:1 | Brownie wirkt nur halb |
| 🎰 Zockerhände | Slots: Paar zahlt 1,5× | Bank-Zinsen +2 % |
| 🐎 Pferdeflüsterer | Pferde zahlen 3,3:1 (bis 250 €) | Überfälle 50 % häufiger |
| 🍺 Eisenmagen | 4 Bier möglich (+25 %), Brownie hält 6 Spins | Postbote: −1 s pro Brief |
| 🤝 Verhandler | Bank-Zinsen −2 %, Vito-Frist 7 Spins | Anlagen zahlen 10 % weniger |
| 🐕 Straßenköter | Kampfchance +15 %, Brieftasche ×2 | Bank-Limit −1.000 € |
| 📬 Briefträgerherz | Postbote +1 s und +5 € pro Brief | Slots: Paare zahlen nichts |

Zockerhände und Briefträgerherz schließen sich aus. „Umskillen" im Skill-Screen (2.000 €) macht
alle drei Wahlen rückgängig, die Punkte bleiben frei und lassen sich neu vergeben. Der
Pferdeflüsterer-Bonus ist wie beim Glück gedeckelt (Bonus wirkt voll bis 250 € Einsatz), darüber
verliert nur der Anteil über 3:1 anteilig – nie eine Geldmaschine.

Insider-Wissen kommt dauerhaft und Meta-weit hinzu – pro abgeschlossenem Story-Teil einmalig
eine Wahl aus drei zufälligen Upgrades (Pferde-Tipp, Roulette-Ausschluss, Kartenzählen, Slots-
Festhalten, Bank-Konditionen, Vitos Neffe, Postmeister). Wie beim Glück wirkt alles, was eine
Gewinnchance direkt anhebt, nur bis 250 € Einsatz voll – darüber anteilig, damit es das Spiel
leichter macht, aber keine Geldmaschine wird.

## Dev-Parameter

| URL-Zusatz | Wirkung |
|---|---|
| `?fresh` | beide Spielstände (frei und Story) löschen und neu starten |
| `?screen=slots` | nur freies Spiel: Titelscreen überspringen und direkt einen Screen öffnen (`roulette`, `slots`, `horses`, `russian`, `blackjack`, `hinterzimmer`, `postman`, `finance`, `invest`, `life`, `stadt`, `royal`, `skills` – bei `stadt` öffnet `&shop=audi|merc|sport` direkt einen Laden, bei `royal` öffnet `&game=megaslots|craps|wheel|stud|sicbo` direkt einen Tisch; `hinterzimmer` (Baccarat) zeigt so auch im freien Spiel, z. B. `?fresh&mode=free&screen=hinterzimmer`). Story-Screens erreicht man stattdessen über `?story=…&job=…` (Mini-Spiele) bzw. nach dem Einstieg per `UI.show('jobs'|'vito'|'skills')` |
| `?scene=divorce` | nur freies Spiel: eine Szene abspielen |
| `?selftest` | Regel-Selbsttest im Browser (Ergebnis als Toast und in der Konsole) |
| `?mode=story` \| `?mode=free` | Titelscreen überspringen, direkt in den Modus |
| `?story=schuld` | Story erzwingen (`schuld`, `kater`, `stash`; impliziert `mode=story`) |
| `?day=12` | Story-Tag setzen (nur zusammen mit `?fresh`; überspringt das Intro). Bei `kater` überspringt ein Sprung hinter Tag 3 auch die Absturz-Nacht – das Flag dann per Konsole setzen, wie im Playtest: `State.s.story.flags.abgestuerzt = true` |
| `?job=spueler` | Jobbörse überspringen, Job direkt starten (impliziert `mode=story`; der Job muss freigeschaltet und seine Voraussetzung erfüllt sein) |
| `?ending=sturz` | ein Story-Ende direkt abspielen (nur beim Story-Neustart, z. B. `?fresh&story=schuld&ending=sturz`, `?fresh&story=kater&prev=doc&ending=wirt` oder `?fresh&story=stash&prev=wirt&ending=abloese`) |
| `?prev=doc` | zusammen mit `?fresh&story=…`: setzt das „vorige Ende" der vorausgesetzten Story (für Fortsetzungen, z. B. `?fresh&story=kater&prev=doc` – Intro-Variante nach dem Doc-Ende; bei `stash` steuert `prev` (`wirt`, `nuechtern`, `taxi`, `stammgast`, `brownie` – die Kater-Enden) zusätzlich den Startkredit und Flags wie `trocken`/`brownie`, z. B. `?fresh&story=stash&prev=wirt`) |
| `?mug=1\|junkie\|jugend\|cousin` | erzwingt den nächsten Überfall (`1` bzw. leer: zufälliger Räubertyp; sonst gezielt `junkie`, `jugend` oder `cousin`) |
| `?fresh&mode=free&screen=shootout&foe=junge\|kessler\|igor\|anabi&weapon=N` | Schießerei direkt öffnen, Gegner erzwingen, `weapon` (0–3) setzt die Waffenstufe fürs Duell |
| `?fresh&story=…&weapon=N` | Story-Neustart mit gesetzter Waffenstufe (0–3, siehe Pfandleihe Kowalski) |
| `?dev` | Admin-Panel-Login einblenden (siehe unten); bleibt in der URL stehen, ist kein Einmal-Parameter |

`story`, `day`, `job`, `ending`, `fresh` und `prev` gelten genau einmal: die Engine entfernt sie nach dem Einstieg
aus der URL, damit „Nächste Story" oder ein Reload nicht wieder dieselbe erzwungene Story starten.

### Admin-Panel

`keller37.html?dev` zeigt ein Login (Benutzer + Passwort). Nach der Anmeldung erscheint unten rechts ein
🛠-Knopf, der auf jedem Screen – auch im Casino Royal und in Cutscenes – eine Schublade mit vier Reitern
öffnet. Die Anmeldung hält, bis der Tab geschlossen wird (`sessionStorage`), auch ohne `?dev` in der URL.

| Reiter | Was geht |
|---|---|
| **Werte** | Kontostand, XP, Stärke, Bier-Pegel, Schulden, Waffenstufe setzen; Royal-Gast, Igor, Brownie, Haus, Ehe, Dealer, Niere schalten; Auto/Schuhe wählen; alle Trophäen, alle Insider, Level max; Spielstand oder alles löschen |
| **Screens** | jeden registrierten Screen öffnen (Keller, Casino Royal, Stadt samt Läden, Story-Screens); Schießerei mit Gegnerwahl; Überfall beim nächsten Spin erzwingen. In der Story werden gesperrte Türen/Räume beim Sprung freigeschaltet |
| **Story** | Story mit vorigem Ende, Starttag (1 = mit Intro) und Waffenstufe neu starten; laufende Story: alle Vars und Flags editieren (auch noch nie gesetzte, z. B. `abgestuerzt`), Tag/Phase setzen, jeden Job erzwingen, jedes Ende abspielen, Türen/Räume/Jobs freischalten |
| **Szenen** | alle Cutscenes (Keller und je Story) mit Suche; Klick spielt eine Vorschau **ohne** Effekte auf den Spielstand; unbekannte Platzhalter bleiben als `{{name}}` sichtbar |

Das Panel ist eine Tür mit Schild, kein Tresor: Die Prüfung steht in der Datei (als Hash, nicht im Klartext);
wer die Browser-Konsole öffnet, kommt daran vorbei. Ohne `?dev` bzw. Anmeldung wird nichts davon ins DOM
gelegt – normale Spieler sehen keinen Unterschied (`tests/desktop-diff.py` bleibt 0 px).

Zugangsdaten ändern: in der Browser-Konsole `DevRules.hash('Name:Passwort')` ausführen und das Ergebnis in
`keller37.html` in `DEV_LOGIN_HASH` (Block `dev-rules`) eintragen.

## Tests

```sh
node tests/run-selftest.mjs         # Node-Selbsttest (freies Spiel + Story-Engine)
tests/dom-selftest.sh               # derselbe Selbsttest headless in Chrome (macOS)
tests/screenshot.sh out.png "?screen=roulette"
python3 tests/playtest-story.py     # CDP-Playtest Story-Modus (Chrome, Port 9335)
python3 tests/desktop-diff.py       # Keller-Screens pixelidentisch zu main? (1280×900, Pillow)
python3 tests/mobile-check.py       # Handy-Ansicht 400×800: Screenshots + Layout-Checks (Port 9361)
python3 tests/playtest-dev.py       # CDP-Playtest Admin-Panel: Login, Werte, Screens, Story, Szenen (Port 9371)
python3 tests/perf-trace.py --mobile  # Chrome-Trace je Szene: Paints, Raster, Layouts pro Sekunde (Port 9377)
node tests/balance-sim.mjs          # Auszahlungsquoten je Spiel/Glück/Einsatz + Erreichbarkeit der Story-Ziele (echte Regelblöcke)
```

`balance-sim.mjs` rechnet mit den echten Regelfunktionen: eine RTP-Tabelle (Glück 0 / +20 / +60, Einsatz unter und über dem Cap) und
zwei Spieler-Modelle über Story 1 und 2 (diszipliniert: Bankroll aufbauen, Einsatz ≈ 10 % bis zum Cap, Bier nur wenn es sich rechnet,
Stop-Loss; wild: halbe Bankroll pro Spin). Referenz nach dem Balancing vom 2026-09-20: disziplinierter Spieler erreicht das gute Ende in
Story 1 zu ~45 %, in Story 2 zu ~36 % (bei langen Abenden ~50 %), der wilde zu ~4 % mit 25 Abenden auf null.

`perf-trace.py` misst, was der Browser während Rad-Spin, Walzen, Taxi, Spüler und im Leerlauf pro Frame wirklich tut. Faustregel:
während einer Compositor-Animation (`transform`/`opacity`) sollen Paint und Layout bei ~0 liegen; alles, was `background-position`,
`box-shadow`, `top`/`left` oder `filter` animiert, malt jedes Frame neu und ruckelt auf dem Handy. Die Raster-Millisekunden sind
Software-Raster auf dem Mac, also nur im Vorher/Nachher-Vergleich aussagekräftig. `PATCH="<JS>"` führt vor jeder Szene Code aus
(z. B. ein `<style>`-Experiment), `--timeline` zeigt den Verlauf in 250-ms-Schritten.

`K37_PORT`, `K37_PROFILE`, `K37_SHOTS` überschreiben Port, Chrome-Profilordner und Screenshot-Ordner des Playtests (Default wie oben); `K37_CHROME` zeigt auf ein Chrome-Binary, sonst werden die üblichen Pfade (macOS, `~/.local/opt/chrome-linux64`, apt) durchsucht – nützlich, um mehrere Läufe parallel zu isolieren. `mobile-check.py` prüft pro Screen horizontale Überbreite und Tap-Ziele ≥ 40 px, dazu Roulette-Tisch, Einsatz-Leiste, Tab-Leiste, Header-Einklappen, als Gegenprobe den Desktop-Tisch und den Zonen-Wechsel (Royal/Keller); Screenshots landen in `/tmp/k37mobile` (bzw. `K37_SHOTS`).

Die Cutscene-Bühne bringt eigene Tests mit: `run-selftest.mjs` prüft `stagePlan`, `validatePanels`, `figureHtml`/`duParts` (`CsCast`), `CsSets` sowie „Regie: alle Story-Szenen" node-seitig ohne DOM (295 bestanden, 0 fehlgeschlagen, Stand 2026-09-20). `dom-selftest.sh` ergänzt dazu DOM-Tests, die einen echten Chrome brauchen: „Cutscene-Bühne: Figuren, eine Blase am Sprecher, Regie, Skip-Endzustand", „Cutscene-Bühne: Klick während Auftritt/Kamerafahrt beendet Weg und Zoom sofort – Blase am Endpunkt", „Cutscene-Kamera close: Zoom zielt auf den gemessenen Kopf – auch liegend und schon gezoomt" (Kevin stehend/liegend, schwankendes „du"), „Cutscene-Kamera close in Echtzeit: Kopf aus der Zielpose berechnet, wide zoomt erst nach dem Rückzug", „Cutscene-Bühne in Echtzeit: Umfallen als Keyframe ohne Neuzeichnen, liegend gefunden ohne Fall, kein talking nach Skip, Klick im Auftritt kürzt die pause ab", „Cutscene-Bühne: cam shake wackelt das Overlay und lässt den Zoom stehen; Vordergrund liegt vor den Figuren", „Cutscene-Keyframes (cs*) animieren nur transform oder opacity" und „Regie: alle Keller-Szenen (Cutscene.SCENES) bestehen validatePanels, Sounds im SFX-Register" (332 bestanden, 0 fehlgeschlagen, Stand 2026-09-20).

Trace-Szenario „Cutscene Regie" (`?screen=hub`, `mug.intro` per Skript gestartet – Auftritt, Kamerafahrt, Schreibmaschine) im Vorher/Nachher-Vergleich mit `main` (Raster-Millisekunden/Sekunde, Software-Raster auf demselben Mac; „meistgemalte Elemente" zeigt bei diesem Branch fast nur `.cs-bubble` aus der Schreibmaschine plus einen einmaligen Auftritts-Repaint von `.cs-body`/`.cs-fig-inner` – keine laufenden Figuren- oder Kulissenteile):

| Szene | `main` Desktop | `main` Mobil | Branch Desktop | Branch Mobil |
|---|---|---|---|---|
| Cutscene idle | 5,9 ms | 2,8 ms | 3,8 ms | 3,5 ms |
| Cutscene Regie | 10,4 ms | 10,4 ms | 5,4 ms | 8,4 ms |

`main` malt bei jedem Tipp-Zeichen den ganzen `.cs-box` neu (Skull-Emoji + Text in einem Knoten); dieser Branch trennt Blase und Figur, sodass nur `.cs-bubble`/`.cs-text` neu gemalt werden – die Bühne ist trotz Auftritt und Kamerafahrt nicht langsamer als der Prototyp, meist schneller. Dass „Cutscene idle" mobil von 2,8 auf 3,5 ms/s steigt, liegt an den lebenden Elementen der Kulissen (SVG-interne Keyframes wie Regen, Wellen, Neon), die die Kulisse neu malen – der Prototyp hatte keine Kulissen-Animation. Überspringen zeigt den Text des letzten Panels sofort komplett (die alte Engine tippte ihn noch).

Die Schießerei bringt eigene Tests mit: `run-selftest.mjs` prüft `GangRules.hitTest` (innen/Rand/außen/Touch-Rand), `foeTime`/`foeFiresAt`, `resolveRound` (Fehlschuss vor dem Signal, erster Treffer zählt, `misses`, Bonus, kein Treffer) samt der Balance-Invariante „`resolveRound` ≡ `duelRound` bei genau einem Treffer" sowie `CsCast`-Looks für Bahnhof-Läufer und -Junge mit `gun: true` (Pistole im rechten Arm-Teil). `dom-selftest.sh` ergänzt „DuelStage: Canvas, Gegnerfigur, Waffe; enter/signal/shot/foeDown/foeShoots/flash/unmount; reduced-motion", „Duell in Ego-Sicht: Bühne, Trefferprüfung, Fehlschuss kostet Zeit, Gegner schießt von sich aus, Fehlschuss vor dem Signal" und „Duell: reduced-motion lässt Zeitfaktor bei 1 und ohne Blitz; Duell-Keyframes nur transform/opacity" (Stand 2026-09-21: 315 bestanden node-seitig, 357 im DOM, je 0 fehlgeschlagen); das DOM-Testbudget (`virtual-time-budget`) musste dafür von 30 s auf 60 s angehoben werden. `playtest-story.py` tippt Duelle über den Helfer `__pt.duelShoot()` durch, statt Bildschirmkoordinaten selbst auszurechnen.

Stufe 3 (Überfall/Roulette): `run-selftest.mjs` prüft `GangRules.timingBonus` (vor/im/nach dem Fenster, ohne Tipp, eigenes Fenster) und `chanceWithBonus` (Deckel 0,95) sowie die Posen `windup/temple/relief`. `dom-selftest.sh` ergänzt „EgoStage: Hand-Varianten, Ring, laufende Kulisse, Trommel, …", „Überfall auf der Ego-Bühne: Kampf mit Timing-Treffer (Bonus 0,10), …" und „Russisch Roulette in Ego-Sicht: …" – Headless-Chrome liefert unter `virtual-time-budget` kaum rAF-Frames, darum takten diese Tests die Bühnen-Uhr von Hand (`EgoStage.loop(last + 50)`); Stand 2026-09-21: 323 node-seitig, 371 im DOM, je 0 fehlgeschlagen. `playtest-story.py` tippt den Überfall-Ring über `__pt.egoTap()` und liest den Bonus aus `__pt.lastMug`.

Trace-Szenario „Duell" (`?screen=shootout&foe=junge&weapon=1`, Signal nach 400 ms, Treffer bei 600 ms, Fall in Zeitlupe – alles innerhalb der 4 s): `main` hat kein `DuelStage` und würde am Auslöser-Skript scheitern, darum misst die `main`-Spalte nur das alte Emoji-Panel im Leerlauf nach dem Mounten (kein Trigger). Das alte Panel zeichnet dabei nichts nach – Paint, Raster und Layout bleiben bei 0.

| Szene | `main` Desktop | `main` Mobil | Branch Desktop | Branch Mobil |
|---|---|---|---|---|
| Duell (`main`: altes Emoji-Panel, idle) | 0,0 ms | 0,0 ms | 35,6 ms | 38,7 ms |

Die Raster-Zeit auf dem Branch verteilt sich auf ~46 (Desktop) bzw. ~35 (Mobil) Raster-Tasks über die 4 Sekunden, also rund 0,8–1,1 ms Zeichenzeit pro Frame – unter dem 2-ms-Budget, `MAX_PARTS` musste nicht gesenkt werden. Layout bleibt bei 1,2/s, das entspricht dem einzigen Layout-Lesevorgang (`foeBox()` beim Tipp). Canvas-Zeichnen taucht in Chromes Paint-Trace nicht als Knoten auf (es läuft über RasterTask); unter „meistgemalte Elemente" stehen deshalb nur zwei einmalige DOM-Repaints (Blitztext, Posenwechsel), keine dauerhaften Neuzeichnungen der Figur.

Trace-Szenarien „Überfall Kampf" (`?screen=hub`, `MugAction.brawl(Mugging.TYPES.junkie, 0.5)` per Skript, Tipp nach 1.500 ms) und „Russisch Roulette" (`?screen=russian`, Trommel auf Kammer 6 gestubbt, `Russian.start()` gefolgt von `Russian.pull()`): „Überfall Kampf" hat auf `main` kein Gegenstück – `MugAction` und die Ego-Bühne für den Überfall gibt es dort nicht, das alte „Kämpfen" löste sofort im Dialog aus, ohne eigene Bühne –, die Branch-Werte stehen für sich (≈4 Paint/s, ≈1,5 Layout/s, meistgemalt `div.cs-fig.duel-foe`/`div.cs-body` beim Ausholen und Treffer). Beim Roulette dominiert auf beiden Ständen der Geldzähler `header#wallet` (Nachzählen nach dem Einsatzabzug) die Paint-Liste – auf `main` mit dem alten Emoji-Panel fast identisch (24,2 Paint/s Desktop / 23,8 Mobil, 10,2 Layout/s, `header#wallet` ×37 Desktop / ×36 Mobil, dazu `div.face` ×6/×4 vom Emoji-Panel); die Raster-Zeit sinkt gegenüber `main` deutlich (86,9 ms Desktop / 59,2 ms Mobil statt 35,9 ms / 20,7 ms auf dem Branch), weil das alte Panel (`div.face` ×6) entfällt. `main`-Werte wurden genauso gemessen: eine Wegwerf-Kopie von `main`s `keller37.html` (`git show main:keller37.html`) mit dem unveränderten `perf-trace.py` dieses Branches, da das Szenario (`State`, `Rules.rrCylinder`, `Russian.start`/`pull`) auf `main` unverändert existiert.

| Szene | `main` Desktop | `main` Mobil | Branch Desktop | Branch Mobil |
|---|---|---|---|---|
| Überfall Kampf (kein `main`-Äquivalent) | – | – | 48,7 ms | 65,4 ms |
| Russisch Roulette (`main`: altes Emoji-Panel) | 86,9 ms | 59,2 ms | 35,9 ms | 20,7 ms |

„Überfall Kampf" bleibt bei ≈4 Paint/s und ≈1,5 Layout/s (Desktop wie Mobil); „Russisch Roulette" bei ≈25 Paint/s und ≈11 Layout/s auf beiden Ständen – deutlich über dem Überfall, weil der Wallet-Zähler bei jedem Klick zwischenzählt, aber gegenüber `main` (24,2/23,8 Paint/s, 10,2 Layout/s) fast unverändert, da derselbe Zähler auch dort mitläuft.

`Gamble Game.html` ist das Original, aus dem die Mechanik 1:1 übernommen wurde. Spec, Plan, Abnahme-Checkliste und Screenshots liegen unter `docs/superpowers/`.
