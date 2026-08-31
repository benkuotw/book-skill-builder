#!/usr/bin/env python3
import sys
import os
import fitz  # PyMuPDF
import re

def create_skill(pdf_path, skill_name):
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)
        
    # Determine workspace root (where .agents lives)
    # The script is in .agents/skills/book-skill-builder/scripts/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    skill_dir = os.path.join(workspace_root, ".agents", "skills", skill_name)
    refs_dir = os.path.join(skill_dir, "references")
    
    os.makedirs(refs_dir, exist_ok=True)
    
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    chapters = []
    
    if toc:
        print("Found Table of Contents. Extracting chapters...")
        # toc format: [level, title, page_number]
        # Take level 1 and 2 to avoid making too many tiny files
        filtered_toc = [item for item in toc if item[0] <= 2]
        
        for i, item in enumerate(filtered_toc):
            title = item[1].strip()
            start_page = item[2] - 1  # 0-indexed in PyMuPDF
            # Find end page
            end_page = doc.page_count - 1
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
        for i in range(0, doc.page_count, chunk_size):
            chapters.append({
                "title": f"Pages {i+1} to {min(i+chunk_size, doc.page_count)}",
                "start": i,
                "end": min(i+chunk_size-1, doc.page_count-1)
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
            if 0 <= pno < doc.page_count:
                page = doc.load_page(pno)
                text_content.append(page.get_text())
                
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(text_content))
            
        toc_links.append(f"* **{chapter['title']}**\n  [Read](./references/{filename})")
        
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

You have access to the contents of {book_title}. When the user asks a question related to these topics, find the most relevant chapter below and use the `view_file` tool to read it before answering or implementing.

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
    if len(sys.argv) < 3:
        print("Usage: python build_book_skill.py <path_to_pdf> <desired_skill_name>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    skill_name = sys.argv[2]
    create_skill(pdf_path, skill_name)
