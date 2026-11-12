# Pastpaper AI

A study site for Cambridge A Level Computer Science (9618) Paper 3 that groups
past exam questions by syllabus topic, with mark schemes and a built-in glossary.

![Screenshot](docs/screenshot.png)

## Why I built it
As a previous A Level student I know how precise cambridge wants answers to be structured in terms of jargon and what to include. Lots of student struggle with that including myself so I built a website that helps you get reps in answering questions categorized by their topic so you can drill down how cambridge would like answers framed.

## What it does
- Browse 651 questions from 32 papers (2021–2026) by syllabus topic
- Search question text and filter by year
- Reveal the mark scheme for each question
- Hover over key terms for explanations from an 87-term glossary

## How it works
1. **Extract:** pdfplumber pulls text out of each question paper and mark scheme
2. **Structure:** the Claude API splits each paper into sub-questions, matches each
   one to its mark scheme, and tags it with the official syllabus topic
3. **Store:** results go into a SQLite database, with duplicate protection
4. **Serve:** a Flask web app reads the database (read-only) and renders the pages

**Tech:** Python, Claude API, pdfplumber, SQLite, Flask

## Run it locally
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000

# What was hard
Getting AI to map past paper questions accurately to mark schemes.