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

        # Команда FFmpeg с микшированием аудио
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", "background.mp4",     # входной видеофайл с оригинальным звуком
            "-i", "audio.mp3",          # озвучка от ElevenLabs
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=shortest[aout]",
            "-map", "0:v",              # карта видео
            "-map", "[aout]",           # карта аудио после микса
            "-c:v", "copy",             # копируем видео без перекодирования
            "-c:a", "aac",              # кодируем микс в AAC
            "-shortest",
        ]



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
