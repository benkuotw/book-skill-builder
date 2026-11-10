# Book Skill Builder

An agent skill that turns a technical book (PDF) into a new skill. When the generated skill is invoked, the agent reads the relevant chapter and applies the book's knowledge directly to your project.

It works with any agent that reads `SKILL.md` skills, including Claude Code and Google Antigravity.

## Installation

1. Go to the skills folder of your agent:

   | Agent | Skills folder |
   | --- | --- |
   | Claude Code (all projects) | `~/.claude/skills` |
   | Claude Code (one project) | `<project>/.claude/skills` |
   | Antigravity (one project) | `<project>/.agents/skills` |
   | Antigravity (all projects) | `~/.gemini/antigravity/skills` (check your version's docs) |

   ```bash
   cd ~/.claude/skills
   ```

2. Clone this repository into a folder named `book-skill-builder`:

   ```bash
   git clone https://github.com/benkuotw/book-skill-builder.git
   ```

3. Install [uv](https://docs.astral.sh/uv/getting-started/installation/). The script declares its own dependency, so `uv run` installs it the first time the script runs.

   Without uv, install the dependency into a virtual environment instead:

   ```bash
   pip install -r book-skill-builder/requirements.txt
   ```

New book skills are created next to `book-skill-builder`, in the same skills folder, so your agent picks them up without any moving.

## Usage

Ask your agent to build a skill for a book:

> **/book-skill-builder** Build a skill for this book: `/path/to/my-book.pdf` and name it `my-book`

You can also run the script yourself:

```bash
uv run scripts/build_book_skill.py /path/to/my-book.pdf my-book
```

To combine a series into one skill, list the PDFs in reading order:

```bash
uv run scripts/build_book_skill.py book1.pdf book2.pdf book3.pdf my-series --title "My Series"
```

Without uv, use `python3` instead of `uv run`.

| Option | What it does |
| --- | --- |
| `--out <folder>` | Create the skill in a different skills folder. |
| `--depth auto` (default) | Split on the top 2 table-of-contents levels, going deeper (up to 4) while any section is longer than 50 pages, so chapters nested under Parts get their own files. |
| `--depth N` | Split on exactly the top N table-of-contents levels. |
| `--title <name>` | Name for the book or series in the generated `SKILL.md` (default: the PDF file names). |
| `--force` | Rebuild a skill that already exists. |

## Dependencies

The script reads PDFs with [pypdfium2](https://github.com/pypdfium2-team/pypdfium2), the Python binding for Chrome's PDF engine (PDFium). pypdfium2 is licensed Apache-2.0 / BSD-3-Clause, and PDFium under a BSD-style license, so the whole tool can be used under this repository's MIT license.
