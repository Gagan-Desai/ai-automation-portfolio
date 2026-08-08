from summarization import (
    count_tokens,
    calculate_available_budget,
    sliding_window_truncate,
    manage_context,
)

def contains_fact(messages: list[dict], fact: str) -> bool:
    return any(fact in msg["content"] for msg in messages)


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

    FACT_TO_CHECK = "X7829-Q"
    system = "You are a helpful assistant for a customer support team."
    budget = calculate_available_budget(system, model_context_window=200, reserved_output_tokens=50)
    print(f"Computed budget for this test: {budget} tokens\n")

    sliding_result = sliding_window_truncate(long_convo, budget=budget)
    sliding_preserved = contains_fact(sliding_result, FACT_TO_CHECK)

    summary_result = manage_context(long_convo, system, model_context_window=200, reserved_output_tokens=50)
    summary_preserved = contains_fact(summary_result, FACT_TO_CHECK)

    print("=" * 55)
    print(f"{'STRATEGY':<25}{'RESULT':<15}{'MESSAGES KEPT'}")
    print("=" * 55)
    print(f"{'Sliding Window':<25}{'PRESERVED' if sliding_preserved else 'LOST':<15}{len(sliding_result)}")
    print(f"{'Hierarchical Summary':<25}{'PRESERVED' if summary_preserved else 'LOST':<15}{len(summary_result)}")
    print("=" * 55)