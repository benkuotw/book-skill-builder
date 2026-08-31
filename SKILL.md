---
name: book-skill-builder
description: >-
  Use this skill when the user asks to build a skill for a given technical book, or
  wants to convert a PDF book into an Antigravity skill for future reference.
---

# Book Skill Builder

This skill automates the creation of new Antigravity skills from PDF books. It extracts the table of contents and text from a PDF, chunking it by chapters, and generates a structured skill ready to be used by the agent.

## Steps to build a skill from a book:

1. Ensure you have the path to the user's PDF book. If not, ask the user for the absolute path.
2. Run the helper Python script `build_book_skill.py` to parse the PDF and generate the skill:
   
   ```bash
   python ./scripts/build_book_skill.py <path_to_pdf> <desired_skill_name>
   ```
   *Note: Ensure the python environment has `PyMuPDF` installed (see `requirements.txt`).*

3. The script will output the path to the newly generated skill. 
4. Confirm with the user that the skill has been created successfully, and tell them they can now use the new skill for their tasks!
