from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_ID = input("Paste your OAuth Client ID: ").strip()
CLIENT_SECRET = input("Paste your OAuth Client Secret: ").strip()
client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    }
}
flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)
print("\n" + "=" * 60)
print("Add these to your upload_to_youtube.py:")
print("=" * 60)
print("refresh_token = " + creds.refresh_token)
print("=" * 60)
