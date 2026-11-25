from pathlib import Path
import hashlib, subprocess,sys,json,difflib,tempfile
p='11c14a1c41971067c7dc97db69375f720a408f68'
repo=Path(sys.argv[1]); base=Path('..')
src=lambda f:subprocess.check_output(['git','-C',repo,'show',p+':HavenlineLevel1/'+f])
pine=base/'hvn-l1-paid-pine-renewal-v1/renewal.patch';pine=pine.resolve()
assert hashlib.sha256(pine.read_bytes()).hexdigest()=='e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd'
with tempfile.TemporaryDirectory() as w:
 q=Path(w)
 for f in ('opening_ledger.gd','previews/integrated_opening.gd'):
  t=q/f;t.parent.mkdir(exist_ok=True);t.write_bytes(src(f))
 subprocess.run(['patch','--fuzz=0','-s','-p2','-i',str(pine)],cwd=q,check=True)
 integrated=(q/'previews/integrated_opening.gd').read_text()
stock=src('wood_stock_view.gd').decode()
s=stock+Path('paid_piece_methods.gdfrag').read_text()
s=s.replace('const Wood = preload','const HardwoodCrown := preload("res://assets/studio/starter_ground_wood_lod.glb")\nconst PAID_CROWN_PITCH := .105\nvar paid_crowns: Array[MeshInstance3D] = []\nvar paid_crown_fit_attempted := false\nconst Wood = preload',1)
# Existing source fallback is untouched, except explicitly clear the paid
# visual before processing a new ordinary publication event.
s=s.replace('func reflect_stock(published_wood: int) -> void:\n','func reflect_stock(published_wood: int) -> void:\n\tfor crown in paid_crowns:\n\t\tcrown.hide()\n')
i=integrated+Path('preview_reader.gdfrag').read_text()
def h(x):return subprocess.check_output(['git','hash-object','--stdin'],input=x.encode()).decode().strip()
assert h(integrated)=='ca88b482831e0898b488be6efa63caf691f2eb95'
targets={'wood_stock_view.gd':(stock,s),'previews/integrated_opening.gd':(integrated,i)}
patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),'a/HavenlineLevel1/'+f,'b/HavenlineLevel1/'+f)) for f,(a,b) in targets.items())
Path('display-only.patch').write_text(patch)
print(json.dumps({f:{'baseline_or_pine_blob':h(a),'presentation_trial_blob':h(b)} for f,(a,b) in targets.items()},indent=2))
