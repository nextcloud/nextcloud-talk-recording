<!--
  - SPDX-FileCopyrightText: 2024 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Prometheus metrics

The recording server exposes various metrics that can be queried by a [Prometheus](https://prometheus.io/) server from the `/metrics` endpoint.

Only clients connecting from an IP that is included in the `allowed_ips` value of the `[stats]` entry in the configuration file are allowed to query the metrics.

## Available metrics

The following metrics are available:

| Metric                                            | Type      | Since     | Description                                                               | Labels                            |
| :------------------------------------------------ | :-------- | --------: | :----------------------------------------------------------------------------------------------------- | :-------------------------------- |
| `recording_recordings_current`                    | Gauge     | 1.0.0     | The current number of recordings                                                                       | `backend`                         |
| `recording_recordings_total`                      | Counter   | 1.0.0     | The total number of recordings                                                                         | `backend`                         |
