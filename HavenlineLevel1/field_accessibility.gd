extends RefCounted
## User preferences are separate from expedition and camp progress.
const PATH := "user://field-accessibility.cfg"
const OPTIONS := {"large_ui":false,"reduced_motion":false,"captions":false,"right_stick":false}
const CAPTIONS := {
	"raid_warning":"Raid approaching",
	"raid_started":"Raid at the camp",
	"raid_site_broken":"A camp structure broke",
	"raid_repelled":"Raid repelled",
	"raid_site_repaired":"Camp structure repaired",
	"boss_arrival":"A larger wolf has arrived",
	"player_hurt":"You took damage",
	"player_fall":"Returning to safety",
	"reset":"Returned to safety at full health",
	"purchase":"Purchase complete"
}
var values: Dictionary = OPTIONS.duplicate()

func load_preferences() -> void:
	var config := ConfigFile.new()
	if config.load(PATH)!=OK: return
	for key: String in OPTIONS:
		var value: Variant = config.get_value("accessibility",key,OPTIONS[key])
		if value is bool: values[key]=value

func toggle(key: String) -> Error:
	if not OPTIONS.has(key): return ERR_INVALID_PARAMETER
	values[key]=not values[key]
	var config := ConfigFile.new()
	for option: String in OPTIONS:
		config.set_value("accessibility",option,values[option])
	var result := config.save(PATH)
	if result!=OK: values[key]=not values[key]
	return result
