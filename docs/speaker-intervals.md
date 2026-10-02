<!--
  - SPDX-FileCopyrightText: 2026 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Speaker Intervals

Alongside each video recording the recording server stores a JSON sidecar file
with the time intervals in which each participant was speaking, and uploads it
together with the recording to the Nextcloud server.

The sidecar file is a hidden file (its name starts with a dot) located next to
the recording file and derived from its name. For example, the recording

    Recording 2026-10-02 17-37-20.webm

gets the sidecar

    .Recording 2026-10-02 17-37-20 speaking times.json

Note that storing it next to the recording requires the corresponding support
in the Talk backend; otherwise the file is uploaded but not moved to its final
location (it stays in the temporary upload share until it expires).

## File format

```json
{
  "recordingStartTimestamp": 1759419440000,
  "intervals": [
    {
      "participantId": "SESSION_ID",
      "participantName": "Alice",
      "participantUserId": "alice",
      "startTimestamp": 1759419444344,
      "stopTimestamp": 1759419445964,
      "startType": "speaking",
      "stopType": "stoppedSpeaking",
      "startTimestampRelative": 4344,
      "stopTimestampRelative": 5964
    }
  ]
}
```

* `participantId` is the session ID of the participant. `participantName` and
  `participantUserId` are resolved when the interval is started, so renames
  during a call are not reflected in already started intervals.
* Timestamps are milliseconds of wall clock time (`Date.now()` in the browser
  of the recording server, same host as the recording server itself).
* `startTimestampRelative` and `stopTimestampRelative` are milliseconds
  relative to the recording start, so they can be used to seek into the
  recording file (a small, roughly constant offset between the recording start
  and the actual first frame of the file may apply).

## Interval start and stop reasons

The fields `startType` and `stopType` indicate how each bound of an interval
was detected, which is useful to interpret the data:

* `speaking` / `stoppedSpeaking`: the participant signaled a change of its
  speaking state through its WebRTC data channel (relayed by the MCU). This is
  the normal, most accurate case. Note that these updates may be lost while a
  participant's connection is being renegotiated (for example, when muting
  without video or when joining again); in that case the interval may be
  closed or re-opened a few seconds late.
* `participantFlagsChanged`: the speaking flag of a SIP participant changed
  (SIP participants have no data channel, so their state is signalled by the
  signaling server).
* `peerEnded`: the connection with the participant was closed, so any interval
  still open is closed at that point. This means the participant left the
  call, but it can also mean that the participant became inaudible (for
  example, muting the microphone without video reconnects the participant with
  different flags). Therefore an interval stopped by `peerEnded` is accurate
  as "end of audible speech" but does not necessarily mean that the
  participant left the call.
* `stillSpeaking`: the recording was stopped while the participant was
  speaking, so the interval is closed at the moment the recording was stopped.
