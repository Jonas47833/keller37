# Checkliste: Tisch & Bank (2026-09-17)

Eine Zeile je Anforderung aus `docs/superpowers/specs/2026-09-17-tisch-und-bank-design.md` (§2.1–2.4, §3, §4), mit Nachweis. Node-Selftests laufen über `?selftest` (Namen wie in `keller37.html`, Block `Tisch & Bank`, ab Zeile 5680); Browser-Playtest über `python3 -u tests/playtest-story.py` (Checks in `scenario_roulette_chips`, sofern nicht anders benannt); Screenshots unter `docs/superpowers/screenshots/`.

## §2.1 Datenmodell

| Anforderung | Nachweis |
|---|---|
| `Roulette.bets = [{ type, n, amount }]`, jeder Klick ein eigener Chip (kein Zusammenlegen) | Playtest `roulette: drei Chips liegen, Summe 80` (`stacks == "even:20,n17:10,red:50"` — drei separate Bets, Anzeige summiert pro Feld) |
| `Roulette.lastBets` für „Wie zuletzt" | Playtest `roulette: Wie zuletzt legt dieselben Chips` |
| `undo()` entfernt den zuletzt gelegten Chip | Playtest `roulette: Chip zurueck entfernt den letzten` (`bets: 3 → 2`) |
| `clear()` entfernt alle | Playtest `roulette: Tisch leeren, Drehen gesperrt` (`bets == 0`) |

## §2.2 Bedienung

| Anforderung | Nachweis |
|---|---|
| Einsatzfeld „Chip", Schnellwahl 10/50/100/500/Max | Screenshot `roulette-chips.png`, `roulette.png` (Chip-Buttons 10/50/100/500/MAX sichtbar) |
| Klick legt Chip mit aktuellem Chip-Wert, `.chip-stack` zeigt Feldsumme | Playtest `roulette: drei Chips liegen, Summe 80`; Screenshot `roulette-chips.png` (Marker „10"/„50"/„20" auf den Feldern) |
| Kopfzeile „Auf dem Tisch: X € · Y Chips", Buttons Drehen/↶ Chip zurück/Tisch leeren/Wie zuletzt | Playtest `roulette: drei Chips liegen, Summe 80` (`total` enthält „80 €" und „3 Chips"); Screenshot `roulette-chips.png` (alle vier Buttons in der Kopfzeile) |
| Chip nur legbar, wenn `Rules.checkSpin(s, total+chip).ok`, sonst Toast | Code `Roulette.place()` (`keller37.html:2888-2897`) ruft `Rules.checkSpin` vor jedem Push; Node-Selftests `checkSpin: ungültiger Einsatz`, `checkSpin: zu wenig Geld inkl. Kosten`, `checkSpin: ok` decken die zugrunde liegende Regel ab |
| Drehen deaktiviert ohne Chips | Playtest `roulette: Tisch leeren, Drehen gesperrt` (`disabled=True` bei `bets=0`) |
| Tisch während der Kugel gesperrt | Code `Roulette.spin()` setzt `#rtable` auf `.locked` und `renderBar()` deaktiviert alle vier Buttons, solange `this.spinning` (`keller37.html:2882-2886,2938`); indirekt bestätigt durch Playtest `roulette: Einsatz 60 einmal abgezogen (Escrow)` direkt nach `#btnSpin`-Klick |

## §2.3 Auswertung

| Anforderung | Nachweis |
|---|---|
| `Game.beginSpin(total)` einmal (Escrow: Summe + Zinsen + Meds) | Playtest `roulette: Einsatz 60 einmal abgezogen (Escrow)` (`bal=940` nach einmaligem Abzug von 60 aus 1000) |
| Auszahlung: Zahl 35:1 + Einsatz zurück, Außenfelder 1:1 + Einsatz zurück, Null lässt Außenfelder verlieren | Node-Selftest `rouletteTotal / rouletteSettle: Zahl + Rot + Gerade` (18 → Rot+Gerade treffen, Zahl verliert, `payout=140`; 17 → nur Zahl trifft, `payout=360`; 0 → `payout=0`) |
| Glück wirkt auf genau einen Chip via `Rules.rouletteLuckTarget` (höchster Einsatz, Zahl vor Außenfeld, dann Reihenfolge) | Node-Selftest `rouletteLuckTarget: höchster Einsatz, Zahl vor Außenfeld, dann Reihenfolge` |
| Statuszeile „Rot ✓ +50 · 17 ✗ · Gerade ✓ +50 → +100 €"-Format | Playtest `roulette: 18 -> 17 verliert, Rot gewinnt, netto +40` (`status` enthält „Rot ✓ +50" und „17 ✗") |
| Tisch nach Dreh geleert, `lastBets` gespeichert | Playtest `roulette: Wie zuletzt legt dieselben Chips` (liest `Roulette.lastBets` nach dem Dreh, legt sie erneut) |
| Bus-Event `roulette:result { bets, rolled, payout, hits }` | Code `Roulette.spin()` (`keller37.html:2975`) emittiert `Bus.emit('roulette:result', { bets, rolled, payout, hits, total, win })` |
| Trophäe „Plein" bei Zahl-Treffer | Code `Bus.on('roulette:result', ...)` (`keller37.html:3515`) schaltet `Achievements.unlock('plein')` bei `hits.some(x => x.win && x.bet.type === 'number')` frei — im Szenario trifft der Zahl-Chip auf 17 nicht (Ergebnis 18), daher kein eigener Playtest-Check für diese Trophäe in dieser Task; reine Code-Prüfung |
| Story-Statistik „Verzockt" bekommt Netto-Verlust über `loss` | Code `Bus.on('loss', ...)` (`keller37.html:4213`) addiert `amount` auf `Story.s.stats.gambled`; unverändert aus Vorgänger-Tasks, kein neuer Test nötig |

## §2.4 Reine Regeln

| Anforderung | Nachweis |
|---|---|
| `Rules.rouletteSettle(bets, rolled) → { payout, hits }` | Node-Selftest `rouletteTotal / rouletteSettle: Zahl + Rot + Gerade` (inkl. leerer Tisch `{ payout: 0, hits: [] }`) |
| `Rules.rouletteLuckTarget(bets) → index`, `-1` bei leerem Tisch | Node-Selftest `rouletteLuckTarget: höchster Einsatz, Zahl vor Außenfeld, dann Reihenfolge` (`T.eq(Rules.rouletteLuckTarget([]), -1)`) |
| `Rules.rouletteTotal(bets) → number` | Node-Selftest `rouletteTotal / rouletteSettle: Zahl + Rot + Gerade` (`T.eq(Rules.rouletteTotal(bets), 80)`) |

## §3 Bank und Vito

| Anforderung | Nachweis |
|---|---|
| `Rules.BANK_RATE = 0.08`; Mercedes C/S/G `bankRate` 0.07/0.06/0.05; Limits unverändert (3.000; 4.000/6.000/10.000) | Node-Selftests `INVEST: neue Werte`, `bankInterest: Mercedes-Zinssatz`, `bankLoanAllowed / isGameOver: Mercedes-Limit, beide Quellen zu`; Playtest `stadt: Bank zeigt Mercedes-Konditionen` (Text „7 %" und „4.000") |
| Ein offener Kredit: `Rules.bankLoanAllowed(s, amt)` verlangt `s.bankDebt === 0` | Node-Selftest `bankLoanAllowed: ein Kredit, Limit 3000` |
| Finanz-Raum: Kredit-Knöpfe gesperrt bei offenem Kredit, Hinweis „Erst den Schuldschein tilgen." | Playtest `bank: bei offenem Kredit alle Kredit-Knoepfe gesperrt, Hinweis sichtbar` (`disabled=True`, `hint` enthält „tilgen"); Screenshot `finance.png` (Bank-Karte: `+200 €`/`+500 €`/`+1.000 €` gedimmt/deaktiviert, Hinweiszeile darunter, `TILGEN` aktiv; Vito-Karte unverändert klickbar, da eigene Schuldenquelle) |
| Tilgen bleibt Gesamtsumme (unverändert) | Code `Finance.repayBank()` unverändert aus Vorgänger-Version, kein neuer Test nötig (out of scope dieser Spec) |
| Vito unverändert (1 Zettel, 5 Spins, ×3); Game-Over-Regel geändert (Ruling, siehe Spec §8): Game Over erst wenn `bankDebt > 0 && mafiaDebt > 0 &&` kein 1-€-Spin mehr bezahlbar ist (vorher `bankDebt >= limit`) — mit nur einem Kredit auf einmal wäre die alte Limit-Regel sonst kaum noch erreichbar | Node-Selftests `mafiaBill = 3x`, `isGameOver: beide Quellen zu und kein Spin mehr bezahlbar` |
| Alle „30 %"-Texte dynamisch oder auf 8 % | Node-Selftest `bankInterest: 8 % gerundet`; Playtest `bank: Konditionen 8 %` (`terms` enthält „8 %"); Playtest `stadt: Bank zeigt Mercedes-Konditionen` (Mercedes-Konditionen jetzt „7 %" statt vormals „27 %" — Szenario-Check dieser Task entsprechend angepasst, siehe Report) |

## §4 Anlagen

| Anforderung | Nachweis |
|---|---|
| Katalog-Werte `INVEST.bank/stock/scam` (rate/spins/risk/min) | Node-Selftest `INVEST: neue Werte` |
| Je Sorte eine laufende Anlage: `Rules.canInvest(s, kind, amount) → { ok, reason }` | Node-Selftest `canInvest / investRunning: je Sorte eine, Mindestbetrag, Geld` |
| Karte zeigt bei laufender Anlage „Festgeld · X € · noch N Spins" statt Eingabe | Playtest `anlagen: Festgeld laeuft, Karte zeigt laufende Anlage, Eingabe weg` (`running` enthält „20 €" und „6 Spins", `form_hidden=True`); Screenshot `invest.png` (Karte „Läuft: 20 € · noch 6 Spins") |
| Trickbetrug-Text „Vito legt es für dich an. Frag nicht, wo." | Screenshot `invest.png` (Text unter der Trickbetrug-Karte sichtbar) |
| Alte Spielstände mit mehreren laufenden Anlagen derselben Sorte laufen aus; neu erst ohne laufende | Node-Selftest `canInvest / investRunning: je Sorte eine, Mindestbetrag, Geld` (Zusatzfall „alte Anlage ohne `type` über den Namen erkannt"); Playtest `anlagen: zweites Festgeld abgelehnt` (Kontostand/Anzahl unverändert nach zweitem Versuch) |

## Screenshots erneuert/neu

- `docs/superpowers/screenshots/roulette.png` — erneuert (`?screen=roulette`, neue Tischleiste mit Kopfzeile/Buttons/Chip-Feld verändert das Referenzbild bewusst; Pixel-Diff dagegen schlägt vor der Erneuerung erwartungsgemäß fehl, siehe Report)
- `docs/superpowers/screenshots/finance.png` — erneuert (Hinweiszeile unter den Kredit-Knöpfen bei offenem Kredit)
- `docs/superpowers/screenshots/invest.png` — erneuert (Festgeld-Karte zeigt laufende Anlage „Läuft: …")
- `docs/superpowers/screenshots/roulette-chips.png` — neu (drei Chips auf dem Tisch, Kopfzeile „Auf dem Tisch: 80 € · 3 Chips")

## Playtest-Läufe

- `python3 -u tests/playtest-story.py` (Lauf 1, vor Erneuerung von `roulette.png`): 90 Checks, 1 fehlgeschlagen (`freie sandbox: ?screen=roulette unveraendert` — erwartet, siehe oben), `ERRORS 0`
- `python3 -u tests/playtest-story.py` (Lauf 2, nach Erneuerung): 90 Checks, 0 fehlgeschlagen, `ERRORS 0`
- `python3 -u tests/playtest-story.py --mobile`: 90 Checks, 0 fehlgeschlagen, `ERRORS 0`
