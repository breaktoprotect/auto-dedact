import pytest

from app.detect_redact.detection import detect_text
from app.detect_redact.regex_utils import iter_regex_matches
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


def test_detect_text_returns_sensitive_data_objects(nric_rule):
    text = "User: S1234567D"
    detections = detect_text(text, nric_rule)

    assert len(detections) == 1
    assert isinstance(detections[0], SensitiveData)


def test_detect_text_content_and_metadata(nric_rule):
    text = "NRIC=S1234567D"
    det = detect_text(text, nric_rule)[0]

    assert det.content == "S1234567D"
    assert det.domain == "PII"
    assert det.data_category == "NRIC"


def test_detect_text_location_offsets(nric_rule):
    text = "abc S1234567D xyz"
    det = detect_text(text, nric_rule)[0]

    assert isinstance(det.location, TextLocation)
    assert det.location.start_char == 4
    assert det.location.end_char == 13
    assert det.location.doc_type == "text"


def test_detect_text_location_span_matches_content_length(nric_rule):
    text = "User S1234567D here"
    det = detect_text(text, nric_rule)[0]

    assert det.location.end_char - det.location.start_char == len(det.content)


def test_detect_text_multiple_matches(nric_rule):
    text = "S1234567D and F7654321Z"
    detections = detect_text(text, nric_rule)

    assert len(detections) == 2
    assert [d.content for d in detections] == ["S1234567D", "F7654321Z"]


def test_detect_text_no_matches_returns_empty_list(nric_rule):
    text = "No NRIC here"
    detections = detect_text(text, nric_rule)

    assert detections == []


def test_detect_text_preserves_match_order(nric_rule):
    text = "X F7654321Z Y S1234567D Z"
    detections = detect_text(text, nric_rule)

    assert [d.content for d in detections] == ["F7654321Z", "S1234567D"]


def test_detect_text_matches_iter_regex_matches_exactly(nric_rule):
    text = "A S1234567D B F7654321Z C"

    expected = [
        (m.group(0), m.start(), m.end()) for m in iter_regex_matches(text, nric_rule)
    ]
    detections = detect_text(text, nric_rule)
    got = [(d.content, d.location.start_char, d.location.end_char) for d in detections]

    assert got == expected


def test_detect_text_match_at_start(nric_rule):
    text = "S1234567D is my NRIC"
    det = detect_text(text, nric_rule)[0]
    assert det.location.start_char == 0


def test_detect_text_match_at_end(nric_rule):
    text = "My NRIC is S1234567D"
    det = detect_text(text, nric_rule)[0]
    assert det.location.end_char == len(text)


def test_detect_text_with_different_rule():
    email_rule = RegexRule(
        name="regex.email.v1",
        domain="PII",
        data_category="EMAIL",
        description="Email address",
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    )
    text = "Contact me at test@example.com"
    detections = detect_text(text, email_rule)
    assert len(detections) == 1
    assert detections[0].data_category == "EMAIL"


def test_detect_text_with_none_text_raises(nric_rule):
    with pytest.raises(TypeError):
        detect_text(None, nric_rule)


def test_detect_text_with_empty_string(nric_rule):
    assert detect_text("", nric_rule) == []
