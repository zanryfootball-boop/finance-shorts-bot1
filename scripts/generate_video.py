import json
import math
import os
import random
import subprocess
import tempfile
import requests
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO

WIDTH, HEIGHT = 1080, 1920
FPS = 30

COLOR_THEMES = {
    "money_green":    {"accent": (0, 200, 80),   "text": (255, 255, 255), "sub": (100, 255, 150), "glow": (0, 180, 60)},
    "gold_rich":      {"accent": (255, 200, 0),  "text": (255, 255, 255), "sub": (255, 220, 80),  "glow": (255, 180, 0)},
    "dark_wealth":    {"accent": (200, 160, 50), "text": (255, 255, 255), "sub": (220, 190, 100), "glow": (180, 140, 30)},
    "crypto_blue":    {"accent": (0, 150, 255),  "text": (255, 255, 255), "sub": (100, 180, 255), "glow": (0, 100, 255)},
    "platinum_white": {"accent": (200, 210, 255),"text": (255, 255, 255), "sub": (220, 225, 255), "glow": (150, 170, 255)},
}

BACKGROUND_PROMPTS = {
    "money_rain":     [
        "raining dollar bills money falling dark background cinematic 4k dramatic lighting",
        "hundred dollar bills flying through air dark luxury background cinematic",
        "money cash pile luxury wealth dark dramatic background 4k professional",
    ],
    "stock_chart":    [
        "stock market trading charts green candles financial data dark background cinematic",
        "wall street trading floor screens financial data dramatic lighting 4k",
        "cryptocurrency trading charts green uptrend dark background professional cinematic",
    ],
    "gold_bars":      [
        "shiny gold bars stacked vault wealth luxury dark dramatic lighting cinematic 4k",
        "gold coins bars wealth luxury dark background dramatic light reflection 4k",
        "treasure vault full of gold bars dark dramatic cinematic professional 4k",
    ],
    "city_skyline":   [
        "futuristic city skyline night lights financial district dark sky cinematic 4k",
        "new york city skyline night aerial view financial district dramatic 4k",
        "modern city skyscrapers night lights luxury wealth dramatic cinematic 4k",
    ],
    "crypto_network": [
        "blockchain cryptocurrency network nodes glowing blue digital dark background 4k",
        "bitcoin cryptocurrency digital network glowing dark background cinematic 4k",
        "digital blockchain technology network futuristic dark blue background 4k",
    ],
    "bank_vault":     [
        "massive bank vault door open gold inside dark dramatic lighting cinematic 4k",
        "bank safe vault interior dark dramatic gold wealth cinematic professional",
        "luxury bank vault massive door security dark dramatic cinematic 4k",
    ],
    "coin_stack":     [
        "stacks of gold coins growing wealth dark luxury background cinematic dramatic",
        "gold coins stacking up wealth growth dark dramatic luxury background 4k",
        "pile of gold silver coins wealth dark luxury dramatic cinematic 4k",
    ],
    "growth_graph":   [
        "financial growth chart going up green arrows success dark background cinematic 4k",
        "stock market growth chart uptrend green success dark background professional",
        "business financial growth success chart dark dramatic cinematic 4k professional",
    ],
}

def get_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_audio_duration(audio_path):
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())

def download_image(prompt, save_path, seed):
    clean_prompt = prompt.replace(" ", "%20")
    url = "https://image.pollinations.ai/prompt/" + clean_prompt + "?width=1280&height=1920&seed=" + str(seed) + "&nologo=true"
    print("[INFO] Downloading: " + prompt[:50] + "...")
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=90)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content)).convert("RGB")
                img = img.resize((WIDTH + 200, HEIGHT + 200), Image.LANCZOS)
                img.save(save_path)
                print("[OK] Image downloaded")
                return True
        except Exception as e:
            print("[WARN] Attempt " + str(attempt + 1) + " failed: " + str(e))
            time.sleep(5)
    fallback = Image.new("RGB", (WIDTH + 200, HEIGHT + 200), (5, 10, 5))
    fallback.save(save_path)
    return False

def prepare_image(img_path):
    img = Image.open(img_path).convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.4)
    enhancer2 = ImageEnhance.Contrast(img)
    img = enhancer2.enhance(1.2)
    return img

def apply_ken_burns(img, t, duration, style):
    iw, ih = img.size
    max_zoom = 1.08
    if style == "zoom_in":
        scale = 1.0 + (max_zoom - 1.0) * (t / duration)
    elif style == "zoom_out":
        scale = max_zoom - (max_zoom - 1.0) * (t / duration)
    elif style == "pan_right":
        scale = 1.04
    elif style == "pan_left":
        scale = 1.04
    else:
        scale = 1.0
    new_w = int(iw / scale)
    new_h = int(ih / scale)
    if style == "pan_right":
        x_offset = int((iw - new_w) * (t / duration))
        y_offset = (ih - new_h) // 2
    elif style == "pan_left":
        x_offset = int((iw - new_w) * (1 - t / duration))
        y_offset = (ih - new_h) // 2
    else:
        x_offset = (iw - new_w) // 2
        y_offset = (ih - new_h) // 2
    cropped = img.crop([x_offset, y_offset, x_offset + new_w, y_offset + new_h])
    return cropped.resize((WIDTH, HEIGHT), Image.LANCZOS)

def crossfade(img1, img2, alpha):
    arr1 = list(img1.getdata())
    arr2 = list(img2.getdata())
    blended = []
    for p1, p2 in zip(arr1, arr2):
        r = int(p1[0] * (1 - alpha) + p2[0] * alpha)
        g = int(p1[1] * (1 - alpha) + p2[1] * alpha)
        b = int(p1[2] * (1 - alpha) + p2[2] * alpha)
        blended.append((r, g, b))
    result = Image.new("RGB", (WIDTH, HEIGHT))
    result.putdata(blended)
    return result

def draw_glow_text(draw, text, font, x, y, text_color, glow_color):
    for radius in range(4, 0, -1):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius:
                    draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=text_color)

def get_current_word(timestamps, t):
    for item in timestamps:
        if item["start"] <= t <= item["end"]:
            return item["word"]
    return None

def render_frame(frame_idx, script, theme, timestamps, total_frames, bg_images, font_word, font_hook, font_small):
    t = frame_idx / FPS
    total_duration = total_frames / FPS
    num_images = len(bg_images)
    img_duration = total_duration / num_images
    fade_duration = 0.8
    img_index = min(int(t / img_duration), num_images - 1)
    time_in_img = t - img_index * img_duration
    kb_styles = ["zoom_in", "zoom_out", "pan_right", "pan_left"]
    kb_style = kb_styles[img_index % len(kb_styles)]
    current_bg = apply_ken_burns(bg_images[img_index], time_in_img, img_duration, kb_style)
    if time_in_img > img_duration - fade_duration and img_index < num_images - 1:
        next_index = img_index + 1
        next_kb = kb_styles[next_index % len(kb_styles)]
        next_bg = apply_ken_burns(bg_images[next_index], 0, img_duration, next_kb)
        alpha = (time_in_img - (img_duration - fade_duration)) / fade_duration
        alpha = max(0.0, min(1.0, alpha))
        current_bg = crossfade(current_bg, next_bg, alpha)
    img = current_bg.copy()
    draw = ImageDraw.Draw(img)
    current_word = get_current_word(timestamps, t)
    is_start = t < (timestamps[3]["end"] if len(timestamps) > 3 else 3)
    if current_word:
        font = font_hook if is_start else font_word
        word_upper = current_word.upper()
        w = draw.textlength(word_upper, font=font)
        x = (WIDTH - w) // 2
        y = HEIGHT // 2 - font.size // 2
        pad = 35
        draw.rounded_rectangle(
            [x - pad, y - pad, x + w + pad, y + font.size + pad],
            radius=25, fill=(0, 0, 0)
        )
        draw_glow_text(draw, word_upper, font, x, y, theme["text"], theme["glow"])
    progress = min(t / (total_duration), 1.0)
    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill=(20, 20, 20))
    draw.rectangle([0, HEIGHT - 12, int(WIDTH * progress), HEIGHT], fill=theme["accent"])
    title = script.get("title", "")[:55]
    tw = draw.textlength(title, font=font_small)
    tx = (WIDTH - tw) // 2
    draw.rounded_rectangle([tx - 20, 45, tx + tw + 20, 45 + font_small.size + 20], radius=12, fill=(0, 0, 0))
    draw.text((tx + 2, 57), title, font=font_small, fill=(0, 0, 0))
    draw.text((tx, 55), title, font=font_small, fill=theme["sub"])
    return img

def generate_video(script_path="script.json", audio_path="narration.mp3", timestamps_path="timestamps.json", output_path="short.mp4"):
    with open(script_path) as f:
        script = json.load(f)
    with open(timestamps_path) as f:
        timestamps = json.load(f)

    theme = COLOR_THEMES.get(script.get("color_theme", "money_green"), COLOR_THEMES["money_green"])
    font_word = get_font(100)
    font_hook = get_font(115)
    font_small = get_font(40)

    bg_style = script.get("background_style", "money_rain")
    prompts = BACKGROUND_PROMPTS.get(bg_style, BACKGROUND_PROMPTS["money_rain"])

    print("[INFO] Downloading " + str(len(prompts)) + " AI background images...")
    bg_images = []
    for i, prompt in enumerate(prompts):
        save_path = "bg_" + str(i) + ".jpg"
        seed = random.randint(1, 99999)
        download_image(prompt, save_path, seed)
        img = prepare_image(save_path)
        bg_images.append(img)
        if os.path.exists(save_path):
            os.remove(save_path)

    audio_duration = get_audio_duration(audio_path)
    print("[INFO] Audio duration: " + str(round(audio_duration, 2)) + "s")
    total_frames = int(audio_duration * FPS) + FPS
    frames_dir = tempfile.mkdtemp()

    print("[INFO] Rendering " + str(total_frames) + " frames...")
    for i in range(total_frames):
        if i % (FPS * 5) == 0:
            print("  Frame " + str(i) + "/" + str(total_frames))
        frame = render_frame(i, script, theme, timestamps, total_frames, bg_images, font_word, font_hook, font_small)
        frame.save(os.path.join(frames_dir, "frame_{:05d}.png".format(i)))

    video_no_audio = output_path.replace(".mp4", "_noaudio.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
        video_no_audio
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_no_audio,
        "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac",
        "-shortest", output_path
    ], check=True)
    os.remove(video_no_audio)
    print("[OK] Video saved: " + output_path)
    return output_path

if __name__ == "__main__":
    generate_video()