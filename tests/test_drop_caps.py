from collections import defaultdict
from unittest.mock import MagicMock

import pytest

from layout import LayoutEngine, PageGeometry
from parser import BlockNode, InlineNode
from render import PDFRenderer
from typography import Typography


@pytest.mark.parametrize('style', ['text', 'bold', 'italic', 'bold_italic', 'code'])
@pytest.mark.parametrize('opening', ['Wide ', 'A '])
def test_drop_cap_lines_stay_inside_right_margin(tmp_path, style, opening):
    geometry = PageGeometry(width=240, margin_left=30, margin_right=30)
    typography = Typography()
    block = BlockNode(type='paragraph', inline=[
        InlineNode(style, opening + 'little words ' * 12),
        InlineNode('text', 'more ordinary words ' * 12),
    ])
    original = [node.content for node in block.inline]
    renderer = PDFRenderer(geometry, typography, str(tmp_path / 'book.pdf'))
    renderer.canvas = MagicMock()
    drawn = []
    font = [None, None]

    def set_font(name, size):
        font[:] = [name, size]

    def draw_string(x, y, text):
        drawn.append((x, y, text, *font))

    renderer.canvas.setFont.side_effect = set_font
    renderer.canvas.drawString.side_effect = draw_string
    renderer.render_chapter(BlockNode(type='chapter', children=[block]), first_chapter=True)

    body = defaultdict(list)
    caps = []
    for x, y, text, name, size in drawn:
        if size > typography.get_body_font_size() * 1.5:
            caps.append(text)
        elif y >= geometry.margin_bottom:
            body[y].append((x, text, name, size))
    lines = [body[y] for y in sorted(body, reverse=True)]
    assert len(lines) > 2
    assert len(caps) == 1
    for line in lines:
        for x, text, name, size in line:
            assert x + typography.measure_text(text, name, size) <= (
                geometry.width - geometry.margin_right + 1e-8
            )
    assert lines[0][0][0] > geometry.margin_left
    assert lines[1][0][0] == pytest.approx(lines[0][0][0])
    assert lines[2][0][0] == geometry.margin_left
    assert caps[0] + ''.join(text for line in lines for _, text, _, _ in line) == ''.join(original)
    assert [node.content for node in block.inline] == original


def test_layout_reserves_two_lines_and_updates_height():
    geometry = PageGeometry(width=240, margin_left=30, margin_right=30)
    typography = Typography()
    engine = LayoutEngine(geometry, typography)
    block = BlockNode(type='paragraph', inline=[InlineNode('text', 'Wide little words ' * 30)])
    normal = engine.layout_block(block, geometry.text_width)
    paragraph = engine.layout_block(block, geometry.text_width, is_first_para_of_chapter=True)
    cap = paragraph.drop_cap
    assert cap is not None
    reduced_width = geometry.text_width - cap.width - cap.gap
    assert all(line.width <= reduced_width for line in paragraph.lines[:2])
    assert any(line.width > reduced_width for line in paragraph.lines[2:])
    assert all(line.width <= geometry.text_width for line in paragraph.lines[2:])
    assert paragraph.height == len(paragraph.lines) * typography.get_line_height(11)
    assert paragraph.height > normal.height
    assert normal.drop_cap is None
    assert ''.join(item.text for line in normal.lines for item in line.items) == block.inline[0].content
