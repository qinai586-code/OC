"""Hand-authored head cels (ASCII pixel art). Keys index art/palette.py (GPT / CLAUDE).

Heads face front ('F'), three-quarter right ('Q'), profile right ('P') or away ('B').
Left-facing uses a horizontal flip. The eye/mouth regions of the base cels are blank skin;
expressions are separate overlays stamped at EYE/MOUTH offsets ('.' in an overlay = keep).
NECK gives the pixel (x, y) in each cel that sits on the body's neck point.
"""
from engine.px import ascii_block as A

# ================================================================== Claude
CL = {}
CL['F'] = A("""
..........oo..........
.........oLHo.........
...........oHo........
.......ooooHHoooo.....
.....ooHHHHHHHHHHoo...
....oHHHLLLHHHHHHHHo..
...oHHLLLHHHHHHHHHHHo.
...oHHHHHHHHHHHHhHHHo.
..oHHHHHHHHHHhHHHhHHHo
..oHHHHHHHhShHHHHHHHHo
..oHHHhShHSSSHhShHHHHo
..oHHhSSShSSShSSShHHHo
..oHHhSSSSSSSSSSShHHHo
..oHhSSSSSSSSSSSSShHHo
..oHhSSSSSSSSSSSSShHHo
..oHhSSSSSSSSSSSSShHHo
..oHhSSSSSSSSSSSSShHHo
..oHHhbbSSSSSSSbbhHHHo
..oHHhhSSSSSSSSShhHHHo
..oHHHhhsSSSSSshhHHHHo
..oHHHHhoSSSSSohHHHHHo
..oHHHHHHoooooHHHHHHHo
""")
CL['Q'] = A("""
...........oo.........
..........oLHo........
............oHo.......
.......oooooHHooo.....
.....ooHHHHHHHHHHoo...
....oHHHHLLLHHHHHHHo..
...oHHHHLLLHHHHHHHHHo.
..oHHHHHHHHHHHHHhHHHHo
..oHHHHHHHHHHhHHHHhHHo
.oHHHHHHHHHhHHHhSHHhHo
.oHHHHHHHhHSShHhSShHho
.oHHHHHHhSSSSShSSSSShSo
.oHHHHHhSSSSSSSSSSSSSso
.oHHHHhSSSSSSSSSSSSSSo.
.oHHHHhSSSSSSSSSSSSSSo.
.oHHHHhSSSSSSSSSSSSSso.
.oHHHHhSSSSSSSSSSSSSo..
.oHHHHHbbSSSSSSSSbSSo..
.oHHHHHhSSSSSSSSSSso...
.oHHHHHhhSSSSSSSsso....
.oHHHHHHhoSSSSSsoo.....
.oHHHHHHHhooooooo......
""")
CL['P'] = A("""
..........oo...........
.........oLHo..........
...........oHo.........
......oooooHHooo.......
....ooHHHHHHHHHHoo.....
...oHHHHHHLLLHHHHHo....
..oHHHHHHLLLHHHHHHHo...
..oHHHHHHHHHHHHHHHHHo..
.oHHHHHHHHHHHHHHHHHHHo.
.oHHHHHHHHHHHHHHHhHHHo.
.oHHHHHHHHHHHHHhHHHhHo.
.oHHHHHHHHHHHHhHSShSSo.
.oHHHHHHHHHhHHhSSSSSSo.
.oHHHHHHHHhHHhSSSSSSSo.
.oHHHHHHHhHHhSSSSSSSSSo
.oHHHHHHhHHhSSSSSSSSSSo
.oHHHHHHhHHhSSSSSSSSSo.
.oHHHHHHHhHhSSSSbSSSSo.
.oHHHHHHHhHHhSSSSSSSo..
.oHHHHHHHHhHhsSSSSSso..
.oHHHHHHHHhHHhssSSoo...
.oHHHHHHHHHhHHhooo.....
""")
CL['B'] = A("""
..........oo..........
.........oLHo.........
...........oHo........
.......ooooHHoooo.....
.....ooHHHHHHHHHHoo...
....oHHHLLLHHHHHHHHo..
...oHHLLLHHHHHHHHHHHo.
...oHHHHHHHHHHHHHHHHo.
..oHHHHHHHHHHHHHHHHHHo
..oHHHHhHHHHHHHhHHHHHo
..oHHHHhHHHHHHHhHHHHHo
..oHHHhHHHHHHHHHhHHHHo
..oHHHhHHHHHHHHHhHHHHo
..oHHHhHHHHHHHHHHhHHHo
..oHHhHHHHHHHHHHHhHHHo
..oHHhHHHHHHHHHHHHhHHo
..oHHhHHHHHHHHHHHHhHHo
..oHHhHHHHHHHHHHHHhHHo
..oHHhHHHHHHHHHHHHhHHo
..oHHhHHHHHHHHHHHHhHHo
..oHHhHHHHHHHHHHHHhHHo
..oHHhHHHHHHHHHHHHhHHo
""")
CL_NECK = {'F': (11, 21), 'Q': (12, 21), 'P': (13, 21), 'B': (11, 21)}
# eye overlay anchors: (x, y) of the top-left of each eye box, per view. Box = 5 x 4.
CL_EYES = {'F': [(5, 13), (13, 13)], 'Q': [(6, 13), (15, 13)], 'P': [(17, 13)]}
CL_MOUTH = {'F': (11, 18), 'Q': (14, 18), 'P': (20, 17)}

# ================================================================== ChatGPT
GP = {}
GP['F'] = A("""
..J....................J..
.gJ....................Jg.
.gjJ..................Jjg.
..gjJ.......oo.......Jjg..
...gjJ..ooookkoooo..Jjg...
....gjokkkkkkkkkkkkojg....
....okkKKkkkkkkkkkkkko....
...okkKKkkkkkkkkkkkkkko...
..okkkkkkkkkkkkkkkkx.xko..
..okkkkkkkkkkkkkkkkkxkko..
.okkkkkkkkkkSkkkkkkx.xkko.
.okkkkkkkSkkSSkkkSkkkkkko.
.okkkkkkSSSkSSSkSSSkSkkko.
.okkkkkSSSSSSSSSSSSSSkkko.
..okkkSSSSSSSSSSSSSSSkko..
..okkkSSSSSSSSSSSSSSSkko..
..okttSSSSSSSSSSSSSSSttko.
..okttSSSSSSSSSSSSSSSttko.
..oktkbbSSSSSSSSSSSbbktko.
..okttkSSSSSSSSSSSSSkttko.
..okTtkksSSSSSSSSSskktTko.
..okTttkkoSSSSSSSokkttTko.
..okTtTkkkoooooookkTtTko..
...okTtTko.......okTtTko..
""")
GP['Q'] = A("""
....J....................J
...gJ...................Jg
...gjJ................Jjg.
....gjJ.......oo.....Jjg..
.....gjJ..ooookkoooo.jg...
......gjookkkkkkkkkkko....
......okkkkKKkkkkkkkkko...
.....okkkkKKkkkkkkkkkkko..
....okkkkkkkkkkkkkkx.xkko.
....okkkkkkkkkkkkkkkxkkko.
...okkkkkkkkkkkkSkkx.xkko.
...okkkkkkkkkSkkSSkkSkkSko
...okkkkkkkkSSSkSSSSSSkSko
...okkkkkkkSSSSSSSSSSSSSo.
...okkkkkkSSSSSSSSSSSSSSo.
...okkkkkkSSSSSSSSSSSSSso.
...okkttkkSSSSSSSSSSSSSo..
...okktttkSSSSSSSSSSSSso..
...okktTtkbbSSSSSSSSbSSo..
...okkttTkkSSSSSSSSSSso...
...okkTtTkkksSSSSSSsso....
...okkTttTkkkoSSSSSoo.....
...okkTtTkkkkkoooooo......
....okkTTko...............
""")
GP['P'] = A("""
.....J....................
....gJ....................
....gjJ...................
.....gjJ.....oo...........
......gjJ.oookkooo........
.......gjokkkkkkkkoo......
......okkkkkkKKKkkkkko....
.....okkkkkkKKKkkkkkkko...
....okkkkkkkkkkkkkkkkkko..
....okkkkkkkkkkkkkkkkkkko.
...okkkkkkkkkkkkkkkkkSkko.
...okkkkkkkkkkkkkkkSSSkko.
...okkkkkkkkkkkkkkSSSSSSo.
...okkkkkkkkkkkkkSSSSSSSo.
...okkkkkkkkkkkkSSSSSSSSSo
...okkkkkkkkkkkkSSSSSSSSSo
...okkttkkkkkkkkSSSSSSSSo.
...okkttkkkkkkkkSSbSSSSSo.
...okkTtkkkkkkkkkSSSSSSo..
...okkTtTkkkkkkkksSSSSso..
...okkTtTkkkkkkkkkssSoo...
...okkTtTtkkkkkkkkooo.....
...okkTTtTkkkkkkkko.......
....okkTTkko...okko.......
""")
GP['B'] = A("""
..J....................J..
.gJ....................Jg.
.gjJ..................Jjg.
..gjJ.......oo.......Jjg..
...gjJ..ooookkoooo..Jjg...
....gjokkkkkkkkkkkkojg....
....okkKKkkkkkkkkkkkko....
...okkKKkkkkkkkkkkkkkko...
..okkkkkkkkkkkkkkkkkkkko..
..okkkkkkkkkrrkkkkkkkkko..
.okkkkkkkkkrRRrkkkkkkkkko.
.okkkkkkkkkkrrkkkkkkkkkko.
.okkkkkkkkkkrrkkkkkkkkkko.
.okkkkkkkkkkkkkkkkkkkkkko.
..okkkkkkkkkkkkkkkkkkkko..
..okkkkkkkkkkkkkkkkkkkko..
..okttkkkkkkkkkkkkkkkttko.
..okttkkkkkkkkkkkkkkkttko.
..oktTkkkkkkkkkkkkkkkTtko.
..okTtkkkkkkkkkkkkkkktTko.
..okTttkkkkkkkkkkkkkttTko.
..okTtTkkkkkkkkkkkkkTtTko.
..okTtTkkkkkkkkkkkkkTtTko.
...okTtTko.......okTtTko..
""")
GP_NECK = {'F': (13, 22), 'Q': (15, 22), 'P': (17, 22), 'B': (13, 22)}
GP_EYES = {'F': [(6, 14), (15, 14)], 'Q': [(9, 14), (18, 14)], 'P': [(20, 13)]}
GP_MOUTH = {'F': (13, 19), 'Q': (16, 19), 'P': (23, 18)}

# ================================================================== expression overlays
def _mirror(L):
    out = []
    for r in L:
        R = list(r[::-1])
        if 'w' in R:
            idx = [q for q, c in enumerate(R) if c in 'waA']
            R = ['a' if c == 'w' else c for c in R]
            R[idx[0]] = 'w'
        out.append(''.join(R))
    return out


# Left-eye boxes (5 wide x 4 tall); the right eye is the mirror with the highlight kept on the left.
_EYES_CL = {  # Claude: heavier upper lash -> calm, restrained
    'open':    ["eeee.", "ewaae", "SaAAe", "SSeeS"],
    'calm':    ["eeeee", "Swaae", "SaAAe", "SSeeS"],
    'wide':    ["eeee.", "ewaae", "eaAae", "SeeeS"],
    'closed':  ["SSSSS", "SSSSS", "eeeeS", "SSSSS"],
    'happy':   ["SSSSS", "SeeeS", "eSSSe", "SSSSS"],
    'worried': ["SSeee", "eeaae", "SaAAe", "SSeeS"],
    'side':    ["eeeee", "Seawe", "SeAae", "SSeeS"],
    'dot':     ["SSSSS", "SSeSS", "SSeSS", "SSSSS"],
    'down':    ["SSSSS", "eeeee", "SaaAe", "SSSSS"],
    'blank':   ["SSSSS", "SSSSS", "SSSSS", "SSSSS"],
    'sharp':   ["SSSSS", "eeeee", "SaAAe", "SSSSS"],
}
_EYES_GP = {  # ChatGPT: open, bright, quick
    'open':    ["eeee.", "eewae", "SaAAe", "SSeeS"],
    'calm':    ["SSSSS", "eeeee", "SwaAe", "SSeeS"],
    'wide':    ["eeee.", "ewaae", "eaAae", "SeeeS"],
    'closed':  ["SSSSS", "SSSSS", "eeeeS", "SSSSS"],
    'happy':   ["SSSSS", "SeeeS", "eSSSe", "SSSSS"],
    'worried': ["SSeee", "eewae", "SaAAe", "SSeeS"],
    'side':    ["eeee.", "eeawe", "SeAae", "SSeeS"],
    'dot':     ["SSSSS", "SSeSS", "SSeSS", "SSSSS"],
    'down':    ["SSSSS", "eeeee", "SaaAe", "SSSSS"],
    'sharp':   ["eeeee", "SeaAe", "SSeeS", "SSSSS"],
    'blank':   ["SSSSS", "SSSSS", "SSSSS", "SSSSS"],
}
EYES = {
    'claude': {k: (v, _mirror(v)) for k, v in _EYES_CL.items()},
    'gpt': {k: (v, _mirror(v)) for k, v in _EYES_GP.items()},
}
# far eye in 3/4 view and the only eye in profile: drop the outer column of the left-eye box
EYES_NARROW = {
    'claude': {k: [r[1:] for r in v] for k, v in _EYES_CL.items()},
    'gpt': {k: [r[1:] for r in v] for k, v in _EYES_GP.items()},
}
# profile eye (3 wide x 4): facing right, lash sweeps back
_EYES_PROF = {
    'open': ["eee", "wae", "aAe", "S.S"], 'calm': ["SSS", "eee", "aAe", "SSS"], 'wide': ["eee", "wae", "aAe", "eeS"],
    'closed': ["SSS", "SSS", "eeS", "SSS"], 'happy': ["SSS", "eeS", "SSe", "SSS"], 'worried': ["See", "wae", "aAe", "SSS"],
    'side': ["eee", "wae", "aAe", "S.S"], 'dot': ["SSS", "SeS", "SeS", "SSS"], 'down': ["SSS", "eee", "aAe", "SSS"],
    'sharp': ["eee", "aAe", "SSS", "SSS"], 'blank': ["SSS", "SSS", "SSS", "SSS"],
}
EYES_PROFILE = {'claude': _EYES_PROF, 'gpt': _EYES_PROF}

MOUTHS = {  # 3 wide x 2 tall, centred on MOUTH anchor
    'none': ["...", "..."],
    'small': [".m.", "..."],
    'flat': ["mm.", "..."],
    'smile': ["m.m", ".m."],
    'open': [".m.", ".m."],
    'o': ["mmm", "mmm"],
    'shout': ["mmm", "emm"],
    'frown': ["...", "mm."],
    'wavy': ["m.m", ".m."],
    'grin': ["mmm", ".m."],
    'chew': ["mm.", "..."],
}
