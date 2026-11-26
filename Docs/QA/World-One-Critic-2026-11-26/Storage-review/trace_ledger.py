"""Reconcile every retained change of an independently driven touch playthrough."""
import json
import pathlib
import sys
rows=exch=0
order=[]
breaches=[]
cost={
    "center_hearth":{"wood":3},"expansion_1":{"wood":3,"stone":1},"storage_wood":{"wood":2},
    "storage_stone":{"wood":2,"stone":1},"storage_meat":{"wood":2,"meat":1},"expansion_2":{"wood":3,"stone":2},
    "watchtower":{"wood":3,"stone":2},"orbit_upgrade":{"stone":2,"meat":1}
}
def check(test, row, label):
    if not test and len(breaches)<20: breaches.append([row["tick"],label])
observations=pathlib.Path(sys.argv[1])
sampled=[json.loads(line) for line in observations.open()]
changes=list(map(json.loads,(observations.parent/"receipt-changes.jsonl").open()))
rows=len(sampled)
assert [r["tick"] for r in sampled]==list(range(rows))
assert all(1<=r["state_id"]<=len(changes) and r["same_camera"] for r in sampled)
for r in changes:
    if "ledger" not in r: continue
    s=r["ledger"];exch+=1
    for kind,total in s["earned"].items():
        debited=sum(stock.get(kind,0) for stock in s["paid"].values())
        check(total==s["carried"][kind]+s["stored"][kind]+debited,r,"unbalanced "+kind)
    if s["order"]!=order:
        check(s["order"]==list(cost)[:len(s["order"])],r,"purchase order")
        check(len(s["order"])==len(order)+1,r,"chained purchase")
        order=s["order"].copy()
        name=order[-1]
        check(s["paid"][name]==cost[name],r,"recipe mismatch "+name)
    if exch==1:check(not any(s["earned"].values()),r,"nonzero fresh wallet")
report={"input":"normal touch joystick; no grants or teleports","sample_ticks":rows,"changed_balance_or_ownership_states":exch,
        "transactions":s["paid"],"earned":s["earned"],"carried":s["carried"],"stored":s["stored"],
        "order":order,"house_tier":s["tier"],"violations":breaches}
print(json.dumps(report,indent=2))
sys.exit(int(bool(breaches) or len(order)!=8 or s["tier"]!=3))
