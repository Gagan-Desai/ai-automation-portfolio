# evaluate_ragas.py
import asyncio
import instructor
import os
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness, AnswerRelevancy
from rag_core import rag_answer, answer_without_retrieval

from ragas.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")



judge_client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ["GROQ_API_KEY"])
judge_llm = llm_factory("openai/gpt-oss-20b", client=judge_client, mode=instructor.Mode.JSON)

faithfulness_scorer = Faithfulness(llm=judge_llm)
relevancy_scorer = AnswerRelevancy(llm=judge_llm, embeddings=embeddings)


async def evaluate_pair(question: str):
    grounded_answer, docs = rag_answer(question)
    ungrounded_answer = answer_without_retrieval(question)

    grounded_faith = await faithfulness_scorer.ascore(user_input=question, response=grounded_answer, retrieved_contexts=docs)
    ungrounded_faith = await faithfulness_scorer.ascore(user_input=question, response=ungrounded_answer, retrieved_contexts=docs)

    grounded_rel = await relevancy_scorer.ascore(user_input=question, response=grounded_answer, retrieved_contexts=docs)

    return {
        "question": question,
        "grounded_faithfulness": grounded_faith.value,
        "ungrounded_faithfulness": ungrounded_faith.value,
        "grounded_relevancy": grounded_rel.value,
    }


async def main():
    questions = [
        "What methodology should firms use to assess consumer protection risk?",
        "What specific changes did the Central Bank of Ireland make to the Consumer Protection Code as a result of industry feedback during the CP158 consultation process, and what was the stated rationale?",
    ]
    for q in questions:
        result = await evaluate_pair(q)
        print(f"\nQuestion: {result['question'][:60]}...")
        print(f"  Grounded faithfulness:   {result['grounded_faithfulness']:.3f}")
        print(f"  Ungrounded faithfulness: {result['ungrounded_faithfulness']:.3f}")
        print(f"  Grounded relevancy:      {result['grounded_relevancy']:.3f}")


if __name__ == "__main__":
    asyncio.run(main())