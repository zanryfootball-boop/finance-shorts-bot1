import json
import os
import subprocess
import whisper

def fix_pronunciation(text):
    replacements = {
        "cryptocurrency": "crypto currency",
        "Cryptocurrency": "crypto currency",
        "blockchain": "block chain",
        "Blockchain": "block chain",
        "portfolio": "port folio",
        "Portfolio": "port folio",
        "dividends": "div ih dends",
        "Dividends": "div ih dends",
        "compounding": "com pounding",
        "Compounding": "com pounding",
        "inflation": "in flay shun",
        "Inflation": "in flay shun",
        "liquidity": "lih kwid ih tee",
        "Liquidity": "lih kwid ih tee",
        "diversification": "dih ver sih fih kay shun",
        "Diversification": "dih ver sih fih kay shun",
        "entrepreneur": "on treh preh nur",
        "Entrepreneur": "on treh preh nur",
        "ROI": "return on investment",
        "ETF": "E T F",
        "S&P": "S and P",
        "401k": "four oh one k",
        "GDP": "G D P",
        "etc": "and so on",
        "vs": "versus",
    }
    for word, replacement in replacements.items():
        text = text.replace(word, replacement)
    return text

def build_text(script):
    all_lines = [script["hook"]] + script["lines"]
    return " ... ".join(all_lines)

def fallback_tts(text, output_path):
    import asyncio
    import edge_tts
    async def synthesize():
        communicate = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="-12%", pitch="-2Hz", volume="+10%")
        await communicate.save(output_path)
    asyncio.run(synthesize())
    print("[OK] Fallback edge-tts done")

def generate_tts(script_path="script.json", output_path="narration.mp3"):
    with open(script_path) as f:
        script = json.load(f)

    full_text = build_text(script)
    full_text = fix_pronunciation(full_text)

    print("[INFO] Generating voice with Kokoro TTS...")
    raw_path = output_path.replace(".mp3", "_raw.wav")

    kokoro_script = (
        "from kokoro import KPipeline\n"
        "import soundfile as sf\n"
        "import numpy as np\n"
        "pipeline = KPipeline(lang_code='a')\n"
        "text = " + repr(full_text) + "\n"
        "audio_chunks = []\n"
        "for _, _, audio in pipeline(text, voice='af_heart', speed=0.85):\n"
        "    audio_chunks.append(audio)\n"
        "if audio_chunks:\n"
        "    full_audio = np.concatenate(audio_chunks)\n"
        "    sf.write('" + raw_path + "', full_audio, 24000)\n"
        "    print('Kokoro done')\n"
    )

    with open("kokoro_run.py", "w") as f:
        f.write(kokoro_script)

    result = subprocess.run(["python3", "kokoro_run.py"], capture_output=True, text=True)
    print(result.stdout)

    if result.returncode != 0 or not os.path.exists(raw_path):
        print("[WARN] Kokoro failed: " + result.stderr[:300])
        print("[INFO] Falling back to edge-tts...")
        fallback_tts(full_text, output_path)
    else:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_path,
                "-af", "highpass=f=80,lowpass=f=12000,volume=1.5",
                "-ar", "44100", "-ac", "1",
                output_path
            ], check=True, capture_output=True)
            print("[OK] Audio enhanced")
        except Exception as e:
            print("[WARN] Enhancement failed: " + str(e))
            import shutil
            shutil.copy(raw_path, output_path)
        if os.path.exists(raw_path):
            os.remove(raw_path)

    if os.path.exists("kokoro_run.py"):
        os.remove("kokoro_run.py")

    print("[OK] Narration saved: " + output_path)
    print("[INFO] Running Whisper medium model...")
    model = whisper.load_model("medium")
    result = model.transcribe(output_path, word_timestamps=True, language="en")
    words = []
    for segment in result["segments"]:
        for word in segment.get("words", []):
            w = word["word"].strip()
            if w:
                words.append({
                    "word": w,
                    "start": round(word["start"], 3),
                    "end": round(word["end"], 3)
                })
    with open("timestamps.json", "w") as f:
        json.dump(words, f, indent=2)
    print("[OK] " + str(len(words)) + " word timestamps saved")

if __name__ == "__main__":
    generate_tts()
