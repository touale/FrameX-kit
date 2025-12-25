# CHANGELOG

<!-- version list -->

## v0.2.6 (2025-12-25)

### Chores

- Change default docs password to admin
  ([`24aca13`](https://github.com/touale/FrameX-kit/commit/24aca13f858f21c3a85268a8e59e6a3e40467b75))

### Documentation

- Improve authentication documentation formatting and structure
  ([`dda03a7`](https://github.com/touale/FrameX-kit/commit/dda03a7251bd303f70c0d22e9fa79090de837a77))

### Features

- Enhance API docs with runtime status and plugin versions
  ([`1435d3d`](https://github.com/touale/FrameX-kit/commit/1435d3dec90ae55d6f189f003bc799613c4bee89))

### Refactoring

- Improve CLI config and auth settings management
  ([`96b0cab`](https://github.com/touale/FrameX-kit/commit/96b0cabe6593dba233cc3d6971b87a3fe05b7f76))

### Testing

- Improve parameter handling and add comprehensive CLI tests
  ([`f37ff4c`](https://github.com/touale/FrameX-kit/commit/f37ff4cdb042b0a90dedfb7c4e076d7ba3ca2cdd))

- Restructure auth configuration into unified rules format
  ([`ebaa96f`](https://github.com/touale/FrameX-kit/commit/ebaa96f0f510a276ed1c3eed6f27a9ef27984149))


## v0.2.5 (2025-12-24)

### Bug Fixes

- Fix proxy function serialization and error handling
  ([`7288013`](https://github.com/touale/FrameX-kit/commit/7288013342ce81cc39dce4dbb07c668997f59723))

- Handle negative num_cpus value in ray initialization
  ([`db98eee`](https://github.com/touale/FrameX-kit/commit/db98eee7b0264019821cf993080de72eb2ff385c))

### Chores

- Upgrade ray from 2.47.1 to 2.53.0
  ([`b4e2bd0`](https://github.com/touale/FrameX-kit/commit/b4e2bd034d8b2b00bb7a0c505ebcf389e84828e6))

- **deps**: Update dependency ruff to v0.14.10
  ([`359d731`](https://github.com/touale/FrameX-kit/commit/359d7312f2c5593918a274b398270906dbcfaf39))

- **deps**: Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.10
  ([`537c431`](https://github.com/touale/FrameX-kit/commit/537c4311df69e313bbf40c352608e25c11ca2fa4))

### Documentation

- Add authentication, concurrency and proxy function documentation
  ([`82ecef1`](https://github.com/touale/FrameX-kit/commit/82ecef173c02f529c48ca4e7fec98f7462648c8c))

### Features

- Add docs authentication with basic auth
  ([`00530f8`](https://github.com/touale/FrameX-kit/commit/00530f8da9a2e21db89dca1bfe3d9740b25185b9))

- Add proxy function registration placeholder
  ([`8a1b9db`](https://github.com/touale/FrameX-kit/commit/8a1b9db3f094b662ced812d6792487dd3bbaef41))

- Add proxy function support
  ([`8b9e474`](https://github.com/touale/FrameX-kit/commit/8b9e47450819ca4fb075afb6b11b0bc04069f67a))

- Enhance proxy function auth with random key generation
  ([`ffa9438`](https://github.com/touale/FrameX-kit/commit/ffa9438f3ebfb5ee2563a2b9f57e352f24603467))

- Enhance proxy function registration and auth
  ([`f169727`](https://github.com/touale/FrameX-kit/commit/f16972742989225a94b75eff570ba6d3363a2936))

### Refactoring

- Simplify proxy decorator and remove proxy_only param
  ([`081026b`](https://github.com/touale/FrameX-kit/commit/081026b89cb0e1cc0b537f6c3b03aa6acb55a4fc))

### Testing

- Add comprehensive application tests and improve auth logging
  ([`fb2b5d5`](https://github.com/touale/FrameX-kit/commit/fb2b5d5da1456939cc6921cf8d940f0e1cfa9d71))

- Add pytest-order and enhance proxy tests
  ([`425984c`](https://github.com/touale/FrameX-kit/commit/425984cdf9e53ccae19a962266ec7597752a3abe))

- Enhance cache encode/decode and proxy exception handling
  ([`9488998`](https://github.com/touale/FrameX-kit/commit/9488998f1b876317f25af62c6a3ee16d2df488db))


## v0.2.4 (2025-10-27)

### Features

- Add configurable excluded log paths support
  ([`73eb430`](https://github.com/touale/FrameX-kit/-/commit/73eb430385d0bf981d4a77cb45caa44bba25f19e))


## v0.2.3 (2025-10-24)

### Documentation

- Add teacher project prediction plugin status
  ([`b81ff66`](https://github.com/touale/FrameX-kit/-/commit/b81ff66374b9cbe725e7a0a992c26c111de409f6))

### Features

- Optimize plugin API logging with batch output
  ([`7cc3a2d`](https://github.com/touale/FrameX-kit/-/commit/7cc3a2d69bcd9d794a6b5066eae34c023c8f3907))

### Testing

- Add exception handling tests for test mode and plugin calls
  ([`75d1a3f`](https://github.com/touale/FrameX-kit/-/commit/75d1a3f0b87e41be2a7974cb1a7e96f8f243162d))


## v0.2.2 (2025-10-21)

### Documentation

- Remove plugin data directory config references
  ([`6466648`](https://github.com/touale/FrameX-kit/-/commit/64666480bba779f9a07b818cbc1b5b83ea7a9066))

### Features

- Remove plugin data directory support
  ([`bcd5dd1`](https://github.com/touale/FrameX-kit/-/commit/bcd5dd1941a0a38abb8e36b55c9f88599b4f01e8))


## v0.2.1 (2025-10-21)

### Chores

- **deps**: Lock file maintenance
  ([`95d70ad`](https://github.com/touale/FrameX-kit/-/commit/95d70ad2f483270d4b40d076459e001ebddd725c))

### Documentation

- Update development.md
  ([`e21019a`](https://github.com/touale/FrameX-kit/-/commit/e21019a12df4e108d934e3c1c1d51c2030db4c57))

- Update precision medicine and international matching status to complete
  ([`28704d1`](https://github.com/touale/FrameX-kit/-/commit/28704d1946441234adf36de4c358bd1d051281c9))

- Update remote_calls.md
  ([`b1a4805`](https://github.com/touale/FrameX-kit/-/commit/b1a48051ca8d6e02289a9dd4c126cd0131fd0172))

- Update technology prediction report status to complete
  ([`4507a66`](https://github.com/touale/FrameX-kit/-/commit/4507a66a75a1abf39e19005def8da32b1d0ccfe2))

- Updateadvanced_test.md
  ([`b267a9f`](https://github.com/touale/FrameX-kit/-/commit/b267a9fc9a9fa5db078698d45d225eee6d172c7f))

### Features

- Enhance CLI with configurable server options and plugin loading
  ([`2de69e0`](https://github.com/touale/FrameX-kit/-/commit/2de69e0dd86e7b043c59f9241c2e40b0d664c0ad))


## v0.2.0 (2025-10-20)

### Update

- Stable version release, improve error message in plugin import failure
  ([`8dc340e`](https://github.com/touale/FrameX-kit/-/commit/8dc340e3e796d648ccba3048df1aa65d629413d0))


## v0.1.21 (2025-10-20)

### Documentation

- Update project status and links
  ([`0049415`](https://github.com/touale/FrameX-kit/-/commit/004941590e3060e44959b399717db44925bdfc45))

### Features

- Add configurable server host, port and CPU count
  ([`bcaacfa`](https://github.com/touale/FrameX-kit/-/commit/bcaacfa784b288a94300e393bf0c1155a9e0370d))


## v0.1.20 (2025-10-16)

### Bug Fixes

- Update API registration and HTTP client timeout handling
  ([`4efe031`](https://github.com/touale/FrameX-kit/-/commit/4efe031a3a798481c815ae42a931e84094874612))

### Chores

- Add line length ignore to ruff config
  ([`619323f`](https://github.com/touale/FrameX-kit/-/commit/619323f2acf1ba568fb180b45860db052c15147b))

### Documentation

- Update plugin config and contribution status
  ([`a2c8efa`](https://github.com/touale/FrameX-kit/-/commit/a2c8efa422d10e12409bde6b3045a7c6ba6adacc))

### Features

- Remove YAML support from configuration handling
  ([`bf281d3`](https://github.com/touale/FrameX-kit/-/commit/bf281d3c503caf3b388d44f1f464ad65aa4846b6))


## v0.1.19 (2025-10-15)

### Features

- Adjust the remote func of LocalAdapter to execute in thread
  ([`1b6163e`](https://github.com/touale/FrameX-kit/-/commit/1b6163e14764f0b22e17f1578c7887f50d51b206))


## v0.1.18 (2025-10-15)

### Bug Fixes

- Update plugin model field definitions
  ([`15fb2d0`](https://github.com/touale/FrameX-kit/-/commit/15fb2d01f5817dbb17b4eafa40c69a307b6101fc))


## v0.1.17 (2025-10-14)

### Documentation

- Update personnel matching and peer search status
  ([`d21a4e0`](https://github.com/touale/FrameX-kit/-/commit/d21a4e023921849aedd6a2df24963846ddf26826))

### Features

- Enhance remote decorator with method support
  ([`43e2ce3`](https://github.com/touale/FrameX-kit/-/commit/43e2ce33fb7a6529eaabd6d98b1dff8a6e926251))


## v0.1.16 (2025-09-29)

### Chores

- **deps**: Lock file maintenance
  ([`fec070c`](https://github.com/touale/FrameX-kit/-/commit/fec070cad0856e2048a58e02adaf01f3081e23a6))

- **deps**: Lock file maintenance
  ([`5b39979`](https://github.com/touale/FrameX-kit/-/commit/5b399799b7f847696e00c87d56a56ada87dc6acb))

### Documentation

- Remove task decomposition from contribution table
  ([`92d05d5`](https://github.com/touale/FrameX-kit/-/commit/92d05d58a2223c08b48de107f5037d2fb8a932dd))

- Update find_policy status in contribution table
  ([`2a13de2`](https://github.com/touale/FrameX-kit/-/commit/2a13de2d661950a3d3b60acdfa1943d9cca47762))

- Update plugin addresses and status in contribution table
  ([`e4c1303`](https://github.com/touale/FrameX-kit/-/commit/e4c1303d8996f1a624c4269af80cd74277f366f8))

### Features

- Add callback support for API params
  ([`2955952`](https://github.com/touale/FrameX-kit/-/commit/29559527720cabb5410f0ce4e7bc20daef7d6fcc))

### Testing

- Enhance VCR recording with response filtering
  ([#3](https://github.com/touale/FrameX-kit/-/merge_requests/3),
  [`cbb47f9`](https://github.com/touale/FrameX-kit/-/commit/cbb47f9ecbf803c764dbe10d8c8fa72cde7a82cb))


## v0.1.15 (2025-09-16)

### Chores

- Add release extras to lock file
  ([`fbd5db7`](https://github.com/touale/FrameX-kit/-/commit/fbd5db78b780377102955f84f328e82ba6d85770))

### Features

- Add CLI interface with click
  ([`1cd4bab`](https://github.com/touale/FrameX-kit/-/commit/1cd4babf67239a2c71dbc78ba79329a6591bc300))

### Performance Improvements

- Simplify plugin configuration handling
  ([`4110dcb`](https://github.com/touale/FrameX-kit/-/commit/4110dcb5268e3db39b1416111c30281ff250e446))


## v0.1.14 (2025-09-15)

### Bug Fixes

- Simplify parameter processing in proxy plugin
  ([`65f9265`](https://github.com/touale/FrameX-kit/-/commit/65f9265ab7805e53d176b533b06fbb9130aeb701))

### Chores

- **deps**: Lock file maintenance
  ([`5f34c36`](https://github.com/touale/FrameX-kit/-/commit/5f34c36132e06599739f1c4d1914d83e7a3fa434))


## v0.1.13 (2025-09-15)

### Chores

- Update gitignore, config schedule and plugin config
  ([`67d735f`](https://github.com/touale/FrameX-kit/-/commit/67d735fbf89eb68e99f91db44e32023bd4e0e4cd))

### Refactoring

- Improve plugin config validation
  ([`30067b6`](https://github.com/touale/FrameX-kit/-/commit/30067b62988806a5fdea373d59e52507d0a02529))


## v0.1.12 (2025-09-12)

### Performance Improvements

- Simplify plugin config retrieval
  ([`63ef0a1`](https://github.com/touale/FrameX-kit/-/commit/63ef0a16a016b7eb482c3e38f298be30eb51ef6a))


## v0.1.11 (2025-09-12)

### Chores

- Add refactor to patch tags in semantic release config
  ([`7160105`](https://github.com/touale/FrameX-kit/-/commit/7160105a3fb23955e33a93394f3f11626e1cb1e2))

- **deps**: Update dependency ruff to v0.13.0
  ([`872deff`](https://github.com/touale/FrameX-kit/-/commit/872deffad1c62225ebb9988cf588ef5a7d14198a))

### Continuous Integration

- Add ray to ignored dependencies in config
  ([`3e0260e`](https://github.com/touale/FrameX-kit/-/commit/3e0260e86eda1c40437a3fbde57fac2a6a1c4871))

### Refactoring

- Optimize plugin config loading
  ([`1590bda`](https://github.com/touale/FrameX-kit/-/commit/1590bda81b69165d4b4714e52daf8d6091716f03))


## v0.1.10 (2025-09-12)

### Continuous Integration

- Extend renovate to run on master and main branches
  ([`31f430d`](https://github.com/touale/FrameX-kit/-/commit/31f430d23b3885fe510e1bc5f7eea6a8c670aed8))

### Documentation

- Add contribution md
  ([`ef58fbd`](https://github.com/touale/FrameX-kit/-/commit/ef58fbdf9e756ab65440bf6c05cf59b66aa49028))

- Add end-to-end examples and improve plugin documentation
  ([`163c164`](https://github.com/touale/FrameX-kit/-/commit/163c1648b78e7df6f6cafe5daadf91a723654193))

- Add last changed info to documentation book
  ([`c70b13d`](https://github.com/touale/FrameX-kit/-/commit/c70b13db962c1c5f4d64bddcca171c739dd943db))

- Fix code indentation and update contribution guide
  ([`115ba2a`](https://github.com/touale/FrameX-kit/-/commit/115ba2a706192de00a8cd7543f887753920f2154))

- Format img
  ([`7e81d60`](https://github.com/touale/FrameX-kit/-/commit/7e81d60f8c8a28286121baa8c7073fb02d0cab84))

- Update development guide and add FAQ section
  ([`4b9b2bf`](https://github.com/touale/FrameX-kit/-/commit/4b9b2bf6c5cb5d2f9a50c1c75928a31b5808adee))

- Update documentation structure and content
  ([`ffbe735`](https://github.com/touale/FrameX-kit/-/commit/ffbe735e20bb1b7b7658f660b63103211abef251))

- Update README and add overview documentation
  ([`5222e34`](https://github.com/touale/FrameX-kit/-/commit/5222e3442bf302f3a4fab66e1b7077239b8c3372))

### Features

- Add renovate config and update plugin documentation
  ([`f7cd12f`](https://github.com/touale/FrameX-kit/-/commit/f7cd12ff74d7796bbfe013b8fb02214a3bb324d1))


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
