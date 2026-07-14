import re
import string
import unicodedata

from flashtext import KeywordProcessor


VIETNAMESE_CHARACTERS = (
    "aăâbcdđeêghiklmnoôơpqrstuưvxy"
    "àáạảãằắặẳẵầấậẩẫ"
    "èéẹẻẽềếệểễ"
    "ìíịỉĩ"
    "òóọỏõồốộổỗờớợởỡ"
    "ùúụủũừứựửữ"
    "ỳýỵỷỹ"
)

WORD_CHARACTERS = set(
    string.ascii_letters
    + string.digits
    + "_"
    + VIETNAMESE_CHARACTERS
    + VIETNAMESE_CHARACTERS.upper()
)


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFC", str(text))
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)

    return text


class WeightedFlashTextMatcher:
    """
    Tạo một KeywordProcessor riêng cho từng subject/intent.

    Việc tách processor giúp một keyword có thể xuất hiện
    ở nhiều nhóm rule mà không bị ghi đè.
    """

    def __init__(self, rules_by_label: dict):
        self.processors = {}
        self.metadata = {}

        for label, rules in rules_by_label.items():
            processor = KeywordProcessor(case_sensitive=False)

            # Quan trọng đối với tiếng Việt.
            processor.set_non_word_boundaries(WORD_CHARACTERS)

            label_metadata = {}

            for rule in rules:
                term = normalize_text(rule["term"])

                if not term:
                    continue

                current = label_metadata.get(term)

                new_rule = {
                    "term": term,
                    "weight": int(rule.get("weight", 1)),
                    "type": rule.get(
                        "type",
                        rule.get("strength", "general")
                    )
                }

                # Nếu rule trùng term, giữ rule có trọng số cao hơn.
                if (
                    current is None
                    or new_rule["weight"] > current["weight"]
                ):
                    label_metadata[term] = new_rule

            for term in label_metadata:
                processor.add_keyword(term, term)

            self.processors[label] = processor
            self.metadata[label] = label_metadata

    def extract(self, text: str, label: str) -> dict:
        normalized_text = normalize_text(text)

        matches = self.processors[label].extract_keywords(
            normalized_text,
            span_info=True
        )

        # Chỉ cộng trọng số một lần cho mỗi keyword.
        # Tránh học sinh lặp từ nhiều lần làm tăng score giả.
        unique_matches = {}

        for term, start, end in matches:
            if term not in unique_matches:
                rule = self.metadata[label][term]

                unique_matches[term] = {
                    "term": term,
                    "weight": rule["weight"],
                    "type": rule["type"],
                    "start": start,
                    "end": end
                }

        matched_rules = list(unique_matches.values())

        score = sum(
            matched_rule["weight"]
            for matched_rule in matched_rules
        )

        strong_count = sum(
            matched_rule["type"] in {
                "strong",
                "domain_specific"
            }
            for matched_rule in matched_rules
        )

        return {
            "label": label,
            "score": score,
            "matched_terms": list(unique_matches.keys()),
            "matched_rules": matched_rules,
            "strong_count": strong_count
        }

    def extract_all(self, text: str) -> dict:
        return {
            label: self.extract(text, label)
            for label in self.processors
        }


class SingleLabelFlashTextMatcher:
    def __init__(self, rules: list, label: str):
        self.label = label
        self.matcher = WeightedFlashTextMatcher({
            label: rules
        })

    def extract(self, text: str) -> dict:
        return self.matcher.extract(text, self.label)
