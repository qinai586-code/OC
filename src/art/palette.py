"""Film palettes. Every colour used by the characters is named here; scenes use the WORLD ramps.

The two protagonists are separated by hue as well as value:
  ChatGPT  = near-black teal + jade   (cool, dark, one bright accent)
  Claude   = copper/amber + cream     (warm, light, soft)
"""

GPT = {
    'o': '#0b0e12',   # outline / darkest
    'k': '#161c22',   # hair base (near black, teal-tinted)
    'K': '#26323a',   # hair light
    'q': '#35505a',   # hair rim highlight (cool sheen)
    't': '#2b6f68',   # teal hair streak / inner locks
    'T': '#3f9a8c',   # teal streak light
    'j': '#2f8f7c',   # jade horn base
    'J': '#6fd3bb',   # jade horn light
    'g': '#1c5249',   # jade horn shadow
    'S': '#f7e3d5',   # skin
    's': '#e7bca7',   # skin shade
    'b': '#f2a9a2',   # blush
    'e': '#0d1a1c',   # lash / eye line
    'a': '#34c3a6',   # iris jade
    'A': '#177a6b',   # iris deep
    'w': '#f2fffb',   # eye highlight
    'm': '#b8645e',   # mouth
    'W': '#ecebe7',   # blouse white
    'v': '#b9bcc6',   # blouse shade
    'r': '#1f4f4a',   # ribbon / tie dark teal
    'R': '#2f7a70',   # ribbon light
    'c': '#1a1c21',   # coat black
    'C': '#2c3038',   # coat light
    'n': '#2b6a63',   # coat teal lining
    'N': '#44988b',   # lining light
    'i': '#d9dad6',   # coat inner white trim
    'p': '#23252b',   # skirt
    'P': '#33363e',   # skirt light
    'l': '#15161a',   # legwear black
    'L': '#262830',   # legwear light
    'f': '#141518',   # shoes
    'F': '#34373f',   # shoe shine
    'x': '#5fd0b5',   # hair clip X (jade)
    'z': '#1d3134',   # tail scales dark
    'Z': '#2e4d4f',   # tail scales light
    'u': '#3b7d75',   # tail belly / teal
    'y': '#63c7ae',   # tail fin
    'Y': '#a8ecd8',   # tail fin light
    'G': '#c9a45a',   # small gold hardware
    'I': '#8ff0d4',   # iris light (portraits)
    'M': '#6e2f33',   # mouth interior
    '9': '#e0807a',   # tongue
}

CLAUDE = {
    'o': '#3e1c12',   # outline / darkest
    'd': '#a24b29',   # hair deep shadow
    'h': '#cf6b3b',   # hair shadow
    'H': '#ea8a4f',   # hair base
    'L': '#f6ab70',   # hair light
    'l': '#fcc996',   # hair sheen
    'S': '#fce9dc',   # skin
    's': '#efc3ad',   # skin shade
    'b': '#f6b1a2',   # blush
    'e': '#3a1b10',   # lash / eye line
    'a': '#eaa434',   # iris amber
    'A': '#a2601a',   # iris deep
    'w': '#fffbef',   # highlight
    'm': '#c46e5e',   # mouth
    'W': '#f7f3ec',   # blouse white
    'v': '#d6cfc6',   # blouse shade
    'r': '#3a2521',   # ribbon dark brown
    'c': '#ead6b2',   # cardigan cream
    'C': '#f6e9d2',   # cardigan light
    'n': '#c9ad86',   # cardigan shade
    'N': '#a88c68',   # cardigan deep / buttons
    'p': '#3e2a27',   # skirt dark brown
    'P': '#56403a',   # skirt light
    'q': '#2a1b19',   # skirt shadow
    'i': '#f1ebe4',   # white stocking
    'I': '#d3c9c0',   # white stocking shade
    'k': '#3b2926',   # dark stocking
    'K': '#51393a',   # dark stocking light / argyle
    'f': '#6b3b27',   # loafer
    'F': '#8e5638',   # loafer light
    'y': '#f3c443',   # star clip gold
    'Y': '#c58a22',   # star clip shade
    'x': '#fbf7ee',   # clip ribbon white
    'u': '#f8d27a',   # iris light (portraits)
    'M': '#6e2f2a',   # mouth interior
    '9': '#e0807a',   # tongue
}

KID = {
    'o': '#1d1612',
    'y': '#f0c232',   # raincoat
    'Y': '#c5941e',   # raincoat shade
    'S': '#f6d9c2',
    's': '#dcae94',
    'k': '#3b2a22',   # hair
    'e': '#1d1612',
    'r': '#c8433f',   # boots
    'R': '#8e2c2c',
    'b': '#f0a090',
}

# World ramps (dark to light). Scenes pick from these so everything shares one production palette.
NIGHT = ['#07070d', '#0e1020', '#171b33', '#222849', '#303a63', '#46568a', '#6a7fb4']
WARM = ['#1e0f0c', '#3b1d15', '#63301f', '#955030', '#c77a45', '#eaa66a', '#fbd8a5']
JADE = ['#051312', '#0b2623', '#123d38', '#1c5c52', '#2c8574', '#4fb49b', '#95e3cc']
PAPER = ['#2a2520', '#4c443b', '#7a6f60', '#a89c88', '#cfc4ae', '#e9e0cc', '#f8f3e6']
DOOM = ['#12060a', '#2c0c14', '#521422', '#86202e', '#bf3a36', '#e8744a', '#ffc27a']
STEEL = ['#0c0e12', '#1b1f27', '#2d333f', '#454d5c', '#687282', '#98a2b0', '#d2d8e0']
PINK = ['#1b0a1a', '#3a1235', '#632058', '#93357e', '#c35ea3', '#e896c8', '#fbd0e6']
GOLD = ['#1f1405', '#3f2a0a', '#6b4812', '#a0701c', '#d4a02c', '#f2cd5a', '#fff0a8']
WHITE = '#fbf8f2'
BLACK = '#050507'
