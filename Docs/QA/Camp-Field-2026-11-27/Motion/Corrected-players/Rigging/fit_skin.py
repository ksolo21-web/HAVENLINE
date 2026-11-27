"""Bind an original static body to Havenline's compact armature using measured landmarks.

The recipe supplies the signed source digest, its facing angle, and the target
joint centers in metre coordinates after overall stature/facing normalization.
Texture bytes, UVs, topology, normals and the body's proportions are preserved.
"""
import argparse
import hashlib
import io
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from glb_helper import Glb, unit
from sleeve_fit import arm_joint, displacement
from guide import landmarks, transformed, transforms, warp


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def controller_data(controller):
    skin = controller.doc["skins"][0]
    parents, matrices = transforms(controller.doc)
    all_points, all_weights, all_normals = [], [], []
    for i, node in enumerate(controller.doc["nodes"]):
        if node.get("skin") != 0:
            continue
        for surface in controller.doc["meshes"][node["mesh"]]["primitives"]:
            attrs = surface["attributes"]
            points = transformed(controller.read(attrs["POSITION"]), matrices[i])
            joints = controller.read(attrs["JOINTS_0"]).astype(int)
            weights = controller.read(attrs["WEIGHTS_0"]).astype(float)
            full = np.zeros((len(points), len(skin["joints"])))
            np.add.at(full, (np.arange(len(points))[:, None], joints), weights)
            all_points.append(points)
            all_weights.append(full)
            all_normals.append(unit(controller.read(attrs["NORMAL"]) @ np.linalg.inv(matrices[i][:3, :3])))
    return skin["joints"], parents, matrices, np.vstack(all_points), np.vstack(all_normals), np.vstack(all_weights)


def original_meshes(asset):
    _, matrices = transforms(asset.doc)
    geometry = {}
    for i, node in enumerate(asset.doc["nodes"]):
        if "mesh" not in node:
            continue
        if node["mesh"] in geometry:
            raise ValueError("Handle mesh instances explicitly before binding")
        if "skin" in node or "weights" in node:
            raise ValueError("Inspect the original skin or shape keys before rebinding")
        mesh = asset.doc["meshes"][node["mesh"]]
        if any(s.get("targets") or s.get("mode", 4) != 4 for s in mesh["primitives"]):
            raise ValueError("Unsupported original primitive for this static-body recipe")
        geometry[node["mesh"]] = (node.get("name", mesh.get("name", "Body")), matrices[i])
    return geometry


def fit(asset, controller, recipe):
    if asset.doc.get("skins") or asset.doc.get("animations"):
        raise ValueError("Original has rigging or animation; assess and reuse it before replacement")
    geometry = original_meshes(asset)
    arrays = []
    for index, (_, matrix) in geometry.items():
        for surface in asset.doc["meshes"][index]["primitives"]:
            arrays.append(transformed(asset.read(surface["attributes"]["POSITION"]), matrix))
    facing = Rotation.from_euler("Y", recipe["face_y_degrees"], degrees=True).as_matrix()
    all_points = np.vstack(arrays) @ facing.T
    low, high = all_points.min(axis=0), all_points.max(axis=0)
    midpoint = (low + high) / 2.
    midpoint[1] = low[1]
    stature = float(recipe.get("stature_m", 1.75)) / (high[1] - low[1])
    normalize = np.eye(4)
    normalize[:3, :3] = facing * stature
    normalize[:3, 3] = -midpoint * stature

    ids, parents, matrices, points, normals, weights = controller_data(controller)
    controller_names = landmarks(controller)
    measured = recipe.get("measured_bind_centers") or None
    original_joints = np.asarray([matrices[i][:3, 3] for i in ids])
    fitted_joints = warp(original_joints, measured, controller_names)
    sleeve = recipe.get("sleeve_fit")
    for row, i in enumerate(ids):
        if arm_joint(controller.doc["nodes"][i]["name"]):
            fitted_joints[row,0] += displacement(fitted_joints[row,0],sleeve)[0]
    frames = {i: matrices[i].copy() for i in ids}
    for i, p in zip(ids, fitted_joints):
        frames[i][:3, 3] = p

    mesh_roots = [{"mesh": index, "name": name, "skin": 0} for index, (name, _) in geometry.items()]
    bone_node = {i: len(mesh_roots) + j for j, i in enumerate(ids)}
    bones, roots = [], []
    for i in ids:
        original = controller.doc["nodes"][i]
        parent = parents.get(i)
        world = frames[i]
        local = np.linalg.inv(frames[parent]) @ world if parent in frames else world
        bone = {"name": original["name"], "translation": local[:3, 3].tolist(),
                "rotation": Rotation.from_matrix(local[:3, :3]).as_quat().tolist()}
        children = [bone_node[c] for c in original.get("children", []) if c in bone_node]
        if children:
            bone["children"] = children
        bones.append(bone)
        if parent not in frames:
            roots.append(bone_node[i])
    if len(roots) != 1:
        raise ValueError("Expected one compact humanoid skeleton")
    asset.doc["nodes"] = mesh_roots + bones
    asset.doc["scenes"] = [{"name": recipe["name"], "nodes": list(range(len(mesh_roots))) + roots}]
    asset.doc["scene"] = 0
    inverse = np.asarray([np.linalg.inv(frames[i]).T.reshape(16) for i in ids], dtype="<f4")
    bind = asset.add(inverse, 5126, "MAT4")
    asset.doc["skins"] = [{"name": recipe["name"] + "Rig", "joints": [bone_node[i] for i in ids],
                          "skeleton": roots[0], "inverseBindMatrices": bind}]
    kd_tree = cKDTree(points)
    names = [controller.doc["nodes"][i]["name"] for i in ids]
    for index, (name, matrix) in geometry.items():
        m = normalize @ matrix
        if np.linalg.det(m[:3, :3]) <= 0.:
            raise ValueError("Negative determinant requires an explicit winding correction")
        for surface in asset.doc["meshes"][index]["primitives"]:
            attrs = surface["attributes"]
            verts = transformed(asset.read(attrs["POSITION"]), m)
            dirs = unit(asset.read(attrs["NORMAL"]) @ np.linalg.inv(m[:3, :3]))
            ref = warp(verts, {k: controller_names[k] for k in measured} if measured else None, measured)
            distances, near = kd_tree.query(ref, k=8)
            similarity = np.maximum(.05, (normals[near] * dirs[:, None, :]).sum(axis=2))
            proximity = similarity / np.maximum(distances, .0002)**2
            proximity /= proximity.sum(axis=1, keepdims=True)
            mapped = np.einsum("ij,ijk->ik", proximity, weights[near])
            # The new hair lengths and boot tops differ from the compact donor.
            # Anchor the actual curls by their material and location so the
            # shoulder and sleeve cannot drag them down during the running pump.
            tex = asset.doc["materials"][surface.get("material", 0)]["pbrMetallicRoughness"]["baseColorTexture"]["index"]
            image = asset.doc["images"][asset.doc["textures"][tex]["source"]]
            view = asset.doc["bufferViews"][image["bufferView"]]
            start = view.get("byteOffset", 0)
            pixels = np.asarray(Image.open(io.BytesIO(asset.blob[start:start+view["byteLength"]])).convert("RGB"))
            uv = np.clip(asset.read(attrs["TEXCOORD_0"]), 0., 1.)
            rgb = pixels[np.minimum((uv[:,1]*pixels.shape[0]).astype(int),pixels.shape[0]-1),
                         np.minimum((uv[:,0]*pixels.shape[1]).astype(int),pixels.shape[1]-1)].astype(float)
            lateral, height, front = verts.T
            brown = (rgb[:,0] > rgb[:,2]*.91) & (rgb.max(axis=1) < 113.)
            hair = brown & (height>recipe["hair_edge"]) & (abs(lateral)>.12) & (abs(lateral)<.449)
            head = np.clip((height-recipe["head_blend_m"][0]) / np.ptp(recipe["head_blend_m"]), 0.,1.)
            head = np.maximum(head, hair)
            mapped *= 1.-head[:,None]
            mapped[:,names.index("Head")] += head
            # These boots have different leather/fleece geometry from C1.
            # Bind their actual heel, forefoot, and cuff instead of inheriting
            # tiny fastener patches from another body's boots.
            for side,sign in [("L",1),("R",-1)]:
                top = recipe["boot_top_m"]
                part = (sign*lateral>0.) & (height<top+.04)
                if not np.any(part):continue
                toe_z = measured["Toe."+side][2]
                toes = np.clip((front[part]-toe_z+.027)/.072,0.,1.)
                toes = toes*toes*(3-2*toes)*(1.-np.clip((height[part]-.095)/.065,0.,1.))
                shin = np.clip((height[part]-.17)/(top-.17),0.,1.)
                shin = shin*shin*(3-2*shin)*.87
                cover = np.clip((top+.04-height[part])/.043,0.,1.)
                mapped[part,:] *= 1.-cover[:,None]
                mapped[part,names.index("Foot."+side)] += cover*(1.-shin-toes)
                mapped[part,names.index("Toe."+side)] += cover*toes
                mapped[part,names.index("Shin."+side)] += cover*shin
            if name in recipe.get("rigid_meshes", {}):
                mapped[:] = 0.
                mapped[:, names.index(recipe["rigid_meshes"][name])] = 1.
            # Only extend cloth from armpit to cuff. Mitten vertices translate
            # together; hair, head, torso, belt and non-arm anatomy keep shape.
            arm_share = mapped[:, [arm_joint(label) for label in names]].sum(axis=1)
            low= np.clip((verts[:,1]-.84)/.06,0.,1.)
            high= np.clip((1.21-verts[:,1])/.055,0.,1.)
            arm_share *= low*low*(3.-2.*low)*high*high*(3.-2.*high)
            move, gradient = displacement(verts[:,0], sleeve)
            verts[:,0] += move*arm_share
            stretch = 1.+gradient*arm_share
            dirs[:,0] /= stretch
            attrs["POSITION"] = asset.add(verts.astype("<f4"), 5126, "VEC3", 34962, limits=True)
            attrs["NORMAL"] = asset.add((unit(dirs) if sleeve else dirs).astype("<f4"), 5126, "VEC3", 34962)
            if "TANGENT" in attrs:
                tangents = asset.read(attrs["TANGENT"]).astype(float)
                tangents[:, :3] = tangents[:, :3] @ m[:3,:3].T
                tangents[:, 0] *= stretch
                tangents[:, :3] = unit(tangents[:, :3])
                attrs["TANGENT"] = asset.add(tangents.astype("<f4"), 5126, "VEC4", 34962)
            joint_idx = np.argsort(mapped, axis=1)[:, -4:][:, ::-1]
            joint_weights = np.take_along_axis(mapped, joint_idx, axis=1)
            joint_weights /= joint_weights.sum(axis=1, keepdims=True)
            attrs["JOINTS_0"] = asset.add(joint_idx.astype("<u2"), 5123, "VEC4", 34962)
            attrs["WEIGHTS_0"] = asset.add(joint_weights.astype("<f4"), 5126, "VEC4", 34962)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ["original", "controller", "recipe", "output"]:
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    recipe = json.loads(args.recipe.read_text())
    if digest(args.original) != recipe["original_sha256"] or digest(args.controller) != recipe["controller_sha256"]:
        parser.error("Original/controller digest is different from the measured recipe")
    raw = Glb(args.original)
    fit(raw, Glb(args.controller), recipe)
    for patch in recipe.get("texture_corrections", []):
        from apply_albedo import replace_texture
        correction=(args.recipe.parent / patch["filename"]).read_bytes()
        replace_texture(raw, patch["image"], correction, patch["sha256"])
    temp = args.output.with_suffix(".temporary")
    raw.save(temp)
    temp.replace(args.output)
