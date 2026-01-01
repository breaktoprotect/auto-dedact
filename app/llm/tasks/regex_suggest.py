from typing import Optional

import instructor
from openai import OpenAI

from app.model.llm_responses import LLMRegexSuggestion


def suggest_regex_rule(
    *,
    client: OpenAI,  # this is now the instructor-patched client
    model: str,
    sample_text: str,
    sensitive_value: str,
    name_hint: Optional[str] = None,
    domain_hint: Optional[str] = None,
    data_category_hint: Optional[str] = None,
    max_retries: int = 2,
) -> LLMRegexSuggestion:
    hints_lines: list[str] = []
    if name_hint:
        hints_lines.append(f'name_hint="{name_hint}"')
    if domain_hint:
        hints_lines.append(f'domain_hint="{domain_hint}"')
    if data_category_hint:
        hints_lines.append(f'data_category_hint="{data_category_hint}"')

    hints_block = "\n".join(hints_lines) if hints_lines else "(none)"

    system_prompt = (
        "You are a senior data loss prevention engineer. "
        "Propose ONE regex rule that detects the provided sensitive value."
    )

    user_prompt = (
        "Goal: propose ONE regex rule.\n\n"
        f"Hints:\n{hints_block}\n\n"
        f"Sensitive value:\n{sensitive_value}\n\n"
        f"Sample text:\n{sample_text}\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = client.chat.completions.create(
        model=model,
        response_model=LLMRegexSuggestion,
        messages=messages,
        max_retries=max_retries,
    )  # type: ignore

    result: LLMRegexSuggestion = response
    return result


if __name__ == "__main__":
    from app.llm.llm_client import get_instructor_client
    from app.llm.tasks.regex_suggest import suggest_regex_rule

    client = get_instructor_client("lm_studio")
    model = "openai/gpt-oss-20b"

    res = suggest_regex_rule(
        client=client,
        model=model,
        sample_text="blah 4111-1111-1111-1111 blah",
        sensitive_value="4111-1111-1111-1111",
        max_retries=2,
    )

    print(res.rule.model_dump())
