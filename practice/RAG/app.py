# app.py
import streamlit as st
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from dotenv import load_dotenv
from MMR import mmr

load_dotenv()

@st.cache_resource
def load_resources():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    db_client = chromadb.PersistentClient(path="./chroma_db")
    groq_client = Groq()
    return model, db_client, groq_client

model, db_client, groq_client = load_resources()
collection_fixed = db_client.get_collection("documents_fixed")
collection_sentence = db_client.get_collection("documents_sentence")

st.title("Financial Services Regulatory Knowledge Assistant")
st.caption("Grounded in real Central Bank of Ireland Consumer Protection Code documents")

with st.sidebar:
    st.header("Settings")
    strategy = st.radio("Chunking strategy", ["Sentence-aware", "Fixed-size"])
    use_mmr = st.checkbox("Use MMR for diverse retrieval", value=True)
    lambda_param = st.slider("MMR lambda (relevance vs diversity)", 0.0, 1.0, 0.6, disabled=not use_mmr)
    show_comparison = st.checkbox("Show comparison without retrieval", value=True)

collection = collection_sentence if strategy == "Sentence-aware" else collection_fixed
question = st.text_input("Ask a question about consumer protection, insurance regulation, or Central Bank guidance:")

if st.button("Ask") and question:
    with st.spinner("Retrieving relevant documents..."):
        question_embedding = model.encode([question]).tolist()[0]
        raw_results = collection.query(query_embeddings=[question_embedding], n_results=10, include=["documents", "metadatas", "embeddings"])

        if use_mmr:
            docs, metas = mmr(question_embedding, raw_results["embeddings"][0], raw_results["documents"][0], raw_results["metadatas"][0], top_k=3, lambda_param=lambda_param)
        else:
            docs = raw_results["documents"][0][:3]
            metas = raw_results["metadatas"][0][:3]

        context = "\n\n".join(f"[Source: {m['source']}]\n{d}" for d, m in zip(docs, metas))

    with st.spinner("Generating grounded answer..."):
        system_prompt = (
            "You are a compliance assistant. Answer the question using ONLY the context provided below. "
            "If the context does not contain enough information to answer, say explicitly: "
            "'I cannot answer this based on the provided documents.' Do not use outside knowledge. "
            "Cite which source document you used."
        )
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ],
            reasoning_effort="low",
            include_reasoning=False,
        )
        grounded_answer = response.choices[0].message.content

    st.subheader("Grounded Answer")
    st.write(grounded_answer)

    with st.expander("View retrieved sources"):
        for doc, meta in zip(docs, metas):
            st.markdown(f"**Source:** {meta['source']}")
            st.text(doc[:400])
            st.divider()

    if show_comparison:
        with st.spinner("Generating comparison (no retrieval)..."):
            response_no_rag = groq_client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Answer the question to the best of your ability."},
                    {"role": "user", "content": question}
                ],
                reasoning_effort="low",
                include_reasoning=False,
            )
            ungrounded_answer = response_no_rag.choices[0].message.content

        st.subheader("⚠️ Without Retrieval (for comparison)")
        st.warning("Generated without access to real source documents — may be fabricated.")
        st.write(ungrounded_answer)