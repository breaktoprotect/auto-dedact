from pydantic import BaseModel, Field
from typing import Optional


class RegexRule(BaseModel):
    name: str = Field(..., description="Stable rule id, e.g. regex.nric.sg.v1")
    domain: str = Field(..., description="e.g. PII, SECRETS, FINANCIAL")
    data_category: str = Field(..., description="e.g. NRIC, CREDIT_CARD_PAN")
    description: Optional[str] = None
    pattern: str  # inline flags allowed, e.g. (?im)
