# Pastpaper AI web app

For a Windows check before hosting, download the `pastpaper-web` branch from GitHub, extract it, and double-click `START_WEBSITE.bat`. Open http://localhost:5000 and keep the launcher window open while testing. Once hosted, the site runs independently of your computer.

Alternatively, from the project directory in PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If activation is blocked, use `.\venv\Scripts\python.exe` directly. Flask runs the local server; Gunicorn is installed only on non-Windows systems for hosting. PDF tools are separate optional processing dependencies.

## What is available

- All 32 supplied 9618 Paper 3 papers, covering 2021–2026.
- 858 exam occurrences; 651 distinct cards after conservative grouping. A group requires matching question text, answer text, marks, topic, and original question/answer page images. Diagrams that differ remain separate. All source-paper references are retained.
- All 15 syllabus sections, year filtering, question-text search, and pages of up to 20 cards.
- An 87-term glossary: dotted terms in questions and answers explain concepts on hover, keyboard focus, or tap. Escape or clicking elsewhere dismisses an explanation. Entries are topic-aware; definitions are explanatory paraphrases, not extra marking points.
- Original-page images and PDF links for diagrams, tables, mathematical notation, and pseudocode formatting that plain-text extraction cannot fully represent. Images load when their layout panel opens.
- A Cambridge reference footer with links to the uploaded syllabus and pseudocode guide.

The app opens `pastpapers.db` read-only, relative to `app.py`. It never imports `database.py`, calls an AI service, or requires an API key to serve the site. Source PDFs, processed JSON, glossary JSON, source catalogue, and generated shared images must be included in a deployment. The provided repository contains them.

Run tests:

```powershell
python -m unittest discover -s tests -v
```

See `PAPER_BANK.md` for the repeatable extraction/import workflow. Hosting remains pending; this update does not create or purchase a Render service.
