# Meshy conveyor hardware

The straight transport, quarter turn and height adapter use three separate crops of the owner's approved D01 transport sheet. Each crop preserves the materials, proportions and photographed view in the original. The image-to-3D jobs used smart-topology geometry, a 2,200-triangle request per module and Meshy N1 texturing. The three jobs together used 45 credits. [Original D01 image](https://github.com/ksolo21-web/HAVENLINE/blob/e501bea5ed9e6f8737abb5b39799cade78b22af1/Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01/selected/conveyor-transport.png) · [Inputs, Meshy IDs, original hashes and fitted hashes](Generation.json)

| Part | Generation input | Original Meshy result |
| --- | --- | --- |
| Straight | [Level rollers, empty](straight-input.png) | [Straight GLB](Generated/straight.glb) |
| Turn | [90-degree corner](corner-input.png) | [Corner GLB](Generated/corner.glb) |
| Ramp | [Height adapter](incline-input.png) | [Incline GLB](Generated/incline.glb) |

The game uses a 0.48 m nominal guarded width. The straight and height adapter retain their Meshy rollers, enamel, motors and supports. Meshy generated a wide symmetric deck on the corner. To create a usable 90-degree turn, the game asset fans that model's individual rollers around a measured radius, retains its supports and fits the straight module's matching guards and drive around the bend. The fitted meshes have 1,984 triangles for the straight, 2,318 for the incline and 3,846 for the corner. The locomotion geometry, paid dock connections and route selection are controlled in the game. [Fitted textured models](Socket-fitted-kit.jpg)
