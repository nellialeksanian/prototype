from io import BytesIO
from gtts import gTTS
from aiogram.types import BufferedInputFile
from ruaccent import RUAccent
import re

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
    'вадим': 'вад+им',
    'рейман': 'р+ейман',
    'елена': 'ел+ена',
    'клейман': 'кл+ейман',
    'дома': "д+ома"
}

accentizer = RUAccent()
accentizer.load(omograph_model_size='turbo3.1', use_dictionary=True, custom_dict=accented_names, tiny_mode=False)

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

async def converter_text_to_voice(text: str) -> BufferedInputFile:
    bytes_file = BytesIO()
    accented_text = await accentize_text(text)
    audio = gTTS(text=accented_text, lang="ru")
    audio.write_to_fp(bytes_file)
    bytes_file.seek(0)
    print(f'Текст с ударениями: {accented_text}')
    
    return BufferedInputFile(file=bytes_file.read(), filename="voice.ogg")
