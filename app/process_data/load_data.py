import pandas as pd
from datasets import Dataset
import re

def load_data():
    # df_loaded = pd.read_parquet('data/paintings_data_tables/full_data.parquet')
    df_loaded = pd.read_parquet('data/paintings_data_tables/Slovcova_embeddings.parquet')
    embeddings_dataset = Dataset.from_pandas(df_loaded)
    embeddings_dataset.add_faiss_index(column="embeddings")

    return embeddings_dataset

def split_text(text, max_length=4096):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def clean_text(text):
    # Удаление всех ссылок, включая домены без префикса (например, example.com)
    text = re.sub(r'\b(?:https?://|www\.|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/\S*)?\b', '', text)
    
    # Удаление списка наград (на примере маркированного или нумерованного списка)
    text = re.sub(r'(?m)^(-|\d+\.)\s.*(?:\n(?!\S))?', '', text)
    
    # Удаление конструкций типа [bookmark: ...]
    text = re.sub(r'\[bookmark: [^\]]+\]', '', text)
    
    # Удаление годов выставок
    text = re.sub(r'(?m)^\d{4}(?:\sгод)?$', '', text)
    
    # Удаление лишних пустых строк (более двух подряд заменяем на одну)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    
    return text

