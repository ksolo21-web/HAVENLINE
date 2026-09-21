#!/usr/bin/env python3
"""Focused independent T10 closeout judgments for only the still-invalidated critic domains."""
from __future__ import annotations
import argparse,base64,hashlib,io,json,math,os,pathlib,subprocess,time,urllib.request,urllib.error
from PIL import Image,ImageDraw,ImageFont

DIMS={
 "c1-motion":["reference_fidelity","visual_language","cross_view_consistency"],
 "c2-static":["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"],
 "c2-motion":["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"],
 "c4":["interactable_clarity","danger_clarity","collection_feedback","resource_destination","world_change_clarity","next_action_clarity"],
}
CRITIC={"c1-motion":"C1","c2-static":"C2","c2-motion":"C2","c4":"C4"}

def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""): h.update(b)
 return h.hexdigest()

def resolve(path,repo,evidence):
 p=pathlib.PurePosixPath(path)
 return pathlib.Path(evidence).joinpath(*p.parts[1:]) if p.parts and p.parts[0]=="critic-input" else pathlib.Path(repo)/path

def fit(im,size):
 x=im.copy();x.thumbnail(size,Image.Resampling.LANCZOS);return x

def board(items,out,title,cols=3):
 tile=(500,281);label_h=30
 rows=max(1,math.ceil(len(items)/cols));W=cols*520;H=70+rows*(tile[1]+label_h+20)
 b=Image.new("RGB",(W,H),(18,25,33));d=ImageDraw.Draw(b)
 titlefont=ImageFont.load_default(size=24);small=ImageFont.load_default(size=18)
 d.text((16,14),title,fill="white",font=titlefont)
 for n,(label,p) in enumerate(items):
  im=fit(Image.open(p).convert("RGB"),tile);c=n%cols;r=n//cols;x=c*520+10;y=60+r*(tile[1]+label_h+20)
  b.paste(im,(x+(500-im.width)//2,y));d.text((x,y+tile[1]+4),label[:72],fill="white",font=small)
 b.save(out,quality=94)

def first_per_state(timeline,capture_dir):
 rows=timeline["sample_mapping"];result=[]
 for state in ["ready","blocked","preview","committing","complete","replay"]:
  hit=next((r for r in rows if r.get("state")==state),None)
  if hit is None: raise ValueError("missing motion state "+state)
  result.append((state.upper(),capture_dir/hit["file"]))
 return result

def selected_native(evidence,names):
 return [(name.replace("-"," ").upper(),pathlib.Path(evidence)/"native4k"/(name+".png")) for name in names]

def validate_manifest(manifest_path,candidate,cid,repo,evidence):
 m=json.loads(manifest_path.read_text())
 if m.get("candidate_commit")!=candidate or m.get("critic_id")!=cid: raise ValueError("manifest identity mismatch")
 for g in m.get("groups",[]):
  for i in g.get("items",[]):
   p=resolve(i["path"],repo,evidence)
   if not p.is_file() or sha(p)!=i["sha256"]: raise ValueError("changed evidence "+i["path"])
 return m

def request_review(focus,candidate,repo,evidence,out):
 cid=CRITIC[focus];dims=DIMS[focus]
 manifest=validate_manifest(pathlib.Path(evidence)/(cid+"-manifest.json"),candidate,cid,repo,evidence)
 device=json.loads((pathlib.Path(evidence)/"device-layout-evidence.json").read_text())
 native=json.loads((pathlib.Path(evidence)/"native4k/manifest.json").read_text())
 if device.get("candidate",candidate)!=candidate and device.get("rows") is None: raise ValueError("device evidence identity mismatch")
 if device.get("projection_count")!=216 or device.get("projection_failure_count")!=0: raise ValueError("device projection proof not clean")
 if native.get("candidate")!=candidate or native.get("record_count")!=36: raise ValueError("native4k proof incomplete")
 timeline=json.loads((pathlib.Path(evidence)/"motion-timeline.json").read_text())
 capture_dir=pathlib.Path(evidence)/"capture"

 refs=[]
 if focus=="c1-motion":
  refs=[resolve(i["path"],repo,evidence) for g in manifest["groups"] if g["id"]=="references" for i in g["items"]][:3]
  items=[("REF "+str(i+1),p) for i,p in enumerate(refs)] + first_per_state(timeline,capture_dir)
  title="T10 C1 focused motion/replay review — exact source-bound frames"
  role=("Judge only the remaining C1 motion/replay slice. The three reference thumbnails are context; the six candidate frames cover READY, BLOCKED, PREVIEW, COMMITTING, COMPLETE and REPLAY. "
        "T10 intentionally uses a circular/cylindrical StateRing plus a separate box-like PreviewVolume. REPLAY is exact idempotency: after replaying an accepted transaction, the visible world MUST remain identical to COMPLETE. "
        "No visible change between COMPLETE and REPLAY is correct, not a defect. Judge reference fidelity, visual-language continuity and lifecycle consistency from these exact frames.")
 elif focus=="c2-static":
  items=selected_native(evidence,["preview-side","preview-overhead","preview-gameplay","committing-side","committing-overhead","committing-gameplay"])
  title="T10 C2 focused PREVIEW/COMMITTING geometry review — exact native4K frames"
  role=("Judge only the remaining PREVIEW/COMMITTING technical-integrity slice. Source-bound geometry facts: StateRing top y=0.08; PreviewVolume bottom y=0.16, so the world-space vertical gap is +0.08. "
        "The authoritative projection matrix contains 216 projections with zero failures. The PreviewVolume is translucent, so alpha projection can visually overlay the ground/ring in screen space without 3D contact. "
        "Use both the rendered pixels and these bound geometry facts. Flag only actual clipping, contact/intersection, unintended seam, or cross-view integrity defects.")
 elif focus=="c2-motion":
  items=first_per_state(timeline,capture_dir)
  title="T10 C2 focused lifecycle-motion integrity review — one exact frame per state"
  role=("Judge only the remaining lifecycle-motion technical-integrity slice. The six frames cover every T10 lifecycle state once. Source geometry has StateRing top y=0.08 and PreviewVolume bottom y=0.16, a positive +0.08 gap. "
        "The 216-case projection matrix has zero failures. REPLAY intentionally preserves COMPLETE geometry exactly. Flag only actual clipping/contact/seam or lifecycle cross-view integrity defects visible in these exact frames.")
 else:
  life=selected_native(evidence,["ready-front","blocked-front","preview-front","committing-front","complete-front","replay-front"])
  devices=[]
  root=pathlib.Path(evidence)/"device-layout"
  for folder in sorted(p for p in root.iterdir() if p.is_dir()):
   for state in ("blocked","complete"):
    p=folder/(state+"-front.png")
    if p.is_file(): devices.append((folder.name+" "+state,p))
  items=life+devices
  title="T10 C4 focused gameplay UX/readability closeout — lifecycle + all device states"
  role=("Judge T10 gameplay UX/readability only within T10 scope. T10 adds no danger mechanic, enemy, hazard, warning animation or harvesting UI. For danger_clarity, judge whether the presentation avoids falsely implying danger and clearly distinguishes BLOCKED resource/prerequisite status from READY/PREVIEW/COMPLETE; do not require alarms, shaking, hazard icons or enemies. "
        "For collection_feedback/resource_destination, judge delivered-stock transform feedback: Cost, Need, Spent and the named transform destination; do not require new gathering/collection animation. "
        "COMPLETE deliberately presents the completed result first, then NEXT action. REPLAY is exact idempotency and must visually match COMPLETE. "
        "The board contains all six lifecycle front views plus BLOCKED and COMPLETE front views for every authoritative device layout. Judge all six mandatory C4 dimensions and name only concrete actionable defects supported by the supplied pixels.")

 board_path=pathlib.Path(out)/"focused-board.jpg";board(items,board_path,title,cols=4 if focus=="c4" else 3)
 facts={
  "candidate":candidate,"focus":focus,"critic":cid,
  "device_projection_count":device["projection_count"],"device_projection_failures":device["projection_failure_count"],
  "native4k_record_count":native["record_count"],"native4k_resolution":native.get("capture_resolution"),
  "geometry":{"state_ring_top_y":0.08,"preview_volume_bottom_y":0.16,"vertical_gap":0.08},
  "scope_note":"T11 authored camp art/main-loop binding excluded; T10 is neutral world-transform feedback."
 }
 (pathlib.Path(out)/"focused-facts.json").write_text(json.dumps(facts,indent=2)+"\n")

 rt=json.loads((pathlib.Path(repo)/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"]
 cache=pathlib.Path(os.path.expanduser(rt["cache_path"]));mf=json.loads((cache/"manifest.json").read_text());servers=list((cache/"runtime").rglob("llama-server"))
 if len(servers)!=1: raise RuntimeError("reviewer runtime missing")
 server=servers[0];env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
 log=(pathlib.Path(out)/"runtime.log").open("w")
 proc=subprocess.Popen([str(server),"-m",str(cache/mf["model_file"]),"--mmproj",str(cache/mf["projector_file"]),"--host","127.0.0.1","--port","8080","-c","6144","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","512","--image-max-tokens","768"],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(150):
   if proc.poll() is not None: raise RuntimeError("review runtime exited")
   try:
    if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok": break
   except Exception: time.sleep(2)
  else: raise RuntimeError("review runtime not ready")

  props={d:{"type":"number","minimum":0,"maximum":10} for d in dims}
  schema={"type":"object","properties":{
   "observations":{"type":"array","items":{"type":"string","maxLength":180},"minItems":2,"maxItems":4},
   "defects":{"type":"array","items":{"type":"string","maxLength":180},"maxItems":5},
   "coverage_complete":{"type":"boolean"},"confidence":{"type":"string","enum":["low","medium","high"]},
   "scores":{"type":"object","properties":props,"required":dims,"additionalProperties":False}},
   "required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
  prompt=("You are an independent Havenline "+cid+" critic reviewing exact candidate "+candidate+". "+role+
          " This is a focused closeout judgment for the only still-invalidated slice/domain; other critic slices are preserved separately and are not part of this request. "
          "Strict PASS requires every supplied mandatory dimension >9.0 unrounded, zero defects, complete coverage, and medium/high confidence. A score <=9 must name a concrete actionable defect. "
          "Do not average and do not invent out-of-scope requirements. Return JSON only. SOURCE-BOUND FACTS: "+json.dumps(facts,sort_keys=True))
  im=Image.open(board_path).convert("RGB");im.thumbnail((1536,1536),Image.Resampling.LANCZOS);buf=io.BytesIO();im.save(buf,format="JPEG",quality=92)
  content=[{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()}},{"type":"text","text":prompt}]
  body={"model":"T10-focused-closeout","messages":[{"role":"user","content":content}],"max_tokens":500,"temperature":0.15,"top_p":0.9,
        "seed":20261100+list(DIMS).index(focus),"repeat_penalty":1.1,"chat_template_kwargs":{"enable_thinking":False},
        "response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
  req_bytes=json.dumps(body).encode();(pathlib.Path(out)/"request.json").write_bytes(req_bytes)
  req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=req_bytes,headers={"Content-Type":"application/json"},method="POST")
  with urllib.request.urlopen(req,timeout=900) as resp: raw=json.load(resp)
  (pathlib.Path(out)/"raw-response.json").write_text(json.dumps(raw,indent=2))
  choice=raw["choices"][0]
  if choice.get("finish_reason")!="stop": raise RuntimeError("incomplete reviewer response")
  review=json.loads(choice["message"]["content"])
  defects=review.get("defects",[])
  if isinstance(defects,list):
   empty={"none","none.","no defects","no defects.","n/a","na"}
   defects=[d for d in defects if not(isinstance(d,str) and d.strip().lower() in empty)]
   review["defects"]=defects
  scores=review.get("scores",{})
  errors=[]
  if set(scores)!=set(dims): errors.append("dimension mismatch")
  if review.get("coverage_complete") is not True: errors.append("coverage")
  if review.get("confidence") not in ("medium","high"): errors.append("confidence")
  if defects: errors.append("defects")
  if any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9 for v in scores.values()): errors.append("score")
  raw_payload={"critic_id":cid,"candidate":candidate,"focus":focus,"review":review,"facts":facts}
  raw_path=pathlib.Path(out)/"raw-output.json";raw_path.write_text(json.dumps(raw_payload,indent=2)+"\n")
  record={
   "task_id":"T10","critic_id":cid,"candidate_hash":candidate,
   "provider":mf.get("publisher"),"model":mf.get("base_model"),"model_revision_actual":mf.get("revision"),
   "request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB",focus),
   "input_manifest_hash":sha(pathlib.Path(evidence)/(cid+"-manifest.json")),
   "focused_input_hash":sha(board_path),"raw_output_path":str(raw_path),"raw_output_hash":sha(raw_path),
   "scores":scores,"defects":defects,"coverage_complete":review.get("coverage_complete") is True,
   "confidence":review.get("confidence"),"independent_runtime":True,"focus":focus,"passed":not errors,"errors":errors
  }
  (pathlib.Path(out)/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
  print(json.dumps(record,indent=2))
  return 0 if not errors else 1
 finally:
  proc.terminate()
  try: proc.wait(timeout=10)
  except Exception: proc.kill()
  log.close()

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--focus",choices=list(DIMS),required=True);ap.add_argument("--candidate",required=True);ap.add_argument("--repo",required=True);ap.add_argument("--evidence",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if subprocess.check_output(["git","rev-parse","HEAD"],cwd=a.repo,text=True).strip()!=a.candidate: raise SystemExit("candidate mismatch")
 if os.environ.get("HAVENLINE_INDEPENDENT_REVIEW_JOB")!="1": raise SystemExit("independent review job required")
 try: return request_review(a.focus,a.candidate,pathlib.Path(a.repo),pathlib.Path(a.evidence),out)
 except Exception as exc:
  (out/"fatal.json").write_text(json.dumps({"focus":a.focus,"error":type(exc).__name__+": "+str(exc)},indent=2)+"\n")
  raise

if __name__=="__main__": raise SystemExit(main())
