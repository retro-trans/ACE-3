"""Package 0.1.42's full/update xdelta releases and decode-verify each one.

Run relayout_disc.py ACE3-English-0.1.42.iso first. Default is a dry run.
No ISO or game file is uploaded by this tool.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from build_ui_patch import ROOT, iso_files, require

VERSION = '0.1.42'
DIR = ROOT/'work/release'
ORIGINAL = next(ROOT.glob('*.iso'))
ORIGINAL_SHA = '5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705'
MOVIE = DIR/'ACE3-English-0.1.42-orig-layout.iso'
TEXT = DIR/'ACE3-English-0.1.42-text-orig-layout.iso'
PREVIOUS_TEXT = DIR/'ACE3-English-0.1.35-orig-layout.iso'
PREVIOUS_MOVIE = DIR/'ACE3-English-0.1.35-movie-test-orig-layout.iso'
XDELTA = ROOT/'xdelta3.exe'
MOVIE_FILE = '/MOVIE0/MOVIE002.PSS'
JOBS = [
    ('ACE3-English-0.1.42.xdelta', ORIGINAL, TEXT),
    ('ACE3-English-0.1.42-movie.xdelta', ORIGINAL, MOVIE),
    ('ACE3-English-0.1.35-to-0.1.42.xdelta', PREVIOUS_TEXT, TEXT),
    ('ACE3-English-0.1.35-to-0.1.42-movie.xdelta', PREVIOUS_MOVIE, MOVIE),
]


def digest(path, offset=0, length=None):
    h = hashlib.sha256()
    with path.open('rb') as f:
        f.seek(offset); left = path.stat().st_size-offset if length is None else length
        while left:
            b = f.read(min(8 << 20, left)); require(b, 'Short read')
            h.update(b); left -= len(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    for name, source, target in JOBS:
        print('PLAN', name, 'source:', source.name, 'target:', target.name, flush=True)
    print('Text edition restores only the original prologue movie; every patch is decoded to a SHA-256 stream.', flush=True)
    if not a.write:
        return
    expected = {ORIGINAL: ORIGINAL_SHA,
                PREVIOUS_TEXT: '15f69e6ca194b8f8a58ca8e0cc84b54e946923b1efe732345015a81443f61da3',
                PREVIOUS_MOVIE: 'db226b8474d3b7f833eff553d78743f7f78d20d2cb3cd78e75a67a67a901d70c'}
    meta = json.loads(MOVIE.with_suffix('.json').read_text())
    require(meta['verified'], 'Relayout verification required')
    expected[MOVIE] = meta['sha256']
    for path, sha in expected.items():
        require(digest(path) == sha, 'Source hash mismatch: '+path.name)
        print('Verified source', path.name, flush=True)
    require(not TEXT.exists() and all(not (DIR/n).exists() for n, _, _ in JOBS), 'Release outputs already exist')
    with ORIGINAL.open('rb') as f:
        original_files = iso_files(f)
    with MOVIE.open('rb') as f:
        output_files = iso_files(f)
    original_movie, target_movie = original_files[MOVIE_FILE], output_files[MOVIE_FILE]
    require(original_movie['size'] == target_movie['size'], 'Movie extents differ in size')
    shutil.copyfile(str(MOVIE), str(TEXT))
    with ORIGINAL.open('rb') as src, TEXT.open('r+b') as dst:
        src.seek(original_movie['offset']); dst.seek(target_movie['offset']); left = target_movie['size']
        while left:
            b = src.read(min(left, 8 << 20)); require(b, 'Movie short read'); dst.write(b); left -= len(b)
    # Whole-disc preservation outside the movie extent, plus original movie equality.
    start, length = target_movie['offset'], target_movie['size']
    for offset, size in ((0, start), (start+length, MOVIE.stat().st_size-start-length)):
        require(digest(TEXT, offset, size) == digest(MOVIE, offset, size), 'Non-movie bytes changed')
    require(digest(TEXT, start, length) == digest(ORIGINAL, original_movie['offset'], length), 'Original movie restore failed')
    expected[TEXT] = digest(TEXT)
    print('Verified text edition', expected[TEXT], flush=True)
    assets = []
    for name, source, target in JOBS:
        patch = DIR/name
        print('Encoding', name, flush=True)
        subprocess.run([str(XDELTA), '-e', '-9', '-S', 'djw', '-B', '67108864', '-s', str(source), str(target), str(patch)], check=True)
        print('Decode-verifying', name, flush=True)
        h = hashlib.sha256(); size = 0
        with subprocess.Popen([str(XDELTA), '-d', '-c', '-s', str(source), str(patch)], stdout=subprocess.PIPE) as child:
            while True:
                block = child.stdout.read(8 << 20)
                if not block:
                    break
                h.update(block); size += len(block)
            require(child.wait() == 0, 'Patch decode failed')
        require(h.hexdigest() == expected[target] and size == target.stat().st_size, 'Patch reconstructed the wrong ISO')
        assets.append({'name': name, 'size': patch.stat().st_size, 'sha256': digest(patch),
                       'source_sha256': expected[source], 'source_size': source.stat().st_size,
                       'output_sha256': expected[target], 'output_size': size, 'decode_verified': True})
        print('Verified patch', name, patch.stat().st_size, flush=True)
    manifest = {'version': VERSION, 'assets': assets, 'runtime_verified': False,
                'release_layout_files_verified': 133, 'build_archive_payloads_verified': 10344}
    (DIR/'ACE3-English-0.1.42-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (DIR/'ACE3-English-0.1.42-SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['name']+'\n' for r in assets), encoding='utf-8')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__':
    main()
