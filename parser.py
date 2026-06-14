import re
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class InlineNode:
    type: str  # text, bold, italic, code
    content: str
    children: List['InlineNode'] = field(default_factory=list)


@dataclass
class BlockNode:
    type: str  # heading, paragraph, list, list_item, code_block, blockquote, horizontal_rule
    level: int = 0
    content: str = ""
    children: List['BlockNode'] = field(default_factory=list)
    inline: List[InlineNode] = field(default_factory=list)
    language: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    chapters: List[BlockNode] = field(default_factory=list)
    body: List[BlockNode] = field(default_factory=list)


def parse_frontmatter(text: str) -> tuple:
    """Extract YAML frontmatter and return (frontmatter_dict, remaining_text)."""
    if not text.startswith('---'):
        return {}, text
    
    match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if not match:
        return {}, text
    
    yaml_text = match.group(1)
    remaining = text[match.end():]
    
    try:
        frontmatter = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError:
        frontmatter = {}
    
    return frontmatter, remaining


def parse_inline(text: str) -> List[InlineNode]:
    """Parse inline markdown into inline nodes."""
    nodes = []
    i = 0
    
    patterns = [
        (r'\*\*\*(.*?)\*\*\*', 'bold_italic'),
        (r'\*\*(.*?)\*\*', 'bold'),
        (r'\*(.*?)\*', 'italic'),
        (r'_(.*?)_', 'italic'),
        (r'`(.*?)`', 'code'),
    ]
    
    while i < len(text):
        earliest_match = None
        earliest_pattern = None
        earliest_start = len(text)
        
        for pattern, node_type in patterns:
            match = re.search(pattern, text[i:])
            if match and match.start() + i < earliest_start:
                earliest_start = match.start() + i
                earliest_match = match
                earliest_pattern = node_type
        
        if earliest_match is None:
            if text[i:]:
                nodes.append(InlineNode(type='text', content=text[i:]))
            break
        
        if earliest_start > i:
            nodes.append(InlineNode(type='text', content=text[i:earliest_start]))
        
        content = earliest_match.group(1)
        nodes.append(InlineNode(type=earliest_pattern, content=content))
        i = earliest_start + len(earliest_match.group(0))
    
    return nodes


def parse_markdown(text: str) -> Document:
    """Parse markdown text into a Document AST."""
    frontmatter, body_text = parse_frontmatter(text)
    
    lines = body_text.split('\n')
    blocks = []
    current_block = None
    current_block_lines = []
    
    def flush_block():
        nonlocal current_block, current_block_lines
        if not current_block_lines:
            return
        
        if current_block == 'paragraph':
            content = ' '.join(current_block_lines)
            blocks.append(BlockNode(
                type='paragraph',
                content=content,
                inline=parse_inline(content)
            ))
        elif current_block == 'code':
            content = '\n'.join(current_block_lines)
            blocks.append(BlockNode(
                type='code_block',
                content=content,
                language=current_block_meta.get('language', '')
            ))
        elif current_block == 'blockquote':
            content = ' '.join(current_block_lines)
            blocks.append(BlockNode(
                type='blockquote',
                content=content,
                inline=parse_inline(content)
            ))
        elif current_block == 'list':
            list_node = BlockNode(type='list', children=[])
            for item_lines in current_block_items:
                item_content = ' '.join(item_lines)
                list_node.children.append(BlockNode(
                    type='list_item',
                    content=item_content,
                    inline=parse_inline(item_content)
                ))
            blocks.append(list_node)
        
        current_block = None
        current_block_lines = []
    
    current_block_meta = {}
    current_block_items = []
    current_item_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Horizontal rule
        if re.match(r'^(\*{3,}|-{3,}|_{3,})$', stripped):
            flush_block()
            blocks.append(BlockNode(type='horizontal_rule'))
            i += 1
            continue
        
        # Heading
        heading_match = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if heading_match:
            flush_block()
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            blocks.append(BlockNode(
                type='heading',
                level=level,
                content=content,
                inline=parse_inline(content)
            ))
            i += 1
            continue
        
        # Code block fence
        code_fence_match = re.match(r'^```(\w*)', stripped)
        if code_fence_match:
            flush_block()
            current_block = 'code'
            current_block_meta = {'language': code_fence_match.group(1)}
            current_block_lines = []
            i += 1
            
            while i < len(lines) and not re.match(r'^```\s*$', lines[i].strip()):
                current_block_lines.append(lines[i])
                i += 1
            
            flush_block()
            i += 1  # Skip closing fence
            continue
        
        # Blockquote
        if stripped.startswith('>'):
            if current_block != 'blockquote':
                flush_block()
                current_block = 'blockquote'
                current_block_lines = []
            
            quote_content = stripped[1:].strip()
            current_block_lines.append(quote_content)
            i += 1
            continue
        
        # List item
        list_match = re.match(r'^([\*\-\+])\s+(.*)$', stripped)
        if list_match:
            if current_block != 'list':
                flush_block()
                current_block = 'list'
                current_block_items = []
                current_item_lines = []
            
            current_item_lines.append(list_match.group(2))
            i += 1
            
            # Continue collecting lines for this item until blank line or new list item
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                if not next_stripped:
                    break
                if re.match(r'^([\*\-\+])\s+', next_stripped):
                    break
                
                # Continuation line (indented or not)
                current_item_lines.append(next_stripped)
                i += 1
            
            current_block_items.append(current_item_lines)
            current_item_lines = []
            continue
        
        # Blank line
        if not stripped:
            flush_block()
            i += 1
            continue
        
        # Regular paragraph line
        if current_block not in ('paragraph',):
            flush_block()
            current_block = 'paragraph'
            current_block_lines = []
        
        current_block_lines.append(stripped)
        i += 1
    
    flush_block()
    
    # Group top-level h1 blocks into chapters
    chapters = []
    current_chapter = None
    current_chapter_body = []
    
    for block in blocks:
        if block.type == 'heading' and block.level == 1:
            if current_chapter is not None or current_chapter_body:
                chapters.append(BlockNode(
                    type='chapter',
                    content=current_chapter.content if current_chapter else '',
                    children=current_chapter_body,
                    inline=current_chapter.inline if current_chapter else []
                ))
            current_chapter = block
            current_chapter_body = []
        else:
            current_chapter_body.append(block)
    
    if current_chapter is not None or current_chapter_body:
        chapters.append(BlockNode(
            type='chapter',
            content=current_chapter.content if current_chapter else '',
            children=current_chapter_body,
            inline=current_chapter.inline if current_chapter else []
        ))
    
    doc = Document(frontmatter=frontmatter, chapters=chapters, body=blocks)
    return doc
