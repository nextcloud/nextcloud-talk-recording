#
# SPDX-FileCopyrightText: 2023 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
#

"""
Module to get the arguments to start the recorder process.
"""

from nextcloud.talk.recording import RECORDING_STATUS_AUDIO_AND_VIDEO
from .Config import config

class RecorderArgumentsBuilder:
    """
    Helper class to get the arguments to start the recorder process.

    Some of the recorder arguments, like the arguments for the output video
    codec, can be customized. By default they are got from the configuration,
    either a specific value set in the configuration file or a default value,
    but the configuration value can be extended or fully overriden, depending on
    the case, by explicitly setting it in RecorderArgumentsBuilder.
    """

    def __init__(self):
        self._ffmpegCommon = None
        self._ffmpegInputAudio = None
        self._ffmpegInputVideo = None
        self._ffmpegOutputAudio = None
        self._ffmpegOutputVideo = None
        self._extension = None

    def getRecorderArguments(self, status, displayId, audioSourceIndex, width, height, extensionlessOutputFileName):
        """
        Returns the list of arguments to start the recorder process.

        :param status: whether to record audio and video or only audio.
        :param displayId: the ID of the display that the browser is running in.
        :param audioSourceIndex: the index of the source for the browser audio
               output.
        :param width: the width of the display and the recording.
        :param height: the height of the display and the recording.
        :param extensionlessOutputFileName: the file name for the recording, without
               extension.
        :returns: the file name for the recording, with extension.
        """

        ffmpegCommon = self.getFfmpegCommon()
        ffmpegInputAudio = self.getFfmpegInputAudio(audioSourceIndex)
        ffmpegInputVideo = self.getFfmpegInputVideo(width, height, displayId)
        ffmpegOutputAudio = self.getFfmpegOutputAudio()
        ffmpegOutputVideo = self.getFfmpegOutputVideo()

        extension = self.getExtension(status)

        outputFileName = extensionlessOutputFileName + extension

        ffmpegArguments = ffmpegCommon
        ffmpegArguments += ffmpegInputAudio

        if status == RECORDING_STATUS_AUDIO_AND_VIDEO:
            ffmpegArguments += ffmpegInputVideo

        ffmpegArguments += ffmpegOutputAudio

        if status == RECORDING_STATUS_AUDIO_AND_VIDEO:
            ffmpegArguments += ffmpegOutputVideo

        return ffmpegArguments + [outputFileName]

    def getFfmpegCommon(self):
        """
        Returns the ffmpeg executable (name or full path) and the global options
        given to ffmpeg.
        """
        if self._ffmpegCommon is not None:
            return self._ffmpegCommon

        return config.getFfmpegCommon()

    def getFfmpegInputAudio(self, audioSourceIndex):
        """
        Returns the options given to ffmpeg for the audio input.
        """
        ffmpegInputAudio = config.getFfmpegInputAudio()

        if self._ffmpegInputAudio is not None:
            ffmpegInputAudio = self._ffmpegInputAudio

        return ffmpegInputAudio + \
            ['-f', 'pulse', '-i', audioSourceIndex]

    def getFfmpegInputVideo(self, width, height, displayId):
        """
        Returns the options given to ffmpeg for the video input.
        """
        ffmpegInputVideo = config.getFfmpegInputVideo()

        if self._ffmpegInputVideo is not None:
            ffmpegInputVideo = self._ffmpegInputVideo

        return ffmpegInputVideo + \
            ['-f', 'x11grab', '-draw_mouse', '0', '-video_size', f'{width}x{height}', '-i', displayId]

    def getFfmpegOutputAudio(self):
        """
        Returns the options given to ffmpeg to encode the audio output.
        """
        if self._ffmpegOutputAudio is not None:
            return self._ffmpegOutputAudio

        return config.getFfmpegOutputAudio()

    def getFfmpegOutputVideo(self):
        """
        Returns the options given to ffmpeg to encode the video output.
        """
        if self._ffmpegOutputVideo is not None:
            return self._ffmpegOutputVideo

        return config.getFfmpegOutputVideo()

    def getExtension(self, status):
        """
        Returns the extension of the output file.

        If no extension was explicitly set the status defines whether the
        extension will be the one configured for audio recordings or the one
        configured for video recordings.
        """
        if self._extension:
            return self._extension

        if status == RECORDING_STATUS_AUDIO_AND_VIDEO:
            return config.getFfmpegExtensionVideo()

        return config.getFfmpegExtensionAudio()

    def setFfmpegCommon(self, ffmpegCommon):
        """
        Sets the ffmpeg executable (name or full path) and the global options
        given to ffmpeg.
        """
        self._ffmpegCommon = ffmpegCommon

    def setFfmpegInputAudio(self, ffmpegInputAudio):
        """
        Sets the (additional) options given to ffmpeg for the audio input.
        """
        self._ffmpegInputAudio = ffmpegInputAudio

    def setFfmpegInputVideo(self, ffmpegInputVideo):
        """
        Sets the (additional) options given to ffmpeg for the video input.
        """
        self._ffmpegInputVideo = ffmpegInputVideo

    def setFfmpegOutputAudio(self, ffmpegOutputAudio):
        """
        Sets the options given to ffmpeg to encode the audio output.
        """
        self._ffmpegOutputAudio = ffmpegOutputAudio

    def setFfmpegOutputVideo(self, ffmpegOutputVideo):
        """
        Sets the options given to ffmpeg to encode the video output.
        """
        self._ffmpegOutputVideo = ffmpegOutputVideo

    def setExtension(self, extension):
        """
        Sets the extension of the output file.
        """
        self._extension = extension
