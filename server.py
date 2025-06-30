from flask import Flask, request, send_file
import subprocess
import os

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        # 🧹 Удаляем старые файлы
        for file in ["audio.mp3", "background.mp4", "subs.srt", "output.mp4"]:
            if os.path.exists(file):
                os.remove(file)

        # 🎵 Сохраняем озвучку (озвучка ElevenLabs)
        audio = request.files["audio"]
        audio.save("audio.mp3")
        print("✅ Audio saved")

        # 🎥 Сохраняем видео (с оригинальным звуком)
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
            "-i", "background.mp4",     # Видеофайл с оригинальным звуком
            "-i", "audio.mp3",          # Озвучка (2-я дорожка)
        ]


        ffmpeg_cmd += [
            "-map", "0:v",    # Видео
            "-map", "0:a",    # Оригинальный звук
            "-map", "1:a",    # Озвучка
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
