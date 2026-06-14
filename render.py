from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, Color
from typing import List, Dict, Any, Tuple, Optional
from layout import PageGeometry, LayoutEngine, Paragraph, Line, LineItem
from typography import Typography
from parser import Document, BlockNode, InlineNode
import os


class PDFRenderer:
    """Render a Document AST to PDF using reportlab."""

    def __init__(self, geometry: PageGeometry, typography: Typography, output_path: str):
        self.geometry = geometry
        self.typography = typography
        self.output_path = output_path
        self.canvas = canvas.Canvas(output_path, pagesize=(geometry.width, geometry.height))
        self.current_page = 0
        self.toc_entries: List[Tuple[str, int, int]] = []  # (title, level, page)
        self._page_numbers_for_toc: bool = False
        self._toc_page_count: int = 0
        self._drop_cap_active: bool = False
        self._drop_cap_width: float = 0.0
        self._drop_cap_lines: int = 0

    def start_page(self):
        self.current_page += 1
        self.current_y = self.geometry.height - self.geometry.margin_top

    def end_page(self):
        self.canvas.showPage()

    def new_page(self):
        if self.current_page > 0:
            self.end_page()
        self.start_page()

    def draw_footer(self):
        """Draw page number in footer (bottom center)."""
        page_num = str(self.current_page)
        font_size = 10
        font_name = self.typography.get_body_font()
        text_width = self.typography.measure_text(page_num, font_name, font_size)
        x = (self.geometry.width - text_width) / 2.0
        y = self.geometry.margin_bottom - 24
        self.canvas.setFont(font_name, font_size)
        self.canvas.setFillColor(black)
        self.canvas.drawString(x, y, page_num)

    def draw_text_line(self, line: Line, x: float, y: float, drop_cap_mode: bool = False, drop_cap_remaining: int = 0):
        """Draw a single line of text at (x, y)."""
        current_x = x
        self.canvas.setFillColor(black)

        for item in line.items:
            self.canvas.setFont(item.font_name, item.font_size)

            if drop_cap_mode and current_x == x and drop_cap_remaining > 0 and item == line.items[0]:
                # Skip the first character of first line - it's handled by drop cap
                if len(item.text) > 1:
                    self.canvas.drawString(current_x + self._drop_cap_width, y, item.text[1:])
            else:
                self.canvas.drawString(current_x, y, item.text)

            current_x += item.width

    def draw_blockquote_border(self, x: float, y: float, height: float):
        """Draw left border for blockquote."""
        border_x = x - 6
        self.canvas.setStrokeColor(Color(0.6, 0.6, 0.6))
        self.canvas.setLineWidth(2)
        self.canvas.line(border_x, y, border_x, y + height)

    def draw_code_background(self, x: float, y: float, width: float, height: float):
        """Draw light gray background for code blocks."""
        self.canvas.setFillColor(Color(0.95, 0.95, 0.95))
        self.canvas.rect(x - 4, y - 2, width + 8, height + 4, fill=1, stroke=0)

    def draw_horizontal_rule(self, x: float, y: float, width: float):
        """Draw a horizontal rule."""
        self.canvas.setStrokeColor(Color(0.5, 0.5, 0.5))
        self.canvas.setLineWidth(1)
        self.canvas.line(x, y, x + width, y)

    def draw_drop_cap(self, char: str, x: float, y: float, font_name: str, font_size: float):
        """Draw a drop cap character."""
        self.canvas.setFont(font_name, font_size)
        self.canvas.setFillColor(black)
        # Draw slightly above baseline for aesthetic
        self.canvas.drawString(x, y + font_size * 0.1, char)

    def render_paragraph(self, paragraph: Paragraph, x: float, y: float,
                          is_blockquote: bool = False, is_code: bool = False,
                          is_first_para_of_chapter: bool = False) -> float:
        """Render a paragraph and return the final y position."""
        if not paragraph.lines:
            return y

        line_height = self.typography.get_line_height(
            paragraph.lines[0].items[0].font_size if paragraph.lines[0].items else 11
        )
        total_height = len(paragraph.lines) * line_height

        if is_blockquote:
            self.draw_blockquote_border(x, y - total_height + line_height, total_height)

        if is_code:
            max_width = max(
                sum(item.width for item in line.items) for line in paragraph.lines
            ) if paragraph.lines else 0
            self.draw_code_background(x, y - total_height, max_width, total_height + line_height)

        drop_cap_info = None
        if is_first_para_of_chapter and paragraph.lines and paragraph.lines[0].items:
            first_item = paragraph.lines[0].items[0]
            if first_item.text:
                char, drop_size, drop_width, remaining = self.typography.make_drop_cap(
                    first_item.text, first_item.font_name, first_item.font_size
                )
                if char and drop_size > first_item.font_size * 1.5:
                    drop_cap_info = (char, drop_size, drop_width, remaining)
                    self._drop_cap_width = drop_width
                    self._drop_cap_lines = 2  # Drop cap spans 2 lines

        for i, line in enumerate(paragraph.lines):
            line_y = y - (i * line_height)

            if drop_cap_info and i == 0:
                char, drop_size, drop_width, remaining = drop_cap_info
                self.draw_drop_cap(char, x, line_y - drop_size * 0.8, line.items[0].font_name, drop_size)
                # Adjust first line to skip the drop cap character
                if remaining or len(line.items) > 1:
                    # Draw remaining text of first item and rest of line
                    current_x = x + drop_width + 4
                    for j, item in enumerate(line.items):
                        if j == 0 and remaining:
                            self.canvas.setFont(item.font_name, item.font_size)
                            self.canvas.drawString(current_x, line_y, remaining)
                            current_x += self.typography.measure_text(remaining, item.font_name, item.font_size)
                        else:
                            self.canvas.setFont(item.font_name, item.font_size)
                            self.canvas.drawString(current_x, line_y, item.text)
                            current_x += item.width
                continue
            elif drop_cap_info and i < self._drop_cap_lines:
                # Indent these lines for drop cap
                self.draw_text_line(line, x + self._drop_cap_width + 4, line_y)
                continue
            else:
                self.draw_text_line(line, x + paragraph.indent, line_y)

        return y - total_height - paragraph.space_after

    def render_chapter(self, chapter: BlockNode, first_chapter: bool = False, collect_toc: bool = True):
        """Render a chapter (which is a BlockNode with type='chapter')."""
        chapter_title = chapter.content
        if chapter_title and collect_toc:
            self.toc_entries.append((chapter_title, 1, self.current_page + 1))

        # Chapter heading on new page
        if not first_chapter or self.current_page > 0:
            self.new_page()
        else:
            self.start_page()

        # Draw chapter title
        if chapter_title:
            title_font = self.typography.get_heading_font(1)
            title_size = self.typography.get_heading_font_size(1)
            self.canvas.setFont(title_font, title_size)
            self.canvas.setFillColor(black)
            title_y = self.current_y - self.typography.get_heading_space_before(1)
            self.canvas.drawString(self.geometry.margin_left, title_y, chapter_title)
            self.current_y = title_y - title_size - self.typography.get_heading_space_after(1)

        # Render chapter body blocks
        first_para = True
        for block in chapter.children:
            layout_engine = LayoutEngine(self.geometry, self.typography)
            paragraph = layout_engine.layout_block(block, self.geometry.text_width)

            # Check if we need a new page
            needed_height = paragraph.height + paragraph.space_before + paragraph.space_after
            if self.current_y - needed_height < self.geometry.margin_bottom:
                self.new_page()

            self.current_y -= paragraph.space_before

            if block.type == 'horizontal_rule':
                self.draw_horizontal_rule(
                    self.geometry.margin_left,
                    self.current_y,
                    self.geometry.text_width
                )
                self.current_y -= 12
                continue

            if block.type == 'list':
                # Layout each list item as a paragraph
                for item in block.children:
                    item_para = layout_engine.layout_block(item, self.geometry.text_width)
                    if self.current_y - item_para.height < self.geometry.margin_bottom:
                        self.new_page()
                    self.current_y = self.render_paragraph(item_para, self.geometry.margin_left, self.current_y)
                continue

            is_blockquote = (block.type == 'blockquote')
            is_code = (block.type == 'code_block')
            is_first = first_para and not (chapter_title and not chapter.children)

            self.current_y = self.render_paragraph(
                paragraph,
                self.geometry.margin_left,
                self.current_y,
                is_blockquote=is_blockquote,
                is_code=is_code,
                is_first_para_of_chapter=is_first
            )
            first_para = False

        self.draw_footer()

    def render_toc(self, title: str = "Table of Contents"):
        """Render table of contents. Returns number of pages used."""
        toc_start_page = self.current_page + 1
        self.new_page()

        # Title
        title_font = self.typography.get_heading_font(1)
        title_size = self.typography.get_heading_font_size(1)
        self.canvas.setFont(title_font, title_size)
        self.canvas.setFillColor(black)
        title_y = self.current_y - self.typography.get_heading_space_before(1)
        self.canvas.drawString(self.geometry.margin_left, title_y, title)
        self.current_y = title_y - title_size - self.typography.get_heading_space_after(1)

        font_name = self.typography.get_body_font()
        font_size = self.typography.get_body_font_size()
        line_height = self.typography.get_line_height(font_size)

        for entry_title, level, page_num in self.toc_entries:
            # Check if we need a new page
            if self.current_y - line_height < self.geometry.margin_bottom:
                self.new_page()

            indent = (level - 1) * 12
            self.canvas.setFont(font_name, font_size)
            self.canvas.setFillColor(black)

            # Draw title
            self.canvas.drawString(self.geometry.margin_left + indent, self.current_y, entry_title)

            # Draw page number
            page_str = str(page_num)
            page_width = self.typography.measure_text(page_str, font_name, font_size)
            self.canvas.drawString(
                self.geometry.margin_left + self.geometry.text_width - page_width,
                self.current_y,
                page_str
            )

            # Draw leader dots
            title_width = self.typography.measure_text(entry_title, font_name, font_size)
            dots_start = self.geometry.margin_left + indent + title_width + 4
            dots_end = self.geometry.margin_left + self.geometry.text_width - page_width - 4
            if dots_end > dots_start:
                self.canvas.setStrokeColor(Color(0.5, 0.5, 0.5))
                self.canvas.setLineWidth(0.5)
                self.canvas.setDash(1, 3)
                self.canvas.line(dots_start, self.current_y + font_size * 0.25, dots_end, self.current_y + font_size * 0.25)
                self.canvas.setDash()

            self.current_y -= line_height

        self.draw_footer()
        toc_end_page = self.current_page
        return toc_end_page - toc_start_page + 1

    def render_document(self, document: Document):
        """Render the full document to PDF."""
        # First pass: render chapters to collect page numbers for TOC
        first_chapter = True
        for chapter in document.chapters:
            self.render_chapter(chapter, first_chapter=first_chapter)
            first_chapter = False
        self.end_page()
        self.canvas.save()

        # Save temp copy and reset for second pass with TOC
        temp_path = self.output_path + '.tmp'
        os.rename(self.output_path, temp_path)

        # Estimate TOC pages needed
        toc_lines = len(self.toc_entries) + 3
        toc_pages = max(1, (toc_lines * 14) // int(self.geometry.text_height // 14))
        self._toc_page_count = toc_pages

        # Adjust collected page numbers by TOC offset
        adjusted_toc = []
        for title, level, page in self.toc_entries:
            adjusted_toc.append((title, level, page + toc_pages))
        self.toc_entries = adjusted_toc

        # Reset canvas for second pass
        self.canvas = canvas.Canvas(self.output_path, pagesize=(self.geometry.width, self.geometry.height))
        self.current_page = 0

        # Render TOC first
        self.render_toc()

        # Render chapters again with correct page numbers
        first_chapter = True
        for chapter in document.chapters:
            self.render_chapter(chapter, first_chapter=first_chapter, collect_toc=False)
            first_chapter = False
        self.end_page()
        self.canvas.save()

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return self.output_path
