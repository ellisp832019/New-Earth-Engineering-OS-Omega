# Local AI Providers

NEOS is designed for localhost-first AI operation.

## Supported Shapes

- Local OpenAI-compatible endpoints
- Mock/deterministic local provider
- Disabled provider mode

## Configuration

Stored settings:

- provider id
- model
- endpoint
- timeout
- context budget
- max output tokens
- streaming flag

Secrets are not stored in ordinary project JSON. If a real provider needs an API key, it must come from the environment.
