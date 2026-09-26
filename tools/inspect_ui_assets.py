"""Inspect indexed UI artwork; dry-run first, --write exports a contact sheet."""
import argparse
import struct
from PIL import Image, ImageDraw
from build_ui_patch import ROOT, inner_bnd, u32
from dialogue_corpus import archive
from ui_textures import decode
from dialogue_font import texture_pixels


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    images=[]; seen=set()
    with (ROOT/'work/output/ACE3-English-0.1.9.iso').open('rb') as f:
        fi,es=archive(f)
        for _,size,offset,bid in es:
            if bid not in (4002050,4002054,4002056,4002057,1200008,1200009,1200010,1200011):continue
            f.seek(fi['offset']+offset);data=f.read(size)
            for rid,s,t in inner_bnd(data[:u32(data,4)]):
                d=data[s:t]
                if rid<50000 or d in seen:continue
                seen.add(d)
                try: img=decode(d)
                except (ValueError,struct.error):continue
                print('DRY RUN',bid,rid,img.size,'format',u32(d,12))
                images.append((str(bid)+'/'+str(rid),img))
                if args.write and bid==4002056:
                    out=ROOT/'work/ui/assets/source'/('%d.png'%rid)
                    out.parent.mkdir(parents=True,exist_ok=True);img.save(out)
    if not args.write:return
    out=ROOT/'work/ui/assets/inspection/all_ui_textures.png'
    sheet=Image.new('RGB',(6*192,((len(images)+5)//6)*212),(10,20,30));draw=ImageDraw.Draw(sheet)
    for i,(name,img) in enumerate(images):
        img.thumbnail((188,188));x=i%6*192;y=i//6*212
        sheet.paste(img,(x,y+20),img);draw.text((x,y),name,fill='white')
    out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out)
    print(out)


if __name__=='__main__':main()
