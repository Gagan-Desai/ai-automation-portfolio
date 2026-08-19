from chunking import fixed_size_chunk, sentence_aware_chunk
from extract_text import extract_text_from_pdfs
from embed_store import embed_and_store, collection_fixed, collection_sentence

document_texts = extract_text_from_pdfs()

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
