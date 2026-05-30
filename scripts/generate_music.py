import subprocess
import os
import requests
import random

MUSIC_TRACKS = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
]

def download_music(output_path="music.mp3"):
    track = random.choice(MUSIC_TRACKS)
    print("[INFO] Downloading background music: " + track)
    try:
        response = requests.get(track, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print("[OK] Music downloaded")
            return True
    except Exception as e:
        print("[WARN] Music download failed: " + str(e))
    return False

def generate_cinematic_music(output_path="music.wav", duration=70):
    mp3_path = "music_raw.mp3"
    success = download_music(mp3_path)
    if success:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", mp3_path,
                "-af", "volume=0.08,afade=t=in:st=0:d=3,afade=t=out:st=" + str(duration - 3) + ":d=3",
                "-t", str(duration),
                "-ar", "44100",
                output_path
            ], check=True, capture_output=True)
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            print("[OK] Music prepared: " + output_path)
            return output_path
        except Exception as e:
            print("[WARN] Music processing failed: " + str(e))
    print("[INFO] Generating fallback music...")
    return generate_fallback_music(output_path, duration)

def generate_fallback_music(output_path, duration):
    import math
    import struct
    import wave
    sample_rate = 44100
    total_samples = int(sample_rate * duration)
    samples = []
    chord_freqs = [130.81, 164.81, 196.00, 246.94]
    for i in range(total_samples):
        t = i / sample_rate
        s = 0
        for freq in chord_freqs:
            s += 0.06 * math.sin(2 * math.pi * freq * t)
            s += 0.03 * math.sin(2 * math.pi * freq * 2 * t)
        fade_in = min(1.0, t / 3.0)
        fade_out = min(1.0, (duration - t) / 3.0)
        s = s * fade_in * fade_out
        s = max(-0.9, min(0.9, s))
        samples.append(int(s * 32767))
    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for sample in samples:
            wf.writeframes(struct.pack("<h", sample))
    print("[OK] Fallback music generated")
    return output_path

def mix_audio(voice_path, music_path, output_path):
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", voice_path,
            "-i", music_path,
            "-filter_complex",
            "[0:a]volume=1.8[voice];[1:a]volume=0.10[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-ar", "44100",
            output_path
        ], check=True, capture_output=True)
        print("[OK] Audio mixed with background music")
    except Exception as e:
        print("[WARN] Mix failed, using voice only: " + str(e))
        import shutil
        shutil.copy(voice_path, output_path)

if __name__ == "__main__":
    generate_cinematic_music()
