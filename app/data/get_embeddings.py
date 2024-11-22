import pandas as pd
from datasets import Dataset
import faiss

def load_data():
    df_loaded = pd.read_parquet('app/data/embeddings_dataset_bge.parquet')
    embeddings_dataset = Dataset.from_pandas(df_loaded)
    embeddings_dataset.add_faiss_index(column="embeddings")

    return embeddings_dataset