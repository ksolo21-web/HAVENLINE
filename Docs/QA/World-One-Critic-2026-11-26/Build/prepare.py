"""Extract the reviewed field from a Havenline Git checkout to a new directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, help="Path to the existing Havenline repository")
    parser.add_argument("output", type=Path, help="New directory for the reviewed Godot project")
    args = parser.parse_args()
    target = args.output.absolute()
    if target.exists():
        parser.error(f"Output already exists: {target}")
    resources = Path(__file__).resolve().parent
    manifest = json.loads((resources / "Reviewed-files.json").read_text())
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".havenline-export-", dir=target.parent) as staging:
        project = Path(staging) / "project"
        project.mkdir()
        for name, expected in sorted(manifest["files"].items()):
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Invalid source path {name}")
            source = f"{manifest['commit']}:HavenlineLevel1/{name}"
            git = ["git", "-C", str(args.repo)]
            if name == "assets/studio/hearth_trial_02.glb" and subprocess.run(git + ["cat-file", "-e", source], stderr=subprocess.DEVNULL).returncode:
                prefix = "HavenlineLevel1/assets/studio/parts"
                parts = subprocess.check_output(git + ["ls-tree", "-r", "--name-only", manifest["commit"], prefix], text=True).splitlines()
                chunks = sorted(p for p in parts if Path(p).name.startswith("hearth_trial_02.part"))
                contents = b"".join(subprocess.check_output(git + ["show", manifest["commit"] + ":" + p]) for p in chunks)
            else:
                contents = subprocess.check_output(git + ["show", source])
            if hashlib.sha256(contents).hexdigest() != expected:
                raise ValueError(f"Source digest mismatch for {name}")
            dest = project / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(contents)
        shutil.copyfile(resources / "export_presets.cfg", project / "export_presets.cfg")
        (project / "export-artwork").mkdir()
        shutil.copyfile(resources / "field-icon-mono.png", project / "export-artwork/field-icon-mono.png")
        project.rename(target)
    print(f"Verified {len(manifest['files'])} files from {manifest['commit']} in {target}")


if __name__ == "__main__":
    main()
