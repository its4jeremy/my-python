"""Import paper archives without executing their contents or overwriting conflicts."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

PAPER_NAME = re.compile(r'^(9618)_([swm])(\d{2})_(qp|ms)_([1-4]\d)(?: \(\d+\))?\.pdf$', re.I)
SEASONS = {'s': 'may_jun', 'w': 'oct_nov', 'm': 'feb_mar'}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(name: str) -> tuple[str, ...] | None:
    match = PAPER_NAME.fullmatch(name)
    return tuple(part.lower() for part in match.groups()) if match else None


def import_archive(archive: Path, root: Path) -> dict:
    root = root.resolve()
    known, hashes = {}, {}
    for path in sorted(root.rglob('*.pdf')):
        if not path.resolve().is_relative_to(root):
            raise ValueError(f'PDF symlink escapes repository: {path}')
        data_hash = digest(path.read_bytes())
        key = identity(path.name)
        relative = path.relative_to(root).as_posix()
        if key and key in known and known[key][0] != data_hash:
            raise ValueError(f'Existing conflicting paper identity: {path.name}')
        if key:
            known[key] = (data_hash, relative)
        hashes.setdefault(data_hash, relative)

    report = {'added': [], 'duplicates': [], 'excluded': [], 'pairs': []}
    planned = []
    with ZipFile(archive) as source:
        entries = [entry for entry in source.infolist() if not entry.is_dir()]
        if sum(entry.file_size for entry in entries) > 512 * 1024 * 1024:
            raise ValueError('Archive exceeds the 512 MB uncompressed limit')
        for entry in entries:
            # Destination is derived from a validated basename, never an archive path.
            name = entry.filename.replace('\\', '/').rsplit('/', 1)[-1]
            key = identity(name)
            if key is None or not key[4].startswith('3'):
                report['excluded'].append(entry.filename)
                continue
            data = source.read(entry)
            if not data.startswith(b'%PDF-'):
                raise ValueError(f'Not a PDF: {entry.filename}')
            data_hash = digest(data)
            code, season, year, kind, variant = key
            filename = f'{code}_{season}{year}_{kind}_{variant}.pdf'
            target = Path('papers') / code / 'paper_3' / ('20' + year) / SEASONS[season] / filename
            if key in known:
                previous_hash, previous_path = known[key]
                if data_hash != previous_hash:
                    raise ValueError(f'Conflicting content for {filename}; nothing imported')
                report['duplicates'].append({'source': entry.filename, 'existing': previous_path})
                continue
            if data_hash in hashes:
                raise ValueError(f'Identical content under different paper identities: {filename} and {hashes[data_hash]}')
            known[key] = (data_hash, target.as_posix())
            hashes[data_hash] = target.as_posix()
            planned.append((target, data))
            report['added'].append({'source': entry.filename, 'path': target.as_posix(), 'sha256': data_hash})

    paper_ids = sorted({(code, season, year, variant) for code, season, year, kind, variant in known if variant.startswith('3')})
    for code, season, year, variant in paper_ids:
        pair = {'paper': f'{code}_{season}{year}_{variant}'}
        for kind in ('qp', 'ms'):
            item = known.get((code, season, year, kind, variant))
            pair[kind] = item[1] if item else None
        pair['complete'] = bool(pair['qp'] and pair['ms'])
        report['pairs'].append(pair)

    # Preflight every destination before writing. Refuse any overwrite.
    for target, data in planned:
        destination = root / target
        if not destination.resolve().is_relative_to(root) or destination.exists():
            raise ValueError(f'Unsafe or occupied destination: {target}')
    for target, data in planned:
        destination = root / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as output:
            output.write(data)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = import_archive(args.archive, args.root)
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Added {len(result['added'])}; skipped {len(result['duplicates'])} exact duplicates; excluded {len(result['excluded'])} unrelated files")
    print(f"Complete pairs: {sum(pair['complete'] for pair in result['pairs'])}/{len(result['pairs'])}")
