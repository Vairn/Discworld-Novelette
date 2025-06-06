#!/usr/bin/env python3
"""
Convert a long HTML book into paginated format with visual pages
"""

import re
from bs4 import BeautifulSoup

def estimate_content_height(text):
    """Estimate how much vertical space content will take"""
    # More conservative estimation based on character count and line breaks
    lines = len(text.split('\n')) + len(text) // 70  # ~70 chars per line (more conservative)
    return lines * 14  # ~14pt line height in pixels (accounting for line spacing)

def format_death_speech(text):
    """Convert Death's all-caps dialogue to small caps formatting"""
    import re
    
    # Multiple patterns to catch different Death speech formats
    # Using DOTALL flag to handle multiline Death speech properly
    patterns = [
        # Standard sentences ending with punctuation (including newlines)
        r'([A-Z][A-Z\s.,!?\'";:\-…\n\r]{3,}[.!?])',
        # Short exclamations or questions
        r'([A-Z]{2,}[.!?])',
        # Sentences that might not end with punctuation (including newlines)
        r'([A-Z][A-Z\s.,!?\'";:\-…\n\r]{5,})',
        # Death's name calls like "COMMANDER VIMES"
        r'([A-Z]{3,}\s+[A-Z]{3,})',
        # Single words in caps that are likely Death
        r'\b([A-Z]{4,})\b',
        # Multi-line Death speech
        r'([A-Z][A-Z\s.,!?\'";:\-…]*\n[A-Z][A-Z\s.,!?\'";:\-…]*[.!?]?)'
    ]
    
    def replace_death_speech(match):
        speech = match.group(1)  # Don't strip - preserve spacing
        if len(speech.strip()) < 3:  # Skip very short matches (but check stripped length)
            return speech
            
        # Don't process if already wrapped
        if '<span class="death-speech">' in speech:
            return speech
            
        # Only convert if it's mostly uppercase (Death's speech)
        uppercase_count = sum(1 for c in speech if c.isupper())
        total_letters = sum(1 for c in speech if c.isalpha())
        
        if total_letters > 0 and uppercase_count / total_letters > 0.6:
            return f'<span class="death-speech">{speech}</span>'
        return speech
    
    # Apply all patterns, but avoid reprocessing already processed text
    result = text
    for pattern in patterns:
        # Skip if this text already has death-speech spans
        if '<span class="death-speech">' in result:
            continue
        compiled_pattern = re.compile(pattern, re.DOTALL | re.MULTILINE)
        result = compiled_pattern.sub(replace_death_speech, result)
    
    return result

def split_into_pages(html_file, output_file):
    """Split HTML content into visual pages"""
    
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Find the main content (skip head, nav, etc.)
    body = soup.find('body')
    if not body:
        print("Error: No body tag found")
        return
    
    # Create new HTML structure
    new_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Occupational Hazard - A Discworld Tale</title>
    <link rel="stylesheet" href="pratchett-book-style.css">
</head>
<body>
"""
    
    # Title page
    new_html += """
    <div class="page" data-page="">
        <div class="title-page">
            <div class="title">Occupational Hazard</div>
            <div class="subtitle">A Discworld Tale</div>
        </div>
    </div>
"""
    
    # Get all content elements
    content_elements = []
    
    # Process TOC first
    toc = soup.find('nav', id='TOC')
    if toc:
        new_html += f'<div class="page" data-page="">{str(toc)}</div>'
    
    # Get main content elements (skip nav)
    main_content = []
    for element in body.find_all(['h1', 'h2', 'h3', 'p', 'hr', 'div']):
        if element.name == 'nav':
            continue
        if element.parent and element.parent.name == 'nav':
            continue
        main_content.append(element)
    
    # Group content into pages
    current_page_content = []
    current_height = 0
    max_height = 500  # Back to original size - Death speech HTML was throwing off estimates
    page_num = 1
    
    for element in main_content:
        element_text = element.get_text()
        element_height = estimate_content_height(element_text)
        
        # Add extra height for headers and special elements
        if element.name in ['h1', 'h2']:
            element_height += 30  # Extra space for large headers (reduced from 40)
        elif element.name == 'h3':
            element_height += 15  # Extra space for smaller headers (reduced from 20)
        elif element.name == 'hr':
            element_height += 20  # Extra space for scene breaks (reduced from 30)
        
        # Force new page for chapters
        if element.name in ['h1', 'h2'] and current_page_content:
            # Close current page
            page_content = ''.join(current_page_content)
            new_html += f'<div class="page" data-page="{page_num}">{page_content}</div>'
            page_num += 1
            current_page_content = []
            current_height = 0
        
        # Check if adding this element would exceed page height
        if current_height + element_height > max_height and current_page_content:
            # Close current page - paragraphs CAN be split across pages
            page_content = ''.join(current_page_content)
            new_html += f'<div class="page" data-page="{page_num}">{page_content}</div>'
            page_num += 1
            current_page_content = []
            current_height = 0
        
        # Format Death's speech in this element
        element_html = str(element)
        element_html = format_death_speech(element_html)
        current_page_content.append(element_html)
        current_height += element_height
    
    # Add any remaining content
    if current_page_content:
        page_content = ''.join(current_page_content)
        new_html += f'<div class="page" data-page="{page_num}">{page_content}</div>'
    
    new_html += """
</body>
</html>"""
    
    # Write the new file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print(f"Created paginated book with {page_num} pages")

if __name__ == "__main__":
    split_into_pages("Pratchett_Style_Book.html", "Paginated_Book.html") 