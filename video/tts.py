#!/usr/bin/env python3
"""Narration for the film. ElevenLabs (Matilda, with-timestamps) when ELEVENLABS_API_KEY works; otherwise the
macOS `say` voice as a fallback with word timings from faster-whisper. Builds video/audio/narration.wav and
video/words.json ({cues:[{id,text,start,dur,words:[{w,s,e}]}], total, voice}). Cue texts come from SCRIPT.md."""
import base64, json, os, re, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio"); os.makedirs(AUDIO, exist_ok=True)
KEY = None
with open(os.path.join(HERE, "..", ".env")) as f:
    for line in f:
        if line.startswith("ELEVENLABS_API_KEY="):
            KEY = line.split("=", 1)[1].strip()
VOICE = "XrExE9yKIg1WjnnlVkGX"  # Matilda
SAY_VOICE = "Daniel"
CUES = []
for line in open(os.path.join(HERE, "SCRIPT.md")):
    m = re.match(r"^(p\d+)\.\s+(.*\S)\s*$", line)
    if m:
        CUES.append((m.group(1), m.group(2)))
GAPS = {"p1": 0.6, "p2": 0.8, "p3": 0.8, "p4": 0.8, "p5": 0.8, "p6": 0.8, "p7": 0.9, "p8": 0.8, "p9": 0.9, "p10": 0.9, "p11": 4.0}
LEAD_IN = 0.6


def eleven_ok():
    if not KEY:
        return False
    try:
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_22050_32",
                                     data=json.dumps({"text": "Check.", "model_id": "eleven_multilingual_v2"}).encode(),
                                     headers={"xi-api-key": KEY, "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=60).read()
        return True
    except Exception:
        return False


def tts_eleven(cue_id, text):
    mp3 = os.path.join(AUDIO, f"{cue_id}.mp3"); aln = os.path.join(AUDIO, f"{cue_id}.align.json")
    if not (os.path.exists(mp3) and os.path.exists(aln)):
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps",
                                     data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                                                      "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "speed": 1.0}}).encode(),
                                     headers={"xi-api-key": KEY, "Content-Type": "application/json"})
        out = json.load(urllib.request.urlopen(req, timeout=180))
        open(mp3, "wb").write(base64.b64decode(out["audio_base64"])); json.dump(out["alignment"], open(aln, "w"))
    align = json.load(open(aln))
    words, cur, start, end = [], "", None, None
    for ch, s, e in zip(align["characters"], align["character_start_times_seconds"], align["character_end_times_seconds"]):
        if ch.isspace():
            if cur:
                words.append({"w": cur, "s": start, "e": end}); cur, start = "", None
        else:
            if start is None:
                start = s
            cur += ch; end = e
    if cur:
        words.append({"w": cur, "s": start, "e": end})
    wav = os.path.join(AUDIO, f"{cue_id}.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", mp3, "-ar", "48000", "-ac", "2", wav], check=True)
    return wav, words


_WHISPER = None


def tts_say(cue_id, text):
    wav = os.path.join(AUDIO, f"{cue_id}.wav"); aiff = os.path.join(AUDIO, f"{cue_id}.aiff")
    if not os.path.exists(wav):
        subprocess.run(["say", "-v", SAY_VOICE, "-r", "168", "-o", aiff, text], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", aiff, "-ar", "48000", "-ac", "2", wav], check=True)
    global _WHISPER
    if _WHISPER is None:
        from faster_whisper import WhisperModel
        _WHISPER = WhisperModel("small.en", device="cpu", compute_type="int8")
    segs, _ = _WHISPER.transcribe(wav, word_timestamps=True, language="en", beam_size=5, initial_prompt=text)
    words = [{"w": w.word.strip(), "s": float(w.start), "e": float(w.end)} for s in segs for w in s.words]
    return wav, words


def dur_of(path):
    return float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())


def main():
    use_eleven = eleven_ok()
    print("narration voice:", "ElevenLabs Matilda" if use_eleven else f"macOS say ({SAY_VOICE}) fallback with faster-whisper timings", flush=True)
    db = {"cues": [], "voice": "elevenlabs-matilda" if use_eleven else f"macos-say-{SAY_VOICE}"}
    clock = LEAD_IN
    parts = [("silence", LEAD_IN)]
    for cue_id, text in CUES:
        wav, words = (tts_eleven if use_eleven else tts_say)(cue_id, text)
        d = dur_of(wav)
        db["cues"].append({"id": cue_id, "text": text, "start": clock, "dur": d, "words": words})
        parts.append(("file", wav)); parts.append(("silence", GAPS[cue_id]))
        clock += d + GAPS[cue_id]
        print(f"  {cue_id}: {d:.1f}s, {len(words)} words", flush=True)
    db["total"] = clock
    # concatenate with silences
    lst = os.path.join(AUDIO, "concat.txt"); sil = os.path.join(AUDIO, "_sil.wav")
    with open(lst, "w") as f:
        for kind, v in parts:
            if kind == "silence":
                p = os.path.join(AUDIO, f"_sil_{v:.2f}.wav")
                if not os.path.exists(p):
                    subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(v), p], check=True)
                f.write(f"file '{p}'\n")
            else:
                f.write(f"file '{v}'\n")
    out = os.path.join(AUDIO, "narration.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-f", "concat", "-safe", "0", "-i", lst, "-c", "pcm_s16le", out], check=True)
    json.dump(db, open(os.path.join(HERE, "words.json"), "w"), indent=1)
    print("total", round(clock, 1), "s ->", out)


if __name__ == "__main__":
    main()
