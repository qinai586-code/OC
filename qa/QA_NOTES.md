# QA notes (self-review)

**Character gate.** `qa/identity_sheet.png` shows both characters in front, 3/4, side, back, an action pose and an
8-drawing run. Reviewed against the references before production: ChatGPT reads as dark + jade + dragon
(near-black hair, two small jade horns, jade eyes, one tail with a jade fin, black coat with teal lining,
asymmetric legwear). Claude reads as amber + long hair + human (no horns, ears or tail; cream cardigan, brown
skirt, one white and one dark stocking). Close-ups use Scale2x of the same sprites plus hand-drawn 2x eyes, so
they always match the full-body design.

**Process.** One contact sheet per chapter (`qa/ch0*_sheet.png`) plus `qa/overview.png` (one frame per shot).
Problems found and fixed in review: goggle eyes and flat profile heads (redrawn); run cycle arms bent backwards
(re-keyed); close-up busts too low (reframed); unreadable BOSS mug (became an insert); the dragon shadow
spilling onto the floor (clipped); empty-seat rows reading as a brick wall (rebuilt as real seats with a
lit/dim palette split); the sepia classroom seen from behind (turned to face camera); the giant reveal only
peeking over the hills (raised); after-images turning into a jade blob (removed).

**Known compromises.**
* Chapters 2-6 were partly drafted by helper agents that stopped at a usage limit; the lead finished them.
  They share the same kit, props and characters, but some middle shots (Chinese room, GPU field, orthogonality)
  are simpler than the opening and ending.
* Subtitles are small word-by-word lyrics at the bottom (bitmap font). Some bottom-of-frame details sit under them.
* Transformer-tower, chinchilla and von Neumann gags are literal and quick by design (1.8-3 s each).
* H.264 4:2:0 chroma can soften colour edges by one output pixel during sub-pixel pans; stills are crisp.
