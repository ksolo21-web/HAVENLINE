extends "res://previews/integrated_opening.gd"
## Never referenced by either playable scene. This test-only adapter consumes the
## unchanged V8 receipt/store in a fresh disposable process, not actual saves.
const OPT_IN := "--l1-enable-combined-cold-fixture"
const COMBINED_PREFIX := "havenline-l1-v3-combined-"
const COMBINED_SENTINEL := "COMBINED-COLD-FIXTURE"
const COMBINED_MARK := "HAVENLINE-COMBINED-COLD-V1\n"
var profile := ""

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.count(OPT_IN) != 1:
		return
	var candidate := ""
	for arg in args:
		if arg.begins_with(Save.FLAG):
			candidate = arg.trim_prefix(Save.FLAG)
	if not candidate.get_file().begins_with(COMBINED_PREFIX) or not save.configure(args):
		return
	var directory := DirAccess.open(candidate)
	if directory == null or not directory.file_exists(COMBINED_SENTINEL) or directory.is_link(COMBINED_SENTINEL):
		return
	var marker := FileAccess.open(candidate.path_join(COMBINED_SENTINEL), FileAccess.READ)
	if marker == null or marker.get_length() != COMBINED_MARK.length() or marker.get_as_text() != COMBINED_MARK:
		return
	profile = candidate
	var recovered: Error = save.load_into(ledger)
	if recovered != OK and recovered != ERR_FILE_NOT_FOUND:
		persist_blocked = true
		persist_error = "Test-only disposable receipt rejected."
		return
	persist_requested = true
	# The accepted combined ready path publishes this one recovered ledger. A
	# failed load above cannot instantiate or publish a fake fresh camp.
	super._ready()
