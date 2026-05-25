# Architectural decision record (ADR) 006: v1 local-only model and privacy policy

## Status

Accepted. BeatCue records local-only model execution as the v1 policy. Remote
model execution, hosted inference, and remote model adapters remain out of
scope until a later privacy and credentials design is accepted.

## Date

2026-05-20.

## Context and problem statement

BeatCue v1 is scoped to deterministic cue extraction from local video and audio
analysis. Later roadmap work will add optional semantic annotation through
model-backed adapters, but those adapters need a clear boundary before package
skeleton work, configuration profiles, and capability discovery make model
selection observable.

The unresolved question is how BeatCue should treat requested remote model
backends in v1. Remote execution can expose video frames, audio, captions,
prompts, object labels, provenance, and user configuration to a third-party
service. It also requires credential handling, payload retention rules, network
failure semantics, and explicit user opt-in. Those concerns are deliberately
not designed in the v1 architecture ratification phase.

BeatCue therefore needs a durable decision that remote model execution is not
available in v1, and that future adapters fail clearly when a caller requests a
remote backend that is not present in the configured capability set. A
configured capability set is the explicit list of model backends that the
composition root makes available for one BeatCue run. Availability must not be
inferred from an installed package or a model name alone.

## Decision drivers

- V1 must keep deterministic local cue extraction as the product boundary.
- User media and model prompts can contain sensitive content.
- Profiles may store model names and output defaults, but must not persist API
  keys, bearer tokens, session cookies, or remote-service credentials.
- Future model adapters need a failure contract before command-line interface
  (CLI), library API, and `agent-context` payloads expose capability
  information.
- The same open-source tooling family can support local execution, localhost
  model serving, and hosted endpoints, so BeatCue must classify locality by
  configured capability and endpoint rather than by adapter brand.
- The domain must not depend on Hugging Face, Ollama, HTTP clients, tokens,
  credentials, or remote-service objects.

## Options considered

### Option A: Keep the informal design wording only

This option leaves the existing design text in place without an ADR. It avoids
extra documentation now, but it leaves later adapter tasks to rediscover the
policy and could produce inconsistent behaviour between configuration,
profiles, CLI errors, and model adapters.

### Option B: Record a strict v1 local-only policy

This option accepts a local-only ADR and defines remote-backend failure as a
capability mismatch. It gives later model-adapter work one contract to
implement while leaving remote credentials, payload handling, and opt-in rules
to post-v1 design work.

### Option C: Permit experimental remote backends now

This option allows remote model execution behind early configuration. It may
accelerate experimentation, but it would create user-visible privacy,
credentials, payload logging, and network-boundary commitments before the
design exists.

| Topic                                | Informal wording | Strict local-only ADR | Experimental remote support    |
| ------------------------------------ | ---------------- | --------------------- | ------------------------------ |
| V1 scope clarity                     | Medium           | Strong                | Weak                           |
| Privacy risk                         | Medium           | Low                   | High                           |
| Credential handling required now     | No               | No                    | Yes                            |
| Future adapter guidance              | Weak             | Strong                | Medium                         |
| Hexagonal boundary                   | Medium           | Strong                | Medium                         |
| Implementation required in this task | None             | Documentation only    | Runtime and configuration work |

_Table 1: Local-only policy options._

## Decision outcome

BeatCue chooses option B. V1 performs local analysis only. Remote model
execution, hosted inference endpoints, remote model adapters, and implicit
remote downloads are out of scope until a separate privacy and credentials
design is accepted.

Future model adapters must advertise their locality and capabilities
explicitly. If a caller requests a remote backend that is absent from the
configured capability set, BeatCue must fail before inference with a clear
capability error. The error must name the unsupported backend and point to the
v1 local-only policy. It must not silently fall back from local execution to
remote execution, and it must not silently fall back from a requested remote
backend to a different local backend.

Future local model adapters must use explicit offline or local-file controls
where the underlying library provides them. For example, an adapter around a
library with a local-files-only option should enable that option for v1 local
execution rather than relying on best-effort network avoidance. Localhost model
servers are not automatically permitted merely because they use a loopback
address. A localhost backend still requires an explicit local capability entry,
and that capability must not generalize into hosted remote execution.

Profiles may name local models and default output settings. Profiles must not
store API keys, bearer tokens, session cookies, OAuth tokens, refresh tokens,
or other remote-service credentials. Credential storage, environment-variable
credential loading, redaction rules, payload retention rules, and remote opt-in
behaviour belong to the post-v1 remote privacy and credentials design.

## Goals and non-goals

Goals:

- Ratify BeatCue v1 as local-only for model execution.
- Define the future failure contract for unsupported requested remote
  backends.
- Preserve profile privacy by forbidding persisted remote credentials.
- Preserve the hexagonal boundary by keeping remote-service details out of the
  domain.
- Give later model-adapter, configuration, CLI, and `agent-context` tasks a
  stable contract to implement and test.

Non-goals:

- Implement production model adapters.
- Add remote inference clients, network calls, hosted endpoint support, model
  download behaviour, or credential storage.
- Add CLI flags, public Python APIs, BeatCue JSON fields, or `agent-context`
  payload fields in this ADR task.
- Decide GPU scheduling, remote model pricing, tenant isolation, payload
  retention, audit logging, or third-party service terms.
- Ban all future remote execution permanently. Remote execution may be
  reconsidered after roadmap item 6.1 defines privacy, credentials, opt-in, and
  failure semantics.

## Migration plan

1. Signpost this ADR from the technical design, developers' guide, users'
   guide, roadmap, and execution plan.
2. In the package skeleton and model-adapter tasks, define domain-owned
   capability concepts before implementing adapters.
3. When local semantic adapters are implemented, make missing local weights and
   unavailable local capabilities fail before inference.
4. When CLI, library API, or `agent-context` surfaces expose model capability
   information, add unit, behavioural, snapshot, and end-to-end tests for the
   unsupported-remote-backend failure path where relevant.
5. Defer all remote credential, redaction, payload logging, service opt-in, and
   hosted endpoint design to roadmap item 6.1.

## Known risks and limitations

- The configured capability set is not yet a concrete runtime type. This ADR
  records the contract that future package-skeleton and model-adapter tasks
  must implement.
- Localhost model servers can still cross process boundaries and may have their
  own logging or retention behaviour. Treating them as local requires explicit
  capability configuration and adapter-specific review.
- Some libraries may try to download model weights, metadata, or telemetry
  unless explicitly configured otherwise. Future adapters must opt into
  available offline or local-file controls and test the no-implicit-remote path.
- This ADR does not define the final error class, exit code, JSON diagnostic,
  or `agent-context` schema for capability failures. Those externally
  observable contracts belong to the implementation tasks that introduce the
  surfaces.

## Architectural rationale

This decision follows BeatCue's hexagonal architecture. The domain owns plain
capability concepts and model-port contracts. Adapters may integrate model
libraries, local model servers, or future hosted services, but those
infrastructure details must stay outside the domain and application contracts.

The decision also keeps the v1 privacy boundary explicit. BeatCue can ship
deterministic local cue extraction and later local semantic enrichment without
accidentally creating a remote-inference product. Remote execution remains a
separate design problem because it needs its own credentials, consent,
redaction, retention, failure, and auditability decisions.
