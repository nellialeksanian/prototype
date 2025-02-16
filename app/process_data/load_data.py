import pandas as pd
from datasets import Dataset

def load_data():
    # df_loaded = pd.read_parquet('data/paintings_data_tables/full_data.parquet')
    df_loaded = pd.read_parquet('data/paintings_data_tables/Slovcova_embeddings.parquet')
    embeddings_dataset = Dataset.from_pandas(df_loaded)
    embeddings_dataset.add_faiss_index(column="embeddings")

    return embeddings_dataset

def split_text(text, max_length=4096):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# def split_into_blocks(sentences, max_length=4096):
#         blocks = []
#         current_block = ""

#         for sentence in sentences:
#             if len(current_block) + len(sentence) + 1 <= max_length:
#                 current_block += " " + sentence if current_block else sentence
#             else:
#                 blocks.append(current_block)
#                 current_block = sentence 
        
#         if current_block:
#             blocks.append(current_block)

#         return blocks