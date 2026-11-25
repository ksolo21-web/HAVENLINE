from PIL import Image
import numpy as np
for name in ('01-shaft-side','02-perpendicular'):
 im=Image.open(name+'.png').convert('RGB')
 pix=np.array(im)
 bg=pix[-1,-1].astype(int)
 fg=np.max(np.abs(pix.astype(int)-bg),axis=2)>15
 white=np.all(pix>=250,axis=2)
 red=(pix[:,:,0]>115)&(pix[:,:,0]>pix[:,:,1].astype(int)+50)&(pix[:,:,0]>pix[:,:,2].astype(int)+30)
 print(name, 'dimensions', im.size, 'near-white foreground',f'{(white&fg).sum()/fg.sum():.2%}','detectably red foreground pixels',int((red&fg).sum()))
 im.save(name+'.jpg',quality=88,subsampling=0,optimize=True)
