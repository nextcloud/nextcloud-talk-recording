<!--
  - SPDX-FileCopyrightText: 2025 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Changelog
All notable changes to this project will be documented in this file.

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
