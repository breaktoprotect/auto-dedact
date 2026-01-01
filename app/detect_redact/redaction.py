from typing import Iterable
import re

from app.models.sensitive_data import SensitiveData
from app.models.regex_rule import RegexRule


def redact_text_by_content(
    text: str,
    detections: Iterable[SensitiveData],
    *,
    token: str = "[REDACTED]",
) -> str:
    """Redact all occurrences of detected sensitive values globally."""
    out = text
    for d in detections:
        if d.content:
            out = out.replace(d.content, token)
    return out


def redact_text_by_regex(
    text: str,
    regex_rule: RegexRule,
    *,
    token: str = "[REDACTED]",
    mask_char: str = "■",
    same_length: bool = True,
) -> str:
    """Redact exactly what the regex matches using a single regex pass."""
    pattern = re.compile(regex_rule.pattern)

    def repl(m: re.Match) -> str:
        return mask_char * (m.end() - m.start()) if same_length else token

    return pattern.sub(repl, text)


# ! Test only
if __name__ == "__main__":
    sample_text = """
    John Tan's NRIC is S1234567D and his credit card number is 1234-5678-9012-3456.
    Mary Lim's NRIC is T7654321A and her credit card number is 6543-2109-8765-4321.
    """

    nric_regex_rule = RegexRule(
        name="regex.nric.sg.v1",
        domain="PII",
        data_category="NRIC",
        pattern=r"\b[STFG]\d{7}[A-Z]\b",
    )

    credit_card_regex_rule = RegexRule(
        name="regex.credit_card.pan.v1",
        domain="FINANCIAL",
        data_category="CREDIT_CARD_PAN",
        pattern=r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
    )

    redacted_text = redact_text_by_regex(
        sample_text,
        nric_regex_rule,
        token="[NRIC REDACTED]",
        same_length=False,
    )

    print("Original Sample Text:")
    print(sample_text)

    print("Redacted Sample Text (NRIC):")
    print(redacted_text)

    redacted_text = redact_text_by_regex(
        sample_text,
        credit_card_regex_rule,
        token="[CREDIT CARD REDACTED]",
        same_length=False,
    )

    print("Redacted Sample Text (Credit Card):")
    print(redacted_text)

    # * Chain redaction: NRIC -> Credit Card
    redacted_text = redact_text_by_regex(
        redact_text_by_regex(
            sample_text,
            nric_regex_rule,
            token="[NRIC REDACTED]",
            same_length=False,
        ),
        credit_card_regex_rule,
        token="[CREDIT CARD REDACTED]",
        same_length=False,
    )
    print("Redacted Sample Text (NRIC + Credit Card):")
    print(redacted_text)

    # * Chain redaction with same length masking: NRIC -> Credit Card
    redacted_text = redact_text_by_regex(
        redact_text_by_regex(
            sample_text,
            nric_regex_rule,
            mask_char="■",
            same_length=True,
        ),
        credit_card_regex_rule,
        mask_char="■",
        same_length=True,
    )
    print("Redacted Sample Text with Same Length Masking (NRIC + Credit Card):")
    print(redacted_text)
