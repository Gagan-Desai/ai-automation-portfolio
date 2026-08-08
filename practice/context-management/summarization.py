from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import tiktoken

client = Groq()  # assumes GROQ_API_KEY is set in your environment




def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def calculate_available_budget(
    system_prompt: str,
    model_context_window: int = 131072,
    reserved_output_tokens: int = 1024,
    encoding_name: str = "cl100k_base"
) -> int:
    system_tokens = count_tokens(system_prompt, encoding_name)
    formatting_overhead = 20  # small safety margin for role markers, message structure
    available = model_context_window - system_tokens - reserved_output_tokens - formatting_overhead
    return max(available, 0)


def sliding_window_truncate(conversation: list[dict], budget: int, encoding_name: str = "cl100k_base") -> list[dict]:
    kept = []
    running_total = 0

    # walk backwards from the most recent message
    for message in reversed(conversation):
        message_tokens = count_tokens(message["content"], encoding_name)
        if running_total + message_tokens > budget:
            break
        kept.insert(0, message)
        running_total += message_tokens

    return kept


def summarize_turns(turns: list[dict]) -> str:
    conversation_text = "\n".join(f"{t['role']}: {t['content']}" for t in turns)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Compress the following into a shorter version, preserving every specific fact, name, ID, or number mentioned. This may be a full conversation or an already-summarized statement — either way, compress it further while keeping all concrete facts. Never say there is nothing to summarize; always output a compressed version of the actual content provided."},
            {"role": "user", "content": conversation_text}
        ]
    )
    return response.choices[0].message.content


def manage_context(conversation: list[dict], system_prompt: str, model_context_window: int = 131072, reserved_output_tokens=1024, _depth=0, _max_depth=5 ) -> list[dict]:

    if _depth >= _max_depth:
        print("Max summarization depth reached — returning best effort.")
        return conversation
    

    budget = calculate_available_budget(system_prompt, model_context_window)
    total_tokens = sum(count_tokens(m["content"]) for m in conversation)

    if total_tokens <= budget:
        return conversation  # nothing to do yet

    # split: everything except the last 4 turns gets summarized; recent turns stay verbatim
    print("Summarization in progress...")
    to_summarize = conversation[:-4]
    to_keep = conversation[-4:]

    summary_text = summarize_turns(to_summarize)
    summary_message = {"role": "system", "content": f"Earlier conversation summary: {summary_text}"}
    print(summary_text)


    new_conversation = [summary_message] + to_keep

    # recursive check: if even the summary + recent turns still don't fit, summarize again
    new_total = sum(count_tokens(m["content"]) for m in new_conversation)
    if new_total > budget:
        print(new_total, "tokens still exceed budget after summarization. Summarizing again...")    
        return manage_context(new_conversation, system_prompt, model_context_window, reserved_output_tokens,_depth+1, _max_depth)

    return new_conversation


if __name__ == "__main__":

    long_convo = [
    {"role": "user", "content": "My account ID is X7829-Q, I'm having trouble logging in."},
    {"role": "assistant", "content": "Thanks for providing your account ID. I've noted it as X7829-Q. Can you tell me what error message you're seeing?"},
    {"role": "user", "content": "It just says invalid credentials, but I'm sure my password is correct."},
    {"role": "assistant", "content": "That can happen if your account was recently flagged for suspicious activity. Let me check on that."},
    {"role": "user", "content": "Okay, how long does that usually take to resolve?"},
    {"role": "assistant", "content": "Typically within 24 hours, but it can sometimes take up to 48 hours depending on volume."},
    {"role": "user", "content": "That's frustrating, is there anything I can do in the meantime?"},
    {"role": "assistant", "content": "You could try resetting your password as a precaution, that sometimes clears the flag faster."},
    {"role": "user", "content": "Alright, I'll try that. Also, what are your support hours?"},
    {"role": "assistant", "content": "Our support team is available Monday through Friday, 9am to 6pm."},
    {"role": "user", "content": "Good to know. One more thing, do you offer phone support as well?"},
    {"role": "assistant", "content": "Yes, phone support is available for premium accounts only."},
                    ]

    print(f"Total messages: {len(long_convo)}")
    print(f"Total tokens: {sum(count_tokens(m['content']) for m in long_convo)}")



    system = "You are a helpful assistant for a customer support team."

    result = manage_context(long_convo, system, model_context_window=200,reserved_output_tokens=50,)

    print(f"\nResult has {len(result)} messages:\n")
    for msg in result:
        print(f"[{msg['role']}] {msg['content']}\n")