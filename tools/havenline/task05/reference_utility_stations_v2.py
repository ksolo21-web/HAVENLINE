#!/usr/bin/env python3
"""T05 reference-driven rebuild for the four remaining legacy utility silhouettes.
Primary authority: user HAVENLINE early-camp board 18607.png.
Secondary polish ceiling only: HAVENLINE late-fortress board 18608.png.
IDs, footprints, sockets, arrangements and gameplay contracts remain frozen.
"""
from __future__ import annotations
import math
import legacy_station_kit_v1 as legacy

UTILITY_IDS=("fishing_rack","intake_machine","cooker_processor","conveyor_straight")

def snow(b,size): legacy.add_snow_foot(b,size)

def leg(b,x,z,h=.70):
    b.beveled_box("wood",(x,.10+h*.5,z),(.18,h,.18),.045)
    b.beveled_box("dark",(x,.09,z),(.25,.10,.25),.035)

def brace(b,x0,x1,z):
    b.rod_between("wood_light",(x0,.28,z),(x1,.80,z),.055,8)
    b.rod_between("wood_light",(x0,.80,z),(x1,.28,z),.055,8)

def build_fishing_rack():
    b=legacy.MeshBuilder("fishing_rack"); snow(b,(3.25,.12,1.45))
    for x in (-1.24,1.24):
        for z in (-.48,.48): leg(b,x,z)
    for z in (-.48,.48):
        b.beveled_box("wood",(0,.40,z),(2.66,.16,.18),.045); brace(b,-1.16,1.16,z)
    for x in (-1.10,-.74,-.38,-.02,.34,.70,1.06):
        b.beveled_box("wood_light",(x,.82,0),(.26,.16,1.02),.045)
    for x in (-1.05,1.05):
        b.rod_between("wood",(x,.82,-.42),(x,2.08,0),.105,10)
        b.rod_between("wood",(x,.82,.42),(x,2.08,0),.105,10)
        b.beveled_box("blue",(x,2.06,0),(.22,.20,.34),.055)
    b.beveled_box("wood_light",(0,2.08,0),(2.36,.20,.22),.055)
    b.beveled_box("snow",(-.42,2.18,-.02),(.78,.07,.20),.025,rotation=(0,.06,.02))
    b.cylinder("metal",(0,1.24,0),.17,1.62,18,rotation=(0,0,math.pi/2))
    for x in (-.48,.48):
        b.cylinder("blue",(x,1.24,0),.31,.34,18,rotation=(0,0,math.pi/2))
        for dx in (-.17,.17):
            b.torus("yellow",(x+dx,1.24,0),.28,.045,16,6,rotation=(0,math.pi/2,0))
        for dz in (-.16,0,.16):
            b.torus("cream",(x,1.24,dz),.235,.018,14,5,rotation=(0,math.pi/2,0))
    b.rod_between("orange",(1.04,1.24,0),(1.32,1.56,0),.055,8)
    b.cylinder("cream",(1.35,1.60,0),.075,.26,10,rotation=(0,0,math.pi/2))
    b.rod_between("wood_light",(-.96,1.92,.06),(-.24,2.50,.54),.065,9)
    b.rod_between("yellow",(-.24,2.50,.54),(-.24,.96,.58),.026,8)
    b.torus("metal",(-.24,.90,.58),.10,.025,12,5,rotation=(math.pi/2,0,0),arc=math.pi)
    b.beveled_box("blue",(0,.97,.48),(1.12,.12,.36),.035)
    for x in (-.34,0,.34):
        b.sphere("cyan",(x,1.08,.50),(.18,.07,.09),5,10)
        b.beveled_box("cream",(x+.12,1.08,.50),(.10,.035,.07),.012)
    return b

def build_intake_machine():
    b=legacy.MeshBuilder("intake_machine"); snow(b,(2.60,.14,2.40))
    for x in (-.88,.88):
        for z in (-.66,.66): leg(b,x,z,.64)
    for x in (-.92,.92): b.beveled_box("wood_light",(x,.22,0),(.16,.18,1.68),.05)
    for z in (-.62,.62): b.beveled_box("wood",(0,.48,z),(1.92,.18,.18),.05)
    b.beveled_box("blue",(0,1.34,-.26),(1.72,.16,1.08),.055,rotation=(.42,0,0))
    b.beveled_box("blue",(0,1.16,.24),(1.72,.16,.82),.055,rotation=(-.34,0,0))
    for x in (-.80,.80):
        b.beveled_box("wood_light",(x,1.27,-.05),(.13,.94,1.06),.040)
    b.beveled_box("dark",(0,1.08,-.72),(1.36,.12,.20),.035)
    b.beveled_box("orange",(0,1.08,-.81),(.92,.08,.08),.025)
    b.cylinder("metal",(0,.91,.38),.43,1.30,20,rotation=(0,0,math.pi/2))
    for x in (-.68,.68): b.torus("yellow",(x,.91,.38),.39,.045,18,6,rotation=(0,math.pi/2,0))
    for x in (-.38,0,.38): b.beveled_box("dark",(x,.91,.80),(.12,.58,.08),.025)
    b.torus("orange",(-.95,.94,.34),.30,.055,16,6,rotation=(0,math.pi/2,0))
    for ang in (0,math.pi/2,math.pi,3*math.pi/2):
        b.rod_between("orange",(-.97,.94,.34),(-.97,.94+math.sin(ang)*.30,.34+math.cos(ang)*.30),.035,8)
    b.cylinder("cream",(-.99,.94,.34),.07,.18,10,rotation=(0,0,math.pi/2))
    b.beveled_box("wood_light",(0,.67,.92),(1.60,.14,.44),.045)
    for x in (-.58,-.19,.20,.59):
        b.cylinder("cyan",(x,.78,.91),.075,.34,10,rotation=(math.pi/2,0,0))
    b.beveled_box("snow",(-.40,1.86,-.23),(.62,.07,.42),.025,rotation=(0,.06,.02))
    return b

def build_cooker_processor():
    """Layered early-camp cooking/processing station with a readable hot chamber."""
    b=legacy.MeshBuilder("cooker_processor"); snow(b,(2.45,.14,2.15))
    for x in (-.82,.82):
        for z in (-.70,.70): leg(b,x,z,.72)
    for z in (-.68,.68):
        b.beveled_box("wood",(0,.40,z),(1.86,.18,.18),.045)
        b.rod_between("wood_light",(-.72,.24,z),(.72,.62,z),.052,8)
        b.rod_between("wood_light",(-.72,.62,z),(.72,.24,z),.052,8)
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

    # Standard T05 front camera looks toward the +Z face. Keep the hot chamber
    # on that face so the purpose reads immediately at gameplay distance.
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

def build_conveyor_straight():
    b=legacy.MeshBuilder("conveyor_straight"); snow(b,(3.35,.10,1.30))
    for z in (-.46,.46):
        b.beveled_box("wood_light",(0,.20,z),(3.05,.14,.15),.045)
        b.beveled_box("blue",(0,.52,z),(2.92,.16,.14),.045)
    for x in (-1.32,1.32):
        for z in (-.46,.46): b.beveled_box("wood",(x,.39,z),(.18,.56,.18),.050)
    for x in (-1.18,-.78,-.38,.02,.42,.82,1.22):
        b.beveled_box("wood_light",(x,.64,0),(.28,.12,.82),.035)
    b.beveled_box("dark",(0,.70,0),(2.72,.08,.72),.035)
    for x in (-1.18,-.79,-.40,-.01,.38,.77,1.16):
        b.cylinder("metal",(x,.76,0),.075,.78,10,rotation=(math.pi/2,0,0))
        b.cylinder("yellow",(x,.76,-.42),.095,.055,10,rotation=(math.pi/2,0,0))
    # Keep the authored drive housing/handwheel fully inside the frozen 3.40 m
    # gameplay footprint. The first materialized R10B pass overhung the left
    # edge by ~0.09 m at the handwheel, which made the rendered mesh disagree
    # with collision/placement clearance even though the station still read well.
    b.beveled_box("blue",(-1.26,.83,-.28),(.42,.48,.42),.075)
    b.torus("orange",(-1.48,.84,-.28),.20,.050,14,6,rotation=(0,math.pi/2,0))
    for ang in (0,math.pi/2,math.pi,3*math.pi/2):
        b.rod_between("orange",(-1.51,.84,-.28),(-1.51,.84+math.sin(ang)*.20,-.28+math.cos(ang)*.20),.030,7)
    b.cylinder("cream",(-1.54,.84,-.28),.060,.16,10,rotation=(0,0,math.pi/2))
    for x in (-1.45,1.45):
        b.beveled_box("blue",(x,.86,0),(.14,.48,1.02),.045)
        b.beveled_box("snow",(x,.99,.16),(.17,.08,.46),.025)
    b.beveled_box("yellow",(1.42,.86,-.54),(.34,.12,.08),.025)
    return b

def build_utility_stations():
    result={
        "fishing_rack":build_fishing_rack(),
        "intake_machine":build_intake_machine(),
        "cooker_processor":build_cooker_processor(),
        "conveyor_straight":build_conveyor_straight(),
    }
    assert tuple(sorted(result))==tuple(sorted(UTILITY_IDS))
    return result

def quality_report():
    a=build_utility_stations()
    return {"asset_ids":list(UTILITY_IDS),
            "triangles":{k:v.triangle_count() for k,v in a.items()},
            "materials":{k:sorted(v.surfaces) for k,v in a.items()}}

if __name__=="__main__":
    import json
    print(json.dumps(quality_report(),indent=2,sort_keys=True))
