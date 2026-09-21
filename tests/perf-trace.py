#!/usr/bin/env python3
"""
Performance-Messung per Chrome-Trace (CDP) – zählt, was der Browser pro Frame wirklich tut.

Für jede Szene wird ein echter Headless-Chrome gestartet, die Szene ausgelöst (Spin, Job, Leerlauf …)
und währenddessen ein Trace der Kategorien devtools.timeline aufgezeichnet. Ausgewertet werden:

    Paint      Main-Thread-Neuzeichnungen (Ziel während Compositor-Animationen: ~0)
    Raster     Raster-Tasks und ihre Dauer – die eigentliche Malarbeit; das ist die Zahl, die auf dem Handy ruckelt
    Layout     Layout-Durchläufe (Ziel während Animationen: ~0)
    Elemente   welche DOM-Knoten am häufigsten neu gemalt werden

Die Millisekunden sind Software-Raster auf dem Entwicklungsrechner, nicht die eines Handys – aber *ob* pro Frame
gemalt wird und wie viel Fläche, ist geräteunabhängig. Vergleiche daher immer vorher/nachher auf demselben Rechner.

Nutzung:
    python3 tests/perf-trace.py [--mobile] [Szenen-Filter …]
    PATCH="<JS>" python3 tests/perf-trace.py --mobile "Gluecksrad Spin"     # JS vor der Szene ausführen (z. B. Style-Experimente)

Referenzwerte (Mac, Software-Raster) stehen im Commit "perf: Compositor statt Repaint".
"""
import asyncio
import collections
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

import websockets

PORT = int(os.environ.get("K37_PERF_PORT", "9377"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(ROOT, "keller37.html")
PROFILE = os.environ.get("K37_PERF_PROFILE", "/tmp/k37perf-profile")
CHROME_CANDIDATES = [
    os.environ.get("K37_CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    os.path.expanduser("~/.local/opt/chrome-linux64/chrome"),
    "/usr/bin/google-chrome", "/usr/bin/chromium",
]
MOBILE = "--mobile" in sys.argv
CATS = ",".join(["devtools.timeline", "disabled-by-default-devtools.timeline", "disabled-by-default-devtools.timeline.frame"])

# Story-Intro durchklicken, dann einen Job direkt nehmen (Jobs gibt es nur im Story-Modus)
STORY_JOB = """(async()=>{
  for (let i = 0; i < 80; i++) {
    if (!(typeof Cutscene !== 'undefined' && Cutscene.active)) break;
    const ch = document.querySelectorAll('.cs-choices button'); if (ch.length) ch[0].click(); else document.querySelector('#cutscene').click();
    await new Promise((r) => setTimeout(r, 150));
  }
  await new Promise((r) => setTimeout(r, 400));
  State.s.balance = 1000; Story.s.jobToday = null;
  if (!Story.s.unlocked.jobs.includes(JOB)) Story.s.unlocked.jobs.push(JOB);
  await Jobs.take(JOB); await new Promise((r) => setTimeout(r, 600));
  return !!document.querySelector(BTN);
})()"""

# (Name, URL-Query, Sekunden, Auslöser-JS, Vorbereitungs-JS)
SCENARIOS = [
    ("Keller-Hub idle", "?screen=hub", 3, None, None),
    ("Royal-Lobby idle", "?screen=royal", 3, None, None),
    ("Stadt idle", "?screen=stadt", 3, None, None),
    ("Titel idle", "", 3, None, None),
    ("MegaSlots idle", "?screen=royal&game=megaslots", 7, None, None),
    ("Gluecksrad Spin", "?screen=royal&game=wheel", 5, "document.querySelector('#btnWheel').click()", None),
    ("Gluecksrad Gewinn-Glow", "?screen=royal&game=wheel", 2.2, "document.querySelector('#wheel').classList.add('hit')", None),
    ("MegaSlots Spin", "?screen=royal&game=megaslots", 5, "document.querySelector('#btnMega').click()", None),
    ("Craps Roll", "?screen=royal&game=craps", 4, "document.querySelector('#btnPass').click(); document.querySelector('#btnRoll').click()", None),
    ("Keller-Slots Spin", "?screen=slots", 4, "document.querySelector('#btnSpin').click()", None),
    ("Roulette Spin", "?screen=roulette", 5, "document.querySelector('.rcell').click(); document.querySelector('#btnSpin').click()", None),
    ("Cutscene idle", "?screen=hub&scene=intro", 4, None, None),
    # mug.intro braucht ctx.type (Überfalltyp) - der generische ?scene=-Kontext in boot() liefert das nicht
    # (nur Dev.previewCtx() tut das), darum wird die Szene hier direkt mit einem Mugging-Kontext gestartet.
    ("Cutscene Regie", "?screen=hub", 4, None,
     "(async()=>{ Cutscene.play('mug.intro', { loot: '40 €', type: Mugging.TYPES.junkie, fight: 50, flee: 30 });"
     " for (let i = 0; i < 20 && !Cutscene.active; i++) await new Promise((r) => setTimeout(r, 20));"
     " return Cutscene.active; })()"),
    ("Duell", "?screen=shootout&foe=junge&weapon=1", 4,
     "GangRules.drawWait = () => 400; Shootout.ready(); setTimeout(() => { const b = DuelStage.foeBox(), R = document.querySelector('#duelStage').getBoundingClientRect();"
     " Shootout.shoot({ clientX: R.left + b.left + b.width / 2, clientY: R.top + b.top + b.height / 2, pointerType: 'mouse' }); }, 600)", None),
    ("Taxi fahren", "?story", 4, "document.querySelector('#btnTaxiStart').click()", STORY_JOB.replace("JOB", "'taxi'").replace("BTN", "'#btnTaxiStart'")),
    ("Spueler", "?story", 4, "document.querySelector('#btnDishStart').click()", STORY_JOB.replace("JOB", "'spueler'").replace("BTN", "'#btnDishStart'")),
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    raise SystemExit("Kein Chrome gefunden (K37_CHROME setzen)")


class CDP:
    def __init__(self):
        self._id = 0
        self.pending = {}
        self.trace = []
        self.errors = []
        self.trace_done = None

    def launch(self):
        shutil.rmtree(PROFILE, ignore_errors=True)
        args = [find_chrome(), "--headless=new", "--disable-gpu", "--remote-debugging-port=%d" % PORT, "--user-data-dir=%s" % PROFILE,
                "--no-first-run", "--hide-scrollbars", "--window-size=1280,900", "--autoplay-policy=no-user-gesture-required"]
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
        self.ws = await websockets.connect(info["webSocketDebuggerUrl"], max_size=None, ping_interval=None)
        self.task = asyncio.create_task(self._listen())
        for m in ("Page.enable", "Runtime.enable", "DOM.enable"):
            await self.send(m)
        if MOBILE:
            await self.send("Emulation.setDeviceMetricsOverride", {"width": 412, "height": 915, "deviceScaleFactor": 2.6, "mobile": True})
            await self.send("Emulation.setTouchEmulationEnabled", {"enabled": True})

    async def _listen(self):
        try:
            async for raw in self.ws:
                m = json.loads(raw)
                if "id" in m:
                    f = self.pending.pop(m["id"], None)
                    if f and not f.done():
                        f.set_result(m)
                elif m.get("method") == "Tracing.dataCollected":
                    self.trace.extend(m["params"]["value"])
                elif m.get("method") == "Tracing.tracingComplete":
                    self.trace_done.set()
                elif m.get("method") == "Runtime.exceptionThrown":
                    self.errors.append(json.dumps(m["params"])[:300])
        except websockets.exceptions.ConnectionClosed:
            pass

    async def send(self, method, params=None, timeout=30):
        self._id += 1
        mid = self._id
        f = asyncio.get_event_loop().create_future()
        self.pending[mid] = f
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        return await asyncio.wait_for(f, timeout)

    async def eval(self, expr, await_promise=True):
        r = await self.send("Runtime.evaluate", {"expression": expr, "awaitPromise": await_promise, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    async def trace_for(self, secs, action=None):
        self.trace = []
        self.trace_done = asyncio.Event()
        await self.send("Tracing.start", {"categories": CATS, "transferMode": "ReportEvents"})
        await asyncio.sleep(0.3)
        if action:
            await self.eval("console.timeStamp('k37click');" + action, await_promise=False)
        await asyncio.sleep(secs)
        await self.send("Tracing.end")
        await asyncio.wait_for(self.trace_done.wait(), 30)
        return self.trace

    async def node_names(self, backend_ids):
        out = {}
        ids = [i for i in backend_ids if i]
        if not ids:
            return out
        try:
            await self.send("DOM.getDocument", {"depth": -1})
            r = await self.send("DOM.pushNodesByBackendIdsToFrontend", {"backendNodeIds": ids})
            for bid, nid in zip(ids, r.get("result", {}).get("nodeIds", [])):
                if not nid:
                    continue
                n = (await self.send("DOM.describeNode", {"nodeId": nid}))["result"]["node"]
                a = n.get("attributes", [])
                a = dict(zip(a[::2], a[1::2]))
                out[bid] = "%s#%s.%s" % (n.get("localName", "?"), a.get("id", ""), a.get("class", "").replace(" ", "."))
        except Exception:
            pass
        return out

    def close(self):
        self.proc.terminate()
        self.proc.wait()
        shutil.rmtree(PROFILE, ignore_errors=True)  # Chrome-Profil aufraeumen (sonst sammeln sich 140 MB pro Lauf in /tmp)


def summarize(evs, secs):
    cnt = collections.Counter()
    dur = collections.Counter()
    painted = collections.Counter()
    for e in evs:
        if e.get("ph") not in ("X", "B", "I", "R"):
            continue
        n = e.get("name")
        cnt[n] += 1
        dur[n] += e.get("dur", 0) / 1000.0
        if n == "Paint":
            painted[e.get("args", {}).get("data", {}).get("nodeId")] += 1
    return cnt, dur, painted


def timeline(evs, secs):
    marks = [e["ts"] for e in evs if e.get("name") == "TimeStamp" and "k37" in json.dumps(e.get("args", {}))]
    frames = [e["ts"] for e in evs if e.get("name") == "DrawFrame"]
    if not marks and not frames:
        return
    t0 = marks[0] if marks else min(frames)
    step = 0.25
    rows = [collections.Counter() for _ in range(int(secs / step) + 4)]
    for e in evs:
        if e.get("ph") not in ("X", "I"):
            continue
        b = int((e["ts"] - t0) / 1e6 / step)
        if 0 <= b < len(rows):
            rows[b][e["name"]] += 1
            if e["name"] == "RasterTask":
                rows[b]["RasterMs"] += e.get("dur", 0) / 1000
    print("    t(s)  Paint Raster RasterMs Layout")
    for i, r in enumerate(rows):
        if r["Paint"] or r["RasterTask"] or r["Layout"]:
            print("    %4.2f  %5d %6d %8.1f %6d" % (i * step, r["Paint"], r["RasterTask"], r["RasterMs"], r["Layout"]))


async def main():
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--timeline" in sys.argv
    c = CDP()
    c.launch()
    try:
        await c.connect()
        print("Modus: %s" % ("Mobile 412x915 @2.6" if MOBILE else "Desktop 1280x900"))
        print("%-24s %7s %8s %9s %7s   %s" % ("Szene", "Paint/s", "Raster/s", "Raster-ms", "Layout/s", "meistgemalte Elemente"))
        for name, q, secs, action, pre in SCENARIOS:
            if only and not any(o.lower() in name.lower() for o in only):
                continue
            await c.send("Page.navigate", {"url": URL + q + ("&" if q else "?") + "fresh"})
            await asyncio.sleep(1.5)
            await c.eval("State.s.balance = 500000; State.save(); UI.renderWallet(); true", await_promise=False)
            if os.environ.get("PATCH"):
                await c.eval(os.environ["PATCH"], await_promise=False)
            if pre:
                ok = await c.eval(pre)
                if not ok:
                    print("%-24s (Szene nicht erreicht)" % name)
                    continue
            await asyncio.sleep(0.5)
            evs = await c.trace_for(secs, action)
            cnt, dur, painted = summarize(evs, secs)
            names = await c.node_names([n for n, _ in painted.most_common(4)])
            top = ", ".join("%s×%d" % (names.get(n, n), k) for n, k in painted.most_common(4))
            print("%-24s %7.1f %8.1f %9.1f %7.1f   %s" % (name, cnt["Paint"] / secs, cnt["RasterTask"] / secs, dur["RasterTask"], cnt["Layout"] / secs, top))
            if verbose:
                timeline(evs, secs)
        if c.errors:
            print("\nJS-Fehler:", c.errors[:5])
    finally:
        c.close()


asyncio.run(main())
