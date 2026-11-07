import sys, re, requests, json
sys.stdout.reconfigure(encoding="utf-8")
raw = dict(re.findall(r"(?m)^([A-Z_]+)=(.*)$", open(".env", encoding="utf-8").read()))
gk = raw["GROQ_API_KEY"].strip()
r = requests.get("https://api.groq.com/openai/v1/rate_limits", headers={"Authorization": "Bearer " + gk}, timeout=30)
print(r.status_code)
d = r.json()
for m in d.get("models", []):
    print(m["model"], "tpm", m["tpm"], "tpd", m["tpd"], "rpm", m["rpm"])
