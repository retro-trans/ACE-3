"""Read-only verification of ACE3 routes with the current Retro Trans catalog.

Pass --manifest to preview a candidate; omit it to check published registration.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
from build_ui_patch import ROOT, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--retro-trans-tools', type=Path, default=ROOT/'work/local/retro-trans-tools')
    args = parser.parse_args()
    sys.path.insert(0, str(args.retro_trans_tools))
    from retro_trans.catalog import Catalog, assert_immutable, matches
    data = json.loads(args.catalog.read_text(encoding='utf-8'))
    previous = Catalog(data)
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        require(manifest['version'] == args.version, 'Candidate version mismatch')
        data = copy.deepcopy(data)
        data['releases'].append(dict(repo='retro-trans/ACE-3', tag='v'+args.version,
            manifest=manifest, assets={p['patch']: 'https://github.com/retro-trans/ACE-3/releases/download/v'+
                args.version+'/'+p['patch'] for p in manifest['patches']}))
    catalog = Catalog(data)
    assert_immutable(previous, catalog)
    releases = [r for r in data['releases'] if r['repo'] == 'retro-trans/ACE-3' and r['tag'] == 'v'+args.version]
    require(len(releases) == 1, 'Release missing or duplicated')
    nodes = [n for n in catalog.nodes.values() if n.id[0] == 'ace-3' and n.id in catalog.available_ids]
    originals = [n for n in nodes if n.version == 'original']
    require({n.edition for n in nodes} == {'English prologue'}, 'Discontinued edition still selectable')
    require(len(originals) == 1, 'Expected a single original-disc choice')
    require(len({(n.size, n.hashes['sha256']) for n in originals}) == 1, 'Edition choices disagree on original disc')
    routes = []
    for node in nodes:
        plan = catalog.plan(node)
        require(plan.target.version == args.version and plan.latest_reachable, 'Latest does not route to release')
        require(plan.target.edition == node.edition, 'Edition changed during upgrade')
        require((len(plan.edges) == 0) == (node.version == args.version), 'Invalid no-op route')
        if node.version == 'original':
            require(len(plan.edges) == 1, 'Original disc should use the direct full patch')
        routes.append(dict(edition=node.edition, source=node.version, target=plan.target.version,
                           patches=[edge.asset.name for edge in plan.edges]))
    require(len(routes) == len(nodes) and {'original', args.version} <= {r['source'] for r in routes},
            'Incomplete source coverage')
    require(not any(matches(n, {'sha256': '0'*64, 'sha1': '0'*40}, originals[0].size) for n in nodes), 'Unknown disc accepted')
    print(json.dumps(dict(version=args.version, candidate=bool(args.manifest), verified=True,
                          unknown_disc_rejected=True, routes=routes), indent=2))


if __name__ == '__main__':
    main()
