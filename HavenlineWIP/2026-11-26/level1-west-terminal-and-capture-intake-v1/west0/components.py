from input_scope import *
def components(T):
 # Component ownership follows welded shared undirected edges, not isolated coincident vertices.
 _, ids=np.unique(np.around(T.reshape(-1,3),9),axis=0,return_inverse=True)
 ids=ids.reshape(-1,3)
 def links(f):return [tuple(sorted((a,b))) for a,b in zip(f,np.roll(f,-1))]
 edge_to={}
 for i,f in enumerate(ids):
  for edge in links(f):edge_to.setdefault(edge,[]).append(i)
 remain=set(range(len(T))); out=[]
 while remain:
  i=remain.pop(); group=[i]
  for j in group:
   for edge in links(ids[j]):
    for k in edge_to[edge]:
     if k in remain:group.append(k);remain.remove(k)
  out.append(sorted(group))
 return out
if __name__=='__main__':
 print(json.dumps({m:[audit(U[M==m][ids]) for ids in components(U[M==m])] for m in sorted(set(M))},indent=2))
