import requests
import json
import re

# BochaAI API 
base_url = ""
api_key = ''

LEAKAGE_TERMS = [
    "fake", "false", "true", "debunked", "fact check", "fact-check",
    "hoax", "rumor", "rumour", "misinformation", "disinformation",
    "真假", "假的", "虚假", "谣言", "辟谣", "事实核查", "不实信息"
]


def sanitize_query(query: str) -> str:
    
    cleaned_query = query

    for term in LEAKAGE_TERMS:

        if re.search(r"[a-zA-Z]", term):
            pattern = r"\b" + re.escape(term) + r"\b"
            cleaned_query = re.sub(pattern, "", cleaned_query, flags=re.IGNORECASE)
        else:
            cleaned_query = cleaned_query.replace(term, "")


    cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()

    return cleaned_query


def is_safe_query(query: str) -> bool:
    
    lower_query = query.lower()
    for term in LEAKAGE_TERMS:
        if term.lower() in lower_query:
            return False
    return True


def Web_search(query, num=10, page=1):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


    safe_query = sanitize_query(query)


    if not safe_query:
        print("The search terms resulted in no results after filtering; please generate more specific, factual keywords.")
        return None


    if not is_safe_query(safe_query):
        print("The search terms still include words that could introduce temporal leakage; please regenerate them.")
        return None

    payload = json.dumps({
        "query": safe_query,
        "summary": True,
        "count": num,
        "page": page
    })

    try:
        response = requests.post(base_url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("API 请求错误:", e)
        return None


