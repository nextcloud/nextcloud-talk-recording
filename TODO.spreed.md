## Speaker Intervals Upload Support

This recording server now uploads an additional JSON sidecar file with speaker
activity intervals when available.

The sidecar file contains an object like:

```json
{
  "recordingStartTimestamp": 1725286200000,
  "intervals": [
    {
      "participantId": "SESSION_ID",
      "participantName": "Alice",
      "startTimestamp": 1725286205123,
      "stopTimestamp": 1725286212789,
      "startTimestampRelative": 5123,
      "stopTimestampRelative": 12789
    }
  ]
}
```

The recording server changes assume the spreed backend will accept this extra
file in both upload modes below.

## Required Spreed Changes

### 1. Chunked upload `store` endpoint

File to inspect in spreed:
- Controller handling `POST /ocs/v2.php/apps/spreed/api/v1/recording/{token}/store`
- Services that move the uploaded file from the temporary upload share to its
  final destination

Required change:
- Accept an optional JSON field `intervalsFileName`
- If present, locate that uploaded file in the same upload share used for the
  recording video
- Move/store it together with the recording file
- Keep the current behaviour unchanged when `intervalsFileName` is absent

Suggested payload shape:

```json
{
  "owner": "user-id",
  "fileName": "Recording 2026-09-02 14-30-00.mp4",
  "intervalsFileName": "Recording 2026-09-02 14-30-00.json"
}
```

Expected behaviour:
- The video file and JSON sidecar end up in the same destination folder
- The JSON file should use the provided `intervalsFileName` as-is
- Post-processing and moderator notifications must continue to work even if the
  JSON sidecar is not present

### 2. Direct upload fallback `store` endpoint

Required change:
- Accept an optional multipart file field named `intervalsFile`
- Store it next to the main uploaded `file`
- Keep the current direct upload behaviour unchanged when `intervalsFile` is
  absent

Expected multipart form fields:
- `owner`
- `file`
- `intervalsFile` (optional)

### 3. Validation

Suggested validation:
- Ensure `intervalsFileName` ends with `.json` for the chunked upload path
- Ensure `intervalsFile` content type or extension is JSON-like in the direct
  upload path
- Treat the sidecar file as optional; rejection should happen only when the
  client explicitly sent it and it is invalid

### 4. Storage semantics

Recommended behaviour:
- Store the JSON sidecar next to the recording file with the same basename
- Example:
  - `Recording 2026-09-02 14-30-00.mp4`
  - `Recording 2026-09-02 14-30-00.json`

### 5. Tests to add in spreed

- Chunked upload path stores both `fileName` and `intervalsFileName`
- Chunked upload path still works without `intervalsFileName`
- Direct upload path stores both `file` and `intervalsFile`
- Direct upload path still works without `intervalsFile`
- Invalid optional intervals payload is rejected cleanly
- Notifications/post-processing remain unchanged when sidecar is present

### 6. Optional follow-up

If spreed should expose the intervals later in the UI or APIs:
- decide whether the JSON sidecar is only stored as a file artifact
- or parsed and indexed in the database for later querying

The recording server currently treats it only as an uploaded companion file.
