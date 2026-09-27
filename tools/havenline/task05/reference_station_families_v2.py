#!/usr/bin/env python3
"""T05 R10 visual rebuild for three confirmed primitive-looking station families.

Primary authority: user HAVENLINE early-camp board 18607.png.
Secondary polish ceiling: user HAVENLINE fortress board 18608.png.
Gameplay IDs, footprints, sockets, arrangements and material vocabulary are frozen.
"""
from __future__ import annotations
import math
import legacy_station_kit_v1 as legacy

STATION_IDS=("service_counter","processing_counter","defense_platform")

def snow(b,size):
    """Irregular winter grounding; never ship a flat rectangular snow slab.

    User HAVENLINE renders ground stations with broken snow banks/rocks rather
    than a primitive white plate. Normalized clusters stay inside each frozen
    footprint and preserve the shallow terrain-seating overlap contract.
    """
    sx, _sy, sz = size
    patches = (
        (-.32,-.31,.14,.12,-.10), (-.10,-.36,.18,.09,.05),
        (.22,-.32,.16,.11,.13), (.36,-.06,.11,.15,-.04),
        (.31,.29,.16,.11,.08), (.03,.36,.19,.09,-.12),
        (-.28,.31,.14,.12,.06), (-.36,.07,.11,.14,-.08),
    )
    for px,pz,rx,rz,rot in patches:
        b.sphere("snow", (px*sx, .035, pz*sz),
                 (rx*sx, .070, rz*sz), 5, 10, rotation=(0,rot,0))
    stones = ((-.35,-.18,.08,.07,.10),(.34,.11,.08,.07,-.16),(-.15,.36,.07,.06,.22))
    for px,pz,rx,rz,rot in stones:
        b.beveled_box("dark", (px*sx,.045,pz*sz),
                      (rx*sx,.085,rz*sz), .025, rotation=(0,rot,0))

def leg(b,x,z,h=.86):
    b.beveled_box("wood",(x,.10+h*.5,z),(.18,h,.18),.045)
    b.beveled_box("dark",(x,.09,z),(.24,.10,.24),.035)

def brace(b,x0,x1,y0,y1,z):
    b.rod_between("wood_light",(x0,y0,z),(x1,y1,z),.06,8)

def build_service_counter():
    b=legacy.MeshBuilder("service_counter")
    snow(b,(3.45,.14,1.95))
    for x in (-1.28,1.28):
        for z in (-.60,.60): leg(b,x,z,.88)
    for z in (-.56,.56):
        b.beveled_box("wood",(0,.40,z),(2.78,.18,.20),.05)
        brace(b,-1.14,1.14,.25,.66,z)
        brace(b,-1.14,1.14,.66,.25,z)
    for index,z in enumerate((-.64,-.32,0,.32,.64)):
        b.beveled_box("wood" if index % 2 == 0 else "wood_light",(0,1.00,z),(3.16,.17,.25),.045)
    b.beveled_box("blue",(0,.91,-.78),(2.74,.22,.10),.035)
    for x in (-1.08,-.54,0,.54,1.08):
        b.cylinder("dark",(x,1.04,-.71),.032,.04,8,rotation=(math.pi/2,0,0))
    for x in (-.78,0,.78):
        b.lathe("green" if x<.4 else "cream",(x,1.10,.08),
                [(.15,0),(.18,.06),(.15,.15),(.10,.18)],12)
    b.beveled_box("orange",(0,1.15,.47),(.84,.13,.32),.05)
    b.beveled_box("cream",(-.42,1.22,-.16),(.44,.09,.26),.04,rotation=(0,.10,.02))
    b.beveled_box("snow",(-.78,1.15,.64),(1.02,.06,.18),.025,rotation=(0,.04,.015))
    return b

def build_processing_counter():
    b=legacy.MeshBuilder("processing_counter")
    snow(b,(3.45,.14,1.95))
    for x in (-1.30,1.30):
        for z in (-.58,.58): leg(b,x,z,.84)
    for z in (-.56,.56):
        b.beveled_box("wood",(0,.37,z),(2.78,.18,.20),.05)
        brace(b,-1.14,1.14,.23,.63,z)
    for index,z in enumerate((-.62,-.31,0,.31,.62)):
        b.beveled_box("wood" if index % 2 == 0 else "wood_light",(0,.90,z),(3.10,.16,.23),.04)
    for x in (-.62,.62):
        b.beveled_box("blue",(x,1.42,.06),(.18,1.12,.22),.055)
        b.beveled_box("dark",(x,1.00,.06),(.24,.16,.28),.045)
    b.beveled_box("wood_light",(0,1.94,.06),(1.52,.18,.24),.055)
    b.cylinder("metal",(0,1.45,0),.46,.10,24,rotation=(math.pi/2,0,0))
    b.cylinder("dark",(0,1.45,-.075),.18,.13,16,rotation=(math.pi/2,0,0))
    b.cylinder("orange",(0,1.45,-.15),.095,.05,12,rotation=(math.pi/2,0,0))
    b.beveled_box("dark",(0,1.02,.26),(1.08,.12,.56),.04)
    b.beveled_box("yellow",(0,1.10,.26),(.72,.06,.38),.025)
    for x in (-.82,-.27,.28,.84):
        b.cylinder("wood",(x,1.07,.42),.11,.60,12,rotation=(math.pi/2,0,0))
        b.cylinder("cream",(x,1.07,.73),.084,.025,10,rotation=(math.pi/2,0,0))
    b.beveled_box("snow",(-.80,2.04,.06),(.44,.06,.21),.025,rotation=(0,.05,.015))
    return b

def build_defense_platform():
    b=legacy.MeshBuilder("defense_platform")
    snow(b,(3.25,.16,3.05))
    for x in (-1.08,1.08):
        for z in (-.98,.98):
            b.beveled_box("wood",(x,.70,z),(.24,1.24,.24),.06)
            b.beveled_box("dark",(x,.11,z),(.30,.12,.30),.045)
    for z in (-.92,.92):
        b.beveled_box("wood_light",(0,.66,z),(2.34,.22,.22),.06)
        brace(b,-.98,.98,.28,1.04,z)
        brace(b,-.98,.98,1.04,.28,z)
    for x in (-1.02,1.02):
        b.beveled_box("wood",(x,.66,0),(.22,.22,1.94),.06)
    for x in (-.84,-.56,-.28,0,.28,.56,.84):
        b.beveled_box("wood_light",(x,1.25,0),(.22,.14,1.84),.04)
    for z in (-.96,.96):
        b.beveled_box("blue",(0,1.48,z),(2.10,.16,.16),.045)
    for x in (-1.02,1.02):
        b.beveled_box("blue",(x,1.48,0),(.16,.16,1.80),.045)
    b.beveled_box("dark",(0,1.36,0),(.84,.14,.84),.08,rotation=(0,math.pi/4,0))
    b.cylinder("metal",(0,1.53,0),.35,.22,16)
    b.torus("orange",(0,1.65,0),.30,.055,16,6)
    b.cylinder("dark",(0,1.73,0),.15,.18,14)
    b.beveled_box("yellow",(0,1.43,-.82),(.50,.12,.12),.035)
    b.beveled_box("snow",(-.68,1.60,.91),(.56,.06,.18),.025,rotation=(0,.04,.015))
    return b

def build_station_families():
    result={
        "service_counter":build_service_counter(),
        "processing_counter":build_processing_counter(),
        "defense_platform":build_defense_platform(),
    }
    assert tuple(sorted(result))==tuple(sorted(STATION_IDS))
    return result

if __name__=="__main__":
    import json
    a=build_station_families()
    print(json.dumps({"assets":list(a),"triangles":{k:v.triangle_count() for k,v in a.items()},
                      "materials":{k:sorted(v.surfaces) for k,v in a.items()}},indent=2))
