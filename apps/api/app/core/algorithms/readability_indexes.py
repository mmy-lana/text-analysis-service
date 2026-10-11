import math
import re
from typing import List, Tuple
from app.models.common import CEFREquivalentEnum
from app.models.readability import (
    ReadabilityAnalysisResponse,
    SentenceComplexityModel,
)


def count_syllables_in_word(word: str) -> int:
    clean = re.sub(r'[^a-z]', '', word.lower())
    if not clean:
        return 0
    if len(clean) <= 3:
        return 1

    clean = re.sub(r'(?:es|ed|e)$', '', clean)
    if not clean:
        return 1

    diphthongs = re.findall(r'[aeiouy]{1,2}', clean)
    count = len(diphthongs)

    if count == 0:
        return 1
    return count


def is_complex_word(word: str, syllable_count: int) -> bool:
    if syllable_count < 3:
        return False
    if word[0].isupper():
        return False
    if word.endswith(("ing", "ed", "es")):
        base_syllables = count_syllables_in_word(re.sub(r'(?:ing|ed|es)$', '', word.lower()))
        return base_syllables >= 3
    return syllable_count >= 3


def segment_text(text: str) -> Tuple[List[str], List[str]]:
    raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", text)
    return raw_sentences, words


def derive_cefr(fk_grade: float) -> CEFREquivalentEnum:
    if fk_grade <= 3.0:
        return CEFREquivalentEnum.A1
    elif fk_grade <= 5.5:
        return CEFREquivalentEnum.A2
    elif fk_grade <= 8.0:
        return CEFREquivalentEnum.B1
    elif fk_grade <= 11.0:
        return CEFREquivalentEnum.B2
    elif fk_grade <= 14.0:
        return CEFREquivalentEnum.C1
    return CEFREquivalentEnum.C2


def analyze_readability(text: str) -> ReadabilityAnalysisResponse:
    sentences, words = segment_text(text)
    total_sentences = max(len(sentences), 1)
    total_words = max(len(words), 1)

    letters = sum(len(w) for w in words)
    characters = len(re.sub(r'\s', '', text))

    syllable_counts = [count_syllables_in_word(w) for w in words]
    total_syllables = sum(syllable_counts)
    complex_words = [w for w, syl in zip(words, syllable_counts) if is_complex_word(w, syl)]
    total_complex = len(complex_words)

    # Flesch Reading Ease
    flesch_re = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    flesch_re = max(-20.0, min(120.0, flesch_re))

    # Flesch-Kincaid Grade Level
    fk_grade = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
    fk_grade = max(0.0, fk_grade)

    # Gunning Fog
    gunning_fog = 0.4 * ((total_words / total_sentences) + 100.0 * (total_complex / total_words))
    gunning_fog = max(0.0, gunning_fog)

    # Coleman-Liau
    l_val = (letters / total_words) * 100.0
    s_val = (total_sentences / total_words) * 100.0
    coleman_liau = 0.0588 * l_val - 0.296 * s_val - 15.8
    coleman_liau = max(0.0, coleman_liau)

    # SMOG (McLaughlin formulation scaled proportionally for manuscripts under 30 sentences)
    scaled_complex = total_complex * (30.0 / total_sentences)
    smog = max(0.0, 1.0430 * math.sqrt(scaled_complex) + 3.1291)

    # Automated Readability Index
    ari = 4.71 * (characters / total_words) + 0.5 * (total_words / total_sentences) - 21.43
    ari = max(0.0, ari)

    # Velocity metrics
    reading_time = math.ceil((total_words / 225.0) * 60)
    speaking_time = math.ceil((total_words / 130.0) * 60)

    # Consensus Grade Level
    consensus_avg = (fk_grade + gunning_fog + coleman_liau + ari) / 4.0
    grade_string = f"Grade {round(consensus_avg, 1)}"

    # Sentence Decomposition
    sentence_breakdown: List[SentenceComplexityModel] = []
    for idx, s in enumerate(sentences):
        s_words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", s)
        s_wc = max(len(s_words), 1)
        s_syls = sum(count_syllables_in_word(sw) for sw in s_words)
        s_chars = sum(len(sw) for sw in s_words)
        s_complex = sum(1 for sw in s_words if is_complex_word(sw, count_syllables_in_word(sw)))

        # Single-sentence ASL computation uses (s_wc / 1.0)
        s_ease = 206.835 - 1.015 * (s_wc / 1.0) - 84.6 * (s_syls / s_wc)

        sentence_breakdown.append(
            SentenceComplexityModel(
                index=idx,
                text=s,
                word_count=s_wc,
                syllable_count=s_syls,
                character_count=s_chars,
                complex_word_count=s_complex,
                reading_ease=round(max(-20.0, min(120.0, s_ease)), 2),
                is_extremely_long=(s_wc >= 30),
            )
        )

    return ReadabilityAnalysisResponse(
        flesch_reading_ease=round(flesch_re, 2),
        flesch_kincaid_grade=round(fk_grade, 2),
        gunning_fog_index=round(gunning_fog, 2),
        coleman_liau_index=round(coleman_liau, 2),
        smog_index=round(smog, 2),
        automated_readability_index=round(ari, 2),
        reading_time_seconds=reading_time,
        speaking_time_seconds=speaking_time,
        syllable_count=total_syllables,
        complex_word_count=total_complex,
        grade_level_consensus=grade_string,
        cefr_equivalent=derive_cefr(fk_grade),
        sentence_breakdown=sentence_breakdown,
    )
