from loguru import logger

from app.logging_config import setup_logging
from app.llm.workflows.self_learning import learn_single_sensitive_data

# TODO: temporary test cases for dev
TEST_CASES = [
    {
        "name": "Easy: NRIC clean token",
        "sample_text": "Customer NRIC: S1234567D\nPlease process.",
        "sensitive_value": "S1234567D",
        "max_attempts": 3,
    },
    {
        "name": "Easy: Email",
        "sample_text": "Contact: alex.tan@example.test\nTicket#123",
        "sensitive_value": "alex.tan@example.test",
        "max_attempts": 3,
    },
    {
        "name": "Medium: PAN with spaces",
        "sample_text": "Card used: 4111 1111 1111 1111\nExpiry: 09/26\nCVV: 123",
        "sensitive_value": "4111 1111 1111 1111",
        "max_attempts": 5,
    },
    {
        "name": "Medium: Bank account with hyphens",
        "sample_text": "Refund account: 123-456789-0\nBank: DBS\nName: Alex Tan",
        "sensitive_value": "123-456789-0",
        "max_attempts": 5,
    },
    {
        # This is designed to be annoying:
        # - Same sensitive value appears multiple times
        # - Some occurrences have extra punctuation attached
        # - One occurrence is split by line breaks / spacing
        # - Has decoy-like nearby numbers to confuse naive regex
        "name": "Hard: PAN repeated, mixed formatting, tricky boundaries (should take several tries)",
        "sample_text": (
            "Incident report:\n"
            "User claims the card is not stored.\n\n"
            "Primary PAN: [4111-1111-1111-1111].\n"
            "Alt format: 4111 1111 1111 1111 (entered in web form)\n"
            "Split across lines: 4111 1111\n"
            "1111 1111\n\n"
            "Decoys nearby: 4111-1111-1111-1112, 4111-1111-1111-1110 (NOT the same)\n"
            "Also appears with punctuation: (4111-1111-1111-1111), and trailing colon 4111-1111-1111-1111:\n"
        ),
        # Pick ONE canonical sensitive_value. The loop should learn a regex for the "type",
        # and redact all occurrences (judge should enforce it).
        "sensitive_value": "4111-1111-1111-1111",
        "max_attempts": 10,
    },
    {
        "name": "Hard: NRIC embedded + punctuation + repeated",
        "sample_text": (
            "Employee record:\n"
            "Name: Alpina Goh\n"
            "NRIC=S1234567D; dept=OPS\n"
            "Audit log: user(S1234567D) authenticated.\n"
            "Note: 'S1234567D,' appeared in chat.\n"
        ),
        "sensitive_value": "S1234567D",
        "max_attempts": 8,
    },
    {
        "name": "Hard: Phone number with multiple acceptable formats",
        "sample_text": (
            "Call logs:\n"
            "1) +65 9876 4321\n"
            "2) (+65)98764321\n"
            "3) 9876-4321\n"
            "Please remove the phone.\n"
        ),
        "sensitive_value": "+65 9876 4321",
        "max_attempts": 10,
    },
]


def main() -> None:
    setup_logging()

    logger.info("Self-learning run started")

    for i, case in enumerate(TEST_CASES, start=1):

        learn_single_sensitive_data(
            sample_text=case["sample_text"],
            sensitive_value=case["sensitive_value"],
            max_learning_attempts=case["max_attempts"],
        )


if __name__ == "__main__":
    main()
