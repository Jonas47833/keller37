#!/usr/bin/env python3
'''
CDP-Playtest des Admin-Panels (?dev + Login) in keller37.html.

Nutzt den CDP-Helfer aus tests/playtest-story.py (wie mobile-check.py). Aufruf:
    python3 tests/playtest-dev.py
Env: K37_PORT (Standard 9371), K37_PROFILE, K37_SHOTS (Screenshots, Standard /tmp/k37dev).
Am Ende: "FAILS n" und Exit-Code 1 bei Fehlern.
'''
import asyncio
import importlib.util
import json
import os
import sys

sys.argv = [sys.argv[0]]
os.environ.setdefault("K37_PORT", "9371")
os.environ.setdefault("K37_PROFILE", "/tmp/k37dev-profile")
os.environ.setdefault("K37_SHOTS", "/tmp/k37dev")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("pt", os.path.join(ROOT, "tests", "playtest-story.py"))
pt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pt)
URL = "file://" + os.path.join(ROOT, "keller37.html")
USER, PASS = "t", "t"

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("%s %s%s" % ("OK  " if ok else "FAIL", name, (" - " + str(detail)) if detail else ""))


async def login(cdp):
    '''Login-Formular ausfüllen und absenden; wartet auf den Knopf. Ist die Sitzung schon angemeldet
    (laut App bleibt sie es bis zum Tab-Ende), fehlt das Formular – dann ist der Knopf schon da.
    Setzt zuvor DevRules.HASH auf einen Wegwerf-Hash (t:t) – die Login-Box ist schon gemountet,
    der Hash wird erst beim Absenden gelesen, kein Klartext-Passwort im Repo nötig.'''
    if await cdp.eval("!!document.querySelector('#devFab')", await_promise=False):
        return True
    await cdp.eval("DevRules.HASH = DevRules.hash('t:t');", await_promise=False)
    await cdp.eval("document.querySelector('#devUser').value = %s; document.querySelector('#devPass').value = %s; document.querySelector('#devLogin').requestSubmit();"
                   % (json.dumps(USER), json.dumps(PASS)), await_promise=False)
    return await cdp.wait_for("!!document.querySelector('#devFab')", timeout=2.0)


async def open_tab(cdp, tab):
    await cdp.eval("(function(){ const p = document.querySelector('#devPanel'); if (!p.classList.contains('open')) Dev.toggle(true); document.querySelector('.dev-tab[data-tab=%s]').click(); })()" % json.dumps(tab), await_promise=False)
    await asyncio.sleep(0.15)


async def scenario_login(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub", wait=1.4)
    present = await cdp.eval("!!(document.querySelector('#devLogin') || document.querySelector('#devFab') || document.querySelector('#devPanel'))", await_promise=False)
    record("ohne ?dev: kein Panel-DOM", present is False, present)

    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    login_visible = await cdp.eval("!!document.querySelector('#devLogin') && !document.querySelector('#devFab')", await_promise=False)
    record("?dev: Login sichtbar, noch kein Knopf", login_visible is True)
    await cdp.eval("DevRules.HASH = DevRules.hash('t:t');", await_promise=False)
    await cdp.eval("document.querySelector('#devUser').value = 't'; document.querySelector('#devPass').value = 'falsch'; document.querySelector('#devLogin').requestSubmit();", await_promise=False)
    await asyncio.sleep(0.1)
    wrong = await cdp.eval("(function(){ const b = document.querySelector('#devLogin'); return { there: !!b, shake: b && b.classList.contains('shake'), fab: !!document.querySelector('#devFab'), pass: b && document.querySelector('#devPass').value }; })()", await_promise=False) or {}
    record("falsches Passwort: bleibt zu, wackelt, Feld geleert", wrong.get("there") and wrong.get("shake") and not wrong.get("fab") and wrong.get("pass") == "", wrong)
    ok = await login(cdp)
    gone = await cdp.eval("!document.querySelector('#devLogin')", await_promise=False)
    record("richtiges Passwort: Knopf da, Login weg", bool(ok) and gone is True)
    ss = await cdp.eval("sessionStorage.getItem('keller37.dev')", await_promise=False)
    record("sessionStorage merkt Anmeldung", ss == "1", ss)

    await cdp.navigate(URL + "?mode=free&screen=hub", wait=1.4)
    fab = await cdp.eval("!!document.querySelector('#devFab') && !document.querySelector('#devLogin')", await_promise=False)
    record("Reload ohne ?dev: Knopf bleibt", fab is True)
    await cdp.eval("document.querySelector('#devFab').click()", await_promise=False)
    await asyncio.sleep(0.3)
    panel = await cdp.eval("(function(){ const p = document.querySelector('#devPanel'); const tabs = [...document.querySelectorAll('.dev-tab')].map(t => t.dataset.tab); return { open: p.classList.contains('open'), tabs, info: document.querySelector('#devInfo').textContent, width: p.getBoundingClientRect().width }; })()", await_promise=False) or {}
    record("Knopf öffnet Schublade mit vier Reitern, 380 px", panel.get("open") and panel.get("tabs") == ["werte", "screens", "story", "szenen"] and abs(panel.get("width", 0) - 380) < 1, panel)
    record("Kopfzeile zeigt Modus, Screen, Kontostand", "frei" in (panel.get("info") or "") and "hub" in (panel.get("info") or "") and "€" in (panel.get("info") or ""), panel.get("info"))
    drawer = await cdp.eval("({ open: document.body.classList.contains('dev-open'), z: getComputedStyle(document.querySelector('#toasts')).zIndex })", await_promise=False) or {}
    record("Schublade offen: body.dev-open gesetzt, Toasts darüber (z-index 99)", drawer.get("open") is True and drawer.get("z") == "99", drawer)
    await cdp.eval("Dev.toggle(false)", await_promise=False)
    await asyncio.sleep(0.1)
    closed = await cdp.eval("document.body.classList.contains('dev-open')", await_promise=False)
    record("Schublade zu: body.dev-open wieder weg", closed is False, closed)
    await cdp.eval("Dev.toggle(true)", await_promise=False)
    await asyncio.sleep(0.1)
    await cdp.screenshot("dev-panel.png")
    await cdp.eval("document.querySelector('.dev-tab[data-tab=story]').click()", await_promise=False)
    await asyncio.sleep(0.1)
    tab = await cdp.eval("sessionStorage.getItem('keller37.devTab')", await_promise=False)
    record("Reiter wird gemerkt", tab == "story", tab)

    await cdp.eval("Dev.logout()", await_promise=False)
    await asyncio.sleep(0.1)
    after = await cdp.eval("(function(){ return { fab: !!document.querySelector('#devFab'), panel: !!document.querySelector('#devPanel'), ss: sessionStorage.getItem('keller37.dev') }; })()", await_promise=False) or {}
    record("Abmelden: Knopf und Panel weg, sessionStorage leer", not after.get("fab") and not after.get("panel") and after.get("ss") is None, after)


async def scenario_werte(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await login(cdp)
    await open_tab(cdp, "werte")
    rows = await cdp.eval("[...document.querySelectorAll('#devBody .dev-row')].map(r => r.title)", await_promise=False) or []
    record("werte: Felder für Kontostand, XP, Stärke, Waffe, Auto, Royal-Gast", all(x in rows for x in ["Kontostand", "XP", "Stärke", "Waffenstufe", "Auto", "Royal-Gast"]), rows)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Kontostand'); r.querySelector('input').value = '5.000'; r.querySelector('button').click(); })()", await_promise=False)
    await cdp.wait_for("State.s.balance === 5000", timeout=1.0)
    bal = await cdp.eval("({ s: State.s.balance, saved: JSON.parse(localStorage.getItem('keller37.state')).balance })", await_promise=False) or {}
    await asyncio.sleep(1.2)  # Money-Counter tweent
    shown = await cdp.eval("document.querySelector('#balance').textContent", await_promise=False)
    record("werte: Kontostand 5.000 gesetzt, gespeichert, Wallet zeigt ihn", bal.get("s") == 5000 and bal.get("saved") == 5000 and "5.000" in (shown or ""), (bal, shown))
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Waffenstufe'); r.querySelector('input').value = '7'; r.querySelector('button').click(); })()", await_promise=False)
    await asyncio.sleep(0.1)
    w = await cdp.eval("State.s.weapon", await_promise=False)
    record("werte: Waffenstufe 7 abgelehnt (max 3)", w == 0, w)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Royal-Gast'); r.querySelector('input').click(); })()", await_promise=False)
    await asyncio.sleep(0.1)
    guest = await cdp.eval("State.s.flags.royalGuest === true", await_promise=False)
    record("werte: Royal-Gast per Schalter", guest is True)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'Auto'); const s = r.querySelector('select'); s.value = 'audiA3'; s.dispatchEvent(new Event('change')); })()", await_promise=False)
    await asyncio.sleep(0.1)
    car = await cdp.eval("State.s.car", await_promise=False)
    record("werte: Auto per Auswahl", car == "audiA3", car)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'Alle Achievements').click()", await_promise=False)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'Alle Insider-Skills').click()", await_promise=False)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'Level max').click()", await_promise=False)
    await asyncio.sleep(0.1)
    all_ = await cdp.eval("({ ach: State.meta.achievements.length === Achievements.DEFS.length, ins: State.meta.insider.length === Rules.INSIDER.length, xp: State.s.xp === Rules.XP_LEVELS[Rules.XP_LEVELS.length - 1] })", await_promise=False) or {}
    record("werte: Alle Achievements / Insider / Level max", all_.get("ach") and all_.get("ins") and all_.get("xp"), all_)
    await cdp.screenshot("dev-werte.png")


async def scenario_screens(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await login(cdp)
    await open_tab(cdp, "screens")
    secs = await cdp.eval("[...document.querySelectorAll('#devBody .dev-sec h4')].map(h => h.textContent)", await_promise=False) or []
    record("screens: Gruppen Keller, Casino Royal, Stadt, Story, Schießerei, Überfall", all(any(x in s for s in secs) for x in ["Keller", "Casino Royal", "Stadt", "Story", "Schießerei", "Überfall"]), secs)
    n = await cdp.eval("document.querySelectorAll('#devBody .dev-btn').length", await_promise=False)
    total = await cdp.eval("UI.screens.size", await_promise=False)
    record("screens: mindestens ein Knopf pro registriertem Screen", (n or 0) >= (total or 99), (n, total))
    jobs_disabled = await cdp.eval("(function(){ const b = [...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'jobs'); return !!b && b.disabled; })()", await_promise=False)
    record("screens: Story-Knopf jobs im freien Modus disabled", jobs_disabled is True, jobs_disabled)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'craps').click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'craps' && !UI.busy", timeout=4.0)
    zone = await cdp.eval("document.body.dataset.zone", await_promise=False)
    still_open = await cdp.eval("document.querySelector('#devPanel').classList.contains('open')", await_promise=False)
    info = await cdp.eval("document.querySelector('#devInfo').textContent", await_promise=False)
    record("screens: craps öffnet mit Zone royal; Panel bleibt am Desktop offen, Kopfzeile aktuell", zone == "royal" and still_open is True and "craps" in (info or ""), (zone, still_open, info))
    await cdp.screenshot("dev-screens.png")
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent.endsWith(' merc')).click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'stadt' && !UI.busy", timeout=4.0)
    shop = await cdp.eval("Stadt.shop", await_promise=False)
    record("screens: Laden merc direkt", shop == "merc", shop)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'kessler').click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'shootout' && !UI.busy", timeout=4.0)
    foe = await cdp.eval("({ screen: document.body.dataset.screen, pending: Shootout.pending })", await_promise=False) or {}
    record("screens: Schießerei öffnet, pending konsumiert", foe.get("screen") == "shootout" and foe.get("pending") is None, foe)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'junkie').click()", await_promise=False)
    force = await cdp.eval("Mugging.force", await_promise=False)
    record("screens: Überfall junkie vorgemerkt", force == "junkie", force)
    # Story: gesperrte Tür wird beim Klick freigeschaltet
    await cdp.navigate(URL + "?fresh&story=schuld&day=1&dev", wait=2.0)
    await cdp.inject_helpers()
    await cdp.advance_cutscene()
    await login(cdp)
    await open_tab(cdp, "screens")
    locked_before = await cdp.eval("Story.isLocked('roulette')", await_promise=False)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-btn')].find(b => b.textContent === 'roulette').click()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'roulette' && !UI.busy", timeout=4.0)
    unlocked = await cdp.eval("State.s.story.unlocked.doors.includes('roulette')", await_promise=False)
    record("screens: gesperrte Story-Tür wird beim Sprung freigeschaltet", locked_before is True and unlocked is True, (locked_before, unlocked))


async def scenario_story(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await cdp.inject_helpers()
    await login(cdp)
    await open_tab(cdp, "story")
    head = await cdp.eval("document.querySelector('#devBody .dev-info') && document.querySelector('#devBody .dev-info').textContent", await_promise=False)
    record("story: ohne Story steht 'Keine Story aktiv'", "Keine Story" in (head or ""), head)
    # Kater ab Tag 5 mit vorigem Ende doc starten
    await cdp.eval("(function(){ const sel = document.querySelector('#devStorySel'); sel.value = 'kater'; sel.dispatchEvent(new Event('change')); const prev = document.querySelector('#devPrevSel'); prev.value = 'doc'; document.querySelector('#devDayIn').value = '5'; document.querySelector('#devStartBtn').click(); })()", await_promise=False)
    await cdp.wait_for("State.mode === 'story' && State.s.story && State.s.story.id === 'kater' && UI.current && !UI.busy && !Cutscene.active", timeout=8.0)
    st = await cdp.eval("({ id: State.s.story.id, day: State.s.story.day, prev: State.s.story.prev.schuld, leber: !!document.querySelector('.hud-leber') })", await_promise=False) or {}
    record("story: Kater ab Tag 5, prev=doc, Leber-HUD sichtbar", st.get("id") == "kater" and st.get("day") == 5 and st.get("prev") == "doc" and st.get("leber"), st)
    await open_tab(cdp, "story")
    await cdp.screenshot("dev-story.png")
    rows = await cdp.eval("[...document.querySelectorAll('#devBody .dev-row')].map(r => r.title)", await_promise=False) or []
    record("story: Vars (pegel, leber) und Flags (abgestuerzt, zitter) als Felder", all(x in rows for x in ["pegel", "leber", "abgestuerzt", "zitter"]), rows[:30])
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'leber'); r.querySelector('input').value = '40'; r.querySelector('button').click(); })()", await_promise=False)
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'abgestuerzt'); r.querySelector('input').click(); })()", await_promise=False)
    await asyncio.sleep(0.2)
    v = await cdp.eval("({ leber: State.s.story.vars.leber, ab: State.s.story.flags.abgestuerzt, saved: JSON.parse(localStorage.getItem('keller37.story')).story.vars.leber, hud: document.querySelector('.hud-leber .val') && document.querySelector('.hud-leber .val').textContent })", await_promise=False) or {}
    record("story: leber=40 und abgestuerzt=true gesetzt, gespeichert, HUD aktuell", v.get("leber") == 40 and v.get("ab") is True and v.get("saved") == 40 and "40" in (v.get("hud") or ""), v)
    # Tag/Phase
    await cdp.eval("(function(){ document.querySelector('#devDaySet').value = '12'; document.querySelector('#devPhaseSel').value = 'evening'; document.querySelector('#devDayBtn').click(); })()", await_promise=False)
    await cdp.wait_for("State.s.story.day === 12 && State.s.story.phase === 'evening' && UI.current && UI.current.id === 'hub' && !UI.busy", timeout=8.0)
    d = await cdp.eval("({ day: State.s.story.day, phase: State.s.story.phase, screen: UI.current.id })", await_promise=False) or {}
    record("story: Tag 12 abends → Hub", d.get("day") == 12 and d.get("phase") == "evening" and d.get("screen") == "hub", d)
    # Job erzwingen (taxi braucht 200 € Kaution – force)
    await cdp.eval("State.s.balance = 0; State.save();", await_promise=False)
    await open_tab(cdp, "story")
    await cdp.eval("(function(){ document.querySelector('#devJobSel').value = 'taxi'; document.querySelector('#devJobBtn').click(); })()", await_promise=False)
    await cdp.wait_for("UI.current && UI.current.id === 'job-taxi' && !UI.busy", timeout=6.0)
    j = await cdp.eval("({ screen: UI.current.id, unlocked: State.s.story.unlocked.jobs.includes('taxi'), phase: State.s.story.phase })", await_promise=False) or {}
    record("story: Job taxi trotz fehlender Kaution gestartet", j.get("screen") == "job-taxi" and j.get("unlocked") and j.get("phase") == "morning", j)
    # Freischalten: Raum mafia (start.unlocked.rooms von Kater enthält bereits 'royal' – ein direkter
    # Tagessprung überspringt den Absturz am Tag 3, der es sonst entzieht; 'mafia' bleibt dagegen immer gesperrt)
    await open_tab(cdp, "story")
    await cdp.eval("(function(){ const r = [...document.querySelectorAll('#devBody .dev-row')].find(r => r.title === 'raum:mafia'); r.querySelector('input').click(); })()", await_promise=False)
    await asyncio.sleep(0.1)
    room = await cdp.eval("State.s.story.unlocked.rooms.includes('mafia')", await_promise=False)
    record("story: Raum mafia freigeschaltet", room is True, room)
    # Ende abspielen
    await cdp.eval("(function(){ document.querySelector('#devEndSel').value = 'wirt'; document.querySelector('#devEndBtn').click(); })()", await_promise=False)
    await asyncio.sleep(0.6)
    await cdp.advance_cutscene(max_steps=40)
    ended = await cdp.eval("(function(){ const p = JSON.parse(localStorage.getItem('keller37.story') || 'null'); const run = JSON.parse(localStorage.getItem('keller37.meta')).storyRuns.kater; return { ended: !!(p && p.story && p.story.ended) || !!(run && run.endings.includes('wirt')), endScreen: !!document.querySelector('.cs-choices, .ending, #cutscene') }; })()", await_promise=False) or {}
    record("story: Ende wirt abgespielt", ended.get("ended") is True, ended)


async def scenario_szenen(cdp):
    await cdp.navigate(URL + "?fresh&mode=free&screen=hub&dev", wait=1.4)
    await cdp.inject_helpers()
    await login(cdp)
    await open_tab(cdp, "szenen")
    groups = await cdp.eval("[...document.querySelectorAll('#devBody .dev-sec h4')].map(h => h.textContent)", await_promise=False) or []
    n = await cdp.eval("document.querySelectorAll('#devBody .dev-list .dev-btn').length", await_promise=False)
    total = await cdp.eval("Object.keys(Cutscene.SCENES).length", await_promise=False)
    record("szenen: Gruppen Keller + Storys, ein Knopf je Szene", groups[:1] == ["Keller"] and any("Kater" in g for g in groups) and n == total, (groups, n, total))
    await cdp.eval("(function(){ const s = document.querySelector('#devSceneSearch'); s.value = 'kater.k'; s.dispatchEvent(new Event('input')); })()", await_promise=False)
    await asyncio.sleep(0.1)
    ids = await cdp.eval("[...document.querySelectorAll('#devBody .dev-list .dev-btn')].map(b => b.textContent)", await_promise=False) or []
    record("szenen: Suche filtert", ids and all("kater.k" in i for i in ids), ids)
    await cdp.screenshot("dev-szenen.png")
    # Vorschau einer Story-Szene mit Entscheidung: Spielstand bleibt unverändert
    before = await cdp.eval("JSON.stringify([State.s.balance, State.s.flags, localStorage.getItem('keller37.state')])", await_promise=False)
    await cdp.eval("(function(){ const s = document.querySelector('#devSceneSearch'); s.value = 'schuld.intro'; s.dispatchEvent(new Event('input')); })()", await_promise=False)
    await asyncio.sleep(0.1)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-list .dev-btn')].find(b => b.textContent === 'schuld.intro').click()", await_promise=False)
    await asyncio.sleep(0.5)
    active = await cdp.eval("Cutscene.active && !document.querySelector('#devPanel').classList.contains('open')", await_promise=False)
    record("szenen: Vorschau läuft, Panel zu", active is True, active)
    await cdp.advance_cutscene(max_steps=40)
    after = await cdp.eval("JSON.stringify([State.s.balance, State.s.flags, localStorage.getItem('keller37.state')])", await_promise=False)
    mode = await cdp.eval("State.mode", await_promise=False)
    record("szenen: Vorschau ändert Spielstand nicht (frei bleibt frei)", before == after and mode == "free", (before, after, mode))
    # Globale mug.*-Szene: previewCtx() muss Mugging-Beispielwerte (ctx.type usw.) liefern, sonst wirft Cutscene.play
    await open_tab(cdp, "szenen")
    await cdp.eval("(function(){ const s = document.querySelector('#devSceneSearch'); s.value = 'mug.intro'; s.dispatchEvent(new Event('input')); })()", await_promise=False)
    await asyncio.sleep(0.1)
    await cdp.eval("[...document.querySelectorAll('#devBody .dev-list .dev-btn')].find(b => b.textContent === 'mug.intro').click()", await_promise=False)
    await asyncio.sleep(0.5)
    mug_active = await cdp.eval("Cutscene.active", await_promise=False)
    record("szenen: Überfall-Vorschau (mug.intro) läuft", mug_active is True, mug_active)
    await cdp.eval("__pt.advance()", await_promise=False)
    await asyncio.sleep(0.2)
    mug_txt = await cdp.eval("document.querySelector('#cutscene .cs-text') && document.querySelector('#cutscene .cs-text').textContent", await_promise=False)
    record("szenen: Überfall-Vorschau ohne 'undefined' im Text", "undefined" not in (mug_txt or ""), mug_txt)
    await cdp.advance_cutscene(max_steps=10)
    # Platzhalter bleiben sichtbar, wenn der Kontext sie nicht kennt (Tippfehler fallen auf)
    await cdp.eval("Cutscene.define('dev.probe', [{ bg: 'bar', who: 'wirt', mood: 'calm', text: 'Kontostand {{balance}}, unbekannt {{gibtsnicht}}' }]); Dev.preview('dev.probe');", await_promise=False)
    await asyncio.sleep(0.5)
    await cdp.eval("__pt.advance()", await_promise=False)  # erster Klick beendet die Tipp-Animation, Text steht komplett
    await asyncio.sleep(0.2)
    txt = await cdp.eval("document.querySelector('#cutscene .cs-text') && document.querySelector('#cutscene .cs-text').textContent", await_promise=False)
    record("szenen: bekannte Platzhalter gefüllt, unbekannte sichtbar", "€" in (txt or "") and "{{gibtsnicht}}" in (txt or ""), txt)
    await cdp.advance_cutscene(max_steps=5)


async def main():
    cdp = pt.CDP()
    cdp.launch()
    try:
        await cdp.connect()
        await scenario_login(cdp)
        await scenario_werte(cdp)
        await scenario_screens(cdp)
        await scenario_story(cdp)
        await scenario_szenen(cdp)
    finally:
        errs = [e for e in cdp.console_errors]
        record("keine Konsolenfehler", not errs, errs[:3])
        await cdp.close()
    fails = [n for n, ok in RESULTS if not ok]
    print("FAILS", len(fails))
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
