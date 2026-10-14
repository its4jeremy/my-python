"""Reviewed, topic-aware explanations with safe inline annotation."""
import json
import re
from pathlib import Path
from markupsafe import Markup, escape

ENTRIES = json.loads((Path(__file__).resolve().parent/'glossary.json').read_text(encoding='utf-8'))


def annotate(text: str | None, phrases: list[str], section: str, prefix: str) -> Markup:
    text = (text or '').replace('\uf0ac', '←')
    aliases = {}
    for entry in ENTRIES:
        if section in entry['sections']:
            names = [entry['term']] + entry['aliases']
            if entry['term'] == 'Set':
                names = entry['aliases']  # Avoid treating the verb "set" as a data type.
            for alias in names:
                aliases[alias.lower()] = entry
    terms = re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(a) for a in sorted(aliases,key=len,reverse=True))+r')(?!\w)',re.I) if aliases else None
    seen, counter = set(), 0

    def term_markup(chunk: str) -> Markup:
        nonlocal counter
        if terms is None:
            return escape(chunk)
        parts, end = [], 0
        for match in terms.finditer(chunk):
            entry = aliases[match.group().lower()]
            if entry['id'] in seen:
                continue
            seen.add(entry['id']); counter += 1
            tip = prefix+'-'+str(counter)
            parts.append(escape(chunk[end:match.start()]))
            parts.append(Markup('<span class="term-wrap"><button type="button" class="glossary-term" aria-describedby="{}" aria-expanded="false" title="{}">{}</button><span class="term-tip" role="tooltip" id="{}" hidden><strong>{}</strong><span>{}</span></span></span>').format(escape(tip),escape(entry['definition']),escape(match.group()),escape(tip),escape(entry['term']),escape(entry['definition'])))
            end = match.end()
        parts.append(escape(chunk[end:]))
        return Markup('').join(parts)

    phrases = sorted({p.strip() for p in phrases if p.strip()},key=len,reverse=True)
    if not phrases:
        return term_markup(text)
    pattern = re.compile('|'.join(re.escape(p) for p in phrases),re.I)
    parts, end = [], 0
    for match in pattern.finditer(text):
        parts.extend([term_markup(text[end:match.start()]),Markup('<mark>'),term_markup(match.group()),Markup('</mark>')])
        end = match.end()
    parts.append(term_markup(text[end:]))
    return Markup('').join(parts)
