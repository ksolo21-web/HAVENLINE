"""New author-created six-post bridge geometry guide; no existing bitmap input.

The identical explicit six-post mesh is projected from two opposing above-ground
cameras. Gray/wood/blue are authoring conventions, never recovered source facts.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb

ROOT=Path(__file__).resolve().parent
PARAMETERS={
 'guide_id':'six-post-bridge-r1',
 'origin':'AUTHOR_CREATED_MATHEMATICAL_GUIDE',
 'source_evidence':False,
 'existing_bitmaps_read_or_modified':[],
 'units':'Abstract authoring units, not game dimensions',
 'ground_plane':'z=0',
 'deck':{'x_min':-1.12,'x_max':1.12,'y_min':-2.2,'y_max':2.2,'bottom_z':0.15,'top_z':0.25,'plank_count':11,'plank_gap':0.012},
 'post_count':6,'cap_count':6,
 'post_positions':[
  {'id':'A1','x':-1.0,'y':-2.0}, {'id':'A2','x':-1.0,'y':0.0}, {'id':'A3','x':-1.0,'y':2.0},
  {'id':'B1','x':1.0,'y':-2.0}, {'id':'B2','x':1.0,'y':0.0}, {'id':'B3','x':1.0,'y':2.0}],
 'post_bottom_z':0.25,'post_top_z':1.3,'post_body_width':0.16,'cap_width':0.24,'cap_bottom_z':1.22,
 'rope_segments':[{'from':'A1','to':'A2'},{'from':'A2','to':'A3'},{'from':'B1','to':'B2'},{'from':'B2','to':'B3'}],
 'rope_endpoint_z':1.06,'rope_midpoint_sag':0.075,'rope_radius':0.022,
 'camera_positions':{'front':[6.0,-8.0,3.0],'rear':[-6.0,8.0,3.0]},
 'camera_target':[0.0,0.0,0.65],'projection':'orthographic',
 'camera_interpretation':'Exactly opposing horizontal positions at the same positive z; both views show the identical object.',
 'panels':['FRONT OBLIQUE','REAR OBLIQUE'],
 'diagram_conventions':{'deck_color':'#b9c3cc','wood_color':'#98734f','blue_cap_color':'#2d7097','rope_color':'#c09a66','A_label_color':'#25668d','B_label_color':'#9a5b32'},
 'drawing_scope':'Control only post/cap count, physical positions and camera opposition for the lower-middle rear bridge panel. Exactly three posts per rail and two rails. Original approved/source bridge art remains the authority for all style and construction; this guide is not final art, source evidence or game dimensions.'}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def facts(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}

def mesh_box(low, high, color):
    x0, y0, z0 = low
    x1, y1, z1 = high
    points = np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
                       [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]], dtype=float)
    return [(points[index], color) for index in [[0,3,2,1],[4,5,6,7],[0,1,5,4],
                                                [1,2,6,5],[2,3,7,6],[3,0,4,7]]]

def tube(start, end, radius, color, sides=8):
    start, end = np.asarray(start), np.asarray(end)
    direction = end - start
    direction /= np.linalg.norm(direction)
    auxiliary = np.array([0.0, 0.0, 1.0]) if abs(direction[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    horizontal = np.cross(direction, auxiliary)
    horizontal /= np.linalg.norm(horizontal)
    vertical = np.cross(direction, horizontal)
    angles = np.arange(sides) * 2.0 * math.pi / sides
    offsets = radius * (np.cos(angles)[:,None] * horizontal + np.sin(angles)[:,None] * vertical)
    a, b = start + offsets, end + offsets
    faces = [(np.array([a[i],a[(i+1)%sides],b[(i+1)%sides],b[i]]), color) for i in range(sides)]
    faces += [(a[::-1], color), (b, color)]
    return faces

def camera(eye):
    eye = np.asarray(eye, dtype=float)
    target = np.asarray(PARAMETERS['camera_target'], dtype=float)
    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward,[0.0,0.0,1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right,forward)
    return eye,target,forward,right,up

def project(points, basis):
    eye,target,forward,right,up = basis
    points = np.asarray(points)
    return np.column_stack(((points-target)@right,(points-target)@up))

def draw_faces(ax, faces, basis):
    eye,target,forward,right,up = basis
    light = np.array([-0.4,-0.6,1.0]); light /= np.linalg.norm(light)
    projected, colors = [],[]
    for vertices,color in sorted(faces,key=lambda row: np.mean((row[0]-eye)@forward),reverse=True):
        normal = np.cross(vertices[1]-vertices[0],vertices[2]-vertices[0])
        normal /= max(np.linalg.norm(normal),1e-12)
        shade = 0.77 + 0.23*abs(np.dot(normal,light))
        projected.append(project(vertices,basis))
        colors.append(np.clip(np.asarray(to_rgb(color))*shade,0,1))
    collection = PolyCollection(projected,facecolors=colors,edgecolors='none',closed=True,zorder=3)
    ax.add_collection(collection)



def bridge_mesh():
    deck=PARAMETERS['deck']; c=PARAMETERS['diagram_conventions']
    faces=[]
    plank_edges=np.linspace(deck['y_min'],deck['y_max'],deck['plank_count']+1)
    for y0,y1 in zip(plank_edges[:-1],plank_edges[1:]):
        faces += mesh_box([deck['x_min'],y0+deck['plank_gap']/2,deck['bottom_z']],
                          [deck['x_max'],y1-deck['plank_gap']/2,deck['top_z']],c['deck_color'])
    for post in PARAMETERS['post_positions']:
        x,y=post['x'],post['y']; a=PARAMETERS['post_body_width']/2; b=PARAMETERS['cap_width']/2
        faces += mesh_box([x-a,y-a,PARAMETERS['post_bottom_z']],[x+a,y+a,PARAMETERS['cap_bottom_z']],c['wood_color'])
        faces += mesh_box([x-b,y-b,PARAMETERS['cap_bottom_z']],[x+b,y+b,PARAMETERS['post_top_z']],c['blue_cap_color'])
    posts={p['id']:p for p in PARAMETERS['post_positions']}
    for segment in PARAMETERS['rope_segments']:
        start,end=posts[segment['from']],posts[segment['to']]
        t=np.linspace(0,1,33)
        points=np.column_stack((start['x']+(end['x']-start['x'])*t,
                                start['y']+(end['y']-start['y'])*t,
                                PARAMETERS['rope_endpoint_z']-4*PARAMETERS['rope_midpoint_sag']*t*(1-t)))
        for p0,p1 in zip(points[:-1],points[1:]):
            faces += tube(p0,p1,PARAMETERS['rope_radius'],c['rope_color'])
    return faces


def panel(ax,eye,title):
    basis=camera(eye)
    ax.set_aspect('equal'); ax.set_xlim(-2.75,2.75); ax.set_ylim(-1.22,1.94); ax.axis('off')
    ground=np.array([[-1.45,-2.5,0],[1.45,-2.5,0],[1.45,2.5,0],[-1.45,2.5,0]])
    ax.add_collection(PolyCollection([project(ground,basis)],facecolors=['#eaf0f4'],edgecolors=['#d3dfe7'],linewidths=0.6,zorder=0))
    for x in [-1.0,0.0,1.0]:
        p=project([[x,-2.4,0],[x,2.4,0]],basis); ax.plot(p[:,0],p[:,1],color='#d9e2e9',lw=.5,zorder=1)
    for y in [-2.0,-1.0,0.0,1.0,2.0]:
        p=project([[-1.35,y,0],[1.35,y,0]],basis); ax.plot(p[:,0],p[:,1],color='#d9e2e9',lw=.5,zorder=1)
    faces=bridge_mesh(); draw_faces(ax,faces,basis)
    annotations=[]
    for post in PARAMETERS['post_positions']:
        point=project([[post['x'],post['y'],PARAMETERS['post_top_z']]],basis)[0]
        label_position=point+np.array([0.0,0.25])
        color=PARAMETERS['diagram_conventions'][post['id'][0]+'_label_color']
        ax.annotate(post['id'],xy=point,xytext=label_position,ha='center',va='center',fontsize=15,fontweight='bold',color=color,
                    bbox={'boxstyle':'round,pad=.23','fc':'#ffffff','ec':color,'lw':0.7},
                    arrowprops={'arrowstyle':'-','color':color,'lw':0.95,'shrinkA':2,'shrinkB':2},zorder=8)
        annotations.append({'id':post['id'],'physical_cap_top':[post['x'],post['y'],PARAMETERS['post_top_z']],
                            'projected_cap_top':point.tolist(),'projected_label_center':label_position.tolist()})
    ax.text(.5,1.075,title,transform=ax.transAxes,ha='center',va='bottom',fontsize=18,fontweight='bold',color='#1c3140')
    ax.text(.5,1.015,'Camera '+str(tuple(int(v) for v in eye))+' · six posts / six blue caps',transform=ax.transAxes,ha='center',va='bottom',fontsize=12,color='#526879')
    ax.text(.5,-.07,'Same physical bridge · labels retain their physical identity',transform=ax.transAxes,ha='center',va='top',fontsize=11.5,color='#526879')
    return {'camera_position':eye,'orthographic_basis':{'forward':basis[2].tolist(),'right':basis[3].tolist(),'up':basis[4].tolist()},
            'post_count':6,'cap_count':6,'rope_segment_count':4,'rendered_polygon_faces':len(faces),'post_annotations':annotations}

assert not (ROOT/'six-post-bridge-r1.png').exists(), 'Create a new revision; do not overwrite prior guides.'
dump(ROOT/'parameters.json',PARAMETERS)
posts=PARAMETERS['post_positions']; identifiers=[p['id'] for p in posts]
front,rear=camera(PARAMETERS['camera_positions']['front']),camera(PARAMETERS['camera_positions']['rear'])
all_positions=[(p['x'],p['y']) for p in posts]
checks={
 'exactly_six_posts_and_six_caps':len(posts)==PARAMETERS['post_count']==PARAMETERS['cap_count']==6,
 'six_unique_physical_post_positions':len(set(all_positions))==6,
 'exact_labels_A1_A2_A3_B1_B2_B3':identifiers==['A1','A2','A3','B1','B2','B3'],
 'rail_A_exactly_three_at_x_minus1_y_minus2_0_plus2':[(p['x'],p['y']) for p in posts if p['id'].startswith('A')]==[(-1.,-2.),(-1.,0.),(-1.,2.)],
 'rail_B_exactly_three_at_x_plus1_y_minus2_0_plus2':[(p['x'],p['y']) for p in posts if p['id'].startswith('B')]==[(1.,-2.),(1.,0.),(1.,2.)],
 'all_caps_finish_z1_3':PARAMETERS['post_top_z']==1.3,
 'all_post_bases_start_on_deck_z0_25':PARAMETERS['post_bottom_z']==PARAMETERS['deck']['top_z']==.25,
 'rope_has_two_segments_on_each_of_two_rails':PARAMETERS['rope_segments']==[{'from':'A1','to':'A2'},{'from':'A2','to':'A3'},{'from':'B1','to':'B2'},{'from':'B2','to':'B3'}],
 'cameras_exactly_requested_opposite_horizontal_positions':PARAMETERS['camera_positions']=={'front':[6.,-8.,3.],'rear':[-6.,8.,3.]},
 'both_cameras_above_ground':bool(front[0][2]>0 and rear[0][2]>0),
 'camera_heading_exactly_opposed_and_equal_elevation':bool(np.allclose(front[2][:2],-rear[2][:2]) and np.isclose(front[2][2],rear[2][2])),
 'same_mesh_function_for_both_views':True,
 'no_existing_bitmap_loaded_or_modified':PARAMETERS['existing_bitmaps_read_or_modified']==[]}
assert all(checks.values())
for basis in [front,rear]:
    cap_points=project([[p['x'],p['y'],1.3] for p in posts],basis)
    assert len({tuple(np.round(p,10)) for p in cap_points})==6
checks['all_six_cap_centers_are_distinct_in_both_projections']=True
dump(ROOT/'geometry-checks.json',{'status':'PASS_BUILDER_GEOMETRY_CHECKS','independent':False,'mandatory_checks':checks,
 'visual_approval':'Pending root and separate critic inspection of the actual PNG.'})
matplotlib.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'havenline-six-post-bridge-r1'})
fig=plt.figure(figsize=(16,8),facecolor='#f7f9fb')
fig.text(.5,.96,'SIX-POST BRIDGE · EXACT POSITION GUIDE',ha='center',va='top',fontsize=23,fontweight='bold',color='#162d3b')
fig.text(.5,.907,'AUTHOR-CREATED DIAGRAM  ·  two rails × three posts  ·  identical geometry from opposite cameras',ha='center',va='top',fontsize=13,color='#496275')
records=[]
for x,eye,title in [(.035,[6.,-8.,3.],'FRONT OBLIQUE'),(.535,[-6.,8.,3.],'REAR OBLIQUE')]:
    records.append(panel(fig.add_axes([x,.285,.43,.49]),eye,title))
fig.text(.5,.195,'A rail: x=-1     A1 y=-2 · A2 y=0 · A3 y=+2',ha='center',va='center',fontsize=13,color='#25668d')
fig.text(.5,.151,'B rail: x=+1     B1 y=-2 · B2 y=0 · B3 y=+2',ha='center',va='center',fontsize=13,color='#9a5b32')
fig.text(.5,.103,'Deck top z=0.25   |   Every post top z=1.30   |   Exactly six cap centers; no fourth post on either rail.',ha='center',va='center',fontsize=12,color='#2b4557')
fig.text(.5,.047,'Position, count and camera guide only. Abstract units and diagram colors are authored; existing source art still controls the final bridge design.',ha='center',va='center',fontsize=10.5,color='#607789')
png=ROOT/'six-post-bridge-r1.png'; svg=ROOT/'six-post-bridge-r1.svg'
fig.savefig(png,dpi=160,facecolor=fig.get_facecolor(),metadata={'Title':'Havenline six-post bridge — author-created position guide'})
fig.savefig(svg,facecolor=fig.get_facecolor(),metadata={'Date':None,'Title':'Havenline six-post bridge — author-created position guide'})
plt.close(fig)
provenance={'schema_version':1,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'author':'/root/missing_archive',
 'authoring_request':'Root requested a new exact six-post bridge guide, three posts on each of x=±1 rails at y=-2,0,+2, with opposing above-ground cameras (6,-8,3) and (-6,8,3).',
 'origin':'AUTHOR_CREATED_MATHEMATICAL_GUIDE','source_evidence':False,
 'image_operation':'New vector/geometry rendering only; no existing bitmap loaded or modified.',
 'code':facts(Path(__file__)),'parameters':facts(ROOT/'parameters.json'),'builder_geometry_checks':facts(ROOT/'geometry-checks.json'),
 'png':facts(png),'svg':facts(svg),'panels':records,
 'intended_use':'Position/count guide for the lower-middle rear bridge panel only; original source art remains the style authority.',
 'imagegen_input_approval':'Pending actual root and independent critic PNG inspection; not final art or recovered source evidence.'}
dump(ROOT/'provenance.json',provenance)
print(json.dumps({'png':provenance['png'],'svg':provenance['svg'],'geometry_checks':checks,'independent_visual_review':'PENDING'},indent=2))
