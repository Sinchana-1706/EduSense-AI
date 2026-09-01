"""
Text Sentiment Analysis Module - NLTK VADER Analyzer.
Performs sentiment polarity analysis on classroom lecture transcripts.
"""

from typing import Dict, Any
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    """
    NLP sentiment analyzer for student speech transcripts and classroom discussion.
    """

    def __init__(self):
        self.is_loaded = False
        self.sia = None

    def load_model(self) -> bool:
        """
        Downloads NLTK VADER lexicon if missing and initializes SentimentIntensityAnalyzer.
        """
        try:
            nltk.download("vader_lexicon", quiet=True)
            self.sia = SentimentIntensityAnalyzer()
            self.is_loaded = True
            return True
        except Exception as e:
            err_msg = str(e).encode("ascii", "ignore").decode("ascii")
            print(f"[Sentiment Notice] Failed to initialize VADER analyzer: {err_msg}")
            self.is_loaded = True
            return False

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyzes transcript text and returns compound score and classification (positive/neutral/negative).
        """
        if not self.is_loaded or self.sia is None:
            self.load_model()

        if not text or not text.strip():
            return {
                "compound_score": 0.0,
                "sentiment": "neutral",
                "confidence": 1.0,
                "details": {"neg": 0.0, "neu": 1.0, "pos": 0.0}
            }

        if self.sia is not None:
            try:
                scores = self.sia.polarity_scores(text)
                compound = float(scores.get("compound", 0.0))

                # Compound thresholding rules
                if compound >= 0.05:
                    sentiment_label = "positive"
                elif compound <= -0.05:
                    sentiment_label = "negative"
                else:
                    sentiment_label = "neutral"

                confidence = abs(compound) if abs(compound) > 0 else 0.5

                return {
                    "compound_score": compound,
                    "sentiment": sentiment_label,
                    "confidence": round(confidence, 4),
                    "details": scores
                }
            except Exception as e:
                err_msg = str(e).encode("ascii", "ignore").decode("ascii")
                print(f"[Sentiment Notice] Sentiment analysis notice: {err_msg}")

        # Fallback simple keyword heuristic
        lower_text = text.lower()
        pos_words = ["good", "great", "understand", "clear", "yes", "excellent", "awesome"]
        neg_words = ["confused", "bad", "difficult", "hard", "no", "problem", "cannot"]

        pos_count = sum(1 for w in pos_words if w in lower_text)
        neg_count = sum(1 for w in neg_words if w in lower_text)

        if pos_count > neg_count:
            label = "positive"
            comp = 0.5
        elif neg_count > pos_count:
            label = "negative"
            comp = -0.5
        else:
            label = "neutral"
            comp = 0.0

        return {
            "compound_score": comp,
            "sentiment": label,
            "confidence": 0.70,
            "details": {"pos": float(pos_count), "neg": float(neg_count), "neu": 1.0}
        }


# Global singleton analyzer instance
sentiment_analyzer = SentimentAnalyzer()
