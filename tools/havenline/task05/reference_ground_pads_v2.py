"""Reference-driven T05-R03 physical camp-platform builders."""
import math
import legacy_station_kit_v1 as legacy

PAD_IDS=("pad_build","pad_upgrade","pad_input","pad_output","pad_stock","pad_payment")
TRIM={"pad_build":"yellow","pad_upgrade":"orange","pad_input":"cyan","pad_output":"blue","pad_stock":"blue","pad_payment":"green"}

def deck(asset_id):
    b=legacy.MeshBuilder(asset_id)
    trim=TRIM[asset_id]
    legacy.add_snow_foot(b,(2.02,.10,2.02),center=(0,-.015,0))
    for i,(x,z) in enumerate(((-.78,-.76),(.78,-.76),(-.78,.76),(.78,.76))):
        b.sphere("cream",(x,.10,z),(.18,.11,.16),5,10,rotation=(0,.22*i,0))
    for x in (-.62,.62):
        b.beveled_box("dark",(x,.14,0),(.13,.13,1.66),.03)
    rows=((-0.66,-.01,"wood"),(-.39,.012,"wood_light"),(-.13,-.008,"wood"),(.13,.01,"wood_light"),(.39,-.012,"wood"),(.66,.008,"wood_light"))
    for z,xoff,mat in rows:
        b.beveled_box(mat,(xoff,.27,z),(1.72,.16,.235),.045,rotation=(0,xoff*.9,0))
    for z in (-.86,.86):
        b.beveled_box("wood",(0,.28,z),(1.86,.18,.12),.035)
        b.beveled_box(trim,(0,.385,z),(1.18,.055,.055),.018)
    for x in (-.86,.86):
        b.beveled_box("wood_light",(x,.28,0),(.12,.18,1.66),.035)
        for z in (-.52,0,.52):
            b.cylinder("dark",(x,.385,z),.035,.03,8,rotation=(math.pi/2,0,0))
    b.beveled_box("snow",(-.48,.385,-.58),(.58,.07,.22),.025,rotation=(0,.08,.012))
    b.beveled_box("snow",(.56,.378,.61),(.40,.055,.18),.022,rotation=(0,-.10,-.01))
    return b

def build_ground_pads():
    result={}
    for asset_id in PAD_IDS:
        b=deck(asset_id)
        if asset_id=="pad_build":
            for x in (-.34,.34): b.beveled_box("wood_light",(x,.60,0),(.14,.50,.70),.038)
            b.beveled_box("yellow",(0,.78,0),(.92,.12,.16),.035)
            b.rod_between("dark",(-.34,.47,-.26),(.34,.74,.26),.035,8)
            b.rod_between("dark",(.34,.47,-.26),(-.34,.74,.26),.035,8)
        elif asset_id=="pad_upgrade":
            b.beveled_box("dark",(0,.47,.10),(.72,.12,.34),.035)
            b.rod_between("orange",(-.46,.50,.18),(0,.80,-.16),.060,9)
            b.rod_between("orange",(0,.80,-.16),(.46,.50,.18),.060,9)
            b.beveled_box("metal",(0,.54,-.18),(.16,.34,.16),.035)
        elif asset_id in ("pad_input","pad_output"):
            incoming=asset_id=="pad_input"; d=1.0 if incoming else -1.0; trim="cyan" if incoming else "blue"; z=-.52*d
            b.beveled_box("dark",(0,.46,z),(1.02,.13,.40),.045)
            b.beveled_box(trim,(0,.565,z),(.82,.10,.30),.035)
            for x in (-.33,.33):
                b.rod_between("metal",(x,.57,z-.20*d),(x,.57,z+.25*d),.032,8)
                b.rod_between(trim,(x,.57,z+.25*d),(x-.11,.57,z+.10*d),.032,8)
                b.rod_between(trim,(x,.57,z+.25*d),(x+.11,.57,z+.10*d),.032,8)
        elif asset_id=="pad_stock":
            for x in (-.40,.40):
                for z in (-.28,.28): b.beveled_box("wood_light",(x,.62,z),(.10,.48,.10),.028)
            for z in (-.28,.28): b.beveled_box("wood",(0,.54,z),(.86,.16,.10),.03)
            b.beveled_box("blue",(0,.47,0),(.70,.12,.42),.045)
            b.beveled_box("snow",(-.10,.76,.02),(.52,.055,.36),.022)
        else:
            b.beveled_box("dark",(0,.47,0),(.92,.14,.58),.05)
            b.beveled_box("green",(0,.56,0),(.78,.10,.46),.04)
            for i,(x,z) in enumerate(((-.23,-.10),(.05,.09),(.27,-.08))):
                b.beveled_box("cream",(x,.655+.025*i,z),(.27,.055,.34),.025,rotation=(0,.08*(i-1),0))
                b.beveled_box("yellow",(x,.69+.025*i,z),(.055,.025,.35),.01)
        result[asset_id]=b
    assert tuple(sorted(result))==tuple(sorted(PAD_IDS))
    return result
