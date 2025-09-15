# sentiment.py
from transformers import pipeline

# Load model once at startup
sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_sentiment(text: str):
    """
    Analyze sentiment of a given text.
    Returns: (label, score)
    """
    if not text or not text.strip():
        return "Neutral", 0.0

    result = sentiment_pipeline(text[:512])[0]  # limit length for performance
    label = result['label']
    score = float(result['score'])

    # Map labels to Positive/Negative/Neutral (depends on model)
    if label.upper() == "POSITIVE":
        return "Positive", score
    elif label.upper() == "NEGATIVE":
        return "Negative", score
    else:
        return "Neutral", score
