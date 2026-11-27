extends SceneTree
const Count = preload("res://exact_count.gd")
func _initialize() -> void:
 var cases: Array = JSON.parse_string(FileAccess.get_file_as_string(get_script().resource_path.get_base_dir().path_join("exact-count-oracle.json")))
 var failed := []
 for i in range(cases.size()):
  var c: Dictionary = cases[i]
  if Count.add(c.a,c.b) != c.add or Count.subtract(c.hi,c.lo) != c.subtract or Count.compare(c.a,c.b) != c.compare: failed.append(i)
 var result := {"cases":cases.size(),"arithmetic_assertions":cases.size()*3,"failed_case_indices":failed,"oracle":"Python arbitrary precision integers, deterministic seed271126","scope":"Exact quantity arithmetic only"}
 var out := FileAccess.open(get_script().resource_path.get_base_dir().path_join("exact-count-oracle-result.json"),FileAccess.WRITE)
 out.store_string(JSON.stringify(result,"\t")+"\n")
 print(JSON.stringify(result))
 quit(0 if failed.is_empty() else 1)
