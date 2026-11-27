# Archive paths and exact provenance

This additive package preserves exact native images and exact author/critic records.
Session paths inside frozen records are provenance locators. The hash resolver
maps those bytes to retained archive paths or immutable baseline source bindings.

| Source | Retained location |
| --- | --- |
| Every native generated PNG | `attempts/<id>.png` |
| Selected approved native PNG | Byte-identical alias under `selected/` |
| Saved prompt document | `prompts/<id>.txt` |
| Exact actual invoked UTF-8 prompt | `prompts/actual-arguments/<id>.txt` |
| Exact invocation record | Versioned under `provenance/invocations/` |
| Requirements/checkpoint versions | `provenance/input-history/` |
| Explicitly frozen author and critic records | Exact public-file manifest locations |
| Existing Havenline source artwork | Immutable baseline commit/blob binding |

Saved prompt documents may add a single final newline; the actual argument is
retained separately. Failed requests without an image have zero generated output.
All produced images, including rejected revisions, remain available. Selection
approval applies to static concept images, not native meshes, rigs, animation,
runtime integration, dimensions, capacities, recipes or game balance.

Public source copies require an explicit individual file allowlist. Full external
videos, full web pages, broad frame collections and audio are not republished.
Earlier stage records remain historical; their words are not new approvals.

[Exact hash resolver](provenance/hash-resolver.json) ·
[Generation and selection manifest](generation-manifest.json) ·
[Root public-file allowlist](provenance/root-public-files.json)
