import pandas as pd
import os
from tqdm import tqdm

def texts_list(files_path):
    data = []
    for filename in tqdm(os.listdir(files_path)): #рекурсия
        filepath = os.path.join(files_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            title = filename
            data.append({'title': title, 'text': text})
    dataset = pd.DataFrame(data)
    return dataset

files_path = 'data/paintings_data'
output_path = 'data/paintings_data_tables'
dataset = texts_list(files_path)
dataset.to_csv(os.path.join(output_path, "dataset.csv"), index=False)