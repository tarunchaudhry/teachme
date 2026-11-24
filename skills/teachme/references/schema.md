# course.json schema (schemaVersion 1)

One file holds the whole course. `scripts/validate.py` enforces everything marked **must**.
All ids are kebab-case (`a-z0-9-`). Quiz-item ids and flashcard ids **must** be unique across the whole course.

```jsonc
{
  "schemaVersion": 1,
  "id": "how-ai-works",
  "title": "How AI works",
  "summary": "One or two sentences: what the learner will be able to do.",   // ==highlight== allowed
  "audience": "curious non-engineers",
  "level": "beginner",                    // beginner | intermediate | advanced
  "language": "en",                       // BCP-47, used for Listen (Web Speech)
  "mastery": 0.8,                         // retrieval-quiz bar for "mastered"
  "desiredRetention": 0.9,                // FSRS target, 0.7-0.97
  "pace": { "mode": "today|daily|weekly|deadline", "minutes": 30, "perWeek": 3, "deadline": "2026-12-15", "retain": "week|month|year" },  // default plan; learner can change it in the Plan tab
  "gaps": ["Things the sources did not cover, stated plainly"],
  "sources": [Source],
  "conceptMap": { "nodes": [{ "id", "label", "lesson"? }], "edges": [["from-id", "to-id"]] },  // must be acyclic; edge = prerequisite -> dependent
  "modules": [{ "id", "title", "lessons": ["lesson-id", ...] }],
  "outline": { "lesson-id": "Title of a lesson not built yet" },   // planned lessons for multi-run courses
  "lessons": [Lesson],
  "checkpoints": [{ "id", "title", "afterLesson": "lesson-id", "items": [QuizItem + "lessonRef"] }]
}
```

## Source
```jsonc
{ "id": "src-3b1b-gpt", "title": "But what is a GPT? (3Blue1Brown)", "url": "https://...", // url optional for user notes
  "kind": "web|pdf|notes|book|paper|video|docs|user|other", "accessed": "2026-11-23",
  "quotes": [{ "id": "q1", "text": "verbatim text copied from sources/<id>.txt" }] }
```
The exact text of each source **must** be saved at `sources/<source-id>.txt` next to course.json. Every quote **must** appear in that file (whitespace, case, curly quotes and dashes are normalised before matching). Quotes of 8-40 words work best.

## Lesson
```jsonc
{
  "id": "next-word-prediction", "title": "...", "summary": "...", "minutes": 16,
  "prerequisites": ["earlier-lesson-id"],                    // must come earlier in module order
  "misconceptions": ["What learners wrongly believe, used for hooks and distractors"],
  "objectives": [{ "id": "o1", "verb": "remember|understand|apply|analyze|evaluate|create", "text": "Explain why ..." }],  // 1-5
  "claims": [Claim],
  "steps": [Step],          // >= 8, phases in protocol order
  "quiz": [QuizItem],       // >= 3 total; retrieval items must cover every objective
  "flashcards": [{ "id": "nwp-f1", "front": "...", "back": "...", "objective": "o1" }]   // 3-15
}
```

## Claim
```jsonc
{ "id": "c1", "text": "GPT-3 has 175 billion parameters.", "kind": "fact|number|definition|illustrative",
  "support": [{ "sourceId": "src-x", "quoteId": "q2" }] }
```
- Non-illustrative claims **must** cite at least one quote.
- `number` claims: every number in the claim text **must** appear in a supporting quote.
- `illustrative` claims hold toy numbers. Their text should say "illustrative", "toy" or "example"; the player labels them.

## Step
```jsonc
{
  "id": "s3", "phase": "hook|activate|explain|worked_example|guided_practice|retrieval|teachback|review",
  "title": "...", "seconds": 90,
  "body": ["Paragraph with **bold**, *italic*, ==highlighted key term==, `code`, [link](https://...)", "- bullet\n- bullet"],
  "callout": "Optional one-line takeaway, shown highlighted",
  "narration": "Optional text for Listen; otherwise the body is read",
  "claims": ["c1"],          // every number in body/callout/workedExample/modelAnswer must appear in one of these claims
  "quiz": ["q1", "q2"],      // ids from lesson.quiz
  "scene": Scene, "simulation": Simulation,
  "workedExample": { "problem": "...", "selfExplainPrompt": "Why does step 2 come before step 3?",
                     "steps": [{ "subgoal": "Find the ...", "text": "...", "faded": false }] },
  "teachback": { "prompt": "Explain to a friend ...", "modelAnswer": ["..."], "rubric": ["Mentions ...", "Says why ..."] }
}
```
Phase rules **enforced**: order never goes backwards; hook, activate, explain, retrieval, teachback and review present; a worked_example or guided_practice present; hook is 1-2 steps, at most 80 words, with a scene or simulation; explain steps at most 150 words; activate step has quiz items; retrieval has at least 3 items, at least a third of them not `mcq`; teachback step has a `teachback` block with at least 2 rubric points.

## Scene (keyed snapshot)
```jsonc
{ "caption": "What the picture shows", "alt": "Screen-reader description",
  "groups": [{ "id": "g1", "label": "Inside the model", "x": 30, "y": 5, "w": 40, "h": 90, "tone": "muted" }],
  "nodes": [{ "id": "tok", "label": "Tokens\n(word pieces)", "x": 10, "y": 50, "shape": "box|pill|circle|diamond|cylinder|text", "tone": "main|accent|muted|ok|warn" }],
  "edges": [{ "from": "tok", "to": "emb", "label": "lookup", "flow": true, "dashed": false, "curve": false }] }
```
- x and y are 0-100 (node centres). Keep 12 nodes or fewer, labels at most 24 characters per line (use `\n`).
- Scenes are full snapshots. Reuse the same node id across consecutive steps and the node glides to its new place; new ids fade in, missing ids fade out. Design a lesson's explain steps as one evolving picture.
- `flow: true` sends a moving dot along the edge (data moving). Use it for one or two edges at a time.

## Simulation (numbers computed in code)
```jsonc
{ "params": [{ "id": "temp", "label": "Temperature", "min": 0.1, "max": 2, "step": 0.1, "default": 1, "unit": "" }],
  "constants": { "a": 2.0, "b": 1.0 },
  "outputs": [{ "id": "pA", "label": "P(\"cat\")", "expr": "exp(a/temp)/(exp(a/temp)+exp(b/temp))", "decimals": 2, "unit": "" }],
  "chart": { "x": "temp", "y": ["pA"] },
  "predict": { "prompt": "If temperature goes up, the top word's probability ...", "options": ["rises", "falls", "stays"], "answer": 1, "explanation": "..." },
  "note": "Toy numbers: two candidate words with made-up scores." }
```
Expression grammar: numbers, param/constant names, `+ - * / ^ **`, parentheses, `pi`, `e`, and functions `exp log ln log10 log2 sqrt abs min max round floor ceil pow sin cos tanh sigmoid`. The validator evaluates every output at the defaults and at each param's min and max.

## QuizItem
Common: `id`, `type`, `prompt`, `objective` (lesson objective id), `explanation` (why the answer is right; required except recall).
| type | extra fields |
|---|---|
| `mcq` | `options` (>=3), `answer` (index). Distractors come from real misconceptions. |
| `multi` | `options`, `answer` (list of indexes) |
| `numeric` | `answer`, `unit`, `tolerance`, `compute: { "expr": "...", "vars": {...} }` (recomputed by the validator) |
| `cloze` | `accept`: list of accepted answers (matched ignoring case and punctuation) |
| `order` | `items` listed in the correct order (the player shuffles them) |
| `recall` | `answer`: model answer (markdown string or list); learner self-grades |

Checkpoint items add `lessonRef` (the lesson the item comes from) so the validator can confirm the checkpoint mixes lessons.
