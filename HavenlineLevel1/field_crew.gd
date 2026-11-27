extends RefCounted
## The owl roost has its own tender and ownership. Earlier saves that earned
## the owl alongside their survivor keep that entitlement without new spending.
const OWL_PLOT := "owl_roost"
const OWL_MEAT := 6
const ROOST_AT := Vector3(3.15,0,8.15)
const SURVIVOR_HP := 18
const OWL_HP := 12
const SURVIVOR_REPLACEMENT_WOOD := 8

static func owns_owl(journal:Dictionary) -> bool:
	return ever_owned_owl(journal) and int(journal.get("owl_hp",OWL_HP)) > 0

static func ever_owned_owl(journal: Dictionary) -> bool:
	return journal.get("owl_legacy",false)==true or journal.get("owl_meat",0)==OWL_MEAT

static func owl_due(journal:Dictionary) -> int:
	if owns_owl(journal): return 0
	var key := "owl_replacement_meat" if ever_owned_owl(journal) else "owl_meat"
	return OWL_MEAT-int(journal.get(key,0))

static func survivor_alive(journal: Dictionary) -> bool:
	return journal.get("rescued",false) and int(journal.get("survivor_hp",SURVIVOR_HP)) > 0

static func survivor_bill(journal: Dictionary, original: int) -> int:
	return SURVIVOR_REPLACEMENT_WOOD if journal.get("rescued",false) else original

static func survivor_due(journal: Dictionary, original: int) -> int:
	if journal.get("rescued",false):
		if survivor_alive(journal): return 0
		return SURVIVOR_REPLACEMENT_WOOD-int(journal.get("survivor_replacement_wood",0))
	return original-int(journal.get("survivor_wood",0))

static func fund_owl(journal: Dictionary, amount: int) -> void:
	if not ever_owned_owl(journal):
		journal.owl_meat += amount
		return
	journal.owl_replacement_meat += amount
	if journal.owl_replacement_meat == OWL_MEAT:
		journal.owl_replacement_meat = 0
		journal.owl_replacements += 1
		journal.owl_hp = OWL_HP

static func fund_survivor(journal: Dictionary, amount: int, original: int) -> void:
	if not journal.rescued:
		journal.survivor_wood += amount
		journal.survivor_paid = journal.survivor_wood == original
		return
	journal.survivor_replacement_wood += amount
	if journal.survivor_replacement_wood == SURVIVOR_REPLACEMENT_WOOD:
		journal.survivor_replacement_wood = 0
		journal.survivor_replacements += 1
		journal.survivor_hp = SURVIVOR_HP

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
