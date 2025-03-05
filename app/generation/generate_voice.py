from io import BytesIO
from gtts import gTTS

async def converter_text_to_voice(text: str) -> BytesIO:
    bytes_file = BytesIO()
    audio = gTTS(text=text, lang="ru")
    audio.write_to_fp(bytes_file)
    bytes_file.seek(0)
    return bytes_file