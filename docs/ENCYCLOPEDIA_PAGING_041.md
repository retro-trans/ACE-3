# Encyclopedia page continuity — 0.1.41

Base: 0.1.40. Output: `work/output/ACE3-English-0.1.41.iso`.

The supplied Zentradi screenshots show a genuine gap: page one ends at "insuff", while page two starts at "fighting instinct". Table 3019 entry 35 still contains the complete sentence. The missing text includes the rest of "insufficient" and "immigration policy and their innate".

The menu body uses a 190-character drawing limit. The ELF callback at 0x2f4760 calls the text-capacity setter at 0x2b6fb0 with 190 at 0x2f47c8; its pointer is stored at 0x369a20. Taking the first 189 visible, non-newline characters reproduces the screenshot's exact "insuff" cutoff. The next screenshot begins at stored line index 8. Thus the renderer stops drawing before the eight-line page advance, dropping the tail of a dense English page. The builder verifies the callback instructions and pointer but does not modify them.

Audit all 88 entries in menu bundles 4002050, 4002054 and 4002057. Of these, 57 exceed the observed 189-character cutoff; three more exceed the conservative 180-character budget. Repage those 60 entries (180 changed instances), retaining original line widths, every word, all punctuation, and exact glossary IDs/labels/order. Keep paragraphs together where possible; split long paragraphs only between existing complete lines. Add blank lines to finish each eight-line page before the next page begins. No page exceeds 180 visible non-newline characters or 187 characters including its newlines. Entries use at most four pages. The densest old page contained 275 visible non-newline characters.

The Zentradi entry remains two pages: the complete naturalization paragraph on page one, and the complete paragraph beginning "However" on page two. Some other entries gain pages or have extra space at the bottom. The 28 already-safe entries remain byte-for-byte unchanged as active strings. All original string pools are retained and changed strings appended. Fonts, layouts, allocations and executable remain unchanged, as do the four separate gameplay glossary copies, whose window is not this eight-line menu panel.

Tools: `tools/build_encyclopedia_paging_patch.py` (dry-run default) and `tools/test_encyclopedia_paging_patch.py`. The generated English pagination catalog is `work/translation/en/encyclopedia_paging_041.json`; screenshots and validation are under `work/ui/encyclopedia_paging_041/`.

Runtime check: boot fresh, load a normal memory-card save, and page down/up through Zentradi. Its second page must begin with "However" and show the complete sentence. Check longer unlocked entries too. The user controls navigation; runtime verification remains pending.

Final validation: all five pagination/finished-disc tests and four boot-metadata tests pass without skips. Tests reproduce the reported cutoff, verify complete words and links for all 88 entries in all three menu copies, enforce page character/width limits and confirm preservation of unrelated resources and the four gameplay copies. The builder verifies 10,344 archive payloads and 133 disc files. Output size: 4,447,076,352 bytes. SHA-256: `8f439b6e501abf6ab44ebe92581f48c2764d6550c3912df6a98cf814b10375be`.
