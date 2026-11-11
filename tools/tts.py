# Usage: python3 tts.py <voice_dir> <text_file> <out.wav> [speed]
import sys, sherpa_onnx, soundfile as sf, glob, os
d, txt, out = sys.argv[1], open(sys.argv[2]).read().strip(), sys.argv[3]
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
onnx = [f for f in glob.glob(f'{d}/*.onnx')][0]
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=onnx, tokens=f'{d}/tokens.txt', data_dir=f'{d}/espeak-ng-data'), num_threads=4), max_num_sentences=1)
tts = sherpa_onnx.OfflineTts(cfg)
a = tts.generate(txt, sid=0, speed=speed)
sf.write(out, a.samples, samplerate=a.sample_rate); print(out, len(a.samples)/a.sample_rate)
