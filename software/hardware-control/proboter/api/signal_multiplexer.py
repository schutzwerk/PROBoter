# Copyright (C) 2023 SCHUTZWERK GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
from dataclasses import dataclass

from quart import Blueprint
from quart_schema import validate_response, tag

from proboter.model import SignalMultiplexerChannel, SignalMultiplexerConfig
from proboter.hardware import SignalMultiplexer, \
    SignalMultiplexerStatus, ProbeType, SignalMultiplexerChannelDigitalLevel

from .utils import ApiTags, ApiErrorResponse, ApiException, inject_signal_multiplexer


log = logging.getLogger(__name__)

bp = Blueprint('signal-multiplexer', __name__,
               url_prefix="/signal-multiplexer")


# Accepted here to reduce the amount of requests to fetch the
# complete signal multiplexer state
# pylint: disable=too-many-instance-attributes
@dataclass
class SignalMultiplexerConfigResponse:
    """
    Signal multiplexer configuration response
    """
    id: int
    name: str
    usb_device_name: str
    baud_rate: int
    channel_1_probe: ProbeType
    channel_2_probe: ProbeType
    channel_3_probe: ProbeType
    channel_4_probe: ProbeType


@dataclass
class SignalMultiplexerChannelTestResponse:
    """
    Response of a signal multiplexer digital voltage
    level measurement
    """
    channel: SignalMultiplexerChannel
    level: SignalMultiplexerChannelDigitalLevel


@bp.route('', methods=["GET"])
@validate_response(SignalMultiplexerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer(must_be_connected=False)
async def get_signal_multiplexer_status(signal_multiplexer: SignalMultiplexer) \
        -> SignalMultiplexerStatus:
    """
    Return the current signal multiplexer status
    """
    log.info("Signal multiplexer status request received")
    return signal_multiplexer.status


@bp.route('/config', methods=["GET"])
@validate_response(SignalMultiplexerConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer(must_be_connected=False)
async def get_signal_multiplexer_config(signal_multiplexer: SignalMultiplexer) \
        -> SignalMultiplexerConfigResponse:
    """
    Return the signal multiplexer configuration
    """
    log.info("Signal multiplexer configuration request received")

    config = await SignalMultiplexerConfig.get_by_id(signal_multiplexer.config.id)
    channel_1_probe = await config.channel_1_probe
    channel_2_probe = await config.channel_2_probe
    channel_3_probe = await config.channel_3_probe
    channel_4_probe = await config.channel_4_probe

    return SignalMultiplexerConfigResponse(id=config.id,
                                           name=config.name,
                                           usb_device_name=config.usb_device_name,
                                           baud_rate=config.baud_rate,
                                           channel_1_probe=channel_1_probe.probe_type,
                                           channel_2_probe=channel_2_probe.probe_type,
                                           channel_3_probe=channel_3_probe.probe_type,
                                           channel_4_probe=channel_4_probe.probe_type)


@bp.route('/route-to-analog/<int:channel>', methods=["POST"])
@validate_response(SignalMultiplexerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer()
async def route_channel_to_analog_input(signal_multiplexer: SignalMultiplexer, channel: int) \
        -> SignalMultiplexerStatus:
    """
    Route input channel to analog output
    """
    log.info("Route channel %d to analog output request received", channel)

    if not channel in SignalMultiplexerChannel.channel_ids():
        raise ApiException("Invalid channel ID")

    await signal_multiplexer.connect_to_analog(SignalMultiplexerChannel(channel))
    return signal_multiplexer.status


@bp.route('/route-to-digital/<int:channel>', methods=["POST"])
@validate_response(SignalMultiplexerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer()
async def route_channel_to_digital_output(signal_multiplexer: SignalMultiplexer, channel: int) \
        -> SignalMultiplexerStatus:
    """
    Route input channel to digital output
    """
    log.info("Route channel %d to digital output request received", channel)

    if not channel in SignalMultiplexerChannel.channel_ids():
        raise ApiException("Invalid channel ID")

    await signal_multiplexer.connect_to_digital(SignalMultiplexerChannel(channel))
    return signal_multiplexer.status


@bp.route('/pull/<int:channel>', methods=["POST"])
@validate_response(SignalMultiplexerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer()
async def pull_channel(signal_multiplexer: SignalMultiplexer, channel: int) \
        -> SignalMultiplexerStatus:
    """
    Pull input channel (set to HIGH voltage)
    """
    log.info("Pull HIGH request received for channel %d", channel)

    if not channel in SignalMultiplexerChannel.channel_ids():
        raise ApiException("Invalid channel ID")

    await signal_multiplexer.pull_channel(SignalMultiplexerChannel(channel))
    return signal_multiplexer.status


@bp.route('/release/<int:channel>', methods=["POST"])
@validate_response(SignalMultiplexerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer()
async def release_channel(signal_multiplexer: SignalMultiplexer, channel: int) \
        -> SignalMultiplexerStatus:
    """
    Release input channel (set to HIGH impedance mode)
    """
    log.info("Release request received for channel %d", channel)

    if not channel in SignalMultiplexerChannel.channel_ids():
        raise ApiException("Invalid channel ID")

    await signal_multiplexer.release_channel(SignalMultiplexerChannel(channel))
    return signal_multiplexer.status


@bp.route('/release-all', methods=["POST"])
@validate_response(SignalMultiplexerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer()
async def release_all_channels(signal_multiplexer: SignalMultiplexer) \
        -> SignalMultiplexerStatus:
    """
    Release all input channels (set to HIGH impedance mode)
    """
    log.info("Release all channels request received")

    await signal_multiplexer.release_all()
    return signal_multiplexer.status


@bp.route('/test-level/<int:channel>', methods=["POST"])
@validate_response(SignalMultiplexerChannelTestResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.SIGNAL_MULTIPLEXER])
@inject_signal_multiplexer()
async def test_channel(signal_multiplexer: SignalMultiplexer, channel: int) \
        -> SignalMultiplexerChannelTestResponse:
    """
    Return the current voltage level of a given channel
    """
    log.info("Request to get the current voltage level of channel %d received",
             channel)

    if not channel in SignalMultiplexerChannel.channel_ids():
        raise ApiException("Invalid channel ID")

    multiplexer_channel = SignalMultiplexerChannel(channel)
    channel_level = await signal_multiplexer.test_channel(multiplexer_channel)
    return SignalMultiplexerChannelTestResponse(channel=multiplexer_channel,
                                                level=channel_level)
