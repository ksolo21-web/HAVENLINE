"""Read original GLB chunks and append aligned glTF accessors."""
import json
import struct
import numpy as np


class Glb:
    def __init__(self, path):
        data = path.read_bytes()
        length = struct.unpack_from("<I", data, 12)[0]
        self.doc = json.loads(data[20:20 + length])
        self.blob = bytearray(data[28 + length:])

    def read(self, index):
        acc = self.doc["accessors"][index]
        view = self.doc["bufferViews"][acc["bufferView"]]
        size = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[acc["type"]]
        dtype = np.dtype({5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[acc["componentType"]])
        shape = (acc["count"], size)
        stride = view.get("byteStride", size * dtype.itemsize)
        start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        return np.ndarray(shape, dtype, self.blob, start, (stride, dtype.itemsize)).copy()

    def add(self, value, kind, typ, target=None, limits=False):
        value = np.ascontiguousarray(value)
        self.blob.extend(b"\0" * (-len(self.blob) % 4))
        view = dict(buffer=0, byteOffset=len(self.blob), byteLength=value.nbytes)
        if target:
            view["target"] = target
        self.blob.extend(value.tobytes())
        ref = len(self.doc["bufferViews"])
        self.doc["bufferViews"].append(view)
        accessor = dict(bufferView=ref, componentType=kind, count=len(value), type=typ)
        if limits:
            accessor.update(min=value.min(axis=0).reshape(-1).tolist(),
                            max=value.max(axis=0).reshape(-1).tolist())
        self.doc["accessors"].append(accessor)
        return len(self.doc["accessors"]) - 1

    def save(self, path):
        self.blob.extend(b"\0" * (-len(self.blob) % 4))
        self.doc["buffers"][0]["byteLength"] = len(self.blob)
        header = json.dumps(self.doc, separators=(",", ":")).encode("utf-8")
        header += b" " * (-len(header) % 4)
        length = 28 + len(header) + len(self.blob)
        path.write_bytes(struct.pack("<4sIII4s", b"glTF", 2, length, len(header), b"JSON")
                         + header + struct.pack("<I4s", len(self.blob), b"BIN\0") + self.blob)


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True).clip(1e-10)


