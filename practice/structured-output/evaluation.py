from extract_json_schema import extract_ticket_json_schema
import examples_set


labeled_examples = [
    {
        "text": "Our entire team can't log into the platform since this morning. This is blocking all our work and we have a client deadline today.",
        "true_category": "technical",
        "true_urgency": "high",
        "true_action_required": True
    },
    {
        "text": "I was charged twice for my subscription this month — once on the 1st and again on the 15th. Can someone refund the duplicate charge?",
        "true_category": "billing",
        "true_urgency": "medium",
        "true_action_required": True
    },
    {
        "text": "Just wanted to say the new dashboard update looks great. No issues to report, just wanted to share positive feedback.",
        "true_category": "general",
        "true_urgency": "low",
        "true_action_required": False
    },
    {
        "text": "The export-to-PDF button has been misaligned on mobile for a few weeks now. Not urgent, just noticed it and figured I'd flag it.",
        "true_category": "technical",
        "true_urgency": "low",
        "true_action_required": True
    },
    {
        "text": "My card was declined during checkout and now I can't access any of my saved reports. I need this resolved today, it's affecting my work.",
        "true_category": "billing",
        "true_urgency": "high",
        "true_action_required": True
    },
    {
        "text": "Quick question — is there a way to change the default currency on my account, or is that fixed once set during signup?",
        "true_category": "general",
        "true_urgency": "low",
        "true_action_required": False
    },
    {
        "text": "Getting an error every time I try to save a new project. It just says 'something went wrong' with no other details. Started happening yesterday.",
        "true_category": "technical",
        "true_urgency": "medium",
        "true_action_required": True
    },
    {
        "text": "I think I was upgraded to the wrong plan tier last month — the features I have don't match what I signed up for, but I'm not sure if it's a billing issue or just a settings thing on my end.",
        "true_category": "billing",
        "true_urgency": "medium",
        "true_action_required": True
    },
    {
        "text": "The app has been running a bit slower than usual over the past couple of days. Not sure if it's on your end or mine, just flagging it in case it's useful.",
        "true_category": "technical",
        "true_urgency": "low",
        "true_action_required": False
    },
]

def evaluate(examples):
    results = []
    for ex in examples:
        predicted = extract_ticket_json_schema(ex["text"])
        results.append({
                 "text": ex["text"][:50],
                "predicted_category": predicted.category.value,
                 "true_category": ex["true_category"],
                 "true_urgency": ex["true_urgency"],
                "category_correct": predicted.category.value == ex["true_category"],
                 "predicted_urgency": predicted.priority.value,
                 "urgency_correct": predicted.priority.value == ex["true_urgency"],
                 "true_action_required": ex["true_action_required"],
                "predicted_action": predicted.requires_immediate_attention,
                "action_correct": predicted.requires_immediate_attention == ex["true_action_required"],
                        })
    return results

def print_report(results):
    n = len(results)
    print(f"Category accuracy: {sum(r['category_correct'] for r in results) / n:.0%}")
    print(f"Urgency accuracy: {sum(r['urgency_correct'] for r in results) / n:.0%}")
    print(f"Action-required accuracy: {sum(r['action_correct'] for r in results) / n:.0%}")

    print("\nCategory misclassifications:")
    for r in results:
        if not r["category_correct"]:
            print(f"  '{r['text']}...' -> predicted {r['predicted_category']}, actual {r['true_category']}")

    print("\nUrgency misclassifications:")
    for r in results:
        if not r["urgency_correct"]:
            print(f"  '{r['text']}...' -> predicted {r['predicted_urgency']}, actual {r['true_urgency']}")

    print("\nAction-required misclassifications:")
    for r in results:
        if not r["action_correct"]:
            print(f"  '{r['text']}...' -> predicted {r['predicted_action']}, actual {r['true_action_required']}")


if __name__ == "__main__":
    results = evaluate(labeled_examples)
    print_report(results)