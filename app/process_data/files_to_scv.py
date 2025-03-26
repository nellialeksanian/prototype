import os
from tika import unpack
import pandas as pd

def read_short_description(short_desc_path, filename):
    """Читает короткое описание, если файл существует, иначе возвращает пустую строку"""
    file_name_without_extension, file_extension = os.path.splitext(filename)

    short_desc_file_txt = os.path.join(short_desc_path, f"{file_name_without_extension}.txt")
    short_desc_file_docx = os.path.join(short_desc_path, f"{file_name_without_extension}.docx")

    if os.path.isfile(short_desc_file_txt):
        try:
            with open(short_desc_file_txt, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            print(f"Ошибка при чтении файла {short_desc_file_txt}. Возможно, неверная кодировка.")
            return ""
    
    elif os.path.isfile(short_desc_file_docx):
        try:
            parsed_unpack = unpack.from_file(short_desc_file_docx, requestOptions={'timeout': None})
            return parsed_unpack.get('content', '')
        except Exception as e:
            print(f"Ошибка при обработке .docx файла {short_desc_file_docx}: {e}")
            return ""
    
    else:
        print(f"Короткое описание для {filename} не найдено: {short_desc_file_txt} или {short_desc_file_docx}")
        return ""

def clean_content(file_path):
    """Очищает контент из файла (например, из DOCX, PDF)"""
    try:
        parsed_unpack = unpack.from_file(file_path, requestOptions={'timeout': None})
        return parsed_unpack.get('content', '')
    except Exception as e:
        print(f"Ошибка при обработке файла {file_path}: {e}")
        return ""

def texts_list(files_path, short_desc_path):
    data = []
    for filename in os.listdir(files_path):
        filepath = os.path.join(files_path, filename)
        if os.path.isdir(filepath):
            continue
        
        text = clean_content(filepath)
        short_description = read_short_description(short_desc_path, filename)
        
        data.append({
            'title': os.path.splitext(filename)[0],
            'text': text,
            'short_description': short_description,
            'image': None
        })
    
    dataset = pd.DataFrame(data)
    return dataset

files_path = 'data/Slovcova/Словцова'
short_desc_path = 'data/Slovcova/Словцова/без лишних дат/'
output_path = 'data/Slovcova/'

dataset = texts_list(files_path, short_desc_path)
dataset.to_csv(os.path.join(output_path, "Slovcova_new_data_format.csv"), index=False)

