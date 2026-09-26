"""Assemble every chapter into the film. A chapter that fails to import is skipped with a warning
(its time range then shows the previous shot), so one broken file never blocks the others."""
import importlib, sys, traceback
import song
from engine.film import Film, Shot

CHAPTERS = ['ch01_lab', 'ch02_chorus1', 'ch03_verse2', 'ch04_chorus2', 'ch04b_chorus2', 'ch05_bridge_c3',
            'ch06_rap', 'ch07_c4', 'ch08_ending']


def _placeholder(name):
    def draw(f):
        f.cv.fill('#101018')
        f.cv.text(name, 160, 86, '#6a7fb4', align='center')
    return draw


shots = []
for ch in CHAPTERS:
    try:
        m = importlib.import_module('scenes.' + ch)
        shots += m.SHOTS
    except ModuleNotFoundError as e:
        if ch not in str(e):
            print(f'[film_def] {ch} failed: {e}', file=sys.stderr)
    except Exception as e:
        print(f'[film_def] {ch} failed to import: {e!r}', file=sys.stderr)
        traceback.print_exc(limit=2)
FILM = Film(shots, song.DURATION)
