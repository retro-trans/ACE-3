"""Find when burned-in subtitles appear in a PSS movie's letterbox. Read-only analysis.

Run with a Python that has PyAV and numpy (the project's default 3.8 has neither):
  py -3.11 tools/movie_subtitle_scan.py work/build/movie_test/MOVIE002.PSS
Prints one segment per distinct subtitle (start/end seconds, bounding box) and writes segments.json.
"""
import json
import sys
from pathlib import Path
import av
import numpy as np

BAND = (352, 448)      # letterbox rows under the picture in the 640x448 frame
BRIGHT, MIN_PIXELS = 150, 60


def main():
    path = Path(sys.argv[1]); out = path.parent/(path.stem+'_segments'); out.mkdir(exist_ok=True)
    container = av.open(str(path)); stream = container.streams.video[0]
    segments, current, previous = [], None, None
    for frame in container.decode(stream):
        t = float(frame.pts*stream.time_base)
        luma = frame.to_ndarray(format='gray')[BAND[0]:BAND[1]]
        mask = luma > BRIGHT
        present = int(mask.sum()) >= MIN_PIXELS
        small = mask.reshape(mask.shape[0]//4, 4, mask.shape[1]//4, 4).any(axis=(1, 3)) if present else None
        same = present and previous is not None and (small ^ previous).sum() <= 0.12*max(small.sum(), previous.sum())
        if current and not same:
            current['end'] = t; segments.append(current); current = None
        if present and current is None:
            ys, xs = np.where(mask)
            current = {'start':t, 'box':[int(xs.min()), int(ys.min())+BAND[0], int(xs.max()), int(ys.max())+BAND[0]], 'frame':frame}
        previous = small
    if current: current['end'] = t; segments.append(current)
    # Merge fades: a segment shorter than 0.2 s is the ramp of its neighbour.
    kept = [s for s in segments if s['end']-s['start'] >= 0.2]
    report = []
    for n, s in enumerate(kept, 1):
        s.pop('frame')  # strips are rendered afterwards with ffmpeg; this interpreter has no Pillow
        report.append({'n':n, 'start':round(s['start'], 2), 'end':round(s['end'], 2), 'box':s['box']})
    (out/'segments.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(len(report), 'segments; movie length', round(t, 2))
    for r in report: print(r)


if __name__ == '__main__': main()
