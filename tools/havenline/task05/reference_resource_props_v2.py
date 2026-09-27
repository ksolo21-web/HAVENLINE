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
    legacy.add_snow_foot(b, size)


def _pallet(b, width, depth, y=.14, material="wood"):
    """Compact slatted pallet that keeps pickup props grounded in the snow."""
    for z in (-depth * .31, 0.0, depth * .31):
        b.beveled_box(material, (0, y, z), (width * .92, .12, depth * .20), .035)
    for x in (-width * .34, width * .34):
        b.beveled_box("wood_light", (x, y - .045, 0), (width * .12, .10, depth * .84), .03)


def _corner_post(b, x, z, height, material="wood_light"):
    b.beveled_box(material, (x, .24 + height * .5, z), (.12, height, .12), .035)


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
            b.sphere("cyan", (x,1.085,z), (.31,.11,.14), 7, 14, rotation=(0,r,0))
            tail_x=x-.28*math.cos(r); tail_z=z+.28*math.sin(r)
            b.beveled_box("blue", (tail_x,1.085,tail_z), (.16,.045,.22), .018, rotation=(0,r,0))
            b.cylinder("cream", (x+.10,1.10,z-.02), .025, .06, 8, rotation=(math.pi/2,0,0))
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


def build_stone_stack():
    b = legacy.MeshBuilder("stone_stack")
    _snow_base(b, (1.73, .10, 1.36))
    _pallet(b, 1.52, 1.12, .12)
    # Old T05 used HL_metal for every rock. Use rough neutral/snow surfaces
    # instead; no metallic material is permitted in this resource builder.
    stones = (
        (-.50,.31,-.22,.40,.29,.34),
        (-.12,.28,.23,.43,.27,.38),
        (.35,.30,-.18,.41,.30,.34),
        (.55,.27,.24,.30,.23,.28),
        (-.34,.62,.13,.34,.27,.31),
        (.12,.61,-.18,.37,.28,.33),
        (.42,.60,.15,.29,.23,.27),
        (-.04,.88,.02,.29,.22,.27),
    )
    for i,(x,y,z,rx,ry,rz) in enumerate(stones):
        mat="cream" if i%3 else "snow"
        b.sphere(mat,(x,y,z),(rx,ry,rz),7,14,rotation=(.11*i,.23*x,.17*z))
        if mat!="snow":
            b.sphere("snow",(x-.04,y+ry*.64,z-.03),(rx*.72,ry*.24,rz*.70),5,12,
                     rotation=(0,.20*i,0))
    # Timber side rails stop the pile reading as random floating spheres.
    for x in (-.71,.71):
        b.beveled_box("wood_light",(x,.47,0),(.10,.65,1.00),.03)
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
    # Reference-driven compact storage canister: shouldered vessel, banding,
    # service cap and rigid carry frame. It keeps the early-camp footprint.
    b.lathe("blue",(0,.18,0),[(.33,0),(.40,.08),(.42,.52),(.36,.78),(.28,.88)],18)
    for y in (.34,.66):
        b.torus("metal",(0,y,0),.405,.035,18,6)
    b.cylinder("dark",(0,1.02,0),.17,.20,14)
    b.cylinder("orange",(0,1.14,0),.12,.08,12)
    b.torus("yellow",(0,1.02,0),.30,.035,16,6,rotation=(math.pi/2,0,0),arc=math.pi)
    for x in (-.30,.30):
        b.beveled_box("metal",(x,.95,0),(.07,.34,.08),.022)
    b.beveled_box("cream",(0,.57,-.405),(.30,.25,.035),.015)
    b.beveled_box("orange",(0,.57,-.427),(.18,.08,.018),.007)
    b.beveled_box("snow",(-.10,1.23,.01),(.38,.06,.34),.025,rotation=(0,.08,0))
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
    # Butcher-table-inspired prepared cuts with bones and a small insulated lid.
    cuts=((-0.36,-.18,.02),(.03,.13,-.08),(.37,-.10,.10),(-.12,.34,-.12))
    for i,(x,z,yaw) in enumerate(cuts):
        b.sphere("orange",(x,.53+(i%2)*.10,z),(.26,.12,.18),6,14,rotation=(0,yaw,0))
        b.rod_between("cream",(x-.16,.57+(i%2)*.10,z),(x+.16,.57+(i%2)*.10,z),.022,8)
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
