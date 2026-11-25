#!/bin/bash
set -eu
export OPENBLAS_NUM_THREADS=1
python controls.py ../c1-nov24-owner-v2/c1-meshy-ultra-multiview.glb ../c1-full-detail-rig-witness-v1/bind-evidence.npz "${1:-/tmp/c1-held-independent.iA3msD/held_owner.npz}" ../hvn-l1-c1-contact-seam-fixture-v1/editable_seam_bearing_landmarks.npz ../hvn-l1-c1-axe-chest-pose-v1/result.json ../c1-v2-axe-static-witness-v1/axe.glb
