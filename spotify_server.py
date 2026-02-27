import os, json, time, threading, webbrowser, base64
import urllib.parse, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
PORT = 8888
REDIRECT_URI = f"http://127.0.0.1:{PORT}/callback"
SCOPE = "user-read-currently-playing user-read-playback-state"

token_data    = {}
current_track = {}

def b64(s):
    return base64.b64encode(s.encode()).decode()

def refresh_access_token():
    """Use the refresh token to get a new access token."""
    data = urllib.parse.urlencode({
        "grant_type":    "refresh_token",
        "refresh_token": token_data["refresh_token"],
    }).encode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={
            "Authorization": f"Basic {b64(CLIENT_ID + ':' + CLIENT_SECRET)}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    token_data["access_token"] = resp["access_token"]
    token_data["expires_at"]   = time.time() + resp["expires_in"] - 30
    if "refresh_token" in resp:
        token_data["refresh_token"] = resp["refresh_token"]
    print("Access token refreshed")

def exchange_code(code):
    """Exchange auth code for tokens."""
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }).encode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={
            "Authorization": f"Basic {b64(CLIENT_ID + ':' + CLIENT_SECRET)}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    token_data["access_token"]  = resp["access_token"]
    token_data["refresh_token"] = resp["refresh_token"]
    token_data["expires_at"]    = time.time() + resp["expires_in"] - 30
    print("Tokens obtained — auth complete, diva")

def fetch_current_track():
    """Poll Spotify every 3 seconds and update current_track"""
    while True:
        try:
            if not token_data.get("access_token"):
                time.sleep(1)
                continue
            if time.time() > token_data.get("expires_at", 0):
                refresh_access_token()

            req = urllib.request.Request(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            try:
                with urllib.request.urlopen(req) as r:
                    if r.status == 204:
                        current_track.clear()
                    else:
                        data = json.loads(r.read())
                        if data and data.get("item"):
                            item = data["item"]
                            current_track.update({
                                "is_playing": data.get("is_playing", False),
                                "title": item["name"],
                                "artist": ", ".join(a["name"] for a in item["artists"]),
                                "album_art": item["album"]["images"][0]["url"]if item["album"]["images"] else "",
                                "duration_ms": item["duration_ms"],
                                "progress_ms": data.get("progress_ms", 0),
                            })
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    refresh_access_token()
        except Exception as ex:
            print(f"Poll error: {ex}")
        time.sleep(3)

WIDGET_HTML_PATH = os.path.join(os.path.dirname(__file__), "widget.html")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/callback":
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                exchange_code(params["code"][0])
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"Diva, your Spotify is connected, and you may now close this tab")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code parameter")
        
        elif parsed.path == "/now-playing":
            payload = json.dumps(current_track).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)

        elif parsed.path == "/script.js":
            try:
                with open(os.path.join(os.path.dirname(__file__), "script.js"), "rb") as f:
                    js = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript")
                self.end_headers()
                self.wfile.write(js)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"script.js not found")
        elif parsed.path == "/styles.css":
            try:
                with open(os.path.join(os.path.dirname(__file__), "styles.css"), "rb") as f:
                    css = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/css")
                self.end_headers()
                self.wfile.write(css)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"styles.css not found")
        elif parsed.path in ("/", "/widget", "/widget.html"):
            try:
                with open(WIDGET_HTML_PATH, "rb") as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"widget.html not found")
        else:
            self.send_response(404)
            self.end_headers()
def open_auth():
    params = urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "response_type": "code",
        "redirect_uri":  REDIRECT_URI,
        "scope":         SCOPE,
    })
    url = f"https://accounts.spotify.com/authorize?{params}"
    print(f"\n→ Opening Spotify auth in your browser…\n  {url}\n")
    webbrowser.open(url)


if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Please set CLIENT_ID and CLIENT_SECRET in spotify_server.py first")
        exit(1)

    print(f" Starting server on http://127.0.0.1:{PORT}")
    print(f" Widget URL (add as OBS Browser Source): http://127.0.0.1:{PORT}/")

    threading.Thread(target=fetch_current_track, daemon=True).start()

    server = HTTPServer(("127.0.0.1", PORT), Handler)

    threading.Timer(0.5, open_auth).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n Server stopped.")
