#
# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

"""
Module to handle incoming requests.
"""

import atexit
import json
import hashlib
import hmac
import logging
import re
from ipaddress import ip_address
from threading import Lock, Thread

from flask import Flask, jsonify, request
from prometheus_client import Counter, Gauge, make_wsgi_app
from werkzeug.exceptions import BadRequest, Forbidden, NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from nextcloud.talk import recording
from nextcloud.talk.recording import RECORDING_STATUS_AUDIO_AND_VIDEO
from .Config import config
from .Service import Service

# prometheus_client removes "_total" from the counter name, so "_current" needs
# to be added to the gauge to prevent a duplicated name.
metricsRecordingsCurrent = Gauge('recording_recordings_current', 'The current number of recordings', ['backend'])
metricsRecordingsTotal = Counter('recording_recordings_total', 'The total number of recordings', ['backend'])

def isAddressInNetworks(address, networks):
    """
    Returns whether the given IP address belongs to any of the given IP
    networks.

    :param address: the IPv4Address or IPv6Address.
    :param networks: a list of IPv4Network and/or IPv6Network.
    :return: True if the address is in any network of the list, False otherwise.
    """
    for network in networks:
        if address in network:
            return True

    return False

class TrustedProxiesFix:
    """
    Middleware to adjust the remote address in the WSGI environment based on the
    configured trusted proxies.
    """

    # pylint: disable=redefined-outer-name
    def __init__(self, app, config):
        self._app = app
        self._config = config

    def __call__(self, environment, startResponse):
        """
        Modifies REMOTE_ADDR in the WSGI environment based on the
        "Forwarded-For" header before calling the wrapped application.
        """

        try:
            environment['REMOTE_ADDR'] = self.getRemoteAddress(environment)
        except ValueError as valueError:
            logging.getLogger(__name__).error("The remote address of the request could not be got: %s", valueError)

        return self._app(environment, startResponse)

    def getRemoteAddress(self, environment):
        """
        Returns the "real" remote address based on the environment and the
        configured trusted proxies.

        If the original remote address comes from a trusted proxy, the "real"
        remote address is the right-most entry in the "X-Forwarded-For" header
        that does not belong to a trusted proxy (or the last one belonging to a
        trusted proxy if the entry to its left is invalid or there are no more
        entries).

        Only IP addresses are taken into account in the "X-Forwarded-For" header
        (optionally with a port, which will be ignored); hostnames or other ids
        will be treated as an invalid entry.

        It is expected that if several "X-Forwarded-For" headers were included
        in the request the "X-Forwarded-For" entry in the environment includes
        all of them separated by commas and in the same order.

        ValueError is raised if REMOTE_ADDR is not included in the environment,
        or if it is empty; none of that should happen, though.

        :return: the "real" remote address.
        :raises ValueError: if there is no REMOTE_ADDR in the given environment.
        """

        if 'REMOTE_ADDR' not in environment:
            raise ValueError('No REMOTE_ADDR in environment')

        remoteAddress = environment['REMOTE_ADDR']
        remoteAddress = self._getAddressWithoutPort(remoteAddress)
        remoteAddress = ip_address(remoteAddress)

        if 'HTTP_X_FORWARDED_FOR' not in environment:
            return environment['REMOTE_ADDR']

        trustedProxies = self._config.getTrustedProxies()

        if not isAddressInNetworks(remoteAddress, trustedProxies):
            return environment['REMOTE_ADDR']

        forwardedFor = environment['HTTP_X_FORWARDED_FOR']
        forwardedFor = [forwarded.strip() for forwarded in forwardedFor.split(',')]
        forwardedFor.reverse()

        candidateAddress = remoteAddress.compressed

        for forwarded in forwardedFor:
            forwarded = self._getAddressWithoutPort(forwarded)
            try:
                forwarded = ip_address(forwarded)
            except ValueError:
                return candidateAddress

            if not isAddressInNetworks(forwarded, trustedProxies):
                return forwarded.compressed

            candidateAddress = forwarded.compressed

        return candidateAddress

    def _getAddressWithoutPort(self, address):
        """
        Returns the address stripping the trailing port, if any.

        "[]" are also stripped from IPv6 addresses, even if there was no port.

        No validation is performed on the input address, the port is removed
        assuming a valid input. Due to that the returned address is not
        guaranteed to be a valid address.

        :param address: the address as a string.
        :return: the address without port.
        """
        colons = address.count(':')
        if colons > 1:
            # IPv6, might or might not have brackets and/or port, but we are
            # only interested in the content between brackets, if any.
            addressInBracketsMatch = re.match('\\[(.*)\\]', address)
            if addressInBracketsMatch and len(addressInBracketsMatch.groups()) == 1:
                return addressInBracketsMatch.group(1)
        elif colons == 1:
            # IPv4 with trailing ":port"
            return address[:address.find(':')]

        return address

class ProtectedMetrics:
    """
    Middleware to serve the metrics only if the remote address is allowed to
    access them.
    """

    # pylint: disable=redefined-outer-name
    def __init__(self, config):
        self.config = config
        self.metrics = make_wsgi_app()

    def __call__(self, environment, startResponse):
        """
        Returns the metrics if the remote address is allowed to access them, or
        an error 403 if not.
        """

        remoteAddress = environment['REMOTE_ADDR']
        remoteAddress = ip_address(remoteAddress)

        if not isAddressInNetworks(remoteAddress, config.getStatsAllowedIps()):
            startResponse('403 FORBIDDEN', [])

            return []

        return self.metrics(environment, startResponse)

app = Flask(__name__)
app.wsgi_app = TrustedProxiesFix(app.wsgi_app, config)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': TrustedProxiesFix(ProtectedMetrics(config), config)
})

services = {}
servicesStopping = {}
servicesLock = Lock()

@app.route("/api/v1/welcome", methods=["GET"])
def welcome():
    """
    Handles welcome requests.
    """
    return jsonify(version=recording.__version__)

@app.route("/api/v1/room/<token>", methods=["POST"])
def handleBackendRequest(token):
    """
    Handles backend requests.
    """
    backend, data = _validateRequest()

    if 'type' not in data:
        raise BadRequest()

    if data['type'] == 'start':
        return startRecording(backend, token, data)

    if data['type'] == 'stop':
        return stopRecording(backend, token, data)

    raise BadRequest()

def _validateRequest():
    """
    Validates the current request.

    :return: the backend that sent the request and the object representation of
             the body.
    """

    if 'Talk-Recording-Backend' not in request.headers:
        app.logger.warning("Missing Talk-Recording-Backend header")
        raise Forbidden()

    backend = request.headers['Talk-Recording-Backend']

    secret = config.getBackendSecret(backend)
    if not secret:
        app.logger.warning("No secret configured for backend %s", backend)
        raise Forbidden()

    if 'Talk-Recording-Random' not in request.headers:
        app.logger.warning("Missing Talk-Recording-Random header")
        raise Forbidden()

    random = request.headers['Talk-Recording-Random']

    if 'Talk-Recording-Checksum' not in request.headers:
        app.logger.warning("Missing Talk-Recording-Checksum header")
        raise Forbidden()

    checksum = request.headers['Talk-Recording-Checksum']

    maximumMessageSize = config.getBackendMaximumMessageSize(backend)

    if not request.content_length or request.content_length > maximumMessageSize:
        app.logger.warning("Message size above limit: %d %d", request.content_length, maximumMessageSize)
        raise BadRequest()

    body = request.get_data()

    expectedChecksum = _calculateChecksum(secret, random, body)
    if not hmac.compare_digest(checksum, expectedChecksum):
        app.logger.warning("Checksum verification failed: %s %s", checksum, expectedChecksum)
        raise Forbidden()

    return backend, json.loads(body)

def _calculateChecksum(secret, random, body):
    secret = secret.encode()
    message = random.encode() + body

    hmacValue = hmac.new(secret, message, hashlib.sha256)

    return hmacValue.hexdigest()

def startRecording(backend, token, data):
    """
    Starts the recording in the given backend and room (identified by its
    token).

    The data must provide the id of the user that will own the recording once
    uploaded. The data must also provide the type and id of the actor that
    started the recording, which will be passed back to the backend when sending
    the request to confirm that the recording was started.

    By default the recording will be a video recording, but an audio recording
    can be started instead if provided in the data.

    Expected data format:
    data = {
      'type' = 'start',
      'start' = {
        'owner' = #STRING#,
        'actor' = {
          'type' = #STRING#,
          'id' = #STRING#,
        },
        'status' = #INTEGER#, // Optional
      }
    }

    :param backend: the backend that send the request.
    :param token: the token of the room to start the recording in.
    :param data: the data used to start the recording.
    """
    serviceId = f'{backend}-{token}'

    if 'start' not in data:
        raise BadRequest()

    if 'owner' not in data['start']:
        raise BadRequest()

    if 'actor' not in data['start']:
        raise BadRequest()

    if 'type' not in data['start']['actor']:
        raise BadRequest()

    if 'id' not in data['start']['actor']:
        raise BadRequest()

    status = RECORDING_STATUS_AUDIO_AND_VIDEO
    if 'status' in data['start']:
        status = data['start']['status']

    owner = data['start']['owner']

    actorType = data['start']['actor']['type']
    actorId = data['start']['actor']['id']

    service = None
    with servicesLock:
        if serviceId in services:
            app.logger.warning("Trying to start recording again: %s %s", backend, token)
            return {}

        service = Service(backend, token, status, owner)

        services[serviceId] = service

    app.logger.info("Start recording: %s %s", backend, token)

    serviceStartThread = Thread(target=_startRecordingService, args=[service, actorType, actorId], daemon=True)
    serviceStartThread.start()

    return {}

def _startRecordingService(service, actorType, actorId):
    """
    Helper function to start a recording service.

    The recording service will be removed from the list of services if it can
    not be started.

    :param service: the Service to start.
    """
    serviceId = f'{service.backend}-{service.token}'

    metricsRecordingsCurrent.labels(service.backend).inc()
    metricsRecordingsTotal.labels(service.backend).inc()

    try:
        service.start(actorType, actorId)
    except Exception as exception:
        with servicesLock:
            if serviceId not in services:
                # Service was already stopped, exception should have been caused
                # by stopping the helpers even before the recorder started.
                app.logger.info("Recording stopped before starting: %s %s", service.backend, service.token, exc_info=exception)

                return

            app.logger.exception("Failed to start recording: %s %s", service.backend, service.token)

            services.pop(serviceId)

            metricsRecordingsCurrent.labels(service.backend).dec()


def stopRecording(backend, token, data):
    """
    Stops the recording in the given backend and room (identified by its token).

    If the data provides the type and id of the actor that stopped the recording
    this will be passed back to the backend when sending the request to confirm
    that the recording was stopped.

    Expected data format:
    data = {
      'type' = 'stop',
      'stop' = {
        'actor' = { // Optional
          'type' = #STRING#,
          'id' = #STRING#,
        },
      }
    }

    :param backend: the backend that send the request.
    :param token: the token of the room to stop the recording in.
    :param data: the data used to stop the recording.
    """
    serviceId = f'{backend}-{token}'

    if 'stop' not in data:
        raise BadRequest()

    actorType = None
    actorId = None
    if 'actor' in data['stop'] and 'type' in data['stop']['actor'] and 'id' in data['stop']['actor']:
        actorType = data['stop']['actor']['type']
        actorId = data['stop']['actor']['id']

    service = None
    with servicesLock:
        if serviceId not in services and serviceId in servicesStopping:
            app.logger.info("Trying to stop recording again: %s %s", backend, token)
            return {}

        if serviceId not in services:
            app.logger.warning("Trying to stop unknown recording: %s %s", backend, token)
            raise NotFound()

        service = services[serviceId]

        services.pop(serviceId)

        servicesStopping[serviceId] = service

    app.logger.info("Stop recording: %s %s", backend, token)

    serviceStopThread = Thread(target=_stopRecordingService, args=[service, actorType, actorId], daemon=True)
    serviceStopThread.start()

    return {}

def _stopRecordingService(service, actorType, actorId):
    """
    Helper function to stop a recording service.

    The recording service will be removed from the list of services being
    stopped once it is fully stopped.

    :param service: the Service to stop.
    """
    serviceId = f'{service.backend}-{service.token}'

    try:
        service.stop(actorType, actorId)
    except Exception:
        app.logger.exception("Failed to stop recording: %s %s", service.backend, service.token)
    finally:
        with servicesLock:
            if serviceId not in servicesStopping:
                # This should never happen.
                app.logger.error("Recording stopped when not in the list of stopping services: %s %s", service.backend, service.token)
            else:
                servicesStopping.pop(serviceId)

            metricsRecordingsCurrent.labels(service.backend).dec()

# Despite this handler it seems that in some cases the geckodriver could have
# been killed already when it is executed, which unfortunately prevents a proper
# cleanup of the temporary files opened by the browser.
def _stopServicesOnExit():
    with servicesLock:
        serviceIds = list(services.keys())
        for serviceId in serviceIds:
            service = services.pop(serviceId)
            del service

# Services should be explicitly deleted before exiting, as if they are
# implicitly deleted while exiting the Selenium driver may not cleanly quit.
atexit.register(_stopServicesOnExit)
