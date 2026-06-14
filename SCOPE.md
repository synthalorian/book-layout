# Scope of Work — Book Layout

## v1: Core PDF Pipeline

**Goal**: Markdown → PDF with basic professionalism.

- [ ] Markdown parser with YAML frontmatter extraction
- [ ] AST representation of document structure (chapters, sections, paragraphs)
- [ ] Box-model layout engine (blocks, inlines, glue, penalties)
- [ ] PDF renderer via reportlab / weasyprint backend
- [ ] Basic typography: font embedding, line spacing, paragraph indentation
- [ ] Page numbers (bottom-center, roman for frontmatter, arabic for body)
- [ ] Automatic Table of Contents generation with page references
- [ ] Chapter breaks (new recto, optional blank verso)

## v2: Typographic Polish

**Goal**: It should look like a real book, not a printout.

- [ ] Running headers (chapter title verso, section title recto)
- [ ] Drop caps on chapter openings
- [ ] Hyphenation (Hunspell / Knuth-Liang algorithm)
- [ ] Figure captions with numbering
- [ ] Cross-references (\ref{}, \pageref{} style)
- [ ] Orphans and widows control
- [ ] Footnotes (bottom-of-page, nested if needed)

## v3: Print Production & Digital Export

**Goal**: Ready for the press and the e-reader.

- [ ] Imposition engine: re-order pages for booklet/signature printing
- [ ] Signature calculation: given page count and sheet size, compute signature layout
- [ ] Cover generation: spine width from page count + paper thickness
- [ ] Crop marks and bleed
- [ ] ePub export: semantic HTML, CSS, NCX/OPF, embedded fonts
- [ ] PDF/X-1a compliance option

## Architecture

```
manuscript.md
     |
     v
+-----------+    +-------+    +-------------+    +--------+
|  Parser   | -> |  AST  | -> | Layout Eng. | -> | Output |
| (md+yaml) |    |       |    | (box model) |    | PDF/   |
+-----------+    +-------+    +-------------+    | ePub   |
                                                  +--------+
```

- **Parser**: CommonMark + YAML frontmatter → structured AST
- **AST**: Semantic tree (Part → Chapter → Section → Paragraph → Inline)
- **Layout Engine**: TeX-inspired box/glue/penalty model, line breaking via Knuth-Plass
- **PDF Renderer**: reportlab for precision, weasyprint for CSS-based fallback
- **ePub Renderer**: Jinja2 templates + zip packaging

## Milestones

| Day | Deliverable | Acceptance Criteria |
|-----|-------------|-------------------|
| 1   | Basic PDF | A markdown file renders to a multi-page PDF with text |
| 3   | Chapters + TOC | Chapters break correctly, TOC has real page numbers |
| 7   | Typography | Drop caps, running headers, hyphenation active |
| 14  | Print-Ready | Imposition + cover + ePub export working end-to-end |

## Non-Goals

- WYSIWYG editor
- Collaborative editing
- Cloud rendering service
- DOCX/Word export
- Complex math typesetting (v1-v3)
