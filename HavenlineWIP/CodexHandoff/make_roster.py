import json
from pathlib import Path

rows = [
 ("alfred", "Alfred", "Coordinator", "Assigns work, clears blockers and tracks handoffs.", "Moves a task card between stations."),
 ("planner", "Planning Bot", "Planning", "Reads the GitHub task plan and prepares the next ready Level 1 jobs.", "Sorts and pins task cards on a planning board."),
 ("builder-camp-pads", "Camp & Pads Builder", "Builder", "Builds the furnace, camp floor, gates, and purchase pads.", "Snaps a model piece into a camp layout."),
 ("builder-customer-counter", "Customer & Counter Builder", "Builder", "Builds the counter, service geometry, and approved customer waiting spaces.", "Checks a model on a counter workbench."),
 ("builder-resource-cooker", "Resource & Cooker Builder", "Builder", "Builds resource and cooker assets, carry rows, and receiver visuals.", "Sets a log or equipment part onto a material tray."),
 ("gameplay-integrator", "Gameplay Integrator", "Integration", "Connects independently verified changes to the game and owns the integrated build.", "Connects two labeled modules at an integration desk."),
 ("rig-character", "Character Rigging Bot", "Rigging", "Authors and checks Character 1's motions, joint weights, contact, and tool grip.", "Scrubs a character motion timeline."),
 ("rig-customer", "Customer NPC Rigging Bot", "Rigging", "Handles NPC animation and rigging for customers and other admitted actors.", "Checks a small character rig beside a motion timeline."),
 ("repair-character", "Character Repair Bot", "Repair", "Fixes character rejects and sends the corrected revision back to the independent critic.", "Repairs a marked joint and returns the review card."),
 ("repair-counter", "Counter Repair Bot", "Repair", "Fixes counter rejects and returns the revised asset or test to the independent critic.", "Reworks a marked counter part and returns a review card."),
 ("critic-game", "Game Engineering Critic", "Independent Critic", "Reviews gameplay, reference fit, and evidence without approving its own work.", "Compares two captures and marks a check or reject."),
 ("critic-rig", "Rigging Critic", "Independent Critic", "Reviews motion, foot planting, and contact at game scale on the submitted revision.", "Compares two full-body avatar takes under a fixed camera."),
 ("level1-verifier", "Level 1 Verifier", "Verification", "Replays authored test routes and checks exact build, inputs, and evidence.", "Runs a test board with separate pass, fail, and waiting lights."),
 ("live-playtester", "Live Playtester", "Playtesting", "Plays the actual build at default camera and reports device and gameplay results.", "Uses a controller at a gameplay station."),
 ("audio-sfx", "Audio & SFX Bot", "Audio", "Owns music, ambience, effects, cue routing, and mock and actual mix handoffs.", "Moves a fader and inspects three separate sound meters.")
]
bots=[{"id":i,"display_name":n,"role_family":family,"responsibility":r,"animation_hint":h} for i,n,family,r,h in rows]
assert len({b['id'] for b in bots})==len(bots)==15
r={"schema_version":1,"project":"Havenline","scope":"Level 1","kind":"role_roster_not_worker_presence",
 "avatar_count":15,"coordinator_count":1,"bot_role_count":14,
 "roles":bots,
 "display_rules":{"avatar_per_role":True,"always_live":False,"role_animation_is_telemetry":False,"status_feed":"status.json","unknown_activity_when_unmapped":True}}
Path("roster.json").write_text(json.dumps(r,indent=2)+"\n")
