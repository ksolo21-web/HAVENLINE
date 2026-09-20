#!/usr/bin/env python3
"""Fresh source-bound C1/C2 visual review for Havenline T10 final candidate."""
from __future__ import annotations
import argparse,base64,hashlib,io,json,math,os,pathlib,subprocess,time,urllib.request
from PIL import Image,ImageDraw,ImageFont

DIMS={
"C1":["reference_fidelity","visual_language","cross_view_consistency"],
"C2":["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"],
}
STATES=["ready","blocked","preview","committing","complete","replay"]
ANGLES=["front","side","three-quarter","overhead","gameplay","detail"]

def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def resolve(path,candidate,evidence):
 p=pathlib.PurePosixPath(path)
 if p.parts and p.parts[0]=="critic-input":return pathlib.Path(evidence).joinpath(*p.parts[1:])
 return pathlib.Path(candidate)/path
def fit(image,size):
 im=image.copy();im.thumbnail(size,Image.Resampling.LANCZOS);return im
def build_board(refs, candidates, out, title):
 W,H=1800,1780;board=Image.new("RGB",(W,H),(18,25,33));draw=ImageDraw.Draw(board)
 font=ImageFont.load_default(size=24);small=ImageFont.load_default(size=18)
 draw.text((18,10),title,fill="white",font=font)
 x=18
 for idx,p in enumerate(refs):
  im=fit(Image.open(p).convert("RGB"),(235,132));y=50
  board.paste(im,(x+(235-im.width)//2,y));draw.text((x,y+136),"REF "+str(idx+1),fill="white",font=small);x+=250
 draw.text((18,215),"SOURCE-BOUND T10 CANDIDATE PANELS",fill="white",font=font)
 cellw,cellh=590,370
 for idx,p in enumerate(candidates):
  im=fit(Image.open(p).convert("RGB"),(560,315));col=idx%3;row=idx//3;x0=col*600+15;y0=255+row*375
  board.paste(im,(x0+(570-im.width)//2,y0+35));draw.text((x0,y0),pathlib.Path(p).stem,fill="white",font=small)
 board.save(out,quality=93);return sha(out)
def build_motion(video,outdir,board_path):
 outdir.mkdir(parents=True,exist_ok=True)
 for p in outdir.glob("frame-*.png"):p.unlink()
 subprocess.run(["ffmpeg","-v","error","-i",str(video),"-vf","fps=2","-frames:v","12",str(outdir/"frame-%02d.png")],check=True,timeout=180)
 frames=sorted(outdir.glob("frame-*.png"))
 if len(frames)<8:raise ValueError("insufficient derived motion frames")
 board=Image.new("RGB",(1800,1280),(18,25,33));draw=ImageDraw.Draw(board);font=ImageFont.load_default(size=22)
 draw.text((18,10),"BOUND LIFECYCLE VIDEO — 2fps temporal samples",fill="white",font=font)
 for i,p in enumerate(frames[:12]):
  im=fit(Image.open(p).convert("RGB"),(430,242));col=i%4;row=i//4;x=col*450+10;y=55+row*400
  board.paste(im,(x+(430-im.width)//2,y+30));draw.text((x,y),"sample "+str(i+1),fill="white",font=font)
 board.save(board_path,quality=93);return frames[:12],sha(board_path)
def call(server,board,prompt,schema,out,name,seed):
 im=Image.open(board).convert("RGB");original=im.size;im.thumbnail((1664,1664),Image.Resampling.LANCZOS);buf=io.BytesIO();im.save(buf,format="JPEG",quality=92);payload=buf.getvalue()
 body={"model":"T10-final-visual","messages":[{"role":"user","content":[{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(payload).decode()}},{"type":"text","text":prompt}]}],"max_tokens":700,"temperature":0.2,"top_p":0.9,"seed":seed,"repeat_penalty":1.1,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
 (out/(name+"-request.json")).write_text(json.dumps({"prompt":prompt,"schema":schema,"image_sha256":hashlib.sha256(payload).hexdigest(),"original_size":original,"input_size":im.size,"seed":seed},indent=2))
 req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
 began=time.monotonic()
 with urllib.request.urlopen(req,timeout=1800) as resp:raw=json.load(resp)
 (out/(name+"-raw.json")).write_text(json.dumps(raw,indent=2))
 choice=raw["choices"][0]
 if choice.get("finish_reason")!="stop":raise ValueError("truncated visual review "+name)
 row=json.loads(choice["message"]["content"]);(out/(name+"-answer.json")).write_text(json.dumps(row,indent=2))
 return row,round(time.monotonic()-began,3)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--critic",choices=["C1","C2"],required=True);ap.add_argument("--candidate",required=True);ap.add_argument("--repo",required=True);ap.add_argument("--evidence",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 role=a.critic;candidate=pathlib.Path(a.repo);evidence=pathlib.Path(a.evidence);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if subprocess.check_output(["git","rev-parse","HEAD"],cwd=candidate,text=True).strip()!=a.candidate:raise ValueError("candidate worktree mismatch")
 manifest_path=evidence/(role+"-manifest.json");manifest=json.loads(manifest_path.read_text())
 if manifest.get("candidate_commit")!=a.candidate or manifest.get("critic_id")!=role:raise ValueError("visual manifest source mismatch")
 refs=[resolve(i["path"],candidate,evidence) for g in manifest["groups"] if g["id"]=="references" for i in g["items"]]
 lifecycle=[resolve(i["path"],candidate,evidence) for g in manifest["groups"] if g["id"]=="lifecycle" for i in g["items"]]
 if len(refs)!=7 or len(lifecycle)!=36:raise ValueError("incomplete visual manifest")
 for g in manifest["groups"]:
  for i in g["items"]:
   p=resolve(i["path"],candidate,evidence)
   if not p.is_file() or sha(p)!=i["sha256"]:raise ValueError("changed visual evidence "+i["path"])
 video=resolve(manifest["video"]["path"],candidate,evidence)
 if sha(video)!=manifest["video"]["sha256"]:raise ValueError("lifecycle video hash mismatch")
 device=evidence/"device-layout-evidence.json"
 if not device.is_file() or sha(device)!=manifest["device_manifest_sha256"]:raise ValueError("device manifest hash mismatch")
 native=json.loads((evidence/"native4k/manifest.json").read_text())
 if native.get("candidate")!=a.candidate or native.get("states")!=STATES or native.get("angles")!=ANGLES or native.get("record_count")!=36:raise ValueError("native4k domain incomplete")
 mapping={}
 for p in lifecycle:
  stem=p.stem
  hits=[(s,ang) for s in STATES for ang in ANGLES if stem==s+"-"+ang]
  if len(hits)!=1:raise ValueError("unexpected lifecycle filename "+stem)
  mapping[hits[0]]=p
 boards=[]
 for idx in range(0,len(STATES),2):
  subset=[mapping[(s,ang)] for s in STATES[idx:idx+2] for ang in ANGLES]
  p=out/("board-%d.jpg"%(idx//2+1));build_board(refs,subset,p,"LOCKED REFERENCES + "+"/".join(STATES[idx:idx+2]).upper()+" — all six angles");boards.append((p,"static"))
 motion_frames,motion_hash=build_motion(video,out/"motion-frames",out/"board-motion.jpg");boards.append((out/"board-motion.jpg","motion"))
 props={d:{"type":"number","minimum":0,"maximum":10} for d in DIMS[role]}
 schema={"type":"object","properties":{"observations":{"type":"array","items":{"type":"string","maxLength":180},"minItems":2,"maxItems":4},"defects":{"type":"array","items":{"type":"string","maxLength":180},"maxItems":5},"coverage_complete":{"type":"boolean"},"confidence":{"type":"string","enum":["low","medium","high"]},"scores":{"type":"object","properties":props,"required":DIMS[role],"additionalProperties":False}},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
 manifest_cfg=json.loads((candidate/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"];cache=pathlib.Path(os.path.expanduser(manifest_cfg["cache_path"]));model_manifest=json.loads((cache/"manifest.json").read_text())
 servers=list((cache/"runtime").rglob("llama-server"))
 if len(servers)!=1:raise ValueError("pinned visual reviewer runtime missing/ambiguous")
 server=servers[0];env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","");log=(out/"inference.log").open("w")
 proc=subprocess.Popen([str(server),"-m",str(cache/model_manifest["model_file"]),"--mmproj",str(cache/model_manifest["projector_file"]),"--host","127.0.0.1","--port","8080","-c","8192","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","1024","--image-max-tokens","2048"],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(180):
   if proc.poll() is not None:raise RuntimeError("visual reviewer runtime exited")
   try:
    if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
   except Exception:time.sleep(2)
  else:raise RuntimeError("visual reviewer runtime not ready")
  if role=="C1":
   role_text="Judge reference fidelity, visual-language match, and cross-view consistency. The reference frames define Havenline visual language, but T10 is deliberately a neutral transformation framework: T11 owns authored camp structures and main-loop art binding. Do not penalize absent T11 art. Judge whether T10's world-response ring/preview/label treatment, readability, scale and coherence fit the reference language across states and angles."
  else:
   role_text="Judge only technical/visual integrity: geometry/contact, clipping/seams, intentional gaps versus defects, projected feedback separation and cross-view integrity. Do not grade art style. Pay special attention to labels/shadows/response overlap, edge clipping, detached or intersecting geometry, and consistency across all six angles."
  common="Exact candidate "+a.candidate+". The top strip contains seven locked authoritative reference frames; all other labelled panels are fresh source-bound T10 renders. Every static board covers two complete lifecycle states across all six required angles; the motion board is derived from the hash-bound 30fps lifecycle video. Inspect every visible candidate panel. A score <=9.0 must correspond to a concrete actionable defect. Forward acceptance requires every score strictly >9.0 unrounded, defects [], complete coverage, medium/high confidence. Return JSON only."
  rows=[]
  for idx,(board,kind) in enumerate(boards):
   extra=" Motion samples represent the full bound lifecycle sequence; judge temporal visual consistency and clipping only." if kind=="motion" else ""
   row,elapsed=call(server,board,common+" "+role_text+extra,schema,out,"slice-%02d"%(idx+1),20260920+idx+(0 if role=="C1" else 100))
   scores=row.get("scores",{})
   if set(scores)!=set(DIMS[role]):raise ValueError("dimension coverage mismatch")
   if any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or not 0<=v<=10 for v in scores.values()):raise ValueError("invalid score")
   rows.append({"slice":idx+1,"kind":kind,"board":board.name,"board_sha256":sha(board),"review":row,"elapsed_seconds":elapsed})
  confidence_order={"low":0,"medium":1,"high":2}
  defects=[];seen=set()
  for row in rows:
   for d in row["review"]["defects"]:
    if d not in seen:seen.add(d);defects.append(d)
  aggregate={"scores":{d:min(row["review"]["scores"][d] for row in rows) for d in DIMS[role]},"defects":defects,"coverage_complete":all(row["review"]["coverage_complete"] is True for row in rows),"confidence":min((row["review"]["confidence"] for row in rows),key=confidence_order.get),"observations":list(dict.fromkeys(x for row in rows for x in row["review"]["observations"]))}
  raw={"task":"T10","candidate":a.candidate,"critic_id":role,"aggregation":"minimum score across all static and motion slices; union defects; no averaging","manifest_sha256":sha(manifest_path),"video_sha256":sha(video),"motion_board_sha256":motion_hash,"slices":rows,"aggregate":aggregate}
  raw_path=out/"raw-output.json";raw_path.write_text(json.dumps(raw,indent=2)+"\n")
  rel=str(raw_path.resolve().relative_to(pathlib.Path.cwd().resolve()))
  record={"task_id":"T10","critic_id":role,"provider":"local-checksum-pinned-public-model","model":model_manifest["base_model"],"request_or_run_id":":".join([os.environ.get("GITHUB_RUN_ID","local"),os.environ.get("GITHUB_RUN_ATTEMPT","0"),os.environ.get("GITHUB_JOB","local"),role]),"candidate_hash":a.candidate,"input_manifest_hash":sha(manifest_path),"raw_output_path":rel,"raw_output_hash":sha(raw_path),"scores":aggregate["scores"],"defects":aggregate["defects"],"coverage_complete":aggregate["coverage_complete"],"confidence":aggregate["confidence"],"independent_runtime":True,"passed":all(v>9.0 for v in aggregate["scores"].values()) and not aggregate["defects"] and aggregate["coverage_complete"] and aggregate["confidence"] in ("medium","high")}
  (out/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n");print(json.dumps(record,indent=2));return 0 if record["passed"] else 1
 finally:
  proc.terminate()
  try:proc.wait(timeout=15)
  except Exception:proc.kill()
  log.close()
if __name__=="__main__":raise SystemExit(main())
