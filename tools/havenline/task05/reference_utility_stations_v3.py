#!/usr/bin/env python3
"""T05 R10C utility compatibility wrapper.

R10C is now implemented in the gated reference_utility_stations_v2 builder so
the existing deterministic source audit remains authoritative without weakening
any test. This wrapper preserves the already-committed R10C import path.
"""
from __future__ import annotations
import reference_utility_stations_v2 as v2

UTILITY_IDS=v2.UTILITY_IDS


def build_utility_stations():
    result=v2.build_utility_stations()
    assert tuple(sorted(result))==tuple(sorted(UTILITY_IDS))
    return result


def quality_report():
    assets=build_utility_stations()
    return {
        "asset_ids":list(UTILITY_IDS),
        "triangles":{name:asset.triangle_count() for name,asset in assets.items()},
        "materials":{name:sorted(asset.surfaces) for name,asset in assets.items()},
    }


if __name__=="__main__":
    import json
    print(json.dumps(quality_report(),indent=2,sort_keys=True))
