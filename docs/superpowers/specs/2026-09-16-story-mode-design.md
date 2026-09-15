# KELLER 37 – Story-Modus

Datum: 2026-09-16
Status: Entwurf, Abschnitte 1–5 im Chat abgestimmt
Branch: `story-mode` (bleibt getrennt von `main`, bis der Modus abgenommen ist)

## 1. Ziel

Ein zweiter Spielmodus neben dem freien Spiel: eine Story über ca. 30 Spieltage mit echten Arbeitsstellen (Mini-Spiele und Schicht-Karten), Kapiteln, Story-Variablen und mehreren Enden. Die Engine ist datengetrieben; drei Storys sind geplant („Die Schuld", „Der Aufstieg", „Die Rückkehr"), bei „Neue Story" wird zufällig eine gezogen. Diese Spec deckt die **Engine, den Job-Pool und Story 1 „Die Schuld"** vollständig ab; Story 2 und 3 sind als Pitch enthalten und werden später als Inhaltspakete ergänzt.

Nicht-Ziele: Änderungen an der Sandbox-Mechanik (§9 der Redesign-Spec bleibt 1:1), neue Casino-Spiele, Multiplayer.

## 2. Rahmenbedingungen

- Weiterhin eine Datei `keller37.html`; Story-Blöcke als eigene `<script id="…">`-Blöcke. Auslagern in `stories/*.js` nur, wenn die Datei > 6.000 Zeilen wird (dann per `<script src>`, Doppelklick funktioniert weiter).
- Das freie Spiel bleibt im Verhalten identisch: eigener Spielstand `keller37.state`, alle Regeln, Spiele, Räume unverändert.
- Story-Spielstand: `keller37.story` (Version 1). Meta (`keller37.meta`) bekommt `storyRuns: { [storyId]: { lastPlayed, endings: [ids] } }`.
- Kein `alert/confirm/prompt`, kein `onclick=""`, Deutsch, Mobile-tauglich, Reduced-Motion wie bisher.
- Dev-Parameter: `?mode=story` (Titel überspringen), `?story=schuld` (Story erzwingen), `?day=12` (Tag setzen, nur mit `?fresh`), `?job=taxi` (Job direkt öffnen), `?ending=sturz` (Ende abspielen).

## 3. Titelbildschirm & Modi

- Beim Laden erscheint ein Titelscreen (Neon „KELLER 37", zwei Türen): **Story** und **Freies Spiel**. Darunter klein: Mute, Trophäen.
- Tür „Freies Spiel": lädt `keller37.state` und startet den Hub wie bisher (Intro-Szene beim ersten Mal).
- Tür „Story": existiert ein laufender Story-Spielstand → Beschriftung „Fortsetzen · Die Schuld · Tag 12/30"; darunter kleiner Link „Neue Story". Sonst „Neue Story".
- „Neue Story" mit laufendem Spielstand → Wirt-Szene mit Rückfrage (wie `newgame.confirm`).
- Story-Auswahl: unter den verfügbaren Storys diejenige mit dem ältesten `lastPlayed` (nie gespielt zählt als ältestes); bei Gleichstand zufällig. Solange nur eine Story existiert, immer diese.
- Rückweg zum Titel: im Story-Modus über die Tagesleiste („Titel"), im freien Spiel über einen neuen Eintrag im Wallet (Icon 🚪), jeweils ohne Datenverlust.
- Der bisherige Sandbox-Game-Over gilt nur im freien Spiel.

## 4. Modus-Umschaltung im Code

- `State` bekommt `mode: 'free' | 'story'` und lädt je nach Modus `keller37.state` oder `keller37.story` in `State.s`. `State.save()` schreibt in den Key des aktiven Modus. Rules, Games, Wallet, Cutscenes bleiben unverändert – sie sehen nur `State.s`.
- Story-Spielstand = Sandbox-Spielstand (gleiche Felder: balance, beers, investments, …) **plus** `story: { id, day, phase: 'morning'|'evening', vars: {}, flags: {}, unlocked: { jobs: [], doors: [], rooms: [] }, jobsDone: { [jobId]: n }, jobToday: null, seen: [sceneIds], ended: null }`.
- `State.freshStory(storyId)` erzeugt ihn aus `fresh()` + Story-Startwerten (`story.start`: balance, unlocked, vars).
- Das Passiv-Einkommen-Intervall und `afterSpin` laufen in beiden Modi; im Story-Modus hängt sich die Engine an `spin:after` (für Ereignisse wie „nach 3 Duell-Siegen").

## 5. Tagesschleife

**Tagesleiste** (ersetzt im Story-Modus das Neonschild als Kopfzeile):
```
Tag 12 / 30   ☀️ Morgen → 🌙 Abend   [Schlafen]        Ziel: Vito 38.500 €
```
Plus die Story-Variablen, die die Story als Zettel anzeigen lässt (z.B. „🤝 Vertrauen 4/10").

- **Morgen** (`phase: 'morning'`): Screen `jobs` (Jobbörse). Ein Job pro Tag (`jobToday`). Nach dem Job (oder per „Kein Job heute") → `phase: 'evening'`.
- **Abend** (`phase: 'evening'`): Hub. Türen/Räume, die nicht in `unlocked` stehen, sind gesperrt (Bretter-Overlay, Kreideschild mit Grund aus der Story, z.B. „Vito sagt nein"). `UI.show()` verweigert gesperrte Screens mit Toast. Seitenleiste zeigt nur freigeschaltete Räume; die Bar ist Raum `bar`.
- **Schlafen** (Knopf in der Tagesleiste, nur am Abend): `Story.night()`:
  1. `night`-Ereignisse der Story (Bedingungen prüfen, Szenen spielen, Effekte anwenden).
  2. Bankzinsen werden nachts **nicht** zusätzlich fällig (sie laufen wie gewohnt pro Spin); Mafia-Kredite gibt es im Story-Modus nur, wenn die Story den Raum `mafia` freischaltet.
  3. Enden prüfen (nach Priorität) → falls eins greift: Ende abspielen, `ended` setzen, Meta aktualisieren, zurück zum Titel.
  4. `day + 1`, `phase: 'morning'`, `jobToday: null`; Kapitel-Wechsel prüfen (Kapitel-Intro-Szene), Freischaltungen anwenden (Toast „Neu an der Pinnwand: …" / „Tür geöffnet: …").
  5. Speichern.
- Tag > `story.days` ohne greifendes Ende → das Ende mit `fallback: true` (jede Story muss genau eins haben).

## 6. Bedingungen (Datensprache)

Jede Bedingung ist ein Objekt; `Story.check(cond, s)` wertet aus:
```js
{ day: { gte: 10 } } | { day: { eq: 25 } } | { day: { lte: 5 } }
{ balance: { gte: 5000 } }
{ var: 'vertrauen', gte: 4 } | { var: 'schuld', lte: 0 }
{ flag: 'igorZweifelt' } | { notFlag: 'geflohen' }
{ jobDone: 'tuersteher', gte: 3 }
{ unlocked: 'croupier' }
{ all: [ … ] } | { any: [ … ] } | { not: … }
```
Vergleichsoperatoren: `eq, ne, gte, lte, gt, lt`. Ungültige Bedingungen werfen beim Laden der Story (der Selbsttest fängt das ab).

## 7. Story-Datenformat

```js
Stories.define({
  id: 'schuld', title: 'Die Schuld', days: 30,
  start: { balance: 50, unlocked: { jobs: ['spueler', 'post'], doors: ['slots', 'horses'], rooms: ['bar', 'vito'] }, vars: { schuld: 50000, vertrauen: 0, ruf: 0 } },
  hud: [ { var: 'schuld', label: 'Vito', fmt: 'money', tone: 'danger' }, { var: 'vertrauen', label: '🤝', max: 10 } ],
  goalText: (s) => `Ziel: Vito ${UI.fmt(s.story.vars.schuld)}`,
  intro: 'schuld.intro',                    // Szene beim Start
  chapters: [ { id, title, when: cond, intro: sceneId, unlock: { jobs, doors, rooms } } ],
  events: [ { id, when: cond, once: true, at: 'night'|'morning'|'spin:after', scene: sceneId, effects: [ … ] } ],
  jobScenes: { tuersteher: [ sceneIds… ], … },   // Story-spezifische Schicht-Karten-Szenen
  endings: [ { id, title, priority, when: cond, scene: sceneId, fallback?: true } ],
});
```
- **Effekte** (in Szenen-Choices und Ereignissen): `{ var: 'vertrauen', add: 1 }`, `{ var: 'schuld', set: 0 }`, `{ flag: 'x' }`, `{ balance: -250 }`, `{ unlock: { jobs: ['taxi'] } }`, `{ force: 'duel' }` (erzwungenes Spiel), `{ loseDay: true }`.
- Szenen werden mit der bestehenden `Cutscene.define` definiert; Choices bekommen zusätzlich `effects: [...]`, die die Engine nach der Wahl anwendet. Platzhalter `{{var.schuld}}`, `{{day}}`, `{{balance}}` werden aus dem Story-Kontext gefüllt.
- **Prüfungen / erzwungene Spiele:** `force: 'duel'` startet `Russian.start({ forced: true, bet: 0 })`: kein Einsatz, Ausgang wird als Flag `duelWon`/`duelLost` gemeldet (Spieler getroffen = Story-Effekt, kein Spital).

## 8. Job-Pool

Gemeinsamer Pool, jede Story schaltet ihre Auswahl frei. Ein Job pro Tag. Lohn fließt über `Game.applyDelta` (kein Spin, kein `afterSpin`).

**Mini-Spiele:**

| id | Name | Mechanik | Lohn |
|---|---|---|---|
| `spueler` | 🍽️ Spüler | Timing-Balken: ein Teller rutscht über ein Band, Klick/Tap in der Trefferzone. 10 Teller, Tempo steigt (Zone 30 % → 12 %). Treffer +5 €, daneben −10 € (Bruch, Klirren, Shake). Reduced-Motion: Zone bleibt 30 %. | 0–50 € |
| `post` | 📬 Postbote | bestehendes Spiel, unverändert (Schicht endet bei Fehler oder nach 15 Briefen) | wie bisher |
| `taxi` | 🚕 Nachttaxi | Draufsicht, 3 Spuren, 60 s. Fahrgäste erscheinen am Rand, Spurwechsel per ←/→ oder Tap links/rechts; Fahrgast aufgenommen = +15 €. Ampeln kreuzen die Straße: bei Rot bremsen (Leertaste/Tap Mitte), sonst Strafzettel −50 €. Voraussetzung 200 € Kaution (bleibt erhalten). | −100 bis 300 € |

**Schicht-Karten** (Klick „Schicht antreten" → eine Szene aus dem Story-spezifischen Satz, zufällig, ohne Wiederholung bis alle gesehen; Grundlohn + Entscheidungs-Effekte):

| id | Name | Grundlohn | Voraussetzung im Pool |
|---|---|---|---|
| `tuersteher` | 🚪 Türsteher | 100 € | Story schaltet frei |
| `croupier` | 🃏 Croupier | 150 € | `jobDone tuersteher ≥ 3` + Story |
| `kurier` | 💊 Kevins Kurier | 300 € | Story |
| `praktikant` | 👔 Praktikant bei Krause | 120 € | Story |
| `docassi` | 🩺 Assistent beim Doc | 250 € | Story |

Jede Schicht-Karte hat in Story 1 mindestens 3 Szenen mit je einer Entscheidung (2–3 Optionen). Typische Effekte: Geld, `vertrauen`, `ruf`, Flags (`insider`, `komplize`, `kesselGehalten`, `verhaftet`), `loseDay` (Kurier verhaftet: Tag endet sofort, −200 €).

**Jobbörse-Screen:** Pinnwand (Kork-Textur) mit Aushängen als Zettel; gesperrte Jobs hängen ausgegraut mit Grund; erledigte Jobs zeigen „heute schon gearbeitet". Knopf „Kein Job heute" → Abend.

## 9. Story 1: „Die Schuld"

**Variablen:** `schuld` (50.000; sinkt durch Zahlungen im Raum `vito` – Ratenzahlung beliebig ab 100 €), `vertrauen` 0–10, `ruf` 0–10. Flags: `chantalKennt`, `hauptbuch`, `safe`, `igorZweifelt`, `kesselGehalten`, `insider`, `komplize`, `verhaftet`, `fluchtBereit`, `duelWon`, `duelLost`.

**Räume:** `bar`, `bank` (ab Kap. 2), `invest` (ab Kap. 3), `vito` (neuer Raum „Vitos Tisch": Rate zahlen, Frist sehen; ersetzt in dieser Story die Mafia-Kredite), `life` (nur Bier-Zwang-Logik; Villa/Tinder gesperrt). Der Sandbox-Mafia-Kredit ist gesperrt.

**Intro** (4 Panels, Keller/Hinterzimmer): Aufwachen, Igors Zettel, Vitos Erklärung („Dreißig Tage. Ich bin kein Unmensch."), Wirt gibt 50 € und den Spüler-Job.

| Kapitel | `when` | Freischaltung | Kernszenen / Ereignisse |
|---|---|---|---|
| 1 „Der Zettel" | day ≥ 1 | Jobs spueler, post · Türen slots, horses · Räume bar, vito | Tag 3 Nacht: Chantal an der Bar (`chantalKennt`). Tag 5 Nacht: Wirt: „Vito hat noch nie jemanden *bezahlen* lassen." |
| 2 „Kleine Fische" | day ≥ 6 | Jobs kurier, praktikant, taxi · Türen roulette, blackjack, russian · Raum bank | Tag 10 Nacht **Kontrolle**: balance ≥ 5.000 oder schuld ≤ 45.000 → Vito zufrieden (+1 vertrauen); sonst erzwungenes Duell (`force: 'duel'`); `duelLost` → −500 € Spital, Flag. |
| 3 „Die Tür" | day ≥ 13 | Jobs tuersteher (wenn vertrauen ≥ 4), docassi · Raum invest | Erste Türsteher-Nacht: Büro-Szene → `hauptbuch` möglich (Entscheidung: reinschauen / nicht). Chantal-Geständnis (Tag ≥ 15, `chantalKennt`). Igor: nach 3 Duell-Siegen (`spin:after`-Ereignis) → `igorZweifelt`. |
| 4 „Abrechnung" | day ≥ 21 | Job croupier (vertrauen ≥ 7) · alle Türen | Croupier: Safe-Szene → `safe`. Tag 25 Nacht **Erinnerung**: Igor, −20 % Konto (min. 100 €). Taxi + balance ≥ 8.000 + day ≥ 20 → Kevin-Szene bietet Flucht (`fluchtBereit`). |

**Enden** (Priorität absteigend, geprüft jede Nacht):
1. `ehrlich` – `schuld ≤ 0`: Hafen, Vito beeindruckt. Sofort in der Nacht, in der die Schuld 0 erreicht.
2. `sturz` – day ≥ 28 ∧ `hauptbuch` ∧ `safe` ∧ `igorZweifelt`: Igor kommt statt Vito, der Wirt übernimmt. (Ab Tag 28 wählbar über Wirt-Szene „Jetzt oder nie" mit Choice; sonst Tag 30.)
3. `taxi` – `fluchtBereit` ∧ Spieler wählt in der Kevin-Szene „Heute Nacht": Hafen, Chantal steigt ein, wenn `chantalKennt` und nicht `komplize`.
4. `doc` – **fallback**, day > 30: Doc-Szene, Blackout.

**Vertrauen:** +1 pro 5.000 € Zahlung, +1 Kontrolle bestanden, +1 pro 3 Türsteher-Schichten ohne „Gast reingelassen", +1 Duell-Sieg (max. 3); −2 `kesselGehalten` erwischt (30 %), −1 `verhaftet`, −3 wenn Igor die Flucht sieht (`fluchtBereit` und Türsteher-Schicht danach). **Ruf:** +1 Taxi-Schicht ≥ 150 €, +1 Kurier, +1 Doc; −2 Kevin verpfiffen.

Szenenzahl Story 1: Intro 4 Panels, 4 Kapitel-Intros (je 2–3), 8 Ereignisse (je 1–3), 5 Schicht-Karten × 3 Szenen (je 2 Panels + Choice), 4 Enden (je 3–4 Panels + Statistik) ≈ 60 Panels.

## 10. Story 2 & 3 (Pitch, nicht Teil des ersten Plans)

- **„Der Aufstieg"** (25 Tage): Rangleiter Spüler → Türsteher → Croupier → rechte Hand; Variablen `rang`, `vertrauen`, `gewissen`; Prüfungen Tag 8 (Duell), 16 (Kevin decken/verpfeifen), 24 (Vitos Angebot); Enden „Der Partner", „Der Wirt", „Der Knast".
- **„Die Rückkehr"** (20 Tage): Variable `beweise` 0–5 (Krause, Doc, Büro, Safe, Chantal), `verdacht` 0–5 (bei 5: Igor holt dich ab); Enden „Der Besitzer", „Der Deal", „Der Hafen".
- Beide nutzen ausschließlich Engine-Features aus §5–8.

## 11. Achievements & Meta

Neue Trophäen: „Erster Arbeitstag", „Tellerwäscher" (10/10 Teller), „Nachtschicht" (Taxi ≥ 200 €), „Der Ehrliche", „Das Taxi", „Der Sturz", „Alle Enden einer Story". Die Trophäenwand bekommt einen Abschnitt „Story". `meta.storyRuns[id].endings` speichert erreichte Enden.

## 12. UI-Details

- Titelscreen: Vollbild, Neonschild, zwei Türen im Hub-Stil, Hover-Buzz, Footer mit Mute/Trophäen.
- Tagesleiste: Bebas Neue, Tagzähler groß; Phase als kleine Neon-Icons; „Schlafen" als Gold-Button; Ziel-Text rechts; Story-Zettel darunter (gleiche `.note`-Optik).
- Gesperrte Tür: zwei diagonale Bretter (CSS), Schild dunkel, Kreide-Tag zeigt Grund.
- Jobbörse: Korkwand, Zettel mit Reißzwecke, Lohn in Courier Prime, Job-Icon groß; Mini-Spiele in eigenen Panels im Stil des Postboten (Tageslicht) bzw. des Kellers (Spüler).
- Nacht-Übergang: kurze Schwarzblende mit „Tag 13" in Neon (1 s), dann Morgen.

## 13. Verifikation

- Selbsttest (Node + Browser): Bedingungs-Auswertung (alle Operatoren, `all/any/not`, ungültig wirft), Story-Auswahl, `Story.night()` auf einem Fixture-State (Tag +1, Phase, Kapitel-Trigger, Freischaltung, Enden-Priorität, Fallback nach Tag 30), Lohnberechnung Spüler/Taxi, Effekt-Anwendung (`add/set/flag/unlock/balance`), Story-1-Daten validieren (jede referenzierte Szene/Job/Tür existiert; genau ein Fallback-Ende).
- CDP-Playthrough-Skript (wie `playtest.py`): eine komplette Story-Runde pro Ende (4 Läufe mit gesetzten Variablen), jede Schicht-Karten-Szene einmal, beide Mini-Spiele, Titel ↔ Modi-Wechsel ohne Datenverlust, Mobile 400 px.
- Freies Spiel: bestehender Selbsttest bleibt bei 57 grün; `?screen=`-Screenshots unverändert.

## 14. Umsetzungsreihenfolge

1. State-Modi + Titelscreen + Story-Save + Tagesleiste + Nacht-Übergang (Engine-Kern, Bedingungen, Effekte, Selbsttests).
2. Jobbörse + Schicht-Karten-Runner + gesperrte Türen/Räume + Raum „Vitos Tisch".
3. Mini-Spiele Spüler und Nachttaxi.
4. Story 1 Kapitel 1–2 (Intro, Szenen, Kontrolle mit erzwungenem Duell).
5. Story 1 Kapitel 3–4 + vier Enden + Achievements.
6. Playtest-Skript, Checkliste, Screenshots.
7. (Später) Story 2, Story 3.
