#!/usr/bin/env python3
"""Validate a teachme course.json against the RAPID-8 protocol and the claims ledger.

Usage: python3 validate.py course.json [--sources-dir DIR] [--json report.json] [--no-source-check]

Exit code 0 = no errors (warnings allowed), 1 = errors found.
Every check here is deterministic code. It catches structural, reference, protocol,
number-coverage and quote-existence problems. It cannot tell whether a real quote
actually supports a claim, so a semantic fact-check pass is still needed.
"""
import json, math, os, re, sys, unicodedata

PHASES = ["hook", "activate", "explain", "worked_example", "guided_practice", "retrieval", "teachback", "review"]
REQUIRED = ["hook", "activate", "explain", "retrieval", "teachback", "review"]
VERBS = {"remember", "understand", "apply", "analyze", "evaluate", "create"}
CLAIM_KINDS = {"fact", "number", "definition", "illustrative"}
SRC_KINDS = {"web", "pdf", "notes", "book", "paper", "video", "docs", "user", "other"}
QTYPES = {"mcq", "multi", "numeric", "cloze", "order", "recall"}
SHAPES = {"box", "pill", "circle", "diamond", "cylinder", "text"}
TONES = {"main", "accent", "muted", "ok", "warn"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VAR_RE = re.compile(r"^[A-Za-z_]\w*$")
NUM_RE = re.compile(r"(?<![A-Za-z_])\d[\d,]*(?:\.\d+)?")

errors, warnings = [], []
def err(where, msg): errors.append(f"{where}: {msg}")
def warn(where, msg): warnings.append(f"{where}: {msg}")

# ---------- expression evaluator (same grammar as the player) ----------
FN = {"exp": math.exp, "log": math.log, "ln": math.log, "log10": math.log10, "log2": math.log2, "sqrt": math.sqrt,
      "abs": abs, "min": min, "max": max, "round": round, "floor": math.floor, "ceil": math.ceil, "pow": math.pow,
      "sin": math.sin, "cos": math.cos, "tanh": math.tanh, "sigmoid": lambda x: 1 / (1 + math.exp(-x))}
TOK = re.compile(r"\s*(\d+\.?\d*(?:e[+-]?\d+)?|\.\d+|[A-Za-z_]\w*|\*\*|[-+*/^(),])")

def eval_expr(src, vars_):
    toks, i = [], 0
    while i < len(src):
        m = TOK.match(src, i)
        if not m:
            if src[i:].strip() == "": break
            raise ValueError(f"bad token at {i}")
        toks.append(m.group(1)); i = m.end()
    pos = [0]
    peek = lambda: toks[pos[0]] if pos[0] < len(toks) else None
    def nxt():
        t = peek(); pos[0] += 1
        if t is None: raise ValueError("unexpected end")
        return t
    def prim():
        t = nxt()
        if t == "(":
            v = add()
            if nxt() != ")": raise ValueError(") expected")
            return v
        if t == "-": return -pw()
        if t == "+": return pw()
        if t[0].isdigit() or t[0] == ".": return float(t)
        if t[0].isalpha() or t[0] == "_":
            if peek() == "(":
                nxt(); args = []
                if peek() != ")":
                    args.append(add())
                    while peek() == ",": nxt(); args.append(add())
                nxt()
                if t not in FN: raise ValueError(f"unknown function {t}")
                return float(FN[t](*args))
            if t == "pi": return math.pi
            if t == "e": return math.e
            if t not in vars_: raise ValueError(f"unknown variable {t}")
            return float(vars_[t])
        raise ValueError(f"unexpected {t}")
    def pw():
        b = prim()
        if peek() in ("^", "**"): nxt(); return math.pow(b, un())
        return b
    def un():
        if peek() == "-": nxt(); return -un()
        return pw()
    def mul():
        v = un()
        while peek() in ("*", "/"):
            o = nxt(); r = un(); v = v * r if o == "*" else v / r
        return v
    def add():
        v = mul()
        while peek() in ("+", "-"):
            o = nxt(); r = mul(); v = v + r if o == "+" else v - r
        return v
    v = add()
    if pos[0] < len(toks): raise ValueError(f"trailing {toks[pos[0]]}")
    return v

# ---------- text helpers ----------
def norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("­", "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = re.sub(r"-\s*\n\s*", "", s)          # undo hyphenation across lines
    s = s.replace("*", "").replace("_", " ")  # ignore markdown emphasis in saved text
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

def numbers(text):
    return {n.replace(",", "").rstrip(".") for n in NUM_RE.findall(re.sub(r"\]\(https?:[^)]+\)", "]", text or ""))}

def words(text): return len(re.findall(r"\S+", text or ""))

def as_text(x):
    if x is None: return ""
    if isinstance(x, list): return "\n".join(map(str, x))
    return str(x)

# ---------- checks ----------
def check_quiz_item(q, where, obj_ids):
    if not isinstance(q, dict) or "id" not in q: err(where, "quiz item without id"); return
    w = f"{where}/quiz:{q['id']}"
    t = q.get("type")
    if t not in QTYPES: err(w, f"type must be one of {sorted(QTYPES)}"); return
    if not q.get("prompt"): err(w, "missing prompt")
    if obj_ids is not None and q.get("objective") not in obj_ids: err(w, f"objective '{q.get('objective')}' is not a lesson objective")
    if not q.get("explanation") and t != "recall": warn(w, "no explanation; explanatory feedback is part of the protocol")
    if t in ("mcq", "multi"):
        opts = q.get("options") or []
        if len(opts) < 3: err(w, "needs at least 3 options")
        ans = q.get("answer")
        if t == "mcq" and not (isinstance(ans, int) and 0 <= ans < len(opts)): err(w, "answer must be an option index")
        if t == "multi" and not (isinstance(ans, list) and ans and all(isinstance(a, int) and 0 <= a < len(opts) for a in ans)): err(w, "answer must be a list of option indexes")
        if len(set(map(str, opts))) != len(opts): err(w, "duplicate options")
    elif t == "numeric":
        if not isinstance(q.get("answer"), (int, float)): err(w, "numeric answer must be a number")
        comp = q.get("compute")
        if comp:
            try:
                v = eval_expr(comp["expr"], comp.get("vars", {}))
                tol = q.get("tolerance", abs(q["answer"]) * 0.02)
                if abs(v - q["answer"]) > tol + 1e-9: err(w, f"answer {q['answer']} does not match recomputed {v:.6g}")
            except Exception as e: err(w, f"compute.expr failed: {e}")
        else: warn(w, "numeric item has no compute {expr, vars}; the answer can't be recomputed in code")
    elif t == "cloze":
        if not q.get("accept"): err(w, "cloze needs accept: [answers]")
    elif t == "order":
        if len(q.get("items") or []) < 3: err(w, "order needs at least 3 items (given in the correct order)")
    elif t == "recall":
        if not q.get("answer"): err(w, "recall needs a model answer")

def check_scene(sc, w):
    nodes = sc.get("nodes") or []
    ids = [n.get("id") for n in nodes]
    if not nodes: err(w, "scene has no nodes")
    if len(ids) != len(set(ids)): err(w, "duplicate node ids")
    if len(nodes) > 12: err(w, f"{len(nodes)} nodes; cap is 12 to avoid clutter")
    if len(sc.get("edges") or []) > 14: err(w, "more than 14 edges")
    if not (sc.get("alt") or sc.get("caption")): err(w, "scene needs alt or caption text")
    for n in nodes:
        for k in ("x", "y"):
            v = n.get(k)
            if not isinstance(v, (int, float)) or not 0 <= v <= 100: err(w, f"node {n.get('id')} {k} must be 0-100")
        if n.get("shape", "box") not in SHAPES: err(w, f"node {n.get('id')} shape must be one of {sorted(SHAPES)}")
        if n.get("tone", "main") not in TONES: err(w, f"node {n.get('id')} tone must be one of {sorted(TONES)}")
        if not n.get("label"): err(w, f"node {n.get('id')} has no label")
        elif max(len(x) for x in str(n["label"]).split("\n")) > 24: warn(w, f"node {n['id']} label line over 24 chars; use \\n to wrap")
    for e in sc.get("edges") or []:
        if e.get("from") not in ids or e.get("to") not in ids: err(w, f"edge {e.get('from')}->{e.get('to')} references a missing node")

def check_sim(sim, w):
    params = sim.get("params") or []
    if not params: err(w, "simulation needs params"); return
    vals = dict(sim.get("constants") or {})
    for p in params:
        if not VAR_RE.match(str(p.get("id", ""))): err(w, f"param id '{p.get('id')}' must be an identifier")
        try:
            if not p["min"] < p["max"]: err(w, f"param {p['id']} min must be < max")
            if not p["min"] <= p["default"] <= p["max"]: err(w, f"param {p['id']} default out of range")
        except KeyError as e: err(w, f"param {p.get('id')} missing {e}")
        vals[p.get("id")] = p.get("default", 0)
    outs = sim.get("outputs") or []
    if not outs: err(w, "simulation needs outputs")
    for o in outs:
        try:
            v = eval_expr(o["expr"], vals)
            if not math.isfinite(v): err(w, f"output {o.get('id')} is not finite at defaults")
            for p in params:   # also sample the range ends
                for edge in (p.get("min"), p.get("max")):
                    t = dict(vals); t[p["id"]] = edge; eval_expr(o["expr"], t)
        except Exception as e: err(w, f"output {o.get('id')} expr '{o.get('expr')}' failed: {e}")
    pr = sim.get("predict")
    if pr:
        if not (isinstance(pr.get("answer"), int) and 0 <= pr["answer"] < len(pr.get("options") or [])): err(w, "predict.answer must index predict.options")
    else: warn(w, "no predict block; predict-then-run is the protocol default")
    ch = sim.get("chart")
    if ch:
        if ch.get("x") not in [p.get("id") for p in params]: err(w, "chart.x must be a param id")
        for y in ch.get("y") or []:
            if y not in [o.get("id") for o in outs]: err(w, f"chart.y '{y}' is not an output id")

def check_lesson(l, src, quote_ok, all_quiz_ids, all_card_ids):
    lid = l.get("id", "?"); L = f"lesson:{lid}"
    if not ID_RE.match(lid): err(L, "id must be kebab-case")
    for k in ("title", "summary", "objectives", "steps", "quiz", "flashcards", "claims"):
        if k not in l: err(L, f"missing {k}")
    objs = l.get("objectives") or []
    if not 1 <= len(objs) <= 5: err(L, "needs 1-5 objectives")
    obj_ids = set()
    for o in objs:
        obj_ids.add(o.get("id"))
        if o.get("verb") not in VERBS: err(L, f"objective {o.get('id')} verb must be one of {sorted(VERBS)}")
    # claims
    claims = {}
    for c in l.get("claims") or []:
        cw = f"{L}/claim:{c.get('id')}"
        if c.get("id") in claims: err(cw, "duplicate claim id")
        claims[c.get("id")] = c
        if c.get("kind") not in CLAIM_KINDS: err(cw, f"kind must be one of {sorted(CLAIM_KINDS)}"); continue
        if c["kind"] == "illustrative":
            if "illustrative" not in norm(c.get("text", "")) and "example" not in norm(c.get("text", "")) and "toy" not in norm(c.get("text", "")):
                warn(cw, "illustrative claim text should say it is illustrative/toy/example")
            continue
        sup = c.get("support") or []
        if not sup: err(cw, "non-illustrative claim needs at least one {sourceId, quoteId}")
        qtexts = []
        for s in sup:
            source = src.get(s.get("sourceId"))
            if not source: err(cw, f"unknown sourceId {s.get('sourceId')}"); continue
            q = next((q for q in source.get("quotes", []) if q.get("id") == s.get("quoteId")), None)
            if not q: err(cw, f"unknown quoteId {s.get('quoteId')} in {source['id']}"); continue
            qtexts.append(q["text"])
            if quote_ok.get((source["id"], q["id"])) is False: err(cw, f"cites quote {source['id']}/{q['id']} which was not found in the source text")
        if c["kind"] == "number" and qtexts:
            missing = numbers(c.get("text")) - set().union(*[numbers(t) for t in qtexts])
            if missing: err(cw, f"numbers {sorted(missing)} are not in any supporting quote")
    # quiz
    quiz = {}
    for q in l.get("quiz") or []:
        if q.get("id") in all_quiz_ids: err(L, f"quiz id {q.get('id')} is not unique across the course")
        all_quiz_ids.add(q.get("id")); quiz[q.get("id")] = q
        check_quiz_item(q, L, obj_ids)
    if len(quiz) < 3: err(L, "needs at least 3 quiz items")
    # flashcards
    fc = l.get("flashcards") or []
    if not 3 <= len(fc) <= 15: err(L, "needs 3-15 flashcards")
    for f in fc:
        if f.get("id") in all_card_ids: err(L, f"flashcard id {f.get('id')} is not unique across the course")
        all_card_ids.add(f.get("id"))
        if not f.get("front") or not f.get("back"): err(L, f"flashcard {f.get('id')} needs front and back")
    # steps
    steps = l.get("steps") or []
    if len(steps) < 8: err(L, f"{len(steps)} steps; RAPID-8 needs at least 8")
    seen_ids, last, used_q, secs = set(), -1, set(), 0
    phases_present = [s.get("phase") for s in steps]
    for p in REQUIRED:
        if p not in phases_present: err(L, f"missing phase '{p}'")
    if "worked_example" not in phases_present and "guided_practice" not in phases_present: err(L, "needs a worked_example or guided_practice step")
    hook_words, hook_steps, hook_visual = 0, 0, False
    retrieval_items = []
    for i, s in enumerate(steps):
        sw = f"{L}/step:{s.get('id', i)}"
        if s.get("id") in seen_ids: err(sw, "duplicate step id")
        seen_ids.add(s.get("id"))
        ph = s.get("phase")
        if ph not in PHASES: err(sw, f"phase must be one of {PHASES}"); continue
        idx = PHASES.index(ph)
        if idx < last: err(sw, f"phase '{ph}' is out of order (protocol order: {' > '.join(PHASES)})")
        last = max(last, idx)
        if not s.get("title"): err(sw, "missing title")
        body = as_text(s.get("body"))
        secs += s.get("seconds") or 0
        if not s.get("seconds"): warn(sw, "no seconds estimate")
        for cid in s.get("claims") or []:
            if cid not in claims: err(sw, f"unknown claim {cid}")
        for qid in s.get("quiz") or []:
            if qid not in quiz: err(sw, f"unknown quiz item {qid}")
            used_q.add(qid)
        # numbers in prose must be covered by a claim on this step
        prose = "\n".join([body, as_text(s.get("callout"))])
        we = s.get("workedExample")
        if we: prose += "\n" + as_text(we.get("problem")) + "\n" + "\n".join(as_text(x.get("text")) for x in we.get("steps", []))
        tb = s.get("teachback")
        if tb: prose += "\n" + as_text(tb.get("modelAnswer"))
        covered = set().union(*[numbers(claims[c].get("text")) for c in s.get("claims") or [] if c in claims]) if s.get("claims") else set()
        bad = numbers(prose) - covered
        if bad: err(sw, f"numbers {sorted(bad, key=lambda x: float(x))} in step text are not in any claim attached to this step (spell small counts in words, or attach a claim; toy numbers need an illustrative claim)")
        if s.get("scene"): check_scene(s["scene"], sw + "/scene")
        if s.get("simulation"): check_sim(s["simulation"], sw + "/simulation")
        if ph == "hook":
            hook_steps += 1; hook_words += words(body)
            hook_visual = hook_visual or bool(s.get("scene") or s.get("simulation"))
        if ph == "explain" and words(body) > 150: err(sw, f"{words(body)} words; explain steps are one idea, at most 150 words")
        if ph == "explain" and not s.get("scene") and not s.get("simulation"): warn(sw, "explain step has no visual; dual coding wants words plus a picture")
        if ph == "activate" and not s.get("quiz"): err(sw, "activate (pretest) step needs at least one quiz item")
        if ph == "retrieval": retrieval_items += [quiz[q] for q in s.get("quiz") or [] if q in quiz]
        if ph == "worked_example":
            if not we: err(sw, "worked_example step needs workedExample {problem, steps[{subgoal,text,faded}], selfExplainPrompt}")
            elif not we.get("selfExplainPrompt"): warn(sw, "worked example has no selfExplainPrompt")
        if ph == "guided_practice" and not (we or s.get("simulation") or s.get("quiz")): err(sw, "guided_practice needs a faded workedExample, a simulation or practice quiz items")
        if we and ph == "guided_practice" and not any(x.get("faded") for x in we.get("steps", [])): warn(sw, "guided practice example has no faded steps")
        if ph == "teachback":
            if not tb or not tb.get("prompt") or not tb.get("modelAnswer") or len(tb.get("rubric") or []) < 2:
                err(sw, "teachback step needs teachback {prompt, modelAnswer, rubric[>=2]}")
    if hook_steps > 2: err(L, "hook should be 1-2 steps")
    if hook_words > 80: err(L, f"hook is {hook_words} words; at most 80")
    if hook_steps and not hook_visual: err(L, "hook needs a scene or simulation")
    if len(retrieval_items) < 3: err(L, "retrieval phase needs at least 3 quiz items")
    if retrieval_items:
        rec = sum(1 for q in retrieval_items if q.get("type") != "mcq") / len(retrieval_items)
        if rec < 0.34: err(L, f"only {rec:.0%} of retrieval items are recall-style (non-mcq); need at least a third")
    for o in obj_ids:
        if not any(q.get("objective") == o for q in retrieval_items): err(L, f"objective {o} is not assessed by any retrieval quiz item")
        if not any(f.get("objective") == o for f in fc): warn(L, f"objective {o} has no flashcard")
    for qid in quiz:
        if qid not in used_q: warn(L, f"quiz item {qid} is not used by any step")
    mins = secs / 60
    if steps and not 8 <= mins <= 25: warn(L, f"steps add up to {mins:.1f} min; target is 12-20")
    if l.get("minutes") and abs(l["minutes"] - mins) > 3: warn(L, f"minutes={l['minutes']} but steps add up to {mins:.1f}")

def find_cycle(nodes, edges):
    g = {n: [] for n in nodes}
    for a, b in edges: g.setdefault(a, []).append(b)
    state = {}
    def dfs(u, path):
        state[u] = 1
        for v in g.get(u, []):
            if state.get(v) == 1: return path + [u, v]
            if not state.get(v):
                c = dfs(v, path + [u])
                if c: return c
        state[u] = 2
    for n in list(g):
        if not state.get(n):
            c = dfs(n, [])
            if c: return c

def validate(course, sources_dir=None, source_check=True):
    errors.clear(); warnings.clear()
    C = "course"
    for k in ("id", "title", "modules", "lessons", "sources"):
        if k not in course: err(C, f"missing {k}")
    if course.get("id") and not ID_RE.match(course["id"]): err(C, "id must be kebab-case")
    src = {}
    quote_ok = {}
    for s in course.get("sources") or []:
        sw = f"source:{s.get('id')}"
        if s.get("id") in src: err(sw, "duplicate source id")
        src[s.get("id")] = s
        if s.get("kind") not in SRC_KINDS: err(sw, f"kind must be one of {sorted(SRC_KINDS)}")
        if not s.get("title"): err(sw, "missing title")
        if not s.get("quotes"): warn(sw, "no quotes")
        text = None
        if source_check and sources_dir:
            p = os.path.join(sources_dir, f"{s.get('id')}.txt")
            if os.path.exists(p):
                with open(p, encoding="utf-8", errors="replace") as fh: text = norm(fh.read())
            else: err(sw, f"no source text at {p}; save the exact fetched/extracted text there")
        qids = set()
        for q in s.get("quotes") or []:
            if q.get("id") in qids: err(sw, f"duplicate quote id {q.get('id')}")
            qids.add(q.get("id"))
            if words(q.get("text")) < 4: warn(sw, f"quote {q.get('id')} is very short; short quotes match too easily")
            if text is not None:
                ok = norm(q.get("text", "")) in text
                quote_ok[(s.get("id"), q.get("id"))] = ok
                if not ok: err(sw, f"quote {q.get('id')} not found verbatim in source text: \"{q.get('text', '')[:80]}\"")
    if source_check and not sources_dir: warn(C, "no --sources-dir given; quotes were not string-matched")
    pace = course.get("pace")
    if pace is not None:
        if pace.get("mode") not in ("today", "daily", "weekly", "deadline"): err("pace", "mode must be today|daily|weekly|deadline")
        if pace.get("mode") in ("daily", "weekly", "deadline") and not 10 <= (pace.get("minutes") or 0) <= 240: err("pace", "minutes must be 10-240")
        if pace.get("mode") == "weekly" and not 1 <= (pace.get("perWeek") or 0) <= 7: err("pace", "perWeek must be 1-7")
        if pace.get("mode") == "deadline" and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(pace.get("deadline", ""))): err("pace", "deadline must be YYYY-MM-DD")
        if pace.get("retain", "month") not in ("week", "month", "year"): err("pace", "retain must be week|month|year")
    lessons = course.get("lessons") or []
    lid = [l.get("id") for l in lessons]
    if len(lid) != len(set(lid)): err(C, "duplicate lesson ids")
    order = [x for m in course.get("modules") or [] for x in m.get("lessons", [])]
    if len(order) != len(set(order)): err(C, "a lesson appears in more than one module slot")
    for x in lid:
        if x not in order: err(C, f"lesson {x} is not listed in any module")
    outline = course.get("outline") or {}
    for x in order:
        if x not in lid and x not in outline: err(C, f"module lists '{x}' which is neither built nor in outline{{}}")
        elif x not in lid: warn(C, f"lesson '{x}' is outlined but not built yet")
    byid = {l.get("id"): l for l in lessons}
    for l in lessons:
        for p in l.get("prerequisites") or []:
            if p not in order: err(f"lesson:{l['id']}", f"prerequisite {p} is not in the course")
            elif order.index(p) > order.index(l["id"]): err(f"lesson:{l['id']}", f"prerequisite {p} comes later in the course order")
    cyc = find_cycle(lid, [(p, l["id"]) for l in lessons for p in l.get("prerequisites") or []])
    if cyc: err(C, f"lesson prerequisites form a cycle: {' -> '.join(cyc)}")
    cm = course.get("conceptMap")
    if cm:
        nids = [n.get("id") for n in cm.get("nodes") or []]
        for a, b in cm.get("edges") or []:
            if a not in nids or b not in nids: err(C, f"conceptMap edge {a}->{b} references a missing node")
        cyc = find_cycle(nids, cm.get("edges") or [])
        if cyc: err(C, f"conceptMap must be acyclic: {' -> '.join(cyc)}")
        for n in cm.get("nodes") or []:
            if n.get("lesson") and n["lesson"] not in order: err(C, f"conceptMap node {n['id']} points to unknown lesson {n['lesson']}")
        if len(nids) > 16: warn(C, f"concept map has {len(nids)} nodes; over 16 gets cluttered")
    else: warn(C, "no conceptMap")
    all_q, all_c = set(), set()
    for l in lessons: check_lesson(l, src, quote_ok, all_q, all_c)
    for cp in course.get("checkpoints") or []:
        w = f"checkpoint:{cp.get('id')}"
        if cp.get("afterLesson") not in order: err(w, "afterLesson must be a lesson id")
        items = cp.get("items") or []
        if len(items) < 4: err(w, "checkpoint needs at least 4 items")
        for q in items:
            if q.get("id") in all_q: err(w, f"quiz id {q.get('id')} is not unique")
            all_q.add(q.get("id")); check_quiz_item(q, w, None)
        if len({q.get("lessonRef") for q in items if q.get("lessonRef")}) < 2: warn(w, "checkpoint items should mix at least 2 lessons (set lessonRef)")
    if len(lessons) >= 4 and not course.get("checkpoints"): warn(C, "4+ lessons but no cumulative checkpoint; add one every 3-5 lessons")
    return errors, warnings

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    path = a[0]
    sd = a[a.index("--sources-dir") + 1] if "--sources-dir" in a else os.path.join(os.path.dirname(os.path.abspath(path)), "sources")
    if not os.path.isdir(sd): sd = None
    with open(path, encoding="utf-8") as fh: course = json.load(fh)
    e, w = validate(course, sd, "--no-source-check" not in a)
    for x in e: print("ERROR  " + x)
    for x in w: print("warn   " + x)
    n_l = len(course.get("lessons") or [])
    n_q = sum(len(s.get("quotes") or []) for s in course.get("sources") or [])
    print(f"\n{len(e)} errors, {len(w)} warnings · {n_l} lessons · {n_q} quotes checked against source text" if sd else f"\n{len(e)} errors, {len(w)} warnings · {n_l} lessons")
    if "--json" in a:
        with open(a[a.index("--json") + 1], "w") as fh: json.dump({"errors": e, "warnings": w}, fh, indent=2)
    sys.exit(1 if e else 0)

if __name__ == "__main__":
    main()
