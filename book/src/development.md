# Development Guide

This document outlines the **branching strategy** and **commit message guidelines** for the project.\
Please follow these rules to ensure smooth collaboration and maintainability.

______________________________________________________________________

## 1) About Branches

### Master (`master | main`)

- The `master` branch is the **stable version** of the project.
- It contains the official releases ready for production.
- Only administrators are allowed to merge into `master`.

### Development (`dev`)

- The `dev` branch is used for **day-to-day development**.
- New features and bug fixes should be merged into `dev`.
- **Beta versions** are managed and released from the `dev` branch for testing before promotion to `master`.

### Personal / Feature Branches

- Developers should create a **personal branch** or **feature branch**:
  - Personal branch: named after the developer, e.g., `username`.
  - Feature branch: named with a clear prefix, e.g., `feat-login`, `fix-bug123`.
- When development is complete, submit a **Pull Request (PR)** targeting the `dev` branch for review.

## 2) Commit Message Guidelines

All commits must follow the format:

```
<tag>: <Message>
```

### Allowed Tags

- **feat**: New features
- **fix**: Bug fixes
- **build**: Build process or dependency changes
- **chore**: Routine tasks with no code changes (e.g., configs)
- **ci**: Continuous Integration / pipeline changes
- **docs**: Documentation updates
- **perf**: Performance improvements
- **style**: Code style changes (formatting, whitespace, etc.)
- **refactor**: Code refactoring without functional changes
- **test**: Adding or updating tests
- **update**: Minor updates or improvements

### Example

```
feat: add support for plugin configuration loading
fix: resolve bug in cross-plugin API call
docs: update README with setup instructions
```

## 3) Versioning Rules

- **Minor version bumps**

  - Triggered by commits tagged with: `update`.
  - Represents **major feature additions**, significant enhancements, or a large batch of changes.
  - Example: if the current version is `1.1.0`, the next release will be `1.2.0`.

- **Patch version bumps**

  - Triggered by commits tagged with: `feat`, `fix`, `perf`, `refactor`, `build`.
  - `feat`: small/new feature additions.
  - `fix`: bug fixes.
  - `perf`: performance improvements.
  - `refactor`: internal code refactoring.
  - `build`: dependency/build-related adjustments.
  - Example: if the current version is `1.1.0`, the next release will be `1.1.1`.

### Examples

- Current version: `1.1.0`
  - A commit with `update: improve plugin loading speed` → new version `1.2.0`
  - A commit with `fix: resolve proxy plugin crash` → new version `1.1.1`

______________________________________________________________________

By following these rules, the team ensures consistency, easier reviews, and automated version management.
