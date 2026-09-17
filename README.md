# KELLER 37

Ein satirisches Casino-Lebenssimulations-Spiel in einer einzigen HTML-Datei. Fünfzig Euro in der Tasche, sechs Türen, ein Wirt, der alles schon gesehen hat – und Chantal-Monique, Don Vito und der Doc warten auch schon.

**Spielen:** `keller37.html` doppelklicken. Keine Installation, kein Build. Läuft offline (Google Fonts sind optional).

## Was drin ist

- **Sechs Spiele:** Roulette mit Setztisch und laufender Kugel, Slots mit echten Walzen, Pferderennen mit Live-Kommentar, Russisches Roulette gegen Igor, Blackjack am Filztisch, Post austragen als ehrlicher Ausweg. Beim Roulette Chips mit dem gewählten Wert auf Zahlen und Außenfelder legen (mehrere gleichzeitig), „Chip zurück", „Tisch leeren" oder „Wie zuletzt" nutzen; ein Dreh wertet alle liegenden Chips auf einmal aus.
- **Leben:** Villa kaufen, auf Tinder Chantal-Monique heiraten, geschieden werden, Therapie zahlen, einen Dealer anheuern. Bier und Brownies an der Bar. Eine Niere fürs Hinterzimmer.
- **Kredite:** Bank (8 % Zinsen pro Spin, Limit 3.000 €, nur ein Kredit auf einmal) oder Don Vito (5 Spins Frist, danach der Doc).
- **Anlagen:** Festgeld +8 % nach 6 Spins (10 % Risiko), Aktien +100 % nach 2 Spins (85 %), Trickbetrug +50 % nach 10 Spins (55 %) – je Sorte eine laufende Anlage.
- **Stadt:** Autohaus (Audi-Linie senkt das Überfallrisiko und erhöht die Fluchtchance, Mercedes-Linie hebt Bank-Limit und senkt die Zinsen) und INTERSPORT (Laufschuhe verbessern die Flucht, bringen mehr Zeit/Lohn beim Postboten und helfen bei den Job-Minispielen). Ein neues Auto nimmt das alte mit 50 % seines Preises in Zahlung, Schuhe gibt es nur zum vollen Preis.
- **Überfälle & Stärke:** auf dem Weg in den Keller kann es einen Überfall geben – Kämpfen, Wegrennen oder Zahlen. Ein Kampf (gewonnen oder verloren) erhöht 💪 Stärke; Stärke verbessert die Kampfchance und den Türsteher-Bonus, schaltet den Job „Eintreiber" frei und macht ab 10 gefürchtet (seltener Ziel für Überfälle).
- **Cutscenes:** 31 Visual-Novel-Szenen mit 13 Charakteren, Typewriter-Text, Entscheidungen und Effekten.
- **Extras:** synthetisierter Sound (Web Audio, keine Dateien), Spielstand in `localStorage`, Game Over mit Statistik, Trophäen, Mobile-Layout, Reduced-Motion.

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

## Dev-Parameter

| URL-Zusatz | Wirkung |
|---|---|
| `?fresh` | beide Spielstände (frei und Story) löschen und neu starten |
| `?screen=slots` | nur freies Spiel: Titelscreen überspringen und direkt einen Screen öffnen (`roulette`, `slots`, `horses`, `russian`, `blackjack`, `postman`, `finance`, `invest`, `life`, `stadt` – bei `stadt` öffnet `&shop=audi|merc|sport` direkt einen Laden). Story-Screens erreicht man stattdessen über `?story=…&job=…` (Mini-Spiele) bzw. nach dem Einstieg per `UI.show('jobs'|'vito')` |
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
```

`Gamble Game.html` ist das Original, aus dem die Mechanik 1:1 übernommen wurde. Spec, Plan, Abnahme-Checkliste und Screenshots liegen unter `docs/superpowers/`.
