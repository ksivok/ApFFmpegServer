from flask import Flask, request, send_file
import subprocess
import os

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        # Удаляем старые файлы
        for file in ["audio.mp3", "background.mp4", "subs.srt", "output.mp4"]:
            if os.path.exists(file):
                os.remove(file)

        # Сохраняем аудио от ElevenLabs
        audio = request.files["audio"]
        audio.save("audio.mp3")
        print("✅ Audio saved")

        # Сохраняем видео (с оригинальным звуком)
        video = request.files["video"]
        video.save("background.mp4")
        print("✅ Video saved")

        # Опционально субтитры
        has_subtitles = False
        try:
            subs = request.files.get("subtitles")
            if subs:
                subs.save("subs.srt")
                has_subtitles = True
                print("✅ Subtitles saved")
        except Exception as e:
            print("⚠️ Subtitles error:", str(e))

        output_file = "output.mp4"

        # Команда FFmpeg с двумя аудиодорожками
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", "background.mp4",     # видео с оригинальным звуком
            "-i", "audio.mp3",          # озвучка ElevenLabs
            "-map", "0:v:0",            # видео
            "-map", "0:a:0",            # звук из видео
            "-map", "1:a:0",            # озвучка
            "-c:v", "copy",             # без перекодирования видео
            "-c:a", "aac",              # кодек для аудио дорожек
            "-shortest",
        ]

        # Добавим сабы если есть
        if has_subtitles and os.path.exists("subs.srt"):
            ffmpeg_cmd.insert(1, "-vf")
            ffmpeg_cmd.insert(2, "subtitles=subs.srt")
            print("🎬 Subtitles filter added")

        ffmpeg_cmd.append(output_file)

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
