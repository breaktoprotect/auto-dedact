from loguru import logger
import time

from app.db.sqlmodels.regex_rule import RegexRuleSQL
from app.db.crud.regex_rule import list_all_rules
from app.detect_redact.redaction import redact_text_by_regex
from app.detect_redact.detection import detect_text
from app.llm.tasks.redaction_judge import judge_redaction_success

LLM_PROVIDER = "openrouter"
# LLM_MODEL = "openai/gpt-5.2"  # extremely smart
LLM_MODEL = "google/gemini-3-flash-preview"


def verify_regex_coverage(sample_text: str, sensitive_value: str) -> bool:
    # * Pull all regex from DB
    all_regex_rules: list[RegexRuleSQL] = list_all_rules(active=True)

    # * Loop through all regex rules
    redacted_text = sample_text
    t0 = time.perf_counter()
    for regex_rule in all_regex_rules:
        redacted_text = redact_text_by_regex(
            text=redacted_text,
            regex_rule=regex_rule,  # type: ignore
            token="",
            mask_char="■",
            same_length=True,
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    logger.info(
        f"Applied all regex rules in {elapsed_ms:.2f} ms | instance=Redaction of {sensitive_value}"
    )

    # * Judge if the redaction is successful
    judge_result = judge_redaction_success(
        provider=LLM_PROVIDER,
        model=LLM_MODEL,
        sensitive_value=sensitive_value,
        original_text=sample_text,
        redacted_text=redacted_text,
        mask_char="■",
    )

    print("Judge Result:", judge_result)
    print("-" * 40)

    if judge_result.successful_redaction:
        logger.bind(instance=f"Redaction of {sensitive_value}").success(
            "Redaction already exist."
        )
        return True
    else:
        logger.bind(instance=f"Redaction of {sensitive_value}").error(
            "Missing effective regex to sufficiently redact sensitive string."
        )
        return False


if __name__ == "__main__":
    sample_text = "Contact: alex.tan@example.test\nTicket#123"
    sensitive_value = "alex.tan@example.test"
    verify_regex_coverage(sample_text=sample_text, sensitive_value=sensitive_value)

    # Expected to fail
    untrained_test_case = {
        "name": "Hard: AWS Secret Access Key leaked in app config + log line",
        "sample_text": (
            "prod deploy notes:\n"
            "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
            "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
            "\n"
            "cloud-init output:\n"
            "[INFO] Loaded AWS credentials from environment.\n"
        ),
        "sensitive_value": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "max_attempts": 10,
    }

    verify_regex_coverage(
        sample_text=untrained_test_case["sample_text"],
        sensitive_value=untrained_test_case["sensitive_value"],
    )
