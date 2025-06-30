from flask import Flask, request, send_file
import os
import subprocess

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        print("🔁 /generate called")
        audio = request.files["audio"]
        video = request.files["video"]
        subs = request.files["subtitles"]

        audio.save("audio.mp3")
        print("✅ Audio saved")
        video.save("background.mp4")
        print("✅ Video saved")
        subs.save("subs.srt")
        print("✅ Subtitles saved")

        output = "output.mp4"

        command = [
            "ffmpeg", "-y",
            "-i", "background.mp4",
            "-i", "audio.mp3",
            "-vf", "subtitles=subs.srt",
            "-c:a", "aac",
            "-shortest",
            output
        ]
        print("🎬 FFmpeg started")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print("🔴 FFmpeg error:")
            print(result.stderr)  # ← логируем
            return f"FFmpeg failed.", 500

        return send_file(output, mimetype="video/mp4")

    except Exception as e:
        return f"Server error: {str(e)}", 500

# 👇 ВАЖНО: слушаем порт из окружения
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
