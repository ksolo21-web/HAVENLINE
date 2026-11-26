"""Synthetic decision kernel for future shadow-only A/A + ON/OFF test. No engine."""
import numpy as np
TAU=1 # pinned original checker maximum allowed outside component delta
def decide(A1,A2,ON,OFF,direct,shadow):
    """Inputs separately authenticated; masks from untouched parent checker."""
    assert A1.shape==A2.shape==ON.shape==OFF.shape==(*direct.shape,4)
    assert direct.dtype==shadow.dtype==np.dtype(bool) and np.any(direct) and not np.any(direct&shadow)
    assert (direct|shadow).sum()<.02*direct.size
    U=~(direct|shadow)
    a,b,on,off=[x.astype(np.int16) for x in (A1,A2,ON,OFF)]
    same=lambda d:np.max(np.abs(d),axis=2)<=TAU
    cmp=lambda new,base:~same(new-base)
    if not same(a-b).all():return 'HOLD_NONREPEATABLE_NO_CROWN'
    # Correction cannot pass by hiding, reducing, or moving the already-tested asset.
    if any((cmp(obj,ctrl)&direct).sum()<100 for obj in (on,off) for ctrl in (a,b)):
      return 'HOLD_MISSING_DIRECT_CROWN'
    ONoutside=(cmp(on,a)|cmp(on,b))&U
    if not ONoutside.any():return 'HOLD_ORIGINAL_OFF_ROI_SIGNATURE_NOT_REPRODUCED'
    if not np.array_equal(cmp(on,a)&U,cmp(on,b)&U):return 'HOLD_ON_OFF_ROI_SIGNATURE_DIFFERS_BETWEEN_CONTROLS'
    # Darkening applies outside the unchanged direct appearance, not texture edits.
    ONrgb=on[:,:,:3]
    for ctrl in (a,b):
      d=ONrgb-ctrl[:,:,:3]
      if np.any(d[ONoutside]>TAU) or not np.all(np.any(d[ONoutside]<-TAU,axis=1)):
       return 'HOLD_ON_OUTSIDE_SIGNATURE_NOT_DARKENING'
    if any(np.any(cmp(off,ctrl)&U) for ctrl in (a,b)):
      return 'HOLD_OFF_OUTSIDE_ORIGINAL_REGION_STILL_CHANGES'
    if not np.all(np.any((off[:,:,:3]-on[:,:,:3])[ONoutside]>TAU,axis=1)):
      return 'HOLD_NOT_REVERSED_BY_CAST_TOGGLE'
    return 'OBSERVED_CAST_CAUSAL_AT_THIS_TICK_ONLY'
def controls():
 D=np.zeros((64,128),bool);D[20:25,35:60]=1
 S=np.zeros_like(D);S[27:31,44:51]=1
 A=np.full((*D.shape,4),255,'u1');A[:,:,:3]=145
 ON=A.copy();ON[D,:3]=90;ON[48,80,:3]=134
 OFF=A.copy();OFF[D,:3]=97
 q=lambda *x: decide(*x,D,S)
 assert q(A,A,ON,OFF)=='OBSERVED_CAST_CAUSAL_AT_THIS_TICK_ONLY'
 q2=A.copy();q2[48,80,:3]=137
 assert q(A,q2,ON,OFF)=='HOLD_NONREPEATABLE_NO_CROWN'
 assert q(A,A,ON,A)=='HOLD_MISSING_DIRECT_CROWN'
 assert q(A,A,OFF,OFF)=='HOLD_ORIGINAL_OFF_ROI_SIGNATURE_NOT_REPRODUCED'
 bright=ON.copy();bright[48,80,:3]=166
 assert q(A,A,bright,OFF)=='HOLD_ON_OUTSIDE_SIGNATURE_NOT_DARKENING'
 assert q(A,A,ON,ON)=='HOLD_OFF_OUTSIDE_ORIGINAL_REGION_STILL_CHANGES'
if __name__=='__main__':
 controls();print('one synthetic causal pattern, five distinct falsifier patterns; no native data')
