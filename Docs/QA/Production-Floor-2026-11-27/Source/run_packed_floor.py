"""Replay the seven-meal line on three launches using the signed APK's exact assets.

Run with --apk FILE --pack FILE if a desktop Godot resource ZIP already exists.
Without --pack, reconstruct the resource ZIP from the supplied APK. Use --project
instead of --apk to rehearse on an imported source checkout. Python 3.11+.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZIP_STORED, ZipFile

SOURCE = Path(__file__).resolve().parent
PROBE = SOURCE / "check_packed_floor.gd"
FIXTURE = SOURCE / "Fixtures" / "Serial-food-fresh-purchase.json"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check_pack(apk_path, pack_path, create):
    with ZipFile(apk_path) as apk:
        resources = {}
        for member in apk.infolist():
            if member.is_dir() or not member.filename.startswith("assets/"):
                continue
            name = member.filename.removeprefix("assets/")
            if name in resources:
                raise ValueError(f"Duplicate Godot asset {name}")
            resources[name] = member
        if create:
            with ZipFile(pack_path, "w", ZIP_STORED) as destination:
                for name, member in resources.items():
                    with apk.open(member) as src, destination.open(name, "w") as dst:
                        shutil.copyfileobj(src, dst)
        with ZipFile(pack_path) as packed:
            if sorted(resources) != sorted(packed.namelist()):
                raise ValueError("The APK resource names do not match the desktop pack")
            for name, member in resources.items():
                with apk.open(member) as a, packed.open(name) as b:
                    if hashlib.file_digest(a, "sha256").digest() != hashlib.file_digest(b, "sha256").digest():
                        raise ValueError(f"Resource mismatch in {name}")
    return len(resources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apk", type=Path)
    mode.add_argument("--project", type=Path)
    parser.add_argument("--pack", type=Path, help="Existing desktop pack containing exactly the APK assets")
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"scene": "res://field_opening.tscn", "engine": subprocess.check_output([args.godot, "--version"], text=True).strip(),
              "probe_sha256": digest(PROBE), "fixture": FIXTURE.name, "fixture_sha256": digest(FIXTURE),
              "runs": []}
    with tempfile.TemporaryDirectory(prefix="havenline-l1-v3-floor-", dir="/tmp") as name:
        profile = Path(name)
        (profile / "L1-DISPOSABLE").write_text("HAVENLINE-ALFRED-V3-DISPOSABLE\n")
        shutil.copyfile(FIXTURE, profile / "field-inventory-v1.json")
        if args.apk:
            apk = args.apk.resolve()
            pack = args.pack.resolve() if args.pack else profile / "same-android-assets.zip"
            entries = check_pack(apk, pack, create=args.pack is None)
            run_args = ["--main-pack", str(pack)]
            report.update(platform="Desktop Godot playing a byte-identical copy of the signed Android APK resources.",
                          apk=apk.name, apk_sha256=digest(apk), verified_resource_entries=entries)
            receipt_path = SOURCE.parent / "Verification" / "Android.json"
            if receipt_path.exists():
                receipt = json.loads(receipt_path.read_text())
                if report["apk_sha256"] != receipt["sha256"] or not receipt["signed_v2"]:
                    raise ValueError("APK differs from the signed Android release receipt")
                report.update(source=receipt["source"], certificate_sha256=receipt["certificate_sha256"])
        else:
            run_args = ["--path", str(args.project.resolve())]
            report["platform"] = "Unexported desktop project rehearsal."
        env = dict(os.environ, XDG_DATA_HOME=str(profile / "data"), XDG_CONFIG_HOME=str(profile / "config"),
                   XDG_CACHE_HOME=str(profile / "cache"), LP_NUM_THREADS="1")
        for phase in ("stock", "serve", "reopen"):
            command = [args.godot, "--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
                       *run_args, "--script", str(PROBE), "--", f"--l1-disposable-profile={profile}", phase]
            proc = subprocess.run(command, cwd=profile, env=env, text=True, capture_output=True, timeout=300)
            output = proc.stdout + proc.stderr
            if proc.returncode or "ERROR:" in output or "WARNING:" in output:
                raise RuntimeError(output)
            row = json.loads(next(line[13:] for line in output.splitlines() if line.startswith("PACKED_FLOOR ")))
            if not row["checks"] or not all(row["checks"].values()):
                raise ValueError(row)
            row["resulting_journal_sha256"] = digest(profile / "field-inventory-v1.json")
            report["runs"].append(row)
            print(f"{phase}: {len(row['checks'])} passed", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
