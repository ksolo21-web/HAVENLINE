"""Detached, renderer-neutral sample for the opening furnace purchase marker.

This cannot charge a ledger, spawn objects, modify collisions, or persist.
Only a trusted future adapter can originate its inputs. Time is physics ticks.
"""
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite

OFFER = "center-hearth"
PAYMENT = {"offer": OFFER, "grant": OFFER, "typed_debit": {"wood": 3}, "revision": 1}
OPENING_SOURCES = frozenset(('wood-a', 'wood-b', 'wood-c'))
FILL_TICKS = 4
FULL_HOLD = 5
EXIT = 8
MOTION_DEADLINE = 45

def valid_receipt(value):
    return (
        type(value) is dict and value.keys() == {"offer", "grant", "typed_debit", "revision"}
        and type(value["offer"]) is str and type(value["grant"]) is str
        and type(value["revision"]) is int and type(value["typed_debit"]) is dict
        and list(value["typed_debit"].keys()) == ["wood"]
        and type(value["typed_debit"]["wood"]) is int
        and value["offer"] == value["grant"] == OFFER
        and value["revision"] == 1 and value["typed_debit"]["wood"] == 3
    )

@dataclass(frozen=True)
class ObservedMount:
    """Adapter-owned observation, not a way to create a visual or earn stock."""
    source_id: str
    native_id: int
    world_affine: tuple
    is_owned_and_visible: bool

def observed_set(observations):
    if type(observations) is not tuple or len(observations) != 3:
        return frozenset()
    for unit in observations:
        if (type(unit) is not ObservedMount or type(unit.source_id) is not str
                or type(unit.native_id) is not int or unit.native_id <= 0
                or unit.is_owned_and_visible is not True
                or type(unit.world_affine) is not tuple or len(unit.world_affine) != 12
                or any(type(v) not in (int, float) or abs(v) > 1e6 for v in unit.world_affine)
                or not all(isfinite(v) for v in unit.world_affine)):
            return frozenset()
        a,b,c,d,e,f,g,h,i = unit.world_affine[:9]
        if abs(a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g)) < 1e-12:
            return frozenset()
    ids = frozenset(unit.native_id for unit in observations)
    return ids if len(ids) == 3 and frozenset(unit.source_id for unit in observations) == OPENING_SOURCES else frozenset()

@dataclass(frozen=True)
class View:
    state: str
    visible: bool
    corners: str
    near_edge_fill: Fraction
    fill_target: Fraction
    marker_scale: Fraction
    marker_opacity: Fraction
    text: str
    # Both reflect the approved paid snapshot, never the optional plot lifecycle.
    show_committed_furnace: bool
    show_committed_camp: bool

class Marker:
    """One pose-independent purchase plot whose state never governs gameplay."""

    def __init__(self, scene_token, restored_receipt=None):
        if type(scene_token) is not str or not scene_token:
            raise ValueError("scene token required")
        if restored_receipt is not None and not valid_receipt(restored_receipt):
            raise ValueError("invalid restored receipt")
        self.scene_token = scene_token
        self._paid = restored_receipt is not None
        self._eligible_tick = None
        self._observed_ids = frozenset()
        self._arrivals = []
        self._fill_origin = Fraction(0)
        self._fill_start = 0
        self._started = None
        self._finished = None
        self._last_tick = 0
        self._expired = False

    def _valid_tick(self, tick):
        return type(tick) is int and tick >= self._last_tick

    def approach(self, tick, eligible_overlap, *, grounded, observations=()):
        """Called with a fresh authoritative-scene observation, not arbitrary UI input."""
        if (not self._valid_tick(tick) or type(eligible_overlap) is not bool
                or type(grounded) is not bool or self._paid):
            return False
        self._last_tick = tick
        self._eligible_tick = tick if eligible_overlap and grounded else None
        self._observed_ids = observed_set(observations) if self._eligible_tick is not None else frozenset()
        return True

    def publish_paid(self, tick, receipt, scene_token, *, live_commit):
        """Trusted publication after success (or restore). No purchase side effects.

        The paid state is always immediate after exact current-scene authority.
        Only local same-tick pre-commit observation of actual mounted IDs enables FX.
        """
        if (self._paid or not self._valid_tick(tick) or type(live_commit) is not bool
                or type(scene_token) is not str or scene_token != self.scene_token
                or not valid_receipt(receipt)):
            return False
        self._last_tick = tick
        self._paid = True
        if live_commit and self._eligible_tick == tick and len(self._observed_ids) == 3:
            self._started = tick
        else:
            self._observed_ids = frozenset()
        return True

    def arrive(self, tick, scene_token, receipt_revision, subject_id):
        """Called after each witnessed arrival, never directly by input or wall time."""
        if (not self._valid_tick(tick) or self._started is None or self._expired
                or tick >= self._started + MOTION_DEADLINE
                or type(scene_token) is not str or scene_token != self.scene_token or type(receipt_revision) is not int
                or receipt_revision != 1 or type(subject_id) is not int
                or subject_id not in self._observed_ids or subject_id in self._arrivals):
            return False
        self._fill_origin = self._fill_at(tick)
        self._fill_start = self._last_tick = tick
        self._arrivals.append(subject_id)
        if len(self._arrivals) == 3:
            self._finished = tick + FILL_TICKS
        return True

    def advance_to(self, tick):
        if not self._valid_tick(tick):
            return False
        self._last_tick = tick
        if self._started is not None and self._finished is None and tick >= self._started + MOTION_DEADLINE:
            self._expired = True
        return True

    def _fill_at(self, tick):
        target = Fraction(len(self._arrivals), 3)
        weight = Fraction(min(FILL_TICKS, max(0, tick - self._fill_start)), FILL_TICKS)
        return self._fill_origin + (target - self._fill_origin) * weight

    def view(self):
        if self._paid and (self._started is None or self._expired):
            return self._completed()
        if self._finished is not None and self._last_tick >= self._finished:
            elapsed = max(0, self._last_tick - self._finished - FULL_HOLD)
            if elapsed >= EXIT:
                return self._completed()
            scale = 1 - Fraction(elapsed, EXIT)
            return View("exit" if elapsed else "full_hold", True, "lime", Fraction(1), Fraction(1),
                        scale, scale, "3 WOOD", True, True)
        if self._started is not None:
            return View("paying", True, "lime", self._fill_at(self._last_tick), Fraction(len(self._arrivals), 3),
                        Fraction(1), Fraction(1), "3 WOOD", True, True)
        armed = self._eligible_tick == self._last_tick
        return View("armed" if armed else "idle", True, "lime" if armed else "white",
                    Fraction(0), Fraction(0), Fraction(1), Fraction(1), "3 WOOD", False, False)

    @staticmethod
    def _completed():
        return View("done", False, "off", Fraction(0), Fraction(0), Fraction(0), Fraction(0), "", True, True)
