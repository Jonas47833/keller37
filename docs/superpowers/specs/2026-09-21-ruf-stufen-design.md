# KELLER 37 – Ruf-Stufen: Angebote in Story 1 und 3

Datum: 2026-09-21 · Status: abgestimmt · Basis: `keller37.html` @ `41466fd` (main, nach Sic Bo)

## 1. Ziel

Ruf (`vars.ruf`, 0–10) wird heute in Story 1 und 3 an vielen Stellen erhöht und gesenkt, aber nur an zwei Stellen abgefragt – beide bei `ruf ≥ 2` (Flucht-Angebot in Story 1, Kesslers Deal in Story 3). Ab Ruf 2 ist jeder weitere Punkt wirkungslos; die Skala bis 10 im HUD verspricht etwas, das das Spiel nicht einlöst. Story 3 zeigt Ruf im HUD gar nicht.

Diese Spec macht Ruf zu einem **Schlüssel für Zugang**: vier benannte Stufen, ein Angebot je Stufe und Story, neue Ruf-Quellen in Story 3, Ruf im HUD beider Stories mit Stufentitel.

Nicht Teil dieser Spec: neue Enden, Änderungen an Vertrauens-Schwellen oder Job-Freischaltungen, Ruf in Story 2 oder im freien Spiel, Ruf als Zahlenbonus außerhalb der Angebote (kein Überfall-Multiplikator, keine Preise, keine Zinsen), Ruf als ausgebbare Währung.

## 2. Stufen-Modell (`StoryRules`, Block `story-rules`)

```js
RUF_STUFEN: [{ id: 'niemand', ab: 0, titel: 'Niemand' }, { id: 'bekannt', ab: 2, titel: 'Bekannt' },
             { id: 'respektiert', ab: 5, titel: 'Respektiert' }, { id: 'legende', ab: 8, titel: 'Legende' }],
rufStufe(ruf) → letzte Stufe mit stufe.ab <= (ruf || 0)          // 0–10 → { id, ab, titel }
```

- Reiner Helfer, Node-testbar, keine DOM-Abhängigkeit. Werte außerhalb 0–10 werden nicht geklemmt (die Stories haben `varMax.ruf = 10`; negative Werte fallen auf „Niemand").
- Die Stories nutzen weiterhin `{ var: 'ruf', gte: N }` in ihren Events – **kein neuer Bedingungstyp**, die Engine bleibt unangetastet. Die Schwellen 2 / 5 / 8 in den Events entsprechen `RUF_STUFEN[i].ab`; ein Selftest prüft, dass jedes Ruf-Event beider Stories genau eine dieser Schwellen verwendet, damit Events und HUD nie auseinanderlaufen.

### 2.1 HUD

- Story 1: HUD-Eintrag `{ var: 'ruf', label: '🔥 Ruf', max: 10 }` wird zu `{ var: 'ruf', label: (s) => '🔥 ' + StoryRules.rufStufe(s.story.vars.ruf).titel, max: 10 }` → `🔥 Bekannt 4/10`. `label` als Funktion wird von `Story.hudNotes` bereits unterstützt.
- Story 3: derselbe Eintrag wird **neu** an das HUD gehängt (nach Kredit): `[Umsatz, Zorn, Kredit, Ruf]`. `varMax.ruf = 10` kommt in Story 3 dazu (heute nur `zorn: 3`).

### 2.2 Stufen-Toast

Beim Wechsel der Stufe ein Toast – hoch in Gold, runter in Rot. Umsetzung als Story-Daten, nicht als Engine-Sonderfall:

- Neue Var `rufStufe` (Index 0–3, Start 0) in beiden Stories.
- Je Story ein Event `rufStufe` mit `at: 'night'` und `at: 'morning'` (zwei Einträge, `daily: true`), `effects: [{ call: 'rufStufe' }]`. Die Story-Funktion `fns.rufStufe(s)` vergleicht `StoryRules.rufStufe(v.ruf)` mit `v.rufStufe`; bei Abweichung setzt sie `v.rufStufe` und gibt `{ toast: { icon: '🔥', title: <Titel>, text: <Satz>, tone: 'win' | 'loss' } }` zurück, sonst `{}`.
- Story 1 hat heute keine `fns`; der Block kommt hinzu (die Engine unterstützt `call` storyübergreifend – `STORY_STASH.fns` ist das Muster).
- Sätze: Bekannt „Man hat deinen Namen gehört." · Respektiert „Man kennt deinen Namen." · Legende „Man erzählt sich Geschichten." · Abstieg: „Der Bahnhof redet weniger über dich."

Damit feuert der Toast genau beim Wechsel, nicht jede Nacht, und ein Sprung über zwei Stufen (z. B. Dev-Panel) ergibt einen Toast mit der neuen Stufe.

## 3. Story 1 „Die Schuld"

Ruf ist die Straßenseite (Taxi, Duelle, Bahnhof), Vertrauen die Vito-Seite (Türsteher ab 4, Croupier ab 7). Die Angebote öffnen über Ruf Wege, die sonst nur über Vito gehen. Bestehende Ruf-Quellen bleiben unverändert.

| Stufe | Event | Bedingung | Szene |
|---|---|---|---|
| Bekannt (2) | `fluchtAngebot` | wie heute | unverändert |
| Respektiert (5) | `vitoRespekt` | `{ var: 'ruf', gte: 5 }`, `once`, `at: 'night'` | `schuld.vitoRespekt` |
| Legende (8) | `igorHoert` | `all: [{ var: 'ruf', gte: 8 }, { notFlag: 'igorZweifelt' }]`, `once`, `at: 'night'` | `schuld.igorHoert` |

### 3.1 `schuld.vitoRespekt` – „Vitos Respekt"

Kulisse `hinterzimmer`, Vito am Tisch, `cam: 'close'` auf dem Angebot. Vito hat gehört, was die Straße sagt, und bietet 10.000 € Nachlass – dafür trägst du seinen Namen.

- **Annehmen** (`cls: 'red'`): `[{ var: 'schuld', add: -10000 }, { var: 'vertrauen', add: 2 }, { flag: 'vitosMann' }]`. `applyEffect` klemmt `add` auf ≥ 0 und `vertrauen` an `varMax` (10) – `schuld` fällt also nie unter 0, kein Sonderfall nötig. Das Flag `vitosMann` hat keine Wirkung auf Enden; es steht für spätere Texte zur Verfügung (die Ende-Szenen dieser Spec lesen es nicht).
- **Ablehnen** (`cls: 'ghost'`): `[{ var: 'ruf', add: 1 }]` – „Er zahlt selbst, sagen sie am Bahnhof."

### 3.2 `schuld.igorHoert` – „Igor hört zu"

Kulisse `bar`, Igor setzt sich zu dir (`enter`), `mood: 'calm'`. Die Straße respektiert dich mehr als Vito; Igor spricht zum ersten Mal über seinen Chef.

- **Zuhören** (`cls: 'blue'`): `[{ flag: 'igorZweifelt' }]`.
- **Abwinken** (`cls: 'ghost'`): keine Effekte.

Wirkung: `igorZweifelt` ist heute nur über `igorZweifel` (drei Duellsiege) erreichbar; das Ende „Der Sturz" (`hauptbuch` + `safe` + `igorZweifelt`) bekommt damit einen zweiten Weg. Feuert `igorZweifel` zuerst, ist `igorHoert` durch `notFlag` blockiert und umgekehrt (`igorZweifel` bleibt wie heute an `duellSiege ≥ 3`; eine doppelte Szene ist harmlos, weil das Flag idempotent ist – `igorZweifel` bekommt trotzdem `notFlag: 'igorZweifelt'`, damit der Spieler nicht zweimal dieselbe Enthüllung sieht).

## 4. Story 3 „Die Wäsche"

### 4.1 Neue Ruf-Quellen

Heute: Tutorial-Duell (+1, Tag 10) und gewonnene Hinterhalte (+1, nur mit Waffe; nach Kesslers Deal keine mehr). Damit bleibt Ruf bei ~3 stehen. Neu – „der Bahnhof sieht es":

| Quelle | Ruf | Umsetzung |
|---|---|---|
| Wochenabrechnung „sauber" | +1 | `fns.abrechnung`: bei `r.ausgang === 'ok'` zusätzlich `v.ruf = Math.min(10, v.ruf + 1)`; der Abrechnungs-Text bekommt eine Zeile „Ruf +1" |
| Eintreiber-Schicht | +1 | Event `eintreiberRuf`: `when: { jobToday: 'eintreiber' }`, `at: 'job:after'`, `daily: true`, `effects: [{ var: 'ruf', add: 1 }, { toast: { icon: '🥊', title: 'Ruf +1', text: 'Die Liste ist kürzer. Der Bahnhof hat es gesehen.', tone: 'win' } }]` |
| Kredit-Rate gezahlt | +1 | `fns.kreditZahlen` (bestehend, Szene `stash.kredit`): nur für eine **volle Rate** (5.000 €) oder die Tilgung, **einmal am Tag** (Flag `kreditRufHeute`, `tagesstart` setzt zurück) – Teilzahlungen geben keinen Ruf, sonst wäre die Stufe per Kleinstbeträgen erreichbar (Review 2026-09-21) |
| Tür nach Überfall repariert | +1, einmal pro Woche | `Story.repair(id)` → nach erfolgreichem `StoryRules.repair` in Story 3: wenn `!f.rufReparaturWoche` → `v.ruf + 1`, `f.rufReparaturWoche = true`, Toast „Er lässt sich nicht kleinkriegen." `fns.lieferung` löscht das Flag beim Wochenwechsel (`v.woche++`) |

Alle vier klemmen bei `varMax.ruf = 10` (`applyEffect` klemmt an `varMax`; die `fns` nutzen `Math.min`). Erwartung: bei gutem Spiel 8+ bis Tag ~25 auch ohne Duelle; wer nur zockt und nichts repariert, bleibt „Bekannt".

### 4.2 Angebote

| Stufe | Event | Bedingung | Szene |
|---|---|---|---|
| Bekannt (2) | `angebot` (Kessler) | wie heute | unverändert |
| Respektiert (5) | `wache` | `all: [{ var: 'ruf', gte: 5 }, { notFlag: 'bahnhof' }, { notFlag: 'wache' }, { notFlag: 'wacheNein' }]`, `once`, `at: 'night'` | `stash.wache` |
| Legende (8) | `anabiHoert` | `{ var: 'ruf', gte: 8 }`, `once`, `at: 'night'` | `stash.anabiHoert` |

Das Wache-Angebot kommt nicht, wenn Kesslers Deal steht (`bahnhof` stoppt Überfälle ohnehin). Nimmt der Spieler die Wache und später Kesslers Deal, bleibt die Wache stehen und kostet weiter – das ist seine Entscheidung; die Kessler-Szene bekommt einen Satz, wenn `wache` gesetzt ist („Deine zwei vor der Tür kannst du behalten. Oder heimschicken."). Heimschicken geht jederzeit über die Bar-Aktion `wacheWeg` („🚪 Wache heimschicken", nur mit `wache`; Szene `stash.wacheWeg`: *Heimschicken* → `unflag wache`, `flag wacheWeg`; *Bleiben* → nichts). Danach kommt das Angebot nicht wieder (`once`).

### 4.3 `stash.wache` – „Die Wache"

Kulisse `strasse` vor dem Keller, zwei Bahnhof-Jungen (`cast: ['du', 'junge']`). Sie bieten sich an: 200 € pro Nacht, dafür bleibt jede Tür ganz.

- **Annehmen** (`cls: 'blue'`): `[{ flag: 'wache' }]`.
- **Ablehnen** (`cls: 'ghost'`): `[{ flag: 'wacheNein' }]`.

Mechanik:

- `GangRules.WACHE_PREIS = 200`. `GangRules.raidChance(flags)` liefert 0, wenn `flags.wache` (zusätzlich zu `bahnhof`); `ambushChance` bleibt unverändert – die Wache steht vor dem Keller, nicht in der Gasse.
- Event `wacheNacht`: `when: { flag: 'wache' }`, `daily: true`, `at: 'night'`, `effects: [{ call: 'wacheNacht' }]`. `fns.wacheNacht(s)`: wenn `s.balance >= WACHE_PREIS` → `s.balance -= WACHE_PREIS`, `{}`; sonst `delete f.wache; f.wacheWeg = true` und `{ toast: { icon: '🚪', title: 'Die Wache geht', text: 'Kein Geld, keine Jungs. Die Tür ist wieder deine Sache.', tone: 'loss' } }`. Reihenfolge: `wacheNacht` steht in der Event-Liste **vor** `ueberfall`, damit eine gegangene Wache in derselben Nacht keinen Schutz mehr bietet.
- Nach `wacheWeg` kommt das Angebot nicht wieder (`once`).
- Der Story-3-Tagestext (`goal`) hängt „· Wache 200 €/Nacht" an, solange `wache` gesetzt ist.

### 4.4 `stash.anabiHoert` – „Anabi hört zu"

Kulisse `keller`, Anabi kommt persönlich (`enter`, `cam: 'close'`): „So einen Namen kauft man nicht. Man hält ihn."

- **Annehmen** (`cls: 'red'`): `[{ call: 'anabiNachlass' }]` – `fns.anabiNachlass`: `v.kredit = Math.round(v.kredit / 2 / 1000) * 1000` (auf volle Tausend), `v.zorn = 0`; Rückgabe `{ toast: { icon: '🤝', title: 'Kredit halbiert', text: <neuer Kredit>, tone: 'win' } }`.
- **Ablehnen** (`cls: 'ghost'`): `[{ var: 'ruf', add: 1 }]` – Anabi geht wortlos.

Wirkung: Das Ende „Die Ablöse" (100.000 € plus Restkredit auf einmal) wird für den, der den Namen hat, bezahlbar. „Anabi stellen" (Krieg) braucht weiterhin Kesslers Deal.

## 5. Szenen

Neue Szenen (Cutscene-Bühne, Regie über `who/mood/bg`, Entscheidungen als `choices`): `schuld.vitoRespekt`, `schuld.igorHoert`, `stash.wache`, `stash.anabiHoert`. Alle Figuren und Kulissen existieren (`vito`, `igor`, `junge`, `anabi`, `stumme`; `hinterzimmer`, `bar`, `strasse`, `keller`). Texte in der Tonlage der jeweiligen Story, je 3–5 Panels, ein Panel mit Entscheidung. Die Kessler-Szene (`stash.angebot`) bekommt das bedingte Panel aus 4.2. Die Abrechnungs-Szene zeigt die neue Ruf-Zeile nur bei `ausgang === 'ok'`.

## 6. Dev-Panel und README

- Dev-Panel „Story": Ruf ist eine Var und damit bereits editierbar; keine Änderung. Die Szenen-Liste zeigt die vier neuen Szenen automatisch.
- README: Story-1-Absatz um Ruf-Stufen und die zwei Angebote, Story-3-Absatz um Ruf-Quellen, Wache und Anabis Angebot ergänzen; Dev-Parameter unverändert.

## 7. Tests

### 7.1 Selftests (Block `selftest`, Node ohne DOM)

- `StoryRules.rufStufe`: 0, 1 → Niemand; 2, 4 → Bekannt; 5, 7 → Respektiert; 8, 10 → Legende; −1 → Niemand.
- Schwellen-Konsistenz: jedes Event in `STORY_SCHULD` und `STORY_STASH` mit einer `ruf`-Bedingung (`gte`) nutzt einen Wert aus `RUF_STUFEN.map(s => s.ab)`.
- `GangRules.raidChance({ wache: true })` = 0; `({ bahnhof: true })` = 0; `({})` unverändert; `ambushChance` mit `wache` unverändert.
- Story 1 über die Engine mit Testzustand (`State.freshStory(STORY_SCHULD)`, Muster wie die bestehenden Story-Tests): `vitoRespekt` feuert nachts bei Ruf 5 genau einmal; Annehmen → `schuld` −10.000 (nicht unter 0, Test mit `schuld = 4000`), `vertrauen` +2 (geklemmt bei 10), `vitosMann`; Ablehnen → `ruf` +1. `igorHoert` feuert bei Ruf 8 nur ohne `igorZweifelt`; Zuhören setzt das Flag; `igorZweifel` feuert nicht mehr, wenn das Flag steht.
- Story 3: `fns.abrechnung` mit Ausgang `ok` → `ruf` +1, andere Ausgänge nicht; `eintreiberRuf` bei `jobToday === 'eintreiber'` am `job:after`; `kreditZahlen` → +1; Reparatur → +1 einmal je Woche, nach `lieferung` wieder möglich; alle Quellen klemmen bei 10. `wache` kommt bei Ruf 5 ohne `bahnhof`, nicht mit; `wacheNacht` zieht 200 € ab; bei `balance < 200` fällt das Flag, Toast, `wacheWeg`; `raid` liefert mit `wache` nie eine Tür. `anabiHoert` bei Ruf 8: Annehmen halbiert `kredit` auf volle Tausend (7.000 → 4.000, 10.000 → 5.000) und setzt `zorn` 0; Ablehnen → `ruf` +1.
- Stufen-Toast: `fns.rufStufe` liefert bei unverändertem Stand `{}`, beim Wechsel 1 → 2 einen Toast mit `tone: 'win'`, beim Wechsel 5 → 4 `tone: 'loss'`, und aktualisiert `rufStufe`.
- Bestehend: „Regie: alle Story-Szenen" (`validatePanels`, Sounds) deckt die neuen Szenen automatisch ab.

### 7.2 Browser-Playtest (`tests/playtest-story.py`, `scenario_ruf(cdp)`)

Einstieg `?fresh&story=stash&day=15&prev=wirt`; per Konsole `ruf = 5` setzen, schlafen → Wache-Szene, annehmen; nächste Nacht 200 € weniger, keine kaputte Tür (mehrere Nächte mit erzwungenem `rng`); `ruf = 8`, schlafen → Anabi-Szene, annehmen → Kredit halbiert, Zorn 0, HUD zeigt `🔥 Legende 8/10`. Dann `?fresh&story=schuld&day=12`, `ruf = 5`, schlafen → Vito-Szene, ablehnen → Ruf 6, HUD „Respektiert". Screenshots `ruf-wache.png`, `ruf-anabi.png`, `ruf-vito.png` nach `docs/superpowers/screenshots/`.

### 7.3 Lauf

`node tests/run-selftest.mjs`, `sh tests/dom-selftest.sh`, `python3 tests/playtest-story.py` (Szenario `ruf`), `python3 tests/mobile-check.py` (HUD-Zeile mit vier Einträgen in Story 3 darf auf dem Handy nicht überbreit werden – falls doch, klappt die Ruf-Note wie die Glück-Zeile beim Scrollen ein).
