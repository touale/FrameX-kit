# Basic Usage Overview

This section introduces the **basic concepts and workflow** for using FrameX as a plugin-based algorithm framework.\
It is designed for developers who are starting with FrameX and want to quickly understand how to:

- Organize their project
- Register plugins and expose APIs
- Configure plugins
- Load and run plugins
- Debug and test their implementations

______________________________________________________________________

## 1) What you will learn

After reading this section, you will be able to:

1. **Understand the project structure**\
   Learn how to organize your project files and keep plugins under the `plugins/` directory.

1. **Register and expose plugin APIs**\
   Use `__plugin_meta__ = PluginMetadata(...)` and `@on_request(...)` to define plugin metadata and expose endpoints.

1. **Cross-plugin communication**\
   Call APIs from other plugins using `_call_remote_api(...)`, and handle synchronous, streaming, and function-style calls.

1. **Manage plugin configuration**\
   Define plugin-specific configuration with `pydantic.BaseModel` and inject it via `config_class`.

1. **Load and start plugins**\
   Load plugins via configuration (`config.toml`) or dynamically from code, and run the FrameX runtime with `framex.run()`.

1. **Debug and test plugins**\
   Use FrameX in non-Ray mode for debugging, and leverage FastAPI’s `TestClient` for writing automated tests.

## 2) Roadmap of this Section

- [Project Structure](./project_structure.md)\
  How to organize your project and where to place your plugins.

- [Plugin Register & API Expose](./plugin_register_&_api_expose.md)\
  How to define plugin metadata and expose APIs.

- [Cross-Plugin Access](./cross_plugin_access.md)\
  How to call APIs provided by other plugins.

- [Plugin Configuration](./plugin_configreation.md)\
  How to define and load plugin configurations.

- [Plugin Loading & Startup](./plugin_loading_&_startup.md)\
  How to load and run plugins from configuration or code.

- [Plugin Debugging & Testing](./plugin_debugging_&_testing.md)\
  How to debug your plugins and write automated tests.

______________________________________________________________________

👉 With these basics, you will be ready to build modular, extensible, and testable algorithmic systems with **FrameX**.
