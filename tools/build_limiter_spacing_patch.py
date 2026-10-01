"""0.9.6: restore the purchase dialogs' reserved space above the cost display.

Dry-run by default. Reuse verified unused table padding; no archive growth.
"""
import json
import struct
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts, controls
from build_stats_panel_patch import ranges
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.9.6'
BASE = ROOT/'work/output/ACE3-English-0.9.5.iso'
BASE_HASH = '1e075a529b5079044fb88b5f1ebb3dc55cd8198823326bf25bc5867841306ec9'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
SPEC = ROOT/'work/ui/limiter_096/dialog.json'
TRANSLATION = ROOT/'work/translation/en/deployment_017.json'
EXPECTED = {
    190: 'Upgrade this unit?\n%s',
    191: 'Change the limiter setting?\nReleasing the limiter lets you\nuse weapons without limit.',
    192: 'Upgrade this unit?\n%s\n(㍻ Cost -25％)',
}


def repair(table, targets):
    size, pointers, count, rows = parse_table(table)
    require(size == len(table), 'Unexpected table allocation')
    insertions = []
    for tid, target in targets.items():
        matches = [r for r in rows if r[1] == tid]
        require(len(matches) == 1, 'Purchase row missing')
        slot, _, ptr, raw = matches[0]
        require(raw.decode('cp932') == EXPECTED[tid], 'Purchase text preimage changed')
        require(sum(r[2] == ptr for r in rows) == 1, 'Purchase string unexpectedly shared')
        encoded = target.encode('cp932')
        require(encoded.startswith(raw) and set(encoded[len(raw):]) == {10}, 'Only trailing line breaks may be added')
        insertions.append((ptr+len(raw), encoded[len(raw):]))
    insertions.sort()
    needed = sum(len(extra) for _, extra in insertions)
    used_end = max(ptr+len(raw)+1 for _, _, ptr, raw in rows)
    require(used_end+needed <= size and not any(table[used_end:]), 'Insufficient unused padding')
    result = bytearray(table)
    for at, extra in reversed(insertions):
        result[at:at] = extra
    del result[size:]
    for slot in range(count):
        pointer = u32(table, pointers+slot*4)
        if pointer:
            shifted = pointer+sum(len(extra) for at, extra in insertions if at < pointer)
            struct.pack_into('<I', result, pointers+slot*4, shifted)
    expected = [(s, i, targets[i].encode('cp932') if i in targets else raw) for s, i, _, raw in rows]
    require([(s, i, raw) for s, i, _, raw in parse_table(result)[3]] == expected, 'Unrelated text changed')
    require(len(result) == len(table) and result[:pointers] == table[:pointers], 'Table structure changed')
    return bytes(result), dict(bytes_used=needed, previous_unused_bytes=size-used_end,
                               remaining_unused_bytes=size-used_end-needed)


def plan():
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    drafts = {r['text_id']: r for r in json.loads(TRANSLATION.read_text(encoding='utf-8'))['rows']}
    edits, reports = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        inventory = []
        for _, size, off, rid in entries:
            if not (4002050 <= rid <= 4002058 or 1200000 <= rid <= 1200011):
                continue
            f.seek(fi['offset']+off)
            data = f.read(size)
            p = parts(data)
            if spec['table_id'] not in p:
                continue
            table = p[spec['table_id']]
            rows = {i: raw.decode('cp932') for _, i, _, raw in parse_table(table)[3]}
            if rows.get(191) != EXPECTED[191]:
                continue
            require(rid in spec['bundles'], 'Unexpected purchase dialog copy')
            inventory.append(rid)
            names = [raw.decode('cp932') for _, _, _, raw in parse_table(p[3000])[3]]
            targets, checks = {}, []
            for tid in spec['text_ids']:
                require(rows[tid] == EXPECTED[tid], 'Different purchase dialog')
                current = rows[tid]
                reserve = spec['total_lines']-len(current.split('\n'))
                require(reserve >= spec['minimum_reserved_lines'], 'No room for cost display')
                target = current+'\n'*reserve
                require(drafts[tid]['en'].replace('%', '％').replace('％s', '%s') == target,
                        'Translation source and runtime text disagree')
                require(len(drafts[tid]['source'].split('\n')) == spec['total_lines'], 'Stock spacer evidence changed')
                require(controls(target) == controls(current), 'Control code changed')
                samples = [target.replace('%s', name) for name in names] if '%s' in target else [target]
                widths = [max(measure_text(p[2500], sample)) for sample in samples]
                require(max(widths) <= spec['width'], 'Expanded prompt exceeds line width')
                require(max(map(len, samples)) <= spec['capacity'], 'Dialog exceeds text allocation')
                require(all(len(s.split('\n')) == spec['total_lines'] for s in samples), 'Wrong reserved height')
                targets[tid] = target
                checks.append(dict(text_id=tid, reserved_lines=reserve, total_lines=spec['total_lines'],
                                   max_width=max(widths), expanded_names_checked=len(samples)))
            after, padding = repair(table, targets)
            start, _ = ranges(data)[spec['table_id']]
            edits.append(dict(offset=fi['offset']+off+start, before=table, after=after))
            reports.append(dict(resource_id=rid, prompts=checks, padding=padding))
    require(inventory == spec['bundles'], 'Incomplete purchase-dialog coverage')
    edits.sort(key=lambda e: e['offset'])
    return edits, dict(copies=reports, runtime_verified=False,
                       retained='Prompt wording, prices, calculations, control codes and other table rows.'), None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
    writer.plan = plan
    writer.main()
