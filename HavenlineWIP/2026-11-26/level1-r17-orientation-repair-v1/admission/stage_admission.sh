#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
base=$(realpath -e -- "$1")
donors=$(realpath -e -- "$2")
test "$(sha256sum "$base/SHA256SUMS" | cut -d' ' -f1)" = 4049ec37b2ab0c7176593d969e286ef673950e506a2d47d8870900e72b9219a9
(cd "$base"; sha256sum -c --status SHA256SUMS)
python3 - "$donors" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1])
pins=json.loads(Path('donor-pins.json').read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(p/pins['manifest_path'])==pins['manifest_sha256']
assert set(pins['output_paths'])==set(pins['output_sha256'])=={'fence_panel.obj','gate_post.obj'}
for old,path in pins['output_paths'].items():
    assert not (p/path).is_symlink() and sha(p/path)==pins['output_sha256'][old]
PY
(cd "$base/staged/HavenlineLevel1"; sha256sum -c --status "../draw-source.sha256")
test ! -e staged
mkdir staged
cp -a "$base/staged/HavenlineLevel1" staged/
python3 - "$donors" <<'PY'
import json,shutil,sys
from pathlib import Path
p=Path(sys.argv[1])
for name,path in json.loads(Path('donor-pins.json').read_text())['output_paths'].items():
    shutil.copyfile(p/path,Path('staged/HavenlineLevel1/previews/r17_fence/assets')/name)
PY
p=staged/HavenlineLevel1
python3 -B verify_stage.py "$base/staged/HavenlineLevel1" "$p" donor-pins.json > custody.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
