#!/usr/bin/env python3
"""T05 R10C refinement for the processing/cooker silhouette.

Primary authority: user HAVENLINE early-camp board 18607.png.
Secondary polish ceiling: user HAVENLINE late-fortress board 18608.png.

R10B solved deterministic utility ownership and footprint regressions, but the
actual Godot close-processing capture still read as one smooth blue tank on a
table. This refinement changes only cooker_processor art. IDs, footprint,
sockets, arrangements, materials, gameplay logic, T03 routes and T04 camera
authority remain frozen.
"""
from __future__ import annotations

import math
import legacy_station_kit_v1 as legacy
import reference_utility_stations_v2 as v2

UTILITY_IDS=v2.UTILITY_IDS


def _leg(b,x,z,h=.72):
    b.beveled_box("wood",(x,.10+h*.5,z),(.18,h,.18),.045)
    b.beveled_box("dark",(x,.09,z),(.25,.10,.25),.035)


def _brace(b,a,c):
    b.rod_between("wood_light",a,c,.052,8)


def build_cooker_processor():
    """Layered early-camp cooking/processing station with a readable hot chamber."""
    b=legacy.MeshBuilder("cooker_processor")
    v2.snow(b,(2.45,.14,2.15))

    for x in (-.82,.82):
        for z in (-.70,.70):
            _leg(b,x,z,.72)
    for z in (-.68,.68):
        b.beveled_box("wood",(0,.40,z),(1.86,.18,.18),.045)
        _brace(b,(-.72,.24,z),(.72,.62,z))
        _brace(b,(-.72,.62,z),(.72,.24,z))
    for x in (-.70,.70):
        b.beveled_box("wood_light",(x,.72,0),(.16,.15,1.52),.040)

    b.beveled_box("dark",(0,.72,0),(1.52,.18,1.28),.075)
    b.lathe("metal",(0,.78,0),[(.52,0),(.68,.10),(.72,.36),(.66,.72),(.52,.86)],20)
    b.lathe("blue",(0,.84,0),[(.46,0),(.60,.10),(.63,.33),(.57,.62),(.45,.72)],20)
    for y in (.96,1.28):
        b.torus("metal",(0,y,0),.615,.045,20,6)
    for angle in (0,math.pi/2,math.pi,3*math.pi/2):
        x=.56*math.sin(angle); z=.56*math.cos(angle)
        b.beveled_box("blue",(x,1.12,z),(.26,.54,.10),.045,rotation=(0,angle,0))
        b.cylinder("yellow",(x,1.27,z),.035,.08,8,rotation=(math.pi/2,0,0))

    # Standard T05 front camera looks toward the +Z face, so the hot chamber
    # is deliberately authored there rather than hidden on the reverse face.
    b.beveled_box("dark",(0,1.02,.665),(1.02,.74,.13),.085)
    b.beveled_box("metal",(0,1.02,.745),(.80,.56,.09),.060)
    b.beveled_box("orange",(0,1.00,.805),(.56,.35,.045),.050)
    b.beveled_box("yellow",(0,1.03,.835),(.32,.20,.028),.035)
    for x in (-.47,.47):
        b.beveled_box("wood_light",(x,1.02,.79),(.12,.72,.12),.040)
        for y in (.78,1.26):
            b.cylinder("cream",(x,y,.86),.035,.045,8,rotation=(math.pi/2,0,0))
    b.beveled_box("wood_light",(0,1.39,.79),(1.06,.12,.12),.040)
    b.beveled_box("snow",(-.18,1.47,.80),(.55,.065,.13),.025,rotation=(0,.05,.02))

    b.cylinder("metal",(0,1.62,0),.53,.15,20)
    b.cylinder("cream",(-.04,1.74,.02),.40,.10,18)
    b.torus("orange",(-.04,1.82,.02),.20,.040,14,5)
    b.cylinder("dark",(.46,2.00,-.28),.16,.68,16)
    b.torus("metal",(.46,2.25,-.28),.18,.035,14,5)
    b.cylinder("blue",(.46,2.38,-.28),.20,.12,14)
    b.torus("orange",(.46,2.46,-.28),.22,.045,14,5)
    b.beveled_box("snow",(.36,2.53,-.31),(.30,.06,.22),.025,rotation=(0,.08,.02))

    b.rod_between("metal",(-.58,1.30,-.22),(-.88,1.58,-.22),.055,10)
    b.rod_between("metal",(-.88,1.58,-.22),(-.88,1.58,.24),.055,10)
    b.torus("orange",(-.88,1.58,.28),.20,.045,14,6,rotation=(math.pi/2,0,0))
    for angle in (0,math.pi/2,math.pi,3*math.pi/2):
        b.rod_between("orange",(-.88,1.58,.30),(-.88+math.sin(angle)*.18,1.58+math.cos(angle)*.18,.30),.025,7)
    b.cylinder("cream",(-.88,1.58,.34),.055,.10,10,rotation=(math.pi/2,0,0))

    b.beveled_box("wood_light",(.73,.94,.20),(.40,.10,.70),.040)
    b.beveled_box("blue",(.73,1.02,.20),(.34,.06,.62),.030)
    for z in (-.02,.20,.42):
        b.lathe("cream",(.73,1.08,z),[(.07,0),(.09,.025),(.08,.16),(.055,.19)],10)
        b.torus("yellow",(.73,1.245,z),.06,.015,10,4)

    b.beveled_box("dark",(0,1.10,-.65),(.70,.45,.10),.050)
    b.beveled_box("blue",(0,1.10,-.715),(.50,.29,.055),.035)
    for x in (-.17,.17):
        b.cylinder("orange",(x,1.10,-.755),.045,.045,9,rotation=(math.pi/2,0,0))

    b.beveled_box("snow",(-.24,1.90,-.03),(.54,.06,.38),.025,rotation=(0,.08,.02))
    b.beveled_box("snow",(.56,.82,-.51),(.34,.055,.22),.022,rotation=(0,-.08,-.01))
    return b


def build_utility_stations():
    result=v2.build_utility_stations()
    result["cooker_processor"]=build_cooker_processor()
    assert tuple(sorted(result))==tuple(sorted(UTILITY_IDS))
    return result


def quality_report():
    assets=build_utility_stations()
    return {
        "asset_ids":list(UTILITY_IDS),
        "triangles":{name:asset.triangle_count() for name,asset in assets.items()},
        "materials":{name:sorted(asset.surfaces) for name,asset in assets.items()},
    }


if __name__=="__main__":
    import json
    print(json.dumps(quality_report(),indent=2,sort_keys=True))
