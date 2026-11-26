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
            contents = subprocess.check_output(["git", "-C", str(args.repo), "show", source])
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
