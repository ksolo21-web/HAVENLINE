from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from owned_queue import *

EVIDENCE=Path(os.environ.get("EXACT_NATIVE_IDENTITY_EVIDENCE","../hvn-l1-starter-wood-native-identity-result-v1"))
RAW=Path(os.environ.get("EXACT_PRIVATE_OBSERVER_LOG","../hvn-l1-starter-identity-private-host-v1/native-native-starter-v1/observed.log"))
ORIGIN=reopen_exact_origins(EVIDENCE,RAW)
KEY=bytes(range(32))   # Portable fictitious signing adapter; never production private data.
E=object()
PROFILE="e"*64
LATEST=max(d.pickup_tick for d in ORIGIN.debts)+4
FORBIDDEN={j for d in ORIGIN.debts for j in (d.source_node,d.source_asset_node)}|{ORIGIN.actor}
# No live IDs are invented for pickup sources. Arbitrary mount IDs below are tests only.
ids=[x for x in range(40001,40040) if x not in FORBIDDEN][:6]
FIT=tuple(Mount(ORIGIN.generation,ORIGIN.actor,d.source,d.ordinal,d.source_node,LATEST,ids[i],ids[i+3],
                  ORIGIN.actor,CROWN_SHA,PROFILE,"individual-crown","portable-fixture",True)
          for i,d in enumerate(ORIGIN.debts))
PAID=Paid(ORIGIN.generation,ORIGIN.actor,"center-hearth","center-hearth",1,3,EXACT_ORDER,LATEST+1,True,False)

def sign(m,key=KEY):
    return sign_payload(key,m)
def q(scope="portable-fixture",restored=False):
    return Queue(ORIGIN,E,KEY,MountPolicy(scope,PROFILE if scope=="portable-fixture" else None),restored)
def fresh(t=PAID.observed_tick):
    return tuple((m,sign(m)) for m in [replace(r,observed_tick=t) for r in FIT])
def attach_all():
    c=q()
    for m in FIT:
        assert c.attach(E,m,sign(m))
    return c

class TestOwned(unittest.TestCase):
    def test_exact_native_ground_origins_and_no_native_carry_currently(self):
        self.assertEqual(tuple(d.source for d in ORIGIN.debts),EXACT_ORDER)
        self.assertEqual(len(FORBIDDEN),7)
        self.assertEqual(q().counts["pending"],3)
        current=q("current-baseline")
        self.assertFalse(current.attach(E,FIT[0],sign(FIT[0])))
        self.assertFalse(current.green_fill_is_authorized())
        self.assertEqual(current.release_for_optional_effect(E,PAID,fresh()),())

    def test_ground_replay_wrong_source_native_log_cannot_mint_visual_debt(self):
        with TemporaryDirectory() as d:
            path=Path(d)/"different.log"
            path.write_bytes(RAW.read_bytes()[:0]+b"forged record")
            with self.assertRaisesRegex(ValueError,"wrong original native log"):
                reopen_exact_origins(EVIDENCE,path)

    def test_duplicate_and_any_visible_anchor_id_collision_rejected(self):
        a=q();m=FIT[0]
        self.assertTrue(a.attach(E,m,sign(m)))
        self.assertFalse(a.attach(E,m,sign(m)))
        for failed in (replace(FIT[1],direct_anchor_id=m.direct_anchor_id),
               replace(FIT[1],current_visible_native_id=m.current_visible_native_id),
               replace(FIT[1],current_visible_native_id=m.direct_anchor_id),
               replace(FIT[1],direct_anchor_id=m.current_visible_native_id)):
            self.assertFalse(a.attach(E,failed,sign(failed)))
        self.assertEqual(a.counts["attached"],1)

    def test_signer_and_wrong_scene_origin_parent_ghost_and_grouped_visual_rejected(self):
        a=q();m=FIT[0]
        self.assertFalse(a.attach(object(),m,sign(m)))
        self.assertFalse(a.attach(E,m,sign(m,b"y"*32)))
        self.assertFalse(a.attach(E,m,sign(FIT[1])))
        for wrong in (replace(m,generation="other"),replace(m,representation="legacy-bundle"),
                      replace(m,parent_actor_id=ORIGIN.actor+1),replace(m,originating_source_node=ORIGIN.debts[1].source_node),
                      replace(m,source_ordinal=2),replace(m,observed_asset_is_grounded_owned_visible=False),
                      replace(m,approved_mount_profile_sha="0"*64),
                      replace(m,current_visible_native_id=ORIGIN.debts[1].source_asset_node),
                      replace(m,direct_anchor_id=ORIGIN.actor),replace(m,observed_tick=ORIGIN.debts[0].pickup_tick-1)):
            self.assertFalse(a.attach(E,wrong,sign(wrong)))
        self.assertEqual(a.counts["attached"],0)

    def test_cancel_burns_detached_visual_attempt_and_restore_does_not_replay(self):
        a=attach_all()
        self.assertFalse(a.cancel(object()))
        self.assertTrue(a.cancel(E))
        self.assertFalse(a.cancel(E))
        self.assertFalse(a.attach(E,FIT[0],sign(FIT[0])))
        self.assertEqual(a.release_for_optional_effect(E,PAID,fresh()),())
        restored=q(restored=True)
        self.assertFalse(restored.attach(E,FIT[0],sign(FIT[0])))
        self.assertEqual(restored.release_for_optional_effect(E,PAID,fresh()),())

    def test_wrong_receipt_failed_save_wrong_order_and_cold_restore_no_effect(self):
        a=attach_all()
        for wrong in (replace(PAID,from_restore=True),replace(PAID,wood_debit=2),replace(PAID,grant="rear_storage"),
                      replace(PAID,live_save_and_publication_verified=False),replace(PAID,collected_in_order=("wood-a","wood-b","wood-c"))):
            self.assertEqual(a.release_for_optional_effect(E,wrong,fresh()),())
            self.assertFalse(a.counts["released_once"])

    def test_mounted_once_same_ids_refresh_cannot_replace_late_or_smuggle(self):
        a=attach_all()
        early=fresh(PAID.observed_tick-1)
        self.assertEqual(a.release_for_optional_effect(E,PAID,early),())
        late=fresh(PAID.observed_tick+1)
        self.assertEqual(a.release_for_optional_effect(E,PAID,late),())
        current=fresh()
        self.assertEqual(a.release_for_optional_effect(E,PAID,current[::-1]),())
        replacement=replace(current[0][0],current_visible_native_id=ids[-1]+8)
        self.assertEqual(a.release_for_optional_effect(E,PAID,((replacement,sign(replacement)),*current[1:])),())
        self.assertEqual(a.release_for_optional_effect(E,PAID,current),tuple(m.current_visible_native_id for m in FIT))
        self.assertFalse(a.green_fill_is_authorized())
        self.assertEqual(a.release_for_optional_effect(E,PAID,current),())
        self.assertFalse(a.attach(E,FIT[0],sign(FIT[0])))

    def test_missing_future_mounted_piece_cannot_release_even_valid_commit(self):
        a=q()
        for m in FIT[:2]:
            self.assertTrue(a.attach(E,m,sign(m)))
        self.assertEqual(a.release_for_optional_effect(E,PAID,fresh()),())
        self.assertFalse(a.green_fill_is_authorized())

if __name__=="__main__":
    unittest.main()
