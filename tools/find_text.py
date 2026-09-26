"""Find every copy of a piece of text on a disc image, in several encodings. Read-only; prints locations only.

usage: python find_text.py <iso path or 'original'> <text> [<text> ...]
The scan always starts at byte 0 and overlaps chunk borders; each hit is mapped to its file and, inside
DATA.BIN, to its resource ID.
"""
import sys
from build_ui_patch import ROOT, iso_files
from dialogue_corpus import archive

ENCODINGS = ('cp932', 'utf-16-le', 'utf-16-be', 'utf-8', 'euc_jp')
CHUNK = 64*1024*1024


def search(path, texts):
    needles = {}
    for text in texts:
        for enc in ENCODINGS:
            try: needles[(text, enc)] = text.encode(enc)
            except UnicodeEncodeError: pass
    overlap = max(len(n) for n in needles.values())
    hits = set()
    with path.open('rb') as f:
        files = iso_files(f); info, entries = archive(f)
        f.seek(0); position = 0; tail = b''
        while True:
            raw = f.read(CHUNK)
            if not raw: break
            buf = tail+raw; start = position-len(tail)
            for key, needle in needles.items():
                at = buf.find(needle)
                while at >= 0:
                    hits.add((start+at, key)); at = buf.find(needle, at+1)
            tail = buf[-overlap:]; position += len(raw)
    out = []
    for offset, (text, enc) in sorted(hits):
        name = next((k for k, v in files.items() if v['offset'] <= offset < v['offset']+v['size']), '(outside any file)')
        resource = None
        if name == '/DATA.BIN':
            resource = next((rid for _, size, off, rid in entries if info['offset']+off <= offset < info['offset']+off+size), None)
        out.append({'offset':offset, 'file':name, 'resource':resource, 'encoding':enc, 'text_index':texts.index(text)})
    return out, position


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    path = next(ROOT.glob('*.iso')) if sys.argv[1] == 'original' else ROOT/sys.argv[1]
    hits, scanned = search(path, sys.argv[2:])
    print('scanned bytes', scanned, 'of', path.stat().st_size, '-', len(hits), 'hits')
    for h in hits: print(h)


if __name__ == '__main__': main()
