#include <float.h>
#include <math.h>
void rast(const double *p,const int *ix,int n,double *z,int W,int H,int x0,int y0,int mode){
 for(int i=0;i<n;i++){
 const double *a=p+3*ix[3*i],*b=p+3*ix[3*i+1],*c=p+3*ix[3*i+2];
 double e=b[0]-a[0],f=b[1]-a[1],g=c[0]-a[0],h=c[1]-a[1],den=e*h-f*g;
 if(fabs(den)<1e-12 || (mode==1&&den<0) ||(mode==-1&&den>0))continue;
 int l=fmax(0,floor(fmin(a[0],fmin(b[0],c[0]))-.5)-x0), r=fmin(W-1,ceil(fmax(a[0],fmax(b[0],c[0]))-.5)-x0);
 int t=fmax(0,floor(fmin(a[1],fmin(b[1],c[1]))-.5)-y0),k=fmin(H-1,ceil(fmax(a[1],fmax(b[1],c[1]))-.5)-y0);
 for(int y=t;y<=k;y++) for(int x=l;x<=r;x++){
 double dx=x+x0+.5-a[0],dy=y+y0+.5-a[1],u=(dx*h-dy*g)/den,v=(e*dy-f*dx)/den;
 if(u>=-1e-9&&v>=-1e-9&&u+v<=1.000000001){
 double d=a[2]+u*(b[2]-a[2])+v*(c[2]-a[2]); if(d>z[y*W+x])z[y*W+x]=d;
 }
 }
 }
}
