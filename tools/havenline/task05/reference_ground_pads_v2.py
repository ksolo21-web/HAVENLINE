"""Reference-driven T05-R03 physical camp platform builders."""
from __future__ import annotations
import legacy_station_kit_v1 as legacy

PAD_IDS=("pad_build","pad_upgrade","pad_input","pad_output","pad_stock","pad_payment")

def build_ground_pads():
    """Build six constructed visual pads; implementation is expanded in the next source commit."""
    legacy_assets=legacy.asset_specs()
    return {asset_id:legacy_assets[asset_id] for asset_id in PAD_IDS}
