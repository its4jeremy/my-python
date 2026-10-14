"""Read-only study browser. Run with python app.py."""
import json
import re
import sqlite3
from pathlib import Path

from flask import Flask, abort, g, render_template, request
from markupsafe import Markup, escape

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
        rows = [dict(row) for row in db().execute(sql + ' ORDER BY id', params)]
        for row in rows:
            row['key_phrases'] = parse_list(row['key_phrases'])
            row['common_mistakes'] = parse_list(row['common_mistakes'])
            row['highlighted_scheme'] = highlight(row['mark_scheme'], row['key_phrases'])
        return rows

    @app.route('/')
    def home() -> str:
        return render_template('home.html', total=len(questions()))

    @app.route('/topics')
    def topics() -> str:
        rows = questions()
        counts = {section: sum(q['syllabus_section'] == section for q in rows) for section in SECTIONS}
        return render_template('topics.html', sections=SECTIONS, counts=counts, total=len(rows))

    @app.route('/topics/<section>')
    def topic(section: str) -> str:
        if section not in SECTIONS:
            abort(404)
        query = request.args.get('q', '').strip()
        return render_template('questions.html', title=SECTIONS[section], section=section,
                               questions=questions(section, query), query=query)

    @app.route('/search')
    def search() -> str:
        query = request.args.get('q', '').strip()
        return render_template('questions.html', title='Search questions', section=None,
                               questions=questions(query=query) if query else [], query=query)

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
