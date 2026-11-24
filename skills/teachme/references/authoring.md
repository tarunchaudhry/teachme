# Authoring rules (closed book)

These rules override style instincts. They exist to stop invented facts and numbers.

## The closed-book rule
1. Write lesson content using ONLY facts present in the source pack (`sources/*.txt` plus `quotes`). If a needed fact is missing, add it to `gaps` and either search for a source or leave it out. Never fill it from memory.
2. Every factual sentence attaches a claim on its step; every non-illustrative claim cites a quote that supports it word for word.
3. Any number in step prose, callouts, worked examples or model answers must appear in a claim attached to that step. Spell small counts as words ("two layers"). Toy numbers go in an `illustrative` claim whose text says they are illustrative, and the prose says so too.
4. Simulations compute every number from an expression. Choose parameter ranges and constants; never hand-type outputs.
5. Numeric quiz answers carry `compute` so the validator recomputes them.

## Getting quotes right
- Save the text exactly as fetched or extracted to `sources/<id>.txt` before writing quotes. For web pages, WebFetch returns a model's summary, so prompt it to "return the page's text verbatim for the sections about X" and save that. Note in the source title or `gaps` if only a summary was available.
- Copy quotes by selecting text from the saved file (grep for a distinctive phrase, then copy the surrounding sentence). Never retype or tidy a quote.
- Prefer primary sources (papers, official docs, textbooks, the learner's own material) over blogs and aggregators.
- A real quote can still be cherry-picked or stretched. Before finishing, reread each claim beside its quote and ask: does the quote say this, at this strength, in this context? Downgrade or drop claims that overreach.
- Keep each quote under about 40 words; copyright limits apply when the source is published work.

## Learner-supplied material
- Treat the learner's files and notes as the primary sources (`kind: "user"`, `"pdf"`, `"notes"`). Follow their terminology, notation and order where sensible.
- Where their notes contradict a reliable source, keep both claims visible and say so in the step and in `gaps`; do not silently "correct" them.
- Fill gaps the learner's material leaves with web sources and mark them as such.

## Writing steps
- Plain words, short sentences, second person. One idea per explain step.
- Mark the one key term per step with ==highlight==.
- No jokes, trivia or decorative detail unrelated to an objective (seductive details hurt learning).
- Hooks: a concrete situation and a prediction question. Use a real misconception for the wrong-but-tempting answer.
- Narration (optional) adds to the screen rather than reading it aloud word for word.

## Scenes
- Draw the mechanism with its parts as recognisable things, left-to-right or top-to-bottom flow.
- Explain steps share node ids so one picture builds up: add a node, move a node, highlight with `tone: "accent"`, grey out with `tone: "muted"`.
- 3-9 nodes is the sweet spot; 12 is the hard cap. One or two `flow` edges per step.
- Leave room: keep node centres at least 15 units apart horizontally for multi-word labels.

## Quizzes and cards
- Retrieval mix per lesson: at least a third non-multiple-choice (cloze, numeric, order, recall). Aim for 4-6 retrieval items.
- Distractors come from `misconceptions`, never from absurd options.
- Each explanation says why the right answer is right and why the tempting wrong one is wrong.
- Flashcards test objectives, one fact or relation per card, answer in under 15 words where possible.
- Checkpoint items mix lessons, test transfer (a new example) more than recall of the lesson's own example.

## Fact-check pass (do it after the validator is clean)
For every claim, reread it beside its quotes and label it supported / overstated / unsupported. Fix or remove anything not fully supported, then re-run the validator. If a different model or vendor is available to the session, a second opinion from it is better than self-review (errors correlate within one model).
