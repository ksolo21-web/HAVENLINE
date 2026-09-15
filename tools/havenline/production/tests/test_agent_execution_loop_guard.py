import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]


class AgentExecutionLoopGuardTests(unittest.TestCase):
    def test_agents_has_status_fast_path(self):
        agents = (ROOT / "AGENTS.md").read_text()
        self.assertIn("Status/continuity fast path", agents)
        self.assertIn("AGENT_EXECUTION_LOOP_GUARD.md", agents)
        self.assertIn("MUST NOT automatically trigger the full production reading order", agents)
        self.assertIn("Three consecutive retrievals", agents)

    def test_guard_has_hard_terminal_conditions(self):
        guard = (ROOT / "Docs/Production/AGENT_EXECUTION_LOOP_GUARD.md").read_text()
        for marker in [
            "ANSWERABLE",
            "CONTRADICTED",
            "BLOCKED",
            "ACTIONABLE",
            "four retrieval actions",
            "two unsuccessful retrieval attempts",
            "three consecutive retrieval actions produce no new material fact",
            "Do not rediscover the HAVENLINE repository",
            "Current authoritative repository state wins",
        ]:
            self.assertIn(marker, guard)

    def test_guard_forbids_search_chain_escalation(self):
        guard = (ROOT / "Docs/Production/AGENT_EXECUTION_LOOP_GUARD.md").read_text()
        self.assertIn("saved checkpoint -> repository search -> installed repository search -> branch search -> commit search", guard)
        self.assertIn("A no-match result means `NO_MATCH`, not \"search forever\"", guard)
        self.assertIn("QUESTION -> AUTHORITATIVE SOURCE -> TARGETED GAP CHECK (IF NEEDED) -> SYNTHESIZE -> STOP", guard)

    def test_guard_is_governance_owned(self):
        ownership = (ROOT / "Docs/Production/PATH_OWNERSHIP.json").read_text()
        self.assertIn("Docs/Production/AGENT_EXECUTION_LOOP_GUARD.md", ownership)


if __name__ == "__main__":
    unittest.main(verbosity=2)
