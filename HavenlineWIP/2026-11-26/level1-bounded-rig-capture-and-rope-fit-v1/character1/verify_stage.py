from pathlib import Path
import json,sys
def load(f):return dict((p,h) for h,p in (l.split(maxsplit=1) for l in Path(f).read_text().splitlines()))
old,new=map(load,sys.argv[1:])
assert set(new)-set(old)=={'./tests/c1_normal_stock_capture.gd'}
assert all(new.get(p)==h for p,h in old.items())
print(json.dumps({'untouched_project_files':len(old),'only_new_leaf_observer':new['./tests/c1_normal_stock_capture.gd'],'engine_executed':False},indent=2))
