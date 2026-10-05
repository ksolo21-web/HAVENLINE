# Havenline agent execution loop guard

This standard prevents tool/retrieval loops in Havenline status, continuity, investigation and production-control work. It complements `ANTI_LOOP_ROOT_CAUSE_STANDARD.md`, which governs critic-driven product repair loops.

## 1. Status and continuity fast path

A read-only question such as "update on T06", "where did we leave off?", "what failed?", or "what is the next action?" MUST NOT trigger the full production bootstrap.

When the repository and task are already known, use this order and stop as soon as the answer is supportable:

1. `Docs/Production/WORKSTREAM_REGISTRY.json` for authoritative lifecycle state.
2. The task's `FROZEN_SCOPE.md`, `TASK_PACKET.md`, `verified-completion.json`, defect ledger, or equivalent task-local status artifact only when needed to explain the state.
3. The registered task branch/head for current implementation progress.
4. The newest relevant workflow run for the exact candidate/head only when the question depends on validation status.

Do not rediscover the HAVENLINE repository, search installed repositories, enumerate unrelated branches, or scan generic recent commits when the repository/task/branch are already named in authoritative project files.

Past-chat checkpoints are secondary continuity hints. Current authoritative repository state wins when they disagree.

## 2. Retrieval budget and evidence-gap rule

For a simple status/continuity request, the default budget is **four retrieval actions** before synthesizing an answer.

Up to two additional retrieval actions are allowed only when each one resolves a named evidence gap that materially changes the answer. Before any action beyond the default budget, the agent must be able to state internally:

`MISSING FACT -> EXACT SOURCE EXPECTED TO RESOLVE IT -> STOP CONDITION`

If that cannot be stated, stop retrieving and answer from the verified evidence already obtained.

Never repeat an equivalent search with broader wording merely because the prior result was incomplete. Never issue the same repository, branch, commit, run, file or semantic search twice unless the underlying source changed during the session.

After **two unsuccessful retrieval attempts for the same fact**, stop. Report the fact as unverified or unavailable and provide the best verified status without continuing to widen the search.

## 3. Terminal conditions

Every retrieval sequence must terminate in one of these states:

- `ANSWERABLE`: enough authoritative evidence exists; synthesize and answer immediately.
- `CONTRADICTED`: two authoritative sources disagree; perform one targeted tie-break check, then report the conflict if unresolved.
- `BLOCKED`: required evidence is inaccessible, absent or malformed after the allowed targeted attempts; state the limitation and stop.
- `ACTIONABLE`: the user asked for a fix/build/change and the diagnosis is sufficient; stop researching and switch to the execution workflow.

"Keep searching" is not a terminal state.

## 4. No search-chain escalation without new information

The following pattern is prohibited unless each hop resolves a distinct named gap:

`saved checkpoint -> repository search -> installed repository search -> branch search -> commit search -> recent commit search -> generic file search`

If an authoritative source already names the branch, candidate SHA, workflow run, task state, blocker or next action, use it directly instead of rediscovering it through broader searches.

A no-match result means `NO_MATCH`, not "search forever". An access error means `ACCESS_BLOCKED`, not "try unrelated sources until something appears".

## 5. Tool-call ledger

For substantial investigations, maintain a lightweight internal ledger with one row per unique evidence question:

- question/fact being verified;
- source queried;
- result class: `FOUND`, `NO_MATCH`, `STALE`, `CONFLICT`, `ACCESS_BLOCKED`;
- whether the fact is now resolved;
- next source, if and only if unresolved.

Do not query a source already marked `FOUND` for the same fact unless the source changed.

## 6. Status-answer contract

A Havenline task-status answer should normally contain:

- current authoritative task state;
- current registered branch/candidate when available;
- last completed test/critic milestone that is actually verified;
- the exact blocker, if any;
- the next executable action;
- any remaining uncertainty stated explicitly.

Do not withhold a usable status answer merely because every historical detail was not recovered.

## 7. Production work bootstrap

The full `AGENTS.md` production reading order applies when actually building, modifying, integrating, reviewing or repairing production work. It does **not** apply wholesale to a simple read-only status request.

Once a status request becomes a user-authorized production change, transition from the fast path to the full production workflow and read the task-relevant required documents before modifying production files.

## 8. Progress updates

Progress commentary must report real milestones, not tool churn. Do not emit a new progress line merely because another search was launched. For substantial work, update after roughly 2-3 meaningful tool calls or when a blocker/state changes.

If the task is already `ANSWERABLE`, provide the answer instead of another progress update.

## 9. Hard anti-loop rule

If three consecutive retrieval actions produce no new material fact, stop immediately and synthesize from the evidence already collected. Continuing past that point requires an explicit contradiction or a newly discovered source that can resolve a named mandatory gap.

The governing loop is:

`QUESTION -> AUTHORITATIVE SOURCE -> TARGETED GAP CHECK (IF NEEDED) -> SYNTHESIZE -> STOP`

not:

`QUESTION -> SEARCH -> SEARCH -> SEARCH -> SEARCH -> ...`
