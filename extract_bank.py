"""Extract source text and question identities locally, without API calls."""
import json
import re
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parent
NUMBER = re.compile(r'^\d+(?:\([a-z]+\)|\(\d+\))*$')


def scheme(path: Path) -> dict:
    answers, last = {}, None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            seen = set()
            for table in page.find_tables():
                headings = {str(cell).strip() for row in table.extract()[:4] for cell in row if cell}
                if not {'Question', 'Answer', 'Marks'}.issubset(headings) and not (table.bbox[0] < 80 and table.bbox[2] - table.bbox[0] > page.width * .7):
                    continue
                for row in table.rows:
                    cells = []
                    for cell in row.cells:
                        if cell:
                            text = page.crop(cell).extract_text() or ''
                            if text.strip():
                                cells.append(text.strip())
                    if not cells:
                        continue
                    signature = tuple(cells)
                    if signature in seen:
                        continue
                    seen.add(signature)
                    number = re.sub(r'\s+', '', cells[0])
                    if not NUMBER.fullmatch(number) or not 1 <= int(number.split('(')[0]) <= 20:
                        continue
                    if len(cells) < 3 or not re.match(r'^\d{1,2}(?:\n|$)', cells[2]):
                        # Continuations may repeat the number without a marks cell.
                        if number in answers and len(cells) > 1:
                            answers[number]['answer'] += '\n' + cells[1]
                            answers[number]['pages'].append(page.page_number)
                        continue
                    answer, marks = cells[1], int(cells[2].splitlines()[0])
                    guidance = '\n'.join(cells[3:])
                    if number in answers:
                        if answer != answers[number]['answer']:
                            answers[number]['answer'] += '\n' + answer
                        if guidance:
                            answers[number]['guidance'] += '\n' + guidance
                        answers[number]['pages'].append(page.page_number)
                    else:
                        answers[number] = dict(answer=answer, marks=marks, guidance=guidance, pages=[page.page_number])
                    last = number
    for value in answers.values():
        value['pages'] = sorted(set(value['pages']))
    return answers


def question_nodes(path: Path) -> dict:
    """Read labels in the left margin; preserve inherited question context."""
    nodes, main, letter, current = {}, None, None, None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[1:]:
            if 'BLANK PAGE' in (page.extract_text() or ''):
                continue
            lines = page.crop((35, 45, page.width-30, page.height-55)).extract_text_lines(layout=False, return_chars=False)
            for line in lines:
                text = line['text'].strip()
                if any(text.startswith(prefix) for prefix in ('Permission to reproduce', 'Cambridge International Education', 'Copyright acknowledgements', '©', 'Trace ID:', 'Re-uploading', 'Licensed for', 'Downloaded from')):
                    break
                text = re.sub(r'(?:\(cid:\d+\))', '', text).replace('\ufffd', '')
                if not text.strip() or (text.isdigit() and line['x0'] > 150):
                    continue
                x = line['x0']
                new_main = re.match(r'^(\d{1,2})(?:\s+(.*))?$', text) if x < 65 else None
                if new_main and int(new_main[1]) < 20:
                    main, letter, current = new_main[1], None, new_main[1]
                    text = new_main[2] or ''
                    nodes.setdefault(current, {'text': [], 'pages': []})
                    x = 72
                marker = re.match(r'^\(([a-z]+)\)\s*(.*)', text) if x < 110 else None
                if marker and main:
                    part = marker[1]
                    if x < 85 and len(part) == 1:
                        letter = part
                        current = main + '(' + part + ')'
                    elif letter and re.fullmatch(r'i|ii|iii|iv|v|vi|vii|viii|ix|x', part):
                        current = main + '(' + letter + ')(' + part + ')'
                    else:
                        marker = None
                    if marker:
                        text = marker[2]
                        nested = re.match(r'^\((i|ii|iii|iv|v|vi)\)\s*(.*)', text)
                        if nested:
                            current += '(' + nested[1] + ')'
                            text = nested[2]
                        nodes.setdefault(current, {'text': [], 'pages': []})
                if current:
                    # Answer-space dots are formatting, not question content.
                    text = re.sub(r'\.{5,}', '', text).strip()
                    if text:
                        nodes[current]['text'].append(text)
                    nodes[current]['pages'].append(page.page_number)
    return nodes


def extract_pair(qp: Path, ms: Path) -> dict:
    nodes, answers = question_nodes(qp), scheme(ms)
    output, missing = [], []
    for number, answer in answers.items():
        if number not in nodes:
            missing.append(number)
            continue
        ancestors = [number[:m.end()] for m in re.finditer(r'^\d+|\([^)]+\)', number)]
        text, pages = [], []
        for ancestor in ancestors:
            node = nodes.get(ancestor)
            if node:
                text.extend(node['text'])
                pages.extend(node['pages'])
        output.append(dict(question_number=number, question_text='\n'.join(text),
                           mark_scheme=answer['answer'], guidance=answer['guidance'],
                           marks=answer['marks'], qp_pages=sorted(set(pages)), ms_pages=answer['pages']))
    return dict(questions=output, missing=missing, ms_count=len(answers), mark_total=sum(a['marks'] for a in answers.values()), nodes=list(nodes))


if __name__ == '__main__':
    manifest = json.loads((ROOT/'paper_bank_manifest.json').read_text(encoding='utf-8'))
    destination = Path('/tmp/pastpaper-extraction')
    destination.mkdir(exist_ok=True)
    for pair in manifest['pairs']:
        result = extract_pair(ROOT/pair['qp'], ROOT/pair['ms'])
        (destination/(pair['paper']+'.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(pair['paper'], 'questions',result['ms_count'], 'marks',result['mark_total'], 'unmatched',result['missing'], flush=True)
