#!/usr/bin/env python3
"""Deterministic geometry-raycast high-to-low normal/AO baker for Blender.

Bakes actual DETAIL_MASTER face normals onto artist UVs of GAME_LOD0.
AO casts deterministic hemispherical rays against the true low mesh.
No solid-color proxy may substitute for rasterized geometry.
CPU fallback for native Cycles environments that return empty textures.
"""
import math
from array import array

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _barycentric(p, a, b, c):
    den=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
    if abs(den)<1e-12:
        return None
    u=((b.y-c.y)*(p.x-c.x)+(c.x-b.x)*(p.y-c.y))/den
    v=((c.y-a.y)*(p.x-c.x)+(a.x-c.x)*(p.y-c.y))/den
    w=1.0-u-v
    if min(u,v,w)<-1e-7:
        return None
    return (u,v,w)


def _world_bvh_ray(bvh, inv, origin, direction, distance):
    # FromObject BVHs use object-local coordinates.
    local_origin=inv @ origin
    local_dir=(inv.to_3x3() @ direction).normalized()
    return bvh.ray_cast(local_origin,local_dir,distance)


def bake(high, low, size, normal_image, ao_image, ao_rays=8, material_index=None, minimum_pixels=32, minimum_coverage=.05):
    if size>1024:
        raise RuntimeError("CPU BVH fallback limited to 1024px; production 4K needs validated native/accelerated bake")
    if any(abs(x-1.0)>1e-4 for x in (*high.scale,*low.scale)):
        raise RuntimeError("Geometry BVH baker requires applied high/low scale")
    if not low.data.uv_layers.active:
        raise RuntimeError("GAME_LOD0 artist UVs required")
    bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    hi_bvh=BVHTree.FromObject(high,depsgraph)
    lo_bvh=BVHTree.FromObject(low,depsgraph)
    high_inv=high.matrix_world.inverted()
    low_inv=low.matrix_world.inverted()
    high_normal_to_world=high_inv.to_3x3().transposed()
    uv=low.data.uv_layers.active.data
    low.data.calc_loop_triangles()
    pix_normal=array("f",(0.5,0.5,1.0,1.0))* (size*size)
    pix_ao=array("f",(1.0,1.0,1.0,1.0))* (size*size)
    touched=bytearray(size*size)
    high_hits=0
    sampled=0
    occlusion_hits=0
    for tri in low.data.loop_triangles:
        if material_index is not None and low.data.polygons[tri.polygon_index].material_index != material_index:
            continue
        loops=[low.data.loops[i] for i in tri.loops]
        coords=[Vector(uv[i].uv) for i in tri.loops]
        vertices=[low.data.vertices[loop.vertex_index] for loop in loops]
        pos=[low.matrix_world @ v.co for v in vertices]
        normals=[(low.matrix_world.to_3x3() @ v.normal).normalized() for v in vertices]
        du1=coords[1].x-coords[0].x
        dv1=coords[1].y-coords[0].y
        du2=coords[2].x-coords[0].x
        dv2=coords[2].y-coords[0].y
        det=du1*dv2-du2*dv1
        if abs(det)<1e-10:
            continue
        tangent=((pos[1]-pos[0])*dv2-(pos[2]-pos[0])*dv1)/det
        hand=1.0 if det>0 else -1.0
        minx=max(0,math.floor(min(c.x for c in coords)*size))
        maxx=min(size-1,math.ceil(max(c.x for c in coords)*size))
        miny=max(0,math.floor(min(c.y for c in coords)*size))
        maxy=min(size-1,math.ceil(max(c.y for c in coords)*size))
        for y in range(miny,maxy+1):
            for x in range(minx,maxx+1):
                weights=_barycentric(Vector(((x+.5)/size,(y+.5)/size)),*coords)
                if weights is None:
                    continue
                index=y*size+x
                if touched[index]:
                    continue
                u,v,w=weights
                point=pos[0]*u+pos[1]*v+pos[2]*w
                N=(normals[0]*u+normals[1]*v+normals[2]*w).normalized()
                T=tangent-N*tangent.dot(N)
                if T.length<1e-8:
                    raise RuntimeError("Degenerate tangent frame on artist UV island")
                T.normalize()
                B=N.cross(T)*hand
                high_hit=_world_bvh_ray(hi_bvh,high_inv,point+N*.2,-N,.40)
                loc,facenormal,faceidx,dist=high_hit
                if facenormal is None:
                    continue
                hn=(high_normal_to_world @ facenormal).normalized()
                ts=Vector((hn.dot(T),hn.dot(B),hn.dot(N))).normalized()
                if ts.z<-.1:
                    continue
                base=index*4
                encoded=[min(1.0,max(0.0,0.5+0.5*t)) for t in ts]
                pix_normal[base:base+4]=array("f",(*encoded,1.0))
                touched[index]=1
                high_hits+=1
                ao_blocked=0
                for sample in range(ao_rays):
                    # Deterministic cosine-weighted hemisphere. Distance to real
                    # geometry produces AO; never assume white or black by fiat.
                    theta=2.0*math.pi*(sample*.61803398875 + (x*13+y*7)%31/31.0)
                    r=math.sqrt((sample+.5)/ao_rays)
                    direction=(T*(math.cos(theta)*r)+B*(math.sin(theta)*r)+
                               N*math.sqrt(1.0-r*r)).normalized()
                    _,_,face,d=_world_bvh_ray(lo_bvh,low_inv,point+N*.01,direction,.65)
                    if face is not None and d is not None and d>.008:
                        ao_blocked+=1
                occlusion_hits+=ao_blocked
                ao_value=1.0-ao_blocked/ao_rays
                pix_ao[base:base+4]=array("f",(ao_value,ao_value,ao_value,1.0))
                sampled+=1
    coverage=sampled/(size*size)
    if sampled<minimum_pixels or coverage<minimum_coverage or high_hits<minimum_pixels:
        raise RuntimeError(f"Geometry-derived bake has inadequate UV/ray coverage: {sampled} pixels, fraction {coverage:.4f}")
    normal_image.pixels.foreach_set(pix_normal)
    ao_image.pixels.foreach_set(pix_ao)
    stats={"backend":"cpu_bvh_real_geometry","material_index":material_index,"rasterized_pixels":sampled,
           "texture_coverage":round(coverage,5),"high_to_low_ray_hits":high_hits,
           "ambient_occlusion_ray_count":sampled*ao_rays,
           "ambient_occlusion_intersections":occlusion_hits}
    print("HAVENLINE BVH_GEOMETRY_BAKE",stats)
    return stats
