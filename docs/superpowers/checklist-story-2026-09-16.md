# KELLER 37 – Story-Modus – Abnahme-Checkliste (2026-09-16)

Verifikation nach zwei Methoden, wie in Spec §13 vorgeschrieben:

1. **Selbsttest** (`tests/run-selftest.mjs` unter Node + `tests/dom-selftest.sh` headless in Chrome) –
   reine Logik: Bedingungsauswertung, Story-Auswahl, `Story.night()`-Fixture, Lohnformeln,
   Effekt-Anwendung, Datenvalidierung.
2. **CDP-Playtest** (`tests/playtest-story.py`, Chrome `--headless=new --remote-debugging-port=9335`,
   python3 `websockets`) – ein echter Browser, echte Klicks auf die gerenderten DOM-Buttons für
   Cutscenes, `State`-Felder werden dort gesetzt, wo die Spec „mit gesetzten Variablen" vorschreibt
   (Enden, Kontrolle), Engine-Methoden (`Story.night()`, `Jobs.runShift()`, `Story.playScene()`, …)
   direkt aufgerufen, um das Ablaufen von bis zu 30 Spieltagen nicht bei jedem Lauf neu vorzuspielen –
   kein Bypass der Engine, nur ein Abkürzen des Weges dorthin (Muster aus
   `docs/superpowers/checklist-2026-09-15.md`). Alle Konsolenfehler/Exceptions wurden über
   `Runtime.consoleAPICalled` / `Runtime.exceptionThrown` mitgeschnitten.

Letzter vollständiger Lauf: `python3 tests/playtest-story.py` → **51 Checks, 0 fehlgeschlagen,
ERRORS 0** (vollständiges Protokoll unten bei den einzelnen Punkten zitiert). Screenshots liegen unter
`/tmp/k37story/*.png`; die acht in Task 9 Schritt 3 geforderten liegen zusätzlich unter
`docs/superpowers/screenshots/story-*.png` und wurden vor dem Einchecken visuell angesehen (siehe
Belege je Punkt).

---

## Spec §13, Punkt für Punkt

### 1. Selbsttest (Node + Browser)

- [x] ✅ **Bedingungs-Auswertung (alle Operatoren, `all/any/not`, ungültig wirft)** –
  `StoryRules.cmp` (eq/ne/gte/lte/gt/lt einzeln), `StoryRules.check: day/balance/var`,
  `StoryRules.check: flag/jobDone/unlocked/all/any/not`, `StoryRules.check: ungültig wirft`
  (wirft bei unbekanntem Schlüssel). Beleg: `node tests/run-selftest.mjs` → alle vier Tests grün.
- [x] ✅ **Story-Auswahl** – `StoryRules.pickStory: am längsten nicht gespielt, dev nie` (wählt
  `lastPlayed`-Minimum, `dev:true`-Storys wie `STORY_PROBE` werden nie zufällig gezogen).
- [x] ✅ **`Story.night()` auf Fixture-State** (Tag +1, Phase, Kapitel-Trigger, Freischaltung,
  Enden-Priorität, Fallback nach Tag 30) – `StoryRules.advanceDay` (Tag+1, Phase→morning,
  jobToday→null), `StoryRules.chapterFor: höchstes passendes Kapitel`, `StoryRules.dueEvents: at,
  when, once/seen`, `StoryRules.ending: Priorität, Fallback nur nach Ablauf`,
  `STORY_SCHULD: Kontrolle Tag 10 und Enden`, `STORY_SCHULD: vier Enden, Prioritäten,
  Sturz-Bedingung` (prüft explizit, dass der Fallback `doc` erst nach Tag 30 greift und alle
  anderen drei Enden Vorrang haben). Zusätzlich per CDP real durchlaufen (siehe Abschnitt 2).
- [x] ✅ **Lohnberechnung Spüler/Taxi** – `StoryRules Lohn`: `spuelerPay(hits,breaks) =
  hits*5-breaks*10`, `taxiPay(passengers,tickets) = passengers*15-tickets*50`, inkl. negativer
  Werte. Zusätzlich real im CDP-Lauf bestätigt: Spüler-Verlust `hits:0,breaks:10` → Konto 50→0 €
  (=-100, aber per `Math.max(pay, -balance)` auf den vorhandenen Betrag gekappt); Taxi-Verlust
  `passengers:19,tickets:18` → 500→0 € (ebenfalls gekappt).
- [x] ✅ **Effekt-Anwendung (`add/set/flag/unlock/balance`)** –
  `StoryRules.applyEffect: var add/set mit Clamp, flag, balance, unlock`,
  `StoryRules.applyEffect: nicht-pure Effekte werden gemeldet` (meldet `scene`/`force`/`loseDay`
  an den Aufrufer statt sie selbst auszuführen – bleibt eine reine Funktion),
  `StoryRules.applyEffect: chance würfelt` (`{chance, effects}` mit injizierbarem RNG).
- [x] ✅ **Story-1-Daten validieren** (jede referenzierte Szene/Job/Tür existiert; genau ein
  Fallback-Ende) – `STORY_SCHULD ist gültig`, `StoryRules.validate: Referenzen und Fallback`
  (baut absichtlich eine Story mit fehlender Intro-Szene/unbekanntem Job und einer Story mit
  zwei bzw. null Fallback-Enden und prüft, dass `validate()` das erkennt). Zur Laufzeit ruft
  `Stories.validateAll()` das bei jedem `Story.enter()` erneut auf (`keller37.html:3311`) und
  meldet Fehler per Toast + `console.error` – im gesamten CDP-Lauf kein einziger solcher Fehler.

**Ergebnis:**
```
$ node tests/run-selftest.mjs
81 bestanden, 0 fehlgeschlagen
$ tests/dom-selftest.sh
data-selftest="passed=81 failed=0"
```
(Ein `[bus] t2 Error: boom` in der Node-Ausgabe ist ein absichtlich erzeugter Fehler in einem
Bus-Error-Handling-Test, kein Fehlschlag – zählt nicht zu den 81.)

### 2. CDP-Playthrough-Skript

- [x] ✅ **Eine komplette Story-Runde pro Ende (4 Läufe mit gesetzten Variablen)** –
  `scenario_endings()` in `tests/playtest-story.py`: vier frische Läufe (`?fresh&story=schuld&day=29`
  bzw. `day=30`), je mit den in Spec §9 genannten Bedingungen gesetzt, dann echter
  `Story.night()`-Aufruf:
  - `ehrlich` – `vars.schuld = 0` → `ended: 'ehrlich'`, in `meta.storyRuns.schuld.endings` vermerkt.
  - `sturz` – `flags.hauptbuch/safe/igorZweifelt/sturzJetzt = true` → `ended: 'sturz'`
    (Screenshot `story-ending-sturz.png`, zeigt Don Vito zu Beginn der Abrechnungs-Szene).
  - `taxi` – `flags.fluchtHeute/chantalKennt = true` → `ended: 'taxi'`.
  - `doc` (Fallback) – **exakt wie im Auftrag verlangt** über `?day=30` ohne ein Ende zu erfüllen;
    `Story.night()` zählt auf Tag 31 hoch, keine Bedingung greift, `fallback:true` greift →
    `ended: 'doc'` (Screenshot `story-ending-doc.png`).
  Nach jedem Ende: `meta.storyRuns.schuld.endings` enthält die ID, zum Schluss alle vier.
  Danach Rückkehr zum Titel und Klick auf „Story" bei bestehendem Lauf zeigt die
  Rückfrage-Cutscene (`newgame.confirm`-Analog) statt sofort eine neue Story zu beginnen.
- [x] ✅ **Jede Schicht-Karten-Szene einmal** (5 Jobs × 3 Szenen = 15) – `scenario_all_job_scenes()`:
  alle 5 Schicht-Jobs freigeschaltet, `Jobs.runShift()` je dreimal aufgerufen; `seenJobScenes[job]`
  enthält danach exakt die 3 in `STORY_SCHULD.jobScenes[job]` gelisteten IDs (ohne Wiederholung vor
  „alle gesehen", wie Spec §8 verlangt) – Protokoll siehe unten, für alle 5 Jobs grün.
- [x] ✅ **Jede Szene von Story 1 einmal** (ergänzt über das in §13 explizit Geforderte hinaus, aus
  der Task-9-Checkliste) – `scenario_all_scenes()`: `Object.keys(Story.story.scenes)` liefert 48
  Szenen-IDs (Intro, 3 Kapitel-Intros, alle Ereignis-Szenen, alle 15 Schicht-Karten-Szenen inkl.
  ihrer seltenen Verzweigungen wie `croup.erwischt` [30 %-Chance], `kurier.verhaftet`, `buero2`,
  `tuer.chantal2`, `doc.gehen`, `prakt.korrekt`, `kurier.igor2`, `croup.safe2`, und alle 4 Enden);
  jede wurde einmal per `Story.playScene(id)` gerendert und per echtem Klick durchgesteuert.
  Ergebnis: `gespielt=48/48 fehler=[]` – keine einzige Szene wirft, keine bleibt leer.
- [x] ✅ **Beide Mini-Spiele** (Gewinn und Verlust) –
  - Spüler Gewinn: `scenario_spueler_and_hub()`, `{'hits': 10, 'breaks': 0}` → Lohn 50 €.
  - Spüler Verlust: `scenario_spueler_taxi_loss()`, `{'hits': 0, 'breaks': 10}`, Konto 50 €→0 €
    (Formel ergäbe −100 €, korrekt auf den vorhandenen Betrag gekappt statt negativ zu werden).
  - Taxi Gewinn: `scenario_fast_forward()`, `{'passengers': 50, 'tickets': 0}` (Screenshot
    `story-taxi.png` mitten in der Schicht).
  - Taxi Verlust: `scenario_spueler_taxi_loss()`, `{'passengers': 19, 'tickets': 18}`, Konto
    500 €→0 € (ebenfalls gekappt statt negativ).
- [x] ✅ **Titel ↔ Modi-Wechsel ohne Datenverlust** – `scenario_mode_switch_no_dataloss()`:
  freies Spiel Kontostand auf 12.345 € gesetzt → Titel → Story (neu) → Story-Kontostand auf 777 €
  und `vars.schuld` auf 42.000 € gesetzt → Titel → Freies Spiel: Kontostand wieder **12.345 €**
  (unverändert) → Titel → Story: Kontostand **777 €**, `schuld` **42.000 €** (unverändert). Beide
  Spielstände bleiben in ihren getrennten `localStorage`-Keys (`keller37.state` / `keller37.story`)
  erhalten, wie Spec §4 vorschreibt.
- [x] ✅ **Mobile 400 px** – `scenario_mobile()`, echte `Emulation.setDeviceMetricsOverride`
  (400×800, nicht das ungenaue `--window-size`-Flag, siehe Hinweis aus der Sandbox-Checkliste):
  Pinnwand und Abend-Hub je `document.documentElement.scrollWidth === clientWidth === 400`
  (kein horizontales Scrollen). Screenshot `story-mobile-jobs.png` visuell geprüft: Tagesleiste,
  Pinnwand-Zettel und Bottom-Tab-Leiste passen ohne Überstand in 400 px.

**Zusätzlich über das in §13 wörtlich Genannte hinaus, aber Teil der Task-9-Checkliste:**

- [x] ✅ **Reload mitten im Tag** – `scenario_reload_mid_day()`: Tag 4, Abend, `vertrauen=3`
  gesetzt und gespeichert, echter Seiten-Reload (`Page.navigate` ohne Query-Parameter). Ein
  blanker Reload zeigt zunächst immer den Titelscreen (Spec §3 – das ist gewollt, kein Bug); ein
  Klick auf „Fortsetzen" (Tür „Story") lädt exakt den gespeicherten Stand: Tag 4, Phase `evening`,
  `vertrauen 3`, zurück im Hub – nichts geht verloren.
- [x] ✅ **Reduced Motion** – `scenario_reduced_motion()`, `Emulation.setEmulatedMedia({features:
  [{name:'prefers-reduced-motion', value:'reduce'}]})`: Cutscene-Text erscheint sofort komplett
  (kein Buchstabe-für-Buchstabe-Tippen, `text.length === full.length` direkt nach Szenenstart);
  Spüler-Zielzone bleibt bei jedem Teller 30 % breit (`Spueler.zone.w === 0.3`) statt wie bei
  normaler Bewegung auf 12 % zu schrumpfen – das war bereits Gegenstand von Commit `b0cb75f`
  („Reduced-Motion für Mini-Spiele"), hier erneut bestätigt.
- [x] ✅ **Selbsttests 81** – siehe Abschnitt 1, `81 bestanden, 0 fehlgeschlagen` in beiden
  Runnern.
- [x] ✅ **Freie Sandbox unverändert** – `scenario_free_sandbox_unchanged()`:
  `?screen=slots|roulette|blackjack|hub` (frischer freier Spielstand) gegen
  `docs/superpowers/screenshots/{slots,roulette,blackjack,hub}.png` verglichen (Pixel-Diff via
  Pillow, nach Zuschnitt auf die gemeinsame Höhe – die Referenzbilder wurden mit
  `--window-size=1280,900` per CLI-Screenshot aufgenommen, `Page.captureScreenshot` liefert die
  tatsächliche Content-Höhe 813 px; das ist ein Aufnahme-Unterschied, keine Layout-Änderung):
  Slots 0,19 %, Roulette 0,11 %, Blackjack 0,09 %, Hub 0,10 % unterschiedliche Pixel – ausschließlich
  dynamischer Inhalt (Kontostand, Walzenposition), keine Layout-Verschiebung. Alle vier Screenshots
  wurden zusätzlich visuell angesehen (Hub- und Slots-Screen: Türen, Positionen, Beschriftungen
  identisch zum Referenzbild).

### 3. Freies Spiel

- [x] ✅ Bestehender Selbsttest bleibt grün (jetzt Teil der 81, siehe oben – die ursprünglichen
  57 Sandbox-Tests sind darin unverändert enthalten, keiner wurde entfernt oder umgeschrieben).
- [x] ✅ `?screen=`-Screenshots unverändert – siehe „Freie Sandbox unverändert" oben.
- [x] ✅ `grep -c 'alert(\|confirm(\|prompt(' keller37.html` → `0`.
- [x] ✅ `grep -c 'onclick="' keller37.html` → `0`.

---

## Vollständiges CDP-Protokoll (letzter grüner Lauf)

```
$ python3 tests/playtest-story.py
OK   trophaeen-button: Panel oeffnet sich - hidden=False
OK   trophaeen-button: Trophaeenwand gerendert - count=19
OK   trophaeen-button: Schliessen funktioniert - hidden=True
OK   title: Titelscreen sichtbar nach Boot - hidden=False
OK   intro: Cutscene startet nach Tuerwahl - active=True
OK   intro: 4 Panels durchgeklickt - steps=8
OK   jobs: Screen nach Intro ist Pinnwand - screen=jobs
OK   jobs: Pinnwand zeigt Zettel - notes=2
OK   spueler: Job-Screen geladen - screen=job-spueler
OK   spueler: Schicht gewinnt (hits>breaks) - {'hits': 10, 'breaks': 0}
OK   hub: nach Schicht automatisch Abend-Hub - screen=hub
OK   hub: gesperrte Tueren sichtbar (Bretter) - locked=4
OK   vito: Vitos Tisch erreichbar - screen=vito
OK   vito: Schuld-Anzeige vorhanden - schuld=50000
OK   schlafen: Tag erhoeht sich (Nachtblende) - 1 -> 2 (Story.night() gestartet: True)
OK   post: Postbote-Schicht (mid) erreichbar - screen=postman
OK   nacht: Tag-3-Ereignis (Chantal) ausgeloest - seen=['chantal3'] day=4
OK   kapitel: Tag 6 -> Kapitel k2, Taxi/Kurier/Praktikant frei - chapter=k2 jobs=['spueler', 'post', 'kurier', 'praktikant', 'taxi']
OK   taxi: Job-Screen geladen - screen=job-taxi
OK   taxi: Schicht abgeschlossen - {'passengers': 50, 'tickets': 0}
OK   kontrolle: Tag 10 Fehlschlag loest erzwungenes Duell aus - duel_seen=True
OK   duell: Ausgang als Flag gemeldet (duelWon/duelLost) - {'chantalKennt': True, 'duelLost': True}
OK   ?job=spueler: startet Job direkt ohne Pinnwand-Klick - screen=job-spueler
OK   schicht-karten tuersteher: alle 3 Szenen gesehen
OK   schicht-karten croupier: alle 3 Szenen gesehen
OK   schicht-karten kurier: alle 3 Szenen gesehen
OK   schicht-karten praktikant: alle 3 Szenen gesehen
OK   schicht-karten docassi: alle 3 Szenen gesehen
OK   spueler verliert: Lohn negativ, Konto sinkt - res={'hits': 0, 'breaks': 10} before=50 after=0
OK   taxi verliert: nur Strafzettel, Konto sinkt - res={'passengers': 19, 'tickets': 18} before=500 after=0
OK   modus-wechsel: freies Spiel behaelt Kontostand nach Story-Ausflug - vorher=12345 nachher=12345
OK   modus-wechsel: Story behaelt Stand nach freiem Ausflug - balance=777 schuld=42000
OK   reload mitten im Tag: Tag/Phase/Variablen erhalten - day=4 phase=evening vertrauen=3 screen=hub
OK   mobile 400px: Pinnwand kein horizontales Scrollen - scrollWidth=400 clientWidth=400
OK   mobile 400px: Abend-Hub kein horizontales Scrollen - scrollWidth=400 clientWidth=400
OK   reduced-motion: Cutscene-Text erscheint sofort komplett - text=82 full=82
OK   reduced-motion: Spueler-Zone bleibt 30% (kein Schrumpfen) - zone.w=0.3
OK   ende ehrlich: erreicht - ended=ehrlich
OK   ende ehrlich: in meta.storyRuns vermerkt
OK   ende sturz: erreicht - ended=sturz
OK   ende sturz: in meta.storyRuns vermerkt
OK   ende taxi: erreicht - ended=taxi
OK   ende taxi: in meta.storyRuns vermerkt
OK   ende doc (Fallback ?day=30): erreicht - ended=doc
OK   titel: nach Ende wieder am Titel
OK   titel: 'Neue Story' bei bestehendem Lauf fragt nach - active=True
OK   story-1: jede Szene einmal gerendert (48 Szenen) - gespielt=48/48 fehler=[]
OK   freie sandbox: ?screen=slots Screenshot erstellt
OK   freie sandbox: ?screen=roulette Screenshot erstellt
OK   freie sandbox: ?screen=blackjack Screenshot erstellt
OK   freie sandbox: ?screen=hub Screenshot erstellt

=== ZUSAMMENFASSUNG ===
Checks: 51, davon fehlgeschlagen: 0
ERRORS 0
```

---

## Gefundene Fehler und Fixe (alle im eigenen Commit `21b3483`, s.u. für Details)

Diese drei waren Controller-Vorgaben aus dem Task-9-Brief (kein Playtest-Fund, sondern vorab
festgelegte Korrekturen), umgesetzt vor dem eigentlichen Playtest:

1. **Titelscreen ohne Trophäen-Zugriff** (Spec §3 nennt „Trophäen" auf dem Titelscreen, war nicht
   umgesetzt) → Button „🏆 Trophäen" neben Mute, öffnet/schließt ein Panel mit
   `Achievements.renderWall()`. Verifiziert: `trophaeen-button: *` (3 grüne Checks), Screenshot
   `story-title-trophies.png`.
2. **`croupierJob`-Ereignis ignorierte die Pinnwand-Voraussetzung** – Croupier verlangt laut
   Job-Pool-Tabelle (Spec §8) `jobDone tuersteher ≥ 3`, das Ereignis, das den Job freischaltet,
   prüfte das aber nicht selbst und hätte ihn schon bei Vertrauen 7 + Tag 21 freigeschaltet, auch
   wenn noch nie eine Türsteher-Schicht gemacht wurde → `when`-Bedingung um
   `{ jobDone: 'tuersteher', gte: 3 }` ergänzt. Task-8-Selbsttest angepasst (siehe Diff), bleibt
   grün.
3. **`?job=<id>` fehlte** (in Spec §2 und globalen Constraints als Dev-Parameter dokumentiert, aber
   nicht implementiert) → in `Story.enter()` nach `morning()` ergänzt (neuer Lauf und
   fortgesetzter Lauf), `boot()` erkennt `?job=` zusätzlich als impliziten Story-Modus. Verifiziert:
   `?job=spueler: startet Job direkt ohne Pinnwand-Klick`.

**Während des Playtest-Skripts selbst wurden keine Fehler im Spiel (`keller37.html`) gefunden** –
alle 16 anfänglich fehlgeschlagenen Checks aus dem ersten Skript-Durchlauf waren Fehler im
Test-Skript selbst (Off-by-one bei Tag-Bedingungen, `UI.show()`-„busy"-Race nach
fire-and-forget-Aufrufen von `Story.morning()`, ein früher Titel-Guard-Check vor Ende der
Intro-Cutscene, ein zu früher Rückgabe-Check nach `Story.finish()`). Details:

- **`Story.night()` wird von `#btnSleep`s Klick-Handler nicht awaitet** (kann er nicht, es ist ein
  `addEventListener('click', ...)`). Das erste Playtest-Skript nahm nach dem Klick eine feste
  `sleep()`-Dauer an; unter Last (mehrere Chrome-Prozesse, viele CDP-Roundtrips) reichte die nicht
  immer. *Kein Bug im Spiel* – im Spiel selbst passiert nichts schneller, als ein Mensch klicken
  kann. Fix im Skript: `Story.sleeping === true` abwarten statt fest zu schlafen, mit einem
  Retry-Klick als Sicherheitsnetz.
- **`kontrolleFail`/`chantal3` prüfen `day:{eq:N}` für den *aktuellen* Tag, bevor `Story.night()`
  ihn hochzählt.** Das erste Skript hatte `day=9` vor dem Aufruf gesetzt in der Annahme, die Nacht
  „nach Tag 9" sei „Tag 10" – tatsächlich wertet `Story.night()` die Ereignisse für den Tag aus, der
  gerade zu Ende geht, **bevor** er hochgezählt wird. Fix: `day=10` direkt setzen (analog für
  `chantal3` mit `day=3`).
- **`UI.show()` ist während der Ein-/Ausblend-Animation (~430 ms) „busy" und ignoriert weitere
  `UI.show()`-Aufrufe lautlos.** Ein `Story.morning()`-Aufruf endet selbst mit einem `UI.show('jobs')`;
  folgte das Skript zu schnell mit `Jobs.take(...)` (das intern `UI.show(job.screen)` aufruft),
  kollidierten beide, und der Job-Screen lud nie. *Kein Bug im Spiel* – ein Mensch kann nicht
  schneller als 430 ms zwei Screens hintereinander anfordern, und selbst dann würde nur der zweite
  Klick ignoriert, kein Datenverlust. Fix: auf `!UI.busy` warten statt eine feste Zeit zu raten.
- **`Title.open()`s Guard `Cutscene.active` blockte den allerersten Aufruf lautlos**, weil beim
  frischen Boot von `?mode=free` zuerst die `intro`-Cutscene abgespielt wird; das Skript rief
  `Title.open()` auf, bevor sie durchgeklickt war. *Kein Bug* – exakt das gewollte Verhalten (man
  soll den Titel nicht mitten in einer Cutscene aufreißen können). Fix: Intro zuerst durchklicken.
- **Ein blanker Reload lädt nie automatisch den zuletzt aktiven Modus, sondern zeigt immer den
  Titelscreen** (Spec §3: „Beim Laden erscheint ein Titelscreen"). Das erste Skript erwartete nach
  einem Reload ohne Parameter direkten Zugriff auf `State.s.story` – das existiert aber nur, wenn
  der Modus aktiv ist, was erst nach einem Türklick der Fall ist. *Kein Bug* – „Fortsetzen" lädt den
  Stand dann exakt wieder, wie im entsprechenden Check nachgewiesen. Fix: nach dem Reload erst durch
  den Titel klicken.
- **`Story.finish()` setzt `story.ended` synchron ganz am Anfang**, lange bevor die (mehrseitige)
  Enden-Cutscene fertig durchgeklickt und `Title.show()` erreicht ist. Das erste Skript brach seine
  Warteschleife ab, sobald `ended` gesetzt war, und prüfte dann sofort `#title.hidden` – zu früh.
  Fix: nach `ended` weiter durch die Cutscene klicken, bis sie zu Ende ist, erst dann den Titel
  prüfen.

Kein einziger dieser sechs Fixe hat `keller37.html` verändert – ausschließlich
`tests/playtest-story.py`. Nach jedem Fix wurde der volle Lauf wiederholt; siehe Commit-Historie
des Testskripts für den Verlauf 16 → 1 → 0 Fehlschläge.

---

## Story-Trophäen (Spec §11)

Alle sieben in der Spec genannten neuen Trophäen sind in `Achievements.DEFS` vorhanden
(`group: 'story'`, eigener Abschnitt „Story" auf der Trophäenwand, per
`trophaeen-button: Trophaeenwand gerendert` sichtbar):
`jobFirst` („Erster Arbeitstag"), `teller10` („Tellerwäscher"), `nachtschicht` („Nachtschicht"),
`endeEhrlich` („Der Ehrliche"), `endeTaxi` („Das Taxi"), `endeSturz` („Der Sturz"),
`alleEnden` („Alle Wege"). `meta.storyRuns['schuld'].endings` wächst im CDP-Lauf korrekt
`['ehrlich'] → [...,'sturz'] → [...,'taxi']`.

## Mobile & Reduced Motion – Zusammenfassung

- Mobile 400 px: Pinnwand und Abend-Hub ohne horizontales Scrollen (siehe oben); visuelle Prüfung
  von `story-mobile-jobs.png` bestätigt lesbare Zettel, keine abgeschnittenen Elemente, Bottom-Tabs
  funktionsfähig (bereits als CSS-Infrastruktur aus der Sandbox-Abnahme vorhanden, hier für die
  Story-Bildschirme Pinnwand/Tagesleiste erneut bestätigt statt neu gebaut).
- Reduced Motion: Cutscene-Typewriter deaktiviert, Spüler-Zielzone bleibt konstant 30 % breit
  (siehe oben) – deckt sich mit der bereits in Commit `b0cb75f` behobenen Anforderung.

## Selbst-Review (Auszug, vollständige Fassung im Report)

- [x] Alle vier Enden erreicht (ehrlich/sturz/taxi/doc) – siehe CDP-Protokoll.
- [x] Alle 15 Schicht-Karten-Szenen gesehen (5 Jobs × 3) – siehe CDP-Protokoll.
- [x] Alle 48 Story-1-Szenen einmal gerendert, keine Exception.
- [x] Beide Mini-Spiele Gewinn/Verlust.
- [x] Titel ↔ Modi ohne Datenverlust (beide Richtungen).
- [x] Reload mitten im Tag ohne Datenverlust.
- [x] Mobile 400 px ohne horizontales Scrollen (Pinnwand, Hub).
- [x] Reduced Motion respektiert (Cutscene-Text, Spüler-Zone).
- [x] Node/DOM-Selbsttest 81/81.
- [x] Beide Grep-Kontrollen 0.
- [x] README aktualisiert (Abschnitt „Story-Modus" + Dev-Parameter-Tabelle).
- [x] Screenshots existieren unter `docs/superpowers/screenshots/story-*.png` und wurden angesehen
  (siehe eingebettete Bilder im Report bzw. Beschreibungen oben).
- [x] `Gamble Game.html` nicht angefasst (`git status` zeigt keine Änderung daran).
