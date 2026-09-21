#!/usr/bin/env python3
"""One source-bound T10 C1/C2 visual slice. Aggregation happens separately."""
from __future__ import annotations
import argparse,base64,hashlib,io,json,math,os,pathlib,subprocess,time,urllib.request
from PIL import Image,ImageDraw,ImageFont
DIMS={"C1":["reference_fidelity","visual_language","cross_view_consistency"],"C2":["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"]}
STATES=["ready","blocked","preview","committing","complete","replay"];ANGLES=["front","side","three-quarter","overhead","gameplay","detail"]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def resolve(path,repo,evidence):
 p=pathlib.PurePosixPath(path)
 return pathlib.Path(evidence).joinpath(*p.parts[1:]) if p.parts and p.parts[0]=="critic-input" else pathlib.Path(repo)/path
def fit(im,size):x=im.copy();x.thumbnail(size,Image.Resampling.LANCZOS);return x
def board(refs,candidates,out,title):
 rows=max(1,math.ceil(len(candidates)/3));W,H=1800,275+rows*375;b=Image.new("RGB",(W,H),(18,25,33));d=ImageDraw.Draw(b);font=ImageFont.load_default(size=24);small=ImageFont.load_default(size=18)
 d.text((18,10),title,fill="white",font=font);x=18
 for i,p in enumerate(refs):
  im=fit(Image.open(p).convert("RGB"),(235,132));b.paste(im,(x+(235-im.width)//2,50));d.text((x,186),"REF "+str(i+1),fill="white",font=small);x+=250
 d.text((18,215),"T10: ring/circle = perimeter; cuboid = separate preview/accepted volume; OUTER IMAGE EDGE = viewport border",fill="white",font=small)
 for i,p in enumerate(candidates):
  im=fit(Image.open(p).convert("RGB"),(560,315));col=i%3;row=i//3;x0=col*600+15;y0=255+row*375;b.paste(im,(x0+(570-im.width)//2,y0+35));d.text((x0,y0),pathlib.Path(p).stem,fill="white",font=small)
 b.save(out,quality=95)
def motion(video,outdir):
 outdir.mkdir(parents=True,exist_ok=True);subprocess.run(["ffmpeg","-v","error","-i",str(video),"-vf","fps=2","-frames:v","12",str(outdir/"frame-%02d.png")],check=True,timeout=180)
 frames=sorted(outdir.glob("frame-*.png"));assert len(frames)>=12
 return frames[:12]
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--critic",choices=["C1","C2"],required=True);ap.add_argument("--slice",type=int,choices=range(4),required=True);ap.add_argument("--candidate",required=True);ap.add_argument("--repo",required=True);ap.add_argument("--evidence",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 repo=pathlib.Path(a.repo);ev=pathlib.Path(a.evidence);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()!=a.candidate:raise ValueError("candidate mismatch")
 mp=ev/(a.critic+"-manifest.json");m=json.loads(mp.read_text())
 if m.get("candidate_commit")!=a.candidate or m.get("critic_id")!=a.critic:raise ValueError("manifest identity mismatch")
 refs=[resolve(i["path"],repo,ev) for g in m["groups"] if g["id"]=="references" for i in g["items"]];life=[resolve(i["path"],repo,ev) for g in m["groups"] if g["id"]=="lifecycle" for i in g["items"]]
 if len(refs)!=7 or len(life)!=36:raise ValueError("visual domain incomplete")
 for g in m["groups"]:
  for i in g["items"]:
   p=resolve(i["path"],repo,ev)
   if not p.is_file() or sha(p)!=i["sha256"]:raise ValueError("changed evidence "+i["path"])
 video=resolve(m["video"]["path"],repo,ev)
 if sha(video)!=m["video"]["sha256"]:raise ValueError("video hash mismatch")
 device=ev/"device-layout-evidence.json"
 if sha(device)!=m["device_manifest_sha256"]:raise ValueError("device hash mismatch")
 native=json.loads((ev/"native4k/manifest.json").read_text())
 if native.get("candidate")!=a.candidate or native.get("states")!=STATES or native.get("angles")!=ANGLES or native.get("record_count")!=36:raise ValueError("native4k domain mismatch")
 mapping={}
 for p in life:
  hits=[(s,x) for s in STATES for x in ANGLES if p.stem==s+"-"+x]
  if len(hits)!=1:raise ValueError("filename mismatch "+p.stem)
  mapping[hits[0]]=p
 boardps=[]
 if a.slice<3:
  pair=STATES[a.slice*2:a.slice*2+2]
  for s in pair:
   bp=out/("board-"+s+".jpg");subset=[mapping[(s,x)] for x in ANGLES];board(refs,subset,bp,"LOCKED REFERENCES + "+s.upper()+" — all six angles");boardps.append(bp)
  kind="static"
 else:
  frames=motion(video,out/"motion-frames")
  for batch,start in enumerate((0,6)):
   bp=out/("board-motion-"+str(batch)+".jpg");board(refs,frames[start:start+6],bp,"LOCKED REFERENCES + LIFECYCLE VIDEO — samples "+str(start+1)+"-"+str(start+6));boardps.append(bp)
  kind="motion"
 rt=json.loads((repo/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"];cache=pathlib.Path(os.path.expanduser(rt["cache_path"]));mf=json.loads((cache/"manifest.json").read_text());servers=list((cache/"runtime").rglob("llama-server"))
 if len(servers)!=1:raise ValueError("reviewer runtime missing")
 server=servers[0];env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","");log=(out/"runtime.log").open("w")
 proc=subprocess.Popen([str(server),"-m",str(cache/mf["model_file"]),"--mmproj",str(cache/mf["projector_file"]),"--host","127.0.0.1","--port","8080","-c","8192","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","1024","--image-max-tokens","2048"],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(180):
   if proc.poll() is not None:raise RuntimeError("review runtime exited")
   try:
    if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
   except Exception:time.sleep(2)
  else:raise RuntimeError("review runtime not ready")
  dims=DIMS[a.critic];props={d:{"type":"number","minimum":0,"maximum":10} for d in dims};schema={"type":"object","properties":{"observations":{"type":"array","items":{"type":"string","maxLength":180},"minItems":2,"maxItems":4},"defects":{"type":"array","items":{"type":"string","maxLength":180},"maxItems":5},"coverage_complete":{"type":"boolean"},"confidence":{"type":"string","enum":["low","medium","high"]},"scores":{"type":"object","properties":props,"required":dims,"additionalProperties":False}},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
  if a.critic=="C1":role="Judge reference fidelity, visual-language match and cross-view consistency. T10 intentionally uses TWO neutral primitives: circular/cylindrical perimeter StateRing and separate box-like PreviewVolume. They are not one foundation mesh and their silhouette difference is not inconsistency. Lifecycle state feedback intentionally changes color/material/form between READY, BLOCKED, PREVIEW, COMMITTING and COMPLETE/REPLAY; cross-view consistency compares the SAME state across angles, not different states across time. T11 owns authored camp content; do not penalize absent T11 art."
  else:role="Judge technical/visual integrity only. Circle=perimeter ring; cuboid=separate preview/accepted volume. The gray ground-plane/panel surface may meet the image edge and is not candidate geometry. Viewport border is only the OUTER IMAGE boundary. Perspective can change apparent screen-space centering; do not require identical centering across angles. Flag only actual ring/cuboid clipping, unintended intersection/contact, or seam defects."
  common="Exact candidate "+a.candidate+". Every candidate panel is source-bound. This slice is one required part of a four-slice review; aggregate uses minimum scores and union defects, never averages. A score <=9 must name a concrete actionable defect. Strict acceptance requires each score >9, zero defects, complete coverage, medium/high confidence."
  content=[];board_hashes=[]
  for boardp in boardps:
   im=Image.open(boardp).convert("RGB");im.thumbnail((1664,1664),Image.Resampling.LANCZOS);buf=io.BytesIO();im.save(buf,format="JPEG",quality=94);payload=buf.getvalue();board_hashes.append(sha(boardp));content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(payload).decode()}})
  content.append({"type":"text","text":common+" "+role+(" This motion slice is derived from the full hash-bound lifecycle video." if kind=="motion" else "")+" Return JSON only."})
  body={"model":"T10-final-visual","messages":[{"role":"user","content":content}],"max_tokens":650,"temperature":0.2,"top_p":0.9,"seed":20261000+(0 if a.critic=="C1" else 100)+a.slice,"repeat_penalty":1.1,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
  req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
  with urllib.request.urlopen(req,timeout=1200) as resp:raw=json.load(resp)
  (out/"raw-response.json").write_text(json.dumps(raw,indent=2));choice=raw["choices"][0]
  if choice.get("finish_reason")!="stop":raise ValueError("truncated review")
  row=json.loads(choice["message"]["content"]);scores=row.get("scores",{});errors=[]
  if set(scores)!=set(dims):errors.append("dimension mismatch")
  if row.get("defects"):errors.append("defects")
  if row.get("coverage_complete") is not True:errors.append("coverage")
  if row.get("confidence") not in ("medium","high"):errors.append("confidence")
  if any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9 for v in scores.values()):errors.append("score")
  combined_board_hash=hashlib.sha256("".join(board_hashes).encode()).hexdigest()
  result={"task_id":"T10","candidate":a.candidate,"critic_id":a.critic,"slice":a.slice,"kind":kind,"input_manifest_hash":sha(mp),"video_sha256":sha(video),"board_sha256":combined_board_hash,"board_sha256s":board_hashes,"provider":mf.get("publisher"),"model":mf.get("base_model"),"model_revision":mf.get("revision"),"review":row,"passed":not errors,"errors":errors,"non_voting":False}
  (out/"slice-result.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2));return 0 if not errors else 1
 finally:
  proc.terminate()
  try:proc.wait(timeout=10)
  except Exception:proc.kill()
  log.close()
if __name__=="__main__":raise SystemExit(main())
