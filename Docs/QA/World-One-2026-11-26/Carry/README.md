# Carry visibility

On `e978a44b1b112bb598f9ec1724b3616ec80e6970`, large loads keep the top packet on screen as the player turns and the camera follows or zooms. Each material retains its own lane and original packet mesh. The rack shows the number of physical packets that fit its camera view and its 9.8 m world-height limit. The HUD and saved inventory continue to count every unit. The only changed gameplay script since `34df87a8` is `field_carry.gd`.

Godot tested portrait and landscape at 1× and 2×, with mixed loads of 3, 12, 37, 42 and 1,000,000 of *each* material. Four actor facings and small movements gave 80 poses. The smallest measured top margin was **10.1% of the viewport**. Normal zoom showed every packet at 3 and 12 units. At full pinch, an overflowing lane displayed fewer packets as needed. An idle camera-only zoom reused the allocated meshes. [Projection cases and receipts](Pack-and-flights.json) · [Frozen regression output](qa_field_pack_bounds.log)

An overflow pickup landed on the upper visible wood mesh after zoom changed in flight. The outgoing deposit and purchase each took one physical unit from the upper visible mesh. Reloading preserved all 61 earned tokens as 59 carried, one stored and one paid. The existing 720-flight shelf regression and complete storehouse purchase test also passed on this commit. [Inventory](qa_field_inventory.log) · [Shelf transfers](qa_field_stock_limits.log) · [Storehouse purchase](qa_field_purchase_scene.log)

[Native camera comparison with 32 images](Native-camera/README.md)

The comparison sheet shows the approved reference beside the former and revised high loads. A separate native-renderer matrix records the physical mesh clearance in landscape and portrait. [Reference and gameplay comparison](Source-and-high-load-comparison.jpg) · [Native-camera review](Native-camera/README.md) · [Current paid route and save](../Storage/Earned-route-e978a44b.json)
