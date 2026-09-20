# Cutscene-Bühne – Design (Stufe 1 von 3)

Datum: 2026-09-20 · Status: entworfen, vom Auftraggeber abgenommen (Abschnitte 1–4)

## Ziel

Die Cutscenes von KELLER 37 sollen wie Cutscenes wirken, nicht wie Textkästen: sichtbare Figuren (auch der Protagonist), Bewegung, Kulissen mit Tiefe und Leben, Sprechblasen. Alle 306 bestehenden Panels profitieren ohne Textänderung; Schlüsselszenen bekommen Hand-Regie.

Dies ist Stufe 1 von drei. Stufe 2 (Schießerei als Action-Sequenz auf derselben Bühne) und Stufe 3 (Überfall, Russisch Roulette, weitere Sonderszenen) bauen darauf auf und bekommen eigene Specs.

## Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|---|---|
| Figurenstil | **Comic-Figuren als Inline-SVG** (Mimik, Blinzeln, Mundbewegung); kein Pixel-Art, keine reinen CSS-Bausteine, keine Emojis als Figuren |
| Dialog | **Sprechblase am Kopf des Sprechers, immer nur eine** (die des aktuellen Sprechers); kein Dialogkasten unten mehr |
| Protagonist | **Ausrüstung + Zustand sichtbar**: Schuhe, Waffe (nur in Waffen-Posen), Anzug in Story 3; rote Wangen/Schwanken nach Bier, blaues Auge, Pflaster/Krücke über Regie, Augenringe bei Mafia-Schulden |
| Architektur | **Auto-Regie plus optionale Regie-Schlüssel** – kein Zeitleisten-Umbau, keine Zwei-Klassen-Engine |

Referenz-Mockups (nicht versioniert, nur zur Anschauung): `.superpowers/brainstorm/69162-1789863620/content/figure-style-v3.html` (Figuren, Stimmungen) und `layout.html` (Sprechblasen).

## Rahmenbedingungen

- Eine Datei `keller37.html`, keine Bilddateien, keine externen Abhängigkeiten. Alle Grafik als Inline-SVG oder CSS.
- Öffentliche Schnittstelle `Cutscene.play(id, ctx)`, `Cutscene.define(id, panels)`, `Cutscene.bind(event, sceneId)` und Rückgabewerte (Wahl-`value`, `SKIP`) bleiben unverändert. Story-Definitionen, Texte, Wahl-Buttons, Klick-/Tasten-Bedienung, Überspringen bleiben wie heute.
- Bewegung ausschließlich über `transform` und `opacity` (Erkenntnisse aus dem Performance-Umbau vom 2026-09-19). Kein Layout- oder Paint-Trigger pro Frame. Zielgerät: Nothing Phone 3a Pro / Chrome.
- `prefers-reduced-motion: reduce`: keine Laufwege, keine Kulissen-Animation, keine Kamera-Fahrt, Blase erscheint sofort; Verhalten sonst identisch.
- Deutsche Spieltexte.

## 1. Bühne, Ebenen, Kulissen

`#cutscene` bleibt das Overlay (z-index, `hidden`, `body.cs-open`, Sperren für Spiele/Tasten unverändert). Innen wird `cs-stage` durch eine Ebenen-Bühne ersetzt, hinten nach vorn:

| Ebene | Inhalt |
|---|---|
| `cs-sky` | Farbverlauf der Kulisse + „Himmel"-Elemente (Mond, Neonschild, Deckenlampe) |
| `cs-back` | Silhouetten mit Tiefe als Inline-SVG-Formen (Häuserzeile, Barregal, Tresen, Kräne). Ersetzt die Emoji-`prop`s. |
| `cs-floor` | Boden mit Standlinie; Figuren stehen darauf |
| `cs-actors` | Figuren (Abschnitt 2) |
| `cs-front` | Vordergrund für Tiefe: Tresenkante, Regen, Rauch, Gitter |
| `cs-fx` | Flash, Blackout, Partikel (bestehend) |
| `cs-bubble` | genau eine Sprechblase, am Kopf des Sprechers verankert |
| `cs-bar` | Streifen am unteren Rand: Kontostand links (`cs-money`, bestehend), Überspringen rechts (`cs-skip`, bestehend), Wahl-Buttons (`cs-choices`) und Statistik (`cs-stats`, `fx: 'stats'`) mittig; sonst leer und durchsichtig |

`cs-sky` … `cs-actors` … `cs-front` liegen in `cs-world` (Kamera-Rahmen, `contain: paint`), das per `transform` zoomt und schwenkt. Blase, `cs-fx` und `cs-bar` liegen außerhalb und bleiben von der Kamera unberührt.

### Kulissen-Register

`Cutscene.SETS[id] = { back, front, life }` – IDs sind die 16 heutigen `bg`-Werte (`bar, keller, hinterzimmer, strasse, gasse, hafen, hafen-morgen, klinik, bank, standesamt, villa, bahnhof, pfandleihe, autohaus, intersport, royal`), damit kein Panel angefasst werden muss. Unbekannte `bg`-Werte fallen auf `bar` zurück (wie heute). `back/front` sind Funktionen, die SVG-Fragmente liefern; der Himmel ist kein Fragment, sondern eine CSS-Klasse `.cs-sky.<id>` (Farbverlauf); `life` benennt die Ambient-Animation (CSS-Keyframes, transform/opacity).

| Kulisse | Formen | Leben |
|---|---|---|
| bar | Regal mit Flaschen, Tresen, Neon „KELLER 37" | Neon flackert, Rauchfaden steigt |
| keller | Automaten-Silhouetten, Deckenlampe am Kabel | Lampe schwingt leicht, Automaten blinken |
| hinterzimmer | Tisch, Kerze, Aschenbecher | Kerzenschein pulsiert, Rauch |
| strasse | Häuserzeile, Laterne, Bordstein | Auto fährt alle paar Sekunden vorbei (Scheinwerferstreifen) |
| gasse | Mülltonnen, Feuerleiter, Mond | Regen im Vordergrund, Katze huscht |
| hafen | Kräne, Container, Wasser, Mond | Wellen glitzern, Möwe |
| hafen-morgen | wie hafen, Sonnenaufgang | Sonne steigt, Wellen |
| klinik | Liege, Monitor, Deckenlicht | EKG-Linie läuft, Licht flackert |
| bank | Schalter, Kursanzeige, Pflanze | Kursanzeige tickt |
| standesamt | Fenster, Blumen, Fahne | Staub im Lichtstrahl |
| villa | Skyline, Pool, Mond | Stadtlichter blinken, Pool spiegelt |
| bahnhof | Gleise, Uhr, Bank | Zug rauscht durch (Lichter), Uhr tickt |
| pfandleihe | Vitrine, Preisschilder | Leuchtreklame flackert |
| autohaus | Auto auf Drehscheibe | Drehscheibe dreht |
| intersport | Schuhregal, Spot | Spot wandert |
| royal | Kronleuchter, roter Vorhang, Säulen | Kronleuchter glitzert |

Mobil (≤ 760 px Breite): gleiche Ebenen, Figuren ~30 % kleiner, Blase bis 70 % der Bühnenbreite, Blase wird innerhalb der Bühne gehalten (nie abgeschnitten, verdeckt nie den Kopf des Sprechers).

## 2. Figuren

### Rig

Jede Figur ist ein Inline-SVG, `viewBox 0 0 100 180`, `overflow: visible`, mit festen Gruppen: `legs`, `body`, `armL`, `armR`, `neck`, `head` → `face` (`brows`, `eyes`, `mouth`), `hair`, `hat`, `extra`. Feste Ankerpunkte für alle Figuren, damit Animationen geteilt werden:

| Anker | Koordinate |
|---|---|
| Schulter links / rechts (Drehpunkt der Arme) | (21, 82) / (79, 82) |
| Kopfmitte | (50, 46) |
| Mundmitte (Blasen-Anker, Mund-Skalierung) | (50, 61) |
| Standlinie | y = 172 |

Statur wird über `transform` auf `body`/`legs` und einen Kopf-Skalierungsfaktor erreicht, nicht über eigene Pfade.

**Umsetzungsnotiz (Plan):** Eine Figur ist kein einzelnes SVG, sondern acht gestapelte `<svg class="part …">` (Beine ×2, Rumpf, Arme ×2, Kopf, Augen, Mund) mit derselben viewBox in `.cs-fig-inner > .cs-body`. Grund: CSS-Transforms auf SVG-Kindknoten werden nicht vom Compositor übernommen und malen die ganze Figur pro Frame neu; auf HTML-Elementen laufen Posen, Blinzeln und Mundbewegung als Compositor-Animationen. Die Anker gelten unverändert, als Prozent der Figur: Schultern (21 %|79 %, 45,6 %), Hüften (38 %|61 %, 65,6 %), Hals (50 %, 34,4 %), Standlinie (50 %, 95,6 %). Der Effekt `muzzle` wird nicht in Stufe 1 vordefiniert, sondern kommt mit der Schießerei (Stufe 2) – kein toter Code. Kopfposition für Blase und Zoom wird nicht gemessen, sondern aus Figuren-Kasten, Zielpose (liegend: Drehung 85° um 50 %/95,6 %) und klein-Versatz berechnet – unabhängig von laufenden Bewegungen.

### Cast-Register

`Cutscene.CAST[id]` behält `name`, `emoji`, `color` und bekommt `look`:

```js
look: { skin, cloth, accent, hair: 'kurz'|'lang'|'glatze'|…, hat: 'cap'|'fedora'|'zylinder'|null, extra: ['sonnenbrille','zigarre',…], build: 'normal'|'breit'|'schmal'|'klein' }
```

Der Körper wird aus `look` zusammengesetzt; nur Frisuren, Hüte und Extras sind eigene kleine Pfade. Alle 20 heutigen Cast-Einträge bekommen einen Look (`wirt, chantal, vito, igor, doc, krause, makler, schmalz, kevin, postmeister, verkaeufer, du, raeuber, sylvie, insider, anabi, stumme, kessler, brandt, kowalski`). Ein Cast-Eintrag ohne `look` (Dev-Figuren) wird als Emoji-Kopf auf Standardkörper gezeichnet – niemand bleibt unsichtbar.

### Mimik

Stimmungen `calm / angry / happy / shock / dead` (bestehende `mood`-Werte) als Klasse auf dem SVG; Brauen, Augen und Mund liegen als Varianten im SVG und werden per CSS `opacity` umgeschaltet. `dead`: Augen als Kreuze, Kopf hängt, Figur liegt. Dazu automatisches Blinzeln (alle ~4 s) und Mundbewegung, solange die Schreibmaschine läuft.

### Posen

`idle` (Atmen), `talk` (Nicken, Hand hebt sich), `point` (Arm zeigt zum Gegenüber), `arms-crossed`, `hands-up`, `walk` (Beine/Arme pendeln), `down` (kippt um, bleibt liegen), `flinch` (Zucken). Alle transform-only. `will-change: transform` nur solange eine Figur `walk` ausführt.

### Protagonist („du")

- Basis: rote Mütze, braune Jacke, helles Hemd, dunkle Hose (wie Mockup).
- Ausrüstung aus `State.s`: `shoes` (Turnschuh / Lederschuh / Lackschuh nach `Rules.GEAR.shoes`-Stufe), `weapon` (`GangRules.WEAPONS[s.weapon]`, nur sichtbar in Posen, die eine Waffe zeigen – in Stufe 1 keine; vorbereitet für Stufe 2), Anzug statt Jacke, sobald Story 3 („stash") aktiv ist.
- Zustand aus `State.s`: `beers ≥ 1 && beerTimer > 0` → rote Wangen; `beers ≥ 3` zusätzlich leichtes Schwanken im `idle`; `story.flags.blauesAuge` → blaues Auge; `mafiaDebt > 0` → Augenringe.
- Verletzungen ohne persistentes Feld (Pflaster nach Streifschuss, Krücke nach Beinbruch) setzt die Regie per `look`-Schlüssel (Abschnitt 3) in den betreffenden Szenen (`rr.headshot`, `mafia.legbreak` und Folgeszenen).
- Ausrüstung und Zustand werden **beim Start jeder Szene** gelesen, nicht mitten in der Szene aktualisiert.

## 3. Regie

### Auto-Regie (jedes Panel ohne Zusatzangaben)

- **Plätze:** `du` immer links, Gegenüber rechts, dritte Figur mittig. Figuren schauen einander an (Spiegelung per `scaleX(-1)` am Figuren-Wrapper).
- **Auftritt:** Wer spricht und nicht auf der Bühne ist, läuft von seiner Seite herein (~0,6 s, Pose `walk`), erst danach erscheint die Blase. `du` ist standardmäßig immer auf der Bühne. Bei mehr als drei Figuren geht die am längsten nicht sprechende, nicht-`du`-Figur ab.
- **Sprechen:** Sprecher erhält Pose `talk` und einen weichen Lichtkegel am Boden; die Blase ploppt am Mund-Anker auf; Schreibmaschine läuft in der Blase mit heutiger Geschwindigkeit und heutigem Klick-zum-Beschleunigen. Andere Figuren `idle`. Nie mehr als eine Blase.
- **Stimmung → Körper:** `angry` → `point`, `happy` → Wippen, `shock` → `flinch`, `dead` → `down`.
- **Kulissenwechsel** zwischen Panels: `cs-world` blendet über (0,5 s), Figuren treten neu auf. Gleiche Kulisse: alles bleibt stehen, nur Blase und Posen wechseln.
- Bestehende `fx` (`flash, shake, blackout, hearts, coins, drain, gain, stats`) unverändert; `drain`/`gain` animieren `cs-money` im Streifen.
- **Überspringen:** springt wie heute zum letzten Panel; die Bühne wird ohne Laufwege direkt in den Endzustand gesetzt (Besetzung, Plätze, Posen des letzten Panels).

Die Auto-Regie ist eine reine Funktion `Cutscene.stagePlan(panels, ctx)` → je Panel `{ cast: [{ who, slot, facing }], enter: [...], exit: [...], speaker, pose }`, damit sie ohne DOM testbar ist.

### Regie-Schlüssel (optional pro Panel, kombinierbar)

| Schlüssel | Wirkung |
|---|---|
| `cast: ['du','vito']` | Bühne beim Panel-Start exakt so besetzen; `[]` = leere Bühne (Erzähler-Panel) |
| `enter: 'igor'` oder `{ who, from: 'left'\|'right' }` | Figur kommt herein, auch ohne zu sprechen |
| `exit: 'vito'` | Figur geht ab |
| `walk: { who, to: 'left'\|'mid'\|'right'\|'far' }` | Figur wechselt den Platz (`far` = Hintergrund, kleiner) |
| `pose: 'point'` oder `{ who, pose }` | Pose für den Sprecher bzw. eine andere Figur (überschreibt die Stimmungs-Pose) |
| `cam: 'close'\|'wide'\|'shake'` | `close` zoomt auf das Gesicht des Sprechers, `wide` zurück, `shake` Wackeln der Welt |
| `shout: 'PÄNG!'` | Comic-Ausruf, groß und kurz neben der Figur, zusätzlich zur Blase |
| `pause: 800` | Wartezeit in ms vor dem Text |
| `sfx: 'gunshot'` | Sound zu diesem Panel (SFX-ID) |
| `look: { du: { hurt: 'pflaster'\|'kruecke' } }` | Überschreibt Zustands-Teile einer Figur für dieses Panel und die folgenden der Szene |

Die Kamera wird beim nächsten Panel mit anderer Kulisse und am Szenenende auf `wide` zurückgesetzt.

### Hand-Regie in Stufe 1

Rund 25 Szenen bekommen Regie-Schlüssel: `intro`, `gameover`, `mafia.loan`, `mafia.lastcall`, `mafia.legbreak`, `mug.intro` + `mug.*`-Ausgänge, `kidney.offer`, `kidney.sold`, `rr.headshot`, `house.bought`, `tinder.match`, `divorce`, `heartbreak.collapse`, dazu je Story (Schuld, Kater, Wäsche) die Eröffnung, alle Enden und drei bis vier Wendepunkte. Die Auswahl der Wendepunkte trifft der Plan; alle übrigen Szenen laufen mit Auto-Regie.

### Validierung

`Story.validate` (bzw. die Szenen-Prüfung im Selbsttest) prüft für jedes Panel: bekannte Regie-Schlüssel, Cast-IDs in `cast/enter/exit/walk/pose/look`, bekannte Posen, `cam`-Werte, `sfx`-IDs im SFX-Register. Unbekanntes ist ein Testfehler, nicht nur eine Konsolen-Warnung.

## 4. Effekte, Performance, Tests, Abgrenzung

### Effekte

Bestehende sieben bleiben. Neu, alle transform/opacity: `rain`, `smoke`, `headlights` (Kulissen-Leben, nicht per Panel), `shout` und `cam` (Abschnitt 3). Der Mündungsblitz `muzzle` wird nicht in Stufe 1 vordefiniert, sondern kommt mit der Schießerei (Stufe 2) – kein toter Code. Kein Blut: Treffer sind Zucken + Umkippen.

### Performance

- Bewegung nur `transform`/`opacity`; Kulissen-Leben als CSS-Keyframes; JS-Ticks nur für die Schreibmaschine.
- `will-change: transform` nur auf gerade laufenden Figuren.
- `cs-world` mit `contain: paint` (Kamera-Zoom ohne Neu-Schichtung des Rands).
- Kulissen-SVGs klein: einfache Pfade, ein `drop-shadow` pro Figur, `blur` nur auf Standbildern.
- Nachweis mit `tests/perf-trace.py` (Szenario `cutscene`, `--mobile`) vorher/nachher: Raster-Zeit pro Sekunde darf gegenüber heute nicht steigen; Ziel: keine Layouts pro Frame.

### Tests

- **Node** (`tests/run-selftest.mjs`): jeder `who`-Wert aller Szenen hat einen Cast-Eintrag mit `look`; jede Kulisse hat `back/front/life` (Himmel als CSS-Klasse `.cs-sky.<id>`); `stagePlan` liefert für Beispiel-Szenen die erwartete Besetzung („Vito betritt bei Panel 2 von rechts", „vierte Figur → älteste geht", `cast: []` leert die Bühne, Skip-Endzustand); Regie-Validierung schlägt bei unbekanntem Schlüssel/Pose/Cast/SFX fehl.
- **DOM** (`tests/dom-selftest.sh`): Szene abspielen → genau eine Blase, am Sprecher verankert; mobil kein `scrollWidth > innerWidth`; alle Cutscene-Keyframes animieren nur `transform`/`opacity`; Skip landet im Endzustand; Zustands-Teile (Bier → Wangen, Story 3 → Anzug) im DOM gesetzt; Wahl-Buttons liefern weiterhin ihren `value`.
- **Playtest** (`tests/playtest-story.py`): alle 165 Checks bleiben grün – Klick-, Tasten- und Wahl-Verhalten ändern sich nicht.

### Unverändert

Alle Texte, Wahl-Buttons und Rückgabewerte, Skip-Logik, Kontostand-Animation, Sound-Sperre, `Cutscene.play/define/bind`, Story-Dateien. Außerhalb des Cutscene-Blocks werden nur die ~25 Szenen mit Regie-Schlüsseln und die Validierung angefasst.

### Nicht in Stufe 1

Schießerei (Stufe 2), Überfall/Russisch Roulette als Action (Stufe 3), Sprachausgabe, Figuren-Editor, Änderungen an Story-Texten.
