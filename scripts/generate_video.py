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
SAFE_TOP = 120
SAFE_BOTTOM = 120
SUBTITLE_Y = int(HEIGHT * 0.72)

COLOR_THEMES = {
    "money_green":    {"accent": (0, 200, 80),   "text": (255, 255, 255), "highlight": (0, 255, 100),  "glow": (0, 180, 60),  "dim": (180, 180, 180)},
    "gold_rich":      {"accent": (255, 200, 0),  "text": (255, 255, 255), "highlight": (255, 235, 80),  "glow": (255, 180, 0),  "dim": (180, 180, 180)},
    "dark_wealth":    {"accent": (200, 160, 50), "text": (255, 255, 255), "highlight": (240, 200, 80),  "glow": (180, 140, 30), "dim": (180, 180, 180)},
    "crypto_blue":    {"accent": (0, 150, 255),  "text": (255, 255, 255), "highlight": (80, 200, 255),  "glow": (0, 100, 255),  "dim": (180, 180, 180)},
    "platinum_white": {"accent": (200, 210, 255),"text": (255, 255, 255), "highlight": (255, 255, 255), "glow": (180, 190, 255),"dim": (180, 180, 180)},
}

BACKGROUND_PROMPTS = {
    "money_rain":     [
        "raining hundred dollar bills dark cinematic dramatic luxury 4k professional",
        "money cash flying through air dark background luxury cinematic professional",
        "dollar bills falling slow motion dark dramatic cinematic luxury 4k",
    ],
    "stock_chart":    [
        "wall street stock market trading screens green charts dark cinematic 4k",
        "financial trading floor screens data green uptrend dramatic 4k professional",
        "stock market bull run green charts dark luxury cinematic professional 4k",
    ],
    "gold_bars":      [
        "gold bars stacked vault dark dramatic luxury cinematic 4k professional",
        "shining gold ingots wealth vault dark dramatic professional 4k cinematic",
        "gold treasure vault dark dramatic luxury cinematic reflection 4k",
    ],
    "city_skyline":   [
        "new york city skyline night aerial financial district dark 4k cinematic",
        "futuristic city skyscrapers night lights wealth dramatic cinematic professional",
        "manhattan skyline night luxury wealth dark dramatic cinematic 4k",
    ],
    "crypto_network": [
        "bitcoin blockchain network glowing blue dark digital cinematic 4k",
        "cryptocurrency digital network nodes glowing dark futuristic 4k professional",
        "blockchain technology network blue glowing dark cinematic professional 4k",
    ],
    "bank_vault":     [
        "massive bank vault door open gold dark dramatic cinematic 4k",
        "luxury bank safe interior gold dark dramatic professional 4k cinematic",
        "bank vault door dark dramatic wealth cinematic 4k professional",
    ],
    "coin_stack":     [
        "gold coins stacking wealth dark luxury dramatic cinematic 4k",
        "pile of gold coins wealth dark luxury dramatic professional 4k",
        "gold silver coins growing stack dark cinematic luxury 4k",
    ],
    "growth_graph":   [
        "financial growth chart green upward dark success cinematic 4k professional",
        "stock market growth uptrend success dark dramatic professional 4k",
        "business financial success chart dark dramatic cinematic 4k professional",
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
    print("[INFO] Downloading: " + prompt[:55] + "...")
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=90)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content)).convert("RGB")
                img = img.resize((WIDTH + 300, HEIGHT + 300), Image.LANCZOS)
                img.save(save_path)
                print("[OK] Downloaded!")
                return True
        except Exception as e:
            print("[WARN] Attempt " + str(attempt + 1) + ": " + str(e))
            time.sleep(5)
    fallback = Image.new("RGB", (WIDTH + 300, HEIGHT + 300), (5, 10, 5))
    fallback.save(save_path)
    return False

def prepare_image(img_path):
    img = Image.open(img_path).convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img = ImageEnhance.Brightness(img).enhance(0.38)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    return img

def apply_ken_burns(img, t, duration, style):
    iw, ih = img.size
    max_zoom = 1.10
    if style == "zoom_in":
        scale = 1.0 + (max_zoom - 1.0) * (t / max(duration, 0.001))
    elif style == "zoom_out":
        scale = max_zoom - (max_zoom - 1.0) * (t / max(duration, 0.001))
    elif style == "pan_right":
        scale = 1.05
    elif style == "pan_left":
        scale = 1.05
    else:
        scale = 1.0
    new_w = int(iw / scale)
    new_h = int(ih / scale)
    if style == "pan_right":
        x_offset = int((iw - new_w) * (t / max(duration, 0.001)))
        y_offset = (ih - new_h) // 2
    elif style == "pan_left":
        x_offset = int((iw - new_w) * (1 - t / max(duration, 0.001)))
        y_offset = (ih - new_h) // 2
    else:
        x_offset = (iw - new_w) // 2
        y_offset = (ih - new_h) // 2
    cropped = img.crop([x_offset, y_offset, x_offset + new_w, y_offset + new_h])
    return cropped.resize((WIDTH, HEIGHT), Image.LANCZOS)

def crossfade(img1, img2, alpha):
    return Image.blend(img1.convert("RGB"), img2.convert("RGB"), alpha)

def draw_subtitle(draw, word, font, theme, y_pos):
    if not word:
        return
    word_upper = word.upper()
    w = draw.textlength(word_upper, font=font)
    x = (WIDTH - w) // 2
    pad_x = 40
    pad_y = 22
    box_x0 = x - pad_x
    box_y0 = y_pos - pad_y
    box_x1 = x + w + pad_x
    box_y1 = y_pos + font.size + pad_y
    draw.rounded_rectangle([box_x0, box_y0, box_x1, box_y1], radius=20, fill=(0, 0, 0))
    a = theme["accent"]
    draw.rounded_rectangle(
        [box_x0 - 3, box_y0 - 3, box_x1 + 3, box_y1 + 3],
        radius=22, outline=a, width=3
    )
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if abs(dx) + abs(dy) <= 3:
                draw.text((x + dx, y_pos + dy), word_upper, font=font, fill=theme["glow"])
    draw.text((x + 2, y_pos + 2), word_upper, font=font, fill=(0, 0, 0))
    draw.text((x, y_pos), word_upper, font=font, fill=theme["highlight"])

def get_current_word(timestamps, t):
    for item in timestamps:
        if item["start"] <= t <= item["end"]:
            return item["word"]
    return None

def add_vignette(img):
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    for r in range(min(WIDTH, HEIGHT) // 2, 0, -2):
        alpha = int(120 * (1 - r / (min(WIDTH, HEIGHT) / 2)) ** 2)
        draw.ellipse(
            [WIDTH // 2 - r, HEIGHT // 2 - r, WIDTH // 2 + r, HEIGHT // 2 + r],
            outline=(0, 0, 0, alpha), width=2
        )
    return Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

def render_frame(frame_idx, script, theme, timestamps, total_frames, bg_images, font_sub, font_hook, font_small, font_title, audio_duration):
    t = frame_idx / FPS
    total_duration = audio_duration
    num_images = len(bg_images)
    img_duration = total_duration / num_images
    fade_duration = 1.0
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
        current_bg = crossfade(current_bg, next_bg, max(0.0, min(1.0, alpha)))
    img = add_vignette(current_bg)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, WIDTH, SAFE_TOP], fill=(0, 0, 0, 200))
    od.rectangle([0, HEIGHT - SAFE_BOTTOM, WIDTH, HEIGHT], fill=(0, 0, 0, 200))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    INTRO_DURATION = 2.0
    OUTRO_START = total_duration - 2.5
    if t < INTRO_DURATION:
        fade_alpha = min(1.0, t / 0.6)
        title = script.get("title", "")[:50]
        tw = draw.textlength(title, font=font_title)
        tx = (WIDTH - tw) // 2
        ty = HEIGHT // 2 - font_title.size // 2
        pad = 45
        title_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        tod = ImageDraw.Draw(title_overlay)
        tod.rounded_rectangle(
            [tx - pad, ty - pad, tx + tw + pad, ty + font_title.size + pad],
            radius=30, fill=(0, 0, 0, int(220 * fade_alpha))
        )
        a = theme["accent"]
        tod.rounded_rectangle(
            [tx - pad - 4, ty - pad - 4, tx + tw + pad + 4, ty + font_title.size + pad + 4],
            radius=34, outline=(a[0], a[1], a[2], int(255 * fade_alpha)), width=4
        )
        img = Image.alpha_composite(img.convert("RGBA"), title_overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if abs(dx) + abs(dy) <= 2:
                    draw.text((tx + dx, ty + dy), title, font=font_title, fill=theme["glow"])
        draw.text((tx, ty), title, font=font_title, fill=theme["highlight"])
    elif t > OUTRO_START:
        fade_alpha = min(1.0, (t - OUTRO_START) / 0.6)
        outro_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, int(200 * fade_alpha)))
        img = Image.alpha_composite(img.convert("RGBA"), outro_overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        follow_text = "FOLLOW FOR MORE"
        fw = draw.textlength(follow_text, font=font_hook)
        fx = (WIDTH - fw) // 2
        fy = HEIGHT // 2 - font_hook.size // 2
        pad = 45
        a = theme["accent"]
        draw.rounded_rectangle(
            [fx - pad, fy - pad, fx + fw + pad, fy + font_hook.size + pad],
            radius=30, fill=(0, 0, 0)
        )
        draw.rounded_rectangle(
            [fx - pad - 4, fy - pad - 4, fx + fw + pad + 4, fy + font_hook.size + pad + 4],
            radius=34, outline=a, width=4
        )
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if abs(dx) + abs(dy) <= 3:
                    draw.text((fx + dx, fy + dy), follow_text, font=font_hook, fill=theme["glow"])
        draw.text((fx, fy), follow_text, font=font_hook, fill=theme["highlight"])
    else:
        current_word = get_current_word(timestamps, t)
        is_hook = t < (timestamps[3]["end"] if len(timestamps) > 3 else 3)
        font = font_hook if is_hook else font_sub
        if current_word:
            draw_subtitle(draw, current_word, font, theme, SUBTITLE_Y)
    progress = min(t / total_duration, 1.0)
    bar_y = HEIGHT - SAFE_BOTTOM + 15
    draw.rectangle([40, bar_y, WIDTH - 40, bar_y + 6], fill=(60, 60, 60))
    draw.rectangle([40, bar_y, 40 + int((WIDTH - 80) * progress), bar_y + 6], fill=theme["accent"])
    draw.ellipse([
        40 + int((WIDTH - 80) * progress) - 8, bar_y - 5,
        40 + int((WIDTH - 80) * progress) + 8, bar_y + 11
    ], fill=theme["highlight"])
    niche_text = script.get("niche", "").upper()[:40]
    nw = draw.textlength(niche_text, font=font_small)
    nx = (WIDTH - nw) // 2
    draw.text((nx, 45), niche_text, font=font_small, fill=theme["highlight"])
    return img

def generate_video(script_path="script.json", audio_path="narration.mp3", timestamps_path="timestamps.json", output_path="short.mp4"):
    with open(script_path) as f:
        script = json.load(f)
    with open(timestamps_path) as f:
        timestamps = json.load(f)
    theme = COLOR_THEMES.get(script.get("color_theme", "money_green"), COLOR_THEMES["money_green"])
    font_sub   = get_font(96)
    font_hook  = get_font(86)
    font_small = get_font(34)
    font_title = get_font(52)
    bg_style = script.get("background_style", "money_rain")
    prompts = BACKGROUND_PROMPTS.get(bg_style, BACKGROUND_PROMPTS["money_rain"])
    print("[INFO] Downloading " + str(len(prompts)) + " AI images...")
    bg_images = []
    for i, prompt in enumerate(prompts):
        save_path = "bg_" + str(i) + ".jpg"
        seed = random.randint(1, 99999)
        download_image(prompt, save_path, seed)
        img = prepare_image(save_path)
        bg_images.append(img)
        if os.path.exists(save_path):
            os.remove(save_path)
    final_audio = audio_path
    audio_duration = get_audio_duration(final_audio)
    print("[INFO] Audio duration: " + str(round(audio_duration, 2)) + "s")
    total_frames = int(audio_duration * FPS) + FPS
    frames_dir = tempfile.mkdtemp()
    print("[INFO] Rendering " + str(total_frames) + " frames...")
    for i in range(total_frames):
        if i % (FPS * 5) == 0:
            print("  Frame " + str(i) + "/" + str(total_frames))
        frame = render_frame(i, script, theme, timestamps, total_frames, bg_images, font_sub, font_hook, font_small, font_title, audio_duration)
        frame.save(os.path.join(frames_dir, "frame_{:05d}.png".format(i)))
    video_no_audio = output_path.replace(".mp4", "_noaudio.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "18",
        video_no_audio
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_no_audio,
        "-i", final_audio,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", output_path
    ], check=True)
    os.remove(video_no_audio)
    if os.path.exists("final_audio.mp3"):
        os.remove("final_audio.mp3")
    if os.path.exists("music.wav"):
        os.remove("music.wav")
    print("[OK] Video saved: " + output_path)
    return output_path

if __name__ == "__main__":
    generate_video()
