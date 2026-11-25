# Havenline Level 1 dashboard input for Codex

Use [status.json](status.json) on the **alfred/level-1-replacement** branch. Do not substitute the default branch or an older PR. This is the machine-readable handoff for the dashboard Codex is building, not the dashboard or a telemetry stream.

## Reading the feed

- Fetch the latest file from the named branch (not from the commit linked in the first chat), or refresh your local copy of that branch before reading. The fetch is read-only; Codex can develop its dashboard separately.
- Show `observed_at_utc` and source links. Mark a snapshot stale after `stale_after_seconds`; show unavailable on network or malformed-data errors. Polling cannot produce a newer observation unless Alfred has written a snapshot. Do not use stale work as present activity.
- Show project roles and their current engineering work. `in_progress` is a work item under active development, not a continuously running worker; `ready` is queued, `blocked` has a dependency, and `done` is scoped to the item and evidence. If you animate the workspace, label the animations as representations of work status, not live workers. Never turn a headless check, design draft or detached render into a running or approved game.
- Keep the pinned playable revision and each detached evidence link separate. Link to the result and show the next action or blocker. Do not change the game, project workflows, primary branch, or permissions to power this dashboard.
- Only sanitized Havenline project status belongs here. No personal links, chat contents, agent/session handles, private renders or capture arrays, credentials, internal notes, machine paths, or telemetry. Never use this repo to store other project activity.

Alfred will refresh this checked-in snapshot at the existing active project check-ins and on significant milestones when safe. No promise of always-on execution or direct access to the Dot's private work session.
