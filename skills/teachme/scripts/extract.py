#!/usr/bin/env python3
"""Extract plain text from a learner's resource so quotes can be string-matched.

Usage: python3 extract.py <input file> <output .txt>

Handles .pdf (pdftotext, else pypdf), .docx (python-docx), .html/.htm, .md/.txt, .pptx (python-pptx), .epub (ebooklib).
Writes UTF-8 text. Scanned PDFs with no text layer need OCR first (the script says so).
"""
import os, re, subprocess, sys, html as H

def pdf(p):
    try:
        return subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True, check=True).stdout
    except Exception:
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(p).pages)

def docx(p):
    import docx as D
    d = D.Document(p)
    parts = [x.text for x in d.paragraphs]
    for t in d.tables:
        for r in t.rows: parts.append(" | ".join(c.text for c in r.cells))
    return "\n".join(parts)

def pptx(p):
    from pptx import Presentation
    out = []
    for i, s in enumerate(Presentation(p).slides, 1):
        out.append(f"--- slide {i} ---")
        for sh in s.shapes:
            if sh.has_text_frame: out.append(sh.text_frame.text)
    return "\n".join(out)

def htmltext(s):
    s = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</h\d>|</li>", "\n", s)
    return H.unescape(re.sub(r"<[^>]+>", " ", s))

def epub(p):
    import ebooklib
    from ebooklib import epub as E
    b = E.read_epub(p)
    return "\n".join(htmltext(i.get_content().decode("utf-8", "replace")) for i in b.get_items() if i.get_type() == ebooklib.ITEM_DOCUMENT)

def main():
    if len(sys.argv) != 3: print(__doc__); sys.exit(2)
    src, out = sys.argv[1:]
    ext = os.path.splitext(src)[1].lower()
    if ext == ".pdf": t = pdf(src)
    elif ext == ".docx": t = docx(src)
    elif ext == ".pptx": t = pptx(src)
    elif ext == ".epub": t = epub(src)
    elif ext in (".html", ".htm"): t = htmltext(open(src, encoding="utf-8", errors="replace").read())
    else: t = open(src, encoding="utf-8", errors="replace").read()
    t = re.sub(r"[ \t]+", " ", t)
    if ext == ".pdf" and len(t.strip()) < 200:
        print("WARNING: almost no text extracted; this PDF is probably scanned and needs OCR (e.g. ocrmypdf) first.")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w", encoding="utf-8").write(t)
    print(f"{out}: {len(t.split())} words")

if __name__ == "__main__":
    main()
