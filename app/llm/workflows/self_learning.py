from loguru import logger

from app.models.llm_responses import LLMRegexSuggestion
from app.detect_redact.redaction import redact_text_by_regex
from app.llm.tasks.regex_suggest import suggest_regex_rule
from app.llm.tasks.redaction_judge import judge_redaction_success
from app.db.crud.regex_rule import create_rule

LLM_PROVIDER = "openrouter"
# LLM_MODEL = "openai/gpt-5.2"  # extremely smart
LLM_MODEL = "google/gemini-3-flash-preview"


def learn_single_sensitive_data(
    sample_text: str, sensitive_value: str, max_learning_attempts: int = 5
) -> bool:
    """Self-learning workflow for a single sensitive data item."""
    logger.bind(instance=f"Redaction of {sensitive_value}").info(
        f"Self-learning started with model->{LLM_MODEL} via provider->{LLM_PROVIDER}"
    )

    learning_is_successful = False

    while max_learning_attempts > 0 and not learning_is_successful:
        max_learning_attempts -= 1
        # * Suggest regex rule via LLM
        suggestion: LLMRegexSuggestion = suggest_regex_rule(
            provider=LLM_PROVIDER,
            model=LLM_MODEL,
            sample_text=sample_text,
            sensitive_value=sensitive_value,
            max_retries=3,
        )

        # debug
        print("Suggested regex rule:", suggestion)

        # * Evaluate the suggested rule
        redacted_text = redact_text_by_regex(
            text=sample_text,
            regex_rule=suggestion.rule,
            token="",
            mask_char="■",
            same_length=True,
        )

        # debug
        print("Redacted Text:", redacted_text)

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
            create_rule(
                name=suggestion.rule.name,
                domain=suggestion.rule.domain,
                data_category=suggestion.rule.data_category,
                description=suggestion.rule.description,
                pattern=suggestion.rule.pattern,
                active=True,
            )
            logger.bind(instance=f"Redaction of {sensitive_value}").success(
                "Learning succeeded"
            )
            return True

        # log retry info
        logger.bind(instance=f"Redaction of {sensitive_value}").warning(
            f"Redaction unsuccessful. Reason: {judge_result.reason}. "
            f"Retrying... ({max_learning_attempts} attempts left)"
        )

    # * Exhausted all attempts - learning failed
    logger.bind(instance=f"Redaction of {sensitive_value}").error("Learning failed")
    return False
