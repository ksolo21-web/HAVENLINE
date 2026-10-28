extends Node3D
## T05 R28 isolated WHITE CHIMNEY SMOKE geometry/motion trial.
## Candidate-only visual effect. Attach to imported cooker in Godot preview.
## This script is not wired into shipping scenes or approved reference art.
const PUFF_COUNT := 10
var billboards: Array[MeshInstance3D] = []
var surfaces: Array[StandardMaterial3D] = []

func _ready() -> void:
    var texture := _build_soft_cloud_texture()
    for i in range(PUFF_COUNT):
        var puff := MeshInstance3D.new()
        puff.name = "R28 smoke puff %02d" % i
        var plane := QuadMesh.new()
        plane.size = Vector2(0.48, 0.48)
        puff.mesh = plane
        var mat := StandardMaterial3D.new()
        mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
        mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
        mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
        mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
        mat.albedo_texture = texture
        mat.albedo_color = Color(0.92, 0.955, 0.98, 0.55)
        puff.material_override = mat
        add_child(puff)
        billboards.append(puff)
        surfaces.append(mat)
    set_motion_time(0.9)

func _build_soft_cloud_texture() -> ImageTexture:
    var side := 96
    var pixels := Image.create(side, side, false, Image.FORMAT_RGBA8)
    for y in range(side):
        for x in range(side):
            var dx := (float(x) + 0.5) / float(side) * 2.0 - 1.0
            var dy := (float(y) + 0.5) / float(side) * 2.0 - 1.0
            var angle := atan2(dy, dx)
            var radius := sqrt(dx * dx + dy * dy)
            var wave := 0.062 * sin(5.0 * angle + 3.1 * radius) + 0.04 * cos(9.0 * angle - 2.4 * radius)
            var edge := clampf((0.93 + wave - radius) / 0.26, 0.0, 1.0)
            var softness := edge * edge * (3.0 - 2.0 * edge)
            pixels.set_pixel(x, y, Color(0.93, 0.97, 1.0, softness * 0.72))
    return ImageTexture.create_from_image(pixels)

func set_motion_time(seconds: float) -> void:
    # Cyclic smoke: stagger release, lift, grow, wind drift, then softly fade.
    for i in range(billboards.size()):
        var age := fposmod(seconds * 0.28 + float(i) / float(PUFF_COUNT), 1.0)
        var horizontal := 0.05 * sin(seconds * 1.3 + float(i) * 1.21) + 0.22 * age * age
        var depth_drift := 0.035 * cos(seconds * 1.7 + float(i) * 0.81)
        billboards[i].position = Vector3(-0.20 + horizontal,
                                        2.40 + age * 0.88,
                                        0.06 + depth_drift)
        var swelling := lerpf(0.52, 1.36, age)
        billboards[i].scale = Vector3.ONE * swelling
        var ramp := clampf(age / 0.15, 0.0, 1.0)
        var fade := pow(1.0 - age, 1.45)
        surfaces[i].albedo_color = Color(0.92, 0.955, 0.98, 0.64 * ramp * fade)
