#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pypdfium2>=5.15.1",
# ]
# ///
"""Turn one or more PDF books into an agent skill, one Markdown file per TOC section."""
import argparse
import os
import re
import shutil
import sys

import pypdfium2 as pdfium

# The skills folder this builder is installed in (the parent of book-skill-builder/).
# New skills go next to the builder, so they land wherever the agent reads skills:
# ~/.claude/skills for Claude Code, .agents/skills for Antigravity, and so on.
DEFAULT_SKILLS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# --depth auto: start at this many TOC levels and go deeper while sections are too long.
AUTO_MIN_DEPTH = 2
AUTO_MAX_DEPTH = 4
AUTO_MAX_PAGES = 50  # a section longer than this is split further if the TOC allows
CHUNK_PAGES = 20     # page chunk size for a PDF without a TOC


def read_toc(doc):
    """Return the bookmarks as (level, title, page_index), level and index 0-based.

    Bookmarks that point nowhere in this document, and ones that point back to an
    earlier page than the one before them, are skipped. Some PDFs end their TOC with
    such an entry (e.g. "Blank Page" on page 1); keeping it would copy the whole book
    into one file.
    """
    page_count = len(doc)
    toc = []
    for bookmark in doc.get_toc():
        title = bookmark.get_title().strip()
        # get_dest() also follows GoTo actions, which many PDFs use instead of a direct destination.
        dest = bookmark.get_dest()
        index = dest.get_index() if dest else None
        if index is None or not 0 <= index < page_count:
            continue
        if toc and index < toc[-1][2]:
            print(f"  Skipping out-of-order TOC entry: {title!r} (page {index + 1})")
            continue
        toc.append((bookmark.level, title, index))
    return toc


def sections_at_depth(toc, depth, page_count):
    """Keep TOC entries above `depth` levels and give each its page range.

    An entry whose next entry starts on the same page (e.g. a Part title right before
    its first chapter) gets no pages; it only appears as a heading in the index.
    """
    kept = [e for e in toc if e[0] < depth]
    sections = []
    for i, (level, title, start) in enumerate(kept):
        next_start = kept[i + 1][2] if i + 1 < len(kept) else page_count
        end = next_start - 1
        if end < start:  # shares its first page with the next entry
            end = start - 1
        sections.append({"level": level, "title": title, "start": start, "end": end})
    return sections


def longest(sections):
    return max((s["end"] - s["start"] + 1 for s in sections), default=0)


def choose_sections(toc, depth, page_count):
    if depth != "auto":
        return sections_at_depth(toc, int(depth), page_count), int(depth)
    max_level = max(e[0] for e in toc) + 1
    d = AUTO_MIN_DEPTH
    sections = sections_at_depth(toc, d, page_count)
    while d < min(AUTO_MAX_DEPTH, max_level) and longest(sections) > AUTO_MAX_PAGES:
        d += 1
        sections = sections_at_depth(toc, d, page_count)
    return sections, d


def page_text(doc, page_index):
    page = doc[page_index]
    textpage = page.get_textpage()
    # Only the visible page area, which leaves out printer marks around it.
    # PDFium ends lines with \r\n, and writes a hyphen at a line break as \x02
    # with the break itself removed.
    text = textpage.get_text_bounded().replace("\r\n", "\n").replace("\x02", "-\n")
    textpage.close()
    page.close()
    return text


def safe_name(text, limit):
    return re.sub(r"[^a-zA-Z0-9_\- ]", "", text).strip().replace(" ", "_")[:limit]


def build_book(pdf_path, refs_dir, link_prefix, depth):
    """Write one book's sections into refs_dir and return its index lines."""
    print(f"Opening PDF: {pdf_path}")
    doc = pdfium.PdfDocument(pdf_path)
    page_count = len(doc)
    toc = read_toc(doc)

    if toc:
        sections, used_depth = choose_sections(toc, depth, page_count)
        print(f"  Found Table of Contents. Splitting at {used_depth} TOC level(s).")
    else:
        print(f"  No Table of Contents found. Chunking by {CHUNK_PAGES} pages.")
        sections = [{"level": 0, "title": f"Pages {i + 1} to {min(i + CHUNK_PAGES, page_count)}",
                     "start": i, "end": min(i + CHUNK_PAGES, page_count) - 1}
                    for i in range(0, page_count, CHUNK_PAGES)]

    os.makedirs(refs_dir, exist_ok=True)
    top = min(s["level"] for s in sections)
    index = []
    files = 0
    for section in sections:
        indent = "  " * (section["level"] - top)
        if section["end"] < section["start"]:  # heading only, no pages of its own
            index.append(f"{indent}* **{section['title']}**")
            continue
        files += 1
        filename = f"{files:02d}_{safe_name(section['title'], 40) or f'section_{files}'}.md"
        text = [f"# {section['title']}\n"]
        text += [page_text(doc, p) for p in range(section["start"], section["end"] + 1)]
        with open(os.path.join(refs_dir, filename), "w", encoding="utf-8") as f:
            f.write("\n".join(text))
        index.append(f"{indent}* [{section['title']}](./{link_prefix}/{filename})")
    doc.close()
    print(f"  Wrote {files} files (longest section: {longest(sections)} pages).")
    return index


def join_titles(titles):
    return titles[0] if len(titles) == 1 else ", ".join(titles[:-1]) + " and " + titles[-1]


def create_skill(pdf_paths, skill_name, skills_dir=DEFAULT_SKILLS_DIR, depth="auto",
                 title=None, force=False):
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            sys.exit(f"Error: PDF file '{pdf_path}' not found.")

    skill_dir = os.path.join(skills_dir, skill_name)
    refs_dir = os.path.join(skill_dir, "references")
    if os.path.exists(skill_dir):
        if not force:
            sys.exit(f"Error: '{skill_dir}' already exists. Pass --force to rebuild it.")
        shutil.rmtree(refs_dir, ignore_errors=True)

    book_titles = [os.path.splitext(os.path.basename(p))[0] for p in pdf_paths]
    source = title or join_titles(book_titles)

    if len(pdf_paths) == 1:
        index_body = "\n".join(build_book(pdf_paths[0], refs_dir, "references", depth))
    else:
        parts = []
        for n, (pdf_path, book) in enumerate(zip(pdf_paths, book_titles), 1):
            folder = f"{n}_{safe_name(book, 40)}"
            lines = build_book(pdf_path, os.path.join(refs_dir, folder), f"references/{folder}", depth)
            parts.append(f"### Book {n}: {book}\n\n" + "\n".join(lines))
        index_body = "\n\n".join(parts)

    order_note = ""
    if len(pdf_paths) > 1:
        order_note = "\nThe books are listed in reading order. Say which book and chapter an answer comes from.\n"

    print("Generating SKILL.md...")
    skill_content = f"""---
name: {skill_name}
description: >-
  Use this skill when the user asks questions or needs help implementing concepts
  from {source}. It contains reference material, best practices, and patterns
  from the {"books" if len(pdf_paths) > 1 else "book"}.
---

# {source} Knowledge Base

You have access to the contents of {source}. When the user asks a question related to these topics, find the most relevant chapter below and read its file before answering or implementing.
{order_note}
## Index / Table of Contents

{index_body}

## Instructions
1. Always read the relevant chapter from the references before providing an answer.
2. Follow the specific coding conventions and architectural patterns outlined in the text.
3. If the user's request spans multiple topics, you may read multiple chapters.
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_content)

    print(f"Successfully generated skill: {skill_name}")
    print(f"Skill located at: {skill_dir}")


def depth_arg(value):
    if value == "auto" or (value.isdigit() and int(value) >= 1):
        return value
    raise argparse.ArgumentTypeError("must be 'auto' or a whole number of at least 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Turn one or more PDF books into an agent skill.",
        epilog="Several PDFs (e.g. a book series) go into one skill, in the order given.")
    parser.add_argument("pdf_paths", nargs="+", metavar="pdf_path",
                        help="path to a PDF book; give several for a series, in reading order")
    parser.add_argument("skill_name", help="name of the new skill (also its folder name)")
    parser.add_argument("--out", default=DEFAULT_SKILLS_DIR,
                        help=f"skills folder to create the skill in (default: {DEFAULT_SKILLS_DIR})")
    parser.add_argument("--depth", default="auto", type=depth_arg,
                        help="how many TOC levels to split on (default: auto, which goes deeper "
                             f"until no section is longer than {AUTO_MAX_PAGES} pages)")
    parser.add_argument("--title", help="name for the book or series in SKILL.md "
                                        "(default: the PDF file names)")
    parser.add_argument("--force", action="store_true",
                        help="rebuild a skill that already exists (replaces its references)")
    args = parser.parse_args()
    create_skill([os.path.abspath(os.path.expanduser(p)) for p in args.pdf_paths], args.skill_name,
                 os.path.abspath(os.path.expanduser(args.out)), args.depth, args.title, args.force)
