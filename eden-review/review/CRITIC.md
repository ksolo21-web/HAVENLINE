# Independent Eden-7 visual review

Review the actual screenshot files from one GitHub Actions artifact. Confirm its
manifest matches the candidate commit and reports a live WebGL context. A passing
capture job means evidence was produced; it is never an aesthetic approval.

Score the world against the user's requested realistic human survival game:

| Criterion | Points |
| --- | ---: |
| Human anatomy, rigging, and visible animation poses | 2.5 |
| Architecture and material realism | 2.0 |
| Composition, depth, and lighting | 1.5 |
| Mobile usability and unobscured scene | 1.5 |
| Visual coherence and detail | 1.5 |
| Observable cooperative activity | 1.0 |

Inspect world, camp, east, north, front/side/rear views of both human rigs,
three phase samples of each rig's walk and run clips, and mobile captures.
Use both the complete interface image and the raw scene image. Inspect the
90-second simulation state and later camp image for observable cooperation.
Controlled poses verify rig deformation at those samples; they do not certify
fluid animation, footsteps, task gestures, or normal camera/touch controls.
Never substitute a screenshot of the loading/error screen for a scene capture.

Distorted or floating humans, dominant toy architecture, major mobile overlap,
or failed scene loading prevent approval above 8. State specific defects and the
evidence filenames. Do not inflate a score to satisfy the threshold. Mark missing
evidence as unverified and keep score null if the scene cannot be judged.

The acceptance threshold is strictly greater than 8/10. Report a score per
criterion, total, blocking defects, and the most useful next corrections. The
main agent implements corrections, uploads a new candidate commit, obtains new
captures, and asks this independent critic to reassess them.

SwiftShader is CPU rendering. Screenshot resolution does not prove 60 fps or
phone performance. These captures also do not certify live Astra connectivity;
the isolated rendering build intentionally runs the local survival simulation.
