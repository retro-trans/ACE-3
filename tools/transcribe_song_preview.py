"""Transcribe a supplied song locally with Whisper; dry-run by default.

Japanese ASR output is restricted to ignored work/local files. No VAD is used:
speech activity detection can discard quiet singing and sustained syllables.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'turbo': ROOT/'work/local/whisper-models/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf',
    'large': ROOT/'work/local/whisper-models/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('audio', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--model', choices=MODELS, default='turbo')
    ap.add_argument('--start', type=float, default=0)
    ap.add_argument('--end', type=float)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    if not args.audio.is_file() or not MODELS[args.model].is_dir():
        raise ValueError('Missing audio or local model')
    if args.output.exists():
        raise ValueError('Refusing to overwrite transcript')
    if not args.output.resolve().is_relative_to((ROOT/'work/local').resolve()):
        raise ValueError('Transcript must remain in ignored work/local')
    print(json.dumps(dict(audio=str(args.audio), output=str(args.output),
        model=args.model, start=args.start, end=args.end, threads=4, write=args.write)), flush=True)
    if not args.write:
        return
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio
    audio = decode_audio(str(args.audio), sampling_rate=16000)
    duration = len(audio)/16000
    stop = duration if args.end is None else min(duration, args.end)
    if not 0 <= args.start < stop:
        raise ValueError('Invalid crop')
    audio = audio[round(args.start*16000):round(stop*16000)]
    model = WhisperModel(str(MODELS[args.model]), device='cpu', compute_type='int8',
                         cpu_threads=4, local_files_only=True)
    segments, _ = model.transcribe(audio, language='ja', task='transcribe', beam_size=5,
        word_timestamps=True, vad_filter=False, condition_on_previous_text=False)
    doc = dict(model=args.model, status='unreviewed_machine_transcription',
        source_sha256=hashlib.sha256(args.audio.read_bytes()).hexdigest(),
        duration=duration, crop=[args.start,stop], complete=False, segments=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for segment in segments:
        row = asdict(segment)
        row['start'] += args.start
        row['end'] += args.start
        for word in row['words'] or []:
            word['start'] += args.start
            word['end'] += args.start
        doc['segments'].append(row)
        args.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('segment',len(doc['segments']),round(row['start'],2),round(row['end'],2),flush=True)
    doc['complete'] = True
    args.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
