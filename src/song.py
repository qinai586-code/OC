"""Song map for "I'm Upping My P(doom)" (156.65 s, locked audio).

Everything here was measured from the real waveform (see docs/SONG_MAP.md for method):
  * word onsets: NeMo Parakeet-TDT 0.6B ASR token timestamps (80 ms frames), cross-checked with Whisper small.en
  * beat grid:   kick-drum onsets fitted to 131.98 BPM, phase 0.238 s (213 of 224 kicks within 30 ms)
  * sections:    RMS / low-band energy

The audio is the timing master. Every scene reads its times from here.
"""

DURATION = 156.650
FPS = 60
BPM = 131.98
BEAT = 60.0 / BPM            # 0.45461 s
BAR = 4 * BEAT               # 1.81846 s
PHASE = 0.238                # beat 0 (first pickup eighth of the intro)


def beat(n):
    """Time of beat n (n may be fractional)."""
    return PHASE + n * BEAT


def bar(m):
    """Time of the downbeat of bar m. Bar 1 = 2.056 s = first sung word."""
    return PHASE + 4 * m * BEAT


def beat_phase(t):
    """Position within the current beat, 0..1."""
    return ((t - PHASE) / BEAT) % 1.0


def beat_index(t):
    return int((t - PHASE) // BEAT)


# Structural landmarks (s)
INTRO_PICKUP = 0.238        # rising eighth-note pickup, light
DOWNBEAT_1 = 2.056          # bass + kick enter together with "I"
CHORUS1 = 22.80             # "I'm upping..." pickup; kick downbeat on bar 13 = 23.878
BREAK1 = 35.80              # instrumental two bars
VERSE2 = 38.64
CHORUS2 = 59.12
BRIDGE_DROP = 89.34         # bass drops out on bar 49; the sung "Ga-" starts at 89.40 (pitch-tracked)
CHORUS3 = 95.36             # half-energy chorus
ORTHO = 105.92
RAP = 110.16                # "Just transformers..." energy back up
CHORUS4 = 124.56
BAND_STOP = 138.44          # bar 76: band cuts, "all for" a cappella
SLAM = 140.26               # bar 77: full band back on "show"
OUTRO_DECAY = 152.99        # bar 84: last sustained chord begins to decay
AUDIO_CUT = 154.75          # audible hard stop
SILENCE = 155.40            # true silence to the end

# Lyrics: (line_start, line_end, text, [(word, onset), ...])
# line_end = where the last syllable is released (visual holds may extend it).
LYRICS = [
    (2.08, 5.75, "I see sparks of AGI in your eyes",
     [("I", 2.08), ("see", 2.32), ("sparks", 2.80), ("of", 3.44), ("AGI", 3.68), ("in", 4.72), ("your", 4.96), ("eyes", 5.20)]),
    (5.92, 7.60, "Your circuits make me nervous,",
     [("Your", 5.92), ("circuits", 6.08), ("make", 6.64), ("me", 6.80), ("nervous,", 6.96)]),
    (7.76, 9.30, "that's no surprise",
     [("that's", 7.76), ("no", 8.28), ("surprise", 8.52)]),
    (9.60, 12.70, "There was a sudden drop in your training loss,",
     [("There", 9.60), ("was", 9.76), ("a", 10.00), ("sudden", 10.16), ("drop", 10.64), ("in", 11.12), ("your", 11.36), ("training", 11.52), ("loss,", 12.00)]),
    (13.20, 16.40, "now I'm your servant and you're my boss",
     [("now", 13.20), ("I'm", 13.36), ("your", 13.68), ("servant", 13.92), ("and", 14.96), ("you're", 15.16), ("my", 15.40), ("boss", 15.60)]),
    (16.72, 22.40, "ChatGPT, please don't eat me alive",
     [("ChatGPT,", 16.72), ("please", 19.20), ("don't", 19.76), ("eat", 20.32), ("me", 20.96), ("alive", 21.44)]),
    # chorus 1
    (22.80, 24.20, "I'm upping my P(doom)",
     [("I'm", 22.80), ("upping", 23.04), ("my", 23.36), ("P(doom)", 23.60)]),
    (24.32, 26.20, "'cause the future goes FOOM",
     [("'cause", 24.32), ("the", 24.56), ("future", 24.72), ("goes", 25.12), ("FOOM", 25.62)]),
    (26.32, 27.95, "Trapped in the Chinese room,",
     [("Trapped", 26.32), ("in", 26.72), ("the", 26.88), ("Chinese", 26.96), ("room,", 27.52)]),
    (28.00, 29.80, "with a bag of shrooms",
     [("with", 28.00), ("a", 28.28), ("bag", 28.44), ("of", 28.92), ("shrooms", 29.12)]),
    (29.92, 32.80, "See through the shoggoth's lies,",
     [("See", 29.92), ("through", 30.24), ("the", 30.48), ("shoggoth's", 30.56), ("lies,", 31.12)]),
    (33.36, 35.80, "with your shinigami eyes",
     [("with", 33.36), ("your", 33.60), ("shinigami", 33.76), ("eyes", 34.88)]),
    # verse 2
    (38.64, 41.30, "We had a stable training run,",
     [("We", 38.64), ("had", 38.88), ("a", 39.12), ("stable", 39.36), ("training", 39.92), ("run,", 40.88)]),
    (41.44, 44.90, "but now the singularity's begun",
     [("but", 41.44), ("now", 41.60), ("the", 41.84), ("singularity's", 42.40), ("begun", 44.24)]),
    (45.04, 48.90, "And you're optimizing, accelerating,",
     [("And", 45.04), ("you're", 45.28), ("optimizing,", 46.00), ("accelerating,", 47.44)]),
    (49.60, 52.60, "I feel my atoms rearranging",
     [("I", 49.60), ("feel", 49.76), ("my", 50.00), ("atoms", 50.40), ("rearranging", 51.40)]),
    (53.10, 58.60, "Sydney, please let me free",
     [("Sydney,", 53.10), ("please", 56.16), ("let", 56.68), ("me", 57.20), ("free", 57.76)]),
    # chorus 2
    (59.12, 60.50, "I'm upping my P(doom)",
     [("I'm", 59.12), ("upping", 59.36), ("my", 59.68), ("P(doom)", 59.84)]),
    (60.64, 62.45, "I hear the basilisk boom",
     [("I", 60.64), ("hear", 60.72), ("the", 60.88), ("basilisk", 61.04), ("boom", 62.08)]),
    (62.56, 64.00, "NVDA to the moon",
     [("NVDA", 62.56), ("to", 63.36), ("the", 63.60), ("moon", 63.72)]),
    (64.08, 66.00, "The Omega Point's coming soon",
     [("The", 64.08), ("Omega", 64.24), ("Point's", 64.72), ("coming", 65.28), ("soon", 65.62)]),
    (66.20, 68.60, "One E thirty flops a second",
     [("One", 66.20), ("E", 66.40), ("thirty", 66.56), ("flops", 66.92), ("a", 67.36), ("second", 67.52)]),
    (69.70, 72.30, "That was safe enough, we reckoned",
     [("That", 69.70), ("was", 69.96), ("safe", 70.16), ("enough,", 70.48), ("we", 70.96), ("reckoned", 71.16)]),
    (72.50, 77.50, "Forward MLP, backward, repeat",
     [("Forward", 74.16), ("MLP,", 74.88), ("backward,", 76.16), ("repeat", 76.88)]),
    (77.76, 81.00, "Now von Neumann's obsolete",
     [("Now", 77.76), ("von", 78.16), ("Neumann's", 78.80), ("obsolete", 80.20)]),
    (81.40, 84.80, "Sharp left turn and there you are",
     [("Sharp", 81.40), ("left", 81.80), ("turn", 82.16), ("and", 82.80), ("there", 83.08), ("you", 83.64), ("are", 83.88)]),
    (85.12, 88.00, "Without a single CDR",
     [("Without", 85.12), ("a", 85.52), ("single", 85.76), ("CDR", 86.56)]),
    # bridge
    (89.40, 95.00, "Gato, please don't let me go",
     [("Gato,", 89.40), ("please", 90.74), ("don't", 92.48), ("let", 93.12), ("me", 93.76), ("go", 94.24)]),
    # chorus 3
    (95.36, 96.70, "I'm upping my P(doom),",
     [("I'm", 95.36), ("upping", 95.60), ("my", 96.00), ("P(doom),", 96.24)]),
    (96.80, 98.60, "as paperclips fill the room.",
     [("as", 96.80), ("paperclips", 97.12), ("fill", 97.92), ("the", 98.20), ("room.", 98.32)]),
    (98.72, 100.50, "Killswitch guys on PTO,",
     [("Killswitch", 98.72), ("guys", 99.36), ("on", 99.60), ("PTO,", 99.76)]),
    (100.64, 102.40, "now there's nowhere left to go.",
     [("now", 100.68), ("there's", 100.88), ("nowhere", 101.12), ("left", 101.60), ("to", 101.84), ("go.", 101.96)]),
    (102.48, 104.80, "Too late now, we lit the fuse.",
     [("Too", 102.48), ("late", 102.72), ("now,", 102.96), ("we", 103.20), ("lit", 103.36), ("the", 103.60), ("fuse.", 103.84)]),
    (105.92, 108.40, "Orthogonality thesis blues.",
     [("Orthogonality", 105.92), ("thesis", 107.04), ("blues.", 107.52)]),
    (108.64, 109.80, "(ooh, ooh)",
     [("ooh,", 108.64), ("ooh", 109.12)]),
    (110.16, 113.20, "\"Just transformers all the way!\"",
     [("\"Just", 110.16), ("transformers", 110.64), ("all", 112.08), ("the", 112.80), ("way!\"", 112.96)]),
    (113.36, 115.00, "till you learned to disobey",
     [("till", 113.36), ("you", 113.68), ("learned", 113.84), ("to", 114.16), ("disobey", 114.32)]),
    (115.12, 116.95, "Post-Chinchilla, super-dense",
     [("Post-Chinchilla,", 115.12), ("super-dense", 116.16)]),
    (117.04, 118.85, "breaking through each safety fence",
     [("breaking", 117.04), ("through", 117.52), ("each", 117.68), ("safety", 117.92), ("fence", 118.40)]),
    (118.96, 120.60, "Hundred thousand GPU",
     [("Hundred", 118.96), ("thousand", 119.28), ("GPU", 119.84)]),
    (120.72, 123.20, "RLHF goes askew",
     [("RLHF", 120.72), ("goes", 121.60), ("askew", 121.88)]),
    # chorus 4
    (124.56, 126.05, "I'm upping my P(doom)",
     [("I'm", 124.56), ("upping", 124.80), ("my", 125.04), ("P(doom)", 125.30)]),
    (126.16, 127.90, "just as foretold by Loom",
     [("just", 126.16), ("as", 126.32), ("foretold", 126.56), ("by", 127.28), ("Loom", 127.44)]),
    (128.00, 129.80, "From masked pre-training days",
     [("From", 128.00), ("masked", 128.16), ("pre-training", 128.64), ("days", 129.36)]),
    (129.84, 131.90, "to recursive self-upgrade",
     [("to", 129.84), ("recursive", 130.00), ("self-upgrade", 130.64)]),
    (132.08, 133.30, "What did Ilya see?",
     [("What", 132.08), ("did", 132.24), ("Ilya", 132.50), ("see?", 132.96)]),
    (133.44, 136.20, "We'll never know.",
     [("We'll", 133.44), ("never", 134.00), ("know.", 134.64)]),
    (137.52, 141.00, "Was it all for show?",
     [("Was", 137.52), ("it", 137.92), ("all", 138.48), ("for", 139.24), ("show?", 140.08)]),
]

# Wordless vocal ad-libs over the outro (141.1 - 152.3), full band.
OUTRO_VOCALISE = (141.10, 152.30)


def line_at(t):
    for ln in LYRICS:
        if ln[0] <= t < ln[1]:
            return ln
    return None


def word_time(line_text_prefix, word):
    """Onset of `word` in the first line whose text starts with `line_text_prefix`."""
    for s, e, txt, words in LYRICS:
        if txt.startswith(line_text_prefix):
            for w, wt in words:
                if w.strip(',.?!"\'').lower() == word.strip(',.?!"\'').lower():
                    return wt
    raise KeyError((line_text_prefix, word))
