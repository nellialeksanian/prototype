from io import BytesIO
from gtts import gTTS
from aiogram.types import BufferedInputFile

async def converter_text_to_voice(text: str) -> BufferedInputFile:
    bytes_file = BytesIO()
    audio = gTTS(text=text, lang="ru")
    audio.write_to_fp(bytes_file)
    bytes_file.seek(0)

    return BufferedInputFile(file=bytes_file.read(), filename="voice.ogg")