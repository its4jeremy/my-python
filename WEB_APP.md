# Pastpaper AI web app

From the project directory in Windows PowerShell:

```powershell
# Create the virtual environment only if you do not already have one.
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://localhost:5000. Stop the server with Ctrl+C. If PowerShell blocks activation, use ` .\venv\Scripts\python.exe -m pip install -r requirements.txt` and ` .\venv\Scripts\python.exe app.py` directly.

The app reads the existing `pastpapers.db` beside `app.py`, regardless of the shell's working directory. It never imports `database.py`, reruns the AI pipeline, inserts questions, or requires an API key. Paper 3 includes paper numbers `3` and the two-digit variants `30`–`39`; the supplied data is variant `31`. All 15 syllabus sections appear, including empty sections.

Use the topic filter to match section numbers or names and optionally hide empty sections. Topic pages also support keyword search within the section. The Search page searches all Paper 3 question text; `%` and `_` are treated as literal characters. Answers open with native HTML details controls and work without JavaScript. Key phrases are highlighted in the mark scheme and listed separately.

Only Flask is needed for the web app. `requirements.txt` covers this app; the existing PDF/AI scripts have separate dependencies. The local development server binds to loopback and runs without debug mode.

Run web tests without executing the existing API or PDF scripts:

```powershell
python -m unittest discover -s tests -v
```

The tests use the supplied 28-question database. To update the question bank, use your existing processing/import workflow separately; note that running `database.py` again inserts rows again rather than replacing them.
