extends RefCounted
## Paint for generated station fittings and shader-driven field overlays.
## Imported surfaces keep their own material and texture data.
const PAINT := preload("res://assets/field_finishes/paint.gdshader")
const INK := preload("res://assets/field_finishes/ink.gdshader")
const PREVIEW := preload("res://assets/field_finishes/layout_preview.gdshader")
const FLASH := preload("res://assets/field_finishes/hit_flash.gdshader")

static func tinted(shader: Shader, pigment: Color) -> ShaderMaterial:
	var surface := ShaderMaterial.new()
	surface.shader = shader
	surface.set_shader_parameter("pigment", pigment)
	return surface

static func paint(pigment: Color, roughness: float, metalness := 0.0) -> ShaderMaterial:
	var surface := tinted(PAINT,pigment)
	surface.set_shader_parameter("roughness",roughness)
	surface.set_shader_parameter("metalness",metalness)
	return surface
