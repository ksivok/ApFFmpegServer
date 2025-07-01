from flask import Flask, request, send_file, render_template_string
import subprocess
import os
from datetime import datetime

app = Flask(__name__)

last_status = {
    "time": None,
    "audio_uploaded": False,
    "video_uploaded": False,
    "ffmpeg_command": "",
    "ffmpeg_error": "",
    "success": None
}

@app.route("/files/<path:filename>")
def get_file(filename):
    filepath = os.path.join(".", filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return "File not found", 404

@app.route("/generate", methods=["POST"])
def generate():
    try:
        for file in ["audio.mp3", "background.mp4", "output.mp4"]:
            if os.path.exists(file):
                os.remove(file)

        last_status.update({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "audio_uploaded": False,
            "video_uploaded": False,
            "ffmpeg_command": "",
            "ffmpeg_error": "",
            "success": False
        })

        audio = request.files["audio"]
        audio.save("audio.mp3")
        last_status["audio_uploaded"] = True

        video = request.files["video"]
        video.save("background.mp4")
        last_status["video_uploaded"] = True

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "default=nw=1", "background.mp4"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        has_video_audio = "codec_type=audio" in probe.stdout
        filter_complex = "[0:a][1:a]amix=inputs=2:duration=shortest[aout]" if has_video_audio else "[1:a]anull[aout]"

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", "background.mp4", "-i", "audio.mp3",
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", "output.mp4"
        ]

        last_status["ffmpeg_command"] = " ".join(ffmpeg_cmd)
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        last_status["ffmpeg_error"] = result.stderr

        if result.returncode != 0 or not os.path.exists("output.mp4"):
            raise RuntimeError("FFmpeg failed or output not created")

        last_status["success"] = True
        return send_file("output.mp4", mimetype="video/mp4")

    except Exception as e:
        last_status["ffmpeg_error"] += f"\nException: {str(e)}"
        return "Internal Server Error", 500

@app.route("/")
def index():
    return status()

@app.route("/status")
def status():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FFmpeg Server Status</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px; }
            h1 { color: #444; }
            pre { background: #eee; padding: 10px; border-radius: 5px; overflow-x: auto; }
            .status { margin-bottom: 1em; }
            .file-links a { margin-right: 15px; }
        </style>
    </head>
    <body>
        <h1>✪ FFmpeg Generation Status</h1>
        <div class="status">
            <p><strong>Last run:</strong> {{ s.time or "N/A" }}</p>
            <p><strong>Audio uploaded:</strong> {{ s.audio_uploaded }}</p>
            <p><strong>Video uploaded:</strong> {{ s.video_uploaded }}</p>
            <p><strong>Success:</strong> {{ s.success }}</p>
            <p><strong>FFmpeg command:</strong></p>
            <pre>{{ s.ffmpeg_command }}</pre>
            <p><strong>FFmpeg log:</strong></p>
            <pre>{{ s.ffmpeg_error or "No log" }}</pre>
        </div>
        <div class="file-links">
            <h3>↓ Download Files</h3>
            <a href="/files/audio.mp3" target="_blank">Audio (ElevenLabs)</a>
            <a href="/files/background.mp4" target="_blank">Background Video</a>
            <a href="/files/output.mp4" target="_blank">Final Output</a>
        </div>
    </body>
    </html>
    """, s=last_status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
