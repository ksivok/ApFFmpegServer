from flask import Flask, request, send_file
import subprocess
import os

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        # Удаляем старые файлы
        for file in ["audio.mp3", "background.mp4", "output.mp4"]:
            if os.path.exists(file):
                os.remove(file)
        print("✅ Old files removed")

        # Сохраняем аудио от ElevenLabs
        audio = request.files["audio"]
        audio.save("audio.mp3")
        print("✅ Audio saved")

        # Сохраняем видео (с оригинальным звуком)
        video = request.files["video"]
        video.save("background.mp4")
        print("✅ Video saved")

        # Проверим наличие аудио в видео
        print("🔍 Checking if background.mp4 has audio stream...")
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "default=nw=1", "background.mp4"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        has_video_audio = "codec_type=audio" in probe.stdout
        print(f"🎧 Background has audio: {has_video_audio}")

        output_file = "output.mp4"

        # Команда FFmpeg с условием
        if has_video_audio:
            filter_complex = "[0:a][1:a]amix=inputs=2:duration=shortest[aout]"
        else:
            filter_complex = "[1:a]anull[aout]"

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # overwrite
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

        print("🎬 Running FFmpeg with command:")
        print(" ".join(ffmpeg_cmd))

        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("🧾 FFmpeg stderr:")
        print(result.stderr)

        if result.returncode != 0:
            raise RuntimeError("FFmpeg failed")

        if not os.path.exists(output_file):
            raise FileNotFoundError("Output file not created")

        print("✅ FFmpeg finished")
        return send_file(output_file, mimetype="video/mp4")

    except Exception as e:
        print("❌ Error:", str(e))
        return "Internal Server Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
