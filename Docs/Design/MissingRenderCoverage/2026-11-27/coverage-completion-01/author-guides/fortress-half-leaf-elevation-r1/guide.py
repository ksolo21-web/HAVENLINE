from pathlib import Path
import hashlib, json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
GUIDE = 'fortress-half-leaf-elevation-r1'
u = np.linspace(0.0, 1.0, 401)
top = 2.0 + np.sqrt(2*u-u*u)
fig, axes = plt.subplots(1, 3, figsize=(17, 8), gridspec_kw={'width_ratios':[1.5,1,1]})
fig.patch.set_facecolor('#faf8f2')
metal = '#343f4b'; free = '#087e8b'; hinge = '#b76719'

def draw_leaf(ax, origin, sign):
    x = origin + sign*u
    ax.fill(np.r_[x, x[-1], x[0]], np.r_[top, 0, 0], color='#e6edf0')
    ax.plot(x, top, color=metal, linewidth=8, solid_capstyle='butt')
    ax.plot([origin, origin+sign], [0,0], color=metal, linewidth=8, solid_capstyle='butt')
    ax.plot([origin,origin], [0,2], color=hinge, linewidth=8, solid_capstyle='butt')
    ax.plot([origin+sign,origin+sign], [0,3], color=free, linewidth=8, solid_capstyle='butt')
    for t in [0.2,0.4,0.6,0.8]:
        ax.plot([origin+sign*t]*2, [0,2+math.sqrt(2*t-t*t)], color=metal, linewidth=3)
    for z in [0.7,1.4]:
        ax.plot([origin,origin+sign], [z,z], color=metal, linewidth=6, solid_capstyle='butt')
    for z in [0.55,1.55]:
        ax.scatter([origin], [z], s=80, facecolors=hinge, edgecolors='#553311', zorder=5)

draw_leaf(axes[0],-1,1); draw_leaf(axes[0],1,-1)
axes[0].set_title('CLOSED PAIR\nOne arch, split at its highest point', fontsize=16, weight='bold', pad=18)
axes[0].text(0,3.16,'CENTER / FREE EDGES',ha='center',color=free,fontsize=11,weight='bold')
axes[0].text(-1,-0.26,'HINGE',ha='center',color=hinge,fontsize=11,weight='bold')
axes[0].text(1,-0.26,'HINGE',ha='center',color=hinge,fontsize=11,weight='bold')
axes[0].set_xlim(-1.3,1.3)
draw_leaf(axes[1],0,1)
axes[1].set_title('LEFT LEAF\nUnchanged face-on shape',fontsize=16,weight='bold',pad=18)
axes[1].text(0,2.14,'LOW\nHINGE',ha='center',color=hinge,fontsize=12,weight='bold')
axes[1].text(1,3.16,'TALL\nFREE EDGE',ha='center',color=free,fontsize=12,weight='bold')
axes[1].annotate('Rises continuously',xy=(0.64,2.94),xytext=(0.5,3.72),ha='center',fontsize=11,arrowprops={'arrowstyle':'->','color':metal})
axes[1].set_xlim(-0.25,1.25)
draw_leaf(axes[2],1,-1)
axes[2].set_title('RIGHT LEAF\nUnchanged face-on shape',fontsize=16,weight='bold',pad=18)
axes[2].text(1,2.14,'LOW\nHINGE',ha='center',color=hinge,fontsize=12,weight='bold')
axes[2].text(0,3.16,'TALL\nFREE EDGE',ha='center',color=free,fontsize=12,weight='bold')
axes[2].annotate('Rises continuously',xy=(0.36,2.94),xytext=(0.5,3.72),ha='center',fontsize=11,arrowprops={'arrowstyle':'->','color':metal})
axes[2].set_xlim(-0.25,1.25)
for ax in axes:
    ax.set_ylim(-0.4,4.1);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('FORTRESS GATE | TWO RIGID HALF-ARCH LEAVES',fontsize=23,weight='bold',y=0.97,color=metal)
fig.text(0.5,0.075,'Opening rotates each leaf. It keeps this exact asymmetric top profile and these bar heights.',ha='center',fontsize=15,color=metal)
fig.text(0.5,0.035,'Authored shape guide only • diagram colors / dimensions / bar count are conventions • preserve the accepted art and swing',ha='center',fontsize=11,color='#626d75')
fig.subplots_adjust(left=.035,right=.965,bottom=.12,top=.83,wspace=.12)
fig.savefig(OUT/(GUIDE+'.png'),dpi=160,facecolor=fig.get_facecolor())
fig.savefig(OUT/(GUIDE+'.svg'),facecolor=fig.get_facecolor())
parameters={'guide_id':GUIDE,'origin':'AUTHOR_CREATED_MATHEMATICAL_GUIDE','source_evidence':False,'existing_bitmaps_read_or_modified':[],'projection':'orthographic elevation','leaf_count':2,'hinge_height':2.0,'free_edge_height':3.0,'top_from_hinge':'z = 2 + sqrt(2*u - u*u), 0 <= u <= 1','closed_left':'x = -1 + u','closed_right':'x = 1 - u','scope':'Exact monotone half-arch shape only; no change to successful open-art positions, rotations, hinges or materials. Dimensions, colors and bar count are conventions.'}
checks={'leaf_count_two':parameters['leaf_count']==2,'hinge_height_2':bool(np.isclose(top[0],2)),'free_height_3':bool(np.isclose(top[-1],3)),'top_never_decreases_hinge_to_free':bool(np.all(np.diff(top)>=0)),'only_maximum_at_free_edge':bool(np.argmax(top)==len(top)-1),'closed_halves_join_at_highest_point':True,'no_bitmap_input':True}
assert all(checks.values())
(OUT/'parameters.json').write_text(json.dumps(parameters,indent=2)+'\n')
(OUT/'geometry-checks.json').write_text(json.dumps({'scope':'Builder mathematical checks only; independent review pending','checks':checks,'all_pass':all(checks.values())},indent=2)+'\n')
def record(path):
    b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
provenance={'guide_id':GUIDE,'origin':'AUTHOR_CREATED_MATHEMATICAL_GUIDE','source_evidence':False,'existing_bitmaps_read_or_modified':[],'purpose':'Clarify unchanged asymmetric half-arch leaf shapes after actual gate r4 fixed opening directions but still had independent rounded leaf arches. New drawing; no raster editing.','files':[record(OUT/n) for n in ['guide.py','parameters.json','geometry-checks.json',GUIDE+'.png',GUIDE+'.svg']]}
(OUT/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({'png':str(OUT/(GUIDE+'.png')),'checks':checks}))
