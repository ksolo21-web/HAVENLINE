#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname "$0")" && pwd -P)
test "$(sha256sum "$here/route.gd" | cut -d' ' -f1)" = 1f42c7a29a34c24a3bb22f51743eb878ac2fc18d8c729394cf3ae11915ebbfd1
test "$(sha256sum "$here/stage.sh" | cut -d' ' -f1)" = effb1dc6f2060949f864e87c73b7bedf77203fe47a586bd2d359cc8866cd14bf
test "$(sha256sum "$here/summarize.py" | cut -d' ' -f1)" = f217a09f29bb322e6c8b47e4fcd5da702b76644d7a3e122ee39c45995e1a6783
bash "$here/stage.sh" "$1" "$2"
p="$here/staged/HavenlineLevel1"
(cd "$p"; sha256sum -c --status ../final.sha256)
test ! -e "$p/tests/hvn_l1_combined_draw.gd"
cp -- "$here/draw_route.gd" "$p/tests/hvn_l1_combined_draw.gd"
test "$(find "$p" -type f | wc -l)" = 131
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$here/staged/draw-source.sha256"
