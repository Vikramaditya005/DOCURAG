from docurag.pipeline import ask
import os
from dotenv import load_dotenv
load_dotenv()
res = ask("what are the questions from the pdf?", use_agents=False)
print("Answer:", res.answer)
print("Answerable:", res.answerable)
