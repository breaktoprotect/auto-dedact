# Description

A system that allows detection and/or redaction of sensitive data defined by user. The system can self-learn via a learning loop using LLM as an analyst to suggest detection mechanisms (e.g. regex pattern) and then as a judge to see if detection and redaction was complete.

# How does the self-learning work?

Samples of sensitive data is to be provided. For each sample, the LLM will read sensitive data definition (e.g. credit card PAN) and the sample data contents containing the sensitive data. LLM will then be asked to suggest a regex pattern to detect and redact. Using the newly suggested regex pattern, the sample data will be parsed to detect and redact the data. The output and the newly suggested regex pattern will then be sent to the LLM in a new session to judge if the detect-redact was complete and successful. If successful, the regex pattern will be added into a persistent storage (e.g. Database with description and medatadata). If incomplete, the LLM is to suggest one or more regex patterns in attempt to detect and redact the defined sensitive data in the sample. The loop continues until success or until the defined max threshold attempts (e.g. 5 times).
