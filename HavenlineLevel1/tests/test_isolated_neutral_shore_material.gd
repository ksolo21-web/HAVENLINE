extends SceneTree
## Opt-in resource probe: no rendered claims, scene nodes, physics or gameplay.
const NeutralSnow = preload("res://materials/neutral_shore_snow.tres")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_check(current_scene == null, "probe does not boot the default scene")
	_check(NeutralSnow is ShaderMaterial, "neutral snow resource type")
	var snow := NeutralSnow as ShaderMaterial
	_check(snow.shader != null, "shader resource is available")
	_check(snow.shader.resource_path == "res://materials/neutral_shore_snow.gdshader", "isolated shader resource identity")
	_check(snow.shader.get_mode() == Shader.MODE_SPATIAL, "spatial terrain material")
	_check(is_equal_approx(float(snow.get_shader_parameter("snow_roughness")), 0.95), "dry snow matte")
	_check(is_equal_approx(float(snow.get_shader_parameter("shore_roughness")), 0.89), "shore matte")
	var palette: Color = snow.get_shader_parameter("shore_color")
	_check(palette.r < palette.g and palette.g < palette.b, "restrained cool shore, no brown floor")
	print(JSON.stringify({"suite":"neutral_shore_material_only", "checks":checks, "failures":failures,
		"live_terrain_bound":false, "pixel_output_tested":false}))
	for label in failures:
		push_error(label)
	quit(0 if failures.is_empty() else 1)

func _check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
