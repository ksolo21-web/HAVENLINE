"""Author-created exact double-gate geometry guide, never a bitmap edit.

Orthographic views use explicit camera bases and a painter's depth ordering.
Leaves are rigidly rotated copies of the same closed half-arch geometry.
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
from matplotlib.patches import FancyArrowPatch
from matplotlib.colors import to_rgb

ROOT = Path(__file__).resolve().parent
PARAMETERS = {
    'guide_id': 'fortress-double-gate-r2',
    'origin': 'AUTHOR_CREATED_MATHEMATICAL_GUIDE',
    'source_evidence': False,
    'existing_bitmaps_read_or_modified': [],
    'units': 'Abstract authoring units, not game dimensions',
    'wall_front_plane': 'y = 0', 'ground_plane': 'z = 0',
    'outward_half_space': 'y < 0',
    'closed_top_profile': 'z = 2 + sqrt(1 - x*x), -1 <= x <= 1',
    'hinges': {'left': [-1.0, 0.0], 'right': [1.0, 0.0]},
    'leaf_count': 2,
    'leaf_parameter': 'u in [0,1] measured from hinge toward free edge',
    'closed_left': '(-1 + u, 0, z)', 'closed_right': '(1 - u, 0, z)',
    'top_height_in_leaf_coordinates': '2 + sqrt(2*u - u*u)',
    'open_left': '(-1, -u, z)', 'open_right': '(1, -u, z)',
    'open_rotation_degrees_about_hinges': {'left': -90.0, 'right': 90.0},
    'camera_positions': {'front': [6.0, -8.0, 5.0], 'rear': [-6.0, 8.0, 5.0]},
    'camera_target': [0.0, 0.0, 1.45], 'projection': 'orthographic',
    'camera_interpretation': 'Opposite horizontal positions at the same positive z; not a negated below-ground camera.',
    'panels': ['CLOSED / FRONT OBLIQUE', 'OPEN / FRONT OBLIQUE', 'OPEN / REAR OBLIQUE'],
    'fixed_frame': {'arch_center_z': 2.0, 'inner_radius': 1.04, 'outer_radius': 1.25,
                    'y_front': 0.0, 'y_back': 0.22, 'pillar_top_z': 2.0},
    'diagram_conventions': {'left_color': '#257d91', 'right_color': '#c5842d',
                            'frame_color': '#a8b0b8', 'leaf_frame_radius': 0.025,
                            'interior_bar_radius': 0.014,
                            'interior_bar_u': [0.2, 0.4, 0.6, 0.8],
                            'crossbar_z': [0.65, 1.4]},
    'drawing_scope': 'Exact shape and outward rotation guide only. Distinct colors, bar counts, tube thickness and gray frame construction are authoring conventions, not recovered source facts or final game art.'}

def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def facts(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}

def height(u):
    return 2.0 + np.sqrt(np.maximum(0.0, 2.0 * np.asarray(u) - np.asarray(u) ** 2))

def leaf_point(side, state, u, z):
    hinge = np.array([-1.0 if side == 'left' else 1.0, 0.0, 0.0])
    local = np.array([u if side == 'left' else -u, 0.0, z])
    if state == 'open':
        theta = math.radians(-90.0 if side == 'left' else 90.0)
        rotation = np.array([[math.cos(theta), -math.sin(theta), 0.0],
                             [math.sin(theta), math.cos(theta), 0.0], [0.0, 0.0, 1.0]])
        local = rotation @ local
    return hinge + local

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

def fixed_frame():
    frame = PARAMETERS['fixed_frame']
    color = PARAMETERS['diagram_conventions']['frame_color']
    ri, ro = frame['inner_radius'], frame['outer_radius']
    yf, yb = frame['y_front'], frame['y_back']
    faces = mesh_box((-ro,yf,0),(-ri,yb,2),color) + mesh_box((ri,yf,0),(ro,yb,2),color)
    for a0, a1 in zip(np.linspace(0,math.pi,65)[:-1],np.linspace(0,math.pi,65)[1:]):
        points = np.array([[radius*math.cos(angle), y, 2+radius*math.sin(angle)]
                           for y in [yf,yb] for radius,angle in [(ri,a0),(ro,a0),(ro,a1),(ri,a1)]])
        faces += [(points[index],color) for index in [[0,3,2,1],[4,5,6,7],[0,1,5,4],
                                                    [1,2,6,5],[2,3,7,6],[3,0,4,7]]]
    # Short fixed hinge brackets connect the exact hinge axes to the gray frame.
    for x in [-1.0,1.0]:
        for z in [0.38,1.63]:
            faces += tube([x,0,z],[math.copysign(1.145,x),0.07,z],0.028,'#737f8a')
        faces += tube([x,0,0.18],[x,0,1.82],0.031,'#606d79')
    return faces

def leaf_faces(side, state):
    convention = PARAMETERS['diagram_conventions']
    color = convention['left_color' if side == 'left' else 'right_color']
    point = lambda u,z: leaf_point(side,state,float(u),float(z))
    faces = []
    for u in [0.0,1.0]:
        faces += tube(point(u,0),point(u,height(u)),convention['leaf_frame_radius'],color)
    faces += tube(point(0,0),point(1,0),convention['leaf_frame_radius'],color)
    for u0,u1 in zip(np.linspace(0,1,65)[:-1],np.linspace(0,1,65)[1:]):
        faces += tube(point(u0,height(u0)),point(u1,height(u1)),convention['leaf_frame_radius'],color)
    for u in convention['interior_bar_u']:
        faces += tube(point(u,0.035),point(u,height(u)-0.035),convention['interior_bar_radius'],color)
    for z in convention['crossbar_z']:
        faces += tube(point(0.025,z),point(0.975,z),0.018,color)
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

def draw_panel(ax, state, eye, title, subtitle):
    basis = camera(eye)
    ax.set_aspect('equal')
    ax.set_xlim(-2.1,2.1)
    ax.set_ylim(-2.05,2.05)
    ax.axis('off')
    ground = np.array([[-1.55,-1.5,0],[1.55,-1.5,0],[1.55,0.5,0],[-1.55,0.5,0]])
    ax.add_collection(PolyCollection([project(ground,basis)],facecolors=['#e9eef2'],edgecolors=['#ccd5de'],linewidths=0.7,zorder=0))
    for x in np.arange(-1.5,1.51,0.5):
        p = project([[x,-1.5,0],[x,0.5,0]],basis)
        ax.plot(p[:,0],p[:,1],color='#d7dfe6',lw=0.55,zorder=1)
    for y in np.arange(-1.5,0.51,0.5):
        p = project([[-1.5,y,0],[1.5,y,0]],basis)
        ax.plot(p[:,0],p[:,1],color='#d7dfe6',lw=0.55,zorder=1)
    wall = project([[-1.5,0,0.006],[1.5,0,0.006]],basis)
    ax.plot(wall[:,0],wall[:,1],color='#727f8d',lw=1.0,ls=(0,(3,3)),zorder=2)
    # A fixed direction marker is visible on the ground in all three views.
    marker = project([[0,-0.12,0.012],[0,-1.3,0.012]],basis)
    ax.add_patch(FancyArrowPatch(marker[0],marker[1],arrowstyle='-|>',mutation_scale=12,
                                color='#586c7e',linewidth=1.4,zorder=2))
    if state == 'open':
        for side in ['left','right']:
            x = -1 if side == 'left' else 1
            angles = np.linspace(0,-math.pi/2,30) if side == 'left' else np.linspace(math.pi,3*math.pi/2,30)
            arc = np.column_stack((x+0.38*np.cos(angles),0.38*np.sin(angles),np.full_like(angles,0.025)))
            p = project(arc,basis)
            color = PARAMETERS['diagram_conventions']['left_color' if side=='left' else 'right_color']
            ax.plot(p[:,0],p[:,1],color=color,lw=1.4,ls=(0,(3,2)),zorder=2)
            ax.add_patch(FancyArrowPatch(p[-3],p[-1],arrowstyle='-|>',mutation_scale=9,color=color,linewidth=1.2,zorder=2))
    faces = fixed_frame()+leaf_faces('left',state)+leaf_faces('right',state)
    draw_faces(ax,faces,basis)
    ax.text(0.5,1.035,title,transform=ax.transAxes,ha='center',va='bottom',fontsize=14,fontweight='bold',color='#1d2a36')
    ax.text(0.5,0.998,subtitle,transform=ax.transAxes,ha='center',va='top',fontsize=9.5,color='#516272')
    if state == 'closed':
        note='Continuous arch · center seam at x=0'
    else:
        note='Exactly 2 unchanged leaves · each swings 90°'
    ax.text(0.5,0.01,note,transform=ax.transAxes,ha='center',va='bottom',fontsize=10.5,color='#324758')
    return {'state':state,'camera_position':eye,'orthographic_basis':{'forward':basis[2].tolist(),'right':basis[3].tolist(),'up':basis[4].tolist()},'rendered_polygon_faces':len(faces)}

dump(ROOT/'parameters.json',PARAMETERS)
u = np.linspace(0,1,501)
left_closed = np.array([leaf_point('left','closed',t,height(t)) for t in u])
right_closed = np.array([leaf_point('right','closed',t,height(t)) for t in u])
left_open = np.array([leaf_point('left','open',t,height(t)) for t in u])
right_open = np.array([leaf_point('right','open',t,height(t)) for t in u])
checks = {
    'exactly_two_defined_leaves': PARAMETERS['leaf_count']==2,
    'closed_top_matches_continuous_arch': bool(np.allclose(left_closed[:,2],2+np.sqrt(1-left_closed[:,0]**2)) and np.allclose(right_closed[:,2],2+np.sqrt(1-right_closed[:,0]**2))),
    'closed_free_edges_meet_at_center_x0_z3': bool(np.allclose(left_closed[-1],[0,0,3]) and np.allclose(right_closed[-1],[0,0,3])),
    'hinge_top_height_remains_z2': bool(np.allclose(left_open[0],[-1,0,2]) and np.allclose(right_open[0],[1,0,2])),
    'left_open_plane_is_x_minus1': bool(np.allclose(left_open[:,0],-1)),
    'right_open_plane_is_x_plus1': bool(np.allclose(right_open[:,0],1)),
    'both_open_leaves_extend_to_y_minus1': bool(np.allclose(left_open[:,1],-u) and np.allclose(right_open[:,1],-u)),
    'both_open_curves_rise_from_hinge_to_free_edge': bool(np.all(np.diff(left_open[:,2])>=0) and np.all(np.diff(right_open[:,2])>=0)),
    'all_top_heights_unchanged_by_rotation': bool(np.allclose(left_closed[:,2],left_open[:,2]) and np.allclose(right_closed[:,2],right_open[:,2])),
    'both_ground_edges_remain_z0': all(abs(leaf_point(side,'open',float(t),0)[2])<1e-12 for side in ['left','right'] for t in u),
    'cameras_opposed_horizontally_and_both_above_ground': PARAMETERS['camera_positions']['rear']==[-6.0,8.0,5.0],
    'fixed_frame_function_used_unchanged_in_all_panels': True}
assert all(checks.values())
dump(ROOT/'geometry-checks.json',{'status':'PASS_BUILDER_GEOMETRY_CHECKS','independent':False,
                                'sampled_top_points_per_leaf':len(u),'mandatory_checks':checks,
                                'visual_approval':'Pending root and separate critic inspection of the actual PNG.'})
matplotlib.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'havenline-fortress-double-gate-r2'})
fig = plt.figure(figsize=(18.0,7.5),facecolor='#f7f9fb')
fig.text(0.5,0.955,'FORTRESS DOUBLE GATE · EXACT GEOMETRY GUIDE',ha='center',va='top',fontsize=21,fontweight='bold',color='#162734')
fig.text(0.5,0.904,'AUTHOR-CREATED DIAGRAM  ·  fixed front wall y=0  ·  ground z=0  ·  outward swing toward y<0',ha='center',va='top',fontsize=11.5,color='#41596b')
fig.text(0.29,0.855,'LEFT LEAF · hinge x=-1',ha='center',va='top',fontsize=11,fontweight='bold',color='#257d91')
fig.text(0.51,0.855,'RIGHT LEAF · hinge x=+1',ha='center',va='top',fontsize=11,fontweight='bold',color='#b17222')
fig.text(0.75,0.855,'GRAY FRAME · stays fixed',ha='center',va='top',fontsize=11,fontweight='bold',color='#6a7682')
panels=[]
for x,state,eye,title,subtitle in [
    (0.025,'closed',[6.0,-8.0,5.0],'CLOSED · FRONT OBLIQUE','Camera (6, -8, 5)'),
    (0.350,'open',[6.0,-8.0,5.0],'OPEN · FRONT OBLIQUE','Same camera (6, -8, 5)'),
    (0.675,'open',[-6.0,8.0,5.0],'OPEN · REAR OBLIQUE','Opposing camera (-6, 8, 5)')]:
    ax=fig.add_axes([x,0.18,0.30,0.61])
    panels.append(draw_panel(ax,state,eye,title,subtitle))
fig.text(0.5,0.126,'Same half-arch shape in every state: hinge top z=2 → free edge z=3.  No replacement grilles, lifted leaves, or shape changes.',ha='center',va='center',fontsize=11.4,color='#1f3b4d')
fig.text(0.5,0.079,'Closed: z = 2 + √(1 − x²)   |   Open left: x=-1, y∈[-1,0]   |   Open right: x=+1, y∈[-1,0]   |   Both free edges point outward.',ha='center',va='center',fontsize=11.2,color='#344e60')
fig.text(0.5,0.035,'Geometry guide only. Colors, bars and frame detail are diagram conventions — not recovered source evidence or final Havenline art.',ha='center',va='center',fontsize=10,color='#657783')
png = ROOT/'fortress-double-gate-r2.png'
svg = ROOT/'fortress-double-gate-r2.svg'
assert not png.exists() and not svg.exists(), 'Keep authored revisions intact; create a new revision folder for a changed diagram.'
fig.savefig(png,dpi=160,facecolor=fig.get_facecolor(),metadata={'Title':'Havenline fortress double gate — author-created exact geometry guide'})
fig.savefig(svg,facecolor=fig.get_facecolor(),metadata={'Date':None,'Title':'Havenline fortress double gate — author-created exact geometry guide'})
plt.close(fig)
provenance={'schema_version':1,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
            'author':'/root/missing_archive','authoring_request':'Root requested a new exact geometric guide for two unchanged half-arch leaves rotating outward 90 degrees about x=±1 hinges.',
            'origin':'AUTHOR_CREATED_MATHEMATICAL_GUIDE','source_evidence':False,
            'image_operation':'New vector/geometry rendering only; no existing bitmap loaded or modified.',
            'code':facts(Path(__file__)),'parameters':facts(ROOT/'parameters.json'),
            'builder_geometry_checks':facts(ROOT/'geometry-checks.json'),
            'png':facts(png),'svg':facts(svg),'panels':panels,
            'imagegen_input_approval':'Pending actual root and independent critic image inspection; not yet an authorized generation input or final art.'}
dump(ROOT/'provenance.json',provenance)
print(json.dumps({'png':provenance['png'],'svg':provenance['svg'],
                  'geometry_checks':'PASS_BUILDER_GEOMETRY_CHECKS','source_evidence':False,
                  'existing_bitmaps_modified':False,'independent_visual_review':'PENDING'},indent=2))
