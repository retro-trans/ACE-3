# ACE3 glossary — 0.1.6

The glossary contains 42 entries: 27 characters, 8 organizations, 6 locations, and 1 technology term. Light Newman was added from the official Dragonar profile for the tutorial. It remains a partial reference; later dialogue terminology proposals are not yet all consolidated.

## Files

- `work/glossary/glossary.json`: canonical lookup data and field-level evidence.
- `work/glossary/sources.json`: 41 linked sources, access dates, and access limitations.
- `work/glossary/research_queue.json`: entry-specific questions and the next research batches.
- `docs/GLOSSARY_INDEX.md`: readable name index with links to naming sources.
- `tools/glossary.py`: read-only validation and lookup, using the Python standard library.

Japanese glossary text is limited to short names and terms. The original ISO remains unchanged. Dialogue is indexed by source offset and hash under `work/translation/en`; see [the dialogue work](TRANSLATING.md) for the partial 0.1.6 test build.

## Lookup

Run from the project root:

```powershell
python tools/glossary.py check
python tools/glossary.py lookup 'フェイ'
python tools/glossary.py lookup 'Fei Roshnante' --exact
python tools/glossary.py lookup 'Go' --exact --category character
python tools/glossary.py lookup 'char.ruri_hoshino' --json
```

Lookup searches names, sourced variants, nicknames, and stable IDs. It normalizes character width, case, and spaces without altering the stored spelling. Use `--exact` for short names. Multiple matches are returned together; the tool never silently chooses a referent and never rewrites translations. Exit codes: 0 for success, 1 for invalid data, 2 for a missing lookup.

## Reading an entry

`name.decision` is `researched` when a reviewed reference supports the current spelling, or `provisional` when a dispute or a working translation remains. Neither value means officially localized or verified on a game screen. Japanese labels are sourced reference forms, not claims of byte-exact game strings.

Every character has gender, nickname, personality, and role fields. Each fact has a value, source IDs, and a status:

- `sourced`: the referenced material supports the statement.
- `unknown`: no fact is asserted; the value is null. Listed sources were consulted but did not establish the fact for this continuity.
- `not_found_in_reviewed_sources`: no nickname was established for this continuity in the material reviewed. An empty list does not mean the character has no nickname.

Profiles describe the stated source-franchise incarnation unless explicitly scoped to ACE3. Their ages, ranks, relationships, loyalties, and later-life events must not be imported into the crossover without scene evidence. Personality notes summarize sources; they do not prescribe how to rewrite a line.

`game_presence.status` distinguishes `reference_confirmed` (attested by a game reference) from `franchise_context` (useful background whose game appearance still needs checking). Five entries are context-only. No entries are yet verified against the ISO or captured game scenes.

Aliases have explicit kinds. A spelling variant is different from an alternate identity, shortened name, or a guide's world label. In particular, alternate identities and nicknames must not be globally replaced with the main name. The tool performs no automatic replacement.

The 19-series checklist combines Akurasu's 18-row series list with the separately documented Plamo-Kyoshiro secret guest. Its participation labels follow those references; they are not measurements of dialogue coverage. Guest and unit-only participation must not be treated as a full story role.

## Current gaps

Seven names or labels are provisional: Faye Rochenante, Ange Raver, Jill Bardona, New Federation, Earth A, Earth B, and Baldora Drive. The JSON records the basis and competing forms where documented. Earth A/B are reference labels; no matching Japanese A/B label has been invented.

Six personality fields remain unknown: Marina, Ange, Jill, Akito's film incarnation, Hikaru's film incarnation, and Asap. Additional nickname research is also needed. Sources that combine multiple adaptations were not used to fill gaps from a different incarnation.

No text-box dimensions, maximum character counts, abbreviations, or relocation implementation have been established. These require later game inspection. No stat terminology from the removed rules has been reinstated.

## Maintaining the data

Research a missing term before using a new canonical spelling. Add a source with its actual access method and date; indexed excerpts must not be represented as full-page review. Keep brief paraphrases and short lookup labels, not copied biographies or Japanese scripts. Favor the relevant franchise/game wiki over an inconsistent corpus spelling, as required by `BASE_RULES.md`. A disagreement between references remains explicit until resolved.

Use stable IDs and retain documented variants. Put sources on the specific field they support, record continuity, and add unanswered questions to both the entry and research queue. Gender must come from evidence, never from a name. Pronouns in a translation still require identifying the referent from scene context.

Preview scripted changes and inspect actual examples before writing. Apply any future meaning fixes first and glossary-name fixes afterward, with corrected spellings on the agents' do-not-touch list. Run the read-only check after an edit, update the reading index, increment the 0.x.y release version, and record the change in `docs/CHANGELOG.md`.
