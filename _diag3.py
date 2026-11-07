import sys, logging
sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s %(message)s")
from backend.app.core import config
from backend.app.services import horoscope_interpreter as hi
print("HOROSCOPE_PROVIDER env:", config.HOROSCOPE_PROVIDER)
try:
    r = hi._request_groq("Trả JSON", config.GROQ_API_KEY, config.GROQ_MODEL)
    print("GROQ OK")
except Exception as e:
    print("GROQ ERR", getattr(e, "code", e))
