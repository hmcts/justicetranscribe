# ruff: noqa

import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any

import nltk
from nltk.tokenize import sent_tokenize

# For semantic similarity - will try to import, fall back gracefully if not available
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    SEMANTIC_AVAILABLE = True
except ImportError:
    print(
        "Warning: sentence-transformers not available. Semantic similarity will be skipped."
    )
    print("Install with: pip install sentence-transformers")
    SEMANTIC_AVAILABLE = False

# Download required NLTK data if not already present
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


class AdvancedDuplicationAnalyzer:
    def __init__(self):
        self.semantic_model = None
        self.semantic_enabled = SEMANTIC_AVAILABLE  # Use a local copy

        if self.semantic_enabled:
            try:
                self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
                print("Loaded semantic similarity model")
            except Exception as e:
                print(f"Warning: Could not load semantic model: {e}")
                self.semantic_enabled = False  # Use instance variable instead

    def fuzzy_sentence_similarity(self, sent1: str, sent2: str) -> float:
        """Calculate fuzzy similarity between two sentences using sequence matching."""
        return SequenceMatcher(
            None, sent1.lower().strip(), sent2.lower().strip()
        ).ratio()

    def find_fuzzy_duplicates(
        self, sentences: list[str], threshold: float = 0.8
    ) -> tuple[int, list[dict]]:
        """
        Find sentences that are similar but not exactly the same.
        Returns count of fuzzy duplicates and details.
        """
        if len(sentences) < 2:
            return 0, []

        fuzzy_pairs = []
        marked_as_duplicate = set()

        for i in range(len(sentences)):
            if i in marked_as_duplicate:
                continue

            for j in range(i + 1, len(sentences)):
                if j in marked_as_duplicate:
                    continue

                similarity = self.fuzzy_sentence_similarity(sentences[i], sentences[j])

                if threshold <= similarity < 1.0:  # Similar but not exactly same
                    fuzzy_pairs.append(
                        {
                            "sentence1_idx": i,
                            "sentence2_idx": j,
                            "sentence1": (
                                sentences[i][:100] + "..."
                                if len(sentences[i]) > 100
                                else sentences[i]
                            ),
                            "sentence2": (
                                sentences[j][:100] + "..."
                                if len(sentences[j]) > 100
                                else sentences[j]
                            ),
                            "similarity": float(round(similarity, 4)),
                        }
                    )
                    marked_as_duplicate.add(j)  # Mark the second one as duplicate

        return len(marked_as_duplicate), fuzzy_pairs

    def find_semantic_duplicates(
        self, sentences: list[str], threshold: float = 0.85
    ) -> tuple[int, list[dict]]:
        """
        Find sentences that are semantically similar using embeddings.
        Returns count of semantic duplicates and details.
        """
        if (
            not self.semantic_enabled
            or self.semantic_model is None
            or len(sentences) < 2
        ):
            return 0, []

        try:
            # Filter out very short sentences that don't carry much meaning
            valid_sentences = [
                (i, sent) for i, sent in enumerate(sentences) if len(sent.strip()) > 20
            ]

            if len(valid_sentences) < 2:
                return 0, []

            indices, sentence_texts = zip(*valid_sentences, strict=False)

            # Generate embeddings
            embeddings = self.semantic_model.encode(sentence_texts)

            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings)

            semantic_pairs = []
            marked_as_duplicate = set()

            for i in range(len(embeddings)):
                if i in marked_as_duplicate:
                    continue

                for j in range(i + 1, len(embeddings)):
                    if j in marked_as_duplicate:
                        continue

                    similarity = similarity_matrix[i][j]

                    if similarity >= threshold:
                        # Check if they're not exactly the same (to avoid double-counting with exact duplicates)
                        if sentence_texts[i].strip() != sentence_texts[j].strip():
                            semantic_pairs.append(
                                {
                                    "sentence1_idx": indices[i],
                                    "sentence2_idx": indices[j],
                                    "sentence1": (
                                        sentence_texts[i][:100] + "..."
                                        if len(sentence_texts[i]) > 100
                                        else sentence_texts[i]
                                    ),
                                    "sentence2": (
                                        sentence_texts[j][:100] + "..."
                                        if len(sentence_texts[j]) > 100
                                        else sentence_texts[j]
                                    ),
                                    "similarity": float(round(similarity, 4)),
                                }
                            )
                            marked_as_duplicate.add(j)

            return len(marked_as_duplicate), semantic_pairs

        except Exception as e:
            print(f"Error in semantic similarity analysis: {e}")
            return 0, []


def calculate_text_length(text: str) -> int:
    """Calculate character length of text."""
    return len(text) if text else 0


def calculate_advanced_duplication_metrics(
    text: str, analyzer: AdvancedDuplicationAnalyzer
) -> dict[str, Any]:
    """
    Calculate comprehensive duplication metrics including semantic and fuzzy matching.
    """
    if not text:
        return {
            "exact_sentence_duplication_ratio": 0.0,
            "fuzzy_sentence_duplication_ratio": 0.0,
            "semantic_sentence_duplication_ratio": 0.0,
            "word_duplication_ratio": 0.0,
            "trigram_duplication_ratio": 0.0,
            "total_sentences": 0,
            "fuzzy_duplicate_details": [],
            "semantic_duplicate_details": [],
        }

    # Tokenize into sentences
    sentences = sent_tokenize(text)
    total_sentences = len(sentences)

    if total_sentences == 0:
        return {
            "exact_sentence_duplication_ratio": 0.0,
            "fuzzy_sentence_duplication_ratio": 0.0,
            "semantic_sentence_duplication_ratio": 0.0,
            "word_duplication_ratio": 0.0,
            "trigram_duplication_ratio": 0.0,
            "total_sentences": 0,
            "fuzzy_duplicate_details": [],
            "semantic_duplicate_details": [],
        }

    # Clean and normalize sentences for exact comparison
    clean_sentences = []
    for sentence in sentences:
        clean_sentence = re.sub(r"[^\w\s]", "", sentence.lower().strip())
        clean_sentence = re.sub(r"\s+", " ", clean_sentence)
        clean_sentences.append(clean_sentence)

    # Calculate exact sentence duplication
    sentence_counts = Counter(clean_sentences)
    exact_duplicated_sentences = sum(
        count - 1 for count in sentence_counts.values() if count > 1
    )
    exact_sentence_duplication_ratio = exact_duplicated_sentences / total_sentences

    # Calculate fuzzy duplication
    fuzzy_duplicate_count, fuzzy_details = analyzer.find_fuzzy_duplicates(
        sentences, threshold=0.8
    )
    fuzzy_sentence_duplication_ratio = fuzzy_duplicate_count / total_sentences

    # Calculate semantic duplication
    semantic_duplicate_count, semantic_details = analyzer.find_semantic_duplicates(
        sentences, threshold=0.85
    )
    semantic_sentence_duplication_ratio = semantic_duplicate_count / total_sentences

    # Calculate word-level duplication (same as before)
    words = re.findall(r"\b\w+\b", text.lower())
    total_words = len(words)
    word_counts = Counter(words)
    duplicated_words = sum(count - 1 for count in word_counts.values() if count > 1)
    word_duplication_ratio = duplicated_words / total_words if total_words > 0 else 0

    # Calculate trigram duplication (same as before)
    trigrams = []
    if len(words) >= 3:
        trigrams = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]

    total_trigrams = len(trigrams)
    trigram_counts = Counter(trigrams)
    duplicated_trigrams = sum(
        count - 1 for count in trigram_counts.values() if count > 1
    )
    trigram_duplication_ratio = (
        duplicated_trigrams / total_trigrams if total_trigrams > 0 else 0
    )

    return {
        "exact_sentence_duplication_ratio": round(exact_sentence_duplication_ratio, 4),
        "fuzzy_sentence_duplication_ratio": round(fuzzy_sentence_duplication_ratio, 4),
        "semantic_sentence_duplication_ratio": round(
            semantic_sentence_duplication_ratio, 4
        ),
        "word_duplication_ratio": round(word_duplication_ratio, 4),
        "trigram_duplication_ratio": round(trigram_duplication_ratio, 4),
        "total_sentences": total_sentences,
        "fuzzy_duplicate_details": fuzzy_details[:3],  # Keep only top 3 examples
        "semantic_duplicate_details": semantic_details[:3],  # Keep only top 3 examples
    }


def calculate_dialogue_to_output_ratio(
    dialogue_length: int, output_length: int
) -> float:
    """Calculate the ratio of dialogue length to output length."""
    if output_length == 0:
        return 0.0
    return round(dialogue_length / output_length, 4)
