"""Assertions for a future isolated native encounter runner; no encounter simulation."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

# Adapter projects its actual, observed candidate state into these fields without
# deriving a success default. Counters are cumulative within the disposable run.
UNCHANGED = (
    'encounter_id', 'animal_id', 'encounter_phase', 'cooldown', 'encounter_clock',
    'animal_health', 'player_health', 'camp_condition', 'pending_custody',
    'damage_events', 'drop_events', 'completion_events', 'exit_events',
    'reward_ledger', 'exit_progress',
)

def is_finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)

def check(evidence):
    errors = []
    before, after = (evidence.get(x) for x in ('restored_before_ticks', 'observed_after_ticks'))
    if not isinstance(before, dict) or not isinstance(after, dict):
        return ['Both native snapshots required']
    if type(evidence.get('ordinary_ticks_observed')) is not int or evidence['ordinary_ticks_observed'] < 1:
        errors.append('No native ordinary gameplay ticks observed')
    if evidence.get('in_contact_geometry_before_ticks') is not True:
        errors.append('Negative control did not start with contact geometry')
    for point, name in ((before, 'before'), (after, 'after')):
        if point.get('binding_approved') is not False or point.get('binding_active') is not False:
            errors.append(f'{name}: exact unbound/unapproved actor proof absent')
        if point.get('encounter_active') is not True or point.get('animal_active') is not True:
            errors.append(f'{name}: recoverable encounter/animal absent or not live')
        for key in ('encounter_id', 'animal_id', 'encounter_phase'):
            if not isinstance(point.get(key), str) or not point[key].strip():
                errors.append(f'{name}: missing actual {key}')
        for key in ('animal_health','player_health','camp_condition','cooldown','encounter_clock'):
            if not is_finite_number(point.get(key)):
                errors.append(f'{name}: invalid or missing observed {key}')
        for key in ('damage_events','drop_events','completion_events','exit_events'):
            if type(point.get(key)) is not int or point[key] < 0:
                errors.append(f'{name}: invalid or missing observed {key}')
        for key in ('pending_custody','reward_ledger','exit_progress'):
            if key not in point or not isinstance(point[key],dict):
                errors.append(f'{name}: actual projected {key} snapshot missing')
    if not is_finite_number(before.get('cooldown')) or before['cooldown'] != 0:
        errors.append('Hard negative control requires ready cooldown')
    for key in UNCHANGED:
        if key not in before or key not in after or before[key] != after[key]:
            errors.append(f'Unexpected change or missing state: {key}')
    return errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    steps = parser.parse_args()
    data = json.loads(steps.evidence.read_text(), parse_constant=lambda v:parser.error(f'invalid constant {v}'))
    if not isinstance(data,dict):
        parser.error('expected native evidence object')
    errors = check(data)
    print(json.dumps({'oracle_only':True,'errors':errors},indent=2))
    raise SystemExit(bool(errors))
