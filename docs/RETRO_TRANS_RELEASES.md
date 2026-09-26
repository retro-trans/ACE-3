# Retro Trans release packaging

ACE3 uses the [Retro Trans release standard](https://github.com/retro-trans/retro-trans-tools/blob/main/docs/RELEASE_STANDARD.md).
The public 0.1.42 release contains a canonical `BUILD-MANIFEST.json`, `VALIDATION.json`, `SHA256SUMS.txt` and
four unchanged xdelta assets. Copies of the canonical metadata live in `docs/releases/0.1.42/`.

The stable game ID is `ace-3`, the platform is `PS2` and the language is `en`. Keep the edition names
**Original prologue** and **English prologue** stable in future releases. The original disc matches both choices;
each published translated disc matches only its own edition. The manifest includes SHA-256, byte sizes and
SHA-1 aliases for CHD identification; extracted disc bytes still require SHA-256 verification before patching.

## Verify existing patches

`tools/package_retro_trans.py` adapts already-built patches without changing their bytes. It uses a separate local
checkout of Retro Trans for its manifest validator and bundled xdelta engine. It does not upload anything.
Python 3.8 or later and the current Windows Retro Trans checkout are required for the bundled engine.

Prepare a manifest following the upstream standard, using the published 0.1.42 manifest as an example. Specify
the exact expected source, patch and target hashes/sizes from the build. `source_commit` identifies the translation
source snapshot. For 0.1.42 it points to the cleaned initial snapshot; see the release's source-history notice.

Keep a private `work/local/retro-trans-sources.json` mapping each source SHA-256 to an ISO path. Paths may be
absolute or relative to that JSON file. Never commit this file or any original/patched game image. Example shape:

```json
{
  "<source SHA-256 from the manifest>": "path/to/source.iso"
}
```

With the four existing patches in `work/release/`, preview the 0.1.42 package:

```text
python tools/package_retro_trans.py docs/releases/0.1.42/BUILD-MANIFEST.json --patch-dir work/release --sources work/local/retro-trans-sources.json --retro-trans-tools work/local/retro-trans-tools --out work/output/retro-trans-release
```

Inspect the edition/source routes, then repeat with `--write`. The output directory must not already exist.
The preview checks patch hashes and input sizes without writing files. The write pass hashes every source,
decodes every patch with Retro Trans's engine, compares output sizes and SHA-256 hashes, and validates the final
package using Retro Trans's own release validator. It also computes SHA-1 aliases. Verification ISOs are temporary;
the final directory contains only the unchanged patches and three metadata files. Allow space for all patch
copies plus the largest decoded ISO.

For newly encoded releases, upstream also supplies `python -m retro_trans.release build`; its configuration and
validation commands are documented in the linked standard. Do not replace a published patch with different bytes.
Use a new `0.x.y` version for changed game output and update the changelog.

## Publish and confirm discovery

Upload every listed patch and both `VALIDATION.json` and `SHA256SUMS.txt` first. Upload `BUILD-MANIFEST.json`
last, so the catalog does not discover an incomplete package. All patch assets in that release must be listed;
the existing versioned ACE3 manifest/checksum files can remain as supplemental documentation.

Retro Trans scans public stable releases hourly. A maintainer can also run **Refresh patch catalog** in that
repository's Actions page. Confirm the run succeeds and the catalog contains `retro-trans/ACE-3` / `v0.1.42`,
then use **Refresh catalog** in the app. Packaging validation verifies patch application, not in-game behavior.
