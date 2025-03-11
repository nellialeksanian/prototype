import pandas as pd
from datasets import Dataset
import re

def load_data():
    df_loaded = pd.read_parquet('data/Slovcova/Slovcova_embeddings_2.parquet')
    embeddings_dataset = Dataset.from_pandas(df_loaded)
    embeddings_dataset.add_faiss_index(column="embeddings")

    return embeddings_dataset

def split_text(text, max_length=4096):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

async def send_text_in_chunks(text, message_func, max_length=4096):
    text = re.sub(r'\n{3,}', '\n\n', text)
    paragraphs = text.split('\n\n')

    chunk = ""
    
    for paragraph in paragraphs:
        if len(chunk) + len(paragraph) + 2 > max_length:
            await message_func(chunk.strip())
            chunk = paragraph
        else:
            if chunk:
                chunk += '\n\n' 
            chunk += paragraph
    
    if chunk:
        await message_func(chunk.strip())


def clean_text(text):
    text = re.sub(r'\b(?:https?://|www\.|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/\S*)?\b', '', text)
    
    text = re.sub(r'(?m)^(-|\d+\.)\s.*(?:\n(?!\S))?', '', text)
    
    text = re.sub(r'\[bookmark: [^\]]+\]', '', text)
    
    text = re.sub(r'(?m)^\d{4}(?:\sгод)?$', '', text)
    
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    
    return text

