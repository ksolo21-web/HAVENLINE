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
    b=legacy.MeshBuilder("cooker_processor"); snow(b,(2.45,.14,2.15))
    for x in (-.78,.78):
        for z in (-.66,.66): leg(b,x,z,.56)
    for z in (-.64,.64): b.beveled_box("wood",(0,.38,z),(1.82,.16,.18),.045)
    for x in (-.68,-.34,0,.34,.68): b.beveled_box("wood_light",(x,.72,0),(.25,.14,1.42),.040)
    b.lathe("blue",(0,.72,0),[(.62,0),(.76,.16),(.78,.74),(.66,1.02),(.52,1.13)],22)
    b.torus("metal",(0,1.02,0),.72,.050,20,6)
    b.beveled_box("dark",(0,.95,-.74),(1.00,.64,.10),.055)
    b.beveled_box("orange",(0,.95,-.81),(.68,.40,.055),.035)
    b.torus("yellow",(0,.95,-.85),.28,.045,16,6,rotation=(math.pi/2,0,0))
    b.cylinder("metal",(0,1.94,0),.53,.16,20)
    b.cylinder("cream",(0,2.07,0),.38,.10,18)
    b.torus("orange",(0,2.14,0),.18,.040,14,5)
    for x in (-.72,.72):
        b.lathe("cream",(x,1.02,.30),[(.18,0),(.23,.06),(.22,.30),(.16,.39)],14)
        b.torus("blue",(x,1.37,.30),.15,.028,12,5)
    b.cylinder("metal",(.58,2.05,.44),.14,.78,14)
    b.torus("orange",(.58,2.40,.44),.21,.060,14,6,rotation=(math.pi/2,0,0),arc=math.pi)
    b.beveled_box("blue",(0,.82,.79),(1.20,.16,.30),.050)
    for x in (-.42,0,.42): b.beveled_box("cream",(x,.93,.80),(.24,.08,.20),.028)
    b.beveled_box("snow",(-.24,2.18,-.04),(.62,.06,.44),.025,rotation=(0,.08,.02))
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
    b.beveled_box("blue",(-1.38,.83,-.28),(.42,.48,.42),.075)
    b.torus("orange",(-1.60,.84,-.28),.20,.050,14,6,rotation=(0,math.pi/2,0))
    for ang in (0,math.pi/2,math.pi,3*math.pi/2):
        b.rod_between("orange",(-1.63,.84,-.28),(-1.63,.84+math.sin(ang)*.20,-.28+math.cos(ang)*.20),.030,7)
    b.cylinder("cream",(-1.66,.84,-.28),.060,.16,10,rotation=(0,0,math.pi/2))
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
