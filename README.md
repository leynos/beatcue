# BeatCue

*Machine-readable timing cues for video analysis.*

BeatCue is being designed as both a Python library and an agent-friendly CLI
for extracting editorial timing cues from video files. The planned package
identifies cuts, transitions, audio beats, ease-in and ease-out ramps, rising
and falling audio-visual intensity, object entries and exits, and selected
image-to-text annotations.

______________________________________________________________________

## Why BeatCue?

Video analysis tools often mix timing, captions, and presentation into one
opaque result. BeatCue keeps those concerns separate:

- **Cue sheets first**: Emit WebVTT metadata cues, BeatCue JSON, and
  OpenTimelineIO markers for downstream tooling.
- **Explainable timing**: Base cues on colour, motion, audio, scene, and object
  signals before semantic annotations are attached.
- **Library and CLI parity**: Keep the Python API and command-line behaviour
  on the same domain model.
- **Agent-native operation**: Design the CLI for `--json`, bounded output,
  non-interactive execution, profiles, jobs, and explicit delivery targets.

______________________________________________________________________

## Quick start

### Installation

This repository currently provides the package skeleton and design documents.
Install the development environment from the repository root:

```bash
uv sync --group dev
```

### Basic usage

The current package exposes a small smoke-check function while the roadmap
builds the video-analysis API and CLI:

```python
from beatcue import hello

print(hello())
```

Run it from the repository root:

```bash
uv run python -c "from beatcue import hello; print(hello())"
```

Expected output:

```text
hello from Python
```

______________________________________________________________________

## Features

Planned capabilities are defined in the technical design and roadmap:

- Hexagonal Python architecture with dependency injection.
- Cyclopts-based CLI specification and tiered configuration.
- Rich human output with clean ASCII machine and LLM-facing payloads.
- Cuprum-backed subprocess calls for `ffprobe`, `ffmpeg`, and helper tools.
- CmdMox-backed tests for external command adapters.
- Deterministic cue extraction from colourgrams, optical flow, scene changes,
  and audio features.
- Optional semantic annotation and object tracking behind domain-owned ports.
- WebVTT, BeatCue JSON, and OpenTimelineIO output writers.

______________________________________________________________________

## Learn more

- [Users' Guide](docs/users-guide.md) — user-facing documentation as the
  package grows
- [Technical design](docs/beatcue-technical-design.md) — architecture,
  contracts, and implementation decisions
- [Roadmap](docs/roadmap.md) — planned features and delivery sequence
- [Contributor guidance](AGENTS.md) — repository workflow and engineering
  standards

______________________________________________________________________

## Licence

ISC — see [LICENSE](LICENSE) for details.

______________________________________________________________________

## Contributing

Contributions are welcome. Please read [AGENTS.md](AGENTS.md) before changing
the repository; it defines the local workflow, quality gates, and documentation
standards.
