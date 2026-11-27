"""Check Build 11 journals and copies re-saved by the previous playtest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def launch(entry, probe, directory, mode, phase):
    env = dict(os.environ, LP_NUM_THREADS="1")
    for key, subdir in (("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_CONFIG_HOME", "config")):
        env[key] = str(directory / subdir)
    command = ["godot", "--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
               *entry, "--script", str(probe), "--", "--l1-disposable-profile=" + str(directory),
               "--" + mode, "--" + phase]
    proc = subprocess.run(command, cwd=directory, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, timeout=150)
    if proc.returncode or any(tag in proc.stdout for tag in ("WARNING:", "ERROR:")):
        raise RuntimeError(proc.stdout)
    result = json.loads(next(line.removeprefix("RETURNING_CAMP ") for line in proc.stdout.splitlines()
                             if line.startswith("RETURNING_CAMP ")))
    if not all(result["checks"].values()):
        raise RuntimeError(str(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--project", type=Path)
    src.add_argument("--pack", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-project", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    entry = ["--main-pack", str(args.pack.resolve())] if args.pack else ["--path", str(args.project.resolve())]
    probe = here / "probe_returning_camp.gd"
    report = {"source": json.loads((here / "Reviewed-files.json").read_text())["commit"],
              "probe_sha256": digest(probe), "scene": "res://field_opening.tscn",
              "build11": "989edd9283148e9f712387fb937ea36038cbd9d2",
              "runner": "signed APK assets under desktop Godot" if args.pack else "source checkout",
              "profiles": {}}
    if args.pack:
        report["resource_pack_sha256"] = digest(args.pack)
    prior = ["--path", str(args.prior_project.resolve())] if args.prior_project else None
    if prior:
        report["previous_playtest"] = "2654f5019b7212968d28600cb071bf1c231c9030"
    for mode in ("custom", "snow", "kitchen"):
        fixture = here / "Fixtures" / ("Build11-" + mode + ".json")
        with tempfile.TemporaryDirectory(prefix="havenline-l1-v3-camp12-layout-", dir="/tmp") as directory:
            target = Path(directory)
            (target / "L1-DISPOSABLE").write_text("HAVENLINE-ALFRED-V3-DISPOSABLE\n")
            shutil.copyfile(fixture, target / "field-inventory-v1.json")
            previous = launch(prior, probe, target, mode, "before") if prior else None
            first, cold = [launch(entry, probe, target, mode, phase) for phase in ("first", "cold")]
            for key in ("stored", "served", "purchases", "layout", "hp", "position"):
                if first[key] != cold[key] or (previous and previous[key] != first[key]):
                    raise RuntimeError(f"{mode} changed {key} after update or restart")
            report["profiles"][mode] = {"fixture_sha256": digest(fixture), "previous": previous, "runs": [first, cold]}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print("Passed initial and cold launches for three Build 11 profiles")


if __name__ == "__main__":
    main()
