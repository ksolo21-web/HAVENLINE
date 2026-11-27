"""Extract the reviewed field from a Havenline Git checkout to a new directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile


def materialize_axe_textures(project):
    """Extract the checked-in axe donor's PNG/JPEG images referenced by the fitted tool."""
    textures = {
        "axe-meshy_normal.png": ("normal", "226b9672f0cb320d13db2aa42e8063e23e4db0714faead745b3103b4d122e248"),
        "axe-meshy_Image_0.jpg": ("Image_0", "f757749623e0abe89fd0311cb8c08d43d80b7433d9e544f3876dead649b7243f"),
        "axe-meshy_Image_1.png": ("Image_1", "7f8c7dab58e9a353a4a305c9e9016be2286abd626a9bae3bb5f48d91050dbec5"),
    }
    import_hashes = {
        "axe-meshy_Image_0.jpg": "807414e089b87d113c4e6737bb2fdfbd84550f913becebbd7646ee713c62ef56",
        "axe-meshy_Image_1.png": "d6d65371d98b618514745cb7ac316d3f40627d616065cc2932b78dd002253939",
        "axe-meshy_normal.png": "b9c3c354d55feddff1c2761a11016b2fe250bdc6fd9f4884cc8121438be32526",
    }
    tools = project / "assets" / "tools"
    donor = (tools / "axe-meshy.glb").read_bytes()
    json_length, json_tag = struct.unpack_from("<I4s", donor, 12)
    if donor[:4] != b"glTF" or json_tag != b"JSON":
        raise ValueError("Invalid axe donor GLB")
    metadata = json.loads(donor[20 : 20 + json_length])
    binary_length, binary_tag = struct.unpack_from("<I4s", donor, 20 + json_length)
    binary = memoryview(donor)[28 + json_length :]
    if binary_tag != b"BIN\0" or len(binary) != binary_length:
        raise ValueError("Invalid axe donor binary payload")
    image_views = {img["name"]: img["bufferView"] for img in metadata["images"]}
    for filename, (image_name, expected) in textures.items():
        view = metadata["bufferViews"][image_views[image_name]]
        start = view.get("byteOffset", 0)
        image = binary[start : start + view["byteLength"]]
        if view["buffer"] != 0 or hashlib.sha256(image).hexdigest() != expected:
            raise ValueError(f"Unexpected embedded image for {filename}")
        (tools / filename).write_bytes(image)
        # These images normally inherit 3-D import settings from the GLB importer.
        # Creating them ahead of their consumer also requires preserving mipmaps and map types.
        import_record = Path(__file__).resolve().parent / "Tool-texture-imports" / (filename + ".import")
        import_settings = import_record.read_bytes()
        if hashlib.sha256(import_settings).hexdigest() != import_hashes[filename]:
            raise ValueError(f"Unexpected tool texture import settings for {filename}")
        (tools / (filename + ".import")).write_bytes(import_settings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, help="Path to the existing Havenline repository")
    parser.add_argument("output", type=Path, help="New directory for the reviewed Godot project")
    parser.add_argument("--qa", action="store_true", help="Use the reviewed QA revision with the same game runtime")
    args = parser.parse_args()
    target = args.output.absolute()
    if target.exists():
        parser.error(f"Output already exists: {target}")
    resources = Path(__file__).resolve().parent
    manifest_name = "Reviewed-QA-files.json" if args.qa and (resources / "Reviewed-QA-files.json").is_file() else "Reviewed-files.json"
    manifest = json.loads((resources / manifest_name).read_text())
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
        materialize_axe_textures(project)
        shutil.copyfile(resources / "export_presets.cfg", project / "export_presets.cfg")
        (project / "export-artwork").mkdir()
        shutil.copyfile(resources / "field-icon-mono.png", project / "export-artwork/field-icon-mono.png")
        project.rename(target)
    print(f"Verified {len(manifest['files'])} files from {manifest['commit']} in {target}")


if __name__ == "__main__":
    main()
