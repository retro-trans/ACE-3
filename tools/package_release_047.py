"""Prepare both 0.1.47 editions and build verified Retro Trans release assets.

Run relayout_disc.py ACE3-English-0.1.47.iso first. Preview by default.
Only patches and canonical metadata go in the release directory.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
from build_ui_patch import ROOT, iso_files, require
from package_release_042 import digest, MOVIE_FILE

VERSION = '0.1.47'
DIR = ROOT/'work/release'
ORIGINAL = next(ROOT.glob('*.iso'))
MOVIE = DIR/'ACE3-English-0.1.47-orig-layout.iso'
TEXT = DIR/'ACE3-English-0.1.47-text-orig-layout.iso'
OUTPUT = ROOT/'work/output/release-0.1.47'
TOOLS = ROOT/'work/local/retro-trans-tools'
EXPECTED = {
    ORIGINAL: '5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705',
    DIR/'ACE3-English-0.1.42-text-orig-layout.iso': 'ad9dffa95cf8b8144c13d25c014d73992574c6f50ce4518661ac9c2be486557d',
    DIR/'ACE3-English-0.1.42-orig-layout.iso': 'c72752b32b5982b63ef8c5db5f171090469e3aad94999245cace2cb760565353',
}


def jobs():
    for edition, suffix, target, previous in (
        ('Original prologue', '', TEXT, DIR/'ACE3-English-0.1.42-text-orig-layout.iso'),
        ('English prologue', '-movie', MOVIE, DIR/'ACE3-English-0.1.42-orig-layout.iso'),
    ):
        for version, source, stem in (
            ('original', ORIGINAL, 'ACE3-English-0.1.47'),
            ('0.1.42', previous, 'ACE3-English-0.1.42-to-0.1.47'),
        ):
            yield dict(patch=stem+suffix+'.xdelta', edition=edition, language='en',
                       source_version=version, source_format='iso', target_format='iso',
                       source=str(source), target=str(target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    require(re.fullmatch(r'[0-9a-f]{40}', args.source_commit), 'Full source commit required')
    config = dict(game_id='ace-3', game_name="Another Century's Episode 3: The Final",
                  platform='PS2', version=VERSION, source_commit=args.source_commit, patches=list(jobs()))
    for row in config['patches']:
        print('PLAN', row['patch'], row['edition'], row['source_version'], '->', VERSION, flush=True)
    print('Restore the original prologue for the text edition; verify all four patch round trips.', flush=True)
    if not args.write:
        return
    require(not TEXT.exists() and not OUTPUT.exists(), 'Release outputs already exist')
    meta = json.loads(MOVIE.with_suffix('.json').read_text())
    require(meta['verified'] and meta['files'] == 133, 'Verified release layout required')
    expected = dict(EXPECTED)
    expected[MOVIE] = meta['sha256']
    for path, sha in expected.items():
        require(digest(path) == sha, 'Source hash mismatch: '+path.name)
        print('Verified source', path.name, flush=True)
    with ORIGINAL.open('rb') as source, MOVIE.open('rb') as target:
        original_movie = iso_files(source)[MOVIE_FILE]
        target_movie = iso_files(target)[MOVIE_FILE]
    require(original_movie['size'] == target_movie['size'], 'Movie extents differ')
    shutil.copyfile(MOVIE, TEXT)
    with ORIGINAL.open('rb') as source, TEXT.open('r+b') as target:
        source.seek(original_movie['offset'])
        target.seek(target_movie['offset'])
        left = target_movie['size']
        while left:
            chunk = source.read(min(left, 8 << 20))
            require(chunk, 'Short movie read')
            target.write(chunk)
            left -= len(chunk)
    start, length = target_movie['offset'], target_movie['size']
    for offset, size in ((0, start), (start+length, MOVIE.stat().st_size-start-length)):
        require(digest(TEXT, offset, size) == digest(MOVIE, offset, size), 'Non-movie bytes changed')
    require(digest(TEXT, start, length) == digest(ORIGINAL, original_movie['offset'], length), 'Original movie mismatch')
    print('Verified original-prologue edition', flush=True)
    sys.path.insert(0, str(TOOLS))
    from retro_trans.release import build_release, validate_directory
    from retro_trans.catalog import atomic_json, file_hashes
    local_config = ROOT/'work/local/release-047-config.json'
    atomic_json(local_config, config)
    last = [None]

    def progress(message, fraction):
        if message != last[0]:
            print(message, flush=True)
            last[0] = message

    manifest = build_release(local_config, OUTPUT, progress=progress,
                             cache=ROOT/'work/local/retro-trans-engine')
    # Add SHA-1 identification aliases for DVD CHD discovery. Recheck every
    # full SHA-256 while computing these; the canonical validator covers the
    # regenerated manifest, validation report and checksums.
    hashes = {}
    for row, private in zip(manifest['patches'], config['patches']):
        for key in ('source', 'target'):
            path = Path(private[key])
            if path not in hashes:
                hashes[path] = file_hashes(path, ('sha256', 'sha1'))
            require(hashes[path]['sha256'] == row[key+'_sha256'], 'Release input changed')
            row[key+'_sha1'] = hashes[path]['sha1']
    atomic_json(OUTPUT/'BUILD-MANIFEST.json', manifest)
    atomic_json(OUTPUT/'VALIDATION.json', dict(schema_version=1,
        manifest_sha256=digest(OUTPUT/'BUILD-MANIFEST.json'),
        patches=[dict(patch=p['patch'], roundtrip_verified=True, target_sha256=p['target_sha256'])
                 for p in manifest['patches']]))
    files = sorted(p for p in OUTPUT.iterdir() if p.name != 'SHA256SUMS.txt')
    (OUTPUT/'SHA256SUMS.txt').write_bytes(''.join(digest(p)+'  '+p.name+'\n' for p in files).encode('utf-8'))
    validate_directory(OUTPUT)
    print('VERIFIED RELEASE', OUTPUT, flush=True)


if __name__ == '__main__':
    main()
