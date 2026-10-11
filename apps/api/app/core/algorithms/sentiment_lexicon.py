import math
import re
from dataclasses import dataclass

from app.models.common import SentimentClassificationEnum
from app.models.sentiment import (
    EmotionSpectrumModel,
    SentenceSentimentItem,
    SentimentAnalysisResponse,
)

LEXICON_POLARITY: dict[str, float] = {
    "brilliant": 0.8,
    "excellent": 0.75,
    "superb": 0.8,
    "good": 0.5,
    "great": 0.6,
    "masterpiece": 0.9,
    "delight": 0.65,
    "clean": 0.3,
    "clarity": 0.4,
    "coherent": 0.45,
    "terrible": -0.8,
    "abysmal": -0.85,
    "poor": -0.5,
    "horrific": -0.9,
    "flawed": -0.4,
    "disaster": -0.8,
    "catastrophic": -0.85,
    "dull": -0.4,
    "broken": -0.6,
    "ugly": -0.55,
}

EMOTION_LEXICON: dict[str, dict[str, float]] = {
    "joy": {
        "delight": 0.8,
        "brilliant": 0.7,
        "victory": 0.9,
        "triumph": 0.85,
        "peace": 0.6,
        "celebrate": 0.75,
    },
    "sadness": {
        "mourn": 0.9,
        "grief": 0.95,
        "abysmal": 0.6,
        "loss": 0.7,
        "tragedy": 0.85,
        "alone": 0.5,
    },
    "anger": {
        "fury": 0.95,
        "rage": 0.9,
        "wrath": 0.85,
        "hate": 0.8,
        "bitter": 0.6,
        "infuriating": 0.75,
    },
    "fear": {
        "terror": 0.95,
        "panic": 0.9,
        "horrific": 0.85,
        "threat": 0.7,
        "dread": 0.8,
        "danger": 0.65,
    },
    "trust": {
        "faith": 0.8,
        "reliable": 0.7,
        "integrity": 0.85,
        "truth": 0.75,
        "honest": 0.7,
        "secure": 0.6,
    },
    "surprise": {
        "astonish": 0.85,
        "sudden": 0.5,
        "shock": 0.8,
        "unbelievable": 0.75,
        "wonder": 0.7,
    },
    "disgust": {"revolt": 0.85, "nauseating": 0.9, "vile": 0.8, "rotten": 0.75, "ugly": 0.6},
    "anticipation": {
        "await": 0.5,
        "prepare": 0.4,
        "horizon": 0.4,
        "longing": 0.6,
        "approaching": 0.5,
    },
}

INTENSIFIERS: dict[str, float] = {
    "very": 1.3,
    "extremely": 1.5,
    "immensely": 1.6,
    "remarkably": 1.4,
    "slightly": 0.7,
    "hardly": 0.5,
}

NEGATORS = {"not", "never", "no", "without", "hardly", "neither", "scarcely"}


def split_into_sentences(text: str) -> list[str]:
    raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in raw_sentences if s.strip()]


def tokenize(sentence: str) -> list[str]:
    return re.findall(r"\b[a-zA-Z]+\b", sentence.lower())


@dataclass(frozen=True)
class SentimentVector:
    """Aggregated lexical valence measures for a token stream."""

    polarity: float
    subjectivity: float
    positivity: float
    neutrality: float
    negativity: float
    # True when opposing strong emotional terms cancel out to an ambiguous
    # compound near zero despite clear subjective content on both sides.
    is_divergent: bool


def evaluate_sentiment_vector(tokens: list[str]) -> SentimentVector:
    if not tokens:
        return SentimentVector(0.0, 0.0, 0.0, 1.0, 0.0, False)

    pos_accum = 0.0
    neg_accum = 0.0
    subjectivity_hits = 0

    for i, token in enumerate(tokens):
        if token in LEXICON_POLARITY:
            score = LEXICON_POLARITY[token]
            subjectivity_hits += 1

            multiplier = 1.0
            if i > 0 and tokens[i - 1] in INTENSIFIERS:
                multiplier = INTENSIFIERS[tokens[i - 1]]

            negated = False
            for lookback in range(max(0, i - 3), i):
                if tokens[lookback] in NEGATORS:
                    negated = True
                    break

            final_val = score * multiplier
            if negated:
                final_val = -final_val * 0.75

            if final_val > 0:
                pos_accum += final_val
            else:
                neg_accum += abs(final_val)

    total_tokens = len(tokens)
    total_val = pos_accum + neg_accum
    subjectivity = min(1.0, (subjectivity_hits * 1.5) / max(total_tokens, 1))

    if total_val == 0.0:
        # Fully objective content: every token is un-scored.
        return SentimentVector(0.0, subjectivity, 0.0, 1.0, 0.0, False)

    # Objective (un-scored) tokens contribute to the neutrality share so the
    # tri-partition positivity + negativity + neutrality stays meaningful.
    objective_share = (total_tokens - subjectivity_hits) / total_tokens

    pos_ratio = pos_accum / total_val
    neg_ratio = neg_accum / total_val
    # Normalize subjective mass into [0, 1 - objective_share].
    subjective_mass = 1.0 - objective_share

    diff = pos_accum - neg_accum
    compound = diff / math.sqrt((diff * diff) + 15.0)
    polarity = max(-1.0, min(1.0, compound))

    divergent = pos_accum > 0.0 and neg_accum > 0.0 and abs(compound) < 0.1

    return SentimentVector(
        polarity=polarity,
        subjectivity=subjectivity,
        positivity=round(subjective_mass * pos_ratio, 4),
        neutrality=round(objective_share, 4),
        negativity=round(subjective_mass * neg_ratio, 4),
        is_divergent=divergent,
    )


def evaluate_emotions(text: str) -> EmotionSpectrumModel:
    tokens = tokenize(text)
    total_tokens = max(len(tokens), 1)
    scores: dict[str, float] = {e: 0.0 for e in EMOTION_LEXICON}

    for token in tokens:
        for emotion, lexicon in EMOTION_LEXICON.items():
            if token in lexicon:
                scores[emotion] += lexicon[token]

    normalized: dict[str, float] = {}
    for emotion, raw in scores.items():
        scaled = raw / (total_tokens * 0.15 + 1.0)
        normalized[emotion] = round(max(0.0, min(1.0, scaled)), 4)

    return EmotionSpectrumModel(**normalized)


def classify_polarity(polarity: float) -> SentimentClassificationEnum:
    if polarity >= 0.45:
        return SentimentClassificationEnum.STRONGLY_POSITIVE
    elif polarity >= 0.1:
        return SentimentClassificationEnum.POSITIVE
    elif polarity <= -0.45:
        return SentimentClassificationEnum.STRONGLY_NEGATIVE
    elif polarity <= -0.1:
        return SentimentClassificationEnum.NEGATIVE
    return SentimentClassificationEnum.NEUTRAL


def analyze_sentiment(text: str) -> SentimentAnalysisResponse:
    sentences = split_into_sentences(text)
    sentence_items: list[SentenceSentimentItem] = []

    all_tokens = tokenize(text)
    vector = evaluate_sentiment_vector(all_tokens)

    for idx, s_text in enumerate(sentences):
        s_tokens = tokenize(s_text)
        s_vector = evaluate_sentiment_vector(s_tokens)
        sentence_items.append(
            SentenceSentimentItem(
                index=idx,
                text=s_text,
                polarity=round(s_vector.polarity, 4),
                subjectivity=round(s_vector.subjectivity, 4),
                classification=classify_polarity(s_vector.polarity),
            )
        )

    emotions = evaluate_emotions(text)

    return SentimentAnalysisResponse(
        polarity=round(vector.polarity, 4),
        subjectivity=round(vector.subjectivity, 4),
        classification=classify_polarity(vector.polarity),
        positivity_score=round(vector.positivity, 4),
        negativity_score=round(vector.negativity, 4),
        neutrality_score=round(vector.neutrality, 4),
        compound_score=round(vector.polarity, 4),
        is_divergent=vector.is_divergent,
        emotions=emotions,
        sentence_breakdown=sentence_items,
    )
