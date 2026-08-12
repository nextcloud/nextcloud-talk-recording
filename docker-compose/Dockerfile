FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get --assume-yes update
RUN apt-get --assume-yes upgrade

# Common dependencies
RUN apt-get --assume-yes install software-properties-common

# nextcloud-talk-recording dependencies
RUN apt-get --assume-yes install ffmpeg pulseaudio python3-pip python3-venv xvfb

# firefox
# RUN apt-get --assume-yes install firefox firefox-geckodriver (replaced by the below)
RUN apt-get --assume-yes install firefox

# chromium
# The phd/chromium repository for Ubuntu is used because since Ubuntu 20.04
# Chromium is provided as a snap package, and the equivalent PPA has been
# discontinued.
RUN echo "deb https://freeshell.de/phd/chromium/focal /" > /etc/apt/sources.list.d/phd-chromium.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 869689FE09306074
RUN apt-get update
RUN apt-get --assume-yes install chromium

COPY ./docker-compose/wrap_chromium_binary /opt/bin/wrap_chromium_binary
RUN chmod u+x /opt/bin/wrap_chromium_binary
RUN /opt/bin/wrap_chromium_binary

# nextcloud-talk-recording config
RUN useradd --create-home recording
COPY server.conf.in /etc/nextcloud-talk-recording/server.conf
RUN sed --in-place 's/#listen =.*/listen = 0.0.0.0:8000/' /etc/nextcloud-talk-recording/server.conf

# Cleanup
RUN apt-get clean && rm --recursive --force /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy recording server sources
RUN mkdir --parents /tmp/recording
COPY src /tmp/recording/
COPY pyproject.toml /tmp/recording/
RUN chown -R recording:recording /tmp/recording

# Switch user
WORKDIR "/home/recording/"
USER "recording"

# create python virtual env
ENV VIRTUAL_ENV=/home/recording/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install python requirements and the recording server
RUN python3 -m pip install --upgrade requests
RUN python3 -m pip install file:///tmp/recording/

# cleanup
RUN rm --recursive --force /tmp/recording

# start the recording server
CMD ["python3", "-m", "nextcloud.talk.recording", "--config", "/etc/nextcloud-talk-recording/server.conf"]
