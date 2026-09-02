<!--
  - SPDX-FileCopyrightText: 2025 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Changelog
All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-09-02
### Added

- Implement chunked uploads of recording files [#95](https://github.com/nextcloud/nextcloud-talk-recording/pull/95)
- Add support for building packages for Debian 12, Debian 13 and Ubuntu 24.04 [#102](https://github.com/nextcloud/nextcloud-talk-recording/pull/102)

### Fixed

- Treat `https://` and `wss://` as equivalent in signaling URL [#85](https://github.com/nextcloud/nextcloud-talk-recording/pull/85)
- Show error message when URLs are duplicated in the configuration [#86](https://github.com/nextcloud/nextcloud-talk-recording/pull/86)
- Correctly parse IPv6 addresses in `http->listen` [#81](https://github.com/nextcloud/nextcloud-talk-recording/pull/81)
- Fix cropped browser window when using Chromium [#107](https://github.com/nextcloud/nextcloud-talk-recording/pull/107)
- Fix missing characters in recorded video due to missing fonts in built packages [#108](https://github.com/nextcloud/nextcloud-talk-recording/pull/108)

### Changed

- Use backend ID as backend label in Prometheus metrics [#106](https://github.com/nextcloud/nextcloud-talk-recording/pull/106)
- Use home directory under _/var/lib_ instead of _/home/nextcloud-talk-recording_ in built packages [#99](https://github.com/nextcloud/nextcloud-talk-recording/pull/99)

## [0.2.1] - 2025-11-13
### Fixed

- Fix minimum required version of Selenium [#67](https://github.com/nextcloud/nextcloud-talk-recording/pull/67)
- Fix issues in packages of Selenium and requests introduced in 0.2.0 [#66](https://github.com/nextcloud/nextcloud-talk-recording/pull/66) [#69](https://github.com/nextcloud/nextcloud-talk-recording/pull/69)

## [0.2.0] - 2025-10-13
### Added

- Add trusted proxies configuration to log the "real" IP of clients [#26](https://github.com/nextcloud/nextcloud-talk-recording/pull/26)
- Add Prometheus stats [#27](https://github.com/nextcloud/nextcloud-talk-recording/pull/27) [#56](https://github.com/nextcloud/nextcloud-talk-recording/pull/56)
- Add support for specifying Selenium driver and browser executable [#33](https://github.com/nextcloud/nextcloud-talk-recording/pull/33)
- Add configuration options for ffmpeg inputs [#57](https://github.com/nextcloud/nextcloud-talk-recording/pull/57)
- Add argument to overwrite the benchmark output file [#58](https://github.com/nextcloud/nextcloud-talk-recording/pull/58)
- Show frames dropped by ffplay in benchmark summary [#59](https://github.com/nextcloud/nextcloud-talk-recording/pull/59)

### Fixed

- Remove unneeded, and sometimes problematic, visit to main Nextcloud server page [#28](https://github.com/nextcloud/nextcloud-talk-recording/pull/28)
- Fix error printed to the log when running benchmark in extra verbose mode [#61](https://github.com/nextcloud/nextcloud-talk-recording/pull/61)

## [0.1.0] - 2023-10-23

- Initial version
