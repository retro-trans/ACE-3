"""0.1.28: demo-player font, HUD/Results and Movie Viewer labels, narrower in-mission wrapping, and the next scenes.

Five independent parts, merged into one DATA.BIN rebuild on top of 0.1.27:
 1. bundle 1200011 (the real-time story-demo player) gets the Latin glyphs every other font bundle already has;
 2. table 3013 (in-mission HUD, Results screen, demo footer) and table 3090 (Movie Viewer titles);
 3. the 0.1.21 in-mission scenes are re-wrapped at 400 units: at 460 a line ran under the wingman icons;
 4. newly reviewed in-mission scenes (complete scenes only), same relocation as before;
 5. reviewed meeting / briefing / archive / hangar-demo scenes from work/translation/en/scenes.
Dry-run unless --write.
"""
import argparse
import hashlib
import json
import re
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table, INDEX
from build_flight_save_patch import parts, controls
from build_intermission_patch import replace_rows
from gameplay_font import supplement
from ui_font import font_map, measure_text
import build_dialogue_patch as builder
import build_dialogs_patch as dialogs
import build_scene_patch as scene
import build_reviewed_scenes_patch as old_scenes

VERSION = '0.1.28'
BASE = ROOT/'work/output/ACE3-English-0.1.27.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.28.iso'
UI = ROOT/'work/translation/en/ui_028.json'
SCENES = ROOT/'work/translation/en/scenes'
BUNDLES = list(range(4002050, 4002059))+list(range(1200000, 1200012))
DEMO_PLAYER = 1200011
MISSION_WIDTH, MISSION_LINES = 400, 4
# Window budgets: meetings keep the 0.1.15 numbers the user has seen working; hangar demos use a window of the
# same width whose stock text never passes 370 units or three lines.
WINDOW = {4003:(460, 3, 128), 4004:(440, 3, 120)}
TAG = re.compile(r'<[^>]*>')
NAME_FIXES = {4003020:('Exbrau', 'Ixbrau')}
FREEDEN = {5:'Warning: Freeden at 5％ damage', 25:'Warning: Freeden at 25％ damage', 50:'Warning: Freeden at 50％ damage',
           75:'Warning: Freeden at 75％ damage'}
GEKKO = {25:'Warning: Gekko at 25％ damage', 50:'Warning: Gekko at 50％ damage', 75:'Warning: Gekko at 75％ damage'}
REINFORCE, ADVANCE = 'Warning: Enemy reinforcements', 'Warning: Enemy advancing'
# HUD labels stored beside the dialogue; wording follows the 0.1.21 labels.
NEW_AUXILIARY = {
 2002040:{3:'Destroy the Gundam Ashtaron', 4:'Objective: Destroy the Gundam Ashtaron', 10:'Objective: Destroy all targets',
          11:'Nav: Watch for the particle field nearby', 12:"Nav: Attack the field weapon's guards",
          13:FREEDEN[5], 14:FREEDEN[50], 15:FREEDEN[75], 16:'Mission Failed: Freeden sunk',
          17:'Warning: Allied forces crippled', 18:'Warning: Allied forces wiped out', 19:'Warning: 5 minutes remaining',
          20:'Mission Failed: Time Over', 21:REINFORCE, 22:REINFORCE, 23:'Info: Enemy strength reduced', 24:ADVANCE,
          25:REINFORCE, 26:'Info: Enemy retreating', 27:REINFORCE, 28:'Info: Particle field down', 29:FREEDEN[25],
          30:'Warning: Allied forces crippled'},
 2002050:{3:'Destroy the Gundam Virsago', 4:'Objective: Destroy the Gundam Virsago', 10:'Objective: Destroy all targets',
          11:'Warning: Allied forces at 50％ damage', 12:'Warning: Allied forces crippled', 15:GEKKO[25], 16:GEKKO[50],
          17:GEKKO[75], 18:'Mission Failed: Gekko sunk', 19:'Warning: 5 minutes remaining', 20:'Mission Failed: Time Over',
          22:ADVANCE, 25:'Info: All targets destroyed', 28:'Info: Base captured', 36:'Info: All bases captured',
          37:REINFORCE, 38:'Info: Allied forces advancing', 39:'Nav: Capture the bases'},
}


def demo_font(get, original):
    """The demo player's own font kept only the stock Latin subset (abdeknoprtuy...), so English lost letters."""
    data = get(DEMO_PLAYER); p = parts(data); game, menu = parts(get(1200000)), parts(get(4002050))
    donors = [('game19', game[2500], game[2000]), ('menu19', menu[2500], menu[2000]), ('global12', original(35), original(36))]
    font, texture, report = supplement(p[2500], p[2000], donors, '’')
    mapping = font_map(font)[0]
    require(all(code in mapping for code in range(32, 127)), 'Demo font still lacks ASCII')
    require(not any(x['source_height'] == 12 for x in report['additions']), 'Small fallback glyph in demo font')
    output = builder.rebuild_bundle(data, {2500:font, 2000:texture})
    return output, {'resource_id':DEMO_PLAYER, 'kind':'demo_player_font', 'old_size':len(data), 'new_size':len(output),
                    'added':''.join(x['character'] for x in report['additions']), 'used_height':report['used_height']}


def reviewed():
    indexed = {r['id']:r for r in json.loads(INDEX.read_text(encoding='utf-8'))['rows']}
    out = {}
    for path in sorted((ROOT/'work/translation/en/dialogue').glob('batch_*.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))  # proposal files share the prefix and are lists
        rows = doc.get('rows', []) if isinstance(doc, dict) else []
        for row in rows if isinstance(rows, list) else []:
            if row.get('status') == 'meaning_reviewed': out[indexed[row['id']]['source_sha256']] = row
    return out


class Mission:
    reflowed = []

    @staticmethod
    def wrap(text, font):
        # Portrait chatter (<op()>) shares the top of the HUD with the wingman icons; event and demo-window
        # lines (<on()>) have the whole window and keep the 0.1.21 budget.
        width = MISSION_WIDTH if text.startswith('<op()>') else 460
        try:
            return scene.wrap_words(text, font, width, MISSION_LINES)
        except ValueError:
            flat = text.replace('\n', ' ')
            require(flat.split() == text.split(), 'Reflow changed words')
            Mission.reflowed.append(text)
            return scene.wrap_words(flat, font, width, MISSION_LINES)


def stock_scene(data, report):
    """Undo a previous relocation: the stock table and script are intact below the appended table."""
    if report is None: return data
    stock = bytearray(data[:report['original_size']]); struct.pack_into('<I', stock, 20, report['original_offset'])
    require(u32(data, 20) == report['relocated_offset'], 'Scene is not in its 0.1.21 form')
    return bytes(stock)


def mission_scenes(get, font):
    translations = reviewed(); replacements, reports, skipped = {}, [], []
    previous = {r['resource_id']:r for r in json.loads((ROOT/'work/ui/mission_relocations_021.json').read_text(encoding='utf-8'))['rows']}
    labels = dict(old_scenes.AUXILIARY); labels.update(NEW_AUXILIARY)
    keep, keep_width = scene.wrap, scene.WIDTH
    scene.wrap, scene.WIDTH = Mission.wrap, 480
    try:
        for scene_id, auxiliary in labels.items():
            for rid in old_scenes.copies(scene_id):
                data = stock_scene(get(rid), previous.get(rid)); old = u32(data, 20); size = parse_table(data, old)[0]
                require(old+size <= len(data), 'Malformed scene %s' % rid)
                missing = [i for _, i, _, raw in parse_table(data, old)[3] if b'<sp(' in raw and hashlib.sha256(raw).hexdigest() not in translations]
                if missing:
                    require(scene_id in NEW_AUXILIARY, 'Released scene lost rows: %s' % rid)
                    skipped.append((rid, len(missing))); continue
                table, rows = scene.rebuild_table(data[old:old+size], translations, font, auxiliary)
                new = builder.align(len(data), 32)
                output = bytearray(data+b'\0'*(new-len(data))+table); struct.pack_into('<I', output, 20, new)
                require(output[24:len(data)] == data[24:] and output[:20] == data[:20], 'Original script modified')
                replacements[rid] = bytes(output)
                reports.append({'resource_id':rid, 'kind':'relocated_dialogue_table', 'original_offset':old, 'relocated_offset':new,
                                'original_size':len(data), 'new_size':len(output), 'rows':rows})
    finally:
        scene.wrap, scene.WIDTH = keep, keep_width
    return replacements, reports, skipped


def rebuild_scene_bundle(data, edits):
    """Like builder.rebuild_bundle, but the last chunk keeps its exact length: hangar demos end with an unpadded tail."""
    rows = inner_bnd(data); output = bytearray(data[:rows[0][1]])
    for n, (entry, start, end) in enumerate(rows):
        struct.pack_into('<I', output, 20+n*8, len(output))
        output.extend(edits.get(entry, data[start:end]))
        if n+1 < len(rows): output.extend(bytes(builder.align(len(output), 32)-len(output)))
    struct.pack_into('<I', output, 4, len(output))
    for (entry, start, end), (_, ns, ne) in zip(rows, inner_bnd(bytes(output))):
        if entry not in edits: require(output[ns:ns+end-start] == data[start:end] and not any(output[ns+end-start:ne]), 'Unrelated scene chunk changed')
    return bytes(output)


def wrap_words_soft(text, font, width, lines):
    """scene.wrap_words with <color> spans allowed to break across lines (the window keeps the colour going);
    <book> link spans stay on one line."""
    out = []
    for paragraph in text.split('\n'):
        words, span = [], None
        for word in paragraph.split(' '):
            if span is not None:
                span += ' '+word
                if '<endbook()>' in word: words.append(span); span = None
            elif word.count('<book(') > word.count('<endbook()>'): span = word
            else: words.append(word)
        if span is not None: words.append(span)
        line, used = [], 0
        for word in words:
            w = measure_text(font, builder.TOKEN.sub('', word))[0]
            require(w <= width, 'One word or span exceeds window width: %r' % word)
            space = measure_text(font, ' ')[0] if line else 0
            if line and used+space+w > width: out.append(' '.join(line)); line, used, space = [], 0, 0
            line.append(word); used += space+w
        out.append(' '.join(line))
    result = '\n'.join(out)
    require(builder.TOKEN.findall(result) == builder.TOKEN.findall(text) and result.split() == text.split(), 'Wrapping changed text')
    require(len(out) <= lines, 'Window text exceeds %d lines: %r' % (lines, text))
    return result


def wrap_window(text, font, family):
    width, lines, chars = WINDOW[family]
    try: wrapped = scene.wrap_words(text, font, width, lines)
    except ValueError: wrapped = wrap_words_soft(text, font, width, lines)
    require(len(TAG.sub('', wrapped)) <= chars, 'Window text exceeds %d characters: %s' % (chars, TAG.sub('', text)))
    return wrapped


def window_scenes(get, font):
    replacements, reports, skipped = {}, [], []
    for path in sorted(SCENES.glob('[0-9]*.json')):
        doc = json.loads(path.read_text(encoding='utf-8')); rid = doc['resource_id']
        if doc.get('status') != 'meaning_reviewed': skipped.append((rid, doc.get('status'))); continue
        data = get(rid); p = parts(data); edits, tables = {}, []
        for tid in sorted({r['table'] for r in doc['rows']}):
            stock = parse_table(p[tid])[3]; targets = {r['slot']:r for r in doc['rows'] if r['table'] == tid}
            require(set(targets) == {s for s, _, _, _ in stock}, 'Incomplete scene table %s/%s' % (rid, tid))
            mappings, rows = {}, []
            for slot, text_id, _, raw in stock:
                source, row = raw.decode('cp932'), targets[slot]
                require(row['text_id'] == text_id, 'Text ID mismatch %s/%s/%s' % (rid, tid, slot))
                require(hashlib.sha256(raw).hexdigest() == row['source_sha256'], 'Scene preimage changed %s/%s/%s' % (rid, tid, slot))
                en = row['en']
                require('\n' not in en and not re.search(r'[^\x20-\x7e]', TAG.sub('', en)), 'Non-ASCII or newline: %s/%s' % (rid, slot))
                title = rid//1000 == 4003 and slot == 0  # a meeting's first row is the screen title
                target = en if title else wrap_window(en, font, rid//1000)
                if title: require(max(measure_text(font, target)) <= 420, 'Title too wide: '+target)
                require(controls(source) == controls(target), 'Scene commands changed %s/%s/%s' % (rid, tid, slot))
                if target != source: mappings[slot] = (source, target)
                rows.append({'slot':slot, 'text_id':text_id, 'target':target, 'widths':measure_text(font, TAG.sub('', target))})
            if mappings: edits[tid] = replace_rows(p[tid], mappings)
            tables.append({'table_id':tid, 'rows':rows})
        if edits:
            replacements[rid] = rebuild_scene_bundle(data, edits)
            reports.append({'resource_id':rid, 'kind':'window_scene', 'old_size':len(data), 'new_size':len(replacements[rid]), 'tables':tables})
    # Name-script pass over released scenes: the unit is Ixbrau (unit_names_014); 0.1.15 shipped one "Exbrau".
    for rid, (old, new) in NAME_FIXES.items():
        require(rid not in replacements, 'Name fix collides with a scene file')
        data = get(rid); p = parts(data)
        mappings = {slot:(raw.decode('cp932'), raw.decode('cp932').replace(old, new)) for slot, _, _, raw in parse_table(p[1])[3] if old.encode() in raw}
        require(mappings, 'Name fix found nothing in %s' % rid)
        for _, target in mappings.values():
            require(max(measure_text(font, TAG.sub('', target))) <= WINDOW[4003][0], 'Name fix widened a line')
        replacements[rid] = builder.rebuild_bundle(data, {1:replace_rows(p[1], mappings)})
        reports.append({'resource_id':rid, 'kind':'name_fix', 'old':old, 'new':new, 'slots':sorted(mappings), 'old_size':len(data), 'new_size':len(replacements[rid])})
    return replacements, reports, skipped


def plan():
    changes, reports, inventory = dialogs.plan(BASE, UI, BUNDLES)
    with BASE.open('rb') as f, next(ROOT.glob('*.iso')).open('rb') as o:
        fi, es = archive(f); oi, oe = archive(o)
        def get(rid):
            e = next(x for x in es if x[3] == rid); f.seek(fi['offset']+e[2]); return f.read(e[1])
        def original(rid):
            e = next(x for x in oe if x[3] == rid); o.seek(oi['offset']+e[2]); return o.read(e[1])
        game_font, menu_font = parts(get(1200000))[2500], parts(get(4002050))[2500]
        data, report = demo_font(get, original); changes[DEMO_PLAYER] = data; reports.append(report)
        mission, mission_reports, mission_skipped = mission_scenes(get, game_font)
        window, window_reports, window_skipped = window_scenes(get, menu_font)
    require(not set(changes) & set(mission) and not (set(changes) | set(mission)) & set(window), 'Resource planned twice')
    changes.update(mission); changes.update(window); reports += mission_reports+window_reports
    summary = {'resources':len(changes), 'ui_tables':inventory, 'ui_instances':sum(n for _, _, n in inventory),
               'allocation_adjustments':sum(len(r.get('allocations', [])) for r in reports),
               'mission_scene_resources':len(mission), 'mission_rows':sum(len(r['rows']) for r in mission_reports),
               'mission_max_width':max(max(x['widths']) for r in mission_reports for x in r['rows']),
               'mission_max_lines':max(x['lines'] for r in mission_reports for x in r['rows']), 'mission_reflowed':len(set(Mission.reflowed)),
               'mission_skipped_incomplete':mission_skipped, 'window_scenes':sorted(window), 'window_rows':sum(len(t['rows']) for r in window_reports for t in r.get('tables', [])),
               'window_skipped_unreviewed':window_skipped}
    return changes, reports, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    changes, reports, summary = plan()
    print('DRY RUN', json.dumps(summary))
    for r in reports:
        if r['kind'] == 'demo_player_font': print(json.dumps(r, ensure_ascii=False))
        if r['kind'] == 'dialogs_and_options': print(r['resource_id'], r['old_size'], '->', r['new_size'], r['changed_subresources'], 'allocations', len(r['allocations']))
        if r['kind'] == 'window_scene':
            print(r['resource_id'], r['old_size'], '->', r['new_size'])
            for x in r['tables'][0]['rows'][:3]: print('    ', repr(x['target']), x['widths'])
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [UI, ROOT/'tools/build_028_patch.py', ROOT/'work/ui/mission_relocations_021.json', ROOT/'tools/build_dialogs_patch.py',
              ROOT/'tools/build_scene_patch.py', ROOT/'tools/build_reviewed_scenes_patch.py', ROOT/'tools/gameplay_font.py']
    inputs += sorted(SCENES.glob('*.json'))+sorted((ROOT/'work/translation/en/dialogue').glob('batch_*.json'))
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'13d2c562bc4f5c37357141d1898d2bc4ea40aa223046b84d05b469b9eabd99d0', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
