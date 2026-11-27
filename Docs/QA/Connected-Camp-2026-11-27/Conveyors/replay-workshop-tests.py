"""Run native paid-sale recovery, overlapping plaza handoffs and loaded forester walks."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
CASES = [
    ("Before-customer-two.json", "qa_conveyor_cash_retry", [("--lock",), ("--retry",)]),
    ("Build9-settled.json", "qa_workshop_floor_access", [("--walk-forester",)]),
    ("Build9-settled.json", "qa_workshop_floor_access", [()]),
    ("Build8-paid-workshops.json", "qa_workshop_floor_access", [()]),
]


def replay(project, fixture, script, launches):
    with tempfile.TemporaryDirectory(prefix="havenline-l1-v3-replay-") as directory:
        profile = Path(directory)
        (profile / "L1-DISPOSABLE").write_text("HAVENLINE-ALFRED-V3-DISPOSABLE\n")
        shutil.copyfile(HERE / "Fixtures" / fixture, profile / "field-inventory-v1.json")
        env = dict(os.environ, XDG_DATA_HOME=str(profile / "data"),
                   XDG_CACHE_HOME=str(profile / "cache"),
                   XDG_CONFIG_HOME=str(profile / "config"), LP_NUM_THREADS="1")
        for flags in launches:
            print(f"{fixture} | {script} {' '.join(flags)}", flush=True)
            subprocess.run([
                "godot", "--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
                "--path", str(project), "--script", f"res://tests/{script}.gd", "--",
                f"--l1-disposable-profile={directory}", *flags,
            ], check=True, env=env)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("godot_project", type=Path)
    args = parser.parse_args()
    for item in CASES:
        replay(args.godot_project.resolve(), *item)
