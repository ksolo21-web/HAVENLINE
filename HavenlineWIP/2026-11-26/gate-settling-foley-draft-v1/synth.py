"""Original procedural dry gate foley. PCM mono; no samples or dependencies."""
from math import sin,cos,exp,pi
from pathlib import Path
import struct,sys,wave
RATE=48000
N=15360
SEED=0xd51793b7

def samples():
 rng=SEED
 body=low=high=last=0.
 for i in range(N):
  t=i/RATE
  rng=(1664525*rng+1013904223)&0xffffffff
  w=(rng>>8)/8388608.-1.
  body+=.069*(w-body)
  low+=.18*(w-low)
  high+=.53*(w-high)
  rough=high-low
  delta=high-last
  last=high
  v=0.
  # Short muted metal catch, not any sustained bell or ring.
  u=t-.012
  if u>=0:
   initial=1-exp(-u/.00048)
   v+=initial*(.37*delta*exp(-u/.0045)+sum(a*sin(2*pi*f*u+.12)*exp(-u/d) for f,a,d in [(2090,.093,.007),(3113,.067,.0045),(4577,.036,.0032)]))
  # Timber body follows the latch by 11 ms, not a second isolated loud impact.
  u=t-.023
  if u>=0:
   bend=1-exp(-u/.0023)
   v+=bend*((.24*body+.12*rough)*exp(-u/.024)+sum(a*sin(2*pi*f*u)*exp(-u/d) for f,a,d in [(113,.143,.023),(181,.101,.033),(276,.073,.028),(435,.037,.018),(726,.019,.016)]))
  # Soft short dry wood seating friction, no added reverb or footsteps.
  u=t-.041
  if 0<=u<.095:
   v+=.135*rough*(1-exp(-u/.007))*exp(-u/.027)*(.68+.32*cos(2*pi*29*u))
  # Unobtrusive dry tail, hard digital silence only after fade reaches zero.
  if t>=.224:
   v*=.5*(1+cos(pi*min(1.,(t-.224)/.056)))
  yield max(-32767,min(32767,round(v*32767)))

def main(path):
 s=tuple(samples())
 with wave.open(str(path),'wb') as f:
  f.setparams((1,2,RATE,N,'NONE','not compressed'))
  f.writeframes(struct.pack('<%dh'%N,*s))
if __name__=='__main__':
 assert len(sys.argv)==2
 main(Path(sys.argv[1]))
