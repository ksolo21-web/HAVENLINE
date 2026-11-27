# Archive paths and exact provenance

This package preserves the original author and critic document bytes. Session
paths inside those frozen records are evidence locators, not live GitHub links.
Use the SHA-256 resolver below to find the exact retained version.

| Session source | Published location |
| --- | --- |
| `renders/<id>.png` | `attempts/<id>.png`; approved versions also have `selected/` aliases |
| `prompts/<id>.txt` | `prompts/<id>.txt`, preserving the saved document bytes |
| Actual invocation prompt argument | `prompts/actual-arguments/<id>.txt`, preserving the exact invoked UTF-8 string |
| `invocations/<id>.json` | `provenance/invocations/<id>--<sha256>.json` |
| `references/existing/` | `research/existing/`, positive manifest selection only |
| `references/new/` | `research/new/`, positive manifest selection only |
| Authored design and retained draft versions | `design/`, as selected by its frozen design manifest |
| Critic reports and native review crops | `reviews/`, with earlier changed versions retained in `history/` subfolders |
| Existing approved Havenline reference art | Exact immutable baseline URLs in the provenance indexes; no duplicate source artwork required |

The saved prompt documents contain one final newline absent from the actual
argument strings. Both exact versions are retained and distinguished in
`generation-manifest.json`. The failed camp r1 tool call produced no image and
is counted separately from the generated originals.

The limited primary-A frames and internal review/layout inputs have explicit
hash-bound allowlists in `generation-inputs/`. Full source videos, full web
pages, broad frame collections and audio are not republished. Their hashes and
source URLs remain provenance records; their absence from this image package
is intentional.

The original requirement/checkpoint and preflight inputs preserve their stage
statuses. Current content acceptance is in the root acceptance document and
the frozen selection; later publication evidence attests a specific immutable
content commit. These are static concepts and design proposals, not runtime,
animation, mechanical fit, capacity, recipe or economy approval.

Review-bound earlier root prose is retained as exact raw UTF-8 `.md.txt` input
snapshots under `provenance/root-document-history/`. Use the canonical root
README and gallery for current navigation; the snapshots preserve earlier
wording without pretending their stage-specific links are the current gallery.

[Exact hash resolver](provenance/hash-resolver.json) ·
[Review evidence index](provenance/review-evidence.json) ·
[Historical preflight inputs](provenance/preflight-inputs/index.json)
