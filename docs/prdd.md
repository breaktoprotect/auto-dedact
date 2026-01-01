# Description

A system that allows detection and/or redaction of sensitive data defined by user. The system can self-learn via a learning loop using LLM as an analyst to suggest detection mechanisms (e.g. regex pattern) and then as a judge to see if detection and redaction was complete.

# How does the self-learning work?

Samples of sensitive data is to be provided. For each sample, the LLM will read sensitive data definition (e.g. credit card PAN) and the sample data contents containing the sensitive data. LLM will then be asked to suggest a regex pattern to detect and redact. Using the newly suggested regex pattern, the sample data will be parsed to detect and redact the data. The output and the newly suggested regex pattern will then be sent to the LLM in a new session to judge if the detect-redact was complete and successful. If successful, the regex pattern will be added into a persistent storage (e.g. Database with description and medatadata). If incomplete, the LLM is to suggest one or more regex patterns in attempt to detect and redact the defined sensitive data in the sample. The loop continues until success or until the defined max threshold attempts (e.g. 5 times).

# Training Workflow (Straight-Through, LLM-in-the-Loop)

This workflow enables AutoDedact to learn new sensitive data detection rules by iteratively proposing, validating, executing, and validating regex-based redaction logic.

The design is intentionally straight-through and deterministic, with LLMs used only where human-like reasoning adds value.

---

## Step 1 — Regex Suggestion (LLM)

The LLM is prompted to suggest a regex rule based on:

- a sample text that contains sensitive data
- the explicit sensitive value to be detected

Example input

Sample text:
[BEGIN_SAMPLE]
blah blah blah blah 4111-1111-1111-1111
blah blah blah blah blah..
[END_SAMPLE]

Sensitive data:
[BEGIN_SENSITIVE]
4111-1111-1111-1111
[END_SENSITIVE]

Expected JSON output (schema-locked)
[BEGIN_JSON]
{
"name": "credit_card_pan_dashes",
"domain": "FINANCIAL",
"data_category": "CREDIT_CARD",
"description": "Detects credit card PAN formatted with dash separators",
"pattern": "<regex pattern>"
}
[END_JSON]

---

## Step 2 — Regex Validation (Programmatic)

The system validates the suggested regex without LLM involvement.

Validation checks include:

- Regex compiles successfully
- Regex matches the provided sensitive data
- Basic safety checks (e.g. no obvious catastrophic backtracking or over-greedy patterns)

If validation fails, the workflow returns to Step 1.
A retry budget applies.

---

## Step 3 — Detection & Redaction (Programmatic)

The validated regex is executed against the sample text to produce redacted output.

Example output:
[BEGIN_OUTPUT]
blah blah blah blah ■■■■■■■■■■■■■■■■■■■
blah blah blah blah blah..
[END_OUTPUT]

Redaction strategies may include:

- fixed token replacement (e.g. [CREDIT CARD REDACTED])
- same-length masking (e.g. ■) to prevent derivation of original values

---

## Step 4 — Redaction Effectiveness Review (LLM Judge)

The LLM is prompted as an expert sensitive data validation analyst to determine whether redaction was successful.

LLM input includes:

- Regex pattern used
- Original text
- Redacted output

Decision rules:

- If redaction is incomplete, incorrect, reversible, or misses variants, set successful_redaction to false
- If all occurrences are properly redacted and no residual sensitive patterns remain, set successful_redaction to true

Expected JSON output (successful)
[BEGIN_JSON]
{
"successful_redaction": true,
"reason": "All occurrences of PAN were masked; no residual PAN patterns detected.",
"regex_pattern": "<regex pattern>"
}
[END_JSON]

Expected JSON output (unsuccessful)
[BEGIN_JSON]
{
"successful_redaction": false,
"reason": "Regex missed PANs without dash separators.",
"regex_pattern": "<suggested improved regex pattern>"
}
[END_JSON]

When unsuccessful, regex_pattern must contain a suggested improvement.

---

## Step 5 — Persist or Retry

- If successful_redaction == true:
  - Persist the regex rule and metadata into the rule database
- If successful_redaction == false:
  - Retry the workflow (implementation-defined starting step)
  - Abort once retry limit is exceeded

---

## Notes

- This is a deterministic workflow, not a free-form agent.
- LLMs are used only for:
  - hypothesis generation (Step 1)
  - expert judgment (Step 4)
- All execution, validation, and persistence are controlled programmatically.

This design ensures:

- bounded behavior
- auditability
- reproducibility
- minimal LLM trust surface

The workflow can later be extended to support:

- multiple regex suggestions
- checksum or algorithmic validators (e.g. Luhn)
- semantic or context-based detection strategies
