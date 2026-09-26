"""Movie test disc: a numbered build (default 0.1.23) with /MOVIE0/MOVIE002.PSS swapped for the English-subtitled remux. Dry-run unless --write.

The remuxed file is exactly as long as the original, so it is written over the original extent and no
filesystem record, file offset or other byte of the disc changes. Kept apart from the numbered text builds
because a movie the game cannot play would freeze the prologue.
"""
import argparse
import hashlib
import json
import shutil
from build_ui_patch import ROOT, iso_files, require

BASE = ROOT/'work/output/ACE3-English-0.1.23.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.23-movie-test.iso'
MOVIE = ROOT/'work/build/movie_test/MOVIE002_en.PSS'
NAME = '/MOVIE0/MOVIE002.PSS'
CHUNK = 8*1024*1024


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true')
    ap.add_argument('--base', default='0.1.23', help='numbered build to take everything except the movie from')
    a = ap.parse_args()
    global BASE, OUTPUT
    BASE = ROOT/('work/output/ACE3-English-%s.iso' % a.base); OUTPUT = ROOT/('work/output/ACE3-English-%s-movie-test.iso' % a.base)
    with BASE.open('rb') as f: entry = iso_files(f)[NAME]
    require(MOVIE.stat().st_size == entry['size'], 'Remuxed movie must be exactly the original size')
    print('DRY RUN', {'file':NAME, 'offset':entry['offset'], 'size':entry['size'], 'output':OUTPUT.name})
    if not a.write: return
    require(not OUTPUT.exists(), 'Output already exists')
    shutil.copyfile(BASE, OUTPUT)
    with OUTPUT.open('r+b') as out, MOVIE.open('rb') as movie:
        out.seek(entry['offset']); shutil.copyfileobj(movie, out, CHUNK)
    # Whole-disc check: identical to the base everywhere except the movie extent, which equals the new file.
    digest = hashlib.sha256(); position = 0; start, end = entry['offset'], entry['offset']+entry['size']
    with BASE.open('rb') as base, OUTPUT.open('rb') as out, MOVIE.open('rb') as movie:
        while True:
            a_raw, b_raw = base.read(CHUNK), out.read(CHUNK)
            if not b_raw: break
            require(len(a_raw) == len(b_raw), 'Size changed')
            expected = bytearray(a_raw)
            lo, hi = max(position, start), min(position+len(b_raw), end)
            if lo < hi:
                movie.seek(lo-start); expected[lo-position:hi-position] = movie.read(hi-lo)
            require(bytes(expected) == b_raw, 'Unexpected change near offset %d' % position)
            digest.update(b_raw); position += len(b_raw)
    report = {'base':BASE.name, 'output':OUTPUT.name, 'sha256':digest.hexdigest(), 'size':position, 'replaced_file':NAME,
              'movie_sha256':hashlib.sha256(MOVIE.read_bytes()).hexdigest(), 'whole_disc_verified':True, 'runtime_verified':False}
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
