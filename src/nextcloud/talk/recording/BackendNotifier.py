#
# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

"""
Module to send requests to the Nextcloud server.
"""

import hashlib
import hmac
import json
import logging
import os
from secrets import token_urlsafe
from urllib.parse import quote

from requests import Request, Session
from requests.exceptions import HTTPError
from requests_toolbelt import MultipartEncoder

from nextcloud.talk import recording
from .Config import config

logger = logging.getLogger(__name__)

def getRandomAndChecksum(backend, data):
    """
    Returns a random string and the checksum of the given data with that random.

    :param backend: the backend to send the data to.
    :param data: the data, as bytes.
    """
    secret = config.getBackendSecret(backend).encode()
    random = token_urlsafe(64)
    hmacValue = hmac.new(secret, random.encode() + data, hashlib.sha256)

    return random, hmacValue.hexdigest()

def _isClientError(exception):
    """
    Returns whether the given exception is a client error (4xx) response.

    :param exception: the exception to check.
    :returns: True if the exception is an HTTP client error, False otherwise.
    """
    if not isinstance(exception, HTTPError) or exception.response is None:
        return False

    return 400 <= exception.response.status_code < 500

def doRequest(backend, request, retries=3):
    """
    Send the request to the backend.

    SSL verification will be skipped if configured.

    :param backend: the backend to send the request to.
    :param request: the request to send.
    :param retries: the number of times to retry in case of failure.
    :returns: the response of the request.
    """
    backendSkipVerify = config.getBackendSkipVerify(backend)

    try:
        session = Session()
        preparedRequest = session.prepare_request(request)
        response = session.send(preparedRequest, verify=not backendSkipVerify)
        response.raise_for_status()

        return response
    except Exception as exception:
        # Client errors (4xx) are deterministic, so retrying them would just fail
        # again and is therefore pointless.
        if retries > 1 and not _isClientError(exception):
            logger.exception("Failed to send message to backend, %d retries left!", retries)
            return doRequest(backend, request, retries - 1)

        logger.exception("Failed to send message to backend, giving up!")
        raise

def backendRequest(backend, data):
    """
    Sends the data to the backend on the endpoint to receive notifications from
    the recording server.

    The data is automatically wrapped in a request for the appropriate URL and
    with the needed headers.

    :param backend: the backend to send the data to.
    :param data: the data to send.
    """
    url = backend.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/backend'

    data = json.dumps(data).encode()

    random, checksum = getRandomAndChecksum(backend, data)

    headers = {
        'Content-Type': 'application/json',
        'OCS-ApiRequest': 'true',
        'Talk-Recording-Random': random,
        'Talk-Recording-Checksum': checksum,
        'User-Agent': recording.USER_AGENT,
    }

    request = Request('POST', url, headers, data=data)

    doRequest(backend, request)

def started(backend, token, status, actorType, actorId):
    """
    Notifies the backend that the recording was started.

    :param backend: the backend of the conversation.
    :param token: the token of the conversation.
    :param actorType: the actor type of the Talk participant that started the
           recording.
    :param actorId: the actor id of the Talk participant that started the
           recording.
    """

    backendRequest(backend, {
        'type': 'started',
        'started': {
            'token': token,
            'status': status,
            'actor': {
                'type': actorType,
                'id': actorId,
            },
        },
    })

def stopped(backend, token, actorType, actorId):
    """
    Notifies the backend that the recording was stopped.

    :param backend: the backend of the conversation.
    :param token: the token of the conversation.
    :param actorType: the actor type of the Talk participant that stopped the
           recording.
    :param actorId: the actor id of the Talk participant that stopped the
           recording.
    """

    data = {
        'type': 'stopped',
        'stopped': {
            'token': token,
        },
    }

    if actorType is not None and actorId is not None:
        data['stopped']['actor'] = {
            'type': actorType,
            'id': actorId,
        }

    backendRequest(backend, data)

def failed(backend, token):
    """
    Notifies the backend that the recording failed.

    :param backend: the backend of the conversation.
    :param token: the token of the conversation.
    """

    data = {
        'type': 'failed',
        'failed': {
            'token': token,
        },
    }

    backendRequest(backend, data)

def uploadRecording(backend, token, fileName, owner):
    """
    Upload the recording specified by fileName.

    The name of the uploaded file is the basename of the original file.

    If the backend supports it the recording is uploaded in chunks through a
    temporary upload share, which allows uploading recordings larger than the
    limits enforced on a regular request. Otherwise the recording is uploaded
    directly in a single request as a fallback for older backends.

    :param backend: the backend to upload the file to.
    :param token: the token of the conversation that was recorded.
    :param fileName: the recording file name.
    :param owner: the owner of the uploaded file.
    """

    logger.info("Upload recording %s to %s in %s as %s", fileName, backend, token, owner)

    uploadShare = requestUpload(backend, token, fileName, owner)

    if uploadShare is None:
        # The backend does not support chunked uploads or public link sharing is disabled
        # Fall back to directly uploading the recording in a single request.
        uploadRecordingDirectly(backend, token, fileName, owner)

        return

    uploadRecordingInChunks(backend, uploadShare, fileName)

    # Once the recording was uploaded and assembled the store endpoint is called
    # with its file name to trigger the post-processing and the notification for
    # the moderators.
    store(backend, token, uploadShare['fileName'], owner)

def requestUpload(backend, token, fileName, owner):
    """
    Requests a temporary upload share to upload a recording in chunks.

    Returns the data of the upload share ("token", "password" and "fileName"),
    or None if chunked uploads are not supported, either because the backend
    does not provide the endpoint to request an upload share (404) or because
    the backend does not allow them, for example if public sharing is disabled
    (400).

    :param backend: the backend to request the upload share to.
    :param token: the token of the conversation that was recorded.
    :param fileName: the recording file name.
    :param owner: the owner of the uploaded file.
    """

    url = backend.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/' + token + '/request-upload'

    data = json.dumps({
        'owner': owner,
        'fileName': os.path.basename(fileName),
    }).encode()

    # The checksum is calculated from the conversation token, like in the other
    # recording endpoints.
    random, checksum = getRandomAndChecksum(backend, token.encode())

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'OCS-ApiRequest': 'true',
        'Talk-Recording-Random': random,
        'Talk-Recording-Checksum': checksum,
        'User-Agent': recording.USER_AGENT,
    }

    request = Request('POST', url, headers, data=data)

    try:
        response = doRequest(backend, request)
    except HTTPError as httpError:
        if httpError.response is not None and httpError.response.status_code == 404:
            logger.info("Backend %s does not support chunked recording uploads, uploading directly", backend)

            return None

        if httpError.response is not None and httpError.response.status_code == 400:
            logger.info("Backend %s does not allow chunked recording uploads (public sharing may be "
                        "disabled), uploading directly", backend)

            return None

        raise

    return response.json()['ocs']['data']

def uploadRecordingInChunks(backend, uploadShare, fileName):
    """
    Uploads the recording specified by fileName in chunks to an upload share.

    The recording is uploaded through the chunked public WebDAV API, using the
    upload share token as the user and its password as the password.

    :param backend: the backend to upload the file to.
    :param uploadShare: the data of the upload share ("token", "password" and
           "fileName") as returned by requestUpload().
    :param fileName: the recording file name.
    """

    backendUrl = backend.rstrip('/')

    shareToken = uploadShare['token']
    sharePassword = uploadShare['password']
    auth = (shareToken, sharePassword)

    # A unique upload directory is used for each upload to prevent conflicts with
    # leftover chunks from a previous failed upload.
    uploadId = token_urlsafe(32)
    uploadUrl = backendUrl + '/public.php/dav/uploads/' + shareToken + '/' + uploadId
    destinationUrl = backendUrl + '/public.php/dav/files/' + shareToken + '/' + quote(uploadShare['fileName'])

    fileSize = os.path.getsize(fileName)

    # The destination of the assembled file and the final file size need to be
    # provided in every request of the chunked upload.
    headers = {
        'Destination': destinationUrl,
        'OC-Total-Length': str(fileSize),
        'User-Agent': recording.USER_AGENT,
    }

    # Initialize the chunked upload.
    doRequest(backend, Request('MKCOL', uploadUrl, headers, auth=auth))

    # Upload the recording in chunks. Chunks are named with sequential numbers
    # starting at 1, which is the order in which they are assembled into the
    # final file.
    chunkSize = config.getBackendUploadChunkSize(backend)
    chunkNumber = 0
    with open(fileName, 'rb') as fileToUpload:
        while True:
            chunk = fileToUpload.read(chunkSize)
            if not chunk:
                break

            chunkNumber += 1
            chunkUrl = uploadUrl + '/' + str(chunkNumber)

            doRequest(backend, Request('PUT', chunkUrl, headers, data=chunk, auth=auth))

    # Assemble the uploaded chunks into the final file at the destination.
    doRequest(backend, Request('MOVE', uploadUrl + '/.file', headers, auth=auth))

def store(backend, token, fileName, owner):
    """
    Triggers the post-processing of a recording previously uploaded in chunks.

    :param backend: the backend to store the recording in.
    :param token: the token of the conversation that was recorded.
    :param fileName: the name of the file uploaded through the upload share, as
           returned by requestUpload().
    :param owner: the owner of the uploaded file.
    """

    url = backend.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/' + token + '/store'

    data = json.dumps({
        'owner': owner,
        'fileName': fileName,
    }).encode()

    # The checksum is calculated from the conversation token, like in the other
    # recording endpoints.
    random, checksum = getRandomAndChecksum(backend, token.encode())

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'OCS-ApiRequest': 'true',
        'Talk-Recording-Random': random,
        'Talk-Recording-Checksum': checksum,
        'User-Agent': recording.USER_AGENT,
    }

    request = Request('POST', url, headers, data=data)

    doRequest(backend, request)

def uploadRecordingDirectly(backend, token, fileName, owner):
    """
    Upload the recording specified by fileName directly in a single request.

    The name of the uploaded file is the basename of the original file.

    This is a fallback for backends that do not support chunked uploads, and
    thus can not upload recordings larger than the limits enforced on a regular
    request.

    :param backend: the backend to upload the file to.
    :param token: the token of the conversation that was recorded.
    :param fileName: the recording file name.
    :param owner: the owner of the uploaded file.
    """

    url = backend.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/' + token + '/store'

    # Plain values become arguments, while tuples become files; the body used to
    # calculate the checksum is empty.
    data = {
        'owner': owner,
        # pylint: disable=consider-using-with
        'file': (os.path.basename(fileName), open(fileName, 'rb')),
    }

    multipartEncoder = MultipartEncoder(data)

    random, checksum = getRandomAndChecksum(backend, token.encode())

    headers = {
        'Content-Type': multipartEncoder.content_type,
        'OCS-ApiRequest': 'true',
        'Talk-Recording-Random': random,
        'Talk-Recording-Checksum': checksum,
        'User-Agent': recording.USER_AGENT,
    }

    uploadRequest = Request('POST', url, headers, data=multipartEncoder)

    doRequest(backend, uploadRequest)
