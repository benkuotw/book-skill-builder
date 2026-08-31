# Book Skill Builder

This is an Antigravity agent skill designed to help users generate a specific skill based on a technical book. When the generated skill is invoked, you can apply knowledge from the book directly to your project.

## Installation

1. Navigate to your project's `.agents/skills` directory:
   ```bash
   cd .agents/skills
   ```
2. Clone this repository into a directory named `book-skill-builder`:
   ```bash
   git clone https://github.com/benkuotw/book-skill-builder.git
   ```
3. Install the required Python dependencies in your workspace's virtual environment:
   ```bash
   pip install -r book-skill-builder/requirements.txt
   ```

## Usage

Once installed, simply ask your agent to build a skill based on a specific book:

> **/book-skill-builder** Build a skill for this book: `/path/to/my-book.pdf` and name it `my-book`