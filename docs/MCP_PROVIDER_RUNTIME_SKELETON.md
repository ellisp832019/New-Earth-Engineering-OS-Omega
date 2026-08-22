# NEOS MCP Provider Runtime Skeleton

## Ownership

The MCP provider skeleton is owned by NEOS. Platform Core remains the authority
for MCP identities, schemas, manifests, capabilities, compatibility, and policy
declarations. GAIA is a future MCP client. Command Centre is a future
operational approval/audit surface.

## Bundle Dependency

The provider accepts one explicit installed bundle directory through
`McpProviderConfig`. It does not search parent directories, scan drives, or
read the Platform Core checkout. The bundle must contain the expected manifest,
registry, and contract paths.

Required pinned values are:

- bundle ID: `new-earth-mcp-contract-bundle-v1`;
- bundle format: `1.0.0`; and
- baseline: `NE-MCP-READONLY-V1-DECLARATIVE-2026-08-21`.

The provider independently checks the NEOS server identity
`neos-engineering-read-server`, manifest
`neos.engineering.read.manifest`, GAIA client registration, and the declared
read-only capability, tools, resources, and queries. Write-like contract content
fails closed.

## Lifecycle and Feature Gate

The provider is an explicit/manual NEOS-owned process. It is not auto-started
and does not allow GAIA to spawn arbitrary processes. The runtime is disabled by
default. It can be enabled explicitly through `McpProviderConfig(enabled=True)`
or `NEOS_MCP_PROVIDER_ENABLED=true` when configured by a future owner.

The development entrypoint is:

```text
neos mcp-provider --bundle <verified-bundle> --enable
```

No installer, activation command, update mechanism, or external repository
mutation is provided.

## Transport Boundary

The skeleton exposes only a testable JSON-lines stdio boundary. It creates no
TCP socket, HTTP listener, WebSocket, LAN binding, or remote transport. The
existing NEOS localhost HTTP service is not called by this slice.

## Recognized Operations

The operation allowlist is loaded from the bundle's declared read tools. The
current recognized IDs are:

- `neos.health.read`
- `neos.project.summary.read`

`neos.health.read` executes the existing in-process `service_health` source used
by the HTTP `/health` route. It returns the health result in the MCP response
envelope and performs no self-HTTP request. `neos.project.summary.read` reads
the existing in-process `project_summary` source used by the HTTP
`/projects/{project_id}/summary` route. It requires exactly one `project_id`
argument. Unknown clients, malformed requests, invalid project IDs, unexpected
arguments, and unknown operations are rejected.

Health execution requires the provider to be enabled, a valid pinned bundle to
be loaded, and the NEOS health database to be configured. Health failures are
returned as controlled MCP errors without stack traces.
Project-summary not-found and unavailable conditions are returned as controlled
results, and partial or stale markers from NEOS are preserved.

## Fail-Closed Behavior

Initialization fails for a missing or malformed bundle, wrong bundle identity or
format, baseline mismatch, missing NEOS identity, missing or mismatched server
manifest, missing declared read-only targets, or write-like contract content.
There is no permissive fallback.

## Runtime Exclusions

MCP-02E does not implement query execution, authorization, approval, audit
persistence, GAIA integration, shell execution, subprocess spawning, network
transport, or write capability.

## Next Slice

MCP-02F may add the GAIA MCP client skeleton. No GAIA integration is included
in this provider slice.
