"""Build the reviewed Paper 3 collection; reruns reuse verified extraction caches."""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from app import SECTIONS
from extract_bank import extract_pair
from import_questions import import_questions

ROOT = Path(__file__).resolve().parent
CATEGORIES = {'13': 'Data Representation', '14': 'Communication and internet technologies',
              '15': 'Hardware and Virtual Machines', '16': 'System Software', '17': 'Security',
              '18': 'Artificial Intelligence', '19': 'Computational thinking and Problem-solving',
              '20': 'Further Programming'}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section_for(paper: str, number: str, mapping: dict) -> str:
    base = paper.rsplit('_', 1)[0]
    group = paper if paper in mapping else base
    return mapping['overrides'].get(group + ':' + number,
            mapping[group][int(number.split('(')[0]) - 1])


def build(cache: Path | None = None) -> dict:
    manifest = json.loads((ROOT/'paper_bank_manifest.json').read_text(encoding='utf-8'))
    mapping = json.loads((ROOT/'topic_map.json').read_text(encoding='utf-8'))
    glossary = json.loads((ROOT/'glossary.json').read_text(encoding='utf-8'))
    legacy = json.loads((ROOT/'output.json').read_text(encoding='utf-8'))
    legacy = {q['question_number']: q for q in legacy}
    processed = ROOT/'processed'
    processed.mkdir(exist_ok=True)
    packages = []
    for pair in manifest['pairs']:
        paper = pair['paper']
        hashes = {kind: file_hash(ROOT/pair[kind]) for kind in ('qp', 'ms')}
        target = processed/(paper+'.json')
        if target.exists():
            package = json.loads(target.read_text(encoding='utf-8'))
            if package['sha256'] != hashes:
                raise ValueError(f'Source changed for {paper}; review before rebuilding')
        else:
            if cache and (cache/(paper+'.json')).exists():
                result = json.loads((cache/(paper+'.json')).read_text(encoding='utf-8'))
            else:
                result = extract_pair(ROOT/pair['qp'], ROOT/pair['ms'])
            if result['missing'] or result['mark_total'] != 75 or result['ms_count'] != len(result['questions']):
                raise ValueError(f'Incomplete extraction: {paper}')
            questions = []
            for item in result['questions']:
                number = item['question_number']
                if not item['question_text'].strip() or not item['mark_scheme'].strip():
                    raise ValueError(f'Missing source text: {paper} {number}')
                marks = re.findall(r'\[(\d{1,2})\]', item['question_text'])
                if not marks or int(marks[-1]) != item['marks']:
                    raise ValueError(f'Question and scheme marks disagree: {paper} {number}')
                section = section_for(paper, number, mapping)
                if section not in SECTIONS:
                    raise ValueError(f'Unmapped section: {paper} {number}')
                phrases = []
                for entry in glossary:
                    if section not in entry['sections']:
                        continue
                    for alias in [entry['term']] + entry['aliases']:
                        match = re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', item['mark_scheme'], re.I)
                        if match:
                            phrases.append(match.group()); break
                row = {key: item[key] for key in ('question_number','question_text','mark_scheme','marks')}
                row.update(syllabus_section=section, topic=CATEGORIES[section.split('.')[0]],
                           subtopic=SECTIONS[section], key_phrases=phrases,
                           common_mistakes=[item['guidance']] if item['guidance'].strip() else [],
                           qp_pages=item['qp_pages'], ms_pages=item['ms_pages'])
                if paper == '9618_w25_31':
                    # Retain the already reviewed original answers and identity fields.
                    original = legacy[number]
                    row.update(original)
                questions.append(row)
            package = dict(paper=paper, qp=pair['qp'], ms=pair['ms'], sha256=hashes,
                           extraction='Local PDF text; original page layouts retained separately',
                           questions=questions, marks=75)
            target.write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if len({q['question_number'] for q in package['questions']}) != len(package['questions']):
            raise ValueError(f'Duplicate identities in {paper}')
        packages.append(package)
    # The full collection passes preflight before any database import starts.
    report = {'papers': [], 'inserted': 0, 'skipped': 0}
    for package in packages:
        result = import_questions(ROOT/'pastpapers.db', package['questions'], package['paper'])
        report['papers'].append(dict(paper=package['paper'], questions=len(package['questions']), **result))
        report['inserted'] += result['inserted']; report['skipped'] += result['skipped']
    with sqlite3.connect(ROOT/'pastpapers.db') as db:
        report['database_questions'] = db.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Database integrity check failed')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extraction-cache', type=Path)
    args = parser.parse_args()
    report = build(args.extraction_cache)
    (ROOT/'bank_import_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"Papers: {len(report['papers'])}; inserted: {report['inserted']}; skipped: {report['skipped']}; database total: {report['database_questions']}")
