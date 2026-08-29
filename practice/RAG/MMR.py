import numpy as np

def mmr(query_embedding, candidate_embeddings, candidate_docs, candidate_metas, top_k=3, lambda_param=0.6):
    print(f"INSIDE mmr — received query_embedding length: {len(query_embedding)}")
    query_embedding = np.array(query_embedding)
    candidate_embeddings = np.array(candidate_embeddings)

    similarities = candidate_embeddings @ query_embedding / (
        np.linalg.norm(candidate_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    selected_idx = []
    remaining_idx = list(range(len(candidate_docs)))

    for _ in range(min(top_k, len(candidate_docs))):
        if not selected_idx:
            best = int(np.argmax(similarities[remaining_idx]))
            chosen = remaining_idx[best]
        else:
            mmr_scores = []
            for idx in remaining_idx:
                relevance = similarities[idx]
                diversity_penalty = max(
                    candidate_embeddings[idx] @ candidate_embeddings[s] /
                    (np.linalg.norm(candidate_embeddings[idx]) * np.linalg.norm(candidate_embeddings[s]))
                    for s in selected_idx
                )
                mmr_scores.append(lambda_param * relevance - (1 - lambda_param) * diversity_penalty)
            chosen = remaining_idx[int(np.argmax(mmr_scores))]

        selected_idx.append(chosen)
        remaining_idx.remove(chosen)
    

    return [candidate_docs[i] for i in selected_idx], [candidate_metas[i] for i in selected_idx]