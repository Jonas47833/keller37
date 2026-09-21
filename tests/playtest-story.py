#!/usr/bin/env python3
"""
CDP-Playtest für den Story-Modus (Keller 37).

Startet einen echten Headless-Chrome (--headless=new --remote-debugging-port=9335),
fährt die in Task-9-Brief/Spec §13 beschriebene Sequenz (Titel -> Story -> Intro ->
Pinnwand -> Spüler -> Abend-Hub mit Sperren -> Vitos Tisch -> Schlafen -> Tag 2 ->
Post-Schicht -> Nacht-Ereignisse -> Kapitel -> Taxi -> Kontrolle/Duell -> alle vier
Enden -> Titel -> freies Spiel, dazu Ein-Job-pro-Tag ohne Feierabend-Klick) und sammelt dabei
Konsolenfehler/Exceptions. Story 2 „Der Kater" (scenario_kater): Sperre ohne Story-1-Ende,
Intro-Variante, Absturz, Freibier/Deckel, Zitter-Tag samt Royal-Sperre, Bett-Ende aus dem
sleep-Hook mit sauberem Start der Folgestory, Kauf-Ende aus einer Szenen-Wahl.

Wo die Spec ausdrücklich "mit gesetzten Variablen" (§13) vorschreibt, werden
Story-Felder direkt über Runtime.evaluate gesetzt und dann echte Engine-Methoden
(`Story.night()`, `Jobs.runShift()`, ...) aufgerufen -- kein Bypass der Engine,
nur ein Abkürzen des Weges dorthin (wie im Sandbox-Playtest vom 2026-09-15).
Cutscenes werden über echte Klicks auf die gerenderten DOM-Buttons durchgeklickt.

Nutzung:
    python3 tests/playtest-story.py [--mobile]

Screenshots landen in /tmp/k37story/. Am Ende wird "ERRORS n" ausgegeben.
"""
import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

import websockets

try:
    from PIL import Image, ImageChops
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

PORT = int(os.environ.get("K37_PORT", "9335"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "keller37.html")
URL_BASE = "file://" + HTML
SHOT_DIR = os.environ.get("K37_SHOTS", "/tmp/k37story")
CHROME_CANDIDATES = [
    os.environ.get("K37_CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    os.path.expanduser("~/.local/opt/chrome-linux64/chrome"),
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

MOBILE = "--mobile" in sys.argv

os.makedirs(SHOT_DIR, exist_ok=True)


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    raise SystemExit("Kein Chrome gefunden")


PAGE_HELPERS = r"""
window.__pt = window.__pt || {};
__pt.advance = function(labelHint) {
  if (typeof Cutscene === 'undefined' || !Cutscene.active) return false;
  const choices = document.querySelectorAll('.cs-choices button');
  if (choices.length) {
    let btn = choices[0];
    if (labelHint) { for (const b of choices) if (b.textContent.includes(labelHint)) { btn = b; break; } }
    btn.click();
  } else {
    const stage = document.querySelector('#cutscene');
    if (stage) stage.click();
  }
  return true;
};
__pt.cutsceneActive = function() { return typeof Cutscene !== 'undefined' && Cutscene.active; };
__pt.duelShoot = function() {
  // Schuss auf die Gegnerfigur (Ego-Duell): Tipp in die Mitte der Figuren-Box
  const b = DuelStage.foeBox(), R = document.querySelector('#duelStage').getBoundingClientRect();
  Shootout.shoot({ clientX: R.left + b.left + b.width / 2, clientY: R.top + b.top + b.height / 2, pointerType: 'mouse' });
  return true;
};
__pt.autoplaySpueler = function(mode) {
  // mode: 'win' (immer treffen) oder 'loss' (immer verfehlen)
  return new Promise((resolve) => {
    const iv = setInterval(() => {
      if (!Spueler.running) { clearInterval(iv); resolve({ hits: Spueler.hits, breaks: Spueler.breaks }); return; }
      if (mode === 'loss') { return; } // nie tappen -> jeder Teller faellt runter (Miss)
      const inZone = Math.abs(Spueler.pos - Spueler.zone.c) <= Spueler.zone.w / 2;
      if (inZone) Spueler.tap();
    }, 15);
  });
};
__pt.autoplayTaxi = function(mode) {
  // faehrt aktiv Spuren/Bremse (win) oder tut nichts (loss: nur Strafzettel)
  return new Promise((resolve) => {
    const iv = setInterval(() => {
      if (!Taxi.running) { clearInterval(iv); resolve({ passengers: Taxi.passengers, tickets: Taxi.tickets }); return; }
      if (mode === 'loss') return;
      const road = document.querySelector('#taxiRoad');
      if (!road) return;
      const H = road.clientHeight; const carY = H - 20 - 44;
      for (const e of Taxi.entities) {
        if (e.done) continue;
        if (e.y > carY - 140 && e.y < carY + 10) {
          if (e.kind === 'rider') { if (e.lane !== Taxi.laneIdx) Taxi.lane(e.lane > Taxi.laneIdx ? 1 : -1); }
          else { Taxi.brake(); }
          break;
        }
      }
    }, 40);
  });
};
true;
"""


class CDP:
    def __init__(self):
        self.proc = None
        self.ws = None
        self._id = 0
        self.pending = {}
        self.console_errors = []
        self._listen_task = None

    def launch(self, mobile=False):
        profile = os.environ.get("K37_PROFILE", "/tmp/k37story-profile")
        subprocess.run(["rm", "-rf", profile])
        self.profile = profile  # wird in close() wieder geloescht -- ein Chrome-Profil sind ~140 MB
        args = [
            find_chrome(),
            "--headless=new",
            "--disable-gpu",
            "--remote-debugging-port=%d" % PORT,
            "--user-data-dir=%s" % profile,
            "--no-first-run",
            "--hide-scrollbars",
            "--window-size=1280,900",
        ]
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/json/version" % PORT, timeout=0.3)
                return
            except Exception:
                time.sleep(0.15)
        raise SystemExit("Chrome CDP nicht erreichbar")

    async def connect(self):
        req = urllib.request.Request("http://127.0.0.1:%d/json/new?about:blank" % PORT, method="PUT")
        info = json.load(urllib.request.urlopen(req))
        ws_url = info["webSocketDebuggerUrl"]
        self.ws = await websockets.connect(ws_url, max_size=None, ping_interval=None)
        self._listen_task = asyncio.create_task(self._listen())
        await self.send("Page.enable")
        await self.send("Runtime.enable")
        await self.send("Log.enable")

    async def _listen(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                if "id" in msg:
                    fut = self.pending.pop(msg["id"], None)
                    if fut and not fut.done():
                        fut.set_result(msg)
                else:
                    await self._on_event(msg)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def _on_event(self, msg):
        method = msg.get("method")
        params = msg.get("params", {})
        if method == "Runtime.consoleAPICalled" and params.get("type") == "error":
            parts = []
            for a in params.get("args", []):
                parts.append(str(a.get("value", a.get("description", ""))))
            self.console_errors.append("console.error: " + " ".join(parts))
        elif method == "Runtime.exceptionThrown":
            d = params.get("exceptionDetails", {})
            text = d.get("text", "")
            exc = d.get("exception", {}) or {}
            desc = exc.get("description", exc.get("value", ""))
            self.console_errors.append("exception: %s %s" % (text, desc))

    async def send(self, method, params=None, timeout=30):
        self._id += 1
        mid = self._id
        fut = asyncio.get_event_loop().create_future()
        self.pending[mid] = fut
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            print("TIMEOUT waiting for", method, params, file=sys.stderr)
            return {}

    async def navigate(self, url, wait=1.2):
        await self.send("Page.navigate", {"url": url})
        await asyncio.sleep(wait)

    async def eval(self, expr, await_promise=True, timeout=30):
        r = await self.send(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
            timeout=timeout,
        )
        result = r.get("result", {})
        if result.get("exceptionDetails"):
            self.console_errors.append("eval-exception: %s" % json.dumps(result["exceptionDetails"])[:400])
        return result.get("result", {}).get("value")

    async def inject_helpers(self):
        await self.eval(PAGE_HELPERS, await_promise=False)

    async def click(self, selector):
        return await self.eval(
            "(function(){var el=document.querySelector(%s); if(!el) return false; el.click(); return true;})()" % json.dumps(selector),
            await_promise=False,
        )

    async def click_all_first(self, selector):
        return await self.eval(
            "(function(){var els=document.querySelectorAll(%s); if(!els.length) return false; els[0].click(); return true;})()" % json.dumps(selector),
            await_promise=False,
        )

    async def screenshot(self, name):
        r = await self.send("Page.captureScreenshot", {"format": "png"})
        data = r.get("result", {}).get("data")
        if not data:
            print("!! Screenshot fehlgeschlagen:", name)
            return None
        path = os.path.join(SHOT_DIR, name)
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print("screenshot:", path)
        return path

    async def set_mobile(self, on=True):
        if on:
            await self.send("Emulation.setDeviceMetricsOverride", {
                "width": 400, "height": 800, "deviceScaleFactor": 2, "mobile": True,
            })
        else:
            await self.send("Emulation.clearDeviceMetricsOverride")

    async def set_reduced_motion(self, on=True):
        await self.send("Emulation.setEmulatedMedia", {
            "features": [{"name": "prefers-reduced-motion", "value": "reduce" if on else "no-preference"}],
        })

    async def advance_cutscene(self, max_steps=60, label_hint=None, step_wait=0.12):
        steps = 0
        while steps < max_steps:
            active = await self.eval("__pt.cutsceneActive()", await_promise=False)
            if not active:
                return steps
            await self.eval("__pt.advance(%s)" % (json.dumps(label_hint) if label_hint else "null"), await_promise=False)
            await asyncio.sleep(step_wait)
            steps += 1
        return steps

    async def wait_for(self, js_expr, timeout=3.0, interval=0.1):
        """Pollt js_expr, bis es truthy ist oder das Timeout erreicht ist. Wird benutzt, um
        auf das Ende einer fire-and-forget-gestarteten async Engine-Methode (Story.morning(),
        UI.show(), ...) zu warten, statt eine feste Sleep-Dauer zu raten (Quelle der meisten
        Race-Conditions in einer ersten Fassung dieses Skripts: ein fixer sleep(0.3) reichte
        nicht immer, wenn UI.show() noch mit dem vorherigen Screen-Wechsel beschaeftigt war)."""
        elapsed = 0.0
        while elapsed < timeout:
            v = await self.eval(js_expr, await_promise=False)
            if v:
                return v
            await asyncio.sleep(interval)
            elapsed += interval
        return await self.eval(js_expr, await_promise=False)

    async def close(self):
        try:
            await self.ws.close()
        except Exception:
            pass
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
        if getattr(self, "profile", None):
            shutil.rmtree(self.profile, ignore_errors=True)  # Chrome-Profil aufraeumen (sonst sammeln sich GBs in /tmp)


RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(("OK  " if ok else "FAIL"), name, "-", detail)


def compare_screenshots(ref_path, new_path, luminance_threshold=10):
    """Vergleicht zwei PNGs pixelweise und gibt (changed_pct, detail) zurueck.

    Beide Bilder werden auf ihre gemeinsame Breite/Hoehe zugeschnitten (Page.captureScreenshot
    liefert die tatsaechliche Viewport-Hoehe, waehrend die Referenzbilder per CLI-Screenshot mit
    festem --window-size aufgenommen wurden -- ein reiner Aufnahme-Unterschied, kein Layout-Diff).
    Ein Pixel gilt als "veraendert", wenn die Luminanz-Differenz > luminance_threshold ist (klein
    genug, um echte Inhaltsaenderungen zu erfassen, aber grob genug, um Anti-Aliasing-Rauschen und
    minimale Kompressionsartefakte zu ignorieren). Ohne Pillow (sollte in dieser Umgebung nicht
    vorkommen, siehe Header-Kommentar) faellt die Funktion auf einen reinen Dateigroessen-Vergleich
    zurueck -- deutlich als Notloesung im detail-String markiert.
    """
    if not HAVE_PIL:
        size_ref = os.path.getsize(ref_path)
        size_new = os.path.getsize(new_path)
        pct = 100.0 * abs(size_ref - size_new) / max(size_ref, 1)
        return pct, "PILLOW FEHLT -- nur Dateigroessen-Vergleich (ref=%d new=%d bytes)" % (size_ref, size_new)
    a = Image.open(ref_path).convert("RGB")
    b = Image.open(new_path).convert("RGB")
    w = min(a.size[0], b.size[0])
    h = min(a.size[1], b.size[1])
    a2 = a.crop((0, 0, w, h))
    b2 = b.crop((0, 0, w, h))
    diff_l = ImageChops.difference(a2, b2).convert("L")
    hist = diff_l.histogram()
    changed = sum(hist[luminance_threshold + 1:])
    total = w * h
    pct = 100.0 * changed / total if total else 0.0
    return pct, "ref=%s neu=%s zugeschnitten=%dx%d veraenderte_px=%d/%d (%.2f%%)" % (a.size, b.size, w, h, changed, total, pct)


async def scenario_title_and_intro(cdp):
    """Titel -> Story -> Intro (mid-typing) -> Pinnwand."""
    await cdp.navigate(URL_BASE + "?fresh")
    await asyncio.sleep(0.6)
    await cdp.inject_helpers()
    hidden = await cdp.eval("document.querySelector('#title').hidden", await_promise=False)
    record("title: Titelscreen sichtbar nach Boot", hidden is False, "hidden=%s" % hidden)
    await cdp.screenshot("story-title.png")

    await cdp.click(".title-door[data-choice='story']")
    await asyncio.sleep(0.35)
    active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("intro: Cutscene startet nach Tuerwahl", bool(active), "active=%s" % active)
    await cdp.screenshot("story-intro-mid-typing.png")

    steps = await cdp.advance_cutscene(max_steps=20)
    record("intro: 4 Panels durchgeklickt", steps > 0, "steps=%s" % steps)
    await asyncio.sleep(0.3)

    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("jobs: Screen nach Intro ist Pinnwand", screen == "jobs", "screen=%s" % screen)
    await cdp.screenshot("story-jobs.png")
    notes = await cdp.eval("document.querySelectorAll('#pinboard .jobnote').length", await_promise=False)
    record("jobs: Pinnwand zeigt Zettel", (notes or 0) >= 2, "notes=%s" % notes)


async def scenario_spueler_and_hub(cdp):
    """Spüler-Schicht (Gewinn), Abend-Hub mit Sperren, Vitos Tisch, Schlafen -> Tag 2."""
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)
    await cdp.click_all_first("#pinboard .jobnote:not(.locked):not(.done)")
    await asyncio.sleep(0.4)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("spueler: Job-Screen geladen", screen == "job-spueler", "screen=%s" % screen)
    await cdp.click("#btnDishStart")
    await asyncio.sleep(0.5)
    await cdp.screenshot("story-spueler.png")
    res = await cdp.eval("__pt.autoplaySpueler('win')", timeout=20)
    record("spueler: Schicht gewinnt (hits>breaks)", (res or {}).get("hits", 0) > (res or {}).get("breaks", 0), str(res))
    await cdp.screenshot("story-spueler-result.png")
    await cdp.click("#btnDishDone")
    await asyncio.sleep(0.5)

    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("hub: nach Schicht automatisch Abend-Hub", screen == "hub", "screen=%s" % screen)
    locked = await cdp.eval("document.querySelectorAll('.door.locked').length", await_promise=False)
    record("hub: gesperrte Tueren sichtbar (Bretter)", (locked or 0) >= 1, "locked=%s" % locked)
    await cdp.screenshot("story-hub-locked.png")

    await cdp.eval("UI.show('vito')")
    await asyncio.sleep(0.3)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("vito: Vitos Tisch erreichbar", screen == "vito", "screen=%s" % screen)
    schuld = await cdp.eval("State.s.story.vars.schuld", await_promise=False)
    record("vito: Schuld-Anzeige vorhanden", schuld == 50000, "schuld=%s" % schuld)
    await cdp.screenshot("story-vito.png")
    await cdp.eval("UI.show('hub')")
    await asyncio.sleep(0.2)

    day_before = await cdp.eval("State.s.story.day", await_promise=False)
    await cdp.click("#btnSleep")
    # Story.night() ist fire-and-forget (der Klick-Handler kann nicht awaiten); auf das
    # tatsaechliche Starten warten statt eine feste Sleep-Dauer zu raten, dann noch einmal
    # klicken, falls der erste Klick den Button in einem seltenen Zwischenzustand traf.
    started = await cdp.wait_for("Story.sleeping === true", timeout=1.0)
    if not started:
        await cdp.click("#btnSleep")
        started = await cdp.wait_for("Story.sleeping === true", timeout=1.0)
    await cdp.screenshot("story-night-fade.png")
    for _ in range(20):
        await cdp.advance_cutscene(max_steps=10)
        sleeping = await cdp.eval("Story.sleeping", await_promise=False)
        if not sleeping:
            break
        await asyncio.sleep(0.15)
    day_after = await cdp.eval("State.s.story.day", await_promise=False)
    record("schlafen: Tag erhoeht sich (Nachtblende)", day_after == day_before + 1,
           "%s -> %s (Story.night() gestartet: %s)" % (day_before, day_after, started))


async def scenario_fast_forward(cdp):
    """Post-Schicht (mid), Tag 3 Chantal, Tag 6 Kapitel, Taxi (mid), Tag 10 Kontrolle+Duell."""
    # Dieses Szenario testet Kapitel-/Ereignis-Fortschritt, keine Ueberfaelle: Story.evening()
    # (ueber Jobs.finishGame('taxi') -> Feierabend) wuerfelt ab Tag 4 sonst mit 12 % einen
    # Abend-Ueberfall, dessen offene Cutscene den spaeteren Story.night()-Aufruf fuer Tag 10
    # (Cutscene.active-Guard) verschluckt -- Cooldown weit genug hochsetzen, dass advanceDay()
    # ihn ueber die restlichen Tage dieses Laufs nicht auf 0 zaehlt.
    await cdp.eval("State.s.mugCooldown = 999; State.save();", await_promise=False)
    # Tag 2: Postbote-Schicht anspielen (mid), dann abbrechen -> zurueck zum Hub, Job zaehlt nicht,
    # aber Screen+Timer wurden real gerendert.
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    if screen != "jobs":
        await cdp.eval("Story.morning()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)
    await cdp.click_all_first("#pinboard .jobnote:not(.locked):not(.done)")
    await asyncio.sleep(0.3)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    if screen == "job-spueler":
        # Tag 2 zog wieder Spueler (Zufallsauswahl war nicht noetig -> nur ein Job im Pool);
        # fuer die Postbote-Deckung wird weiter unten Jobs.take('post') direkt genutzt.
        await cdp.eval("Jobs.abort(); UI.show('jobs')")
        await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)
    await cdp.eval("Jobs.take('post')")
    await cdp.wait_for("UI.current && UI.current.id === 'postman'", timeout=3.0)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("post: Postbote-Schicht (mid) erreichbar", screen == "postman", "screen=%s" % screen)
    await cdp.click("#btnShift")
    await asyncio.sleep(0.5)
    await cdp.screenshot("story-post-mid.png")
    await cdp.eval("Jobs.abort(); UI.show('hub')")
    await asyncio.sleep(0.3)

    # Tag-3-Ereignis (Chantal): Story.night() wertet die 'night'-Ereignisse fuer den AKTUELLEN
    # Tag aus, bevor er hochgezaehlt wird -> Tag direkt auf 3 setzen und genau einmal schlafen
    # (ein Off-by-one mit einer Zwei-Naechte-Schleife ab Tag 1 hier landete faelschlich bei
    # Tag 3, ohne dass die Nacht fuer Tag 3 je lief).
    await cdp.eval("State.s.story.day = 3; State.s.story.phase='evening'; State.save();")
    await cdp.eval("Story.night()", await_promise=False)
    for _ in range(20):
        await cdp.advance_cutscene(max_steps=10)
        phase = await cdp.wait_for("State.s.story.phase", timeout=0.3)
        if phase == "morning":
            break
        await asyncio.sleep(0.15)
    seen_events = await cdp.eval("State.s.story.seen.slice()", await_promise=False)
    day = await cdp.eval("State.s.story.day", await_promise=False)
    record("nacht: Tag-3-Ereignis (Chantal) ausgeloest", "chantal3" in (seen_events or []), "seen=%s day=%s" % (seen_events, day))

    # Story.night() laeuft nach dem Phasenwechsel auf 'morning' noch fire-and-forget weiter
    # (fade -> advanceDay -> fade -> applyChapter -> morning() -> runEvents('morning')), bevor
    # es im finally-Block Story.sleeping wieder auf false setzt. Ab Tag 4 feuert dort das
    # Morgen-Ereignis 'stadtOffen' (einmalig) und oeffnet Kevins Szene (schuld.stadt, 3 Panels)
    # als echte Cutscene. Die obige Schleife bricht bereits beim blossen Phasenwechsel ab und
    # liefe daher weiter, waehrend diese Cutscene noch offen ist -- ohne diese Abwarte-Schleife
    # bleibt Story.sleeping/Cutscene.active haengen, und der spaetere Story.night()-Aufruf fuer
    # Tag 10 kehrt an seinem eigenen sleeping/Cutscene-Guard sofort und lautlos zurueck (die
    # eigentliche Ursache des vermeintlichen "kontrolle: Tag 10"-Flakes).
    for _ in range(40):
        await cdp.advance_cutscene(max_steps=10)
        sleeping = await cdp.eval("Story.sleeping", await_promise=False)
        cs = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
        if not sleeping and not cs:
            break
        await asyncio.sleep(0.15)
    unlocked_rooms = await cdp.eval("State.s.story.unlocked.rooms.slice()", await_promise=False)
    seen_events = await cdp.eval("State.s.story.seen.slice()", await_promise=False)
    record("stadt: Morgen nach Tag-3-Nacht (Tag 4) feuert stadtOffen, stadt freigeschaltet",
           "stadt" in (unlocked_rooms or []) and "stadtOffen" in (seen_events or []),
           "rooms=%s seen=%s" % (unlocked_rooms, seen_events))

    # Tag 6 Kapitel-Szene: Tag direkt setzen und Kapitel-Wechsel real anwenden.
    await cdp.eval("State.s.story.day = 6; State.s.story.phase='evening'; State.save();")
    await cdp.eval("Story.applyChapter()", await_promise=False)
    await asyncio.sleep(0.3)
    await cdp.advance_cutscene(max_steps=10)
    chapter = await cdp.eval("State.s.story.chapter", await_promise=False)
    unlocked_jobs = await cdp.eval("State.s.story.unlocked.jobs.slice()", await_promise=False)
    record("kapitel: Tag 6 -> Kapitel k2, Taxi/Kurier/Praktikant frei", chapter == "k2" and "taxi" in (unlocked_jobs or []), "chapter=%s jobs=%s" % (chapter, unlocked_jobs))

    # Taxi (mid): Kaution 200 EUR noetig. Story.morning() ist fire-and-forget (zeigt am Ende
    # die Pinnwand ueber UI.show(), das waehrend der Uebergangsanimation kurz "busy" ist) --
    # auf den tatsaechlichen Screen-Wechsel warten, statt eine feste Sleep-Dauer zu raten,
    # sonst kollidiert der direkt folgende Jobs.take() mit UI.show()s busy-Guard und laedt
    # nie den Job-Screen (das war die urspruengliche Ursache von "taxi: Job-Screen geladen").
    await cdp.eval("State.s.balance = 500; UI.setBalance(State.s.balance); State.save();")
    await cdp.eval("Story.morning()", await_promise=False)
    # 'stadtOffen' ist bereits an Tag 4 (s.o.) und damit vor Tag 6 gesehen worden, feuert hier
    # also nicht erneut -- keine Cutscene zu erwarten.
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)
    await cdp.eval("Jobs.take('taxi')")
    await cdp.wait_for("UI.current && UI.current.id === 'job-taxi'", timeout=3.0)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("taxi: Job-Screen geladen", screen == "job-taxi", "screen=%s" % screen)
    await cdp.click("#btnTaxiStart")
    await asyncio.sleep(1.0)
    await cdp.screenshot("story-taxi.png")
    res = await cdp.eval("__pt.autoplayTaxi('win')", timeout=70)
    record("taxi: Schicht abgeschlossen", res is not None, str(res))
    await cdp.click("#btnTaxiDone")
    await asyncio.sleep(0.4)
    await cdp.eval("Jobs.abort(); UI.show('hub')")
    await asyncio.sleep(0.2)

    # Tag 10 Kontrolle (fail) + erzwungenes Duell: Bedingungen bewusst NICHT erfuellen.
    # kontrolleFail wertet 'day:{eq:10}' fuer den AKTUELLEN Tag aus -> Tag muss bereits 10 sein,
    # nicht 9 (Story.night() wuerde sonst die Nacht von Tag 9 auswerten, in der das Ereignis
    # noch nicht faellig ist, und den Tag nur auf 10 hochzaehlen, ohne das Duell auszuloesen).
    await cdp.eval("State.s.story.day = 10; State.s.balance = 10; State.s.story.vars.schuld = 49000; State.s.story.phase='evening'; State.save();")
    # Defensive Kontrolle: Story.night() kehrt an seinem eigenen Guard sofort und lautlos zurueck,
    # wenn Story.sleeping noch true ist oder eine Cutscene noch offen ist (siehe Kommentar oben zu
    # Tag 3/4) -- das direkt vor dem Aufruf zu pruefen, macht eine kuenftige Regression dieser Art
    # sofort sichtbar, statt sie erst am ausbleibenden Duell zu erraten.
    sleeping = await cdp.eval("Story.sleeping", await_promise=False)
    cs = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("kontrolle: kein Schlaf/keine Cutscene vor Tag-10-Nacht", not sleeping and not cs, "sleeping=%s cutscene=%s" % (sleeping, cs))
    await cdp.eval("Story.night()", await_promise=False)
    ok = False
    duel_seen = False
    for _ in range(60):
        active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
        in_duel = await cdp.eval("typeof Russian !== 'undefined' && Russian.inDuel", await_promise=False)
        if in_duel:
            duel_seen = True
            await cdp.screenshot("story-duel-forced.png")
            break
        if active:
            await cdp.advance_cutscene(max_steps=5)
        await asyncio.sleep(0.15)
    record("kontrolle: Tag 10 Fehlschlag loest erzwungenes Duell aus", duel_seen, "duel_seen=%s" % duel_seen)
    if duel_seen:
        # Erst evtl. laufende "igor.first"-Cutscene durchklicken (spielt vor dem ersten Duell je einmal),
        # dann echten Abzugsknopf klicken, bis das Duell entschieden ist.
        for _ in range(30):
            in_duel = await cdp.eval("typeof Russian !== 'undefined' && Russian.inDuel", await_promise=False)
            if not in_duel:
                break
            active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            if active:
                await cdp.advance_cutscene(max_steps=5)
            else:
                await cdp.click("#btnTrigger")
            await asyncio.sleep(0.4)
        await asyncio.sleep(0.3)
        flags = await cdp.eval("State.s.story.flags", await_promise=False)
        record("duell: Ausgang als Flag gemeldet (duelWon/duelLost)", bool((flags or {}).get("duelWon") or (flags or {}).get("duelLost")), str(flags))


async def scenario_endings(cdp):
    """Vier Enden ueber gesetzte Variablen + echten Story.night()-Aufruf."""
    async def run_ending(setup_js, expect_id, shot=None):
        await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=29")
        await asyncio.sleep(0.7)
        await cdp.inject_helpers()
        # Bei Start mit ?day=29 wendet Story.enter() sofort Kapitel 4 an (day>=21), dessen
        # Intro-Szene 'schuld.k4' eine echte Cutscene ist -- die muss erst durchgeklickt sein,
        # sonst blockt Story.nights Cutscene.active-Guard jeden Story.night()-Aufruf lautlos
        # (Ursache der urspruenglichen "ended=None" bei allen vier Enden).
        await cdp.advance_cutscene(max_steps=10)
        await cdp.eval("State.s.story.phase = 'evening'; " + setup_js + " State.save();")
        await cdp.eval("Story.night()", await_promise=False)
        ended = None
        for _ in range(80):
            active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            if active:
                if shot and ended is None:
                    await cdp.screenshot(shot)
                await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
            ended = await cdp.eval("State.s.story.ended", await_promise=False)
            title_hidden = await cdp.eval("document.querySelector('#title').hidden", await_promise=False)
            if ended and title_hidden is False:
                break
            await asyncio.sleep(0.15)
        record("ende %s: erreicht" % expect_id, ended == expect_id, "ended=%s" % ended)
        run_info = await cdp.eval("State.meta.storyRuns['schuld']", await_promise=False)
        record("ende %s: in meta.storyRuns vermerkt" % expect_id, bool(run_info and expect_id in run_info.get("endings", [])), str(run_info))
        # zurueck zum freien Spiel, um den naechsten Lauf sauber zu starten
        return ended

    await run_ending("State.s.story.vars.schuld = 0;", "ehrlich")
    await run_ending(
        "State.s.story.flags.hauptbuch = true; State.s.story.flags.safe = true; "
        "State.s.story.flags.igorZweifelt = true; State.s.story.flags.sturzJetzt = true;",
        "sturz",
        shot="story-ending-sturz.png",
    )
    await run_ending("State.s.story.flags.fluchtHeute = true; State.s.story.flags.chantalKennt = true;", "taxi")

    # Doc-Ende (Fallback) exakt wie im Brief: ueber ?day=30, kein Ende erfuellt.
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=30")
    await asyncio.sleep(0.7)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)  # Kapitel-4-Intro erst wegklicken, siehe run_ending()
    await cdp.eval("State.s.story.phase = 'evening'; State.save();")
    await cdp.eval("Story.night()", await_promise=False)
    ended = None
    for _ in range(80):
        active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
        if active:
            await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
        ended = await cdp.eval("State.s.story.ended", await_promise=False)
        if ended:
            break
        await asyncio.sleep(0.15)
    record("ende doc (Fallback ?day=30): erreicht", ended == "doc", "ended=%s" % ended)
    await cdp.screenshot("story-ending-doc.png")

    # `ended` wird schon zu Beginn von Story.finish() gesetzt, lange bevor die Enden-Cutscene
    # (mehrere Panels + Statistik) durchgeklickt ist -- erst zu Ende klicken, dann kommt Title.show().
    for _ in range(40):
        active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
        if not active:
            break
        await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
        await asyncio.sleep(0.15)

    # "Titel -> Neue Story" nach einem Ende
    await cdp.wait_for("document.querySelector('#title').hidden === false", timeout=2.0)
    title_hidden = await cdp.eval("document.querySelector('#title').hidden", await_promise=False)
    if title_hidden is False:
        record("titel: nach Ende wieder am Titel", True, "")
        await cdp.click(".title-door[data-choice='story']")
        await asyncio.sleep(0.3)
        confirm_active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
        record("titel: 'Neue Story' bei bestehendem Lauf fragt nach", bool(confirm_active), "active=%s" % confirm_active)
    else:
        record("titel: nach Ende wieder am Titel", False, "title_hidden=%s" % title_hidden)


async def scenario_title_trophies(cdp):
    """Trophaeen-Button am Titelscreen (Task-9-Ruling a)."""
    await cdp.navigate(URL_BASE)
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    hidden = await cdp.eval("document.querySelector('#title').hidden", await_promise=False)
    if hidden:
        record("trophaeen-button: Titelscreen sichtbar", False, "hidden=%s" % hidden)
        return
    await cdp.click("#titleTrophiesBtn")
    await asyncio.sleep(0.3)
    panel_hidden = await cdp.eval("document.querySelector('#titleTrophiesPanel').classList.contains('hidden')", await_promise=False)
    record("trophaeen-button: Panel oeffnet sich", panel_hidden is False, "hidden=%s" % panel_hidden)
    count = await cdp.eval("document.querySelectorAll('#titleTrophyGrid .trophy').length", await_promise=False)
    record("trophaeen-button: Trophaeenwand gerendert", (count or 0) > 0, "count=%s" % count)
    await cdp.screenshot("story-title-trophies.png")
    await cdp.click("#titleTrophiesClose")
    await asyncio.sleep(0.2)
    panel_hidden = await cdp.eval("document.querySelector('#titleTrophiesPanel').classList.contains('hidden')", await_promise=False)
    record("trophaeen-button: Schliessen funktioniert", panel_hidden is True, "hidden=%s" % panel_hidden)


async def scenario_job_param(cdp):
    """?job=<id> ueberspringt die Pinnwand (Task-9-Ruling c)."""
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=1&job=spueler")
    await asyncio.sleep(1.0)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("?job=spueler: startet Job direkt ohne Pinnwand-Klick", screen == "job-spueler", "screen=%s" % screen)


async def scenario_all_job_scenes(cdp):
    """Alle 15 Schicht-Karten-Szenen (5 Jobs x 3) je einmal sehen."""
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=1")
    await asyncio.sleep(0.9)
    await cdp.inject_helpers()
    await cdp.eval(
        "State.s.story.unlocked.jobs = ['tuersteher','croupier','kurier','praktikant','docassi']; "
        "State.s.story.jobsDone.tuersteher = 3; State.s.balance = 5000; State.save();"
    )
    seen_all = {}
    for job_id in ["tuersteher", "croupier", "kurier", "praktikant", "docassi"]:
        for _ in range(3):
            await cdp.eval("Jobs.runShift(Jobs.POOL[%s])" % json.dumps(job_id), await_promise=False)
            await cdp.advance_cutscene(max_steps=15)
            await asyncio.sleep(0.15)
        seen = await cdp.eval("(State.s.story.seenJobScenes[%s]||[]).slice()" % json.dumps(job_id), await_promise=False)
        seen_all[job_id] = seen
        expected = await cdp.eval("(Story.story.jobScenes[%s]||[]).slice()" % json.dumps(job_id), await_promise=False)
        ok = sorted(seen or []) == sorted(expected or [])
        record("schicht-karten %s: alle 3 Szenen gesehen" % job_id, ok, "seen=%s expected=%s" % (seen, expected))


async def scenario_spueler_taxi_loss(cdp):
    """Verlust-Fall beider Mini-Spiele (negativer Lohn)."""
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=1&job=spueler")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    balance_before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.click("#btnDishStart")
    await asyncio.sleep(0.3)
    res = await cdp.eval("__pt.autoplaySpueler('loss')", timeout=20)
    await cdp.click("#btnDishDone")
    await asyncio.sleep(0.4)
    balance_after = await cdp.eval("State.s.balance", await_promise=False)
    record("spueler verliert: Lohn negativ, Konto sinkt", (res or {}).get("breaks", 0) > 0 and balance_after < balance_before,
           "res=%s before=%s after=%s" % (res, balance_before, balance_after))

    # jobToday steht noch auf 'spueler' vom Verlust-Lauf eben (ein Job pro Tag) -- zuruecksetzen,
    # sonst haelt StoryRules.jobAvailable() den Taxi-Job fuer "heute schon erledigt".
    await cdp.eval("State.s.story.unlocked.jobs.push('taxi'); State.s.balance = 500; State.s.story.jobToday = null; State.save();")
    await cdp.eval("Story.morning()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)
    await cdp.eval("Jobs.take('taxi')")
    await cdp.wait_for("UI.current && UI.current.id === 'job-taxi'", timeout=3.0)
    balance_before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.click("#btnTaxiStart")
    await asyncio.sleep(0.3)
    res = await cdp.eval("__pt.autoplayTaxi('loss')", timeout=70)
    await cdp.click("#btnTaxiDone")
    await asyncio.sleep(0.4)
    balance_after = await cdp.eval("State.s.balance", await_promise=False)
    record("taxi verliert: nur Strafzettel, Konto sinkt", (res or {}).get("tickets", 0) > 0 and balance_after < balance_before,
           "res=%s before=%s after=%s" % (res, balance_before, balance_after))


async def scenario_job_consumed_before_feierabend(cdp):
    """Ein Job pro Tag auch ohne "Feierabend"-Klick: Spueler-Schicht beenden, dann Escape (statt
    "Feierabend") -> Pinnwand zeigt "Heute erledigt", Spueler nicht erneut klickbar; Reload danach
    -> Fortsetzen landet im Abend mit gesetztem jobToday und ohne doppelten Lohn."""
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=1&job=spueler")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.click("#btnDishStart")
    await asyncio.sleep(0.3)
    await cdp.eval("__pt.autoplaySpueler('win')", timeout=20)
    await asyncio.sleep(0.3)
    job_today = await cdp.eval("State.s.story.jobToday", await_promise=False)
    phase = await cdp.eval("State.s.story.phase", await_promise=False)
    record("ein-job-pro-tag: Schichtende verbraucht den Tag sofort (vor Feierabend)", job_today == "spueler" and phase == "morning",
           "jobToday=%s phase=%s" % (job_today, phase))
    for typ in ("keyDown", "keyUp"):
        await cdp.send("Input.dispatchKeyEvent", {"type": typ, "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    stamps = await cdp.eval("[...document.querySelectorAll('#pinboard .jobnote.done .done-stamp')].map((e) => e.textContent)", await_promise=False)
    record("ein-job-pro-tag: Escape morgens -> Pinnwand mit 'Heute erledigt'", screen == "jobs" and "Heute erledigt" in (stamps or []),
           "screen=%s stamps=%s" % (screen, stamps))
    await cdp.eval("[...document.querySelectorAll('#pinboard .jobnote')].forEach((n) => n.click())", await_promise=False)
    await asyncio.sleep(0.5)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("ein-job-pro-tag: Spueler nicht erneut klickbar", screen == "jobs", "screen=%s" % screen)
    balance = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.navigate(URL_BASE)
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.click(".title-door[data-choice='story']")
    await cdp.wait_for("State.mode === 'story' && UI.current && UI.current.id === 'hub' && !UI.busy", timeout=3.0)
    st = await cdp.eval("({phase: State.s.story.phase, jobToday: State.s.story.jobToday, screen: UI.current && UI.current.id, balance: State.s.balance, jobs: State.s.story.stats.jobs})", await_promise=False) or {}
    record("ein-job-pro-tag: Reload nach Schichtende -> Abend, jobToday gesetzt, Lohn nur einmal",
           st.get("phase") == "evening" and st.get("jobToday") == "spueler" and st.get("screen") == "hub" and st.get("balance") == balance and st.get("jobs") == 1,
           "%s (balance vorher=%s)" % (st, balance))


async def scenario_mode_switch_no_dataloss(cdp):
    """Titel <-> Modi ohne Datenverlust (frei -> Titel -> Story -> Titel -> frei)."""
    await cdp.navigate(URL_BASE + "?fresh&mode=free")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    # Frisches freies Spiel spielt beim ersten Boot die intro-Cutscene ab; solange die laeuft,
    # blockt Title.opens Cutscene.active-Guard jeden Titel-Aufruf lautlos (Ursache dafuer, dass
    # der erste "Story"-Tuerklick unten urspruenglich ins Leere ging und der Modus nie wechselte).
    await cdp.advance_cutscene(max_steps=10)
    await cdp.eval("State.s.balance = 12345; State.save();")
    balance_free = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("Title.open()", await_promise=False)
    await cdp.wait_for("document.querySelector('#title').hidden === false", timeout=2.0)
    await cdp.click(".title-door[data-choice='story']")
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene(max_steps=10)
    await cdp.wait_for("State.mode === 'story'", timeout=2.0)
    await cdp.eval("State.s.balance = 777; State.s.story.vars.schuld = 42000; State.save();")
    story_balance = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("Title.open()", await_promise=False)
    await cdp.wait_for("document.querySelector('#title').hidden === false", timeout=2.0)
    await cdp.click(".title-door[data-choice='free']")
    await cdp.wait_for("State.mode === 'free'", timeout=2.0)
    free_balance_again = await cdp.eval("State.s.balance", await_promise=False)
    record("modus-wechsel: freies Spiel behaelt Kontostand nach Story-Ausflug", free_balance_again == balance_free,
           "vorher=%s nachher=%s" % (balance_free, free_balance_again))
    await cdp.eval("Title.open()", await_promise=False)
    await cdp.wait_for("document.querySelector('#title').hidden === false", timeout=2.0)
    await cdp.click(".title-door[data-choice='story']")
    await cdp.wait_for("State.mode === 'story'", timeout=2.0)
    story_balance_again = await cdp.eval("State.s.balance", await_promise=False)
    schuld_again = await cdp.eval("State.s.story.vars.schuld", await_promise=False)
    record("modus-wechsel: Story behaelt Stand nach freiem Ausflug", story_balance_again == 777 and schuld_again == 42000,
           "balance=%s schuld=%s" % (story_balance_again, schuld_again))


async def scenario_reload_mid_day(cdp):
    """Reload mitten im Tag (Abend, Tag 4) erhaelt Spielstand."""
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=4")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.eval("State.s.story.phase = 'evening'; State.s.story.vars.vertrauen = 3; State.save();")
    day_before = await cdp.eval("State.s.story.day", await_promise=False)
    await cdp.navigate(URL_BASE)
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    # Ein blanker Reload zeigt immer erst den Titelscreen (Spec §3) -- er laedt den Modus nicht
    # automatisch wieder, das ist gewollt. "Fortsetzen" (Tuer "Story") fuehrt ohne weiteren Klick
    # zurueck an genau die Stelle, an der gespeichert wurde; das ist hier zu pruefen.
    hidden = await cdp.eval("document.querySelector('#title').hidden", await_promise=False)
    if hidden is False:
        await cdp.click(".title-door[data-choice='story']")
        await cdp.wait_for("State.mode === 'story'", timeout=2.0)
    day_after = await cdp.eval("State.s.story.day", await_promise=False)
    phase_after = await cdp.eval("State.s.story.phase", await_promise=False)
    vertrauen_after = await cdp.eval("State.s.story.vars.vertrauen", await_promise=False)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("reload mitten im Tag: Tag/Phase/Variablen erhalten", day_after == day_before and phase_after == "evening" and vertrauen_after == 3,
           "day=%s phase=%s vertrauen=%s screen=%s" % (day_after, phase_after, vertrauen_after, screen))


async def scenario_mobile(cdp):
    """Mobile 400px: Pinnwand ohne horizontales Scrollen."""
    await cdp.set_mobile(True)
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=1")
    await asyncio.sleep(1.0)
    await cdp.screenshot("story-mobile-jobs.png")
    scroll_w = await cdp.eval("document.documentElement.scrollWidth", await_promise=False)
    client_w = await cdp.eval("document.documentElement.clientWidth", await_promise=False)
    record("mobile 400px: Pinnwand kein horizontales Scrollen", scroll_w == client_w, "scrollWidth=%s clientWidth=%s" % (scroll_w, client_w))

    await cdp.eval("UI.show('hub')")
    await asyncio.sleep(0.3)
    scroll_w = await cdp.eval("document.documentElement.scrollWidth", await_promise=False)
    client_w = await cdp.eval("document.documentElement.clientWidth", await_promise=False)
    record("mobile 400px: Abend-Hub kein horizontales Scrollen", scroll_w == client_w, "scrollWidth=%s clientWidth=%s" % (scroll_w, client_w))
    await cdp.set_mobile(False)


async def scenario_reduced_motion(cdp):
    """Reduced Motion: Cutscene-Text sofort da, Spueler-Zone bleibt 30%."""
    await cdp.set_reduced_motion(True)
    await cdp.navigate(URL_BASE + "?fresh")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.click(".title-door[data-choice='story']")
    await asyncio.sleep(0.25)
    text_len = await cdp.eval("(document.querySelector('.cs-text')||{}).textContent.length", await_promise=False)
    full_len = await cdp.eval(
        "Cutscene.SCENES['schuld.intro'][0].text.length", await_promise=False
    )
    record("reduced-motion: Cutscene-Text erscheint sofort komplett", text_len == full_len, "text=%s full=%s" % (text_len, full_len))
    await cdp.advance_cutscene(max_steps=20)
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)

    await cdp.eval("Jobs.take('spueler')")
    await cdp.wait_for("UI.current && UI.current.id === 'job-spueler'", timeout=3.0)
    await cdp.click("#btnDishStart")
    await asyncio.sleep(0.15)
    await cdp.eval("for (let i=0;i<5;i++) Spueler.nextPlate();")
    zone_w = await cdp.eval("Spueler.zone.w", await_promise=False)
    record("reduced-motion: Spueler-Zone bleibt 30% (kein Schrumpfen)", abs((zone_w or 0) - 0.3) < 1e-9, "zone.w=%s" % zone_w)
    await cdp.set_reduced_motion(False)


async def scenario_all_scenes(cdp):
    """Jede Szene von Story 1 einmal (Spec-Checkliste), inkl. seltener Verzweigungen
    (Croupier erwischt 30%, Kurier verhaftet, Buero-Entscheidung...), die im natuerlichen
    Spielverlauf nicht zuverlaessig in einem einzigen Lauf auftreten. Story.playScene() ist
    exakt die Methode, die jede Szene im echten Spiel rendert (Jobs.runShift, Ereignisse,
    Story.finish() rufen sie alle auf) -- hier wird sie fuer jede in STORY_SCHULD.scenes
    registrierte Szenen-ID einmal direkt aufgerufen, jede Cutscene bis zum Ende durchgeklickt.
    """
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=1")
    await asyncio.sleep(0.9)
    await cdp.inject_helpers()
    scene_ids = await cdp.eval("Object.keys(Story.story.scenes)", await_promise=False) or []
    errors_before = len(cdp.console_errors)
    played = []
    for sid in scene_ids:
        await cdp.eval("Story.playScene(%s)" % json.dumps(sid), await_promise=False)
        await cdp.wait_for("__pt.cutsceneActive()", timeout=1.0)
        for _ in range(20):
            active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            if not active:
                break
            await cdp.advance_cutscene(max_steps=1)
        played.append(sid)
    new_errors = cdp.console_errors[errors_before:]
    record("story-1: jede Szene einmal gerendert (%d Szenen)" % len(scene_ids), len(played) == len(scene_ids) and not new_errors,
           "gespielt=%d/%d fehler=%s" % (len(played), len(scene_ids), new_errors))


async def scenario_stadt_shop(cdp):
    """Stadt: Kauf abgelehnt ohne Geld, Kauf, Upgrade, Markenwechsel mit Bestaetigung, Abbruch."""
    await cdp.navigate(URL_BASE + "?fresh&screen=stadt")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.eval("State.meta.insider = []; State.meta.insiderClaimed = {}; State.saveMeta(); 0", await_promise=False)
    # Strasse: vier Schaufenster (Autohaus, INTERSPORT, Casino Royal ohne Auto gesperrt), Laden noch zu
    n_fronts = await cdp.eval("document.querySelectorAll('#strasse .storefront, #strasse .facade').length", await_promise=False)
    royal_locked = await cdp.eval("document.querySelector('#strasse .facade').classList.contains('locked')", await_promise=False)
    laden_hidden = await cdp.eval("document.querySelector('#laden').classList.contains('hidden')", await_promise=False)
    record("stadt: Strasse zeigt vier Schaufenster (Casino Royal ohne Auto gesperrt), Laden zu",
           n_fronts == 4 and royal_locked is True and laden_hidden is True,
           "fronts=%s royal_locked=%s laden_hidden=%s" % (n_fronts, royal_locked, laden_hidden))
    await cdp.screenshot("stadt-strasse.png")
    await cdp.click(".storefront.audi")
    await asyncio.sleep(0.3)
    n_cards = await cdp.eval("document.querySelectorAll('#laden .gear-card').length", await_promise=False)
    title = await cdp.eval("document.querySelector('#stadtTitle').textContent", await_promise=False)
    record("stadt: Klick auf Audi Zentrum oeffnet Laden mit drei Karten", n_cards == 3 and title is not None and "Audi Zentrum" in title, "cards=%s title=%s" % (n_cards, title))
    n_buttons = await cdp.eval("document.querySelectorAll('#laden .btn').length", await_promise=False)
    record("stadt: ohne Geld kein Kaufen-Button", n_buttons == 0, "buttons=%s" % n_buttons)
    await cdp.screenshot("stadt-arm.png")
    await cdp.eval("State.s.balance = 20000; State.save(); UI.setBalance(20000, {animate:false}); Stadt.render(); 0", await_promise=False)
    await asyncio.sleep(0.2)
    await cdp.eval("Stadt.buyCar('audiA3'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.4)
    car = await cdp.eval("State.s.car", await_promise=False)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    record("stadt: A3 gekauft", car == "audiA3" and bal == 18500, "car=%s bal=%s" % (car, bal))
    label = await cdp.eval("[...document.querySelectorAll('#laden .gear-card')][1].querySelector('.btn').textContent", await_promise=False)
    record("stadt: RS 4 zeigt Upgrade-Preis mit Inzahlungnahme", label is not None and "7.250" in label, "label=%s" % label)
    await cdp.screenshot("stadt-a3.png")
    # Markenwechsel mit Bestaetigung: erst abbrechen, dann zustimmen
    await cdp.eval("Stadt.buyCar('mercC'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene(label_hint="Doch nicht")
    await asyncio.sleep(0.3)
    car = await cdp.eval("State.s.car", await_promise=False)
    record("stadt: Abbruch laesst Auto unveraendert", car == "audiA3", "car=%s" % car)
    await cdp.eval("Stadt.buyCar('mercC'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene(label_hint="Ja, tauschen")
    await asyncio.sleep(0.4)
    car = await cdp.eval("State.s.car", await_promise=False)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    record("stadt: Markenwechsel A3 -> C-Klasse kostet 1.250", car == "mercC" and bal == 18500 - 1250, "car=%s bal=%s" % (car, bal))
    await cdp.eval("Stadt.buyShoes('trail'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.3)
    shoes = await cdp.eval("State.s.shoes", await_promise=False)
    record("stadt: Trail-Runner gekauft", shoes == "trail", "shoes=%s" % shoes)
    await cdp.click("#stadtBack")
    await asyncio.sleep(0.3)
    owned = await cdp.eval("[...document.querySelectorAll('#strasse .storefront .owned')].map(e=>e.textContent).join('|')", await_promise=False)
    record("stadt: Zurueck auf die Strasse zeigt Besitz an den Schaufenstern", owned is not None and "Mercedes C-Klasse" in owned and "Trail-Runner Pro" in owned, "owned=%s" % owned)
    line = await cdp.eval("document.querySelector('#gearLine') && document.querySelector('#gearLine').textContent", await_promise=False)
    record("stadt: Seitenleiste zeigt Besitz", line is not None and "Mercedes C-Klasse" in line and "Trail-Runner" in line and "💪 0" in line, "line=%s" % line)
    terms = await cdp.eval("UI.show('finance').then(()=>document.querySelector('#bankTerms').textContent)")
    record("stadt: Bank zeigt Mercedes-Konditionen", terms is not None and "7 %" in terms and "4.000" in terms, "terms=%s" % terms)


async def scenario_royal_free(cdp):
    """Casino Royal im freien Spiel: kein zweiter Eintritt ueber die Seitenleiste, Eintritts-Toast erst
    nach der Erstbesuch-Szene, Freispiele/Craps-Tisch haengen am Spielstand, Craps rechnet den
    Schnappschuss der Einsaetze ab (Remount waehrend des Wurfs erzeugt kein Geld)."""
    await cdp.navigate(URL_BASE + "?fresh&mode=free")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)
    await cdp.eval("State.s.car = 'audiA3'; State.s.balance = 1000; State.save(); UI.renderWallet(); UI.renderSide();", await_promise=False)
    # Erster Eintritt: 100 EUR, royal.first-Szene laeuft, der Toast darf erst danach kommen (#5)
    await cdp.click("#side [data-action='royal']")
    await cdp.wait_for("__pt.cutsceneActive()", timeout=2.0)
    toast_during = await cdp.eval("document.querySelector('#toasts').textContent.includes('Eintritt')", await_promise=False)
    await cdp.advance_cutscene(max_steps=10)
    await cdp.wait_for("UI.current && UI.current.id === 'royal' && !UI.busy", timeout=3.0)
    toast_after = await cdp.eval("document.querySelector('#toasts').textContent.includes('Eintritt')", await_promise=False)
    balance = await cdp.eval("State.s.balance", await_promise=False)
    record("royal: erster Eintritt kostet 100 EUR, Toast erst nach der Erstbesuch-Szene",
           balance == 900 and toast_during is False and toast_after is True,
           "balance=%s toast_waehrend=%s toast_danach=%s" % (balance, toast_during, toast_after))
    # Seitenleiste erneut: kein zweiter Eintritt, Screen bleibt Lobby (#1)
    await cdp.click("#side [data-action='royal']")
    await asyncio.sleep(0.6)
    balance2 = await cdp.eval("State.s.balance", await_promise=False)
    screen2 = await cdp.eval("UI.current.id", await_promise=False)
    record("royal: Seitenleisten-Klick in der Lobby kassiert nicht erneut", balance2 == 900 and screen2 == "royal",
           "balance=%s screen=%s" % (balance2, screen2))
    # Vom Tisch aus: zurueck in die Lobby, ohne Gebuehr (#1)
    await cdp.eval("UI.show('megaslots')")
    await cdp.click("#side [data-action='royal']")
    await cdp.wait_for("UI.current && UI.current.id === 'royal' && !UI.busy", timeout=3.0)
    balance3 = await cdp.eval("State.s.balance", await_promise=False)
    screen3 = await cdp.eval("UI.current.id", await_promise=False)
    record("royal: Seitenleisten-Klick am Tisch fuehrt gebuehrenfrei in die Lobby", balance3 == 900 and screen3 == "royal",
           "balance=%s screen=%s" % (balance3, screen3))
    # Craps: Einsatz platziert, Remount waehrend des Wurfs gibt place() wieder frei -- abgerechnet wird trotzdem nur der Schnappschuss (#4)
    await cdp.eval("UI.show('craps')")
    craps = await cdp.eval("""(async function(){
      RoyalRules.crapsRoll = function(){ return [3, 4]; };  // 7 im Come-out: Pass gewinnt 1:1
      document.querySelector('#crapsBet').value = '100';
      Craps.place('pass');
      var before = State.s.balance, placed = Craps.bets.pass;
      var p = Craps.roll();
      UI.current.def.unmount(); UI.current.def.mount(document.querySelector('#stage'));  // Remount: rolling=false, place() wieder moeglich
      Craps.place('pass');
      var live = Craps.bets.pass;
      await p;
      return { before: before, placed: placed, live: live, after: State.s.balance, pass: Craps.bets.pass, field: Craps.bets.field };
    })()""")
    craps_ok = bool(craps) and craps.get("placed") == 100 and craps.get("live") == 200 and craps.get("after") == craps.get("before") + 100 and craps.get("pass") == 0 and craps.get("field") == 0
    record("royal: Craps rechnet den Einsatz-Schnappschuss ab (Remount waehrend des Wurfs erzeugt kein Geld)", craps_ok, "%s" % (craps,))
    # Freispiele und Craps-Tisch haengen am Spielstand: neuer State.s -> verfallen (#2)
    await cdp.eval("MegaSlots.freeLeft = 3; MegaSlots.lastBet = 100; MegaSlots.freeRun = State.s; Craps.point = 6; Craps.bets.pass = 100; Craps.run = State.s;", await_promise=False)
    await cdp.eval("State.reset(); Modes.enter('free')", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene(max_steps=10)
    await cdp.wait_for("UI.current && UI.current.id === 'hub' && !UI.busy", timeout=3.0)
    await cdp.eval("UI.show('megaslots')")
    free_left = await cdp.eval("MegaSlots.freeLeft", await_promise=False)
    mega_btn = await cdp.eval("document.querySelector('#btnMega').textContent", await_promise=False)
    await cdp.eval("UI.show('craps')")
    craps_point = await cdp.eval("Craps.point", await_promise=False)
    craps_pass = await cdp.eval("Craps.bets.pass", await_promise=False)
    record("royal: Freispiele und Craps-Tisch verfallen mit neuem Spielstand",
           free_left == 0 and mega_btn == "Drehen" and craps_point is None and craps_pass == 0,
           "freeLeft=%s btn=%s point=%s pass=%s" % (free_left, mega_btn, craps_point, craps_pass))


async def scenario_mugging(cdp):
    """Ueberfall im freien Spiel: alle drei Ausgaenge per ?mug."""
    async def setup(mug):
        await cdp.navigate(URL_BASE + "?fresh&screen=hub&mug=" + mug)
        await asyncio.sleep(1.0)
        await cdp.inject_helpers()
        await cdp.eval("State.s.balance = 1000; State.s.stats.spins = 20; State.save(); UI.setBalance(1000, {animate:false}); 0", await_promise=False)
    # Zahlen
    await setup("junkie")
    await cdp.click(".door[data-screen=slots]")
    await asyncio.sleep(0.6)
    active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("mug: Szene erscheint beim Tuerwechsel", active is True, "active=%s" % active)
    # Bis zum Wahl-Panel vorklicken (2 Klicks/Panel: Tipp-Text fertigstellen, dann weiter; das
    # dritte Panel braucht nur den ersten Klick, um die Choice-Buttons zu rendern) statt gleich zu
    # screenshotten -- der Brief schoss hier noch auf Panel 1 ("Der kurze Weg...", Screenshot ohne
    # Raeuber und ohne Prozent-Buttons); Step 3 verlangt aber genau die Choice-Buttons mit Prozenten.
    await cdp.advance_cutscene(max_steps=5)
    n_choices = await cdp.eval("document.querySelectorAll('.cs-choices button').length", await_promise=False)
    record("mug: Wahl-Panel zeigt genau drei Choice-Buttons", n_choices == 3, "n_choices=%s" % n_choices)
    await cdp.screenshot("mug-intro.png")
    await cdp.advance_cutscene(label_hint="Zahlen")
    await asyncio.sleep(0.6)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    cd = await cdp.eval("State.s.mugCooldown", await_promise=False)
    record("mug: Zahlen kostet 200 und fuehrt zu den Slots", bal == 800 and screen == "slots" and cd == 15, "bal=%s screen=%s cd=%s" % (bal, screen, cd))
    # Kaempfen mit Staerke 20 (Math.random gestubbt, kein zufaelliger Sieg): Rules.fightChance(20)
    # ist bei Rules.MUG.CHANCE_CAP = 0.9 gedeckelt, also bleibt selbst bei Staerke 20 immer eine
    # ~10 %-Chance auf eine Niederlage -- ohne Stub war dieser Check entsprechend flakig (siehe
    # Fix-Report). Math.random() -> 0 macht Math.random() < fightChance immer wahr (Sieg) und
    # Rules.mugWallet(rng) liefert damit exakt 50 (unterste Grenze 50-150).
    await setup("cousin")
    await cdp.eval("State.s.strength = 20; State.save(); 0", await_promise=False)
    await cdp.click(".door[data-screen=roulette]")
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene(max_steps=5)
    await cdp.eval("window.__origRandom = Math.random; Math.random = () => 0; 0", await_promise=False)
    await cdp.eval("__pt.advance('Kämpfen')", await_promise=False)
    await asyncio.sleep(0.5)
    # Screenshot mitten in der Ergebnis-Szene (Gasse-Hintergrund, Portrait, Kampftext) statt erst
    # nach deren vollstaendiger Aufloesung -- die Brief-Version schoss erst nach dem kompletten
    # Durchklicken, als bereits wieder das Roulette-Blatt zu sehen war (siehe Report).
    await cdp.screenshot("mug-fight.png")
    await cdp.advance_cutscene()
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    await asyncio.sleep(0.4)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    won = await cdp.eval("State.s.stats.fightsWon", await_promise=False)
    record("mug: Kampf mit Staerke 20 gewonnen, Brieftasche 50-150, Staerke 21", bal == 1050 and st == 21 and won == 1, "bal=%s st=%s won=%s" % (bal, st, won))
    # Wegrennen mit R8 + Carbon (90 % Fluchtchance): Math.random gestubbt (>= jeder moeglichen
    # Fluchtchance) macht die Flucht deterministisch erwischt, analog zum Kampf-Stub oben (siehe
    # Fix-Report) -- ohne Stub war dieser Check entsprechend flakig (bal 1000 oder 700).
    await setup("jugend")
    await cdp.eval("State.s.car = 'audiR8'; State.s.shoes = 'carbon'; State.save(); 0", await_promise=False)
    await cdp.click(".door[data-screen=blackjack]")
    await asyncio.sleep(0.6)
    await cdp.eval("window.__origRandom = Math.random; Math.random = () => 0.99; 0", await_promise=False)
    await cdp.advance_cutscene(label_hint="Wegrennen")
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    await asyncio.sleep(0.6)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    st = await cdp.eval("State.s.strength", await_promise=False)
    record("mug: Flucht erwischt (RNG gestubbt) kostet 300, Staerke bleibt 0", bal == 700 and st == 0, "bal=%s st=%s" % (bal, st))
    # Kein Ueberfall bei Cooldown
    await cdp.eval("Mugging.force = true; State.s.mugCooldown = 5; 0", await_promise=False)
    await cdp.eval("UI.show('hub'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.click(".door[data-screen=slots]")
    await asyncio.sleep(0.6)
    active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("mug: ?mug erzwingt auch im Cooldown (Dev), Szene laeuft", active is True, "active=%s" % active)
    await cdp.advance_cutscene(label_hint="Zahlen")


async def scenario_story_stadt(cdp):
    """Story: Tag 4 schaltet die Stadt frei, Abend-Ueberfall, Eintreiber ab Staerke 4."""
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=4")
    await asyncio.sleep(1.2)
    await cdp.inject_helpers()
    await cdp.advance_cutscene()
    await asyncio.sleep(0.4)
    rooms = await cdp.eval("JSON.stringify(State.s.story.unlocked.rooms)", await_promise=False)
    record("story: Tag 4 schaltet stadt frei", rooms is not None and "stadt" in rooms, "rooms=%s" % rooms)
    has_btn = await cdp.eval("!!document.querySelector('#side [data-action=stadt]')", await_promise=False)
    record("story: Seitenleiste zeigt Stadt-Knopf", has_btn is True, "has=%s" % has_btn)
    await cdp.screenshot("stadt-story-tag4.png")
    # Abend-Ueberfall erzwingen
    await cdp.eval("Mugging.force = 'cousin'; State.s.balance = 500; State.save(); 0", await_promise=False)
    await cdp.eval("Jobs.take('spueler'); 0", await_promise=False)
    await asyncio.sleep(0.8)
    await cdp.eval("Spueler.finish && Spueler.finish(); 0", await_promise=False)
    await asyncio.sleep(0.8)
    await cdp.eval("Story.evening(); 0", await_promise=False)
    await asyncio.sleep(0.8)
    active = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("story: Ueberfall am Abend", active is True, "active=%s" % active)
    await cdp.advance_cutscene(label_hint="Zahlen")
    await asyncio.sleep(0.5)
    cd = await cdp.eval("State.s.mugCooldown", await_promise=False)
    phase = await cdp.eval("State.s.story.phase", await_promise=False)
    record("story: Cooldown 3 Tage, Abend erreicht", cd == 3 and phase == "evening", "cd=%s phase=%s" % (cd, phase))
    # Eintreiber
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&day=13")
    await asyncio.sleep(1.2)
    await cdp.inject_helpers()
    await cdp.advance_cutscene()
    # Race: der Boot-Kettenaufruf Story.enter() -> applyChapter() -> morning() zeigt 'jobs' selbst
    # noch an, waehrend advance_cutscene() bereits zurueckkehrt (Cutscene.active wird synchron
    # false, bevor der then()-Rest von morning() den Screen tatsaechlich neu rendert). Ohne diese
    # Wartezeile landet der direkt folgende manuelle UI.show('jobs')-Aufruf noch in UI.busy und
    # wird stillschweigend zum No-Op -- das zuvor gepushte 'eintreiber' fehlt dann auf der
    # Pinnwand, obwohl State.s.story.unlocked.jobs es bereits enthaelt (siehe Selbst-Review).
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=3.0)
    await cdp.eval("Story.s.unlocked.jobs.push('eintreiber'); State.s.strength = 3; State.save(); UI.show('jobs'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    locked = await cdp.eval("(()=>{const c=[...document.querySelectorAll('#pinboard .jobnote')].find(e=>e.textContent.includes('Eintreiber')); return c ? c.textContent.includes('Stärke 4') : 'missing'})()", await_promise=False)
    record("story: Eintreiber bei Staerke 3 gesperrt", locked is True, "locked=%s" % locked)
    await cdp.eval("State.s.strength = 4; State.save(); UI.show('jobs'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    locked = await cdp.eval("(()=>{const c=[...document.querySelectorAll('#pinboard .jobnote')].find(e=>e.textContent.includes('Eintreiber')); return c ? c.textContent.includes('Stärke 4') : 'missing'})()", await_promise=False)
    record("story: Eintreiber bei Staerke 4 offen", locked is False, "locked=%s" % locked)
    await cdp.screenshot("stadt-story-eintreiber.png")


DIFF_THRESHOLD_PCT = 2.0


async def scenario_free_sandbox_unchanged(cdp):
    """Freies Spiel unveraendert: ?screen=-Screenshots per echtem Pixel-Diff (Pillow) gegen
    docs/superpowers/screenshots/*.png vergleichen -- nicht nur "Datei existiert"."""
    ref_dir = os.path.join(ROOT, "docs", "superpowers", "screenshots")
    if not HAVE_PIL:
        record("freie sandbox: Pillow verfuegbar", False, "import PIL schlug fehl -- Vergleich faellt auf Dateigroesse zurueck")
    # Insider-Upgrades sind Meta-weit und ueberleben "?fresh" (das loescht nur den Spielstand) --
    # scenario_endings() kann beim Durchklicken einer Story-Ende-Cutscene zufaellig eins mitnehmen.
    # Fuer den reinen UI-Pixel-Vergleich hier zuruecksetzen, sonst ist der Vergleich nicht deterministisch.
    await cdp.eval("localStorage.removeItem('keller37.meta'); 0", await_promise=False)
    for screen in ["slots", "roulette", "blackjack", "hub"]:
        await cdp.send("Emulation.clearDeviceMetricsOverride")
        await cdp.navigate(URL_BASE + "?fresh&screen=%s" % screen)
        await asyncio.sleep(0.8)
        path = await cdp.screenshot("story-free-%s.png" % screen)
        ref = os.path.join(ref_dir, "%s.png" % screen)
        if not (path and os.path.exists(ref)):
            record("freie sandbox: ?screen=%s unveraendert (Pixel-Diff)" % screen, False,
                   "Screenshot oder Referenzbild fehlt (path=%s ref_exists=%s)" % (path, os.path.exists(ref)))
            continue
        pct, detail = compare_screenshots(ref, path)
        record("freie sandbox: ?screen=%s unveraendert (Pixel-Diff < %.0f%%)" % (screen, DIFF_THRESHOLD_PCT),
               pct < DIFF_THRESHOLD_PCT, detail)


async def scenario_kater(cdp):
    """Story 2: Sperre ohne Story-1-Ende, Intro-Variante, Absturz, Zitter-Tag, Bett-Ende aus dem
    sleep-Hook heraus samt sauberem Start der Folgestory, Kauf-Ende aus einer Szenen-Wahl."""

    async def settle(max_rounds=60, label_hint=None):
        """Story.night()/enter() laufen fire-and-forget weiter (Blenden, Kapitel-Intro, Morgen-Events).
        Cutscenes durchklicken, bis kein Schlaf und keine Cutscene mehr offen ist -- sonst kehrt der
        naechste Story.night()-Aufruf an seinem sleeping/Cutscene-Guard lautlos zurueck."""
        for _ in range(max_rounds):
            if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                await cdp.advance_cutscene(max_steps=4, label_hint=label_hint)
            sleeping = await cdp.eval("Story.sleeping", await_promise=False)
            cs = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            busy = await cdp.eval("UI.busy", await_promise=False)
            if not sleeping and not cs and not busy:
                return True
            await asyncio.sleep(0.15)
        return False

    async def click_choice(hint, max_steps=8):
        """Vorklicken, bis ein Choice-Button mit diesem Text da ist, dann genau den klicken."""
        for _ in range(max_steps):
            if not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                return False
            found = await cdp.eval(
                "(function(){var b=[...document.querySelectorAll('.cs-choices button')].find(function(x){return x.textContent.includes(%s)}); if(!b) return false; b.click(); return true;})()" % json.dumps(hint),
                await_promise=False)
            if found:
                return True
            await cdp.eval("__pt.advance(null)", await_promise=False)
            await asyncio.sleep(0.15)
        return False

    # Ohne Story-1-Ende ist Der Kater gesperrt: Titel zeigt Die Schuld als naechste Story.
    # ?fresh loescht nur die Spielstaende, nicht State.meta (storyRuns) -- die vorigen Szenarien haben
    # Die Schuld bereits zu Ende gespielt, also die Enden-Historie erst leeren und dann neu booten.
    await cdp.navigate(URL_BASE + "?fresh")
    await asyncio.sleep(0.5)
    await cdp.eval("State.meta.storyRuns = {}; State.saveMeta(); 0", await_promise=False)
    await cdp.navigate(URL_BASE + "?fresh")
    await asyncio.sleep(0.7)
    tag = await cdp.eval("document.querySelector('#titleStoryTag').textContent", await_promise=False)
    record("kater: ohne Story-1-Ende startet Die Schuld", "Die Schuld" in (tag or ""), tag)
    lock = await cdp.eval("document.querySelector('#titleStoryLock').textContent", await_promise=False)
    record("kater: Titel nennt die Sperre", "Der Kater" in (lock or ""), lock)
    # Erzwungen mit vorigem Ende doc: Intro-Variante Doc (Klinik), Hochzeit, Villa
    await cdp.navigate(URL_BASE + "?fresh&story=kater&prev=doc")
    await asyncio.sleep(0.7)
    await cdp.inject_helpers()
    await cdp.wait_for("__pt.cutsceneActive() && document.querySelector('#cutscene .cs-name')", timeout=2.0)
    first_bg = await cdp.eval("(document.querySelector('#cutscene .cs-sky')||{}).className || ''", await_promise=False)
    first_who = await cdp.eval("(document.querySelector('#cutscene .cs-name')||{}).textContent", await_promise=False)
    await cdp.advance_cutscene(max_steps=20)
    # Tag-1-Morgen (einrichten/niereWeg) laeuft nach dem Intro fire-and-forget bis zur Pinnwand
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy && State.s.story.seen.includes('einrichten')", timeout=4.0)
    record("kater: Intro-Variante Doc (erstes Panel beim Doc in der Klinik)", first_who == "Der Doc" and "klinik" in (first_bg or ""), "who=%s bg=%s" % (first_who, first_bg))
    leber = await cdp.eval("State.s.story.vars.leber", await_promise=False)
    record("kater: Doc-Ende → Leber 70", leber == 70, "leber=%s" % leber)
    car = await cdp.eval("State.s.car", await_promise=False)
    house = await cdp.eval("State.s.hasHouse", await_promise=False)
    record("kater: Mercedes am Tag 1", car == "mercC" and house is True, "car=%s hasHouse=%s" % (car, house))
    gear = await cdp.eval("(document.querySelector('#gearLine')||{}).textContent", await_promise=False)
    notes = await cdp.eval("document.querySelector('#notes').textContent", await_promise=False)
    hud = await cdp.eval("""(function(){
      return { leber: (document.querySelector('.hud-leber .val') || {}).textContent,
               kruege: document.querySelectorAll('.hud-pegel .krug.on').length,
               deckel: (document.querySelector('.hud-deckel .val') || {}).textContent };
    })()""", await_promise=False) or {}
    record("kater: HUD zeigt Mercedes, Villa-Ertrag und Leber/Pegel/Deckel",
           gear is not None and "Mercedes" in gear and notes is not None and "💸" in notes and hud.get("leber") == "70" and hud.get("kruege") == 0 and hud.get("deckel") == "0 €",
           "gear=%s notes=%s hud=%s" % (gear, notes, hud))
    pin = await cdp.eval("[...document.querySelectorAll('#pinboard .jobnote')].map(n => n.textContent.includes('Filialleiter') ? 'fil' : '').filter(Boolean).length", await_promise=False)
    record("kater: Filialleiter an der Pinnwand", pin == 1, "filialleiter-zettel=%s" % pin)
    royal_ok = await cdp.eval("Story.roomUnlocked('royal') && !Story.isLocked('royal') && !!document.querySelector('#side [data-action=royal]:not([disabled])')", await_promise=False)
    record("kater: Casino Royal am Tag 1 erreichbar (Auto da)", royal_ok is True, "royal_ok=%s" % royal_ok)
    await cdp.screenshot("kater-tag1.png")
    # Drei Naechte schlafen (Job ueberspringen: 'Kein Job heute' = Story.evening())
    await cdp.eval("State.s.mugCooldown = 999; State.save();", await_promise=False)
    for d in (1, 2, 3):
        await cdp.eval("Story.evening()", await_promise=False)
        await cdp.wait_for("UI.current && UI.current.id === 'hub' && !UI.busy", timeout=3.0)
        await cdp.eval("Story.night()", await_promise=False)
        await cdp.wait_for("Story.sleeping === true", timeout=1.0)
        if d == 3:
            # Absturz-Szene (Nacht 3) real sehen
            await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
            await cdp.screenshot("kater-absturz.png")
        for _ in range(40):
            if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                await cdp.advance_cutscene(max_steps=4)
            if await cdp.eval("State.s.story.day", await_promise=False) == d + 1 and not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                break
            await asyncio.sleep(0.15)
        await settle()
    bal = await cdp.eval("State.s.balance", await_promise=False)
    flag = await cdp.eval("State.s.story.flags.abgestuerzt", await_promise=False)
    record("kater: Absturz Nacht 3", bal == 0 and flag is True, "balance=%s abgestuerzt=%s" % (bal, flag))
    car = await cdp.eval("State.s.car", await_promise=False)
    house = await cdp.eval("State.s.hasHouse", await_promise=False)
    chapter = await cdp.eval("State.s.story.chapter", await_promise=False)
    jobs = await cdp.eval("State.s.story.unlocked.jobs.slice()", await_promise=False)
    royal_room = await cdp.eval("Story.roomUnlocked('royal')", await_promise=False)
    record("kater: nach dem Absturz kein Auto, keine Villa, Kapitel 2, Filialleiter/Royal gesperrt",
           car is None and house is False and chapter == "k2" and "filialleiter" not in (jobs or []) and "spueler" in (jobs or []) and royal_room is False,
           "car=%s house=%s chapter=%s jobs=%s royal=%s" % (car, house, chapter, jobs, royal_room))
    price = await cdp.eval("StoryRules.price(State.s, 'beer')", await_promise=False)
    record("kater: erstes Bier umsonst", price == 0, "price=%s" % price)
    side_price = await cdp.eval("(document.querySelector('#side [data-action=beer] .price')||{}).textContent", await_promise=False)
    record("kater: Seitenleiste zeigt Bier 0 €", side_price == "0 €", "side=%s" % side_price)
    await cdp.eval("Story.evening()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'hub' && !UI.busy", timeout=3.0)
    await cdp.eval("Actions.beer()")
    deckel = await cdp.eval("State.s.story.vars.deckel", await_promise=False)
    record("kater: Deckel 50 nach Freibier", deckel == 50, "deckel=%s" % deckel)
    side_price = await cdp.eval("(document.querySelector('#side [data-action=beer] .price')||{}).textContent", await_promise=False)
    hud = await cdp.eval("""(function(){
      return { kruege: document.querySelectorAll('.hud-pegel .krug.on').length,
               deckel: (document.querySelector('.hud-deckel .val') || {}).textContent };
    })()""", await_promise=False) or {}
    record("kater: danach Bier 50 €, Deckel im HUD", side_price == "50 €" and hud.get("deckel") == "50 €" and hud.get("kruege") == 1,
           "side=%s hud=%s" % (side_price, hud))
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("Story.sleeping === true", timeout=1.0)
    for _ in range(40):
        if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            await cdp.advance_cutscene(max_steps=4)
        if await cdp.eval("State.s.story.flags.zitter", await_promise=False):
            break
        await asyncio.sleep(0.15)
    zitter = await cdp.eval("State.s.story.flags.zitter", await_promise=False)
    entzug_seen = await cdp.eval("State.s.story.seen.includes('entzugSzene')", await_promise=False)
    record("kater: Zitter-Tag nach Entzugsnacht", zitter is True and entzug_seen is True, "zitter=%s entzugSzene=%s" % (zitter, entzug_seen))
    await settle()
    toast = await cdp.eval("document.querySelector('#toasts').textContent", await_promise=False)
    record("kater: Entzugs-Toast", toast is not None and "Entzugsnacht" in toast, "toasts=%s" % (toast or "")[:120])
    await cdp.screenshot("kater-zitter.png")
    # Zitter-Sperre am Casino Royal: Raum ist bis Kapitel 3 zu -- Auto und Raum setzen, Schaufenster und Eintritt pruefen
    await cdp.eval("State.s.car = 'audiA3'; State.s.story.unlocked.rooms.push('royal'); State.save(); UI.renderSide();", await_promise=False)
    await cdp.eval("UI.show('stadt')")
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=3.0)
    front = await cdp.eval("(document.querySelector('#strasse .facade .doorman')||{}).textContent", await_promise=False)
    front_locked = await cdp.eval("!!document.querySelector('#strasse .facade.locked')", await_promise=False)
    record("kater: Royal-Schaufenster zeigt die Zitter-Sperre", front is not None and "Sie zittern" in front and front_locked is True, "seller=%s locked=%s" % (front, front_locked))
    await cdp.eval("Royal.enter()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=2.0)
    scene_who = await cdp.eval("(document.querySelector('#cutscene .cs-name')||{}).textContent", await_promise=False)
    scene_txt = await cdp.eval("(document.querySelector('#cutscene .cs-text')||{}).textContent", await_promise=False)
    await cdp.advance_cutscene(max_steps=6)
    screen = await cdp.eval("UI.current && UI.current.id", await_promise=False)
    record("kater: Royal.enter() am Zitter-Tag spielt kater.royal.zitter (Erzaehlung: Du), kein Eintritt", scene_who == "Du" and screen == "stadt", "who=%s screen=%s text=%s" % (scene_who, screen, (scene_txt or "")[:60]))
    # erstes Bier hebt den Zitter-Tag auf
    await cdp.eval("Story.evening()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'hub' && !UI.busy", timeout=3.0)
    await cdp.eval("Actions.beer()")
    zitter = await cdp.eval("State.s.story.flags.zitter", await_promise=False)
    front = await cdp.eval("StoryRules.gate(Story.story, State.s, 'royal')", await_promise=False)
    record("kater: erstes Bier hebt den Zitter-Tag auf", zitter is not True and front is None, "zitter=%s gate=%s" % (zitter, front))
    # Sofortiges Ende aus dem sleep-Hook heraus (Plan-1-Review, Critical #1): Leber 1 → Entzugsnacht −2 → „Bett" mitten in Story.night();
    # danach gibt es keine „Nächste Story": Die Wäsche ist nach dem Bett-Ende gesperrt, und ein stiller Rückfall in Die Schuld
    # soll nicht mehr passieren – „Und jetzt?" bietet nur „Zum Titel".
    await cdp.eval("State.s.story.vars.leber = 1; State.s.story.vars.pegel = 0; State.s.story.phase = 'evening'; State.save();")
    sleeping = await cdp.eval("Story.sleeping", await_promise=False)
    cs = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
    record("kater: kein Schlaf/keine Cutscene vor der Bett-Nacht", not sleeping and not cs, "sleeping=%s cutscene=%s" % (sleeping, cs))
    await cdp.eval("Story.night()", await_promise=False)
    ended = None
    shot_done = False
    final_labels = None
    for _ in range(80):
        if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            if not shot_done and await cdp.eval("(State.meta.storyRuns.kater || {}).last", await_promise=False) == "bett":
                await cdp.screenshot("kater-ende-bett.png"); shot_done = True
            labels = await cdp.eval("[...document.querySelectorAll('.cs-choices button')].map(b => b.textContent)", await_promise=False) or []
            if "Zum Titel" in labels:
                final_labels = labels
            await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
        ended = await cdp.eval("(State.meta.storyRuns.kater || {}).last", await_promise=False)
        on_title = await cdp.eval("document.querySelector('#title').hidden === false", await_promise=False)
        if ended == "bett" and on_title and not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            break
        await asyncio.sleep(0.15)
    record("kater: Ende Bett aus der Entzugsnacht", ended == "bett", "last=%s" % ended)
    trophy = await cdp.eval("Achievements.has('endeBett')", await_promise=False)
    record("kater: Trophaee endeBett vergeben", trophy is True, "trophy=%s" % trophy)
    record("kater: nach dem Bett-Ende keine Naechste Story (Waesche gesperrt), nur Zum Titel", final_labels == ["Zum Titel"], "labels=%s" % final_labels)
    on_title = await cdp.eval("document.querySelector('#title').hidden === false && !(State.s.story && State.s.story.id === 'schuld' && State.s.story.day === 1 && State.mode === 'story')", await_promise=False)
    record("kater: landet auf dem Titel statt still in Die Schuld", on_title, "on_title=%s" % on_title)
    # Frueher startete hier „Naechste Story" Die Schuld und stempelte ihr lastPlayed; seit dem Titel-Ende bleibt Die Schuld
    # in diesem Lauf ungespielt (0) und stuende bei der Titel-Wahl weiter unten gleichauf mit Die Waesche (Zufall).
    # Den Stempel deshalb ausdruecklich setzen: Die Schuld gilt als gespielt, Die Waesche als nie gespielt.
    await cdp.eval("State.meta.storyRuns.schuld = Object.assign({ lastPlayed: 0, endings: [] }, State.meta.storyRuns.schuld || {}, { lastPlayed: Date.now() }); State.saveMeta(); 0", await_promise=False)
    # Story-Therapie (Review-Fix #1): Life.therapy() darf im Kater NICHT die Anwalt-Szene therapy.done (Dr. Schmalz)
    # spielen, sondern nur die Doc-Szene kater.therapie aus dem buy:therapy-Hook. Dazu Story-Zustand direkt setzen.
    await cdp.navigate(URL_BASE + "?fresh&story=kater&prev=doc&day=12")
    await asyncio.sleep(0.7)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)  # Kapitel-3-Intro (kater.k3)
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=4.0)
    await settle()
    await cdp.eval("State.s.story.flags.abgestuerzt = true; State.s.balance = 6000; StoryRules.applyEffect(State.s, { enable: ['therapy'] }, Story.story); State.save(); UI.renderSide();")
    await cdp.eval("Life.therapy()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive() && document.querySelector('#cutscene .cs-name')", timeout=2.0)
    th_who = await cdp.eval("(document.querySelector('#cutscene .cs-name')||{}).textContent", await_promise=False)
    th_txt = await cdp.eval("(document.querySelector('#cutscene .cs-text')||{}).textContent", await_promise=False)
    await cdp.advance_cutscene(max_steps=6)
    await settle()
    nuechtern = await cdp.eval("State.s.story.flags.nuechtern", await_promise=False)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    record("kater: Story-Therapie spielt die Doc-Szene, nicht Dr. Schmalz", th_who == "Der Doc" and "Schmalz" not in (th_txt or "") and nuechtern is True and bal == 1000,
           "who=%s nuechtern=%s balance=%s text=%s" % (th_who, nuechtern, bal, (th_txt or "")[:50]))
    # Seitenleiste: Royal-Eintritt zeigt 100 EUR, nach bezahltem Eintritt am selben Tag „heute frei" (Review-Fix #12)
    await cdp.eval("State.s.car = 'audiA3'; if (!State.s.story.unlocked.rooms.includes('royal')) State.s.story.unlocked.rooms.push('royal'); State.save(); UI.renderSide();", await_promise=False)
    fee_txt = await cdp.eval("(document.querySelector('#side [data-action=royal] .price')||{}).textContent", await_promise=False)
    await cdp.eval("State.s.story.royalPaidDay = State.s.story.day; State.save(); UI.renderSide();", await_promise=False)
    free_txt = await cdp.eval("(document.querySelector('#side [data-action=royal] .price')||{}).textContent", await_promise=False)
    record("kater: Seitenleiste Royal 100 EUR, nach Eintritt heute frei", fee_txt == "100 €" and free_txt == "heute frei", "vorher=%s nachher=%s" % (fee_txt, free_txt))
    # zurueck in eine frische Kater-Story fuer den Kauf-Test
    await cdp.navigate(URL_BASE + "?fresh&story=kater&prev=doc&day=22")
    await asyncio.sleep(0.7)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)  # Kapitel-4-Intro (kater.k4)
    await cdp.wait_for("UI.current && UI.current.id === 'jobs' && !UI.busy", timeout=4.0)
    # ?day=22 überspringt Intro und Absturz-Nacht – das Flag setzen, sonst bleibt die Kauf-Aktion gesperrt
    await cdp.eval("State.s.story.flags.abgestuerzt = true; State.s.story.phase = 'evening'; State.s.balance = 60000; State.save(); UI.renderSide(); Story.renderDaybar();")
    await asyncio.sleep(0.3)
    has_action = await cdp.eval("!!document.querySelector('[data-story-action=\"kauf\"]')", await_promise=False)
    label = await cdp.eval("(document.querySelector('[data-story-action=\"kauf\"]')||{}).textContent", await_promise=False)
    record("kater: Kauf-Aktion in der Seitenleiste", has_action is True and label == "🔑 Über den Keller reden", "label=%s" % label)
    goal = await cdp.eval("document.querySelector('#dayGoal').textContent", await_promise=False)
    record("kater: Tagesziel nennt den Kaufpreis", goal is not None and "40.000" in goal, "goal=%s" % goal)
    await cdp.eval("Story.action('kauf')", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=2.0)
    clicked = await click_choice("Kaufen")
    record("kater: Kaufgespraech bietet Kaufen · 40.000 EUR", clicked is True, "clicked=%s" % clicked)
    ended = None
    shot_done = False
    for _ in range(80):
        if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            if not shot_done and await cdp.eval("State.s.story.ended", await_promise=False) == "wirt":
                await cdp.screenshot("kater-ende-wirt.png"); shot_done = True
            await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
        ended = await cdp.eval("State.s.story.ended", await_promise=False)
        if ended and not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            break
        await asyncio.sleep(0.15)
    record("kater: Ende Wirt sofort nach Kauf", ended == "wirt", "ended=%s" % ended)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    record("kater: Kaufpreis abgebucht", bal == 20000, "balance=%s" % bal)
    # Reentrancy-/Guard-Abdeckung fuer Story.checkImmediate (Plan 1, Task 6): das Ende kam aus einer
    # Szenen-Wahl (Story.action -> playScene -> applyEffects -> checkImmediate), nicht aus Story.night().
    finishing = await cdp.eval("Story.finishing", await_promise=False)
    record("kater: finishing-Flag nach dem Ende zurueckgesetzt", finishing is False, "finishing=%s" % finishing)
    phase = await cdp.eval("State.s.story && State.s.story.phase", await_promise=False)
    record("kater: keine Phasenaenderung nach sofortigem Ende", phase == "evening", "phase=%s" % phase)
    # „Zum Titel": Titel zeigt die am laengsten nicht gespielte zulaessige Story. Kater endete gerade mit „wirt“,
    # das schaltet Die Waesche neu frei (requires: kater, prevEndings enthaelt wirt) -- nie gespielt zaehlt als
    # aeltestes und sticht damit Die Schuld, die in diesem Lauf schon mehrfach mit frischem Zeitstempel lief.
    await cdp.wait_for("document.querySelector('#title').hidden === false", timeout=3.0)
    tag = await cdp.eval("(document.querySelector('#titleStoryTag')||{}).textContent", await_promise=False)
    record("kater: Titel nach dem Wirt-Ende zeigt Neue Story · Die Wäsche", tag is not None and "Die Wäsche" in tag, "tag=%s" % tag)
    trophy = await cdp.eval("Achievements.has('endeWirt')", await_promise=False)
    record("kater: Trophaee Hausherr (endeWirt) vergeben", trophy is True, "trophy=%s" % trophy)


async def scenario_stash(cdp):
    """Story 3 „Die Wäsche": Sperre nach Bett, Intro je Vorgängerende, Lieferung, Umsatz per Baccarat,
    Abrechnung ok, Überfall + Reparatur, Waffe, Schießerei, Brandt/Belege, Razzia-Ende; zweiter Lauf Kanal."""

    async def settle(max_rounds=60):
        """Story.night() laeuft fire-and-forget weiter und spielt dabei mehrere Cutscenes hintereinander
        (z. B. Lieferung -> Tisch-Szene, oder Abrechnung -> Kapitel-2-Intro). Ein reines wait_for() ohne
        Klicks kann in der Luecke zwischen zwei Szenen faelschlich "fertig" melden, obwohl die naechste
        Szene gleich darauf startet und unbeklickt haengen bleibt -- das faengt jede darauffolgende, direkt
        aufgerufene Engine-Methode (Story.evening/Story.action) im sleeping/busy-Guard lautlos ab (siehe
        scenario_kater.settle). Deshalb hier wie dort: klicken, bis sleeping/Cutscene/busy wirklich weg sind."""
        for _ in range(max_rounds):
            if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
                await cdp.advance_cutscene(max_steps=4)
            sleeping = await cdp.eval("Story.sleeping", await_promise=False)
            cs = await cdp.eval("__pt.cutsceneActive()", await_promise=False)
            busy = await cdp.eval("UI.busy", await_promise=False)
            if not sleeping and not cs and not busy:
                return True
            await asyncio.sleep(0.15)
        return False

    # Sperre: Kater endete im Bett
    await cdp.navigate(URL_BASE + "?fresh&mode=free")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)
    await cdp.eval("State.meta.storyRuns = { schuld: { lastPlayed: 1, endings: ['ehrlich'], last: 'ehrlich' }, kater: { lastPlayed: 2, endings: ['bett'], last: 'bett' } }; State.saveMeta();", await_promise=False)
    locked = await cdp.eval("Stories.locked().map(l => l.id + ':' + l.text)", await_promise=False)
    record("stash: nach Bett gesperrt mit eigenem Text", any(l.startswith("stash:") and "Bett" in l for l in locked), str(locked))
    # Start nach Wirt
    await cdp.navigate(URL_BASE + "?fresh&story=stash&prev=wirt")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=20)
    await cdp.wait_for("State.mode === 'story' && Story.s && Story.s.day === 1 && UI.current && !UI.busy", timeout=5.0)
    st = await cdp.eval("({ kredit: Story.s.vars.kredit, car: State.s.car, hz: !!Story.s.enabled.hinterzimmer, doorHidden: document.querySelector('[data-screen=\"hinterzimmer\"]') ? document.querySelector('[data-screen=\"hinterzimmer\"]').hidden : null })", await_promise=False)
    record("stash: Tag 1 – Kredit 0, Mercedes, Hinterzimmer sichtbar", st["kredit"] == 0 and st["car"] == "mercC" and st["hz"] is True, str(st))
    # Nacht 1: Lieferung
    await cdp.eval("Story.evening()")
    await asyncio.sleep(0.4)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    await settle()  # Lieferung- und Tisch-Szene laufen als zwei Cutscenes direkt hintereinander
    v = await cdp.eval("({ balance: State.s.balance, woche: Story.s.vars.woche, ziel: Story.s.vars.ziel, hzOpen: Story.s.unlocked.doors.includes('hinterzimmer') })", await_promise=False)
    record("stash: Lieferung Woche 1 – +10.000, Ziel 20.000, Hinterzimmer offen", v["balance"] == 16250 and v["woche"] == 1 and v["ziel"] == 20000 and v["hzOpen"], str(v))
    # Umsatz per Baccarat (Hand gestubbt: Push, damit das Geld bleibt)
    await cdp.eval("Story.evening()")
    await cdp.eval("UI.show('hinterzimmer')")
    await cdp.wait_for("UI.current && UI.current.id === 'hinterzimmer' && !UI.busy", timeout=3.0)
    umsatz = await cdp.eval("""(async function(){
      BaccaratRules.deal = function(){ return { player: [{val:'5',suit:'♠'},{val:'K',suit:'♥'}], banker: [{val:'2',suit:'♦'},{val:'3',suit:'♣'}], p: 5, b: 5, natural: false, winner: 'tie' }; };
      for (let i = 0; i < 2; i++) { document.querySelector('#bacBet').value = '10000'; Baccarat.place('player'); await Baccarat.deal(); }
      return { umsatz: Story.s.vars.umsatz, hz: Story.s.vars.umsatzHinterzimmer, balance: State.s.balance };
    })()""")
    record("stash: zwei Push-Hände à 10.000 → Umsatz 20.000, Geld bleibt", umsatz["umsatz"] == 20000 and umsatz["hz"] == 20000 and umsatz["balance"] == 16250, str(umsatz))
    # Tag 7 Abrechnung ok
    await cdp.eval("Story.s.day = 7; Story.s.phase = 'evening'; State.save(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    await settle()  # Abrechnung-Szene, danach Kapitel-2-Intro laufen direkt hintereinander
    a = await cdp.eval("({ balance: State.s.balance, zorn: Story.s.vars.zorn, belege: Story.s.vars.belege, ok: Story.s.vars.abrechnungenOk, pf: !!Story.s.enabled.pfandleihe })", await_promise=False)
    record("stash: Abrechnung ok – 11.000 weg, Zorn 0, Beleg 1, Pfandleihe offen", a["balance"] == 16250 - 11000 + 1250 and a["zorn"] == 0 and a["belege"] == 1 and a["ok"] == 1 and a["pf"], str(a))
    # Überfall erzwingen: Tür kaputt → 🔧 in der Lobby → reparieren
    await cdp.eval("Story.s.broken = { slots: 4000 }; State.save(); UI.show('hub');", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'hub' && !UI.busy", timeout=3.0)
    b = await cdp.eval("({ btn: !!document.querySelector('[data-screen=\"slots\"] .repair'), locked: Story.isLocked('slots'), reason: Story.lockReason('slots') })", await_promise=False)
    record("stash: kaputte Slots – 🔧-Knopf, gesperrt, Grund Zertrümmert", b["btn"] and b["locked"] and b["reason"] == "Zertrümmert", str(b))
    await cdp.eval("Story.repair('slots')")
    await asyncio.sleep(0.6)
    r = await cdp.eval("({ broken: Story.s.broken, rep: Story.s.vars.repariert_slots, locked: Story.isLocked('slots') })", await_promise=False)
    record("stash: Reparatur – Eintrag weg, Zähler 1, Tür offen", r["broken"] == {} and r["rep"] == 1 and not r["locked"], str(r))
    # Waffe kaufen
    await cdp.eval("State.s.balance = 40000; State.save(); UI.show('stadt');", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=3.0)
    n = await cdp.eval("document.querySelectorAll('#strasse .storefront, #strasse .facade').length", await_promise=False)
    record("stash: Stadt zeigt fünf Schaufenster (mit Pfandleihe)", n == 5, "n=%s" % n)
    await cdp.eval("Stadt.open('pfandleihe'); Stadt.buyWeapon(1)", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
    await cdp.advance_cutscene(max_steps=6)
    w = await cdp.eval("({ weapon: State.s.weapon, balance: State.s.balance })", await_promise=False)
    record("stash: Makarov gekauft", w["weapon"] == 1 and w["balance"] == 25000, str(w))
    # Schießerei (Hinterhalt) erzwingen: Nacht 9 mit gestubbtem rng über GangRules
    await cdp.eval("GangRules.raid = () => null; GangRules.ambushChance = () => 1; GangRules.ambushCount = () => 1; GangRules.drawWait = () => 40; Story.s.day = 9; Story.s.phase = 'evening'; State.save(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    await cdp.advance_cutscene(max_steps=6)
    # !UI.busy zusaetzlich abwarten: UI.current/Shootout.running kippen schon waehrend des Mount-Uebergangs,
    # bevor UI.show('shootout') selbst zurueckkehrt. Story.forceFight() prueft "Shootout.running" aber erst
    # NACH diesem Uebergang (Sicherheitsnetz fuer "Screen nicht bereit") -- tippt das Skript schneller, als
    # dieser Uebergang dauert, sieht die Pruefung faelschlich running=false (Duell laengst gewonnen) und
    # loest den Erzwingen-Aufruf mit einem synthetischen "aborted, won:false" auf, das den echten Sieg
    # verschluckt (kein Spieler ist so schnell -- drawWait ist real 1,5-4 s, hier nur zum Testen auf 40 ms
    # gestellt). Deshalb hier zusaetzlich auf busy=false warten, statt die Pruefung zu unterlaufen.
    await cdp.wait_for("UI.current && UI.current.id === 'shootout' && Shootout.running && !UI.busy", timeout=5.0)
    await cdp.eval("Shootout.ready()", await_promise=False)
    await cdp.wait_for("Shootout.phase === 'draw'", timeout=3.0)
    await cdp.eval("__pt.duelShoot()", await_promise=False)
    await asyncio.sleep(0.3)
    won = await cdp.eval("({ running: Shootout.running, won: Shootout.results[0] && Shootout.results[0].won })", await_promise=False)
    record("stash: Hinterhalt – Duell gewonnen", won["running"] is False and won["won"] is True, str(won))
    await cdp.click("#btnDuelDone")
    await cdp.wait_for("Story.s.day === 10 && !Story.sleeping", timeout=8.0)
    await cdp.advance_cutscene(max_steps=8)
    ruf = await cdp.eval("Story.s.vars.ruf", await_promise=False)
    record("stash: Ruf +1 nach gewonnenem Hinterhalt", ruf == 1, "ruf=%s" % ruf)
    # Brandt, Belege, Razzia → Ende Kommissar
    await cdp.eval("Story.s.day = 26; Story.s.phase = 'evening'; Story.s.vars.belege = 3; Story.s.vars.belegeOffen = 3; Story.s.flags.igor = true; State.save(); UI.renderSide(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.action('brandt')", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
    await cdp.advance_cutscene(max_steps=6)
    for _ in range(3):
        await cdp.eval("Story.action('beleg')", await_promise=False)
        await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
        await cdp.advance_cutscene(max_steps=4)
        await asyncio.sleep(0.3)
    ub = await cdp.eval("({ u: Story.s.vars.uebergeben, zorn: Story.s.vars.zorn, razzia: StoryRules.actionsFor(Story.story, State.s, 'bar').some(a => a.id === 'razzia') })", await_promise=False)
    record("stash: drei Belege übergeben ohne Risiko (Igor), Razzia-Knopf da", ub["u"] == 3 and ub["zorn"] == 0 and ub["razzia"], str(ub))
    await cdp.eval("Story.action('razzia')", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=3.0)
    await cdp.advance_cutscene(max_steps=12)
    await asyncio.sleep(0.5)
    ende = await cdp.eval("(State.meta.storyRuns.stash || {}).last", await_promise=False)
    record("stash: Ende Der Kommissar", ende == "kommissar", "last=%s" % ende)
    await cdp.advance_cutscene(max_steps=10)  # Insider/„Und jetzt?“ → Titel
    # Zweiter Lauf: Zorn 3 → Kanal sofort, nächste Story sauber
    await cdp.navigate(URL_BASE + "?fresh&story=stash&prev=stammgast&day=7")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=10)
    await cdp.wait_for("State.mode === 'story' && Story.s && Story.s.day === 7", timeout=5.0)
    await cdp.eval("Story.s.vars.zorn = 2; Story.s.vars.ziel = 20000; Story.s.vars.rueckgabe = 11000; Story.s.vars.woche = 1; State.s.balance = 0; Story.s.phase = 'evening'; State.save(); Story.renderDaybar();", await_promise=False)
    await cdp.eval("Story.night()", await_promise=False)
    await cdp.wait_for("__pt.cutsceneActive()", timeout=4.0)
    # Abrechnung/Kanal-Ende/Insider (fuer "stash" schon vergeben, siehe oben) bis zur Abschlussfrage durchklicken – ohne sie
    # zu beantworten. Die Wäsche ist die letzte Story: statt „Und jetzt?" + „Nächste Story" steht „Fortsetzung folgt…"
    # mit nur „Zum Titel" – kein Sprung in eine alte Story.
    final = None
    for _ in range(120):
        if not await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            await asyncio.sleep(0.15); continue
        labels = await cdp.eval("[...document.querySelectorAll('.cs-choices button')].map(b => b.textContent)", await_promise=False) or []
        if "Zum Titel" in labels:
            final = {"labels": labels, "text": await cdp.eval("(document.querySelector('#cutscene .cs-text')||{}).textContent", await_promise=False)}
            await cdp.screenshot("stash-ende-fortsetzung.png")
            break
        await cdp.eval("__pt.advance(null)", await_promise=False)
        await asyncio.sleep(0.15)
    k = await cdp.eval("({ last: (State.meta.storyRuns.stash || {}).last, ended: Story.s ? Story.s.ended : null })", await_promise=False)
    record("stash: Abrechnung ohne Geld bei Zorn 2 → Kanal sofort", k["last"] == "kanal", str(k))
    record("stash: letzte Story endet mit Fortsetzung folgt... und nur Zum Titel", final is not None and final["labels"] == ["Zum Titel"] and "Fortsetzung folgt" in (final["text"] or ""), str(final))
    await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
    await cdp.wait_for("document.querySelector('#title').hidden === false", timeout=8.0)
    on_title = await cdp.eval("document.querySelector('#title').hidden === false", await_promise=False)
    record("stash: danach der Titel, keine andere Story gestartet", on_title, "on_title=%s" % on_title)


async def scenario_roulette_chips(cdp):
    """Roulette: Chips legen/zurueck/leeren, ein Dreh wertet alles aus, Wie zuletzt; Bank-Sperre; Anlagen-Sperre."""
    await cdp.navigate(URL_BASE + "?fresh&screen=roulette")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.eval("State.meta.insider = []; State.meta.insiderClaimed = {}; State.saveMeta(); 0", await_promise=False)
    await cdp.eval("State.s.balance = 1000; State.save(); UI.setBalance(1000, {animate:false}); 0", await_promise=False)
    await cdp.eval("document.querySelector('#rouletteBet').value = 10; Roulette.place('number', 17, Roulette.cellFor('number', 17)); 0", await_promise=False)
    await cdp.eval("document.querySelector('#rouletteBet').value = 50; Roulette.place('red', null, Roulette.cellFor('red', null)); 0", await_promise=False)
    await cdp.eval("document.querySelector('#rouletteBet').value = 20; Roulette.place('even', null, Roulette.cellFor('even', null)); 0", await_promise=False)
    await asyncio.sleep(0.6)
    total = await cdp.eval("document.querySelector('#tableTotal').textContent", await_promise=False)
    stacks = await cdp.eval("[...document.querySelectorAll('.chip-stack')].map(e=>e.dataset.key+':'+e.textContent).sort().join(',')", await_promise=False)
    record("roulette: drei Chips liegen, Summe 80", total is not None and "80 €" in total and "3 Chips" in total and stacks == "even:20,n17:10,red:50", "total=%s stacks=%s" % (total, stacks))
    await cdp.click(".chip[data-chip=max]")
    await asyncio.sleep(0.2)
    maxval = await cdp.eval("document.querySelector('#rouletteBet').value", await_promise=False)
    record("roulette: Max-Chip zieht bereits liegende Chips ab (1000 - 80 = 920)", maxval == "920", "val=%s" % maxval)
    await cdp.screenshot("roulette-chips.png")
    await cdp.click("#btnUndo")
    await asyncio.sleep(0.2)
    n = await cdp.eval("Roulette.bets.length", await_promise=False)
    record("roulette: Chip zurueck entfernt den letzten", n == 2, "bets=%s" % n)
    await cdp.click("#btnClear")
    await asyncio.sleep(0.2)
    n = await cdp.eval("Roulette.bets.length", await_promise=False)
    spin_disabled = await cdp.eval("document.querySelector('#btnSpin').disabled", await_promise=False)
    record("roulette: Tisch leeren, Drehen gesperrt", n == 0 and spin_disabled is True, "bets=%s disabled=%s" % (n, spin_disabled))
    # erneut legen, Ergebnis 18 (rot, gerade) erzwingen: rouletteRoll = floor(rng*37) -> rng = 18.5/37; Luck ist 0
    await cdp.eval("document.querySelector('#rouletteBet').value = 10; Roulette.place('number', 17, Roulette.cellFor('number', 17)); document.querySelector('#rouletteBet').value = 50; Roulette.place('red', null, Roulette.cellFor('red', null)); 0", await_promise=False)
    await cdp.eval("window.__origRandom = Math.random; Math.random = () => 18.5/37; 0", await_promise=False)
    await cdp.click("#btnSpin")
    await asyncio.sleep(0.3)
    bal_mid = await cdp.eval("State.s.balance", await_promise=False)
    record("roulette: Einsatz 60 einmal abgezogen (Escrow)", bal_mid == 940, "bal=%s" % bal_mid)
    await asyncio.sleep(4.6)  # Kugel 4000 ms (animateBall) + wait(4100) im Spin-Ablauf + Puffer
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    status = await cdp.eval("document.querySelector('#rouletteStatus').textContent", await_promise=False)
    record("roulette: 18 -> 17 verliert, Rot gewinnt, netto +40", bal == 1040 and status is not None and "Rot ✓ +50" in status and "17 ✗" in status, "bal=%s status=%s" % (bal, status))
    last = await cdp.eval("JSON.stringify(Roulette.lastBets)", await_promise=False)
    await cdp.click("#btnRepeat")
    await asyncio.sleep(0.3)
    again = await cdp.eval("JSON.stringify(Roulette.bets)", await_promise=False)
    record("roulette: Wie zuletzt legt dieselben Chips", last is not None and again == last, "last=%s again=%s" % (last, again))
    # Bank: ein Kredit auf einmal
    await cdp.eval("UI.show('finance'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.eval("Finance.loanBank(500); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.3)
    disabled = await cdp.eval("[...document.querySelectorAll('[data-loan]')].every(b=>b.disabled)", await_promise=False)
    hint = await cdp.eval("document.querySelector('#bankHint').textContent", await_promise=False)
    debt = await cdp.eval("State.s.bankDebt", await_promise=False)
    record("bank: bei offenem Kredit alle Kredit-Knoepfe gesperrt, Hinweis sichtbar", debt == 500 and disabled is True and hint is not None and "tilgen" in hint, "debt=%s disabled=%s hint=%s" % (debt, disabled, hint))
    terms = await cdp.eval("document.querySelector('#bankTerms').textContent", await_promise=False)
    record("bank: Konditionen 8 %", terms is not None and "8 %" in terms, "terms=%s" % terms)
    # Limit-Kredit: erst tilgen (Guthaben reicht), dann bis zum Limit leihen
    await cdp.eval("Finance.repayBank(); 0", await_promise=False)
    await asyncio.sleep(0.3)
    await cdp.click("[data-loan=limit]")
    await asyncio.sleep(0.3)
    await cdp.advance_cutscene()
    await asyncio.sleep(0.3)
    debt_limit = await cdp.eval("State.s.bankDebt", await_promise=False)
    record("bank: Limit-Knopf leiht bis zum Kreditlimit (3000)", debt_limit == 3000, "debt=%s" % debt_limit)
    await cdp.screenshot("story-free-finance.png")
    # Anlagen: je Sorte eine
    await cdp.eval("UI.show('invest'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.eval("document.querySelector('#invBank').value = 20; Invest.invest('bank'); 0", await_promise=False)
    await asyncio.sleep(0.4)
    running = await cdp.eval("document.querySelector('.chalk.inv[data-type=bank] .inv-running').textContent", await_promise=False)
    form_hidden = await cdp.eval("document.querySelector('.chalk.inv[data-type=bank] .inv-form').classList.contains('hidden')", await_promise=False)
    inv = await cdp.eval("JSON.stringify(State.s.investments)", await_promise=False)
    record("anlagen: Festgeld laeuft, Karte zeigt laufende Anlage, Eingabe weg", form_hidden is True and running is not None and "20 €" in running and "6 Spins" in running and inv is not None and '"type":"bank"' in inv, "running=%s hidden=%s inv=%s" % (running, form_hidden, inv))
    bal_before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("Invest.invest('bank'); 0", await_promise=False)
    await asyncio.sleep(0.3)
    bal_after = await cdp.eval("State.s.balance", await_promise=False)
    n_inv = await cdp.eval("State.s.investments.length", await_promise=False)
    record("anlagen: zweites Festgeld abgelehnt", bal_after == bal_before and n_inv == 1, "before=%s after=%s n=%s" % (bal_before, bal_after, n_inv))
    await cdp.screenshot("story-free-invest.png")


async def scenario_perks(cdp):
    """XP -> Level 2 -> Skill; Umskillen; Insider-Wahl am Story-Ende; Croupier-Auge; Stallbursche; Mechaniker."""
    await cdp.navigate(URL_BASE + "?fresh&screen=skills")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.eval("localStorage.removeItem('keller37.meta'); State.meta.insider = []; State.meta.insiderClaimed = {}; State.saveMeta(); 0", await_promise=False)
    try:
        await _scenario_perks_body(cdp)
    finally:
        await cdp.eval("State.meta.insider = []; State.meta.insiderClaimed = {}; State.saveMeta(); 0", await_promise=False)


async def _scenario_perks_body(cdp):
    n = await cdp.eval("document.querySelectorAll('#skillCards .btn').length", await_promise=False)
    record("perks: ohne Punkt kein Waehlen-Button", n == 0, "buttons=%s" % n)
    await cdp.eval("Perks.addXp(Rules.XP_LEVELS[1], 'test'); 0", await_promise=False)
    await asyncio.sleep(0.4)
    pulsing = await cdp.eval("document.querySelector('#lvBadge').classList.contains('point')", await_promise=False)
    n = await cdp.eval("document.querySelectorAll('#skillCards .btn').length", await_promise=False)
    record("perks: Level 2 -> Badge pulsiert, 9 Skills waehlbar", pulsing is True and n == 9, "pulsing=%s buttons=%s" % (pulsing, n))
    await cdp.screenshot("skills.png")
    # Zusaetzliche XP auf Level 4 (XP_LEVELS[3] gesamt = 2 Skill-Punkte), damit nach dem Pick von
    # Zockerhaende noch ein Punkt frei ist -- sonst meldet canPickSkill fuer Brieftraegerherz
    # "points" statt "conflict" (Punkt-Pruefung kommt vor der Konflikt-Pruefung), und der naechste
    # Check koennte den Konflikt-Grund nie sehen.
    await cdp.eval("Perks.addXp(Rules.XP_LEVELS[3] - Rules.XP_LEVELS[1], 'test'); 0", await_promise=False)
    await asyncio.sleep(0.4)
    await cdp.eval("Perks.pick('zockerhaende'); 0", await_promise=False)
    await asyncio.sleep(0.3)
    skills = await cdp.eval("JSON.stringify(State.s.skills)", await_promise=False)
    conflict = await cdp.eval("[...document.querySelectorAll('#skillCards .skill-card')].find(c=>c.textContent.includes('Brieftr')).querySelector('.reason').textContent", await_promise=False)
    record("perks: Skill aktiv, Konflikt-Grund sichtbar", skills == '["zockerhaende"]' and conflict is not None and "Passt nicht" in conflict, "skills=%s conflict=%s" % (skills, conflict))
    await cdp.eval("State.s.balance = 5000; State.save(); UI.setBalance(5000, {animate:false}); Perks.respec(); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.advance_cutscene(label_hint="Ja, alles vergessen")
    await asyncio.sleep(0.4)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    skills = await cdp.eval("JSON.stringify(State.s.skills)", await_promise=False)
    record("perks: Umskillen kostet 2000 und leert die Skills", bal == 3000 and skills == "[]", "bal=%s skills=%s" % (bal, skills))
    # Insider-Wahl am Story-Ende: Statistik-Panel -> Insider-Angebot -> erst danach "Nächste Story / Zum Titel"
    await cdp.navigate(URL_BASE + "?fresh&story=schuld&ending=ehrlich")
    await asyncio.sleep(1.5)
    await cdp.inject_helpers()
    await cdp.eval("State.meta.insider = []; State.meta.insiderClaimed = {}; State.saveMeta(); 0", await_promise=False)
    n_choices = 0
    for _ in range(40):
        n_choices = await cdp.eval("document.querySelectorAll('.cs-choices button').length", await_promise=False)
        if n_choices == 3:
            break
        await cdp.eval("__pt.advance(null)", await_promise=False)
        await asyncio.sleep(0.15)
    record("insider: Story-Ende bietet 3 Upgrades (vor der Nächste-Story-Wahl)", n_choices == 3, "choices=%s" % n_choices)
    await cdp.screenshot("insider-offer.png")
    await cdp.eval("__pt.advance(null)", await_promise=False)
    await asyncio.sleep(0.5)
    ins = await cdp.eval("JSON.stringify(State.meta.insider)", await_promise=False)
    claimed = await cdp.eval("JSON.stringify(State.meta.insiderClaimed)", await_promise=False)
    record("insider: Wahl in Meta gespeichert, Story-Teil abgehakt", ins is not None and ins != "[]" and claimed is not None and "schuld" in claimed, "insider=%s claimed=%s" % (ins, claimed))
    await cdp.advance_cutscene(max_steps=3, label_hint="Zum Titel")
    # Croupier-Auge + Stallbursche im freien Spiel
    await cdp.navigate(URL_BASE + "?fresh&screen=roulette")
    await asyncio.sleep(1.0)
    await cdp.inject_helpers()
    await cdp.eval("State.meta.insider = ['croupierauge', 'stallbursche', 'mechaniker']; State.saveMeta(); Perks.refreshExcluded(); Roulette.applyExcluded(); 0", await_promise=False)
    await asyncio.sleep(0.3)
    n_ex = await cdp.eval("document.querySelectorAll('.rcell.excluded').length", await_promise=False)
    never = await cdp.eval("(()=>{const ex=State.s.insiderExcluded; for(let i=0;i<200;i++){ if(ex.includes(Rules.rouletteRoll(Math.random, ex))) return false; } return true; })()", await_promise=False)
    record("insider: Croupier-Auge graut 12 Zahlen aus, Kugel faellt nie dorthin", n_ex == 12 and never is True, "excluded=%s never=%s" % (n_ex, never))
    await cdp.screenshot("roulette-croupierauge.png")
    await cdp.eval("UI.show('horses'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    lame = await cdp.eval("(()=>{const r=document.querySelector('.runner.lame'); return r ? parseInt(r.id.slice(2),10) : null})()", await_promise=False)
    sel = await cdp.eval("State.s.selectedHorse", await_promise=False)
    record("insider: Stallbursche markiert ein lahmes Pferd (nicht das gewaehlte)", lame is not None and lame != sel, "lame=%s selected=%s" % (lame, sel))
    await cdp.eval("UI.show('slots'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.eval("State.s.balance = 1000; State.s.mechRespins = 5; State.save(); window.__origRandom = Math.random; Math.random = () => 0.0; 0", await_promise=False)
    # Math.random -> 0 liefert drei 🍒 (Drilling) – für eine Niete andere Werte: 0.05 / 0.4 / 0.8 -> 🍒 🍇 💎
    await cdp.eval("let q=[0.05,0.4,0.8,0.99,0.99]; Math.random = () => q.length ? q.shift() : 0.99; 0", await_promise=False)
    await cdp.click("#btnSpin")
    await asyncio.sleep(2.8)
    await cdp.eval("Math.random = window.__origRandom; 0", await_promise=False)
    holds = await cdp.eval("[...document.querySelectorAll('.hold-btn')].filter(b=>!b.classList.contains('hidden')).length", await_promise=False)
    record("insider: Mechaniker zeigt nach Niete Festhalten-Buttons", holds == 3, "holds=%s" % holds)


async def scenario_royal_look(cdp):
    """Art-deco-Paket: Zone + Vorhang beim Betreten/Verlassen, Fassade in drei Zustaenden,
    Kater-HUD, Freispiel-Banner, Bankrott-Blackout, Goldregen."""
    # Fassade ohne Auto
    await cdp.navigate(URL_BASE + "?fresh&mode=free&screen=stadt")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    await cdp.eval("localStorage.removeItem('keller37.meta')", await_promise=False)
    f = await cdp.eval("(function(){ const f=document.querySelector('.facade'); return f && {locked: f.classList.contains('locked'), sign: f.querySelector('.brass-sign').textContent, doorman: !!f.querySelector('.doorman')}; })()", await_promise=False) or {}
    record("fassade: ohne Auto gesperrt mit Parkservice-Schild", f.get("locked") and "Parkservice" in (f.get("sign") or "") and not f.get("doorman"), f)
    # Fassade mit Auto + Zone beim Betreten
    await cdp.eval("State.s.car = 'audiA3'; State.s.balance = 5000; State.s.flags.royalSeen = true; State.save(); Stadt.render();", await_promise=False)
    f = await cdp.eval("(function(){ const f=document.querySelector('.facade'); return {locked: f.classList.contains('locked'), sign: f.querySelector('.brass-sign').textContent}; })()", await_promise=False) or {}
    record("fassade: mit Auto offen, Schild Eintritt 100", not f.get("locked") and "100" in (f.get("sign") or ""), f)
    zone_before = await cdp.eval("document.body.dataset.zone", await_promise=False)
    await cdp.eval("document.querySelector('.facade').click()", await_promise=False)
    await asyncio.sleep(0.15)
    fade_on = await cdp.eval("document.querySelector('#zonefade').classList.contains('on')", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'royal' && !UI.busy", timeout=4.0)
    zone_after = await cdp.eval("document.body.dataset.zone", await_promise=False)
    sub = await cdp.eval("getComputedStyle(document.querySelector('#brandSub')).display", await_promise=False)
    record("zone: Vorhang beim Betreten, Zone royal, Untertitel sichtbar", zone_before == "keller" and fade_on is True and zone_after == "royal" and sub == "block",
           "before=%s fade=%s after=%s sub=%s" % (zone_before, fade_on, zone_after, sub))
    portals = await cdp.eval("document.querySelectorAll('.portal').length", await_promise=False)
    record("lobby: fünf Portale", portals == 5, "portals=%s" % portals)
    # Mega Seven: Freispiel-Banner + Gewinnlinie
    await cdp.eval("UI.show('megaslots')")
    mega = await cdp.eval("""(async function(){
      /* Gewinnlinie 🍒×3 (Reihe 0) + 3 Scatter ⭐ (Reihe 2, Walzen 0-2): sichere Freispiele + eine
         Gewinnlinie, aber Auszahlung (40 €) bleibt weit unter RoyalRules.GUEST_WIN (5000) -- eine
         5er-Reihe 7️⃣ (wie ursprünglich hier verdrahtet) loest sonst Royal.onWin()/Cutscene('royal.guest')
         aus, die auf einen Klick wartet und den Test aufhaengt. */
      RoyalRules.megaRoll = function(){ return [['🍒','💎','⭐'],['🍒','BAR','⭐'],['🍒','🔔','⭐'],['BAR','🍒','7️⃣'],['💎','7️⃣','BAR']]; };
      RoyalRules.megaLuckOverride = function(g){ return g; };
      document.querySelector('#megaBet').value = '100';
      await MegaSlots.spin();
      return { banner: document.querySelector('#megaFree').classList.contains('show'), free: MegaSlots.freeLeft,
               lines: document.querySelectorAll('#megaLinesSvg polyline').length, cls: document.querySelector('.mega-machine').classList.contains('free') };
    })()""")
    record("mega: Freispiel-Banner und goldene Gewinnlinie", mega and mega.get("banner") and mega.get("free", 0) > 0 and mega.get("lines", 0) >= 1 and mega.get("cls"), mega)
    # Echte Walzen: waehrend des Drehs laufen Streifen (rolling), Ergebnis landet in den Zielzellen; Freispiel-Trigger zeigt das Banner
    await cdp.eval("MegaSlots.freeLeft = 0; MegaSlots.freeRun = null; MegaSlots.syncFree(); State.s.balance = 20000; State.save();", await_promise=False)
    await cdp.eval("window.__mega = MegaSlots.spin(); 0", await_promise=False)
    rolling = await cdp.wait_for("document.querySelectorAll('.mega-reel.rolling').length === 5 && document.querySelector('.mega-machine').classList.contains('rolling')", timeout=1.5)
    free_banner = await cdp.wait_for("document.querySelector('#megaBanner').classList.contains('show') && document.querySelector('#megaBanner').classList.contains('free')", timeout=6.0)
    scat = await cdp.eval("document.querySelectorAll('.mega-grid .cell.scatter').length", await_promise=False)
    await cdp.eval("__mega", timeout=15)
    landed = await cdp.eval("(function(){ const t = [['🍒','💎','⭐'],['🍒','BAR','⭐'],['🍒','🔔','⭐'],['BAR','🍒','7️⃣'],['💎','7️⃣','BAR']]; for (let r=0;r<5;r++) for (let w=0;w<3;w++) { const el = document.querySelector('.cell[data-reel=\"'+r+'\"][data-row=\"'+w+'\"]'); if (!el || el.textContent !== t[r][w]) return false; } return document.querySelectorAll('.mega-reel.rolling').length === 0; })()", await_promise=False)
    record("mega: Walzenstreifen laufen, Freispiel-Banner mit Sternen, Ziel landet", rolling and free_banner and scat == 3 and landed, "rolling=%s banner=%s scatter=%s landed=%s" % (rolling, free_banner, scat, landed))
    # Spannung + Big Win: 💎 auf Walze 0-2 der Mittellinie → letzte zwei Walzen laufen laenger (tense), 💎×5 = 2.000 € = 20× → BIG WIN
    await cdp.eval("MegaSlots.freeLeft = 0; MegaSlots.freeRun = null; MegaSlots.syncFree(); RoyalRules.megaRoll = function(){ return [['🍒','💎','BAR'],['🔔','💎','🍒'],['BAR','💎','🔔'],['🍒','💎','BAR'],['🔔','💎','🍒']]; }; window.__mega = MegaSlots.spin(); 0", await_promise=False)
    tense = await cdp.wait_for("document.querySelector('.mega-machine').classList.contains('tense') && document.querySelectorAll('.mega-reel.rolling').length === 2", timeout=3.0)
    big = await cdp.wait_for("document.querySelector('#megaBanner').classList.contains('show') && document.querySelector('#megaBanner').classList.contains('big')", timeout=8.0)
    title = await cdp.eval("document.querySelector('#megaBanner .mb-title').textContent", await_promise=False)
    res = await cdp.eval("__mega", timeout=15)
    record("mega: Spannung nach drei Diamanten, dann BIG WIN-Banner", tense and big and title == "BIG WIN" and res and res.get("tier") == "big" and res.get("payout") == 2000, "tense=%s big=%s title=%s res=%s" % (tense, big, title, res))
    # Auto-Spin: drei Runden am Stueck mit Nieten, dann von selbst Schluss; Knopf zeigt waehrenddessen Stopp (n)
    await cdp.eval("RoyalRules.megaRoll = function(){ return [['🍒','🔔','BAR'],['🔔','BAR','🍒'],['💎','🍒','🔔'],['🍒','🔔','BAR'],['🔔','BAR','🍒']]; }; RoyalRules.MEGA.AUTO_ROUNDS = 3; State.s.balance = 5000; UI.setBalance(5000, {animate:false}); window.__auto = MegaSlots.autoToggle(); 0", await_promise=False)
    stop_lbl = await cdp.wait_for("document.querySelector('#btnMegaAuto').textContent === 'Stopp (3)'", timeout=1.0)
    await cdp.eval("__auto", timeout=30)
    auto_done = await cdp.eval("({ auto: MegaSlots.auto, lbl: document.querySelector('#btnMegaAuto').textContent, bal: State.s.balance, spinning: MegaSlots.spinning })", await_promise=False)
    await cdp.eval("RoyalRules.MEGA.AUTO_ROUNDS = 10; MegaSlots.syncAuto();", await_promise=False)
    record("mega: Auto-Spin dreht 3 Runden und stoppt", stop_lbl and auto_done and auto_done.get("auto") == 0 and auto_done.get("lbl") == "Auto ×3" and auto_done.get("bal") == 4700 and not auto_done.get("spinning"), "stop=%s %s" % (stop_lbl, auto_done))
    # Glücksrad: Bankrott -> Blackout-Klasse + Sylvie-Toast
    # Die Blackout-Klasse liegt nur zwischen dem 4.6s-Dreh-Wait und dem 900ms-Timeout danach an
    # (~4.6-5.5s); ein einzelner fester sleep(4.8) traf dieses Fenster unter Last (viele vorige
    # Szenarien im selben Tab) nicht zuverlässig -- daher wird gepollt statt einmalig geprueft.
    await cdp.eval("UI.show('wheel')")
    await cdp.eval("""(function(){
      RoyalRules.wheelSpin = function(){ return 0; };
      RoyalRules.wheelLuckOverride = function(i){ return i; };
      document.querySelector('#wheelBet').value = '100';
      window.__wheelSpin = Wheel.spin();
    })()""", await_promise=False)
    black = await cdp.wait_for("document.querySelector('.wheel-panel').classList.contains('blackout')", timeout=8.0)
    toast = await cdp.eval("document.querySelector('#toasts').textContent.includes('Das Haus dankt')", await_promise=False)
    seg = await cdp.eval("document.querySelector('.wheel .seg.bust') !== null", await_promise=False)
    await cdp.eval("window.__wheelSpin", timeout=10)
    wheel = {"black": black, "toast": toast, "seg": seg}
    record("wheel: Bankrott dunkelt ab, Sylvie-Toast, Bust-Segmente", wheel and wheel.get("black") and wheel.get("toast") and wheel.get("seg"), wheel)
    # Goldregen + zurueck in die Stadt = Zone keller
    rain = await cdp.eval("Royal.goldRain(); document.querySelectorAll('.gold-drop').length", await_promise=False)
    record("royal: Goldregen erzeugt Partikel", (rain or 0) >= 12, "drops=%s" % rain)
    await cdp.eval("UI.show('royal')")
    await cdp.wait_for("UI.current && UI.current.id === 'royal' && !UI.busy", timeout=4.0)
    # Rueckweg kostet (freies Spiel, kein Gast): Sylvie fragt nach. "Bleiben" -> Royal, nochmal + "Gehen" -> Stadt
    await cdp.click("#royalLeave")
    asked = await cdp.wait_for("__pt.cutsceneActive() && document.querySelectorAll('.cs-choices button').length === 2", timeout=4.0)
    text = await cdp.eval("document.querySelector('.cs-bubble').textContent", await_promise=False) or ""
    labels = await cdp.eval("[...document.querySelectorAll('.cs-choices button')].map(b => b.textContent)", await_promise=False)
    record("royal: Verlassen fragt nach (Sylvie, 100 EUR, Bleiben/Gehen)", asked and "100" in text and labels == ["Bleiben", "Gehen"], "asked=%s labels=%s" % (asked, labels))
    await cdp.eval("__pt.advance('Bleiben')", await_promise=False)
    await asyncio.sleep(0.4)
    stayed = await cdp.eval("!__pt.cutsceneActive() && UI.current.id === 'royal' && document.body.dataset.zone === 'royal'", await_promise=False)
    record("royal: Bleiben -> weiter im Royal", stayed, "stayed=%s" % stayed)
    await cdp.click("#royalLeave")
    await cdp.wait_for("__pt.cutsceneActive() && document.querySelectorAll('.cs-choices button').length === 2", timeout=4.0)
    await cdp.eval("__pt.advance('Gehen')", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=4.0)
    zone_back = await cdp.eval("document.body.dataset.zone", await_promise=False)
    record("zone: zurueck in die Stadt = keller", zone_back == "keller", "zone=%s" % zone_back)
    # Gast des Hauses: kein Dialog
    await cdp.eval("State.s.flags.royalGuest = true; State.save(); UI.show('royal')", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'royal' && !UI.busy", timeout=4.0)
    await cdp.click("#royalLeave")
    await asyncio.sleep(0.3)
    no_ask = await cdp.eval("!__pt.cutsceneActive()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=4.0)
    record("royal: Gast des Hauses verlaesst ohne Nachfrage", no_ask, "no_ask=%s" % no_ask)
    await cdp.eval("State.s.flags.royalGuest = false; State.save();", await_promise=False)
    # Kater-HUD + Zitter + Tuersteher
    await cdp.navigate(URL_BASE + "?fresh&story=kater&prev=doc&day=5")
    await asyncio.sleep(1.2)
    await cdp.inject_helpers()
    await cdp.advance_cutscene(max_steps=30)
    hud = await cdp.eval("""(function(){
      Story.s.vars.leber = 25; Story.s.vars.pegel = 2; Story.s.vars.deckel = 250; Story.s.flags.zitter = true; State.s.car = 'audiA3'; State.save(); UI.renderWallet();
      const bar = document.querySelector('.hud-leber .fill'); const kr = document.querySelectorAll('.hud-pegel .krug.on').length;
      return { width: bar && bar.style.width, danger: !!document.querySelector('.hud-leber.danger'), kruege: kr,
               marks: (document.querySelector('.hud-deckel .coaster') || {}).textContent, zitter: document.body.classList.contains('zitter'),
               note: document.querySelector('#notes').textContent.includes('Zittern') };
    })()""", await_promise=False) or {}
    record("kater-hud: Leber 25 rot, 2 Kruege, 5 Striche, Zittern", hud.get("width") == "25%" and hud.get("danger") and hud.get("kruege") == 2 and hud.get("zitter") and hud.get("note") and hud.get("marks") == "|||||", hud)
    # Nach dem Intro laeuft der Tag-1-Morgen (einrichten/niereWeg) noch fire-and-forget bis zur
    # Pinnwand (UI.busy bleibt bis dahin true) -- UI.show() ist ein No-Op solange busy, also erst warten
    await cdp.wait_for("!UI.busy && !__pt.cutsceneActive()", timeout=5.0)
    await cdp.eval("UI.show('stadt')")
    door = await cdp.eval("(function(){ const f=document.querySelector('.facade'); return f && {gated: f.classList.contains('gated'), doorman: !!f.querySelector('.doorman'), txt: (f.querySelector('.doorman')||{}).textContent}; })()", await_promise=False) or {}
    record("fassade: Zitter-Tag zeigt Tuersteher", door.get("gated") and door.get("doorman") and "zittern" in (door.get("txt") or "").lower(), door)


async def scenario_poker(cdp):
    """Poker: Tuer im Hub, festes Deck (Full House gegen Paar), Setzen -> Showdown, Kontostand und Achievement."""
    await cdp.navigate(URL_BASE + "?fresh&mode=free&screen=hub")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    door = await cdp.eval("!!document.querySelector('.door[data-screen=\"poker\"]')", await_promise=False)
    record("poker: Tuer im Keller-Hub", door is True)
    await cdp.eval("UI.show('poker'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    # Deck: pop() zieht vom Ende -> zuerst 5 Spielerkarten (Full House K/3), dann 5 Wirtkarten (Paar 9),
    # dann die 3 Tauschkarten des Wirts (junk: er behaelt nur das Paar) -> Ergebnis deterministisch.
    await cdp.eval(r"""(function(){
      const C = (val, suit) => ({ val, suit });
      const player = [C('K','♠'), C('K','♥'), C('K','♦'), C('3','♣'), C('3','♠')];
      const wirt = [C('9','♠'), C('9','♥'), C('2','♦'), C('5','♣'), C('7','♠')];
      const junk = [C('4','♥'), C('6','♦'), C('J','♣')];
      const used = [...player, ...wirt, ...junk];
      const rest = Rules.newDeck(Math.random).filter(c => !used.some(x => x.val === c.val && x.suit === c.suit));
      Poker.forceDeck = [...rest, ...junk.slice().reverse(), ...wirt.slice().reverse(), ...player.slice().reverse()];
      State.s.balance = 1000; State.save(); UI.setBalance(1000, {animate:false});
    })(); 0""", await_promise=False)
    await cdp.click("#btnPkDeal")
    await cdp.wait_for("Poker.round && Poker.round.phase === 'draw'", timeout=5.0)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    n_player = await cdp.eval("document.querySelectorAll('#pkPlayerCards .pcard').length", await_promise=False)
    n_hidden = await cdp.eval("document.querySelectorAll('#pkWirtCards .pcard.hidden-card').length", await_promise=False)
    hand = await cdp.eval("document.querySelector('#pkHandName').textContent", await_promise=False)
    record("poker: Geben bucht Ante ab, 5 offen / 5 verdeckt, Handname", bal == 990 and n_player == 5 and n_hidden == 5 and hand == "Full House", "bal=%s player=%s hidden=%s hand=%s" % (bal, n_player, n_hidden, hand))
    await cdp.screenshot("poker.png")
    await cdp.click("#btnPkDraw")   # Behalten
    await cdp.wait_for("Poker.round && Poker.round.phase === 'bet'", timeout=5.0)
    wdraw = await cdp.eval("document.querySelector('#pkWirtDraw').textContent", await_promise=False)
    record("poker: Wirt tauscht 3 (Paar haelt)", wdraw == "tauscht 3", wdraw)
    await cdp.click("#btnPkBet")    # Setzen -> Wirt hat Paar 9 -> geht mit -> Showdown
    await cdp.wait_for("!Poker.inRound", timeout=8.0)
    await asyncio.sleep(0.6)
    bal = await cdp.eval("State.s.balance", await_promise=False)
    ach = await cdp.eval("Achievements.has('fullhouse')", await_promise=False)
    status = await cdp.eval("document.querySelector('#pkStatus').textContent", await_promise=False)
    # Pot 40 (2 Antes + Setzen + Call), Spieler-Einsatz 20 -> 1000 + 20
    record("poker: Showdown gewonnen (Full House schlaegt Paar), Kontostand +20, Achievement", bal == 1020 and ach is True and "Full House" in status and "Paar" in status, "bal=%s ach=%s status=%s" % (bal, ach, status))
    # Aussteigen mitten in der Runde: Screen verlassen -> Einsatz weg, Toast
    await cdp.click("#btnPkDeal")
    await cdp.wait_for("Poker.round && Poker.round.phase === 'draw'", timeout=5.0)
    before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("UI.show('hub'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    after = await cdp.eval("State.s.balance", await_promise=False)
    in_round = await cdp.eval("Poker.inRound", await_promise=False)
    record("poker: Screen verlassen laesst die Hand fallen (Ante weg)", after == before and in_round is False, "before=%s after=%s inRound=%s" % (before, after, in_round))
    # Story 1: Poker erst ab Kapitel 2 offen
    await cdp.navigate(URL_BASE + "?fresh&story=schuld")
    await asyncio.sleep(1.5)
    await cdp.inject_helpers()
    locked = await cdp.eval("Story.isLocked('poker')", await_promise=False)
    record("poker: in Story 1 Tag 1 gesperrt", locked is True, "locked=%s" % locked)


async def scenario_stud(cdp):
    """Caribbean Stud im Royal: Portal, festes Deck (Zwei Paare gegen Paar), Mitgehen -> Bonus 2:1, Dealer nicht
    qualifiziert -> Ante 1:1, Passen, Flush -> Achievement, Screen verlassen laesst die Hand fallen, Insider-Blick mit Kappe."""
    await cdp.navigate(URL_BASE + "?fresh&mode=free&screen=royal")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    portal = await cdp.eval("!!document.querySelector('.portal[data-screen=\"stud\"]')", await_promise=False)
    record("stud: Portal in der Royal-Lobby", portal is True)
    await cdp.screenshot("royal-lobby.png")
    await cdp.eval("State.s.car = 'audiA3'; State.s.balance = 1000; State.save(); UI.renderWallet(); 0", await_promise=False)
    await cdp.eval("UI.show('stud'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    zone = await cdp.eval("document.body.dataset.zone", await_promise=False)
    record("stud: Zone royal", zone == "royal", zone)
    # forceDeck wird von oben abwechselnd verteilt: Index 0,2,4,6,8 Spieler, 1,3,5,7,9 Dealer
    def deck_js(player, dealer):
        cards = []
        for p, d in zip(player, dealer):
            cards.append(p); cards.append(d)
        arr = ", ".join("C('%s','%s')" % (c[:-1], c[-1]) for c in cards)
        return ("(function(){ const C = (val, suit) => ({ val, suit }); const top = [%s];"
                " const rest = Rules.newDeck(Math.random).filter(c => !top.some(x => x.val === c.val && x.suit === c.suit));"
                " Stud.forceDeck = [...top, ...rest]; })(); 0") % arr

    async def play(player, dealer, ante, action):
        await cdp.eval(deck_js(player, dealer), await_promise=False)
        await cdp.eval("document.querySelector('.chip[data-chip=\"%d\"]').click(); 0" % ante, await_promise=False)
        before = await cdp.eval("State.s.balance", await_promise=False)
        await cdp.click("#btnStudDeal")
        await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
        after_deal = await cdp.eval("State.s.balance", await_promise=False)
        hidden = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
        if action == "shot":
            await cdp.screenshot("royal-stud.png")
            action = "call"
        await cdp.click("#btnStudCall" if action == "call" else "#btnStudFold")
        await cdp.wait_for("!Stud.inRound", timeout=8.0)
        await asyncio.sleep(0.5)
        after = await cdp.eval("State.s.balance", await_promise=False)
        status = await cdp.eval("document.querySelector('#studStatus').textContent", await_promise=False)
        return before, after_deal, hidden, after, status

    # Trophaeen und Insider-Wissen (State.meta.insider) liegen im Meta-Speicher und ueberleben ?fresh und fruehere Laeufe im selben Chrome-Profil: hier zuruecksetzen
    await cdp.eval("State.meta.insider = []; State.meta.achievements = State.meta.achievements.filter(id => id !== 'karibik'); State.saveMeta(); 0", await_promise=False)
    # 1) Zwei Paare gegen Paar 9, Ante 100: Bet 200, Bonus 2:1 -> net +500
    b0, bd, hidden, b1, status = await play(["K♠", "K♥", "7♣", "7♠", "2♥"], ["9♦", "9♣", "5♠", "4♦", "Q♥"], 100, "shot")
    ach = await cdp.eval("Achievements.has('karibik')", await_promise=False)
    record("stud: Geben bucht Ante ab, 4 Dealer-Karten verdeckt, Mitgehen gewinnt Bonus 2:1 (+500)",
           bd == b0 - 100 and hidden == 4 and b1 == b0 + 500 and "Bonus 2:1" in status and ach is False,
           "b0=%s deal=%s hidden=%s b1=%s status=%s ach=%s" % (b0, bd, hidden, b1, status, ach))
    # 2) Dealer A-Q nicht qualifiziert: Ante 1:1, Bet zurueck -> net +100
    b0, bd, hidden, b1, status = await play(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"], 100, "call")
    record("stud: Dealer nicht qualifiziert zahlt Ante 1:1 (+100)", b1 == b0 + 100 and "nicht qualifiziert" in status, "b0=%s b1=%s status=%s" % (b0, b1, status))
    # 3) Passen: Ante weg
    b0, bd, hidden, b1, status = await play(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "K♦", "J♣", "9♥", "2♠"], 100, "fold")
    hidden_after = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
    record("stud: Passen verliert die Ante, Dealer bleibt verdeckt", b1 == b0 - 100 and hidden_after == 4 and "Gepasst" in status, "b0=%s b1=%s hidden=%s status=%s" % (b0, b1, hidden_after, status))
    # 4) Flush gegen Paar -> Achievement
    b0, bd, hidden, b1, status = await play(["2♥", "5♥", "8♥", "J♥", "K♥"], ["9♦", "9♣", "5♠", "4♦", "Q♠"], 100, "call")
    ach = await cdp.eval("Achievements.has('karibik')", await_promise=False)
    record("stud: Flush gewinnt Bonus 5:1 (+1100) und Trophaee Karibische Nacht", b1 == b0 + 1100 and ach is True, "b0=%s b1=%s ach=%s status=%s" % (b0, b1, ach, status))
    # 5) Screen verlassen mitten in der Hand -> Ante verfallen
    await cdp.eval(deck_js(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"]), await_promise=False)
    await cdp.click("#btnStudDeal")
    await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
    before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("UI.show('royal'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    after = await cdp.eval("State.s.balance", await_promise=False)
    in_round = await cdp.eval("Stud.inRound", await_promise=False)
    rnd = await cdp.eval("Stud.round === null", await_promise=False)
    toast = await cdp.eval("document.querySelector('#toasts').textContent.includes('Hand aufgegeben')", await_promise=False)
    record("stud: Screen verlassen laesst die Hand fallen (Ante weg, Toast)", after == before and in_round is False and rnd is True and toast is True,
           "before=%s after=%s inRound=%s round=null:%s toast=%s" % (before, after, in_round, rnd, toast))
    # 6) Insider Sylvies Blick: Ante 100 -> zweite Dealer-Karte offen; Ante 500 -> verdeckt + Hinweis
    await cdp.eval("State.meta.insider = ['sylviesblick']; State.saveMeta(); 0", await_promise=False)
    await cdp.eval("UI.show('stud'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.eval(deck_js(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"]), await_promise=False)
    await cdp.eval("document.querySelector('.chip[data-chip=\"100\"]').click(); 0", await_promise=False)
    await cdp.click("#btnStudDeal")
    await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
    hidden_peek = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
    hint_peek = await cdp.eval("document.querySelector('#studPeek').textContent", await_promise=False)
    await cdp.click("#btnStudFold")
    await cdp.wait_for("!Stud.inRound", timeout=5.0)
    await cdp.eval("State.s.balance = 5000; State.save(); UI.renderWallet(); 0", await_promise=False)
    await cdp.eval(deck_js(["9♠", "9♥", "K♦", "4♣", "2♠"], ["A♠", "Q♦", "J♣", "9♥", "2♠"]), await_promise=False)
    await cdp.eval("document.querySelector('.chip[data-chip=\"500\"]').click(); 0", await_promise=False)
    await cdp.click("#btnStudDeal")
    await cdp.wait_for("Stud.round && Stud.round.phase === 'decide'", timeout=5.0)
    hidden_cap = await cdp.eval("document.querySelectorAll('#studDealerCards .pcard.hidden-card').length", await_promise=False)
    hint_cap = await cdp.eval("document.querySelector('#studPeek').textContent", await_promise=False)
    await cdp.click("#btnStudFold")
    await cdp.wait_for("!Stud.inRound", timeout=5.0)
    record("stud: Sylvies Blick zeigt bei Ante 100 die zweite Dealer-Karte, bei 500 verdeckt mit Kappen-Hinweis",
           hidden_peek == 3 and hint_peek == "🎩 Sylvies Blick" and hidden_cap == 4 and "wirkt bis 250" in hint_cap,
           "hidden100=%s hint100=%s hidden500=%s hint500=%s" % (hidden_peek, hint_peek, hidden_cap, hint_cap))
    await cdp.eval("State.meta.insider = []; State.saveMeta(); 0", await_promise=False)
    # 7) Ante ausserhalb 100-1000: Toast, keine Karten
    await cdp.eval("document.querySelector('#studBet').value = '50'; 0", await_promise=False)
    await cdp.click("#btnStudDeal")
    await asyncio.sleep(0.4)
    cards = await cdp.eval("document.querySelectorAll('#studPlayerCards .pcard').length", await_promise=False)
    toast = await cdp.eval("document.querySelector('#toasts').textContent.includes('Zwischen 100')", await_promise=False)
    in_round = await cdp.eval("Stud.inRound", await_promise=False)
    record("stud: Ante 50 wird abgelehnt", in_round is False and toast is True, "cards=%s toast=%s inRound=%s" % (cards, toast, in_round))


async def scenario_sicbo(cdp):
    """Sic Bo im Royal: Portal, Zone, fester Wurf 2·3·4 (Klein + Summe 9), Triple 4·4·4 -> Achievement,
    Leeren, Wuerfeln ohne Einsatz, Insider Gezinkter Becher mit Kappe."""
    await cdp.navigate(URL_BASE + "?fresh&mode=free&screen=royal")
    await asyncio.sleep(0.8)
    await cdp.inject_helpers()
    portal = await cdp.eval("!!document.querySelector('.portal[data-screen=\"sicbo\"]')", await_promise=False)
    record("sicbo: Portal in der Royal-Lobby", portal is True)
    await cdp.screenshot("royal-lobby.png")
    # Meta-Speicher (Insider, Trophaeen) ueberlebt ?fresh und fruehere Laeufe im selben Chrome-Profil: zuruecksetzen
    await cdp.eval("State.meta.insider = []; State.meta.achievements = State.meta.achievements.filter(id => id !== 'dreiGleiche'); State.saveMeta(); 0", await_promise=False)
    await cdp.eval("State.s.car = 'audiA3'; State.s.balance = 1000; State.save(); UI.renderWallet(); 0", await_promise=False)
    await cdp.eval("UI.show('sicbo'); 0", await_promise=False)
    await asyncio.sleep(0.6)
    zone = await cdp.eval("document.body.dataset.zone", await_promise=False)
    cells = await cdp.eval("document.querySelectorAll('.sb-cell[data-bet]').length", await_promise=False)
    record("sicbo: Zone royal, 29 Felder", zone == "royal" and cells == 29, "zone=%s cells=%s" % (zone, cells))

    async def roll(dice):
        before = await cdp.eval("State.s.balance", await_promise=False)
        await cdp.eval("SicBo.forceDice = %s; 0" % json.dumps(dice), await_promise=False)
        await cdp.click("#btnSbRoll")
        await cdp.wait_for("!SicBo.rolling || __pt.cutsceneActive()", timeout=6.0)
        # Ein Nettogewinn >= RoyalRules.GUEST_WIN (5000) loest einmalig die "Gast des Hauses"-Cutscene aus
        # (Royal.onWin, Bus 'win'), die Game.settle() bis zum Durchklicken blockiert (SicBo.rolling bleibt
        # dann true) -- durchklicken, falls sie gerade offen ist, dann erneut auf das Rollenende warten.
        if await cdp.eval("__pt.cutsceneActive()", await_promise=False):
            await cdp.advance_cutscene(max_steps=10)
            await cdp.wait_for("!SicBo.rolling", timeout=3.0)
        await asyncio.sleep(0.5)
        after = await cdp.eval("State.s.balance", await_promise=False)
        status = await cdp.eval("document.querySelector('#sbStatus').textContent", await_promise=False)
        return before, after, status

    # 1) Chip 50 auf Klein + Summe 9, Wurf 2·3·4 -> +50 + 300
    await cdp.eval("document.querySelector('.chip[data-chip=\"50\"]').click(); SicBo.place('small'); SicBo.place('sum9'); 0", await_promise=False)
    await cdp.screenshot("royal-sicbo.png")
    b0, b1, status = await roll([2, 3, 4])
    won = await cdp.eval("['small','sum9'].every(id => document.querySelector('.sb-cell[data-bet=\"' + id + '\"]').classList.contains('won'))", await_promise=False)
    record("sicbo: Klein + Summe 9 gewinnen bei 2·3·4 (+350)", b1 == b0 + 350 and won is True and "Summe 9" in status, "b0=%s b1=%s won=%s status=%s" % (b0, b1, won, status))
    # 2) Klein, Beliebiger Triple, Triple 4; Wurf 4·4·4 -> -50 + 1500 + 9000, Trophaee
    await cdp.eval("SicBo.place('small'); SicBo.place('tripleAny'); SicBo.place('triple4'); 0", await_promise=False)
    b0, b1, status = await roll([4, 4, 4])
    ach = await cdp.eval("Achievements.has('dreiGleiche')", await_promise=False)
    record("sicbo: Triple 4·4·4 zahlt 180:1 + 30:1, Klein verliert (+10450), Trophaee Drei Gleiche", b1 == b0 + 10450 and ach is True and "Triple" in status, "b0=%s b1=%s ach=%s status=%s" % (b0, b1, ach, status))
    # 3) Leeren nimmt alles zurueck, Wuerfeln ohne Einsatz macht nichts
    await cdp.eval("document.querySelector('.chip[data-chip=\"200\"]').click(); SicBo.place('big'); 0", await_promise=False)
    stack_before = await cdp.eval("document.querySelector('.sb-cell[data-bet=\"big\"] .chip-stack').classList.contains('hidden')", await_promise=False)
    await cdp.click("#btnSbClear")
    stack_after = await cdp.eval("document.querySelector('.sb-cell[data-bet=\"big\"] .chip-stack').classList.contains('hidden')", await_promise=False)
    before = await cdp.eval("State.s.balance", await_promise=False)
    die_before = await cdp.eval("document.querySelector('#sbDie1').textContent", await_promise=False)
    await cdp.eval("SicBo.roll(); 0", await_promise=False)
    await asyncio.sleep(0.4)
    after = await cdp.eval("State.s.balance", await_promise=False)
    rolling = await cdp.eval("SicBo.rolling", await_promise=False)
    die_after = await cdp.eval("document.querySelector('#sbDie1').textContent", await_promise=False)
    record("sicbo: Leeren nimmt Chips zurueck, Wuerfeln ohne Einsatz macht nichts",
           stack_before is False and stack_after is True and after == before and rolling is False and die_before == die_after,
           "stack=%s/%s bal=%s/%s rolling=%s die=%s/%s" % (stack_before, stack_after, before, after, rolling, die_before, die_after))
    # 4) Insider Gezinkter Becher: Wuerfel 1 liegt offen, wird bei Risiko <= 250 uebernommen, darueber nicht
    await cdp.eval("State.meta.insider = ['becher']; State.saveMeta(); 0", await_promise=False)
    await cdp.eval("UI.show('royal'); 0", await_promise=False)
    # UI.show() ist fire-and-forget (Zonen-Blende, Template-Wechsel); ein fixer sleep(0.4) reicht nicht
    # immer, und der direkt folgende UI.show('sicbo') wuerde dann durch den UI.busy-Guard verschluckt
    # (Bildschirm bleibt 'royal', #sbDie1 existiert nicht) -- daher wie sonst im Skript auf UI.busy warten.
    await cdp.wait_for("UI.current && UI.current.id === 'royal' && !UI.busy", timeout=3.0)
    await cdp.eval("UI.show('sicbo'); 0", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'sicbo' && !UI.busy", timeout=3.0)
    await asyncio.sleep(0.3)
    peek = await cdp.eval("SicBo.peekDie", await_promise=False)
    die1 = await cdp.eval("document.querySelector('#sbDie1').textContent", await_promise=False)
    hint = await cdp.eval("document.querySelector('#sbPeek').textContent", await_promise=False)
    faces = ["?", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    record("sicbo: Becher zeigt Wuerfel 1 vorab", isinstance(peek, int) and 1 <= peek <= 6 and die1 == faces[peek] and "liegt schon" in hint, "peek=%s die1=%s hint=%s" % (peek, die1, hint))
    others = [n for n in range(1, 7) if n != peek][:2]      # zwei Werte != peek fuer Wuerfel 2/3
    x = [n for n in range(1, 7) if n != peek and n not in others][0]
    await cdp.eval("document.querySelector('.chip[data-chip=\"50\"]').click(); SicBo.place('one%d'); 0" % peek, await_promise=False)
    b0, b1, status = await roll([x, others[0], others[1]])
    shown = await cdp.eval("document.querySelector('#sbDie1').textContent", await_promise=False)
    record("sicbo: Becher-Wuerfel wird bei Risiko 50 uebernommen, Einzelzahl zahlt 1:1", shown == faces[peek] and b1 == b0 + 50, "peek=%s shown=%s b0=%s b1=%s status=%s" % (peek, shown, b0, b1, status))
    peek2 = await cdp.eval("SicBo.peekDie", await_promise=False)
    await cdp.eval("document.querySelector('.chip[data-chip=\"500\"]').click(); SicBo.place('big'); 0", await_promise=False)
    hint_cap = await cdp.eval("document.querySelector('#sbPeek').textContent", await_promise=False)
    force = [6, 6, 5] if peek2 != 6 else [1, 6, 5]
    b0, b1, status = await roll(force)
    shown = await cdp.eval("document.querySelector('#sbDie1').textContent", await_promise=False)
    record("sicbo: ueber 250 Euro Risiko bleibt der Wurf frisch, Hinweis nennt die Kappe", "wirkt bis 250" in hint_cap and shown == faces[force[0]] and b1 == b0 + 500, "hint=%s peek2=%s shown=%s b0=%s b1=%s" % (hint_cap, peek2, shown, b0, b1))
    await cdp.eval("State.meta.insider = []; State.saveMeta(); 0", await_promise=False)
    # 5) Verlassen ohne Toast, Konto unveraendert
    before = await cdp.eval("State.s.balance", await_promise=False)
    await cdp.eval("UI.show('royal'); 0", await_promise=False)
    await asyncio.sleep(0.5)
    after = await cdp.eval("State.s.balance", await_promise=False)
    toast = await cdp.eval("document.querySelector('#toasts').textContent.includes('aufgegeben')", await_promise=False)
    record("sicbo: Verlassen ohne Einsatzverlust und ohne Toast", after == before and toast is False, "before=%s after=%s toast=%s" % (before, after, toast))


async def main():
    cdp = CDP()
    cdp.launch(mobile=MOBILE)
    try:
        await cdp.connect()
        await scenario_title_trophies(cdp)
        await scenario_title_and_intro(cdp)
        await scenario_spueler_and_hub(cdp)
        await scenario_fast_forward(cdp)
        await scenario_job_param(cdp)
        await scenario_all_job_scenes(cdp)
        await scenario_spueler_taxi_loss(cdp)
        await scenario_job_consumed_before_feierabend(cdp)
        await scenario_mode_switch_no_dataloss(cdp)
        await scenario_reload_mid_day(cdp)
        await scenario_mobile(cdp)
        await scenario_reduced_motion(cdp)
        await scenario_endings(cdp)
        await scenario_all_scenes(cdp)
        await scenario_free_sandbox_unchanged(cdp)
        await scenario_stadt_shop(cdp)
        await scenario_royal_free(cdp)
        await scenario_royal_look(cdp)
        await scenario_kater(cdp)
        await scenario_stash(cdp)
        await scenario_mugging(cdp)
        await scenario_story_stadt(cdp)
        await scenario_roulette_chips(cdp)
        await scenario_perks(cdp)
        await scenario_poker(cdp)
        await scenario_stud(cdp)
        await scenario_sicbo(cdp)
    finally:
        n_errors = len(cdp.console_errors)
        for e in cdp.console_errors:
            print("CONSOLE-ERROR:", e[:500])
        await cdp.close()

    failed = [r for r in RESULTS if not r[1]]
    print("\n=== ZUSAMMENFASSUNG ===")
    print("Checks: %d, davon fehlgeschlagen: %d" % (len(RESULTS), len(failed)))
    for name, ok, detail in failed:
        print("FEHLGESCHLAGEN:", name, "-", detail)
    print("ERRORS", n_errors)
    return 0 if (not failed and n_errors == 0) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
