# Schießerei in Ego-Sicht – Design (Stufe 2 von 3)

Datum: 2026-09-21 · Status: entworfen, vom Auftraggeber abgenommen (Abschnitte 1–5)

## Ziel

Die Schießerei (Story 3: Tutorial, Hinterhalte, Finale; Dev-Aufruf) sieht heute aus wie ein Kästchen mit zwei Emojis und einer Statuszeile. Sie wird eine Action-Sequenz in **Ego-Sicht** auf einer Canvas-Bühne: der Gegner kommt aus dem Dunkel, zieht, man schießt auf ihn – mit Mündungsfeuer, Zeitlupe, Blut und Staub. Die Mechanik wird um **Zielen** erweitert (Fehlschüsse kosten Zeit, der Gegner schießt von sich aus), die Balance der Reaktionszeiten bleibt.

Stufe 1 (Cutscene-Bühne, `2026-09-20-cutscene-buehne-design.md`) liefert Figuren-Rig, Looks und Posen; Stufe 3 (Überfall, Russisch Roulette) folgt später.

## Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|---|---|
| Mechanik | Reaktionsduell **plus Zielen**: nach dem Signal muss der Tipp den Gegner treffen |
| Fehlschuss | **verlorene Zeit** – der erste treffende Tipp entscheidet; der Gegner feuert von sich aus zu seiner Zeit |
| Signal | **beides**: der Gegner reißt den Arm hoch **und** ein kurzer Blitz mit „ZIEH!" |
| Technik | **Canvas** für Welt und Effekte, in **Ego-Sicht**; die Gegnerfigur kommt aus dem Cutscene-Rig (kein zweites Figurensystem) |
| Blut | ja, im Comic-Stil (Spritzer, Tropfen, Bodenfleck, Kamera-Tropfen) |

## Rahmenbedingungen

- Eine Datei `keller37.html`, keine Bilddateien, keine externen Abhängigkeiten.
- `Shootout.start(cfg)`, `Shootout.pending`, `Shootout.forced`, `Shootout.leave()`, Events `fight:done { kind, won, rounds[, aborted] }` und `fight:leave { kind, won[, aborted] }` bleiben; `Story.forceFight` und die Story-Auswertung (Flags `fightWon/fightLost`, Hinterhalt-Raub, Finale) werden nicht angefasst.
- Balance-Zahlen unverändert: `GangRules.FOES` (base/spread), `GangRules.WEAPONS` (bonus), `GangRules.DRAW_WAIT`, `duelRound`.
- Deutsche Spieltexte. Kein Push/Merge ohne Freigabe.

## 1. Bild und Ablauf

**Perspektive.** Ego-Sicht: unten rechts die eigene Hand mit Waffe (Makarov / Glock / „Die Goldene" in Gold; ohne eigene Waffe die geliehene Pistole – im Tutorial Anabis), in der Bildmitte der Gegner frontal, dahinter die Kulisse mit Fluchtpunkt. Gegner sind die Comic-Figuren aus den Cutscenes (gleiche Farben, gleiches Rig); jeder hält eine Pistole in der rechten Hand.

**Kulisse nach `fight.kind`:** `tutorial` → Bahnhof (Unterführung, Gleise, Neonröhre), `hinterhalt` → Gasse (Mauern, Tonnen, Laterne, Regen/Nebel), `finale` → Keller (Tisch, Lampe am Kabel), Dev → Gasse.

**Ablauf einer Runde:**
1. **Auftakt (~1 s):** Kulisse, treibender Staub/Nebel, Lampe flackert. Der Gegner kommt aus dem Dunkel auf den Spieler zu (Skalierung 0,4 → 1), Namensschild „Bahnhof-Junge · 1 / 3". Die eigene Waffe hebt sich von unten ins Bild. Hinweis: „Warte, bis er zieht."
2. **Anspannung (zufällig `DRAW_WAIT`, wie heute):** Gegner atmet, Hand zuckt zur Waffe, Herzschlag-Schleife wird schneller, Rand dunkelt leicht ab.
3. **Signal:** Pose `draw` (Arm schnellt hoch, Mündung zeigt auf den Spieler) + weißer Blitz + kurz „ZIEH!". Ab hier läuft die Uhr.
4. **Schusswechsel:**
   - Tipp auf den Gegner → eigene Waffe ruckt, Mündungsfeuer, Hülse, Schussspur; Gegner Pose `hit` (Zucken), Blutspritzer am Einschlag mit fliegenden Tropfen, **Zeitlupe** (Zeitfaktor 0,3 für 500 ms) während er fällt (Pose `down`), Staubwolke, dunkler Fleck am Boden.
   - Daneben getippt → Schuss ins Leere: Mündungsfeuer, Funken an der Wand am Tippunkt, `ricochet`-Sound, die Uhr läuft weiter.
   - Zu früh (vor dem Signal) → Schuss in den Boden, „Zu früh!", Runde verloren (wie heute).
   - Kein Treffer bis zur Gegnerzeit → **der Gegner schießt**: sein Mündungsfeuer auf die Kamera, Bild ruckt, roter Rand, ein paar Bluttropfen laufen über die „Kamera", „Du liegst."
5. **Nächster Gegner:** nach ~1 s aus dem Dunkel, Zähler zählt hoch. Am Ende „Alle liegen. Du gehst." bzw. „Du liegst. Sie gehen." und der Weiter-Knopf wie heute.

**Reduced motion:** keine Zeitlupe, kein Ruck, kein Blitz (nur „ZIEH!"), keine treibenden Partikel; Mündungsfeuer und Blutspritzer als Standbild für 150 ms; Wartezeit bleibt zufällig.

## 2. Regeln (`GangRules`, DOM-frei)

Bestehend und unverändert: `duelRound({ reaction, bonus, foe, rng })`, `drawWait(rng)`, `FOES`, `WEAPONS`, `weapon(s)`.

Neu, alles reine Funktionen:

- `hitTest(tap, box, margin)` → `boolean`: `tap = { x, y }`, `box = { left, top, width, height }` (Figuren-Kasten in Bühnenkoordinaten), Treffer wenn innerhalb der um `margin` vergrößerten Box. Rand 24 px, bei Touch 32 px.
- `resolveRound({ taps, foeTime, bonus })` → `{ won, misfire, you, foeTime, misses }`: `taps = [{ t, hit }]` mit `t` in ms relativ zum Signal (negativ = vor dem Signal). Erster Tipp mit `t < 0` → `misfire: true, won: false, you: null`. Sonst zählt der erste Tipp mit `hit: true`: `you = max(0, t − bonus)`, `won = you < foeTime`; `misses` = Zahl der nicht treffenden Tipps vor diesem (bzw. aller, wenn keiner trifft). Ohne treffenden Tipp: `won: false, you: null`.
- `foeFiresAt(foeTime, bonus)` → `foeTime + bonus` (ms nach dem Signal): Zeitpunkt, zu dem der Gegner schießt, wenn bis dahin kein Treffer kam. Das ist genau der Punkt, ab dem `duelRound` heute verlieren würde – die Balance ändert sich nicht.

Invariante (Test): für eine Tipp-Liste mit genau einem treffenden Tipp liefert `resolveRound` dasselbe `won/you/foeTime` wie `duelRound({ reaction: t, bonus, foe })` bei gleicher Gegnerzeit.

`fight:done` bleibt `{ kind, won, rounds }`; jede Runde `{ won, misfire, foeTime, you, misses }`.

Tastatur: Leertaste/Enter = „Bereit" bzw. Schuss mit automatischem Treffer. Dev-Aufruf `?screen=shootout&foe=<id>&weapon=<0–3>` bleibt.

## 3. Aufbau

**Schichten des Duell-Screens** (Template `tpl-shootout` wird eine Bühne, die den Bildschirmbereich füllt; Handy: volle Breite):

| Schicht | Technik | Inhalt |
|---|---|---|
| Welt-Canvas (hinten) | `<canvas>` | Himmel/Kulissenfarbe, Boden mit Fluchtpunkt, Kulissen-Silhouetten (vorgerendert auf Offscreen-Canvas), Nebelbänder, treibender Staub, Lampenflackern |
| Gegner | DOM-Figur `CsCast.figureHtml(foe, { gun: true })` in einem `.cs-fig`-Kasten (Posen-CSS der Cutscenes) | Annäherung per `transform: scale()`, Posen `idle → draw → hit → down` |
| Effekt-Canvas (vorn) | `<canvas>` | Mündungsfeuer beider Seiten, Schussspur, Funken, Hülsen, Blutspritzer/Tropfen, Bodenfleck, Blitz, roter Rand, Kamera-Tropfen, Zeitlupen-Vignette |
| Eigene Waffe | Inline-SVG unten rechts | Hand + Waffe nach Stufe, Rückstoß per `transform`; Mündungsfeuer aus dem Effekt-Canvas an der Laufspitze |
| Anzeige | DOM | Namensschild + Zähler oben links, Hinweiszeile, Knöpfe „Bereit" / „Nächster" / „Weiter" wie heute |

**Module:**
- `GangRules`: bestehende Regeln + `hitTest`, `resolveRound`, `foeFiresAt`.
- `DuelStage` (neu, Block `game-shootout`, rein darstellend): `mount(root, { set, weapon })`, `enter(foeId, idx, n)`, `signal()`, `shot({ x, y, hit })`, `foeShoots()`, `foeDown()`, `flash(text)`, `setTimeScale(k)`, `unmount()`. Trifft keine Spielentscheidung.
- `Shootout` (bestehend): behält `start/ready/tap/resolve/finish/leave/onKey/pending/forced` und die Story-Anbindung; neu: Tipp-Koordinaten aus `pointerdown`, `hitTest`, Gegner-Timer (`foeFiresAt`), Tipp-Liste je Runde, `resolveRound`; ruft `DuelStage` für alles Sichtbare.
- `CsCast`: Looks für `laeufer` (Trainingsjacke, Kapuze) und `junge` (Kappe, Hoodie); Option `gun: true` zeichnet eine Pistole (Griff + Lauf) in die rechte Hand.
- `CsDirector.POSES` erhält `draw` und `hit`; CSS-Posen in Abschnitt 5 des Stylesheets: `draw` (rechter Arm 100° hoch), `hit` (Zucken nach hinten, transform-only).

**Canvas-Loop:** `requestAnimationFrame` nur, solange der Screen gemountet ist; DPR-Skalierung bis 2; Partikel in Pools (max. ~150); Zeitlupe über einen Zeitfaktor im Loop; Kulissen-Silhouetten einmal auf ein Offscreen-Canvas gezeichnet und pro Frame kopiert. `ResizeObserver` skaliert Canvas und Figur bei Rotation nach.

## 4. Steuerung, Handy, Barrierefreiheit

- Schuss = `pointerdown` (nicht `click`); `touch-action: none` auf der Bühne. Koordinate → `hitTest` mit dem im Moment des Tipps gemessenen Figuren-Kasten.
- Vor „Bereit" und nach dem Ergebnis löst kein Tipp einen Schuss aus.
- Tastatur: Leertaste/Enter = „Bereit" bzw. Schuss mit automatischem Treffer.
- Haptik: `navigator.vibrate(30)` beim eigenen Schuss, `vibrate([40, 40, 80])` beim Getroffenwerden – nur wo verfügbar.
- Größen: Gegner ≈ 45 % der Bühnenhöhe (hochkant) bzw. 55 % (quer); eigene Waffe ≈ 35 % der Breite unten rechts; Namensschild/Hinweis oben; nichts überlappt die Treffer-Box.
- Verlassen des Screens mitten im Kampf: `fight:done` mit `aborted` wie heute; `unmount` stoppt Loop und Timer.
- Reduced motion wie in Abschnitt 1.
- Sound: bestehende `gunshot`, `dryfire`, `heartbeat`-Schleife (schneller beim Anspannen), `reelStop` fürs Signal; neu `ricochet` (kurzer Zisch-Klick) im SFX-Synth.

## 5. Tests, Performance, Abgrenzung

**Node:** `hitTest` (innen/Rand/außen/Touch-Rand); `resolveRound` (Fehlschuss vor dem Signal; erster Treffer zählt; `misses`; Bonus; Tipps nach der Gegnerzeit ohne Wirkung); `foeFiresAt`; Invariante `resolveRound` ≡ `duelRound` bei genau einem Treffer; `CsCast`-Looks `laeufer`/`junge`, `gun: true`; `CsDirector.POSES` enthält `draw`/`hit`; Regie-Validierung aller Szenen bleibt grün.

**DOM (headless):** Screen mounten (`?screen=shootout&foe=junge`): beide Canvas, Gegner als `.cs-fig` mit Rig-Teilen, Waffe, Zähler „1 / 1". Ablauf mit gestubbtem `drawWait`: Bereit → Signal (`draw`, Blitztext) → `pointerdown` auf die Figur → `fight:done` `won: true`, `misses 0`; erst daneben, dann Treffer → `misses 1`; kein Tipp → Gegner-Timer → `won: false`; Tipp vor dem Signal → `misfire`. Reduced motion: Zeitfaktor bleibt 1, kein Blitz-Element. Duell-Keyframes nur transform/opacity. `unmount` stoppt `requestAnimationFrame` und Timer; Abbruch liefert `aborted`.

**Playtest:** Story-3-Checks (Tutorial, Hinterhalt, Finale) bleiben grün; Helfer `__pt.duelShoot()` tippt auf die Figur.

**Performance:** Trace-Szenario „Duell" in `tests/perf-trace.py`; Canvas-Frames sind erwartet, Ziel < 2 ms Zeichenzeit pro Frame (Mac, Software-Raster), keine Repaints der DOM-Figur, keine Layouts pro Frame. Handy-Check durch den Auftraggeber.

**Unverändert:** Story-Definitionen und -Texte, `forceFight`/`fight:done`/`fight:leave`, Waffenkauf, Balance-Zahlen.

**Nicht in Stufe 2:** Überfall und Russisch Roulette (Stufe 3), neue Gegner oder Waffen, Trefferzonen (Kopf/Körper), Munition.

## Umsetzungsnotiz

Die Pistole des Gegners ist ein Extra im rechten Arm-Teil (`class="pistole"`), die Pose `draw` dreht den Arm um 100° nach oben – in der Frontansicht zeigt der Lauf zur Seite, das Mündungsfeuer kommt aus dem Effekt-Canvas an der Hand. Die Zeitlupe verlangsamt die Partikel (Zeitfaktor 0,3) und verlängert den Fall (`--fall: 1.2s`); der nächste Gegner kommt nach `Shootout.NEXT_MS = 1400` ms statt 900. Anspannung: `DuelStage.tension(true)` dunkelt den Rand über ~4 s ab, der Herzschlag wechselt nach 1,2 s auf 550 ms Takt, die Hand des Gegners zuckt im `idle` alle 2,6 s zur Waffe (`duelTwitch`). `Shootout.tap()` ohne Argument bleibt „Schuss mit Treffer" (Tastatur, Playtest, alte Tests); `Shootout.shoot(ev)` ist der Zeigerpfad mit Trefferprüfung. `DuelStage.toStage(clientX, clientY)` rechnet Viewport- in Bühnenkoordinaten um, weil `.body` auf großen Bildschirmen mit `zoom: 1.15–1.65` skaliert wird – ohne die Umrechnung träfe ein Tipp am Bildschirmrand daneben. Die Bühne ist auf dem Handy `calc(100vh - 410px)` hoch (mindestens 300 px), damit „Bereit" oberhalb der Tab-Leiste stehen bleibt.
