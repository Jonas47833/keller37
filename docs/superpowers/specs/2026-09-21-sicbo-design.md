# KELLER 37 – Sic Bo im Casino Royal

Datum: 2026-09-21 · Status: abgestimmt · Basis: `keller37.html` @ `cfb965c` (main, nach Caribbean Stud)

## 1. Ziel

Ein fünftes Spiel im **Casino Royal**: **Sic Bo** – drei Würfel, ein Wurf, ein kompaktes Wettfeld mit vier Wettarten (Klein/Groß, Summe, Einzelzahl, Triple) und Quoten von 1:1 bis 180:1. Einsätze werden wie beim Craps per Chip auf Felder gelegt; nach dem Wurf ist der Tisch leer.

Dazu: Glück wirkt auf den Wurf (Baccarat/Stud-Muster), ein zehnter Insider („Gezinkter Becher"), ein Achievement.

Nicht Teil dieser Spec: Dubletten/Zwei-Würfel-Kombinationen/Gerade-Ungerade, neuer Skill, Story-Szenen am Tisch, Änderungen an Craps/Stud/Glücksrad.

## 2. Regeln

### 2.1 Wettfeld und Quoten

29 Felder in vier Wettarten. Feld-Ids sind die Schlüssel des `bets`-Objekts.

| Wettart | Feld-Ids | Quote (Gewinn : Einsatz) | Regel |
|---|---|---|---|
| Klein | `small` | 1:1 | Summe 4–10, **verliert bei jedem Triple** |
| Groß | `big` | 1:1 | Summe 11–17, **verliert bei jedem Triple** |
| Summe | `sum4` … `sum17` | 4/17 → 60 · 5/16 → 30 · 6/15 → 18 · 7/14 → 12 · 8/13 → 8 · 9/10/11/12 → 6 | exakte Augensumme |
| Einzelzahl | `one1` … `one6` | 1 / 2 / 3 je Anzahl Würfel mit der Zahl | mindestens ein Würfel zeigt die Zahl |
| Triple | `triple1` … `triple6` | 180 | alle drei Würfel zeigen genau diese Zahl |
| Beliebiger Triple | `tripleAny` | 30 | alle drei Würfel gleich |

`SicBoRules.PAY`:

```js
PAY: { small: 1, big: 1, tripleAny: 30, triple: 180, one: [0, 1, 2, 3],
       sum: { 4: 60, 5: 30, 6: 18, 7: 12, 8: 8, 9: 6, 10: 6, 11: 6, 12: 6, 13: 8, 14: 12, 15: 18, 16: 30, 17: 60 } }
```

`SicBoRules.FIELDS` = Liste aller 29 Ids in Tisch-Reihenfolge (`small`, `sum4`…`sum17`, `big`, `triple1`…`triple6`, `tripleAny`, `one1`…`one6`).

### 2.2 Einsätze

- `SicBoRules.BET = { MIN: 50, MAX: 2000 }` je Feld. Chip-Wert = Wert des nur lesbaren Felds `#sicBet` (Chips 50 / 200 / 500 / 2000, Start 50). Klick auf ein Feld addiert den Chip-Wert, gedeckelt bei `MAX` (`Math.min(MAX, alt + chip)`); ein Feld unter `MIN` gibt es nicht, weil der kleinste Chip `MIN` ist.
- **Risiko** eines Wurfs = Summe aller gesetzten Felder (`SicBoRules.risk(bets)`). Würfeln ohne Einsatz tut nichts.
- „Leeren" nimmt alle Einsätze zurück (nichts wurde abgebucht – Einsätze werden erst beim Wurf treuhänderisch über `Game.beginSpin(risk)` abgezogen).
- Nach dem Wurf werden alle Einsätze auf 0 gesetzt (kein Liegenlassen).

### 2.3 Wurf und Abrechnung

- `SicBoRules.roll(rng)` → `[d1, d2, d3]`, je `Math.floor(rng() * 6) + 1`.
- `SicBoRules.settle(bets, dice)` → `{ delta, won, lost, sum, triple }`:
  - `sum` = Augensumme, `triple` = `dice[0] === dice[1] && dice[1] === dice[2]`.
  - Je gesetztes Feld: gewonnen → `+bet × Quote` und Id in `won`; verloren → `−bet` und Id in `lost`. Einzelzahl mit 0 Treffern verliert.
  - `delta` = Netto aller Felder (kann 0 sein, wenn nichts gesetzt war).
- Geldfluss: `Game.beginSpin(risk)` vor dem Wurf; `Game.settle(delta, { from, game: 'sicbo', bet: risk, run })` danach (schreibt `delta + risk` gut). Schnappschuss der Einsätze wie beim Craps: abgerechnet wird, was abgebucht wurde.

Beispiele (Einsatz 100 je Feld): Wurf 2·3·4 (Summe 9): Klein +100, Summe 9 +600, Einzelzahl 3 +100, Groß −100. Wurf 4·4·4: Klein und Groß −100, Triple 4 +18.000, Beliebiger Triple +3.000, Summe 12 +600, Einzelzahl 4 +300.

## 3. Systeme

### 3.1 Glück (`SicBoRules.luckOverride(dice, bets, luck, rng)`)

- Glück > 0 und `settle(bets, dice).delta < 0` → mit `luck` % (`rng() * 100 < luck`) einmal `SicBoRules.roll(rng)` (alle drei Würfel neu).
- Pech < 0 und `delta > 0` → mit `|luck|` % (`Rules.pech(luck, rng)`) einmal neu.
- Sonst dasselbe Array zurück. Höchstens ein RNG-Entscheidungsaufruf, höchstens ein Neuwurf.
- Wirksames Glück: `Rules.effectiveLuck(Rules.luck(State.s, mods), risk)`.
- Reihenfolge im Modul: Becher (3.2) → Glück → Abrechnung. Ein Glücks-Neuwurf würfelt auch den offen liegenden Würfel neu (Becher und Glück stapeln nicht).

### 3.2 Insider „Gezinkter Becher" 🥤

```js
{ id: 'becher', name: 'Gezinkter Becher', icon: '🥤',
  text: 'Sic Bo: ein Würfel liegt vor dem Wurf schon offen – du siehst einen der drei Werte, bevor du setzt.',
  capped: true, mods: { sicboPeek: true } }
```

- `Rules.NEUTRAL_MODS.sicboPeek = false`, `MOD_STACK.sicboPeek = 'set'`; Katalog 10 Insider.
- Modul-Zustand `SicBo.peekDie` (1–6 oder `null`): mit Insider wird beim Mount und nach jedem Wurf `peekDie = SicBoRules.roll(Math.random)[0]` gesetzt und als Würfel 1 offen angezeigt; ohne Insider `null`, alle Würfel zeigen „?".
- Beim Wurf: `SicBoRules.peekDice(peekDie, dice)` → ersetzt `dice[0]` durch `peekDie`, wenn `peekDie != null`. Das Modul ruft das nur auf, wenn `Rules.effectiveInsider(mods.sicboPeek, risk)` wahr ist (Risiko ≤ 250 €); darüber bleibt der Wurf frisch.
- Hinweiszeile `#sbPeek` (Klasse `insider-hint`), live bei jeder Einsatzänderung gerendert: Risiko ≤ 250 → „🥤 Der erste Würfel liegt schon"; Risiko > 250 → „🥤 Gezinkter Becher: wirkt bis 250 €"; ohne Insider verborgen.

### 3.3 Achievement

```js
{ id: 'dreiGleiche', title: 'Drei Gleiche', icon: '🎲', desc: 'Beim Sic Bo einen Triple getroffen – gezielt oder beliebig.' }
```

`Bus.on('sicbo:result', ({ won }) => { if (won.some((id) => id.startsWith('triple'))) Achievements.unlock('dreiGleiche'); })`. Event-Payload: `{ delta, bet, dice, sum, triple, won, lost }` nach jedem Wurf.

### 3.4 Royal-Mechanik

Eintritt, Auto-Pflicht, Story-Sperre laufen über die Royal-Tür; der Screen ist nur aus der Lobby erreichbar. `Bus 'win'` (aus `Game.settle`) speist „Gast des Hauses" ab 5.000 € Nettogewinn wie bei den anderen Tischen. Keine Änderung an `Story.DOORS`, Kapitel-Türlisten, `Mugging.CASINO`, `GangRules`.

## 4. Tisch (UI)

### 4.1 Lobby-Portal

Fünfte Kachel nach Caribbean Stud:

```html
<button class="portal" data-screen="sicbo"><span class="portal-crown"></span><span class="plaque">Sic Bo</span><span class="glyph">🎲</span><span class="engraved">3 Würfel · bis 180:1</span></button>
```

Desktop 3 + 2, Handy 2 + 2 + 1 – kein neues Lobby-CSS.

### 4.2 Screen `sicbo` (Template `tpl-sicbo`)

Gleicher Filz-Tisch wie Craps (`panel craps-panel`, `.craps-table`, `.craps-head`, `.die`, `.chip-stack`, `.won`/`.lost`):

```
<div class="craps-head"><span class="neon">SIC BO</span><span class="craps-history" id="sbHistory"></span></div>
<div class="craps-dice"><div class="die" id="sbDie1">?</div><div class="die" id="sbDie2">?</div><div class="die" id="sbDie3">?</div></div>
<div class="insider-hint hidden" id="sbPeek"></div>
<div class="sicbo-grid">
  <button class="sb-cell sb-side" data-bet="small"><b>KLEIN</b><small>4–10 · 1:1</small><span class="chip-stack hidden"></span></button>
  <div class="sb-sums"> 14× <button class="sb-cell" data-bet="sumN"><b>N</b><small>Q:1</small><span class="chip-stack hidden"></span></button> </div>
  <button class="sb-cell sb-side" data-bet="big"><b>GROSS</b><small>11–17 · 1:1</small><span class="chip-stack hidden"></span></button>
</div>
<div class="sicbo-row"><span class="sb-label">TRIPLE</span> 6× <button class="sb-cell" data-bet="tripleN"><b>N N N</b><small>180:1</small>…</button> <button class="sb-cell" data-bet="tripleAny"><b>BELIEBIG</b><small>30:1</small>…</button></div>
<div class="sicbo-row"><span class="sb-label">ZAHL</span> 6× <button class="sb-cell" data-bet="oneN"><b>⚀…⚅</b><small>1:1 · 2:1 · 3:1</small>…</button></div>
<div class="status" id="sbStatus">Einsatz wählen, auf Felder legen, würfeln</div>
<div class="bet-bar"> #sicBet (readonly, 50) · Chips 50/200/500/2000 · #btnSbClear „Leeren" · #btnSbRoll „Würfeln" · #sbBack „← Lobby" </div>
```

Der Verlauf `#sbHistory` zeigt die letzten 6 Würfe als „2·3·4" mit „ · " getrennt (Konvention `#crapsHistory`).

**CSS (neu, klein):**
- `.sicbo-grid { display: grid; grid-template-columns: 1fr 7fr 1fr; gap: 8px }`, `.sb-sums { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px }`, `.sicbo-row { display: grid; grid-template-columns: auto repeat(7, 1fr); gap: 6px; align-items: stretch }` (ZAHL-Reihe hat 6 Felder + leere Spalte).
- `.sb-cell { position: relative; min-height: 44px; border: 1px solid var(--gold); background: rgba(0,0,0,.25); color: var(--ivory); font-family: inherit; cursor: pointer }`, `.sb-cell b` Display-Schrift, `.sb-cell small` `--dim` 0,7 rem; `.sb-cell.won { background: var(--gold); color: #141216 }`, `.sb-cell.lost { opacity: .45 }`.
- Handy ≤ 760 px: `.sicbo-grid { grid-template-columns: 1fr 1fr }` mit `.sb-sums { grid-column: 1 / -1 }` (Klein/Groß nebeneinander, Summen darunter 7 pro Reihe), `.sicbo-row { grid-template-columns: repeat(4, 1fr) }` mit `.sb-label { grid-column: 1 / -1 }`; alle Zellen ≥ 40 px hoch (Mobile-Check).
- `.chip-stack` sitzt wie beim Craps oben rechts in der Zelle (Zelle ist `position: relative`).

### 4.3 Ablauf und Statustexte

| Situation | `#sbStatus` |
|---|---|
| Leer | „Einsatz wählen, auf Felder legen, würfeln" |
| Würfeln ohne Einsatz | unverändert, `SFX 'click'`, kein Wurf |
| Während des Wurfs | „Die Würfel rollen…" (`.die.rolling`, 900 ms / Reduced-Motion 150 ms, `SFX.loop('reelSpin')`) |
| Ergebnis | „⚁ ⚂ ⚃ = 9 · Klein · Summe 9 zahlt 6:1 · (+700 €)" – Würfel-Glyphen, Summe, Gewinnfelder mit Quote, bei Triple „Triple!" vorn; Betrag mit `win`/`loss`-Span wie Craps; ohne Treffer „⚀ ⚀ ⚁ = 4 · nichts getroffen (−200 €)" |

Nach dem Wurf: Gewinnzellen `.won`, Verlustzellen `.lost`; `chip-stack`s bleiben mit dem Schnappschuss-Betrag sichtbar bis zum nächsten Klick auf ein Feld oder „Leeren" (Konvention Craps). Würfel zeigen das Ergebnis, bis der nächste Wurf beginnt; mit Insider wird Würfel 1 danach auf den neuen `peekDie` gesetzt und Würfel 2/3 auf „?".

### 4.4 Modul `SicBo`

Nach dem Craps-Muster: `root, rolling, gen, bets, history, run, peekDie, forceDice`, `alive(gen)`, `checkRun()` (anderer `State.s` → `reset()`), `place(id)`, `clear()`, `reset()`, `render()` (Beträge, Stacks, Peek-Hinweis, Würfel-Vorschau), `roll()`, `onKey(e)` (Leertaste = Würfeln). `forceDice` (Array `[d1, d2, d3]` oder `null`) ersetzt den `roll()`-Aufruf für den nächsten Wurf (Dev/Test); der Becher gilt auch dann (Würfel 1 aus `peekDie`, wenn Insider wirksam).

`UI.register('sicbo', { template: 'tpl-sicbo', mount, unmount })`: Mount bindet `Game.bindBet(root, 'sicBet')`, Feld-Klicks per Delegation auf `.sb-cell[data-bet]`, Buttons, Tastatur; setzt `peekDie` (wenn Insider) und rendert. Unmount entfernt den Key-Listener, stoppt `reelSpin`, `root = null`, `rolling = false`. Ungeworfene Chips verfallen nicht (nie abgebucht); sie bleiben im Modul liegen und werden bei anderem Spielstand geleert.

## 5. Listen und Einbindung

Alle bekommen `'sicbo'`: `Royal.GAMES`, `RoyalRules.SCREENS`, `DevRules.ROYAL_SCREENS`, `Story.ROOM_OF.sicbo = ['royal']`, `STORY_STASH.turnoverGroups.umsatzRoyal` (+ gleichnamige Test-Fixture), Boot-Parameter `?screen=royal&game=sicbo`, `tests/run-selftest.mjs` (Block `'sicbo-rules'` nach `'stud-rules'`), `tests/mobile-check.py` (`FREE_SCREENS`, Zonen-Schleife und `record`-Zeile, `TAP_SELECTORS` + `".sb-cell"`).

Texte: Cutscene `royal.first` „Vier Tische." → „Fünf Tische."; README Royal-Absatz („Fünf Tische …", Sic-Bo-Satz, „fünf Portalen", Liste der Tische mit festen Einsätzen), README `&game=megaslots|craps|wheel|stud|sicbo`; Playtest-Check „lobby: vier Portale" → „fünf Portale" (`portals == 5`).

Neue Script-Blöcke: `<script id="sicbo-rules">` nach `stud-rules` (DOM-frei, nutzt `Rules.pech`), `<script id="game-sicbo">` nach `game-stud`.

## 6. Tests

### 6.1 Selftests (Block `selftest`)

- `PAY`: Summe 4 → 60, 10 → 6, 15 → 18; `FIELDS.length === 29`.
- `settle` (Einsatz 100 je Feld): Wurf 2·3·4 mit `small, big, sum9, one3, one5` → `delta = 100 − 100 + 600 + 100 − 100 = 600`, `won = ['small','sum9','one3']`, `lost = ['big','one5']`, `sum 9`, `triple false`; Wurf 4·4·4 mit `small, big, triple4, tripleAny, sum12, one4` → `delta = −200 + 18000 + 3000 + 600 + 300 = 21700`, `triple true`; Einzelzahl 2× → 2:1 (Wurf 5·5·1, `one5` → +200); leeres `bets` → `delta 0`, leere Listen.
- `risk`: Summe der Felder.
- `roll(seq(0, 0.5, 0.99))` → `[1, 4, 6]`.
- `peekDice(4, [1, 2, 3])` → `[4, 2, 3]`; `peekDice(null, d)` → `d` (gleiche Referenz).
- `luckOverride`: Verlust (`small` bei 6·6·6) + Glück 50, `seq(0.1, 0, 0, 0)` → neuer Wurf `[1, 1, 1]` (andere Referenz); `seq(0.9)` → gleiche Referenz; Gewinn + Pech −50, `seq(0.1, …)` → neu; Gewinn + Glück → gleiche Referenz, 0 RNG-Aufrufe; ohne Einsatz (`delta 0`) → unverändert, 0 Aufrufe.
- Katalog: `INSIDER.length === 10`, `becher` vorhanden und `capped`, `NEUTRAL_MODS.sicboPeek === false`, `MOD_STACK.sicboPeek === 'set'`; `effectiveInsider(true, 250) === true`, `(true, 300) === false`; `insiderDraw`-Test auf `slice(0, 8)` (Pool 2 → 2 gezogen).
- Listen: `RoyalRules.SCREENS` enthält `sicbo` (Liste im Test aktualisieren), `DevRules.ROYAL_SCREENS`, `STORY_STASH.turnoverGroups.umsatzRoyal`, `zoneFor('sicbo') === 'royal'`.
- DOM: Achievement `dreiGleiche` – `sicbo:result` mit `won: ['tripleAny']` schaltet frei, mit `won: ['small']` nicht; `Royal.GAMES`/`ROOM_OF`/Portal-Plakette „Sic Bo"; Chip-Test `['sicbo', 'sicBet', '50', '200']`; Geldfluss über den Screen: Konto 1000, Chip 50 auf `small` und `sum9`, `SicBo.forceDice = [2, 3, 4]`, Wurf → 1000 − 100 + (350 + 100) = 1350, Zellen `small`/`sum9` `.won`, Status enthält „Summe 9".

### 6.2 Browser-Playtest (`tests/playtest-story.py`, `scenario_sicbo(cdp)`)

Freies Spiel, Auto, Royal betreten, `UI.show('sicbo')`, `State.meta.insider = []` und `dreiGleiche` zurücksetzen (Meta überlebt `?fresh`):

1. Portal `.portal[data-screen="sicbo"]` in der Lobby; Zone `royal` am Tisch; Screenshot `royal-sicbo.png` nach dem Setzen (vor dem Wurf).
2. Chip 50 auf `small` + `sum9`, `forceDice = [2, 3, 4]`, Würfeln → Konto +350, Status enthält „Summe 9", `small` und `sum9` haben `.won`, `big` nicht gesetzt.
3. Chip 50 auf `small`, `tripleAny`, `triple4`; `forceDice = [4, 4, 4]` → Konto +50·(−1 + 30 + 180) = +10.450, Erfolg `dreiGleiche` freigeschaltet, Status enthält „Triple".
4. Chip 200 auf `big`, „Leeren" → alle Stacks verborgen, Würfeln → Konto unverändert, kein Wurf (`SicBo.rolling` false, Würfel unverändert).
5. Insider `becher`: `UI.show('sicbo')` erneut; `SicBo.peekDie` ist 1–6 und `#sbDie1` zeigt die Augenzahl; `#sbPeek` „Der erste Würfel liegt schon"; Chip 50 auf `one<peekDie>`, `forceDice = [x, y, z]` mit `x ≠ peekDie` und `y, z ≠ peekDie` (z. B. die zwei kleinsten Zahlen ≠ peekDie) → Wurf zeigt `peekDie` als Würfel 1, `one<peekDie>` gewinnt genau 1:1 (+50); danach 500 auf `big` (Chip 500) → `#sbPeek` enthält „wirkt bis 250"; `forceDice = [6, 6, 5]` → Würfel 1 ist 6 (nicht `peekDie`, es sei denn `peekDie === 6` – dann `forceDice = [1, 6, 5]`), Groß gewinnt +500.
6. Insider zurücksetzen, Screen verlassen → keine Toasts, Konto unverändert.

Screenshots: `royal-lobby.png` (5 Portale) erneuern, `royal-sicbo.png` neu, `mobile-royal.png` erneuern, `mobile-sicbo.png` neu (aus `tests/mobile-check.py`).

### 6.3 Lauf

`node tests/run-selftest.mjs`, `tests/dom-selftest.sh`, `python3 tests/mobile-check.py`, `python3 tests/playtest-story.py` (eigene `K37_PORT`/`K37_PROFILE`/`K37_SHOTS`). Alles grün vor Merge.
