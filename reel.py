# Usage: python3 reel.py templates/<reel>.html <nscenes> <out.mp4> [secs_per_scene] [voice.mp3]
# Renders each scene (#1..#n) at 1080x1920, then builds an MP4 with slow zoom + crossfades (ffmpeg).
import sys, os, subprocess, tempfile
KEEP = '--keep' in sys.argv
sys.argv = [a for a in sys.argv if a != '--keep']
from playwright.sync_api import sync_playwright
src, n, out = os.path.abspath(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
dur = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
voice = sys.argv[5] if len(sys.argv) > 5 else None
tmp = tempfile.mkdtemp()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    for i in range(1, n + 1):
        pg.goto(f'file://{src}#{i}'); pg.reload(); pg.wait_for_timeout(800)
        pg.screenshot(path=f'{tmp}/s{i}.png')
    b.close()
fps, xf = 30, 0.5
inputs, filt = [], []
for i in range(1, n + 1):
    inputs += ['-loop', '1', '-t', str(dur), '-i', f'{tmp}/s{i}.png']
    fr = int(dur * fps)
    filt.append(f"[{i-1}:v]scale=2160:3840,zoompan=z='1+0.04*on/{fr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s=1080x1920:fps={fps},format=yuv420p[v{i}]")
last = 'v1'
for i in range(2, n + 1):
    off = (i - 1) * (dur - xf)
    filt.append(f"[{last}][v{i}]xfade=transition=fade:duration={xf}:offset={off}[x{i}]"); last = f'x{i}'
cmd = ['ffmpeg', '-y', '-loglevel', 'error'] + inputs
amap = []
if voice:
    cmd += ['-i', voice]; amap = ['-map', f'{n}:a', '-c:a', 'aac', '-b:a', '160k', '-shortest']
else:
    cmd += ['-f', 'lavfi', '-t', str(n * dur), '-i', 'anullsrc=r=44100:cl=stereo']; amap = ['-map', f'{n}:a', '-c:a', 'aac', '-shortest']
cmd += ['-filter_complex', ';'.join(filt), '-map', f'[{last}]'] + amap + ['-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-r', str(fps), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
for i in range(1, n + 1): os.rename(f'{tmp}/s{i}.png', out.replace('.mp4', f'-s{i}.png')) if KEEP else None
print(out)
