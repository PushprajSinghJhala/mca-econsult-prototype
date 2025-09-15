# sentiment.py
import os
import requests

# Get API key from environment variable
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}

def analyze_sentiment(text: str):
    """
    Analyze sentiment using Hugging Face Inference API.
    Returns: (label, score)
    """
    if not text or not text.strip():
        return "Neutral", 0.0

    payload = {"inputs": text[:512]}  # limit text length
    try:
        response = requests.post(HF_URL, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            result = data[0][0]  # first prediction
            label = result["label"]
            score = float(result["score"])
        else:
            return "Neutral", 0.0

        # Normalize label
        if label.upper() == "POSITIVE":
            return "Positive", score
        elif label.upper() == "NEGATIVE":
            return "Negative", score
        else:
            return "Neutral", score

    except Exception as e:
        print("HF API error:", e)
        return "Neutral", 0.0
