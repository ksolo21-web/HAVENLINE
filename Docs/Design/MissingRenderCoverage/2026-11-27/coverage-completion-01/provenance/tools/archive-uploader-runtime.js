async function uploadStagedImages(planMode="staged", concurrency=4){
 const started=Date.now();
 if(!["staged","draft"].includes(planMode)||!Number.isInteger(concurrency)||concurrency<1||concurrency>8)throw new Error("Unsupported transfer mode/concurrency");
 const command=planMode==="draft"?"python havenline-missing-renders-2026-11-27/archive-draft-image-upload-plan.py --limit 100":"python havenline-missing-renders-2026-11-27/archive-tools.py upload-plan";
 const r=await tools.exec_command({cmd:command,max_output_tokens:220000});
 if(r.exit_code!==0)throw new Error(r.output);
 const plan=JSON.parse(r.output);
 async function uploadOne(row){
  if(!/^[A-Za-z0-9_./-]+$/.test(row.local_path))throw new Error("Unexpected path syntax");
  const chunk=524286,offsets=Array.from({length:Math.ceil(row.bytes/chunk)},(_,i)=>i*chunk);
  const parts=await Promise.allSettled(offsets.map(offset=>tools.exec_command({
   cmd:"python - <<'PY'\nfrom pathlib import Path\nimport base64,sys,hashlib\np=Path('"+row.local_path+"')\nassert hashlib.sha256(p.read_bytes()).hexdigest() == '"+row.sha256+"'\nwith p.open('rb') as f:\n f.seek("+offset+")\n sys.stdout.write(base64.b64encode(f.read("+chunk+")).decode('ascii'))\nPY",max_output_tokens:220000})));
  let b64="";
  for(let i=0;i<parts.length;i++){const r=parts[i];if(r.status!=="fulfilled")throw new Error("Chunk failed");const q=r.value,s=q.output.trim(),n=4*Math.ceil(Math.min(chunk,row.bytes-offsets[i])/3);if(q.exit_code!==0||s.length!==n||!/^[A-Za-z0-9+/]*={0,2}$/.test(s))throw new Error("Incomplete chunk");b64+=s;}
  if(b64.length!==4*Math.ceil(row.bytes/3))throw new Error("Assembly mismatch");
  let q=await tools.mcp__codex_apps__github_create_blob({repository_full_name:"ksolo21-web/HAVENLINE",encoding:"base64",content:b64});
  while(q?.structuredContent)q=q.structuredContent;
  if(!q.sha&&typeof q.content==="string")q=JSON.parse(q.content);
  if(!q.sha&&Array.isArray(q.content))q=JSON.parse(q.content.find(z=>z.type==="text").text);
  if(q.sha!==row.git_blob_sha)throw new Error("Remote identity mismatch");
  const data=JSON.stringify({...row,remote_git_blob_sha:q.sha,remote_url:q.url??null,status:"IMMUTABLE_BLOB_UPLOADED_UNATTACHED"},null,2)+"\n";
  await tools.apply_patch("*** Begin Patch\n*** Add File: /workspace/scratch/9c51da47f878/havenline-missing-renders-2026-11-27/archive-upload-receipts/"+row.git_blob_sha+".json\n"+data.split("\n").slice(0,-1).map(l=>"+"+l).join("\n")+"\n*** End Patch");
  return {path:row.path,bytes:row.bytes,git_blob_sha:q.sha};
 }
 let uploaded=0,failure=null;
 try{
  for(let start=0;start<plan.pending.length;start+=concurrency){
   const results=await Promise.allSettled(plan.pending.slice(start,start+concurrency).map(uploadOne));
   const errors=[];
   for(const result of results){if(result.status==="fulfilled")uploaded++;else errors.push(String(result.reason));}
   if(uploaded%20===0||start+concurrency>=plan.pending.length)text({transfer_mode:planMode,uploaded_this_batch:uploaded,planned_this_batch:plan.pending.length,pending_before_batch:plan.pending_total_before_limit??plan.pending.length,elapsed_seconds:Math.round((Date.now()-started)/1000),branch_published:false});
   if(errors.length)throw new Error(errors.join(" | "));
  }
 }catch(error){failure=error;}
 const merge=await tools.exec_command({cmd:"python - <<'PY'\nfrom pathlib import Path\nimport json,importlib.util\nr=Path('havenline-missing-renders-2026-11-27').resolve();spec=importlib.util.spec_from_file_location('a',r/'archive-tools.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)\np=r/'archive-blob-receipts.json';doc=a.read(p) if p.exists() else {'schema_version':1,'meaning':'Unattached immutable Git objects until final verified branch publication.','receipts':[]}\nby={x['git_blob_sha']:x for x in doc['receipts']}\nfor path in sorted((r/'archive-upload-receipts').glob('*.json')):\n row=a.read(path)\n if row['git_blob_sha'] in by:assert all(by[row['git_blob_sha']][k]==row[k] for k in ['bytes','sha256','git_blob_sha','remote_git_blob_sha'])\n else:by[row['git_blob_sha']]=row\n assert row['git_blob_sha']==row['remote_git_blob_sha']\ndoc['receipts']=list(by.values());a.write(p,doc)\nprint(json.dumps({'uploaded_distinct_blobs':len(by),'remote_branch_created':False}))\nPY",max_output_tokens:1000});
 if(merge.exit_code!==0)throw new Error(merge.output);
 text(merge.output);
 if(failure)throw failure;
 return {uploaded_this_batch:uploaded,pending_before_batch:plan.pending_total_before_limit??plan.pending.length};
}
