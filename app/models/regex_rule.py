from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class RegexRule(BaseModel):
    name: str = Field(..., description="Stable rule id, e.g. sg_nric")
    domain: str = Field(..., description="e.g. PII, SECRETS, FINANCIAL")
    data_category: str = Field(..., description="e.g. NRIC, CREDIT_CARD_PAN")
    description: Optional[str] = None  # "Useful and brief description of the rule"
    pattern: str  # inline flags allowed, e.g. (?im)

    @field_validator("name", "domain", "data_category")
    @classmethod
    def no_newlines_or_ellipsis_in_fields(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        if "\n" in v or "\r" in v:
            raise ValueError("must be a single line")
        if "…" in v:
            raise ValueError("must not contain ellipsis character")
        return v

    @field_validator("pattern")
    @classmethod
    def validate_regex(cls, v: str) -> str:
        v = v.strip()

        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"invalid regex: {e}")

        # Cheap quality gates to trigger Instructor retry on obvious junk
        if len(v) < 3:
            raise ValueError("pattern too short to be useful")
        if v in {".*", "^.*$", "^.*", ".*$"}:
            raise ValueError("pattern too broad")

        return v
