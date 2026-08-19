
# embed_store.py
import chromadb
from sentence_transformers import SentenceTransformer
from extract_text import extract_text_from_pdfs
from chunking import fixed_size_chunk, sentence_aware_chunk


model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")

collection_fixed = client.get_or_create_collection(name="documents_fixed", metadata={"hnsw:space": "cosine"})
collection_sentence = client.get_or_create_collection(name="documents_sentence", metadata={"hnsw:space": "cosine"})


def embed_and_store(chunks: list[dict], collection):
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts).tolist()
    ids = [f"{c['source']}_{i}" for i, c in enumerate(chunks)]
    metadatas = [{"source": c["source"]} for c in chunks]
    collection.add(embeddings=embeddings, documents=texts, ids=ids, metadatas=metadatas)