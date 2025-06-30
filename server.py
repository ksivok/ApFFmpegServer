from flask import Flask, request, send_file
import subprocess
import os

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        # 🎵 Сохраняем аудио
        audio = request.files["audio"]
        audio.save("audio.mp3")
        print("✅ Audio saved")

        # 🎥 Сохраняем видео
        video = request.files["video"]
        video.save("background.mp4")
        print("✅ Video saved")

        # 📝 Пробуем сохранить субтитры (если есть)
        has_subtitles = False
        try:
            subs = request.files.get("subtitles")
            if subs:
                subs.save("subs.srt")
                has_subtitles = True
                print("✅ Subtitles saved")
        except Exception as e:
            print("⚠️ Subtitles error:", str(e))

        # 🎬 Команда FFmpeg
        output_file = "output.mp4"
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", "background.mp4",
            "-i", "audio.mp3",
        ]

        if has_subtitles and os.path.exists("subs.srt"):
            ffmpeg_cmd += ["-vf", "subtitles=subs.srt"]
        else:
            print("⚠️ No subtitles found or error – proceeding without them")

        ffmpeg_cmd += [
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            output_file
        ]

        print("🎬 FFmpeg started")
        subprocess.run(ffmpeg_cmd, check=True)
        print("✅ FFmpeg finished")

        return send_file(output_file, mimetype="video/mp4")

    except Exception as e:
        print("❌ Error:", str(e))
        return "Internal Server Error", 500


# 👇 ВАЖНО: слушаем порт из окружения
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
