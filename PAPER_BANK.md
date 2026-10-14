# Paper bank and duplicate protection

The uploaded archive contains 64 Paper 3 PDFs: 32 question-paper/mark-scheme pairs spanning 2021–2026. Two PDFs match the existing root-level October/November 2025 variant 31 files exactly; those existing files are reused. The other 62 PDFs are stored under `papers/9618/paper_3/<year>/<session>/`. The manifest records original archive paths, destinations, SHA-256 hashes for additions, duplicates, excluded files, and complete pairs.

Dates/session folders are derived from Cambridge filenames rather than the archive's folder names. `9618_s25_qp_32 (1).pdf` is normalised to `9618_s25_qp_32.pdf`. Nine unrelated Paper 4 support/system files are excluded, retained in the original uploaded ZIP, and never executed.

## Import additional ZIPs

```powershell
python paper_bank.py "path\to\papers.zip" --report paper_bank_manifest.json
```

PDF detection uses both Cambridge paper identity and SHA-256 content. Identical copies are skipped, even with a download suffix. Different content claiming the same paper identity stops the import before any PDFs are written. Identical bytes claiming different identities also require review. Existing PDFs are never overwritten. Rerunning the supplied archive added zero PDFs.

## Import processed questions

PDF ingestion does not call Claude, generate answers, or populate the web question bank. The website still contains the original 28 processed questions. Process and review each complete pair separately before importing its JSON:

```powershell
python import_questions.py "processed\9618_w25_31.json" --paper 9618_w25_31
```

The safe importer locks the SQLite transaction, compares paper identity plus question number, skips identical questions, and rejects changed content for an existing identity. A conflict rolls back the entire import, including earlier new questions in the batch. Repeated question wording on a different paper is preserved as a separate exam occurrence, not silently removed.

The database also has a unique index on paper code, year, season, paper variant, and question number. This blocks exact duplicate identities even if the legacy `database.py` is rerun; that legacy script will raise an integrity error rather than safely skip duplicates. Use `import_questions.py` going forward. The safe importer also normalises whitespace/case in question numbers for comparison and rejects pre-existing duplicates for review rather than deleting data.

No AI API calls were made during archive ingestion or importer tests. Definition/glossary extraction remains a later step after question processing and source review.
