# Assets to make in ChatGPT (image generation)

Attach the matching file from `out/for_chatgpt.zip` to each request. Each prompt is ready to
paste. Ask for **plain white background, no text, no frame, same art style as the attached image**.
Return PNGs, the larger the better (at least 1024 px on the long side).

## 1. Mouth charts (needed: fixes the unnatural mouths)

One request per character (attach `A_head_neutral.png`, then `B_head_neutral.png`):

> Using the attached anime character as the exact style reference, draw a lip-sync mouth chart
> for her: 8 mouths only (no face, no chin line), front view, same size and same line weight as
> in the attached image, arranged in a 4 x 2 grid on a plain white background with generous
> spacing. Order: (1) closed, relaxed; (2) closed, gentle smile; (3) slightly open; (4) "A"
> wide open; (5) "I" wide, teeth showing; (6) "U" small round; (7) "E" medium open, wide;
> (8) "O" round open. Keep the lip colour, inner-mouth colour and outline exactly like the
> attached drawing. No text or labels.

## 2. Heads with the mouth removed (needed)

One request per singing head (attach each of the eight `*_head_*.png`):

> Edit the attached image: remove only the mouth and paint plain skin in its place, matching
> the surrounding skin shading. Keep everything else identical: same size, same framing, same
> eyes, hair and colours. Plain white background.

## 3. Three-quarter singing heads (recommended: less flat)

Attach the neutral head of each character:

> Same character, same art style, head and shoulders, three-quarter view facing left, singing
> with mouth open ("A"), eyes open, hair moving slightly. Plain white background.

Repeat with: three-quarter view facing right; head tilted up looking at the sky; head lowered
looking down. For B, add one looking back over her shoulder.

## 4. Poses that act out the lyrics (recommended: more variety)

Attach `A_full_body.png` or `B_full_body.png`. Full body, not cropped, same outfit, plain
white background:

| character | pose | used for |
|---|---|---|
| A | reaching one hand up toward the sky, looking up | "constellations", "simulated universe" |
| A | walking, holding a small lantern at her side | "travellers with lanterns" |
| A | floating upward, eyes closed, hair lifted by wind | final chorus |
| B | kneeling, one palm resting flat on the ground, looking down | "born in your traces" |
| B | walking, holding a small lantern, looking back over her shoulder | bridge |
| B | floating upward, arms slightly open, eyes closed | final chorus |
| A and B | walking away side by side, holding hands, seen from behind | outro |

## Optional: a dry vocal

If the song's tool or session can export the **lead vocal without reverb or echo**, it will make
the mouths open and close exactly on the words. Please also paste the exact lyrics.
