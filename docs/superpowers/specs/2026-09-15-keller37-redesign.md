# KELLER 37 – Komplett-Redesign des „Underground Casino"

Datum: 2026-09-15
Status: Entwurf, vom Autor abgestimmt (Abschnitte 1–5 in Chat freigegeben)

## 1. Ziel

Die bestehende Datei `Gamble Game.html` (1.206 Zeilen, ein satirisches Casino-Lebenssim-Spiel auf Deutsch) wird als **eine neue HTML-Datei** neu aufgebaut. Ziele:

- Die Spielmechanik bleibt **1:1** erhalten (alle Quoten, Preise, Timer, Wahrscheinlichkeiten – siehe Abschnitt 9). Einzige Regeländerung: Bank-Kreditlimit als Voraussetzung für Game Over (Abschnitt 8.3).
- Alle `alert()` / `confirm()` / `prompt()` verschwinden. Story-Ereignisse werden Visual-Novel-Cutscenes, Kleinkram wird Toast.
- Ein durchgehender Look („Seedy Underground") mit Textur, Neon, Filz statt gleichförmiger grauer Karten.
- Jedes Minispiel bekommt echte Animation.
- Neu: Sound (synthetisiert), Speichern (localStorage), Game Over mit Neustart, Achievements.

Nicht-Ziele: Balancing ändern, Build-Tooling, Frameworks, externe Assets außer Google Fonts (mit Fallback).

## 2. Rahmenbedingungen

- Genau eine Datei: `keller37.html`. Die alte Datei bleibt unangetastet als Referenz liegen.
- Läuft per Doppelklick (`file://`), keine Abhängigkeiten außer optional geladenen Google Fonts.
- Desktop-first, ab < 760 px Breite ein Mobile-Layout (Abschnitt 8.5).
- Sprache der UI und Szenen: Deutsch.
- `prefers-reduced-motion` schaltet Shake, Partikel und Flackern ab.

## 3. Architektur

### 3.1 Dateigliederung

Feste Blöcke mit Kommentar-Bannern in dieser Reihenfolge:

```
<style>
  1. Tokens        – Farben, Fonts, Abstände, Schatten
  2. Basis/Textur  – Reset, Körnung, Vignette, Filz, Neon-Flackern
  3. Layout        – Shell, Wallet-Bar, Seitenleiste, Screens, Übergänge
  4. Komponenten   – Buttons, Chips, Zettel, Kreidetafel, Toasts, Modal
  5. Cutscene      – Overlay, Orte, Portrait, Dialogbox, Choices
  6. Spiele        – ein Block je Spiel und je Raum
  7. Animationen   – alle @keyframes gesammelt
<body>
  Shell (Wallet-Bar, Seitenleiste, Bühne) + je Screen ein <template>
<script>
  1. Rules         – reine Funktionen, kein DOM, kein State
  2. State         – state-Objekt, save()/load()/reset(), Versionierung
  3. Bus           – on(event, handler) / emit(event, payload) → Promise
  4. UI            – Screen-Router, Toasts, Money-Counter, FloatingNumber, Shake
  5. Cutscene      – Engine, Charaktere, Orte, Szenen-Daten
  6. SFX           – Web-Audio-Synth, mute
  7. Achievements  – Definitionen + Listener
  8. Games         – roulette, slots, horses, russian, blackjack, postman
  9. Rooms         – life, invest, finance, bar
  10. Boot         – load, mount, Intro oder Hub
```

### 3.2 Grundregeln

- **`Rules`** enthält nur pure Funktionen. Alles, was eine Zahl aus dem alten Spiel reproduziert, lebt hier:
  `luck(state)`, `spinCosts(state)`, `maxBet(state)`, `roulettePayout(type, chosen, rolled, bet)`, `rouletteLuckOverride(type, chosen, rolled, luck, rng)`, `slotMultiplier(a,b,c)`, `slotLuckOverride(res, luck, rng)`, `horseStep(isSelected, luck, rng)`, `handSum(hand)`, `dealerShouldHit(hand)`, `bjOutcome(player, dealer)`, `postmanTier(streak)`, `investmentResolve(inv, rng)`, `mafiaBill(debt)`, `bankInterest(debt)`, `isGameOver(state)`.
  `rng` wird injiziert (Default `Math.random`), damit der Selbsttest deterministisch ist.
- **`state`** ist ein einziges Objekt (Abschnitt 3.3). Keine losen globalen Variablen.
- Spiellogik ruft nie direkt UI, Sound oder Cutscene auf. Sie tut `await Bus.emit('divorce', {...})`. `emit` wartet, bis alle Handler (inkl. Cutscene-Promise) fertig sind.
- Kein `onclick=""` im HTML. Jeder Screen hat `mount(root)` (Events binden, initial rendern) und `unmount()` (Timer aufräumen).
- `afterSpin()` behält exakt die alte Reihenfolge: Bier-Timer → Brownie-Timer → Ehe → Liebeskummer → Mafia → Anlagen → Game-Over-Check → save.

### 3.3 State

```js
state = {
  v: 1,
  balance: 50,
  beers: 0, beerTimer: 0,
  brownieTimer: 0, brownieCost: 1000,
  kidneySold: false,
  bankDebt: 0, mafiaDebt: 0, mafiaSpins: 0,
  investments: [ {name, amount, rate, spins, risk} ],
  hasHouse: false, isMarried: false, marriageSpins: 0, isHeartbroken: false, hasDealer: false,
  flags: { intro:false, mafiaLoan:false, bankLoan:false, brownie:false, igor:false },  // "Szene schon gesehen"
  stats: { spins:0, maxBalance:50, biggestWin:0, kidneys:0, postStreakBest:0 },   // wird bei "Nochmal" zurückgesetzt
  selectedHorse: 1
}
// getrennt gespeichert (überleben Reset):
meta = { achievements: [ids], muted: false, gameOvers: 0 }
```

Speicher-Keys: `keller37.state`, `keller37.meta`. `load()` prüft `v`; unbekannte Version → Neustart mit Hinweis-Toast.

### 3.4 Bus

`Bus.on(name, fn)`; `Bus.emit(name, payload)` ruft alle Handler, sammelt zurückgegebene Promises, gibt `Promise.all` zurück. Events (Auszug): `spin:before`, `spin:after`, `balance:change {delta, source}`, `win`, `loss`, alle Szenen-Events aus Abschnitt 6.4, `achievement:unlock`.

## 4. Look & Layout

### 4.1 Tokens

| Token | Wert | Verwendung |
|---|---|---|
| `--bg` | `#0a0c09` | Grund |
| `--panel` | `#141712` | Panels, Seitenleiste |
| `--felt` | `#0f3d2e` | Spieltische |
| `--gold` | `#c9a227` | Gewinn, Rahmen, Wallet |
| `--neon-red` | `#ff3b3b` | Roulette, Verlust, Gefahr |
| `--neon-amber` | `#ffb432` | Slots, Warnung |
| `--neon-blue` | `#4cc9f0` | Russisches Roulette, Bank |
| `--neon-green` | `#3ddc84` | Pferde |
| `--day` | `#f5d67a` | Post (Tageslicht) |
| `--text` | `#e8e2d0` | Fließtext |
| `--dim` | `#8a8577` | Nebentext |

Fonts (Google Fonts `<link>`, mit Fallback): **Bebas Neue** (Schilder, Titel, Buttons; Fallback Impact/Arial Narrow), **Courier Prime** (alle Zahlen; Fallback Courier New), System-Sans für Fließtext.

### 4.2 Textur

- Körnung: SVG `feTurbulence` als Data-URI, fixed-position Overlay, `opacity: .05`, `pointer-events: none`.
- Vignette: `radial-gradient` fixed über `body`.
- Filz: dunkles Grün + `repeating-linear-gradient` mit 1px-Versatz, sehr niedrige Deckkraft.
- Neon: Text mit mehrfachem `text-shadow`; Flackern per `@keyframes neonFlicker` mit unregelmäßigen Keyframes, ~7 s Zyklus, `animation-delay` per Element gestreut.

### 4.3 Shell

```
┌──────────────────────────────────────────────────────┐
│ [KELLER 37 neon] [🔇]     🍀 ▮▮▮░░      💰 1.250 €   │  Wallet-Bar (sticky)
│      Status-Zettel: [💍 Chantal · 1 Spin] [🕶 3.000 € · 2 Spins] [💊 -20 €/Spin]
├──────────────────────────────────┬───────────────────┤
│                                  │  DIE BAR          │
│   Bühne: Hub oder Screen         │  🍺 Bier 50 €     │
│                                  │  🍪 Brownie 1k €  │
│                                  ├───────────────────┤
│                                  │  HINTERZIMMER     │
│                                  │  🫁 Niere         │
│                                  │  🏦 Kredite       │
│                                  │  📈 Anlagen       │
│                                  ├───────────────────┤
│                                  │  ZUHAUSE 🏡       │
└──────────────────────────────────┴───────────────────┘
```

- Wallet: Kontostand in Courier Prime, zählt animiert (Money-Counter, ~600 ms, ease-out). Gewinn: Goldpuls. Verlust: Rotpuls + 200 ms Wackeln. Zusätzlich fliegt eine „+120 €"/„−50 €"-Zahl vom Spiel-Element zur Wallet.
- Glück als 5-Segment-Kleeblatt-Meter (0/10/15/20/40/60 → Segmente + Glow), Tooltip mit Prozent.
- Status-Zettel: kleine „Notizzettel" mit leichter Rotation; erscheinen/verschwinden mit Pop.
- Klick auf das Neonschild = zurück zum Hub. `Esc` ebenfalls. Kein Zurück-Button.

### 4.4 Hub („Der Gang")

Sechs Türen in 3×2 (Mobile 1 Spalte), jede: Tür-Silhouette, Neonschild in Signalfarbe, Kreide-Untertitel (Quote), beim Hover: Schild hell, Lichtspalt unter der Tür, `neonBuzz`-Sound. Reihenfolge: Roulette, Slots, Pferderennen, Russisches Roulette, Black Jack, Post austragen (Tür mit Tageslicht).

### 4.5 Screen-Wechsel

Alter Screen: opacity→0, translateY(−8px), 180 ms. Neuer: opacity 0→1, translateY(8px→0), 250 ms. Während des Wechsels `pointer-events: none`. `unmount()` des alten Screens räumt Intervalle auf (Postbote-Timer!).

## 5. Komponenten

- **Button**: Bebas Neue, Uppercase, 2px Rahmen in Signalfarbe, Innenglow bei Hover, `scale(.97)` beim Drücken, disabled = ausgegraut mit Kreide-Notiz daneben statt langem Text im Button.
- **Chip**: runde Spielchip-Optik (Doppelrand, Wert mittig), Werte 10/25/50/100/Max; Klick setzt Einsatz, Chip „fliegt" 300 ms zum Einsatzfeld.
- **Einsatzfeld**: Number-Input in Courier Prime, mit −/+ Tasten; Max = `Rules.maxBet(state)`.
- **Zettel** (Status, Schuldschein, Ticket): heller Papierton, leichte Rotation, Schatten.
- **Kreidetafel**: dunkler Grund, Kreidefont-Optik (leicht unscharfer weißer Text), für Auszahlungstabellen und gesperrte Hinweise.
- **Toast**: rechts unten, Zettel-Optik, Icon + Titel + Text, slide-in 250 ms, 3 s stehen, max. 3 gestapelt.
- **Modal** (nur für „Neues Spiel?"): wird als Cutscene beim Wirt mit Choice umgesetzt, kein eigenes Modal.

## 6. Cutscene-System

### 6.1 Engine

- Vollbild-Overlay (`position: fixed`), Hintergrund = Ort-Layer + Abdunkelung + `backdrop-filter: blur(6px)` auf dem Spiel darunter.
- Aufbau: Ort (oben, ganze Fläche), Portrait (links, ~180 px Kreis mit Goldrahmen, Emoji ~6 rem), Name-Tag (Charakterfarbe), Dialogbox (unten, Papier/Dunkel je nach Ort), Weiter-Pfeil, „Überspringen"-Link rechts unten.
- Typewriter: 30 ms/Zeichen, Satzzeichen 120 ms Pause, `typewriter`-Sound alle 3 Zeichen. Klick/Leertaste/Enter: Zeile sofort komplett; nochmal: nächstes Panel.
- Überspringen: springt zum letzten Panel; Effekte aller übersprungenen Panels werden sofort (ohne Animation) ausgeführt, damit der State stimmt.
- API: `await Cutscene.play(sceneId, ctx)`; `ctx` liefert Werte für Platzhalter (`{{bill}}`, `{{half}}`).
- Choices: Panel mit `choices: [{label, value}]` rendert Buttons statt Weiter-Pfeil; `play()` resolved mit dem gewählten `value`.

### 6.2 Panel-Datenformat

```js
{ bg:'hafen', who:'vito', mood:'calm'|'angry'|'happy'|'shock'|'dead', text:'…',
  fx?: 'flash'|'shake'|'blackout'|'hearts'|'drain'|'coins', choices?: [...] }
```
Moods steuern Portrait-Animation: `angry` wackelt, `happy` hüpft, `shock` zoomt kurz, `dead` graut aus und kippt.

### 6.3 Orte (CSS-Gradients + 1–2 Silhouetten)

`bar` (warm, Flaschenregal), `hinterzimmer` (Holz, Lampe), `standesamt` (hell, Blumen), `villa` (Nachtblau, Skyline), `hafen` (Schwarz-Blau, Kran, Mond), `hafen-morgen` (Orange-Grau, Sonnenaufgang), `klinik` (kaltes Türkis, Neonröhre), `bank` (Glas, blau), `strasse` (Tageslicht), `keller` (Beton, Glühbirne, für Igor).

### 6.4 Cast

| id | Name | Emoji | Farbe | Stimme |
|---|---|---|---|---|
| `wirt` | Der Wirt | 🍺 | amber | müde, trocken |
| `chantal` | Chantal-Monique | 💅 | pink | „Ehrlich jetzt", ✨ |
| `vito` | Don Vito | 🕶️ | rot | höflich, jedes Wort Drohung |
| `igor` | Igor | 🐻 | blau | einsilbig |
| `doc` | Der Doc | 🥼 | türkis | zynischer Hinterzimmer-Chirurg |
| `krause` | Herr Krause | 👔 | blau | Beamten-Freundlichkeit |
| `makler` | Der Makler | 🧑‍💼 | gold | schleimig |
| `schmalz` | Dr. Schmalz | ⚖️ | grau | rechnet laut |
| `kevin` | Kevin | 🧢 | lila | „Digga" |
| `postmeister` | Der Postmeister | 📬 | gelb | anständig |
| `du` | Du | 🤠 | weiß | (nur in Choices / Reaktionen) |

### 6.5 Szenen

| Event | Auslöser | Ort | Panels | Effekte / Choices |
|---|---|---|---|---|
| `intro` | erster Start (kein Save) | bar | 3 | – |
| `house.bought` | Villa gekauft | villa | 2 | – |
| `tinder.match` | Tinder Gold | standesamt | 3 | `hearts` |
| `divorce` | 2 Spins nach Hochzeit | hafen | 4 | `drain` (Kontostand halbiert sich sichtbar), Wirt-Panel am Ende: 2-Bier-Pflicht |
| `heartbreak.collapse` | Spin mit < 2 Bier bei Liebeskummer | klinik | 2 | `shake`, −250 € |
| `therapy.done` | Therapie bezahlt | hinterzimmer | 2 | – |
| `dealer.hired` | Dealer bezahlt | strasse | 2 | – |
| `kidney.offer` | Klick auf Niere | klinik | 2 | Choice „Ja, brauch das Geld" / „Nein" |
| `kidney.sold` | Choice Ja | klinik | 2 | `blackout`, `coins` |
| `mafia.loan` | erster Mafia-Kredit | hinterzimmer | 3 | – |
| `mafia.lastcall` | mafiaSpins == 1 nach Spin | hinterzimmer | 1 | – |
| `mafia.legbreak` | Frist abgelaufen | hinterzimmer→klinik | 3 | `blackout`, `shake`, Rechnung `{{bill}}` |
| `bank.loan` | erster Bankkredit | bank | 2 | – |
| `bank.limit` | Kreditanfrage über Limit | bank | 1 | – |
| `brownie.first` | erster Brownie | bar | 1 | – |
| `igor.first` | erstes Duell | keller | 2 | – |
| `rr.headshot` | Kugel beim Spieler | klinik | 1 | `flash`, `shake` |
| `newgame.confirm` | „Neues Spiel" | bar | 1 | Choice „Ja, alles weg" / „Doch nicht" |
| `gameover` | siehe 8.3 | hafen-morgen | 3 | Panel 3 zeigt Statistik-Tabelle + Button „Nochmal" |

Toasts (kein Overlay): Bier (Prost, +x %), Brownie (ab dem zweiten), Zinsen/Meds abgezogen, Anlage ausgezahlt/verloren, Passiveinkommen (nur alle 60 s ein Sammel-Toast), Achievement, Spielstand geladen, Max. 3 Bier.

## 7. Spiele

Alle Zahlen: Abschnitt 9. Wer einen Spiel-Screen mitten in einer Runde verlässt (Blackjack-Hand, Pferderennen, Duell), verliert den Einsatz: Er wurde beim Start abgezogen (Abschnitt 9, „Kosten pro Spin") und wird nicht zurückgezahlt; ein Toast „Einsatz verfallen" weist darauf hin. Bereits laufende Animationen mit feststehendem Ergebnis (Slots, Roulette) laufen im Hintergrund zu Ende und werden normal abgerechnet.

### 7.1 Roulette (rot)
- Kessel: Canvas 320 px, Holzrand, 37 Fächer (Reihenfolge wie bisher), Gold-Speichen, Innenschatten. Dreht per CSS-Transform wie bisher (5 Umdrehungen + Ziel, 4 s, gleiche Easing).
- **Kugel**: eigenes Element über dem Canvas, läuft per `requestAnimationFrame` gegen die Drehrichtung, verlangsamt über 3,2 s, hüpft 2–3× (vertikale Sinus-Sprünge), landet bei 4,0 s im Zielfach und dreht ab dann mit dem Kessel mit. `ballTick` im Rhythmus der Fächer.
- **Setztisch** unter dem Kessel: 0 links, Grid 3×12 (1–36, Farben wie Kessel), darunter Rot / Schwarz / Gerade / Ungerade. Klick auf ein Feld = Wette; Chip fliegt vom Wallet aufs Feld; nur eine Wette pro Spin (wie bisher). Zahlwette = Klick auf eine Zahl. Kein `prompt()`.
- Ergebnis: Zielfach glüht, Zahl erscheint groß in Farbe, Gewinn: Chips verdoppeln sich und rutschen zum Wallet; Verlust: Chip wird vom Croupier-Rechen (SVG) weggezogen.

### 7.2 Slots (amber)
- Drei Walzen: jede ein vertikaler Streifen mit 3× der Symbolfolge, per `translateY` gescrollt, `filter: blur(2px)` während des Laufs, Stop mit `cubic-bezier` Rückfeder. Stop-Zeiten 800 / 1400 / 2000 ms.
- Hebel rechts (SVG), Klick oder Leertaste zieht ihn (rotate −40°), dann Start.
- Kreidetafel „Auszahlung": 7️⃣7️⃣7️⃣ 50×, 💎💎💎 25×, 🔔🔔🔔 15×, sonst Drilling 5×, Paar 1,5×.
- Gewinnlinie blitzt gold; ≥ 25× zusätzlich Münzregen (~40 Partikel, 1,5 s) + „JACKPOT"-Neon.

### 7.3 Pferderennen (grün)
- Bahn: 4 Spuren, Startboxen links, Zielstreifen rechts, Zaun oben/unten. Pferde bobben (`@keyframes gallop`, 200 ms), Staub-Partikel hinter jedem laufenden Pferd.
- Setzkarten links: Name + Farbe, Klick kippt Karte nach vorn (Auswahl).
- Kommentarzeile über der Bahn, alle 600 ms aus den Positionen generiert („Phantom führt", „Lucky holt auf", „Kopf an Kopf!").
- Ziel: weißer Fotofinish-Blitz 120 ms, Siegerpferd galoppiert aus dem Bild, andere stoppen. Sieger-Toast.

### 7.4 Russisches Roulette (blau)
- Mitte: SVG-Trommel mit 6 Kammern, dreht bei jedem Abzug um 60° (Rasten-Sound). Bereits leere Kammern werden grau markiert; Anzeige „Kammern übrig: 6 → …".
- Links Spieler-Karte 🤠, rechts Igor 🐻. Vor dem ersten Duell Szene `igor.first`.
- Abzug: kurzer Zoom auf die Trommel, `dryfire` oder `gunshot`. Schuss: weißer Flash 80 ms, `shake`, Portrait → 💀. Herzschlag-Loop ab Duellstart, Tempo +15 % je leerer Kammer.
- Igor-Zug nach 1.100 ms wie bisher.

### 7.5 Blackjack (filz)
- Halbrunder Filztisch, Kartenschuh oben rechts, Dealer-Bereich oben, Spieler unten, Einsatz-Kreis mit Chip.
- Karten: 64×92 px, Ecken mit Wert+Farbe, großes Symbol mittig, Rücken-Design (Rautenmuster). Austeilen: Karte fliegt vom Schuh mit Rotation an ihren Platz, 80 ms Versatz, `cardSlide`.
- Dealer-Hole-Card: 3D-Flip (`rotateY`) beim Aufdecken.
- Hand-Werte als Kreidezahl neben der Hand. Bust: Karten glühen rot, rutschen weg. Push: beide Werte gelb.

### 7.6 Post austragen (tageslicht)
- Einziger heller Screen: Straße mit 4 Häusern (Farben wie bisher: #12 amber, #45 blau, #88 grün, #99 rot), Briefkasten vor jedem Haus.
- Brief-Karte oben: „An Haus #45" in Hausfarbe + Belohnung.
- Timer = Lunte über der Szene, brennt von rechts nach links ab, Funken-Glow am Ende.
- Streak-Zähler groß; bei Stufenwechsel (2/6/11) Stempel „TEMPO!" mit Slam-In.
- Richtig: Brief fliegt in den Kasten, Fahne hoch, `coin`. Falsch/zu langsam: Hund 🐕 springt aus dem Haus, Zettel „25 € Strafe", Schicht beendet.
- Verlassen des Screens räumt den Timer auf.

## 8. Räume & Extras

### 8.1 Zuhause (Leben)
Ein Panel „Lebenslauf": Villa-Slot (leer / gekauft mit Bild), Beziehungsstatus, Liebeskummer-Zustand, Dealer, Trophäenwand (Achievements, gesperrt = grau). Aktionen nur sichtbar, wenn möglich; gesperrte Aktionen als Kreide-Notiz mit Grund („Erst Schulden tilgen", „Ohne Haus keine Matches").

### 8.2 Anlagen & Kredite
- Anlagen: Kreidetafel mit drei Spalten, je Einsatzfeld + Button; laufende Anlagen als Tickets mit Spin-Countdown.
- Kredite: zwei Schalter – Bank (Glas, blau, Krause) und Vito (Holz, rot). Schulden als Schuldschein; Vitos Frist als rot pulsierende Zahl. Bank-Buttons deaktiviert, wenn Limit erreicht.

### 8.3 Game Over (neue Regel)
- Bankkredite sind auf **3.000 € Gesamtschulden** gedeckelt; ein Kredit, der das Limit überschreiten würde, wird abgelehnt (Szene `bank.limit` beim ersten Mal, danach Toast).
- Game Over, wenn nach `afterSpin()` gilt: `balance < 0` **und** `bankDebt >= 3000` **und** `mafiaDebt > 0`. (Solange noch eine Kreditquelle offen ist, geht es weiter.)
- Ablauf: Szene `gameover` (Vito, Hafen bei Sonnenaufgang), Panel 3 mit Statistik (Spins, höchster Kontostand, größter Gewinn, verkaufte Nieren, Game Overs) und Button „Nochmal" → `State.reset()` (50 €, alles zurück), `meta` bleibt, `meta.gameOvers++`. Die Statistik im Panel zeigt die Werte des beendeten Durchlaufs. Achievement „Auferstanden" beim ersten Weiterspielen.

### 8.4 Sound
Modul `SFX` mit `play(name)`, `loop(name)/stop(name)`, `mute(bool)`. Alle Sounds aus `OscillatorNode` + `BufferSource`-Rauschen + `GainNode`-Hüllkurven. Namen: `click, chip, coin, cash, lose, reelSpin, reelStop, ballTick, whinny, gallop, heartbeat, dryfire, gunshot, cardSlide, neonBuzz, typewriter, unlock, stamp, dog`. AudioContext wird beim ersten User-Klick erzeugt/resumed. Mute-Toggle in der Wallet-Bar, in `meta` gespeichert.

### 8.5 Achievements
| id | Titel | Bedingung |
|---|---|---|
| `firstWin` | Erster Gewinn | erstes `win` |
| `highRoller` | Hoch gepokert | Einsatz ≥ 500 € |
| `jackpot` | Jackpot | 7️⃣7️⃣7️⃣ |
| `plein` | Plein | Roulette-Zahl getroffen |
| `igor` | Igor besiegt | Igor erschossen |
| `regular` | Stammgast | 3 Bier gleichzeitig |
| `donor` | Organspender | Niere verkauft |
| `owner` | Hausbesitzer | Villa gekauft |
| `divorced` | Frisch geschieden | `divorce` |
| `vitosFriend` | Vitos Freund | Mafia-Kredit fristgerecht getilgt |
| `postman` | Fleißiger Bote | Post-Streak 11 |
| `phoenix` | Auferstanden | nach Game Over weitergespielt |

Unlock: Toast mit `unlock`-Sound und Gold-Glow; Trophäenwand im Zuhause-Screen.

### 8.6 Mobile (< 760 px)
Seitenleiste wird Bottom-Bar mit drei Tabs (Bar / Hinterzimmer / Zuhause), die ein Sheet hochschieben. Hub 1 Spalte. Roulette-Setztisch skaliert per `transform: scale`. Slots-Walzen 60 px, Blackjack-Karten 60 %. Cutscene bleibt Vollbild, Portrait über dem Text.

## 9. Mechanik-Referenz (muss 1:1 reproduziert werden)

**Kosten pro Spin** (`checkCosts`): Einsatz muss `> 0` sein. `interest = bankDebt > 0 ? round(bankDebt·0,3) : 0`, `meds = kidneySold ? 20 : 0`. Wenn `balance < bet + interest + meds` → abgelehnt (Toast mit Aufschlüsselung). Sonst werden `bet + interest + meds` sofort abgezogen (`Game.beginSpin`): Zinsen und Meds endgültig, der Einsatz treuhänderisch. Bei der Abrechnung (`Game.settle(netto, {bet})`) zahlt das Spiel **brutto** aus: `balance += netto + bet` (Gewinn `bet + Gewinn`, Verlust `0`, Push `bet`). Netto ist damit exakt wie im Original (`Rules.*Delta`/`*Payout`); Anzeige, Statistik `biggestWin` und Achievements werten den Netto-Betrag. Eine Runde, die nicht abgerechnet wird (Screen verlassen, siehe 7), verfällt samt Einsatz; eine Abrechnung, deren Spielstand inzwischen ersetzt wurde (Game Over, Neues Spiel), wird verworfen. `maxBet = max(1, balance − interest − meds)`.

**Glück**: Bier: 1 → +10 %, 2 → +15 %, 3 → +20 % (nur solange `beerTimer > 0`); Brownie +40 % solange `brownieTimer > 0`. Summe.

**Bar**: Bier 50 €, max. 3, jedes Bier setzt `beerTimer = 2`; wenn Timer auf 0 fällt → `beers = 0`. Brownie: 1.000 €, danach 10.000 €; `brownieTimer = 1`; nicht kaufbar solange aktiv.

**Niere**: einmalig +2.000 €, danach 20 € Meds pro Spin.

**Bank**: +200 / +500 / +1.000 €, 30 % Zinsen auf die Gesamtschuld pro Spin (abgezogen vor dem Einsatz). Tilgen nur komplett. Neu: Limit 3.000 € (8.3).

**Mafia**: +300 / +600 / +1.000 €, nur ein Kredit gleichzeitig, `mafiaSpins = 5`. Pro Spin −1; bei `≤ 0`: `bill = mafiaDebt·3` wird abgezogen, `mafiaDebt = 0`. Tilgen nur komplett.

**Passiv**: alle 6 s: Villa +3 €, Dealer +5 €.

**Leben**: Villa 2.500 €, nur ohne Bank-/Mafia-Schulden, nicht bei Liebeskummer, nicht verheiratet. Tinder 50 €, nur mit Villa, nicht verheiratet, nicht bei Liebeskummer → `isMarried`, `marriageSpins = 0`. Nach 2 Spins: `isMarried = false`, `hasHouse = false`, `isHeartbroken = true`, `balance = floor(balance/2)`. Liebeskummer: jeder Spin mit `beers < 2` → −250 €. Therapie 5.000 € hebt Liebeskummer auf. Dealer 5.000 €, einmalig.

**Anlagen** (Mindesteinsatz 10, Guthaben nötig): Festgeld 8 %, 5 Spins, Risiko 10 %; Aktien 100 %, 2 Spins, Risiko 85 %; Trickbetrug 30 %, 10 Spins, Risiko 55 %. Fällig wenn `spins ≤ 0`: `rng()·100 ≥ risk` → +`round(amount·(1+rate))`, sonst Totalverlust.

**afterSpin-Reihenfolge**: beerTimer → brownieTimer → Ehe → Liebeskummer → Mafia → Anlagen (rückwärts iteriert) → [neu: Game-Over-Check] → sync/save.

**Roulette**: Kesselreihenfolge `0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26`; rot: `1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36`. `rolled = floor(rng()·37)`. Glück: wenn `rng()·100 < luck` und `rolled ≠ 0`: Rot → 7, Schwarz → 8, Zahl → gewählte Zahl (Gerade/Ungerade unbeeinflusst). Gewinn: Rot/Schwarz/Gerade/Ungerade `+bet` (0 verliert immer), Zahl `+bet·35`; Verlust `−bet`. Kesseldrehung 5 volle Umdrehungen + Zieldifferenz, Ergebnis nach 4.100 ms.

**Slots**: Symbole `🍒 🍋 🍇 🔔 💎 7️⃣`, drei unabhängige Zufallszüge. Glück: wenn `rng()·100 < luck`: mit 30 % alle drei = 7️⃣ oder 💎 (50/50), sonst `res2 = res1`. Multiplikator: Drilling 7️⃣ 50, 💎 25, 🔔 15, sonst 5; jedes Paar 1,5; sonst 0. Gewinn: `balance += round(bet·m) − bet`; Verlust `−bet`.

**Pferde**: Blitz 🔴, Donner 🔵, Phantom 🟣, Lucky 🟡. Alle 30 ms: `step = rng()·3 + 1`, gewähltes Pferd `+ luck·0,02`, `pos += step·1,5`; Ziel `Bahnbreite − 65 px`. Erstes Pferd über Ziel gewinnt. Gewinn `+bet·3` (Anzeige `bet·4`), Verlust `−bet`.

**Russisches Roulette**: 6 Kammern, 1 Kugel zufällig. Spieler zieht zuerst (Index 0), Igor danach (Index 1), abwechselnd. Kugel beim Spieler: `−(bet + 100)`. Kugel bei Igor: `+bet` (Anzeige `bet·2`). Igor-Zug nach 1.100 ms.

**Blackjack**: 52 Karten, Fisher-Yates-Shuffle (statt `sort(random)` – gleiches Ergebnis-Spektrum, sauberer). Ass 11, dann 1 solange > 21. Dealer zieht bei `< 17`. Spieler bust → `−bet`; Dealer bust oder Spieler höher → `+bet`; gleich → Push; sonst `−bet`. Kein Blackjack-Bonus, kein Double/Split.

**Post**: Stufen nach Streak: `< 2`: 5 s / 5 €; `< 6`: 3 s / 10 €; `< 11`: 1,5 s / 25 €; sonst 0,5 s / 50 €. Häuser 12/45/88/99, zufällig gemischt. Richtig: `+reward`, `streak++`. Falsch oder Zeit abgelaufen: `−25 €`, Schicht beendet. Post löst **kein** `afterSpin()` aus.

## 10. Verifikation

1. **`?selftest`**: Beim Laden mit diesem Query-Parameter laufen Asserts gegen `Rules` (mit injiziertem `rng`), Ergebnis in der Konsole und als Toast. Mindestens abgedeckt: Glück-Stufen; Spin-Kosten inkl. Ablehnung; maxBet; alle Roulette-Auszahlungen + 0-Fälle + Glück-Override je Typ; alle Slot-Multiplikatoren + Glück-Override beide Zweige; Pferde-Step mit/ohne Glück; Blackjack Ass-Logik (A+A+9 = 21, A+K = 21, A+9+5 = 15), Dealer-Regel, alle vier Ergebnisse; Post-Stufen an den Grenzen 1/2/5/6/10/11; Anlagen beide Zweige; Mafia-Rechnung; Bank-Zinsen (Rundung); Game-Over-Bedingung.
2. **Manuelle Checkliste** (vor „fertig"): jede Szene aus 6.5 einmal auslösen; jedes Spiel gewinnen und verlieren; Speichern → Reload → Zustand identisch; Neues Spiel; Game Over erreichen und „Nochmal"; Mute; Mobile-Breite 400 px; Reduced-Motion; Postbote-Timer stoppt beim Verlassen; Esc/Schild zurück; Cutscene überspringen führt Effekte aus.
3. Screenshots von Hub, jedem Spiel und zwei Szenen als Nachweis.

## 11. Umsetzungsreihenfolge (Grobskizze für den Plan)

1. Gerüst: Tokens, Textur, Shell, Router, Wallet, Toasts, `Rules` + `State` + `Bus` + Selbsttest.
2. Cutscene-Engine mit Cast/Orten, `intro` als erste Szene.
3. Bar, Kredite, Anlagen, Zuhause (alle Szenen dieser Räume).
4. Spiele in der Reihenfolge Slots → Blackjack → Roulette → Pferde → Russisches Roulette → Post.
5. SFX, Achievements, Game Over, Save-Feinschliff, Mobile, Reduced-Motion.
6. Manuelle Checkliste + Screenshots.
