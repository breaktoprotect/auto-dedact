from app.model.regex_rule import RegexRule
from app.model.sensitive_data import SensitiveData, TextLocation
from app.detect_redact.regex_utils import iter_regex_matches


def detect_text(text: str, regex_rule: RegexRule) -> list[SensitiveData]:
    if not isinstance(text, str):
        raise TypeError("text must be a str")

    detections: list[SensitiveData] = []

    for match in iter_regex_matches(text, regex_rule):
        detections.append(
            SensitiveData(
                content=match.group(0),
                domain=regex_rule.domain,
                data_category=regex_rule.data_category,
                location=TextLocation(
                    start_char=match.start(),
                    end_char=match.end(),
                ),
            )
        )

    return detections
