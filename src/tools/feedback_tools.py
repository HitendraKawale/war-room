from __future__ import annotations

from collections import Counter
from typing import Any


POSITIVE_KEYWORDS = {
    "faster",
    "smooth",
    "useful",
    "like",
    "love",
    "worked fine",
    "easy",
    "cleaner",
    "relevant",
    "helped",
    "cool",
}
NEGATIVE_KEYWORDS = {
    "slow",
    "lag",
    "buggy",
    "freeze",
    "froze",
    "failed",
    "crashed",
    "flaky",
    "spinning",
    "revert",
    "delay",
    "nothing",
    "unusable",
    "not a great first impression",
    "locked out",
}

THEME_KEYWORDS = {
    "payment_failure": [
        "payment failed",
        "retry payment",
        "charged",
        "flaky",
        "pay button",
        "could not complete",
    ],
    "latency_slow_loading": ["slow", "lag", "loading", "spinning", "delay", "heavier"],
    "crash_freeze": ["freeze", "froze", "crash", "crashed", "closed"],
    "positive_recommendations": ["bundle", "recommendations", "accessories", "relevant", "cool"],
    "ux_positive": ["fewer taps", "easy", "cleaner", "worked fine", "smooth"],
    "rollback_request": ["revert"],
    "privacy_outlier": ["microphone", "listening"],
    "data_loss_outlier": ["deleted my entire order history"],
    "account_lockout_outlier": ["locked out"],
}


def classify_sentiment(text: str) -> str:
    lowered = text.lower()
    pos_hits = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in lowered)
    neg_hits = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in lowered)

    if neg_hits > pos_hits:
        return "negative"
    if pos_hits > neg_hits:
        return "positive"
    return "neutral"


def detect_themes(text: str) -> list[str]:
    lowered = text.lower()
    matches = [
        theme for theme, keywords in THEME_KEYWORDS.items() if any(k in lowered for k in keywords)
    ]
    return matches or ["misc"]


def analyze_feedback(feedback: list[dict[str, Any]]) -> dict[str, Any]:
    sentiment_counts = Counter()
    theme_counts = Counter()
    theme_quotes: dict[str, list[str]] = {}
    classified_entries: list[dict[str, Any]] = []

    for entry in feedback:
        text = entry["text"]
        sentiment = classify_sentiment(text)
        themes = detect_themes(text)

        sentiment_counts[sentiment] += 1
        classified_entries.append(
            {
                "id": entry["id"],
                "date": entry["date"],
                "channel": entry["channel"],
                "segment": entry["segment"],
                "text": text,
                "sentiment": sentiment,
                "themes": themes,
            }
        )

        for theme in themes:
            theme_counts[theme] += 1
            theme_quotes.setdefault(theme, [])
            if len(theme_quotes[theme]) < 2:
                theme_quotes[theme].append(text)

    top_themes = []
    for theme, count in theme_counts.most_common():
        if theme == "misc":
            continue

        theme_sentiments = [
            item["sentiment"] for item in classified_entries if theme in item["themes"]
        ]
        dominant_sentiment = Counter(theme_sentiments).most_common(1)[0][0]

        top_themes.append(
            {
                "theme": theme,
                "count": count,
                "dominant_sentiment": dominant_sentiment,
                "representative_quotes": theme_quotes.get(theme, []),
            }
        )

    repeated_issues = [
        theme["theme"]
        for theme in top_themes
        if theme["count"] >= 2 and theme["dominant_sentiment"] == "negative"
    ]

    outlier_themes = {
        "privacy_outlier",
        "data_loss_outlier",
        "account_lockout_outlier",
    }
    outliers = [
        item["text"]
        for item in classified_entries
        if any(theme in outlier_themes for theme in item["themes"])
    ]

    trust_risks = []
    if "payment_failure" in repeated_issues:
        trust_risks.append("Repeated payment-related complaints may reduce customer trust.")
    if "crash_freeze" in repeated_issues:
        trust_risks.append(
            "Repeated crash/freeze complaints suggest users are experiencing core flow instability."
        )
    if outliers:
        trust_risks.append(
            "A few severe outlier complaints should be investigated even if not yet broadly corroborated."
        )

    return {
        "sentiment_counts": {
            "positive": sentiment_counts.get("positive", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "negative": sentiment_counts.get("negative", 0),
        },
        "top_themes": top_themes,
        "repeated_issues": repeated_issues,
        "outliers": outliers,
        "trust_risks": trust_risks,
        "classified_entries": classified_entries,
    }
