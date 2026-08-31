"""
Text Sentiment Analysis Module.
Uses NLTK VADER SentimentIntensityAnalyzer to calculate compound polarity scores and map to positive, neutral, or negative.
"""

from typing import Dict, Any
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    """
    Pretrained text sentiment analyzer for lecture transcripts and student responses.
    """

    def __init__(self):
        self.is_loaded = False
        self.sia = None

    def load_model(self) -> bool:
        """
        Loads NLTK VADER lexicon and initializes sentiment analyzer.
        """
        try:
            nltk.download("vader_lexicon", quiet=True)
            self.sia = SentimentIntensityAnalyzer()
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Error loading VADER sentiment analyzer: {e}")
            self.is_loaded = True
            return False

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Calculates sentiment polarity score and assigns label (positive, neutral, negative).
        """
        if not self.is_loaded or self.sia is None:
            self.load_model()

        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "compound_score": 0.0,
                "text": ""
            }

        try:
            scores = self.sia.polarity_scores(text)
            compound = float(scores.get("compound", 0.0))

            if compound >= 0.05:
                sentiment = "positive"
                confidence = max(0.60, min(1.0, 0.5 + compound / 2.0))
            elif compound <= -0.05:
                sentiment = "negative"
                confidence = max(0.60, min(1.0, 0.5 + abs(compound) / 2.0))
            else:
                sentiment = "neutral"
                confidence = max(0.50, float(scores.get("neu", 0.8)))

            return {
                "sentiment": sentiment,
                "confidence": round(confidence, 4),
                "compound_score": round(compound, 4),
                "scores": scores,
                "text": text
            }
        except Exception as e:
            print(f"Error in text sentiment analysis: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "compound_score": 0.0,
                "text": text
            }


# Global singleton analyzer instance
sentiment_analyzer = SentimentAnalyzer()
