# Security Review

Observed security properties:

- localhost service binding
- no shell execution exposed through the AI gateway
- no repository mutation path in v0.6
- repository content is treated as untrusted
- secrets are not persisted in the AI settings tables
