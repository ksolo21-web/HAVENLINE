"""Detached, renderer-neutral sample for the opening furnace purchase marker.

This cannot charge a ledger, spawn objects, modify collisions, or persist.
Only a trusted future adapter can originate its inputs. Time is physics ticks.
"""
from dataclasses import dataclass
from fractions import Fraction

OFFER = "center-hearth"
PAYMENT = {"offer": OFFER, "grant": OFFER, "typed_debit": {"wood": 3}, "revision": 1}
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
class View:
    state: str
    visible: bool
    corners: str
    near_edge_fill: Fraction
    fill_target: Fraction
    marker_scale: Fraction
    marker_opacity: Fraction
    text: str
    # Reflect an existing grant visually only. This does not authorize a grant.
    show_committed_furnace: bool

class Marker:
    """One marker for one opening scene. All reject branches leave state alone."""

    def __init__(self, scene_token, restored_receipt=None):
        if type(scene_token) is not str or not scene_token:
            raise ValueError("scene token required")
        if restored_receipt is not None and not valid_receipt(restored_receipt):
            raise ValueError("invalid restored receipt")
        self.scene_token = scene_token
        self._paid = restored_receipt is not None
        self._hover = False
        self._order = ()
        self._arrivals = []
        self._fill_origin = Fraction(0)
        self._fill_start = 0
        self._started = None
        self._finished = None
        self._last_tick = 0
        self._expired = False

    def _valid_tick(self, tick):
        return type(tick) is int and tick >= self._last_tick

    def approach(self, tick, eligible_overlap):
        """The caller computes eligibility and overlap from actual game state."""
        if not self._valid_tick(tick) or type(eligible_overlap) is not bool or self._paid:
            return False
        self._last_tick = tick
        self._hover = eligible_overlap
        return True

    def begin_after_live_commit(self, tick, receipt, scene_token, actual_arrival_ids):
        """Trusted success only, after payment. IDs are existing presentation subjects."""
        IDs = actual_arrival_ids
        if (not self._valid_tick(tick) or self._paid or not self._hover
                or type(scene_token) is not str or scene_token != self.scene_token or not valid_receipt(receipt)
                or type(IDs) is not tuple or len(IDs) != 3
                or any(type(ident) is not str or not ident for ident in IDs)
                or len(set(IDs)) != 3):
            return False
        self._last_tick = self._started = tick
        self._paid = True
        self._order = IDs
        return True

    def arrive(self, tick, scene_token, receipt_revision, subject_id):
        """Called after each witnessed arrival, never directly by input or wall time."""
        if (not self._valid_tick(tick) or self._started is None or self._expired
                or tick >= self._started + MOTION_DEADLINE
                or type(scene_token) is not str or scene_token != self.scene_token or type(receipt_revision) is not int
                or receipt_revision != 1 or len(self._arrivals) >= len(self._order)
                or type(subject_id) is not str or subject_id != self._order[len(self._arrivals)]):
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
                        scale, scale, "3 WOOD", elapsed > 0)
        if self._started is not None:
            return View("paying", True, "lime", self._fill_at(self._last_tick), Fraction(len(self._arrivals), 3),
                        Fraction(1), Fraction(1), "3 WOOD", False)
        return View("armed" if self._hover else "idle", True, "lime" if self._hover else "white",
                    Fraction(0), Fraction(0), Fraction(1), Fraction(1), "3 WOOD", False)

    @staticmethod
    def _completed():
        return View("done", False, "off", Fraction(0), Fraction(0), Fraction(0), Fraction(0), "", True)
