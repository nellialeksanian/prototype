from sentence_transformers import SentenceTransformer
import torch 
from data.get_embeddings import load_data  

embeddings_dataset = load_data()

model_emb = SentenceTransformer("BAAI/bge-m3")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_emb.to(device)

def get_embeddings(text):
    embeddings = model_emb.encode(
        text, convert_to_tensor=True, device=device
    )
    return embeddings

def search(query, k):
    query_embedding = get_embeddings([query]).cpu().detach().numpy()
    scores, retrieved_examples = embeddings_dataset.get_nearest_examples(
        "embeddings", query_embedding,
        k=k
    )
    return scores, retrieved_examples
