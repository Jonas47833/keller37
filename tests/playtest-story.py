#!/usr/bin/env python3
"""
CDP-Playtest für den Story-Modus (Keller 37).

Startet einen echten Headless-Chrome (--headless=new --remote-debugging-port=9335),
fährt die in Task-9-Brief/Spec §13 beschriebene Sequenz (Titel -> Story -> Intro ->
Pinnwand -> Spüler -> Abend-Hub mit Sperren -> Vitos Tisch -> Schlafen -> Tag 2 ->
Post-Schicht -> Nacht-Ereignisse -> Kapitel -> Taxi -> Kontrolle/Duell -> alle vier
Enden -> Titel -> freies Spiel, dazu Ein-Job-pro-Tag ohne Feierabend-Klick) und sammelt dabei
Konsolenfehler/Exceptions.

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

PORT = 9335
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "keller37.html")
URL_BASE = "file://" + HTML
SHOT_DIR = "/tmp/k37story"
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

MOBILE = "--mobile" in sys.argv

os.makedirs(SHOT_DIR, exist_ok=True)


def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
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
        profile = "/tmp/k37story-profile"
        subprocess.run(["rm", "-rf", profile])
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


DIFF_THRESHOLD_PCT = 2.0


async def scenario_free_sandbox_unchanged(cdp):
    """Freies Spiel unveraendert: ?screen=-Screenshots per echtem Pixel-Diff (Pillow) gegen
    docs/superpowers/screenshots/*.png vergleichen -- nicht nur "Datei existiert"."""
    ref_dir = os.path.join(ROOT, "docs", "superpowers", "screenshots")
    if not HAVE_PIL:
        record("freie sandbox: Pillow verfuegbar", False, "import PIL schlug fehl -- Vergleich faellt auf Dateigroesse zurueck")
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
