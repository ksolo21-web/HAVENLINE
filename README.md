# HAVENLINE source-history recovery anchor

This separate branch retains the 85 source branch heads captured in SOURCE_SNAPSHOT.json. Its commit has all 79 distinct captured heads as parents, so their reachable Git histories remain recoverable through this one additional reference.

## Recovery role

This is an inert history anchor, not a production integration. Never merge this branch into main or any work branch. The consolidated source and build navigation are prepared separately for main; current Level 1 work continues on alfred/level-1-replacement.

Resolve the full original commit from SOURCE_SNAPSHOT.json and inspect or restore from that commit when recovering material. The anchor's two-file tree is intentionally only an index; the parent histories retain the original source trees and filenames.

No existing branch was deleted, renamed or reset to construct this anchor. Existing pull request heads remain separate. Operational .github files are absent from this tree.

## Scope

Git reachability preserves tracked objects and LFS pointer identities. It does not by itself copy LFS server payloads, Actions artifacts, private original videos or editable studio originals. Those have separate custody receipts and explicit unresolved status. Missing T71-T80 source definitions are not invented.
