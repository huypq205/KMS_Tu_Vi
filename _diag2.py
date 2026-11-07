import sys, re, json, logging
sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
from backend.app.core import config
from backend.app.services import horoscope_interpreter as hi

print("cfg GROQ:", config.GROQ_API_KEY[:14], "DS:", config.DEEPSEEK_API_KEY[:14], "GEM:", config.GEMINI_API_KEY[:14])
for name, fn in (("groq", hi._request_groq), ("deepseek", hi._request_deepseek)):
    pass

try:
    r = hi._request_groq("Trả JSON", config.GROQ_API_KEY, config.GROQ_MODEL)
    print("GROQ OK", list(r)[:5])
except Exception as e:
    print("GROQ ERR", getattr(e, "code", e))

try:
    r = hi._request_deepseek("Trả JSON", config.DEEPSEEK_API_KEY, config.DEEPSEEK_MODEL)
    print("DS OK", list(r)[:5])
except Exception as e:
    print("DS ERR", getattr(e, "code", e))

try:
    r = hi._request_gemini("Trả JSON", config.GEMINI_API_KEY, "gemini-3.6-flash")
    print("GEM OK", list(r)[:5])
except Exception as e:
    print("GEM ERR", getattr(e, "code", e))
