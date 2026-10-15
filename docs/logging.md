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

## Log format

The logs use the standard Python logging system. Therefore they include not only the messages explicitly printed by the recording server, but also the messages printed by the libraries it uses.

Due to that there is only a general format `LOG_LEVEL:LOGGER_NAME:MESSAGE`, but no common format between different messages besides that. Multiline messages will not prepend again the log level and logger name for the second and following lines.

Note that, in general, timestamps are not printed in the logs (unless the unit printing them does it, like `werkzeug`). If needed, timestamps are expected to be added by loading the logs through another tool (like `journalctl`).

## Log example

The following example contains an excerpt of some messages printed when a call is recorded and the debug level is enabled.

```
INFO:nextcloud.talk.recording.Server:Start recording: https://my.nc.com:8443/ 1t13h8x
INFO:werkzeug:192.168.15.16 - - [22/Sep/2004 16:16:23] "POST /api/v1/room/1t13h8x HTTP/1.1" 200 -
DEBUG:pyvirtualdisplay.abstractdisplay:command: ['Xvfb', '-br', '-nolisten', 'tcp', '-screen', '0', '1920x1080x24', '-displayfd', '4']
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x:Starting participant
DEBUG:selenium.webdriver.common.selenium_manager:Selenium Manager binary found at: /usr/lib/python3/dist-packages/selenium/webdriver/common/linux/selenium-manager
DEBUG:selenium.webdriver.common.selenium_manager:Executing process: /usr/lib/python3/dist-packages/selenium/webdriver/common/linux/selenium-manager --browser firefox --debug --output json
[...]
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x:Joining call
DEBUG:selenium.webdriver.remote.remote_connection:POST http://localhost:48108/session/0d42aecb-3194-457e-8156-b74b747e943f/url {'url': 'https://my.nc.com:8443/index.php/call/1t13h8x/recording'}
DEBUG:urllib3.connectionpool:http://localhost:48108 "POST /session/0d42aecb-3194-457e-8156-b74b747e943f/url HTTP/11" 200 0
DEBUG:selenium.webdriver.remote.remote_connection:Remote response: status=200 | data={"value":null} | headers=HTTPHeaderDict({'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-cache', 'content-length': '14', 'date': 'Wed, 22 Sep 2004 16:16:42 GMT'})
DEBUG:selenium.webdriver.remote.remote_connection:Finished Request
[...]
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x.BiDiLogsHelper:16:16:42 D Connecting to wss://my.hpb.com:8443/spreed for 1t13h8x
[...]
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x.BiDiLogsHelper:16:16:42 D Request offer from 7K2557EPN0ln_Kx8Aw6_SChp3f6kyLGrOKwtxb--xEggzc-KR5UfZnSQweZT undefined
[...]
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x.BiDiLogsHelper:16:16:42 D Peer created 7K2557EPN0ln_Kx8Aw6_SChp3f6kyLGrOKwtxb--xEggzc-KR5UfZnSQweZT [object Object]
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x.BiDiLogsHelper:16:16:42 D Changing simulcast stream 7K2557EPN0ln_Kx8Aw6_SChp3f6kyLGrOKwtxb--xEggzc-KR5UfZnSQweZT [object Object] 2 2
[...]
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x.BiDiLogsHelper:16:17:04 D Users left 92WnUoNXIYwDPtW-wtIEwICsM_r61Ryp2aeXV1cZ3EFT01o_vZ_MlkOFR-Ts
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x.BiDiLogsHelper:16:17:04 D Remove disconnected peer 92WnUoNXIYwDPtW-wtIEwICsM_r61Ryp2aeXV1cZ3EFT01o_vZ_MlkOFR-Ts
[...]
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x:Unloading audio module
DEBUG:nextcloud.talk.recording.Service-https://my.nc.com:8443/-1t13h8x:Stopping display
[...]
DEBUG:urllib3.connectionpool:https://my.nc.com:8443 "POST /ocs/v2.php/apps/spreed/api/v1/recording/backend HTTP/11" 200 116
INFO:nextcloud.talk.recording.BackendNotifier:Upload recording /tmp/httpsmynccom/1t13h8x/Recording 2004-09-22 16-16-42.webm to https://my.nc.com:8443/ in 1t13h8x as admin
[...]
DEBUG:urllib3.connectionpool:https://my.nc.com:8443 "POST /ocs/v2.php/apps/spreed/api/v1/recording/1t13h8x/request-upload HTTP/11" 400 103
ERROR:nextcloud.talk.recording.BackendNotifier:Failed to send message to backend, giving up!
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/nextcloud/talk/recording/BackendNotifier.py", line 69, in doRequest
    response.raise_for_status()
  File "/usr/lib/python3/dist-packages/requests/models.py", line 943, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 400 Client Error: Bad request for url: https://my.nc.com:8443/ocs/v2.php/apps/spreed/api/v1/recording/1t13h8x/request-upload
INFO:nextcloud.talk.recording.BackendNotifier:Backend https://my.nc.com:8443/ does not allow chunked recording uploads (public sharing may be disabled), uploading directly
```

`werkzeug` will print with info level all the requests received by the recording server. The recording server will print the main actions that it performs also with info level. Some specific actions are printed only with debug level, as they are typically interesting only when trying to debug an issue. As expected the debug level is rather verbose, as the recording server prints the browser logs, but the underlying libraries also print their own debug messages (for example, including all the requests sent by the recording server). In case of error the stack trace of the exception will be printed with error level.
