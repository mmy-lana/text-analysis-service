"""English syllable counting heuristic engine.

Handles diphthong clusters, silent endings, and inflectional suffixes without
any dictionary dependency. This module is the single source of truth for
syllabification; `readability_indexes.py` delegates to it.
"""

from __future__ import annotations

import re

# Familiar compound suffixes whose trailing 'e'/'es'/'ed' are typically silent.
_SILENT_ENDING = re.compile(r"(?:es|ed|e)$")
_INFLECTION_SUFFIX = re.compile(r"(?:ing|ed|es)$")


def count_syllables_in_word(word: str) -> int:
    """Estimate the syllable count of a single English word.

    Heuristic pipeline:
    1. Normalize to lowercase ASCII letters only (digits/symbols contribute 0).
    2. Words of three or fewer letters carry one syllable.
    3. Strip silent endings (-es, -ed, -e) unless nothing remains.
    4. Count vowel/diphthong nuclei via ``[aeiouy]{1,2}`` clusters.
    5. Words without recognized vowels default to a baseline of one syllable.
    """
    clean = re.sub(r"[^a-z]", "", word.lower())
    if not clean:
        return 0
    if len(clean) <= 3:
        return 1

    clean = _SILENT_ENDING.sub("", clean)
    if not clean:
        return 1

    diphthongs = re.findall(r"[aeiouy]{1,2}", clean)
    if not diphthongs:
        return 1
    return len(diphthongs)


def base_word_for_complexity(word: str) -> str:
    """Strip inflectional suffixes (-ing, -ed, -es) for complexity re-checks."""
    return _INFLECTION_SUFFIX.sub("", word.lower())


def is_complex_word(word: str, syllable_count: int) -> bool:
    """Gunning Fog complexity: 3+ syllables, excluding capitalized nouns and
    words whose complexity disappears once standard inflectional suffixes are
    removed."""
    if syllable_count < 3:
        return False
    if word[:1].isupper():
        return False
    if word.endswith(("ing", "ed", "es")):
        base_syllables = count_syllables_in_word(base_word_for_complexity(word))
        return base_syllables >= 3
    return syllable_count >= 3
