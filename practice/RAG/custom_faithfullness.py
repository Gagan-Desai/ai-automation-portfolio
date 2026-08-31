# custom_faithfulness.py
import json
from enum import Enum
from typing import List
from pydantic import BaseModel
from groq import Groq
from rag_core import rag_answer
import chromadb

client = Groq()

class Verdict(int, Enum):
    unsupported = 0
    supported = 1

class ClaimVerdict(BaseModel):
    statement: str
    reason: str
    verdict: Verdict

class FaithfulnessResult(BaseModel):
    claims: List[ClaimVerdict]


def check_faithfulness(question: str, answer: str, contexts: list[str]):
    context_text = "\n\n".join(contexts)
    schema = FaithfulnessResult.model_json_schema()

    system_prompt = (
        "Break the given answer into individual factual claims. For each claim, "
        "determine if it is directly supported by the provided context. "
        f"Respond with JSON matching this schema: {json.dumps(schema)}"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context_text}\n\nAnswer to evaluate:\n{answer}"}
        ],
        response_format={"type": "json_object"},
        reasoning_effort="low",
        include_reasoning=False,
    )

    parsed = json.loads(response.choices[0].message.content)
    result = FaithfulnessResult(**parsed)

    supported = sum(1 for c in result.claims if c.verdict == Verdict.supported)
    score = supported / len(result.claims) if result.claims else 0.0
    return score, result.claims

db_client = chromadb.PersistentClient(path="./chroma_db")
collection_fixed = db_client.get_collection("documents_fixed")

question="What methodology should firms use to assess consumer protection risk?"
answer, docs = rag_answer(question, collection_fixed)

ungrounded_answer = """A practical, repeatable framework for assessing consumer‑protection risk...
Step 1: Define the scope & objectives... Step 7: Evaluate controls & mitigations (ISO 31000 or NIST CSF frameworks)..."""

score, claims = check_faithfulness(
    question=question,
    answer=answer,
    contexts=docs
)
print(f"Faithfulness: {score:.2f}")
for c in claims:
    print(f"  [{c.verdict.name}] {c.statement} — {c.reason}")