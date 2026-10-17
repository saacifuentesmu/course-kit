#!/usr/bin/env python3
"""Check course material against the course standard (STANDARD.md).

    coursekit.py lint [COURSE_DIR] [--summary] [--json]
    coursekit.py sync [COURSE_DIR]
    coursekit.py render DECK [--format pdf|png|html] [-o OUT]

Standard library only (Python 3.11+). Exit code 1 when any error is found.
"""
import argparse
import fnmatch
import json
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

KIT = Path(__file__).resolve().parent.parent
KIT_THEME = KIT / "theme" / "course.css"
MARP = "@marp-team/marp-cli@4.0.3"

BUDGETS = {"lab": 1500, "event": 1500, "sop": 1500, "notes": 2500, "script": 1200}
TALK = {"minutes": 40, "slide_words": 60}
IGNORE = [".git/**", "**/build/**", "build/**", "**/node_modules/**", "**/.venv/**", ".cache/**"]

LAB_SECTIONS = [
    ("measure", r"what you.?ll measure|predict"),
    ("tasks", r"^tasks?\b"),
    ("deliverables", r"^deliverables"),
    ("rubric", r"^(rubric|grading)"),
]

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s")
INLINE_ENUM = re.compile(r"(?:^|[\s(:])1[.)]\s+\S.*?[\s(]2[.)]\s+\S|\(1\)\s*\S.*?\(2\)\s*\S")
LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^()\s>]*(?:\([^()\s]*\)[^()\s>]*)*)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)")
HTML_REF = re.compile(r"<(?:img|a|source)\b[^>]*?\b(?:src|href)=[\"']([^\"']+)[\"']", re.I)
HTML_ID = re.compile(r"<[a-z]+\b[^>]*?\b(?:id|name)=[\"']([^\"']+)[\"']", re.I)
INLINE_CODE = re.compile(r"`+[^`]*`+")
DIRECTIVE = re.compile(r"^\s*_?[A-Za-z][\w-]*\s*:")
TIMING = re.compile(r"^\s*\d+:\d\d")
WORD = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")
FILLER = re.compile(r"(\*\*|^#+\s*)(TL;DR|in plain english)\b", re.I)


@dataclass
class Issue:
    path: str
    line: int
    level: str
    rule: str
    msg: str


@dataclass
class Doc:
    path: Path
    rel: str
    kind: str
    lines: list = field(default_factory=list)  # (lineno, text, zone)
    frontmatter: dict = field(default_factory=dict)
    words: int = 0


def load_config(root):
    cfg_path = root / "coursekit.toml"
    if not cfg_path.exists():
        sys.exit(f"{cfg_path} not found: copy templates/coursekit.toml into the course root")
    with open(cfg_path, "rb") as f:
        cfg = tomllib.load(f)
    cfg.setdefault("types", {})
    cfg["budgets"] = {**BUDGETS, **cfg.get("budgets", {})}
    cfg["talk"] = {**TALK, **cfg.get("talk", {})}
    cfg["ignore"] = IGNORE + cfg.get("ignore", {}).get("paths", [])
    return cfg


def matches(rel, patterns):
    return any(fnmatch.fnmatch(rel, p) for p in patterns)


def classify(rel, cfg):
    for kind, patterns in cfg["types"].items():
        if matches(rel, patterns):
            return kind
    return "doc"


def zone_lines(text):
    """Tag each line as front matter, code, comment or text."""
    out, zone, in_comment = [], "text", False
    raw = text.split("\n")
    i = 0
    if raw and raw[0].strip() == "---":
        for j in range(1, len(raw)):
            if raw[j].strip() == "---":
                for k in range(j + 1):
                    out.append((k + 1, raw[k], "front"))
                i = j + 1
                break
    fence = None
    for n in range(i, len(raw)):
        line = raw[n]
        if fence:
            out.append((n + 1, line, "code"))
            if line.strip().startswith(fence):
                fence = None
            continue
        m = FENCE.match(line)
        if m and not in_comment:
            fence = m.group(1)
            out.append((n + 1, line, "code"))
            continue
        if in_comment:
            out.append((n + 1, line, "comment"))
            in_comment = "-->" not in line
            continue
        if line.lstrip().startswith("<!--"):
            out.append((n + 1, line, "comment"))
            in_comment = "-->" not in line.split("<!--", 1)[1]
            continue
        out.append((n + 1, line, "text"))
    return out


def parse_frontmatter(lines):
    fm = {}
    for _, text, zone in lines:
        if zone == "front":
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", text)
            if m:
                fm[m.group(1)] = m.group(2).strip()
    return fm


def strip_markup(text):
    text = re.sub(r"<!--.*?-->", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\]\([^)]*\)", "]", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def count_words(lines):
    return sum(len(WORD.findall(strip_markup(t))) for _, t, z in lines if z == "text")


def slugs(doc):
    seen, out = {}, set()
    for _, text, zone in doc.lines:
        if zone != "text":
            continue
        for m in HTML_ID.finditer(text):
            out.add(m.group(1))
        h = HEADING.match(text)
        if not h:
            continue
        s = strip_markup(h.group(2)).strip().lower()
        s = re.sub(r"[^\w\- ]", "", s).replace(" ", "-")
        n = seen.get(s, 0)
        seen[s] = n + 1
        out.add(s if n == 0 else f"{s}-{n}")
    return out


def headings(doc, level):
    return [(n, HEADING.match(t).group(2)) for n, t, z in doc.lines
            if z == "text" and HEADING.match(t) and len(HEADING.match(t).group(1)) == level]


def check_links(doc, root, docs_by_path, issues):
    for n, text, zone in doc.lines:
        if zone != "text":
            continue
        clean = INLINE_CODE.sub("", text)
        targets = [m.group(1) for m in LINK.finditer(clean)]
        targets += [m.group(1) for m in HTML_REF.finditer(clean)]
        m = REF_DEF.match(clean)
        if m:
            targets.append(m.group(1))
        for t in targets:
            if re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I) or t.startswith("//"):
                continue
            path_part, _, anchor = t.partition("#")
            path_part = unquote(path_part)
            if path_part:
                base = root if path_part.startswith("/") else doc.path.parent
                target = (base / path_part.lstrip("/")).resolve()
                if not target.exists():
                    issues.append(Issue(doc.rel, n, "error", "link", f"broken link: {t}"))
                    continue
            else:
                target = doc.path
            if anchor and target.suffix == ".md":
                tdoc = docs_by_path.get(target)
                if tdoc and anchor.lower() not in {s.lower() for s in slugs(tdoc)}:
                    issues.append(Issue(doc.rel, n, "error", "anchor", f"no heading for #{anchor} in {target.name}"))


def check_style(doc, issues):
    for n, text, zone in doc.lines:
        if zone != "text" or text.lstrip().startswith("|") or LIST_ITEM.match(text) or HEADING.match(text):
            continue
        clean = INLINE_CODE.sub("", text)
        if INLINE_ENUM.search(clean):
            issues.append(Issue(doc.rel, n, "warn", "inline-list", "enumeration inside a paragraph: make it a list"))
        if FILLER.search(clean):
            issues.append(Issue(doc.rel, n, "warn", "filler", "repeats content (TL;DR / plain-English recap)"))


def section_lines(doc, start_line, level=2):
    out, inside = [], False
    for n, text, zone in doc.lines:
        h = HEADING.match(text) if zone == "text" else None
        if n == start_line:
            inside = True
            continue
        if inside and h and len(h.group(1)) <= level:
            break
        if inside:
            out.append((n, text, zone))
    return out


def check_lab(doc, cfg, issues):
    h2 = headings(doc, 2)
    first_h2 = h2[0][0] if h2 else 10**9
    if not any("**From:**" in t or "**From**:" in t for n, t, z in doc.lines if z == "text" and n < first_h2):
        issues.append(Issue(doc.rel, 1, "error", "memo", "no **From:** memo before the first section"))
    found, last = {}, -1
    for role, pattern in LAB_SECTIONS:
        hit = next(((n, t) for n, t in h2 if re.search(pattern, strip_markup(t).strip(), re.I)), None)
        if not hit:
            issues.append(Issue(doc.rel, 1, "error", "section", f"missing section: {role}"))
            continue
        found[role] = hit
        if hit[0] < last:
            issues.append(Issue(doc.rel, hit[0], "warn", "order", f"section '{hit[1]}' is out of order"))
        last = hit[0]
    if "measure" in found:
        body = section_lines(doc, found["measure"][0])
        header = next((t for _, t, z in body if z == "text" and t.lstrip().startswith("|")), "")
        if "predict" not in header.lower():
            issues.append(Issue(doc.rel, found["measure"][0], "warn", "predict", "measure table has no prediction column"))
        if not any("____" in t for _, t, _ in body):
            issues.append(Issue(doc.rel, found["measure"][0], "warn", "blanks", "measure table has no ____ cells"))
    if "tasks" in found:
        body = section_lines(doc, found["tasks"][0])
        tasks = [(n, HEADING.match(t).group(2)) for n, t, z in body
                 if z == "text" and HEADING.match(t) and len(HEADING.match(t).group(1)) == 3]
        for i, (n, name) in enumerate(tasks):
            end = tasks[i + 1][0] if i + 1 < len(tasks) else 10**9
            if not any(re.search(r"\*\*Evidence:?\*\*", t) for m, t, z in body if n < m < end and z == "text"):
                issues.append(Issue(doc.rel, n, "warn", "evidence", f"task '{name}' has no **Evidence:** line"))
    if "rubric" in found:
        body = section_lines(doc, found["rubric"][0])
        pts = []
        for _, t, z in body:
            if z == "text" and t.lstrip().startswith("|") and not re.match(r"^\s*\|[\s:|-]+\|\s*$", t):
                cell = t.strip().strip("|").split("|")[-1].strip()
                if cell.isdigit():
                    pts.append(int(cell))
        if pts and sum(pts) != 100:
            issues.append(Issue(doc.rel, found["rubric"][0], "warn", "rubric", f"rubric adds up to {sum(pts)}, not 100"))


def slides(doc):
    out, cur = [], []
    for item in doc.lines:
        if item[2] == "front":
            continue
        if item[2] == "text" and item[1].strip() == "---":
            out.append(cur)
            cur = []
        else:
            cur.append(item)
    out.append(cur)
    return [s for s in out if any(t.strip() for _, t, _ in s)]


def comments(slide):
    blocks, cur = [], None
    for n, t, z in slide:
        if z != "comment":
            if cur:
                blocks.append(cur)
                cur = None
            continue
        if cur is None:
            cur = (n, [])
        cur[1].append(t)
        if "-->" in t:
            blocks.append(cur)
            cur = None
    if cur:
        blocks.append(cur)
    out = []
    for n, body in blocks:
        text = "\n".join(body).replace("<!--", "").replace("-->", "")
        out.append((n, [l for l in text.split("\n") if l.strip()]))
    return out


def check_talk(doc, cfg, issues):
    if doc.frontmatter.get("marp") != "true":
        issues.append(Issue(doc.rel, 1, "error", "marp", "talk is not a Marp deck (front matter needs marp: true)"))
        return
    deck = slides(doc)
    for n, body in comments(deck[0]) if deck else []:
        if any(l.strip().startswith("style:") for l in body) and len(body) > 10:
            issues.append(Issue(doc.rel, n, "warn", "inline-css", f"{len(body)} lines of inline CSS: use the shared theme"))
    if doc.frontmatter.get("theme") != "course":
        issues.append(Issue(doc.rel, 1, "warn", "theme", "deck does not use the shared theme (theme: course)"))
    limit = cfg["talk"]["minutes"]
    if len(deck) > limit:
        issues.append(Issue(doc.rel, 1, "warn", "slides", f"{len(deck)} slides for a {limit}-minute talk"))
    no_notes, no_time, wordy, classes = [], [], [], set()
    for i, s in enumerate(deck, 1):
        notes = []
        for _, body in comments(s):
            if DIRECTIVE.match(body[0]):
                for l in body:
                    m = re.match(r"^\s*_?class:\s*(.+)$", l)
                    if m:
                        classes.update(m.group(1).split())
            else:
                notes.append(body)
        if not notes:
            no_notes.append(i)
        elif not TIMING.match(notes[0][0]):
            no_time.append(i)
        visible = sum(len(WORD.findall(strip_markup(t))) for _, t, z in s if z == "text" and not HEADING.match(t))
        if visible > cfg["talk"]["slide_words"]:
            wordy.append(i)
    if no_notes:
        issues.append(Issue(doc.rel, 1, "warn", "notes", f"slides without speaker notes: {fmt(no_notes)}"))
    if no_time:
        issues.append(Issue(doc.rel, 1, "warn", "timing", f"notes without a time window: slides {fmt(no_time)}"))
    if wordy:
        issues.append(Issue(doc.rel, 1, "warn", "wordy", f"over {cfg['talk']['slide_words']} visible words: slides {fmt(wordy)}"))
    if "question" not in classes:
        issues.append(Issue(doc.rel, 1, "warn", "question", "no question slide (_class: question)"))


def check_sop(doc, cfg, issues):
    if not any(re.search(r"troubleshoot", t, re.I) for _, t in headings(doc, 2)):
        issues.append(Issue(doc.rel, 1, "warn", "troubleshooting", "no Troubleshooting section"))


def fmt(nums):
    return ", ".join(map(str, nums[:12])) + (" …" if len(nums) > 12 else "")


def collect(root, cfg):
    docs = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if matches(rel, cfg["ignore"]):
            continue
        d = Doc(path=p.resolve(), rel=rel, kind=classify(rel, cfg))
        d.lines = zone_lines(p.read_text(encoding="utf-8", errors="replace"))
        d.frontmatter = parse_frontmatter(d.lines)
        d.words = count_words(d.lines)
        docs.append(d)
    return docs


def lint(root):
    cfg = load_config(root)
    docs = collect(root, cfg)
    by_path = {d.path: d for d in docs}
    issues = []
    for d in docs:
        check_links(d, root, by_path, issues)
        if d.kind != "talk":
            check_style(d, issues)
        budget = cfg["budgets"].get(d.kind)
        if budget and d.words > budget:
            issues.append(Issue(d.rel, 1, "warn", "budget", f"{d.words} words, budget {budget}"))
        {"lab": check_lab, "talk": check_talk, "sop": check_sop}.get(d.kind, lambda *a: None)(d, cfg, issues)
    theme = root / cfg.get("theme", {}).get("path", "theme/course.css")
    if any(d.kind == "talk" for d in docs):
        if not theme.exists():
            issues.append(Issue(theme.relative_to(root).as_posix(), 0, "warn", "theme", "shared theme missing: run coursekit.py sync"))
        elif theme.read_bytes() != KIT_THEME.read_bytes():
            issues.append(Issue(theme.relative_to(root).as_posix(), 0, "warn", "theme", "differs from the kit's theme: run coursekit.py sync"))
    validated = {int(k) for k in cfg.get("validated", {}) if k.isdigit()}
    missing = sorted({int(m.group()) for d in docs if d.kind in ("lab", "event")
                      for m in [re.search(r"\d+", Path(d.rel).name)] if m} - validated)
    if missing:
        issues.append(Issue("coursekit.toml", 0, "info", "validated", f"sessions never validated on hardware: {fmt(missing)}"))
    return cfg, docs, issues


def report(cfg, docs, issues, summary):
    course = cfg.get("course", {})
    print(f"{course.get('code', '')} {course.get('name', '')}".strip())
    per = {}
    for i in issues:
        per.setdefault(i.path, {"error": 0, "warn": 0, "info": 0})[i.level] += 1
    typed = [d for d in docs if d.kind != "doc"]
    print(f"\n{'type':7} {'words':>11}  {'E':>2} {'W':>2}  file")
    for d in typed:
        b = cfg["budgets"].get(d.kind)
        words = f"{d.words}/{b}" if b else str(d.words)
        c = per.get(d.rel, {"error": 0, "warn": 0})
        print(f"{d.kind:7} {words:>11}  {c['error'] or '':>2} {c['warn'] or '':>2}  {d.rel}")
    other = [d for d in docs if d.kind == "doc"]
    oc = [per.get(d.rel, {"error": 0, "warn": 0}) for d in other]
    print(f"{'doc':7} {len(other):>8} md  {sum(c['error'] for c in oc) or '':>2} {sum(c['warn'] for c in oc) or '':>2}  (other Markdown files)")
    if not summary:
        print()
        for i in sorted(issues, key=lambda i: ({"error": 0, "warn": 1, "info": 2}[i.level], i.path, i.line)):
            loc = f"{i.path}:{i.line}" if i.line else i.path
            print(f"{i.level:5} {i.rule:15} {loc}: {i.msg}")
    clean = sum(1 for d in typed if d.rel not in per or not (per[d.rel]["error"] or per[d.rel]["warn"]))
    e = sum(1 for i in issues if i.level == "error")
    w = sum(1 for i in issues if i.level == "warn")
    print(f"\n{clean}/{len(typed)} session documents clean · {e} errors · {w} warnings")


def render(deck, fmt_, out):
    root = next((d for d in deck.parents if (d / "coursekit.toml").exists()), None)
    if root is None:
        sys.exit(f"no coursekit.toml above {deck}")
    cfg = load_config(root)
    theme = root / cfg.get("theme", {}).get("path", "theme/course.css")
    if out:
        out = Path(out)
    elif fmt_ == "html":
        out = deck.with_suffix(".html")  # beside the deck, so relative image paths still resolve
    else:
        out = root / "build" / "slides" / deck.with_suffix("." + fmt_).name
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npx", "-y", MARP, str(deck), "--theme-set", str(theme), "--allow-local-files", "-o", str(out)]
    cmd += {"html": [], "pdf": ["--pdf"], "png": ["--images", "png"]}[fmt_]
    sys.exit(subprocess.run(cmd, stdin=subprocess.DEVNULL).returncode)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("lint", help="check a course against the standard")
    p.add_argument("course", nargs="?", default=".")
    p.add_argument("--summary", action="store_true", help="table and totals only")
    p.add_argument("--json", action="store_true")
    s = sub.add_parser("sync", help="copy the kit's shared theme into the course")
    s.add_argument("course", nargs="?", default=".")
    r = sub.add_parser("render", help="build a talk deck with the shared theme (Node.js; Chrome for pdf/png)")
    r.add_argument("deck")
    r.add_argument("--format", choices=["pdf", "png", "html"], default="pdf")
    r.add_argument("-o", "--out")
    a = ap.parse_args()
    if a.cmd == "render":
        render(Path(a.deck).resolve(), a.format, a.out)
        return
    root = Path(a.course).resolve()
    if a.cmd == "sync":
        cfg = load_config(root)
        dest = root / cfg.get("theme", {}).get("path", "theme/course.css")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(KIT_THEME, dest)
        print(f"theme → {dest.relative_to(root)}")
        return
    cfg, docs, issues = lint(root)
    if a.json:
        print(json.dumps({"docs": [{"file": d.rel, "type": d.kind, "words": d.words} for d in docs],
                          "issues": [i.__dict__ for i in issues]}, indent=1))
    else:
        report(cfg, docs, issues, a.summary)
    sys.exit(1 if any(i.level == "error" for i in issues) else 0)


if __name__ == "__main__":
    main()
