---
name: session
description: Write or revise one session of a course (lab guide, Marp talk, optional SOP) to the shared course standard. Use when creating a new week, porting a lab to a new toolchain, restructuring a lab or lecture to the standard, or updating a session after a hardware or toolchain change.
---

# Write or revise a session

The kit lives at `${CLAUDE_PLUGIN_ROOT}`: the standard is `STANDARD.md`, templates are in
`templates/`, the checker is `tools/coursekit.py`.

## Read first

1. `STANDARD.md`, all of it.
2. The course's `coursekit.toml` (document types, where files live), its README (schedule,
   through-line), its scenario (stakeholders and how each one talks) and its record template.
3. The previous and the next session: what students already know, the numbers they
   measured, who spoke last, what the next session assumes.
4. This session's existing files, and the code or firmware it uses.

## Plan, then confirm

Write a plan of at most ten lines: objectives with measurable verbs, the measurement table
(quantity and target), the tasks and their evidence, the record sections touched, and what
moves to the talk or the SOP. Show it to the teacher before writing when the session is
new or its goal changes.

## Write

1. Lab first (`templates/lab.md`, sections and order from STANDARD §3), then the talk
   (`templates/talk.md`; use the `slides` skill for figures and rendering), then an SOP only
   when the lab needs more than about ten commands.
2. The talk explains only what the lab needs. Its notes are the script, each opening with a
   time window. At least one question slide, whose wrong options encode real misconceptions.
3. Keep the course's voice, stakeholders, file names and link style.
4. Never invent a measured value. Prediction and value cells stay `____`. Expected values
   go to the teacher's key, only from real measurements or cited sources; list the missing ones.
5. Check facts about protocols, standards, APIs and parts against the source (the spec
   section, the docs, the code in the workspace) and cite section numbers.
6. Build or run every command and snippet you write, or mark it unverified in the report.

## Check

Run `python3 ${CLAUDE_PLUGIN_ROOT}/tools/coursekit.py lint <course root>`. Fix every error
and warning in this session's files, or say why one stays.

## Report

Files changed; what must be validated on hardware (commands, expected outputs, numbers);
decisions left to the teacher.
