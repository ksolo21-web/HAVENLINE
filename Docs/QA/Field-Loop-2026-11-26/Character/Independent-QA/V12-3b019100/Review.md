# Character 1 movement review

**8.7/10 · Held for an inward knee bend on turns.** Character skin V12 and motor `3b019100` were tested together on field source commit `e38ed1bb7d198327d6c05e74905a0921e4b3c91c`. Walk and Run are free of the large shin stretching and pouch overlap found on earlier versions. In the first 0.10-second contact windows, a returning planted boot moved at most 2.4 mm in five running turn entries and 2.1 mm in five walking turns. The boot and opposite shin no longer intersected in the measured surface sweeps.

During a walking about-face, the planted right knee still falls 14 cm toward the middle of the body relative to the hip-to-ankle line. This pulls the white boot cuff and ankle sideways. The swing leg can deviate 21 cm. The center and bottom rows of the diagnostic show the difference between the boot orientation and knee direction. The failure is in the protected turn applied inside Godot. The supplied Walk and Run clips have regular knee tracking by themselves.

[Posed knee comparison](turn-knees.jpg) · [Sole measurements](Support-motion.json) · [Triangle tests](Boot-collision.json) · [Rig ledger](ledger.json) · [Coverage verifier result](Gate-result.txt)
