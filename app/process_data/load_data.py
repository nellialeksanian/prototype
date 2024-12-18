import pandas as pd
from datasets import Dataset

def load_data():
    df_loaded = pd.read_parquet('data/paintings_data_tables/full_data.parquet')
    embeddings_dataset = Dataset.from_pandas(df_loaded)
    embeddings_dataset.add_faiss_index(column="embeddings")

    return embeddings_dataset

def split_text(text, max_length):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]