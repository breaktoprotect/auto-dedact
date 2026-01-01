import instructor

from app.models.llm_responses import LLMRegexSuggestion
from app.llm.llm_client import get_instructor_client, get_client


def main():
    provider = "lmstudio"
    model = "openai/gpt-oss-20b"

    # client: OpenAI = get_client(provider)
    # client = get_instructor_client(provider=provider)

    base_client = get_client(provider)
    client = instructor.patch(base_client, mode=instructor.Mode.JSON_SCHEMA)

    SYSTEM_PROMPT = """
    You are a senior data loss prevention engineer.

    You MUST respond with valid YAML ONLY.
    Do NOT include markdown, explanations, or extra text.
    """.strip()

    USER_PROMPT = """
    Sensitive value:
    4012 8888 8888 1881

    Sample text:
    blah blah 4012 8888 8888 1881 blah

    Propose ONE regex rule that detects the sensitive value. It must be robust enough to detect the value in different contexts.
    """.strip()

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        response_model=LLMRegexSuggestion,
        max_retries=5,
    )  # type: ignore

    print("RAW RESPONSE:", resp)


if __name__ == "__main__":
    main()
