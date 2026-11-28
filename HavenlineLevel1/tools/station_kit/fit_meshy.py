"""Pack an opaque Meshy base color as JPEG without changing topology or UVs."""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

from PIL import Image


def fit(source: Path, destination: Path):
    payload = source.read_bytes()
    signature, version, total, size, tag = struct.unpack_from("<4sIIII", payload)
    assert (signature, version, total, tag) == (b"glTF", 2, len(payload), 0x4E4F534A)
    doc = json.loads(payload[20:20 + size])
    raw = payload[28 + size:]
    assert len(doc["images"]) == 1
    image = doc["images"][0]
    view = doc["bufferViews"][image["bufferView"]]
    start = view["byteOffset"]
    assert all(v is view or v.get("byteOffset", 0) + v["byteLength"] <= start for v in doc["bufferViews"])
    with Image.open(io.BytesIO(raw[start:start + view["byteLength"]])) as color:
        assert color.mode == "RGB"
        jpg = io.BytesIO()
        color.save(jpg, format="JPEG", quality=94, subsampling=0, optimize=True)
    binary = raw[:start] + jpg.getvalue()
    binary += b"\x00" * (-len(binary) % 4)
    view["byteLength"] = jpg.tell()
    doc["buffers"][0]["byteLength"] = len(binary)
    image["mimeType"] = "image/jpeg"
    document = json.dumps(doc, separators=(",", ":")).encode()
    document += b" " * (-len(document) % 4)
    destination.write_bytes(
        struct.pack("<4sIIII", b"glTF", 2, 28 + len(document) + len(binary), len(document), 0x4E4F534A)
        + document + struct.pack("<I4s", len(binary), b"BIN\0") + binary
    )
    return hashlib.sha256(destination.read_bytes()).hexdigest()


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("source", type=Path)
    cli.add_argument("destination", type=Path)
    args = cli.parse_args()
    print(fit(args.source, args.destination))
