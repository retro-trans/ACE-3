# Branching Situation Reports, 0.1.45

The reported Shirahime dialogue is resource 4004002, table 1, text 20. Its
topic title is Federation Movements. Earlier scene inputs stopped before this
group of branching reports, leaving their active text in Japanese.

The missing resources are 4004002, 4004012, 4004022, 4004032, 4004042,
4004062, 4004072, 4004102, 4004112, 4004122, 4004142, 4004162, 4004192,
4004202, 4004212 and 4004222. They contain 142 nonempty rows: 141 Japanese
rows and a fullwidth D.O.M.E. title. All were read in scene order and locally
reviewed; no independent reviewer is claimed. Canonical names follow the
existing glossary and Encyclopedia entries.

`tools/build_branch_reports_patch.py` reads the source from the local 0.1.44
image and the ordered English bodies from
`work/translation/en/branch_reports_045.json`. It preserves the leading scene
commands verbatim, checks every embedded command against the original order,
and verifies the full nonempty row set. These are sparse tables: the null
slots before text 20 must remain null, rather than being compacted.

English strings are appended to the text table and its pointers updated.
The original string pool remains intact. Scene chunks other than the text
table remain byte-identical. Report titles use one line; dialogue is limited
to three lines, 460 measured units per line and 128 visible characters. Every
result is checked against all three menu fonts. Glossary links cannot straddle
lines. The Shirahime wording was shortened without dropping the explosion,
loss of colony functions, or casualties.

The audit scans active tables in all 4003xxx/4004xxx BND window resources,
including titles, rather than searching discarded string pools for Japanese.
It also checks the explicit 40-resource mission set supported by the existing
scene builders. Neighboring numeric IDs include legacy and unclassified
variants; their runtime use is not inferred from their IDs. The audit is not
a claim that all Japanese artwork or all unknown formats have been translated.

Run the builder without arguments and inspect the sample first. `--write`
creates a new 0.1.45 test ISO, verifies all archive payloads and disc files,
compares the 16 finished report bundles, and reruns the active-table audit on
the finished ISO. The output JSON includes source row hashes, English text,
line widths and coverage counts without exporting Japanese source scripts.

For runtime testing, fresh-boot 0.1.45 and load a normal memory-card save.
Open Federation Movements at the branch point, then check each available topic
and its glossary links. The user handles navigation. All route conditions and
images are preserved; in-game appearance remains pending.
