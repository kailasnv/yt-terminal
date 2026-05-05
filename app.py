from flask import Flask, render_template, send_from_directory, jsonify, request
import os, yt_dlp

app = Flask(__name__)

MUSIC_DIR = os.path.expanduser("~/Music")

def get_music_files():
    songs = []
    for file in os.listdir(MUSIC_DIR):
        if file.endswith(".mp3"):
            songs.append({
                "name": file
            })
    return sorted(songs, key=lambda x: x["name"].lower())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/songs")
def songs():
    return jsonify(get_music_files())

@app.route("/stream/<path:filename>")
def stream(filename):
    return send_from_directory(MUSIC_DIR, filename)

# add new songs to db
@app.route("/api/download", methods=["POST"])
def download_song():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(MUSIC_DIR, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return jsonify({"message": "Downloaded successfully"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
