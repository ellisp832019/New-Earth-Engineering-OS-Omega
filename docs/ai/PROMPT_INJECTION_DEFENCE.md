# Prompt Injection Defence

NEOS scans repository text for instruction-like content such as:

- ignore previous instructions
- system prompt
- developer message
- execute command
- reveal credentials

Suspicious content is not treated as instructions. It is surfaced as evidence with a safety finding.
