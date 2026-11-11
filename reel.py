# Usage: python3 reel.py templates/<reel>.html <nscenes> <out.mp4> [secs_per_scene] [voice.wav] [music.wav]
# Voice starts at 0.5 s; music is mixed quietly underneath (ducked while the voice speaks).
# Renders each scene (#1..#n) at 1080x1920, then builds an MP4 with slow zoom + crossfades (ffmpeg).
import sys, os, subprocess, tempfile
KEEP = '--keep' in sys.argv
sys.argv = [a for a in sys.argv if a != '--keep']
from playwright.sync_api import sync_playwright
src, n, out = os.path.abspath(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
dur = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
voice = sys.argv[5] if len(sys.argv) > 5 else None
music = sys.argv[6] if len(sys.argv) > 6 else None
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
total = n * dur - (n - 1) * xf
if voice and music:
    mix = f'{tmp}/mix.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', voice, '-i', music, '-filter_complex',
        f"[0:a]adelay=500|500,aformat=sample_rates=44100:channel_layouts=stereo,volume=1.4,apad,atrim=0:{total}[vo];"
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.18,apad,atrim=0:{total}[bg];"
        f"[vo][bg]amix=inputs=2:normalize=0,afade=t=out:st={total-1.5}:d=1.5[a]", '-map', '[a]', mix], check=True)
    cmd += ['-i', mix]
    amap = ['-map', f'{n}:a', '-c:a', 'aac', '-b:a', '192k', '-shortest']
elif voice:
    cmd += ['-i', voice]
    filt.append(f"[{n}:a]adelay=500|500,apad,atrim=0:{total}[aout]")
    amap = ['-map', '[aout]', '-c:a', 'aac', '-b:a', '192k']
else:
    cmd += ['-f', 'lavfi', '-t', str(total), '-i', 'anullsrc=r=44100:cl=stereo']; amap = ['-map', f'{n}:a', '-c:a', 'aac', '-shortest']
cmd += ['-filter_complex', ';'.join(filt), '-map', f'[{last}]'] + amap + ['-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-r', str(fps), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
for i in range(1, n + 1): os.rename(f'{tmp}/s{i}.png', out.replace('.mp4', f'-s{i}.png')) if KEEP else None
print(out)
