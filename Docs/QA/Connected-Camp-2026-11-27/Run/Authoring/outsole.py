"""Sample skin-weighted boot treads and their heel and forefoot material regions."""

import numpy as np
from gltf_pose import Model


def model_info(source):
    model = Model(source)
    sample_phases = np.linspace(0, 1, 241)
    base_translations, base_rotations, base_scales = model.samples(
        "FieldRun", sample_phases * 44 / 60
    )
    world = model.world(base_translations, base_rotations, base_scales)
    mesh = model.document["meshes"][0]["primitives"][0]["attributes"]
    skin = model.document["skins"][0]
    vertices = model.accessor(mesh["POSITION"])
    inverse_bind = (
        model.accessor(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    )
    contacts = {}
    for side, sign in [("L", 1), ("R", -1)]:
        mask = (vertices[:, 1] < 0.048) & (vertices[:, 0] * sign > 0)
        sole_vertices = vertices[mask]
        joint_indices = model.accessor(mesh["JOINTS_0"])[mask]
        weights = model.accessor(mesh["WEIGHTS_0"])[mask]
        rest_homogeneous = np.c_[sole_vertices, np.ones(len(sole_vertices))]
        xyz = np.stack(
            [
                np.einsum(
                    "nvij,nj,nv->ni",
                    (world[skin["joints"], f] @ inverse_bind)[joint_indices, :3, :],
                    rest_homogeneous,
                    weights,
                )
                for f in range(len(sample_phases))
            ]
        )
        heel_patch = np.quantile(sole_vertices[:, 2], 0.13)
        toe_patch = np.quantile(sole_vertices[:, 2], 0.87)
        contacts[side] = (
            xyz.min(axis=1)[:, 1],
            xyz[np.arange(len(sample_phases)), xyz[:, :, 1].argmin(axis=1), :],
            xyz[:, sole_vertices[:, 2] < heel_patch].mean(axis=1),
            xyz[:, sole_vertices[:, 2] > toe_patch].mean(axis=1),
        )
    return (
        model,
        sample_phases,
        base_translations,
        base_rotations,
        base_scales,
        world,
        contacts,
    )
