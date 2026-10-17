# course-kit

A shared format for UNAL Manizales engineering courses, and the tools that keep courses
on it. Draft v0.1, proposed for discussion from 4101137 Real-Time Systems and 4201327
IoT Systems Design.

| | |
|---|---|
| [STANDARD.md](STANDARD.md) | The proposal: principles, documents, session format, writing, visuals, assessment, maintenance, open questions |
| [templates/](templates/) | Lab guide, talk deck, SOP, course README, team record, `coursekit.toml` |
| [theme/course.css](theme/course.css) | The shared Marp theme: one look, one palette, a course accent |
| [tools/coursekit.py](tools/coursekit.py) | Checker and deck renderer (Python 3.11+, standard library only) |
| [skills/](skills/) | Agent skills that write, illustrate and review sessions to the standard |

Everything is plain Markdown, CSS and Python, so the standard, templates and checker work
without any AI tool. The skills are a thin layer on top: they point an agent at the same
files a teacher reads.

## Use it in a course

1. Copy [templates/coursekit.toml](templates/coursekit.toml) to the course root and map the
   course's files to document types. Existing layouts work; nothing has to move.
2. Check the course:
   ```bash
   python3 ../course-kit/tools/coursekit.py lint .            # every finding
   python3 ../course-kit/tools/coursekit.py lint . --summary  # one row per document
   ```
3. Copy the theme into the course (re-run when the kit's theme changes; `lint` reports drift):
   ```bash
   python3 ../course-kit/tools/coursekit.py sync .
   ```
4. Build a deck. PDF and PNG need Node.js and Chrome (or `CHROME_PATH`); HTML is written
   beside the deck:
   ```bash
   python3 ../course-kit/tools/coursekit.py render labs/presentations/05_tracing.md
   ```
   To preview in VS Code, install the Marp extension and add the theme to the workspace
   settings: `"markdown.marp.themes": ["theme/course.css"]`.

## Use the skills

The kit is a Claude Code plugin. [Agent Skills](https://agentskills.io) is an open format,
so other agents can read the same `skills/*/SKILL.md` files.

```bash
claude plugin marketplace add <path or GitHub owner/repo of this kit>
claude plugin install course-kit@unal-courses
```

| Skill | Use it to |
|---|---|
| `/course-kit:session` | Write or revise a week: lab guide, talk, SOP |
| `/course-kit:slides` | Turn a lecture script, lab or outline into a deck with figures, and render it |
| `/course-kit:review` | Audit one or more courses: the checker, then correctness, continuity and alignment |

The skills never invent measured values: those stay `____` until someone measures them on
hardware.

## Changing the standard

The standard changes by agreement between the teachers who use it. When it changes,
update `STANDARD.md`, the templates and the checker together, and bump the version in
`.claude-plugin/plugin.json`.
