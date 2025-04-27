import asyncio
from io import BytesIO
from gtts import gTTS
from aiogram.types import BufferedInputFile
from ruaccent import RUAccent
import re
import logging
import time
logger = logging.getLogger(__name__)
accented_names = {
    'юлия': '+юлия',
    'миллер': 'м+иллер',
    'максим': 'макс+им',
    'родионов': 'роди+онов',
    'диана': 'ди+ана',
    'гатауллина': 'гата+уллина',
    'окаева': 'ок+аева',
    'дарья': 'д+арья',
    'щелкун': 'щелк+ун',
    'жаслан': 'жасл+ан',
    'тасымов': 'тас+ымов',
    'анна': '+анна',
    'алексеева': 'алекс+еева',
    'саша': 'с+аша',
    'мельникова': 'м+ельникова',
    'савелий': 'сав+елий',
    'мельчаков': 'мельчак+ов',
    'корсак': 'к+орсак',
    'эльвира': 'эльв+ира',
    'хусаинова': 'хуса+инова',
    'анастасия': 'анастас+ия',
    'васильева': 'вас+ильева',
    'екатерина': 'екатер+ина',
    'чикерева': 'ч+икерева',
    'евгения': 'евг+ения',
    'овчинникова': 'овч+инникова',
    'никита': 'ник+ита',
    'плеханов': 'плех+анов',
    'кристина': 'крист+ина',
    'бабина': 'б+абина',
    'ксения': 'кс+ения',
    'баданова': 'бад+анова',
    'евгений': 'евг+ений',
    'проводенко': 'провод+енко',
    'василий': 'вас+илий',
    'кириллов': 'кир+иллов',
    'александр': 'алекс+андр',
    'кузьмин': 'кузьм+ин',
    'константин': 'констант+ин',
    'росляков': 'росляк+ов',
    'лада': 'л+ада',
    'ладная': 'л+адная',
    'артем': 'арт+ем',
    'долгих': 'долг+их',
    'молоков': 'м+олоков',
    'шилина': 'ш+илина',
    'александра': 'алекс+андра',
    'жернакова': 'жернак+ова',
    'жернова': 'жерн+ова',
    'вадим': 'вад+им',
    'рейман': 'р+ейман',
    'елена': 'ел+ена',
    'клейман': 'кл+ейман',
    'дома': "д+ома"
}

accentizer = RUAccent()
accentizer.load(omograph_model_size='tiny2', use_dictionary=True, custom_dict=accented_names, tiny_mode=False)

async def replace_plus_with_accent(text):
    def repl(match):
        word = match.group(0)
        plus_idx = word.find('+')
        if plus_idx != -1 and plus_idx + 1 < len(word):
            return word[:plus_idx] + word[plus_idx+1] + '\u0301' + word[plus_idx+2:]
        return word
    return re.sub(r'\S*\+\S*', repl, text)

async def accentize_text(text: str):
    accented_text = accentizer.process_all(text)
    converted = await replace_plus_with_accent(accented_text)
    return converted

async def converter_text_to_voice_old(text: str) -> BufferedInputFile:
    start_time_audio = time.time()
    bytes_file = BytesIO()
    accented_text = await accentize_text(text)
    logging.info(f'Текст с ударениями: {accented_text}')
    try:
        logging.info('HTTP Request: POST https://translate.google.com/_/TranslateWebserverUi/data/batchexecute')
        audio = gTTS(text=accented_text, lang="ru")
        audio.write_to_fp(bytes_file)
        bytes_file.seek(0)
        logging.info(f"Audio generated")
    except Exception as e:
        logging.error(f"Error while generating audio from text: {e}")
    end_time_audio = time.time() 
    generation_time_audio = float(end_time_audio - start_time_audio)
    
    return BufferedInputFile(file=bytes_file.read(), filename="voice.ogg"), generation_time_audio

def generate_audio_blocking(accented_text: str, bytes_file: BytesIO) -> BufferedInputFile:
    audio = gTTS(text=accented_text, lang="ru")
    audio.write_to_fp(bytes_file)
    bytes_file.seek(0)


async def converter_text_to_voice(text: str) -> BufferedInputFile:
    start_time_audio = time.time()
    bytes_file = BytesIO()
    accented_text = await accentize_text(text)  # still async part
    logging.info(f'Текст с ударениями: {accented_text}') 

    try: 
        # Use asyncio.to_thread to run the blocking function
        logging.info('HTTP Request: POST https://translate.google.com/_/TranslateWebserverUi/data/batchexecute')
        await asyncio.to_thread(generate_audio_blocking, accented_text, bytes_file)
        logging.info(f"Audio generated")
        audio_file = BufferedInputFile(file=bytes_file.read(), filename="voice.ogg")
    except Exception as e:
        logging.error(f"Error during audio generation asyncio.to_thread: {e}")
        audio_file = None
    
    end_time_audio = time.time()
    generation_time_audio = float(end_time_audio - start_time_audio)

    return audio_file, generation_time_audio
