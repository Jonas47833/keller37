# Checkliste: Stadt & Überfall (Spec `2026-09-16-stadt-und-ueberfall-design.md`)

Eine Zeile je Spec-Anforderung aus §2.2, §2.4, §3, §4, §4.5, §6. Nachweis = Node-Selftest-Name
(`node tests/run-selftest.mjs`, `T.test('…')` in `keller37.html`), Browser-Playtest-Check-Name
(`python3 tests/playtest-story.py`, `record('…')`) oder Screenshot unter
`docs/superpowers/screenshots/`. „Lücke" markiert Anforderungen ohne automatisierten Nachweis
(Code wurde gelesen, aber nicht durch einen Test/Screenshot in diesem Repo belegt).

## §2.2 Katalog `Rules.GEAR`

| Anforderung | Nachweis |
|---|---|
| Preise steigen je Linie (Audi/Mercedes), Glück ≤ 4, Zinsen sinken mit Stufe | Node: `GEAR: Preise steigen je Linie, Glück ≤ 4, Zinsen sinken` |
| Neutrale Defaults ohne Ausrüstung (`mugMult:1`, `flee:0`, `luck:0`, `bankLimit`/`bankRate` = Basiswerte, `postTime/postPay/spuelerBand/taxiTip:0`) | Node: `gear: ohne Ausrüstung neutral` |
| Kombinierte Boni (Audi R8 + Carbon-Sprinter; Mercedes G) | Node: `gear: Audi R8 + Carbon`, `gear: Mercedes G` |
| `TRADE_IN` 0,5 in `carUpgradeCost`/`canBuyCar` (Linie + Markenwechsel, kein Downgrade, kein Geld zurück) | Node: `carUpgradeCost / canBuyCar`; Browser: `stadt: A3 gekauft`, `stadt: RS 4 zeigt Upgrade-Preis mit Inzahlungnahme`, `stadt: Markenwechsel A3 -> C-Klasse kostet 1.250` |
| `canBuyShoes` nur Aufstieg, Sprung erlaubt, voller Preis | Node: `canBuyShoes: nur Aufstieg, Sprung erlaubt, voller Preis`; Browser: `stadt: Trail-Runner gekauft` |
| Katalog im Screen sichtbar (Icon/Name/Preis/Boni-Stichpunkte je 3 Karten × 3 Schaufenster) | Screenshot: `stadt-arm.png`, `stadt-a3.png` |

## §2.4 Hooks in bestehenden Regeln

| Anforderung | Nachweis |
|---|---|
| `Rules.luck(s)` `+ gear.luck` | Node: `luck: Auto-Glück addiert sich` |
| `Rules.bankInterest(debt, s)` nutzt `gear.bankRate` | Node: `bankInterest: Mercedes-Zinssatz`; Browser: `stadt: Bank zeigt Mercedes-Konditionen` |
| `Rules.bankLoanAllowed(s, amt)` nutzt `gear.bankLimit` | Node: `bankLoanAllowed / isGameOver: Mercedes-Limit` |
| `Rules.postmanTier(streak, s)` `+ gear.postTime/postPay` | Node: `postmanTier: Schuhe geben Zeit und Lohn` |
| Spüler-Timing-Band `+ gear.spuelerBand` | Node: `gear: Audi R8 + Carbon` (Wert `spuelerBand: 0.2`); **Lücke**: kein Browser-Check, der die tatsächlich breitere Zone im Spüler-Minispiel misst (nur die reduced-motion-Variante ohne Schuhe wird geprüft: `reduced-motion: Spueler-Zone bleibt 30% (kein Schrumpfen)`) |
| Taxi `+ gear.taxiTip`, `StoryRules.taxiPay(p, t, tip)` | Node: `taxiPay mit Trinkgeld, tuerBonus-Deckel` |
| Türsteher-Schicht `+ min(50, 10 × strength)`, Toast nennt Bonus | Node: `taxiPay mit Trinkgeld, tuerBonus-Deckel` (`StoryRules.tuerBonus`); **Lücke**: kein Test prüft den Toast-Text im Browser (nur dass die Türsteher-Szenen laufen: `schicht-karten tuersteher: alle 3 Szenen gesehen`) |
| Finanz-Raum zeigt `gear.bankLimit`/`gear.bankRate` | Browser: `stadt: Bank zeigt Mercedes-Konditionen` |

## §3 Screen „Stadt"

| Anforderung | Nachweis |
|---|---|
| Hub-Tür „Stadt" 🏙️, `data-screen="stadt"`, Chalk-Tag „Autohaus · INTERSPORT" | Screenshot: `hub.png` (erneuert, siehe unten) |
| Story: `stadt` als Raum, verdeckt bis freigeschaltet, offen morgens **und** abends, Kauf kostet keinen Tag | Node: `StoryRules.validate: Räume` (akzeptiert `stadt`); Browser: `story: Tag 4 schaltet stadt frei`, `story: Seitenleiste zeigt Stadt-Knopf` |
| Story 1 „Die Schuld": Event `stadtOffen` Tag 4 (once), Szene `schuld.stadt`, Effekt unlockt `rooms:['stadt']` | Node: `Story Schuld: stadtOffen an Tag 4, Eintreiber mit Türsteher freigeschaltet`; Browser: `story: Tag 4 schaltet stadt frei`; Screenshot: `stadt-story-tag4.png` |
| Drei Schaufenster nebeneinander bei 1280 px | Screenshot: `stadt-arm.png`, `stadt-a3.png` (1280×900 Desktop-Viewport) |
| Schaufenster untereinander unter 760 px | **Lücke**: kein Screenshot der Stadt bei 400 px in diesem Task (Brief listet dafür keine Datei); `scenario_mobile` prüft nur Pinnwand/Abend-Hub auf horizontales Scrollen, nicht `?screen=stadt` |
| Karte: Icon/Name/Preis/Boni als Stichpunkte, Buttons „Kaufen"/„Upgrade"/„Deins"/deaktiviert | Screenshot: `stadt-arm.png` (deaktiviert, „Zu wenig Bargeld"), `stadt-a3.png` (. „Deins", „Upgrade · 7.250 €", „Kaufen · …") |
| Verkäufer-Zeile je Zustand (kein Auto / gleiche Marke / andere Marke / Sport) | Screenshot: `stadt-arm.png` („Zu Fuß gekommen? Mutig."), `stadt-a3.png` („Schön, dass du wieder da bist." / „Der Wechsel lohnt sich. Sagen alle." / „Für Leute, die es eilig haben.") |
| Kaufablauf: Bestätigungspanel bei Inzahlungnahme/Markenwechsel, Cutscene 2 Panels, `Game.applyDelta`, kein Kauf während `Cutscene.active`/`Game.inFlight` | Browser: `stadt: Markenwechsel A3 -> C-Klasse kostet 1.250`, `stadt: Abbruch laesst Auto unveraendert` |
| Seitenleiste Besitz-Zeile `🚗 … · 👟 … · 💪 …`, fehlende Teile weggelassen, „Zu Fuß · 💪 0" ohne Ausrüstung | Node: `State.fresh: Gear-Felder` (Defaults `car:null, shoes:null, strength:0`); Browser: `stadt: Seitenleiste zeigt Besitz` |

## §4 Überfall

| Anforderung | Nachweis |
|---|---|
| Auslöser freies Spiel: `UI.show(screen)` beim Wechsel `hub` → Casino-Tür | Browser: `mug: Szene erscheint beim Tuerwechsel` |
| Auslöser Story: `Story.evening()` vor `UI.show('hub')` | Browser: `story: Ueberfall am Abend` |
| Kein Überfall bei `Cutscene.active`/`Game.inFlight`/`gameOverPending`/`Story.sleeping` | Code-Review `Mugging.blocked()` (Zeile ~3419); kein dedizierter Test in diesem Task – indirekt dadurch belegt, dass in allen anderen Szenarien (Cutscenes, Spins) nie ungewollt ein Überfall dazwischenfunkt (`ERRORS 0` über den gesamten Lauf) |
| `Rules.mugChance`: Schwellen (Bargeld < 100, Cooldown, Spins < 10 frei, Tag < 4 Story), ×2 ab 2.000 €, Audi-Multiplikator, Abend-Basis 0,12 | Node: `mugChance: Schwellen`, `mugChance: Abend in der Story` |
| Cooldown 15 Spins (frei) / 3 Tage (Story), Countdown in `afterSpin`/`advanceDay` | Node: `advanceDay: Überfall-Cooldown sinkt pro Tag`; Browser: `mug: Zahlen kostet 200 und fuehrt zu den Slots` (`cd == 15` nach Überfall), `story: Cooldown 3 Tage, Abend erreicht` (`cd == 3`); **Lücke**: kein Test lässt im freien Spiel tatsächlich einen Spin laufen, um das Herunterzählen von `mugCooldown` in `Game.afterSpin` selbst zu beobachten (nur der gesetzte Startwert nach dem Überfall ist geprüft; `afterSpin` ist DOM-abhängig und läuft nicht im Node-Selftest-Harness mit) |
| `Rules.mugLoot(balance)`: 20 %, geklemmt 50–1500, nie mehr als Bargeld | Node: `mugLoot: 20 %, 50–1500, nie mehr als Bargeld`; Browser: `mug: Zahlen kostet 200 und fuehrt zu den Slots` (200 € bei 1.000 € Bargeld) |
| Drei Räubertypen (junkie/jugend/cousin) per `?mug=`, Cutscene `gasse` mit drei Choices + Prozentwerten | Browser: `mug: Szene erscheint beim Tuerwechsel` (`?mug=junkie`), `mug: Kampf mit Staerke 20 gewonnen…` (`?mug=cousin`), `mug: Flucht laesst Staerke unveraendert…` (`?mug=jugend`); Screenshot: `mug-intro.png` (Choice-Panel mit „💪 Kämpfen (35 %)" / „👟 Wegrennen (30 %)" / „💸 Zahlen (200 €)") |
| Kämpfen: `fightChance`, Sieg ohne Verlust + Stärke+1 + ggf. Brieftasche ab Stärke 5, Niederlage `-loot` + Stärke+1 | Node: `fightChance / fleeChance / Deckel`, `mugWallet: 50–150`; Browser: `mug: Kampf mit Staerke 20 gewonnen, Brieftasche 50-150, Staerke 21`; Screenshot: `mug-fight.png` |
| Wegrennen: `fleeChance`, Erfolg ohne Verlust, Misserfolg `-loot - 10 % Bargeld`, keine Stärke | Node: `fightChance / fleeChance / Deckel`; Browser: `mug: Flucht laesst Staerke unveraendert, Kontostand 1000 (gelungen) oder 700 (erwischt)` |
| Zahlen: `-loot`, keine Stärke | Browser: `mug: Zahlen kostet 200 und fuehrt zu den Slots` |
| `stats.muggings`/Cooldown/`State.save()` nach jedem Ausgang, danach Raumwechsel bzw. Abend | Browser: `mug: Zahlen kostet 200 und fuehrt zu den Slots` (`screen == "slots"`) |
| Dev-Parameter `?mug=1` (Chance 1) und `?mug=junkie\|jugend\|cousin` (Typ), wirkt auch im Cooldown | Browser: `mug: ?mug erzwingt auch im Cooldown (Dev), Szene laeuft` |

## §4.5 Stärke außerhalb des Kampfs

| Anforderung | Nachweis |
|---|---|
| Türsteher-Bonus `min(50, 10 × strength)` | Node: `taxiPay mit Trinkgeld, tuerBonus-Deckel` (`StoryRules.tuerBonus`) |
| Eintreiber-Job (Stärke ≥ 4, `requireText: 'Stärke 4'`), gemeinsam mit Türsteher-Event freigeschaltet, zwei Szenen mit `jobEffects` `ruf +1` | Node: `jobAvailable: Eintreiber braucht Stärke 4`, `Story Schuld: stadtOffen an Tag 4, Eintreiber mit Türsteher freigeschaltet`; Browser: `story: Eintreiber bei Staerke 3 gesperrt`, `story: Eintreiber bei Staerke 4 offen`; Screenshot: `stadt-story-eintreiber.png` |
| Freies Spiel: Igor-Begrüßung ab Stärke 8 mit Respekt-Zeile | **Lücke**: Code vorhanden (`Cutscene.define('igor.first', …)`, Zeile ~3111–3115, Bedingung `Rules.MUG.STR_RESPECT`), aber kein Node- oder Browser-Test in diesem oder einem vorherigen Task prüft die Zusatzzeile |
| Trophäen `strassenkaempfer` (5 Kämpfe gewonnen), `vollausgestattet` (Top-Auto Stufe 3 + Carbon-Sprinter) | Definitionen sichtbar in `trophaeen-button: Trophaeenwand gerendert` (Trophäenwand enthält beide Einträge, `count=21`); **Lücke**: kein Test lässt tatsächlich 5 Überfälle gewinnen oder Top-Auto+Carbon kombinieren, um `Achievements.unlock('strassenkaempfer'|'vollausgestattet')` selbst auszulösen |

## §6 Tests

### 6.1 Node-Selftest (`node tests/run-selftest.mjs`)

| Anforderung | Nachweis |
|---|---|
| Katalog: Preise je Linie, Glück ≤ 4, Flucht-Summe ≤ 80, Zinsen sinken | Node: `GEAR: Preise steigen je Linie, Glück ≤ 4, Zinsen sinken` |
| `Rules.gear`: neutral ohne Ausrüstung, R8+Carbon, Mercedes G, Stärke 10 halbiert `mugMult` | Node: `gear: ohne Ausrüstung neutral`, `gear: Audi R8 + Carbon`, `gear: Mercedes G`, `gear: Stärke 10 halbiert mugMult` |
| `carUpgradeCost`: kein Auto/A3→RS4/A3→C-Klasse/RS4→A3 (Downgrade) | Node: `carUpgradeCost / canBuyCar` |
| `canBuyShoes`: Basic→Carbon (Sprung), Carbon→Trail (Downgrade) | Node: `canBuyShoes: nur Aufstieg, Sprung erlaubt, voller Preis` |
| `luck`, `bankLoanAllowed`, `bankInterest`, `postmanTier` mit/ohne Ausrüstung | Node: `luck: Auto-Glück addiert sich`, `bankInterest: Mercedes-Zinssatz`, `bankLoanAllowed / isGameOver: Mercedes-Limit`, `postmanTier: Schuhe geben Zeit und Lohn` |
| `mugChance`: <100 €, Cooldown, Spins<10, Story-Tag<4, ≥2000 € verdoppelt, Audi-Multiplikator, Abend-Basis 0,12 | Node: `mugChance: Schwellen`, `mugChance: Abend in der Story` |
| `mugLoot`: 100→50, 10.000→1.500, 60→50, 30→30 | Node: `mugLoot: 20 %, 50–1500, nie mehr als Bargeld` |
| `fightChance(0)=0.35`, `fightChance(7)=0.9`, `fleeChance`-Deckel 0,9 | Node: `fightChance / fleeChance / Deckel` |
| `StoryRules.check` mit `strength`; `validate` akzeptiert Raum `stadt` und Job `eintreiber`; `jobAvailable` Eintreiber Stärke 3/4 | Node: `StoryRules.check: strength`, `StoryRules.validate: Räume`, `jobAvailable: Eintreiber braucht Stärke 4` |
| Tick-Regeln: `afterSpin` senkt `mugCooldown`; `advanceDay` senkt ihn in der Story | Node: `advanceDay: Überfall-Cooldown sinkt pro Tag` für die Story-Seite; **Lücke**: `afterSpin` ist Teil des DOM-abhängigen `game-core`-Blocks und läuft nicht im Node-Selftest-Harness (`tests/run-selftest.mjs` lädt nur `rules, gear-rules, util, state, bus, story-rules, story-probe, story-schuld, selftest`) – siehe Browser-Lücke oben unter §4 |
| Node-Selftest insgesamt grün | `node tests/run-selftest.mjs` → „107 bestanden, 0 fehlgeschlagen" |

### 6.2 Browser-Playtest (`tests/playtest-story.py`, headless Chrome, 1280 und 400 px)

| Anforderung | Nachweis |
|---|---|
| Stadt öffnen, Kauf mit zu wenig Geld: Button deaktiviert, Kontostand unverändert | Browser: `stadt: ohne Geld kein Kaufen-Button`; Screenshot `stadt-arm.png` |
| A3 kaufen → Upgrade RS 4 (Kosten mit Inzahlungnahme) → Markenwechsel C-Klasse mit Bestätigung → Abbruch lässt Auto unverändert | Browser: `stadt: A3 gekauft`, `stadt: RS 4 zeigt Upgrade-Preis mit Inzahlungnahme`, `stadt: Abbruch laesst Auto unveraendert`, `stadt: Markenwechsel A3 -> C-Klasse kostet 1.250`; Screenshot `stadt-a3.png` |
| Seitenleiste zeigt Besitz und Stärke | Browser: `stadt: Seitenleiste zeigt Besitz` |
| `?mug=1`/Typ: alle drei Ausgänge je einmal (Kampf Stärke 20, Zahlen, Flucht), Kontostand/Stärke wie erwartet, danach im gewählten Raum | Browser: `mug: Zahlen kostet 200 und fuehrt zu den Slots`, `mug: Kampf mit Staerke 20 gewonnen, Brieftasche 50-150, Staerke 21`, `mug: Flucht laesst Staerke unveraendert, Kontostand 1000 (gelungen) oder 700 (erwischt)`, `mug: ?mug erzwingt auch im Cooldown (Dev), Szene laeuft` |
| Story: Tag-4-Morgen-Event schaltet Stadt frei; Eintreiber-Karte erst ab Stärke 4; Türsteher-Toast nennt Bonus | Browser: `story: Tag 4 schaltet stadt frei`, `story: Seitenleiste zeigt Stadt-Knopf`, `story: Eintreiber bei Staerke 3 gesperrt`, `story: Eintreiber bei Staerke 4 offen`; **Lücke**: Türsteher-Toast-Text nicht separat geprüft (siehe §2.4) |
| Screenshots `stadt-*.png`, `mug-*.png` | `docs/superpowers/screenshots/stadt-arm.png`, `stadt-a3.png`, `stadt-story-tag4.png`, `stadt-story-eintreiber.png`, `mug-intro.png`, `mug-fight.png` |
| Playtest insgesamt grün (Desktop + `--mobile`) | `python3 tests/playtest-story.py` → „Checks: 74, davon fehlgeschlagen: 0" / „ERRORS 0"; `python3 tests/playtest-story.py --mobile` → gleiches Ergebnis |

## Referenz-Screenshot erneuert

`docs/superpowers/screenshots/hub.png` wurde bewusst überschrieben (vorher ohne, jetzt mit der
„Stadt"-Tür und dem neuen Seitenleisten-Abschnitt „Stadt"/`#gearLine`) – vor dem Commit visuell
gegenübergestellt (altes vs. neues Bild) und geprüft, dass der einzige Unterschied die neue Tür,
das Seitenleisten-Feld und ein kleiner Trophäen-Icon-Zusatz im Kopfbereich sind, keine
unbeabsichtigte Regression. Der Pixel-Diff-Check `freie sandbox: ?screen=hub unveraendert
(Pixel-Diff < 2%)` lief vor der Erneuerung mit `FAIL` (5,85 % Abweichung durch die neue Tür) und
nach der Erneuerung mit `OK` (0,00 % Abweichung).
