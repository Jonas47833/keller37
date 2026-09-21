# Überfall und Russisch Roulette auf der Ego-Bühne – Design (Stufe 3 von 3)

Datum: 2026-09-21 · Status: entworfen, vom Auftraggeber abgenommen (Abschnitte 1–5)

## Ziel

Die beiden verbliebenen Sonderszenen werden Action-Sequenzen auf der Ego-Bühne aus Stufe 2: Beim **Überfall** sieht man Kampf und Flucht statt nur Text und kann mit einem Tipp im richtigen Moment einen kleinen Bonus holen; **Russisch Roulette** spielt in Ego-Sicht mit der Mündung auf der Kamera und Igor gegenüber am Tisch. Zufalls- und Geldregeln bleiben bis auf einen additiven Timing-Bonus unverändert.

Voraussetzungen: Cutscene-Bühne (`2026-09-20-cutscene-buehne-design.md`), Schießerei in Ego-Sicht (`2026-09-21-schiesserei-ego-design.md`).

## Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|---|---|
| Überfall | **c – Mischung:** Ausgang bleibt gewürfelt, ein Tipp im richtigen Moment gibt +10 Prozentpunkte |
| Russisch Roulette | **b – Ego-Sicht** wie das Duell: Mündung dreht sich auf die Kamera, Igor gegenüber |
| Architektur | **eine gemeinsame Ego-Bühne** (`DuelStage` → `EgoStage`), drei Nutzer: Duell, Überfall, Roulette |

## Rahmenbedingungen

- Eine Datei `keller37.html`, keine Bilddateien, keine externen Abhängigkeiten.
- Unverändert: `Rules.mugChance`, `Rules.fightChance`, `Rules.fleeChance` (der Bonus wird außerhalb addiert), `Rules.mugLoot`, `mugWallet`, `fleeFailExtra`, Cooldown, Stärke-Regeln; `Rules.rrCylinder`, `rrDelta`, Einsatzabzug, `rr:result`/`rr:forced`, `Game.settle`, Vitos erzwungene Prüfung (`Russian.start({ forced: true })`), `rr.headshot`-Szene; `Shootout` und seine Tests.
- Öffentliche Schnittstellen bleiben: `Mugging.maybe/run/force/running/TYPES`, `mug:done`-Event (bekommt zusätzlich `bonus`), `Russian.start/pull/end/drop/inDuel/duel/busy`, Template-IDs `#rrStatus`, `#rrBetControls`, `#rrActionControls`, `#btnTrigger`, `#btnDuel`, `#rrBet`, `#chambersLeft`.
- Bewegung nur `transform`/`opacity`; Canvas zeichnet pro Frame nur Bewegtes. `prefers-reduced-motion` wie in Stufe 2 plus die hier genannten Sonderfälle.
- Deutsche Spieltexte. Kein Push/Merge ohne Freigabe.

## 1. Überfall: Ablauf und Regeln

Das Wahl-Panel (`mug.intro`, drei Buttons) bleibt. Danach je nach Wahl:

**Kämpfen** – Vollbild-Ego-Bühne (Overlay `#ego`, Kulisse Gasse), der Räuber (`raeuber`) steht vor dir, deine Faust hebt sich unten rechts.
1. Anlauf ~0,8 s (Tipps werden ignoriert).
2. Räuber holt aus (Pose `windup`), um ihn zieht sich ein **Timing-Ring** über 900 ms zusammen, die letzten 250 ms sind gold.
3. Erster Tipp zählt: im goldenen Fenster → Bonus +0,10, Ausruf „TREFFER!", Haptik 20 ms; sonst kein Bonus, kein Malus; ohne Tipp Bonus 0.
4. Würfeln: `p = min(0.95, Rules.fightChance(strength, mods) + bonus)`.
5. Ausgang auf der Bühne: **gewonnen** – Faust ruckt, Einschlag, Blutspritzer, Räuber `hit` → `down`, Zeitlupe, Staub; **verloren** – seine Faust auf die Kamera (`punch(false)`), Ruck, roter Rand, Tropfen, „Du liegst".
6. Overlay schließt; Text-Panel `mug.fightWon`/`mug.fightLost` mit Beute/Stärke wie heute.

**Wegrennen** – Ego-Bühne mit **laufender Kulisse** (`motion(true)`: Bodenlinien und Wandkanten ziehen zum Betrachter, leichtes Laufwackeln), der Räuber in der Bildmitte wächst (holt auf).
1. Anlauf ~0,8 s.
2. Nach ~1,2 s Lauf taucht die Abzweigung auf (Mülltonne rechts im Effekt-Canvas), der Ring zieht sich zu (900/250 ms).
3. Tipp im goldenen Fenster → Bonus +0,10, „HAKEN!".
4. Würfeln: `p = min(0.95, Rules.fleeChance(gear) + bonus)`.
5. Ausgang: **entkommen** – Räuber schrumpft ins Dunkel (`foeScale(0.3, 900)`), Kulisse kommt zur Ruhe; **erwischt** – Räuber wächst bis ins Bild, `grab()` (Bild reißt nach hinten, roter Rand), „Erwischt".
6. Overlay schließt; `mug.fled`/`mug.caught` wie heute.

**Zahlen** – wie heute, nur Text.

**Regeln (rein, `GangRules`):** `timingBonus(t, { window = 900, gold = 250, bonus = 0.10 })` → `bonus` wenn `t != null && window − gold ≤ t ≤ window`, sonst 0. `Mugging` addiert ihn und deckelt bei 0,95; `mug:done` trägt `{ outcome, loot, strength, bonus }`.

**Reduced Motion:** Ring als statische Leiste mit Marker ohne Easing (Fenster gleich), Kulisse steht, Räuber wechselt Größe in Stufen, Effekte als Standbild.

## 2. Russisch Roulette: Ablauf

Screen `russian` bleibt (Einsatz-Leiste, „Duell starten", `forced`); das Panel wird zur Ego-Bühne mit Kulisse **Hinterzimmer**: Tisch quer im Vordergrund (Ebene im Effekt-Canvas, vor der Figur), Kerze, Aschenbecher, Igor (`igor`) dahinter.

- **Start:** Igor tritt an den Tisch (Annäherung), `igor.first` beim ersten Mal wie heute. Trommel-Nahaufnahme unten links (`cylinder({ idx: 0, spent: [] })`, 6 Kammern, Kugel unsichtbar), `#chambersLeft` „6 Kammern".
- **Dein Zug:** Hand `revolver` hebt sich, dreht in ~0,6 s zur Mündungssicht (`revolverMuzzle`: großer dunkler Lauf-Kreis, Hahn gespannt); Trommel dreht 60° auf die nächste Kammer; Herzschlag wie heute (900 → schneller pro Kammer); Rand dunkelt. **Abzug** = `#btnTrigger`, Tipp auf die Bühne, Leertaste/Enter. **Klick** → `dryfire`, Kammer markiert, Hand senkt sich, Status „*Klick*… Leer. Igor ist dran…"; **Knall** → Blitz, Ruck, roter Rand, Tropfen, „PÄNG · Streifschuss …", danach `end('player')` → `rr.headshot` wie heute.
- **Igors Zug:** Revolver gleitet als Requisite über den Tisch, Igor Pose `temple` (Revolver an der Schläfe), 1,1 s, Trommel dreht. **Klick** → Igor Pose `relief` (Ausatmen, Nicken) → `idle`, „*Klick*… Igor lebt. Du bist dran."; **Knall** → Mündungsblitz am Kopf, Blutspritzer, Igor `down` mit Zeitlupe, Fleck, „PÄNG · Igor liegt …", `end('igor')`.
- **Abbruch:** Screen verlassen mitten im Zug → `drop` wie heute; `EgoStage.unmount` im `unmount` des Screens.
- **Reduced Motion:** Revolver ohne Drehung (direkt Mündungssicht), Trommel springt, kein Blitz/Ruck, Blut als Standbild.

## 3. Aufbau und Module

**`EgoStage`** (Umbenennung von `DuelStage`; `const DuelStage = EgoStage` bleibt als Alias, damit Duell, Tests und Playtest unverändert laufen). Bestehend: Welt-Canvas mit vorgerenderter Kulisse, DOM-Figur aus dem Rig, Effekt-Canvas, Partikel-Pool, `toStage`, Zeitlupe auf der Bühnen-Uhr, `flash`, `tension`, Reduced Motion. Neu:

| Erweiterung | Schnittstelle |
|---|---|
| Kulisse `hinterzimmer` | `SETS.hinterzimmer` (Wände, Kerze, Aschenbecher hinten) + Vordergrund-Tisch, gezeichnet im Effekt-Canvas unterhalb der Partikel |
| Hand-Varianten | `hand(kind)` mit `gun`, `fist`, `revolver`, `revolverMuzzle`, `none`; `handRise()` / `handDrop()` per Transform |
| Timing-Ring | `ring(ms, goldMs)` startet den Ring um die Figur (Canvas: schrumpfender Kreis, letzte `goldMs` gold), `ringTime()` (ms seit Start, Bühnen-Uhr) , `ringStop()` |
| Laufende Kulisse | `motion(on)` – Bodenlinien/Wandkanten scrollen, Laufwackeln; `foeScale(s, ms)` setzt die Figurengröße per Transition |
| Trommel | `cylinder({ idx, spent })` zeichnet die Nahaufnahme unten links; Drehung um 60° je `idx` über den Zeitfaktor |
| Posen | `windup`, `temple`, `relief` in `CsDirector.POSES` + CSS (transform-only) |
| Effekte | `punch(hit)` (Einschlag beim Gegner bzw. Faust auf die Kamera + Ruck + roter Rand), `grab()` (Kragengriff: Bild reißt zurück, roter Rand), `muzzleAt(x, y)` |

**`GangRules.timingBonus`** (Abschnitt 1).

**`Mugging.run`:** nach der Wahl `fight` → `await MugAction.brawl(type)`, `flee` → `await MugAction.chase(type)` (neues Objekt `MugAction` im Block `mugging`): öffnet das Vollbild-Overlay `#ego` (fixed, `z-index` wie `#cutscene`, `body.ego-open`), mountet `EgoStage` (Gasse), spielt Anlauf → Ring → Tipp → Würfeln → Ausgang, schließt das Overlay, gibt `{ won, bonus }` zurück. `Mugging` schreibt Stärke/Beute/Statistik wie heute und spielt das Text-Panel. `pay` ohne Overlay.

**`Russian`:** behält `start/pull/end/drop/inDuel/duel/busy` und die Events; `drawCylinder/rotateTo/markSpent/setTurn/bang` werden durch `EgoStage`-Aufrufe ersetzt. Template `tpl-russian`: Bühne `#rrStage` (Klasse `duel-stage`) statt `.duel`/`.fighter`/`#cylinder`, Status, Einsatz-Leiste, `#btnTrigger`, `#chambersLeft` bleiben.

**`Shootout`:** unverändert (Alias).

## 4. Steuerung, Handy, Barrierefreiheit

- Überfall-Einschub: Tipp irgendwo auf die Bühne (`pointerdown`, nur der erste zählt) oder Leertaste/Enter = Timing-Tipp; kein „Bereit", kein Überspringen (~4 s); Tipps vor Ringstart werden ignoriert; schließt sich von selbst.
- Russisch Roulette: Abzug per Knopf, Tipp auf die Bühne, Leertaste/Enter; während Igors Zug und der Auflösung gesperrt (`busy`).
- Haptik: `vibrate(20)` Timing-Treffer, `vibrate([40, 40, 80])` Faust/Kragen/Streifschuss, `vibrate(15)` Klick des Hahns – nur wo verfügbar.
- Größen: Bühne wie Duell (`min(72vh, 720px)`, Handy `calc(100vh − 410px)`, min. 300 px); Ring-Radius ≈ Figurenbreite; Trommel ≈ 22 % der Bühnenbreite (Handy 30 %).
- Verlassen: RR → `drop` wie heute; Überfall-Overlay nicht verlassbar; Rotation per `ResizeObserver`.
- Reduced Motion: Abschnitte 1 und 2.
- Sound: vorhanden `gunshot`, `dryfire`, `heartbeat`, `ricochet`, `click`; neu `punch` (dumpfer Schlag) und `whoosh` (Ausholen/Laufen).

## 5. Tests, Performance, Abgrenzung

**Node:** `timingBonus` (vor/im/nach dem Fenster, ohne Tipp; Deckel 0,95 in `Mugging`-Helfer `chanceWithBonus(p, bonus)`); `CsDirector.POSES` enthält `windup`, `temple`, `relief`; Regie-Validierung grün.

**DOM:** `EgoStage`-Erweiterungen (Hand-Varianten, `ring`/`ringTime`, `motion`, `cylinder`, `punch`/`grab`, Kulisse `hinterzimmer`, Alias); Überfall-Flow mit gestubbtem `Cutscene.play` und `Math.random` (fight mit Treffer → Bonus 0,10 in `mug:done`, Stärke +1, Overlay geschlossen; flee mit Tipp daneben → Bonus 0; pay → kein Overlay; beide Ausgänge); RR-Flow mit gestubbter Trommel (Klick/Klick/Kugel beim Spieler bzw. bei Igor, `forced`, `drop` beim Verlassen); Keyframes `duel*`/`cs*`/`ego*` nur transform/opacity. Bestehende RR-, Überfall- und Shootout-Tests bleiben grün.

**Playtest:** Story-1-Checks (erzwungenes Duell, `Russian.inDuel`, `duelWon/duelLost`) und Überfall-Checks bleiben grün; neuer Helfer `__pt.egoTap()` tippt in den Ring.

**Performance:** Trace-Szenarien „Überfall Kampf" und „Russisch Roulette"; Ziel < 2 ms Zeichenzeit pro Frame, keine DOM-Repaints der Figur, Layouts ≤ 2/s.

**Unverändert:** siehe Rahmenbedingungen.

**Nicht in Stufe 3:** neue Überfalltypen, Trefferzonen, Mehrfach-Tipps, Inszenierung von Blackjack/Poker/anderen Spielen.

## Umsetzungsnotiz

`chanceWithBonus` liegt neben `timingBonus` in `GangRules` (nicht in `Mugging`), damit der Node-Selbsttest es ohne DOM prüfen kann; `MugAction.brawl/chase` bekommen die Grundchance als zweites Argument, `Mugging.run` rechnet sie wie bisher aus. Die Trommel dreht wie vorher am Anfang jedes Abzugs auf die aktuelle Kammer. Igor trägt die Pistole des Rigs nur in seinem Zug (`EgoStage.foeGun`, Klasse `unarmed`), der Räuber nie; der Zähler `#duelCount` bleibt bei einem einzelnen Gegner leer. Am Ende eines Duells setzt `setTurn(null)` keine Pose mehr – sonst stünde ein gefallener Igor wieder auf. Headless-Tests takten die Bühnen-Uhr per `EgoStage.loop(last + 50)`, weil `virtual-time-budget` kaum rAF-Frames liefert. Der DOM-Test deckt bei der Flucht den Fall „ohne Tipp“ ab (Bonus 0); das „daneben“-Fenster selbst prüft der Node-Selbsttest von `GangRules.timingBonus`.
