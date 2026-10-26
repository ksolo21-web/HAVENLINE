#!/usr/bin/env python3
"""Reference-driven T05 R07 resource-prop rebuild.

This module replaces only the eight R07 pickup/storage props while preserving
their IDs, catalog footprints, sockets, gameplay contracts and material budget.
The visual target is the user-supplied HAVENLINE early-camp board (18607.png),
with the late-fortress board (18608.png) used only as a material/polish ceiling.

The builders intentionally compose authored silhouettes from multiple parts;
they do not introduce engine/debug primitives, new gameplay nodes or new
material slots. In particular, the stone stack no longer uses the metallic
surface that made the old resource read like steel.
"""
from __future__ import annotations

import math
import legacy_station_kit_v1 as legacy

RESOURCE_IDS = (
    "wood_stack",
    "stone_stack",
    "metal_stack",
    "fuel_canister",
    "fish_crate",
    "cooked_food_stack",
    "money_stack",
    "cargo_crate",
)


def _snow_base(b, size):
    """Irregular local snow contact; never a rectangular shipping slab."""
    w,d=float(size[0]),float(size[2])
    patches=(
        (-.24*w,-.20*d,.20*w,.16*d,-.10),
        (.21*w,-.18*d,.18*w,.14*d,.08),
        (-.18*w,.19*d,.17*w,.15*d,.05),
        (.24*w,.18*d,.19*w,.14*d,-.06),
        (0.0,-.03*d,.21*w,.13*d,.02),
    )
    for x,z,rx,rz,yaw in patches:
        b.sphere("snow",(x,.045,z),(rx,.055,rz),4,7,rotation=(0,yaw,0))


def _pallet(b, width, depth, y=.14, material="wood"):
    """Compact slatted pallet that keeps pickup props grounded in the snow."""
    for z in (-depth * .31, 0.0, depth * .31):
        b.beveled_box(material, (0, y, z), (width * .92, .12, depth * .20), .035)
    for x in (-width * .34, width * .34):
        b.beveled_box("wood_light", (x, y - .045, 0), (width * .12, .10, depth * .84), .03)


def _corner_post(b, x, z, height, material="wood_light"):
    b.beveled_box(material, (x, .24 + height * .5, z), (.12, height, .12), .035)


def _authored_fish_body(b, center, length, yaw):
    """Tapered sculpted skin with a head, belly and tail instead of a lozenge.

    Rings are symmetric in count but asymmetric in profile. The 12-sided skin
    and two caps use the same triangle allocation as the former smooth fish;
    separate outward normals retain readable volume under studio lighting.
    """
    profile=((-1.0,.12),(-.79,.38),(-.48,.74),(-.08,1.0),
             (.35,.91),(.73,.56),(1.0,.14))
    sides=12
    vertices=[];normals=[];indices=[]
    for t,rad in profile:
        for j in range(sides):
            a=math.tau*float(j)/sides
            sn=math.sin(a);cs=math.cos(a)
            vertices.append((length*t,.115*rad*sn,.13*rad*cs))
            normals.append((0.0,sn,cs))
    for k in range(len(profile)-1):
        for j in range(sides):
            a=k*sides+j; bj=k*sides+(j+1)%sides
            c=(k+1)*sides+(j+1)%sides;d=(k+1)*sides+j
            indices.extend((a,bj,c,a,c,d))
    b.triangles("cyan",vertices,normals,indices,center,(0,yaw,0))
    for end,sign in ((0,-1),(len(profile)-1,1)):
        xs=profile[end][0]*length
        rad=profile[end][1]
        vv=[(xs,0.0,0.0)]
        for j in range(sides):
            a=math.tau*float(j)/sides
            vv.append((xs,.115*rad*math.sin(a),.13*rad*math.cos(a)))
        capn=(float(sign),0.0,0.0)
        ii=[]
        for j in range(sides):ii.extend((0,1+j,1+(j+1)%sides))
        b.triangles("cyan",vv,[capn]*len(vv),ii,center,(0,yaw,0))

def _crate_shell(b, name, fish=False):
    _snow_base(b, (1.68, .10, 1.34))
    _pallet(b, 1.48, 1.10, .12)
    # Separated planks and corner posts create a readable storage-crate
    # silhouette instead of one rounded box with trim painted on it.
    for y in (.32, .55, .78):
        b.beveled_box("wood", (0, y, -.49), (1.38, .16, .10), .035)
        b.beveled_box("wood", (0, y, .49), (1.38, .16, .10), .035)
    for x in (-.64, .64):
        for y in (.32, .55, .78):
            b.beveled_box("wood", (x, y, 0), (.10, .16, .92), .035)
        _corner_post(b, x, -.49, .74)
        _corner_post(b, x, .49, .74)
    # Continuous inset liner closes the hollow box under the visible payload;
    # short inner boards give the fish believable support from side angles.
    b.beveled_box("wood_light", (0, .71, 0), (1.22, .055, .82), .022)
    # Cross-bracing is real geometry and stays inside the locked footprint.
    for sign in (-1, 1):
        b.beveled_box("wood_light", (0, .55, -.555), (.11, .80, .07), .028,
                      rotation=(0, 0, sign * .94))
    b.beveled_box("dark", (0, .90, 0), (1.30, .08, .92), .025)
    # Uneven snow lip gives the top edge the same winter-loaded read as 18607.
    b.beveled_box("snow", (-.20, .965, .02), (.86, .09, .80), .040, rotation=(0, .06, .02))
    b.beveled_box("snow", (.44, .955, -.07), (.48, .07, .58), .030, rotation=(0, -.10, -.015))
    if fish:
        # Ice bed plus three authored fish forms. The fish keep the readable
        # cyan family but no longer float above an open generic cube.
        b.beveled_box("snow", (0, 1.005, 0), (1.08, .06, .70), .025)
        for i, (x, z, r) in enumerate(((-.32,-.10,-.20),(.05,.12,.18),(.34,-.12,-.12))):
            # Unequal tapered body proportions and small embedded eyes/gill marks;
            # flesh intersects the ice bed rather than hovering over a hollow box.
            length=(.30,.33,.27)[i]
            _authored_fish_body(b,(x,1.075,z),length,r)
            tail_x=x-length*.91*math.cos(r); tail_z=z+length*.91*math.sin(r)
            for dz in (-.075,.075):
                b.rod_between("blue",(tail_x,1.075,tail_z),(tail_x-.12,1.075,tail_z+dz),.027,6)
            b.sphere("cream", (x+.11,1.084,z-.045), (.026,.018,.015), 4, 8)
            b.rod_between("blue",(x+.065,1.102,z-.107),(x+.10,1.045,z-.105),.012,6)
    else:
        # Hardware plate/rope lock keeps cargo identity visible at gameplay zoom.
        b.beveled_box("blue", (0,.57,-.565), (.48,.34,.055), .025)
        b.beveled_box("yellow", (0,.57,-.598), (.26,.17,.025), .012)
        for x in (-.48,.48):
            b.cylinder("metal", (x,.58,-.59), .035, .055, 8, rotation=(math.pi/2,0,0))
    return b


def build_wood_stack():
    b = legacy.MeshBuilder("wood_stack")
    _snow_base(b, (1.68, .10, 1.16))
    _pallet(b, 1.50, .98, .12)
    # Timber rack echoes the early-camp stockpile rather than a loose pyramid.
    for x in (-.66, .66):
        _corner_post(b, x, -.40, .78)
        _corner_post(b, x, .40, .78)
    for level, y in enumerate((.31, .55, .79)):
        count = 4 if level < 2 else 3
        spacing = .34
        for i in range(count):
            x=(i-(count-1)/2)*spacing
            b.cylinder("wood", (x,y,0), .135, .82, 14, rotation=(math.pi/2,0,0))
            for z in (-.415,.415):
                b.cylinder("cream", (x,y,z), .108, .025, 12, rotation=(math.pi/2,0,0))
    # Bound blue weather cover and lashing; these make the bundle intentionally
    # built and readable, not a group of raw cylinders.
    b.beveled_box("blue", (0,1.00,.04), (1.30,.12,.88), .055, rotation=(0,0,.015))
    b.beveled_box("snow", (-.18,1.075,.02), (.82,.07,.70), .030, rotation=(0,.08,.02))
    for x in (-.48,.48):
        b.beveled_box("yellow", (x,.62,-.455), (.055,.86,.045), .015)
    return b


def _faceted_stone(b, center, radii, rotation, seed):
    """Irregular outward-facing flat-cut quarry rock, not a smooth snowball.

    20 low-poly facets have independent flat normals. Deterministic asymmetric
    radii preserve locked resource bounds, existing material palette, and the
    snow-cap contact without introducing primitive placeholder cylinders.
    """
    phi=(1.0+math.sqrt(5.0))*.5
    raw=((-1,phi,0),(1,phi,0),(-1,-phi,0),(1,-phi,0),
         (0,-1,phi),(0,1,phi),(0,-1,-phi),(0,1,-phi),
         (phi,0,-1),(phi,0,1),(-phi,0,-1),(-phi,0,1))
    faces=((0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
           (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
           (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
           (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1))
    verts=[]
    for k,(x,y,z) in enumerate(raw):
        variation=1.0+.035*math.sin(float(seed+3)*1.3+k*2.71)
        verts.append((x/phi*radii[0]*variation,y/phi*radii[1]*variation,
                      z/phi*radii[2]*variation))
    for ia,ib,ic in faces:
        a,bv,c=verts[ia],verts[ib],verts[ic]
        n=legacy.vnorm(legacy.vcross(legacy.vsub(bv,a),legacy.vsub(c,a)))
        mid=tuple((a[i]+bv[i]+c[i])/3.0 for i in range(3))
        if sum(n[i]*mid[i] for i in range(3))<0.0:
            bv,c=c,bv
            n=tuple(-v for v in n)
        b.triangles("cream",[a,bv,c],[n,n,n],[0,1,2],center,rotation)

def build_stone_stack():
    b = legacy.MeshBuilder("stone_stack")
    _snow_base(b, (1.73, .10, 1.36))
    _pallet(b, 1.52, 1.12, .12)

    # Faceted, nonuniform rock forms replace the smooth snowball-like pile.
    stones = (
        (-.50,.33,-.23,.38,.27,.32,.10,-.18,.06),
        (-.13,.30,.24,.41,.25,.35,-.06,.23,-.04),
        (.34,.32,-.18,.39,.28,.31,.08,-.16,.07),
        (.54,.29,.25,.29,.22,.27,-.08,.31,.03),
        (-.34,.61,.13,.32,.25,.28,.06,.14,-.08),
        (.10,.61,-.18,.35,.26,.30,-.04,-.22,.07),
        (.40,.59,.15,.27,.21,.25,.10,.27,-.04),
        (-.03,.86,.02,.27,.20,.24,-.08,.11,.05),
    )
    for i,(x,y,z,rx,ry,rz,px,py,pz) in enumerate(stones):
        _faceted_stone(b,(x,y,z),(rx,ry,rz),(px,py,pz),i)
        if i in (0,2,4,6):
            b.sphere("dark",(x-.03,y-ry*.46,z+.02),(rx*.54,ry*.18,rz*.50),3,7,
                     rotation=(0,py*.5,0))
        b.sphere("snow",(x-.04,y+ry*.67,z-.03),(rx*.66,ry*.18,rz*.62),3,8,
                 rotation=(0,.17*i,0))

    # Timber containment and a small blue inventory tab make the pile intentional.
    for x in (-.71,.71):
        b.beveled_box("wood_light",(x,.47,0),(.10,.65,1.00),.03)
    b.beveled_box("wood",(0,.22,-.52),(1.42,.11,.10),.03)
    b.beveled_box("blue",(.54,.72,-.54),(.22,.18,.05),.018)
    return b

def build_metal_stack():
    b = legacy.MeshBuilder("metal_stack")
    _snow_base(b, (1.73, .10, 1.23))
    _pallet(b, 1.52, 1.02, .12, "blue")
    # Forged ingots have stepped ends and orange retaining bands rather than
    # being one row of generic boxes.
    for level in range(3):
        count=3-level
        for i in range(count):
            x=(i-(count-1)/2)*.47
            y=.29+level*.27
            yaw=.035*(i-level)
            b.beveled_box("metal",(x,y,0),(.40,.20,.86),.065,rotation=(0,yaw,0))
            b.beveled_box("dark",(x,y+.105,0),(.30,.035,.67),.014,rotation=(0,yaw,0))
            for z in (-.34,.34):
                b.beveled_box("orange",(x,y,z),(.42,.07,.055),.018,rotation=(0,yaw,0))
    for x in (-.55,.55):
        b.beveled_box("yellow",(x,.54,-.47),(.055,.70,.045),.014)
    b.beveled_box("snow",(-.20,1.02,.03),(.72,.07,.76),.030,rotation=(0,.08,.02))
    return b


def build_fuel_canister():
    b=legacy.MeshBuilder("fuel_canister")
    _snow_base(b,(1.13,.10,1.06))
    _pallet(b,1.02,.88,.11,"wood")

    # Two strapped winter canisters replace the former smooth blue tank stack.
    for x,h,yaw in ((-.25,.76,-.04),(.24,.70,.05)):
        b.beveled_box("blue",(x,.56,0),(.42,h,.58),.145,rotation=(0,yaw,0))
        # Narrow pressed shoulder seam reads as canister shell, not a plate cap.
        b.beveled_box("metal",(x,.56+h*.36,.0),(.365,.034,.51),.016,rotation=(0,yaw,0))
        b.beveled_box("dark",(x,.56,-.302),(.28,h*.58,.035),.016,rotation=(0,yaw,0))
        b.beveled_box("metal",(x,.56,-.324),(.08,h*.48,.020),.008,rotation=(0,yaw,0))
        b.beveled_box("cream",(x,.50,-.338),(.16,.13,.012),.005,rotation=(0,yaw,0))
        b.beveled_box("orange",(x,.50,-.346),(.08,.045,.008),.003,rotation=(0,yaw,0))
        b.cylinder("orange",(x+.09,.96 if x<0 else .92,.03),.065,.08,10)
        b.torus("yellow",(x,.94 if x<0 else .90,0),.16,.028,12,5,rotation=(math.pi/2,0,0),arc=math.pi)
        for hx in (-.12,.12):
            b.beveled_box("metal",(x+hx,.73,.28),(.045,.45,.045),.014,rotation=(0,yaw,0))

    # Shared retaining frame, cross lashing and uneven snow load.
    # Four open corner struts replace two broad, featureless side walls. These
    # retain the canisters on their rack without hiding the formed sheet metal
    # from lateral gameplay views or creating primitive wooden slab silhouettes.
    for x in (-.47,.47):
        for z in (-.31,.31):
            b.rod_between("wood_light",(x,.19,z),(x,.88,z),.040,7)
    b.rod_between("yellow",(-.43,.34,-.32),(.43,.75,-.32),.025,7)
    b.rod_between("yellow",(-.43,.75,-.32),(.43,.34,-.32),.025,7)
    b.beveled_box("snow",(-.25,1.03,.02),(.28,.055,.34),.020,rotation=(0,.07,.02))
    b.beveled_box("snow",(.20,.98,-.04),(.24,.045,.28),.018,rotation=(0,-.10,-.01))
    return b

def build_fish_crate():
    return _crate_shell(legacy.MeshBuilder("fish_crate"), "fish_crate", True)


def build_cargo_crate():
    return _crate_shell(legacy.MeshBuilder("cargo_crate"), "cargo_crate", False)


def build_cooked_food_stack():
    b=legacy.MeshBuilder("cooked_food_stack")
    _snow_base(b,(1.63,.10,1.26))
    _pallet(b,1.44,1.04,.12)
    b.beveled_box("wood_light",(0,.28,0),(1.30,.18,.92),.06)
    b.beveled_box("dark",(0,.39,0),(1.16,.07,.78),.025)
    # Varied prepared red-meat cuts, broad cream fat caps (not uniform rolls).
    cuts=((-0.36,-.18,.02,.26,.18),(.03,.13,-.22,.31,.15),(.37,-.10,.14,.24,.21),(-.12,.34,.31,.22,.17))
    for i,(x,z,yaw,rx,rz) in enumerate(cuts):
        y=.51+(i%2)*.085
        b.sphere("orange",(x,y,z),(rx,.115,rz),5,13,rotation=(0,yaw,0))
        b.sphere("cream",(x-.048,y+.085,z+.024),(rx*.62,.031,rz*.69),3,9,rotation=(0,yaw,0))
        b.rod_between("cream",(x-rx*.50,y+.095,z),(x+rx*.44,y+.096,z),.016,7)
    b.beveled_box("blue",(0,.78,.34),(1.06,.09,.25),.035,rotation=(.05,0,0))
    b.beveled_box("snow",(-.16,.845,.34),(.62,.05,.20),.020)
    return b


def build_money_stack():
    b=legacy.MeshBuilder("money_stack")
    _snow_base(b,(1.53,.10,1.22))
    _pallet(b,1.34,.98,.12)
    # Organized supply lockbox/bundles: stacked vouchers remain green, but the
    # whole object now has a protective blue/wood frame and brass-like hardware.
    b.beveled_box("blue",(0,.36,0),(1.22,.44,.88),.10)
    b.beveled_box("dark",(0,.59,0),(1.05,.08,.72),.025)
    for level in range(3):
        count=3 if level<2 else 2
        for i in range(count):
            x=(i-(count-1)/2)*.36
            b.beveled_box("green",(x,.67+level*.15,-.02),(.32,.11,.58),.040,
                          rotation=(0,.035*(i-level),0))
            b.beveled_box("cream",(x,.67+level*.15,-.315),(.08,.115,.022),.008)
    for x in (-.40,0,.40):
        b.cylinder("yellow",(x,.45,-.465),.10,.045,14,rotation=(math.pi/2,0,0))
    b.beveled_box("snow",(-.14,1.06,.05),(.66,.055,.55),.025,rotation=(0,.08,.01))
    return b


def build_resource_props():
    """Return the exact R07 override set consumed by generate_station_kit.py."""
    result={
        "wood_stack":build_wood_stack(),
        "stone_stack":build_stone_stack(),
        "metal_stack":build_metal_stack(),
        "fuel_canister":build_fuel_canister(),
        "fish_crate":build_fish_crate(),
        "cooked_food_stack":build_cooked_food_stack(),
        "money_stack":build_money_stack(),
        "cargo_crate":build_cargo_crate(),
    }
    assert tuple(sorted(result))==tuple(sorted(RESOURCE_IDS))
    return result


def quality_report():
    assets=build_resource_props()
    return {
        "asset_ids":list(RESOURCE_IDS),
        "triangles":{name:asset.triangle_count() for name,asset in assets.items()},
        "materials":{name:sorted(asset.surfaces) for name,asset in assets.items()},
        "stone_uses_metal":"metal" in assets["stone_stack"].surfaces,
        "material_slots":sorted({m for asset in assets.values() for m in asset.surfaces}),
    }


if __name__=="__main__":
    import json
    print(json.dumps(quality_report(),indent=2,sort_keys=True))
