"""Create shared page images so extracted text does not lose diagrams or formatting."""
import hashlib
import json
from pathlib import Path
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parent


def render_sources() -> dict:
    destination=ROOT/'static'/'source_pages'
    destination.mkdir(exist_ok=True)
    catalog={}
    existing={p.name for p in destination.glob('*.webp')}
    for path in sorted((ROOT/'processed').glob('*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        item={}
        for kind in ('qp','ms'):
            pages=sorted({p for q in data['questions'] for p in q[kind+'_pages']})
            document=pdfium.PdfDocument(str(ROOT/data[kind]))
            images={}
            for number in pages:
                page=document[number-1]
                width,height=page.get_size()
                bitmap=page.render(scale=1.5)
                image=bitmap.to_pil()
                bottom_margin=90 if width>height else 65
                image=image.crop((int(35*1.5),int(55*1.5),int((width-30)*1.5),int((height-bottom_margin)*1.5))).convert('RGB')
                # Share byte-identical visual pages across papers and variants.
                name=hashlib.sha256(str(image.size).encode()+image.tobytes()).hexdigest()+'.webp'
                if name not in existing:
                    image.save(destination/name,format='WEBP',quality=85)
                    existing.add(name)
                images[str(number)]='source_pages/'+name
                bitmap.close();page.close()
            document.close()
            item[kind]=dict(path=data[kind],pages=images)
        catalog[data['paper']]=item
        print(data['paper'],len(existing),'unique page images',flush=True)
    (ROOT/'source_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return catalog


if __name__=='__main__':
    render_sources()
