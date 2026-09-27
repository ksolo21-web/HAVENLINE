#!/usr/bin/env python3
"""T05 R10G station-family visual repair.

Primary visual authority:
- newest user-supplied HAVENLINE furnace render for construction/material language;
- user HAVENLINE early-camp board 18607.png for early utility silhouettes.

This pass preserves station IDs, metadata, sockets, placements, material vocabulary,
and frozen gameplay contracts while repairing the remaining weak reads in the counter/defense family:
service_counter, processing_counter and defense_platform.
"""
from __future__ import annotations
import math
import reference_station_families_v2 as v2


def _augment_service_counter(service):
    # A chunky lower storage carcass breaks the bare-table read while staying
    # inside the frozen 3.45 x 1.95 footprint.
    for z in (-.48, -.16, .16, .48):
        service.beveled_box("wood_light", (0, .55, z), (2.46, .12, .24), .035)
    service.beveled_box("blue", (0, .68, -.68), (1.62, .50, .24), .065)
    service.beveled_box("dark", (0, .69, -.815), (1.30, .31, .035), .012)
    service.beveled_box("cream", (-.34, .69, -.838), (.42, .16, .018), .006)
    service.beveled_box("orange", (.34, .69, -.838), (.42, .16, .018), .006)
    for x in (-.58, 0, .58):
        service.cylinder("yellow", (x, .69, -.865), .045, .035, 10,
                         rotation=(math.pi / 2, 0, 0))

    # Chopping-block mass and cold tray create purpose at gameplay scale.
    service.lathe("wood", (-.72, 1.18, .14),
                  [(.30, 0), (.34, .08), (.32, .22), (.29, .34)], 14)
    service.beveled_box("cream", (-.72, 1.38, .14), (.48, .075, .46), .025,
                        rotation=(0, .09, .015))
    service.beveled_box("cyan", (.42, 1.20, -.15), (.46, .09, .32), .04,
                        rotation=(0, -.08, 0))
    service.beveled_box("dark", (.90, 1.17, .22), (.56, .10, .38), .035)
    service.beveled_box("orange", (.90, 1.245, .22), (.38, .055, .25), .018)

    # Timber gantry and hanging tools give a recognizable authored silhouette
    # from front, rear and oblique views rather than a decorated slab.
    for x in (-1.30, 1.30):
        service.beveled_box("wood", (x, 1.60, .50), (.16, 1.18, .16), .045)
        service.beveled_box("blue", (x, 1.67, .50), (.21, .16, .21), .05)
    service.beveled_box("wood_light", (0, 2.14, .50), (2.78, .18, .18), .05)
    service.beveled_box("snow", (-.28, 2.245, .50), (1.46, .055, .20), .022,
                        rotation=(0, .03, .012))
    for x in (-.72, -.24, .24, .72):
        service.rod_between("metal", (x, 2.08, .50), (x, 1.72, .50), .023, 8)
        service.torus("yellow", (x, 1.68, .50), .075, .017, 10, 5,
                      rotation=(math.pi / 2, 0, 0), arc=math.pi)
    service.rod_between("metal", (-.18, 1.93, .48), (.18, 1.77, .48), .028, 8)
    return service



def _augment_processing_counter(processing):
    # Actual six-angle gameplay-scale review showed the legacy processing bench
    # reading as a bare table with a target-like disk. Turn that disk into a
    # mechanically legible saw/chop station using the user's early-camp language.
    # The existing wheel remains purposeful machinery rather than decoration.
    processing.torus("blue", (0, 1.45, -.17), .54, .050, 24, 7,
                     rotation=(math.pi / 2, 0, 0), arc=math.pi)
    for i in range(12):
        a = math.tau * float(i) / 12.0
        x = .49 * math.cos(a)
        y = 1.45 + .49 * math.sin(a)
        processing.beveled_box("metal", (x, y, -.184), (.11, .055, .045), .010,
                               rotation=(0, 0, a))

    # Substantial timber feed bed and blue guide rails make the workstation read
    # as a production tool rather than a collection of primitives.
    for z in (-.48, -.18, .12, .42):
        processing.beveled_box("wood", (0, 1.03, z), (2.78, .12, .22), .035)
    for z in (-.55, .49):
        processing.rod_between("blue", (-1.23, 1.15, z), (1.23, 1.15, z), .042, 8)
    for x in (-1.10, 1.10):
        processing.beveled_box("blue", (x, 1.34, -.05), (.16, .66, .20), .045)
        processing.beveled_box("snow", (x-.02, 1.70, -.05), (.20, .055, .23), .020,
                               rotation=(0, .05 if x < 0 else -.05, .02))

    # Clamp, workpiece and powered side box provide use-state storytelling at
    # vertical-isometric distance while keeping the frozen sockets/footprint.
    processing.rod_between("wood", (-.96, 1.17, .34), (.96, 1.17, .34), .13, 12)
    for x in (-.97, .97):
        processing.cylinder("cream", (x, 1.17, .34), .10, .035, 10,
                            rotation=(0, 0, math.pi / 2))
    processing.beveled_box("metal", (-.88, 1.36, -.42), (.38, .42, .42), .075)
    processing.beveled_box("blue", (-.88, 1.39, -.64), (.44, .34, .10), .035)
    processing.cylinder("orange", (-.88, 1.39, -.705), .11, .07, 12,
                        rotation=(math.pi / 2, 0, 0))
    processing.rod_between("metal", (.70, 1.37, -.40), (1.15, 1.72, -.40), .035, 8)
    processing.torus("yellow", (1.16, 1.74, -.40), .12, .026, 12, 6,
                     rotation=(math.pi / 2, 0, 0))
    processing.beveled_box("orange", (.92, .62, -.69), (.48, .12, .30), .035,
                           rotation=(0, 0, -.08))
    return processing

def _augment_defense_platform(platform):
    # Snow-capped palisade corner posts tie the platform into the user's
    # boundary language and improve the silhouette without moving gameplay.
    for x, z, h in (
        (-1.20, -1.08, 1.05), (1.20, -1.08, .94),
        (-1.20, 1.08, .92), (1.20, 1.08, 1.02),
    ):
        platform.cylinder("wood_light", (x, 1.56 + h * .5, z), .115, h, 9,
                          top_radius=.035)
        platform.cylinder("snow", (x - .018, 1.615 + h, z + .012),
                          .085, .11, 9, top_radius=.012)

    # Cross-braced blue rails make the raised deck read as engineered Havenline
    # construction instead of a square timber frame.
    platform.rod_between("blue", (-1.22, 1.45, -1.10), (1.22, 1.78, -1.10), .055, 9)
    platform.rod_between("blue", (-1.22, 1.78, -1.10), (1.22, 1.45, -1.10), .055, 9)
    platform.rod_between("wood_light", (-1.18, 1.38, 1.08), (1.18, 1.72, 1.08), .050, 9)

    # Layered central guard station with directional sighting rail, windlass-like
    # side hardware and an asymmetric snow load. This replaces the old stack of
    # concentric cylinders while retaining the same central interaction area.
    platform.beveled_box("dark", (0, 1.55, 0), (.92, .18, .76), .075,
                         rotation=(0, math.pi / 4, 0))
    platform.beveled_box("metal", (0, 1.68, -.06), (.40, .16, 1.34), .055)
    platform.rod_between("wood_light", (-.78, 1.79, -.23), (.78, 1.79, -.23), .080, 10)
    platform.rod_between("blue", (-.66, 1.81, -.24), (0, 1.73, .24), .055, 9)
    platform.rod_between("blue", (.66, 1.81, -.24), (0, 1.73, .24), .055, 9)
    platform.rod_between("metal", (0, 1.83, -.92), (0, 1.83, .66), .048, 10)
    platform.beveled_box("orange", (0, 1.83, -.88), (.22, .12, .22), .045)
    for x in (-.38, .38):
        platform.cylinder("yellow", (x, 1.70, .22), .105, .13, 12,
                          rotation=(0, 0, math.pi / 2))
        platform.rod_between("orange", (x, 1.69, .18), (x, 1.47, .43), .026, 8)
    platform.beveled_box("snow", (-.22, 1.93, .20), (.56, .055, .38), .022,
                         rotation=(0, .10, .015))
    return platform


def build_station_families():
    result = v2.build_station_families()
    result["service_counter"] = _augment_service_counter(result["service_counter"])
    result["processing_counter"] = _augment_processing_counter(result["processing_counter"])
    result["defense_platform"] = _augment_defense_platform(result["defense_platform"])
    assert tuple(sorted(result)) == tuple(sorted(v2.STATION_IDS))
    # Fail closed if visual geometry exceeds the frozen placement footprint.
    for asset_id, builder in result.items():
        footprint = v2.legacy.METADATA[asset_id][0]
        xs = [p[0] for surface in builder.surfaces.values() for p in surface.positions]
        zs = [p[2] for surface in builder.surfaces.values() for p in surface.positions]
        assert max(xs) - min(xs) <= float(footprint[0]) + .03, (asset_id, "footprint_x")
        assert max(zs) - min(zs) <= float(footprint[1]) + .03, (asset_id, "footprint_z")
    return result


if __name__ == "__main__":
    import json
    assets = build_station_families()
    print(json.dumps({
        "assets": list(assets),
        "triangles": {k: v.triangle_count() for k, v in assets.items()},
        "materials": {k: sorted(v.surfaces) for k, v in assets.items()},
    }, indent=2))
