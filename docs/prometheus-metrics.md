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
| `recording_recordings_current`                    | Gauge     | 0.2.0     | The current number of recordings                                                                       | `backend`                         |
| `recording_recordings_failed_total`               | Counter   | 0.2.0     | The total number of failed recordings, see [notes](#recording_recordings_failed_total)                 | `backend`                         |
| `recording_recordings_uploads_failed_total`       | Counter   | 0.2.0     | The total number of failed uploads, see [notes](#recording_recordings_uploads_failed_total)            | `backend`                         |
| `recording_recordings_total`                      | Counter   | 0.2.0     | The total number of recordings                                                                         | `backend`                         |
| `recording_recordings_duration_seconds`           | Counter   | 0.2.0     | The total duration of all recordings, see [notes](#recording_recordings_duration_seconds)              | `backend`                         |

### Notes

#### `recording_recordings_failed_total`

- Recordings that were successful but that failed to be uploaded are not included. That is, `recording_recordings_failed_total` and `recording_recordings_uploads_failed_total` have no elements in common.

#### `recording_recordings_uploads_failed_total`

- Recordings that were already in the temporary directory when the recording server was started are not included. That is, the value always starts at 0 when the recording server is started, even if in the temporary directory there are recordings that failed to be uploaded in a previous execution.
- An alert can be set whenever the value changes to know that there is a recording file that could not be uploaded and will need manual handling.

#### `recording_recordings_duration_seconds`

- The value is increased once a recording finishes, but it is not updated during the recording itself.
- Failed recordings are not taken into account. However, successful recordings that could not be uploaded are.
- The reported duration might have a difference of a few seconds with the actual duration of the recordings.
