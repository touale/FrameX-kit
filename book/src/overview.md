# Overview

## What is FrameX?

**FrameX** is a lightweight, pluggable Python framework designed for building modular and extensible algorithmic systems.

It provides a clean architecture that supports **dynamic plugin registration**, **isolated execution**, and **secure invocation**, making it well-suited for multi-algorithm collaboration, heterogeneous task scheduling, and distributed deployments.

Each algorithm can be developed, deployed, and loaded as an independent plugin, achieving infinite scalability.

<div align="center">
  <figure>
    <img src="./img/v2andv3.svg" alt="algov2" width="100%">
    <figcaption>A Comparison Between the v2 (Regular FastAPI) and v3 (FrameX) Architectures</figcaption>
  </figure>
</div>

**Note:**

- v2 can be considered a regular FastAPI project.

## Key Features

- **Plugin-Based Architecture**\
  Algorithms are encapsulated as independent plugins, which can be added, removed, or updated without impacting others.
- **Distributed Execution with Ray**\
  Optional Ray integration delivers high concurrency, high throughput, and resilience against blocking tasks.
- **Cross-plugin Calls**\
  Enables interaction between local and remote plugins. If a plugin is not available locally, the system automatically routes the request to the corresponding cloud plugin.
- **Backward Compatibility**\
  FrameX can seamlessly forward requests to standard FastAPI endpoints, enabling smooth integration without code changes.
- **Streaming Support**\
  Native support for streaming responses, suitable for long-running or large-scale inference tasks.
- **Built-in Observability**\
  Integrated logging, tracing, and performance monitoring to ease debugging and root-cause analysis.
- **Flexible Configuration & Tooling**\
  Clean configuration management (`.toml`, `.env`) plus scaffolding, packaging, and CI/CD integration for automation.

<div align="center">
  <figure>
    <img src="./img/hub.svg" alt="algov2" width="50%">
    <figcaption>FrameX hub</figcaption>
  </figure>
</div>

## Application Scenarios

- **Quick Onboarding & Project Setup**\
  New developers can rapidly bootstrap projects and reuse existing algorithms via remote calls, without accessing legacy code.

- **Multi-Team Parallel Development & Isolation**\
  Different teams manage their own isolated plugin spaces. Access control ensure security and reduce interference.

- **Hybrid Deployment & Smooth Migration**\
  Supports hybrid calls with other FastAPI services, dynamic endpoint registration, and multi-instance FrameX deployment with inter-instance communication.

- **Modular Delivery & Commercial Licensing**\
  Deliver selected algorithm modules locally to clients while keeping others as remotely callable services. This supports licensing, pay-per-use, and flexible business models.
