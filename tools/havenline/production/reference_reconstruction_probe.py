#!/usr/bin/env python3
"""One read-only QA authoring-capability probe; never a production candidate.

Reconstruct one exact user-supplied furnace crop using pinned TripoSR code. Retain
input, implementation/weight identities, raw mesh, metrics and failures. No score,
approval, lifecycle mutation, runtime file write or automatic integration occurs.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,re,subprocess,sys,time,traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/'Docs/Production/Evidence/ReferenceReconstruction'
OUT=ROOT/'reconstruction-probe'
INPUT_SHA='5a920bba088e837f0ae688ead05ac684907f5693c9b3a9bf8d0119ea9249c052'
CODE_SHA='107cefdc244c39106fa830359024f6a2f1c78871'
SOURCE_SHA='e372bf74be027cb63a0f83c4247a7843a8195a9c579e75a415ddcf3c0052eaec'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def record(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')


def prepare():
    encoded=''.join(''.join((INPUT/f'input_{n}.b64').read_text().split()) for n in [1,20,21,22,23])
    raw=base64.b64decode(encoded,validate=True)
    if len(raw)!=13464 or hashlib.sha256(raw).hexdigest()!=INPUT_SHA:
        raise ValueError('Exact supplied furnace crop bytes do not match')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'source-furnace.jpg').write_bytes(raw)
    record('input-provenance.json',{
        'source_file':'18600.png','source_sha256':SOURCE_SHA,
        'crop_pixels':[430,30,715,268],'derived_dimensions':[224,187],
        'derived_file':'source-furnace.jpg','derived_sha256':INPUT_SHA,
        'role':'user-supplied larger rounded furnace from construction sheet',
        'not_source':'18567.png meat processor is not used',
        'mode':'AUTHORING_CAPABILITY_DIAGNOSTIC_ONLY',
        'runtime_files_changed':False,'task_approved':False,'visual_approved':False,
        'independent_critic':False,'reusable_for_approval':False,
        'run_id':os.environ.get('GITHUB_RUN_ID'),'diagnostic_source':os.environ.get('GITHUB_SHA')})


def infer():
    prepare()
    from PIL import Image
    import numpy as np
    import torch
    import rembg
    from huggingface_hub import HfApi,snapshot_download
    code=Path(os.environ['RECONSTRUCTION_CODE'])
    actual=subprocess.check_output(['git','-C',str(code),'rev-parse','HEAD'],text=True).strip()
    if actual!=CODE_SHA:raise ValueError('Reconstruction implementation SHA mismatch')
    sys.path.insert(0,str(code))
    from tsr.system import TSR
    from tsr.utils import remove_background,resize_foreground
    torch.set_num_threads(4);torch.manual_seed(20260926);np.random.seed(20260926)
    image=Image.open(OUT/'source-furnace.jpg');image.load()
    if image.size!=(224,187):raise ValueError('Source crop dimensions changed')
    started=time.monotonic()
    info=HfApi().model_info('stabilityai/TripoSR')
    revision=info.sha
    if not isinstance(revision,str) or not re.fullmatch('[0-9a-f]{40}',revision):
        raise ValueError('Missing exact official weight revision')
    weights=Path(snapshot_download('stabilityai/TripoSR',revision=revision,
        allow_patterns=['config.yaml','model.ckpt','README.md','LICENSE*']))
    weight_manifest={p.name:digest(p) for p in weights.iterdir() if p.is_file()}
    record('model-provenance.json',{
        'code_repository':'VAST-AI-Research/TripoSR','code_sha':actual,
        'weight_repository':'stabilityai/TripoSR','resolved_weight_revision':revision,
        'weight_files':weight_manifest,'device':'cpu','torch_version':torch.__version__,
        'mesh_resolution':192,'renderer_chunk':8192,'single_input':True,
        'task_approved':False,'reusable_for_approval':False})
    print('Exact official model inputs retained',flush=True)
    rgba=remove_background(image,rembg.new_session('u2net'))
    rgba=resize_foreground(rgba,.85)
    rgba.save(OUT/'foreground.png')
    array=np.array(rgba,dtype=np.float32)/255.
    composited=array[:,:,:3]*array[:,:,3:4]+(1-array[:,:,3:4])*.5
    prepared=Image.fromarray((composited*255).astype(np.uint8))
    prepared.save(OUT/'model-input.png')
    print('Foreground prepared',time.monotonic()-started,flush=True)
    model=TSR.from_pretrained(str(weights),config_name='config.yaml',weight_name='model.ckpt')
    model.eval();model.to('cpu');model.renderer.set_chunk_size(8192)
    print('CPU model loaded',time.monotonic()-started,flush=True)
    with torch.inference_mode():
        scene=model([prepared],device='cpu')
        print('Single-image inference completed',time.monotonic()-started,flush=True)
        meshes=model.extract_mesh(scene,True,resolution=192)
    if len(meshes)!=1:raise ValueError('Expected exactly one reconstructed mesh')
    mesh=meshes[0]
    if len(mesh.vertices)==0 or len(mesh.faces)==0 or not np.isfinite(mesh.vertices).all():
        raise ValueError('Reconstruction is empty or nonfinite')
    path=OUT/'furnace-reconstruction-UNAPPROVED.glb'
    mesh.export(path)
    record('result.json',{
        'execution_complete':True,'authoring_probe_completed':True,
        'input_sha256':INPUT_SHA,'code_sha':actual,'weight_revision':revision,
        'model_input_sha256':digest(OUT/'model-input.png'),
        'mesh_file':path.name,'mesh_sha256':digest(path),'mesh_bytes':path.stat().st_size,
        'vertices':len(mesh.vertices),'triangles':len(mesh.faces),
        'bounds':mesh.bounds.tolist(),'is_watertight':bool(mesh.is_watertight),
        'winding_consistent':bool(mesh.is_winding_consistent),
        'visual_kind':mesh.visual.kind,'elapsed_authoring_seconds':time.monotonic()-started,
        'source_reconstruction_is_exact_copy':False,
        'unobserved_surfaces_require_review':True,'gameplay_contracts_not_applied':True,
        'lod_uv_material_performance_review_complete':False,
        'task_approved':False,'visual_approved':False,'independent_critic':False,
        'reusable_for_approval':False,'physical_4k60_certified':False})
    print('Unapproved authoring mesh retained',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--infer',action='store_true');a=ap.parse_args()
    try:
        infer() if a.infer else prepare()
    except Exception as exc:
        record('failure.json',{'execution_complete':False,'error_type':type(exc).__name__,
               'error':str(exc),'traceback':traceback.format_exc(),
               'task_approved':False,'visual_approved':False,'reusable_for_approval':False})
        raise
