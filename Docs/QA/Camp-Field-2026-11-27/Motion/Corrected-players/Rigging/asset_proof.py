"""Compare original geometry/materials to the fitted game-body GLB and its bind pose."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from glb_helper import Glb
from sleeve_fit import displacement
from guide import transforms, transformed


def inventory(model):
    _, matrices = transforms(model.doc)
    skin = model.doc.get("skins", [{}])[0]
    bound = np.asarray([matrices[i] for i in skin.get("joints", [])])
    inverse = None
    if "inverseBindMatrices" in skin:
        inverse = model.read(skin["inverseBindMatrices"]).reshape((-1, 4, 4)).transpose(0, 2, 1)
    textures = []
    for image in model.doc["images"]:
        view = model.doc["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        image_bytes = model.blob[start:start + view["byteLength"]]
        textures.append(hashlib.sha256(image_bytes).hexdigest())
    pieces = []
    for i, node in enumerate(model.doc["nodes"]):
        if "mesh" not in node:
            continue
        for surface in model.doc["meshes"][node["mesh"]]["primitives"]:
            attrs = surface["attributes"]
            points = transformed(model.read(attrs["POSITION"]), matrices[i])
            topology = hashlib.sha256(model.read(surface["indices"]).tobytes()).hexdigest()
            uv = hashlib.sha256(model.read(attrs["TEXCOORD_0"]).tobytes()).hexdigest()
            patch = {"vertices": len(points), "faces": len(model.read(surface["indices"])) // 3, "topology": topology, "uv": uv}
            if inverse is not None:
                ws = model.read(attrs["WEIGHTS_0"])
                js = model.read(attrs["JOINTS_0"])
                drivers = (bound @ inverse)[js]
                deformed = np.einsum("ij,ijab,ib->ia", ws, drivers, np.c_[points, np.ones(len(points))])[:, :3]
                patch.update(rest_error_m=float(np.max(np.linalg.norm(deformed - points, axis=1))),
                             weight_sum_max_error=float(np.max(np.abs(ws.sum(axis=1)-1))),
                             influenced_bones=int(len(set(js[ws > 1e-4]))))
            pieces.append((patch, points))
    return pieces, textures


def proof(raw_path, runtime_path, recipe_path):
    original = Glb(raw_path)
    runtime = Glb(runtime_path)
    old_pieces, old_images = inventory(original)
    new_pieces, new_images = inventory(runtime)
    materials_identical = original.doc["materials"] == runtime.doc["materials"]
    recipe = json.loads(recipe_path.read_text())
    expected = old_images.copy()
    for patch in recipe.get("texture_corrections", []):
        expected[patch["image"]] = patch["sha256"]
    if expected != new_images or not materials_identical or len(old_pieces) != len(new_pieces):
        raise ValueError("Material or geometry count changed")
    for (old, old_points), (new, new_points) in zip(old_pieces, new_pieces):
        if any(old[k] != new[k] for k in ("vertices", "faces", "topology", "uv")):
            raise ValueError("Mesh topology/UV changed")
        low, high = old_points.min(axis=0), old_points.max(axis=0)
        mid=(low+high)/2;mid[1]=low[1]
        normalized = (old_points-mid)*(1.75/(high[1]-low[1]))
        delta = new_points-normalized
        new["shape_max_change_m"] = float(np.max(np.linalg.norm(delta, axis=1)))
        new["raw_span_over_stature"] = float(np.ptp(normalized[:,0]) / np.ptp(normalized[:,1]))
        new["bound_span_over_stature"] = float(np.ptp(new_points[:,0]) / np.ptp(new_points[:,1]))
        sleeve=recipe.get("sleeve_fit")
        if sleeve:
            limit = sleeve["extension_each_m"]
            detached = (abs(normalized[:,0])<sleeve["shoulder_x"]) | (normalized[:,1]>1.22) | (normalized[:,1]<.84)
            furthest = abs(normalized[:,0])>sleeve["wrist_x"]+.025
            new["torso_head_lower_body_max_change_m"]=float(np.max(abs(delta[detached])))
            new["all_mesh_vertical_depth_max_change_m"]=float(np.max(abs(delta[:,1:])))
            new["mittens_translation_error_m"]=float(np.max(abs(abs(delta[furthest,0])-limit)))
            if (max(new[k] for k in ("torso_head_lower_body_max_change_m","all_mesh_vertical_depth_max_change_m","mittens_translation_error_m"))>1.0e-4
                    or abs(new["bound_span_over_stature"]-sleeve["source_span_over_stature"])>.001
                    or new["shape_max_change_m"]>limit+1e-5):
                raise ValueError(new)
        elif new["shape_max_change_m"]>1e-5:
            raise ValueError("Unrequested rest-pose shape change")
        if new["rest_error_m"]>1e-5 or new["weight_sum_max_error"]>1e-5:
            raise ValueError("Bad bind/weights")
    return {"raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "runtime_sha256": hashlib.sha256(runtime_path.read_bytes()).hexdigest(),
            "skin_bones": len(runtime.doc["skins"][0]["joints"]), "materials_unchanged": materials_identical,
            "source_maps_sha256": old_images, "embedded_maps_sha256": new_images,
            "approved_map_edits": recipe.get("texture_corrections", []), "parts": [part for part, _ in new_pieces]}


if __name__ == "__main__":
    print(json.dumps(proof(*(Path(f) for f in sys.argv[1:4])),indent=2))
