import hashlib,json,struct,re
from pathlib import Path
P=Path(__file__).resolve().parent.parent
S=P/'hvn-pad-mount-admission/isolated-source/HavenlineLevel1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gitblob(p):
 b=p.read_bytes();return hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()
paths={'previews/integrated_opening.tscn':'39180754353c4f73355f253dc4d9cb7e1427d1c1','previews/integrated_opening.gd':'cc54fb10b5270f513baa2c3743d4879e29ebb41a','previews/hero_locomotion.gd':'d8f32b0a2cc3c512982f3b7f17d9a952a5a6a7a7','resource_tree.gd':'a0a846551bb574728cedcd3b76bfe785cd0b5192','opening.gd':'8de9499b0a48d920516d3b07c889cfb8a0808038'}
assert all(gitblob(S/p)==h for p,h in paths.items())
def glb(p,h):
 assert sha(p)==h
 b=p.read_bytes();n,m=struct.unpack_from('<II',b,12);assert m==0x4e4f534a
 j=json.loads(b[20:20+n]);return dict(sha256=h,joints=[len(k['joints']) for k in j['skins']],animations=[a['name'] for a in j.get('animations',[])])
stock=glb(S/'assets/characters/Character1.glb','95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099')
fingered=glb(P/'hvn-c1-distinct-art-source-read/Character 1 rigged - with fingers - no animation.glb','280d493b9ddedd728835a4df2ba8c1c810ae03e3dd52c4b323c773150d03d39c')
assert stock['joints']==[66] and len(stock['animations'])==3 and fingered['joints']==[73] and not fingered['animations']
D=P/'hvn-l1-carry-pose-quantization-v1/graphics-evidence.pPDeoK45'
A=D/'carry-pose-evidence.json';assert sha(A)=='287a848ccf8bd253f19c191eca6d480e60b9c89369804d6fb13a8c0c1129419a'
keys=['funded-approach-moving','funded-near-moving']
hashes=['77582036564ea5c1eddf532a14011a273039110bdc10628a7607e0e864844da4','7b6c3782d7083bc555440cf539c7f45d2d2eec776d2031607d8b232fb1fd840d']
for k,h in zip(keys,hashes):assert sha(D/(k+'.png'))==h
w=[json.loads(x) for x in re.findall(r'^CARRY_POSE_WITNESS (.+)$',(D/'write.log').read_text(),re.M)]
native=json.loads(A.read_bytes())['phases']
assert [x['stage'] for x in native]==keys and len(w)==2 and all('l1_hero_preview/run' in json.dumps(a) for a in w)
E=P/'hvn-l1-carry-cycle-palette-v1/graphics-evidence.WJBzcCP5'; e=E/'palette.json'
assert sha(e)=='adc3a22f4f87c4b51ad49940477e3b78a638f50fd5e6bf4c2de237a5347ac836'
r=json.loads(e.read_bytes())['rows']
assert len(r)==77 and [x['tick'] for x in r]==list(range(8,85)) and {x['clip'] for x in r}=={'l1_hero_preview/run'}
out=dict(scene_git_blobs=paths,stock=stock,fingered_source=fingered,
 run_registered_frames=[dict(stage=x['stage'],phase=x['runtime_clip_pos_s'],png_sha256=h,receipt_physics=f,actual_pose_shader_model_error_m=x['host_bake_and_source_shader_formula_error_m']) for x,h,f in zip(native,hashes,[347,356])],
 run_cycle=dict(rows=len(r),first_last=[{k:x[k] for k in ('tick','process','physics','phase','clip')} for x in (r[0],r[-1])],png_stream=False),
 admission='run registration only, no continuous RGB, stock walk or axe comparator')
print(json.dumps(out,indent=2))
