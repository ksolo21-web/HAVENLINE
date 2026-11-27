# New conveyor research for Havenline

## Result and evidence boundary

Six new core video references were found. Four core clips and one additional defect-demonstration clip were downloaded from the official Factorio media CDN, decoded and inspected as full-duration frame samples. Two core Dorner videos and two additional videos remain metadata/documentation-only; they have no invented observation timestamps. There is no claim of continuous video/audio playback.

The complete source register is `new-source-register.json`. Source timestamps, sampling method, SHA-256 hashes and media dimensions are recorded in `frame-sampling.json` and `local-media-manifest.json`. The five inspected clips belong to three official developer articles, so they are not five independent publishers. Existing user-provided Havenline references are handled by the separate reference audit.

## The useful design conclusions

1. **Make every connection readable.** The drop-marker demonstration shows why the exact delivery point must remain visible as machinery is placed or rotated. Havenline should use clear arrows, socket direction and a resource icon. One readable belt lane is sufficient unless its own design calls for more. [NEW-V03]
2. **Give the storage house separate receiving and dispatch adapters.** Goods enter bounded inventory; an outbound adapter releases a requested resource to a known destination. The developer unloading demonstration is a storage/transport interface analogy, not a reason to copy a giant factory layout. [NEW-V04]
3. **Keep direct recipe links.** A machine can feed the next relevant machine directly, with storage used for raw inventory, finished stock and optional buffers. This is a design inference that reduces unnecessary trips through the house.
4. **Differentiate split, merge and filter.** They solve different problems. Priority routing and filtering must also remain distinct: overflow should never send a filtered item into an incompatible recipe input. [NEW-D01, NEW-D02]
5. **Make full destinations propagate a wait.** The desired behavior is a finite output buffer, then a stopped machine, then upstream accumulation. Blocked goods must not disappear. The exact buffer size remains Havenline balancing work. [NEW-V07 documentation; NEW-D02, NEW-D03]
6. **Protect human routes.** Both camp gates, the furnace and the customer face need clear access. A belt crossing needs a deliberate bridge, tunnel or controlled gate state; a belt laid across a route is not automatically traversable. The real-world lift-gate source is a physical analogy. [NEW-V06 documentation]
7. **Model the handoff.** Aligned belt surfaces, a small transfer plate/roller, side containment on turns and clear start/end fittings make machine connections physically legible. [NEW-V05 documentation]
8. **Keep customer stock, the queue and cash collection separate.** This should follow the actual user reference inspected by the other agent. The SayGames candidate has not been watched and is not proof of a counter layout. [NEW-V08 boundary]

## Six core video references

| ID | Source | Date | Review status | Use |
|---|---|---|---|---|
| NEW-V01 | Factorio, splitter timing-gap example in Friday Facts #287 | 2019-03-22 | Actual clip, 0–28.83 s timeline sampled | An intermittent input must not produce inexplicable transfer behavior. |
| NEW-V02 | Factorio, corrected splitter example in Friday Facts #287 | 2019-03-22 | Actual clip, 0–28.83 s timeline sampled, native detail | A short bounded holding area can resolve junction timing; exact fix is documented, not independently measured. |
| NEW-V03 | Factorio, drop-lane indication in Friday Facts #442 | 2026-06-12 | Actual clip, 0–18.12 s timeline sampled, native detail | Output markers and placement feedback. |
| NEW-V04 | Factorio, landing-pad unloading bays in Friday Facts #443 | 2026-06-19 | Actual clip, 0–39.67 s timeline sampled | Distinct inventory/transport interface and outgoing routes. |
| NEW-V05 | Dorner, Conveyor Transfers | 2020-04-23 | Official title/description and article only; stream unavailable | In-line, side and right-angle transfer geometry. |
| NEW-V06 | Dorner, Lift Gate Conveyors | 2020-12-10 | Official title/description and article only; embedded media unavailable | Preserve walk-through access. |

Video URLs and primary source pages are in the JSON register. Additional links: Dorner's **Accumulation System with Product Elevator** (2021-04-13; description verified, not viewed), SayGames **My Perfect Hotel** (2023-08-30; metadata only), and Factorio's machine-rotation/fluid mismatch clip (2026-06-12; actual sampled video, a negative-case example).

## Render and system checks

Trace an approved resource from gathering through its machine into storage; trace a recipe intermediate into the next machine; trace a finished product from dispatch to the rear counter intake. Verify every arrow, connector and support height. Show full storage, full counter, wrong-item and crossing states. Both gate routes and furnace access must remain usable. Exact recipes, speeds and capacities must come from Havenline's own design, not these external examples.

## Archive boundary

Do not publish the downloaded source clips or complete HTML pages. They are local research inputs and no full-source republication licence was established. Preserve the source register, original analysis, hashes and proportionate attributed evidence stills as appropriate. This agent has made no GitHub or runtime changes.
