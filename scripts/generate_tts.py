import asyncio
import json
import os
import whisper
import edge_tts
import subprocess

VOICE = "en-US-AndrewNeural"

async def synthesize(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice, rate="-5%", pitch="+0Hz")
    await communicate.save(output_path)

def fix_pronunciation(text):
    replacements = {
        "cryptocurrency": "crypto currency",
        "Cryptocurrency": "crypto currency",
        "cryptocurrencies": "crypto currencies",
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
        "amortization": "amor tih zay shun",
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
        "IQ": "eye queue",
    }
    for word, replacement in replacements.items():
        text = text.replace(word, replacement)
    return text

def build_text(script):
    all_lines = [script["hook"]] + script["lines"]
    return " ... ".join(all_lines)

def enhance_audio(input_path, output_path):
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-af", "highpass=f=80,lowpass=f=12000,volume=1.5",
            "-ar", "44100", "-ac", "1",
            output_path
        ], check=True, capture_output=True)
        print("[OK] Audio enhanced")
    except Exception as e:
        print("[WARN] Enhancement failed: " + str(e))
        import shutil
        shutil.copy(input_path, output_path)

def generate_tts(script_path="script.json", output_path="narration.mp3"):
    with open(script_path) as f:
        script = json.load(f)
    full_text = build_text(script)
    full_text = fix_pronunciation(full_text)
    print("[INFO] Synthesizing with voice: " + VOICE)
    raw_path = output_path.replace(".mp3", "_raw.mp3")
    asyncio.run(synthesize(full_text, VOICE, raw_path))
    enhance_audio(raw_path, output_path)
    if os.path.exists(raw_path):
        os.remove(raw_path)
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
