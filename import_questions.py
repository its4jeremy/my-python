"""Import reviewed pipeline JSON atomically; skip identical questions, reject conflicts."""
import argparse
import json
import re
import sqlite3
from pathlib import Path

FIELDS = ('syllabus_section', 'question_number', 'topic', 'subtopic', 'question_text',
          'mark_scheme', 'key_phrases', 'common_mistakes', 'marks')
SEASONS = {'s': 'May/June', 'w': 'October/November', 'm': 'February/March'}


def canonical_key(row: dict) -> tuple[str, ...]:
    aliases = {'oct/nov': 'october/november', 'may/june': 'may/june',
               'feb/mar': 'february/march'}
    season = str(row['season']).strip().lower()
    return (str(row['paper_code']).strip(), str(row['year']).strip(),
            aliases.get(season, season), str(row['paper_number']).strip(),
            re.sub(r'\s+', '', str(row['question_number'])).lower())


def payload(row: dict) -> tuple:
    values = []
    for field in FIELDS:
        if field == 'question_number':
            continue
        value = row[field]
        if field in ('key_phrases', 'common_mistakes') and isinstance(value, str):
            value = json.loads(value)
        values.append(value)
    return tuple(values)


def import_questions(database: Path, questions: list[dict], paper: str) -> dict:
    match = re.fullmatch(r'(9618)_([swm])(\d{2})_(3\d)', paper)
    if not match:
        raise ValueError('Paper must identify a Paper 3 variant, e.g. 9618_w25_31')
    code, season, year, number = match.groups()
    prepared = []
    for question in questions:
        if not isinstance(question, dict) or any(field not in question for field in FIELDS):
            raise ValueError('Every question must contain all pipeline fields')
        if not isinstance(question['question_number'], str) or not question['question_number'].strip():
            raise ValueError('Question number is required')
        for field in ('key_phrases', 'common_mistakes'):
            if not isinstance(question[field], list) or not all(isinstance(v, str) for v in question[field]):
                raise ValueError(f'{field} must be a list of strings')
        row = {field: question[field] for field in FIELDS}
        row.update(paper_code=code, year='20' + year, season=SEASONS[season], paper_number=number)
        prepared.append(row)
    connection = sqlite3.connect(database.resolve().as_uri() + '?mode=rw', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        # Lock before duplicate detection; concurrent importers cannot race inserts.
        connection.execute('BEGIN IMMEDIATE')
        existing = {}
        for stored in connection.execute('SELECT * FROM questions'):
            row = dict(stored)
            key = canonical_key(row)
            if key in existing:
                raise ValueError('Database already contains duplicate question identities; review required')
            existing[key] = payload(row)
        new, skipped = [], 0
        for row in prepared:
            key, content = canonical_key(row), payload(row)
            if key in existing:
                if existing[key] != content:
                    raise ValueError(f'Conflicting answer for {paper} question {row["question_number"]}; import rolled back')
                skipped += 1
            else:
                existing[key] = content
                new.append(row)
        connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS unique_paper_question ON questions (paper_code, year, season, paper_number, question_number)')
        columns = ('paper_code', 'year', 'season', 'paper_number') + FIELDS
        for row in new:
            values = [json.dumps(row[col], ensure_ascii=False) if col in ('key_phrases', 'common_mistakes') else row[col] for col in columns]
            connection.execute(f'INSERT INTO questions ({", ".join(columns)}) VALUES ({", ".join("?" for _ in columns)})', values)
        connection.commit()
        return {'inserted': len(new), 'skipped': skipped}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('json_file', type=Path)
    parser.add_argument('--paper', required=True)
    parser.add_argument('--database', type=Path, default=Path(__file__).resolve().parent / 'pastpapers.db')
    args = parser.parse_args()
    data = json.loads(args.json_file.read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError('JSON must contain a list of questions')
    print(import_questions(args.database, data, args.paper))
