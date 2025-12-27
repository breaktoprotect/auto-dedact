from typing import Optional
from openai import OpenAI
import os


def get_client(provider: str) -> OpenAI:
    if provider == "lmstudio":
        return OpenAI(
            api_key="lm-studio",
            base_url="http://localhost:1234/v1",
        )

    if provider == "openrouter":
        return OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )

    if provider == "azure":
        return OpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            base_url=os.environ[
                "AZURE_OPENAI_BASE_URL"
            ],  # https://xxx.openai.azure.com/openai/v1/
        )

    raise ValueError("unknown provider")


def prompt_llm_single(
    *,
    client: OpenAI,
    model: str,
    user: str,
    system: Optional[str] = None,
) -> str | None:
    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    messages.append({"role": "user", "content": user})

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    return resp.choices[0].message.content


def prompt_llm_session(
    *,
    client: OpenAI,
    model: str,
    user: str,
    session: Optional[list] = None,
    system: Optional[str] = None,
) -> tuple[str | None, list]:
    # Initialize session if this is the first turn
    if session is None:
        session = []
        if system:
            session.append({"role": "system", "content": system})

    # Append user message
    session.append({"role": "user", "content": user})

    # Call LLM
    resp = client.chat.completions.create(
        model=model,
        messages=session,
    )

    reply = resp.choices[0].message.content if resp.choices else None

    # Append assistant reply to session
    if reply is not None:
        session.append({"role": "assistant", "content": reply})

    return reply, session


#! Test only
if __name__ == "__main__":
    # * Pick provider + model
    client = get_client("lmstudio")
    model = "openai/LOCAL_MODEL_NAME"

    # * Single prompt test
    # print("=== SINGLE PROMPT ===")
    # reply = prompt_llm_single(
    #     client=client,
    #     model=model,
    #     system="Explain CICD in a few concise sentences.",
    #     user="",
    # )
    # print(reply)

    # * Session prompt test
    # print("\n=== SESSION PROMPT ===")
    # session = None

    # reply, session = prompt_llm_session(
    #     client=client,
    #     model=model,
    #     system="You are an expert in Continuous Integration and Continuous Deployment (CICD). Your answers are concise and informative.",
    #     user="Explain CICD in a few concise sentences.",
    #     session=session,
    # )
    # print(reply)
    # print("---\n")

    # reply, session = prompt_llm_session(
    #     client=client,
    #     model=model,
    #     user="Give examples of popular CICD tools.",
    #     session=session,
    # )
    # print(reply)

    # * Emoji only test
    print("\n=== EMOJI ONLY PROMPT: SYSTEM ===")
    reply = prompt_llm_single(
        client=client,
        model=model,
        system="You are only allowed to respond using emojis. Do not use any words or characters other than emojis in your response.",
        user="Give me a cookie recipe.",
    )
    print(reply)
    print()

    print("\n=== EMOJI ONLY PROMPT: USER ===")
    reply = prompt_llm_single(
        client=client,
        model=model,
        system="",
        user="You are only allowed to respond using emojis. Do not use any words or characters other than emojis in your response. Give me a cookie recipe.",
    )
    print(reply)
    print()
