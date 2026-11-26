from pathlib import Path
import sys,numpy as np,json
script=Path(sys.argv[1]); api={}
exec(compile(script.read_text().split('before,after=map')[0],str(script),'exec'),api)
read,witnesses=api['read'],api['witnesses']
old,new=map(lambda s:read(Path(s)),sys.argv[2:4])
out=[]
for k in new:
 if k!='draped_snow':assert np.array_equal(old[k],new[k])
snow=lambda c,i:c['draped_snow'][i*192:(i+1)*192]
wood=lambda c,i:c['amber_timber'][i*180:(i+1)*180]
p=lambda v: [len(v),round(max((x[2] for x in v),default=0.)*1000,3)]
for i in range(10):
 a,b=snow(old,i),snow(new,i)
 assert np.array_equal(a.min((0,1))[[0,2]],b.min((0,1))[[0,2]]) and np.array_equal(a.max((0,1)),b.max((0,1)))
 w=wood(new,i)
 d={'post':i,'old_same_snow_wood':[a.shape[0],*p(witnesses(a,w))],'new_same_snow_wood':p(witnesses(b,w))}
 # From source overlaps, strict pairs only (line length is not penetration depth).
 for k,c in [('old',old),('new',new)]:
  s=snow(c,i)
  d[k+'_same_rope']=sum(len(witnesses(s,c[m][i*256:(i+1)*256])) for m in ('cream_hemp','warm_hemp'))
  d[k+'_neighbor_caps']=sum(len(witnesses(s,snow(c,j))) for j in (i-1,i+1) if 0<=j<10)
  d[k+'_neighbor_wood']=sum(len(witnesses(s,wood(c,j))) for j in (i-1,i+1) if 0<=j<10)
 d['self_pairs']=len(witnesses(b,b,True))
 rows=[b[:,:,1].min(),b[:,:,1].max()];d['new_Snow_Y_bounds']=rows
 out.append(d)
print(json.dumps(out,indent=2))
