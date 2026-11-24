#!/usr/bin/env python3
"""Presses every control in the lesson player and checks the result, including diagram animation.

Run: python3 tests/test_ui.py   (needs playwright + a Chromium)
Uses the how-ai-works example plus a few in-memory additions (a multi-select item, a faded step)
so every quiz type and control is exercised.
"""
import copy, json, os, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, "skills", "teachme")
from playwright.sync_api import sync_playwright

fails, passes = [], 0
def check(ok, msg):
    global passes
    print(("  ok   " if ok else "  FAIL ") + msg)
    if ok: passes += 1
    else: fails.append(msg)

course = json.load(open(os.path.join(SK, "examples", "how-ai-works", "course.json")))
c = copy.deepcopy(course); L1 = c["lessons"][0]
L1["steps"][5]["workedExample"]["steps"][2]["faded"] = True
L1["quiz"].append({"id": "nw-qm", "type": "multi", "objective": "o2", "prompt": "Which are tokens?", "options": ["the", "un", "a whole book", ","], "answer": [0, 1, 3], "explanation": "Words, word pieces and punctuation."})
L1["steps"][7]["quiz"].append("nw-qm")
tpl = open(os.path.join(SK, "assets", "player.html")).read()
out = os.path.join(tempfile.mkdtemp(), "ui.html")
open(out, "w").write(tpl.replace("/*__COURSE_JSON__*/", json.dumps(c).replace("</", "<\\/"), 1).replace("__TITLE__", c["title"], 1))
URL = "file://" + out
MOCK = """window.__spoken = []; try { Object.defineProperty(window, 'speechSynthesis', {value: {speaking:false, cancel(){ this.speaking=false; }, speak(u){ window.__spoken.push(u.text); this.speaking=true; }}}); } catch (e) {}"""

def node_xy(pg, nid):
    return pg.evaluate("id => { const g = document.querySelector(`#fig g.n[data-id='${id}']`); if (!g) return null; const m = new DOMMatrix(getComputedStyle(g).transform); return [Math.round(m.e), Math.round(m.f), +getComputedStyle(g).opacity]; }", nid)

def go_step(pg, lid, i):
    pg.evaluate("([k,lid,i]) => { const S = JSON.parse(localStorage.getItem(k)||'{}'); S.lessons = S.lessons||{}; S.lessons[lid] = Object.assign(S.lessons[lid]||{answers:{}}, {step:i}); localStorage.setItem(k, JSON.stringify(S)); }", ["teachme:" + c["id"], lid, i])
    pg.goto("about:blank"); pg.goto(URL + "#l-" + lid); pg.wait_for_timeout(300)

with sync_playwright() as p:
    exe = next((x for x in ["/usr/bin/google-chrome", "/usr/bin/chromium"] if os.path.exists(x)), None)
    b = p.chromium.launch(**({"executable_path": exe} if exe else {}), args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 1280, "height": 900}); ctx.add_init_script(MOCK)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL + "#home"); pg.wait_for_timeout(800)

    print("Home and navigation")
    for h, sel in [("plan", "h1:has-text('learning plan')"), ("review", "h1:has-text('Review')"), ("test", "h1:has-text('1-week test')"), ("sources", "h1:has-text('Sources')"), ("home", "h1:has-text('How AI works')")]:
        pg.click(f"#topnav a[href='#{h}']"); pg.wait_for_timeout(200); check(pg.is_visible(sel), f"top nav: {h}")
    fs0 = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--fs')")
    pg.click("#szp"); pg.click("#szp"); fs1 = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--fs')")
    pg.click("#szm"); pg.click("#szm"); fs2 = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--fs')")
    check(fs1.strip() == "20px" and fs2.strip() == fs0.strip(), f"A+/A- text size ({fs0.strip()} -> {fs1.strip()} -> {fs2.strip()})")
    pg.wait_for_timeout(700)
    n = pg.query_selector("#mapfig g.n[data-id='train']")
    if n: n.click(); pg.wait_for_timeout(300)
    check("#l-how-models-learn" in pg.url, "concept map node opens its lesson")
    pg.goto(URL + "#home"); pg.wait_for_timeout(300)
    pg.click("a.btn.pri"); pg.wait_for_timeout(300); check("#l-next-word" in pg.url, "Start button opens lesson 1")
    pg.click("#rail a[href='#l-assistant-and-hallucination']"); pg.wait_for_timeout(300); check("Step 1 of" in (pg.text_content(".kicker") or "").title() or "step 1 of" in (pg.text_content(".kicker") or ""), "rail link opens a lesson")

    print("Animated diagrams")
    go_step(pg, "next-word", 2); pg.wait_for_timeout(900)
    a = node_xy(pg, "model"); fig1 = pg.evaluate("document.querySelector('#fig')")
    trans = pg.evaluate("getComputedStyle(document.querySelector('#fig g.n')).transitionProperty")
    check("transform" in trans, f"nodes have a transform transition ({trans})")
    pk = pg.query_selector_all("#fig .pk")
    check(len(pk) >= 1, f"flow edges carry moving dots ({len(pk)})")
    if pk:
        p1 = pk[0].bounding_box(); pg.wait_for_timeout(400); p2 = pk[0].bounding_box()
        check(p1 and p2 and (abs(p1["x"] - p2["x"]) + abs(p1["y"] - p2["y"])) > 3, "dot moves along its arrow")
    pg.evaluate("window.__keep = document.querySelector(\"#fig g.n[data-id='model']\")")
    pg.click('[data-nav="1"]'); pg.wait_for_timeout(60)
    same = pg.evaluate("document.querySelector(\"#fig g.n[data-id='model']\") === window.__keep")
    mid = node_xy(pg, "model"); new_mid = node_xy(pg, "t1")
    pg.wait_for_timeout(900); b2 = node_xy(pg, "model"); new_end = node_xy(pg, "t1")
    check(same, "shared node survives the step change (same element, so it can glide)")
    check(a and b2 and (a[0], a[1]) != (b2[0], b2[1]), f"shared node moved to its new place {a[:2]} -> {b2[:2] if b2 else None}")
    check(mid and b2 and (mid[0], mid[1]) != (b2[0], b2[1]), f"move is animated, not a jump (mid {mid[:2] if mid else None})")
    check(new_mid is not None and new_end and new_mid[2] < new_end[2] and new_end[2] > 0.95, f"new node fades in (opacity {new_mid[2] if new_mid else None} -> {new_end[2] if new_end else None})")
    gone = pg.evaluate("[...document.querySelectorAll('#fig g.n')].map(g => g.dataset.id)")
    check("w2" not in gone and "w3" not in gone, "nodes not in the next snapshot are removed")
    ed = pg.evaluate("document.querySelectorAll('#fig .edges path').length")
    check(ed >= 5, f"arrows redrawn for the new step ({ed})")
    lbl = pg.evaluate("[...document.querySelectorAll('#fig .nodes text')].map(t => t.textContent).join('|')")
    check("believ" in lbl and "numbers" in lbl, "node labels render")
    go_step(pg, "next-word", 0); pg.wait_for_timeout(700); check(len(pg.query_selector_all("#fig g.n")) == 2, "hook diagram renders")

    print("Pretest and skip-ahead")
    go_step(pg, "next-word", 1)
    pg.click("[data-q='nw-q1'] [data-opt='1']"); pg.wait_for_timeout(100); pg.click("[data-q='nw-q2'] [data-opt='1']"); pg.wait_for_timeout(150)
    check(pg.is_visible("[data-q='nw-q1'] .opt.right") and pg.is_visible(".fb b.ok"), "multiple choice marks the right answer")
    j = pg.query_selector("[data-jump]"); check(j is not None, "perfect pretest offers skip-ahead")
    if j: j.click(); pg.wait_for_timeout(200); check("step 8 of" in pg.text_content(".kicker"), "skip-ahead jumps to the recall quiz")

    print("Worked example, simulation, keyboard, Listen")
    go_step(pg, "next-word", 5)
    check(pg.is_visible("[data-rev]"), "faded step is hidden behind Show step"); pg.click("[data-rev]"); pg.wait_for_timeout(150)
    check(not pg.query_selector("[data-rev]"), "Show step reveals it")
    pg.fill("[data-se]", "because each token depends on the last"); pg.wait_for_timeout(100)
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(150); check("step 6 of" in pg.text_content(".kicker"), "arrow keys ignored while typing")
    pg.click("h2"); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200); check("step 7 of" in pg.text_content(".kicker"), "Right arrow key goes to next step")
    pg.click("h2"); pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(200); check(pg.input_value("[data-se]").startswith("because"), "self-explanation text is kept")
    pg.click('[data-nav="1"]'); pg.wait_for_timeout(200)
    check(not pg.query_selector("[data-p]"), "sliders stay hidden until you predict"); pg.click("[data-pred='0']"); pg.wait_for_timeout(300)
    check(pg.is_visible(".fb b.no"), "wrong prediction gets feedback")
    v1 = pg.text_content("#simout"); pg.evaluate("const i = document.querySelector('[data-p=temp]'); i.value = 0.3; i.dispatchEvent(new Event('input'))"); pg.wait_for_timeout(150); v2 = pg.text_content("#simout")
    check(v1 != v2 and "97" in v2, f"slider recomputes outputs ({v1.strip()[:40]} -> {v2.strip()[:40]})")
    check(pg.evaluate("document.querySelectorAll('#simchart path').length") >= 1, "simulation chart draws a curve")
    pg.click("#listen"); pg.wait_for_timeout(100); spoken = pg.evaluate("window.__spoken")
    check(len(spoken) == 1 and "temperature" in spoken[0].lower(), "Listen speaks the step")

    print("Every quiz type and the mastery gate")
    go_step(pg, "next-word", 7)
    pg.fill("#in-nw-q4", "Tokens!"); pg.click("[data-q='nw-q4'] [data-check]"); pg.wait_for_timeout(100); check(pg.is_visible("[data-q='nw-q4'] b.ok"), "fill-in ignores case and punctuation")
    pg.click("[data-q='nw-q5'] [data-opt='1']"); pg.wait_for_timeout(100); check(pg.is_visible("[data-q='nw-q5'] .opt.wrong"), "wrong choice marked wrong and right one shown")
    pg.click("[data-q='nw-qm'] [data-opt='0']"); pg.click("[data-q='nw-qm'] [data-check]"); pg.wait_for_timeout(100)
    check(pg.is_visible("[data-q='nw-qm'] b.no") and pg.is_visible("[data-q='nw-qm'] .opt.right"), "multi-select: partial answer marked wrong, full answer shown")
    pg.fill("#in-nw-q6", "sampling"); pg.click("[data-q='nw-q6'] [data-show]"); pg.wait_for_timeout(100)
    check(pg.is_visible("[data-q='nw-q6'] .fb"), "recall shows the model answer"); pg.click("[data-q='nw-q6'] [data-self='1']"); pg.wait_for_timeout(100)
    items = L1["quiz"][2]["items"]
    for _ in range(12):
        cur = pg.eval_on_selector_all("[data-q='nw-q3'] .ord span", "e => e.map(x => x.textContent)")
        k = next((i for i in range(1, len(cur)) if items.index(cur[i]) < items.index(cur[i-1])), None)
        if k is None: break
        pg.click(f"[data-q='nw-q3'] [data-up='{k}']"); pg.wait_for_timeout(60)
    pg.click("[data-q='nw-q3'] [data-check]"); pg.wait_for_timeout(150)
    check(pg.is_visible("[data-q='nw-q3'] b.ok"), "ordering with up/down buttons")
    check(pg.is_visible("[data-retry]"), "score under 80% shows the mastery gate")
    pg.click("[data-anyway]"); pg.wait_for_timeout(150); check("step 9 of" in pg.text_content(".kicker"), "Continue anyway moves on")
    go_step(pg, "next-word", 7); pg.click("[data-reexplain]"); pg.wait_for_timeout(150); check("step 3 of" in pg.text_content(".kicker"), "Review the explanation goes back")
    go_step(pg, "next-word", 7); pg.click("[data-retry]"); pg.wait_for_timeout(150)
    check(len(pg.query_selector_all(".fb")) == 0, "Retry clears the answers")
    pg.click("[data-q='nw-q5'] [data-opt='0']"); pg.fill("#in-nw-q4", "tokens"); pg.click("[data-q='nw-q4'] [data-check]")
    for q, opts in [("nw-qm", [0, 1, 3])]:
        for o in opts: pg.click(f"[data-q='{q}'] [data-opt='{o}']")
        pg.click(f"[data-q='{q}'] [data-check]")
    pg.fill("#in-nw-q6", "x"); pg.click("[data-q='nw-q6'] [data-show]"); pg.click("[data-q='nw-q6'] [data-self='1']")
    for _ in range(12):
        cur = pg.eval_on_selector_all("[data-q='nw-q3'] .ord span", "e => e.map(x => x.textContent)")
        k = next((i for i in range(1, len(cur)) if items.index(cur[i]) < items.index(cur[i-1])), None)
        if k is None: break
        pg.click(f"[data-q='nw-q3'] [data-up='{k}']"); pg.wait_for_timeout(60)
    pg.click("[data-q='nw-q3'] [data-check]"); pg.wait_for_timeout(150)
    check(pg.is_visible(".callout:has-text('Mastered')") and pg.is_visible("[data-q='nw-qm'] b.ok"), "multi-select all-correct; all correct shows Mastered")

    print("Numeric answer (lesson 2)")
    go_step(pg, "how-models-learn", 6); pg.click("[data-pred='1']"); pg.wait_for_timeout(150)
    pg.fill("#in-ml-q3", "3"); pg.click("[data-q='ml-q3'] [data-check]"); pg.wait_for_timeout(100); check(pg.is_visible("[data-q='ml-q3'] b.ok"), "numeric answer within tolerance")

    print("Teach-back, review deck, persistence")
    go_step(pg, "next-word", 8)
    pg.evaluate("const r = document.querySelector('[data-conf]'); r.value = 5; r.dispatchEvent(new Event('input'))")
    pg.fill("[data-tb]", "It predicts the next token in a loop."); pg.click("[data-tbshow]"); pg.wait_for_timeout(150)
    check(pg.is_visible(".fb:has-text('Model answer')"), "Compare shows the model answer")
    pg.check("[data-rub='0']"); pg.wait_for_timeout(100); cal = pg.text_content("#calib")
    check("25%" in cal and "Confidence ran ahead" in cal, f"rubric ticks give a calibration message ({cal[:60]})")
    pg.reload(); pg.wait_for_timeout(300); check(pg.input_value("[data-tb]").startswith("It predicts"), "teach-back text survives reload")
    pg.click('[data-nav="1"]'); pg.wait_for_timeout(150); pg.click("[data-addcards]"); pg.wait_for_timeout(150)
    check(pg.is_visible(".badge:has-text('In your review deck')"), "Add to review deck")
    pg.click('[data-nav="1"]'); pg.wait_for_timeout(200); check("#l-how-models-learn" in pg.url, "Finish lesson goes to the next lesson")
    pg.goto(URL + "#home"); pg.wait_for_timeout(300); check(pg.is_visible(".dot.ok, .dot.half"), "finished lesson marked in the rail")
    pg.goto(URL + "#review"); pg.wait_for_timeout(200); due0 = pg.text_content(".note")
    pg.click("[data-flip]"); pg.wait_for_timeout(100); check(pg.is_visible(".flash .back") and len(pg.query_selector_all("[data-g]")) == 4, "card flips and shows four ratings with intervals")
    ivs = pg.eval_on_selector_all("[data-g] small", "e => e.map(x => x.textContent)"); check(ivs[0] == "10m" and ivs[2].endswith("d"), f"intervals look right {ivs}")
    pg.click("[data-g='3']"); pg.wait_for_timeout(150); due1 = pg.text_content(".note")
    check(due0 != due1, f"rating a card advances the deck ({due0.split('·')[0].strip()} -> {due1.split('·')[0].strip()})")
    pg.click("details.card summary"); pg.click("[data-copy]"); pg.wait_for_timeout(200)
    check(pg.is_visible("[data-copy]:has-text('Copied')") or pg.is_visible("details textarea"), "Anki export copies (or shows text to copy)")

    print("Checkpoint, 1-week test, plan")
    pg.goto(URL + "#c-cp1"); pg.wait_for_timeout(200); pg.click("[data-q='cp1-q1'] [data-opt='1']"); pg.wait_for_timeout(100)
    check(pg.is_visible("[data-q='cp1-q1'] b.ok"), "checkpoint question answers")
    pg.goto(URL + "#test"); pg.wait_for_timeout(200); f = pg.query_selector("[data-force]")
    check(f is not None, "1-week test waits a week, with Take it now"); f and f.click(); pg.wait_for_timeout(200)
    check(len(pg.query_selector_all("#main [data-q]")) >= 3, "1-week test shows mixed questions")
    pg.goto(URL + "#plan"); pg.wait_for_timeout(200)
    for mode in ["today", "weekly", "deadline", "daily"]:
        pg.click(f".pace:has(input[value='{mode}'])"); pg.wait_for_timeout(150)
        check(pg.is_checked(f"input[value='{mode}']") and len(pg.query_selector_all(".sess")) >= 1, f"plan: {mode}")
    pg.evaluate("const i = document.querySelector('#pmin'); i.value = 120; i.dispatchEvent(new Event('change'))"); pg.wait_for_timeout(150)
    check(len(pg.query_selector_all(".sess")[0].query_selector_all("a[href^='#l-']")) >= 2, "2 hours a day fits two lessons today")
    pg.select_option("#pret", "year"); pg.wait_for_timeout(150); check(pg.input_value("#pret") == "year", "remember-for select")
    pg.goto(URL + "#home"); pg.wait_for_timeout(300); check(pg.is_visible(".plan-today"), "home shows today's session")
    pg.goto(URL + "#sources"); pg.wait_for_timeout(150); pg.click("details.card summary"); check(pg.is_visible("blockquote"), "sources panel opens claims and quotes")
    check(not errs, "no script errors on desktop" + ("" if not errs else ": " + "; ".join(errs[:3])))

    print("Phone and reduced motion")
    ctx2 = b.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce"); ctx2.add_init_script(MOCK)
    m = ctx2.new_page(); e2 = []; m.on("pageerror", lambda e: e2.append(str(e)))
    m.goto(URL + "#l-next-word"); m.wait_for_timeout(300)
    m.click("#menuBtn"); m.wait_for_timeout(100); check(m.is_visible("#rail"), "phone: Lessons menu opens")
    m.click("#closeRail"); m.wait_for_timeout(100); check(not m.is_visible("#rail"), "phone: menu closes")
    for _ in range(2): m.click('[data-nav="1"]'); m.wait_for_timeout(150)
    m.wait_for_timeout(700)
    tr = m.evaluate("getComputedStyle(document.querySelector('#fig g.n')).transitionDuration")
    pk = m.evaluate("[...document.querySelectorAll('#fig .pk')].every(x => getComputedStyle(x).display === 'none')")
    check(tr in ("0s",) and pk, f"reduced motion: no glide ({tr}), no moving dots")
    h = m.evaluate("document.querySelector('#fig').clientHeight"); vert = m.evaluate("(() => { const ys = [...document.querySelectorAll('#fig g.n')].map(g => new DOMMatrix(getComputedStyle(g).transform).f); return Math.max(...ys) - Math.min(...ys); })()")
    check(h >= 400 and vert > 150, f"phone: diagram turns vertical ({h}px tall, spread {round(vert)}px)")
    check(m.evaluate("document.documentElement.scrollWidth") <= 390, "phone: no sideways scroll")
    check(not e2, "no script errors on phone" + ("" if not e2 else ": " + "; ".join(e2[:3])))
    b.close()

print(f"\n{passes} passed, {len(fails)} failed")
for f in fails: print("  - " + f)
sys.exit(1 if fails else 0)
