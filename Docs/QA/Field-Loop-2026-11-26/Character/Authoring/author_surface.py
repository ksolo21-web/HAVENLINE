"""Rebind the lower coat and trousers of the V9 rig, preserving its mesh and actions."""
from pathlib import Path
import sys

import bpy
import numpy as np


def smooth(lower, upper, value):
    amount = np.clip((value - lower) / (upper - lower), 0, 1)
    return amount * amount * (3 - 2 * amount)


def fit_garments(points, weights, names):
    lateral, height, forward = points.T
    seam_width = .008 + .102 * smooth(.32, .51, height)
    left_influence = smooth(-seam_width, seam_width, lateral)
    # The cuff reaches higher up the posterior of the calf. Giving that fabric a
    # longer transition lets the bent boot tuck beneath the coat without folding.
    hip_end = .54 + .10 * (1 - smooth(-.16, .08, forward))
    pelvis = smooth(.10, hip_end, height)
    thigh = smooth(.36 - .70 / 2, .36 + .70 / 2, height)
    shin = smooth(.06, .35, height)

    garment = np.zeros_like(weights)
    for side, side_weight in [('L', left_influence), ('R', 1 - left_influence)]:
        leg = side_weight * (1 - pelvis)
        garment[:, names.index('Foot.' + side)] = leg * (1 - thigh) * (1 - shin)
        garment[:, names.index('Shin.' + side)] = leg * (1 - thigh) * shin
        garment[:, names.index('Thigh.' + side)] = leg * thigh
    garment[:, names.index('Pelvis')] = pelvis

    lower_leg = smooth(.09, .21, height)
    below_waist = 1 - smooth(.715, .89, height)
    inside_coat = 1 - smooth(.33, .43, np.abs(lateral))
    influence = (lower_leg * below_waist * inside_coat)[:, None]
    blended = weights * (1 - influence) + garment * influence
    # Match the four influences supported by the production glTF skin.
    strongest = np.argsort(blended, axis=1)[:, -4:]
    rows = np.arange(len(points))[:, None]
    result = np.zeros_like(weights)
    result[rows, strongest] = blended[rows, strongest]
    return result / result.sum(axis=1)[:, None]


def main():
    source, destination = map(Path, sys.argv[sys.argv.index('--') + 1:])
    destination.mkdir(exist_ok=True, parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    armature = next(obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE')
    model = next(obj for obj in bpy.context.scene.objects if obj.type == 'MESH')
    vertices = model.data.vertices
    blender_xyz = np.array([vertex.co[:] for vertex in vertices])
    # Work in the character's glTF coordinate system: Y up, Z forward.
    points = blender_xyz[:, [0, 2, 1]].copy()
    points[:, 2] *= -1
    names = [group.name for group in model.vertex_groups]
    weights = np.zeros((len(vertices), len(names)), float)
    for vertex in vertices:
        for group in vertex.groups:
            weights[vertex.index, group.group] = group.weight

    fitted = fit_garments(points, weights, names)
    changed = np.flatnonzero(np.max(np.abs(fitted - weights), axis=1) > 1e-6)
    for index in changed:
        vertex_id = int(index)
        for group in list(vertices[vertex_id].groups):
            model.vertex_groups[group.group].remove([vertex_id])
        for group_id in np.flatnonzero(fitted[index] > 1e-8):
            model.vertex_groups[int(group_id)].add([vertex_id], float(fitted[index, group_id]), 'REPLACE')

    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    model.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.wm.save_as_mainfile(filepath=str(destination / 'Character-1-Rigged.blend'))
    bpy.ops.export_scene.gltf(
        filepath=str(destination / 'Character-1-Rigged.glb'),
        use_selection=True,
        export_skins=True,
        export_animations=True,
        export_animation_mode='ACTIONS',
        export_all_influences=False,
        export_rest_position_armature=True,
    )


if __name__ == '__main__':
    main()
