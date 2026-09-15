# KELLER 37

Ein satirisches Casino-Lebenssimulations-Spiel in einer einzigen HTML-Datei. Fünfzig Euro in der Tasche, sechs Türen, ein Wirt, der alles schon gesehen hat – und Chantal-Monique, Don Vito und der Doc warten auch schon.

**Spielen:** `keller37.html` doppelklicken. Keine Installation, kein Build. Läuft offline (Google Fonts sind optional).

## Was drin ist

- **Sechs Spiele:** Roulette mit Setztisch und laufender Kugel, Slots mit echten Walzen, Pferderennen mit Live-Kommentar, Russisches Roulette gegen Igor, Blackjack am Filztisch, Post austragen als ehrlicher Ausweg.
- **Leben:** Villa kaufen, auf Tinder Chantal-Monique heiraten, geschieden werden, Therapie zahlen, einen Dealer anheuern. Bier und Brownies an der Bar. Eine Niere fürs Hinterzimmer.
- **Kredite:** Bank (30 % Zinsen pro Spin, Limit 3.000 €) oder Don Vito (5 Spins Frist, danach der Doc).
- **Cutscenes:** 19 Visual-Novel-Szenen mit elf Charakteren, Typewriter-Text, Entscheidungen und Effekten.
- **Extras:** synthetisierter Sound (Web Audio, keine Dateien), Spielstand in `localStorage`, Game Over mit Statistik, zwölf Trophäen, Mobile-Layout, Reduced-Motion.

## Dev-Parameter

| URL-Zusatz | Wirkung |
|---|---|
| `?fresh` | Spielstand löschen und neu starten |
| `?screen=slots` | direkt einen Screen öffnen (`roulette`, `slots`, `horses`, `russian`, `blackjack`, `postman`, `finance`, `invest`, `life`) |
| `?scene=divorce` | eine Szene abspielen |
| `?selftest` | Regel-Selbsttest im Browser (Ergebnis als Toast und in der Konsole) |

## Tests

```sh
node tests/run-selftest.mjs      # 57 Regel-Tests unter Node
tests/dom-selftest.sh            # derselbe Selbsttest headless in Chrome (macOS)
tests/screenshot.sh out.png "?screen=roulette"
```

`Gamble Game.html` ist das Original, aus dem die Mechanik 1:1 übernommen wurde. Spec, Plan, Abnahme-Checkliste und Screenshots liegen unter `docs/superpowers/`.
