# Overview

<p align="center">
  <img src="./img/framex-logo.svg" alt="FrameX logo" width="120" height="120">
</p>

**FrameX** is a plugin-first Python framework for teams that need service decomposition, multi-team parallel development, private implementation boundaries, and one consistent service surface across local plugins and upstream APIs.

It is designed for services that are growing beyond a single cohesive code path and need clearer capability boundaries without forcing teams to build a custom platform first.

![FrameX architecture](./img/framex-architecture.svg)

## What Problem It Solves

FrameX is most useful when multiple teams need to ship capabilities in parallel, call each other through stable service interfaces, and keep implementation details private so each team can work without understanding or depending on other teams' codebases.

Use it when you need to:

- build service capabilities as plug-and-play modules
- let multiple engineers or teams ship in parallel with clearer ownership boundaries
- split a growing service into independently evolving capability units
- call other teams' capabilities without depending on their codebases
- expose local plugins and upstream APIs behind one consistent service surface
- integrate third-party or internal HTTP services with minimal client-side changes
- start with simple local execution and scale to Ray when needed
- keep the system extensible as capabilities, teams, and traffic grow

## Core Concepts

FrameX is built around a few core ideas:

- `Plugin`: a capability package with its own code, metadata, and API surface
- `@on_register()`: registers a plugin class as a runtime unit
- `@on_request(...)`: exposes plugin methods as HTTP APIs, internal callable APIs, or both
- `required_remote_apis`: declares which other plugin or HTTP APIs a plugin depends on
- `call_plugin_api(...)`: lets one capability call another through a stable service interface
- `@remote()`: keeps the same call style across local execution and Ray execution
- `proxy` plugin: makes upstream OpenAPI services look like part of the same service surface

## Why FrameX Instead Of Plain FastAPI

Plain FastAPI is a good choice for a single cohesive application. FrameX is better when the real problem is not route handling, but service decomposition, team boundaries, and cross-service integration.

Compared with plain FastAPI, FrameX gives you:

- plugin boundaries for clearer ownership between capabilities and teams
- a better development model for plug-and-play modules and parallel delivery
- one consistent surface for local capabilities and upstream HTTP services
- internal callable APIs in addition to normal HTTP routes
- explicit dependency declarations between capabilities
- the ability to start locally and move to Ray-backed execution without rewriting plugin code

If you only need a small application with a stable route surface and one codebase, plain FastAPI is usually simpler.

## Where It Fits Best

FrameX is a good fit when you want to:

- build modular service capabilities as plugins
- support multi-person or multi-team parallel development
- reduce cross-team code familiarity requirements
- expose local modules and upstream APIs behind one consistent service surface
- start with a simple deployment model and scale execution later

Typical scenarios include:

- multi-team service development with stable interfaces and private implementation boundaries
- capability-oriented service splitting inside one growing service
- transparent upstream HTTP integration through the same service boundary
- gradual scaling from local execution to Ray-backed execution
