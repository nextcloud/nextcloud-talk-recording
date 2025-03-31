#
# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

# Disable message for the module but enable it again for the rest of the file.
# pylint: disable=invalid-name
# pylint: enable=invalid-name

"""
Module to provide the command line interface for the recorder.
"""

import argparse
import logging

from nextcloud.talk import recording
from .Config import config
from .Server import app

def main():
    """
    Runs the recorder with the arguments given in the command line.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="path to configuration file", default="server.conf")
    parser.add_argument("-v", "--version", help="show version and quit", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(recording.__version__)

        return

    config.load(args.config)

    logging.basicConfig(level=config.getLogLevel())
    logging.getLogger('werkzeug').setLevel(config.getLogLevel())

    listen = config.getListen()
    host, port = listen.split(':')

    app.run(host, port, threaded=True)

if __name__ == '__main__':
    main()
