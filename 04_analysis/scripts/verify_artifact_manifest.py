"""Verify published file hashes on LF or CRLF checkouts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    manifest = json.loads((ROOT / "ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    expected = manifest["sha256"]
    bad = []
    for relative, digest in expected.items():
        path = ROOT / relative
        actual = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if path.is_file() else None
        if actual != digest:
            bad.append(relative)
    if bad:
        raise SystemExit(f"Manifest mismatch ({len(bad)}): {bad[:10]}")
    print(f"Verified {len(expected)} published file hashes.")


if __name__ == "__main__":
    main()
