import re
from typing import List, Tuple, Optional
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch


class Typography:
    """Font handling, line spacing, hyphenation, and drop caps."""

    def __init__(self, body_font_name='Helvetica', heading_font_name='Helvetica-Bold',
                 code_font_name='Courier', body_font_size=11, heading_font_size=18):
        self.body_font_name = body_font_name
        self.heading_font_name = heading_font_name
        self.code_font_name = code_font_name
        self.body_font_size = body_font_size
        self.heading_font_size = heading_font_size
        self.code_font_size = body_font_size * 0.85
        self._line_spacing_factor = 1.4
        self._paragraph_indent = 0.0
        self._paragraph_space_before = 0.0
        self._paragraph_space_after = 6.0
        self._heading_space_before = 24.0
        self._heading_space_after = 12.0
        self._blockquote_indent = 24.0
        self._code_indent = 12.0
        self._list_indent = 24.0
        self._cache = {}

    def measure_text(self, text: str, font_name: str, font_size: float) -> float:
        """Measure text width in points using reportlab font metrics."""
        key = (text, font_name, font_size)
        if key in self._cache:
            return self._cache[key]

        try:
            font = pdfmetrics.getFont(font_name)
            width = sum(font.charWidths.get(ord(c), font.defaultWidth) for c in text)
            result = width * font_size / 1000.0
        except Exception:
            # Fallback: approximate width
            result = len(text) * font_size * 0.5

        self._cache[key] = result
        return result

    def get_body_font(self) -> str:
        return self.body_font_name

    def get_body_font_size(self) -> float:
        return self.body_font_size

    def get_heading_font(self, level: int = 1) -> str:
        return self.heading_font_name

    def get_heading_font_size(self, level: int = 1) -> float:
        sizes = {1: 24, 2: 18, 3: 14, 4: 12, 5: 10, 6: 9}
        return sizes.get(level, self.heading_font_size)

    def get_code_font(self) -> str:
        return self.code_font_name

    def get_code_font_size(self) -> float:
        return self.code_font_size

    def get_bold_font(self, base_font: str) -> str:
        if base_font == 'Helvetica':
            return 'Helvetica-Bold'
        if base_font == 'Times-Roman':
            return 'Times-Bold'
        return base_font + '-Bold'

    def get_italic_font(self, base_font: str) -> str:
        if base_font == 'Helvetica':
            return 'Helvetica-Oblique'
        if base_font == 'Times-Roman':
            return 'Times-Italic'
        return base_font + '-Italic'

    def get_bold_italic_font(self, base_font: str) -> str:
        if base_font == 'Helvetica':
            return 'Helvetica-BoldOblique'
        if base_font == 'Times-Roman':
            return 'Times-BoldItalic'
        return base_font + '-BoldItalic'

    def get_line_height(self, font_size: float) -> float:
        return font_size * self._line_spacing_factor

    def get_paragraph_indent(self) -> float:
        return self._paragraph_indent

    def get_paragraph_space_before(self) -> float:
        return self._paragraph_space_before

    def get_paragraph_space_after(self) -> float:
        return self._paragraph_space_after

    def get_heading_space_before(self, level: int = 1) -> float:
        return self._heading_space_before * (1.5 / level)

    def get_heading_space_after(self, level: int = 1) -> float:
        return self._heading_space_after / level

    def get_blockquote_indent(self) -> float:
        return self._blockquote_indent

    def get_code_indent(self) -> float:
        return self._code_indent

    def get_list_indent(self) -> float:
        return self._list_indent

    # ---- Hyphenation (basic) ----

    def hyphenate_word(self, word: str, max_width: float, font_name: str, font_size: float) -> List[str]:
        """Basic hyphenation: break word at syllable-like boundaries."""
        if not word or len(word) <= 4:
            return [word]

        # Simple vowel-consonant syllable breaking
        vowels = 'aeiouAEIOU'
        syllables = []
        current = ''
        last_was_vowel = False

        for ch in word:
            is_vowel = ch in vowels
            if current and not last_was_vowel and is_vowel and len(current) >= 2:
                # Break before this vowel if current syllable is long enough
                if len(current) >= 3:
                    syllables.append(current)
                    current = ch
                else:
                    current += ch
            else:
                current += ch
            last_was_vowel = is_vowel

        if current:
            syllables.append(current)

        # Merge tiny syllables
        merged = []
        for s in syllables:
            if merged and len(merged[-1]) < 3:
                merged[-1] += s
            else:
                merged.append(s)

        if not merged:
            merged = [word]

        # Check if parts fit within width
        parts = []
        for i, syllable in enumerate(merged[:-1]):
            parts.append(syllable + '-')
        parts.append(merged[-1])

        return parts if len(parts) > 1 else [word]

    # ---- Drop Caps (simple v1) ----

    def make_drop_cap(self, text: str, font_name: str, body_font_size: float) -> Tuple[str, float, float, str]:
        """Return (drop_char, drop_font_size, drop_width, remaining_text)."""
        if not text:
            return '', 0, 0, ''

        # First alphanumeric character
        match = re.search(r'([a-zA-Z0-9])', text)
        if not match:
            return text[0], body_font_size * 2, body_font_size * 2, text[1:] if len(text) > 1 else ''

        char = match.group(1)
        idx = match.start()
        drop_size = body_font_size * 3.0
        drop_width = self.measure_text(char, font_name, drop_size)
        remaining = text[:idx] + text[idx+1:]
        return char, drop_size, drop_width, remaining
