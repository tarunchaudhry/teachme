#!/usr/bin/env python3
"""Render a validated course.json into one self-contained HTML lesson site.

Usage: python3 render.py course.json [--out index.html] [--sources-dir DIR] [--force]

Runs validate.py first and refuses to render if it finds errors (unless --force).
"""
import html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate as V  # noqa: E402

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    path = a[0]
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(os.path.dirname(os.path.abspath(path)), "index.html")
    sd = a[a.index("--sources-dir") + 1] if "--sources-dir" in a else os.path.join(os.path.dirname(os.path.abspath(path)), "sources")
    with open(path, encoding="utf-8") as fh: course = json.load(fh)
    e, w = V.validate(course, sd if os.path.isdir(sd) else None)
    if e and "--force" not in a:
        for x in e: print("ERROR  " + x)
        print(f"\nNot rendered: {len(e)} errors. Fix them (or pass --force for a draft preview).")
        sys.exit(1)
    with open(os.path.join(HERE, "..", "assets", "player.html"), encoding="utf-8") as fh: tpl = fh.read()
    data = json.dumps(course, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
    page = tpl.replace("/*__COURSE_JSON__*/", data, 1).replace("__TITLE__", html.escape(course.get("title", "Course")), 1)
    with open(out, "w", encoding="utf-8") as fh: fh.write(page)
    print(f"Rendered {out} ({len(page)//1024} KB) · {len(course.get('lessons') or [])} lessons · {len(w)} warnings")

if __name__ == "__main__":
    main()
