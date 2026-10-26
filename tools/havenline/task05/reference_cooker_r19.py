#!/usr/bin/env python3
"""T05 R19 source rebuild: object-specific 18567.png cooker, without gameplay changes."""
from __future__ import annotations
import math
import legacy_station_kit_v1 as legacy

def build_cooker_processor():
    b=legacy.MeshBuilder("cooker_processor")
    pi=math.pi
    def fast_box(material,center,size,rotation=(0,0,0)):
        half=[v*.5 for v in size]
        for axis in range(3):
            sides=[i for i in range(3) if i!=axis]
            for sign in (-1,1):
                face=[]
                for u,v in ((-1,-1),(1,-1),(1,1),(-1,1)):
                    q=[0.,0.,0.];q[axis]=sign*half[axis]
                    q[sides[0]]=u*half[sides[0]];q[sides[1]]=v*half[sides[1]]
                    face.append(tuple(q))
                normal=tuple(float(sign if i==axis else 0) for i in range(3))
                b.triangles(material,face,[normal]*4,[0,1,2,0,2,3],center,rotation)
    # Snow/stone terrain contact.
    for x,z,rx,rz in [(-.87,-.53,.29,.19),(-.92,.62,.20,.23),(.92,-.53,.26,.22),(.88,.68,.27,.18),(-.30,.77,.32,.12),(.30,-.75,.30,.13)]:
        b.sphere("snow",(x,.05,z),(rx,.068,rz),4,8)
    for x,z in ((-1.03,-.44),(1.02,.55)):
        b.beveled_box("dark",(x,.045,z),(.15,.09,.15),.034)
    # Raised timber platform and iron shoes.
    for x in (-.99,.99):
        for z in (-.61,.61):
            b.beveled_box("wood",(x,.36,z),(.18,.65,.20),.056)
            fast_box("metal",(x,.10,z),(.23,.16,.25))
            b.cylinder("dark",(x,.14,-.743 if z<0 else .743),.035,.029,6,rotation=(pi/2,0,0))
    for z in (-.61,.61):
        b.beveled_box("wood",(0,.53,z),(2.20,.16,.18),.056)
        fast_box("blue",(0,.44,z),(2.12,.07,.16))
    for x in (-1.0,1.0):
        fast_box("wood_light",(x,.63,0),(.14,.15,1.34))
    for z in (-.52,.52):
        b.rod_between("wood_light",(-.90,.18,z),(.86,.52,z),.050,7)
    for x in (-.71,-.22,.27,.73):
        fast_box("wood_light",(x,.72,0),(.43,.14,1.31))
    # Main oven housing and structural timber.
    b.beveled_box("blue",(0,1.21,-.08),(1.07,.91,.95),.174)
    for x in (-.50,.50):
        b.beveled_box("wood",(x,1.16,-.02),(.145,.98,1.09),.056)
        fast_box("metal",(x,.77,-.46),(.17,.19,.19))
        for y in (.82,1.51):
            b.cylinder("cream",(x,y,-.590),.032,.035,7,rotation=(pi/2,0,0))
    fast_box("metal",(0,.855,-.567),(.90,.17,.074))
    b.beveled_box("blue",(0,1.67,-.11),(1.16,.15,1.05),.07)
    fast_box("metal",(0,1.71,-.10),(1.01,.057,.91))
    # Reference-specific front arched inset and mechanical saw blade (-Z).
    b.beveled_box("metal",(0,1.284,-.579),(.79,.59,.092),.090)
    fast_box("dark",(0,1.29,-.635),(.665,.495,.041))
    for x in (-.366,.366):
        b.rod_between("metal",(x,1.064,-.673),(x,1.37,-.673),.048,8)
    b.rod_between("metal",(-.366,1.065,-.673),(.366,1.065,-.673),.053,8)
    last=None
    for j in range(11):
        theta=pi-j*pi/10
        pt=(math.cos(theta)*.365,1.37+math.sin(theta)*.145,-.673)
        if last is not None:b.rod_between("metal",last,pt,.043,7)
        last=pt
    b.cylinder("metal",(.03,1.270,-.669),.205,.035,16,rotation=(pi/2,0,0))
    for i in range(12):
        a=i*math.tau/12
        verts=[(.03+radius*math.cos(ang),1.27+radius*math.sin(ang),-.694)
               for radius,ang in ((.177,a-.115),(.264,a+.055),(.189,a+.185))]
        b.triangles("metal",verts,[(0,0,-1)]*3,[0,1,2])
    b.cylinder("dark",(.03,1.270,-.708),.075,.043,12,rotation=(pi/2,0,0))
    b.cylinder("orange",(.03,1.270,-.740),.042,.053,10,rotation=(pi/2,0,0))
    # Orange crossbar and formed fittings.
    for x in (-.23,.23):
        b.rod_between("metal",(x,.905,-.624),(x,.905,-.770),.053,7)
    b.rod_between("orange",(-.25,.900,-.781),(.25,.900,-.781),.076,10)
    for x in (-.28,.28):
        b.cylinder("metal",(x,.90,-.787),.052,.032,8,rotation=(pi/2,0,0))
    # Wood raw-food bin left.
    bx=-.82
    fast_box("wood",(bx,.91,.14),(.67,.085,.79))
    for z in (-.25,.52):
        fast_box("wood_light",(bx,1.045,z),(.69,.25,.072))
    for x in (-1.143,-.497):
        fast_box("wood_light",(x,1.045,.14),(.074,.25,.80))
    for x in (-1.09,-.54):
        for z in (-.25,.52):
            fast_box("wood",(x,1.049,z),(.110,.33,.116))
            b.beveled_box("snow",(x,1.226,z),(.12,.065,.12),.035)
    for j,(x,z,rx,rz) in enumerate([(-1.04,-.06,.16,.12),(-.76,-.02,.18,.15),(-.55,.12,.13,.13),(-.93,.26,.17,.15),(-.65,.37,.17,.13)]):
        y=1.15+(j%2)*.037
        b.sphere("orange",(x,y,z),(rx,.10,rz),4,10,rotation=(0,.15*j,0))
        b.sphere("cream",(x-.025,y+.067,z+.02),(rx*.56,.03,rz*.64),3,8)
    for x,z in ((-1.04,-.28),(-.57,.54)):
        b.sphere("snow",(x,1.185,z),(.125,.072,.09),3,8)
    # Steel prepared-food pan right with raised lip.
    tx=.832
    b.beveled_box("metal",(tx,.94,.16),(.68,.12,.84),.053)
    fast_box("dark",(tx,1.010,.16),(.57,.048,.73))
    for z in (-.235,.555):
        fast_box("metal",(tx,1.11,z),(.69,.18,.062))
    for x in (.505,1.159):
        fast_box("metal",(x,1.11,.16),(.058,.18,.86))
    for x,z,w,r in ((.67,-.07,.21,.05),(.94,-.08,.18,-.12),(.67,.22,.20,.16),(.96,.26,.19,-.17)):
        b.beveled_box("orange",(x,1.145,z),(w,.155,.23),.065,rotation=(0,r,0))
        fast_box("cream",(x-.037,1.236,z),(.075,.031,.18),rotation=(0,r,0))
        fast_box("yellow",(x,1.24,z),(.034,.038,.225),rotation=(0,r,0))
    for x in (.53,1.13):
        for z in (-.26,.585):
            b.cylinder("cream",(x,1.207,z),.026,.028,6)
    # Pressure canister, hose and gauge.
    b.lathe("dark",(.45,1.20,.56),[(.13,0),(.16,.07),(.17,.31),(.13,.42),(.10,.48)],12)
    b.torus("metal",(.45,1.49,.56),.138,.025,10,5)
    b.cylinder("metal",(.45,1.71,.56),.075,.10,10)
    b.rod_between("metal",(.45,1.71,.56),(.45,1.78,.56),.036,7)
    b.rod_between("metal",(.41,1.31,.51),(.39,1.31,.41),.04,7)
    # Layered chimney, steel rings and open exit.
    px,pz=.18,.05
    b.cylinder("dark",(px,1.94,pz),.117,.33,12)
    b.cylinder("metal",(px,2.20,pz),.14,.23,12)
    for y in (2.070,2.285):
        b.torus("metal",(px,y,pz),.155,.033,12,5)
    b.cylinder("blue",(px,2.35,pz),.177,.112,12)
    b.torus("metal",(px,2.41,pz),.175,.036,12,5)
    b.cylinder("dark",(px,2.438,pz),.115,.028,12)
    # Thick overhanging irregular snow bank; keep appliance window clear.
    for x,y,z,rx,ry,rz in [
        (-.31,1.81,-.35,.36,.15,.30),(.14,1.85,-.37,.34,.19,.30),
        (.39,1.82,-.02,.31,.17,.34),(-.34,1.83,.28,.32,.16,.33),
        (.05,1.85,.34,.38,.14,.29),(-.44,1.71,-.01,.18,.12,.32)]:
        b.sphere("snow",(x,y,z),(rx,ry,rz),4,9)
    for x,y,z,rx in ((-.35,1.69,-.575,.105),(-.05,1.69,-.595,.14),(.38,1.70,-.555,.11)):
        b.sphere("snow",(x,y,z),(rx,.092,.12),3,7)
    return b
