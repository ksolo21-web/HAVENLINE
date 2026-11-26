"""Controller-minted scratch only. --guard-only never starts an engine."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

BASE=Path(__file__).resolve().parent
ENGINE="/opt/godot/4.7.2/Godot_v4.7.2-stable_linux.x86_64"
TMP=Path("/tmp")
NAME="opening-v3.json"
MARKS={"L1-DISPOSABLE":b"HAVENLINE-ALFRED-V3-DISPOSABLE\n"}
PREFIX="havenline-l1-v3-pine-fork-"
ALLOW_OBJ=re.compile(r"^WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|brace_back|snow|metal|rope|rope_dark)' is ignored in PBR$")
def sha(b):return hashlib.sha256(b).hexdigest()
class Denied(Exception):pass
def need(x,msg):
    if not x: raise Denied(msg)
def identity(p):
    s=p.lstat()
    return s.st_dev,s.st_ino
def full_snapshot(p):
    children=sorted(p.iterdir())
    result={}
    for q in children:
        s=q.lstat()
        need(stat.S_ISREG(s.st_mode) and s.st_nlink==1, "nonregular-or-shared-child")
        result[q.name]={"mode":stat.S_IMODE(s.st_mode),"sha256":sha(q.read_bytes()),"inode":s.st_ino,"size":s.st_size}
    return {"dir_identity":identity(p),"dir_mode":stat.S_IMODE(p.stat().st_mode),"files":result}
def valid_payload(raw, version):
    j=json.loads(raw)
    need(set(j)=={"version","payload","sha256"} and j["version"]==1 and sha(j["payload"].encode())==j["sha256"],"invalid-envelope")
    q=json.loads(j["payload"])
    need(set(q)==({"version","collected","stock","receipt"}|({"pine_occurrences"} if version==2 else set())),"invalid-schema")
    need(q["version"]==version and q["collected"]==["wood-b","wood-c","wood-a"] and q["stock"]=={"wood":version-1},"wrong-authority")
    need(q["receipt"]=={"offer":"center-hearth","grant":"center-hearth","revision":1,"typed_debit":{"wood":3}},"wrong-receipt")
    if version==2: need(q["pine_occurrences"]==1,"wrong-occurrence")
    return q

class Trial:
    def __init__(self, holder):
        self.holder=holder
        self.held=[Path(tempfile.mkdtemp(prefix=p, dir=TMP)) for p in ("havenline-l1-v3-combined-pine-fork-old-",PREFIX+"new-")]
        self.a,self.b=self.held
        self.v=holder/"backup-not-routable"
        self.v.mkdir(mode=0o700)
        self.roles={"old":(self.a,identity(self.a)),"new":(self.b,identity(self.b))}
        self.rejects={}
        for role,(p,i) in self.roles.items():
            for n,data in self.marks(role).items(): (p/n).write_bytes(data)
    def marks(self, role):
        m={**MARKS,"PINE-FORK-ROLE":f"PINE-FORK-{role.upper()}-V1\n".encode()}
        if role=="old":m["COMBINED-COLD-FIXTURE"]=b"HAVENLINE-COMBINED-COLD-V1\n"
        return m
    def close(self):
        for p in self.held:
            if p.exists() and not p.is_symlink(): shutil.rmtree(p)
        if self.v.exists(): self.v.chmod(0o700)
    def route(self, role, offered, state, expected_sha=None):
        need(role in self.roles,"unknown-role")
        p,dp=self.roles[role]
        if not offered.is_absolute() or offered.parent!=TMP or offered.is_symlink():raise Denied("not-direct-nonlink-tmp")
        need(offered==p,"wrong-minted-role-path")
        d=offered.lstat()
        need(stat.S_ISDIR(d.st_mode) and identity(offered)==dp,"directory-identity-changed")
        snap=full_snapshot(offered)
        full=self.marks(role)
        wanted=set(full)|({NAME} if state is not None else set())
        need(set(snap["files"])==wanted,"unexpected-children")
        for n,b in full.items():need(snap["files"][n]["sha256"]==sha(b),"wrong-owner-marker")
        if state is not None:
            raw=(offered/NAME).read_bytes()
            valid_payload(raw,state)
            if expected_sha is not None: need(sha(raw)==expected_sha,"wrong-provenance-digest")
        return "--l1-disposable-profile="+str(offered)
    def rejected(self,name,code,fn):
        try:fn()
        except Denied as e:
            need(str(e)==code,f"{name}:wrong-denial:{e}")
            self.rejects[name]=code
        else:raise AssertionError("wrong acceptance: "+name)
    def exercise(self):
        self.rejected("old-to-candidate","wrong-minted-role-path",lambda:self.route("new",self.a,None))
        self.rejected("candidate-to-old","wrong-minted-role-path",lambda:self.route("old",self.b,None))
        self.rejected("backup-as-candidate","not-direct-nonlink-tmp",lambda:self.route("new",self.v,None))
        self.rejected("backup-as-old","not-direct-nonlink-tmp",lambda:self.route("old",self.v,None))
        alias=self.b.with_name(self.b.name+"-alias")
        alias.symlink_to(self.b,target_is_directory=True)
        try:self.rejected("same-role-symlink-alias","not-direct-nonlink-tmp",lambda:self.route("new",alias,None))
        finally:alias.unlink()
        clone=Path(tempfile.mkdtemp(prefix=PREFIX+"new-mock-",dir=TMP))
        self.held.append(clone)
        for n,b in self.marks("new").items(): (clone/n).write_bytes(b)
        self.rejected("different-inode-even-with-valid-marker","wrong-minted-role-path",lambda:self.route("new",clone,None))
        wrong=self.b/"PINE-FORK-ROLE"
        known=wrong.read_bytes()
        wrong.write_bytes(b"PINE-FORK-OLD-V1\n")
        try:self.rejected("roles-swapped-at-same-path","wrong-owner-marker",lambda:self.route("new",self.b,None))
        finally:wrong.write_bytes(known)
        # A local scratch link test only; never link one admitted profile to another.
        dummy=self.b/"link-canary"
        dummy.write_bytes(b"guard prelaunch only")
        try:
            os.link(dummy,self.b/"extra-hardlink")
            self.rejected("hardlink-child","nonregular-or-shared-child",lambda:self.route("new",self.b,None))
        finally:
            (self.b/"extra-hardlink").unlink(missing_ok=True)
            dummy.unlink()
        # Exact prelaunch directory identity matters even if restored name+contents.
        moved=self.b.with_name(self.b.name+"-held")
        self.b.rename(moved)
        self.b.mkdir(mode=0o700)
        try:
            for n,b in self.marks("new").items(): (self.b/n).write_bytes(b)
            self.rejected("minted-path-but-replaced-directory","directory-identity-changed",lambda:self.route("new",self.b,None))
        finally:
            shutil.rmtree(self.b)
            moved.rename(self.b)
        self.route("old",self.a,None)
        self.route("new",self.b,None)
    def seed(self, raw):
        self.route("new",self.b,None)
        valid_payload(raw,1)
        snap=full_snapshot(self.b)
        fd, temp=tempfile.mkstemp(prefix=".seed-v1-",dir=self.b)
        temp=Path(temp)
        try:
            with os.fdopen(fd,"wb") as file:
                file.write(raw); file.flush(); os.fsync(file.fileno())
            need(temp.read_bytes()==raw and not (self.b/NAME).exists(),"bad-seed-readback")
            # Hard-link in own B to an initially absent name, then remove temp:
            # no existing primary can be replaced, and final nlink is one.
            os.link(temp,self.b/NAME,follow_symlinks=False)
        finally:temp.unlink()
        need((self.b/NAME).read_bytes()==raw,"seed-byte-readback")
        self.route("new",self.b,1,sha(raw))
        return snap

def output(t, command, project, files, importing=False):
    iso=t.holder/("env-"+command)
    iso.mkdir(mode=0o700)
    env=dict(os.environ)
    for e in ("HOME","XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME","XDG_STATE_HOME","XDG_RUNTIME_DIR","TMPDIR"):
        d=iso/e;d.mkdir(mode=0o700);env[e]=str(d)
    r=subprocess.run([ENGINE,"--headless","--path",str(project),*files],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
    log=r.stdout.decode("utf-8",errors="replace")
    (t.holder.parent/(command+".log")).write_text(log)
    need(r.returncode==0 and re.search(r"^Godot Engine v4\.7\.2\.stable\.official\.",log,re.M),f"{command}:engine-exit-{r.returncode}")
    warnings=[x for x in log.splitlines() if re.search(r"ERROR:|WARNING:|^FAIL |Parse Error",x,re.I)]
    if importing:
        need(len(warnings)==18 and all(ALLOW_OBJ.fullmatch(x) for x in warnings),f"{command}:import-diagnostics")
    else:need(not warnings,f"{command}:runtime-diagnostics")
    return log

def native(t, out):
    need(Path(ENGINE).is_file(),"required-engine-missing")
    s=BASE/"staged"
    manifest=s/"content.sha256"
    subprocess.run(["sha256sum","-c","--status",manifest],cwd=s,check=True)
    for d in ("old","new","read-only-old"):shutil.copytree(s/d,t.holder/d)
    old=t.holder/"old"; new=t.holder/"new/HavenlineLevel1"; r=t.holder/"read-only-old"
    output(t,"old-import",old,["--editor","--import","--quit"],True)
    output(t,"new-import",new,["--editor","--import","--quit"],True)
    old_log=output(t,"old-generate",old,["--fixed-fps","60","--script","res://tests/test_integrated_disposable_opening.gd","--",t.route("old",t.a,None),"--l1-enable-combined-cold-fixture","--phase=write"])
    count_old=int(re.search(r"^combined cold fixture checks=(\d+) failures=0$",old_log,re.M)[1])
    t.route("old",t.a,1)
    a=full_snapshot(t.a)
    unchanged=(t.a/NAME).read_bytes()
    digest=sha(unchanged)
    backup=t.v/NAME
    with backup.open("xb") as f:f.write(unchanged);f.flush();os.fsync(f.fileno())
    backup.chmod(0o400);t.v.chmod(0o500)
    need(backup.read_bytes()==unchanged and identity(backup)!=identity(t.a/NAME),"backup-copy-readback")
    v=full_snapshot(t.v)
    def original():
        need(full_snapshot(t.a)==a and full_snapshot(t.v)==v and backup.read_bytes()==unchanged,"old-or-backup-mutated")
    original()
    t.seed(backup.read_bytes())
    need((t.b/NAME).read_bytes()==unchanged and identity(t.b/NAME)!=identity(backup) and identity(t.b/NAME)!=identity(t.a/NAME),"candidate-must-own-separate-copy")
    t.rejected("wrong-b-digest","wrong-provenance-digest",lambda:t.route("new",t.b,1,"f"*64))
    assert t.route("new",t.b,1,digest)
    original()
    earn=output(t,"new-earn",new,["--fixed-fps","60","--script","res://tests/hvn_pine_profile_fork.gd","--",t.route("new",t.b,1,digest),"--hvn-pine-fork=earn"])
    n_earn=int(re.search(r"^PINE_FORK_CANDIDATE checks=(\d+) failures=0$",earn,re.M)[1])
    original()
    v2=(t.b/NAME).read_bytes();valid_payload(v2,2);v2h=sha(v2)
    marked_b=full_snapshot(t.b)
    cold=output(t,"new-cold",new,["--fixed-fps","60","--script","res://tests/hvn_pine_profile_fork.gd","--",t.route("new",t.b,2,v2h),"--hvn-pine-fork=cold"])
    n_cold=int(re.search(r"^PINE_FORK_CANDIDATE checks=(\d+) failures=0$",cold,re.M)[1])
    original()
    need(full_snapshot(t.b)==marked_b,"cold-mutated-b")
    t.rejected("upgraded-b-rejected-by-old-router","wrong-minted-role-path",lambda:t.route("old",t.b,2,v2h))
    old_read=output(t,"old-read-a",r,["--script","res://old_read.gd","--",t.route("old",t.a,1,digest),"--hvn-pine-fork-old-read"])
    need("PINE_FORK_OLD_READ preserved_paid_v1=true" in old_read,"old-a-positive-control")
    original()
    need(full_snapshot(t.b)==marked_b,"old-read-mutated-b")
    subprocess.run(["sha256sum","-c","--status",manifest],cwd=t.holder,check=True)
    subprocess.run(["sha256sum","-c","--status",manifest],cwd=s,check=True)
    need(not list(t.holder.rglob("opening-v3.*"))==[], "backup-lost")
    all_intended=[p for p in t.holder.rglob("opening-v3.*")]
    need(all_intended==[backup],"unexpected-save-path")
    result={"stage":"actual native separate-profile scratch fork","source":"11c14a1c41971067c7dc97db69375f720a408f68",
        "author_patch":"e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd",
        "checks": {"old_writer":count_old,"new_earn":n_earn,"new_cold":n_cold,"old_read_preserved_a":1},
        "a_original_v1_read_unchanged":True,"backup_v_verified_unchanged":True,"b_copied_v1_byte_for_byte":True,"b_cold_v2_once":True,
        "guard_explicit_denials_before_launch":t.rejects,"state_hashes":{"a_preserved_paid_v1_sha256":digest,"v_backup_sha256":sha(backup.read_bytes()),"b_upgraded_v2_sha256":v2h},
        "no_cross_role_launch":True,"no_raw_profiles_in_result":True,"release_or_production_rollback":False}
    (out/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    need(len(sys.argv)==2 and sys.argv[1] in ("--guard-only","--root-granted-functional-lease"),"explicit-test-only-mode")
    native_mode=sys.argv[1]=="--root-granted-functional-lease"
    os.umask(0o077)
    if native_mode:
        lock=open("/tmp/havenline-godot-headless.lock","a+b")
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ps=subprocess.check_output(["ps","-u",str(os.getuid()),"-o","comm="],text=True)
        need(not any(re.match(r"(godot|blender)",x.strip(),re.I) for x in ps.splitlines()),"native-engine-present")
    out=Path(tempfile.mkdtemp(prefix="run.",dir=BASE)) if native_mode else None
    with tempfile.TemporaryDirectory(prefix="hvn-pine-profile-fork-controller-",dir=out if out else TMP) as h:
        trial=Trial(Path(h))
        try:
            trial.exercise()
            if native_mode: native(trial,out)
            else: print(json.dumps({"no_engine":True,"guard_explicit_denials_before_launch":trial.rejects},sort_keys=True))
        finally:trial.close()
