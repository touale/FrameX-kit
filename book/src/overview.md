# Overview

## What is FrameX?

**FrameX** is a lightweight, pluggable Python framework designed for building modular and extensible algorithmic systems.\
It provides a clean architecture that supports **dynamic plugin registration**, **isolated execution**, and **secure invocation**, making it well-suited for multi-algorithm collaboration, heterogeneous task scheduling, and distributed deployments.

As an infrastructure layer for algorithms, FrameX emphasizes **extensibility**, **isolation**, and **runtime flexibility**, enabling teams to construct complex algorithmic platforms with modular components.\
Each algorithm can be developed, deployed, and loaded as an independent plugin, achieving infinite scalability.

______________________________________________________________________

## Key Features

- **Plugin-Based Architecture**\
  Algorithms are encapsulated as independent plugins, which can be added, removed, or updated without impacting others.
- **Distributed Execution with Ray**\
  Optional Ray integration delivers high concurrency, high throughput, and resilience against blocking tasks.
- **Security & Isolation**\
  Plugins run in isolated environments by default. Legacy algorithms remain accessible via safe remote calls.
- **Backward Compatibility**\
  v3 can seamlessly forward requests to v2 APIs, enabling gradual migration without code changes.
- **Streaming Support**\
  Native support for streaming responses, suitable for long-running or large-scale inference tasks.
- **Built-in Observability**\
  Integrated logging, tracing, and performance monitoring to ease debugging and root-cause analysis.
- **Flexible Configuration & Tooling**\
  Clean configuration management (`.toml`, `.yaml`, `.env`) plus scaffolding, packaging, and CI/CD integration for automation.

## Application Scenarios

- **Quick Onboarding & Project Setup**\
  New developers can rapidly bootstrap projects and reuse existing algorithms via remote calls, without accessing legacy code.

- **Multi-Team Parallel Development & Isolation**\
  Different teams manage their own isolated plugin spaces. Access control ensure security and reduce interference.

- **Hybrid Deployment & Smooth Migration**\
  Support for mixed v2 + v3 environments ensures business continuity. Legacy algorithms are automatically handled by v2 until migrated.

- **Modular Delivery & Commercial Licensing**\
  Deliver selected algorithm modules locally to clients while keeping others as remotely callable services. This supports licensing, pay-per-use, and flexible business models.
