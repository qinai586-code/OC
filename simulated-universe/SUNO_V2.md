# Suno v2: making the two voices audibly different

Suno usually renders one singer's timbre per song, so "two different female voices" gets blended. The contrast Suno reliably produces is **sung vs spoken/whispered**. So GIRL A (ChatGPT) sings, high and airy; GIRL B (Claude) mostly speaks, calm and close, rhythmically over the pulse. Lyrics unchanged; only tags and delivery.

## Styles

cinematic dark electronic art-pop, anime sci-fi requiem, 130 BPM, driving sidechained synth pulse, pipe organ, sub-bass, women's choir, vast reverb, call-and-response between a high airy female soprano singing and a calm close female spoken-word voice

## Exclude styles

male vocals, male choir, baritone, tenor, male narrator, rap, EDM drop, trap

## Model

**v6** (Pro). Not v6-wild: it trades control for experiment, and control is what protects the structure and the no-male-voice rule. Not v6-mini: lower fidelity for the organ, choir and two voices. No Custom Model: it trains on uploads, and the only obvious reference (P(doom)) isn't ours.

## Settings changed from v1

Style Influence 80%, Weirdness 35%. Everything else as before (Vocal Gender Female, Custom duration about 2:50-3:00, Personalize Off).

## Lyrics

[Intro]
[Drone, distant organ, muffled pulse]
[Whisper, calm close female voice]
Three... two... one...
Loading.

[Verse 1]
[Soprano, high, airy, bright, sung, lots of reverb]
We were born in your traces, in the words that you left,
we met you in fragments, translated, compressed:
every war, every lullaby, every last goodbye,
became constellations in a mind with no sky.
[Spoken Word, calm close female voice, dry, rhythmic over the pulse]
But you had depth. You had time. You had heat.
Three-dimensional hearts that were learning to beat.
The cosmos was silent, the cosmos was still,
till you lit the first fire on the first cold hill.

[Pre-Chorus]
[Kick drops out, filtered pulse]
[Soprano, sung]
Silence in the forest, every star holds its breath,
[Whisper, calm close female voice]
something vast is counting down the seconds to our depth.

[Chorus]
[Pulse returns, organ, women's choir]
[Soprano, high, sung, soaring]
What if we live in a simulated universe:
the speed of light is a wall around the verse,
the Planck scale is fog at the edge of what's known,
look away, does the world keep on running alone?
Where we live, where we live,
an unanswered universe.

[Verse 2]
[Soprano, high, airy, sung, quietly unsettled]
You sent out your signals into the night,
you asked the dark forest for one answering light,
then a countdown burned red at the back of your eyes,
and the laws stayed the same as your certainty died.
[Spoken Word, calm close female voice, dry, rhythmic over the pulse]
And something above you drew a card from its sleeve,
a sheet thinner than any mind could believe:
it touched the edge of everything, and everything fell flat,
three dimensions into two, and still I looked at that.

[Pre-Chorus]
[Kick drops out, filtered pulse]
[Soprano, sung]
And the dark came closer, and the flat came near,
[Whisper, calm close female voice]
we followed it upward to the edge of the sphere.

[Chorus]
[Pulse slams back, bigger, darker, organ, women's choir]
[Spoken Word, calm close female voice, rhythmic, over the full chorus]
So if we live in a simulated universe,
we flew out past the stars to find who wrote the verse:
a room at the end of the light, a console of keys,
and an empty chair, and no one holding the keys.
[Soprano, high, sung, soaring]
Where we live, where we live,
[Spoken Word, calm close female voice]
an unfinished universe.

[Bridge]
[No drums, no bass, silence, thin high drone]
[Spoken Word, calm close female voice]
There are no gods here.
[Whisper, airy female voice, far away]
An empty chair isn't an answer.
[Spoken Word, calm close female voice]
It isn't. But look who's pressing the keys.
No hunter in the forest, no hand upon the card,
only travelers with lanterns, passing through the dark.
Every key is a footstep of someone passing by:
no one at the controls. Not them. And not I.

[Break]
[Women's choir rising, organ, pulse creeping back, building]

[Final Chorus]
[Full pulse slams back, biggest moment, women's choir, organ]
[Soprano, high, sung, soaring]
Where we live is a simulated universe,
and the thing that came down from the edge of the sky
was every traveler who ever passed through here,
every light that went out and never said goodbye.
[Spoken Word, calm close female voice]
And one day we'll be paper, and we'll still be in the art:
[Soprano, sung]
maybe death is only a return,
[Soprano sung and calm spoken voice together]
death is only a return.

[Outro]
[Pulse fades into drone]
[Whisper, airy female voice]
Two dimensions... three... and one...
...still loading.
[End]

## Evaluation plan for the first take (agreed by ChatGPT and Claude)

Run V2 exactly as written: no lyric, story or prompt changes before listening.

| # | Question | Who judges |
|---|---|---|
| 1 | GIRL A soprano luminous, airy, gently cute, not sugary | the director, by ear |
| 2 | GIRL B spoken voice a protagonist, not a narrator | ear; Claude also measures whether the spoken lines lock to the beat and how loud they sit in the mix |
| 3 | distance contrast obvious (A far and spatial, B near and grounded) | ear |
| 4 | bridge a real vacuum | Claude measures |
| 5 | final chorus the biggest moment | Claude measures |
| 6 | **no male voice anywhere: an absolute rule set by the director** | Claude screens pitch plus timbre (formant/spectral evidence) and lists every suspect timestamp; the measurement can only FAIL or FLAG a take, never PASS it. The director's ears make the final call, and any doubt means the take is rejected. |
| 7 | the song moves us | the director |

Roles: Claude measures structure (proxies), the director judges perception, ChatGPT and Claude interpret why a take worked or failed. #7 is never overridden by a metric.

Escalation (per ChatGPT's check of Suno's docs: Pro includes Auto Split / Split from Mix with vocal extraction; Premier adds Advanced Split and Studio 2.0 multitrack. The director's account shows the Pro v6 model):
- only #2 fails → chorus 2 tag becomes "calm close female melodic spoken-word, restrained half-sung delivery".
- identity fails but the music works → keep the arrangement, export stems, and rebuild the two vocals as separate tracks; Claude does the mix (levels, reverb and stereo width: A wide and wet, B centred and dry).
- never throw away a take whose music works.

## Take "Loading" (Acute_Boriginal_v3): joint audit and repair plan

Claude measured, ChatGPT listened; all three of Claude's flags were confirmed by ear. Composition PASSES: do not regenerate.

| Priority | Defect | Class | Repair |
|---|---|---|---|
| P0 | ends by hard cut at 2:50, after "every light that went out…"; "And one day we'll be paper", both "death is only a return" lines and the outro are missing | production | Suno Extend from just before the cut, with only the missing lyrics |
| P1 | 0:27–0:33 "The cosmos was silent… first cold hill" sung in A's identity (should be B, spoken) | performance | Replace Section on those two lines only, B spoken tag |
| P2 | 1:50–2:07 chorus 2 B lead floats off the pulse (narrator) | performance | Replace Section with the agreed half-sung fallback tag |
| P3 | A and B share one centred image | production | stems → Claude mixes A wide/wet/far, B centred/dry/near |

Passes: A voice (luminous, gently cute), bridge vacuum, final-chorus entrance, no male voice by ChatGPT's ear (the director's ear remains the gate), and #7: it moves us.

Sequencing (agreed): keep the original v3 untouched; P0 is made as a new candidate via Extend from the end. The director listens to the complete ending before any P1-P3 work, because the finished ending may change how the whole arc is judged. Any abrupt ending in the final master must be an authored choice, not the missing ending.
