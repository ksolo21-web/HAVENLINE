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
    for index,x in enumerate((-1.10,-.74,-.38,-.02,.34,.70,1.06)):
        b.beveled_box("wood" if index % 2 == 0 else "wood_light",(x,.82,0),(.26,.16,1.02),.045)
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
    b=legacy.MeshBuilder("intake_machine")
    for x,z,rx,rz in ((-.92,-.72,.34,.24),(.88,-.70,.31,.22),(-.92,.70,.30,.23),(.88,.72,.35,.24),(0,-.86,.42,.18),(0,.87,.38,.17)):
        b.sphere("snow",(x,.08,z),(rx,.08,rz),5,10)
    for x in (-.88,.88):
        for z in (-.66,.66): leg(b,x,z,.78)
    for z in (-.66,.66):
        b.beveled_box("wood",(0,.40,z),(1.96,.18,.20),.050)
        brace(b,-.78,.78,z)
    for x in (-.86,.86): b.beveled_box("wood_light",(x,.62,0),(.18,.16,1.55),.045)
    for x in (-.66,-.22,.22,.66): b.beveled_box("wood_light",(x,.77,.04),(.38,.12,1.36),.040)
    b.beveled_box("dark",(0,.84,-.04),(1.58,.07,1.22),.030)
    for x in (-.70,.70):
        b.beveled_box("wood",(x,1.48,-.42),(.18,1.08,.20),.050)
        b.beveled_box("blue",(x,1.52,-.30),(.12,.72,.72),.045,rotation=(.16,0,0))
    b.beveled_box("wood_light",(0,1.98,-.44),(1.60,.18,.22),.050)
    b.beveled_box("metal",(0,1.64,-.47),(1.30,.12,.62),.045,rotation=(.40,0,0))
    b.beveled_box("blue",(0,1.39,-.20),(1.26,.12,.56),.045,rotation=(-.30,0,0))
    b.beveled_box("cream",(0,1.94,-.57),(1.06,.08,.18),.030)
    for x in (-.46,0,.46): b.beveled_box("yellow",(x,1.93,-.67),(.12,.12,.08),.025)
    for z in (.02,.38):
        b.cylinder("metal",(0,1.18,z),.22,1.32,18,rotation=(0,0,math.pi/2))
        for x in (-.68,.68): b.torus("yellow",(x,1.18,z),.215,.040,16,5,rotation=(0,math.pi/2,0))
        for x in (-.34,.34): b.beveled_box("blue",(x,1.18,z),(.16,.34,.46),.040)
    for x in (-.72,.72): b.beveled_box("dark",(x,1.20,.20),(.12,.66,.68),.035)
    b.beveled_box("blue",(-.74,1.16,.18),(.30,.62,.78),.080)
    b.beveled_box("metal",(.74,1.16,.18),(.28,.54,.74),.070)
    b.torus("orange",(-.96,1.18,.16),.28,.055,16,6,rotation=(0,math.pi/2,0))
    b.cylinder("cream",(-1.02,1.18,.16),.065,.16,10,rotation=(0,0,math.pi/2))
    b.beveled_box("wood_light",(0,.88,.78),(1.55,.14,.42),.045)
    b.beveled_box("dark",(0,.97,.77),(1.34,.07,.32),.025)
    for x in (-.52,-.18,.18,.52):
        b.cylinder("cyan",(x,1.03,.77),.075,.34,10,rotation=(math.pi/2,0,0))
        b.cylinder("cream",(x,1.03,.95),.085,.04,10,rotation=(math.pi/2,0,0))
    b.beveled_box("blue",(0,.82,1.00),(1.40,.18,.16),.040)
    b.beveled_box("snow",(-.37,2.08,-.45),(.52,.07,.22),.025,rotation=(0,.08,.02))
    b.beveled_box("snow",(.55,1.50,-.22),(.26,.05,.30),.020,rotation=(0,-.10,-.03))
    return b

def build_cooker_processor():
    """Reference-built early-camp cook/processing station.

    R10D removes the dominant generic tank silhouette from R10C. The station now
    combines the 18607 cookfire + butcher-table language: a constructed timber
    chassis, a blue/dark stove core with a clearly recessed hot chamber, a real
    prep surface, cookware and an offset banded flue. IDs/footprint/sockets stay
    frozen; primitive helpers are only sub-parts, never the shipping silhouette.
    """
    b=legacy.MeshBuilder("cooker_processor"); snow(b,(2.45,.14,2.15))

    # Chunky timber chassis: four feet, perimeter rails and visible cross braces.
    for x in (-.84,.84):
        for z in (-.68,.68):
            b.beveled_box("wood",(x,.42,z),(.20,.66,.20),.050)
            b.beveled_box("dark",(x,.10,z),(.26,.10,.26),.035)
    for z in (-.68,.68):
        b.beveled_box("wood",(0,.38,z),(1.82,.18,.18),.050)
        b.rod_between("wood_light",(-.72,.22,z),(.72,.58,z),.050,7)
        b.rod_between("wood_light",(-.72,.58,z),(.72,.22,z),.050,7)
    for x in (-.76,.76):
        b.beveled_box("wood_light",(x,.66,0),(.16,.14,1.46),.040)

    # Heavy work deck with separated slats, not a single block.
    for x in (-.66,-.22,.22,.66):
        b.beveled_box("wood_light",(x,.73,-.02),(.38,.12,1.48),.045)
    b.beveled_box("dark",(0,.80,.04),(1.66,.08,1.34),.035)

    # Purpose-built stove core occupies the right half. Layered shell/trim makes
    # it read as fabricated equipment rather than a cube or cylinder.
    b.beveled_box("blue",(.34,1.13,.17),(.90,.66,.78),.120)
    b.beveled_box("dark",(.34,1.13,.565),(.72,.50,.12),.060)
    b.beveled_box("metal",(.34,1.13,.638),(.58,.38,.07),.040)
    b.beveled_box("orange",(.34,1.11,.685),(.42,.24,.045),.040)
    b.beveled_box("yellow",(.34,1.12,.714),(.24,.12,.026),.025)
    for x in (.02,.66):
        b.beveled_box("wood_light",(x,1.13,.690),(.09,.52,.08),.030)
        for y in (.93,1.33):
            b.cylinder("cream",(x,y,.742),.030,.040,7,rotation=(math.pi/2,0,0))
    b.beveled_box("wood_light",(.34,1.42,.690),(.72,.09,.08),.030)
    b.rod_between("yellow",(.63,1.09,.755),(.76,1.09,.755),.030,7)

    # Cooktop with a readable lidded pot and side pan; kept subordinate to the
    # constructed chassis so no single primitive dominates the silhouette.
    b.beveled_box("metal",(.34,1.52,.10),(.78,.10,.68),.055)
    b.lathe("dark",(.34,1.58,.08),[(.25,0),(.31,.06),(.30,.24),(.24,.31)],14)
    b.cylinder("cream",(.34,1.91,.08),.20,.07,12)
    b.torus("orange",(.34,1.95,.08),.12,.028,10,4)
    b.rod_between("metal",(-.02,1.69,-.06),(-.39,1.69,-.20),.040,7)
    b.cylinder("metal",(-.46,1.69,-.23),.18,.07,12)

    # Left prep station echoes the 18607 butcher table.
    b.beveled_box("wood_light",(-.55,1.02,-.28),(.68,.10,.58),.045)
    b.beveled_box("cream",(-.55,1.09,-.28),(.52,.055,.42),.025)
    b.sphere("orange",(-.58,1.18,-.28),(.20,.09,.14),6,12,rotation=(0,.18,0))
    b.rod_between("cream",(-.72,1.21,-.28),(-.43,1.21,-.28),.018,7)
    b.rod_between("metal",(-.78,1.15,-.05),(-.42,1.15,-.05),.025,7)
    b.beveled_box("blue",(-.55,.88,-.30),(.62,.08,.48),.030)

    # Offset flue: segmented pipe, clamp bands and snow cap.
    b.cylinder("dark",(.70,1.72,-.22),.12,.42,12)
    b.cylinder("metal",(.70,2.06,-.22),.14,.28,12)
    for y in (1.90,2.18):
        b.torus("orange",(.70,y,-.22),.145,.030,12,5)
    b.cylinder("blue",(.70,2.28,-.22),.18,.12,12)
    b.torus("yellow",(.70,2.36,-.22),.19,.035,12,5)
    b.beveled_box("snow",(.64,2.44,-.24),(.28,.06,.22),.025,rotation=(0,.08,.02))

    # Small service gauge/handwheel on the left rear adds mechanical asymmetry.
    b.rod_between("metal",(-.76,1.30,-.08),(-.92,1.48,-.08),.040,7)
    b.torus("orange",(-.92,1.49,-.08),.15,.035,10,4,rotation=(math.pi/2,0,0))
    for ang in (0,2*math.pi/3,4*math.pi/3):
        b.rod_between("orange",(-.92,1.49,-.08),(-.92+math.sin(ang)*.13,1.49+math.cos(ang)*.13,-.08),.020,6)

    # Irregular snow loading ties the machine into the winter silhouette.
    b.beveled_box("snow",(.20,1.61,-.04),(.38,.055,.26),.022,rotation=(0,.08,.02))
    b.beveled_box("snow",(-.60,1.15,-.32),(.30,.045,.24),.018,rotation=(0,-.07,-.01))
    return b

def build_conveyor_straight():
    b=legacy.MeshBuilder("conveyor_straight")
    for x,z,rx,rz in ((-1.34,-.48,.26,.18),(-1.34,.48,.24,.17),(1.34,-.48,.28,.18),(1.34,.48,.25,.17),(-.42,-.52,.32,.13),(.54,.52,.30,.13)):
        b.sphere("snow",(x,.07,z),(rx,.07,rz),5,10)
    for z in (-.46,.46):
        b.beveled_box("wood",(0,.22,z),(3.02,.18,.18),.050)
        b.rod_between("wood_light",(-1.18,.22,z),(1.18,.64,z),.050,7)
        b.rod_between("wood_light",(-1.18,.64,z),(1.18,.22,z),.050,7)
    for x in (-1.30,1.30):
        for z in (-.46,.46):
            b.beveled_box("wood",(x,.44,z),(.20,.62,.20),.050)
            b.beveled_box("dark",(x,.11,z),(.27,.10,.27),.035)
    for z in (-.48,.48):
        b.beveled_box("wood_light",(0,.62,z),(2.86,.15,.16),.045)
        b.beveled_box("blue",(0,.79,z),(2.70,.12,.12),.035)
    for x in (-1.22,1.22):
        b.beveled_box("blue",(x,.88,0),(.18,.52,1.02),.055)
        b.beveled_box("metal",(x,.79,0),(.10,.34,.86),.035)
    for i,x in enumerate((-1.05,-.75,-.45,-.15,.15,.45,.75,1.05)):
        b.beveled_box("dark" if i%2==0 else "blue",(x,.80,0),(.24,.09,.70),.030)
        b.cylinder("metal",(x,.70,0),.070,.78,10,rotation=(math.pi/2,0,0))
        b.cylinder("yellow",(x,.70,-.42),.088,.045,10,rotation=(math.pi/2,0,0))
        b.cylinder("cream",(x,.70,.42),.082,.040,10,rotation=(math.pi/2,0,0))
    b.beveled_box("blue",(-1.34,.88,-.22),(.34,.58,.50),.075)
    b.beveled_box("dark",(-1.35,.88,.20),(.28,.40,.26),.055)
    b.torus("orange",(-1.53,.90,-.22),.18,.045,14,5,rotation=(0,math.pi/2,0))
    b.cylinder("cream",(-1.57,.90,-.22),.055,.12,10,rotation=(0,0,math.pi/2))
    b.beveled_box("metal",(1.32,.88,.08),(.26,.52,.58),.065)
    b.beveled_box("blue",(1.45,.89,-.24),(.16,.30,.32),.050)
    b.beveled_box("yellow",(1.46,.92,-.49),(.22,.12,.08),.025)
    for x in (-.78,.78): b.beveled_box("wood",(x,1.10,.34),(.13,.54,.13),.040)
    b.beveled_box("wood_light",(0,1.36,.34),(1.68,.14,.16),.045)
    b.beveled_box("blue",(0,1.42,.34),(1.24,.07,.12),.025)
    b.beveled_box("snow",(-.42,.90,.49),(.52,.055,.14),.020,rotation=(0,.06,.02))
    b.beveled_box("snow",(.67,.88,-.49),(.38,.050,.14),.018,rotation=(0,-.08,-.02))
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
