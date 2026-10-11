"""Integration tests for the sentiment analysis engine and HTTP endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.algorithms.sentiment_lexicon import (
    analyze_sentiment,
    classify_polarity,
    evaluate_emotions,
    evaluate_sentiment_vector,
    split_into_sentences,
    tokenize,
)
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Pure algorithmic engine
# ---------------------------------------------------------------------------


class TestTokenization:
    def test_tokenize_lowercases_and_strips_punctuation(self) -> None:
        # Mixed alphanumeric runs (C3PO) yield no pure-alpha tokens per the
        # `\b[a-zA-Z]+\b` contract.
        assert tokenize("Hello, World! It's C3PO.") == ["hello", "world", "it", "s"]

    def test_tokenize_empty_string(self) -> None:
        assert tokenize("") == []

    def test_sentence_splitting(self) -> None:
        text = "One sentence here. Another follows! A third? And a fragment"
        assert split_into_sentences(text) == [
            "One sentence here.",
            "Another follows!",
            "A third?",
            "And a fragment",
        ]


class TestSentimentVector:
    def test_empty_tokens_are_neutral(self) -> None:
        polarity, subjectivity, pos, neu, neg = evaluate_sentiment_vector([])
        assert polarity == 0.0
        assert subjectivity == 0.0
        assert pos == 0.0
        assert neu == 1.0
        assert neg == 0.0

    def test_positive_text_yields_positive_polarity(self) -> None:
        polarity, *_ = evaluate_sentiment_vector(tokenize("A brilliant masterpiece"))
        assert 0.1 <= polarity <= 1.0

    def test_negative_text_yields_negative_polarity(self) -> None:
        polarity, *_ = evaluate_sentiment_vector(
            tokenize("A horrific catastrophic disaster")
        )
        assert polarity < -0.5

    def test_neutral_text(self) -> None:
        polarity, subjectivity, pos, neu, neg = evaluate_sentiment_vector(
            tokenize("the table sat quietly near the wall")
        )
        assert polarity == 0.0
        assert subjectivity == 0.0
        assert pos == 0.0
        assert neu == 1.0
        assert neg == 0.0

    def test_negation_flips_polarity(self) -> None:
        plain, *_ = evaluate_sentiment_vector(tokenize("brilliant"))
        negated, *_ = evaluate_sentiment_vector(tokenize("not brilliant"))
        assert plain > 0
        assert negated < 0

    def test_intensifier_amplifies(self) -> None:
        plain, *_ = evaluate_sentiment_vector(tokenize("good"))
        amplified, *_ = evaluate_sentiment_vector(tokenize("very good"))
        assert amplified > plain

    def test_polarity_is_bounded(self) -> None:
        tokens = tokenize(" ".join(["brilliant"] * 500))
        polarity, *_ = evaluate_sentiment_vector(tokens)
        assert -1.0 <= polarity <= 1.0


class TestClassification:
    @pytest.mark.parametrize(
        ("polarity", "expected"),
        [
            (0.9, "strongly_positive"),
            (0.45, "strongly_positive"),
            (0.3, "positive"),
            (0.1, "positive"),
            (0.0, "neutral"),
            (-0.2, "negative"),
            (-0.45, "strongly_negative"),
            (-0.95, "strongly_negative"),
        ],
    )
    def test_classification_boundaries(self, polarity: float, expected: str) -> None:
        assert classify_polarity(polarity).value == expected


class TestEmotions:
    def test_joy_words_raise_joy(self) -> None:
        emotions = evaluate_emotions("We celebrate the victory and triumph")
        assert emotions.joy > 0.0
        assert emotions.joy >= max(
            emotions.sadness,
            emotions.anger,
            emotions.fear,
            emotions.trust,
            emotions.surprise,
            emotions.disgust,
            emotions.anticipation,
        )

    def test_all_axes_present_and_bounded(self) -> None:
        emotions = evaluate_emotions("grief fury terror faith astonish vile longing")
        for value in (
            emotions.joy,
            emotions.sadness,
            emotions.anger,
            emotions.fear,
            emotions.trust,
            emotions.surprise,
            emotions.disgust,
            emotions.anticipation,
        ):
            assert 0.0 <= value <= 1.0

    def test_empty_text_all_zero(self) -> None:
        emotions = evaluate_emotions("")
        assert all(
            value == 0.0
            for value in (
                emotions.joy,
                emotions.sadness,
                emotions.anger,
                emotions.fear,
                emotions.trust,
                emotions.surprise,
                emotions.disgust,
                emotions.anticipation,
            )
        )


class TestAnalyzeSentiment:
    def test_full_pipeline_positive(self) -> None:
        result = analyze_sentiment("The novel is a brilliant masterpiece of clarity.")
        assert result.polarity > 0.1
        assert result.classification.value in ("positive", "strongly_positive")
        assert result.positivity_score > result.negativity_score
        assert result.compound_score == result.polarity
        assert len(result.sentence_breakdown) == 1

    def test_sentence_breakdown_indexes(self) -> None:
        result = analyze_sentiment("Great news today. Terrible outcome though. Plain text.")
        assert [item.index for item in result.sentence_breakdown] == [0, 1, 2]

    def test_non_english_defaults_neutral(self) -> None:
        result = analyze_sentiment("这是一个没有英文标记的段落")
        assert result.polarity == 0.0
        assert result.subjectivity == 0.0
        assert result.classification.value == "neutral"

    def test_html_injection_is_ignored(self) -> None:
        result = analyze_sentiment("<script>alert('brilliant')</script>")
        assert result.polarity != 0.0  # token still lexically analyzed, no crash
        assert result.polarity > 0


# ---------------------------------------------------------------------------
# HTTP API surface
# ---------------------------------------------------------------------------


class TestSentimentEndpoints:
    def test_analyze_endpoint_camel_case_contract(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sentiment/analyze",
            json={"text": "A superb and coherent argument."},
        )
        assert response.status_code == 200
        body = response.json()
        assert "positivityScore" in body
        assert "negativityScore" in body
        assert "neutralityScore" in body
        assert "compoundScore" in body
        assert "sentenceBreakdown" in body
        assert set(body["emotions"]) == {
            "joy",
            "sadness",
            "anger",
            "fear",
            "trust",
            "surprise",
            "disgust",
            "anticipation",
        }

    def test_analyze_accepts_snake_case_input(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sentiment/analyze",
            json={"text": "Superb.", "store_result": False},
        )
        assert response.status_code == 200

    def test_blank_text_is_rejected(self, client: TestClient) -> None:
        response = client.post("/api/v1/sentiment/analyze", json={"text": "   "})
        assert response.status_code == 422

    def test_oversized_text_is_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sentiment/analyze", json={"text": "word " * 30000}
        )
        assert response.status_code == 422

    def test_batch_endpoint(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sentiment/batch",
            json={"texts": ["brilliant work", "horrific disaster", "plain text"]},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["results"]) == 3
        assert body["results"][0]["classification"] == "positive"
        assert body["results"][1]["classification"] in ("negative", "strongly_negative")
        assert body["results"][2]["classification"] == "neutral"

    def test_batch_rejects_empty_list(self, client: TestClient) -> None:
        response = client.post("/api/v1/sentiment/batch", json={"texts": []})
        assert response.status_code == 422

    def test_batch_rejects_more_than_fifty(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sentiment/batch", json={"texts": ["ok"] * 51}
        )
        assert response.status_code == 422
