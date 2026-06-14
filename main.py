#!/usr/bin/env python3
"""Book Layout Engine v1 - CLI entry point."""

import argparse
import sys
import os

from parser import parse_markdown
from layout import PageGeometry, LayoutEngine
from typography import Typography
from render import PDFRenderer


def main():
    parser = argparse.ArgumentParser(
        description='Book Layout Engine v1 - Markdown to PDF'
    )
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('--output', '-o', required=True, help='Output PDF path')
    parser.add_argument('--page-size', default='letter', choices=['letter', 'a4'],
                        help='Page size (letter or a4)')
    parser.add_argument('--font-size', type=float, default=11, help='Body font size')
    parser.add_argument('--margin', type=float, default=72, help='Page margins in points')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    # Read input
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    # Parse markdown
    document = parse_markdown(text)
    print(f"Parsed {len(document.chapters)} chapter(s)")

    # Setup geometry
    if args.page_size == 'a4':
        geometry = PageGeometry(width=595, height=842, margin_top=args.margin,
                                 margin_bottom=args.margin, margin_left=args.margin,
                                 margin_right=args.margin)
    else:
        geometry = PageGeometry(width=612, height=792, margin_top=args.margin,
                                 margin_bottom=args.margin, margin_left=args.margin,
                                 margin_right=args.margin)

    # Setup typography
    typography = Typography(body_font_size=args.font_size)

    # Render PDF
    renderer = PDFRenderer(geometry, typography, args.output)
    output_path = renderer.render_document(document)

    print(f"PDF generated: {output_path}")
    print(f"Total pages: {renderer.current_page}")


if __name__ == '__main__':
    main()
