from MMR import mmr
from sentence_transformers import SentenceTransformer
import chromadb
from chunking import fixed_size_chunk, sentence_aware_chunk
from extract_text import extract_all_documents
from embed_store import embed_and_store, collection_fixed, collection_sentence

from groq import Groq
from dotenv import  load_dotenv

load_dotenv()

client2 = Groq()

model = SentenceTransformer("all-MiniLM-L6-v2")




def rag_answer(question: str, collection, top_k: int = 5, use_mmr: bool = True, final_k: int = 3, lambda_param: float = 0.6):
    question_embedding = model.encode([question]).tolist()[0]
    print(f"question_embedding length: {len(question_embedding)}")
    raw_results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "embeddings"]
    )

    if use_mmr:
        docs, metas = mmr(question_embedding, raw_results["embeddings"][0], raw_results["documents"][0], raw_results["metadatas"][0], top_k=final_k, lambda_param=lambda_param)
    else:
        docs = raw_results["documents"][0][:final_k]
        metas = raw_results["metadatas"][0][:final_k]

    context = "\n\n".join(f"[Source: {m['source']}]\n{d}" for d, m in zip(docs, metas))

    system_prompt = (
        "You are a compliance assistant. Answer the question using ONLY the context provided below. "
        "If the context does not contain enough information to answer, say explicitly: "
        "'I cannot answer this based on the provided documents.' Do not use outside knowledge. "
        "Cite which source document you used."
    )

    response = client2.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    )
    return response.choices[0].message.content, docs, metas


def answer_without_retrieval(question: str) -> str:
    response = client2.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "Answer the question to the best of your ability."},
            {"role": "user", "content": question}
        ],
        reasoning_effort="low",
        include_reasoning=False,
    )
    #print(response)
    print("finish_reason:", response.choices[0].finish_reason)
    return response.choices[0].message.content



filenames = [
    "resources/general_guidance.pdf",
    "resources/securing_customers_interests.pdf",
    "resources/vulnerable_circumstances.pdf",
    "resources/risk_assessment_guide.pdf",
    "resources/cp158_consultation.pdf",
    "resources/cp158_feedback.pdf",
    "resources/insurance_general_good_rules.pdf",
    "resources/insurance_undertaking_requirements.pdf",
]
document_texts = extract_all_documents(filenames)

all_fixed_chunks = []
all_sentence_chunks = []

for filename, text in document_texts.items():
    fixed = fixed_size_chunk(text, chunk_size=500, overlap=75)
    sentence_based = sentence_aware_chunk(text, max_chunk_size=500)

    print(f"{filename}: {len(fixed)} fixed-size chunks, {len(sentence_based)} sentence-aware chunks")

    all_fixed_chunks.extend([{"text": c, "source": filename} for c in fixed])
    all_sentence_chunks.extend([{"text": c, "source": filename} for c in sentence_based])

    
print(f"Embedding {len(all_fixed_chunks)} fixed-size chunks...")
embed_and_store(all_fixed_chunks, collection_fixed)

print(f"Embedding {len(all_sentence_chunks)} sentence-aware chunks...")
embed_and_store(all_sentence_chunks, collection_sentence)

print(f"\nFixed collection count: {collection_fixed.count()}")
print(f"Sentence collection count: {collection_sentence.count()}")

model = SentenceTransformer("all-MiniLM-L6-v2")

def retrieve(question: str, collection, top_k: int = 3):
    question_embedding = model.encode([question]).tolist()
    results = collection.query(query_embeddings=question_embedding, n_results=top_k)
    return results


#question = "According to the Central Bank of Ireland's guidance, which specific provisions of the Consumer Protection Code deal with conflicts of interest and transparency for insurance distributors?"
question = "What specific changes did the Central Bank of Ireland make to the Consumer Protection Code as a result of industry feedback during the CP158 consultation process, and what was the stated rationale?"
results = retrieve(question, collection_fixed, top_k=3)

results_sentence = retrieve(question, collection_sentence, top_k=3)






client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("documents_fixed")
question_embedding = model.encode([question]).tolist()[0]
raw_results = collection.query(query_embeddings=[question_embedding], n_results=10, include=["documents", "metadatas", "embeddings"])




print("=== WITHOUT RETRIEVAL ===")
print(answer_without_retrieval(question))



print("\n=== WITH RETRIEVAL (full RAG) ===")
answer, docs, metas = rag_answer(question, collection_sentence)
print(answer)
for doc, meta in zip(docs, metas):
    print(f"--- {meta['source']} ---")
    print(doc[:300])
    print()

