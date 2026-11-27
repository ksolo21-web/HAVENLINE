extends RefCounted
## The owl roost has its own tender and ownership. Earlier saves that earned
## the owl alongside their survivor keep that entitlement without new spending.
const OWL_PLOT := "owl_roost"
const OWL_MEAT := 6
const ROOST_AT := Vector3(3.15,0,8.15)

static func owns_owl(journal:Dictionary) -> bool:
	return journal.get("owl_legacy",false)==true or journal.get("owl_meat",0)==OWL_MEAT

static func owl_due(journal:Dictionary) -> int:
	return 0 if owns_owl(journal) else OWL_MEAT-int(journal.get("owl_meat",0))

static func migrate(previous:Variant) -> Variant:
	if not previous is Dictionary:return null
	var state:Dictionary=previous.duplicate(true)
	state.owl_legacy=state.get("survivor_paid",false)==true
	state.owl_meat=0
	return state

static func valid(journal:Dictionary, paid_order:Array) -> bool:
	if not journal.get("owl_legacy") is bool:return false
	var meat:Variant=journal.get("owl_meat")
	if not (meat is int or meat is float) or not is_finite(float(meat)) or meat!=int(meat) or meat<0 or meat>OWL_MEAT:return false
	if journal.owl_legacy and (not journal.get("survivor_paid",false) or meat!=0):return false
	return (not journal.owl_legacy and meat==0) or "center_hearth" in paid_order
