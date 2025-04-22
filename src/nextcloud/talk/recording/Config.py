#
# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

"""
Module for getting the configuration.

Other modules are expected to import the shared "config" object, which will be
loaded with the configuration file at startup.
"""

import logging
import os

from ipaddress import ip_network

from configparser import ConfigParser

class Config:
    """
    Class for the configuration.

    The configuration values are loaded from a configuration file, but all the
    properties have a default value if the value is not explicitly set in the
    loaded configuration file.

    There is a getter method for each of the configuration values. If the value
    can be overriden by a backend the URL of the backend needs to be given to
    get the value.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

        self._configParser = ConfigParser()

        self._trustedProxies = []
        self._backendIdsByBackendUrl = {}
        self._signalingIdsBySignalingUrl = {}
        self._statsAllowedIps = []

    def load(self, fileName):
        """
        Loads the configuration from the given file name.

        :param fileName: the absolute or relative (to the current working
               directory) path to the configuration file.
        """
        fileName = os.path.abspath(fileName)

        if not os.path.exists(fileName):
            self._logger.warning("Configuration file not found: %s", fileName)
        else:
            self._logger.info("Loading %s", fileName)

        self._configParser.read(fileName)

        self._loadTrustedProxies()
        self._loadBackends()
        self._loadSignalings()
        self._loadStatsAllowedIps()

    def _loadTrustedProxies(self):
        self._trustedProxies = []

        if 'app' not in self._configParser or 'trustedproxies' not in self._configParser['app']:
            return

        trustedProxies = self._configParser.get('app', 'trustedproxies')
        trustedProxies = [trustedProxy.strip() for trustedProxy in trustedProxies.split(',')]

        for trustedProxy in trustedProxies:
            try:
                trustedProxy = ip_network(trustedProxy)

                self._trustedProxies.append(trustedProxy)
            except ValueError as valueError:
                self._logger.error("Invalid trusted proxy: %s", valueError)

    def _loadBackends(self):
        self._backendIdsByBackendUrl = {}

        if 'backend' not in self._configParser or 'backends' not in self._configParser['backend']:
            self._logger.warning("No configured backends")

            return

        backendIds = self._configParser.get('backend', 'backends')
        backendIds = [backendId.strip() for backendId in backendIds.split(',')]

        for backendId in backendIds:
            if 'url' not in self._configParser[backendId]:
                self._logger.error("Missing 'url' property for backend %s", backendId)
                continue

            if 'secret' not in self._configParser[backendId]:
                self._logger.error("Missing 'secret' property for backend %s", backendId)
                continue

            backendUrl = self._configParser[backendId]['url'].rstrip('/')
            self._backendIdsByBackendUrl[backendUrl] = backendId

    def _loadSignalings(self):
        self._signalingIdsBySignalingUrl = {}

        if 'signaling' not in self._configParser:
            self._logger.warning("No configured signalings")

            return

        if 'signalings' not in self._configParser['signaling']:
            if 'internalsecret' not in self._configParser['signaling']:
                self._logger.warning("No configured signalings")

            return

        signalingIds = self._configParser.get('signaling', 'signalings')
        signalingIds = [signalingId.strip() for signalingId in signalingIds.split(',')]

        for signalingId in signalingIds:
            if 'url' not in self._configParser[signalingId]:
                self._logger.error("Missing 'url' property for signaling %s", signalingId)
                continue

            if 'internalsecret' not in self._configParser[signalingId]:
                self._logger.error("Missing 'internalsecret' property for signaling %s", signalingId)
                continue

            signalingUrl = self._configParser[signalingId]['url'].rstrip('/')
            self._signalingIdsBySignalingUrl[signalingUrl] = signalingId

    def _loadStatsAllowedIps(self):
        self._statsAllowedIps = []

        if 'stats' not in self._configParser or 'allowed_ips' not in self._configParser['stats']:
            self._statsAllowedIps.append(ip_network('127.0.0.1'))

            return

        allowedIps = self._configParser.get('stats', 'allowed_ips')
        allowedIps = [allowedIp.strip() for allowedIp in allowedIps.split(',')]

        for allowedIp in allowedIps:
            try:
                allowedIp = ip_network(allowedIp)

                self._statsAllowedIps.append(allowedIp)
            except ValueError as valueError:
                self._logger.error("Invalid allowed IP %s", valueError)

    def getLogLevel(self):
        """
        Returns the log level.

        Defaults to INFO (20).
        """
        return int(self._configParser.get('logs', 'level', fallback=logging.INFO))

    def getListen(self):
        """
        Returns the IP and port to listen on for HTTP requests.

        Defaults to "127.0.0.1:8000".
        """
        return self._configParser.get('http', 'listen', fallback='127.0.0.1:8000')

    def getTrustedProxies(self):
        """
        Returns the list of trusted proxies.

        All proxies are returned as an IPv4Network or IPv6Network, even if they
        are a single IP address.

        Defaults to an empty list.
        """
        return self._trustedProxies

    def getBackendSecret(self, backendUrl):
        """
        Returns the shared secret for requests from and to the backend servers.

        Defaults to None.
        """
        if self._configParser.get('backend', 'allowall', fallback=None) == 'true':
            return self._configParser.get('backend', 'secret')

        backendUrl = backendUrl.rstrip('/')
        if backendUrl in self._backendIdsByBackendUrl:
            backendId = self._backendIdsByBackendUrl[backendUrl]

            return self._configParser.get(backendId, 'secret', fallback=None)

        return None

    def getBackendSkipVerify(self, backendUrl):
        """
        Returns whether the certificate validation of backend endpoints should
        be skipped or not.

        Defaults to False.
        """
        return self._getBackendValue(backendUrl, 'skipverify', False) == 'true'

    def getBackendMaximumMessageSize(self, backendUrl):
        """
        Returns the maximum allowed size in bytes for messages sent by the
        backend.

        Defaults to 1024.
        """
        return int(self._getBackendValue(backendUrl, 'maxmessagesize', 1024))

    def getBackendVideoWidth(self, backendUrl):
        """
        Returns the width for recorded videos.

        Defaults to 1920.
        """
        return int(self._getBackendValue(backendUrl, 'videowidth', 1920))

    def getBackendVideoHeight(self, backendUrl):
        """
        Returns the height for recorded videos.

        Defaults to 1080.
        """
        return int(self._getBackendValue(backendUrl, 'videoheight', 1080))

    def getBackendDirectory(self, backendUrl):
        """
        Returns the temporary directory used to store recordings until uploaded.

        Defaults to False.
        """
        return self._getBackendValue(backendUrl, 'directory', '/tmp')

    def _getBackendValue(self, backendUrl, key, default):
        backendUrl = backendUrl.rstrip('/')
        if backendUrl in self._backendIdsByBackendUrl:
            backendId = self._backendIdsByBackendUrl[backendUrl]

            if self._configParser.get(backendId, key, fallback=None):
                return self._configParser.get(backendId, key)

        return self._configParser.get('backend', key, fallback=default)

    def getSignalingSecret(self, signalingUrl):
        """
        Returns the shared secret for authenticating as an internal client of
        signaling servers.

        Defaults to None.
        """
        signalingUrl = signalingUrl.rstrip('/')
        if signalingUrl in self._signalingIdsBySignalingUrl:
            signalingId = self._signalingIdsBySignalingUrl[signalingUrl]

            if self._configParser.get(signalingId, 'internalsecret', fallback=None):
                return self._configParser.get(signalingId, 'internalsecret')

        return self._configParser.get('signaling', 'internalsecret', fallback=None)

    def getFfmpegCommon(self):
        """
        Returns the ffmpeg executable (name or full path) and the global options
        given to ffmpeg.

        Defaults to ['ffmpeg', '-loglevel', 'level+warning', '-n'].
        """
        return self._configParser.get('ffmpeg', 'common', fallback='ffmpeg -loglevel level+warning -n').split()

    def getFfmpegOutputAudio(self):
        """
        Returns the options given to ffmpeg to encode the audio output.

        Defaults to ['-c:a', 'libopus'].
        """
        return self._configParser.get('ffmpeg', 'outputaudio', fallback='-c:a libopus').split()

    def getFfmpegOutputVideo(self):
        """
        Returns the options given to ffmpeg to encode the video output.

        Defaults to ['-c:v', 'libvpx', '-deadline:v', 'realtime', '-crf', '10', '-b:v', '1M'].
        """
        return self._configParser.get('ffmpeg', 'outputvideo', fallback='-c:v libvpx -deadline:v realtime -crf 10 -b:v 1M').split()

    def getFfmpegExtensionAudio(self):
        """
        Returns the extension of the output file for audio recordings.

        Defaults to ".ogg".
        """
        return self._configParser.get('ffmpeg', 'extensionaudio', fallback='.ogg')

    def getFfmpegExtensionVideo(self):
        """
        Returns the extension of the output file for video recordings.

        Defaults to ".webm".
        """
        return self._configParser.get('ffmpeg', 'extensionvideo', fallback='.webm')

    def getBrowserForRecording(self):
        """
        Returns the browser identifier that will be used for recordings.

        Defaults to "firefox".
        """
        return self._configParser.get('recording', 'browser', fallback='firefox')

    def getDriverPathForRecording(self):
        """
        Returns the path to override the Selenium driver that will be used for
        recordings.

        Defaults to None.
        """
        return self._configParser.get('recording', 'driverPath', fallback=None)

    def getBrowserPathForRecording(self):
        """
        Returns the path to override the browser executable that will be used
        for recordings.

        Defaults to None.
        """
        return self._configParser.get('recording', 'browserPath', fallback=None)

    def getStatsAllowedIps(self):
        """
        Returns the list of IPs allowed to query the stats.

        All IPs are returned as an IPv4Network or IPv6Network, even if they are
        a single IP address.

        Defaults to ['127.0.0.1'].
        """
        return self._statsAllowedIps

config = Config()
