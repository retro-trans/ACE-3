"""Compare native font contrast locally; does not modify fonts or the ISO."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from build_controller_patch import NativeGlyphs
from build_flight_save_patch import parts
from dialogue_corpus import archive

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/ui/font_preview'
BASE = ROOT / 'work/output/ACE3-English-0.9.6.iso'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with BASE.open('rb') as stream:
        info, entries = archive(stream)
        entry = next(e for e in entries if e[3] == 4002050)
        stream.seek(info['offset'] + entry[2])
        resources = parts(stream.read(entry[1]))
    original = NativeGlyphs(resources[2500], resources[2000])
    clearer = NativeGlyphs(resources[2500], resources[2000])
    # Contrast experiment only: retain every glyph's shape, metrics and alpha.
    # Limit the change to a separate preview atlas, not the game's palette.
    levels = [round(20 + 235 * max(0, min(1, (v - 55) / 125)))
              for v in range(256)]
    r, g, b, a = clearer.atlas.split()
    clearer.atlas = Image.merge('RGBA', (r.point(levels), g.point(levels),
                                       b.point(levels), a))
    small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 21)
    title = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 28)
    canvas = Image.new('RGB', (1000, 1110), '#0d1420')
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 18), 'Font clarity comparison', font=title, fill='white')
    draw.text((24, 58), 'Same game glyphs, spacing and size. Preview only.',
              font=small, fill='#bbc9db')
    for i, (name, glyphs) in enumerate([
            ('CURRENT — extracted game font', original),
            ('PROPOSED — brighter strokes, stronger contrast', clearer)]):
        y = 106 + i * 440
        draw.text((24, y), name, font=small, fill='#93c9ef')
        panel = Image.new('RGBA', (640, 236), '#061324')
        d = ImageDraw.Draw(panel)
        for yy in range(0, 236, 4):
            d.line((0, yy, 640, yy), fill='#09182a')
        def label(text, xy):
            panel.alpha_composite(glyphs.render(text), xy)
        label('Intermission', (20, 12))
        for j, text in enumerate(['Deploy', 'Combat Records', 'Unit Upgrades']):
            yy = 44 + j * 28
            d.rectangle((19, yy, 220, yy + 24), outline='#657483')
            label(text, (26, yy + 3))
        d.rectangle((19, 145, 620, 222), fill='#080e20', outline='#46566b')
        label('Renton', (29, 151))
        label("They were fun days, but Eureka wasn't there.", (29, 177))
        label('I kept feeling like something was missing.', (29, 201))
        panel.convert('RGB').save(OUT / ('current.png' if i == 0 else 'clearer.png'))
        # Identical bilinear enlargement in both cases, approximating texture
        # filtering. This is a specimen, not a screenshot of an emulator run.
        canvas.paste(panel.convert('RGB').resize((960, 354), Image.Resampling.BILINEAR),
                     (20, y + 38))
    draw.text((24, 1001), 'No extra resolution is added by this contrast adjustment.',
              font=small, fill='#bbc9db')
    draw.text((24, 1033), 'Both samples use identical 1.5x enlargement and filtering.',
              font=small, fill='#bbc9db')
    draw.text((24, 1065), 'Final appearance still needs an in-game check.',
              font=small, fill='#bbc9db')
    canvas.save(OUT / 'font-clarity-comparison.png')
    (OUT / 'preview.json').write_text(json.dumps({
        'status': 'preview_only_not_applied', 'base_version': '0.9.6',
        'bundle': 4002050, 'font': 2500, 'texture': 2000,
        'change': 'RGB contrast only; glyph alpha and metrics unchanged',
        'levels': {'input_black': 55, 'input_white': 180,
                   'output_black': 20, 'output_white': 255},
        'enlargement': '1.5x bilinear on both specimens',
        'limitations': ['Not a runtime screenshot', 'No added texture resolution',
                        'Not tested against bright gameplay backgrounds',
                        'Other font atlases and icons are not evaluated']
    }, indent=2) + '\n', encoding='utf-8')
    print(OUT / 'font-clarity-comparison.png')


if __name__ == '__main__':
    main()
