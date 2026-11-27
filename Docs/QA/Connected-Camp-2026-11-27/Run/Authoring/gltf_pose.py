"""Sample the packed linear animation tracks in the Havenline character GLB."""

from pathlib import Path
import json
import struct
import numpy as np
from scipy.spatial.transform import Rotation as Rotation, Slerp


class Model:
    def __init__(self, model_file):
        self.source_bytes = Path(model_file).read_bytes()
        json_size = struct.unpack_from("<I", self.source_bytes, 12)[0]
        self.document = json.loads(self.source_bytes[20 : 20 + json_size])
        self.binary = bytearray(self.source_bytes[28 + json_size :])
        self.nodes = self.document["nodes"]
        self.names = {descriptor["name"]: i for i, descriptor in enumerate(self.nodes)}
        self.parent = {
            entry: i
            for i, descriptor in enumerate(self.nodes)
            for entry in descriptor.get("children", [])
        }
        self.order = []

        def walk(i):
            self.order.append(i)
            for entry in self.nodes[i].get("children", []):
                walk(entry)

        for root in self.document["scenes"][0]["nodes"]:
            walk(root)

    def accessor(self, i):
        descriptor = self.document["accessors"][i]
        b = self.document["bufferViews"][descriptor["bufferView"]]
        dimensions = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16, "SCALAR": 1}[
            descriptor["type"]
        ]
        dtype = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[
            descriptor["componentType"]
        ]
        return np.frombuffer(
            self.binary,
            dtype=dtype,
            offset=b.get("byteOffset", 0) + descriptor.get("byteOffset", 0),
            count=descriptor["count"] * dimensions,
        ).reshape(-1, dimensions)

    def samples(self, clip, seconds):
        nodes_count = len(self.nodes)
        frames_count = len(seconds)
        translations = np.zeros((nodes_count, frames_count, 3))
        rotations = np.broadcast_to(
            [0.0, 0, 0, 1], (nodes_count, frames_count, 4)
        ).copy()
        scales = np.ones((nodes_count, frames_count, 3))
        tracks = {"rotation": rotations, "translation": translations, "scale": scales}
        for i, node in enumerate(self.nodes):
            for k, values in tracks.items():
                if k in node:
                    values[i] = node[k]
        a = next(
            descriptor
            for descriptor in self.document["animations"]
            if descriptor["name"] == clip
        )
        for entry in a["channels"]:
            sampler = a["samplers"][entry["sampler"]]
            key_times = self.accessor(sampler["input"]).flatten()
            key_values = self.accessor(sampler["output"])
            target = entry["target"]
            joint = target["node"]
            key = target["path"]
            u = np.clip(seconds, key_times[0], key_times[-1])
            tracks[key][joint] = (
                Slerp(key_times, Rotation.from_quat(key_values))(u).as_quat()
                if key == "rotation"
                else np.stack(
                    [np.interp(u, key_times, key_values[:, ax]) for ax in range(3)],
                    axis=1,
                )
            )
        return translations, rotations, scales

    def world(self, translations, rotations, scales):
        nodes_count, frames_count = translations.shape[:2]
        matrices = np.zeros((nodes_count, frames_count, 4, 4))
        matrices[:, :, 3, 3] = 1
        matrices[:, :, :3, :3] = (
            Rotation.from_quat(rotations.reshape(-1, 4))
            .as_matrix()
            .reshape(nodes_count, frames_count, 3, 3)
            * scales[:, :, None, :]
        )
        matrices[:, :, :3, 3] = translations
        for i in self.order:
            if i in self.parent:
                matrices[i] = matrices[self.parent[i]] @ matrices[i]
        return matrices

    def write(self, destination):
        document = json.dumps(self.document, separators=(",", ":")).encode()
        document += b" " * (-len(document) % 4)
        b = self.binary
        destination = Path(destination)
        temporary = destination.with_suffix(".tmp")
        temporary.write_bytes(
            struct.pack("<4sII", b"glTF", 2, len(document) + len(b) + 28)
            + struct.pack("<I4s", len(document), b"JSON")
            + document
            + struct.pack("<I4s", len(b), b"BIN\x00")
            + b
        )
        temporary.replace(destination)
