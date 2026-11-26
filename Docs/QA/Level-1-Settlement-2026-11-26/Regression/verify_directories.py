"""Open both native app directories under one test-only XDG home and compare saved bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

def main():
    parser = argparse.ArgumentParser()
    for name in ("old", "new", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    probe = Path(__file__).resolve().with_name("native-directory.gd")
    rows = []
    with tempfile.TemporaryDirectory(prefix="havenline-l1-native-dir-") as temp:
        root = Path(temp)
        env = dict(os.environ, XDG_DATA_HOME=str(root / "data"),XDG_CACHE_HOME=str(root / "cache"),
                   XDG_CONFIG_HOME=str(root / "config"),HAVENLINE_QA_PRIVATE_XDG=str(root / "data"),LP_NUM_THREADS="1")
        before = {}
        for name, project, mode in [("old",args.old,"write"),("new",args.new,"write"),("old",args.old,"read"),("new",args.new,"read")]:
            command = ["godot","--headless","--audio-driver","Dummy","--fixed-fps","60","--path",str(project),
                       "--script",str(probe),"--","--directory-"+mode]
            if name=="old":
                command.append("--old-store")
            result = subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
            log = args.output / (name+"-"+mode+".log")
            log.write_text(result.stdout)
            assert result.returncode==0 and all(word not in result.stdout for word in ("ERROR:","WARNING:")),log
            row = next(json.loads(line.split(" ",1)[1]) for line in result.stdout.splitlines() if line.startswith("NATIVE_DIRECTORY "))
            assert row["passed"] and row["expected_native_directory"]
            file = root/"data"/row["app_folder"]/"world-one"/"field-inventory-v1.json"
            assert file.exists()
            if mode=="write":
                before[row["app_folder"]] = hashlib.sha256(file.read_bytes()).hexdigest()
            for folder, digest in before.items():
                # A game may update its own position on close. The sibling's bytes must never move.
                if folder!=row["app_folder"]:
                    assert hashlib.sha256((root/"data"/folder/"world-one"/file.name).read_bytes()).hexdigest()==digest
            before[row["app_folder"]] = hashlib.sha256(file.read_bytes()).hexdigest()
            rows.append({"launch":name+"-"+mode,"result":row,"log":log.name,"sha256":hashlib.sha256(log.read_bytes()).hexdigest()})
        assert len(before)==2
    (args.output/"Directory-results.json").write_text(json.dumps({"passed":True,"private_xdg":True,"launches":rows},indent=2)+"\n")
if __name__=="__main__":
    main()
