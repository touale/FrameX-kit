# CHANGELOG

<!-- version list -->

## v0.0.2-beta.4 (2025-07-11)

### Performance Improvements

- Optimize plugin config and data dir setup
  ([`1a15f5b`](https://github.com/touale/FrameX-kit/-/commit/1a15f5b0e614b205e33a9c1761faa5e08b5340bf))


## v0.0.2-beta.3 (2025-07-10)

### Performance Improvements

- Enhance plugin loading and settings integration
  ([`bf64c50`](https://github.com/touale/FrameX-kit/-/commit/bf64c508178b3fe62a33497384695d182d25b80e))


## v0.0.2-beta.2 (2025-07-10)

### Features

- Support mixed plugin import
  ([`1178495`](https://github.com/touale/FrameX-kit/-/commit/1178495bbcd94dca648be4214e87300326269a45))

### Performance Improvements

- Enhance proxy handling
  ([`ce18798`](https://github.com/touale/FrameX-kit/-/commit/ce187988139c57ad57e23784ba093d7b49efe803))


## v0.0.2-beta.1 (2025-07-09)

### Build System

- Add verbose flag to tag step in release task
  ([`9a1d528`](https://github.com/touale/FrameX-kit/-/commit/9a1d5287723efbaa1630a1ffbf9b358ade45e646))

### Continuous Integration

- Add git fetch to release step for better branch sync
  ([`c4d0afd`](https://github.com/touale/FrameX-kit/-/commit/c4d0afd00f0b3fad9b1cc3ab1ef6e24313c262a9))

- Disable allow_failure in secret_detection job
  ([`eb305f0`](https://github.com/touale/FrameX-kit/-/commit/eb305f0929ddc4f218a1b19065fac58f2bccb111))

### Features

- Add 'perf' to patch tags and optimize plugin API handling
  ([`c27982c`](https://github.com/touale/FrameX-kit/-/commit/c27982c82dca7e5390c37e6addb344f49f3688e1))

### Performance Improvements

- Refine API model typing and adjust on_request call_type
  ([`e1dda26`](https://github.com/touale/FrameX-kit/-/commit/e1dda267ed28f38fc99c711c9e9cdc6dd6bef61a))


## v0.0.1 (2025-07-09)

### Build System

- Configure semantic release
  ([`d4125f6`](https://github.com/touale/FrameX-kit/-/commit/d4125f661477e9d48a6bb0fc161cecf4fc07aa39))

### Code Style

- Enhance ruff config, add type hints, and refine plugin APIs
  ([`23bdaed`](https://github.com/touale/FrameX-kit/-/commit/23bdaedf229f66f1c38d4cbd27d25cf621c2d041))

- Enhance ruff config, update ServerConfig, and optimize plugin data dir
  ([`67df965`](https://github.com/touale/FrameX-kit/-/commit/67df96501387ea9517aca9521d9225fd57ab0964))

### Continuous Integration

- Add git checkout and status to CI/CD pipeline
  ([`3f757b9`](https://github.com/touale/FrameX-kit/-/commit/3f757b9ed07c2c651eb99771a1f24d9f9d88b9fd))

- Add poethepoet to release deps and update uv.lock
  ([`a3e5e53`](https://github.com/touale/FrameX-kit/-/commit/a3e5e538eee0a2f6ffc1aaa7bbdea1b130d41c72))

- Add release stage, update config, and refine tasks
  ([`3238f5f`](https://github.com/touale/FrameX-kit/-/commit/3238f5f01065ef51f8ba3116047d2141e5fd975a))

- Enhance pre-commit failure handling with diff output
  ([`f7324fa`](https://github.com/touale/FrameX-kit/-/commit/f7324fa91f4bccf605dfc9b7854e8e8229c587c2))

- Opt release step
  ([`d05a0cc`](https://github.com/touale/FrameX-kit/-/commit/d05a0cc33b09ab8aaf6321175bcce74c68d60b07))

- Optimize CI/CD config, update pre-commit repos, and adjust test-ci task
  ([`7c0332a`](https://github.com/touale/FrameX-kit/-/commit/7c0332ad8f3f1dcc155ba43f1ceba33abf33a358))

- Refactor CI/CD, add poe_tasks, and update dependencies
  ([`f5547ce`](https://github.com/touale/FrameX-kit/-/commit/f5547ce8ba5fa9327b0f0b879c5e44001ab2ec5f))

- Update branch matching and reorder config sections
  ([`0af1739`](https://github.com/touale/FrameX-kit/-/commit/0af1739af7111a254bbd0a610b7dcb97b40a02f0))

- Update CI/CD image path for Python container
  ([`848ca93`](https://github.com/touale/FrameX-kit/-/commit/848ca93f966c50e8f3debb725caf79c1c11bed52))

- Update secret detection and pre-commit pip version
  ([`2bbaab7`](https://github.com/touale/FrameX-kit/-/commit/2bbaab7aefa04ea8a2891fb1bbac81acba7f6296))

### Documentation

- Enhance plugin example in README
  ([`5243675`](https://github.com/touale/FrameX-kit/-/commit/52436758fe67298d79ff238b51dcc5b420b92bc9))

### Features

- Add BaseModel validation in on_request decorator
  ([`cebf955`](https://github.com/touale/FrameX-kit/-/commit/cebf955e65ebdd05533d385c27f351a0f93a4a7c))

- Add config support and proxy plugin enhancements
  ([`a8ea1db`](https://github.com/touale/FrameX-kit/-/commit/a8ea1db933bda9e506eff2f9abf600f25d293dfc))

- Add proxy plugin and enhance API response handling
  ([`c028153`](https://github.com/touale/FrameX-kit/-/commit/c028153955d348fb25e23b4eabbbf4de300bbd1f))

- Add proxy plugin support and enhance API handling
  ([`a482823`](https://github.com/touale/FrameX-kit/-/commit/a482823449b3b4431e1c0cc43f91d773f213f4ba))

- Add streaming support and optimize API registration
  ([`35a7c8a`](https://github.com/touale/FrameX-kit/-/commit/35a7c8a1e4e94abb7ab13668078a7c6bb92ddffd))

- Enhance logging, update config, and optimize plugin setup
  ([`9a27f06`](https://github.com/touale/FrameX-kit/-/commit/9a27f06d8bd8b8a593ebc830f1a7a54627793780))

### Performance Improvements

- Optimize BaseModel transfer for remote calls
  ([`57a9c5c`](https://github.com/touale/FrameX-kit/-/commit/57a9c5c7271a23961e1564494881607604151808))

### Refactoring

- Refactor plugin loading and API setup in framex
  ([`483c6e5`](https://github.com/touale/FrameX-kit/-/commit/483c6e5601f4c6f2c5846e7e55112d0e7a40e348))

### Testing

- Simplify CI/CD, update pre-commit, and configure ruff
  ([`348b3f8`](https://github.com/touale/FrameX-kit/-/commit/348b3f80f6e74494234eb4c05780606332e326d2))
