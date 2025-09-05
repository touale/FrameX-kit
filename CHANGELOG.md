# CHANGELOG

<!-- version list -->

## v0.1.9 (2025-09-05)

### Features

- Update plugin loading and config handling, add documentation book for framex
  ([`b686a9b`](https://github.com/touale/FrameX-kit/-/commit/b686a9b53fd3d7d919f884b4595655b204c03fb6))


## v0.1.8 (2025-09-02)

### Features

- Optimize API handling and plugin management
  ([`de76f9f`](https://github.com/touale/FrameX-kit/-/commit/de76f9f3f776a856e864306e6592f21fb3aacc2a))


## v0.1.7 (2025-08-08)

### Features

- Add remote func support and update tests
  ([`fff01e3`](https://github.com/touale/FrameX-kit/-/commit/fff01e3cd72b20155f8b07c13fe6ecc85a0fb602))


## v0.1.6 (2025-07-31)

### Features

- Add path white/black lists to ProxyPlugin and modify APIIngress return type
  ([`a0f5ba8`](https://github.com/touale/FrameX-kit/-/commit/a0f5ba8a219cfdbbbc2b16a9cf071a6b6d364b98))


## v0.1.5 (2025-07-22)


## v0.1.5-beta.1 (2025-07-22)

### Bug Fixes

- Lock ray version to 2.47.1 and update uv.lock
  ([`1a7d274`](https://github.com/touale/FrameX-kit/-/commit/1a7d274bfa5c16e0591d6571fca74c9829038890))

- Remove str handle type in APIIngress and ProxyPlugin
  ([`071d88c`](https://github.com/touale/FrameX-kit/-/commit/071d88ce2a4ab213ff673f17684a0a21e3ecc417))


## v0.1.4 (2025-07-22)

### Continuous Integration

- Skip release job for merge requests
  ([`8db6b74`](https://github.com/touale/FrameX-kit/-/commit/8db6b74eaff125e9fb080c6a972d50235a14646e))


## v0.1.4-beta.2 (2025-07-22)

### Bug Fixes

- Optimize pre-commit install and add test silent mode
  ([`24dda1e`](https://github.com/touale/FrameX-kit/-/commit/24dda1e2a63c13b2611093b5667fdd2f17497fa5))

### Refactoring

- Enhance BaseAdapter and remove redundant code in Local/Ray Adapters
  ([`43dad3a`](https://github.com/touale/FrameX-kit/-/commit/43dad3a8b4410c016ca900bd5aadb78e9a1ba8c4))

### Testing

- Add pytest-asyncio, asyncio_mode, and plugin tests
  ([`1b2fcc9`](https://github.com/touale/FrameX-kit/-/commit/1b2fcc901f587a9c1e8157a979990e5de6edb14e))


## v0.1.4-beta.1 (2025-07-18)

### Bug Fixes

- Fixed the problem of abnormal parameters of proxy plugin parsing remote API
  ([`51a7083`](https://github.com/touale/FrameX-kit/-/commit/51a708343e04a935a9ca4cd35967e56f3be6f2d1))

### Continuous Integration

- Add pre-commit cache and env var to .gitlab-ci.yml
  ([`2614993`](https://github.com/touale/FrameX-kit/-/commit/2614993f16542e2fd868c851448288c4856111bf))


## v0.1.3 (2025-07-17)

### Bug Fixes

- Ensure reversion starts with 'v' in _setup_sentry
  ([`a0f12c7`](https://github.com/touale/FrameX-kit/-/commit/a0f12c72afb531708a26615fd7a4fecc255bad25))


## v0.1.2 (2025-07-17)

### Features

- Add reversion param to _setup_sentry and run
  ([`588a78e`](https://github.com/touale/FrameX-kit/-/commit/588a78eefcac498a171ba61e08666b9a105ed8db))


## v0.1.1 (2025-07-17)

### Documentation

- Update LICENSE
  ([`b1512b2`](https://github.com/touale/FrameX-kit/-/commit/b1512b28a2af22254532c31128430c9877eb6bf8))

### Features

- Rename to framex-kit, add reversion env, default use_ray false
  ([`ca0c993`](https://github.com/touale/FrameX-kit/-/commit/ca0c993cb74ed97c7ec023090038878b15fbccb9))


## v0.1.0 (2025-07-17)


## v0.1.0-beta.1 (2025-07-17)

### Chores

- Disable Sentry in pytest config
  ([`e9243a0`](https://github.com/touale/FrameX-kit/-/commit/e9243a0e0b56c71e2632e02d9a5e16ec291a2993))

### Features

- Integrate Sentry for error tracking and logging
  ([`5b9847e`](https://github.com/touale/FrameX-kit/-/commit/5b9847ef6665e692f2c74bfca6979489c5f7fc81))

### Refactoring

- Rename and restructure settings for server and proxy
  ([`a39738f`](https://github.com/touale/FrameX-kit/-/commit/a39738fa838574d685f594485830f524cc96572d))

### Update

- Optimize log filtering logic for sentry and ignore prefixes
  ([`5140174`](https://github.com/touale/FrameX-kit/-/commit/5140174b0e279725aed70e9d3c8c0c4836838b25))


## v0.0.2-beta.7 (2025-07-16)

### Features

- Introduce adapter to reduce dependence on `use_ray` config
  ([`487316c`](https://github.com/touale/FrameX-kit/-/commit/487316cbdc4d49cdd03c836c029fcaff1ef74618))


## v0.0.2-beta.6 (2025-07-15)

### Bug Fixes

- Fix ray cannot recognize other routes
  ([`9145a83`](https://github.com/touale/FrameX-kit/-/commit/9145a83715caded218d4a4c4a8bcaeace66f739f))

### Chores

- Disable proxy by default in config
  ([`59763bc`](https://github.com/touale/FrameX-kit/-/commit/59763bc36404733d3d1a72d98db693156a6f886d))

- Simplify proxy config and default values
  ([`8292de3`](https://github.com/touale/FrameX-kit/-/commit/8292de3e313cc52b61c6be8bce4498637f1e4ab1))

### Features

- Add health check, invoker plugin, and test cases
  ([`11fe877`](https://github.com/touale/FrameX-kit/-/commit/11fe877f4f5d79add245d12d01615fda095fc3e8))

### Refactoring

- Refactor call remote func
  ([`dec8fee`](https://github.com/touale/FrameX-kit/-/commit/dec8fee25901af167eb15c22b402061fd44425c8))


## v0.0.2-beta.5 (2025-07-15)

### Code Style

- Add return type annotations for better type checking
  ([`ff32a01`](https://github.com/touale/FrameX-kit/-/commit/ff32a018b2ad50dd7900d876c8b4d6af7c3d84fa))

### Features

- Add multi TOML and YAML support for plugin configs
  ([`7210af1`](https://github.com/touale/FrameX-kit/-/commit/7210af1faa7a8fd82012cc59ab654322dca28ae2))

- Add Ray and non-Ray mode support for server
  ([`ce02945`](https://github.com/touale/FrameX-kit/-/commit/ce029454eaa9393eb51b4b5aeb30c711d8010368))

### Refactoring

- Add logger catch and optimize proxy handling in plugin init
  ([`578b4ee`](https://github.com/touale/FrameX-kit/-/commit/578b4ee5d78000c979b6cd0864772595b6370b18))

### Testing

- Add test coverage and pytest config for better reliability
  ([`5119039`](https://github.com/touale/FrameX-kit/-/commit/5119039e0239d5690fdb7e933eb06b711ec04a1d))


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
