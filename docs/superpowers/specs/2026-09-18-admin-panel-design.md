# Admin-Panel (Dev-Werkzeug im Spiel) – Design

**Datum:** 2026-09-18
**Status:** Entwurf, zur Freigabe

## Ziel

Ein verstecktes, passwortgeschütztes Werkzeug in `keller37.html`, mit dem man jeden Teil des Spiels
sofort prüfen kann, ohne ihn freizuspielen: Geld und Grundwerte setzen, jeden Screen öffnen
(Keller, Casino Royal, Stadt, Schießerei, Überfall), jede Story an jedem Tag mit beliebigen Flags
und Vars starten oder fortsetzen, jedes Ende und jede Szene einzeln abspielen. Es ersetzt das
Auswendiglernen der URL-Dev-Parameter und die Browser-Konsole – und funktioniert damit auch auf dem
Handy.

Die bestehenden URL-Parameter bleiben erhalten (Playtests und Doku bauen darauf auf).

## Nicht-Ziele

- Keine echte Sicherheit. Bei einer öffentlichen Ein-Datei-Seite steht die Prüfung in der Datei;
  wer die Konsole öffnet, kommt daran vorbei. Das Panel ist eine Tür mit Schild, kein Tresor.
- Keine handgebauten Sondermasken pro Story. Alles wird aus den vorhandenen Datenstrukturen
  erzeugt, damit neue Storys ohne Pflege im Panel erscheinen.
- Kein Einfluss auf normale Spieler: ohne `?dev` bzw. ohne Anmeldung wird kein DOM angelegt und
  kein Listener registriert. Der Desktop-Screenshot-Diff bleibt 0 px.

## Zugang & Anmeldung

- `keller37.html?dev` öffnet nach dem regulären Boot (Titel oder direkter Screen) eine Login-Box
  (Benutzer, Passwort, „Anmelden"). `dev` ist kein Einmal-Parameter: es wird **nicht** in
  `Story.consumeDevParams` entfernt und zählt **nicht** zu `skipTitle`.
- Prüfung: `DevRules.login(user, pass)` vergleicht `DevRules.hash(user + ':' + pass)` mit der
  Konstante `DEV_LOGIN_HASH`. Der Hash ist cyrb53 (53 Bit, reine JS-Funktion), damit es unter
  `file://`, im LAN ohne HTTPS und in Headless-Tests gleich läuft. Benutzer und Passwort stehen
  nirgends im Klartext.
- Falsche Eingabe: Box wackelt kurz (`.dev-login.shake`, 300 ms), Passwortfeld leert sich, keine
  Angabe, was falsch war.
- Erfolg: `sessionStorage['keller37.dev'] = '1'`. Gilt bis der Tab geschlossen wird, überlebt
  Reloads und Modus-/Story-Wechsel, auch ohne `?dev` in der URL. „Abmelden" löscht den Eintrag und
  entfernt Knopf und Panel.
- Angemeldet: unten rechts ein runder 🛠-Knopf (`#devFab`, 44 × 44 px, `position: fixed`,
  z-Index über Cutscene und Zonen-Vorhang), der das Panel auf- und zuklappt. Er bleibt auf jedem
  Screen, in Cutscenes und im Royal sichtbar.
- Zugangsdaten ändern: In der Browser-Konsole `DevRules.hash('Name:Passwort')` ausführen und das
  Ergebnis in `DEV_LOGIN_HASH` eintragen (steht so in der README).

## Panel-Aufbau

- Schublade von rechts (`#devPanel.open`), Desktop 380 px breit, ≤ 760 px volle Breite; eigener
  schlichter Look (dunkles Grau `#1b1d22`, Monospace, Akzent `#7dd3fc`), bewusst weder Keller- noch
  Royal-Stil. Reagiert nicht auf `body[data-zone]`.
- Kopfzeile: „🛠 Admin" · Modus (frei/Story) · aktueller Screen · Kontostand live · „Abmelden" · „✕".
- Vier Reiter: **Werte · Screens · Story · Szenen**. Der zuletzt offene Reiter wird in
  `sessionStorage['keller37.devTab']` gemerkt.
- Das Spiel läuft hinter der Schublade weiter und bleibt bedienbar. Änderungen wirken sofort
  (Wallet, Seitenleiste, Tagesleiste, Screen neu gerendert, Spielstand gespeichert). Aktionen, die
  einen Neustart bedeuten, tragen „⟲" im Label.
- Jede Aktion bestätigt per Toast (z. B. „🛠 Kontostand → 5.000 €").
- Handy: Reiter als vier gleich breite Knöpfe, Felder volle Breite, alle Tap-Ziele ≥ 44 px, Panel
  scrollt intern (`overflow: auto`, `-webkit-overflow-scrolling: touch`).

## Reiter „Werte"

Wirkt auf `State.s` (frei und Story). Feldnamen kommen aus `State.fresh()`.

- Zahlenfelder mit „Setzen": `balance`, `xp`, `strength`, `beers`, `bankDebt`, `mafiaDebt`,
  `weapon` (0–3). Werte werden per `DevRules.parseNumber(raw, {min, max, int})` geprüft; Müll
  ergibt keine Änderung und einen Toast „Ungültig".
- Schalter (Checkbox): `flags.royalGuest`, `flags.igor`, `flags.brownie`, `hasHouse`, `isMarried`,
  `hasDealer`, `kidneySold`.
- Auswahl: `car` (keins + alle Schlüssel aus `Rules.GEAR.cars`), `shoes` (keins + alle aus `Rules.GEAR.shoes`).
- Knöpfe: „Alle Achievements" (`Achievements.unlock` für alle IDs), „Alle Insider-Skills"
  (`State.meta.insider` = alle IDs, `Perks.refreshExcluded`), „Level max" (`xp` auf den letzten
  Eintrag von `Rules.XP_LEVELS`), „Spielstand löschen (frei) ⟲", „Alles löschen ⟲" (beide
  Spielstände und Meta; entspricht `?fresh`, danach Reload mit `?dev`).
- Nach jeder Änderung: `State.save(); UI.setBalance(State.s.balance); UI.renderWallet();
  UI.renderSide(); if (State.mode === 'story') Story.renderDaybar();`.

## Reiter „Screens"

- Alle Einträge aus `UI.screens` als Knöpfe, gruppiert per `DevRules.groupScreens(ids)`:
  Keller (`hub, roulette, slots, horses, russian, blackjack, hinterzimmer, postman, finance,
  invest, life, skills`), Casino Royal (`royal, megaslots, craps, wheel`), Stadt (`stadt` plus je
  ein Knopf pro Laden aus `Stadt.SHOPS`), Story (`jobs, vito` und alles Übrige – im freien Modus
  ausgegraut), Sonstiges (unbekannte IDs, z. B. `shootout`, damit nichts verloren geht).
- Klick → `UI.show(id)` (bei Läden vorher `Stadt.shop = id`). Zonenwechsel laufen damit normal
  inklusive Gold-Vorhang.
- „Schießerei": Auswahl des Gegners (`junge, kessler, igor, anabi`) → `Shootout.start({ kind:
  'dev', foes: [foe], bonus: GangRules.weapon(State.s).bonus })` und `UI.show('shootout')`.
- „Überfall erzwingen": Knöpfe zufällig / junkie / jugend / cousin → `Mugging.force = true |
  'junkie' | …`; greift beim nächsten Spin. Toast „Nächster Spin: Überfall (…)".

## Reiter „Story"

Kopf: aktuelle Story (Titel), Tag, Phase, voriges Ende (`Story.s.prev`), oder „Keine Story
aktiv".

**Starten (immer verfügbar, „⟲"):**
- Story-Auswahl aus `Stories.all` (inkl. `dev`-Storys, mit Kennzeichnung), voriges Ende
  (Auswahl aus den `endings` der Story in `requires`, nur wenn `requires` gesetzt), Starttag (Zahl,
  Standard 1; > 1 überspringt das Intro wie `?day`), Waffenstufe.
- „Story starten ⟲" → `Story.enter('newstory', opts)`. Dafür wird das Auslesen der URL-Parameter
  in `Story.enter` in ein Options-Objekt `{ fresh, story, prev, day, weapon, ending, job }`
  ausgelagert (`Story.optsFromParams(params)`); URL und Panel füllen dasselbe Objekt, es gibt
  genau einen Startpfad. Vorher wird der Story-Spielstand gelöscht und `State.setMode('story')`
  gesetzt.

**Läuft eine Story:**
- **Vars**: ein Zahlenfeld pro `Object.keys(Story.s.vars)` mit „Setzen".
- **Flags**: eine Checkbox pro Name aus `Object.keys(Story.s.flags) ∪ DevRules.flagNamesIn(story)`.
  `flagNamesIn` sammelt Flag-Namen aus Effekten (`{ flag: … }`, `{ unflag: … }` – die Formen aus
  `StoryRules.applyEffect`) und aus Bedingungen (`flag`, `notFlag`, rekursiv durch `not`, `all`,
  `any` – die Formen aus `StoryRules.check`) in Szenen-Choices, Events, Gates und Enden. So ist z. B. `abgestuerzt` bei „Kater" schaltbar, bevor es je gesetzt wurde.
- „Tag/Phase setzen": Zahl + Auswahl morgens/abends → `Story.s.day`, `Story.s.phase`,
  `State.save()`, dann `Story.enter('story')` – der bestehende Fortsetzungspfad, der `setup()`,
  `applyChapter()` und je nach Phase `morning()` bzw. `evening()` ausführt. Kein eigener Pfad.
- „Job starten": Auswahl aus `Jobs.POOL` gefiltert auf die Jobs der Story (`start.unlocked.jobs`
  ∪ per Effekt freischaltbare) → Job wird in `Story.s.unlocked.jobs` eingetragen, Phase auf
  `morning`, dann `Jobs.take(id)`.
- „Ende abspielen": Auswahl aus `story.endings` → `Story.finish(end)`.
- „Freischalten": Checkboxen für Türen (`Story.DOORS`), Räume (alle Werte aus `Story.ROOM_OF`
  flach) und Jobs → `Story.s.unlocked.*`; danach `UI.renderSide()` und Hub neu rendern.
- Nach jeder Änderung an Vars/Flags: `State.save(); Story.renderDaybar(); UI.renderWallet();
  UI.renderSide();` – **kein** `checkImmediate()`, damit das Panel nicht ungefragt ein Ende auslöst.

## Reiter „Szenen"

- Suchfeld oben (filtert nach ID, Groß-/Kleinschreibung egal).
- Liste aller `Object.keys(Cutscene.SCENES)`, gruppiert: „Keller" (IDs ohne Story-Präfix) und je
  ein Block pro Story aus `Stories.all` (IDs, die in `story.scenes` liegen). Enden werden als
  eigene Zeile „Ende: …" unter der Story geführt und über `Story.finish` abgespielt (nur wenn
  diese Story läuft, sonst ausgegraut).
- Klick → **Vorschau**: `Cutscene.play(id, ctx)` direkt, nicht `Story.playScene`. Entscheidungen
  laufen normal durch, ihre Effekte greifen nicht auf den Spielstand. Kontext: läuft eine Story,
  `Story.ctx()`; sonst der Beispiel-Kontext des heutigen `?scene=` (`bill 900, before 1000, after
  500, price '1.000 €', debt 300, stats {…}`) ergänzt um die Startwerte der Story (`start.vars`
  als Strings, `day 1`, `balance` formatiert). Fehlende Platzhalter bleiben als `{{name}}` sichtbar –
  das ist gewollt, so fallen Tippfehler auf.
- Während einer Szenen-Vorschau schließt sich das Panel; der 🛠-Knopf bleibt.

## Technik

- Zwei neue Script-Blöcke in `keller37.html`:
  - `dev-rules` (rein, kein DOM, nach `royal-rules`): `DEV_LOGIN_HASH`, `DevRules.hash(str)`
    (cyrb53, gibt Zahl als String zurück), `DevRules.login(user, pass)`, `DevRules.parseNumber
    (raw, { min, max, int })` → Zahl oder `null`, `DevRules.flagNamesIn(story)` → sortiertes
    Array, `DevRules.groupScreens(ids)` → `{ keller: [], royal: [], stadt: [], story: [], sonst:
    [] }`, `DevRules.sceneGroups(sceneIds, stories)` → `[{ title, ids }]`. Wird in
    `tests/run-selftest.mjs` in die Block-Liste aufgenommen.
  - `dev` (Panel, nach `story-kater`/`story-stash`, vor `selftest`): `Dev.init()`, `Dev.login()`,
    `Dev.logout()`, `Dev.toggle()`, `Dev.render()` (baut den aktiven Reiter neu), je ein
    `renderWerte/renderScreens/renderStory/renderSzenen`, `Dev.toast(text)`.
- Boot: nach dem regulären Ablauf `if (params.has('dev') || sessionStorage['keller37.dev'])
  Dev.init();`. `Dev.init` legt erst dann DOM an. Nicht angemeldet → Login-Box; angemeldet →
  Knopf.
- CSS-Block `/* -- Admin-Panel -- */` vor `/* -- Reduced Motion -- */`; alle Regeln unter
  `#devFab`, `#devPanel`, `#devLogin`. Keine Regel greift ohne diese IDs.
- `Story.enter(choice, opts)`: `opts` ersetzt die direkten `params.get/has`-Zugriffe. Ohne `opts`
  wird `Story.optsFromParams(new URLSearchParams(location.search))` benutzt; `consumeDevParams`
  bleibt unverändert. `Modes.enter` reicht `opts` durch.
- Bei jedem `UI.show` und `Story.renderDaybar` ruft das Panel, falls offen, `Dev.render()`
  (über den vorhandenen `Bus`, Event `dev:refresh`, das `UI.show` am Ende emittiert – nur wenn
  `Dev.active`).
- Das Panel greift auf globale Module (`State, UI, Story, Stories, Jobs, Cutscene, Shootout,
  Mugging, Stadt, Perks, Achievements, Rules, GangRules`) zu, prüft aber jeweils
  `typeof X !== 'undefined'`, damit es im Node-Runner nicht evaluiert werden muss und im Browser
  bei fehlenden Teilen nur der betreffende Knopf fehlt.

## Fehlerfälle

- Ungültige Zahl → keine Änderung, Toast „Ungültig: …".
- Story-Start mit `prev`, das die Voraussetzung nicht kennt → Auswahl bietet nur gültige Werte an;
  Tag > `story.days` wird auf `story.days` begrenzt.
- „Job starten" mit einem Job, der eine Voraussetzung hat (`requires`), setzt die Voraussetzung
  nicht – der Job startet trotzdem, das Panel ist ein Werkzeug, keine Regelinstanz. Toast weist
  darauf hin.
- Szenen-Vorschau, während eine Cutscene läuft → Knopf inaktiv (`Cutscene.active`).
- `sessionStorage` nicht verfügbar (privater Modus o. ä.) → Anmeldung gilt nur bis zum Reload,
  Panel funktioniert trotzdem.

## Tests

- **Node-Selftest** (`dev-rules`, im Block `selftest` wie die `RoyalRules`-Tests): `hash`
  deterministisch, verschieden für `a:b`/`a:c`; `login`
  richtig, falsch, andere Groß-/Kleinschreibung, führendes Leerzeichen → falsch; `parseNumber`
  mit `min/max/int`, leer, Text, `1e3`; `flagNamesIn(STORY_KATER)` enthält `abgestuerzt`,
  `flagNamesIn(STORY_PROBE)` ist sortiert und ohne Duplikate; `groupScreens` sortiert bekannte
  Screens richtig und legt Unbekanntes in `sonst`; `sceneGroups` ordnet `kater.*` der Story zu.
- **Playtest** `tests/playtest-dev.py` (gleiche Infrastruktur wie `playtest-story.py`, eigener
  Port, Env `K37_PORT/K37_PROFILE/K37_SHOTS`): ohne `?dev` kein `#devFab/#devLogin/#devPanel`;
  mit `?dev` Login sichtbar, falsches Passwort → bleibt zu und `.shake`; richtiges → Knopf da;
  Reload ohne `?dev` → Knopf bleibt; Kontostand setzen → `#balance` zeigt den Wert; Screen
  „royal" → `body[data-zone="royal"]`; Story `kater`, Tag 5 starten → `.hud-leber` sichtbar;
  Flag `abgestuerzt` an → `State.s.story.flags.abgestuerzt === true`; Ende abspielen → Endscreen;
  Vorschau einer Story-Szene mit Entscheidung (Wahl bestätigen) → Kontostand und Vars unverändert;
  Abmelden → Knopf weg, `sessionStorage` leer. Screenshots `docs/superpowers/screenshots/dev-*.png`.
- **Bestehende Suiten** bleiben grün: `node tests/run-selftest.mjs`, `sh tests/dom-selftest.sh`,
  `python3 tests/desktop-diff.py` (0 px), `python3 tests/mobile-check.py` (+ Check: mit `?dev`
  und Anmeldung sind Reiter, Felder und Knöpfe im Panel ≥ 44 px bei 390 px Breite, kein
  horizontaler Overflow), `python3 tests/playtest-story.py`.
- **README**: Abschnitt „Admin-Panel" unter „Dev-Parameter": Aufruf `?dev`, Reiter-Übersicht,
  Hash-Einzeiler, Hinweis „Schild, kein Tresor", neue Test-Zeile.

## Offen / bewusst weggelassen

- Keine Geheimgeste im Spiel (nur `?dev`), keine separate `dev.html`.
- Kein Bearbeiten von `State.meta` jenseits Achievements/Insider (Story-Runs lassen sich über
  „Story starten" mit `prev` nachstellen).
- Keine Live-Bearbeitung von Szenentexten.

## Umsetzungsentscheidungen (Plan 2026-09-18-admin-panel.md)

- `parseNumber` nur Ganzzahlen (Option `int` entfällt); Tausenderpunkte erlaubt.
- „Alle Achievements" schreibt die IDs direkt in `State.meta.achievements` (keine 20 Toasts).
- `UI.show` ruft `Dev.render()` direkt (guarded) statt über ein Bus-Event.
- „Job starten" listet alle Jobs aus `Jobs.POOL`; `Jobs.take(id, { force: true })` überspringt die Verfügbarkeitsprüfung.
- Screen-Sprung auf gesperrten Story-Screen schaltet Tür/Raum frei und lässt Gates einmal durch (`Story.allowOnce`).
- Starttag 1 spielt das Intro, > 1 überspringt es.
- Playtest als eigene Datei `tests/playtest-dev.py` (Port 9371), importiert `playtest-story.py` wie `mobile-check.py`.
- „Jede Aktion bestätigt per Toast" gilt für Änderungen, die die Seite nicht verlassen; die zwei
  Lösch-Knöpfe (⟲) laden sofort neu und zeigen keinen Toast.
- Szenen-Vorschau: `previewCtx()` liefert zusätzlich einen Beispiel-Überfall-Kontext (`type`,
  `loot`, `fight`, `flee`, `extra`, `wallet`, `strength`), `preview()` fängt Fehler mit Toast ab.
- Schießerei aus dem Panel läuft über `Shootout.pending` + Mount-Handshake statt `Shootout.start`
  vor `UI.show` (`start` braucht den bereits gemounteten Screen).
- Toasts bleiben über der offenen Schublade sichtbar: `Dev.toggle`/`Dev.logout` setzen/entfernen
  `body.dev-open`, CSS hebt `#toasts` in dem Zustand über `#devPanel` an.
- `Story.renderDaybar` ruft am Ende ebenfalls `Dev.render()` (guarded wie `UI.show`), damit die
  Schublade auch nach einer reinen Tagesleisten-Aktualisierung aktuell bleibt.
- Story-Screen-Knöpfe im freien Modus sind zusätzlich zur `dim`-Klasse `disabled`.
- Zugangsdaten stehen nirgends im Klartext (weder im Code noch in Tests oder Plänen); Tests nutzen
  Wegwerf-Zugangsdaten über `DevRules.HASH` bzw. den dritten `login`-Parameter.
