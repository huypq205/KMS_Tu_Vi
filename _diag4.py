import sys, re, json, requests
sys.stdout.reconfigure(encoding="utf-8")
raw = dict(re.findall(r"(?m)^([A-Z_]+)=(.*)$", open(".env", encoding="utf-8").read()))
gk = raw["GROQ_API_KEY"].strip()
from backend.app.services import horoscope_interpreter as hi
schema = hi.response_schema(include_annual=False)
payload = {"model": "openai/gpt-oss-20b",
           "messages": [{"role": "system", "content": hi.HOROSCOPE_SYSTEM_PROMPT + "\n" + json.dumps(schema, ensure_ascii=False)},
                        {"role": "user", "content": "viết JSON"}],
           "temperature": 0.0, "max_tokens": 2500}
r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                   headers={"Authorization": "Bearer " + gk, "Content-Type": "application/json"},
                   json=payload, timeout=60)
print("GROQ FULL:", r.status_code)
print(r.text[:800])
