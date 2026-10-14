# Paper bank and duplicate protection

All 32 uploaded Paper 3 question-paper/mark-scheme pairs have been processed locally. Every paper reconciles to 75 marks; each of the 858 sub-question identities is present in both documents, and its question-paper mark value agrees with the mark scheme. The database contains 858 exam occurrences, including the original 28 reviewed records. No Claude/API calls were used.

## Sources and reproducibility

- `paper_bank_manifest.json`: archive additions, duplicates, exclusions and pairs.
- `processed/*.json`: source hashes, extracted/reviewed questions, syllabus sections and source page numbers. Preserve these reviewed caches; automatic extraction does not replace topic review.
- `topic_map.json`: reviewed topic assignments and sub-question overrides. Unrecognised future papers require an explicit mapping before import.
- `source_catalog.json`: original PDFs and shared page-image locations.
- `bank_import_report.json`: initial full-bank import, 830 new records and 28 skipped.
- `glossary.json`: 87 explanatory definitions, section scopes, aliases and related mark-scheme references. Entries are reviewed paraphrases; the related answer is available for comparison. They are not claimed as verbatim official definitions or additional marking points.

Archive ingestion reused two exact existing PDFs and added 62. The original Cambridge filenames determine the year/session; a browser download suffix `(1)` was removed. Nine unrelated Paper 4 support/system files were excluded and remain in the original uploaded ZIP.

## Repeatable import

```powershell
python paper_bank.py "path\to\papers.zip" --report paper_bank_manifest.json
python -m pip install -r requirements-processing.txt
python build_bank.py
python render_sources.py
```

`build_bank.py` uses the reviewed `processed` caches when present and checks source SHA-256 hashes. Without a cache it extracts question labels, inherited context and mark-scheme rows, then checks identities and marks. It stops on unsupported topic mappings or incomplete extraction. For newly uploaded papers, review the extracted content and assign topics before accepting the output. Keep the old manifest alongside a new archive report; `--report` writes the selected report file.

PDF text cannot fully preserve diagrams, mathematical overbars or arbitrary typography. The original layouts and PDFs are accessible from every question, including the mark-scheme layouts. Do not replace those originals with text alone.

For a separately reviewed pipeline JSON file:

```powershell
python import_questions.py "processed_answers.json" --paper 9618_w25_31
```

The safe importer locks the SQLite transaction, compares paper identity plus question number, skips identical records, and rejects conflicting content. A conflict rolls back the whole paper’s import, including earlier new questions in the batch. A unique database index also blocks exact duplicate identities, including inserts attempted by the legacy `database.py`. Use the safe importer instead of that legacy insertion script.

The full-bank import was repeated: **zero new rows; all 858 skipped**. Reimporting the original ZIP adds zero PDFs. Repeated questions from different papers retain distinct source occurrences; the website groups matching content and layouts into one card without discarding their citations. Shared page images are stored once by a hash of their pixels.

The existing `pipeline.py` and `database.py` remain unchanged. They are not used by the offline collection builder or the web app.
