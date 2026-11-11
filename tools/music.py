# Original royalty-free background track: soft pads + gentle beat. Usage: python3 music.py <seconds> <out.wav>
import sys, numpy as np, soundfile as sf
T, out = float(sys.argv[1]), sys.argv[2]; sr = 44100; bpm = 100; beat = 60 / bpm
t = np.arange(int(T * sr)) / sr
def n(m): return 440 * 2 ** ((m - 69) / 12)
prog = [[60,64,67,72],[55,59,62,67],[57,60,64,69],[53,57,60,65]]  # C G Am F
bar = 4 * beat; y = np.zeros_like(t)
for i in range(int(T / bar) + 1):
    s, e = int(i*bar*sr), min(int((i+1)*bar*sr), len(t))
    if s >= len(t): break
    tt = t[s:e] - t[s]; env = np.minimum(1, tt/0.6) * np.minimum(1, (bar-tt)/0.6)
    for m in prog[i % 4]:
        f = n(m); y[s:e] += env * (0.5*np.sin(2*np.pi*f*tt) + 0.2*np.sin(2*np.pi*2*f*tt) + 0.1*np.sin(2*np.pi*f*1.003*tt)) * 0.12
    bf = n(prog[i % 4][0] - 24); y[s:e] += env * 0.25 * np.sin(2*np.pi*bf*tt)
# soft kick on beats 1 & 3, shaker on off-beats
rng = np.random.default_rng(1)
for k in range(int(T / beat)):
    s = int(k*beat*sr); L = int(0.25*sr); seg = np.arange(min(L, len(t)-s)) / sr
    if k % 2 == 0: y[s:s+len(seg)] += 0.45*np.sin(2*np.pi*(50+80*np.exp(-seg*30))*seg)*np.exp(-seg*12)
    s2 = int((k+0.5)*beat*sr); L2 = min(int(0.06*sr), len(t)-s2)
    if L2 > 0: y[s2:s2+L2] += 0.05*rng.standard_normal(L2)*np.exp(-np.arange(L2)/sr*60)
fade = np.minimum(1, np.minimum(t/1.0, (T-t)/2.0)); y *= fade
y /= np.max(np.abs(y)) + 1e-9; y *= 0.8
sf.write(out, np.stack([y, y], 1), sr); print(out)
