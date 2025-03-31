#
# SPDX-FileCopyrightText: 2024 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

# pylint: disable=missing-docstring

import sys
from ipaddress import ip_address, ip_network

import pytest

# pulsectl tries to load the PulseAudio library on initialization, so a fake
# module is set instead to prevent a failure when (indirectly) importing it if
# the library is not installed in the system.
sys.modules['pulsectl'] = {}

# pylint: disable=wrong-import-position
from nextcloud.talk.recording.Server import isAddressInNetworks, TrustedProxiesFix

@pytest.mark.parametrize('address, networks, expectedResult', [
    ('192.168.57.42', [], False),
    ('192.168.57.42', ['192.168.58.0/24'], False),
    ('192.168.57.42', ['192.168.57.0/24'], True),
    ('2001:db8::abc', [], False),
    ('2001:db8::abc', ['2001:db8::b00/120'], False),
    ('2001:db8::abc', ['2001:db8::a00/120'], True),
    ('192.168.57.42', ['192.168.58.0/24', '2001:db8::a00/120', '192.168.57.42', '2001:db8::b00/120'], True),
    ('192.168.59.42', ['192.168.58.0/24', '2001:db8::a00/120', '192.168.57.42', '2001:db8::b00/120'], False),
    ('2001:db8::abc', ['192.168.58.0/24', '2001:db8::a00/120', '192.168.57.42', '2001:db8::b00/120'], True),
    ('2001:db8::cbc', ['192.168.58.0/24', '2001:db8::a00/120', '192.168.57.42', '2001:db8::b00/120'], False),
])
def testIsAddressInNetworks(address, networks, expectedResult):
    address = ip_address(address)
    networks = [ip_network(network) for network in networks]

    assert isAddressInNetworks(address, networks) == expectedResult

class TrustedProxiesFixTest:

    @pytest.fixture
    def fakeConfig(self):
        class FakeConfig:
            def __init__(self):
                self.trustedProxies = []

            def getTrustedProxies(self):
                return self.trustedProxies

        return FakeConfig()

    @pytest.mark.parametrize('remoteAddress, xForwardedFor, trustedProxies, expectedRemoteAddress', [
        # No trusted proxy
        (
            '4.8.15.16',
            '',
            '',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0',
            '',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 10.11.12.13',
            '',
            '4.8.15.16'
        ),
        (
            '4.8.15.16:12345',
            '',
            '',
            '4.8.15.16:12345'
        ),
        (
            '2001:db8:4815::16',
            '',
            '',
            '2001:db8:4815::16'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108',
            '',
            '2001:db8:4815::16'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108, 2001:db8:1011::1213',
            '',
            '2001:db8:4815::16'
        ),
        (
            '[2001:db8:4815::16]:12345',
            '',
            '',
            '[2001:db8:4815::16]:12345'
        ),
        (
            '4.8.15.16',
            '2001:db8:2342::108',
            '',
            '4.8.15.16'
        ),
        (
            '2001:db8:4815::16',
            '23.42.108.0',
            '',
            '2001:db8:4815::16'
        ),
        # Trusted proxy not matching remote address
        (
            '4.8.15.16',
            '',
            '10.11.12.13',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '10.11.12.13',
            '10.11.12.13',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0',
            '10.11.12.13',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 10.11.12.13',
            '10.11.12.13',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 10.11.12.13',
            '4.8.16.0/24, 10.11.12.13',
            '4.8.15.16'
        ),
        (
            '4.8.15.16:12345',
            '',
            '10.11.12.13',
            '4.8.15.16:12345'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:1011::1213',
            '2001:db8:1011::1213',
            '2001:db8:4815::16'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108, 2001:db8:1011::1213',
            '2001:db8:4816::0/48, 2001:db8:1011::1213',
            '2001:db8:4815::16'
        ),
        (
            '[2001:db8:4815::16]:12345',
            '2001:db8:1011::1213',
            '2001:db8:1011::1213',
            '[2001:db8:4815::16]:12345'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 2001:db8:1011::1213',
            '2001:db8:1011::1213',
            '4.8.15.16'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108, 10.11.12.13',
            '10.11.12.13',
            '2001:db8:4815::16'
        ),
        # Trusted proxy matching remote address
        (
            '4.8.15.16',
            '',
            '4.8.15.16',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0',
            '4.8.15.16',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '23.42.108.0',
            '4.8.15.0/24',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '23.42.108.0',
            '10.11.12.13, 4.8.15.0/24',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '23.42.108.0',
            '10.11.12.13, 4.8.15.0/24, 10.11.12.14',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '10.11.12.13, 23.42.108.0',
            '4.8.15.16',
            '23.42.108.0'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108',
            '2001:db8:4815::16',
            '2001:db8:2342::108'
        ),
        (
            '4.8.15.16',
            '2001:db8:2342::108',
            '4.8.15.0/24',
            '2001:db8:2342::108'
        ),
        (
            '2001:db8:4815::16',
            '23.42.108.0',
            '2001:db8:4815::0/112',
            '23.42.108.0'
        ),
        # Trusted proxy matching remote address and forwarded header
        (
            '4.8.15.16',
            '23.42.108.0',
            '4.8.15.16, 23.42.108.0',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 4.8.15.108',
            '4.8.15.0/24',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 10.11.12.13',
            '4.8.15.16, 10.11.12.13',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 10.11.12.13',
            '10.11.12.13, 4.8.15.16',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '10.11.12.13, 23.42.108.0',
            '4.8.15.16, 10.11.12.13',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, 10.11.12.13',
            '4.8.15.16, 10.11.12.0/24',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '10.11.12.15, 23.42.108.0, 10.11.12.14, 10.11.12.13',
            '4.8.15.16, 10.11.12.0/24',
            '23.42.108.0'
        ),
        (
            '4.8.15.16',
            '10.11.12.15, 23.42.108.0, 10.11.12.14, 10.11.12.13',
            '4.8.15.16, 10.11.12.13, 10.11.12.14, 10.11.12.15',
            '23.42.108.0'
        ),
        (
            '4.8.15.16:12345',
            '10.11.12.15:23456, 23.42.108.0:34567, 10.11.12.14:45678, 10.11.12.13:56789',
            '4.8.15.16, 10.11.12.13, 10.11.12.14, 10.11.12.15',
            '23.42.108.0'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108',
            '2001:db8:4815::16, 2001:db8:2342::108',
            '2001:db8:2342::108'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:1011::1215, 2001:db8:2342::108, 2001:db8:1011::1214, 2001:db8:1011::1213',
            '2001:db8:1011::0/48, 2001:db8:4815::16',
            '2001:db8:2342::108'
        ),
        (
            '4.8.15.16',
            '10.11.12.15, 2001:db8:2342::108, 10.11.12.14, 2001:db8:1011::1213',
            '2001:db8:1011::0/48, 4.8.15.16, 10.11.12.14',
            '2001:db8:2342::108'
        ),
        (
            '2001:db8:4815::16',
            '10.11.12.15, 23.42.108.0, 2001:db8:1011::1214, 10.11.12.13',
            '10.11.12.13, 2001:db8::0/32',
            '23.42.108.0'
        ),
        (
            '[2001:db8:4815::16]:12345',
            '10.11.12.15:23456, 23.42.108.0:34567, [2001:db8:1112::1314], [2001:db8:1011::1214]:45678, 10.11.12.13:56789',
            '10.11.12.13, 2001:db8::0/32',
            '23.42.108.0'
        ),
        # Invalid IP in forwarded header
        (
            '4.8.15.16',
            'not-an-ip',
            '4.8.15.0/24',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, not-an-ip',
            '4.8.15.0/24',
            '4.8.15.16'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, not-an-ip, 4.8.15.108',
            '4.8.15.0/24',
            '4.8.15.108'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108, not-an-ip, 2001:db8:4815::108',
            '2001:db8:4815::0/112',
            '2001:db8:4815::108'
        ),
        (
            '4.8.15.16',
            '23.42.108.0, not-an-ip, 2001:db8:4815::108',
            '4.8.15.16, 2001:db8:4815::108',
            '2001:db8:4815::108'
        ),
        (
            '2001:db8:4815::16',
            '2001:db8:2342::108, not-an-ip, 4.8.15.108',
            '2001:db8:4815::16, 4.8.15.108',
            '4.8.15.108'
        ),
        (
            '2001:db8:4815::16',
            ',,not-an-ip,,2001:db8:2342::108,,,     ,    4.8.15.108   ',
            '2001:db8:4815::16, 4.8.15.108',
            '4.8.15.108'
        ),
    ])
    def testGetRemoteAddress(self, fakeConfig, remoteAddress, xForwardedFor, trustedProxies, expectedRemoteAddress):
        environment = {
            'REMOTE_ADDR': remoteAddress,
        }
        if xForwardedFor:
            environment['HTTP_X_FORWARDED_FOR'] = xForwardedFor

        trustedProxies = [ip_network(trustedProxy.strip()) for trustedProxy in trustedProxies.split(',') if trustedProxy]
        fakeConfig.trustedProxies = trustedProxies

        trustedProxiesFix = TrustedProxiesFix(None, fakeConfig)

        assert trustedProxiesFix.getRemoteAddress(environment) == expectedRemoteAddress

    def testGetRemoteAddressWithoutOriginalRemoteAddress(self, fakeConfig):
        trustedProxiesFix = TrustedProxiesFix(None, fakeConfig)

        with pytest.raises(ValueError):
            trustedProxiesFix.getRemoteAddress({})

    def testGetRemoteAddressWithEmptyOriginalRemoteAddress(self, fakeConfig):
        trustedProxiesFix = TrustedProxiesFix(None, fakeConfig)

        with pytest.raises(ValueError):
            trustedProxiesFix.getRemoteAddress({
                'REMOTE_ADDR': '',
            })

    @pytest.mark.parametrize('address, expectedAddress', [
        ('192.168.0.42', '192.168.0.42'),
        ('192.168.0.42:12345', '192.168.0.42'),
        ('::1', '::1'),
        ('2001:db8::0', '2001:db8::0'),
        ('2001:0db8:1234:5678:90ab:cdef:1234:5678', '2001:0db8:1234:5678:90ab:cdef:1234:5678'),
        ('[::1]', '::1'),
        ('[2001:db8::0]', '2001:db8::0'),
        ('[2001:0db8:1234:5678:90ab:cdef:1234:5678]', '2001:0db8:1234:5678:90ab:cdef:1234:5678'),
        ('[::1]:12345', '::1'),
        ('[2001:db8::0]:12345', '2001:db8::0'),
        ('[2001:0db8:1234:5678:90ab:cdef:1234:5678]:12345', '2001:0db8:1234:5678:90ab:cdef:1234:5678'),
        ('not-an-ip', 'not-an-ip'),
        ('not-an-ip:at-all', 'not-an-ip'),
        ('not:an:ip::at-all', 'not:an:ip::at-all'),
        ('[not:an:ip][very][::weird]', 'not:an:ip][very][::weird'),
    ])
    def testGetAddressWithoutPort(self, fakeConfig, address, expectedAddress):
        trustedProxiesFix = TrustedProxiesFix(None, fakeConfig)

        # pylint: disable=protected-access
        assert trustedProxiesFix._getAddressWithoutPort(address) == expectedAddress
