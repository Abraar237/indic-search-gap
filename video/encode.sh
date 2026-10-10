#!/bin/bash
# frames + narration -> film_master.mp4 (1080p60, loudnorm -14 LUFS) and a poster frame
cd "$(dirname "$0")"
ffmpeg -y -loglevel error -framerate 60 -i frames/f%06d.png -i audio/narration.wav \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -af "loudnorm=I=-14:TP=-1.5:LRA=11" -movflags +faststart -shortest film_master.mp4
cp film_master.mp4 film_final.mp4
ffmpeg -y -loglevel error -ss 00:01:02 -i film_final.mp4 -frames:v 1 ../docs/assets/film-poster.png
cp film_final.mp4 ../docs/assets/film.mp4
ffprobe -v quiet -show_entries format=duration -of csv=p=0 film_final.mp4
