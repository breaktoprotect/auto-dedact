from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.regex_rule import RegexRule


class LLMRegexSuggestion(BaseModel):
    """
    Step 1: LLM suggests a regex rule with metadata.
    We wrap RegexRule to avoid duplicating canonical fields.
    """

    model_config = ConfigDict(extra="forbid")

    rule: RegexRule


class LLMJudgeResult(BaseModel):
    """
    Step 4: LLM judges if redaction was successful.

    regex_pattern:
      - if successful_redaction == True: "N/A"
      - if successful_redaction == False: suggested improved regex pattern
    """

    model_config = ConfigDict(extra="forbid")

    successful_redaction: bool = Field(
        ..., description="True if redaction is successful"
    )
    reason: str = Field(..., description="Explanation of why it passed/failed")
    regex_pattern: str = Field(
        description='Improved regex pattern if unsuccessful; "N/A" if successful',
    )
