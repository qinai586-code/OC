// config.js: project settings.
//   duration: film length in seconds (78 bars at 150 BPM).
//   fps:      output frame rate. Body motion is evaluated continuously; this is only the sampling rate.
//   bpm:      song tempo. At 150 BPM one beat is exactly 24 frames at 60 fps.
//   boil:     background brush-boil rate (Hz). Characters never boil.
const PROJECT = { duration: 124.8, fps: 60, bpm: 150, offset: 0, boil: 8 };
