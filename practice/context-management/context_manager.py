# pip install tiktoken --break-system-packages
import tiktoken

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


print(count_tokens("Hello, world!"))
print(count_tokens("My account ID is X7829-Q."))


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

system = "You are a helpful assistant for a customer support team."
print(calculate_available_budget(system))



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


fake_convo = [
    {"role": "user", "content": "My account ID is X7829-Q."},
    {"role": "assistant", "content": "Got it, thanks!"},
    {"role": "user", "content": "What's the weather like today?"},
    {"role": "assistant", "content": "I don't have access to real-time weather."},
]
result = sliding_window_truncate(fake_convo, budget=15)
print(result)