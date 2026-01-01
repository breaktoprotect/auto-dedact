import pytest

from app.detect_redact.redaction import redact_text_by_content, redact_text_by_regex
from app.model.regex_rule import RegexRule
from app.model.sensitive_data import SensitiveData, TextLocation


@pytest.fixture
def nric_rule():
    return RegexRule(
        name="regex.nric.sg.v1",
        domain="PII",
        data_category="NRIC",
        description="Singapore NRIC",
        pattern=r"\b[STFG]\d{7}[A-Z]\b",
    )


@pytest.fixture
def cc_rule():
    return RegexRule(
        name="regex.credit_card.pan.v1",
        domain="FINANCIAL",
        data_category="CREDIT_CARD_PAN",
        description="Credit card PAN with dashes",
        pattern=r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
    )


def test_redact_text_by_content_replaces_all_occurrences_globally():
    text = "NRIC S1234567D appears twice: S1234567D."
    detections = [
        SensitiveData(
            content="S1234567D",
            domain="PII",
            data_category="NRIC",
            location=TextLocation(start_char=5, end_char=14),
        )
    ]

    out = redact_text_by_content(text, detections, token="[REDACTED]")

    assert out == "NRIC [REDACTED] appears twice: [REDACTED]."


def test_redact_text_by_regex_fixed_token(nric_rule):
    text = "User NRIC: S1234567D"
    out = redact_text_by_regex(
        text, nric_rule, token="[NRIC REDACTED]", same_length=False
    )

    assert out == "User NRIC: [NRIC REDACTED]"


def test_redact_text_by_regex_same_length_masking(nric_rule):
    text = "User NRIC: S1234567D"
    out = redact_text_by_regex(text, nric_rule, mask_char="■", same_length=True)

    assert out == "User NRIC: " + ("■" * 9)


def test_redact_text_by_regex_multiple_matches_same_length(nric_rule):
    text = "S1234567D and F7654321Z"
    out = redact_text_by_regex(text, nric_rule, mask_char="■", same_length=True)

    assert out == ("■" * 9) + " and " + ("■" * 9)


def test_redact_text_by_regex_chain_nric_then_cc_fixed_token(nric_rule, cc_rule):
    text = "NRIC S1234567D CC 1234-5678-9012-3456"
    out = redact_text_by_regex(
        redact_text_by_regex(text, nric_rule, token="[NRIC]", same_length=False),
        cc_rule,
        token="[CC]",
        same_length=False,
    )

    assert out == "NRIC [NRIC] CC [CC]"


def test_redact_text_by_regex_chain_nric_then_cc_same_length(nric_rule, cc_rule):
    text = "NRIC S1234567D CC 1234-5678-9012-3456"
    out = redact_text_by_regex(
        redact_text_by_regex(text, nric_rule, mask_char="■", same_length=True),
        cc_rule,
        mask_char="■",
        same_length=True,
    )

    cc = "1234-5678-9012-3456"
    assert out == "NRIC " + ("■" * 9) + " CC " + ("■" * len(cc))


def test_redact_text_by_regex_respects_inline_im_flags():
    rule = RegexRule(
        name="regex.header.test",
        domain="TEST",
        data_category="HEADER",
        description="Match header lines starting with 'secret:'",
        pattern=r"(?im)^secret:\s*(.+)$",
    )

    text = "SECRET: topvalue\nnormal: ok\nsecret: lowervalue"
    out = redact_text_by_regex(
        text, rule, token="SECRET: [REDACTED]", same_length=False
    )

    assert out == "SECRET: [REDACTED]\nnormal: ok\nSECRET: [REDACTED]"


def test_redact_text_by_regex_does_not_reprocess_its_own_token():
    rule = RegexRule(
        name="regex.word",
        domain="TEST",
        data_category="WORD",
        description="Match word 'secret'",
        pattern=r"secret",
    )
    text = "secret secret"
    out = redact_text_by_regex(text, rule, token="[REDACTED]", same_length=False)
    assert out == "[REDACTED] [REDACTED]"


def test_redact_text_by_regex_no_matches_returns_original(nric_rule):
    text = "No NRIC here"
    out = redact_text_by_regex(text, nric_rule, same_length=False)
    assert out == text


def test_redact_text_by_regex_empty_string(nric_rule):
    assert redact_text_by_regex("", nric_rule) == ""


def test_redact_text_by_content_multiple_different_types():
    text = "NRIC S1234567D and CC 1234-5678-9012-3456"
    detections = [
        SensitiveData(
            content="S1234567D",
            domain="PII",
            data_category="NRIC",
            location=TextLocation(start_char=5, end_char=14),
        ),
        SensitiveData(
            content="1234-5678-9012-3456",
            domain="FINANCIAL",
            data_category="CREDIT_CARD_PAN",
            location=TextLocation(start_char=19, end_char=38),
        ),
    ]

    out = redact_text_by_content(text, detections, token="[REDACTED]")
    assert out == "NRIC [REDACTED] and CC [REDACTED]"


def test_redact_text_by_regex_with_groups():
    rule = RegexRule(
        name="regex.email",
        domain="PII",
        data_category="EMAIL",
        pattern=r"(\w+)@(\w+\.\w+)",
    )
    text = "Contact me at user@example.com"
    out = redact_text_by_regex(text, rule, token="[EMAIL]", same_length=False)
    assert out == "Contact me at [EMAIL]"


def test_redact_text_by_regex_unicode():
    rule = RegexRule(
        name="regex.unicode",
        domain="TEST",
        data_category="UNICODE",
        pattern=r"[α-ω]+",
    )
    text = "Greek letters: αβγδε"
    out = redact_text_by_regex(text, rule, mask_char="■", same_length=True)
    assert out == "Greek letters: " + ("■" * 5)


def test_redact_text_by_regex_overlapping_matches():
    rule = RegexRule(
        name="regex.overlap",
        domain="TEST",
        data_category="OVERLAP",
        pattern=r"aa",
    )
    text = "aaa"
    out = redact_text_by_regex(text, rule, token="X", same_length=False)
    # Should only match first 'aa' (non-overlapping)
    assert out == "Xa"
