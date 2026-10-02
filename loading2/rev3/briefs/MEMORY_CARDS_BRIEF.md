# Memory cards: asset brief for ChatGPT (5 shots, 10 PNG files)

**What this is for:** in the 0–43 s demo, five human memories appear as drawings on paper cards. The current drawings are code placeholders that fix only the layout. This brief asks for the finished drawings. The code still does all motion, lighting, glow, steam, sparks and fire.

**Layout images to attach** (`briefs/memory_cards/`):
- `lullaby_layout.png`
- `farewell_layout.png`
- `bowl_layout.png`
- `newborn_layout.png`
- `fire_layout.png`

In each one, red, green and blue outlines mark the separate layers, the orange circles mark effects added in code, and the arrows show motion.

**Where the files go:** `loading2/rev3/art/memory_cards/`, named exactly as below. `tools/demo43.py` picks a shot up as soon as all of its files exist and replaces that shot's placeholder. Shots with no files keep their placeholders.

---

## Text to paste to ChatGPT (with the five layout images)

Please draw five small illustrations for a music video, as layered PNGs. Each attached layout image is a placeholder: keep its composition, but replace the drawing.

**Canvas.** 1536 × 1024 px, landscape, for every file. All layers of one shot share the same canvas and line up with each other.

**Positions.**
- Keep every element where the layout puts it, within about 30 px. Code animates the layers and adds lights at fixed points.
- Pixel coordinates below are on the 1536 × 1024 canvas.

**Style (all five).**
- An ink-and-wash drawing on warm cream paper, like a page from someone's sketchbook:
  - confident pen or brush-pen outlines with natural changes in weight;
  - a light grey-brown wash for form and shadow;
  - paper grain visible.
- No colour other than the paper and the ink.
- No glow, light rays, steam, sparks, fire or text: the video adds those.
- Draw lamps and candles unlit, as plain objects.
- The people are anonymous adults and a baby. They are not anime characters, and only the newborn's face is shown.
- **Hands must read at a glance as real human hands** (correct thumb, finger lengths, knuckles, a relaxed grip). This is the main reason for the request.
- Keep everything simple and uncluttered, readable at small size.

**Layers.**
- Files ending in `_bg`, and `bowl.png`, are opaque full-canvas drawings.
- Every other file is the same canvas with a **transparent background** containing only that layer's drawing. If you cannot make transparency, use a flat pure-white background with no shadow under the drawing.
- A moving layer must be complete on its own. The background must also be complete *underneath* it, because movement reveals what lies behind.

### 1. Lullaby (`lullaby_bg.png`, `lullaby_cradle.png`)

| | |
|---|---|
| framing | a small bedroom at night, seen straight on at the cradle's height, the whole cradle in frame |
| pose | a wicker rocking cradle on the floor, centre; a baby asleep inside, only its head and blanket visible. A parent's hand enters from the right edge (forearm and sleeve, no body) and rests on the cradle's rim, fingers curled over it as if rocking it |
| `lullaby_bg` | the room: floor line, a small bedside table with a lampshade at left (lamp centre ≈ 205, 369), a window above. The wall and floor must also continue behind the cradle |
| `lullaby_cradle` | the cradle, the baby and the parent's hand and forearm, as one layer |
| motion (code) | the cradle layer rocks ±4° about the middle of the rockers where they touch the floor (≈ 799, 819), so the hand rocks with it. The lamp's light is added at the lampshade |

### 2. Farewell (`farewell_bg.png`, `farewell_train.png`)

| | |
|---|---|
| framing | a station platform at night, side view, the train door at left |
| pose | a passenger's hand reaches out of the open train door toward a hand reaching from the right (someone on the platform). Their fingertips almost touch at ≈ 896, 589. A face is seen only as a dark silhouette in the train's lit window |
| `farewell_bg` | the platform, a lamp post at right, the night beyond, and the platform person's hand and forearm (entering from the right edge). It must be complete where the train stands, because the train leaves |
| `farewell_train` | the railway carriage (its left part can run off the canvas), the open door with the dark interior, the lit window with the silhouette, the wheels, and the passenger's hand and forearm coming out of the door |
| motion (code) | the train layer slides about 30 px left as the fingertips part, then accelerates away to the left. A warm spark appears in the gap and rises |

### 3. Warm bowl (`bowl.png`)

| | |
|---|---|
| framing | a table at night, seen at eye level; a frosted window behind, upper right |
| pose | one steaming bowl in the centre. An old person's hand, wrinkled at the knuckles, cups it from the left; a child's smaller hand cups it from the right. Forearms and sleeves only, no bodies |
| layer | one opaque drawing; leave the air above the bowl empty (steam rises from ≈ 768, 532) |
| motion (code) | steam, warm light from the bowl, a slow push in |

### 4. Newborn (`newborn_back.png`, `newborn_baby.png`, `newborn_hand_open.png`)

| | |
|---|---|
| framing | a close view from above: a newborn asleep on a parent's bare chest |
| pose | the baby's head is turned toward us, eyes closed, cheek resting on the chest; a tiny hand near its chin; its body is wrapped in a soft blanket running to the lower right. The parent's large hand rests on the baby's back from the right edge |
| `newborn_back` | the parent's chest and collarbone, the blanket, the parent's hand, and the tiny hand as a **closed fist** (≈ 620, 730). The chest and blanket must continue under the baby's head |
| `newborn_baby` | the baby's head only (around ≈ 650, 512), transparent elsewhere |
| `newborn_hand_open` | the same tiny hand, in the same place, with its fingers **open**; only the hand |
| motion (code) | the head layer floats slightly above the back layer for depth while the camera orbits a little. Both lift gently with the parent's breathing. On two beats the open hand replaces the fist for a moment |

### 5. Fire striking (`fire_bg.png`, `fire_hand.png`)

| | |
|---|---|
| framing | close on the ground of a bare hilltop at night; the horizon line crosses about two-thirds of the way down |
| pose | a person (hand and forearm only, from the upper right) holds a stone in a fist, raised to strike another stone on the ground |
| `fire_bg` | dark night sky, the hilltop with dry grass along its edge, a flat stone on the ground with a little tinder of dry grass on it (≈ 676, 681), and the ground continuing under where the hand will strike |
| `fire_hand` | the fist with the striking stone held in it, **raised** (stone ≈ 875, 384) |
| motion (code) | the hand layer moves straight down about 205 px to strike, twice. Sparks fly from the lower stone, a flame catches in the tinder, and its light rises on the hand |

**Deliver:** the 10 PNG files named exactly:
- `lullaby_bg`, `lullaby_cradle`
- `farewell_bg`, `farewell_train`
- `bowl`
- `newborn_back`, `newborn_baby`, `newborn_hand_open`
- `fire_bg`, `fire_hand`

---

## Notes for us

- **The list is the minimum.**
  - Each separate layer is a part that moves on its own: the cradle, the train, the baby's head for depth, the open hand for the beat, and the striking hand.
  - The war card (M1) is not in this request: it has no figures and reads well enough as it is.
  - No other artwork is requested.
- **Integration:**
  - Copy the files into `art/memory_cards/` and re-render; nothing else changes.
  - If a delivered drawing sits more than about 30 px off the layout, I adjust the anchor points in `demo43.py` (lamp, pivot, spark, steam, heartbeat, flame) to match. I do not resample the art.
  - I tested the drop-in with the placeholders exported as stand-in layers (`tools/memory_layouts.py --layers DIR`, then `DEMO_ART=DIR`): all five shots composite and animate.
