#
# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

# Disable message for the module but enable it again for the rest of the file.
# pylint: disable=invalid-name
# pylint: enable=invalid-name

"""
Module to initialize the package.
"""

__version__ = '0.2.1'

RECORDING_STATUS_AUDIO_AND_VIDEO = 1
RECORDING_STATUS_AUDIO_ONLY = 2

USER_AGENT = f'Nextcloud-Talk-Recording/{__version__}'
