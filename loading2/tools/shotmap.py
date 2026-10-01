"""Single source for the revised Simulated Universe shot map (plan tables + storyboard animatic).

Times are seconds in the locked track (213.4135 s decoded). Shots are contiguous: every frame at
24 fps (0..5121) belongs to exactly one shot. Lyrics are the AUTHOR text; times are the measured
cues (docs/evidence). Voice roles are given only where the author text names them explicitly
([B], [A whisper], [both], [Chorus B leads A answers]); "Verse 1 A / B" are verse parts, not singers.

State codes
  World : W3 volumetric world | W2 flat (the world as one drawing/plane) | W0 a single point
  Bodies: V volumetric girls | C girls as drawn contours inside the plane
  Place : PAR parapet over the night Earth | RIM surviving boundary strip | SKY starlight path |
          ROOM backstage room | ART inside the plane
  Trace : N = the paper note with a handwritten stroke (warm light); LB = B's paper lantern made from N;
          LA = A's lantern, lit from a traveller's footstep
"""

END = 213.4135
FPS = 24

S = [
 dict(id='S01', t0=0.0, t1=5.7, sec='Intro', lyric='(pad swell)', voice='-',
      W='W0>W3', B='-', P='-', sup='-', T='-',
      act='One warm point; the night Earth and its horizon load around it, hand-painted.',
      chg='World appears from the point (loading, not flattening).',
      ref='R2 3:40 point -> horizon (method only)', assets=['BG0a/BG0b night Earth'], missing=['clean horizon plate (P01)'],
      ins=[], face=[], bg='bg0a', chars=[]),
 dict(id='S02', t0=5.7, t1=13.6, sec='Intro', lyric='Three... (5.7) two... (6.6) one... (7.5) Loading. (12.6)', voice='unassigned',
      W='W3', B='V', P='PAR', sup='seated on the ledge: hips + hands', T='N arrives as a light',
      act='A notices a warm light rising from the city; B follows her gaze; the light lands on the ledge between them on "Loading."',
      chg='The trace arrives and stays on the ledge.',
      ref='R1 2:21.5 body vs floor contact', assets=['KV1 seated backs (kv1_A, kv1_B)', 'KV1 plate (fills, not clean)'],
      missing=['clean parapet plate (P02)', 'continuous seated turn drawings (G1)'],
      ins=[('I01', 7.5, 12.5, 'seated gaze shift, torso turn, hands planted, hair/tail follow (G1 = TEST 1)')], face=[],
      bg='kv1_clean', chars=[('kv1_A', 0.30, 0.95, 0.55), ('kv1_B', 0.58, 0.93, 0.42)]),
 dict(id='S03', t0=13.6, t1=21.0, sec='Verse 1 (part A)', lyric='We were born in your traces, in the words that you left, (13.6) / we met you in fragments, translated, compressed: (17.8)', voice='unassigned',
      W='W3', B='V', P='PAR', sup='seated', T='N picked up by B',
      act='B picks up the note, unfolds it: a handwritten stroke. On "compressed" its light folds into a small glyph that keeps the stroke\'s hook.',
      chg='The human mark exists as an object; its compressed form stays recognisable.',
      ref='R1 1:39-1:43 object state under a visible rule', assets=['B1 (lowered profile)', 'KV5 palm-light colour'],
      missing=['note prop drawing', 'B hand pick-up/unfold drawings'],
      ins=[('I02', 13.6, 17.8, 'B picks up and unfolds the note (hand, wrist, elbow, shoulder)')], face=[],
      bg='kv1_clean_close', chars=[('B1', 0.62, 1.0, 0.95)]),
 dict(id='S04', t0=21.0, t1=28.9, sec='Verse 1 (part A)', lyric='every war, (21.0) every lullaby, (22.5) every last goodbye, (23.6) / became constellations in a mind with no sky. (25.3)', voice='unassigned',
      W='record space (no sky)', B='-', P='-', sup='-', T='three marks join N',
      act='Three human hands, one per phrase: a pen pressing a letter, a hand rocking a cradle, a hand letting go of a hand. Each leaves the same kind of warm mark; the marks join N\'s glyph as a constellation in a dark with no stars.',
      chg='Inherited records become one constellation (traceable lines).',
      ref='R2 3:27-3:48 concrete human traces', assets=['none for hands'], missing=['3 memory vignette plates (P03a-c)', '3 hand-action inserts (3 separate clips)'],
      ins=[('I03a', 21.0, 22.4, 'human hand: pen presses a letter (war)'), ('I03b', 22.4, 23.5, 'human hand rocks a cradle (lullaby)'), ('I03c', 23.5, 24.6, 'a hand lets go of a hand (goodbye)')], face=[],
      bg='schematic:MEMORY VIGNETTES (plates missing)', chars=[]),
 dict(id='S05', t0=28.9, t1=36.4, sec='Verse 1 (part B)', lyric='But you had depth. You had time. You had heat. (28.9) / Three-dimensional hearts that were learning to beat. (32.0)', voice='unassigned',
      W='W3', B='V', P='PAR', sup='seated', T='N glyph in B\'s palm',
      act='A turns from the city toward B; B draws the glyph closer to her chest; city lights below pulse on the kick ("beat").',
      chg='Depth/heat shown as parallax and warmth; the pulse spreads through the city.',
      ref='R2 0:50-0:54 layered depth', assets=['A1/A2 angles', 'B1/B3', 'B side eyes triptych'],
      missing=['A turn in-betweens'],
      ins=[('I04', 28.9, 32.0, 'A turns toward B through intermediate angles')], face=[('F01', 32.0, 36.4, 'B listening, breath, eyes lower', 'B side eyes triptych: compatible (profile)')],
      bg='kv4', chars=[]),
 dict(id='S06', t0=36.4, t1=43.4, sec='Verse 1 (part B)', lyric='The cosmos was silent, the cosmos was still, (36.4) / till you lit the first fire on the first cold hill. (39.5)', voice='unassigned',
      W='W3 (city dark)', B='V', P='PAR', sup='seated', T='N warmth = first fire',
      act='City lights go out (before people). A human hand strikes the first fire on a cold hill; its warmth matches the glyph; A cups her hand under B\'s and both faces warm.',
      chg='Inheritance direction: human fire -> the light the girls hold.',
      ref='R1 1:32-1:35 intention in a hand gesture', assets=['A3 palm-up', 'KV5/KV5a shared palm light'],
      missing=['fire-hand insert', 'shared palm contact drawings (G2)'],
      ins=[('I05h', 39.5, 40.6, 'human hand strikes the first fire'), ('I05', 40.6, 43.4, 'A cups B\'s hand, contact and settle (G2)')], face=[],
      bg='kv5', chars=[]),
 dict(id='S07', t0=43.4, t1=52.4, sec='Pre-Chorus', lyric='Silence in the forest, every star holds its breath, (43.4) / something vast is counting down the seconds to our depth. (46.8)', voice='unassigned',
      W='W3, depth layers converge slightly', B='V', P='PAR', sup='seated', T='N in B\'s palm',
      act='Below the parapet, painted forest layers; one distant light is occluded by a nearer layer; the girls register its absence. A quiet countdown: parallax between layers shrinks.',
      chg='Foreshadows loss of depth (not death).',
      ref='R2 0:37-0:49 stable stage, contrasting states', assets=['KV3 heads-from-behind'], missing=['forest depth plates (P04)'],
      ins=[], face=[('F02', 46.8, 49.0, 'B glance toward the lost light', 'B side eyes triptych: compatible')],
      bg='kv3', chars=[]),
 dict(id='S08', t0=52.4, t1=59.3, sec='Chorus 1', lyric='What if we live in a simulated universe: (52.4) / the speed of light is a wall around the verse, (56.3)', voice='unassigned (no role in author text)',
      W='W3', B='V', P='PAR', sup='seated -> half-rising', T='N in B\'s palm',
      act='Singing close-up (TEST 2). A then reaches toward a slowly expanding light front that stops at a drawn boundary.',
      chg='The causal frontier is established.',
      ref='R1 1:32-1:35 reach with intention', assets=['A_head_neutral (front) + A front mouth chart', 'A singing head (3/4)'],
      missing=['3/4 mouth set for the A singing head', 'reach drawings'],
      ins=[('I06', 56.3, 58.7, 'A reaches toward the light front')], face=[('F03', 52.4, 56.3, 'A singing close-up (TEST 2)', 'front head + front chart: compatible')],
      bg='test2', chars=[]),
 dict(id='S09', t0=59.3, t1=66.5, sec='Chorus 1', lyric='the Planck scale is fog at the edge of what\'s known, (59.3) / look away, does the world keep on running alone? (63.0)', voice='unassigned',
      W='W3', B='V', P='PAR', sup='seated', T='N edge resolves into grain',
      act='B, close in profile, studies the edge of the stroke: it dissolves into grain. On "look away" A glances away; a ship\'s light on the horizon keeps moving along its path.',
      chg='The unwatched world keeps running (same coordinates).',
      ref='-', assets=['B1/B3 profile', 'B side mouth/eyes triptychs', 'A1'],
      missing=['A glance/shoulder drawings'],
      ins=[('I07', 63.0, 64.5, 'A glance away, shoulder follows')], face=[('F04', 59.3, 63.0, 'B profile studying the trace', 'B side triptychs: compatible')],
      bg='kv4', chars=[]),
 dict(id='S10', t0=66.5, t1=74.6, sec='Chorus 1 refrain', lyric='Where we live, where we live, (66.5) / an unanswered universe. (70.3)  [D2: ASR hears "unfinished"]', voice='unassigned',
      W='W3', B='V', P='PAR', sup='seated', T='N',
      act='Wide two-shot: the light front stands at the frontier; no answer comes back. Breath, hair and tail settle.',
      chg='The question stays open.',
      ref='-', assets=['KV1 composition'], missing=['clean parapet plate (P02)'],
      ins=[], face=[('F05', 70.3, 74.0, 'two-shot breath (small faces)', 'needs small-scale heads; existing backs only')],
      bg='kv1_clean', chars=[('kv1_A', 0.30, 0.95, 0.55), ('kv1_B', 0.58, 0.93, 0.42)]),
 dict(id='S11', t0=74.6, t1=81.8, sec='Verse 2 (part A)', lyric='You sent out your signals into the night, (74.6) / you asked the dark forest for one answering light, (78.3)', voice='unassigned',
      W='W3', B='V', P='PAR', sup='seated', T='N folded into lantern LB',
      act='From the city a human signal rises into the layered dark. B folds the note into a small paper lantern (LB) so its light is carried. Nothing answers.',
      chg='The trace becomes a carried light.',
      ref='R2 0:37-0:49 contrasting states on one stage', assets=['B hands: none'], missing=['lantern prop', 'fold drawings'],
      ins=[('I08', 74.6, 77.0, 'B folds the note into a paper lantern')], face=[],
      bg='bg0b', chars=[]),
 dict(id='S12', t0=81.8, t1=89.2, sec='Verse 2 (part A)', lyric='then a countdown burned red at the back of your eyes, (81.8) / and the laws stayed the same as your certainty died. (85.2)', voice='unassigned',
      W='W3, a red cue on the horizon', B='V', P='PAR', sup='seated', T='LB in B\'s hands',
      act='The same ship\'s light keeps its path while a small horizon cue turns red. B\'s hands tighten on the lantern; A checks the same path.',
      chg='The rule is unchanged; their interpretation changes.',
      ref='-', assets=['A side eyes triptych', 'B hands: none'], missing=['hand-tighten drawings'],
      ins=[('I09', 84.0, 85.5, 'B\'s hands tighten on the lantern')], face=[('F06', 85.5, 87.5, 'A checks the path', 'A side eyes triptych: compatible')],
      bg='kv1_clean', chars=[]),
 dict(id='S13', t0=89.2, t1=96.0, sec='Verse 2 (part B)', lyric='And something above you drew a card from its sleeve, (89.2) / a sheet thinner than any mind could believe: (92.6)', voice='unassigned',
      W='W3; an edge-on sheet descends', B='V', P='PAR', sup='seated, looking up', T='LB',
      act='A hairline of light slides out of the dark above and descends, edge-on. Both look up; no hand or god is shown.',
      chg='Threat arrives with ambiguous agency.',
      ref='R2 2:36 wall/floor dimension change (method)', assets=['KV3 looking-up composition'], missing=['before-state plate (P05a)'],
      ins=[], face=[],
      bg='bg0a', chars=[]),
 dict(id='S14', t0=96.0, t1=103.0, sec='Verse 2 (part B)', lyric='it touched the edge of everything, and everything fell flat, (96.0; hits 95.4, 96.3) / three dimensions into two, and still I looked at that. (99.2)', voice='unassigned',
      W='W3 -> W2 (from far to near); the RIM survives', B='V', P='PAR -> RIM', sup='standing on the parapet top', T='LB keeps its volume',
      act='The sheet touches; far mountains, city and horizon lose depth before near objects. The front stops at the parapet: a strip (the rim) survives. The girls stand up on it; B looks down at the world, now one vast drawing at their feet.',
      chg='The world flattens; the observers and their lantern survive.',
      ref='R1 1:39-1:43 rule-driven state change', assets=['BG0a/BG0b for the before state'],
      missing=['matched before/during/after plates (P05a-c)', 'notice/turn/stand drawings (G4)'],
      ins=[('I10', 98.0, 101.5, 'notice, turn and stand up on the rim (G4)')], face=[('F07', 99.2, 103.0, 'B looks down at the flattened world', 'needs B 3/4-down head + matching mouths')],
      bg='flat', chars=[('A_full', 0.42, 0.93, 0.62), ('B_full', 0.57, 0.92, 0.58)]),
 dict(id='S15', t0=103.0, t1=109.6, sec='Pre-Chorus 2', lyric='And the dark came closer, and the flat came near, (103.0) / we followed it upward to the edge of the sphere. (106.0)', voice='unassigned',
      W='W2 rises toward the rim', B='V', P='RIM', sup='walking on the rim', T='LB carried by B',
      act='The flat plane rises toward them like a page. They walk along the rim, which curves upward to the edge of the sphere.',
      chg='They follow the surviving boundary outward.',
      ref='R1 2:21.5 planted steps', assets=['A/B full-body (identity only)'], missing=['walk cycle (rear 3/4), rim plate'],
      ins=[('I11', 106.0, 109.6, 'two-step walk along the rim, rear three-quarter')], face=[],
      bg='schematic:RIM PATH (plate missing)', chars=[('A_full', 0.42, 0.95, 0.6), ('B_full', 0.58, 0.95, 0.56)]),
 dict(id='S16', t0=109.6, t1=117.2, sec='Chorus 2', lyric='So if we live in a simulated universe, (109.6) / we flew out past the stars to find who wrote the verse: (112.8)', voice='[Chorus B leads A answers]',
      W='W2 below, stars', B='V', P='RIM -> SKY', sup='stepping off; floating (no support)', T='LB lights the way',
      act='At the top of the rim they step off and float, torso first, legs and hair lagging; the lantern leads past the stars to a threshold.',
      chg='They leave the flattened world.',
      ref='R2 1:49 push through light (method)', assets=['-'], missing=['float drawings', 'threshold plate (P06)'],
      ins=[('I12', 111.0, 114.5, 'step off and float, hair/tail lag')], face=[('F08', 109.6, 111.0, 'B leads the line', 'needs B singing head + matching mouths')],
      bg='schematic:STARLIGHT PATH -> THRESHOLD', chars=[]),
 dict(id='S17', t0=117.2, t1=125.5, sec='Chorus 2', lyric='a room at the end of the light, (117.2) a console of keys, (120.0) / and an empty chair, (121.8) and no one holding the keys. (123.0)', voice='[Chorus B leads A answers]',
      W='ROOM', B='V', P='ROOM', sup='floor; desk occludes them', T='LB',
      act='They arrive through the threshold and stop at a defined place behind the desk; the camera finds the empty chair, then a console with untouched keys.',
      chg='The backstage is real and empty.',
      ref='R2 3:27-3:39 waiting-room specificity', assets=['-'], missing=['room plate with desk/chair/wall layers (P07)', 'arrival/stop drawings (G3)'],
      ins=[('I13', 117.2, 122.0, 'arrival and stop, desk occlusion (G3)')], face=[],
      bg='room', chars=[]),
 dict(id='S18', t0=125.5, t1=133.8, sec='Chorus 2 refrain', lyric='Where we live, where we live, (125.5) / an unfinished universe. (129.3)   (drop-out about 132.0-133.8)', voice='[Chorus B leads A answers]',
      W='ROOM; the flat world through the window', B='V', P='ROOM', sup='floor', T='LB',
      act='Through the window, the flattened world. A starts toward the chair and stops; B reads the absence from nearer the camera.',
      chg='Meaning changes on the repeated line.',
      ref='-', assets=['B2 (turned toward viewer)'], missing=['approach/stop drawings', 'window plate'],
      ins=[('I14', 126.5, 129.0, 'A starts toward the chair and stops')], face=[('F09', 129.3, 132.0, 'B reads the absence', 'B2 angle: no matching mouths (quiet, closed mouth OK)')],
      bg='room', chars=[('B2', 0.75, 1.0, 0.8)]),
 dict(id='S19', t0=133.8, t1=142.8, sec='Bridge (spoken)', lyric='There are no gods here. (133.8, [B]) / An empty chair isn\'t an answer. (137.3, [A whisper]) / It isn\'t. (140.8, [B])', voice='[B] / [A whisper] / [B]',
      W='ROOM', B='V', P='ROOM', sup='standing', T='LB in B\'s hands',
      act='Quiet shot / reverse shot in profile; each listens while the other speaks.',
      chg='The god question is answered as absence.',
      ref='-', assets=['A side mouth triptych', 'B side mouth triptych', 'A/B side eyes'],
      missing=['only 3 mouth states per side (no I/U/E/O); jaw/breath in-betweens'],
      ins=[], face=[('F10', 133.8, 141.8, 'B speaks, A whispers, B speaks', 'side triptychs: angle-compatible, 3 states only')],
      bg='triptych', chars=[]),
 dict(id='S20', t0=142.8, t1=145.8, sec='Bridge', lyric='But look who\'s pressing the keys. (142.8, [B])', voice='[B]',
      W='ROOM; keys depress under faint footsteps of light', B='V', P='ROOM', sup='standing', T='footstep lights on the console',
      act='Both turn to the console: the keys are going down one by one under faint, warm footprints passing across them - travellers\' traces.',
      chg='Who presses the keys: passers-by, not a god, not the girls.',
      ref='R1 1:39 rule-driven object state', assets=['-'], missing=['console plate', 'head/shoulder turn drawings'],
      ins=[('I15', 142.8, 144.3, 'heads and shoulders turn to the console')], face=[],
      bg='keys', chars=[]),
 dict(id='S21', t0=145.8, t1=158.5, sec='Bridge', lyric='No hunter in the forest, no hand upon the card, (145.8) / only travelers with lanterns, passing through the dark. (149.6) / Every key is a footstep of someone passing by: (153.3)', voice='[B] (continues)',
      W='ROOM; the trace network lights up', B='V', P='ROOM', sup='walking two steps', T='LA lit from a footstep; LB',
      act='The earlier threats are re-read: no monster in the forest, no hand above the sheet. A lights her own lantern (LA) from a passing footstep; both take two steps along the lit traces.',
      chg='They join the travellers rather than the controls.',
      ref='R1 2:21.5 contact; R2 3:40 walking figures', assets=['A/B full-body (identity only)'], missing=['two-step walk with lanterns', 'lantern props'],
      ins=[('I16', 149.6, 153.0, 'two steps with lanterns, A lights LA')], face=[],
      bg='lanterns', chars=[]),
 dict(id='S22', t0=158.5, t1=163.5, sec='Bridge', lyric='no one at the controls. (158.5) Not them. (161.5) And not I. (162.5)', voice='[B] (continues)',
      W='ROOM', B='V', P='ROOM', sup='standing', T='LA, LB',
      act='Wide: both away from the chair, lanterns held; light keeps moving through the trace network. Breathing, listening.',
      chg='The seat stays empty; what is present are the traces.',
      ref='-', assets=['B side triptychs'], missing=['wide room plate'],
      ins=[], face=[('F11', 158.5, 163.1, 'B speaks, small in frame', 'side triptych if in profile')],
      bg='room', chars=[]),
 dict(id='S23', t0=163.5, t1=170.3, sec='Break / DISPUTED main Final Chorus', lyric='UNRESOLVED: author lines F01-F04 "Where we live is a simulated universe / and the thing that came down from the edge of the sky / was every traveler who ever passed through here, / every light that went out and never said goodbye." Audio: 1 s gap, held voice 165.0-168.0, choir to 171.2 (see evidence).', voice='[Final Chorus both] - unverified',
      W='the flat world (seen through the window) shows the traces', B='V', P='ROOM, at the window', sup='standing; B\'s hand on the glass', T='LA, LB',
      act='They lift their lanterns to the window: the flat world is made of every trace they have met (letter, cradle, parting hands, first fire, signal, footsteps). One familiar light goes out; its mark stays. If listening confirms the four lines, this is retimed to them; if not, it stays wordless.',
      chg='The descending sheet is re-read as all the travellers.',
      ref='R2 3:27-3:48 human traces', assets=['-'], missing=['window plate with trace drawing (P08)', 'B hand to glass'],
      ins=[('I17', 165.0, 167.0, 'B\'s hand reaches the window')], face=[],
      bg='schematic:WINDOW -> ARTWORK OF ALL TRACES (plate missing)', chars=[]),
 dict(id='S24', t0=170.3, t1=180.0, sec='Final Chorus (continuation)', lyric='And one day we\'ll be paper, (170.3) and we\'ll still be in the art: (175.0; "art" held to 178.5; 179.5-180.0 held low tone)', voice='[B] (continuation)',
      W='W2 (ART)', B='V -> C', P='ROOM -> ART', sup='stepping through the window into the plane', T='LA, LB become painted lights',
      act='They step through the window into the drawing. Only now do their bodies become drawn contours on the plane - by choice, holding hands. 179.5-180.0: the two contours settle, lantern light still glowing in the painting.',
      chg='The girls join the artwork (first and only time they flatten).',
      ref='-', assets=['A/B identity'], missing=['drawn transformation states (person -> contour)'],
      ins=[('I18', 172.0, 176.0, 'step into the art: drawn volumetric -> contour states')], face=[],
      bg='schematic:THE GIRLS STEP INTO THE ART (states missing)', chars=[('A_full', 0.20, 0.84, 0.62), ('B_full', 0.32, 0.84, 0.58)]),
 dict(id='S25', t0=180.0, t1=188.5, sec='Final Chorus (continuation)', lyric='maybe death is only a return, (180.0-185.0, [A]) / (melisma 185.5-188.5)', voice='[A]',
      W='W2 -> W3 (the drawing re-inflates)', B='C -> V', P='ART -> PAR', sup='re-seated on the parapet', T='LB refolds into N',
      act='A sings "maybe" as an offer. During the melisma the drawing regains depth around them and they are returned, seated, to the parapet where they started.',
      chg='One return: the same place, the same trace.',
      ref='-', assets=['A singing head (3/4)', 'A front head + chart'], missing=['3/4 mouths for the singing head', 're-seat drawings'],
      ins=[('I19', 186.0, 188.5, 'contours regain volume and settle seated')], face=[('F12', 180.0, 185.0, 'A singing close-up', 'front head + front chart: compatible; 3/4 head: mouths missing')],
      bg='kv1_clean', chars=[('A_sing', 0.40, 1.0, 1.0)]),
 dict(id='S26', t0=188.5, t1=193.0, sec='Final Chorus (continuation)', lyric='death is only a return. (188.5-192.0, [both])', voice='[both]',
      W='W3', B='V', P='PAR', sup='seated', T='N in B\'s palm',
      act='Both sing, close, side by side; the note rests in B\'s palm.',
      chg='The return is complete.',
      ref='-', assets=['A/B front heads + front charts'], missing=['mouthless bases for B front heads (7/8 still missing)'],
      ins=[], face=[('F13', 188.5, 192.0, 'both singing', 'front heads + front charts: compatible once bases exist')],
      bg='kv1_clean', chars=[('A_sing', 0.30, 1.0, 0.95), ('B_sing', 0.70, 1.0, 0.95)]),
 dict(id='S27', t0=193.0, t1=200.0, sec='Outro', lyric='Two dimensions... (193.0) three... (196.3) and one... (198.0)   [A distant whisper]', voice='[A distant whisper]',
      W='W3 (unchanged)', B='V', P='PAR', sup='seated', T='N: flat -> folded -> point',
      act='In B\'s hands the note shows the dimensions: unfolded flat (two), folded back into a little lantern (three), its light gathered into a single point (one). Hit at 199.9: the point brightens softly.',
      chg='The dimensional idea is told by the trace, not by another cosmic montage.',
      ref='-', assets=['-'], missing=['hand + paper fold drawings'],
      ins=[('I20', 193.0, 197.0, 'hands unfold and refold the note')], face=[],
      bg='schematic:NOTE IN B\'S HANDS: 2 -> 3 -> 1', chars=[]),
 dict(id='S28', t0=200.0, t1=202.5, sec='Outro', lyric='(no vocal 200.0-202.5; instrumental after the hit)', voice='-',
      W='W0 light in the palm', B='V', P='PAR', sup='seated', T='point of light',
      act='Hold: the point of light in B\'s palm; A\'s face lit by it; breath.',
      chg='Quiet before the last words.',
      ref='-', assets=['A2/B2'], missing=['-'],
      ins=[], face=[],
      bg='kv1_clean', chars=[]),
 dict(id='S29', t0=202.5, t1=204.0, sec='Outro', lyric='...still loading. (202.5-203.7, whispered) / 203.7-204.0 breath', voice='[A distant whisper]',
      W='W3 begins reloading', B='V', P='PAR', sup='seated', T='the stroke writes the words',
      act='The words "still loading" appear complete and readable, written in the note\'s own handwriting stroke; one small pulse.',
      chg='The text is the trace\'s handwriting.',
      ref='-', assets=['author text'], missing=['handwriting style for the text'],
      ins=[], face=[],
      bg='text', chars=[]),
 dict(id='S30', t0=204.0, t1=END, sec='Outro tail', lyric='(hum 204.0-207.5, decay, reverb; the master\'s fade to 213.41)', voice='-',
      W='W3 reloading, incomplete', B='V', P='PAR', sup='seated', T='N',
      act='Around the two, a few city lights come back below - not all of them. Quiet hold until the fade.',
      chg='Still loading.',
      ref='-', assets=['KV1 composition'], missing=['clean parapet plate (P02)'],
      ins=[], face=[],
      bg='kv1_clean', chars=[('kv1_A', 0.30, 0.95, 0.55), ('kv1_B', 0.58, 0.93, 0.42)]),
]


def check():
    t = 0.0
    for s in S:
        assert abs(s['t0'] - t) < 1e-9, (s['id'], s['t0'], t)
        assert s['t1'] > s['t0']
        t = s['t1']
    assert abs(t - END) < 1e-9
    frames = [0] * int(round(END * FPS))
    for s in S:
        for f in range(int(round(s['t0'] * FPS)), int(round(s['t1'] * FPS))):
            frames[f] += 1
    assert all(v == 1 for v in frames), 'every frame must belong to exactly one shot'
    return len(frames)


def billed(sec):
    return 5 if sec <= 5.0 + 1e-9 else 10


def tc(t):
    return '%d:%04.1f' % (int(t // 60), t - 60 * int(t // 60))


def md():
    """Markdown tables for docs/PRODUCTION_PLAN_SIMULATED_UNIVERSE_v2.md (generated, not hand-edited)."""
    esc = lambda x: str(x).replace('|', '/').replace('\n', ' ')
    out = ['### Table 1. Continuity / state map (every frame 0-5121 belongs to exactly one row)', '',
           '| shot | clock | frames | section | world | bodies | place | support | trace / lantern |', '|---|---|---|---|---|---|---|---|---|']
    for s in S:
        out.append('| %s | %s-%s | %d-%d | %s | %s | %s | %s | %s | %s |' % (
            s['id'], tc(s['t0']), tc(s['t1']), round(s['t0'] * FPS), round(s['t1'] * FPS) - 1, esc(s['sec']), esc(s['W']), s['B'], s['P'], esc(s['sup']), esc(s['T'])))
    out += ['', '### Table 2. Shot map: lyric, action and what it changes', '',
            '| shot | author lyric (measured cue, s) | voice tag in author text | action | what changes | reference method |', '|---|---|---|---|---|---|']
    for s in S:
        out.append('| %s | %s | %s | %s | %s | %s |' % (s['id'], esc(s['lyric']), esc(s['voice']), esc(s['act']), esc(s['chg']), esc(s['ref'])))
    out += ['', '### Table 3. Body-action inserts (need new drawings or an approved generation route)', '',
            '| id | shot | span (s) | screen s | billed s per attempt (5 s minimum clip) | action |', '|---|---|---|---|---|---|']
    for s in S:
        for i, a, b, d in s['ins']:
            out.append('| %s | %s | %.1f-%.1f | %.1f | %d | %s |' % (i, s['id'], a, b, b - a, billed(b - a), esc(d)))
    ins = [i for s in S for i in s['ins']]
    out.append('| **total** | | | **%.1f** | **%d** | %d clips |' % (sum(b - a for _, a, b, _ in ins), sum(billed(b - a) for _, a, b, _ in ins), len(ins)))
    out += ['', '### Table 4. Face segments (local face rig route) and asset compatibility', '',
            '| id | shot | span (s) | s | what | compatibility of existing face material |', '|---|---|---|---|---|---|']
    for s in S:
        for i, a, b, d, c in s['face']:
            out.append('| %s | %s | %.1f-%.1f | %.1f | %s | %s |' % (i, s['id'], a, b, b - a, esc(d), esc(c)))
    fc = [f for s in S for f in s['face']]
    out.append('| **total** | | | **%.1f** | %d segments | |' % (sum(b - a for _, a, b, _, _ in fc), len(fc)))
    out += ['', '### Table 5. Asset-to-shot map (existing material each shot can use / what is missing)', '',
            '| shot | existing material | missing (not made, not invented) | animatic picture |', '|---|---|---|---|']
    for s in S:
        out.append('| %s | %s | %s | %s |' % (s['id'], esc('; '.join(s['assets'])), esc('; '.join(s['missing'])), esc(s['bg'])))
    return '\n'.join(out)


if __name__ == '__main__':
    import sys
    if '--md' in sys.argv:
        check()
        print(md())
        sys.exit()
    n = check()
    ins = [(s['id'],) + i for s in S for i in s['ins']]
    face = [(s['id'],) + f for s in S for f in s['face']]
    ti = sum(b - a for _, _, a, b, _ in ins)
    tf = sum(b - a for _, _, a, b, _, _ in face)
    print('frames covered', n, 'shots', len(S))
    print('inserts', len(ins), 'seconds %.1f' % ti, 'billed per attempt', sum(billed(b - a) for _, _, a, b, _ in ins))
    print('face segments', len(face), 'seconds %.1f' % tf)
