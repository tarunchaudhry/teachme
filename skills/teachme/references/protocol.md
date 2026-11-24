# RAPID-8 lesson protocol

Every lesson is 12-20 minutes and runs eight phases in this order. Retrieval and spacing do most of the work; everything else sets them up.

| Phase | Min | Rule | Avoid | Evidence |
|---|---|---|---|---|
| **hook** | 1-2 | A concrete problem the learner can feel, then ask for a prediction before any teaching. Scene or sim required, at most 80 words. | Motivational intros, fun facts unrelated to the objective, defining terms before they matter | Productive failure (Sinha & Kapur 2021, g≈0.36), pretesting (Richland 2009), coherence/seductive details (Rey 2012) |
| **activate** | 1-2 | Pretest of 1-3 items on what is about to be taught. Wrong answers are welcome; say so. Strong scorers may skip ahead (expertise reversal). | Grading tone, items on things not taught | Pretesting effect (Richland 2009); expertise reversal (Kalyuga 2003) |
| **explain** | 4-6 | One idea per step (2-4 steps), words plus a synced visual. The scene evolves step to step with stable node ids. Concrete first, then the abstract rule. | Walls of text, decorative pictures, narration that repeats on-screen text | Cognitive load (Sweller 1988), multimedia principles (Mayer 2008), segmenting (Rey 2019), signaling (Schneider 2018), dual coding (Paivio 1991), concreteness fading (Fyfe 2014) |
| **worked_example** | 2-3 | A full solution with sub-goal labels, then a self-explain prompt. | Unlabelled steps, skipping the "why" | Worked examples (Sweller & Cooper 1985), self-explanation (Chi 1989) |
| **guided_practice** | 3-4 | A faded example (later steps hidden for the learner to do) or a predict-then-run simulation. | Practice that only repeats the worked example verbatim | Fading (Renkl & Atkinson 2003), generation effect (Slamecka & Graf 1978) |
| **retrieval** | 2-4 | Mostly recall (cloze, numeric, order, recall); every objective assessed; explanatory feedback; mastery gate at 80% with retry, review and continue-anyway. | All multiple choice, trick questions, testing wording rather than understanding | Testing effect (Roediger & Karpicke 2006), recall over recognition (Rowland 2014), feedback (Hattie & Timperley 2007), mastery learning (Kulik 1990) |
| **teachback** | 2-3 | Confidence rating first, then explain in own words, then compare with a model answer and rubric. Shows calibration. | Calling it the "Feynman technique" (no direct trials) | Learning by teaching (Fiorella & Mayer 2013), metacognition (Dunlosky & Rawson 2012) |
| **review** | 0.5-1 | Show the flashcards and add them to the spaced-review deck (FSRS). | Cards that test trivia instead of objectives | Spacing (Cepeda 2006/2008), FSRS (Ye 2022) |

Outside lessons: 5-10 minutes of mixed due cards daily; a cumulative interleaved checkpoint every 3-5 lessons (Rohrer & Taylor 2007); a delayed 1-week test, the honest measure of learning.

## Where the evidence is weak (keep the course honest)
- Learning styles are a myth (Pashler 2008). Offer several modalities because dual coding helps everyone; never ask for a learner's style.
- Bloom's 2-sigma is overstated: tutoring is about d≈0.79 (VanLehn 2011). Never promise 2-sigma results.
- Problem-first reverses for young children and domain-general skills, so keep the hook short.
- Lab effects shrink in the field; only delayed tests on your own learners show real gains.
- Mastery gates can cut completion, hence continue-anyway.

## Sizing
| Request | Shape |
|---|---|
| One concept ("what is a hash map") | 1 lesson, 1 module |
| A topic ("how AI works") | 3-6 lessons, 1-2 modules |
| A chapter of a book or a course unit | 4-8 lessons, 1-2 modules, 1 checkpoint |
| A subject or a whole book/course | Modules of 3-6 lessons; build module 1 in this run, outline the rest in `outline{}` |

Each lesson covers 1-5 objectives that fit in 20 minutes. If an objective needs more, split the lesson.

## Design defaults by level
- **beginner**: more explain steps (3-4), fully worked example plus a faded one, concrete analogies first, plain words.
- **intermediate**: 2-3 explain steps, one worked example, practice by simulation or faded steps.
- **advanced**: 1-2 dense explain steps, skip to practice, harder retrieval (numeric, order, recall), comparisons and edge cases.
