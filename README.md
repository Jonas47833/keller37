# KELLER 37

Ein satirisches Casino-Lebenssimulations-Spiel in einer einzigen HTML-Datei. Fünfzig Euro in der Tasche, sechs Türen, ein Wirt, der alles schon gesehen hat – und Chantal-Monique, Don Vito und der Doc warten auch schon.

**Spielen:** `keller37.html` doppelklicken. Keine Installation, kein Build. Läuft offline (Google Fonts sind optional).

## Was drin ist

- **Sechs Spiele:** Roulette mit Setztisch und laufender Kugel, Slots mit echten Walzen, Pferderennen mit Live-Kommentar, Russisches Roulette gegen Igor, Blackjack am Filztisch, Post austragen als ehrlicher Ausweg (eine Schicht endet nach 15 Briefen oder beim ersten Fehler). Beim Roulette Chips mit dem gewählten Wert auf Zahlen und Außenfelder legen (mehrere gleichzeitig), „Chip zurück", „Tisch leeren" oder „Wie zuletzt" nutzen; ein Dreh wertet alle liegenden Chips auf einmal aus.
- **Leben:** Villa kaufen, auf Tinder Chantal-Monique heiraten, geschieden werden, Therapie zahlen, einen Dealer anheuern. Bier und Brownies an der Bar geben Glück – es wirkt voll bis 100 € Einsatz, darüber anteilig, und nie auf Roulette-Zahlen (ein Trinkgeld, keine Geldmaschine). Eine Niere fürs Hinterzimmer.
- **Kredite:** Bank (8 % Zinsen pro Spin, Limit 3.000 €, nur ein Kredit auf einmal) oder Don Vito (5 Spins Frist, danach der Doc).
- **Anlagen:** Festgeld +8 % nach 6 Spins (10 % Risiko), Aktien +100 % nach 2 Spins (85 %), Trickbetrug +50 % nach 10 Spins (55 %) – je Sorte eine laufende Anlage.
- **Stadt:** Autohaus (Audi-Linie senkt das Überfallrisiko und erhöht die Fluchtchance, Mercedes-Linie hebt Bank-Limit und senkt die Zinsen) und INTERSPORT (Laufschuhe verbessern die Flucht, bringen mehr Zeit/Lohn beim Postboten und helfen bei den Job-Minispielen). Ein neues Auto nimmt das alte mit 50 % seines Preises in Zahlung, Schuhe gibt es nur zum vollen Preis.
- **Überfälle & Stärke:** auf dem Weg in den Keller kann es einen Überfall geben – Kämpfen, Wegrennen oder Zahlen. Ein Kampf (gewonnen oder verloren) erhöht 💪 Stärke; Stärke verbessert die Kampfchance und den Türsteher-Bonus, schaltet den Job „Eintreiber" frei und macht ab 10 gefürchtet (seltener Ziel für Überfälle).
- **Cutscenes:** 31 Visual-Novel-Szenen mit 13 Charakteren, Typewriter-Text, Entscheidungen und Effekten.
- **Extras:** synthetisierter Sound (Web Audio, keine Dateien), Spielstand in `localStorage`, Game Over mit Statistik, Trophäen, Reduced-Motion.
- **Handy (≤ 760 px):** Roulette-Tisch hochkant (Zero oben, 1-2-3 nebeneinander, Außenfelder unten), Einsatz-Leiste in drei festen Zeilen (Stepper / Chips / Hauptknopf), Tab-Leiste mit Icons, Header-Knöpfe in Touch-Größe, die Glück/Level-Zeile klappt beim Scrollen ein. Auf dem Handy entfallen Backdrop-Blur, Filmkorn und die Tür-Schatten, der Screen-Wechsel blendet nur über – das spart Mobile-Chrome das Ruckeln beim Wechsel zurück in den Keller. Am Desktop ändert sich nichts.

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
- **Jobs:** zwei Mini-Spiele (🍽️ Spüler – Teller im Timing-Fenster treffen; 🚕 Nachttaxi –
  Fahrgäste einsammeln und bei Rot bremsen) und mehrere Schicht-Karten-Jobs (🚪 Türsteher,
  🃏 Croupier, 💊 Kurier, 👔 Praktikant, 🩺 Arzthelfer), die jeweils kurze Szenen mit echten
  Entscheidungen zeigen und Geld sowie Story-Variablen verändern.
- **Enden:** Story 1 „Die Schuld" hat vier unterschiedliche Enden, je nachdem wie die 30 Tage
  verlaufen – mehr wird hier nicht verraten. Erreichte Enden werden pro Story gemerkt; die
  Trophäenwand bekommt einen eigenen Abschnitt für Story-Erfolge.

## Skills & Insider

Erfahrung durch Spielen: pro Dreh +1 XP, pro Gewinn zusätzlich +2 XP, pro erledigtem Job +5 XP,
pro überstandenem Story-Tag +5 XP, pro neuer Trophäe +10 XP. Ein Level-Badge neben dem Glück
in der Kopfzeile zeigt den Fortschritt zum nächsten Level und pulsiert, sobald ein Skill-Punkt
frei ist; ein Klick öffnet den Screen „🧠 Kopf" (Seitenleiste, Sektion „Kopf", nie gesperrt).

Auf Level 2, 4 und 6 gibt es je einen Skill-Punkt – maximal drei Skills gleichzeitig aktiv, von
acht möglichen. Jeder Skill hat eine Lichtseite und einen Haken an anderer Stelle:

| Skill | Lichtseite | Schattenseite |
|---|---|---|
| 🃏 Pokerface | Blackjack: natürlicher Blackjack zahlt 3:2, Push bringt +10 % | Bier gibt kein Glück |
| 🧊 Kalter Kopf | Roulette-Zahlen zahlen 36:1 | Brownie wirkt nur halb |
| 🎰 Zockerhände | Slots: Paar zahlt 1,3× | Bank-Zinsen +2 % |
| 🐎 Pferdeflüsterer | Pferde zahlen 3,3:1 (bis 250 €) | Überfälle 50 % häufiger |
| 🍺 Eisenmagen | 4 Bier möglich (+25 %), Brownie hält 2 Spins | Postbote: −1 s pro Brief |
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
| `?screen=slots` | nur freies Spiel: Titelscreen überspringen und direkt einen Screen öffnen (`roulette`, `slots`, `horses`, `russian`, `blackjack`, `postman`, `finance`, `invest`, `life`, `stadt`, `skills` – bei `stadt` öffnet `&shop=audi|merc|sport` direkt einen Laden). Story-Screens erreicht man stattdessen über `?story=…&job=…` (Mini-Spiele) bzw. nach dem Einstieg per `UI.show('jobs'|'vito'|'skills')` |
| `?scene=divorce` | nur freies Spiel: eine Szene abspielen |
| `?selftest` | Regel-Selbsttest im Browser (Ergebnis als Toast und in der Konsole) |
| `?mode=story` \| `?mode=free` | Titelscreen überspringen, direkt in den Modus |
| `?story=schuld` | Story erzwingen (impliziert `mode=story`) |
| `?day=12` | Story-Tag setzen (nur zusammen mit `?fresh`; überspringt das Intro) |
| `?job=spueler` | Jobbörse überspringen, Job direkt starten (impliziert `mode=story`; der Job muss freigeschaltet und seine Voraussetzung erfüllt sein) |
| `?ending=sturz` | ein Story-Ende direkt abspielen (nur beim Story-Neustart, z. B. `?fresh&story=schuld&ending=sturz`) |
| `?mug=1\|junkie\|jugend\|cousin` | erzwingt den nächsten Überfall (`1` bzw. leer: zufälliger Räubertyp; sonst gezielt `junkie`, `jugend` oder `cousin`) |

`story`, `day`, `job`, `ending` und `fresh` gelten genau einmal: die Engine entfernt sie nach dem Einstieg
aus der URL, damit „Nächste Story" oder ein Reload nicht wieder dieselbe erzwungene Story starten.

## Tests

```sh
node tests/run-selftest.mjs         # Node-Selbsttest (freies Spiel + Story-Engine)
tests/dom-selftest.sh               # derselbe Selbsttest headless in Chrome (macOS)
tests/screenshot.sh out.png "?screen=roulette"
python3 tests/playtest-story.py     # CDP-Playtest Story-Modus (Chrome, Port 9335)
python3 tests/mobile-check.py       # Handy-Ansicht 400×800: Screenshots + Layout-Checks (Port 9361)
```

`K37_PORT`, `K37_PROFILE`, `K37_SHOTS` überschreiben Port, Chrome-Profilordner und Screenshot-Ordner des Playtests (Default wie oben) – nützlich, um mehrere Läufe parallel zu isolieren. `mobile-check.py` prüft pro Screen horizontale Überbreite und Tap-Ziele ≥ 40 px, dazu Roulette-Tisch, Einsatz-Leiste, Tab-Leiste, Header-Einklappen und als Gegenprobe den Desktop-Tisch; Screenshots landen in `/tmp/k37mobile` (bzw. `K37_SHOTS`).

`Gamble Game.html` ist das Original, aus dem die Mechanik 1:1 übernommen wurde. Spec, Plan, Abnahme-Checkliste und Screenshots liegen unter `docs/superpowers/`.
