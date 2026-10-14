# pastpaper-ai Guidelines

## Project Purpose
Automated pipeline to parse, clean, and structure A-Level past papers (Computer Science, Mathematics, Business Studies) into topical exam practice questions.

## Tech Stack & Environment
- **Language:** Python 3.12+
- **Environment:** Windows PowerShell (`venv` virtual environment)
- **Primary Libraries:** Anthropic SDK / Google GenAI SDK, PyPDF2 / pdfplumber

## System & Execution Rules
1. **Encoding:** ALWAYS open, read, and write files using UTF-8 encoding (`encoding="utf-8"`) to handle mathematical notation, arrows ($\rightarrow$), and special symbols cleanly on Windows.
2. **Terminal Execution:** When running Python scripts in PowerShell, ensure the active `venv` environment is activated.
3. **Error Handling:** If script execution fails during parsing or file I/O, analyze the stack trace, fix the script, and re-run automatically to verify success.
4. **Data Integrity:** Keep extracted raw text separated from structured outputs (e.g., JSON or Markdown).

## Coding Conventions
- Write modular, clean functions with explicit type hints.
- Output clean JSON schema for parsed questions including subject, topic, year, paper number, and mark schemes where applicable.