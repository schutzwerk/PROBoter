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

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple

import cv2
import numpy as np
from pydantic import Field
from quart import Blueprint, request, make_response, current_app
from quart_schema import validate_response, validate_request, \
    validate_querystring, tag

from proboter.fields import NumpyArray
from proboter.model import StaticCameraConfig, StaticCameraCalibrationConfig, \
    ReferenceBoardConfig
from proboter.hardware import StaticCamera, CameraStatus
from proboter.tasks import CalibrateStaticCameraTask, CalibrateStaticCameraParameter, \
    CalibrateStaticCameraResult, CalibrateCameraIntrinsicsTask, \
    CalibrateCameraIntrinsicsParameter, CalibrateCameraIntrinsicsResult, \
    ScanPcbStaticCameraTask, ScanPcbStaticCameraParameter, ScanPcbStaticCameraResult, \
    TaskProcessor

from .utils import ApiTags, ApiException, ApiErrorResponse, inject_static_camera, \
    inject_task_processor


log = logging.getLogger(__name__)

bp = Blueprint('camera-static', __name__, url_prefix="/camera/static")


@dataclass
class CameraSnapshotRequest:
    """
    Camera snapshot request
    """
    # Snapshot resolution width
    width: Optional[int] = 640
    # Snapshot resolution height
    height: Optional[int] = 480
    # Whether any lens distortion should be removed
    undistort: Optional[bool] = False


@dataclass
class StaticCameraConfigUpdateRequest:
    """
    Static camera configuration update request
    """
    name: str = Field()
    usb_device_name: str = Field()
    resolution: Tuple[int, int] = Field()
    camera_matrix: NumpyArray = Field(np_shape=(3, 3))
    distortion_coefficients: NumpyArray = Field(np_shape=(1, 5))
    tmat_to_global: NumpyArray = Field(np_shape=(4, 4))

    def update_config(self, config: StaticCameraConfig) -> None:
        """
        Update a given camera config with the values of this request

        :param config: Camera configuration to update
        :type config: StaticCameraConfig
        """
        config.name = self.name
        config.usb_device_name = self.usb_device_name
        config.resolution_width = self.resolution[0]
        config.resolution_height = self.resolution[1]
        config.camera_matrix = self.camera_matrix
        config.distortion_coefficients = self.distortion_coefficients
        config.tmat_to_global = self.tmat_to_global


@dataclass
class StaticCameraConfigResponse(StaticCameraConfigUpdateRequest):
    """
    Static camera configuration response
    """
    id: int = Field()

    @staticmethod
    def from_config(config: StaticCameraConfig) \
            -> "StaticCameraConfigResponse":
        """
        Create an API response from a given camera configuration
        :rtype: StaticCameraConfigResponse
        """
        return StaticCameraConfigResponse(id=config.id,
                                          name=config.name,
                                          usb_device_name=config.usb_device_name,
                                          resolution=(config.resolution_width,
                                                      config.resolution_height),
                                          camera_matrix=config.camera_matrix,
                                          distortion_coefficients=config.distortion_coefficients,
                                          tmat_to_global=config.tmat_to_global)


@dataclass
class StaticCameraCalibrationConfigUpdateRequest:
    """
    Static camera calibration configuration update request
    """
    brightness_threshold: int
    image_resolution: NumpyArray = Field(np_shape=2)

    def update_config(self, config: StaticCameraCalibrationConfig) -> None:
        """
        Update a given camera calibration config with the values of this request

        :param config: Camera calibration configuration to update
        :type config: StaticCameraCalibrationConfig
        """
        config.brightness_threshold = self.brightness_threshold
        config.image_resolution = self.image_resolution


@dataclass
class StaticCameraCalibrationConfigResponse(
        StaticCameraCalibrationConfigUpdateRequest):
    """
    Static camera calibration configuration response
    """
    @staticmethod
    def from_config(config: StaticCameraCalibrationConfig) \
            -> "StaticCameraCalibrationConfigResponse":
        """
        Create an API response from a given camera calibration configuration
        :rtype: StaticCameraCalibrationConfigResponse
        """
        return StaticCameraCalibrationConfigResponse(brightness_threshold=config.brightness_threshold,
                                                     image_resolution=config.image_resolution)


@dataclass
class StaticCameraCalibrationResponse:
    """
    Multi-camera calibration result container
    """
    results: List[CalibrateStaticCameraResult]


@ bp.route('/<int:camera_idx>', methods=["GET"])
@ validate_response(CameraStatus, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera(must_be_connected=False)
async def get_static_camera_status(camera: StaticCamera) -> CameraStatus:
    """
    Return the status of a single static camera of the current PROBoter instance
    """
    log.info("Static camera '%s' status request received", camera.id)
    return camera.status


@ bp.route('/<int:camera_idx>/snapshot', methods=["GET"])
@ validate_querystring(CameraSnapshotRequest)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera()
async def capture_static_camera_snapshot(camera: StaticCamera, \
    query_args: CameraSnapshotRequest) -> bytes:
    """
    Return the status of a single static camera of the current PROBoter instance
    """
    log.info("Static camera '%s' snapshot request received", camera.id)
    raw_snapshot = await camera.capture_snapshot(resolution=(query_args.width,
                                                             query_args.height),
                                                 undistort=query_args.undistort)
    _, snapshot_encoded = cv2.imencode(".png", raw_snapshot)
    return snapshot_encoded.tobytes(), 200, {"Content-Type": "image/png"}


@ bp.route('/<int:camera_idx>/scan', methods=["POST"])
@ validate_request(ScanPcbStaticCameraParameter)
@validate_response(ScanPcbStaticCameraResult, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera()
@inject_task_processor()
async def scan_pcb_with_static_camera(task_processor: TaskProcessor,
                                      camera: StaticCamera,
                                      data: ScanPcbStaticCameraParameter)  \
        -> ScanPcbStaticCameraResult:
    """
    Create a PCB scan with a static camera system

    The resulting PCB scan is directly sent to the project
    storage.
    """
    log.info("Static camera '%s' scan request received",
             camera.id)
    print(data)
    task = ScanPcbStaticCameraTask(data, camera)
    return await task_processor.execute_task(task)


@ bp.route('/<int:camera_idx>/feed', methods=["GET"])
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera()
async def get_camera_feed(camera: StaticCamera):
    """
    Static camera video feed
    """
    log.info("Static camera '%s' feed request received",
             camera.id)

    async def multipart_stream():

        try:
            async for frame_jpeg in camera.stream():
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_jpeg + b"\r\n")
        except asyncio.CancelledError:
            log.info("Connection to static camera feed '%d' was canceled",
                     camera.id)

    response = await make_response(multipart_stream(),
                                   200,
                                   {"Content-Type": 'multipart/x-mixed-replace; boundary=frame'})
    # This has to be done to disable the 'slow response consumption' DoS-protection mechanism
    # provided by quart (https://pgjones.gitlab.io/quart/discussion/dos_mitigations.html).
    # Otherwise, the continuous stream of data will be canceled after 60
    # seconds by default.
    response.timeout = None

    return response


@ bp.route('/<int:camera_idx>/config', methods=["GET"])
@validate_response(StaticCameraConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera(must_be_connected=False)
async def get_static_camera_config(camera: StaticCamera) -> StaticCameraConfigResponse:
    """
    Return static camera configuration
    """
    log.info("Static camera '%s' configuration request received",
             camera.id)
    config = await StaticCameraConfig.get_by_id(camera.id)
    return StaticCameraConfigResponse.from_config(config)


@ bp.route('/<int:camera_idx>/config', methods=["PUT"])
@validate_request(StaticCameraConfigUpdateRequest)
@validate_response(StaticCameraConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera(must_be_connected=False)
async def update_static_camera_config(camera: StaticCamera,
                                      data: StaticCameraConfigUpdateRequest) \
        -> StaticCameraConfigResponse:
    """
    Update a static camera's configuration
    """
    log.info("Static camera '%s' configuration update request received",
             camera.id)

    config = await StaticCameraConfig.get_by_id(camera.id)
    data.update_config(config)
    await config.save()

    # Reconnect / reload the PROBoter hardware so that the
    # new configuration is applied
    await current_app.reconnect_proboter()

    return StaticCameraConfigResponse.from_config(config)


@ bp.route('/<int:camera_idx>/calibration-config', methods=["GET"])
@validate_response(StaticCameraCalibrationConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera(must_be_connected=False)
async def get_static_camera_calibration_config(camera: StaticCamera) \
        -> StaticCameraCalibrationConfigResponse:
    """
    Return static camera calibration configuration
    """
    log.info("Static camera '%s' calibration configuration request received",
             camera.id)

    config = await StaticCameraCalibrationConfig.get_by_id(camera.id)
    return StaticCameraCalibrationConfigResponse.from_config(config)


@ bp.route('/<int:camera_idx>/calibration-config', methods=["PUT"])
@validate_request(StaticCameraCalibrationConfigUpdateRequest)
@validate_response(StaticCameraCalibrationConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera(must_be_connected=False)
async def update_static_camera_calibration_config(camera: StaticCamera,
                                                  data: StaticCameraCalibrationConfigUpdateRequest) \
        -> StaticCameraCalibrationConfigResponse:
    """
    Update a static camera's calibration configuration
    """
    log.info("Static camera '%s' calibration configuration update request received",
             camera.id)

    config = await StaticCameraCalibrationConfig.get_by_id(camera.id)
    data.update_config(config)
    await config.save()
    return StaticCameraCalibrationConfigResponse.from_config(config)


@ bp.route('/<int:camera_idx>/calibrate', methods=["POST"])
@ validate_request(CalibrateStaticCameraParameter)
@ validate_response(StaticCameraCalibrationResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera()
@inject_task_processor()
async def calibrate_static_camera(task_processor: TaskProcessor,
                                  camera: StaticCamera,
                                  data: CalibrateStaticCameraParameter) \
        -> StaticCameraCalibrationResponse:

    """
    Perform a calibration of the camera by taking a snapshot of a \\
    reference board
    """
    log.info("Static camera '%d' calibration request received",
             camera.id)
    log.info(data)

    # Fetch the reference board
    board_config = await ReferenceBoardConfig.get_by_id(data.reference_board)
    if board_config is None:
        raise ApiException("Reference board not found")

    # Calibrate the static camera
    results = []
    for i in range(data.num_calibration_runs):
        log.info('Running calibration run %d of %d',
                 i + 1, data.num_calibration_runs)
        task = CalibrateStaticCameraTask(data, camera, board_config)
        results.append(await task_processor.execute_task(task))
        # Important: Transposing of the transformation matrix is
        #            required, because the (de)serialization somehow
        # has the same effect (futher inspection is recommended)
        # result.tmat = result.tmat.T
        await asyncio.sleep(0.5)

    return StaticCameraCalibrationResponse(results)


@ bp.route('/<int:camera_idx>/calibrate-intrinsics', methods=["POST"])
@ validate_response(CalibrateCameraIntrinsicsResult, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.CAMERA_STATIC])
@ inject_static_camera(must_be_connected=False)
@inject_task_processor()
async def calibrate_static_camera_intrinsics(task_processor: TaskProcessor,
                                             camera: StaticCamera) \
        -> CalibrateCameraIntrinsicsResult:
    """
    Perform a camera calibration

    The intrinsic camera parameters represented by the camera
    matrix and a distortion coefficient vector are determined
    from several chessboard images
    """
    log.info("Static camera '%s' intrinsics calibration request received",
             camera.id)

    # TODO Replace manual input parsing!!

    # Manual form data parsing
    form_data = await request.form

    # Manual file conversion
    snapshots = []
    files = await request.files
    for raw_image in files.getlist("snapshots"):
        nparr = np.fromstring(raw_image.read(), np.uint8)
        chessboard_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        snapshots.append(chessboard_image)

    if len(snapshots) < 1:
        raise ApiException("No chessboard snapshots provided")

    # Bundle all input parameters
    params = CalibrateCameraIntrinsicsParameter(int(form_data["gridSizeX"]),
                                                int(form_data["gridSizeY"]),
                                                float(form_data["fieldSizeX"]),
                                                float(form_data["fieldSizeY"]),
                                                snapshots=snapshots)

    task = CalibrateCameraIntrinsicsTask(params)
    return await task_processor.execute_task(task)
