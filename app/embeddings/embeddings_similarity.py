from sentence_transformers import SentenceTransformer
from process_data.load_data import load_data  
from embeddings.get_embeddings import get_embeddings

embeddings_dataset = load_data()

def search(query, k):
    query_embedding = get_embeddings([query]).cpu().numpy()  #.cpu().detach().numpy() 
    scores, retrieved_examples = embeddings_dataset.get_nearest_examples(
        "embeddings", query_embedding,
        k=k
    )
    return scores, retrieved_examples
