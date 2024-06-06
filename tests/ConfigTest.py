#
# @copyright Copyright (c) 2024, Daniel Calviño Sánchez (danxuliu@gmail.com)
#
# @license GNU AGPL version 3 or any later version
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# pylint: disable=missing-docstring

import pytest

from nextcloud.talk.recording.Config import Config

class ConfigTest:

    @pytest.fixture
    def configLoadedFromString(self, monkeypatch):
        # pylint: disable=protected-access
        config = Config()

        # pylint: disable=unused-argument
        def mockRead(fileName):
            # pylint: disable=no-member
            config._configParser.read_string(config.configString)

        monkeypatch.setattr(config._configParser, 'read', mockRead)

        return config

    def testGetBackendValuesWhenNotSet(self, configLoadedFromString):
        configLoadedFromString.configString = """
[backend]
"""
        configLoadedFromString.load('fake-file-name')

        backendUrl = 'https://cloud.unknown.com'
        assert configLoadedFromString.getBackendSecret(backendUrl) is None
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 1024
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 1920
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 1080
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/tmp'

    def testGetBackendValuesWhenSet(self, configLoadedFromString):
        configLoadedFromString.configString = """
[backend]
backends = backend1
skipverify = true
maxmessagesize = 512
videowidth = 960
videoheight = 540
directory = /srv/recording

[backend1]
url = https://cloud.server.com
secret = the-shared-secret
"""
        configLoadedFromString.load('fake-file-name')

        backendUrl = 'https://cloud.unknown.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) is None
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is True
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 512
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 960
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 540
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/srv/recording'

        backendUrl = 'https://cloud.server.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is True
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 512
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 960
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 540
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/srv/recording'

    def testGetBackendValuesWhenSetByBackend(self, configLoadedFromString):
        configLoadedFromString.configString = """
[backend]
backends = backend1
skipverify = false
maxmessagesize = 256
videowidth = 480
videoheight = 270
directory = /tmp/files

[backend1]
url = https://cloud.server.com
secret = the-shared-secret
skipverify = true
maxmessagesize = 512
videowidth = 960
videoheight = 540
directory = /srv/recording
"""
        configLoadedFromString.load('fake-file-name')

        backendUrl = 'https://cloud.unknown.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) is None
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 256
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 480
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 270
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/tmp/files'

        backendUrl = 'https://cloud.server.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is True
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 512
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 960
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 540
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/srv/recording'

    def testGetBackendValuesWhenAllowingAll(self, configLoadedFromString):
        configLoadedFromString.configString = """
[backend]
allowall = true
secret = the-shared-secret-common
backends = backend1

[backend1]
url = https://cloud.server.com
secret = the-shared-secret
skipverify = true
maxmessagesize = 512
videowidth = 960
videoheight = 540
directory = /srv/recording
"""
        configLoadedFromString.load('fake-file-name')

        backendUrl = 'https://cloud.unknown.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret-common'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 1024
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 1920
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 1080
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/tmp'

        backendUrl = 'https://cloud.server.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret-common'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is True
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 512
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 960
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 540
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/srv/recording'

    def testGetBackendValuesWhenExplicitlyDisallowingAll(self, configLoadedFromString):
        configLoadedFromString.configString = """
[backend]
allowall = false
secret = the-shared-secret-common
backends = backend1

[backend1]
url = https://cloud.server.com
secret = the-shared-secret
skipverify = true
maxmessagesize = 512
videowidth = 960
videoheight = 540
directory = /srv/recording
"""
        configLoadedFromString.load('fake-file-name')

        backendUrl = 'https://cloud.unknown.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) is None
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 1024
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 1920
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 1080
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/tmp'

        backendUrl = 'https://cloud.server.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is True
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 512
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 960
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 540
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/srv/recording'

    def testGetBackendValuesWhenExplicitlyDisallowingAllWithoutCommonSecret(self, configLoadedFromString):
        configLoadedFromString.configString = """
[backend]
allowall = false
backends = backend1

[backend1]
url = https://cloud.server.com
secret = the-shared-secret
skipverify = true
maxmessagesize = 512
videowidth = 960
videoheight = 540
directory = /srv/recording
"""
        configLoadedFromString.load('fake-file-name')

        backendUrl = 'https://cloud.unknown.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) is None
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 1024
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 1920
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 1080
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/tmp'

        backendUrl = 'https://cloud.server.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is True
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 512
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 960
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 540
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/srv/recording'

    def testGetBackendValuesWhenSeveralBackends(self, configLoadedFromString):
        configLoadedFromString.configString = """
[backend]
backends = first-backend, second-backend
maxmessagesize = 2048

[first-backend]
url = https://cloud.server1.com
secret = the-shared-secret1
maxmessagesize = 512
videowidth = 960
videoheight = 540

[second-backend]
url = https://cloud.server2.com
secret = the-shared-secret2
directory = /srv/recording
"""
        configLoadedFromString.load('fake-file-name')

        backendUrl = 'https://cloud.unknown.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) is None
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 2048
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 1920
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 1080
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/tmp'

        backendUrl = 'https://cloud.server1.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret1'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 512
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 960
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 540
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/tmp'

        backendUrl = 'https://cloud.server2.com/'
        assert configLoadedFromString.getBackendSecret(backendUrl) == 'the-shared-secret2'
        assert configLoadedFromString.getBackendSkipVerify(backendUrl) is False
        assert configLoadedFromString.getBackendMaximumMessageSize(backendUrl) == 2048
        assert configLoadedFromString.getBackendVideoWidth(backendUrl) == 1920
        assert configLoadedFromString.getBackendVideoHeight(backendUrl) == 1080
        assert configLoadedFromString.getBackendDirectory(backendUrl) == '/srv/recording'

    def testGetSignalingSecretWhenNotSet(self, configLoadedFromString):
        configLoadedFromString.configString = """
[signaling]
"""
        configLoadedFromString.load('fake-file-name')

        signalingUrl = 'https://signaling.unknown.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) is None

    def testGetSignalingSecretWhenSet(self, configLoadedFromString):
        configLoadedFromString.configString = """
[signaling]
internalsecret = the-internal-secret-common
signalings = signaling1

[signaling1]
url = https://signaling.server.com
"""
        configLoadedFromString.load('fake-file-name')

        signalingUrl = 'https://signaling.unknown.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) == 'the-internal-secret-common'

        signalingUrl = 'https://signaling.server.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) == 'the-internal-secret-common'

    def testGetSignalingSecretWhenSetBySignaling(self, configLoadedFromString):
        configLoadedFromString.configString = """
[signaling]
signalings = signaling1

[signaling1]
url = https://signaling.server.com
internalsecret = the-internal-secret
"""
        configLoadedFromString.load('fake-file-name')

        signalingUrl = 'https://signaling.unknown.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) is None

        signalingUrl = 'https://signaling.server.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) == 'the-internal-secret'

    def testGetSignalingSecretWhenSeveralSignalings(self, configLoadedFromString):
        configLoadedFromString.configString = """
[signaling]
internalsecret = the-internal-secret-common
signalings = signaling1, signaling2

[signaling1]
url = https://signaling.server1.com
internalsecret = the-internal-secret1

[signaling2]
url = https://signaling.server2.com
internalsecret = the-internal-secret2
"""
        configLoadedFromString.load('fake-file-name')

        signalingUrl = 'https://signaling.unknown.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) == 'the-internal-secret-common'

        signalingUrl = 'https://signaling.server1.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) == 'the-internal-secret1'

        signalingUrl = 'https://signaling.server2.com'
        assert configLoadedFromString.getSignalingSecret(signalingUrl) == 'the-internal-secret2'
