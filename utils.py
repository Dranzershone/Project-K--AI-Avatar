import openai
import os
import speech_recognition as sr
from pydub import AudioSegment
import pyttsx3

openai.api_type = "azure"
openai.api_base = ""
openai.api_version = "2024-02-15-preview"
openai.api_key = ""

AZURE_DEPLOYMENT_NAME = "gpt-4o" 

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    sound = AudioSegment.from_file(file_path)
    wav_path = file_path.replace(".mp3", ".wav")
    sound.export(wav_path, format="wav")

    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."

def is_domain_question(text):
    keywords = ["ai", "data science", "machine learning", "deep learning", "department", "kalpita", "faculty", "curriculum"]
    return any(keyword in text.lower() for keyword in keywords)

def query_openai(prompt):
    response = openai.ChatCompletion.create(
        engine=AZURE_DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are Professor Kalpita, an expert in AI and Data Science. Respond only to related queries.If asked who are you respond that You are Proffessor Kalpita AI assistannt for Department of Artificial Intelligence and Data science"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content.strip()

def speak_text(text):
    engine = pyttsx3.init()
    output_path = "audio/response.mp3"
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    return output_path
