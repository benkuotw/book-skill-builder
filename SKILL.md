---
name: book-skill-builder
description: >-
  Use this skill when the user asks to build a skill for a given technical book, or
  wants to convert a PDF book (or a series of books) into an agent skill for future reference.
---

# Book Skill Builder

This skill creates a new agent skill from a PDF book, or from several books (such as a series) combined into one skill. It splits each book's text into one file per chapter (using the PDF's table of contents) and writes a `SKILL.md` index for them, so you can read the right chapter when the user asks about the book.

## Steps to build a skill from a book:

1. Ensure you have the path to the user's PDF book. If not, ask the user for the absolute path. For a series, get every PDF and the reading order; if the user gives no order, use the series' publication order and say so.
2. Run the helper script from this skill's folder (the folder containing this `SKILL.md`). If `uv` is installed, use it, because it installs the script's dependency automatically:

   ```bash
   uv run scripts/build_book_skill.py <path_to_pdf> <desired_skill_name>
   ```

   For a series, list the PDFs in reading order before the skill name, and give the series a name with `--title`:

   ```bash
   uv run scripts/build_book_skill.py <book1.pdf> <book2.pdf> <book3.pdf> <desired_skill_name> --title "<Series name>"
   ```

   Each book goes in its own `references/<n>_<book>/` folder, and the index lists the books in that order.

   The new skill is created next to this one, in the same skills folder, so the agent can use it right away. Add `--out <skills_folder>` only if the user wants it somewhere else.

   Other options:

   | Option | What it does |
   | --- | --- |
   | `--depth auto` (default) | Splits on the top 2 table-of-contents levels, and goes deeper (up to 4) while any section is longer than 50 pages. This catches books whose chapters sit under Parts. |
   | `--depth N` | Splits on exactly the top N levels. |
   | `--force` | Rebuilds a skill that already exists. Without it, the script stops rather than overwrite. Ask the user before using it. |

   *Note: Without `uv`, run `python3 scripts/build_book_skill.py` with the same arguments. It needs `pypdfium2` (see `requirements.txt`); if the import fails, install it into a virtual environment with `pip install -r requirements.txt`.*

3. The script prints the path of the new skill, how many TOC levels it split on, the longest section in pages, and warns about any table-of-contents entries it skipped. If the longest section is still very long, try a larger `--depth`.
4. Confirm with the user that the skill has been created successfully. Tell them it can be used in new conversations (some agents only load skills when a conversation starts).
