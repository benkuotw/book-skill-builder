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

3. Install the Python dependency (use a virtual environment if you prefer):

   ```bash
   pip install -r book-skill-builder/requirements.txt
   ```

New book skills are created next to `book-skill-builder`, in the same skills folder, so your agent picks them up without any moving.

## Usage

Ask your agent to build a skill for a book:

> **/book-skill-builder** Build a skill for this book: `/path/to/my-book.pdf` and name it `my-book`

You can also run the script yourself:

```bash
python3 scripts/build_book_skill.py /path/to/my-book.pdf my-book
```

Add `--out <folder>` to create the skill in a different skills folder.
