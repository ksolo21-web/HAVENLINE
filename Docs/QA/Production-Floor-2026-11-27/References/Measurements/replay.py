"""Run the review against an imported Godot project using copies of the recorded saves."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent.parent / "Source" / "Fixtures"
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("project", type=Path)
p.add_argument("output", type=Path)
p.add_argument("--tag", default="build12")
args = p.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)

def profile(root, fixture):
    (root / "L1-DISPOSABLE").write_text("HAVENLINE-ALFRED-V3-DISPOSABLE\n")
    shutil.copy2(FIXTURES / fixture, root / "field-inventory-v1.json")

def run(script, private, log, **extra):
    env = dict(os.environ, XDG_DATA_HOME=str(private / "data"),
               XDG_CONFIG_HOME=str(private / "config"), XDG_CACHE_HOME=str(private / "cache"),
               LP_NUM_THREADS="1", **extra)
    command = ["godot", "--headless", "--path", str(args.project.resolve()), "--script",
               str(HERE / script), "--fixed-fps", "60", "--audio-driver", "Dummy",
               "--", "--l1-disposable-profile=" + str(private)]
    with log.open("w") as file:
        subprocess.run(command, env=env, stdout=file, stderr=subprocess.STDOUT, check=True)

for mode, initial_save in [("serial", "Serial-food-fresh-purchase.json"),
                           ("expanded", "Build9-raw-in-flight.json")]:
    with tempfile.TemporaryDirectory(prefix="havenline-l1-v3-review-") as temp:
        private = Path(temp)
        profile(private, initial_save)
        stem = "layout-" + args.tag + "-" + mode
        run("layout-probe.gd", private, out / (stem + ".log"),
            HL12_REF_LAYOUT=str(out / (stem + ".json")))

with tempfile.TemporaryDirectory(prefix="havenline-l1-v3-review-") as temp:
    private = Path(temp)
    profile(private, "Serial-food-fresh-purchase.json")
    for phase in ("outbound", "resume"):
        run("unattended.gd", private, out / (phase + ".log"), HL12_REVIEW_PHASE=phase)
