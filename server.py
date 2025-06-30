@app.route("/generate", methods=["POST"])
def generate():
    try:
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
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            return f"FFmpeg error:\n{result.stderr}", 500

        return send_file(output, mimetype="video/mp4")

    except Exception as e:
        return f"Server error: {str(e)}", 500
