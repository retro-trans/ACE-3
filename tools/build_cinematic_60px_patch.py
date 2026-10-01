"""0.9.16: reduce the cinematic text's leftward shift from 90 to 60 units.

Reuse the audited coordinate scan and whole-disc verification. Dry-run by
default; --write creates a new local test ISO while retaining 0.9.15 fixes.
"""
import build_cinematic_left_patch as patch

patch.VERSION = '0.9.16'
patch.BASE = patch.ROOT/'work/output/ACE3-English-0.9.15.iso'
patch.OUTPUT = patch.ROOT/'work/output/ACE3-English-0.9.16.iso'
patch.BASE_HASH = 'ec1932d24c6a44ee361fa1fe3ce1afcb2414b5d5e606c8d982d29965024c15f8'
patch.CONFIG_HASH = '2d426050e60246251f463cfdfdb24d58eeccb65f5917f9a49087eb343fef4698'
patch.FOLDER = patch.ROOT/'work/ui/cinematic_left_0916'
patch.SOURCE_COORDINATES = [(0, 'speaker', (-290, 145)), (1, 'dialogue', (-274, 165))]
patch.SHIFT = 30
patch.SPEAKER_MARGIN = 60
patch.TOTAL_SHIFT = -60

if __name__ == '__main__':
    writer = patch.writer
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = (
        patch.VERSION, patch.BASE, patch.OUTPUT, patch.BASE_HASH)
    writer.plan = patch.plan
    writer.main()
