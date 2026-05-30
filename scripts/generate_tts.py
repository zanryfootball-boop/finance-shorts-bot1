import asyncio
import json
import os
import whisper
import edge_tts

VOICE = "en-US-GuyNeural"

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
        "portfolio": "port fol ee oh",
        "Portfolio": "port fol ee oh",
        "dividends": "div ih dends",
        "Dividends": "div ih dends",
        "compounding": "com pound ing",
        "Compounding": "com pound ing",
        "inflation": "in flay shun",
        "Inflation": "in flay shun",
        "amortization": "ah mor tih zay shun",
        "liquidity": "lih KWID ih tee",
        "Liquidity": "lih KWID ih tee",
        "diversification": "dih ver sih fih KAY shun",
        "Diversification": "dih ver sih fih KAY shun",
        "entrepreneur": "on treh preh NEUR",
        "Entrepreneur": "on treh preh NEUR",
        "millennials": "mih LEN ee ulz",
        "Millennials": "mih LEN ee ulz",
        "etc": "and so on",
        "vs": "versus",
        "IQ": "eye queue",
        "ROI": "return on investment",
        "ETF": "E T F",
        "S&P": "S and P",
        "401k": "four oh one k",
        "GDP": "G D P",
    }
    for word, replacement in replacements.items():
        text = text.replace(word, replacement)
    return text

def build_text(script):
    all_lines = [script["hook"]] + script["lines"]
    result = " ... ".join(all_lines)
    return result

def generate_tts(script_path="script.json", output_path="narration.mp3"):
    with open(script_path) as f:
        script = json.load(f)
    full_text = build_text(script)
    full_text = fix_pronunciation(full_text)
    print("[INFO] Synthesizing with voice: " + VOICE)
    asyncio.run(synthesize(full_text, VOICE, output_path))
    print("[OK] Narration saved: " + output_path)
    print("[INFO] Running Whisper for word timestamps...")
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
