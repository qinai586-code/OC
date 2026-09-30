# FINAL QC — Loading / Death Is Only a Return face assets

## Reference identity
GIRL A / ChatGPT
- right-facing SIDE profile
- dark hair with jade/teal streaks
- jade-tipped horns
- teal eye
- dark ribbon / teal hair clip
- white shirt + dark coat

GIRL B / Claude
- left-facing SIDE profile
- long wavy copper hair
- amber eye
- star clip + black/white ribbon
- cream cardigan + black bow

## Expression sheets
PASS:
- A_mouth.png — 1536x1024, A faces RIGHT, three mouth states.
- A_eyes.png — 1536x1024, A faces RIGHT, oo / half-lid / closed-eye states.
- B_mouth.png — 1536x1024, B faces LEFT, three mouth states.
- B_eyes.png — 1536x1024, B faces LEFT, oo / half-lid / closed-eye states.

Stabilization rule:
- Each triptych was normalized so that outside the local mouth/jaw or eyelid edit region,
  panels 2 and 3 are pixel-identical to panel 1.
- This locks nose, eye position (for mouth sheets), horns/clips, hair, clothing, framing and scale.
- Background corners are pure #FFFFFF.
- No text, numbers or panel borders are included.

## Key poses
PASS after visual self-check:
- A1 — right-facing, chin raised, eyes upward, open 'ah' singing pose.
- A2 — turns toward viewer, calm, mouth closed.
- A3 — right-facing, hand enters frame palm-up.
- B1 — left-facing, head lowered, eyes down, mouth slightly open.
- B2 — turns toward viewer, small calm smile.
- B3 — left-facing, eyes closed, quiet exhale/silence pose.

## Compromise / caveat
These are generated animation reference frames, not literal traced vector redraws of the original model sheets.
The expression sheets were stabilized after generation to remove inter-panel face/hair drift.
For final production, use the four triptychs as fixed mouth/eye assets; treat the six key poses as acting references,
not as frame-by-frame interchangeable lip-sync heads.

