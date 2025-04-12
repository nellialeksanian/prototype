from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

try:
    model_emb = SentenceTransformer("BAAI/bge-m3")
except Exception as e:
    MODEL_PATH = os.getenv("MODEL_PATH")
    print("Error loading model:", e)
    print("Trying to load from local path...")
    model_emb = SentenceTransformer(MODEL_PATH)

def get_embeddings(text_list):
    embeddings = model_emb.encode(
        text_list, convert_to_tensor=True, 
    )
    return embeddings
