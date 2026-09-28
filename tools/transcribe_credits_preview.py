"""Local Whisper transcription for a credits capture. Dry-run by default."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'work/local/whisper-models/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('audio', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    if not args.audio.is_file():
        raise ValueError('Missing audio')
    if args.output.exists():
        raise ValueError('Refusing to replace transcript')
    if not args.output.resolve().is_relative_to((ROOT / 'work/local').resolve()):
        raise ValueError('Japanese transcript must remain in ignored local files')
    print(json.dumps(dict(audio=str(args.audio), output=str(args.output), model=str(MODEL), write=args.write)), flush=True)
    if not args.write:
        return
    from faster_whisper import WhisperModel
    model = WhisperModel(str(MODEL), device='cpu', compute_type='int8', cpu_threads=8, local_files_only=True)
    segments, info = model.transcribe(str(args.audio), language='ja', task='transcribe', beam_size=5,
        word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
    rows = []
    for segment in segments:
        rows.append(asdict(segment))
        print('segment', len(rows), round(segment.end, 2), flush=True)
        args.output.write_text(json.dumps(dict(model='large-v3-turbo', status='unreviewed_machine_transcription',
            complete=False, segments=rows), ensure_ascii=False, indent=2), encoding='utf-8')
    args.output.write_text(json.dumps(dict(model='large-v3-turbo', status='unreviewed_machine_transcription',
        complete=True, duration=info.duration, segments=rows), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
