---
name: review
description: Audit course material against the shared course standard and for correctness, continuity and alignment between courses. Use before a semester starts, before publishing a session, when comparing two courses, or when asked whether material is ready, consistent or aligned.
---

# Review course material

The kit lives at `${CLAUDE_PLUGIN_ROOT}`; the standard is `STANDARD.md`.

## 1. Run the checker

`python3 ${CLAUDE_PLUGIN_ROOT}/tools/coursekit.py lint <course root>` for each course. Keep
its counts; don't repeat its findings one by one.

## 2. Check what the checker can't

For each session in scope:

1. **One explanation per concept**: the same concept explained in the lab and in the talk
   or the SOP.
2. **Leaked answers**: questions in student documents that carry their answer.
3. **Unsupported claims**: numbers with no measurement or source; protocol, standard or
   datasheet facts with no section; commands for a toolchain version the course doesn't pin.
4. **Continuity**: uses only what earlier sessions taught; references to other sessions
   (Lab N, §n, "last week") point at the right content.
5. **Stakeholders**: the memo sounds like its author in the scenario; every stakeholder
   question is answered by a measurement.
6. **Load**: the tasks and setup fit the session's time.
7. **Visuals**: colors follow the palette in `coursekit.toml`; figures use the course's own
   data where it exists.

## 3. Across courses (when given two or more)

1. Terms defined differently in the glossaries, or one concept under two names.
2. Prerequisites one course assumes that the other doesn't teach, or teaches later.
3. Format drift: section names, rubric shape, theme, record structure.

## 4. Report

Findings ranked by impact on students, each with `file:line`, the problem and the fix.
Keep standard conformance separate from correctness. Edit nothing unless asked.
