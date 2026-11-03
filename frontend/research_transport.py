"""HTTP boundary for research tools; no hidden writes or fallback sample data."""
import os
import requests
from frontend.horoscope_transport import _headers, _raise_for_status


def api_get(path: str, **params):
    base = os.getenv('KMS_API_BASE', 'http://127.0.0.1:8000').rstrip('/')
    response = requests.get(base+path, params=params, headers=_headers(), timeout=(5,30))
    _raise_for_status(response)
    return response.json()


def api_post(path: str, payload: dict):
    base = os.getenv('KMS_API_BASE', 'http://127.0.0.1:8000').rstrip('/')
    response = requests.post(base+path,json=payload,headers=_headers(),timeout=(5,30))
    _raise_for_status(response)
    return response.json()
