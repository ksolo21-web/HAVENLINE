#!/usr/bin/env python3
"""T05 R10a station-family wrapper.

Keeps the R10 authored geometry and restores the camp's existing cyan cold-detail
surface as a purposeful insulated tray on the service station.
"""
from __future__ import annotations
import reference_station_families_v2 as v2

def build_station_families():
    result=v2.build_station_families()
    service=result["service_counter"]
    service.beveled_box("cyan",(.42,1.20,-.15),(.34,.07,.24),.035,rotation=(0,-.08,0))
    return result

if __name__=="__main__":
    import json
    a=build_station_families()
    print(json.dumps({"assets":list(a),"triangles":{k:v.triangle_count() for k,v in a.items()},
                      "materials":{k:sorted(v.surfaces) for k,v in a.items()}},indent=2))
