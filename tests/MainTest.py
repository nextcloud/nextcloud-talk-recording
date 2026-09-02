#
# SPDX-FileCopyrightText: 2026 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

# pylint: disable=missing-docstring

import logging
import re
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
        # IPv4-mapped IPv6 addresses, not very useful as typically the raw IPv4
        # address would be used instead, but possible nevertheless
        ('[::ffff:192.168.0.42]:12345',                    '::ffff:192.168.0.42',                     12345),
    ])
    def testListenAddressParsing(self, listen, expectedHost, expectedPort, monkeypatch):
        monkeypatch.setattr(mainModule.config, 'getListen', lambda: listen)

        capturedArgs = {}
        monkeypatch.setattr(mainModule.app, 'run', lambda host, port, **kwargs: capturedArgs.update({'host': host, 'port': port}))

        mainModule.main()

        assert capturedArgs['host'] == expectedHost
        assert capturedArgs['port'] == expectedPort

    @pytest.mark.parametrize('listen, exceptionMessage', [
        # A negative lookahead is used when the exception happens even before
        # the host or port can be checked.
        # Missing port
        ('127.0.0.1', 'No port'),
        ('localhost', 'No port'),
        ('[::1]', 'No port'),
        # Missing host
        (':8000', 'No host'),
        # Depending on the Python version parsing the address is acepted as
        # empty or rejected as invalid, hence the almost useless regexp:
        # https://github.com/python/cpython/issues/103848
        # The Python version can not be checked to test one case or the other as
        # an old version with the previous behaviour might have been patched and
        # behave as a newer version (like Python 3.8 package in Ubuntu 20.04).
        ('[]:8000', r'(?!.*No host|.*No port)|No host'),
        # Missing brackets in IPv6 address
        ('::1', r'(?!.*No host|.*No port)'),
        ('::', r'(?!.*No host|.*No port)'),
    ])
    def testListenInvalidAddress(self, listen, exceptionMessage, monkeypatch):
        monkeypatch.setattr(mainModule.config, 'getListen', lambda: listen)
        monkeypatch.setattr(mainModule.app, 'run', lambda host, port, **kwargs: pytest.fail('The server should not be started'))

        with pytest.raises(ValueError, match=rf'Invalid http->listen value \({re.escape(listen)}\): {exceptionMessage}'):
            mainModule.main()
