# KELLER 37 – Abnahme-Checkliste (2026-09-15)

Alle Punkte wurden über das Chrome DevTools Protocol (Python, `websockets`) gegen eine echte
Headless-Chrome-Instanz ausgeführt: State/Rules-Felder gesetzt, `Game.afterSpin()` /
`Actions.*()` / `Room.*()`-Methoden direkt aufgerufen, Cutscenes über echte Klicks auf die
gerenderten DOM-Buttons durchgeklickt (kein Bypass der Engine), Konsole/Exceptions live über
`Runtime.consoleAPICalled` / `Runtime.exceptionThrown` mitgeschnitten. Für „viele Spins beim
Null-Fall" wurde zusätzlich `Rules.rouletteRoll`/`Rules.roulettePayout` 20.000× in einer
Schleife aufgerufen (reine Logik, kein DOM nötig).

## Szenen (je einmal ausgelöst)
- [x] ✅ intro (erster Start) – echter Boot ohne `?screen`/`?scene`: `Cutscene.active=true`, Sprecher „Der Wirt", nach Durchklicken `flags.intro=true`, Screen `hub`.
- [x] ✅ house.bought – `Life.buyHouse()` bei Guthaben ≥2.500 €: 2 Panels, −2.500 €, Trophäe „Hausbesitzer" (`owner`) freigeschaltet.
- [x] ✅ tinder.match – `Life.tinder()` nach Hauskauf: 3 Panels, −50 €, `isMarried=true`.
- [x] ✅ divorce (Kontostand halbiert sich sichtbar im Panel 3) – nach 2 `marriageSpins` ausgelöst; State zeigt `balance = floor(before/2)` **bevor** die Szene rendert (Panel 3, `fx:'drain'`, `{{before}}`/`{{after}}` korrekt interpoliert: 450 € → 225 €), Trophäe „Frisch geschieden" (`divorced`).
- [x] ✅ heartbreak.collapse – läuft automatisch direkt im selben `afterSpin()`-Aufruf nach divorce (isHeartbroken && beers<2): −250 € Rechnung angewendet.
- [x] ✅ therapy.done – `Life.therapy()`: `isHeartbroken=false`, −5.000 €.
- [x] ✅ dealer.hired – `Life.dealer()`: `hasDealer=true`, −5.000 €.
- [x] ✅ kidney.offer → Nein (nichts passiert) / Ja → kidney.sold – beide Antworten geprüft: „Nein" ändert State nicht; „Ja" setzt `kidneySold=true`, +2.000 €, Trophäe „Organspender" (`donor`).
- [x] ✅ mafia.loan (nur beim ersten Kredit) – `Finance.loanMafia(300)` erstmalig: 3 Panels, `flags.mafiaLoan=true`.
- [x] ✅ mafia.lastcall (bei 1 Spin Rest) – `mafiaSpins` erreicht nach Dekrement 1: Text „Noch ein Spin, mein Freund. 300 €…" mit korrekt interpoliertem `{{debt}}`.
- [x] ✅ mafia.legbreak (Blackout, Shake, Rechnung) – `mafiaSpins` erreicht 0: 3 Panels (blackout/shake/drain-fx), Rechnung `debt×3` abgezogen (300→900 €), `mafiaDebt=0`.
- [x] ✅ bank.loan (nur beim ersten Kredit) – `Finance.loanBank(300)` erstmalig: 2 Panels, `flags.bankLoan=true`.
- [x] ✅ bank.limit (beim ersten abgelehnten Kredit) – Kreditwunsch über 3.000 €-Limit: 1 Panel, `flags.bankLimit=true`, `bankDebt` unverändert.
- [x] ✅ brownie.first – `Actions.brownie()` erstmalig: −1.000 €, `flags.brownie=true`.
- [x] ✅ igor.first – erstes `Russian.start()`: 2 Panels vor Duellbeginn, `flags.igor=true`.
- [x] ✅ rr.headshot – Spieler als Opfer (`victim==='player'`): „Streifschuss"-Panel, `Rules.rrDelta` zieht Einsatz+100 € Spital ab.
- [x] ✅ newgame.confirm (beide Antworten) – „Doch nicht": State komplett unverändert. „Ja, alles weg": Reset auf 50 €, Haus/Schulden weg, Intro-Cutscene spielt erneut, `flags.intro=true`.
- [x] ✅ gameover (Statistik + Nochmal) – `balance<0 && bankDebt≥3000 && mafiaDebt>0` am Ende von `afterSpin()`: 3-Panel-Szene mit `.cs-stats`-Tabelle, „Nochmal" setzt `balance=50`, `State.meta.gameOvers` +1, Trophäe „Auferstanden" (`phoenix`).
- [x] ✅ Überspringen in einer Szene mit drain-Effekt (divorce): Kontostand am Ende korrekt – Skip-Button im ersten Panel sichtbar, Klick springt zum letzten Panel; End-Kontostand korrekt (−10 €, aus 480 €: halbiert=240, −250 € Herzschlag-Rechnung), da die State-Änderung bereits vor dem Rendern erfolgt und vom Skip unberührt bleibt.

## Spiele (gewinnen und verlieren)
- [x] ✅ Roulette: Farbe, Gerade/Ungerade, Zahl; Null-Fall (Konsole: Glück 0, viele Spins) – alle 5 Wett-Typen einzeln mit kontrolliertem `Math.random` erzwungen und gewonnen (Rot auf 1, Schwarz auf 2, Gerade auf 4, Ungerade auf 5, Plein auf 7 → +350 €, Trophäe „Plein"). Null-Fall: Rot-Einsatz auf gewürfelte 0 verliert korrekt (−10 €); zusätzlich 20.000 reine `Rules`-Durchläufe zeigen 521/20.000 Nullen (≈1/37 erwartet: 540,5) und **nie** eine Auszahlung von Rot/Schwarz/Gerade/Ungerade bei 0.
- [x] ✅ Slots: Niete, Paar, Drilling, Jackpot (mit 60 % Glück) – alle vier Ergebnisse mit kontrollierter Zufallsfolge erzwungen: Niete (🍒🍋🍇, −10 €), Paar (🍒🍒🍋, 1,5×, +15 €), Drilling (🍒🍒🍒, 5×, +50 €). Jackpot **über den echten 60 %-Glückspfad** (3 Bier + Brownie aktiv → `Rules.luck=60`, `slotLuckOverride`-Zweig ausgelöst) auf 7-7-7, 50×, +500 €, Trophäe „Jackpot".
- [x] ✅ Pferde: Sieg und Niederlage, Kommentar läuft – 8 reale Rennen (ungesteuerter RNG), beide Ausgänge beobachtet (Sieg +30 €, mehrere Niederlagen −10 €); 23 unterschiedliche Kommentarzeilen live erfasst, inkl. „Dein Pferd liegt vorn!" bei führendem eigenem Pferd.
- [x] ✅ Russisches Roulette: Spieler trifft (Doc-Szene), Igor trifft – beide Ausgänge über 2 reale (ungesteuerte) Duelle beobachtet: Spieler-Treffer zeigt rr.headshot-Szene und zieht Einsatz+100 € ab; Igor-Treffer zahlt Einsatz aus und schaltet Trophäe „Igor besiegt" frei.
- [x] ✅ Blackjack: Win, Bust, Dealer, Push – alle vier Ausgänge über `Blackjack.finish()` mit synthetischen Händen deterministisch ausgelöst (Win 20 vs 16 → +20 €; Bust 24 → −20 €; Dealer 16 vs 19 → −20 €; Push 18 vs 18 → ±0 €), zusätzlich ein echter Durchlauf (`start()`+`stand()`) fehlerfrei komplett gespielt.
- [x] ✅ Post: Streak bis Stufe 3 (TEMPO! zweimal), falscher Kasten, zu langsam – 6 korrekte Zustellungen in Folge erreichen Stufe 3 (`{t:1.5, r:25}`) mit genau 2 `stamp()`-Aufrufen (TEMPO! bei Streak 2 und Streak 6). Falscher Kasten: −25 €, Schicht endet, Hund erscheint. Zu langsam: Timer real ablaufen lassen (kein Eingriff) → −25 €, Schicht endet nach 0 Briefen.

## Zustand
- [x] ✅ Nach jedem Spin: Bier-Timer, Brownie-Timer, Ehe-Countdown, Mafia-Frist, Anlagen-Countdown stimmen – ein `afterSpin()`-Aufruf mit allen fünf Zuständen gleichzeitig aktiv zeigt korrekte Dekremente/Auflösung: `beerTimer` 2→1, `brownieTimer` 1→0 (Toast „Brownie verdaut"), `marriageSpins` 0→1, `mafiaSpins` 3→2, Investment mit `spins:1` aufgelöst und ausgezahlt.
- [x] ✅ Zinsen + Meds werden vor dem Einsatz abgezogen (Toast „Abzüge") – `bankDebt=200`, `kidneySold=true`: Zinsen 60 €+Meds 20 € vor dem eigentlichen Slot-Spin abgezogen, Toast-Text exakt „Zinsen 60 € · Meds 20 €".
- [x] ✅ Max-Chip = Guthaben − Zinsen − Meds (mind. 1) – `Rules.maxBet` gegen Formel geprüft (920 € bei 1.000 €/200 €-Schuld/Niere verkauft) und Floor-Verhalten bei extrem negativem Rest (→1) bestätigt.
- [x] ✅ Speichern → Reload → Kontostand, Besitz, Schulden, Ehe-Status, Glück identisch – vollständiger State-Snapshot (Kontostand, Haus, Dealer, Bank-/Mafia-Schulden, Ehe-Status, Flags, Trophäen) plus `Rules.luck()` vor und nach echtem Seiten-Reload aus `localStorage` **identisch**.
- [x] ✅ Neues Spiel: Reset, Intro, Trophäen bleiben – „Ja, alles weg" setzt Kontostand/Haus/Schulden zurück, spielt Intro erneut, Trophäenliste bleibt unverändert (separater `localStorage`-Key für Meta/Achievements).
- [x] ✅ Game Over erreichbar (Konsole), danach 50 €, Trophäe „Auferstanden" – per Konsole gesetzte Werte (`balance<0`, `bankDebt=3000`, `mafiaDebt>0`) lösen Game Over aus, Neustart auf 50 €, `gameOvers`-Zähler +1, Trophäe „Auferstanden" (`phoenix`).
- [x] ✅ Mute an/aus, überlebt Reload – `SFX.setMuted(true)` bleibt nach echtem Reload erhalten (`State.meta.muted=true`, Icon 🔇).

## Technik
- [x] ✅ `tests/run-selftest.mjs` und `tests/dom-selftest.sh` grün – `57 bestanden, 0 fehlgeschlagen` bzw. `passed=57 failed=0` (57, nicht 56 – siehe Hinweis im Auftrag).
- [x] ✅ Keine Konsolenfehler während eines 10-Minuten-Spiels durch alle Räume – umfangreicher automatisierter Rundgang durch **alle** Räume (Roulette, Slots, Pferde, Russisches Roulette, Blackjack, Post, Kredite, Anlagen, Leben) plus alle 19 Szenen, alle Spielausgänge, Mobile-Emulation, Reduced-Motion und Offline-Fonts-Sessions: **null** `console.error`/`Runtime.exceptionThrown`-Events in Summe über alle Testläufe dieser Abnahme (deckt mehr Codepfade ab als ein 10-minütiges manuelles Spiel).
- [x] ✅ Postbote-Timer stoppt beim Verlassen; Herzschlag stoppt beim Verlassen; Galopp stoppt beim Verlassen – alle drei geprüft: `Postman.timeLeft` bleibt nach Verlassen mitten in einer Schicht exakt eingefroren (Intervall real via `clearInterval` gestoppt, nicht nur `active=false`); `SFX.loops.has('heartbeat')`/`('gallop')` wechseln jeweils korrekt `true→false` nach `UI.show('hub')` mitten im Duell/Rennen.
- [x] ✅ Esc und Neonschild führen zum Hub; Esc während Cutscene tut nichts – beide Navigationswege bestätigt; Esc während aktiver Cutscene lässt `Cutscene.active=true` und den Screen unverändert (kein Effekt).
- [x] ✅ Mobile 400 px: alle Screens ohne horizontales Scrollen; Tabs funktionieren *(Fehler gefunden und behoben, siehe unten)* – nach dem Fix: alle 10 Screens `scrollWidth===clientWidth===400`, Tabs öffnen/schließen/restaurieren korrekt (per CDP `Emulation.setDeviceMetricsOverride`, nicht per `--window-size`-Flag).
- [x] ✅ Reduced Motion: keine Shakes/Partikel/Flackern, Text sofort da – `matchMedia` greift, Neon-`animation-name:none`, `UI.shake()` No-Op (keine `.shake`-Klasse), Cutscene-Text erscheint sofort vollständig (kein Buchstabe-für-Buchstabe-Tippen), Slot-Walzen-`animation-name:none`.
- [x] ✅ Offline (ohne Google Fonts): Fallback-Fonts, nichts bricht – `fonts.googleapis.com`/`fonts.gstatic.com` per CDP blockiert: Seite rendert vollständig (6 Türen im Hub), Font-Stacks mit Fallbacks (`Impact`, `"Courier New"`, `sans-serif`) korrekt deklariert, Navigation/Interaktion funktioniert weiter, keine Konsolenfehler.
- [x] ✅ `grep -c "alert(\|confirm(\|prompt(\|onclick=\"" keller37.html` → `0` – beide Teil-Greps liefern `0`.

## Gefundener Fehler und Fix

**❌ → ✅ Mobile 400 px: Roulette-Screen scrollt horizontal (behoben)**

*Befund:* Bei echter 400 px-Viewport-Emulation (CDP `Emulation.setDeviceMetricsOverride`, nicht das ungenaue `--window-size`-CLI-Flag) hatte der Roulette-Screen `document.documentElement.scrollWidth = 442` gegen `clientWidth = 400` – 42 px horizontaler Überstand. Ursache: Die mobile Regel `.table-box { transform: scale(.78); … }` verkleinert den 13-spaltigen Zahlentisch nur optisch – `transform` beeinflusst laut CSS-Spezifikation nicht die Layout-Breite, mit der der Flex-Elternteil `.roulette-top` seine eigene (auto-)Breite berechnet. Der Elternteil blieb bei seiner ungeskalierten Breite von 484 px, wurde zentriert und hing dadurch 42 px rechts (und 42 px links, `left:-42`) über den 400 px-Viewport hinaus.

*Fix:* In `keller37.html`, mobiler Media-Query-Block – statt den fertigen Tisch nachträglich zu skalieren, wird die Grid-Zellengröße von `.rtable` direkt für Mobile reduziert (23 px statt 34 px, Gap 1 px, Padding 5 px) plus passende kleinere Schriftgrößen für `.rcell`/`.rcell.out`. Das verkleinert die tatsächliche Layout-Breite (13×23+12×1+2×5+2 border ≈ 323 px, passt in die 334 px Panel-Innenbreite bei 400 px Viewport), kein Scale-Hack mehr nötig.

*Verifikation nach Fix:* Alle 10 Screens `scrollWidth===clientWidth===400` (siehe oben), Tab-Interaktion weiterhin korrekt, `node tests/run-selftest.mjs` → `57 bestanden, 0 fehlgeschlagen`, `tests/dom-selftest.sh` → `passed=57 failed=0`, beide Grep-Kontrollen weiterhin `0`. Screenshot des reparierten Screens visuell geprüft (Tisch lesbar, alle Buttons sichtbar, keine abgeschnittenen Elemente).

*Commit:* `d39da73` — „fix: Roulette-Tisch verursacht horizontalen Scroll bei 400px"

## Schritt 3: Grep-Kontrollen

```
$ grep -c 'alert(\|confirm(\|prompt(' keller37.html
0
$ grep -c 'onclick="' keller37.html
0
$ node tests/run-selftest.mjs
57 bestanden, 0 fehlgeschlagen
$ tests/dom-selftest.sh
data-selftest="passed=57 failed=0"
```

(57 statt der im Auftrag an einigen Stellen genannten 56 – wie im Task-Kontext erwartet.)
