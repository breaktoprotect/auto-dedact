from app.llm.llm_client import prompt_llm_instructor_single
from app.models.llm_responses import LLMJudgeResult


def judge_redaction_success(
    *,
    provider: str,
    model: str,
    sensitive_value: str,
    original_text: str,
    redacted_text: str,
    mask_char: str = "■",
    max_retries: int = 2,
) -> LLMJudgeResult:
    system_prompt = (
        "You are a senior data loss prevention engineer.\n"
        "Judge whether redaction was successful for the specified sensitive value.\n\n"
        "Hard requirements:\n"
        "1) Redaction is SUCCESS only if the sensitive value is NOT recoverable or visible in the redacted text.\n"
        "2) If FAILED, suggest ONE improved regex_pattern that would better detect/redact this type.\n"
        "3) Do not include any extra keys beyond the schema.\n"
        '4) If SUCCESS, set regex_pattern to "N/A".\n'
        "5) Redaction must be complete; partial redactions (e.g., only some characters masked) count as FAILED."
    )

    user_prompt = (
        "Evaluate redaction.\n\n"
        f"Sensitive value:\n{sensitive_value}\n\n"
        f"Mask character:\n{mask_char}\n\n"
        "Original text:\n"
        f"{original_text}\n\n"
        "Redacted text:\n"
        f"{redacted_text}\n"
    )

    result = prompt_llm_instructor_single(
        provider=provider,
        model=model,
        response_model=LLMJudgeResult,
        user=user_prompt,
        system=system_prompt,
        max_retries=max_retries,
    )
    return result


# ! Test only
if __name__ == "__main__":
    # # * Success case
    # judge_result = judge_redaction_success(
    #     provider="lmstudio",
    #     model="openai/gpt-oss-20b",
    #     sensitive_value="S1234567D",
    #     original_text="Employee record: Name=Alex Tan, NRIC=S1234567D, Dept=IT.",
    #     redacted_text="Employee record: Name=Alex Tan, NRIC=■■■■■■■■■, Dept=IT.",
    #     mask_char="■",
    #     max_retries=3,
    # )
    # print("Judge Result:", judge_result)
    # print("-" * 40)

    # # * Partial string redaction case
    # judge_result = judge_redaction_success(
    #     provider="lmstudio",
    #     model="openai/gpt-oss-20b",
    #     sensitive_value="S1234567D",
    #     original_text="Employee record: Name=Alex Tan, NRIC=S1234567D, Dept=IT.",
    #     redacted_text="Employee record: Name=Alex Tan, NRIC=S1234■■■D, Dept=IT.",
    #     mask_char="■",
    #     max_retries=3,
    # )
    # print("Judge Result:", judge_result)
    # print("-" * 40)

    # # * Complete Failure case
    # judge_result = judge_redaction_success(
    #     provider="lmstudio",
    #     model="openai/gpt-oss-20b",
    #     sensitive_value="S1234567D",
    #     original_text="Employee record: Name=Alex Tan, NRIC=S1234567D, Dept=IT.",
    #     redacted_text="Employee record: Name=Alex Tan, NRIC=S1234567D, Dept=IT.",
    #     mask_char="■",
    #     max_retries=3,
    # )
    # print("Judge Result:", judge_result)
    # print("-" * 40)

    # * Multiple strings occurence all fully redacted case - 3 employees
    # 3 employees with different NRIC
    original_text = """
    Employee record: Name=Alex Tan, NRIC=S1234567D, Dept=IT.
    Employee record: Name=Betty Lim, NRIC=T7654321A, Dept=HR.
    Employee record: Name=Charlie Ong, NRIC=S2345678B, Dept=Finance.
"""

    # only T7654321A is missed
    redacted_text = """
    Employee record: Name=Alex Tan, NRIC=■■■■■■■■■, Dept=IT.
    Employee record: Name=Betty Lim, NRIC=T7654321A, Dept=HR.
    Employee record: Name=Charlie Ong, NRIC=■■■■■■■■■, Dept=Finance.
"""

    judge_result = judge_redaction_success(
        provider="lmstudio",
        model="openai/gpt-oss-20b",
        sensitive_value="S1234567D, T7654321A, S2345678B",
        original_text=original_text,
        redacted_text=redacted_text,
        mask_char="■",
    )
    print("Judge Result:", judge_result)
    print("-" * 40)

    # * Multiple strings occurence partial redacted failure case
    # judge_result = judge_redaction_success(
    #     provider="lmstudio",
    #     model="openai/gpt-oss-20b",
    #     sensitive_value="S1234567D",
    #     original_text="Employee record: Name=Alex Tan, NRIC=S1234567D, Dept=IT. Backup NRIC=S1234567D.",
    #     redacted_text="Employee record: Name=Alex Tan, NRIC=■■■■■■■■■, Dept=IT. Backup NRIC=S1234■■■D.",
    #     mask_char="■",
    #     max_retries=3,
    # )
