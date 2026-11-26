from pathlib import Path
exec(Path('/tmp/winter-independent/gallery.py').read_text().split("for clip in ([None]")[0])
D=Image.new('RGB',(720,3*226),'#263036');draw=ImageDraw.Draw(D)
for i,(name,idx,ids,eye) in enumerate([('Walk',58,[5521,13978],(13,11,0)),('Run',46,[13978,14714],(13,11,0)),('Run',2,[3944,5157],(-9,11,-9))]):
 ts,ms=pose(next(x for x in g['animations'] if x['name']==name));x=get_pose(ms[idx]);v=x[ids];t=v.mean(0)
 for j,(m,ctr,hh) in enumerate([(P,P[ids].mean(0),.25),(x,t,.25),(x,t,.25)]):
  im=render(m,eye,ctr,hh,(235,204))
  if j==2:
   e=unit(np.asarray(eye));uu=unit(np.cross([0,1,0],e));vv=unit(np.cross(e,uu))
   pts=[(117.5+(a-ctr).dot(uu)*204/hh,102-(a-ctr).dot(vv)*204/hh) for a in v]
   ImageDraw.Draw(im).line(pts,fill='#ff563a',width=2)
  D.paste(im,(240*j,226*i+19))
 draw.text((4,226*i+3),f'{name} {idx}/120 s  |  rest surface, moving surface, measured edge')
D.save(out/'Residual-detail.jpg',quality=90)
