#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pypdfium2>=5.15.1",
# ]
# ///
import argparse
import sys
import os
import pypdfium2 as pdfium
import re

# The skills folder this builder is installed in (the parent of book-skill-builder/).
# New skills go next to the builder, so they land wherever the agent reads skills:
# ~/.claude/skills for Claude Code, .agents/skills for Antigravity, and so on.
DEFAULT_SKILLS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

def read_toc(doc):
    """Return the bookmarks as [level, title, page_number], both 1-indexed.

    page_number is 0 for a bookmark that points nowhere in this document.
    """
    toc = []
    for bookmark in doc.get_toc():
        # get_dest() also follows GoTo actions, which many PDFs use instead of a direct destination.
        dest = bookmark.get_dest()
        page_index = dest.get_index() if dest else None
        page_number = page_index + 1 if page_index is not None else 0
        toc.append([bookmark.level + 1, bookmark.get_title(), page_number])
    return toc

def create_skill(pdf_path, skill_name, skills_dir=DEFAULT_SKILLS_DIR):
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)

    skill_dir = os.path.join(skills_dir, skill_name)
    refs_dir = os.path.join(skill_dir, "references")
    
    os.makedirs(refs_dir, exist_ok=True)
    
    print(f"Opening PDF: {pdf_path}")
    doc = pdfium.PdfDocument(pdf_path)
    page_count = len(doc)
    toc = read_toc(doc)
    
    chapters = []
    
    if toc:
        print("Found Table of Contents. Extracting chapters...")
        # toc format: [level, title, page_number]
        # Take level 1 and 2 to avoid making too many tiny files, in page order.
        # Some PDFs end their TOC with an entry pointing back to an earlier page
        # (e.g. "Blank Page" on page 1). Keeping it would copy the whole book into
        # one file and cut the chapter before it down to a single page.
        filtered_toc = []
        for item in toc:
            if item[0] > 2 or not 1 <= item[2] <= page_count:
                continue
            if filtered_toc and item[2] < filtered_toc[-1][2]:
                print(f"Skipping out-of-order TOC entry: {item[1].strip()!r} (page {item[2]})")
                continue
            filtered_toc.append(item)

        for i, item in enumerate(filtered_toc):
            title = item[1].strip()
            start_page = item[2] - 1  # 0-indexed in pypdfium2
            # Find end page
            end_page = page_count - 1
            if i + 1 < len(filtered_toc):
                end_page = filtered_toc[i+1][2] - 1 - 1 # Page before next chapter
                if end_page < start_page:
                    end_page = start_page # Fallback
            
            chapters.append({
                "title": title,
                "start": start_page,
                "end": end_page
            })
    else:
        print("No Table of Contents found. Chunking by 20 pages...")
        chunk_size = 20
        for i in range(0, page_count, chunk_size):
            chapters.append({
                "title": f"Pages {i+1} to {min(i+chunk_size, page_count)}",
                "start": i,
                "end": min(i+chunk_size-1, page_count-1)
            })
            
    print(f"Extracting text into {len(chapters)} files...")
    
    toc_links = []
    
    for idx, chapter in enumerate(chapters, 1):
        # Sanitize filename
        safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', chapter["title"]).strip().replace(' ', '_')
        if not safe_title:
            safe_title = f"chapter_{idx}"
            
        filename = f"{idx:02d}_{safe_title[:30]}.md"
        filepath = os.path.join(refs_dir, filename)
        
        # Extract text for page range
        text_content = [f"# {chapter['title']}\n"]
        for pno in range(chapter["start"], chapter["end"] + 1):
            if 0 <= pno < page_count:
                page = doc[pno]
                textpage = page.get_textpage()
                # Only the visible page area, which leaves out printer marks around it.
                # PDFium ends lines with \r\n, and writes a hyphen at a line break as \x02
                # with the break itself removed.
                text = textpage.get_text_bounded().replace("\r\n", "\n").replace("\x02", "-\n")
                text_content.append(text)
                textpage.close()
                page.close()
                
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(text_content))
            
        toc_links.append(f"* **{chapter['title']}**\n  [Read](./references/{filename})")
        
    doc.close()

    print("Generating SKILL.md...")
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    
    # Extract book title from filename if possible
    book_title = os.path.basename(pdf_path).replace('.pdf', '')
    
    skill_content = f"""---
name: {skill_name}
description: >-
  Use this skill when the user asks questions or needs help implementing concepts
  from {book_title}. It contains reference material, best practices, and patterns
  from the book.
---

# {book_title} Knowledge Base

You have access to the contents of {book_title}. When the user asks a question related to these topics, find the most relevant chapter below and read its file before answering or implementing.

## Index / Table of Contents

{chr(10).join(toc_links)}

## Instructions
1. Always read the relevant chapter from the references before providing an answer.
2. Follow the specific coding conventions and architectural patterns outlined in the text.
3. If the user's request spans multiple topics, you may read multiple chapters.
"""
    with open(skill_md_path, "w", encoding="utf-8") as f:
        f.write(skill_content)
        
    print(f"Successfully generated skill: {skill_name}")
    print(f"Skill located at: {skill_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Turn a PDF book into an agent skill.")
    parser.add_argument("pdf_path", help="path to the PDF book")
    parser.add_argument("skill_name", help="name of the new skill (also its folder name)")
    parser.add_argument("--out", default=DEFAULT_SKILLS_DIR,
                        help=f"skills folder to create the skill in (default: {DEFAULT_SKILLS_DIR})")
    args = parser.parse_args()
    create_skill(args.pdf_path, args.skill_name, os.path.abspath(os.path.expanduser(args.out)))
