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


def test_detect_text_multiple_matches(nric_rule):
    text = "S1234567D and F7654321Z"

    detections = detect_text(text, nric_rule)

    assert len(detections) == 2
    assert detections[0].content == "S1234567D"
    assert detections[1].content == "F7654321Z"


def test_iter_regex_matches_inline_im_flags():
    rule = RegexRule(
        name="regex.header.test",
        domain="TEST",
        data_category="HEADER",
        description="Match header lines starting with 'secret:'",
        pattern=r"(?im)^secret:\s*(.+)$",
    )

    text = "SECRET: topvalue\nnormal: ok\nsecret: lowervalue"

    matches = list(iter_regex_matches(text, rule))

    assert len(matches) == 2

    assert matches[0].group(0) == "SECRET: topvalue"
    assert matches[1].group(0) == "secret: lowervalue"

    assert matches[0].group(1) == "topvalue"
    assert matches[1].group(1) == "lowervalue"


def test_detect_text_no_matches(nric_rule):
    text = "No NRIC here"

    detections = detect_text(text, nric_rule)

    assert detections == []


def test_detect_text_preserves_match_order(nric_rule):
    text = "X F7654321Z Y S1234567D Z"

    detections = detect_text(text, nric_rule)

    assert [d.content for d in detections] == ["F7654321Z", "S1234567D"]


def test_iter_regex_matches_without_i_flag_is_case_sensitive():
    rule = RegexRule(
        name="regex.header.test",
        domain="TEST",
        data_category="HEADER",
        description="Case-sensitive header match",
        pattern=r"(?m)^secret:\s*(.+)$",
    )

    text = "SECRET: topvalue\nsecret: lowervalue"

    matches = list(iter_regex_matches(text, rule))

    assert len(matches) == 1
    assert matches[0].group(0) == "secret: lowervalue"


def test_detect_text_location_span_matches_content_length(nric_rule):
    text = "User S1234567D here"

    det = detect_text(text, nric_rule)[0]

    assert det.location.end_char - det.location.start_char == len(det.content)  # type: ignore


def test_text_location_default_doc_type_is_text(nric_rule):
    text = "S1234567D"

    det = detect_text(text, nric_rule)[0]

    assert det.location.doc_type == "text"
