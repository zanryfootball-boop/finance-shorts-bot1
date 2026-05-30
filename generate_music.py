import subprocess
import math
import os
import struct
import wave
import random

def generate_cinematic_music(output_path="music.wav", duration=70):
    sample_rate = 44100
    total_samples = int(sample_rate * duration)
    samples = []

    def sine(freq, t, amp=0.3):
        return amp * math.sin(2 * math.pi * freq * t)

    def note(base, t, amp=0.15):
        return (
            sine(base, t, amp) +
            sine(base * 2, t, amp * 0.4) +
            sine(base * 3, t, amp * 0.2)
        )

    chord_progression = [
        [130.81, 164.81, 196.00],
        [146.83, 185.00, 220.00],
        [123.47, 155.56, 185.00],
        [138.59, 174.61, 207.65],
    ]

    for i in range(total_samples):
        t = i / sample_rate
        chord_idx = int(t / (duration / len(chord_progression))) % len(chord_progression)
        chord = chord_progression[chord_idx]
        s = 0
        for freq in chord:
            s += note(freq, t, 0.08)
        fade_in = min(1.0, t / 3.0)
        fade_out = min(1.0, (duration - t) / 3.0)
        envelope = fade_in * fade_out
        beat = 0.5 + 0.5 * math.sin(2 * math.pi * 0.5 * t)
        s = s * envelope * (0.7 + 0.3 * beat)
        s = max(-0.9, min(0.9, s))
        samples.append(int(s * 32767))

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for sample in samples:
            wf.writeframes(struct.pack("<h", sample))

    print("[OK] Background music generated: " + output_path)
    return output_path

def mix_audio(voice_path, music_path, output_path):
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", voice_path,
            "-i", music_path,
            "-filter_complex",
            "[0:a]volume=1.8[voice];[1:a]volume=0.12[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[out]",
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
