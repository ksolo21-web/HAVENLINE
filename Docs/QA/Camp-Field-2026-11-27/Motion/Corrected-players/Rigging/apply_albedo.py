"""Replace one embedded color map while retaining the original glTF geometry and PBR maps."""
import hashlib


def replace_texture(model, index, content, expected):
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("Corrected texture does not match the approved image")
    image = model.doc["images"][index]
    view = model.doc["bufferViews"][image["bufferView"]]
    old_start = view.get("byteOffset", 0)
    old_end = (old_start + view["byteLength"] + 3) & ~3
    padded = content + b"\0" * (-len(content) % 4)
    difference = len(padded) - (old_end - old_start)
    model.blob[old_start:old_end] = padded
    for other in model.doc["bufferViews"]:
        if other is view:
            continue
        start = other.get("byteOffset", 0)
        if start >= old_end:
            other["byteOffset"] = start + difference
        elif start + other["byteLength"] > old_start:
            raise ValueError("Color-map range overlaps another buffer view")
    view["byteLength"] = len(content)
