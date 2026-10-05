"""R01-only sculpted platework refinement; original V3 stays immutable.

The same nine shared materials are used. Neutral cream is tinted per vertex
for matte painted iron; this avoids changing shared PBR definitions, creating
material-name collisions, or making any other station emissive.
"""
from __future__ import annotations
import math
import numpy as np
from reference_hearth_v3 import Model, Part, furnace as previous_furnace, rotation, basis_from_y, PALETTE


def paint(part, rgb, variation=0.035):
    """Apply authored local color through the existing neutral matte material."""
    part.material = 'cream'
    base=np.array(PALETTE['cream'][0])
    p=part.vertices
    texture=np.sin(p[:,0]*9.7+p[:,2]*8.1)*np.sin(p[:,1]*7.9)*variation
    height=(p[:,1]-p[:,1].min())/max(float(np.ptp(p[:,1])),.001)
    tone=(.96+.08*height+texture)[:,None]
    c=np.ones((len(p),4));c[:,:3]=np.asarray(rgb)[None,:]/base[None,:]*tone
    part.colors=np.clip(c,0.,1.)


def plate(m, name, angle, profile, width=.61):
    """A closed curved plate, rather than a rectangular stave against a barrel."""
    n=9; k=len(profile); v=[]; f=[]
    for inside in (False,True):
        for y,r in profile:
            for i in range(n):
                t=i/(n-1);a=angle+(t-.5)*width
                rad=r-.065 if inside else r-.012*(abs(2*t-1)**6)
                v.append((rad*math.cos(a),y,rad*.92*math.sin(a)))
    def quad(a,b,c,d):f.extend(((a,b,c),(a,c,d)))
    offset=k*n
    for j in range(k-1):
        for i in range(n-1):
            a=j*n+i;b=a+1;c=b+n;d=a+n
            quad(a,b,c,d);quad(offset+d,offset+c,offset+b,offset+a)
    for i in range(n-1):
        quad(i+1,i,offset+i,offset+i+1)
        a=(k-1)*n+i;quad(a,a+1,offset+a+1,offset+a)
    for j in range(k-1):
        a=j*n;d=(j+1)*n;quad(a,d,offset+d,offset+a)
        a=j*n+n-1;d=(j+1)*n+n-1;quad(d,a,offset+a,offset+d)
    p=m.add(name,'cream',v,f,smooth=True)
    shade=.018*math.sin(angle*3.7)
    paint(p,(.35+shade,.315+shade,.258+shade))


def radial_rivet(m, name, r,y,angle, radius=.027):
    centre=np.array((r*math.cos(angle),y,r*.92*math.sin(angle)))
    normal=np.array((math.cos(angle),0.,math.sin(angle)))
    m.loft(name,'metal',[(-.012,radius*.86),(-.004,radius),(.012,radius*.95),(.023,radius*.72)],centre,10,matrix=basis_from_y(centre,centre+normal),tint=(1.,.91,.78))


def furnace():
    m=previous_furnace()
    # Replace only the parts corroborated in the front/reverse inspection.
    discard=('lower_shell_stave_', 'flame_', 'flame_heart_', 'glowing_coal_')
    m.parts=[p for p in m.parts if not p.name.startswith(discard)]
    for p in m.parts:
        if p.name.startswith(('upper_rounded_pressure_shell','cap_transition','chimney_wall')):
            paint(p,(.35,.315,.258),.035)
        elif p.name.startswith(('foundation_','front_step_')):
            paint(p,(.28,.255,.225),.065)
        elif p.name.startswith(('firebox_jamb','arched_keystone_')):
            paint(p,(.30,.27,.225),.025)
        elif p.name=='enamel_armor_tab':
            # The original blue enamel material remains; muted authored pigment.
            p.colors[:,:3]*=np.array((.83,.67,.58))
    profile=[(.29,.61),(.32,.655),(.40,.67),(.89,.67),(.985,.625),(1.01,.61)]
    for i in range(10):
        if i in (7,8):continue
        a=math.tau*i/10
        plate(m,'forged_lower_plate_%02d'%i,a,profile)
        radial_rivet(m,'plate_lower_bolt_%02d'%i,.67,.41,a,.021)
        radial_rivet(m,'plate_upper_bolt_%02d'%i,.655,.92,a,.023)
    # A low, connected bed of embers replaces the four isolated candle-like spikes.
    for i in range(7):
        x=-.21+.07*i
        p=m.stone('ember_coal_%02d'%i,'orange',(x,.366,-.51),(.095,.058,.14),100+i,tint=(.9,.61,.35))
    for i,(x,z,h,w) in enumerate([(-.155,-.485,.255,.098),(-.06,-.47,.38,.118),(.055,-.485,.325,.115),(.165,-.475,.23,.095)]):
        p=m.loft('sculpted_flame_%02d'%i,'orange',[(.36,0),(.395,w*.72),(.455,w),(.36+h*.62,w*.65),(.36+h*.87,w*.28),(.36+h,0)],(x,0,z),14,radii=(1,.64))
        v=p.vertices.copy();faces=p.faces.copy();m.parts.pop()
        t=np.clip((v[:,1]-.36)/h,0,1)
        v[:,0]+=.052*math.sin(i*1.4)*t*t+.018*np.sin(t*5.1+i)*t
        p=m.add('sculpted_flame_%02d'%i,'orange',v,faces)
        p.colors[:,:3]*=np.stack((np.ones_like(t),.72+.27*t,.33+.64*t),axis=1)
        m.loft('gold_flame_core_%02d'%i,'yellow',[(.37,0),(.41,w*.52),(.37+h*.40,w*.37),(.37+h*.63,0)],(x,0,z-.058),12,radii=(1,.6))
    # Bronze cast liner: a construction layer, not another token on the shell.
    m.arch('firebox_bronze_reveal','wood_light',(0,.70,-.727),(.324,.35),(.284,.325),.065,18,tint=(1.,.76,.43))
    for side in (-1,1):
        for y in (.395,.75):
            m.loft('firebox_frame_fastener','metal',[(-.01,.025),(.01,.033),(.025,.021)],(side*.366,y,-.796),10,matrix=rotation(x=math.pi/2))
    # Reference-inspired side service hatch, supporting braces and hand wheel.
    for j,z in enumerate((-.175,.005,.185)):
        p=m.bevel_box('service_hatch_panel_%d'%j,'wood_light',(.11,.57,.175),(.715,.67,z),.025,tint=(.79,.60,.40),variation=.045)
    for z in (-.305,.315):
        m.bevel_box('service_hatch_side_frame','wood_light',(.15,.76,.095),(.757,.68,z),.029,tint=(1.,.82,.55))
    for y in (.315,1.045):
        m.bevel_box('service_hatch_horizontal_frame','wood_light',(.16,.095,.71),(.755,y,.005),.025,tint=(1.,.82,.55))
    m.bevel_box('service_hatch_cross_strap','metal',(.052,.07,.57),(.837,.66,.005),.017,tint=(.86,.81,.69))
    for z in (-.28,.29):
        for y in (.35,1.01):
            m.loft('service_hatch_bolt','metal',[(-.007,.024),(.01,.032),(.025,.022)],(.847,y,z),10,matrix=rotation(z=-math.pi/2))
    # Side-frame contact seats and a mechanically readable shut-off wheel.
    for z in (-.25,.27):
        m.bevel_box('service_hatch_seat','wood',(.25,.18,.14),(.73,.265,z),.033)
    centre=np.array((.765,1.19,-.295)); B=rotation(y=-.28,x=math.pi/2)
    ring=[centre+B@np.array((.115*math.cos(a),0,.115*math.sin(a))) for a in np.linspace(0,math.tau,33)]
    m.tube('valve_handwheel','wood_light',ring,.022,8,tint=(1.,.83,.5))
    for a in np.linspace(0,math.tau,4)[:-1]:
        end=centre+B@np.array((.105*math.cos(a),0,.105*math.sin(a)))
        m.tube('valve_spoke','wood_light',[centre,end],.015,6,tint=(1.,.83,.5))
    m.loft('valve_hub','metal',[(-.04,.038),(.03,.038)],centre,12,matrix=B)
    # Deliberate pipe unions; unlike free-floating ornament each touches the pipe.
    for side in (-1,1):
        for y in (.61,1.13):
            m.ring('pipe_union_flange','metal',[(.065,-.025),(.097,-.025),(.105,0),(.097,.025),(.065,.025)],(side*.90,y,.15),16,tint=(1.,.93,.77))
    # Gauge ticks are modeled only on its existing visible face.
    for i,a in enumerate(np.linspace(-.68,3.8,8)):
        c=np.array((.73,1.,-.294));p=c+np.array((.096*math.cos(a),.096*math.sin(a),0))
        q=c+np.array((.074*math.cos(a),.074*math.sin(a),0))
        m.beam('pressure_gauge_tick_%02d'%i,'dark',p,q,.009,.006,.002)
    for p in m.parts:
        if p.name.startswith(('service_hatch_panel','service_hatch_side_frame','service_hatch_horizontal_frame')):
            paint(p,(.46,.235,.090),.055)
    from r01_ambient_bake_v4 import apply_baked_occlusion
    apply_baked_occlusion(m)
    return m


def build_legacy(builder_type):
    model=furnace();builder=builder_type('hearth_vessel')
    for part in model.parts:
        builder.triangles(part.material,part.vertices,part.normals,part.faces.reshape(-1))
    builder.reference_model=model
    return builder
