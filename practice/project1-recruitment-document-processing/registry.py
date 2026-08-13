
from document_models import JobApplication, ReferenceLetter, OfferAcceptance

DOCUMENT_REGISTRY = {
    "job_application": {
        "model": JobApplication,
        "instruction": "This is a job application form. Extract the candidate's contact details, position applied for, experience, education history, and skills."
    },
    "reference_letter": {
        "model": ReferenceLetter,
        "instruction": "This is a reference letter. Extract the referee's details, the candidate's name, the relationship, and infer the overall recommendation strength (strong/moderate/weak) from the tone and content, along with the key strengths mentioned."
    },
    "offer_acceptance": {
        "model": OfferAcceptance,
        "instruction": "This is a signed offer acceptance form. Extract the candidate, position, dates, salary, and acceptance status."
    },
}