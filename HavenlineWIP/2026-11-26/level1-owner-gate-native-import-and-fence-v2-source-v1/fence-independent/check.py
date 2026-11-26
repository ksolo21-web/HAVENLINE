from pathlib import Path
import sys,json,numpy as np
api={}
p=Path(sys.argv[1]); exec(p.read_text().split('before,after=')[0],api)
g=api['read'](Path(sys.argv[2])); fit=api['witnesses']
c=np.concatenate(tuple(g.values())).reshape(-1,3)
rw,gold=[np.split(g[m],2) for m in ('ivory_hemp_cream','ivory_hemp_warm')]
rails=np.split(g['front_rounded_rails'],2)
o=[]
for i,(W,G,R) in enumerate(zip(rw,gold,rails)):
 def ring(a):return a.reshape(180,12,3,3)[:,::2,0,:].mean(1)
 a,b=ring(W),ring(G); z=slice(90,171)
 def rr(x):return x[90*12:170*12]
 pairs=fit(W,G)
 o.append({'band':i,'rail_z_min_max': [float(R[:,:,2].min()),float(R[:,:,2].max())], 'front_contacts':len(pairs),'positive_z_pairs':int(sum(W[j,:,2].min()>0 and G[k,:,2].min()>0 for j,k,_ in pairs)),'rear_centers_vertical_max_separation_m':float(np.max(abs(a[z,1]-b[z,1]))),'rear_centers_depth_max_separation_m':float(np.max(abs(a[z,2]-b[z,2]))),'rear_rope_crossings':len(fit(rr(W),rr(G))), 'minimum_front_x_symmetrical_strand_center_slope_box_m':float(min(abs(a[j+2,1]-b[j+2,1]) for j in range(5,80,10)))})
print(json.dumps({'world_depth_m':float(np.ptp(c[:,2])*1.95),'band':o},indent=2))
