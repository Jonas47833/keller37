# Casino Royal – Art-déco-Look, Kater-HUD und Royal-Momente (Design)

Datum: 2026-09-18 · Status: abgestimmt · Basis: `main` ab `abc9cd3` (Story 2 „Der Kater" mit Casino Royal, Mobile-Paket)

## 1. Ziel

Das Casino Royal aus Story 2 soll sich anfühlen wie ein anderer, teurerer Ort als der Keller: Art déco in Gold und Schwarz statt verranztem Neon. Dazu werden die Story-2-Elemente rundherum aufgehübscht: die Fassade in der Stadt, das Kater-HUD (Leber/Pegel/Deckel, Zitter-Tag), der Royal-Cutscene-Hintergrund und die Gewinn-/Verlust-Momente in den drei Royal-Spielen.

Nicht Teil dieses Pakets: Spielregeln, Auszahlungen, Story-Texte, Story-Logik. Der Keller am Desktop bleibt pixelidentisch.

## 2. Globale Vorgaben

- Eine Datei `keller37.html`, Deutsch, keine Bilddateien – alle Texturen (Sonnenstrahlen, Marmor, Kronleuchter, Glühbirnen) sind CSS-Verläufe oder DOM-Elemente.
- Schrift: „Cinzel" (Google Fonts, 400/700) wird zusätzlich zu Bebas Neue und Courier Prime geladen; Fallback `Georgia, "Times New Roman", serif`. Zahlen bleiben Courier Prime.
- Royal-Regeln hängen ausnahmslos an `body[data-zone="royal"]`; ohne diese Zone ändert sich kein Pixel am Desktop-Keller (Gegenprobe per Screenshot-Diff auf `hub`, `roulette`, `slots`, `finance`, `stadt`).
- Handy (≤ 760 px): die Regeln des Mobile-Pakets gelten weiter (kein Backdrop-Blur, kein Filmkorn, Opacity-Wechsel, Tap-Ziele ≥ 40 px, keine Überbreite). Lauflichter, Lichtläufe und Goldregen laufen nur unter `(hover: hover)`; auf dem Handy sind sie statisch bzw. auf einen einzigen Durchlauf reduziert.
- `prefers-reduced-motion: reduce` schaltet alle Royal-Animationen ab (Lauflicht, Lichtlauf, Zittern, Goldregen, Lichter-aus-Fade werden zu sofortigen Zustandswechseln).
- Performance-Budget: pro Screen höchstens drei geschichtete Verläufe auf großen Flächen, keine `filter: blur` auf dem Handy, keine dauerhaft laufenden Animationen außer dem Marquee-Lauflicht am Desktop.

## 3. Zonen-Mechanik

`UI.show(id)` setzt `document.body.dataset.zone = ROYAL_SCREENS.includes(id) ? 'royal' : 'keller'` mit `ROYAL_SCREENS = ['royal', 'megaslots', 'craps', 'wheel']` (Konstante bei `Royal.GAMES` bzw. daneben; `Royal.GAMES` enthält bereits die drei Spiele, die Lobby kommt dazu). Beim Wechsel der Zone (Keller → Royal oder Royal → Keller) blendet `UI.show` statt des normalen Bühnen-Übergangs einen **Gold-Vorhang**: `#nightfade`-artiges Overlay `#zonefade` (fixed, schwarz mit goldenem Mittelschimmer), 0,4 s ein, Bühne tauschen, 0,4 s aus. Auf dem Handy 0,25 s, bei Reduced-Motion kein Overlay. Die Wartezeiten liegen in `UI.zoneFade(from, to)`; `UI.busy` bleibt währenddessen gesetzt.

`#zonefade` bekommt z-Index 78: über der Bühne und der Seitenleiste (30), unter Cutscene (80), `#nightfade` (85) und Toasts – eine Royal-Cutscene liegt also immer über dem Vorhang. Das Overlay hat `pointer-events: none` und ist außerhalb des Wechsels unsichtbar (`opacity: 0`).

Tokens unter `body[data-zone="royal"]`:

```
--bg: #0b0a0c; --panel: #141216; --panel-2: #1c1920;
--gold: #c9a961; --gold-2: #f1dfa8; --bronze: #8a6a2e;
--emerald: #1d6b4a; --bordeaux: #5a1a24; --ivory: #efe6cf; --text: #efe6cf; --dim: #9d9481;
--font-display: "Cinzel", Georgia, "Times New Roman", serif;
--radius: 4px; --shadow: 0 12px 34px rgba(0,0,0,.7);
```

Hintergrund des `body`: `--bg` plus Sonnenstrahl-Fächer oben mittig (`conic-gradient` aus 24 Strahlen, Gold 3 % Deckung) und ein flacher Marmor-Schimmer (`radial-gradient`, weiß 2 %). Vignette bleibt, Filmkorn bekommt im Royal 3 % statt 6 %.

## 4. Kopfzeile und Seitenleiste im Royal

- `.wallet`: Hintergrund `#0b0a0c`, unten **doppelte Goldlinie** (1 px Gold, 3 px Abstand, 1 px Bronze – als `border-bottom` + `box-shadow`). Marke „Keller 37" in Cinzel-Gold ohne Neon-Flackern, darunter in 0,65 rem Kapitälchen „Gast im Casino Royal" (Element `.brand-sub`, nur in der Zone sichtbar; wird bei `flags.royalGuest` zu „Gast des Hauses").
- Kontostand `.balance`: Goldplakette – Hintergrund `linear-gradient(#2a2418, #14110b)`, Rand 1 px Gold, Innenlinie 1 px Bronze im Abstand 3 px (`box-shadow: inset 0 0 0 3px #14110b, inset 0 0 0 4px var(--bronze)`), Schrift Champagner.
- Zettel `.note`: Elfenbein-Papier `#efe6cf` mit Bronze-Rand, Rotation bleibt; `.note.danger` bekommt eine Bordeaux-Linie links statt Rosa-Grund.
- Glücksleiste und Level-Badge: Segmente in Gold statt Grün, Rahmen Bronze.
- Seitenleiste `.side-sec`: Onyx-Karte `--panel` mit 1 px Goldlinie, Überschrift in Cinzel-Kapitälchen 0,85 rem mit Ornamentstrich `— ✦ —` unter dem Titel (`h3::after`), Knöpfe `.side-btn` mit Bronze-Rand, Hover Gold; Preise in Champagner.
- Handy-Tab-Leiste: Hintergrund `#0b0a0c`, Goldlinie oben, aktiver Reiter Gold; Icons bleiben Emoji.
- Icon-Knöpfe: Bronze-Rand, Hover Gold.

## 5. Lobby (`tpl-royal`)

Struktur ersetzt das bisherige Panel:

```
<div class="royal-foyer">
  <div class="deco-arch"><h2>Casino Royal</h2></div>
  <div class="deco-card"><p id="royalLine"></p></div>
  <div class="deco-portals">
    <button class="portal" data-screen="megaslots">…</button> ×3
  </div>
  <div class="bet-bar"><button class="btn ghost sm" id="royalLeave">← Zurück in die Stadt</button></div>
</div>
```

- **Bogen** `.deco-arch`: 100 % breit, 120 px hoch (Handy 90 px), Sonnenstrahl-Fächer (`conic-gradient` Gold auf Onyx, 3 % Deckung) hinter einem Halbkreis mit doppelter Goldlinie; Titel „CASINO ROYAL" in Cinzel 700, 2,4 rem (Handy 1,6 rem), Letterspacing 0,25 em, Champagner mit einem weichen Goldschein (`text-shadow: 0 0 18px rgba(201,169,97,.45)` – ein Schatten, kein Flackern).
- **Visitenkarte** `.deco-card`: Elfenbein, 1 px Bronze-Rand, Schrift Courier Prime kursiv `#2a2418`, kleines 🎩 links; enthält weiterhin `#royalLine` (Text aus `Royal.line()`).
- **Portale** `.portal`: drei hohe Türen (Desktop 3 Spalten, 260 px hoch; Handy 2 Spalten + einzelne letzte über beide, 170 px). Aufbau: Onyx-Fläche, außen 2 px Gold, innen 1 px Bronze im Abstand 4 px; oben ein Stufenmuster aus drei absteigenden Goldbalken (`.portal-crown`, CSS-Pseudoelemente); **Messingplakette** `.plaque` (Verlauf `#b8923f → #e2c77a → #9a7a2f`, gravierte Schrift Cinzel 700 `#2a1d08`, `text-shadow: 0 1px 0 rgba(255,255,255,.35)`), Symbol 3 rem (Handy 2,2 rem) mit `drop-shadow` nur am Desktop, unten die gravierte Zeile `.engraved` in Cinzel 0,75 rem Bronze. Hover (nur `(hover: hover)`): Innenfläche wird warm (`radial-gradient` Gold 12 %), Plakette bekommt einen Lichtreflex (`::after` mit linearem Verlauf, 0,5 s). Tap: `transform: scale(.98)`.
- **Boden**: `.deco-portals` liegt auf einem flachen Schachbrett aus zwei `repeating-linear-gradient` (Onyx/`#1a171c`), 45° gedreht, mit Perspektiv-Verlauf nach oben ins Schwarz (Overlay `linear-gradient`). Drei Verläufe insgesamt, Handy identisch (billig).
- Klick-Logik unverändert (`data-screen` → `UI.show`).

## 6. Die drei Spiele

Gemeinsam in der Zone:
- Chips `.chip`: schwarz `#141216`, Doppelring (4 px gestrichelter Goldrand + `inset 0 0 0 3px #0b0a0c, inset 0 0 0 4px var(--bronze)`), Wert in Champagner; Hover/Tap Goldfüllung mit schwarzer Schrift. Die Keller-Farben nach `data-v` werden in der Zone nicht angewendet (eine Zonen-Regel überschreibt `--chip`).
- Hauptknopf `.btn.solid`: Goldverlauf, schwarze Cinzel-Schrift 700, Letterspacing 0,15 em; Nebenknöpfe `.btn` Goldumriss, `.btn.ghost` Bronze-Umriss; `.btn.green/.blue/.red` bekommen in der Zone Smaragd/Champagner/Bordeaux-Umrisse.
- Auszahlungstafeln `.chalk.paytable`: **Messingtafel** – Verlauf wie die Plakette, Text `#2a1d08` in Courier Prime, Überschrift Cinzel; Rand 2 px `#5a4520`, Innenlinie 1 px `#e2c77a`.
- Status-Zeile `.status`: Cinzel 0,95 rem Champagner.
- Klassen `.neon` wirken in der Zone ohne Flackern und mit einem einzigen weichen Goldschein.

### 6.1 Mega Seven
- `.mega-machine`: Onyx-Gehäuse, Doppelrahmen (2 px Gold + 1 px Bronze innen), oben eine **Stufenkrone** (`::before`: drei Goldbalken 60/40/20 % Breite, je 4 px). Titel in Cinzel 700 Champagner mit **Lichtlauf**: `background-clip: text` mit Goldverlauf, der alle 6 s einmal in 1,2 s durchläuft (Keyframe `royalSheen`, nur `(hover: hover)`, nicht bei Reduced-Motion).
- Zellen `.mega-grid .cell`: Elfenbein `#efe6cf` mit 1 px Goldkante, Symbole wie bisher; `.cell.spin` behält den Flicker (Blur nur Desktop).
- **Gewinnlinien**: zusätzlich zur Zell-Markierung zeichnet `Mega.showWin` pro getroffener Linie eine goldene Linie über das Raster – `div.mega-line` (absolute, 3 px, Gold, Schein 6 px), Position aus den Zellrechtecken der Linie (Polylinie als SVG `<svg class="mega-lines-svg">` über dem Raster, `<polyline>` je Linie, `stroke-dasharray`-Animation 0,4 s einmalig). Wird beim nächsten Dreh geleert. Die 5 Linienmuster liest sie aus `RoyalRules.MEGA.LINES` (Reihe je Walze, vorhanden).
- **Freispiele**: `#megaFree` wird ein Banner, das von oben über die Maschine klappt (`.mega-free.show` → `transform: translateY(0)`, 0,35 s), Text „FREISPIELE ×2 · noch N" in Cinzel Gold auf Onyx mit Goldlinie; während der Freispiele bekommen die Zellen einen Champagner-Rand (`.mega-machine.free .cell`). Ende: Banner klappt weg, Status „Freispiele vorbei · +X €" (Summe der Freispiel-Gewinne, in `Mega.freeTotal` mitgezählt).

### 6.2 Craps
- `.craps-table`: tiefes Smaragd (`radial-gradient(#1f6b4a, #0e3d2a 70%, #082416)`), Rand 6 px Onyx mit 2 px Goldborte (`box-shadow: 0 0 0 2px var(--gold), 0 0 0 6px #141216`), Ecken 80 px / 30 px.
- Titel „CRAPS" Cinzel Champagner; Puck `.craps-point`: schwarz-goldener Puck (Onyx, Goldrand, Cinzel), `.on` invertiert (Gold, schwarze Schrift „PUNKT 6").
- Felder `.craps-bet`: eingelassen (`inset`-Schatten), 1 px Goldlinie, Überschrift Cinzel; beim Setzen erscheint ein **Chip-Stapel-Marker** rechts oben (`.chip-stack`, identisch zum Roulette) mit Betrag; `won` → Goldrahmen + Marker gold, `lost` → Marker grau, Feld gedimmt.
- Würfel `.die`: Elfenbein, Augen `#141216`, 2 px Goldrand, Schatten `0 6px 10px rgba(0,0,0,.6)`; Wurf-Animation bleibt.
- Verlauf `.craps-history`: Cinzel 0,8 rem Champagner 70 %.

### 6.3 Glücksrad
- Rad `.wheel`: 8 px Goldrand plus **Zahnkranz** (`::before` mit `repeating-conic-gradient` 24 Zähne, Gold/Bronze, 6 px außerhalb), Nabe `.wheel-hub`: Onyx mit Goldrand und 🎩.
- Segmentfarben nach Multiplikator (statt Regenbogen): ×10 Gold `#c9a961` mit schwarzer Schrift, ×5 Champagner `#f1dfa8` schwarz, ×2 Smaragd `#1d6b4a`, ×1 Onyx-hell `#2a262e`, Hälfte Bordeaux `#5a1a24`, Bankrott Onyx-dunkel `#141216` mit Text „BANKROTT" in Bronze und ☠ davor. Farbe kommt aus `data-mult` am Segment (`Wheel.build` setzt `data-mult`), die Zone mappt per CSS.
- Zeiger `.wheel-pointer`: goldene Feder (▼ in Gold mit weichem Schein bleibt, Form via `clip-path`-Dreieck 18 × 26 px).
- Dreh: Rand-Lichter – 24 Punkte auf dem Zahnkranz (`.wheel-lights` mit `repeating-conic-gradient`), die während `.wheel.spinning` in 0,15 s-Schritten blinken (Keyframe, nur Desktop).
- **Bankrott**: Rad stoppt, Segment leuchtet 0,4 s Bordeaux, dann **Lichter aus**: `.wheel-panel.blackout` dunkelt das Panel 0,6 s auf 15 % ab, Kontostand blitzt rot (`.balance.down`), Sylvie-Toast „Das Haus dankt." (Icon 🎩). Bei Reduced-Motion nur der Toast.

## 7. Fassade in der Stadt (`Stadt.render`, Royal-Karte)

Die Royal-Karte wird `div.storefront.royal.facade` mit eigenem Aufbau; Klick bleibt `Royal.enter()`:

```
<div class="facade" data-shop="royal">
  <div class="marquee"><span class="bulbs"></span><h3>Casino Royal</h3><span class="bulbs"></span></div>
  <div class="portal-door">🎩</div>
  <div class="brass-sign">…</div>
  <div class="doorman hidden">🕴️ Sie zittern. Wir haben eine Hausordnung.</div>
</div>
```

- Sockel schwarzer Stein (`#141216` mit horizontalen Fugen aus `repeating-linear-gradient`), Goldportal mit Stufenbogen (`.portal-door`, 3 Stufen als Pseudoelemente), Tür-Innenfläche dunkel; leuchtet warm (`radial-gradient` Gold 18 %) wenn `chk.ok && !gate`.
- **Marquee**: Titel in Cinzel 700 Champagner, links und rechts je 8 Glühbirnen (`.bulbs` mit `radial-gradient`-Punkten); Lauflicht via `background-position`-Animation 1,2 s linear endlos – nur `(hover: hover)`, sonst statisch an.
- **Messingschild** `.brass-sign` (Plakettenverlauf, gravierte Schrift): ohne Auto `chk.text` („Parkservice only – zu Fuß kommt hier keiner rein."), mit Auto „Eintritt 100 €" bzw. „Gast des Hauses"; ohne Auto bleibt die Tür dunkel und die Fassade bekommt `.locked` (Sättigung 60 %).
- **Türsteher-Panel** `.doorman`: erscheint bei `gate` (Zitter-Tag), schiebt sich vor die Tür (schwarz, Goldlinie, 🕴️ links, Gate-Text), Fassade ausgegraut; Klick spielt weiter die Gate-Szene.
- Handy: Fassade 200 px hoch, Marquee-Titel 1,3 rem, je 5 Birnen.

## 8. Kater-HUD und Zitter-Tag

Nur wenn `Story.story.id === 'kater'`: `Story.hudNotes()` liefert statt drei `.note`-Zetteln ein Element `div.kater-hud` (bleibt in `#notes`, Story 1 unverändert):

- **Leber** `.hud-leber`: Label „🫀", Balken 90 × 10 px (Handy 70 px) mit Füllung `leber` %, Farbe grün `#3ddc84` (> 60), gelb `#e8c65a` (31–60), rot `#ff3b3b` (≤ 30); bei ≤ 30 pulsiert der Balken (`pulseText`-artig, 1,2 s) – nicht bei Reduced-Motion. Zahl „74/100" in Courier Prime daneben.
- **Pegel** `.hud-pegel`: drei 🍺, gefüllte Krüge (Index < `vars.pegel`) Deckung 1, leere 0,3; mit `flags.sucht` zusätzlich ein 🍪-Marker, der bei `vars.brownieHeute > 0` gefüllt ist; Tooltip „Pegel 2/3". Bei `pegel` ≥ 3 (oder Sucht + Brownie) bekommt das Element eine kleine grüne Linie unten („gedeckt").
- **Deckel** `.hud-deckel`: runder Bierdeckel 34 px (Pappe `#d9c7a3`, gestrichelter Innenring, Strichliste `𝍸`-Zeichen je 50 €, maximal 8 Striche, darunter „…"), Betrag als Tooltip und daneben in Courier Prime; 0 € → Deckel ausgegraut.
- **Zitter-Tag** (`flags.zitter`): `body.zitter` wird von `Story.renderDaybar`/`UI.renderWallet` gesetzt. Wirkung: `.balance` und `.hud-pegel` bekommen `animation: zitter 3s infinite` (Keyframe: 0–8 % 1 px Versatz hin und her, Rest Ruhe), im Header ein roter Zettel `.note.danger` „🫨 Zittern · −15 Glück"; beim Ende (Hook `zitterEnde`/`zitterEndeBrownie`) Toast „Ruhige Hände." (Icon 🍺/🍪) – als `{ toast: … }`-Effekt an diesen beiden Hook-Einträgen (Effekt-Typ existiert). Kein Zittern bei Reduced-Motion.
- Werte kommen weiterhin aus `s.story.vars`; die `hud`-Definition der Kater-Story bleibt als Fallback (z. B. für Tests), das Rendering prüft `story.hudRender === 'kater'` (neue Eigenschaft an `STORY_KATER`).

## 9. Cutscenes und Momente

- **Hintergrund `royal`**: bestehender Verlauf plus (a) Kronleuchter oben mittig – `::before` mit einem Goldbogen (Border-Radius-Halbkreis 220 × 60 px, 2 px Gold) und 7 Lichtpunkten (`radial-gradient`-Liste, Champagner, weicher Schein 8 px), (b) Sonnenstrahl-Fächer (`conic-gradient`, Gold 4 %), (c) Marmorboden unten 30 % (Schachbrett wie in der Lobby). Drei Ebenen, keine Bilder.
- **Sylvie-Portrait**: `.cs-portrait` bekommt in Royal-Szenen (`bg === 'royal'` oder `who === 'sylvie'`) einen Goldrahmen (2 px Gold + 1 px Bronze) statt des Charakterfarb-Rings.
- **Gast des Hauses**: vor `Cutscene.play('royal.guest')` spielt `Royal.goldRain()` – 30 Partikel 🪙/✨ über der Bühne (eigene, kleine Partikelfunktion analog `Cutscene._particles`, 2 s), gleichzeitig `.balance.gold-flash` (0,8 s Goldschein). Bei Reduced-Motion oder auf dem Handy 12 Partikel.
- **High-Roller-Trophäe** (`royalHigh`): das Achievement-Toast bekommt `tone: 'gold'` (neuer Toast-Ton: Goldlinie links, Onyx-Hintergrund) und einen Konfetti-Burst (12 ✦-Partikel um den Toast, 1 s, nicht auf Reduced-Motion).
- Mega-Seven-Freispiel-Banner und Glücksrad-Lichter-aus: siehe 6.1 / 6.3.

## 10. Tests und Abnahme

- Node- und DOM-Selftests bleiben grün; neue Regel-Tests nur für `Rules`-nahe Helfer (Leber-Farbstufe `RoyalRules.leberTone(v)` → `'ok'|'warn'|'danger'`, Deckel-Strichzahl `RoyalRules.deckelMarks(v)` → 0…8, Segmentfarb-Klasse `RoyalRules.wheelTone(mult)`).
- `tests/mobile-check.py` prüft die Royal-Screens weiter (Überbreite, Tap-Ziele); zusätzlich `body.dataset.zone` auf `royal`/`megaslots`/`craps`/`wheel` = `'royal'` und auf `hub` = `'keller'`.
- `tests/playtest-story.py` neues Szenario `scenario_royal_look`: Zonenwechsel beim Betreten/Verlassen (inkl. `#zonefade`), Fassade in drei Zuständen (ohne Auto: `.locked` + Parkservice-Text; mit Auto: warmes Portal + „Eintritt 100 €"; Zitter: `.doorman` sichtbar), Kater-HUD (Leber-Balkenbreite = `leber` %, Pegel-Krüge gefüllt = `pegel`, Deckel-Striche), Freispiel-Banner sichtbar bei `freeLeft > 0`, Bankrott-Blackout-Klasse, Goldregen-Partikel bei Gast-des-Hauses.
- Desktop-Gegenprobe: Screenshot-Diff `main` vs. Branch auf `hub`, `roulette`, `slots`, `finance`, `stadt` (ohne Royal-Karte-Unterschied: `stadt` wird mit `?fresh&mode=free` ohne Auto verglichen – die Fassade darf sich ändern, der Rest nicht; der Diff wird deshalb auf die drei oberen Karten beschränkt).
- Screenshots erneuert: `royal-lobby.png`, `royal-mega.png`, `royal-craps.png`, `royal-wheel.png`, `royal-fassade.png`, `kater-hud.png`, `scene-royal.png`, dazu `mobile-royal.png`, `mobile-craps.png`.
- README: Abschnitt „Casino Royal" (Look, Zone, Momente) und Kater-HUD-Beschreibung.

## 11. Umsetzungsreihenfolge

1. Zone + Tokens + Gold-Vorhang + Kopfzeile/Seitenleiste (Fundament, Screenshot-Gegenprobe Keller).
2. Lobby.
3. Mega Seven (inkl. Gewinnlinien, Freispiel-Banner).
4. Craps (inkl. Chip-Marker).
5. Glücksrad (inkl. Segmentfarben, Bankrott-Blackout).
6. Fassade + Türsteher.
7. Kater-HUD + Zitter.
8. Cutscene-Hintergrund, Sylvie-Rahmen, Goldregen, Trophäen-Toast.
9. Tests, Screenshots, README.
