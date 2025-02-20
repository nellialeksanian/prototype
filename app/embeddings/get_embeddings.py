from sentence_transformers import SentenceTransformer
# from datasets import Dataset
# import pandas as pd
# import torch

# df = pd.read_csv('data/paintings_data_tables/dataset.csv')
# df = pd.read_parquet('data/paintings_data_tables/Slovcova.parquet')
# data = Dataset.from_pandas(df)

model_emb = SentenceTransformer("BAAI/bge-m3")

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# model_emb.to(device)

def get_embeddings(text_list):
    embeddings = model_emb.encode(
        text_list, convert_to_tensor=True, #device=device
    )
    return embeddings

# embeddings_dataset = data.map(
#     lambda x:{"embeddings": get_embeddings(x["text"]).cpu().numpy()}
# )

# embeddings_dataset.to_parquet('data/paintings_data_tables/Slovcova_embeddings.parquet') 