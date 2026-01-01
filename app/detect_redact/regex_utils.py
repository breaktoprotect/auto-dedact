import re
from typing import Iterable
from app.model.regex_rule import RegexRule


def iter_regex_matches(text: str, regex_rule: RegexRule) -> Iterable[re.Match]:
    """
    Canonical regex execution.
    Everyone (detect / redact) must go through this.
    """
    pattern = re.compile(regex_rule.pattern)
    return pattern.finditer(text)
