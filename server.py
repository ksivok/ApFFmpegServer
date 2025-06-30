from flask import Flask, request, send_file
import os
import subprocess

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    audio = request.files["audio"]
    video = request.files["video"]
    subs = request.files["subtitles"]

    audio.save("audio.mp3")
    video.save("background.mp4")
    subs.save("subs.srt")

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
    subprocess.run(command)

    return send_file(output, mimetype="video/mp4")
