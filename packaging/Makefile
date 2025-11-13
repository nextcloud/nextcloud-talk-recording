#
# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

OS_VERSION ?= $(shell . /etc/os-release 2> /dev/null && echo $$ID$$VERSION_ID)
RELEASE ?= 1
DEBIAN_VERSION ?= $(RELEASE)~$(OS_VERSION)

BUILD_DIR ?= build/$(OS_VERSION)

NEXTCLOUD_TALK_RECORDING_VERSION := $(shell cd ../src && python3 -c "from nextcloud.talk.recording import __version__; print(__version__)")

PULSECTL_VERSION := 22.3.2
PYVIRTUALDISPLAY_VERSION := 3.0
REQUESTS_VERSION := 2.32.0
SELENIUM_VERSION := 4.14.0

CERTIFI_VERSION := 2024.7.4
TRIO_VERSION := 0.21.0
TRIO_WEBSOCKET_VERSION := 0.9.2
URLLIB3_VERSION := 1.26.19

timestamp-from-git = git log -1 --pretty=%ct $(1)

timestamp-from-source-python-package = tar --list --verbose --full-time --gzip --file $(1) | head --lines 1 | sed 's/ \+/ /g' | cut --delimiter " " --fields 4-5 | date --file - +%s

build-source-python-package = python3 -m build --sdist --outdir $(1) $(2)

download-source-python-package = python3 -m pip download --dest $(BUILD_DIR) --no-binary :all: --no-deps "$(1) == $(2)"

extract-source-python-package = cd $(BUILD_DIR) && tar --extract --gzip --file $(1)-$(2).tar.gz

# Since the 60.0.0 release, Setuptools includes a local, vendored copy of
# distutils; this copy does not seem to work with stdeb, so it needs to be
# disabled with "SETUPTOOLS_USE_DISTUTILS=stdlib".
build-deb-package = cd $(BUILD_DIR)/$(1)-$(2)/ && SOURCE_DATE_EPOCH=$(3) SETUPTOOLS_USE_DISTUTILS=stdlib python3 setup.py --command-packages=stdeb.command sdist_dsc --debian-version $(DEBIAN_VERSION) bdist_deb

copy-binary-deb-package = cp $(BUILD_DIR)/$(1)-$(2)/deb_dist/$(3)_$(2)-$(DEBIAN_VERSION)_all.deb $(BUILD_DIR)/deb/

define build-deb-python-package-full
$(call download-source-python-package,$(1),$(2))
$(call extract-source-python-package,$(1),$(2))
$(call build-deb-package,$(1),$(2),$$($(call timestamp-from-source-python-package,../$(1)-$(2).tar.gz)))
$(call copy-binary-deb-package,$(1),$(2),python3-$(3))
endef

build-packages-deb: build-packages-deb-nextcloud-talk-recording build-packages-deb-nextcloud-talk-recording-dependencies

$(BUILD_DIR)/deb:
	mkdir --parents $(BUILD_DIR)/deb

build-packages-deb-nextcloud-talk-recording: $(BUILD_DIR)/deb/nextcloud-talk-recording_$(NEXTCLOUD_TALK_RECORDING_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/nextcloud-talk-recording_$(NEXTCLOUD_TALK_RECORDING_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-source-python-package,$(BUILD_DIR),../)

	# Starting with setup tools 69.3 the name of the generated Python source
	# package is canonicalized based on PEP 625, so it becomes
	# "nextcloud_talk_recording". The name of the Debian binary package is
	# not affected, so it is still matches the project name,
	# "nextcloud-talk-recording".

	$(call extract-source-python-package,nextcloud_talk_recording,$(NEXTCLOUD_TALK_RECORDING_VERSION))

	# Add extra files needed to create Debian packages:
	# - debian/py3dist-overrides: Python dependencies to Debian dependencies for
	#   dh_python3 (also needed in the regenerated Python package, as it is
	#   needed in the Debian package).
	# - MANIFEST.in: the source package is regenerated to include the extra
	#   files needed for the Debian package; MANIFEST.in explicitly adds those
	#   files not included by default in a Python package (so setup.py does not
	#   need to be included in MANIFEST.in, but debian/py3dist-overrides does).
	# - setup.py: legacy setup file needed for stdeb (also needed in the
	#   regenerated Python package, as stdeb is invoked through it to create the
	#   source Debian package).
	# - stdeb.cfg: additional configuration for stdeb (not needed in the
	#   regenerated Python package, as stdeb loads it before changing to the
	#   uncompressed source Python package).
	cp --recursive nextcloud-talk-recording/. $(BUILD_DIR)/nextcloud_talk_recording-$(NEXTCLOUD_TALK_RECORDING_VERSION)/
	cp ../server.conf.in $(BUILD_DIR)/nextcloud_talk_recording-$(NEXTCLOUD_TALK_RECORDING_VERSION)/

	# Build a source Debian package (with the systemd addon for dh) and then,
	# from it, a binary Debian package.
	cd $(BUILD_DIR)/nextcloud_talk_recording-$(NEXTCLOUD_TALK_RECORDING_VERSION)/ && SOURCE_DATE_EPOCH=$$($(call timestamp-from-git,../../../../)) SETUPTOOLS_USE_DISTUTILS=stdlib python3 setup.py --command-packages=stdeb.command sdist_dsc --with-dh-systemd --debian-version $(DEBIAN_VERSION) bdist_deb

	$(call copy-binary-deb-package,nextcloud_talk_recording,$(NEXTCLOUD_TALK_RECORDING_VERSION),nextcloud-talk-recording)

# Builds the Python dependencies that are not included in at least one of the
# Ubuntu supported releases:
# - Debian 11 (bullseye): pulsectl, pyvirtualdisplay >= 2.0, selenium >= 4.11.0
# - Ubuntu 20.04 (focal): pulsectl, pyvirtualdisplay >= 2.0, requests >= 2.25, selenium >= 4.11.0
# - Ubuntu 22.04 (jammy): pulsectl, selenium >= 4.11.0
#
# requests is not an explicit dependency, but required by requests-toolbelt.
# However, requests < 2.25 is not compatible with urllib3 >= 1.26, which is
# required by selenium.
build-packages-deb-nextcloud-talk-recording-dependencies: build-packages-deb-nextcloud-talk-recording-dependencies-$(OS_VERSION)

build-packages-deb-nextcloud-talk-recording-dependencies-debian11: build-packages-deb-pulsectl build-packages-deb-pyvirtualdisplay build-packages-deb-selenium build-packages-deb-selenium-dependencies
build-packages-deb-nextcloud-talk-recording-dependencies-ubuntu20.04: build-packages-deb-pulsectl build-packages-deb-pyvirtualdisplay build-packages-deb-requests build-packages-deb-selenium build-packages-deb-selenium-dependencies
build-packages-deb-nextcloud-talk-recording-dependencies-ubuntu22.04: build-packages-deb-pulsectl build-packages-deb-selenium build-packages-deb-selenium-dependencies

build-packages-deb-pulsectl: $(BUILD_DIR)/deb/python3-pulsectl_$(PULSECTL_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-pulsectl_$(PULSECTL_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-deb-python-package-full,pulsectl,$(PULSECTL_VERSION),pulsectl)

build-packages-deb-pyvirtualdisplay: $(BUILD_DIR)/deb/python3-pyvirtualdisplay_$(PYVIRTUALDISPLAY_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-pyvirtualdisplay_$(PYVIRTUALDISPLAY_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-deb-python-package-full,PyVirtualDisplay,$(PYVIRTUALDISPLAY_VERSION),pyvirtualdisplay)

build-packages-deb-requests: $(BUILD_DIR)/deb/python3-requests_$(REQUESTS_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-requests_$(REQUESTS_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-deb-python-package-full,requests,$(REQUESTS_VERSION),requests)

build-packages-deb-selenium: $(BUILD_DIR)/deb/python3-selenium_$(SELENIUM_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-selenium_$(SELENIUM_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call download-source-python-package,selenium,$(SELENIUM_VERSION))

	$(call extract-source-python-package,selenium,$(SELENIUM_VERSION))

	# The Python dependencies are added automatically to the .deb dependencies,
	# but they do not include the version. The supported distributions provide
	# an incompatible version for some of the dependencies, so
	# "debian/py3dist-overrides" is used to explicitly set the version in the
	# .deb packages and ensure that the right dependency is installed.
	cp --recursive selenium/debian $(BUILD_DIR)/selenium-$(SELENIUM_VERSION)/
	# The package provides its own MANIFEST.in, so the contents need to be
	# appended rather than just copied.
	cat selenium/MANIFEST.in >> $(BUILD_DIR)/selenium-$(SELENIUM_VERSION)/MANIFEST.in

	# The source Python package includes a pre-built Selenium manager, but
	# without execute permissions, so they need to be explicitly set.
	chmod a+x $(BUILD_DIR)/selenium-$(SELENIUM_VERSION)/selenium/webdriver/common/linux/selenium-manager

	$(call build-deb-package,selenium,$(SELENIUM_VERSION),$$($(call timestamp-from-source-python-package,../selenium-$(SELENIUM_VERSION).tar.gz)))

	$(call copy-binary-deb-package,selenium,$(SELENIUM_VERSION),python3-selenium)

# Builds the Python dependencies that are not included in at least one of the
# Ubuntu supported releases:
# - Debian 11 (bullseye): python3-certifi >= 2021.10.8, python3-trio ~= 0.17, python3-trio-websocket ~= 0.9
# - Ubuntu 20.04 (focal): python3-certifi >= 2021.10.8, python3-trio ~= 0.17, python3-trio-websocket ~= 0.9, python3-urllib3 ~= 1.26
# - Ubuntu 22.04 (jammy): python3-certifi >= 2021.10.8, python3-trio-websocket ~= 0.9
build-packages-deb-selenium-dependencies: build-packages-deb-selenium-dependencies-$(OS_VERSION)

build-packages-deb-selenium-dependencies-debian11: build-packages-deb-certifi build-packages-deb-trio build-packages-deb-trio-websocket
build-packages-deb-selenium-dependencies-ubuntu20.04: build-packages-deb-certifi build-packages-deb-trio build-packages-deb-trio-websocket build-packages-deb-urllib
build-packages-deb-selenium-dependencies-ubuntu22.04: build-packages-deb-certifi build-packages-deb-trio-websocket

build-packages-deb-certifi: $(BUILD_DIR)/deb/python3-certifi_$(CERTIFI_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-certifi_$(CERTIFI_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-deb-python-package-full,certifi,$(CERTIFI_VERSION),certifi)

build-packages-deb-trio: $(BUILD_DIR)/deb/python3-trio_$(TRIO_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-trio_$(TRIO_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-deb-python-package-full,trio,$(TRIO_VERSION),trio)

build-packages-deb-trio-websocket: $(BUILD_DIR)/deb/python3-trio-websocket_$(TRIO_WEBSOCKET_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-trio-websocket_$(TRIO_WEBSOCKET_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-deb-python-package-full,trio-websocket,$(TRIO_WEBSOCKET_VERSION),trio-websocket)

build-packages-deb-urllib: $(BUILD_DIR)/deb/python3-urllib3_$(URLLIB3_VERSION)-$(DEBIAN_VERSION)_all.deb
$(BUILD_DIR)/deb/python3-urllib3_$(URLLIB3_VERSION)-$(DEBIAN_VERSION)_all.deb: | $(BUILD_DIR)/deb
	$(call build-deb-python-package-full,urllib3,$(URLLIB3_VERSION),urllib3)
