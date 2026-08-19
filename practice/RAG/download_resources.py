import requests, time

urls = {
    "general_guidance.pdf": "https://www.centralbank.ie/docs/default-source/regulation/consumer-protection/other-codes-of-conduct/consumer-protection-code-review/general-guidance-on-the-consumer-protection-code.pdf",
    "securing_customers_interests.pdf": "https://www.centralbank.ie/docs/default-source/regulation/consumer-protection/other-codes-of-conduct/consumer-protection-code-review/securing-customers-interests-guidance.pdf",
    "vulnerable_circumstances.pdf": "https://www.centralbank.ie/docs/default-source/regulation/consumer-protection/other-codes-of-conduct/consumer-protection-code-review/guidance-on-protecting-consumers-in-vulnerable-circumstances.pdf",
    "risk_assessment_guide.pdf": "https://www.centralbank.ie/docs/default-source/regulation/consumer-protection/compliance-monitoring/reviews-and-research/a-guide-to-consumer-protection-risk-assessment.pdf",
    "cp158_consultation.pdf": "https://www.centralbank.ie/docs/default-source/publications/consultation-papers/cp158/cp158-consultation-paper-consumer-protection-code.pdf",
    "cp158_feedback.pdf": "https://www.centralbank.ie/docs/default-source/publications/consultation-papers/cp158/feedback-statement-cp158-consultation-consumer-protection-code.pdf",
    "insurance_general_good_rules.pdf": "https://www.centralbank.ie/docs/default-source/regulation/industry-market-sectors/insurance-reinsurance/solvency-ii/requirements-and-guidance/general-good-rules.pdf",
    "insurance_undertaking_requirements.pdf": "https://www.centralbank.ie/docs/default-source/regulation/industry-market-sectors/insurance-reinsurance/solvency-ii/requirements-and-guidance/general-good-requirements-for-insurance-undertakings.pdf",
}



for filename, url in urls.items():
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"{filename}: {response.status_code}, {len(response.content)} bytes")
    time.sleep(1)