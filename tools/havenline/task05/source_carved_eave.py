"""Actual volume sculpt of the owner-render T05 front timber eave.

Uses real nonrectangular source geometry and the original material pixel crop.
Only this one part. Not a final cooker, nor a camera-calibrated reconstruction.
"""
import numpy as np
import trimesh
from trimesh.visual.texture import TextureVisuals

def build_carved_eave(material,map_pt):
    # Coordinate pairs are 1280-wide displayed reference coordinates.
    # map_pt converts them to the ACTUAL 1536x1536 owner source reference.
    upper=np.asarray([
      [359,411],[375,392],[407,393],[435,392],[469,390],[516,389],
      [554,390],[595,385],[634,388],[669,391],[705,390],
      [735,386],[774,384],[808,386],[839,401]],float)
    lower=np.asarray([
      [359,436],[376,446],[407,450],[433,450],[470,452],
      [512,451],[555,449],[598,450],[632,449],[670,451],
      [705,451],[738,448],[771,451],[809,449],[840,443]],float)
    nx,ny=112,20
    rows=(nx+1)*(ny+1)
    xs=np.linspace(359,840,nx+1)
    top=np.interp(xs,upper[:,0],upper[:,1])
    bottom=np.interp(xs,lower[:,0],lower[:,1])
    def at(layer,i,j):return layer*rows+i*(ny+1)+j
    vertices=[];uv=[]
    for layer in (0,1):
        for i,xx in enumerate(xs):
            u=i/nx
            for j in range(ny+1):
                v=j/ny
                yy=(1-v)*top[i]+v*bottom[i]
                xxworld,yworld=map_pt(xx,yy)
                if layer==0:
                    # Physical shallow hand-hewn channels, not painted grooves.
                    grain=(.011*np.sin(25*u+3*v)+.006*np.sin(77*u+11*v))*(
                      .4+.6*np.sin(np.pi*v)**2)
                    carved=.014*np.exp(-((v-(.63+.10*np.sin(8*u)))**2)/.0004)
                    notch=.018*np.exp(-((u-.38)**2)/.0005)*np.exp(-((v-.90)**2)/.001)
                    depth=.61+grain-carved-notch
                else:
                    depth=-.12
                vertices.append((xxworld,yworld,depth))
                uv.append((u,v))
    faces=[]
    for i in range(nx):
        for j in range(ny):
            a,b,c,d=at(0,i,j),at(0,i+1,j),at(0,i+1,j+1),at(0,i,j+1)
            faces.extend(((a,b,c),(a,c,d)))
            a,b,c,d=at(1,i,j),at(1,i+1,j),at(1,i+1,j+1),at(1,i,j+1)
            faces.extend(((a,c,b),(a,d,c)))
    for i in range(nx):
        for j in (0,ny):
            a,b=at(0,i,j),at(0,i+1,j)
            aa,bb=at(1,i,j),at(1,i+1,j)
            faces.extend(((a,aa,bb),(a,bb,b)))
    for j in range(ny):
        for i in (0,nx):
            a,b=at(0,i,j),at(0,i,j+1)
            aa,bb=at(1,i,j),at(1,i,j+1)
            faces.extend(((a,b,bb),(a,bb,aa)))
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False,
        visual=TextureVisuals(uv=uv,material=material))
    mesh.fix_normals()
    assert mesh.is_watertight and mesh.is_winding_consistent
    return mesh
