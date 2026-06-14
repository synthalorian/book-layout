from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class PageGeometry:
    width: float = 612.0  # Letter width in points (8.5in)
    height: float = 792.0  # Letter height in points (11in)
    margin_top: float = 72.0  # 1 inch
    margin_bottom: float = 72.0
    margin_left: float = 72.0
    margin_right: float = 72.0

    @property
    def text_width(self) -> float:
        return self.width - self.margin_left - self.margin_right

    @property
    def text_height(self) -> float:
        return self.height - self.margin_top - self.margin_bottom

    @property
    def text_area(self) -> Tuple[float, float, float, float]:
        """Return (x, y, width, height) of text area."""
        return (
            self.margin_left,
            self.margin_bottom,
            self.text_width,
            self.text_height
        )


@dataclass
class LineItem:
    text: str
    width: float
    font_name: str
    font_size: float
    is_bold: bool = False
    is_italic: bool = False
    is_code: bool = False


@dataclass
class Line:
    items: List[LineItem] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0
    spacing: float = 0.0


@dataclass
class Paragraph:
    lines: List[Line] = field(default_factory=list)
    height: float = 0.0
    indent: float = 0.0
    space_before: float = 0.0
    space_after: float = 0.0


@dataclass
class TextBlock:
    paragraphs: List[Paragraph] = field(default_factory=list)
    total_height: float = 0.0


class LayoutEngine:
    def __init__(self, geometry: PageGeometry, typography):
        self.geometry = geometry
        self.typography = typography
        self.current_y = geometry.height - geometry.margin_top
        self.current_page = 0

    def reset_page(self):
        self.current_y = self.geometry.height - self.geometry.margin_top
        self.current_page += 1

    def fits_on_page(self, height: float) -> bool:
        return self.current_y - height >= self.geometry.margin_bottom

    def advance(self, height: float):
        self.current_y -= height

    def break_paragraph_into_lines(self, inline_nodes, font_name: str, font_size: float,
                                    available_width: float, indent: float = 0.0) -> List[Line]:
        """Break inline nodes into lines that fit within available_width."""
        lines = []
        current_line = Line(items=[], width=0.0, height=font_size * 1.2)
        first_line = True

        def flush_line():
            nonlocal current_line, lines, first_line
            if current_line.items:
                lines.append(current_line)
                current_line = Line(items=[], width=0.0, height=font_size * 1.2)
                first_line = False

        for node in inline_nodes:
            if node.type == 'text':
                words = node.content.split(' ')
                for i, word in enumerate(words):
                    if i < len(words) - 1:
                        word = word + ' '
                    
                    text_width = self.typography.measure_text(word, font_name, font_size)
                    effective_width = available_width - (indent if first_line else 0)
                    
                    if current_line.width + text_width > effective_width and current_line.items:
                        flush_line()
                    
                    current_line.items.append(LineItem(
                        text=word,
                        width=text_width,
                        font_name=font_name,
                        font_size=font_size
                    ))
                    current_line.width += text_width
                    
            elif node.type in ('bold', 'italic', 'bold_italic', 'code'):
                words = node.content.split(' ')
                for i, word in enumerate(words):
                    if i < len(words) - 1:
                        word = word + ' '
                    
                    # Determine effective font
                    effective_font = font_name
                    if node.type == 'bold':
                        effective_font = self.typography.get_bold_font(font_name)
                    elif node.type == 'italic':
                        effective_font = self.typography.get_italic_font(font_name)
                    elif node.type == 'bold_italic':
                        effective_font = self.typography.get_bold_italic_font(font_name)
                    elif node.type == 'code':
                        effective_font = self.typography.get_code_font()
                        font_size = font_size * 0.9
                    
                    text_width = self.typography.measure_text(word, effective_font, font_size)
                    effective_width = available_width - (indent if first_line else 0)
                    
                    if current_line.width + text_width > effective_width and current_line.items:
                        flush_line()
                    
                    current_line.items.append(LineItem(
                        text=word,
                        width=text_width,
                        font_name=effective_font,
                        font_size=font_size,
                        is_bold=(node.type in ('bold', 'bold_italic')),
                        is_italic=(node.type in ('italic', 'bold_italic')),
                        is_code=(node.type == 'code')
                    ))
                    current_line.width += text_width
        
        flush_line()
        return lines

    def layout_block(self, block, available_width: float) -> Paragraph:
        """Layout a single block into a Paragraph."""
        if block.type == 'paragraph':
            font_name = self.typography.get_body_font()
            font_size = self.typography.get_body_font_size()
            lines = self.break_paragraph_into_lines(
                block.inline, font_name, font_size, available_width,
                indent=self.typography.get_paragraph_indent()
            )
            return Paragraph(
                lines=lines,
                height=len(lines) * self.typography.get_line_height(font_size),
                indent=self.typography.get_paragraph_indent(),
                space_before=self.typography.get_paragraph_space_before(),
                space_after=self.typography.get_paragraph_space_after()
            )
        
        elif block.type == 'heading':
            font_name = self.typography.get_heading_font(block.level)
            font_size = self.typography.get_heading_font_size(block.level)
            lines = self.break_paragraph_into_lines(
                block.inline, font_name, font_size, available_width
            )
            return Paragraph(
                lines=lines,
                height=len(lines) * self.typography.get_line_height(font_size),
                space_before=self.typography.get_heading_space_before(block.level),
                space_after=self.typography.get_heading_space_after(block.level)
            )
        
        elif block.type == 'blockquote':
            font_name = self.typography.get_body_font()
            font_size = self.typography.get_body_font_size()
            quote_width = available_width - self.typography.get_blockquote_indent()
            lines = self.break_paragraph_into_lines(
                block.inline, font_name, font_size, quote_width,
                indent=self.typography.get_blockquote_indent()
            )
            return Paragraph(
                lines=lines,
                height=len(lines) * self.typography.get_line_height(font_size),
                indent=self.typography.get_blockquote_indent(),
                space_before=self.typography.get_paragraph_space_before(),
                space_after=self.typography.get_paragraph_space_after()
            )
        
        elif block.type == 'code_block':
            font_name = self.typography.get_code_font()
            font_size = self.typography.get_code_font_size()
            lines = []
            for line_text in block.content.split('\n'):
                text_width = self.typography.measure_text(line_text, font_name, font_size)
                lines.append(Line(
                    items=[LineItem(
                        text=line_text,
                        width=text_width,
                        font_name=font_name,
                        font_size=font_size,
                        is_code=True
                    )],
                    width=text_width,
                    height=font_size * 1.2
                ))
            return Paragraph(
                lines=lines,
                height=len(lines) * self.typography.get_line_height(font_size),
                indent=self.typography.get_code_indent(),
                space_before=self.typography.get_paragraph_space_before(),
                space_after=self.typography.get_paragraph_space_after()
            )
        
        elif block.type == 'list':
            paragraphs = []
            for item in block.children:
                if item.type == 'list_item':
                    font_name = self.typography.get_body_font()
                    font_size = self.typography.get_body_font_size()
                    # Prepend bullet
                    bullet_text = '• '
                    bullet_width = self.typography.measure_text(bullet_text, font_name, font_size)
                    item_width = available_width - self.typography.get_list_indent()
                    
                    lines = self.break_paragraph_into_lines(
                        item.inline, font_name, font_size, item_width - bullet_width,
                        indent=self.typography.get_list_indent()
                    )
                    if lines:
                        lines[0].items.insert(0, LineItem(
                            text=bullet_text,
                            width=bullet_width,
                            font_name=font_name,
                            font_size=font_size
                        ))
                        lines[0].width += bullet_width
                    
                    paragraphs.append(Paragraph(
                        lines=lines,
                        height=len(lines) * self.typography.get_line_height(font_size),
                        indent=self.typography.get_list_indent(),
                        space_before=2,
                        space_after=2
                    ))
            
            total_height = sum(p.height + p.space_before + p.space_after for p in paragraphs)
            return Paragraph(
                lines=[],
                height=total_height,
                indent=0,
                space_before=self.typography.get_paragraph_space_before(),
                space_after=self.typography.get_paragraph_space_after()
            )
        
        return Paragraph(lines=[], height=0, indent=0, space_before=0, space_after=0)

    def layout_document(self, document) -> List[TextBlock]:
        """Layout entire document into a list of page-sized text blocks."""
        blocks = []
        for chapter in document.chapters:
            for block in chapter.children:
                para = self.layout_block(block, self.geometry.text_width)
                blocks.append(TextBlock(
                    paragraphs=[para],
                    total_height=para.height + para.space_before + para.space_after
                ))
        return blocks
