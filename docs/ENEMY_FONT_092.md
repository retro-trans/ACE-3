# Lock-on enemy names — 0.9.2

The screenshot's `???s??? ????10` matches **Monsuno type10** rendered through
the separate HUD font 2501. Previous font repairs covered 2500, used for
dialogue and menus, but missed 2501. The same sparse HUD font occurs in all
eight gameplay bundles 1200000–1200007.

The repair adds 32 ASCII aliases to existing fullwidth glyphs and supplies
47 missing characters from the game's complete font (resources 35/36).
Together these cover printable ASCII 32–126, fixing other translated target
names affected by the same missing-letter problem. No name text is changed.

The 256×256 linear 4-bit atlas keeps its dimensions, PSMT4HH GPU header and
palette. Added glyphs occupy unused atlas space; all 242 original glyphs
retain their exact mappings, UVs, metrics and pixel rectangles. The helper
temporarily treats the CPU's linear index buffer as PSMT4, then restores the
original texture header. It never changes the uploaded GPU format.

Run `C:/Python/python.exe tools/build_enemy_font_patch.py --preview` for a
dry-run plan and a local font proof. Add `--write` to build the new 0.9.2 ISO
from 0.9.1. The builder checks all original glyphs, printable ASCII coverage,
every archive payload and every disc file. The Deployment caption repair
from 0.9.1 is retained. The two outstanding CG movies remain unintegrated.

Runtime verification is pending. Fresh-boot and load a memory-card save to
check the Monsuno target and other enemies; an old emulator state retains
its cached font. This is a local test build, not a published release.
