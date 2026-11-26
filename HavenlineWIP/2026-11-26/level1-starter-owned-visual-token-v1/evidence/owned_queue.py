"""Detached source-debt and optional visual mount queue. No engine authority."""
from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re

SOURCE_EVIDENCE = "f40723cd3dedb1b148d450469eb025ed096e594ca859a25deb41bba50ae45473"
SOURCE_RESULT_HASH = "187a697ed53d4b71809412e847845693d7c0a48e00c127855abf70227c1e5412"
CAPTURE_HASH = "405c761d5c195fa2089fc0d53424389b6549c7f4e08dc9c825507e49b68c5fa3"
EXACT_ORDER = ("wood-b","wood-c","wood-a")
CROWN_SHA = "31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554"
OFFER="center-hearth"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()
def owned_int(j):
    return type(j) is int and j>0
def is_sha(text):
    return type(text) is str and re.fullmatch("[0-9a-f]{64}",text) is not None

@dataclass(frozen=True)
class Debt:
    source: str
    ordinal: int
    pickup_tick: int
    source_node: int
    source_asset_node: int

@dataclass(frozen=True)
class Origin:
    generation: str
    actor: int
    debts: tuple

def reopen_exact_origins(portable_evidence, private_observer_log):
    """Reopen actual source authority — accepted native log bytes only, never fabricated IDs."""
    folder=Path(portable_evidence)
    raw_result=(folder/"result.json").read_bytes()
    if digest((folder/"SHA256SUMS").read_bytes())!=SOURCE_EVIDENCE or digest(raw_result)!=SOURCE_RESULT_HASH:
        raise ValueError("wrong starter evidence manifest/result")
    evidence=json.loads(raw_result)
    raw=Path(private_observer_log).read_bytes()
    if digest(raw)!=CAPTURE_HASH or evidence.get("observer_log_sha256")!=CAPTURE_HASH:
        raise ValueError("wrong original native log")
    if evidence.get("source_ids_in_actual_commit_order")!=list(EXACT_ORDER) or not (
       evidence.get("carry_identity_established") is False and evidence.get("paid_receipt_observed") is False
    ):
        raise ValueError("wrong exact evidence status")
    s=raw.decode().splitlines()
    rows=[json.loads(l.split(" ",1)[1]) for l in s if l.startswith("STARTER_WOOD_INTAKE_COMMIT ")]
    separate=[l.removeprefix("WOOD_EXPECT_GENERATION ") for l in s if l.startswith("WOOD_EXPECT_GENERATION ")]
    if len(rows)!=3 or len(separate)!=1:
        raise ValueError("missing exact earlier measured commits")
    generation=separate[0]
    actors={r["actor_id"] for r in rows}
    if len(actors)!=1 or not owned_int(next(iter(actors))):
        raise ValueError("wrong exact native actor pool")
    ids={ident for r in rows for ident in (r["source_root_id"],r["asset_root_id"])}
    if len(ids)!=6 or not all(owned_int(j) for j in ids) or next(iter(actors)) in ids:
        raise ValueError("duplicate actual original source ID")
    before=[]
    picked=[]
    for i,row in enumerate(rows,1):
        source=EXACT_ORDER[i-1]
        if (generation!=row["generation"] or row["source"]!=source or row["ordinal"]!=i
                or row["kind"]!="wood" or row["carry_identity_established"] is not False
                or not owned_int(row["tick"])
                or row["before"]!={"version":1,"collected":before,"stock":{"wood":i-1},"receipt":{}}
                or row["after"]!={"version":1,"collected":before+[source],"stock":{"wood":i},"receipt":{}}):
            raise ValueError("wrong original typed authority/source transition")
        picked.append(Debt(source,i,row["tick"],row["source_root_id"],row["asset_root_id"]))
        before=before+[source]
    if tuple(x.pickup_tick for x in picked)!=tuple(sorted(x.pickup_tick for x in picked)):
        raise ValueError("wrong native time lineage")
    return Origin(generation,next(iter(actors)),tuple(picked))

@dataclass(frozen=True)
class Mount:
    generation: str
    actor: int
    source: str
    source_ordinal: int
    originating_source_node: int
    observed_tick: int
    current_visible_native_id: int
    direct_anchor_id: int              # unique mount/socket, not the actor/common owner
    parent_actor_id: int
    art_sha: str
    approved_mount_profile_sha: str
    representation: str
    scope: str
    observed_asset_is_grounded_owned_visible: bool

@dataclass(frozen=True)
class MountPolicy:
    scope: str                         # "portable-fixture" can never produce accept-green result
    approved_native_mount_profile_sha: str | None

@dataclass(frozen=True)
class Paid:
    generation: str
    actor: int
    offer: str
    grant: str
    revision: int
    wood_debit: int
    collected_in_order: tuple
    observed_tick: int
    live_save_and_publication_verified: bool
    from_restore: bool

def sign_payload(private_key, mount):
    if type(private_key) is not bytes or len(private_key)<32 or type(mount) is not Mount:
        raise ValueError("wrong private fixture input")
    encoded=json.dumps(asdict(mount),sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    return hmac.new(private_key,b"havenline/starter-visual-bind/v1:"+encoded,"sha256").hexdigest()

class Queue:
    """Optional visual bookkeeping; native receipt and ledger can never wait on this queue."""
    def __init__(self, origin, emitter, private_key, policy, restored=False):
        if type(origin) is not Origin or emitter is None or type(policy) is not MountPolicy or type(private_key) is not bytes or len(private_key)<32:
            raise ValueError("invalid private queue inputs")
        if type(restored) is not bool or policy.scope not in ("current-baseline","portable-fixture","future-approved-native"):
            raise ValueError("invalid proof scope")
        if policy.scope=="current-baseline" and policy.approved_native_mount_profile_sha is not None:
            raise ValueError("current baseline has no approved native mount binding")
        self.origin=origin
        self._emitter=emitter
        self._secret=private_key
        self.policy=policy
        self._debt={d.source:d for d in origin.debts}
        self._mounted={}
        self._dead=False
        self._restored=restored
        self._complete=False

    @property
    def counts(self):
        return {"pending":0 if self._dead or self._complete or self._restored else len(self._debt)-len(self._mounted),
                "attached":0 if self._dead or self._complete or self._restored else len(self._mounted),
                "cancelled":self._dead,"released_once":self._complete,"restored":self._restored}

    def _verified_mount(self, emitter, m, signature):
        p=self.policy
        if (emitter is not self._emitter or self._dead or self._complete or self._restored
                or type(m) is not Mount or not is_sha(signature) or type(m.source) is not str
                or m.source not in self._debt or p.scope=="current-baseline"
                or not is_sha(p.approved_native_mount_profile_sha)):
            return False
        try:
            if not hmac.compare_digest(sign_payload(self._secret,m),signature):
                return False
        except (TypeError,ValueError):
            return False
        d=self._debt[m.source]
        if (m.generation!=self.origin.generation or type(m.actor) is not int or m.actor!=self.origin.actor
                or type(m.parent_actor_id) is not int or m.parent_actor_id!=self.origin.actor
                or type(m.source_ordinal) is not int or m.source_ordinal!=d.ordinal
                or type(m.originating_source_node) is not int or m.originating_source_node!=d.source_node
                or not owned_int(m.observed_tick) or m.observed_tick<d.pickup_tick
                or not owned_int(m.current_visible_native_id) or not owned_int(m.direct_anchor_id)
                or m.current_visible_native_id==m.direct_anchor_id or m.art_sha!=CROWN_SHA
                or m.approved_mount_profile_sha!=p.approved_native_mount_profile_sha or m.scope!=p.scope
                or m.representation!="individual-crown" or m.observed_asset_is_grounded_owned_visible is not True):
            return False
        ground={self.origin.actor,*[j for v in self.origin.debts for j in (v.source_node,v.source_asset_node)]}
        return m.current_visible_native_id not in ground and m.direct_anchor_id not in ground

    def attach(self, emitter, m, signature):
        if not self._verified_mount(emitter,m,signature) or m.source in self._mounted:
            return False
        existing={j for v in self._mounted.values() for j in (v.current_visible_native_id,v.direct_anchor_id)}
        if m.current_visible_native_id in existing or m.direct_anchor_id in existing:
            return False
        self._mounted[m.source]=m
        return True

    def cancel(self, emitter):
        if emitter is not self._emitter or self._dead or self._complete or self._restored:
            return False
        self._dead=True
        self._mounted.clear()
        return True

    def release_for_optional_effect(self, emitter, paid, settled_view):
        """Return original IDs only with same-tick refreshed signed view; no deck/green authority."""
        if (emitter is not self._emitter or self._dead or self._complete or self._restored
                or type(paid) is not Paid or paid.generation!=self.origin.generation
                or type(paid.actor) is not int or paid.actor!=self.origin.actor
                or paid.offer!=OFFER or paid.grant!=OFFER or type(paid.revision) is not int or paid.revision!=1
                or type(paid.wood_debit) is not int or paid.wood_debit!=3
                or paid.collected_in_order!=EXACT_ORDER or not owned_int(paid.observed_tick)
                or paid.live_save_and_publication_verified is not True or paid.from_restore is not False
                or len(self._mounted)!=3 or type(settled_view) is not tuple or len(settled_view)!=3):
            return ()
        for expected,pair in zip(EXACT_ORDER,settled_view):
            if type(pair) is not tuple or len(pair)!=2:
                return ()
            m,signature=pair
            if not self._verified_mount(emitter,m,signature) or m.source!=expected or m.observed_tick!=paid.observed_tick:
                return ()
            old=self._mounted[expected]
            if m.observed_tick<old.observed_tick or (asdict(m)|{"observed_tick":old.observed_tick})!=asdict(old):
                return ()
        self._complete=True
        return tuple(self._mounted[x].current_visible_native_id for x in EXACT_ORDER)

    def green_fill_is_authorized(self):
        # This queue can never enable fill. Only a separately qualified receiver-bound actual arrival proof can.
        return False
