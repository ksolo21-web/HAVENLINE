# Independent native fuel review — repaired candidate

**Approved for the standalone fuel/custody/grant component only: 9.8/10.** All mandatory scoped checks pass. This is not a live-game or balance approval.

## Actual verification

- 16/16 source/result identities matched the refreshed manifest before copying the candidate.
- 107/107 legacy checks reran.
- 80/80 builder fuel checks reran.
- 32/32 independently authored adversarial checks passed, including 100 Python big-integer multiplication oracle cases.
- All three runs exited 0 with zero stderr.

The previously failing valid-identifier collision is repaired by an unambiguous canonical tuple. The exact original reproduction now passes. The rejected R1 source/report/results remain preserved.

The independent checks cover paid tank-versus-spending allocation, active and paused clock edges, previously denied windows after refilling, frame partition invariance, huge exact clocks, grant replay and payload conflict, stale-observation rollback, explicit save authority, fractional wreck estates, replacement recovery and exterior loss.

## Practical limits

The bound adapter still owns truthful current time, source/receipt/contact/geometry observations and complete-world persistence. The physical world must apply a granted action once; replaying the same receipt never authorizes a second physical action. Actual driving, tools, producers, route recovery, partial contribution migration, sound, balance and devices were not implemented or approved by this review. Stronger native art and final reference gates remain active.
