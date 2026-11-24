"""Restore the exact Level 1 furnace from its versioned GitHub parts."""
import hashlib
import os
from pathlib import Path
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
STUDIO = PROJECT / "assets" / "studio"
FURNACE = "hearth_trial_02.glb"
PARTS = (
    ("hearth_trial_02.part00", "3d3a9855b1be7cbf8a31912f3da8b6f2a0c26ac5dfe2f206e1a5d577c4031a94"),
    ("hearth_trial_02.part01", "9a5f638862150a88caea1f5b9ca0b53d98e88e9e773209828a5fc7e37fb307da"),
    ("hearth_trial_02.part02", "852b0f438a598ce48c52ee23963bebbeb9eca20c8ac722f128460258eefeca95"),
)
EXPECTED = {
    FURNACE: "35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a",
    "purchase_pad_v5.glb": "d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb",
    "starter_ground_wood_lod.glb": "31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554",
    "wood_bundle_v3.glb": "1004ea2f41751bf79ad10ab0165c60a05e5ee581d35095913a0794f16931abd9",
}

def verify(path, expected):
    with path.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch: {path.name}")

def main():
    for name, digest in EXPECTED.items():
        if name != FURNACE:
            verify(STUDIO / name, digest)
    sources = [(STUDIO / "parts" / name, digest) for name, digest in PARTS]
    for source, digest in sources:
        verify(source, digest)
    target = STUDIO / FURNACE
    if target.exists():
        verify(target, EXPECTED[FURNACE])
    else:
        fd, tmp_name = tempfile.mkstemp(prefix=".hearth-", dir=STUDIO)
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as output:
                assembled = hashlib.sha256()
                for source, expected in sources:
                    part = hashlib.sha256()
                    with source.open("rb") as handle:
                        while data := handle.read(1024 * 1024):
                            part.update(data)
                            assembled.update(data)
                            output.write(data)
                    if part.hexdigest() != expected:
                        raise SystemExit(f"Checksum changed while reading: {source.name}")
            if assembled.hexdigest() != EXPECTED[FURNACE]:
                raise SystemExit("Assembled furnace checksum mismatch")
            os.link(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
    print("Verified all four Level 1 studio assets.")

if __name__ == "__main__":
    main()
