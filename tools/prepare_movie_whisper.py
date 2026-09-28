"""Prepare local movie audio and Whisper drafts; never modify the game disc.

Requires the local 64-bit Python with faster-whisper. Dry-run by default.
Japanese drafts stay in ignored work/build, not the translation repository.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import wave

from pss_audio import private_payloads

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'work/build/movie_test'
WORK = ROOT/'work/build/movie_previews_055'
MOVIES = ['MOVIE%03d' % n for n in (1, 3, 4, 5, 6)]
MODEL = Path('C:/Users/Binh/.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120')


def extract(path):
    data = path.read_bytes()
    stream = b''.join(p[4:] for p in private_payloads(data))
    start = stream.find(b'SShd')
    if start < 0:
        raise ValueError('No Sony audio header')
    _, fmt, rate, channels, interleave = struct.unpack_from('<5I', stream, start+4)
    body = stream.find(b'SSbd', start)
    length = struct.unpack_from('<I', stream, body+4)[0]
    pcm = stream[body+8:body+8+length]
    if fmt not in (0, 1) or channels != 2 or len(pcm) != length:
        raise ValueError('Unsupported or incomplete audio')
    if fmt == 0:
        raw = bytearray(pcm)
        raw[0::2], raw[1::2] = pcm[1::2], pcm[0::2]
        pcm = bytes(raw)
    if interleave:
        if len(pcm) % (2*interleave):
            raise ValueError('Incomplete stereo block')
        out = bytearray(len(pcm))
        for at in range(0, len(pcm), 2*interleave):
            left, right = pcm[at:at+interleave], pcm[at+interleave:at+2*interleave]
            block = bytearray(2*interleave)
            block[0::4], block[1::4] = left[0::2], left[1::2]
            block[2::4], block[3::4] = right[0::2], right[1::2]
            out[at:at+2*interleave] = block
        pcm = bytes(out)
    return pcm, dict(movie=path.stem, source_sha256=hashlib.sha256(data).hexdigest(),
                     format=fmt, rate=rate, channels=channels, interleave=interleave,
                     audio_seconds=len(pcm)/(rate*channels*2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--transcribe', action='store_true')
    args = ap.parse_args()
    model = None
    if args.transcribe:
        from faster_whisper import WhisperModel
        WORK.mkdir(parents=True, exist_ok=True)
        model = WhisperModel(str(MODEL), device='cpu', compute_type='int8', cpu_threads=8,
                             local_files_only=True)
    inventory = []
    for name in MOVIES:
        pcm, info = extract(SOURCE/(name+'.PSS'))
        inventory.append(info)
        print(json.dumps(info), flush=True)
        if not model:
            continue
        wav = WORK/(name+'.wav')
        with wave.open(str(wav), 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(info['rate'])
            w.writeframes(pcm)
        target = WORK/(name+'_whisper_ja.json')
        if target.exists():
            print('EXISTS', target.name, flush=True)
            continue
        segments, meta = model.transcribe(str(wav), language='ja', task='transcribe',
            beam_size=5, word_timestamps=True, vad_filter=True,
            condition_on_previous_text=False)
        rows = []
        for s in segments:
            rows.append(dict(start=s.start, end=s.end, text=s.text, avg_logprob=s.avg_logprob,
                             no_speech_prob=s.no_speech_prob,
                             words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in (s.words or [])]))
            print(name, 'segment', len(rows), round(s.end, 2), flush=True)
        target.write_text(json.dumps(dict(source=info, model='Systran/faster-whisper-small',
             status='unreviewed_machine_transcription', segments=rows), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if model:
        (WORK/'inventory.json').write_text(json.dumps(inventory, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
