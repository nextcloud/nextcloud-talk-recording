<!--
  - SPDX-FileCopyrightText: 2026 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Logging

Log messages are printed to the standard error stream (_stderr_). Therefore, when the recording server is run through systemd its logs can be seen in the systemd journal with `journalctl --unit nextcloud-talk-recording`.

## Log levels

The amount of detail in the logs can be defined by setting `logs->level` in [the configuration file](installation.md#recording-server-configuration) to a specific numeric value. Lower values provide more details, while higher values provide less. Each level includes its own messages plus the messages of all the levels above it:

- 50: critical level, only the most severe errors (like a crashing application)
- 40: error level, problems that prevent performing some action (like a failed request to the Nextcloud server)
- 30: warning level, something unexpected happened (like missing required parameters in a request received from the Nextcloud server)
- 20: info level, general information of what is being done by the recording server (like starting or stopping a recording)
- 10: debug level, detailed information of what is being done by the recording server (like the console messages in the browser doing the recording)

By default, if no level is explicitly set, info level will be used.

In info level and higher the recording server logs do not include any personal data about the participants in the call.

However, when debug level is set, which is meant to be used only for development and/or to diagnose problems, the logs will contain also the logs from the browser used to do the recording. Therefore, in this case the recording server logs can potentially include details like user ids, participant names, or even chat messages (although the amount of details will also depend on whether the debug mode is also enabled in the Nextcloud server itself or not).
