import hashlib
import json
import re
import sqlite3
import unittest

from app import ROOT, SECTIONS
from glossary import ENTRIES
from import_questions import canonical_key, payload


class CollectionTests(unittest.TestCase):
    def test_full_collection_matches_database_and_sources(self):
        catalog=json.loads((ROOT/'source_catalog.json').read_text(encoding='utf-8'))
        packages=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'processed').glob('*.json')]
        self.assertEqual(len(packages),32)
        expected={}
        for package in packages:
            self.assertEqual(sum(q['marks'] for q in package['questions']),75,package['paper'])
            for kind in ('qp','ms'):
                file=ROOT/package[kind]
                self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),package['sha256'][kind])
            code,session,variant=package['paper'].split('_')
            for q in package['questions']:
                self.assertIn(q['syllabus_section'],SECTIONS)
                self.assertTrue(q['question_text'].strip())
                self.assertTrue(q['mark_scheme'].strip())
                for kind in ('qp','ms'):
                    self.assertTrue(q[kind+'_pages'])
                    for page in q[kind+'_pages']:
                        image=catalog[package['paper']][kind]['pages'][str(page)]
                        self.assertTrue((ROOT/'static'/image).is_file())
                row=dict(q,paper_code=code,year='20'+session[1:],paper_number=variant,
                         season={'s':'May/June','w':'October/November','m':'February/March'}[session[0]])
                key=canonical_key(row)
                self.assertNotIn(key,expected)
                expected[key]=payload(row)
        with sqlite3.connect(ROOT/'pastpapers.db') as db:
            db.row_factory=sqlite3.Row
            actual={canonical_key(dict(r)):payload(dict(r)) for r in db.execute('SELECT * FROM questions')}
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(len(actual),db.execute('SELECT COUNT(*) FROM questions').fetchone()[0])
        self.assertEqual(actual,expected)
        self.assertEqual(len(actual),858)

    def test_glossary_sources_are_real_and_term_ids_are_unique(self):
        self.assertEqual(len({entry['id'] for entry in ENTRIES}),len(ENTRIES))
        for entry in ENTRIES:
            paper=entry['source']['paper']
            package=json.loads((ROOT/'processed'/(paper+'.json')).read_text(encoding='utf-8'))
            questions={q['question_number']:q for q in package['questions']}
            self.assertIn(entry['source']['question'],questions)
            self.assertTrue(entry['source']['pages'])
            self.assertTrue(entry['definition'].strip())
            self.assertTrue(set(entry['sections']).issubset(SECTIONS))
        entries={entry['id']:entry for entry in ENTRIES}
        self.assertIn('base case',entries['base-case']['example_answer'].lower())
        self.assertIn('general case',entries['general-case']['example_answer'].lower())
