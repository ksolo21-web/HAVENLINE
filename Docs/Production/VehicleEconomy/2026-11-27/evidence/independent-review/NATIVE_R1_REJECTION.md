# Independent native fuel review — R1 rejected

The exact frozen source reran 107 legacy and 70 builder fuel checks without failures or stderr. The independent adversarial run passed 31 of 32 assertions, including 100 independent Python-integer multiplication oracle cases.

## FUEL-R1-01: valid grant identity collision

Vehicle `a` generation 1 with usage `x:1/u` and vehicle `a:1/x` generation 1 with usage `u` both form key `a:1/x:1/u`. Both vehicle identifiers and usage identifiers satisfy the current public ID contract. A valid first grant for the second vehicle rejects as a replay despite separate garages and a fresh nonoverlapping clock window. Use an unambiguous tuple encoding or nested per-instance usage map, then rerun the exact reproduction and meaningful existing checks.

Other independent checks covered durable zero-fuel denial windows, paused zero clocks, active clock carry across 320 digits, time partition independence, precommit rollback, authority rejection, changed request payloads, exact JSON receipt replay, 73-unit debit with 60 tank/13 material spending, and whole/fractional salvage separation.

No approval while this functional defect remains. This evidence concerns a standalone reducer, not live driving, extraction/refinery behavior, grant application by the world, balance or devices.
