# Pastpaper AI

A Flask study browser for Cambridge International AS & A Level Computer Science (9618), Paper 3.

The bank covers the 32 supplied papers, with 858 exam occurrences grouped into 651 distinct question cards. Explore syllabus topics, search question text, reveal mark schemes, and hover or tap dotted terms for explanations from the 87-term glossary. Each question links to original source documents and layouts.

For a Windows test, download this branch, extract it, and double-click **START_WEBSITE.bat**. Open **http://localhost:5000** while the launcher is running. Python 3.12+ is required. Hosting instructions are in [DEPLOYMENT.md](DEPLOYMENT.md); the site has not been deployed yet.

- [Web app instructions](WEB_APP.md)
- [Paper bank and duplicate protection](PAPER_BANK.md)
- [Import report](bank_import_report.json)

The web app reads SQLite without modifying it and needs no API key. The original processing pipeline is retained separately. No Node or frontend framework is used.
