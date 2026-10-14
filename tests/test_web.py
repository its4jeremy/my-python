import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from html.parser import HTMLParser

from app import ROOT, SECTIONS, create_app, highlight
from glossary import ENTRIES, annotate


class HTMLAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.described = []
        self.sources = []
        self.occurrences = []
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if 'aria-describedby' in attrs:
            self.described.append(attrs['aria-describedby'])
        if tag == 'article' and 'data-occurrences' in attrs:
            self.occurrences.append(int(attrs['data-occurrences']))
        if tag == 'a' and attrs.get('href','').startswith('/sources/'):
            self.sources.append(attrs['href'])
        if tag == 'img' and 'data-src' in attrs:
            self.assets.append(attrs['data-src'])


class StudyBrowserTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def page_audit(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code,200,url)
        parser = HTMLAudit(); parser.feed(response.get_data(as_text=True))
        self.assertEqual(len(parser.ids),len(set(parser.ids)),url)
        self.assertTrue(set(parser.described).issubset(parser.ids),url)
        return response, parser

    def test_home_and_topic_counts(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'858 exam occurrences across 32 papers', response.data)
        self.assertNotIn(b'AI-processed study material',response.data)
        response = self.client.get('/topics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count(b'data-topic='), 15)
        self.assertNotIn(b'data-count="0"',response.data)

    def test_paginated_topic_coverage_and_accessibility(self):
        occurrence_count, distinct = 0, 0
        question_ids = set()
        for section in SECTIONS:
            first = self.client.get('/topics/' + section).get_data(as_text=True)
            pages = int(re.search(r'Page 1 of (\d+)',first)[1])
            for page in range(1,pages+1):
                response,audit = self.page_audit(f'/topics/{section}?page={page}')
                occurrence_count += sum(audit.occurrences)
                distinct += len(audit.occurrences)
                ids = {i for i in audit.ids if i.startswith('question-') and not re.search(r'-\d+-\d+$',i)}
                self.assertFalse(ids.intersection(question_ids))
                question_ids.update(ids)
                self.assertLessEqual(len(audit.occurrences),20)
                self.assertTrue(audit.sources)
        with sqlite3.connect(ROOT/'pastpapers.db') as db:
            expected=db.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
        self.assertEqual(occurrence_count,expected)
        self.assertLess(distinct,occurrence_count)

    def test_answers_explanations_and_original_layouts(self):
        response,audit = self.page_audit('/topics/19.2')
        self.assertIn(b'Base case',response.data)
        self.assertIn(b'role="tooltip"',response.data)
        self.assertIn(b'<mark>',response.data)
        self.assertIn(b'Original question layout',response.data)
        self.assertIn(b'Reveal mark scheme',response.data)
        image = self.client.get(audit.assets[0]);self.assertEqual(image.status_code,200);image.close()

    def test_search_and_year_filters(self):
        for query in ["' OR 1=1 --", 'nonexistentkeyword', '<script>alert(1)</script>']:
            response = self.client.get('/search',query_string={'q':query})
            self.assertEqual(response.status_code,200)
            self.assertNotIn(b'<script>alert(1)</script>',response.data)
            self.assertNotIn(b'<article',response.data)
        response,audit=self.page_audit('/search?q=%25')
        with sqlite3.connect(ROOT/'pastpapers.db') as db:
            literal_matches=db.execute("SELECT COUNT(*) FROM questions WHERE instr(question_text, '%') > 0").fetchone()[0]
        self.assertEqual(sum(audit.occurrences),literal_matches)
        response=self.client.get('/search?q=recursion')
        self.assertIn(b'<article',response.data)
        self.assertNotIn(b'<article',self.client.get('/search').data)
        response=self.client.get('/topics/13.1?year=2025')
        self.assertIn(b'<article',response.data)
        self.assertNotIn(b'2024',re.sub(rb'<option.*?</option>',b'',response.data))
        self.assertNotIn(b'<article',self.client.get('/topics/13.1?year=1900').data)

    def test_topic_search_stays_in_section(self):
        self.assertIn(b'<article',self.client.get('/topics/13.1?q=ClubMember').data)
        self.assertNotIn(b'<article',self.client.get('/topics/13.2?q=ClubMember').data)

    def test_source_references_and_glossary(self):
        catalog=json.loads((ROOT/'source_catalog.json').read_text(encoding='utf-8'))
        for paper in catalog:
            for kind in ('qp','ms'):
                response=self.client.get(f'/sources/{paper}/{kind}')
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.mimetype,'application/pdf')
                self.assertTrue(response.data.startswith(b'%PDF-'));response.close()
        for name in ['syllabus','pseudocode']:
            response=self.client.get('/references/'+name)
            self.assertEqual(response.status_code,200);response.close()
        response,audit=self.page_audit('/glossary')
        self.assertEqual(response.data.count(b'class="card glossary-entry"'),len(ENTRIES))
        filtered=self.client.get('/glossary?q=base+case')
        self.assertIn(b'id="base-case"',filtered.data)
        self.assertIn(b'id="stopping-condition"',filtered.data)
        self.assertLess(filtered.data.count(b'class="card glossary-entry"'),len(ENTRIES))
        self.assertIn(b'&lt;script&gt;',self.client.get('/glossary?q=%3Cscript%3E').data)

    def test_invalid_selection_pagination_and_assets(self):
        self.assertEqual(self.client.get('/topics/99.9').status_code,404)
        self.assertEqual(self.client.get('/topics?subject=other').status_code,400)
        self.assertEqual(self.client.get('/topics?paper=1').status_code,400)
        self.assertEqual(self.client.get('/sources/not-a-paper/ms').status_code,404)
        self.assertEqual(self.client.get('/sources/9618_w25_31/nope').status_code,404)
        for page in ['invalid','-1','99999']:
            self.assertEqual(self.client.get('/topics/13.1?page='+page).status_code,200)
        for asset in ['style.css','filters.js','glossary.js']:
            response=self.client.get('/static/'+asset)
            self.assertEqual(response.status_code,200);response.close()

    def test_database_is_read_only_and_missing_database_is_not_created(self):
        before=(ROOT/'pastpapers.db').read_bytes()
        self.client.get('/topics')
        self.assertEqual(before,(ROOT/'pastpapers.db').read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'missing.db'
            self.assertEqual(create_app(path).test_client().get('/').status_code,503)
            self.assertFalse(path.exists())

    def test_glossary_boundaries_scopes_and_escaping(self):
        result=str(annotate('<script>Base case and stopping condition</script>', ['Base case'],'19.2','test'))
        self.assertNotIn('<script>',result)
        self.assertIn('&lt;script&gt;',result)
        self.assertIn('<mark>',result)
        self.assertIn('role="tooltip"',result)
        self.assertNotIn('role="tooltip"',str(annotate('Base case',[],'13.3','test')))
        self.assertNotIn('role="tooltip"',str(annotate('Set up a variable',[],'13.1','test')))
        text=str(annotate('asymmetric encryption',[],'17.1','test'))
        self.assertIn('Asymmetric encryption',text)
        self.assertNotIn('<strong>Symmetric encryption</strong>',text)
        result=str(highlight('<script>DECLARE A+B</script>',['DECLARE','A+B','A']))
        self.assertIn('<mark>A+B</mark>',result)
        self.assertNotIn('<script>',result)
