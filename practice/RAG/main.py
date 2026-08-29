from chunking import fixed_size_chunk, sentence_aware_chunk
from extract_text import extract_all_documents
from embed_store import embed_and_store, collection_fixed, collection_sentence
from sentence_transformers import SentenceTransformer
import chromadb
from MMR import mmr


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

# question = "What are insurance undertakings required to disclose about conflicts of interest?"
# question = "What protections exist for vulnerable consumers, and how should firms adapt their processes for them?"
question = "What methodology should firms use to assess consumer protection risk?"
results = retrieve(question, collection_fixed, top_k=3)
results_sentence = retrieve(question, collection_sentence, top_k=3)


""" for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
    print(f"Source: {meta['source']} | Distance: {dist:.4f}")
    print(f"{doc[:200]}...\n") """


""" print("=== FIXED-SIZE ===")
for doc in results["documents"][0]:
    print(doc[:200], "\n---")

print("\n=== SENTENCE-AWARE ===")
for doc in results_sentence["documents"][0]:
    print(doc[:200], "\n---") """



client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("documents_fixed")
question_embedding = model.encode([question]).tolist()[0]
raw_results = collection.query(query_embeddings=[question_embedding], n_results=10, include=["documents", "metadatas", "embeddings"])



diverse_docs, diverse_metas = mmr(
    question_embedding,
    raw_results["embeddings"][0],
    raw_results["documents"][0],
    raw_results["metadatas"][0],
    top_k=3,
    lambda_param=0.6
)

for doc, meta in zip(diverse_docs, diverse_metas):
    print(f"Source: {meta['source']}")
    print(f"{doc[:200]}...\n")

