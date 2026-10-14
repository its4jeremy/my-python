"""Read-only study browser. Run with python app.py."""
import json
import re
import sqlite3
import math
import unicodedata
from pathlib import Path

from flask import Flask, abort, g, render_template, request, send_file, url_for
from markupsafe import Markup, escape
from glossary import ENTRIES, annotate

ROOT = Path(__file__).resolve().parent
SECTIONS = {
    '13.1': 'User-defined data types',
    '13.2': 'File organisation and access',
    '13.3': 'Floating-point numbers',
    '14.1': 'Protocols',
    '14.2': 'Circuit switching and packet switching',
    '15.1': 'Processors, Parallel Processing and Virtual Machines',
    '15.2': 'Boolean Algebra and Logic Circuits',
    '16.1': 'Purposes of an Operating System',
    '16.2': 'Translation Software',
    '17.1': 'Encryption, Encryption Protocols and Digital Certificates',
    '18.1': 'Artificial Intelligence',
    '19.1': 'Algorithms',
    '19.2': 'Recursion',
    '20.1': 'Programming Paradigms',
    '20.2': 'File Processing and Exception Handling',
}


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        result = json.loads(value)
    except (ValueError, TypeError):
        return [str(value)]
    return [str(item) for item in result] if isinstance(result, list) else [str(result)]


def highlight(text: str | None, phrases: list[str]) -> Markup:
    """Escape all source text before adding trusted highlight tags."""
    text = text or ''
    phrases = sorted({p.strip() for p in phrases if p.strip()}, key=len, reverse=True)
    if not phrases:
        return escape(text)
    pattern = re.compile('|'.join(re.escape(p) for p in phrases), re.IGNORECASE)
    parts, end = [], 0
    for match in pattern.finditer(text):
        parts.extend([escape(text[end:match.start()]), Markup('<mark>'),
                      escape(match.group()), Markup('</mark>')])
        end = match.end()
    parts.append(escape(text[end:]))
    return Markup('').join(parts)


def create_app(database_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    app.config['DATABASE'] = str(database_path or ROOT / 'pastpapers.db')

    catalog = json.loads((ROOT/'source_catalog.json').read_text(encoding='utf-8'))
    metadata = {}
    for path in (ROOT/'processed').glob('*.json'):
        package = json.loads(path.read_text(encoding='utf-8'))
        for item in package['questions']:
            metadata[(package['paper'], item['question_number'])] = item

    def db() -> sqlite3.Connection:
        if 'db' not in g:
            path = Path(app.config['DATABASE']).resolve()
            # Never create an empty database or import database.py (which inserts rows).
            g.db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(error: BaseException | None) -> None:
        connection = g.pop('db', None)
        if connection is not None:
            connection.close()

    def selection() -> tuple[str, str]:
        subject = request.args.get('subject', '9618')
        paper = request.args.get('paper', '3')
        if subject != '9618' or paper != '3':
            abort(400, description='Only Computer Science 9618 Paper 3 is currently available.')
        return subject, paper

    def questions(section: str | None = None, query: str = '') -> list[dict]:
        subject, paper = selection()
        sql = 'SELECT * FROM questions WHERE paper_code = ? AND (paper_number = ? OR paper_number GLOB ?)'
        params = [subject, paper, paper + '[0-9]']
        if section:
            sql += ' AND syllabus_section = ?'
            params.append(section)
        if query:
            sql += " AND question_text LIKE ? ESCAPE '\\'"
            literal = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            params.append('%' + literal + '%')
        year = request.args.get('year', '').strip()
        if year:
            sql += ' AND year = ?'
            params.append(year)
        rows = [dict(row) for row in db().execute(sql + ' ORDER BY CAST(year AS INTEGER) DESC, season, paper_number, id', params)]
        for row in rows:
            row['key_phrases'] = parse_list(row['key_phrases'])
            row['common_mistakes'] = parse_list(row['common_mistakes'])
            row['highlighted_scheme'] = annotate(row['mark_scheme'], row['key_phrases'], row['syllabus_section'], f"scheme-{row['id']}")
            row['annotated_question'] = annotate(row['question_text'], [], row['syllabus_section'], f"question-{row['id']}")
            season = {'October/November': 'w', 'May/June': 's', 'February/March': 'm'}.get(row['season'])
            paper_id = f"{row['paper_code']}_{season}{str(row['year'])[-2:]}_{row['paper_number']}"
            row['paper_id'] = paper_id
            item = metadata.get((paper_id, row['question_number']), {})
            row['sources'] = []
            if item and paper_id in catalog:
                row['sources'] = [dict(paper=paper_id, number=row['question_number'],
                    qp_pages=item['qp_pages'], ms_pages=item['ms_pages'])]
            row['layouts'] = {kind: [dict(page=p, image=catalog[paper_id][kind]['pages'][str(p)])
                for p in item.get(kind+'_pages', [])] for kind in ('qp', 'ms')} if paper_id in catalog else {'qp': [], 'ms': []}
        # Merge only when text AND the original visual pages agree. Diagrams that
        # differ are kept separate even if extracted text happens to be identical.
        grouped = {}
        for row in rows:
            normalize = lambda text: ' '.join(unicodedata.normalize('NFKC', text or '').split())
            visuals = tuple(layout['image'] for kind in ('qp','ms') for layout in row['layouts'][kind])
            key = (row['syllabus_section'], row['marks'], normalize(row['question_text']),
                   normalize(row['mark_scheme']), visuals or (row['id'],))
            if key in grouped:
                grouped[key]['sources'].extend(row['sources'])
            else:
                grouped[key] = row
        return list(grouped.values())

    @app.route('/')
    def home() -> str:
        rows = questions()
        years = [str(r[0]) for r in db().execute('SELECT DISTINCT year FROM questions ORDER BY year DESC')]
        total_occurrences = db().execute('SELECT COUNT(*) FROM questions').fetchone()[0]
        return render_template('home.html', total=len(rows), occurrences=total_occurrences,
                               papers=len(catalog), years=years)

    @app.route('/topics')
    def topics() -> str:
        rows = questions()
        counts = {section: sum(q['syllabus_section'] == section for q in rows) for section in SECTIONS}
        return render_template('topics.html', sections=SECTIONS, counts=counts, total=len(rows),
                               year=request.args.get('year',''), years=available_years())

    def available_years() -> list[str]:
        return [str(row[0]) for row in db().execute('SELECT DISTINCT year FROM questions ORDER BY year DESC')]

    def question_page(title: str, section: str | None, query: str, rows: list[dict]) -> str:
        try:
            page = max(1, int(request.args.get('page', 1)))
        except ValueError:
            page = 1
        pages = max(1, math.ceil(len(rows)/20))
        page = min(page, pages)
        links = {key: value for key, value in request.args.items() if key != 'page'}
        endpoint = 'topic' if section else 'search'
        if section:
            links['section'] = section
        return render_template('questions.html', title=title, section=section,
            questions=rows[(page-1)*20:page*20], query=query, total=len(rows), page=page, pages=pages,
            prev_url=url_for(endpoint, **links, page=page-1) if page>1 else None,
            next_url=url_for(endpoint, **links, page=page+1) if page<pages else None,
            year=request.args.get('year',''), years=available_years())

    @app.route('/sources/<paper>/<kind>')
    def source_pdf(paper: str, kind: str):
        if paper not in catalog or kind not in ('qp', 'ms'):
            abort(404)
        return send_file(ROOT/catalog[paper][kind]['path'], mimetype='application/pdf')

    @app.route('/references/<name>')
    def reference_pdf(name: str):
        names = {'syllabus': '9618 2026 syllabus.pdf',
                 'pseudocode': '697401-2026-pseudocode-guide-for-teachers.pdf'}
        if name not in names:
            abort(404)
        return send_file(ROOT/names[name], mimetype='application/pdf')

    @app.route('/glossary')
    def glossary_page() -> str:
        query = request.args.get('q', '').strip()
        entries = [entry for entry in ENTRIES if query.lower() in
                   (' '.join([entry['term'],entry['definition']]+entry['aliases'])).lower()]
        return render_template('glossary.html', entries=sorted(entries,key=lambda e:e['term'].lower()), query=query)

    @app.route('/topics/<section>')
    def topic(section: str) -> str:
        if section not in SECTIONS:
            abort(404)
        query = request.args.get('q', '').strip()
        return question_page(SECTIONS[section], section, query, questions(section, query))

    @app.route('/search')
    def search() -> str:
        query = request.args.get('q', '').strip()
        return question_page('Search questions', None, query, questions(query=query) if query else [])

    @app.errorhandler(400)
    @app.errorhandler(404)
    def page_error(error) -> tuple[str, int]:
        return render_template('error.html', message=error.description), error.code

    @app.errorhandler(sqlite3.Error)
    def database_error(error: sqlite3.Error) -> tuple[str, int]:
        app.logger.error('Database unavailable: %s', error)
        return render_template('error.html', message='The question database is unavailable. Check that pastpapers.db is beside app.py and contains the questions table.'), 503

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
