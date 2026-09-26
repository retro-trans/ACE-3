"""Verify existing xdelta patches and add Retro Trans release metadata.

Defaults to a read-only preview. Requires a local retro-trans-tools checkout.
The sources JSON maps source SHA-256 hashes to local ISO paths; keep it private.
Published patch bytes are copied unchanged, never re-encoded.
"""

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--patch-dir", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--retro-trans-tools", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.retro_trans_tools.resolve()))
    from retro_trans.catalog import atomic_json, file_hashes, validate_manifest
    from retro_trans.core import PatchError, decode, engine_context, sha256_file
    from retro_trans.release import validate_directory

    manifest = validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
    sources_file = args.sources.resolve()
    sources = {k.lower(): (sources_file.parent / v).resolve() for k, v in
               json.loads(sources_file.read_text(encoding="utf-8")).items()}
    output = args.out.resolve()
    if output.exists():
        raise PatchError("Choose a new output directory; existing releases are never overwritten.")
    jobs = []
    for row in manifest["patches"]:
        source = sources[row["source_sha256"].lower()]
        patch = (args.patch_dir / row["patch"]).resolve()
        if not source.is_file() or source.stat().st_size != row["source_bytes"]:
            raise PatchError("Source missing or wrong size: " + row["patch"])
        if not patch.is_file() or patch.stat().st_size != row["patch_bytes"]:
            raise PatchError("Patch missing or wrong size: " + row["patch"])
        if sha256_file(patch) != row["patch_sha256"].lower():
            raise PatchError("Patch checksum mismatch: " + row["patch"])
        jobs.append((row, source, patch))
        print("{}: {} / {} -> {}".format(row["patch"], row["edition"],
              row["source_version"], manifest["version"]), flush=True)
    if not args.write:
        print("Preview: {} unchanged patches plus BUILD-MANIFEST.json, VALIDATION.json, "
              "and SHA256SUMS.txt. Use --write to hash sources and decode-verify every patch."
              .format(len(jobs)))
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    required = max(r["target_bytes"] for r, _, _ in jobs) + sum(r["patch_bytes"] for r, _, _ in jobs)
    if shutil.disk_usage(output.parent).free < required + 64 * 1024 * 1024:
        raise PatchError("Not enough space for patch copies and a verification ISO.")
    digests = {}
    for row, source, _ in jobs:
        if source not in digests:
            print("Verifying source: " + source.name, flush=True)
            digests[source] = file_hashes(source, ("sha256", "sha1"))
        if digests[source]["sha256"] != row["source_sha256"].lower():
            raise PatchError("Source checksum mismatch: " + row["patch"])
        if row.get("source_sha1", digests[source]["sha1"]) != digests[source]["sha1"]:
            raise PatchError("Source SHA-1 mismatch: " + row["patch"])
        row["source_sha1"] = digests[source]["sha1"]

    # All temporary files live inside this invocation's newly created directory.
    with tempfile.TemporaryDirectory(prefix=".retro-trans-verify-", dir=str(output.parent)) as temporary:
        stage = Path(temporary)
        with engine_context(cache=stage / "engine-cache") as engine:
            for row, source, patch in jobs:
                print("Decode-verifying: " + row["patch"], flush=True)
                copied = stage / row["patch"]
                shutil.copyfile(patch, copied)
                decoded = stage / "verification.part"
                decode(engine, source, copied, decoded, row["target_bytes"])
                hashes = file_hashes(decoded, ("sha256", "sha1"))
                if decoded.stat().st_size != row["target_bytes"] or hashes["sha256"] != row["target_sha256"].lower():
                    raise PatchError("Decoded output mismatch: " + row["patch"])
                if row.get("target_sha1", hashes["sha1"]) != hashes["sha1"]:
                    raise PatchError("Target SHA-1 mismatch: " + row["patch"])
                row["target_sha1"] = hashes["sha1"]
                decoded.unlink()
                print("Verified: " + row["patch"], flush=True)
        for source, hashes in digests.items():
            if sha256_file(source) != hashes["sha256"]:
                raise PatchError("A source changed during verification.")
        atomic_json(stage / "BUILD-MANIFEST.json", manifest)
        atomic_json(stage / "VALIDATION.json", {
            "schema_version": 1,
            "manifest_sha256": sha256_file(stage / "BUILD-MANIFEST.json"),
            "patches": [{"patch": r["patch"], "roundtrip_verified": True,
                         "target_sha256": r["target_sha256"]} for r, _, _ in jobs],
        })
        files = sorted(p for p in stage.iterdir() if p.is_file())
        checksums = "".join("{}  {}\n".format(sha256_file(p), p.name) for p in files)
        (stage / "SHA256SUMS.txt").write_bytes(checksums.encode("utf-8"))
        validate_directory(stage)
        output.mkdir()  # Exclusive: fail if another process created it meanwhile.
        for path in sorted(p for p in stage.iterdir() if p.is_file()):
            path.rename(output / path.name)
    print("Verified Retro Trans release: " + str(output))


if __name__ == "__main__":
    main()
