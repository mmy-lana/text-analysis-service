"""Readability engine tests validating metrics against standardized literary
reference passages and edge-case invariants."""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from app.core.algorithms.readability_indexes import (
    analyze_readability,
    count_syllables_in_word,
    derive_cefr,
    is_complex_word,
    segment_text,
)
from app.core.algorithms.syllables import base_word_for_complexity
from app.main import app

# Classic example sentence used in Gunning's own teaching materials: exactly
# three polysyllabic words in one sentence -> SMOG ~= 13.0.
SMOG_REFERENCE = "The Australian platypus is seemingly a hybrid of a mammal and reptile creature."

SIMPLE_REFERENCE = "The sun was up. The sky was blue. The boy ran fast."


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


class TestSyllableEngine:
    @pytest.mark.parametrize(
        ("word", "expected"),
        [
            ("the", 1),
            ("make", 1),  # silent -e ending stripped
            ("nation", 2),
            ("beautiful", 4),
            ("idea", 2),
            ("queue", 2),
            ("strengths", 1),  # no vowel nuclei after reduction
            ("rhythm", 1),  # y acts as vowel nucleus
            ("1234", 0),  # digits excluded
            ("", 0),
            ("cat", 1),
            ("running", 2),
        ],
    )
    def test_syllable_counts(self, word: str, expected: int) -> None:
        assert count_syllables_in_word(word) == expected

    def test_base_word_strips_inflections(self) -> None:
        assert base_word_for_complexity("running") == "runn"
        assert base_word_for_complexity("established") == "establish"

    def test_complex_word_rules(self) -> None:
        assert is_complex_word("establishment", count_syllables_in_word("establishment"))
        assert not is_complex_word("Wonderful", count_syllables_in_word("Wonderful"))  # capitalized
        assert not is_complex_word("dog", 1)
        # Inflected form loses complexity once suffix removed.
        assert not is_complex_word("managed", count_syllables_in_word("managed"))


class TestSegmentation:
    def test_segment_sentences_and_words(self) -> None:
        sentences, words = segment_text("Hello there. Second one!")
        assert sentences == ["Hello there.", "Second one!"]
        assert words == ["Hello", "there", "Second", "one"]

    def test_repeated_punctuation_does_not_create_empty_sentences(self) -> None:
        sentences, _ = segment_text("What?! Really?! Yes.")
        assert sentences == ["What?!", "Really?!", "Yes."]

    def test_empty_text(self) -> None:
        sentences, words = segment_text("")
        assert sentences == []
        assert words == []


class TestReadabilityMetrics:
    def test_smog_reference_passage(self) -> None:
        result = analyze_readability(SMOG_REFERENCE)
        # SMOG formula: 1.0430 * sqrt(complex * 30 / sentences) + 3.1291
        expected = 1.0430 * math.sqrt(result.complex_word_count * 30.0) + 3.1291
        assert result.smog_index == pytest.approx(round(expected, 2), abs=0.01)

    def test_simple_passage_is_very_easy(self) -> None:
        result = analyze_readability(SIMPLE_REFERENCE)
        assert result.flesch_reading_ease > 90.0
        assert result.cefr_equivalent.value in ("A1", "A2")
        assert result.flesch_kincaid_grade < 3.0

    def test_complex_passage_is_difficult(self) -> None:
        academic = (
            "The epistemological ramifications of post-structuralist hermeneutics "
            "necessitate a comprehensive reconfiguration of contemporary pedagogical "
            "methodology. Interdisciplinary incomprehensibility perpetuates "
            "institutional resistance toward meaningful curricular transformation, "
            "thereby exacerbating existing socioeconomic disparities. Nevertheless, "
            "phenomenological investigation demonstrates considerable interpretive "
            "flexibility regarding authenticity and subjectivity."
        )
        result = analyze_readability(academic)
        assert result.flesch_reading_ease < 50.0
        assert result.cefr_equivalent.value in ("C1", "C2")
        assert result.complex_word_count > 0

    def test_reading_and_speaking_time(self) -> None:
        text = " ".join(["word"] * 225)
        result = analyze_readability(text)
        assert result.reading_time_seconds == 60  # 225 wpm
        assert result.speaking_time_seconds == math.ceil((225 / 130.0) * 60)

    def test_grade_consensus_format(self) -> None:
        result = analyze_readability(SIMPLE_REFERENCE)
        assert result.grade_level_consensus.startswith("Grade ")

    def test_sentence_breakdown_flags_long_sentences(self) -> None:
        long_sentence = " ".join(["content"] * 30) + "."
        result = analyze_readability("Short one. " + long_sentence)
        assert result.sentence_breakdown[1].is_extremely_long is True
        assert result.sentence_breakdown[0].is_extremely_long is False

    def test_sentence_breakdown_math_invariants(self) -> None:
        result = analyze_readability(SMOG_REFERENCE)
        sentence = result.sentence_breakdown[0]
        assert sentence.index == 0
        assert sentence.word_count == 13
        assert sentence.character_count == sum(
            len(w) for w in segment_text(SMOG_REFERENCE)[1]
        )
        assert -20.0 <= sentence.reading_ease <= 120.0


class TestEdgeCases:
    def test_single_word_manuscript(self) -> None:
        result = analyze_readability("Hello")
        assert result.syllable_count == count_syllables_in_word("Hello")
        assert result.flesch_reading_ease <= 120.0
        assert result.sentence_breakdown[0].word_count == 1

    def test_empty_manuscript_does_not_crash(self) -> None:
        result = analyze_readability("")
        assert result.flesch_reading_ease is not None

    def test_pure_numeric_text_excluded_from_syllables(self) -> None:
        result = analyze_readability("2024 1999 42.")
        assert result.syllable_count == 0
        assert result.cefr_equivalent.value == "A1"

    def test_cefr_thresholds(self) -> None:
        assert derive_cefr(2.0).value == "A1"
        assert derive_cefr(5.0).value == "A2"
        assert derive_cefr(7.0).value == "B1"
        assert derive_cefr(10.0).value == "B2"
        assert derive_cefr(13.0).value == "C1"
        assert derive_cefr(18.0).value == "C2"


class TestReadabilityEndpoint:
    def test_endpoint_camel_case_contract(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/readability/analyze", json={"text": SIMPLE_REFERENCE}
        )
        assert response.status_code == 200
        body = response.json()
        assert "fleschReadingEase" in body
        assert "fleschKincaidGrade" in body
        assert "gunningFogIndex" in body
        assert "colemanLiauIndex" in body
        assert "smogIndex" in body
        assert "automatedReadabilityIndex" in body
        assert "gradeLevelConsensus" in body
        assert "cefrEquivalent" in body
        assert "sentenceBreakdown" in body
        breakdown = body["sentenceBreakdown"][0]
        assert "wordCount" in breakdown
        assert "isExtremelyLong" in breakdown

    def test_blank_text_rejected(self, client: TestClient) -> None:
        response = client.post("/api/v1/readability/analyze", json={"text": "  "})
        assert response.status_code == 422

    def test_oversized_text_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/readability/analyze", json={"text": "word " * 30000}
        )
        assert response.status_code == 422
