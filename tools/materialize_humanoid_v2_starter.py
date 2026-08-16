#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "digital-characters" / "humanoid-v2" / "import" / "starter-pack"
OUTPUT = ROOT / "digital-characters" / "humanoid-v2" / "runtime" / "starter.pack"
EXPECTED_SHA256 = "2457cd8e7ad5955c6c443698a3408b93eafe717df05766eb0a24b39d6372f996"
EXPECTED_PARTS = 17


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
    if not payload.startswith(b"SRN2PACK"):
        print("starter pack magic is invalid", file=sys.stderr)
        return 4
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)
    print(f"materialized {OUTPUT.relative_to(ROOT)} ({len(payload)} bytes, sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
