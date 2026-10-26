#!/usr/bin/env python3
"""Havenline physical Android observation bundle. Never self-certifies 60 FPS.

Requires Android Debug Bridge, an attached physical device, and a running
Havenline package. Use Android GPU Inspector / Perfetto for actual sustained
CPU/GPU frame timelines. This utility only captures reproducible raw evidence.
"""
import argparse,hashlib,json,pathlib,subprocess,time,datetime,sys
def run(args,deadline=30):
    r=subprocess.run(args,capture_output=True,text=True,timeout=deadline)
    if r.returncode:raise RuntimeError("ADB failure "+str(r.returncode)+": "+r.stderr[:600])
    return r.stdout
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--serial",required=True,help="Specific authorized physical Android serial")
    p.add_argument("--package",required=True,help="Installed Havenline Android package ID")
    p.add_argument("--out",required=True)
    p.add_argument("--observe-seconds",type=int,default=60)
    a=p.parse_args()
    if a.observe_seconds<60:raise SystemExit("Minimum 60-second sustained observation required")
    root=pathlib.Path(a.out).resolve();root.mkdir(parents=True,exist_ok=True)
    adb=["adb","-s",a.serial]
    if run(adb+["get-state"]).strip()!="device":raise SystemExit("Physical connected device required")
    props={
      "manufacturer":run(adb+["shell","getprop","ro.product.manufacturer"]).strip(),
      "model":run(adb+["shell","getprop","ro.product.model"]).strip(),
      "hardware":run(adb+["shell","getprop","ro.hardware"]).strip(),
      "build_fingerprint":run(adb+["shell","getprop","ro.build.fingerprint"]).strip(),
      "android_release":run(adb+["shell","getprop","ro.build.version.release"]).strip()
    }
    if any(x in (props["hardware"]+" "+props["model"]).lower() for x in ("goldfish","ranchu","emulator","sdk_gphone")):
        raise SystemExit("Android emulator cannot certify physical device performance")
    captured=[]
    def dump(label,cmd):
        output=run(adb+cmd,deadline=50)
        path=root/(label+".txt");path.write_text(output)
        captured.append({"label":label,"file":path.name,"sha256":hashlib.sha256(output.encode()).hexdigest()})
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    dump("gfxinfo_before",["shell","dumpsys","gfxinfo",a.package,"framestats"])
    dump("meminfo_before",["shell","dumpsys","meminfo",a.package])
    dump("thermal_before",["shell","dumpsys","thermalservice"])
    time.sleep(a.observe_seconds)
    dump("gfxinfo_after",["shell","dumpsys","gfxinfo",a.package,"framestats"])
    dump("meminfo_after",["shell","dumpsys","meminfo",a.package])
    dump("thermal_after",["shell","dumpsys","thermalservice"])
    end=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result={"schema_version":1,"task":"HAVENLINE_GLOBAL_ANDROID_OBSERVATION",
        "status":"RAW_ANDROID_CAPTURE_ONLY_NOT_60FPS_CERTIFICATION",
        "device_type":"physical_android_checked_for_emulator_signatures",
        "serial_sha256":hashlib.sha256(a.serial.encode()).hexdigest(),
        "device_metadata":props,"package":a.package,
        "start_utc":start,"end_utc":end,
        "observation_seconds_requested":a.observe_seconds,
        "profilers_required":"Perfetto or Android GPU Inspector actual CPU/GPU frame timelines required for physical C6",
        "sustained_fps":None,"p95_cpu_ms":None,"p95_gpu_ms":None,
        "owner_approval":False,"shipping_approved":False,"files":captured}
    (root/"observation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"capture_status":result["status"],"raw_files":len(captured),"output":str(root)}))
if __name__=="__main__":
    try:main()
    except (subprocess.TimeoutExpired,RuntimeError) as e:
        print(str(e),file=sys.stderr);sys.exit(1)
