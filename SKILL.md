---
name: book-skill-builder
description: >-
  Use this skill when the user asks to build a skill for a given technical book, or
  wants to convert a PDF book into an agent skill for future reference.
---

# Book Skill Builder

This skill creates a new agent skill from a PDF book. It splits the book's text into one file per chapter (using the PDF's table of contents) and writes a `SKILL.md` index for them, so you can read the right chapter when the user asks about the book.

## Steps to build a skill from a book:

1. Ensure you have the path to the user's PDF book. If not, ask the user for the absolute path.
2. Run the helper script from this skill's folder (the folder containing this `SKILL.md`):

   ```bash
   python3 scripts/build_book_skill.py <path_to_pdf> <desired_skill_name>
   ```

   The new skill is created next to this one, in the same skills folder, so the agent can use it right away. Add `--out <skills_folder>` only if the user wants it somewhere else.

   *Note: The script needs `PyMuPDF` (see `requirements.txt`). If the import fails, install it with `pip install -r requirements.txt`.*

3. The script prints the path of the new skill, and warns about any table-of-contents entries it skipped.
4. Confirm with the user that the skill has been created successfully. Tell them it can be used in new conversations (some agents only load skills when a conversation starts).
