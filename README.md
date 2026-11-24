# teachme

`/teachme` turns any topic, chapter, subject or course, plus your own PDFs, notes, slides and links, into an interactive website you can learn from fast and actually remember.

## Use it
```
/teachme how AI works
/teachme Chapter 4 of my thermodynamics notes   (attach the PDF)
/teachme React Server Components --level advanced --lessons 4
/teachme continue how-ai-works                   (build the next module of a big course)
```

## What every course gets
- Lessons built on **RAPID-8**: problem hook, pretest, explanation with a live animated diagram, worked example, practice or a predict-then-run simulation, recall quiz with an 80% mastery gate, teach-back with a confidence check, spaced review.
- **Spaced-review deck** (FSRS-style scheduler), mixed **checkpoints** every few lessons, and a **1-week test**.
- **Sources panel**: every fact is tied to an exact quote, checked word for word by a script against the saved source text. Toy numbers are labelled.
- Skip-ahead if the pretest shows you already know it; continue-anyway if the mastery gate blocks you; Listen (on-device speech); Anki export; a Plan tab that paces the course (all today, daily minutes, a few days a week, or by a date); text-size control; works on phones.
- No video: diagrams are animated SVG built from the lesson data, so every label can be checked.

## How it is built
1. Intake and sizing (one concept → 1 lesson; topic → 3-6; subject → modules, one module per run).
2. Source pack: your files first (`scripts/extract.py`), then the web. Exact text saved per source.
3. Concept map and outline (pauses for approval when a course has 4+ lessons).
4. Lessons written into one `course.json` (see `skills/teachme/references/schema.md`).
5. `scripts/validate.py`: schema, protocol order, quote matching, numbers-must-have-claims, numeric answers recomputed, objectives assessed, simulation formulas evaluated.
6. `scripts/render.py`: injects the course into a single self-contained HTML player.
7. Published as an artifact (or delivered as `index.html`).

## Honest limits
- No human expert reviews the content. Quote matching proves a quote exists in the saved text, not that the source is right or the quote is used fairly; the sources panel is there so learners can check.
- Web pages fetched through a summarising tool may be saved as excerpts rather than full text; the course lists this under known gaps.
- Progress and the review deck live in one browser on one device.
- Not for safety-critical or regulated content without an expert, weekly-changing topics, hands-on motor skills, or contested values questions.

## Tests
```
python3 tests/run_all.py            # checker mutation tests + every step at laptop/phone, light/dark, contrast, pacing
python3 tests/test_ui.py            # presses every control: quizzes, mastery gate, sims, diagrams animating, review deck, plan, phone menu, reduced motion
```
Both need Playwright and a Chromium for the browser parts.

Requires Python 3 in the session. Optional: `pdftotext` or `pypdf`, `python-docx`, `python-pptx`, `ebooklib` for extracting learner files.
