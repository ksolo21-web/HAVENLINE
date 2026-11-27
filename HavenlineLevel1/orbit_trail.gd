extends MeshInstance3D
## Tapered white 57-degree blade afterimage sampled in the weapon's horizontal plane.
const SEGMENTS := 16
var ribbon := ImmediateMesh.new()
var finish := ShaderMaterial.new()
func _init() -> void:
	mesh = ribbon
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var shader_source := Shader.new()
	shader_source.code = "shader_type spatial; render_mode unshaded,cull_disabled,depth_draw_never; void fragment(){float soft=1.0-smoothstep(0.38,1.0,abs(UV.y*2.0-1.0)); ALBEDO=vec3(1.0); ALPHA=soft*pow(1.0-UV.x,0.53)*0.91;}"
	finish.shader = shader_source

func redraw(positions: PackedVector3Array, radial_axes: PackedVector3Array, width: float, planes := PackedVector3Array()) -> void:
	ribbon.clear_surfaces()
	ribbon.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP, finish)
	for i in range(positions.size()):
		var progress := float(i)/SEGMENTS
		var half_width := width * .5 * pow(1.0-progress,.61)
		ribbon.surface_set_uv(Vector2(progress,0)); ribbon.surface_add_vertex(_inside(positions[i]-radial_axes[i]*half_width,planes))
		ribbon.surface_set_uv(Vector2(progress,1)); ribbon.surface_add_vertex(_inside(positions[i]+radial_axes[i]*half_width,planes))
	ribbon.surface_end()

func _inside(p: Vector3, planes: PackedVector3Array) -> Vector3:
	for plane in planes:
		var n := Vector3(plane.x,0,plane.y)
		var d := n.dot(p)-plane.z
		if d<0.: p-=n*d
	return p
