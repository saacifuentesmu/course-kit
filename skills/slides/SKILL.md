---
name: slides
description: Build or update a talk deck in Marp with the shared course theme, from a lecture script, a lab guide or an outline, with figures and speaker notes, then render it to check. Use when making lectures more graphical, converting a lecture script into slides, drawing or plotting figures for a talk, or fixing deck warnings from the course checker.
---

# Build a talk deck

The kit lives at `${CLAUDE_PLUGIN_ROOT}`. Read STANDARD §3 (Talk) and §5 (Visuals), the
header of `theme/course.css` (classes and palette), the `[palette]` of the course's
`coursekit.toml`, and the session's lab: the talk serves it.

## Plan

A slide list with time windows, at most one slide per minute. Each title states one claim.
Mark which slides need a figure and where the question slides go.

## Figures

1. **Data exists** (captures, logs, measurements): plot it with a script saved beside the
   figure (`img/<name>.py` → `img/<name>.svg`), colored by the course palette.
2. **Diagrams**: hand-written SVG; palette strong colors for strokes and text, tints for
   fills; the theme's font stack; a wide viewBox (about 1100 × 450).
3. **Screenshots** of analyzers and traces: crop to the event, annotate in palette colors.
4. No figure beats a decorative one.

## Write

1. Start from `templates/talk.md`. The front matter sets only `--course`, plus rules for one
   unusual slide when nothing in the theme fits.
2. Classes come from the theme: `lead`, `agenda`, `s1`…`s8` for segment N of the agenda,
   `question`, `takeaway`, `figure`.
3. At most 60 visible words per slide.
4. Notes on every slide, opening with the time window: what to say, what to point at, the
   misconception to anticipate.
5. Converting a lecture script: objectives become the agenda, segments `s1`…`sN`, board
   sketches figures, questions for the room question slides, misconceptions notes. Remove
   the script only when the teacher agrees.

## Render and look

`python3 ${CLAUDE_PLUGIN_ROOT}/tools/coursekit.py render <deck> --format png -o <scratch dir>/s.png`
(needs Node.js and Chrome; set `CHROME_PATH` if Chrome isn't found). Look at every slide
image; fix overflow, clipped figures and text too small to read from the back of a room.

## Check

Run `python3 ${CLAUDE_PLUGIN_ROOT}/tools/coursekit.py lint <course root>` and clear the
deck's warnings, or say why one stays.
