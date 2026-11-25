# Visible Character 1 right boot and shin proof · rejected

This records the actual Blender build source and native results. The 49,324,192-byte Blender artifact is generated from the exact pinned rig and reviewed here by checksum, not stored in this WIP folder. The SHA-256 of the tested artifact is recorded in the source packet; regenerating a Blender container may change its file hash if Blender inserts metadata, so compare the measured surface and behavior as well. This source does not put a new boot in Havenline.

Set `C1_EXACT_GLB`, `C1_EXACT_BLEND`, and `C1_KNEE_DATA` to the exact assets/pose-data directory. Use a fresh private Blender CPU profile with NumPy and SciPy. Run `build.py` to generate the detached Blender file and surface arrays, and the accompanying verification scripts to measure the seam, normals, silhouette probes, and three pose tests. Visible toe movement is real; failed overlap/edge and changed contact figures block the candidate.
