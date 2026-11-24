import json,hashlib
from pathlib import Path
from PIL import Image
BASE=Path('/workspace/scratch/fc906e16b0fb/havenline-plot-renders')
ROOT=BASE/'reviews'
CONTRACT=json.loads((BASE/'acceptance-contract.json').read_text())
ASSETS={a['id']:a for a in CONTRACT['assets']}
def record(filename,batch,iteration,specs,extra=None):
    entries=[]
    for s in specs:
        d=dict(s)
        p=Path(d['candidate_path'])
        d.update(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,dimensions=list(Image.open(p).size),format=d.get('format',ASSETS[d['asset']]['format']),source_status=ASSETS[d['asset']].get('source_status','reference_derived_state_concept'),actual_full_sheet_inspected=True)
        if d['format']=='8_view_turnaround': d.update(view_count=8,panel_count=8,view_order_degrees=[0,45,90,135,180,225,270,315])
        entries.append(d)
    out={'reviewer_agent':'/root/turnaround_critic','contract_version':CONTRACT['version'],'contract_sha256':hashlib.sha256((BASE/'acceptance-contract.json').read_bytes()).hexdigest(),'batch':batch,'iteration':iteration,'assets':entries,'gate':'PASS requires score strictly above 9.0 with all mandatory concept-image checks passed. Unseen or failed evidence remains blocked.'}
    if extra:out.update(extra)
    path=ROOT/filename
    path.write_text(json.dumps(out,indent=2)+'\n')
    indexpath=ROOT/'review-index.json'; index=json.loads(indexpath.read_text())
    if str(path) not in index['asset_reviews']:index['asset_reviews'].append(str(path))
    latest={}
    for f in index['asset_reviews']:
        for a in json.loads(Path(f).read_text())['assets']:latest[a['asset']]=a
    passed=sum(a['verdict']=='PASS_CONCEPT_SHEET' for a in latest.values())
    blocked=len(latest)-passed;unseen=26-len(latest)
    index['status']=f'{passed}_PASS_{blocked}_REPAIR_PENDING_{unseen}_UNREVIEWED'
    index['counts']={'required':26,'pass':passed,'blocked':blocked,'unreviewed':unseen}
    indexpath.write_text(json.dumps(index,indent=2)+'\n')
    print(filename,hashlib.sha256(path.read_bytes()).hexdigest(),index['status'])
