from flask import Flask, request, send_file, jsonify, send_from_directory
import azure.cognitiveservices.speech as speechsdk
import json
import os
import subprocess
import uuid

app = Flask(__name__)

# Azure credentials
speech_key = "1FbKr7aMi3k5oIGQ5QKA7FFGexOGh1wGw3d2BUz1F5srFgBsjFXYJQQJ99BGACGhslBXJ3w3AAAYACOGT0re"
region = "centralindia"

@app.route("/generate", methods=["POST"])
def generate():
    os.makedirs("static", exist_ok=True)

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    # Unique ID for each request
    uid = str(uuid.uuid4())[:8]
    input_webm = f"static/input_{uid}.webm"
    wav_path = f"static/input_{uid}.wav"
    temp_wav = f"static/temp_{uid}.wav"
    mp3_path = f"static/output_{uid}.mp3"
    viseme_path = f"static/visemes_{uid}.json"

    # Save uploaded audio
    audio_file = request.files["audio"]
    audio_file.save(input_webm)

    # Convert webm to wav using ffmpeg
    try:
        subprocess.run([
            "C:/Users/Lenovo/AppData/Local/ffmpeg/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe",
            "-y", "-i", input_webm, wav_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "ffmpeg conversion failed", "details": str(e)}), 500
    finally:
        if os.path.exists(input_webm):
            os.remove(input_webm)

    # === Speech to Text ===
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)
    audio_input = speechsdk.audio.AudioConfig(filename=wav_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = recognizer.recognize_once()
    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        return jsonify({"error": "Could not recognize speech"}), 400

    text = result.text.strip()
    if not text:
        return jsonify({"error": "Recognized speech was empty"}), 400

    print("Recognized:", text)

    # === TTS & Viseme ===
    speech_config.speech_synthesis_voice_name = "en-IN-NeerjaNeural"
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    viseme_data = []

    def viseme_callback(evt):
        viseme_data.append({
            "id": evt.viseme_id,
            "start": int(evt.audio_offset / 10000)  # ms
        })

    synthesizer.viseme_received.connect(viseme_callback)
    result = synthesizer.speak_text_async(text).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        return jsonify({"error": "Speech synthesis failed"}), 500

    stream = speechsdk.AudioDataStream(result)
    stream.save_to_wav_file(temp_wav)

    subprocess.run([
        "C:/Users/Lenovo/AppData/Local/ffmpeg/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe",
        "-y", "-i", temp_wav, mp3_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Cleanup temporary files
    for file in [wav_path, temp_wav]:
        if os.path.exists(file):
            try:
                os.remove(file)
            except PermissionError:
                print(f"{file} still in use — skipping delete")

    # Save viseme data
    with open(viseme_path, "w") as f:
        json.dump(viseme_data, f)

    return jsonify({
        "audio_url": f"/{mp3_path}",
        "viseme_url": f"/{viseme_path}"
    })

@app.route("/")
def index():
    return send_file("index.html")

@app.route('/mouths/<path:filename>')
def serve_mouths(filename):
    return send_from_directory('mouths', filename)

if __name__ == "__main__":
    app.run(debug=True)
