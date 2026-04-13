# Basic Usage Overview

This section covers the day-to-day programming model of FrameX.

The goal is to help you build service capabilities as plugins, expose them through a consistent API surface, and organize a codebase that can scale across people, teams, and execution modes.

## What You Will Learn

After this section, you will understand how to:

1. organize a FrameX project and place plugin modules clearly
1. define plugin metadata and register runtime units with `@on_register()`
1. expose HTTP APIs and internal callable APIs with `@on_request(...)`
1. declare dependencies with `required_remote_apis` and call capabilities with `call_plugin_api(...)`
1. configure plugins and runtime settings cleanly
1. load plugins and start the service through CLI or configuration
1. debug and test plugins in local, non-Ray mode

## Section Roadmap

- [Project Structure](./project_structure.md)
  Understand how to organize a FrameX project and where plugin modules usually live.

- [Plugin Register & API Expose](./plugin_register_&_api_expose.md)
  Learn how plugin metadata, `@on_register()`, and `@on_request(...)` define the service surface.

- [Cross-Plugin Access](./cross_plugin_access.md)
  Learn how one capability calls another through `required_remote_apis` and `call_plugin_api(...)`.

- [Plugin Configuration](./plugin_configreation.md)
  Define plugin-specific configuration and load it through FrameX settings.

- [Plugin Loading & Startup](./plugin_loading_&_startup.md)
  Start FrameX with the right plugin set through CLI options and configuration files.

- [Plugin Debugging & Testing](./plugin_debugging_&_testing.md)
  Debug plugins locally and test them with normal FastAPI-compatible tooling.

## What This Section Is For

Use this section when you are:

- building your first real plugin
- turning a growing service into modular capabilities
- standardizing how teams expose and consume service interfaces
- preparing for later use of proxy mode or Ray without changing the basic development model
