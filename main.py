from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils import transcribe_audio, is_domain_question, query_openai, speak_text
import shutil
import os
import uuid


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask_question(
    text: str = Form(None),
    audio: UploadFile = File(None)
):
    try:
        if audio:
            os.makedirs("audio", exist_ok=True)
            unique_filename = f"{uuid.uuid4().hex}_{audio.filename}"
            file_path = os.path.join("audio", unique_filename)

            with open(file_path, "wb") as f:
                shutil.copyfileobj(audio.file, f)

            text = transcribe_audio(file_path)

            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Warning: Could not delete audio file: {e}")

        if not text:
            return {"text": "No input detected."}

        if not is_domain_question(text):
            return {
                "text": "I'm designed to answer AI and Data Science related questions only."
            }

        response = query_openai(text)
        if not response:
            raise ValueError("OpenAI returned an empty response.")

        
        audio_file = speak_text(response)
        if not audio_file or not os.path.exists(audio_file):
            raise ValueError("Failed to synthesize audio.")

        return {"text": response, "audio_file": audio_file}

    except Exception as e:
        print(f"🔥 ERROR in /ask: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
