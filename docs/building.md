<!--
  - SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Building

## Prerequisites

The main branch of the [Nextcloud Talk Recording Server repository](https://github.com/nextcloud/nextcloud-talk-recording) is needed to build packages and should be cloned. Currently the recording server in the main branch is backwards compatible with previous Talk releases, so the latest version from the main branch is expected to be used.

## System packages

Distribution packages are supported for the following GNU/Linux distributions:
- Debian 11
- Ubuntu 20.04
- Ubuntu 22.04

They can be built on those distributions by calling `make` in the _recording/packaging_ directory of the git sources. Nevertheless, the Makefile assumes that the build dependencies have been already installed in the system. Therefore it is recommended to run `build.sh` in the _recording/packaging_ directory, which will create Docker containers with the required dependencies and then run `make` inside them. Alternatively the dependencies can be checked under `Installing required build dependencies` in `build.sh` and manually installed in the system. Using `build.sh` the packages can be built for those target distributions on other distributions too.

The built packages can be found in _recording/packaging/build/{DISTRIBUTION-ID}/{PACKAGE-FORMAT}/_ (even if they were built inside the Docker containers using `build.sh`). They include the recording server itself (_nextcloud-talk-recording_) as well as the Python3 dependencies that are not included in the repositories of the distributions. Note that the built dependencies change depending on the distribution type and version.
