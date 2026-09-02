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

def _getIntervalsFileName(fileName):
    """
    Returns the sidecar JSON filename matching the given recording file.

    :param fileName: the recording file name.
    :return: the intervals JSON file name.
    """

    extensionlessFileName, _ = os.path.splitext(fileName)
    return extensionlessFileName + ' speaking times.json'

def getRandomAndChecksum(backendUrl, data):
    """
    Returns a random string and the checksum of the given data with that random.

    :param backendUrl: the URL of the backend to send the data to.
    :param data: the data, as bytes.
    """
    secret = config.getBackendSecret(backendUrl).encode()
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

def doRequest(backendUrl, request, retries=3):
    """
    Send the request to the backend.

    SSL verification will be skipped if configured.

    :param backendUrl: the URL of the backend to send the request to.
    :param request: the request to send.
    :param retries: the number of times to retry in case of failure.
    :returns: the response of the request.
    """
    backendSkipVerify = config.getBackendSkipVerify(backendUrl)

    try:
        session = Session()
        preparedRequest = session.prepare_request(request)
        response = session.send(preparedRequest, verify=not backendSkipVerify)
        response.raise_for_status()

        return response
    except Exception as exception:
        # Client errors (4xx) are deterministic, so retrying them would just
        # fail again and is therefore pointless.
        if retries > 1 and not _isClientError(exception):
            logger.exception("Failed to send message to backend, %d retries left!", retries)
            return doRequest(backendUrl, request, retries - 1)

        logger.exception("Failed to send message to backend, giving up!")
        raise

def backendRequest(backendUrl, data):
    """
    Sends the data to the backend on the endpoint to receive notifications from
    the recording server.

    The data is automatically wrapped in a request for the appropriate URL and
    with the needed headers.

    :param backendUrl: the URL of the backend to send the data to.
    :param data: the data to send.
    """
    url = backendUrl.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/backend'

    data = json.dumps(data).encode()

    random, checksum = getRandomAndChecksum(backendUrl, data)

    headers = {
        'Content-Type': 'application/json',
        'OCS-ApiRequest': 'true',
        'Talk-Recording-Random': random,
        'Talk-Recording-Checksum': checksum,
        'User-Agent': recording.USER_AGENT,
    }

    request = Request('POST', url, headers, data=data)

    doRequest(backendUrl, request)

def started(backendUrl, token, status, actorType, actorId):
    """
    Notifies the backend that the recording was started.

    :param backendUrl: the URL of the backend of the conversation.
    :param token: the token of the conversation.
    :param actorType: the actor type of the Talk participant that started the
           recording.
    :param actorId: the actor id of the Talk participant that started the
           recording.
    """

    backendRequest(backendUrl, {
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

def stopped(backendUrl, token, actorType, actorId):
    """
    Notifies the backend that the recording was stopped.

    :param backendUrl: the URL of the backend of the conversation.
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

    backendRequest(backendUrl, data)

def failed(backendUrl, token):
    """
    Notifies the backend that the recording failed.

    :param backendUrl: the URL of the backend of the conversation.
    :param token: the token of the conversation.
    """

    data = {
        'type': 'failed',
        'failed': {
            'token': token,
        },
    }

    backendRequest(backendUrl, data)

def uploadRecording(backendUrl, token, fileName, owner):
    """
    Upload the recording specified by fileName.

    The name of the uploaded file is the basename of the original file.

    If the backend supports it the recording is uploaded in chunks through a
    temporary upload share, which allows uploading recordings larger than the
    limits enforced on a regular request. Otherwise the recording is uploaded
    directly in a single request as a fallback for older backends.

    :param backendUrl: the URL of the backend to upload the file to.
    :param token: the token of the conversation that was recorded.
    :param fileName: the recording file name.
    :param owner: the owner of the uploaded file.
    """

    intervalsFileName = _getIntervalsFileName(fileName)
    intervalsFileName = intervalsFileName if os.path.exists(intervalsFileName) else None

    logger.info("Upload recording %s to %s in %s as %s", fileName, backendUrl, token, owner)

    if intervalsFileName:
        logger.info("Also uploading speaker intervals from %s", intervalsFileName)

    uploadShare = requestUpload(backendUrl, token, fileName, owner)

    if uploadShare is None:
        # The backend does not support chunked uploads or public link sharing is
        # disabled. Fall back to directly uploading the recording in a single
        # request.
        uploadRecordingDirectly(backendUrl, token, fileName, owner)

        return

    uploadRecordingInChunks(backendUrl, uploadShare, fileName)

    # Once the recording was uploaded and assembled the store endpoint is called
    # with its file name to trigger the post-processing and the notification for
    # the moderators.
    store(backendUrl, token, uploadShare['fileName'], owner)

def requestUpload(backendUrl, token, fileName, owner):
    """
    Requests a temporary upload share to upload a recording in chunks.

    Returns the data of the upload share ("token", "password" and "fileName"),
    or None if chunked uploads are not supported, either because the backend
    does not provide the endpoint to request an upload share (404) or because
    the backend does not allow them, for example if public sharing is disabled
    (400).

    :param backendUrl: the URL of the backend to request the upload share from.
    :param token: the token of the conversation that was recorded.
    :param fileName: the recording file name.
    :param owner: the owner of the uploaded file.
    """

    url = backendUrl.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/' + token + '/request-upload'

    data = json.dumps({
        'owner': owner,
        'fileName': os.path.basename(fileName),
    }).encode()

    # The checksum is calculated from the conversation token, like in the other
    # recording endpoints.
    random, checksum = getRandomAndChecksum(backendUrl, token.encode())

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
        response = doRequest(backendUrl, request)
    except HTTPError as httpError:
        if httpError.response is not None and httpError.response.status_code == 404:
            logger.info("Backend %s does not support chunked recording uploads, uploading directly", backendUrl)

            return None

        if httpError.response is not None and httpError.response.status_code == 400:
            logger.info("Backend %s does not allow chunked recording uploads (public sharing may be "
                        "disabled), uploading directly", backendUrl)

            return None

        raise

    return response.json()['ocs']['data']

def uploadRecordingInChunks(backendUrl, uploadShare, fileName):
    """
    Uploads the recording specified by fileName in chunks to an upload share.

    The recording is uploaded through the chunked public WebDAV API, using the
    upload share token as the user and its password as the password.

    :param backendUrl: the URL of the backend to upload the file to.
    :param uploadShare: the data of the upload share ("token", "password" and
           "fileName") as returned by requestUpload().
    :param fileName: the recording file name.
    """

    backendUrl = backendUrl.rstrip('/')

    shareToken = uploadShare['token']
    sharePassword = uploadShare['password']
    auth = (shareToken, sharePassword)

    intervalsFileName = _getIntervalsFileName(fileName)
    intervalsFileName = intervalsFileName if os.path.exists(intervalsFileName) else None

    # A unique upload directory is used for all upload to prevent conflicts
    # with leftover chunks from a previous failed upload.
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
    doRequest(backendUrl, Request('MKCOL', uploadUrl, headers, auth=auth))

    # Upload the recording in chunks. Chunks are named with sequential numbers
    # starting at 1, which is the order in which they are assembled into the
    # final file.
    chunkSize = config.getBackendUploadChunkSize(backendUrl)
    chunkNumber = 0
    with open(fileName, 'rb') as fileToUpload:
        while True:
            chunk = fileToUpload.read(chunkSize)
            if not chunk:
                break

            chunkNumber += 1
            chunkUrl = uploadUrl + '/' + str(chunkNumber)

            doRequest(backendUrl, Request('PUT', chunkUrl, headers, data=chunk, auth=auth))

    # Assemble the uploaded chunks into the final file at the destination.
    doRequest(backendUrl, Request('MOVE', uploadUrl + '/.file', headers, auth=auth))

    if intervalsFileName:
        _uploadSmallFileViaWebDAV(backendUrl, shareToken, sharePassword, intervalsFileName)

def _uploadSmallFileViaWebDAV(backendUrl, shareToken, sharePassword, fileName):
    """
    Uploads a small file via a single WebDAV PUT request to the public
    WebDAV endpoint.

    :param backendUrl: the base URL of the backend.
    :param shareToken: the token of the upload share.
    :param sharePassword: the password of the upload share.
    :param fileName: the file to upload.
    """

    backendUrl = backendUrl.rstrip('/')
    auth = (shareToken, sharePassword)

    destinationUrl = backendUrl + '/public.php/dav/files/' + shareToken + '/' + quote(os.path.basename(fileName))

    headers = {
        'Destination': destinationUrl,
        'User-Agent': recording.USER_AGENT,
    }

    # pylint: disable=consider-using-with
    doRequest(
        backendUrl,
        Request('PUT', destinationUrl, headers, data=open(fileName, 'rb'), auth=auth)
    )


def store(backendUrl, token, fileName, owner):
    """
    Triggers the post-processing of a recording previously uploaded in chunks.

    :param backendUrl: the URL of the backend to store the recording in.
    :param token: the token of the conversation that was recorded.
    :param fileName: the name of the file uploaded through the upload share, as
           returned by requestUpload().
    :param owner: the owner of the uploaded file.
    """

    url = backendUrl.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/' + token + '/store'

    intervalsBaseName = os.path.basename(_getIntervalsFileName(fileName))

    storeData = {
        'owner': owner,
        'fileName': fileName,
        'intervalsFileName': intervalsBaseName,
    }

    data = json.dumps(storeData).encode()

    # The checksum is calculated from the conversation token, like in the other
    # recording endpoints.
    random, checksum = getRandomAndChecksum(backendUrl, token.encode())

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'OCS-ApiRequest': 'true',
        'Talk-Recording-Random': random,
        'Talk-Recording-Checksum': checksum,
        'User-Agent': recording.USER_AGENT,
    }

    request = Request('POST', url, headers, data=data)

    doRequest(backendUrl, request)

def uploadRecordingDirectly(backendUrl, token, fileName, owner):
    """
    Upload the recording specified by fileName directly in a single request.

    The name of the uploaded file is the basename of the original file.

    This is a fallback for backends that do not support chunked uploads, and
    thus can not upload recordings larger than the limits enforced on a regular
    request.

    :param backendUrl: the URL of the backend to upload the file to.
    :param token: the token of the conversation that was recorded.
    :param fileName: the recording file name.
    :param owner: the owner of the uploaded file.
    """

    url = backendUrl.rstrip('/') + '/ocs/v2.php/apps/spreed/api/v1/recording/' + token + '/store'

    intervalsFileName = _getIntervalsFileName(fileName)
    intervalsFileName = intervalsFileName if os.path.exists(intervalsFileName) else None

    # Plain values become arguments, while tuples become files; the body used to
    # calculate the checksum is empty.
    data = {
        'owner': owner,
        # pylint: disable=consider-using-with
        'file': (os.path.basename(fileName), open(fileName, 'rb')),
    }

    if intervalsFileName:
        # pylint: disable=consider-using-with
        data['intervalsFile'] = (os.path.basename(intervalsFileName), open(intervalsFileName, 'rb'))

    multipartEncoder = MultipartEncoder(data)

    random, checksum = getRandomAndChecksum(backendUrl, token.encode())

    headers = {
        'Content-Type': multipartEncoder.content_type,
        'OCS-ApiRequest': 'true',
        'Talk-Recording-Random': random,
        'Talk-Recording-Checksum': checksum,
        'User-Agent': recording.USER_AGENT,
    }

    uploadRequest = Request('POST', url, headers, data=multipartEncoder)

    doRequest(backendUrl, uploadRequest)
