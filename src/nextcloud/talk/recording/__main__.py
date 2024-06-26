#
# @copyright Copyright (c) 2023, Daniel Calviño Sánchez (danxuliu@gmail.com)
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
