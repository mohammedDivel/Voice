import os
import requests
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pydub import AudioSegment
import uvicorn

app = FastAPI()

# إنشاء مجلد مؤقت لحفظ الملفات الصوتية
UPLOAD_DIR = "temp_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# إعدادات ElevenLabs (يجب تحديث هذه القيم)
# ==========================================
API_KEY = "ضع_المفتاح_الخاص_بك_هنا"
VOICE_ID = "ضع_معرف_الصوت_هنا"

@app.post("/convert-voice/")
async def convert_voice(audio_file: UploadFile = File(...)):
    """
    نقطة النهاية (Endpoint) لاستقبال الصوت، معالجته، وإعادته كـ Voice Note
    """
    # 1. حفظ الملف القادم من تطبيق الموبايل
    input_path = f"{UPLOAD_DIR}/{audio_file.filename}"
    with open(input_path, "wb") as buffer:
        buffer.write(await audio_file.read())

    # 2. إرسال الصوت لخدمة ElevenLabs مع إعدادات المشاعر المتقدمة
    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Accept": "audio/mpeg"
    }
   
    # إعدادات لضمان نقل الانفعالات (كالضحك) بوضوح
    data = {
        "model_id": "eleven_multilingual_sts_v2",
        "voice_settings": '{"stability": 0.3, "similarity_boost": 0.9, "style": 0.8, "use_speaker_boost": true}'
    }

    with open(input_path, "rb") as audio_data:
        files = {"audio": (audio_file.filename, audio_data, "audio/wav")}
        response = requests.post(url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        # 3. حفظ النتيجة وتحويلها إلى صيغة Voice Note (OGG/Opus)
        temp_mp3 = f"{UPLOAD_DIR}/temp.mp3"
        final_ogg = f"{UPLOAD_DIR}/voice_note.ogg"
       
        with open(temp_mp3, "wb") as f:
            f.write(response.content)
           
        # استخدام pydub للتحويل إلى OGG
        audio = AudioSegment.from_file(temp_mp3)
        audio.export(final_ogg, format="ogg", codec="libopus", parameters=["-strict", "-2"])
       
        # تنظيف الملفات المؤقتة لتوفير المساحة
        os.remove(temp_mp3)
        os.remove(input_path)
       
        return FileResponse(final_ogg, media_type="audio/ogg", filename="voicenote.ogg")
    else:
        return {"error": "فشل التحويل في ElevenLabs", "details": response.text}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
