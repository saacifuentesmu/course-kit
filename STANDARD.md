# Course Standard — draft v0.1

A shared format for project-based engineering courses at UNAL Manizales. Students
meet the same structure in every course; teachers can reuse each other's sessions;
material stays correct with less effort. Drafted from 4101137 Real-Time Systems and
4201327 IoT Systems Design as a starting point for discussion. Items marked
**[decide]** are open.

## 1. Principles

1. **One project, all semester.** Each course follows one product through a scenario
   with stakeholders. Every session is a step in building it.
2. **Evidence over assertion.** Students predict, measure, then explain. Every claim in
   a deliverable cites a measurement, a capture or a source.
3. **One explanation per concept.** The talk explains, the lab applies, the SOP holds
   the mechanics. A document links to an explanation instead of repeating it.
4. **Short and visual.** Every document type has a word budget. Tables and figures
   beat prose; figures come from real data when it exists.
5. **Validated before students see it.** Each session records the toolchain version
   and the hardware it last ran on, and when.

## 2. The course repository

| Document | For | Holds |
|---|---|---|
| README | everyone | One-paragraph pitch, through-line, prerequisites (and which course teaches each), outcomes, schedule, assessment, hardware and cost, toolchain versions, references |
| Scenario | students | The company, the product, the stakeholders and what each one asks |
| Setup | students | What to install before week 1, ending in a check that proves it works |
| Record template | students | The team's living deliverable (RET, DDR, …) and its sections |
| Glossary | students | Every course term, with its Spanish (or English) equivalent |
| Readings | students | Per-week reading, with what to skip |
| `coursekit.toml` | tools | Which file is which document type, budgets, palette |

The README schedule has one row per week: talk, lab, and what the record gains that
week. File layout is free: `coursekit.toml` maps files to types. New courses use
`sessions/NN-slug/` with `lab.md`, `talk.md`, `sop.md` and `img/` inside, so a whole
session can move between courses.

## 3. The session

One weekly meeting: a talk (40 min) and a lab (2 h). **[decide]** the default lengths.

| Document | For | Job | Budget |
|---|---|---|---|
| Talk | the class; the instructor's script lives in the speaker notes | Explain what the lab needs, and no more | ≤ 1 slide per minute; ≤ 60 visible words per slide |
| Lab guide | students | Mission, predictions, tasks with evidence, deliverables, rubric | ≤ 1,500 words |
| SOP | students | Commands, wiring, checks, troubleshooting | ≤ 1,500 words; only when the lab needs more than ~10 commands |
| Notes | students | Background no external reading covers | ≤ 2,500 words; optional |
| Key | instructor | Expected values on the reference hardware, rubric notes | Outside the student repository |

### Lab guide

Sections, in this order:

1. **Memo**: a `**From:**` paragraph before the first heading: one stakeholder states the
   problem in their words. It is the objective. A stakeholder table follows when
   several people care.
2. **What you'll measure**: a table of quantity, prediction, your value and target, with
   `____` for every value the lab produces. Predictions are handed in before the lab.
3. **Tasks**: `### Task A — name`, each ending in an `**Evidence:**` line that says
   which log, capture or table proves it.
4. **A course box** (optional): one fixed, course-specific lens, e.g. *What about
   FreeRTOS?* or *ISO/IEC 30141 mapping*.
5. **Deliverables**: which record sections change today.
6. **Rubric**: 100 points, as execution 40 · evidence 30 · analysis 30 unless the
   course says otherwise.

### Talk

A [Marp](https://marp.app) deck in the shared theme (`theme: course`). The speaker
notes are the script: each starts with its time window (`0:00–1:30`) and holds the
question for the room and the misconception to anticipate. Every talk has a title
slide, the objectives, at least one question slide (vote, discuss, vote again), a
bridge to the lab (what they'll measure and the predictions due) and references.

### SOP

Numbered steps, each with exact commands and a **Verify:** line showing the expected
output. Ends with a troubleshooting table: symptom, cause, fix. No theory.

## 4. Writing

1. One document language per course. **[decide]** English or Spanish per course; the
   glossary carries both; code, identifiers and commands stay in English.
2. Student documents ask questions without answering them; answers go in the key.
3. Enumerations are real Markdown lists, never inline `1. … 2. …` in a paragraph.
4. Heavy math goes in `<details>`; the formulas students use go in the readings.
5. No sections that repeat each other (TL;DR, "in plain English", recaps).
6. Numbers carry SI units. A measured number names the board it came from.
7. Links are relative and must resolve.
8. Memos stay under 80 words and sound like the person writing them.

## 5. Visuals

1. **One theme.** Every deck uses `theme/course.css`; a course sets only its accent
   color.
2. **Color means something, all semester.** The course assigns each recurring entity
   (a task, a protocol layer, a node role) one palette color in `coursekit.toml`;
   every figure, slide and annotated capture uses it.
3. **Real data first.** Logic-analyzer captures, traces and plots from the course's own
   measurements beat drawn diagrams. A generated figure keeps its script next to it.
4. **SVG** for figures; Mermaid for diagrams inside documents (GitHub renders it).
5. **Explorables** for concepts that move (schedules, retransmissions, backoff): one
   self-contained HTML file per concept, usable in class and afterwards.

## 6. Assessment

1. The record is the main deliverable: updated weekly, handed in twice.
2. Predictions are graded on reasoning, not on matching the measurement.
3. Raw evidence outranks prose: captures and logs carrying the board's ID and a
   timestamp are the primary artifacts.
4. Every lab closes with a short check at the bench: each member explains one capture
   of their own.
5. AI tools are allowed and declared; the evidence must come from the team's hardware.

## 7. Maintenance

1. Toolchains are pinned per semester in the repository (e.g. a `west.yml`) and bumped
   between semesters after revalidation.
2. `coursekit.toml` holds one validation line per session: date, toolchain, hardware.
3. Continuous integration builds every firmware and runs `coursekit lint` on each push.
4. AI assistance uses the kit's skills, which follow this standard. They never invent
   a measured value: those stay `____` until someone measures them on hardware.

## 8. Open questions

1. Session lengths, and whether every course follows talk + lab.
2. Language policy per course.
3. Default rubric weights.
4. Talks as decks with speaker notes, or a separate script.
5. Where keys live: a gitignored folder or a private repository.
6. One shared scenario universe across courses, or one per course.
