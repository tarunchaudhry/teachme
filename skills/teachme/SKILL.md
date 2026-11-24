---
name: teachme
description: Turns any topic, chapter, subject or course, plus the learner's own PDFs, notes, slides and links, into an interactive learn-fast lesson website built on the RAPID-8 protocol (pretest, explain with live diagrams, worked examples, recall quizzes with a mastery gate, teach-back, spaced review). Use when someone types /teachme, or asks to "teach me X", "make a course on X", "turn these notes/this PDF into lessons", or "help me learn X fast".
---

# /teachme

Build a short, sourced, interactive course a learner can finish fast and remember. Output is one self-contained web page: lessons with live diagrams and simulations, recall quizzes, a mastery gate, teach-back, a spaced-review deck, checkpoints, a 1-week test and a sources panel.

Arguments: `/teachme <topic or request> [--pace "2h daily" | today | "3x a week" | "by 2026-12-15"] [--lessons N] [--level beginner|intermediate|advanced] [--audience "..."] [--lang xx] [--no-web]`, plus any attached files or pasted links.

Read before building: `references/protocol.md` (phases, sizing), `references/schema.md` (the course.json contract), `references/authoring.md` (closed-book rules). A complete worked example (3 lessons, validator-clean) is in `examples/how-ai-works/`; copy its patterns. Scripts live in this skill's `scripts/` folder; run them with python3 using paths relative to this skill's base directory.

## Workflow

Keep a visible task list. Work in a fresh folder, e.g. `./teachme-<course-id>/` containing `course.json`, `sources/` and the rendered `index.html`.

### 1. Intake and scope
- Parse the request: topic, level, audience, language, lesson count, and every attached file or link.
- Pick the size from the sizing table in protocol.md unless `--lessons` is given.
- Set the learning pace. If the request doesn't say (no `--pace`, no "today", "daily", "by Friday" etc.), ask one question with these options: all today in one sitting; a set time every day (ask how many minutes, default 30); a few sessions a week; by a date (exam, interview). Also ask how long they need to remember it (a week, a month or two, a year or more) unless a date already implies it. Store the answer as `pace` (see protocol.md, Pacing). If no one can answer, use daily, 30 minutes, a month, and say so. The pace also shapes size: with "all today" and under 2 hours, keep the course short enough to finish.
- If the request is truly ambiguous (e.g. "Python" could be a language or a snake; no level and the audience matters), ask one short question. Otherwise state the reading you took in one line and continue.
- Big subjects (more than about 8 lessons): plan all modules, build only module 1 this run, and list the rest in `outline{}`. Say how to continue: run `/teachme continue <course-id>`.

### 2. Source pack
- Learner material first: for each file run `scripts/extract.py <file> sources/<id>.txt`. Images: read them and transcribe the relevant text into a notes source. Pasted notes: save verbatim as `sources/<id>.txt`.
- Links the learner gave: fetch each and save the text.
- Fill gaps with web research (skip with `--no-web`): 3-8 good sources for a topic, primary sources first. Save fetched text to `sources/<id>.txt`.
- Pull verbatim quotes into `sources[].quotes`. Record what nothing covers in `gaps`.

### 3. Concept map and outline
- Build a prerequisite concept map (acyclic, at most 16 nodes, each node pointing to the lesson that teaches it) and a list of common misconceptions.
- Order lessons so prerequisites come first. Write 1-5 objectives per lesson with Bloom verbs.
- Checkpoint: for 4 or more lessons, show the outline (modules, lesson titles, objectives in one line each) and ask the learner to approve or adjust before building. For 1-3 lessons, build straight through.

### 4. Lessons
Write each lesson into course.json following schema.md and authoring.md: claims first, then steps in protocol order, then quiz items and flashcards. Design each lesson's explain steps as one evolving scene. Add a simulation wherever a quantity changes with a parameter. Add a checkpoint every 3-5 lessons.

### 5. Validate and repair
Run `python3 scripts/validate.py course.json --sources-dir sources`. Fix every ERROR by changing content, not by weakening it: find a supporting quote, attach the claim, mark toy numbers illustrative, or cut the sentence. Re-run. At most two repair rounds per lesson; if errors remain, report them plainly. Then do the fact-check pass in authoring.md and re-run the validator.

### 6. Render
Run `python3 scripts/render.py course.json --out index.html`. It refuses to render with errors.

### 7. Deliver and check
- If an artifact publishing tool is available, publish `index.html` as an artifact (title = course title, icon "book"). For a continued course, republish the same artifact. Otherwise send the file.
- Open or read back the page once if the session can; at least confirm the JSON embedded and the page has no script errors (e.g. a headless browser if installed).
- Reply briefly: what was built (lessons, minutes), what the sources were, any gaps or unverified areas, and the one habit that matters: come back for Review and take the 1-week test.

## Continuing and editing
- `/teachme continue <course-id>`: load the existing course.json, build the next outlined module, re-validate, re-render, republish the same artifact. Progress is kept in the learner's browser by course id, so keep the id unchanged.
- Edits ("make lesson 2 easier", "add my lecture notes"): change course.json, re-validate, re-render, republish.

## Limits to state honestly
- No human expert reviews the content; the claims panel shows every fact and its quote so learners can check. Quote matching proves a quote exists in the saved text, not that it is correct or used in context.
- Progress and the review deck are saved in the learner's browser on one device.
- Not suited to safety-critical or regulated content without an expert, fast-changing news, hands-on motor skills, or contested values questions with no single right answer. Say so and offer a lighter alternative if asked for these.
