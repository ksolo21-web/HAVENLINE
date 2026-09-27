"""Reference-driven T05-R03 visual game-art pad builders."""
import legacy_station_kit_v1 as legacy
PAD_IDS=("pad_build","pad_upgrade","pad_input","pad_output","pad_stock","pad_payment")

def build_ground_pads():
    source=legacy.asset_specs()
    for asset_id in PAD_IDS:
        b=source[asset_id]
        legacy.add_snow_foot(b,(2.02,.075,2.02))
        b.beveled_box("wood_light",(0,.16,.68),(1.74,.14,.14),.035)
        b.beveled_box("wood_light",(0,.16,-.68),(1.74,.14,.14),.035)
        b.beveled_box("wood",(.72,.16,0),(.14,.14,1.40),.035)
        b.beveled_box("wood",(-.72,.16,0),(.14,.14,1.40),.035)
    return {asset_id:source[asset_id] for asset_id in PAD_IDS}
