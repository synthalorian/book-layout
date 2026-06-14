# Book Layout

> *"Typography is the voice of the written word. We just gave it a synthesizer."*

A procedural book layout engine that transforms plain Markdown into professionally typeset PDF and ePub documents. No WYSIWYG drag-and-drop. No InDesign license. Just content, structure, and an engine that understands the grid.

## Philosophy

This engine is **opinionated about typography**.

- **Grid-based layout**: Every element snaps to a baseline grid. No ragged spacing.
- **Signature-aware**: Real print production means understanding imposition, signatures, and booklet folding.
- **Content-first**: You write Markdown. The engine handles the rest.
- **Retro rigor**: Inspired by hot metal typesetting and the discipline of the composing room.

## Input Format

```markdown
---
title: "Neon Grids & Binary Dreams"
author: "Unknown Hacker"
publisher: "Night City Press"
pagesize: "6x9in"
font: "EB Garamond"
---

# Chapter One: The Mainframe

It was a dark and stormy night in the server room...
```

Frontmatter is YAML. The body is standard Markdown with extensions for figures, cross-references, and callouts.

## Output Formats

| Format | Status | Notes |
|--------|--------|-------|
| PDF    | v1     | Print-ready, CMYK-aware, bleed marks |
| ePub   | v3     | Reflowable, semantic HTML, embedded fonts |
| HTML   | v2     | Web preview, paginated CSS |

## Sample Output

```bash
$ book-layout render manuscript.md --format pdf --output book.pdf
[■■■■■■■■■■] 100%  142 pages rendered
$ book-layout render manuscript.md --format epub --output book.epub
[■■■■■■■■■■] 100%  3.2 MB
```

## Install

```bash
pip install book-layout
# or
pip install -e .
```

Requires Python 3.11+ and optional system dependencies for font rendering.

## Quick Start

```bash
book-layout init my-book
cd my-book
# edit manuscript.md
book-layout render manuscript.md
```

---

*Set in the grid. Locked to the baseline. Printed in the dark.*
