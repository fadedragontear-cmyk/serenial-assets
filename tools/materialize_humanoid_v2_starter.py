#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "digital-characters" / "humanoid-v2" / "import" / "starter-pack"
OUTPUT = ROOT / "digital-characters" / "humanoid-v2" / "runtime" / "starter.pack"
EXPECTED_SHA256 = "4a9a4cf67317ca4a723b080145a298f53a76898e0a54cef5d156c39ce1c07260"
EXPECTED_PARTS = 54
EXPECTED_MODULES = 30


def main() -> int:
    parts = sorted(PARTS.glob("*.b64part"))
    if len(parts) != EXPECTED_PARTS:
        print(f"expected {EXPECTED_PARTS} parts, found {len(parts)}", file=sys.stderr)
        return 2
    encoded = "".join(part.read_text(encoding="ascii").strip() for part in parts)
    payload = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        print(f"starter pack sha256 mismatch: {digest}", file=sys.stderr)
        return 3
    try:
        raw = zlib.decompress(payload)
        header_length = struct.unpack("<I", raw[:4])[0]
        header = json.loads(raw[4:4 + header_length])
    except Exception as error:
        print(f"starter pack could not be decoded: {error}", file=sys.stderr)
        return 4
    if header.get("schema") != 2 or header.get("cell") != 192:
        print(f"unexpected starter pack contract: {header}", file=sys.stderr)
        return 5
    if len(header.get("modules", [])) != EXPECTED_MODULES:
        print(f"expected {EXPECTED_MODULES} modules, found {len(header.get('modules', []))}", file=sys.stderr)
        return 6
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)
    print(
        f"materialized {OUTPUT.relative_to(ROOT)} "
        f"({len(payload)} compressed bytes, {len(raw)} decoded bytes, sha256={digest})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
