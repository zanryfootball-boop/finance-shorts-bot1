import os
import sys
import traceback
from datetime import datetime

def log(msg):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print("[" + ts + "] " + msg, flush=True)

def run():
    log("=== Finance Shorts Bot Starting ===")
    log("Step 1/5: Generating script...")
    from generate_script import generate_script
    script = generate_script()
    log("Niche: " + script["niche"])
    log("Title: " + script["title"])
    log("Step 2/5: Generating TTS narration...")
    from generate_tts import generate_tts
    generate_tts()
    log("Step 3/5: Generating background music...")
    from generate_music import generate_cinematic_music
    generate_cinematic_music()
    log("Step 4/5: Rendering video...")
    from generate_video import generate_video
    generate_video()
    log("Step 5/5: Uploading to YouTube...")
    from upload_to_youtube import upload_video
    video_id = upload_video()
    log("=== Done! https://youtube.com/shorts/" + video_id + " ===")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print("[ERROR] Pipeline failed: " + str(e), file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
