<!--
  - SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
# Installation

The recording server requires an HPB (High Performance Backend for Talk) to be setup. However, it is recommended to setup the recording server in a different machine than the HPB to prevent their load to interfere with each other. Moreover, as the recording server requires some dependencies that are not typically found in server machines, like Firefox, it is recommended to use its own "isolated" machine (either a real machine or a virtual machine). A container would also work, although it might require a special configuration to start the server when the container is started.

In practice the recording server acts just as another Talk client, so it could be located anywhere as long as it can connect to the Nextcloud server and to the HPB, in the later case either directly or through the TURN server. Nevertheless, for simplicity and reliability, it is recommended for the recording server to have direct access to the HPB (so if the HPB is running in an internal network the recording server should be setup in that same internal network as the HPB).

## Hardware requirements

As a quick reference, with the default settings, in an AMD Ryzen 7 3700X 8-Core Processor (so 16 threads, theoretically a maximum usage of 1600% CPU) recording a single call uses 200% CPU (mostly to encode the video). The recording server provides [a benchmark tool](encoders.md) that can be used to check the load with different encoding settings and find out an approximation of the load that will occur when recording a call. Nevertheless in a real recording there is an additional load from the WebRTC connections, the rendering of the browser and so on, but in general the encoding uses the most CPU.

Regarding RAM memory the encoding does not use much, and it should be calculated based on how many simultaneous recordings and therefore browsers are expected. For a single browser 2 GiB should be enough, although it would be recommended to play safe and have more if possible due to the increasing memory requirements of browsers (and also if the calls to be recorded include a lot of participants).

Finally disk size will also depend on the number of simultaneous recordings, as well as the quality and codec used, which directly affect the size of the recording. In general the recorded videos will stay on the recording server only while being recorded and they will be removed as soon as they are uploaded to the Nextcloud server. However, if the upload fails the recorded video will be kept in the recording server until manually removed.

## Installation type

* For customers pre-built packages are available, please refer to [the Nextcloud Talk Recording Server section of the portal](https://portal.nextcloud.com/article/Installation/Installation---Nextcloud-Talk-Recording-Server).
* For some GNU/Linux distributions the installation can be done through packages. Please see the [instructions to build packages](https://github.com/nextcloud/nextcloud-talk-recording/blob/main/docs/building.md).
* A ["manual" installation](https://github.com/nextcloud/nextcloud-talk-recording/blob/main/docs/installation.md#manual-installation) is required in all other cases.

### Prerequisites

Before packages can be installed using the package managers of the distributions, some distributions have additional requirements that need to be fulfilled first.

#### Debian 11

In Debian 11 there is no _geckodriver_ package, which is required to control Firefox from the recording server. Therefore the [PPA from Mozilla](https://launchpad.net/~mozillateam/+archive/ubuntu/ppa) needs to be setup instead before installing the packages. Although `add-apt-repository` is available in Debian 11 the PPA does not provide packages for _bullseye_, so the PPA needs to be manually added to use the packages for _focal_ (Ubuntu 20.04):
```
apt-key adv --keyserver hkps://keyserver.ubuntu.com --recv-keys 0AB215679C571D1C8325275B9BDB3D89CE49EC21
echo 'deb https://ppa.launchpadcontent.net/mozillateam/ppa/ubuntu focal main' > /etc/apt/sources.list.d/mozillateam-ubuntu-ppa.list
```

Besides that the Firefox ESR package from the PPA needs to be configured to take precedence over the one in the Debian repositories:
```
echo '
Package: *
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 1001
' | sudo tee /etc/apt/preferences.d/mozilla-firefox
```

#### Ubuntu 22.04

In Ubuntu 22.04 the normal Firefox package was replaced by a Snap. Unfortunately the Snap package can not be used with the default packages, so the [PPA from Mozilla](https://launchpad.net/~mozillateam/+archive/ubuntu/ppa) needs to be setup instead before installing the packages (`add-apt-repository` is included in the package `software-properties-common`):
```
add-apt-repository ppa:mozillateam/ppa
```

Besides that the Firefox package from the PPA needs to be configured to take precedence over the Snap one with:
```
echo '
Package: *
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 1001
' | sudo tee /etc/apt/preferences.d/mozilla-firefox
```

### Built packages installation

**Note:** This only applies to manually build packages!

In Debian and Ubuntu the built packages can be installed by first changing to the _recording/packaging/build/{DISTRIBUTION-ID}/deb/_ directory and then running:
```
apt install ./*.deb
```

Note that given that the packages do not belong to a repository it is not possible to just install `nextcloud-talk-recording`, as the other deb packages would not be taken into account if not explicitly given.

Besides installing the recording server and its dependencies a _nextcloud-talk-recording_ user is created to run the recording server, and a systemd service is created to start the recording server when the machine boots.

Although it is possible to configure the recording server to use Chromium/Chrome instead of Firefox only Firefox is officially supported, so only Firefox is a dependency of the `nextcloud-talk-recording` package. In order to use Chromium/Chrome it needs to be manually installed.

### Manual installation

Please make sure you cloned the main branch of the [Nextcloud Talk Recording Server repository](https://github.com/nextcloud/nextcloud-talk-recording). Currently the recording server in the main branch is backwards compatible with previous Talk releases, so the latest version from the main branch is expected to be used.

The recording server has the following non-Python dependencies:
- FFmpeg
- Firefox*
- [geckodriver](https://github.com/mozilla/geckodriver/releases) (on a [version compatible with the Firefox version](https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html))
- PulseAudio
- Xvfb

*Chromium/Chrome can be used too, but only Firefox is officially supported and therefore used by default.

Those dependencies must be installed, typically using the package manager of the distribution, in the system running the recording server.

Then, the recording server and all its Python dependencies can be installed using Python pip. Note that the recording server is not available in the Python Package Index (PyPI); you need to manually clone the git repository and then install it from there:
```
git clone https://github.com/nextcloud/nextcloud-talk-recording
python3 -m pip install "file://$(pwd)/nextcloud-talk-recording"
```

The recording server does not need to be run as root (and it should not be run as root). It can be started as a regular user with `nextcloud-talk-recording --config {PATH_TO_THE_CONFIGURATION_FILE)` (or, if the helper script is not available, directly with `python3 -m nextcloud.talk.recording --config {PATH_TO_THE_CONFIGURATION_FILE)`. Nevertheless, please note that the user needs to have a home directory.

You might want to configure a systemd service (or any equivalent service) to automatically start the recording server when the machine boots. The sources for the _.deb_ packages include a service file in _recording/packaging/nextcloud-talk-recording/debian/nextcloud-talk-recording.service_ that could be used as inspiration.

## System setup

Independently of how it was installed the recording server needs to be configured. Depending on the setup additional components like a firewall might also need to be setup or adjusted.

### Recording server configuration

When the recording server is started through its systemd service the configuration will be loaded from `/etc/nextcloud-talk-recording/server.conf`. If `nextcloud-talk-recording` is directly invoked the configuration file to use can be set with `--config XXX`.

The configuration file must be edited to set the Nextcloud servers that are allowed to use the recording server, as well as the credentials for the recording server to use the signaling servers of those Nextcloud servers. Please refer to the sections below for the details.

The temporary directory where the videos are stored while being recorded (and if they fail to be uploaded to the Nextcloud server) is `/tmp/`. That directory is typically a temporary file system stored in RAM, so depending on the available RAM and the number of simultaneous recordings it could affect the system or cause some recordings to suddenly fail due to running out of space. This can be customized in `backend->directory` to use a more suitable directory (for example, a directory under the home directory of the user running the recording server).

As described in a section below it is recommended to set up a TLS termination proxy in front of the recording server. In that case (or if there is any other additional proxy) the proxy or proxies should add, comma-separated, the remote IP address of the requests they receive to the `X-Forwarded-For` header (so if a request passes through several proxies their addresses will be "chained" in the final header reaching the recording server), and in the recording server configuration the IP address (or CIDR networks) of the proxies should be added to `app->trustedproxies`. This will make possible for the recording server to know the "real" remote IP address of a request, rather than just seeing it as coming from the proxy. Note that the trusted proxies should be set only once it has been checked that the remote IP address of the requests is added to the `X-Forwarded-For` header as expected, as otherwise remote clients could spoof the IP address of a request by providing their own `X-Forwarded-For` header.

Besides that the configuration file can be used to customize other things, like the log level, the resolution of the recorded video, the ffmpeg options to use by the encoder or the browser to perform the recording from. The encoder options have [their own documentation page](encoders.md). For the rest please refer to the comments in the configuration file itself.

### Talk configuration

Any Nextcloud server that will use the recording server must be explicitly allowed in the recording server configuration (except if `allowall = true` is set, but that should not be used in production).

Each Nextcloud server needs to be configured in its own section. Any section name can be used, except the reserved names for built-in sections, like `logs`, `backend`, `signaling`... The section names must be added to `backend->backends`.

Each backend section requires at least a `url` and a `secret`. The `url` must be set to the URL of the Nextcloud server, including the webroot, if any. The `secret` is a shared value between the Nextcloud server and the recording server used to authenticate the requests between them. You can use any string, but it is recommended to generate a random key with something like `openssl rand -hex 32`.

Additionally other backend properties can be optionally overriden for each backend (please refer to the comments for the `backend` properties in the configuration file itself). For example, the default video resolution for the backends could be 1920x1080, but videos recorded on a specific backend could have a lower resolution of 960x540.

In the example below comments were stripped for briefness, but it is recommended to keep them in the configuration file:
```
[backend]
...
backends = production-cloud, experiments
...

[production-cloud]
url = https://cloud.mydomain.com
secret = d21e7fba706c5757e25bf0419a18dfaf3bb2c89b9554b5bec138a07d20ad5bb5

[experiments]
url = https://testing.mydomain.com/cloud
secret = 123456
videowidth = 960
videoheight = 540
```

The recording server to be used by a Nextcloud server must be set as well in Talk Administration settings.

Log in the Nextcloud server as an administrator, open the Administration settings, open Talk section and under `Recording backend` set the URL of the recording server. If you are using a self-signed certificate for development purposes you will need to uncheck `Validate SSL certificate`. Besides the URL the same secret set in the recording server must be set in Talk.

Once the URL is set it will be checked if the Nextcloud server can access the recording server, and if everything is correct you should see a valid checkmark with the text `OK: Running version XXX` (where XXX will be the recording server version). Note, however, that currently it is only checked that the recording server can be accessed, but it is not verified if the shared secret matches.

Besides the Talk Administration settings [`upload_max_filesize`](https://www.php.net/manual/en/ini.core.php#ini.upload-max-filesize) and [`post_max_size`](https://www.php.net/manual/en/ini.core.php#ini.post-max-size) may need to be set in the PHP settings, as the maximum size of the videos uploaded to the Nextcloud server by the recording server is limited by those values.

### Signaling server configuration

The recording server must be allowed to access any signaling server used by the configured Nextcloud servers. Setting a signaling server in the recording server configuration does not mean that the recording server will use that signaling server, the signaling server to be used will be provided by the Nextcloud server.

Each signaling server needs to be configured in its own section. Any section name can be used, except the reserved names for built-in sections, like `logs`, `backend`, `signaling`... The section names must be added to `signaling->signalings`.

Each signaling section requires a `url` and an `internalsecret` (unless a common `internalsecret` is set in `signaling->internalsecret`). The `url` must be set to the URL of the signaling server (the same signaling server URL set in Talk Administration settings). The `internalsecret` is a shared value between the signaling server and the recording server used to allow the recording server to access the signaling server. This secret is unrelated to the secret used in the Talk administration settings and shared between the Nextcloud server and the recording server. This value must match the value of `clients->internalsecret` in `/etc/nextcloud-spreed-signaling/server.conf`, which is automatically generated when the signaling server is installed. Nevertheless a custom value can be set, as long as it matches in both the signaling server and the recording server.

In the example below comments were stripped for briefness, but it is recommended to keep them in the configuration file:
```
[signaling]
...
signalings = main-signaling, development
...

[main-signaling]
url = https://hpb.mydomain.com/standalone-signaling
internalsecret = 0005b57434a23bf05a50dab2cddd555b532e76ffa1fb1d9904bfe513b23855bf

[development]
url = https://192.168.57.21:18443
internalsecret = the-internal-secret
```

### TLS termination proxy

The recording server only listens for HTTP requests (the address and port is set in `http->listen` in the configuration file). It is recommended to set up a TLS termination proxy (which can be just a webserver) to add support for HTTPS connections (similar to what is done [for the signaling server](https://github.com/strukturag/nextcloud-spreed-signaling#setup-of-frontend-webserver)).

### Firewall

Independently of the installation method, the recording server requires some dependencies that are not typically found in server machines, like Firefox. It is highly recommended to setup a firewall that prevents any access from the outside to the machine, except those strictly needed by the recording server (and, of course, any additional service that might be needed in the machine, like SSH).

This is specially relevant when the recording server runs in a machine directly connected to the Internet, although it is of less concern when running in an internal network or in a virtual machine with a bridged network, as in those cases the external access would be already limited.

The recording server acts similar to a regular participant in the call, so the firewall needs to allow access to the Nextcloud server and the HPB. Independently of whether the firewall is set in the recording server machine itself or somewhere else these are the connections that need to be allowed from the recording server:
- Nextcloud server using HTTPS (TCP on port 443 of the Nextcloud server).
- HPB using HTTPS (TCP on port 443 of the signaling server).
  The HTTPS connection must be upgradeable to a WebSocket connection.
- HPB using UDP.
  The recording server connects to a port in the range 20000-40000 (or whatever range is configured in Janus, the WebRTC gateway), while the WebRTC gateway may connect on any port of the recording server.

Depending on the setup the recording server might also need to access the STUN server and/or the TURN server, although typically it will not be needed (especially if both the HPB and the recording server can directly access each other):
- STUN server using UDP (port depends on the STUN server configuration).
- TURN server using UDP or TCP (protocol and port depend on the TURN server configuration).

## Testing and troubleshooting

Once the configuration is done it is recommended to record a call to verify that everything works as expected. Recording server log level should be preferably set to `10` (debug) during the verification to have the most information if something fails:
- Start a call as a moderator (only moderators can record a call)
- Start the call recording
- Once the recording has started speak for some seconds, preferably with video enabled
- Stop the recording
- Eventually you will receive a notification that the recording is available
- Check the recording

If something did not work as expected please check below for some possible causes.

If the recording worked as expected note that there could still be a subtle issue. When a recording is started the Selenium Manager will try to find the browser to use for recordings as well as its corresponding Selenium driver. If the Selenium Manager is not able to find them (for example, the ESR version of Firefox from the Mozilla PPA is installed to `/usr/bin/firefox-esr`, which may not be recognized by the Selenium Manager) they may be automatically downloaded by the Selenium Manager (depending on the Selenium version). Despite that it is highly recommended to explicitly install the browser and the Selenium driver instead, preferably from system packages, to have a better control of them and their updates. Therefore, even if the recording worked as expected, the recording server logs should be checked to verify that the Selenium Manager did not download the Selenium driver or the browser but used the ones from the system. This requires the log level to have been set to `10` (debug) so messages from `selenium.webdriver.common.selenium_manager` like `Browser path: /the/path/to/the/browser`, `Driver path: /the/path/to/the/driver` or `Using driver at: /the/path/to/the/driver` are shown. If the Selenium Manager downloaded the Selenium driver and/or the browser (which can be inferred from the paths in those messages) it is recommended to remove them and the path to the system ones should be set in the recording server configuration in `recording->driverPath` and/or `recording->browserPath`.

### The Selenium driver or the browser can not be found

If the Selenium Manager is not available (for example, when running Linux on arm64/aarch64) when a recording is started Selenium will not be able to find the driver and the recording will fail. When the Selenium Manager is not available the path to the Selenium driver must be explicitly set in the recording server configuration in `recording->driverPath`. In that case the path to the browser may also need to be set in `recording->browserPath` if the Selenium driver is not able to find it.

Independently of that, even if the Selenium Manager is available, the recording could also fail if `recording->driverPath` or `recording->browserPath` are set to an invalid value. However, in some Selenium versions setting the paths does not fully override the automated handling of Selenium Manager, so if the paths are set to an invalid value the recording could also work due to Selenium Manager still falling back to downloading the driver or the browser.

Note that in some cases the error `Unable to obtain driver for firefox/chrome` might be thrown even if the driver could be found but not the browser. This could happen, for example, if the browser is not found and Selenium Manager tries to download it, but the format of the URL to download the browser changed and an old Selenium Manager version that has not been adjusted yet is still used (Selenium < 4.28 trying to download Firefox >= 135). It is recommended to check the previous messages to verify the source of the problem.

### No configured signaling secret for `signaling-server-url`

This error will be logged when a recording was started, but the recording server is unable to determine the secret for the signaling server. In this case:
- Verify that the `url` parameter of the signaling configuration is correct
- Check that you're using the same URL scheme (`https://` vs. `wss://`) for the signaling server in your nextcloud instance and the recording server

### The recording is stuck in _Starting_ but never starts nor fails

It is very likely that the recording server could not send the request to mark the recording as started or failed. It is typically one of the cases below:
- The shared secret between the Nextcloud server and the recording server is not the same (`Checksum verification failed` is shown in the logs of the recording server).
- The Nextcloud server is using a self-signed certificate (`certificate verify failed: self signed certificate` is shown in the logs of the recording server). The recording server can be configured to skip verification of the Nextcloud server certificate with the `skipverify` setting in `server.conf`. However, please note that this should be used only for development and a proper certificate should be used in production.

### The recording fails to be started

It is typically one of the cases below:
- The shared secret between the signaling server and the recording server is not the same (`Authentication failed for signaling server` is shown in the logs of the recording server).
- The recording server was not able to connect to the signaling server. Both the logs of the recording server and the signaling server may provide some hints, although the problem is typically related to the firewall.
- The ffmpeg configuration is invalid (`recorder ended unexpectedly` is shown in the logs of the recording server; note that this error could appear in other (strange) cases too, like if ffmpeg crashes). The specific cause can be seen in the messages tagged as `nextcloud.talk.recording.Service.recorder`.

### The recording fails to be uploaded

In this case the explanation is probably found in the Nextcloud server logs. Typically the problem is that the recording size exceeded the values configured for `upload_max_filesize` (`The uploaded file exceeds the upload_max_filesize directive in php.ini` is shown in the logs of the Nextcloud server) or `post_max_size` (`OCA\\Talk\\Controller\\RecordingController::store(): Argument #1 ($owner) must be of type string, null given` is shown in the logs of the Nextcloud server).

If a video could not be uploaded it will be still kept in the recording server under `/{TEMPORARY-DIRECTORY-FOR-RECORDINGS}/{CONVERSATION-TOKEN}`. Note that the default temporary directory for recordings is `/tmp/`, so a recorded video that could not be uploaded may be removed if the machine is restarted. The conversation token is the part after `/call/` in the URL of the conversation.

### The recording was uploaded, but the recording shows that the connection could not be established with other participants

The recording server was not able to connect to Janus, the WebRTC gateway (or, if direct access to Janus is not possible, to the TURN server). Both the logs of the recording server and the HPB (signaling server and Janus) may provide some hints, although the problem is typically related to the firewall.

In some rare cases it can be related as well to the network topology and how the browsers handle WebRTC connections; in those cases changing the browser used to do the recordings may solve the issue.

To diagnose this problem and check which WebRTC candidates are being tried to establish the connection between the recording server and Janus it is possible to access the browser window being used to do a recording using `x11vnc`. It must be launched as the same user that started the X server, `nextcloud-talk-recording`. As that user does not have a login shell it needs to be specified when running `su`: `su - nextcloud-talk-recording --shell /bin/bash --command "x11vnc -rfbport 5900 -display :XXX"`, where `XXX` is the display number used by the X server used for the recording. Each recording has its own X server, so for simplicity it is recommended to test this when there is a single recording; in that case `-display :0` will typically connect to the expected X server. For extra security it would be recommended to tunnel the VNC connection through SSH. Please refer to `x11vnc` help.

Once `x11vnc` is running a VNC viewer can be started in a different machine that has a graphic server and access to the recording server machine to see and interact with the browser window. The browser will be running in kiosk mode, so there will be no address bar nor menu. However, in the case of Firefox, the WebRTC candidates can be checked by first opening a new tab with `Ctrl+T` and then, in the new tab, "opening" the address bar with `Ctrl+L` and then typing `about:webrtc` to load the helper page with the WebRTC connections.

If `x11vnc` is not started with `-forever` or `-shared` the server should be automatically closed once the viewer is closed. Nevertheless, it is highly recommended to verify that it was indeed the case.
