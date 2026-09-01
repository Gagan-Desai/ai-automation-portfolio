# rag_core.py
import os
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from dotenv import load_dotenv
from MMR import mmr

load_dotenv()
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))

model = SentenceTransformer("all-MiniLM-L6-v2")
#db_client = chromadb.PersistentClient(path="./chroma_db")
groq_client = Groq()

collection_sentence = db_client.get_collection("documents_sentence")
collection_fixed = db_client.get_collection("documents_fixed")

def retrieve(question: str, collection, top_k: int = 10, use_mmr: bool = True, final_k: int = 3, lambda_param: float = 0.6):
    question_embedding = model.encode([question]).tolist()[0]
    raw_results = collection.query(query_embeddings=[question_embedding], n_results=top_k, include=["documents", "metadatas", "embeddings"])
    if use_mmr:
        docs, metas = mmr(question_embedding, raw_results["embeddings"][0], raw_results["documents"][0], raw_results["metadatas"][0], top_k=final_k, lambda_param=lambda_param)
    else:
        docs = raw_results["documents"][0][:final_k]
        metas = raw_results["metadatas"][0][:final_k]
    return docs, metas


def rag_answer(question: str, collection=collection_fixed):
    docs, metas = retrieve(question, collection)
    context = "\n\n".join(f"[Source: {m['source']}]\n{d}" for d, m in zip(docs, metas))
    system_prompt = (
        "You are a compliance assistant. Answer the question using ONLY the context provided below. "
        "If the context does not contain enough information to answer, say explicitly: "
        "'I cannot answer this based on the provided documents.' Do not use outside knowledge. "
        "Cite which source document you used."
    )
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
        reasoning_effort="low", include_reasoning=False,
    )
    return response.choices[0].message.content, docs


def answer_without_retrieval(question: str) -> str:
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "system", "content": "Answer the question to the best of your ability."}, {"role": "user", "content": question}],
        reasoning_effort="low", include_reasoning=False,
    )
    return response.choices[0].message.content