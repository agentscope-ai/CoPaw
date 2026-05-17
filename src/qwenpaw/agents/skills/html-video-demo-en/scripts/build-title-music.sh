#!/usr/bin/env bash
# build-title-music.sh — synthesize a warm ambient pad for the title scene.
#
# The result is a calm, slowly-evolving chord (A minor 9th) with reverb and a
# soft fade in/out. Total duration ~8s, designed to sit under the QwenPaw
# title card.
#
# Output: ./assets/audio/title-music.wav
set -eu
cd "$(dirname "$0")/.."

OUT="${1:-assets/audio/title-music.wav}"
mkdir -p "$(dirname "$OUT")"

# Notes (Hz): A2 110, E3 164.81, C4 261.63, G4 392, B4 493.88 — A minor 9 voicing.
# Each sine modulated very slowly + low-pass + plate reverb + gain envelope.
DURATION=8.5

ffmpeg -y -loglevel error \
  -f lavfi -i "sine=frequency=110:duration=$DURATION,volume=0.20"   \
  -f lavfi -i "sine=frequency=164.81:duration=$DURATION,volume=0.16" \
  -f lavfi -i "sine=frequency=220:duration=$DURATION,volume=0.12"   \
  -f lavfi -i "sine=frequency=261.63:duration=$DURATION,volume=0.10" \
  -f lavfi -i "sine=frequency=392:duration=$DURATION,volume=0.08"   \
  -f lavfi -i "sine=frequency=493.88:duration=$DURATION,volume=0.06" \
  -filter_complex "
    [0:a]aformat=channel_layouts=stereo:sample_rates=48000[a0];
    [1:a]aformat=channel_layouts=stereo:sample_rates=48000[a1];
    [2:a]aformat=channel_layouts=stereo:sample_rates=48000[a2];
    [3:a]aformat=channel_layouts=stereo:sample_rates=48000[a3];
    [4:a]aformat=channel_layouts=stereo:sample_rates=48000[a4];
    [5:a]aformat=channel_layouts=stereo:sample_rates=48000[a5];
    [a0][a1][a2][a3][a4][a5]amix=inputs=6:duration=longest:normalize=0[mix];
    [mix]
      aphaser=in_gain=0.4:out_gain=0.6:delay=3.0:decay=0.4:speed=0.5,
      lowpass=f=4200,
      highpass=f=70,
      aecho=0.8:0.85:60|110:0.35|0.22,
      aecho=0.8:0.85:240|410:0.22|0.18,
      tremolo=f=0.18:d=0.10,
      volume=2.6,
      afade=t=in:st=0:d=1.5,
      afade=t=out:st=$(echo "$DURATION-1.3" | bc):d=1.3
    [aout]
  " -map "[aout]" -ar 48000 -ac 2 "$OUT"

echo "wrote $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
