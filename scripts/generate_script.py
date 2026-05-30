import json
import random
import os
from datetime import datetime
from groq import Groq

NICHES = [
    "money habits of millionaires",
    "how to save money fast",
    "investing for beginners",
    "passive income ideas that work",
    "how rich people think about money",
    "financial mistakes to avoid",
    "how to get out of debt fast",
    "stocks and investing basics",
    "how to build wealth from zero",
    "money facts that will shock you",
    "secrets of the wealthy",
    "how compound interest works",
    "side hustles that make real money",
    "budgeting tips that actually work",
    "financial freedom secrets",
]

BACKGROUNDS = [
    "money_rain",
    "stock_chart",
    "gold_bars",
    "city_skyline",
    "crypto_network",
    "bank_vault",
    "coin_stack",
    "growth_graph",
]

COLOR_THEMES = [
    "money_green",
    "gold_rich",
    "dark_wealth",
    "crypto_blue",
    "platinum_white",
]

HASHTAGS = [
    "#money #finance",
    "#investing #wealth",
    "#financialfreedom #money",
    "#richmindset #success",
    "#passiveincome #investing",
    "#stockmarket #money",
    "#moneytips #finance",
    "#wealthbuilding #rich",
    "#financetips #viral",
    "#makemoney #shorts",
    "#millionaire #mindset",
    "#budgeting #moneyhacks",
]

def generate_script():
    api_key = ""
    client = Groq(api_key=api_key)
    niche = random.choice(NICHES)
    background = random.choice(BACKGROUNDS)
    color_theme = random.choice(COLOR_THEMES)
    hashtags = random.choice(HASHTAGS)
    slot = "morning" if datetime.now().hour < 12 else "evening"
    prompt = (
        "You are a viral YouTube Shorts script writer specializing in finance and money. "
        "Write a 60-second mind-blowing script for a Short about: " + niche + "\n\n"
        "The video is for the " + slot + " audience.\n\n"
        "Rules:\n"
        "- Start with a shocking money hook that makes people stop scrolling\n"
        "- Use simple language anyone can understand\n"
        "- Each line must be short and punchy (max 10 words)\n"
        "- Include one shocking money statistic or fact\n"
        "- End with a strong call to action\n\n"
        "Return ONLY valid JSON with this exact structure:\n"
        "{\n"
        '  "title": "YouTube title (max 70 chars, money/finance focused)",\n'
        '  "description": "YouTube description (2-3 sentences) end with these exact hashtags: ' + hashtags + ' #shorts",\n'
        '  "tags": ["shorts", "youtubeshorts"],\n'
        '  "hook": "First 3 seconds hook line (shocking money fact)",\n'
        '  "lines": [\n'
        '    "Line 1 (short, shocking money fact)",\n'
        '    "Line 2",\n'
        '    "Line 3",\n'
        '    "Line 4",\n'
        '    "Line 5",\n'
        '    "Line 6",\n'
        '    "Line 7 - powerful closing + follow for more"\n'
        '  ],\n'
        '  "background_style": "' + background + '",\n'
        '  "color_theme": "' + color_theme + '"\n'
        "}"
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.9,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    script = json.loads(raw)
    script["niche"] = niche
    script["generated_at"] = datetime.utcnow().isoformat()
    with open("script.json", "w") as f:
        json.dump(script, f, indent=2)
    print("[OK] Script generated: " + script["title"])
    return script

if __name__ == "__main__":
    generate_script()
