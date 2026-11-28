#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <set>
#include <vector>
struct Vec {
 float x[3]{};
 float operator[](int k) const {return x[k];}
 Vec operator-(Vec b) const {return {{x[0]-b[0],x[1]-b[1],x[2]-b[2]}};}
};
float dot(Vec a,Vec b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
Vec cross(Vec a,Vec b){return {{a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]}};}
struct Box {
 Vec lo{{INFINITY,INFINITY,INFINITY}},hi{{-INFINITY,-INFINITY,-INFINITY}};
 void add(Vec v){for(int a=0;a<3;++a){lo.x[a]=std::min(lo[a],v[a]);hi.x[a]=std::max(hi[a],v[a]);}}
 void add(Box b){add(b.lo);add(b.hi);}
 bool overlaps(Box b) const {for(int a=0;a<3;++a)if(lo[a]>=b.hi[a]||hi[a]<=b.lo[a])return false;return true;}
};
using Face=std::array<int,3>;
using Tri=std::array<Vec,3>;
using Key=std::uint64_t;
bool hit(Tri a,Tri b) {
 Vec b1=b[1]-b[0],b2=b[2]-b[0];
 for(int i=0;i<3;++i) {
  Vec line=a[(i+1)%3]-a[i],h=cross(line,b2);
  const float det=dot(b1,h);
  if(std::abs(det)<1e-12f)continue;
  Vec delta=a[i]-b[0];
  const float u=dot(delta,h)/det;
  if(u<=1e-5f || u>=1.f-1e-5f)continue;
  const Vec vvec=cross(delta,b1);
  const float v=dot(line,vvec)/det;
  if(v<=1e-5f || u+v>=1.f-1e-5f)continue;
  const float p=dot(b2,vvec)/det;
  if(p>1e-5f&&p<1.f-1e-5f)return true;
 }
 return false;
}
struct Node {int begin,end,left=-1,right=-1;};
struct Audit {
 std::vector<Face> faces;
 std::vector<int> weld,order;
 std::vector<Node> nodes;
 std::vector<Box> boxes,tri_boxes;
 std::vector<Tri> triangles;
 void set_mesh(const std::vector<Vec>& points){
  for(size_t i=0;i<faces.size();++i){
   tri_boxes[i]=Box{};
   for(int j=0;j<3;++j){
    triangles[i][j]=points[faces[i][j]];
    tri_boxes[i].add(triangles[i][j]);
   }
  }
 }
 int split(int first,int last){
  int index=nodes.size();nodes.push_back({first,last});
  if(last-first<=8)return index;
  Box box{};
  for(int i=first;i<last;++i)box.add(tri_boxes[order[i]]);
  int axis=0;
  for(int a=1;a<3;++a)if(box.hi[a]-box.lo[a]>box.hi[axis]-box.lo[axis])axis=a;
  int middle=(first+last)/2;
  std::nth_element(order.begin()+first,order.begin()+middle,order.begin()+last,[&](int a,int b){
   return tri_boxes[a].lo[axis]+tri_boxes[a].hi[axis]<tri_boxes[b].lo[axis]+tri_boxes[b].hi[axis];
  });
  const int left=split(first,middle),right=split(middle,last);
  nodes[index].left=left; nodes[index].right=right;
  return index;
 }
 Box refit(int n) {
  const Node p=nodes[n]; Box box;
  if(p.left < 0)for(int i=p.begin;i<p.end;++i)box.add(tri_boxes[order[i]]);
  else{box.add(refit(p.left));box.add(refit(p.right));}
  return boxes[n]=box;
 }
 void compare(int ia,int ib,std::vector<Key>& results) const {
  if(!boxes[ia].overlaps(boxes[ib]))return;
  Node a=nodes[ia],b=nodes[ib];
  if(a.left<0&&b.left<0){
   for(int i=a.begin;i<a.end;++i)for(int j=std::max(b.begin,ia==ib?i+1:b.begin);j<b.end;++j){
    int fi=order[i],fj=order[j];
    if(!tri_boxes[fi].overlaps(tri_boxes[fj]))continue;
    bool connects=false;
    for(int u:faces[fi])for(int v:faces[fj])if(weld[u]==weld[v])connects=true;
    if(!connects&&(hit(triangles[fi],triangles[fj])||hit(triangles[fj],triangles[fi])))
     results.push_back((static_cast<Key>(std::min(fi,fj))<<32)|std::max(fi,fj));
   }
  }else if(ia==ib){
   compare(a.left,a.left,results);compare(a.left,a.right,results);compare(a.right,a.right,results);
  }else if(a.left>=0&&(b.left<0||a.end-a.begin>=b.end-b.begin)){
   compare(a.left,ib,results);compare(a.right,ib,results);
  }else{
   compare(ia,b.left,results);compare(ia,b.right,results);
  }
 }
};
template <typename T> std::vector<T> load(std::ifstream& handle,int count){
 std::vector<T> value(count); handle.read(reinterpret_cast<char*>(value.data()),count*sizeof(T));return value;
}
int main(int argc,char** argv) {
 if(argc!=8)return 2;
 const int verts=std::stoi(argv[3]),skin=std::stoi(argv[4]),joints=std::stoi(argv[5]),faces=std::stoi(argv[6]),frames=std::stoi(argv[7]);
 std::ifstream mesh(argv[1],std::ios::binary),poses(argv[2],std::ios::binary);
 auto rest=load<Vec>(mesh,verts);auto idx=load<int>(mesh,verts*skin);auto weights=load<float>(mesh,verts*skin);
 Audit audit; audit.faces=load<Face>(mesh,faces);
 audit.weld=load<int>(mesh,verts); audit.order.resize(faces); std::iota(audit.order.begin(),audit.order.end(),0);
 audit.triangles.resize(faces);audit.tri_boxes.resize(faces);
 std::set<Key> baseline;
 auto points=std::vector<Vec>(verts);
 for(int frame=0;frame<frames;++frame){
  auto mats=load<float>(poses,joints*12);
  for(int i=0;i<verts;++i){
   Vec p{};
   for(int j=0;j<skin;++j){
    int k=i*skin+j;const float* m=mats.data()+idx[k]*12;const float weight=weights[k];
    for(int a=0;a<3;++a)p.x[a]+=weight*(rest[i][0]*m[a]+rest[i][1]*m[3+a]+rest[i][2]*m[6+a]+m[9+a]);
   }
   points[i]=p;
  }
  audit.set_mesh(points);
  if(frame==0){audit.split(0,faces);audit.boxes.resize(audit.nodes.size());}
  audit.refit(0);
  std::vector<Key> hits; audit.compare(0,0,hits);
  if(frame==0)baseline.insert(hits.begin(),hits.end());
  std::cout<<frame<<" "<<hits.size();
  for(Key key:hits)if(!baseline.count(key))std::cout<<" "<<(key>>32)<<":"<<(key&0xffffffff);
  std::cout<<"\n";
 }
}
