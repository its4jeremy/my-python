import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import ROOT, SECTIONS, create_app, highlight


class StudyBrowserTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_home_and_topic_counts(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'28 questions available', response.data)
        response = self.client.get('/topics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count(b'data-topic='), 15)
        self.assertIn(b'data-count="4"', response.data)

    def test_all_topic_pages_and_total(self):
        total = 0
        for section in SECTIONS:
            response = self.client.get('/topics/' + section)
            self.assertEqual(response.status_code, 200)
            total += response.data.count(b'<article')
        self.assertEqual(total, 28)
        self.assertIn(b'No questions have been added', self.client.get('/topics/13.2').data)

    def test_answer_content(self):
        response = self.client.get('/topics/13.1')
        self.assertIn(b'<mark>DECLARE</mark>', response.data)
        self.assertIn(b'Common mistakes', response.data)
        self.assertIn(b'<details>', response.data)
        self.assertIn(b'1 mark', response.data)

    def test_search_matches_database(self):
        with sqlite3.connect(ROOT / 'pastpapers.db') as db:
            expected = db.execute("SELECT count(*) FROM questions WHERE question_text LIKE '%recursion%'").fetchone()[0]
        self.assertGreater(expected, 0)
        response = self.client.get('/search', query_string={'q': 'recursion'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count(b'<article'), expected)
        for query in ['%', '_', "' OR 1=1 --", 'nonexistentkeyword', '<script>alert(1)</script>']:
            response = self.client.get('/search', query_string={'q': query})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'<script>alert(1)</script>', response.data)
            self.assertNotIn(b'<article', response.data)
        self.assertNotIn(b'<article', self.client.get('/search').data)

    def test_topic_search_stays_in_section(self):
        response = self.client.get('/topics/13.1?q=ClubMember')
        self.assertIn(b'ClubMember', response.data)
        self.assertIn(b'<article', response.data)
        self.assertNotIn(b'<article', self.client.get('/topics/13.2?q=ClubMember').data)

    def test_invalid_selection_and_assets(self):
        self.assertEqual(self.client.get('/topics/99.9').status_code, 404)
        self.assertEqual(self.client.get('/topics?subject=other').status_code, 400)
        self.assertEqual(self.client.get('/topics?paper=1').status_code, 400)
        for asset in ['style.css', 'filters.js']:
            response = self.client.get('/static/' + asset)
            self.assertEqual(response.status_code, 200)
            response.close()

    def test_database_is_read_only_and_missing_database_is_not_created(self):
        before = (ROOT / 'pastpapers.db').read_bytes()
        self.client.get('/topics')
        self.assertEqual(before, (ROOT / 'pastpapers.db').read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.db'
            self.assertEqual(create_app(path).test_client().get('/').status_code, 503)
            self.assertFalse(path.exists())

    def test_highlight_escapes_markup_and_handles_overlaps(self):
        result = str(highlight('<script>DECLARE A+B</script>', ['DECLARE', 'A+B', 'A']))
        self.assertNotIn('<script>', result)
        self.assertIn('<mark>A+B</mark>', result)
        self.assertIn('&lt;script&gt;', result)


if __name__ == '__main__':
    unittest.main()
