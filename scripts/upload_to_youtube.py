import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_credentials():
    creds = Credentials(
        token=None,
        refresh_token="",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="",
        client_secret="",
        scopes=SCOPES,
    )
    return creds

def upload_video(script_path="script.json", video_path="short.mp4"):
    with open(script_path) as f:
        script = json.load(f)
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": script["title"],
            "description": script["description"],
            "tags": script.get("tags", []) + ["shorts", "youtubeshorts"],
            "categoryId": "22",
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024 * 1024 * 5)
    print("[INFO] Uploading: " + script["title"])
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print("  Upload " + str(pct) + "%")
    video_id = response["id"]
    print("[OK] Uploaded! https://youtube.com/shorts/" + video_id)
    return video_id

if __name__ == "__main__":
    upload_video()
