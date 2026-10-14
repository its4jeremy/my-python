import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from app import ROOT
from import_questions import import_questions
from paper_bank import import_archive


class ImportTests(unittest.TestCase):
    def test_archive_repeat_and_renamed_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'bank'
            root.mkdir()
            archive = Path(directory) / 'papers.zip'
            with ZipFile(archive, 'w') as z:
                z.writestr('../9618_s25_qp_32 (1).pdf', b'%PDF-qp')
                z.writestr('copy/9618_s25_qp_32.pdf', b'%PDF-qp')
                z.writestr('9618_s25_ms_32.pdf', b'%PDF-ms')
                z.writestr('desktop.ini', b'not instructions')
            first = import_archive(archive, root)
            self.assertEqual(len(first['added']), 2)
            self.assertEqual(len(first['duplicates']), 1)
            self.assertTrue(first['pairs'][0]['complete'])
            self.assertEqual(len(import_archive(archive, root)['added']), 0)
            self.assertEqual(len(list(root.rglob('*.pdf'))), 2)

    def test_conflicting_pdf_aborts_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'bank'
            root.mkdir()
            archive = Path(directory) / 'papers.zip'
            with ZipFile(archive, 'w') as z:
                z.writestr('9618_s25_qp_32.pdf', b'%PDF-original')
                z.writestr('copy/9618_s25_qp_32.pdf', b'%PDF-conflicting')
            with self.assertRaises(ValueError):
                import_archive(archive, root)
            self.assertEqual(list(root.rglob('*.pdf')), [])

    def test_database_reimports_conflicts_and_distinct_papers(self):
        questions = json.loads((ROOT / 'output.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'bank.db'
            with sqlite3.connect(ROOT / 'pastpapers.db') as source, sqlite3.connect(database) as target:
                source.backup(target)
            self.assertEqual(import_questions(database, questions, '9618_w25_31'), {'inserted': 0, 'skipped': 28})
            self.assertEqual(import_questions(database, questions, '9618_w25_31'), {'inserted': 0, 'skipped': 28})
            changed = [dict(questions[0]), dict(questions[1])]
            changed[0]['question_number'] = '99(a)'
            changed[1]['mark_scheme'] = 'Conflicting answer'
            with self.assertRaises(ValueError):
                import_questions(database, changed, '9618_w25_31')
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute('select count(*) from questions').fetchone()[0], 28)
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute('INSERT INTO questions SELECT NULL, paper_code, year, season, paper_number, syllabus_section, question_number, topic, subtopic, question_text, mark_scheme, key_phrases, common_mistakes, marks FROM questions WHERE id=1')
            self.assertEqual(import_questions(database, [questions[0], questions[0]], '9618_w24_31'), {'inserted': 1, 'skipped': 1})
            self.assertEqual(import_questions(database, [questions[0]], '9618_w24_31'), {'inserted': 0, 'skipped': 1})
