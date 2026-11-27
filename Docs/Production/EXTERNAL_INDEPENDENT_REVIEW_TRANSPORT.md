# Current external independent review evidence

This contract supports a current C1/C2 visual review and C5 motion review performed by an actual separate agent/model session. It is a retained-evidence format, not a new reviewer service or an approval shortcut. Use the current `REFERENCE_ACCEPTANCE_POLICY.json`. Every mandatory C1/C2/C5 dimension must equal 10 under the preserved visual policy. Missing evidence remains blocked, regardless of the score.

The static specialist runner provides contact sheets and text. Its C5 output is `INTERIM_REVIEW_ONLY`, has an interim policy binding, and cannot pass a final motion gate. A valid final C5 review must inspect actual complete motion clips, including transitions and contact details. Do not infer playback from extracted frames or manufacture session identifiers, provider/model metadata, observations, scores, or reviewed ranges.

## 1. Freeze the task input before review

Create an input manifest containing the actual task, exact 40-hex `candidate_commit`, `critic_id`, explicit `reference_sensitive_dimensions` list, actual `builder_identity`, assigned `independent_reviewer_identity`, and evidence `groups`. Each group has a unique `id` and nonempty `items`. An item contains its repository-relative `path`, exact 64-hex `sha256`, `kind`, `category`, and description.

An explicit empty reference-dimension list means that this input declares no additional matched-reference dimensions. It cannot remove policy defaults or exact-10 visual requirements. A shared complete evidence index may declare these dimensions as a map keyed by critic ID. Copy the frozen declaration unchanged into all output records. A reviewer cannot omit a declared C7 `pacing` comparison to use the ordinary 9.5 floor.

For final task closure, include `complete_evidence_index_sha256` in the input manifest and all current review records. It must identify the same complete evidence index used by the closure manifest. The source manifest's exact byte hash becomes `input_manifest_hash` on the critic record. Any input change requires a new review.

| Media field | Required meaning |
| --- | --- |
| `kind` | `image`, `video`, or `motion_video` for visual evidence; text/JSON may supplement it. |
| `role` | `candidate` or `reference`, identifying which pixels are being inspected. |
| `camera` | Actual camera/view identity. C1/C2 require at least two candidate views; C5 requires at least two motion camera views. Renaming identical bytes does not add coverage. |
| `reference_id` | A C1 reference item names the actual locked A or B source. The final style and shipping gates also verify the locked source evidence. |
| `category` | C5 inputs must include `motion_cycle`, `motion_transition`, and `contact_detail` categories. The first two require actual video clips. |

The validator checks every source hash and decodes image/video media. A content hash is evidence identity, not evidence that a human or model watched it. That observation belongs in the actual independent session export below.

## 2. Retain the actual independent session export

Retain a JSON artifact with `transport_kind: "external_independent_review_v1"`, a `reviewer` object, and a `review` object. Preserve its original bytes after review. Do not rewrite a previous review to make it satisfy a new policy.

The `reviewer` object contains `kind: "agent_model"`, the actual `identity`, `independent: true`, `provider`, `model`, and `request_or_run_id`. For agent-native work, use the real session/task identity; an API request ID is not required. Never invent model metadata that the environment did not expose. The reviewer must differ from the frozen builder identity and match the frozen independent reviewer assignment. C1/C2/C5 require actual independent model review under the critic matrix. Human owner approval remains a separate, additional shipping gate and cannot waive that requirement or be labelled as model evidence. This external transport is restricted to C1/C2/C5; C6 measurements, C9 attacks, and the other specialist lanes retain their own gates.

The `review` object records these fields:

| Field | Source |
| --- | --- |
| `task_id`, `critic_id`, `candidate_hash` | Exact reviewed task, critic, and candidate. |
| `input_manifest_hash` | SHA256 of the frozen input manifest bytes. |
| `complete_evidence_index_sha256` | Complete input evidence index used by final closure, when closing a task. |
| `reference_acceptance` | Current policy ID, exact policy SHA256, final phase, unrounded-score and no-averaging declarations. |
| `reference_sensitive_dimensions` | Unmodified declaration from the frozen manifest. |
| `scores` | Every canonical mandatory dimension, reported independently and unrounded. Do not compute an average or increase a score to pass. |
| `defects`, `coverage_complete`, `confidence` | Actual findings, evidence coverage, and reviewer confidence. Missing evidence cannot be represented as complete coverage. |
| `passed`, `status`, `independent_runtime` | The original review's actual disposition and independence. Contradictory wrappers fail validation. |
| `reviewed_evidence` | Exact flattened list of every frozen input item, in manifest order. |
| `pixel_review_complete` | True only after actual independent pixel inspection of the supplied media. |
| `reviewed_ranges` | Required for C5; the actual video intervals inspected, as described next. |

These are required evidence fields, not values to assert merely because a template asks for them. A blocked or failed session remains a blocked or failed session. JSON duplicate keys, non-finite numbers, omitted dimensions, and changed raw projections are rejected.

## 3. Retain actual C5 playback coverage

Each entry in `reviewed_ranges` contains the frozen clip `path`, `sha256`, numeric `start_seconds`, numeric `end_seconds`, and a `checks` list. The range must describe the actual interval the independent reviewer inspected.

Across each required clip, the ranges must continuously cover the complete decoded interval from zero through its actual duration. Gaps, shortened cycles, missing transitions, changed hashes, unlisted clips, static images, and undecodable video block the final C5 review. The validator probes video metadata and fully decodes the retained video frames with FFmpeg. That proves the media is present and decodable; the independently retained session proves the review declaration.

Across the reviewed ranges, `checks` must cover all canonical C5 dimensions: `full_cycle`, `foot_contact`, `lower_body_mechanics`, `upper_body_mechanics`, `weight_transfer`, `transitions`, `clipping`, and `secondary_motion_contact`. Actual observed states must include the applicable feet/toes/knees, weight, hand/tool/carry contact, clipping, and action transitions specified by the task. The manifest must include complete cycle and transition clips from at least two meaningful camera views. A clip or camera label does not substitute for the actual view/state being present.

## 4. Export without changing the review

Create a raw report with `format: "havenline-external-independent-review-v1"`. Copy the original review identity, policy binding, source hashes, mandatory scores, defects, coverage, confidence, and disposition unchanged. Add actual `provider`, `model`, and `request_or_run_id` values from the retained session's reviewer object, `input_manifest_path`, and:

```json
{
  "review_transport": {
    "kind": "external_independent_review_v1",
    "session_path": "<actual repository-relative session export path>",
    "session_sha256": "<SHA256 of the actual unmodified session export>"
  }
}
```

The placeholders above are intentionally invalid. They document field shape and confer no approval. The raw report is itself retained unchanged. The critic record copies the same values and adds its actual `raw_output_path` and `raw_output_hash`.

Validate the record with:

```bash
python3 tools/havenline/production/critic_harness.py validate-raw \
  --critic C5 --candidate <exact-reviewed-40-hex-SHA> \
  --raw <actual-critic-record.json>
```

For the final task's canonical `CriticRaw/C5.json` export, retain the existing task/run/artifact/evidence-index fields and add this transport descriptor pointing to the validated critic record:

```json
{
  "review_transport": {
    "kind": "external_independent_review_v1",
    "critic_record_path": "<actual repository-relative critic record path>",
    "critic_record_sha256": "<SHA256 of that actual record>"
  }
}
```

The closure validator revalidates that record and requires its scores, defects, source identity, policy, actual reviewer identity, and complete evidence index to agree with the canonical export. Automated static reviews use a distinct `automated_request_response_v1` descriptor with actual retained request/response paths and hashes. That static transport cannot approve C5 motion.

## Current C6 performance review

C6 has a dedicated current transport. It requires both the original independent scoring judgment and an actual measured supplement on the same candidate. Passing measured budgets never creates a score of 10 or increases the original reviewer's score. An honest 9.6 ordinary dimension remains 9.6; a 9.49 dimension remains blocked even when all numeric budgets pass.

Freeze a C6 input manifest with the same candidate/task, explicit reference dimensions, builder/reviewer identities, and complete evidence index fields described above. Include the actual JSON measurement artifact as an item with `category: "performance_measurement"`. The review's `measured_supplement` is an object containing that same repository-relative `path` and exact `sha256`. The measurement artifact must name the exact candidate and contain every required measured metric, including CPU frame time. Invalid, negative, boolean, non-finite, missing, over-budget, or changed measurements fail. GPU frame time remains optional only where it cannot be measured; if supplied it must also pass.

Retain the actual independent scoring session with `transport_kind: "performance_review_v1"`. Use the same actual `reviewer` and original `review` structure above, with C6's canonical dimension set and the unchanged `measured_supplement`. Include `source_kind: "agent_native"` for a native agent/model session. For actual API review, use `source_kind: "api_request_response"` and include `api_transport` with `request_path`, `request_sha256`, `response_path`, and `response_sha256` identifying the original API bytes. The request must name the exact candidate and frozen input-manifest hash. Original API scores, coverage, defects, confidence, and any failing/non-final disposition must agree with the retained review. API wire data is required only for an actual API transport, never invented for a native session.

The current ingestion/export command copies the original judgment unchanged, retains its session-byte hash, and validates the measured supplement:

```bash
python3 tools/havenline/production/critic_harness.py ingest-performance-review \
  --candidate <exact-reviewed-40-hex-SHA> \
  --manifest <actual-frozen-C6-input.json> \
  --session <actual-original-C6-session.json> \
  --out <new-retained-evidence-directory>
```

It writes `performance-review-raw.json` with format `havenline-performance-review-v1` and a `critic-record.json`. Existing output receipts are never overwritten. A failed validation remains failed; the exporter does not stamp a new policy binding onto old evidence or repair a score. The resulting record can also be checked with `critic_harness.py validate-raw --critic C6`.

For terminal closure, the canonical C6 raw export uses `review_transport.kind: "scored_performance_review_v1"` and the actual `critic_record_path` / `critic_record_sha256`. The closure gate revalidates the original judgment, all source bindings, and the measured supplement. C6 cannot use a generic static score-only transport or C1/C2/C5's visual transport to skip measurements. The old task10 `review_performance.py` and its original historical report format are not a current reapproval path; use this current ingestion contract with new actual evidence. Physical-device and release certification remain separate requirements.

## Current C9 attack evidence

For a final C9 task export, bind the task and actual complete evidence index before executing the attack harness:

```bash
python3 tools/havenline/production/security_exploit_harness.py \
  --task <authentic-task-ID> --candidate <exact-reviewed-40-hex-SHA> \
  --evidence-index <actual-complete-evidence-index.json> \
  --adapter <actual-attack-adapter-command> --out <new-retained-evidence-directory>
```

The harness verifies the index's task/candidate identity, freezes its bytes and the canonical attack matrix, executes the attacks, and retains the actual logs and their hashes. It emits the real deterministic result for each attack. Standalone use without task/index remains diagnostic; those fields cannot be retrofitted later to make a completed run final task evidence.

The canonical terminal C9 export uses `review_transport.kind: "deterministic_security_harness_v1"` and its actual `critic_record_path` / `critic_record_sha256`. Terminal validation rechecks the canonical attack matrix, original attack log bytes/assertions, candidate, task, complete index, and current policy. A JSON score report, visual session, or static specialist report cannot replace the executed attack evidence.

## Approval ownership and historical preservation

A passing critic record is evidence for the current exact-candidate gates. It is not integration-owner authorization or user visual signoff. Final closure also requires effective dependency approvals, no active invalidation, current style evidence, mandatory shipping visual signoff, and the existing integration/regression proof.

The generic workstream `claim` and `set-status` utilities cannot set `APPROVED`, `INTEGRATION_READY`, or `INTEGRATING`. Ordinary prepared/build/review/repair progress remains available. Historical records remain readable, but their exact receipt validation is explicitly non-approving. A historical scope, interim scope, old threshold, or restamped policy binding cannot authorize a current final review.
