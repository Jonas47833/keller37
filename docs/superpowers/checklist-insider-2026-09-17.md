# Checkliste — Insider & Skills (2026-09-17)

Nachweis je Spec-Zeile aus `docs/superpowers/specs/2026-09-17-insider-skills-design.md`
(§2.3–2.7 und §3.1–3.4). Quellen:

- **Node** = `node tests/run-selftest.mjs` (127 bestanden, 0 fehlgeschlagen, Stand dieses Laufs)
- **Playtest** = `tests/playtest-story.py` (`scenario_perks` u. a.; Desktop und Mobile je
  101 Checks, 0 fehlgeschlagen, 0 Fehler, isolierte Umgebung `K37_PORT=9345
  K37_PROFILE=/tmp/k37story-profile-insider K37_SHOTS=/tmp/k37story-insider`)
- **Screenshot** = Datei in `docs/superpowers/screenshots/`

## §2.3 XP und Level

| Anforderung | Nachweis |
|---|---|
| XP-Quellen: Spin +1, Sieg +2, Job +5, Story-Tag +5, Trophäe +10 (`Rules.XP_GAIN`) | Node: „Kataloge: Skills mit Licht/Schatten, mods-Schlüssel bekannt" (prüft `Rules.XP_GAIN` exakt); Code: `Bus.on('spin:after'|'win'|'job:done'|'achievement:unlock'|'story:day', …)` (keller37.html:4175–4179) |
| `XP_LEVELS = [0,25,60,110,180,270]`, `xpLevel(xp)` Schwellen/Punkte, „Lv 6 · max" über Level 6 | Node: „xpLevel: Schwellen und Punkte" |
| Freie Punkte = `points − skills.length` | Node: „canPickSkill / skillPointsFree" |
| Level-Erhöhung vergibt XP im Spiel selbst (nicht nur Rules) | Playtest: „perks: Level 2 -> Badge pulsiert, 8 Skills waehlbar" (`Perks.addXp(25)` über echten Aufruf, kein Rules-Stub) |

## §2.4 Skill-Katalog `Rules.SKILLS`

| Anforderung | Nachweis |
|---|---|
| 8 Skills, je genau ein Licht- und ein Schatten-Text, `mods`-Schlüssel bekannt | Node: „Kataloge: Skills mit Licht/Schatten, mods-Schlüssel bekannt" |
| Konflikt `zockerhaende` ↔ `brieftraeger` (`reason: 'conflict'`) | Node: „canPickSkill / skillPointsFree"; Playtest: „perks: Skill aktiv, Konflikt-Grund sichtbar" (Karte zeigt „Passt nicht zu einem aktiven Skill") |
| Additive Stapelung (`bankRateAdd`, `postTimeAdd`, …), multiplikative Stapelung (`slotPairMult`, `mugChanceMult`, …) | Node: „mods: Skills und Insider stapeln" (Zinsen `0,02-0,02-0,03`, `mugChanceMult 1,5×0,5` etc.) |
| Umskillen setzt `skills=[]`, `skillRespecs++`, kostet 2.000 € | Playtest: „perks: Umskillen kostet 2000 und leert die Skills" |

## §2.5 Insider-Katalog `Rules.INSIDER`

| Anforderung | Nachweis |
|---|---|
| 7 Insider-Upgrades, `capped`-Flag, `mods`-Schlüssel bekannt | Node: „Kataloge: Skills mit Licht/Schatten, mods-Schlüssel bekannt" |
| `effectiveInsider(value, bet)`: voll bis `INSIDER_CAP=250`, darüber anteilig/aus (bool) | Node: „effectiveInsider: Deckel 250" |
| „Heißes Deck": Anteil 10er/Asse > 40 % (`Rules.deckHot`) | Node: „deckHot / pickExcluded / pickLoser" |
| Mehrere `mafiaSpins`-Quellen → Maximum; `bankLimitAdd` addiert sich (Untergrenze 500 €) | Node: „mods: Skills und Insider stapeln" (`mafiaSpins` Maximum von 7 und 8 → 8); „Bank/Vito mit mods" (`bankLimitFor` Untergrenze 500) |
| Croupier-Auge: 12 ausgegraute Zahlen, Kugel fällt nie hinein | Node: „Roulette mit mods: 36:1, Ausschlussliste" (1.000 Würfe nie ausgeschlossen); Playtest: „insider: Croupier-Auge graut 12 Zahlen aus, Kugel faellt nie dorthin" (200 Stub-Würfe); Screenshot: `roulette-croupierauge.png` |
| Stallbursche: markiertes Pferd ≠ gewähltes, 0,85× Schritt | Node: „deckHot / pickExcluded / pickLoser" (`pickLoser` nie das gewählte, 50 Läufe), „Slots/Pferde mit mods" (`horseStep` Handicap); Playtest: „insider: Stallbursche markiert ein lahmes Pferd (nicht das gewaehlte)" |
| Mechaniker: nach Niete alle 5 Runden Festhalten möglich | Playtest: „insider: Mechaniker zeigt nach Niete Festhalten-Buttons" (`holds=3`) |
| Bankinsider / Vitos Neffe / Postmeister (nicht `capped`) | Node: „Bank/Vito mit mods" (Zinsen/Limit), „Anlagen/Post/Überfall mit mods" (`postmanTier` mit `postLetters`/`postPayAdd`); Playtest zieht diese Upgrades im Insider-Angebot (`insider-offer.png` zeigt „Bankinsider", „Kartenzähler", „Postmeister" als Auswahl) |
| Kartenzähler: „Deck heiß" zahlt 1,2:1 | Node: „Blackjack mit mods: Natural 3:2, Push +10 %, heißes Deck 1,2:1" (inkl. Deckel-Abschwächung über 250 €/500 €/1000 €) |

## §2.6 `Rules.mods(s, meta)`

| Anforderung | Nachweis |
|---|---|
| Pure Funktion, liefert immer alle Neutralwerte, unbekannte IDs ignoriert | Node: „mods: neutral ohne Skills/Insider" (`Rules.mods(base(), {insider:[]})` == `NEUTRAL_MODS`), „mods: Skills und Insider stapeln" (`skills:['unbekannt']` → `NEUTRAL_MODS`) |

## §2.7 Regel-Hooks

| Regel | Nachweis |
|---|---|
| `Rules.luck` (Bier-/Brownie-Multiplikator) | Node: „luck mit mods: Bier/Brownie-Multiplikatoren, 4. Bier" |
| `canBeer`, `MAX_BEERS` (Eisenmagen: 4 Bier) | Node: „luck mit mods …" (`canBeer` mit `maxBeers:4`) |
| Brownie-Timer (`brownieSpins`) | Node: „Kataloge …" prüft `k.brownieSpins` über `M(eisenmagen.mods)`-Auszug (Zeile 6252) |
| `bankInterest` / `gear.bankRate` (+ `bankRateAdd`, Untergrenze 0,01) | Node: „Bank/Vito mit mods" (`bankRateFor` Untergrenze 1 %) |
| `bankLoanReason` / `gear.bankLimit` (+ `bankLimitAdd`, Untergrenze 500) | Node: „Bank/Vito mit mods"; Playtest: „bank: Konditionen 8 %" / „bank: Limit-Knopf leiht bis zum Kreditlimit (3000)" (regulärer Bank-Flow ohne Insider, bestätigt Basiswerte weiterhin korrekt nach Isolations-Fix) |
| `MAFIA_SPINS`, `mafiaBill` (`mafiaSpins`, `mafiaMult`) | Node: „Bank/Vito mit mods" |
| `roulettePayout` (Zahl zahlt `rouletteNumberPayout`) | Node: „Roulette mit mods: 36:1, Ausschlussliste" |
| `rouletteRoll(rng, excluded)` (würfelt weiter bis erlaubt, Fallback) | Node: „Roulette mit mods …" (1.000 Würfe + „zweiter Wurf nach Ausschluss"); Playtest s. o. |
| `slotMultiplier` (Paar = `slotPairMult`, 0 = nichts; Drilling unberührt) | Node: „Slots/Pferde mit mods" |
| `horseDelta` (Sieg = `bet × horsePayout`) | Node: „Slots/Pferde mit mods" |
| `horseStep` (`handicap` 0,85 fürs markierte Pferd) | Node: „Slots/Pferde mit mods" |
| `bjDelta` (`natural`, `push`, `hot`; Natural schlägt heiß) | Node: „Blackjack mit mods …" |
| `investmentResolve` (Zinsanteil × `investRateMult`) | Node: „Anlagen/Post/Überfall mit mods" |
| `Rules.mugChance` (× `mugChanceMult`) | Node: „Anlagen/Post/Überfall mit mods" |
| `Rules.fightChance` (+ `fightAdd`, Deckel 0,9 bleibt) | Node: „Anlagen/Post/Überfall mit mods" |
| `Rules.mugWallet` (× `walletMult`) | Node: „Anlagen/Post/Überfall mit mods" |
| `postmanTier` (+ `postTimeAdd`, Untergrenze 0,5 s, Schuh-Deckel 1,5 s bleibt; + `postPayAdd`) | Node: „Anlagen/Post/Überfall mit mods" |
| Postbote Schichtende nach `postLetters` Briefen | Node: „Kataloge …" prüft `k.postLetters` (Eisenmagen-Auszug); **Lücke**: kein Playtest-Check zählt tatsächlich 20 statt 15 zugestellte Briefe in einer Postboten-Schicht mit Postmeister |
| Deckel: `stallbursche`/`croupierauge`/`kartenzaehler`/`mechaniker` nur bis `bet ≤ INSIDER_CAP`, Hinweis „Insider-Wissen wirkt bis 250 €" | Node: „effectiveInsider: Deckel 250", „Blackjack mit mods …" (Deckel-Abschwächung); Screenshot `roulette-croupierauge.png` zeigt den Hinweistext „Croupier-Auge: 12 Zahlen fallen nicht (wirkt bis 250 € Gesamteinsatz)" unter dem Tisch |

## §3.1 Kopfzeile

| Anforderung | Nachweis |
|---|---|
| Badge „Lv N" mit Mini-Fortschrittsbalken | Screenshot `skills.png` (Kopfzeile zeigt „Lv 2" mit Balken); Playtest bestätigt `#lvBadge` |
| Pulsiert bei freiem Skill-Punkt | Playtest: „perks: Level 2 -> Badge pulsiert, 8 Skills waehlbar" (`pulsing=True`) |
| Klick öffnet Skill-Screen | **Lücke**: kein Playtest-Check klickt `#lvBadge` und prüft den Screen-Wechsel (Scenario navigiert stattdessen direkt per `?screen=skills`); Code vorhanden (`onclick` auf Badge), aber ungetestet |
| Level-Up-Toast „Level 4 – ein Skill-Punkt wartet." | Screenshot `skills.png` zeigt den Toast „LEVEL 2 / Ein Skill-Punkt wartet – klick auf das Level." (Text leicht abweichend vom Beispieltext der Spec, gleiche Bedeutung); Code: `Perks.addXp` (keller37.html:4053–4062) |

## §3.2 Screen `skills` („Kopf")

| Anforderung | Nachweis |
|---|---|
| Seitenleiste „Kopf" mit Button „🧠 Skills" (Preis-Spalte „N Punkt frei" / „Lv N") | Screenshot `skills.png` (Seitenleiste rechts unten „Skills · Lv 1") |
| XP-Balken „Lv N · x / y XP", drei Slots (belegt/frei/gesperrt) | Screenshot `skills.png` (Balken „Lv 2 · 25 / 60 XP", Slots „frei" / „ab Lv 4" / „ab Lv 6") |
| 8 Skill-Karten: Icon, Name, Licht (grün), Schatten (rot), „Wählen"/„Aktiv"/Grund | Screenshot `skills.png`; Playtest: „perks: ohne Punkt kein Waehlen-Button", „perks: Level 2 -> Badge pulsiert, 8 Skills waehlbar", „perks: Skill aktiv, Konflikt-Grund sichtbar" |
| „Umskillen · 2.000 €" | Playtest: „perks: Umskillen kostet 2000 und leert die Skills"; Screenshot `skills.png` zeigt Button „UMSKILLEN · 2.000 €" |
| Meta-Bereich „Insider" (gewonnene Upgrades oder Leertext) | Screenshot `skills.png` zeigt Kasten „🕵️ INSIDER / Noch keins – schließe ein Story-Teil ab." (Leerfall); **Lücke**: kein Playtest-Check zeigt den befüllten Zustand (Karte mit Icon/Name/Text nach einer Wahl) im Skill-Screen selbst |

## §3.3 Insider-Wahl

| Anforderung | Nachweis |
|---|---|
| `Story.finish(end)`: bei `!meta.insiderClaimed[story.id]` Szene `insider.offer` (Hintergrund „hinterzimmer", Figur „Der Insider" 🕵️), ein Panel Vorstellung + ein Panel mit 3 Choices | Playtest: „insider: Story-Ende bietet 3 Upgrades" (`choices=3`); Screenshot `insider-offer.png` (Hintergrund, Figur, 3 Buttons „Bankinsider"/„Kartenzähler"/„Postmeister") |
| Wahl → `meta.insider.push(id)`, `meta.insiderClaimed[story.id]=true`, `State.save()`, Toast | Playtest: „insider: Wahl in Meta gespeichert, Story-Teil abgehakt" (`insider` gefüllt, `claimed={"schuld":true}`) |
| Keine ungezogenen Upgrades mehr → Szene entfällt, Toast „Der Insider hat nichts Neues." | Node: „insiderDraw: 3 ungezogene, weniger wenn Pool kleiner" (`insiderDraw({insider: all}, …) === []`); **Lücke**: kein Playtest-Durchlauf mit vollständig leergezogenem Pool prüft den tatsächlichen Toast-Text im Browser |
| Zweites Ende derselben Story bietet keine Wahl mehr | Code: `offerInsider` prüft `meta.insiderClaimed[storyId]` vor dem Ziehen (keller37.html:4144); **Lücke**: kein Playtest-Check durchläuft zwei Enden derselben Story und bestätigt, dass die zweite Szene ausbleibt |
| Titel-Trophäen-Panel: Abschnitt „Insider" mit gewonnenen Upgrades | Code: `titleTrophiesBtn`-Handler fügt Trenner „Insider" ein (keller37.html:4340); **Lücke**: kein Playtest-Check öffnet das Titel-Trophäen-Panel nach einer Insider-Wahl und prüft den Abschnitt |

## §3.4 Spiele

| Anforderung | Nachweis |
|---|---|
| Roulette: ausgegraute Zellen `.rcell.excluded`, keine Chips möglich, Hinweis unter dem Tisch | Playtest: „insider: Croupier-Auge graut 12 Zahlen aus, Kugel faellt nie dorthin" (`excluded=12`); Screenshot `roulette-croupierauge.png` zeigt gedimmte Zellen und Hinweistext „Croupier-Auge: 12 Zahlen fallen nicht (wirkt bis 250 € Gesamteinsatz)"; **Lücke**: kein Check klickt explizit eine ausgegraute Zelle, um zu bestätigen, dass kein Chip gesetzt werden kann |
| Pferde: markierter Runner „🚫 lahmt", Auswahl bleibt möglich, Status warnt | Playtest: „insider: Stallbursche markiert ein lahmes Pferd (nicht das gewaehlte)"; Code: `.lame-tag` „🚫 lahmt" (keller37.html:3361), `#horseInsider`-Hinweis (keller37.html:3362); **Hinweis**: die Implementierung zieht den Verlierer bei jeder Pferdewahl neu und schließt dabei stets das aktuell gewählte Pferd aus (`Rules.pickLoser(State.s.selectedHorse, …)`), sodass der in der Spec beschriebene Fall „gewähltes Pferd ist zugleich das markierte" über die normale Auswahl nicht erreichbar ist — kein Playtest-Check prüft diesen Randfall gezielt |
| Blackjack: „🔥 Deck heiß" / „❄️ Deck kalt" (nur mit Kartenzähler), Status nennt 3:2 bzw. 1,2:1 | Node: „Blackjack mit mods: Natural 3:2, Push +10 %, heißes Deck 1,2:1" (Regel-Ebene vollständig); **Lücke**: kein Playtest-Check öffnet Blackjack mit Kartenzähler-Insider und prüft die UI-Anzeige „🔥 Deck heiß" bzw. den Auszahlungstext |
| Slots: „Festhalten" nach Niete (nur `mechRespins ≥ 5`), hält eine Walze, dreht die anderen zwei ohne neuen Einsatz, `mechRespins=0` | Playtest: „insider: Mechaniker zeigt nach Niete Festhalten-Buttons" (`holds=3`); **Lücke**: kein Check klickt tatsächlich „Festhalten" und prüft, dass nur zwei Walzen neu drehen, kein Einsatz abgebucht wird und `mechRespins` danach 0 ist |
| Bar: Bier-Knopf zeigt „(3/4)" mit Eisenmagen | Node: „Kataloge …" (`k.maxBeers === 4` für Eisenmagen-Mods); Code: `btn('🍺 Bier${s.beers>0?\` (${s.beers}/${mods.maxBeers})\`:''}', …)` (keller37.html:1822); **Lücke**: kein Playtest-Check aktiviert Eisenmagen und prüft den Button-Text im Bar-Screen |

## Zusammenfassung

- Node-Selbsttest: **127 bestanden, 0 fehlgeschlagen** (`node tests/run-selftest.mjs`).
- Browser-Playtest (`tests/playtest-story.py`), isolierte Umgebung (Port 9345, eigenes Chrome-Profil
  `/tmp/k37story-profile-insider`, eigenes Screenshot-Verzeichnis `/tmp/k37story-insider`):
  - Mobile (`--mobile`): **101 Checks, 0 fehlgeschlagen, 0 Fehler**.
  - Desktop: **101 Checks, 0 fehlgeschlagen, 0 Fehler**.
- Regel-Ebene (§2.3–2.7) ist durchgehend durch Node-Tests abgedeckt; die Kern-UI-Flows aus §3.1–3.3
  (Badge, Skill-Screen, Insider-Wahl, Croupier-Auge, Stallbursche, Mechaniker) sind durch
  `scenario_perks` im Browser abgedeckt und durch drei neue Screenshots belegt.
- Ehrliche Lücken (UI-Verhalten, das nur über Code-Lesen, nicht über einen automatisierten Check
  bestätigt ist): Klick auf das Lv-Badge öffnet den Skill-Screen; befüllter Insider-Bereich im
  Skill-Screen; „nichts Neues"-Toast bei leergezogenem Insider-Pool; Sperre der zweiten Insider-Wahl
  am zweiten Ende derselben Story; „Insider"-Abschnitt im Titel-Trophäen-Panel; Klick auf eine
  ausgegraute Roulette-Zelle; Blackjack-Anzeige „Deck heiß/kalt" und deren Auszahlungstext; tatsächlicher
  Klick auf „Festhalten" bei den Slots (Walzen-Neudreh, `mechRespins`-Reset); Bar-Button „(3/4)" mit
  Eisenmagen; Postboten-Schicht mit 20 statt 15 Briefen (Postmeister).
