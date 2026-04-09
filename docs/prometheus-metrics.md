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
| `recording_recordings_duration_seconds_total`     | Counter   | 0.2.0     | The total duration of all recordings, see [notes](#recording_recordings_duration_seconds_total)        | `backend`                         |

### Notes

#### Integer values

Although conceptually some metrics should be integers instead of floats (like `recording_recordings_current` or `recording_recordings_total`) unfortunately that is not possible, at least for the time being. The official Python client for Prometheus (which is the library used to expose the metrics) [treats all values strictly as floats](https://github.com/prometheus/client_python/blob/7b9959209492c06968785c66bc6ea2316d156f91/prometheus_client/exposition.py#L292-L296). The reason was that [the original Prometheus format states that values must be floats](https://redirect.github.com/prometheus/client_python/issues/465#issuecomment-529941965) (or, rather, [_a float represented as required by Go's ParseFloat() function_](https://github.com/prometheus/docs/blob/cbea98f4e962b77ead05aaf7172b2a47a0f15107/docs/instrumenting/exposition_formats.md#comments-help-text-and-type-information)), which [always includes the decimal point](https://go.dev/ref/spec#Floating-point_literals) (it does not parse an integer as a float).

Nevertheless, nowadays the original Prometheus format is legacy and the newer OpenMetrics format (which was derived from Prometheus) is the official one. The OpenMetrics format explicitly supports either float or integer values, but it also states that [ingestors may only support floats](https://github.com/prometheus/OpenMetrics/blob/6c847344ff49fa6241a35e8b4f65bf098da5a161/specification/OpenMetrics.txt#L240-L242). Therefore it might be just a matter of time until integers are also provided by the Python library, although it seems that it has not happened yet, probably to ensure backwards compatibility with older ingestors.

#### `_created`

The `_created` metrics are not explicitly added by the recording server. They are a [Prometheus / OpenMetrics convention](https://prometheus.io/docs/specs/om/open_metrics_spec/#counter) and added by default by the official Python client for Prometheus.

[Since version 0.14 of of the client](https://github.com/prometheus/client_python/releases/tag/v0.14.0) the `_created` metrics [can be disabled with the environment variable `PROMETHEUS_DISABLE_CREATED_SERIES=True`](https://prometheus.github.io/client_python/instrumenting/#disabling-_created-metrics). If a systemd service is used to manage the recording server the environment variable could be set by calling `systemctl edit nextcloud-talk-recording` and adding:
```
[Service]
Environment="PROMETHEUS_DISABLE_CREATED_SERIES=True"
```

Unfortunately the system packages for the client (`python3-prometheus-client`) provided by Ubuntu 20.04, Ubuntu 22.04 and Debian 11 are older than version 0.14, so the `_created` metrics can not be disabled when using them.

#### `recording_recordings_failed_total`

- Recordings that were successful but that failed to be uploaded are not included. That is, `recording_recordings_failed_total` and `recording_recordings_uploads_failed_total` have no elements in common.

#### `recording_recordings_uploads_failed_total`

- Recordings that were already in the temporary directory when the recording server was started are not included. That is, the value always starts at 0 when the recording server is started, even if in the temporary directory there are recordings that failed to be uploaded in a previous execution.
- An alert can be set whenever the value changes to know that there is a recording file that could not be uploaded and will need manual handling.

#### `recording_recordings_duration_seconds_total`

- The value is increased once a recording finishes, but it is not updated during the recording itself.
- Failed recordings are not taken into account. However, successful recordings that could not be uploaded are.
- The reported duration might have a difference of a few seconds with the actual duration of the recordings.
