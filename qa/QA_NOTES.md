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

## Revision 2 (after review)

Fixed from the user's screenshots: **MLP (1:16)** ChatGPT ran through the bottom row of nodes and her after-images
merged into a blob; the network now lives in the upper band, she runs a lane underneath, and an EPOCH counter plus
beams to the column above her replace the silhouettes. **Museum (1:20)** the machine slid off its plinth and the case
landed beside it; now the tail knocks it, it wobbles and powers down in place, and the case drops exactly over it.

Also fixed: the 1E30 counter now reaches thirty zeros on "second" and bursts on "yeah"; beat punches fade out before
"What did Ilya see?" so that passage is still; one flash (not two) at 110.1; pixel-exact 1.5x framing for the
Chinese room, the shrooms and the Loom tapestry; Claude hangs beside the knob instead of covering it; the figure is
already at the keyhole on "Ilya"; subtitles move to the top in bust shots; hand-drawn tiny figures replace
stride-downsampled sprites in the lights-out shot; the kid appears in their own crayon drawing (links the bedroom to
them); Sydney's cage builds heart by heart on the beats; camera pans quantised to 2 output px (less chroma smear);
parallel encoder.

Still open: the scale thread (giant vs normal-size ChatGPT across the rap) is not fully consistent; no match cut
between FOOM and the Chinese room.
