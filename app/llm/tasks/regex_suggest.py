# app/llm/tasks/regex_suggest.py
from typing import Optional

from app.models.llm_responses import LLMRegexSuggestion
from app.llm.llm_client import prompt_llm_instructor_single


def suggest_regex_rule(
    *,
    provider: str,
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
        "You are a senior data loss prevention engineer.\n"
        "Your job is to propose ONE reusable regex rule that detects the SAME TYPE of sensitive data\n"
        "as the provided sensitive value, within similar text.\n\n"
        "Hard requirements:\n"
        "1) Do NOT hardcode the exact sensitive value.\n"
        "2) The regex MUST match the provided sensitive value as shown.\n"
        "3) Prefer high precision. Avoid overly broad patterns that match common words/numbers.\n"
        "4) Make it reasonably general for that data type (support common real-world variants).\n"
        "5) Keep it safe/performant (avoid catastrophic backtracking; avoid nested .* where possible).\n"
        "6) If hints are provided (name/domain/data_category), follow them exactly.\n"
        "7) Return exactly ONE rule (no alternatives, no explanations outside the schema)."
    )

    user_prompt = (
        "Goal: propose ONE regex rule.\n\n"
        "What you are given:\n"
        "- A sensitive value (one instance)\n"
        "- A sample text containing it\n"
        "- Optional hints (taxonomy/labels)\n\n"
        "What you must do:\n"
        "A) Infer what TYPE of sensitive data it is based on the value + surrounding context.\n"
        "B) Write a regex that matches that type, not just this exact instance.\n"
        "C) Include boundaries/anchors appropriate for the type.\n"
        "D) If the value has a checksum/semantic validation (e.g., Luhn), do NOT attempt it in regex.\n\n"
        "Design guidance (apply only if relevant):\n"
        "- If the value is an ID with fixed structure (e.g., NRIC/SSN), encode that structure.\n"
        "- If the value is a token/key, look for stable prefixes, length ranges, and allowed charset.\n"
        "- If the value is free-form (e.g., addresses), prefer conservative patterns that latch onto\n"
        "  strong cues (postal code formats, country/state patterns) rather than matching any text.\n"
        "- If ambiguity is unavoidable, choose precision over recall.\n\n"
        f"Hints:\n{hints_block}\n\n"
        "Sensitive value (your regex must match this):\n"
        f"{sensitive_value}\n\n"
        "Sample text:\n"
        f"{sample_text}\n"
    )

    result = prompt_llm_instructor_single(
        provider=provider,
        model=model,
        response_model=LLMRegexSuggestion,
        user=user_prompt,
        system=system_prompt,
        max_retries=max_retries,
    )

    return result


if __name__ == "__main__":
    from app.llm.tasks.regex_suggest import suggest_regex_rule

    provider = "lmstudio"
    model = "openai/gpt-oss-20b"

    cases = [
        {
            "title": "Credit card PAN",
            "sample_text": "Payment issue. Card used: 4111-1111-1111-1111. Please refund.",
            "sensitive_value": "4111-1111-1111-1111",
            "name_hint": "credit_card_pan",
            "domain_hint": "financial",
            "data_category_hint": "payment_card_number",
        },
        {
            "title": "Singapore NRIC",
            "sample_text": "Employee record: Name=Alex Tan, NRIC=S1234567D, Dept=IT.",
            "sensitive_value": "S1234567D",
            "name_hint": "nric_sg",
            "domain_hint": "pii",
            "data_category_hint": "nric",
        },
        {
            "title": "US SSN",
            "sample_text": "New hire onboarding: SSN 123-45-6789 (do not share).",
            "sensitive_value": "123-45-6789",
            "name_hint": "ssn_us",
            "domain_hint": "pii",
            "data_category_hint": "ssn",
        },
        {
            "title": "Email address",
            "sample_text": "Contact: alex.tan@example.test for details.",
            "sensitive_value": "alex.tan@example.test",
            "name_hint": "email_address",
            "domain_hint": "pii",
            "data_category_hint": "email",
        },
        {
            "title": "Singapore phone",
            "sample_text": "Call +65 9876 4321 if you need help.",
            "sensitive_value": "+65 9876 4321",
            "name_hint": "phone_sg",
            "domain_hint": "pii",
            "data_category_hint": "phone_number",
        },
        {
            "title": "AWS Access Key ID (example format)",
            "sample_text": "AWS creds: AccessKeyId=AKIA1234567890ABCD12 (rotate asap).",
            "sensitive_value": "AKIA1234567890ABCD12",
            "name_hint": "aws_access_key_id",
            "domain_hint": "credentials",
            "data_category_hint": "api_key",
        },
        {
            "title": "GitHub token-like (example)",
            "sample_text": "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890abcd",
            "sensitive_value": "ghp_abcdefghijklmnopqrstuvwxyz1234567890abcd",
            "name_hint": "github_token",
            "domain_hint": "credentials",
            "data_category_hint": "api_token",
        },
        {
            "title": "JWT-like (example)",
            "sample_text": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aaa.bbb",
            "sensitive_value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aaa.bbb",
            "name_hint": "jwt_token",
            "domain_hint": "credentials",
            "data_category_hint": "token",
        },
        {
            "title": "IPv4 private (sometimes treated as sensitive infra data)",
            "sample_text": "Server IP: 10.12.34.56 is reachable from subnet A.",
            "sensitive_value": "10.12.34.56",
            "name_hint": "ip_address",
            "domain_hint": "infrastructure",
            "data_category_hint": "ip",
        },
    ]

    for c in cases:
        print(f"\n=== {c['title']} ===")
        res = suggest_regex_rule(
            provider=provider,
            model=model,
            sample_text=c["sample_text"],
            sensitive_value=c["sensitive_value"],
            name_hint=c.get("name_hint"),
            domain_hint=c.get("domain_hint"),
            data_category_hint=c.get("data_category_hint"),
            max_retries=2,
        )
        print(res.rule.model_dump())
