#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

# Helper script to build the recording backend packages for Nextcloud Talk.
#
# This script creates containers with the supported operating systems, installs
# all the needed dependencies in them and builds the packages for the recording
# backend inside the container. If the container exists already the previous
# container will be reused and this script will simply build the recording
# backend in it. The packages will be created in the
# "build/{DISTRIBUTION-ID}/{PACKAGE-FORMAT}/" directory under "packaging" with
# the same user that owns the "packaging" directory.
#
# Due to that the Docker container will not be stopped nor removed when the
# script exits (except when the container was created but it could not be
# started); that must be explicitly done once the container is no longer needed.
#
#
#
# DOCKER AND PERMISSIONS
#
# To perform its job, this script requires the "docker" command to be available.
#
# The Docker Command Line Interface (the "docker" command) requires special
# permissions to talk to the Docker daemon, and those permissions are typically
# available only to the root user. Please see the Docker documentation to find
# out how to give access to a regular user to the Docker daemon:
# https://docs.docker.com/engine/installation/linux/linux-postinstall/
#
# Note, however, that being able to communicate with the Docker daemon is the
# same as being able to get root privileges for the system. Therefore, you must
# give access to the Docker daemon (and thus run this script as) ONLY to trusted
# and secure users:
# https://docs.docker.com/engine/security/security/#docker-daemon-attack-surface

# Sets the variables that abstract the differences in command names and options
# between operating systems.
#
# Switches between timeout on GNU/Linux and gtimeout on macOS (same for mktemp
# and gmktemp).
function setOperatingSystemAbstractionVariables() {
	case "$OSTYPE" in
		darwin*)
			if [ "$(which gtimeout)" == "" ]; then
				echo "Please install coreutils (brew install coreutils)"
				exit 1
			fi

			MKTEMP=gmktemp
			TIMEOUT=gtimeout
			DOCKER_OPTIONS="-e no_proxy=localhost "
			;;
		linux*)
			MKTEMP=mktemp
			TIMEOUT=timeout
			DOCKER_OPTIONS=" "
			;;
		*)
			echo "Operating system ($OSTYPE) not supported"
			exit 1
			;;
	esac
}

# Removes Docker container if it was created but failed to start.
function cleanUp() {
	# Disable (yes, "+" disables) exiting immediately on errors to ensure that
	# all the cleanup commands are executed (well, no errors should occur during
	# the cleanup anyway, but just in case).
	set +o errexit

	# The name filter must be specified as "^/XXX$" to get an exact match; using
	# just "XXX" would match every name that contained "XXX".
	if [ -n "$(docker ps --all --quiet --filter status=created --filter name="^/$CONTAINER-debian11$")" ]; then
		echo "Removing Docker container $CONTAINER-debian11"
		docker rm --volumes --force $CONTAINER-debian11
	fi
	if [ -n "$(docker ps --all --quiet --filter status=created --filter name="^/$CONTAINER-ubuntu20.04$")" ]; then
		echo "Removing Docker container $CONTAINER-ubuntu20.04"
		docker rm --volumes --force $CONTAINER-ubuntu20.04
	fi
	if [ -n "$(docker ps --all --quiet --filter status=created --filter name="^/$CONTAINER-ubuntu22.04$")" ]; then
		echo "Removing Docker container $CONTAINER-ubuntu22.04"
		docker rm --volumes --force $CONTAINER-ubuntu22.04
	fi
}

# Exit immediately on errors.
set -o errexit

# Execute cleanUp when the script exits, either normally or due to an error.
trap cleanUp EXIT

# Ensure working directory is script directory, as some actions (like mounting
# the volumes in the container) expect that.
cd "$(dirname $0)"

HELP="Usage: $(basename $0) [OPTION]...

Options (all options can be omitted, but when present they must appear in the
following order):
--help prints this help and exits.
--container CONTAINER_NAME the name (prefix) to assign to the containers.
  Defaults to nextcloud-talk-recording-packages-builder."
if [ "$1" = "--help" ]; then
	echo "$HELP"

	exit 0
fi

CONTAINER="nextcloud-talk-recording-packages-builder"
if [ "$1" = "--container" ]; then
	CONTAINER="$2"

	shift 2
fi

if [ -n "$1" ]; then
	echo "Invalid option (or at invalid position): $1

$HELP"

	exit 1
fi

setOperatingSystemAbstractionVariables

# If the containers are not found new ones are prepared. Otherwise the existing
# containers are used.
#
# The name filter must be specified as "^/XXX$" to get an exact match; using
# just "XXX" would match every name that contained "XXX".
if [ -z "$(docker ps --all --quiet --filter name="^/$CONTAINER-debian11$")" ]; then
	echo "Creating Nextcloud Talk recording packages builder container for Debian 11"
	docker run --detach --tty --volume "$(realpath ../)":/nextcloud-talk-recording/ --name=$CONTAINER-debian11 $DOCKER_OPTIONS debian:11 bash

	echo "Installing required build dependencies"
	# "noninteractive" is used to provide default settings instead of asking for
	# them (for example, for tzdata).
	docker exec $CONTAINER-debian11 bash -c "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes make python3 python3-pip python3-venv python3-all debhelper dh-python git dh-exec"
	docker exec $CONTAINER-debian11 bash -c "python3 -m pip install stdeb build 'setuptools >= 61.0'"
fi
if [ -z "$(docker ps --all --quiet --filter name="^/$CONTAINER-ubuntu20.04$")" ]; then
	echo "Creating Nextcloud Talk recording packages builder container for Ubuntu 20.04"
	docker run --detach --tty --volume "$(realpath ../)":/nextcloud-talk-recording/ --name=$CONTAINER-ubuntu20.04 $DOCKER_OPTIONS ubuntu:20.04 bash

	echo "Installing required build dependencies"
	# "noninteractive" is used to provide default settings instead of asking for
	# them (for example, for tzdata).
	docker exec $CONTAINER-ubuntu20.04 bash -c "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes make python3 python3-pip python3-venv python3-all debhelper dh-python git dh-exec"
	docker exec $CONTAINER-ubuntu20.04 bash -c "python3 -m pip install stdeb build 'setuptools >= 61.0'"
fi
if [ -z "$(docker ps --all --quiet --filter name="^/$CONTAINER-ubuntu22.04$")" ]; then
	echo "Creating Nextcloud Talk recording packages builder container for Ubuntu 22.04"
	docker run --detach --tty --volume "$(realpath ../)":/nextcloud-talk-recording/ --name=$CONTAINER-ubuntu22.04 $DOCKER_OPTIONS ubuntu:22.04 bash

	echo "Installing required build dependencies"
	# "noninteractive" is used to provide default settings instead of asking for
	# them (for example, for tzdata).
	# Due to a bug in python3-build in Ubuntu 22.04 python3-virtualenv needs to
	# be used instead of python3-venv:
	# https://bugs.launchpad.net/ubuntu/+source/python-build/+bug/1992108
	# Even with virtualenv there is no proper virtual environment, so the build
	# dependencies specified in pyproject.toml need to be installed system wide.
	# setuptools >= 71.0.0 prefers installed dependencies over vendored ones,
	# but as it requires packaging >= 22 and the installed python3-packaging is
	# 21.3 it can not be used.
	# https://github.com/pypa/setuptools/issues/4483
	docker exec $CONTAINER-ubuntu22.04 bash -c "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes make python3 python3-pip python3-virtualenv python3-build python3-stdeb python3-all debhelper dh-python git dh-exec"
	docker exec $CONTAINER-ubuntu22.04 bash -c "python3 -m pip install 'setuptools >= 69.3, < 71.0.0'"
	# Some packages need to be installed so the unit tests can be run in the
	# packages being built.
	docker exec $CONTAINER-ubuntu22.04 bash -c "apt-get install --assume-yes pulseaudio python3-async-generator python3-trio python3-wsproto"
fi

# Start existing containers if they are stopped.
if [ -n "$(docker ps --all --quiet --filter status=exited --filter name="^/$CONTAINER-debian11$")" ]; then
	echo "Starting Talk recording packages builder container for Debian 11"
	docker start $CONTAINER-debian11
fi
if [ -n "$(docker ps --all --quiet --filter status=exited --filter name="^/$CONTAINER-ubuntu20.04$")" ]; then
	echo "Starting Talk recording packages builder container for Ubuntu 20.04"
	docker start $CONTAINER-ubuntu20.04
fi
if [ -n "$(docker ps --all --quiet --filter status=exited --filter name="^/$CONTAINER-ubuntu22.04$")" ]; then
	echo "Starting Talk recording packages builder container for Ubuntu 22.04"
	docker start $CONTAINER-ubuntu22.04
fi

USER=$(ls -l --numeric-uid-gid --directory . | sed 's/ \+/ /g' | cut --delimiter " " --fields 3)

echo "Building recording backend packages for Debian 11"
docker exec --tty --interactive --user $USER --workdir /nextcloud-talk-recording/packaging $CONTAINER-debian11 make

echo "Building recording backend packages for Ubuntu 20.04"
docker exec --tty --interactive --user $USER --workdir /nextcloud-talk-recording/packaging $CONTAINER-ubuntu20.04 make

echo "Building recording backend packages for Ubuntu 22.04"
docker exec --tty --interactive --user $USER --workdir /nextcloud-talk-recording/packaging $CONTAINER-ubuntu22.04 make
