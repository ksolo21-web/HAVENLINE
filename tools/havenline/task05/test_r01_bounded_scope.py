"""Exercise trusted T03 routing in real Git repositories, without an engine."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_r01_v4_scope as scope


class BoundedR01ScopeTests(unittest.TestCase):
    allowed={'HavenlineGodot/assets/stations_v2/hearth_vessel.glb'}

    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo=Path(self.directory.name)
        self.raw=scope.git('show','f74a84a2a288ab3d3935fba7a6cb9b975c2df239:'+scope.BOUNDARY_REQUEST)
        self.git('init');self.git('config','user.name','Bounded scope test')
        self.git('config','user.email','test@example.invalid')
        (self.repo/'baseline').write_text('baseline')
        self.git('add','.');self.git('commit','-m','Base without authority')
        self.base=self.git('rev-parse','HEAD')
        p=self.repo/scope.BOUNDARY_REQUEST;p.parent.mkdir(parents=True);p.write_bytes(self.raw)
        self.git('add','.');self.git('commit','-m','Trusted owner authority')
        self.trusted=self.git('rev-parse','HEAD')
        (self.repo/'candidate').write_text('candidate')
        self.git('add','.');self.git('commit','-m','Candidate')
        self.head=self.git('rev-parse','HEAD')

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL,text=True).strip()

    def verify(self,changed=None,integration=None,head=None):
        if changed is None:changed=self.allowed|scope.BOUNDARY_GAME_PATHS
        with patch.object(scope,'ROOT',self.repo):
            return scope.verify_changed_scope(changed,self.allowed,head or self.head,integration)

    def test_historical_exact_scope_needs_no_new_authority(self):
        self.assertIsNone(self.verify(self.allowed))

    def test_exact_trusted_route_preserves_acceptance_gap(self):
        proof=self.verify(integration=self.trusted)
        self.assertEqual(set(proof['changed_paths']),scope.BOUNDARY_GAME_PATHS)
        self.assertFalse(proof['mechanical_or_visual_acceptance_claimed'])

    def test_extras_without_explicit_trusted_head_fail(self):
        with self.assertRaises(AssertionError):self.verify()

    def test_unknown_path_even_with_valid_grant_fails(self):
        with self.assertRaises(AssertionError):self.verify(self.allowed|scope.BOUNDARY_GAME_PATHS|{'HavenlineGodot/scripts/main.gd'},self.trusted)

    def test_incomplete_routed_delta_fails(self):
        with self.assertRaises(AssertionError):self.verify(self.allowed|{next(iter(scope.BOUNDARY_GAME_PATHS))},self.trusted)

    def test_missing_historical_r01_path_fails(self):
        with self.assertRaises(AssertionError):self.verify(scope.BOUNDARY_GAME_PATHS,self.trusted)

    def test_candidate_local_grant_is_not_authority(self):
        with self.assertRaises(subprocess.CalledProcessError):self.verify(integration=self.base)

    def test_nonancestor_authority_fails(self):
        self.git('checkout','--detach',self.base)
        (self.repo/'unrelated').write_text('independent branch')
        self.git('add','.');self.git('commit','-m','Nonancestor authority')
        with self.assertRaises(AssertionError):self.verify(integration=self.git('rev-parse','HEAD'))

    def test_changed_owner_record_fails_identity_pin(self):
        (self.repo/scope.BOUNDARY_REQUEST).write_bytes(self.raw+b'\n')
        self.git('add','.');self.git('commit','-m','Changed request')
        changed=self.git('rev-parse','HEAD')
        with self.assertRaises(AssertionError):self.verify(integration=changed,head=changed)


if __name__=='__main__':unittest.main()
