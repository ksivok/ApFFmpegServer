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
        # Удаляем старые файлы
        for file in ["audio.mp3", "background.mp4", "output.mp4"]:
            if os.path.exists(file):
                os.remove(file)
        print("✅ Old files removed")

        last_status["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        last_status["audio_uploaded"] = False
        last_status["video_uploaded"] = False
        last_status["ffmpeg_command"] = ""
        last_status["ffmpeg_error"] = ""
        last_status["success"] = False

        # Сохраняем аудио
        audio = request.files["audio"]
        audio.save("audio.mp3")
        last_status["audio_uploaded"] = True
        print("✅ Audio saved")

        # Сохраняем видео
        video = request.files["video"]
        video.save("background.mp4")
        last_status["video_uploaded"] = True
        print("✅ Video saved")

        # Проверим наличие аудио в видео
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "default=nw=1", "background.mp4"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        has_video_audio = "codec_type=audio" in probe.stdout
        print(f"🎧 Background has audio: {has_video_audio}")

        output_file = "output.mp4"
        filter_complex = "[0:a][1:a]amix=inputs=2:duration=shortest[aout]" if has_video_audio else "[1:a]anull[aout]"

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", "background.mp4",
            "-i", "audio.mp3",
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_file
        ]

        last_status["ffmpeg_command"] = " ".join(ffmpeg_cmd)
        print("🎬 FFmpeg started")

        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        last_status["ffmpeg_error"] = result.stderr

        if result.returncode != 0:
            raise RuntimeError("FFmpeg failed")

        if not os.path.exists(output_file):
            raise FileNotFoundError("Output file not created")

        print("✅ FFmpeg finished")
        last_status["success"] = True
        return send_file(output_file, mimetype="video/mp4")

    except Exception as e:
        last_status["ffmpeg_error"] += f"\nException: {str(e)}"
        print("❌ Error:", str(e))
        return "Internal Server Error", 500

@app.route("/status")
def status():
    return render_template_string("""
    <html><body>
    <h1>🎛 FFmpeg Status</h1>
    <ul>
        <li><strong>Last run:</strong> {{ s.time or "N/A" }}</li>
        <li><strong>Audio uploaded:</strong> {{ s.audio_uploaded }}</li>
        <li><strong>Video uploaded:</strong> {{ s.video_uploaded }}</li>
        <li><strong>Command:</strong> <pre>{{ s.ffmpeg_command }}</pre></li>
        <li><strong>Success:</strong> {{ s.success }}</li>
        <li><strong>FFmpeg log:</strong> <pre style="white-space: pre-wrap">{{ s.ffmpeg_error or "no log" }}</pre></li>
    </ul>
    </body></html>
    """, s=last_status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
