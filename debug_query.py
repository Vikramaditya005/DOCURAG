import traceback, logging
from docurag.pipeline import ask

logging.basicConfig(level=logging.INFO)

QUESTIONS = [
    "What does the license agreement contain?",
    "What is written in the MLS assignment?",
    "What is in the Infosys aptitude paper?",
    "Describe the image Formal_pic.jpeg",
]

for q in QUESTIONS:
    print("\n" + "=" * 70, "\nQ:", q)
    try:
        res = ask(q, use_agents=False)
        print(res if not isinstance(res, dict) else {k: (str(v)[:300]) for k, v in res.items()})
    except Exception:
        traceback.print_exc()