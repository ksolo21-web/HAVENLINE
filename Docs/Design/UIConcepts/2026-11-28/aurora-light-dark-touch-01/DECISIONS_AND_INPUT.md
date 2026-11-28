# Aurora selection and input direction

## Owner decision

> Aurora. But lets make a dark them for it too. We dont a on-screen joystick. the user can touch anywhere

**Aurora is confirmed as the selected UI family.** The owner requested a matching dark theme, removed the visible on-screen joystick and specified touch-anywhere control. These choices supersede the earlier unselected-options state and visible-joystick guidance for new UI work. Earlier concepts and review records remain unchanged history.

The new Light and Dark artwork is presented for owner review. Selection of the Aurora family is not automatic approval of these exact new images or native game behavior.

## Proposed input interpretation

Touch and drag anywhere in the gameplay viewport not owned by UI—including over world objects—sets an invisible movement origin. Drag direction controls movement; release stops it. There is no visible joystick, fixed thumb zone or empty-ground restriction. A tap without meaningful drag should not cause unwanted walking; dead-zone and response tuning remain unfixed.

Touches that begin on controls, menus, status interactions, the minimap, expanded map or a modal belong to that UI and do not initiate movement. One stable movement pointer may coexist with an eligible nonmodal UI pointer; crossing boundaries does not transfer ownership. Release, OS cancellation, focus loss, rotation, fold/resize and blocking modal opening clear movement immediately. A fresh touch is required to resume.

Existing automatic/contextual gathering and attacking remain the intended control philosophy. This proposal adds no tap-to-destination pathfinding or manual attack controls. An optional dismissible first-use hint could say “Drag anywhere to move”; it is not a permanent overlay.

These drag/release, pointer-ownership and cancellation details are an implementation interpretation, not additional owner quotations or implemented behavior.

## Proposed theme preference

System / Light / Dark, with System as the proposed default. This setting is a design proposal; the owner requested matching Light/Dark visuals but did not specify a default or preference menu. Dark mode changes UI surfaces and text while preserving the daylight game scene.

## Scope

Static image review does not test movement, touch targets, map opening, OS safe insets, same-device rotation, fold transitions or native gameplay. Runtime implementation and testing remain outstanding. The exact saved requirements retain their planning-stage milestone fields; the separate checkpoint records this archive candidate's final state.
