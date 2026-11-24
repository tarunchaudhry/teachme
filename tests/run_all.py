#!/usr/bin/env python3
"""teachme test suite. Run: python3 tests/run_all.py [--shots DIR]

1. Validator: every example course must be clean; deliberately broken copies must be rejected.
2. Player (needs playwright + chromium): render every example, click through every step of every
   lesson at laptop and phone widths in light and dark, fail on script errors, sideways scroll,
   unreachable steps, or text contrast below WCAG AA.
"""
import copy, glob, json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, "skills", "teachme")
sys.path.insert(0, os.path.join(SK, "scripts"))
import validate as V  # noqa: E402

fails = []
def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok: fails.append(msg)

EXAMPLES = sorted(glob.glob(os.path.join(SK, "examples", "*", "course.json")))

def validator_tests():
    print("Validator")
    for p in EXAMPLES:
        c = json.load(open(p)); e, w = V.validate(c, os.path.join(os.path.dirname(p), "sources"))
        check(not e, f"{os.path.basename(os.path.dirname(p))} is clean ({len(e)} errors, {len(w)} warnings)")
    base = json.load(open(EXAMPLES[0])); sd = os.path.join(os.path.dirname(EXAMPLES[0]), "sources")
    L = lambda c, i=0: c["lessons"][i]
    def step(c, phase, i=0): return next(s for s in L(c, i)["steps"] if s["phase"] == phase)
    def first_num_quiz(c):
        for l in c["lessons"]:
            for q in l["quiz"]:
                if q["type"] == "numeric": return q
    def first_sim(c):
        for l in c["lessons"]:
            for s in l["steps"]:
                if s.get("simulation"): return s["simulation"]
    muts = {
        "number with no claim": lambda c: step(c, "explain")["body"].append("It has 175 billion parameters."),
        "invented quote": lambda c: c["sources"][0]["quotes"][0].update(text="This sentence is not in the source at all, not anywhere"),
        "wrong numeric answer": lambda c: first_num_quiz(c).update(answer=first_num_quiz(c)["answer"] + 5),
        "phases out of order": lambda c: L(c)["steps"].insert(0, L(c)["steps"].pop(5)),
        "missing teach-back": lambda c: L(c)["steps"].remove(step(c, "teachback")),
        "objective never quizzed": lambda c: L(c)["objectives"].append({"id": "oX", "verb": "apply", "text": "x"}),
        "all multiple-choice recall": lambda c: [q.update(type="mcq", options=["a", "b", "c"], answer=0) for q in L(c)["quiz"]],
        "broken simulation formula": lambda c: first_sim(c)["outputs"][0].update(expr="exp(nope)"),
        "diagram edge to missing node": lambda c: step(c, "explain")["scene"]["edges"].append({"from": "x1", "to": "x2"}),
        "concept map cycle": lambda c: c["conceptMap"]["edges"].append([c["conceptMap"]["edges"][-1][1], c["conceptMap"]["edges"][0][0]]),
        "hook too long": lambda c: step(c, "hook")["body"].append("word " * 90),
        "duplicate quiz id across lessons": lambda c: L(c, 1)["quiz"][0].update(id=L(c)["quiz"][0]["id"]),
        "unsupported fact claim": lambda c: L(c)["claims"].append({"id": "cz", "text": "x", "kind": "fact", "support": []}),
    }
    for name, f in muts.items():
        c = copy.deepcopy(base); f(c); e, _ = V.validate(c, sd)
        check(bool(e), f"rejects: {name}")

def lum(rgb):
    def ch(v):
        v /= 255; return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb; return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)
def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)

PAIRS = [("body", "--ink", "--bg", 7.0), ("body", "--soft", "--bg", 4.5), ("body", "--ink", "--card", 7.0), ("body", "--ink", "--panel", 4.5),
         ("body", "--pri", "--bg", 4.5), ("body", "--onc", "--pri", 4.5), ("body", "--ink", "--hl", 4.5), ("body", "--miss", "--card", 4.5),
         ("body", "--ok", "--card", 4.5), ("body", "--soft", "--panel", 4.5)]

def player_tests(shots):
    print("Player")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  skip playwright not installed"); return
    import render as R  # noqa
    exe = next((x for x in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"] if os.path.exists(x)), None)
    tmp = tempfile.mkdtemp()
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}), args=["--no-sandbox"])
        for cp in EXAMPLES:
            name = os.path.basename(os.path.dirname(cp)); out = os.path.join(tmp, name + ".html")
            course = json.load(open(cp)); tpl = open(os.path.join(SK, "assets", "player.html")).read()
            data = json.dumps(course, ensure_ascii=False).replace("</", "<\\/")
            open(out, "w").write(tpl.replace("/*__COURSE_JSON__*/", data, 1).replace("__TITLE__", course["title"], 1))
            url = "file://" + out
            for w, h in [(1280, 860), (390, 844)]:
                for scheme in ["light", "dark"]:
                    tag = f"{name} {w}px {scheme}"
                    pg = b.new_page(viewport={"width": w, "height": h}, color_scheme=scheme); errs = []
                    pg.on("pageerror", lambda e: errs.append(str(e)))
                    pg.goto(url + "#home"); pg.wait_for_timeout(700)
                    if shots: pg.screenshot(path=f"{shots}/{name}-{w}-{scheme}-home.png")
                    if scheme == "light" or w == 1280:
                        cols = pg.evaluate("""() => { const d = document.createElement('div'); document.body.appendChild(d); const o = {};
                          for (const v of ['--ink','--soft','--bg','--card','--panel','--pri','--onc','--hl','--miss','--ok']) { d.style.color = `var(${v})`; o[v] = getComputedStyle(d).color; }
                          d.remove(); return o; }""")
                        rgb = {k: tuple(int(float(x)) for x in v[v.index('(') + 1:v.index(')')].replace('/', ',').split(',')[:3]) for k, v in cols.items()}
                        bad = [f"{f} on {bg} {contrast(rgb[f], rgb[bg]):.1f}<{m}" for _, f, bg, m in PAIRS if contrast(rgb[f], rgb[bg]) < m]
                        check(not bad, f"{tag}: contrast " + ("AA+" if not bad else "; ".join(bad)))
                    steps_seen = 0
                    for l in course["lessons"]:
                        pg.goto(url + "#l-" + l["id"]); pg.wait_for_timeout(250)
                        for i, s in enumerate(l["steps"]):
                            k = pg.text_content(".kicker") or ""
                            if f"step {i+1} of" in k: steps_seen += 1
                            pd = pg.query_selector("[data-pred]")
                            if pd: pd.click(); pg.wait_for_timeout(150)
                            if shots and (s["phase"] in ("explain", "guided_practice") and i in (2, 6)):
                                pg.wait_for_timeout(700); pg.screenshot(path=f"{shots}/{name}-{l['id']}-{i+1}-{w}-{scheme}.png", full_page=True)
                            if i < len(l["steps"]) - 1: pg.click('[data-nav="1"]'); pg.wait_for_timeout(120)
                        sw = pg.evaluate("document.documentElement.scrollWidth")
                        if sw > w: errs.append(f"sideways scroll {sw}px in {l['id']}")
                    for r in ["review", "test", "sources"] + [f"c-{c['id']}" for c in course.get("checkpoints", [])]:
                        pg.goto(url + "#" + r); pg.wait_for_timeout(200)
                    total = sum(len(l["steps"]) for l in course["lessons"])
                    check(steps_seen == total and not errs, f"{tag}: {steps_seen}/{total} steps, " + ("no errors" if not errs else "; ".join(errs[:3])))
                    pg.close()
        b.close()

if __name__ == "__main__":
    shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
    if shots: os.makedirs(shots, exist_ok=True)
    validator_tests(); player_tests(shots)
    print(f"\n{'PASS' if not fails else 'FAIL'}: {len(fails)} failing checks")
    sys.exit(1 if fails else 0)
