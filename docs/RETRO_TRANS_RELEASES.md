# Retro Trans release packaging

ACE3 follows the [Retro Trans release standard](https://github.com/retro-trans/retro-trans-tools/blob/main/docs/RELEASE_STANDARD.md).
Publish only **English prologue**, using stable game ID `ace-3`, platform `PS2` and language `en`.
The user discontinued the non-movie edition on 2026-09-26. Preserve its historical binary identities in withdrawn catalog records, not selectable downloads.

## Build and validate

For 0.9.16, master `ACE3-English-0.9.16.iso` with `tools/relayout_disc.py` (dry run, then `--write`). Use `tools/package_release_0916.py --source-commit <full-source-commit>` with Python 3.12+ (dry run, then `--write`). The reviewed upstream standard and validator are pinned to commit `36f90fcb316195a537aaa7d25361ca2add5a0b1d`, extracted under `work/local/retro-trans-release-0916/retro-trans-tools-36f90fcb316195a537aaa7d25361ca2add5a0b1d`. Routes are original disc and exact published English-prologue 0.9.3; earlier published editions use their existing upgrade chain. Record candidate and public catalog route verification under `docs/releases/0.9.16/`. Local test ISO bytes differ from the mastered release and are not inputs to the published upgrade patch.

For 0.9.3, prepare and integrate the two reviewed story movies with `tools/build_remaining_movies_patch.py --prepare`, then `--write`, based on local 0.9.2. Inspect the decoded frame samples and validation reports. Master `ACE3-English-0.9.3.iso` with `tools/relayout_disc.py` (dry run, then `--write`). Refresh the upstream tools checkout and review its release standard. Run `tools/package_release_093.py --source-commit <full-source-commit>` (dry run, then `--write`). Routes are original disc and exact published English-prologue 0.9.0; earlier supported versions route through their existing upgrades. Verify candidate routes, uploaded hashes and public catalog routes for 0.9.3.

For 0.9.0, master the latest local 0.1.68 image with `tools/relayout_disc.py ACE3-English-0.1.68.iso` (dry run, then `--write`). Name the verified image and JSON report `ACE3-English-0.9.0-orig-layout.iso` / `.json` under `work/release/`, and update the report's output path. Refresh the upstream checkout under `work/local/retro-trans-release-065` and inspect its current release standard. Run `tools/package_release_090.py --source-commit <full-source-commit>` (dry run, then `--write`). Routes are the original disc and exact published English-prologue 0.1.65; older supported releases use existing intermediate upgrades. Verify published routes with version `0.9.0` and the refreshed tools checkout.

For 0.1.65, run `tools/relayout_disc.py ACE3-English-0.1.64.iso` first, then with `--write`. This release gives the remastered 0.1.64 content a distinct binary identity. Check out the current Retro Trans Tools sources under ignored `work/local/retro-trans-release-065`, inspect `tools/package_release_065.py --source-commit <full-source-commit>`, then repeat with `--write`. Its routes are original disc and published English-prologue 0.1.47. Use `--retro-trans-tools work/local/retro-trans-release-065` with the route verifier to check all active previous versions, including multi-step upgrades.

For 0.1.47, preview `python tools/relayout_disc.py ACE3-English-0.1.47.iso`, inspect the planned extents, then repeat with `--write`.
Preview `python tools/package_release_047.py --source-commit <full-source-commit>`, then repeat with `--write`.
The packager invokes the current Retro Trans builder for the original-disc full patch and the matching published 0.1.42 upgrade.
It verifies source identities, decodes each patch, compares the complete target image, adds SHA-1 aliases for DVD CHD identification, and validates the canonical package.
Only patches, `BUILD-MANIFEST.json`, `VALIDATION.json` and `SHA256SUMS.txt` belong in the release assets. Never upload an ISO, private configuration, dump or extracted game data.

The general `tools/package_retro_trans.py` remains available to validate existing patches without changing their bytes. Keep its source-path mapping private under `work/local/`.
New translations require a new `0.x.y` version; never replace a published patch with different bytes.

## Publish and confirm discovery

Follow the [SRW-Z release format](https://github.com/retro-trans/SRW-Z/releases): Apply, changes, release status, included content, translation details, acknowledgements, Source code and Contribute. Keep local notes and canonical metadata under `docs/releases/`.
Stage a draft, upload every listed patch plus `VALIDATION.json` and `SHA256SUMS.txt`, and upload `BUILD-MANIFEST.json` last. Check uploaded sizes and hashes before publishing.

Run **Refresh patch catalog** in Retro Trans Tools Actions after publishing. Confirm its validator succeeds and the release appears in the public catalog.
Use `tools/verify_release_routes.py --version 0.1.47 --catalog <catalog.json>` to check original-disc and upgrade paths, current-version no-op, discontinued-edition exclusion and unknown-disc rejection.
Add `--manifest <BUILD-MANIFEST.json>` only for a candidate preview against a catalog that does not yet contain the release.

Removing an older published patch requires updating its live manifest, validation report and checksums, and moving its exact catalog identities into `withdrawn_releases` with the maintainer's reason. Retro Trans 0.3.1 or later supports refreshing these withdrawals from older cached catalogs. The remaining patch bytes stay unchanged.

Packaging and catalog checks verify patch application, not in-game behavior. Keep runtime limitations explicit in the notes.
