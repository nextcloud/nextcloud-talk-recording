#
# SPDX-FileCopyrightText: 2026 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

# pylint: disable=missing-docstring

import logging
import sys

import pytest

# pulsectl tries to load the PulseAudio library on initialization, so a fake
# module is set instead to prevent a failure when (indirectly) importing it if
# the library is not installed in the system.
sys.modules['pulsectl'] = {}

# pylint: disable=wrong-import-position
import nextcloud.talk.recording.__main__ as mainModule

class MainTest:

    @pytest.fixture(autouse=True)
    def mockMain(self, monkeypatch):
        monkeypatch.setattr(mainModule.config, 'load', lambda fileName: None)
        monkeypatch.setattr(mainModule.config, 'getLogLevel', lambda: logging.WARNING)
        monkeypatch.setattr(sys, 'argv', ['nextcloud-talk-recording'])

    @pytest.mark.parametrize('listen, expectedHost, expectedPort', [
        # IPv4
        ('127.0.0.1:8000',     '127.0.0.1',     8000),
        ('0.0.0.0:8000',       '0.0.0.0',       8000),
        ('4.8.15.16:8000',     '4.8.15.16',     8000),
        ('192.168.0.42:12345', '192.168.0.42', 12345),
        # IPv6
        ('[::1]:8000',                                     '::1',                                      8000),
        ('[::]:8000',                                      '::',                                       8000),
        ('[2001:db8:4815::16]:8000',                       '2001:db8:4815::16',                        8000),
        ('[2001:db8::abc]:12345',                          '2001:db8::abc',                           12345),
        ('[2001:0db8:1234:5678:90ab:cdef:1234:5678]:8000', '2001:0db8:1234:5678:90ab:cdef:1234:5678',  8000),
    ])
    def testListenAddressParsing(self, listen, expectedHost, expectedPort, monkeypatch):
        monkeypatch.setattr(mainModule.config, 'getListen', lambda: listen)

        capturedArgs = {}
        monkeypatch.setattr(mainModule.app, 'run', lambda host, port, **kwargs: capturedArgs.update({'host': host, 'port': port}))

        mainModule.main()

        assert capturedArgs['host'] == expectedHost
        assert capturedArgs['port'] == expectedPort
