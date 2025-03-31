<!--
  - SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Nextcloud Talk Recording Server

[![REUSE status](https://api.reuse.software/badge/github.com/nextcloud/nextcloud-talk-recording)](https://api.reuse.software/info/github.com/nextcloud/nextcloud-talk-recording)

This is the official recording server to be used with Nextcloud Talk (https://github.com/nextcloud/spreed).

It requires the standalone signaling server for Nextcloud Talk (https://github.com/strukturag/nextcloud-spreed-signaling).

The recording server only provides an HTTP API. It is expected that TLS termination will be provided by an additional component, like a reverse proxy. 
