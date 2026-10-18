![book-layout](.github/preview.png)

<p align="center">
  <img src=".github/assets/synthalorian-idle-128.gif" width="128" height="128" alt="The synthalorian: a pixel-art figure in a black helmet with a pink T-visor, idling">
</p>
<p align="center"><em>Markdown in, typeset PDF and ePub out. Typography with a synthesizer.</em></p>

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

---

## ☕ Support the Developer

If this project saved you time, solved a problem, or just made your day a little more neon, you can fuel the next one:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://buymeacoffee.com/synthalorian)

---

<p align="center">
  <img src=".github/assets/synthalorian-idle-128.gif" width="32" height="32" alt="The synthalorian sprite"><br>
  <sub>Built by <a href="https://github.com/synthalorian">the synthalorian</a></sub>
  <br><sub>AI-assisted art: the banner image at the top of this README was made with AI image tools. The synthalorian sprite is code-drawn pixel art.</sub>
</p>
