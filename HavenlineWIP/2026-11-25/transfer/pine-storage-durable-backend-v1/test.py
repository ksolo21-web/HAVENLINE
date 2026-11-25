#!/usr/bin/env python3
from backend import *
from oracle import RECEIPT,STARTERS
import signal,subprocess,tempfile
os.umask(0o077)
assert sha((P.parent/"hvn-l1-paid-pine-renewal-v1"/"renewal.patch").read_bytes())=="e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd"
prior=P.parent/"hvn-l1-paid-pine-independent-v1.ILpLHK"
m=(prior/"SHA256SUMS").read_bytes()
assert sha(m)=="f4ca5871f9d30c8be7c6a186a96ed8ef9d5912042336b70e6ee0d03c75b8393b"
for row in m.decode().splitlines():
    dig,name=row.split(None,1);assert sha((prior/name.strip()).read_bytes())==dig
n=0
def ck(x):
    global n
    assert x
    n+=1
def snap(s):return [s.harvested,s.carried,s.stored,s.deposited]
def legacy(renewals=0,paid=True,ids=STARTERS):
    x=dict(version=2 if renewals else 1,collected=list(ids),stock={"wood":renewals if paid else len(ids)},receipt=RECEIPT if paid else {})
    if renewals:x["pine_occurrences"]=renewals
    return wire(x)
def seed(directory,doc):
    p=Path(directory)
    (p/"fixture.marker").write_bytes(MARK)
    (p/"fixture.primary").write_bytes(doc)
def child(prof,*args):
    own_env={"PATH":os.environ["PATH"],"PYTHONDONTWRITEBYTECODE":"1","HOME":prof,"TMPDIR":prof}
    return subprocess.Popen([sys.executable,str(Path(__file__).with_name("child.py").resolve()),prof,*args],
       stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=own_env)
def read(p,event):
    import selectors,time
    data=bytearray(); end=time.monotonic()+3
    with selectors.DefaultSelector() as sel:
        sel.register(p.stdout,selectors.EVENT_READ)
        while not data.endswith(b"\n"):
            room=end-time.monotonic()
            assert room>0 and sel.select(room),f"child {event} timeout"
            x=os.read(p.stdout.fileno(),1)
            assert x and len(data)<8192
            data.extend(x)
    row=json.loads(data);ck(row["pid"]==p.pid and row["event"]==event)
    assert p.poll() is None or event in ("released","boot","new")
    return row
def cleanup(p,kill=False):
    if p.poll() is None and kill:p.kill()  # exact subprocess Popen identity only
    out,err=p.communicate(timeout=5)
    ck(p.returncode==(-signal.SIGKILL if kill else 0) and not err)

compat=[]
for raw in (legacy(0,False,("wood-c",)),legacy(),legacy(2)):
    with tempfile.TemporaryDirectory(prefix=PREFIX,dir="/tmp") as p:
        seed(p,raw)
        with Store(p) as st:
            e,s=record(st.read("fixture.primary"));ck(e==0 and st.read("fixture.primary")==raw)
            x=st.boot();ck(x.epoch==1 and x.state==s and record(st.read("fixture.primary"))==(1,s))
            ck(s.v3()["receipt"] in ({},RECEIPT))
            compat.append(snap(s))

# True process supersession, same-process stale ticket identity, lock refusal.
with tempfile.TemporaryDirectory(prefix=PREFIX,dir="/tmp") as p:
    seed(p,legacy(2))
    with Store(p) as st:
        a=st.boot(); old=a.stage_trusted("harvest",3,source="wood-a",first_paid=True,settled=True);ck(old is not None)
        q=child(p,"read");r=read(q,"boot");cleanup(q);baseline=st.read("fixture.primary")
        ck(r["state"]==[2,2,0,0] and r["epoch"]==a.epoch+1)
        ck(a.publish(old)=="denied-stale" and st.read("fixture.primary")==baseline)
        new=st.boot()
        shadow=Session(st,new.epoch,new.state,new.expected)
        shadow_token=shadow.stage_trusted("harvest",3,source="wood-a",first_paid=True,settled=True)
        ck(shadow_token is not None)
        ck(new.stage_trusted("deposit",2,sink=new.test_sink) is None)
        ck(new.stage_trusted("deposit",1,sink=object()) is None)
        ck(new.stage_trusted("deposit",1,sink=new.test_sink,material="food") is None)
        ck(new.stage_trusted("deposit",1,sink=new.test_sink,units=True) is None)
        ck(new.stage_trusted("harvest",3,source="wood-b",first_paid=True,settled=True) is None)
        ck(new.stage_trusted("harvest",3,source="wood-a",first_paid=False,settled=True) is None)
        ck(new.stage_trusted("harvest",3,source="wood-a",first_paid=True,settled=False) is None)
        intent=new.stage_trusted("deposit",1,sink=new.test_sink)
        ck(intent is not None and new.publish(old)=="denied-token" and new.publish({"id":1})=="denied-token")
        q=child(p,"hold-lock");read(q,"held")
        hold=st.read("fixture.primary");ck(new.publish(intent)=="denied-held-lock")
        ck(st.read("fixture.primary")==hold)
        q.stdin.write("release\n");q.stdin.flush();read(q,"released");cleanup(q)
        ck(new.publish(intent)=="committed"); ck(new.publish(intent)=="denied-token")
        dep_raw=st.read("fixture.primary")
        ck(record(dep_raw)[0]==shadow.epoch and sha(dep_raw)!=shadow.expected)
        ck(shadow.publish(shadow_token)=="denied-stale" and st.read("fixture.primary")==dep_raw)
        ck(snap(new.state)==[2,1,1,1] and new.state.v3()["receipt"]==RECEIPT)
        next0=new.stage_trusted("harvest",3,source="wood-a",first_paid=True,settled=True)
        ck(next0 is not None and new.publish(intent)=="denied-token" and new.publish(next0)=="committed")
        ck(new.stage_trusted("deposit",1,sink=new.test_sink) is None)
        ck(snap(new.state)==[3,2,1,1])

# Distinct, real OS process termination while waiting at harness-controlled barriers.
# Primary identity at each barrier is recorded before killing its specific child.
crash={}
for kind in ("deposit","harvest"):
    for phase in ("before","after"):
        with tempfile.TemporaryDirectory(prefix=PREFIX,dir="/tmp") as p:
            seed(p,legacy(2))
            q=child(p,"crash",phase,kind)
            try:
                started=read(q,"boot")
                at=read(q,phase)
                ck(q.poll() is None)
                expected=[2,2,0,0] if phase=="before" else ([2,1,1,1] if kind=="deposit" else [3,3,0,0])
                ck(at["live_state"]==started["state"]==[2,2,0,0] and at["durable_state"]==expected)
                ck((started["identity"]==at["primary_identity"])==(phase=="before"))
            finally:
                cleanup(q,kill=True)
            with Store(p) as st:
                ck(sha(st.read("fixture.primary"))==at["primary_identity"])
                ck(record(st.read("fixture.primary"))[1].v3()["receipt"]==RECEIPT)
                if phase=="before":
                    e,staged=record(st.read("fixture.stage"));ck(staged!=record(st.read("fixture.primary"))[1])
                else:
                    ck(not Path(p,"fixture.stage").exists())
            # A new interpreter boots, abandons any old stage, and for the
            # gold route performs the distinct next genuine trusted cut.
            advance=phase=="after" and kind=="deposit"
            q=child(p,"next" if advance else "read")
            reopened=read(q,"boot")
            if advance:later=read(q,"new")
            cleanup(q)
            ck(reopened["epoch"]==at["epoch"]+1 and reopened["state"]==expected)
            with Store(p) as st:
                e,s=record(st.read("fixture.primary"));ck(s.v3()["receipt"]==RECEIPT and not Path(p,"fixture.stage").exists())
                ck(snap(s)==([3,2,1,1] if advance else expected))
            crash[kind+"_"+phase]={"before_sigkill_durable":expected,"after_new_interpreter_boot":reopened["state"],
          "post_recovery_new_cut":later["state"] if advance else None,"old_process_publication_absent":True}
print(json.dumps({"checked":n,"existing_exact_pine_independent_manifest":sha(m),"trusted_fixture_legacy_v1_v2_read":compat,
 "process_crash_controls":crash,"engine_or_game_receiver_used":False,"filesystem_only_disposable":True,
 "one_fresh_process_epoch_guarded":True,"same_epoch_stale_snapshot_denied":True,"same_process_stale_token_denied":True,"live_writer_contention_denied":True,
 "filesystem_power_loss_claim":False},indent=2,sort_keys=True))
