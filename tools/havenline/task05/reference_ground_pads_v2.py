"""Reference-driven T05-R03 visual game-art pad builders."""
import legacy_station_kit_v1 as legacy
PAD_IDS=("pad_build","pad_upgrade","pad_input","pad_output","pad_stock","pad_payment")

def build_ground_pads():
    source=legacy.asset_specs()
    source["pad_build"].beveled_box("wood_light",(0,.16,.68),(1.74,.14,.14),.035)
    return {asset_id:source[asset_id] for asset_id in PAD_IDS}
