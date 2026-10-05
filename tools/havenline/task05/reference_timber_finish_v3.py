"""R16 authored timber finish; integrated local faces, no overlay strips."""
import math
import legacy_station_kit_v1 as legacy
from reference_surface_relief_v2 import SurfaceReliefBuilder


def _seed(center, size):
    return math.sin(center[0]*3.1+center[1]*4.7+center[2]*2.3+sum(size)*1.7)


def _grain(t, u, seed):
    # Three broad gently bent lines plus one broad eye knot: screen-scale shapes.
    bend=.12*math.sin(t*2.8+seed)+.055*math.sin(t*5.1-seed)
    stripes=sum(math.exp(-((u-c-bend)/.20)**2) for c in (-.62,.02,.63))
    eye_t=.15+.12*seed;eye_u=.22+.10*seed
    r=math.sqrt(((t-eye_t)/.34)**2+((u-eye_u)/.39)**2)
    knot= .30*math.exp(-((r-.65)/.28)**2)+ .22*math.exp(-(r/.29)**2)
    envelope=max(0.,1-t*t)*max(0.,1-u*u)
    carved=min(1.,.52*stripes+knot)*envelope
    shade=1.4-.80*stripes*envelope-knot*envelope+.055*math.cos(u*3.5+seed)
    return carved, max(.38,min(1.45,shade))


def _end(u,v,seed):
    # Concentric broad ellipses on the existing endface, no overlay ring geometry.
    r=math.sqrt((u+.06*seed)**2+((v-.05*seed)*1.12)**2)
    rings=.5+.5*math.cos(r*math.pi*3.4+.18*seed)
    edge=max(0.,1-max(abs(u),abs(v))**3)
    shade=.80+.15*rings-.17*math.exp(-(r/.26)**2)
    return (1-rings)*edge, max(.53,min(1.,shade))


original_carved_board = SurfaceReliefBuilder._carved_board

def carved_board(self,material,center,size,bevel,rotation):
    if not (max(size)>=.75 and min(size)>=.17):
        # Preserve the validated broad face finish on thin planks. Dense heroic
        # grain on a narrow pad seam aliases into dots at gameplay distance.
        return original_carved_board(self,material,center,size,bevel,rotation)
    axis=max(range(3),key=lambda i:size[i]); half=tuple(v*.5 for v in size)
    bevel=max(.001,min(bevel,min(half)*.46));inner=tuple(v-bevel for v in half)
    hero=max(size)>=.75 and min(size)>=.17
    seed=_seed(center,size)
    verts,norms,inds,pigments=[],[],[],[]
    def profile(p,fixed,sign):
        if fixed==axis:
            others=[i for i in range(3) if i!=axis]
            u,v=(p[i]/inner[i] for i in others)
            val,col=_end(u,v,seed)
        else:
            cross=next(i for i in range(3) if i not in (axis,fixed))
            t,u=p[axis]/inner[axis],p[cross]/inner[cross]
            val,col=_grain(t,u,seed+sign*.18)
        envelope=1. if fixed==axis else max(0.,1-(p[axis]/inner[axis])**2)
        return min(.008,size[fixed]*.06)*val*envelope,col
    for fixed,ua,va,sign in ((0,1,2,1),(0,1,2,-1),(1,0,2,1),(1,0,2,-1),(2,0,1,1),(2,0,1,-1)):
        def coords(a):
            if hero:
                fractions=(-1,-.67,-.33,0,.33,.67,1) if fixed!=axis and a==axis else (-1,-.5,0,.5,1)
                return [-half[a]]+[inner[a]*f for f in fractions]+[half[a]]
            return [-half[a],-inner[a],inner[a],half[a]] if fixed==axis else [-half[a],-inner[a],-.4*inner[a],.4*inner[a],inner[a],half[a]]
        us,vs=coords(ua),coords(va);grid=[]
        for vv in vs:
            row=[]
            for uu in us:
                p=[0.,0.,0.];p[fixed]=sign*half[fixed];p[ua]=uu;p[va]=vv
                q=[max(-inner[i],min(inner[i],p[i])) for i in range(3)]
                n=legacy.vnorm(legacy.vsub(p,q));pos=list(legacy.vadd(q,legacy.vmul(n,bevel)));shade=1.
                if abs(uu)<=inner[ua] and abs(vv)<=inner[va]:
                    depth,shade=profile(p,fixed,sign);pos[fixed]-=sign*depth
                    normal=[0.,0.,0.];normal[fixed]=sign
                    for tangent in (ua,va):
                        eps=.0001;a=list(p);b=list(p);a[tangent]+=eps;b[tangent]-=eps
                        normal[tangent]=(profile(a,fixed,sign)[0]-profile(b,fixed,sign)[0])/(2*eps)
                    n=legacy.vnorm(normal)
                row.append(len(verts));verts.append(pos);norms.append(n);pigments.append(shade)
            grid.append(row)
        for v in range(len(vs)-1):
            for u in range(len(us)-1):
                a,b,c,d=grid[v][u],grid[v][u+1],grid[v+1][u+1],grid[v+1][u]
                inds.extend((a,b,c,a,c,d))
    start=len(self._surface(material).positions);self.triangles(material,verts,norms,inds,center,rotation)
    self.vertex_pigments.setdefault(material,{}).update((start+i,s) for i,s in enumerate(pigments) if s!=1.)

original_cylinder=SurfaceReliefBuilder.cylinder

def cylinder(self,material,center,radius,height,segments=16,rotation=(0,0,0),top_radius=None):
    if self.name=='hearth_vessel' or material not in ('wood','wood_light') or radius<.065 or height<.45:
        return original_cylinder(self,material,center,radius,height,segments,rotation,top_radius)
    top_radius=radius if top_radius is None else top_radius
    seed=_seed(center,(radius,height,top_radius));verts,norms,inds,shade=[],[],[],[]
    slope=(radius-top_radius)/max(height,1e-6)
    axial=5 if self.name=="fishing_rack" and radius>=.085 and height>=.9 else 1
    for ring in range(axial+1):
        t=ring/axial; y=-height*.5+t*height;rad=radius+(top_radius-radius)*t
        for i in range(segments):
            a=math.tau*i/segments
            # Inward sculpted bark facet (never broadens declared member bound).
            dent=1-.027*(.5+.5*math.sin(a*3+seed+.28*math.sin(t*5)))
            verts.append((math.cos(a)*rad*dent,y,math.sin(a)*rad*dent));norms.append(legacy.vnorm((math.cos(a),slope,math.sin(a))))
            shade.append(.45+.95*math.sin(a*2.1+seed+.27*math.sin(t*5))**2)
    for ring in range(axial):
        for i in range(segments):
            j=(i+1)%segments; a=ring*segments+i;b=ring*segments+j;c=(ring+1)*segments+i;d=(ring+1)*segments+j
            inds.extend((a,d,b,a,c,d))
    for sign,rad in ((-1,radius),(1,top_radius)):
        rings=[]
        for frac in (0.,.48,1.):
            ring=[]
            count=1 if frac==0 else segments
            for i in range(count):
                a=math.tau*i/max(count,1);ring.append(len(verts))
                rim_dent=1-.027*(.5+.5*math.sin(a*3+seed+.28*math.sin(t*5)))
                cap_radius=rad*frac*(rim_dent if frac==1. else 1.)
                verts.append((math.cos(a)*cap_radius,sign*height*.5,math.sin(a)*cap_radius));norms.append((0,sign,0))
                shade.append((.55 if frac==0 else .98 if frac==.48 else .65)+.035*math.cos(a+seed))
            rings.append(ring)
        for i in range(segments):
            j=(i+1)%segments;inds.extend((rings[0][0],rings[1][i],rings[1][j],rings[1][i],rings[2][i],rings[2][j],rings[1][i],rings[2][j],rings[1][j]))
    start=len(self._surface(material).positions);self.triangles(material,verts,norms,inds,center,rotation)
    self.vertex_pigments.setdefault(material,{}).update((start+i,s) for i,s in enumerate(shade))


def install():
    SurfaceReliefBuilder._carved_board=carved_board
    SurfaceReliefBuilder.cylinder=cylinder
