# Evidence package and resumption

This directory supports the [task-plan refresh](../../TASK_PLAN_REFRESH_2026-11-27.md). Its validator checks documentation integrity and traceability; it does not run or approve the game.

## Reproduce the documentation checks

In a repository checkout, ensure both immutable source commits are available:

```bash
git fetch --filter=blob:none origin bbc9c57b24d21765c8c65985d4bafd858dcaf652
git fetch --filter=blob:none origin a868ae89cdf2f120b478aa0a48fff35e09cc465c
python3 Docs/Production/ReferenceRefresh/2026-11-27/validate_refresh.py
```

The fetches obtain source objects without moving remote branches. Blob filtering avoids downloading the entire image collection for a path/blob comparison. The validator writes only its local `VALIDATION.json` receipt. Missing objects produce a specific fetch instruction rather than a fabricated result.

`FREEZE.json` binds the content reviewed by the separate plan critic. Review, validation, publication and checkpoint receipts are excluded from the content digest to avoid circular self-hashes. Changes to scoped content require a new digest and affected review.

## How to read the researcher reports

`RAW_REFERENCE_AUDIT.md` and `RAW_RENDER_AUDIT.md` preserve the two researcher handoffs. The task matrix and refresh overview contain the integrated dispositions. The reference handoff's shorthand “approved warehouse/render” does not establish a new human or runtime approval: the authoritative meaning here is owner-requested design and selected archived reference with its recorded static review. Its reference to a normal landscape camera is subject to the explicit portrait/landscape reconciliation in the current overview. Official Snowbusters documentation supplies contextual support; association with a particular video remains an interpretation of that video's identity and images, not a direct statement by the publisher about the uploaded clip.

Local scratch paths in the raw handoff are research breadcrumbs, not durable release inputs. Use `REFERENCE_EVIDENCE.json` and its pinned public source/coverage links for resumption. Original private videos are identified by hash and custody manifest; they are not republished in this package. The complete 293-image register is an identity audit; only seven representative render sheets and 19 reference contact sheets were freshly inspected visually in this research. No full video playback or audio listening pass is claimed.
