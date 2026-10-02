#
# SPDX-FileCopyrightText: 2026 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

# pylint: disable=missing-docstring,invalid-name,unused-argument

import json
import logging
from types import SimpleNamespace

from nextcloud.talk.recording.Participant import Participant


class FakeParticipant(Participant):
    """
    Participant that returns the given speaker events without requiring a real
    browser (only "seleniumHelper.execute" is used to get them).
    """

    # pylint: disable=super-init-not-called
    def __init__(self, events):
        self._parentLogger = logging.getLogger('FakeParticipant')
        self.seleniumHelper = SimpleNamespace(
            execute=lambda script: events,
        )


class ParticipantTest:

    def testGetIntervalsFileName(self):
        assert Participant.getIntervalsFileName('Recording 2026-10-02 17-37-20.webm') == \
            '.Recording 2026-10-02 17-37-20 speaking times.json'

    def testGetIntervalsFileNameWithDirectory(self):
        assert Participant.getIntervalsFileName('/tmp/httpstest1plutonminifoxfr/cmp5dqnk/Recording x.mp4') == \
            '/tmp/httpstest1plutonminifoxfr/cmp5dqnk/.Recording x speaking times.json'

    def testSaveSpeakerEventsToFile(self, tmp_path):
        events = [
            {
                'participantId': 'SESSION1',
                'participantName': 'Alice',
                'participantUserId': 'alice',
                'startTimestamp': 1759419444344,
                'stopTimestamp': 1759419445964,
                'startType': 'speaking',
                'stopType': 'stoppedSpeaking',
            },
            {
                'participantId': 'SESSION2',
                'participantName': '',
                'participantUserId': '',
                'startTimestamp': 1759419452062,
                'stopTimestamp': 1759419452945,
                'startType': 'speaking',
                'stopType': 'stillSpeaking',
            },
        ]

        participant = FakeParticipant(events)

        fileName = str(tmp_path / '.Recording 2026-10-02 17-37-20 speaking times.json')

        assert participant.saveSpeakerEventsToFile(fileName, 1759419440000) is True

        with open(fileName, encoding='utf-8') as f:
            document = json.load(f)

        assert document == {
            'recordingStartTimestamp': 1759419440000,
            'intervals': [
                {
                    'participantId': 'SESSION1',
                    'participantName': 'Alice',
                    'participantUserId': 'alice',
                    'startTimestamp': 1759419444344,
                    'stopTimestamp': 1759419445964,
                    'startType': 'speaking',
                    'stopType': 'stoppedSpeaking',
                    'startTimestampRelative': 4344,
                    'stopTimestampRelative': 5964,
                },
                {
                    'participantId': 'SESSION2',
                    'participantName': '',
                    'participantUserId': '',
                    'startTimestamp': 1759419452062,
                    'stopTimestamp': 1759419452945,
                    'startType': 'speaking',
                    'stopType': 'stillSpeaking',
                    'startTimestampRelative': 12062,
                    'stopTimestampRelative': 12945,
                },
            ],
        }

    def testSaveSpeakerEventsToFileWithoutEvents(self, tmp_path):
        participant = FakeParticipant([])

        fileName = str(tmp_path / '.Recording x speaking times.json')

        assert participant.saveSpeakerEventsToFile(fileName, 1759419440000) is False

        assert not tmp_path.joinpath('.Recording x speaking times.json').exists()
