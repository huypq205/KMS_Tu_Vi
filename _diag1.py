import sys, re, requests, json
sys.stdout.reconfigure(encoding="utf-8")
raw = dict(re.findall(r"(?m)^([A-Z_]+)=(.*)$", open(".env", encoding="utf-8").read()))
gk = raw["GEMINI_API_KEY"].strip()
from backend.app.services import horoscope_interpreter as hi
payload = {"systemInstruction": {"parts": [{"text": hi.HOROSCOPE_SYSTEM_PROMPT}]},
           "contents": [{"parts": [{"text": "viết JSON"}]}],
           "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8192,
                                "responseMimeType": "application/json",
                                "responseJsonSchema": hi.response_schema(include_annual=False)}}
r = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
                   headers={"x-goog-api-key": gk}, json=payload, timeout=60)
print("ENVFILE GEMINI FULL:", r.status_code, r.text[:300].replace("\n", " "))
