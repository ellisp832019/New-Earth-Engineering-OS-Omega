# Provider Abstraction

NEOS uses a provider boundary so AI can be local, mock, or HTTP-compatible without changing the desktop app.

## Implemented Providers

- `MockProvider` - deterministic local provider used for out-of-the-box behavior and tests.
- `NullProvider` - explicit no-provider mode.
- `CompatibleHTTPProvider` - OpenAI-style chat completion adapter for local or remote endpoints.

## Capability Model

- chat
- structured output
- streaming support flag
- read-only tool routing stays on the NEOS side

## Current Default

The local mock provider is the default configuration stored in the service database.
