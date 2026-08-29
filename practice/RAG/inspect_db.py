# inspect_db.py
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
print("Collections:", client.list_collections())

collection = client.get_collection("documents_fixed")
print(f"Total items: {collection.count()}")

sample = collection.get(limit=3, include=["documents", "metadatas", "embeddings"])
for i in range(len(sample["ids"])):
    print(f"\nID: {sample['ids'][i]}")
    print(f"Source: {sample['metadatas'][i]}")
    print(f"Text: {sample['documents'][i][:150]}...")
    print(f"Embedding: {len(sample['embeddings'][i])} dimensions, starts with {sample['embeddings'][i][:5]}")