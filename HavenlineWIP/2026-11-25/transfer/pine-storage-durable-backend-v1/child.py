#!/usr/bin/env python3
"""A child created by the exact harness; no arbitrary sleeps or PIDs."""
from backend import Store,sha,record
import json,os,sys
def emit(**d):
    print(json.dumps(dict(pid=os.getpid(),**d),sort_keys=True),flush=True)
def brief(s):return [s.harvested,s.carried,s.stored,s.deposited]
with Store(sys.argv[1]) as st:
    mode=sys.argv[2]
    if mode=="hold-lock":
        with st.writer():
            emit(event="held")
            assert sys.stdin.readline()=="release\n"
        emit(event="released")
        sys.exit(0)
    x=st.boot()
    emit(event="boot",epoch=x.epoch,identity=x.expected,state=brief(x.state))
    if mode in ("read","next"):
        if mode=="next":
            t=x.stage_trusted("harvest",x.state.harvested+1,source="wood-a",first_paid=True,settled=True)
            assert t is not None and x.publish(t)=="committed"
            emit(event="new",state=brief(x.state),epoch=x.epoch,identity=x.expected)
    elif mode=="crash":
        phase,kind=sys.argv[3:]
        def stop(here):
            if here!=phase:return
            epoch,s=record(st.read("fixture.primary"))
            emit(event=here,epoch=epoch,primary_identity=sha(st.read("fixture.primary")),durable_state=brief(s),live_state=brief(x.state))
            # Parent will issue SIGKILL only after reading this exact child PID.
            assert sys.stdin.readline()=="release\n"
        if kind=="deposit":t=x.stage_trusted("deposit",1,sink=x.test_sink)
        elif kind=="harvest":t=x.stage_trusted("harvest",x.state.harvested+1,source="wood-a",first_paid=True,settled=True)
        else:raise ValueError("kind")
        assert t is not None
        assert x.publish(t,stop)=="committed"
    else:raise ValueError("mode")
