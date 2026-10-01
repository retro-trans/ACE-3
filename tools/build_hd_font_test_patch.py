"""0.9.7: local native 4x main-font test. Dry-run unless --write.

Preserve Japanese glyphs referenced by the main menu/gameplay BND tables. Other
legacy mission variants remain unclassified; this is not a release candidate.
Credits and 20px/16px secondary fonts are unchanged. No texture replacements.
"""
import hashlib
import json
import struct

from build_ui_patch import ROOT, require
from build_flight_save_patch import parts
from dialogue_corpus import archive, parse_table
from prototype_english_hd_font import pack, JAPANESE
from ui_font import codepoint, font_map, measure_text
from build_stats_panel_patch import ranges
import build_stats_panel_patch as writer

VERSION='0.9.7'
BASE=ROOT/'work/output/ACE3-English-0.9.6.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH='cd80b3aca2313530875c9c3079d4a64252ecb51a1236961aa5b4efe8f2cbbda3'
BUNDLES=(1200000,1200001,1200004,1200005,1200006,1200007,1200011,
         4002050,4002051,4002052,4002053,4002054,4002057)


def plan():
    inventory={};used={'menu':set(),'game':set()};texts={'menu':[],'game':[]}
    with BASE.open('rb') as stream:
        fi,entries=archive(stream)
        for _,size,offset,rid in entries:
            if not (1200000<=rid<=1200011 or 4002050<=rid<=4002058):
                continue
            stream.seek(fi['offset']+offset);data=stream.read(size);resources=parts(data)
            inventory[rid]=(fi['offset']+offset,data,resources)
            group='menu' if rid>=4002050 else 'game'
            for tid,table in resources.items():
                try:rows=parse_table(table)[3]
                except (ValueError,UnicodeError,struct.error):continue
                for _,text_id,_,raw in rows:
                    text=raw.decode('cp932')
                    used[group].update(codepoint(c) for c in JAPANESE.findall(text))
                    texts[group].append(text)
    edits=[];reports=[];cache={}
    for rid in BUNDLES:
        origin,data,p=inventory[rid];group='menu' if rid>=4002050 else 'game'
        key=(hashlib.sha256(p[2500]+p[2000]).hexdigest(),group)
        if key not in cache:
            cache[key]=pack(p[2500],p[2000],retain_codes=used[group],pad_native=False)
        font,texture,report=cache[key]
        old_map,old_start,_=font_map(p[2500]);new_map,new_start,_=font_map(font)
        require(len(font)<=len(p[2500]),'New font exceeds allocated resource')
        require(len(texture)==len(p[2000]),'Texture allocation changed')
        require(all(c in new_map for c in used[group] if c in old_map),'Required Japanese glyph lost')
        # Check every previously supported character in these tables, including
        # symbols/fullwidth aliases. Widths remain unchanged for retained text.
        checked=0
        for text in texts[group]:
            codes=[codepoint(c) for c in text if c not in '\r\n\t']
            require(all(c in new_map for c in codes if c in old_map),'Referenced table glyph lost')
            if '\r' not in text and '\t' not in text and all(c in old_map for c in codes):
                require(measure_text(font,text)==measure_text(p[2500],text),'Text width changed')
                checked+=1
        locations=ranges(data)
        for tid,after in [(2500,font+bytes(len(p[2500])-len(font))),(2000,texture)]:
            start,end=locations[tid];before=data[start:end]
            require(len(before)==len(after),'Fixed resource extent changed')
            edits.append(dict(offset=origin+start,before=before,after=after))
        reports.append(dict(bundle=rid,source_sha256=key[0],font=report,text_rows_width_checked=checked))
    edits.sort(key=lambda e:e['offset'])
    require(all(a['offset']+len(a['before'])<=b['offset'] for a,b in zip(edits,edits[1:])), 'Overlapping edits')
    require(len(reports)==13,'Missing main font copy')
    return edits,dict(font_scale=4,unique_font_variants=len(cache),bundles=reports,
                      font_typeface='Times New Roman rasterized locally; no TTF embedded',
                      texture_replacements_required=False,credits_unchanged=True,
                      inherited_build='0.9.6',runtime_verified=False,
                      limitations=['Main 19px fonts only; 20px and small HUD fonts remain original',
                                   'Renderer size, filtering and texture seams need in-game testing',
                                   'Japanese used by menu/gameplay BND tables retained; unclassified legacy mission variants are outside coverage',
                                   'Baked image labels and movies unchanged',
                                   'Local test only, not published']),None


if __name__=='__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH=VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan=plan
    writer.main()
