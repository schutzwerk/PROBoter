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

"""
CLI script to initialize the database for
the PROBoter application
"""
import asyncio
import logging

import numpy as np
from quart import Quart
from tortoise import Tortoise, connections

from proboter.model import ProboterConfig, ProbeConfig, StaticCameraConfig, \
    MovableCameraConfig, AxesControllerConfig, SignalMultiplexerConfig, \
    ProbeCalibrationConfig, StaticCameraCalibrationConfig,\
    MovableCameraCalibrationConfig, ReferenceBoardConfig, ProbeType,\
    PicoscopeConfig, UartInterfaceAdapterConfig, SignalMultiplexerChannel, \
    TargetPowerControllerConfig

# Disable max. line length checks only for this file as there are some configuration values / steps
# that would be less readable if the default length is enforced here.
# pylint: disable=line-too-long
def proboter_cli(app: Quart) -> None:
    """
    PROBoter CLI extension
    """

    @app.cli.command()
    def seed_db() -> None:
        """
        Seed the database with with some dummy data
        """
        logging.basicConfig(level=logging.DEBUG)
        asyncio.get_event_loop().run_until_complete(_seed_db())

    async def _seed_db():
        await initialize_db(app)


async def initialize_db(app: Quart):
    """
    Populate a database with a default PROBoter hardware configuration
    """
    # Establish a connection to the database
    await Tortoise.init(
        db_url=app.config["DATABASE_URI"],
        modules={"models": ["proboter.model"]}
    )

    # Generate schema
    await Tortoise.generate_schemas()

    # PROBoter config
    proboter_1 = await ProboterConfig.create(name="Default config",
                                             is_active=True)

    # Axes controller configs
    axes_controller_1 = await AxesControllerConfig.create(uuid="83c711bc-8cd2-455b-8569-9d68caae3c40",
                                                          usb_device_name="/dev/proboter_probe-11",
                                                          baud_rate=115200,
                                                          is_light_controller=False)

    axes_controller_2 = await AxesControllerConfig.create(uuid="91be47ca-4bc1-463e-b729-c8780844b754",
                                                          usb_device_name="/dev/proboter_probe-1",
                                                          baud_rate=115200,
                                                          is_light_controller=False)

    axes_controller_3 = await AxesControllerConfig.create(uuid="29f6b5f4-f75e-40a2-976e-eff0b0aad122",
                                                          usb_device_name="/dev/proboter_probe-2",
                                                          baud_rate=115200,
                                                          is_light_controller=True)

    axes_controller_4 = await AxesControllerConfig.create(uuid="f6248c8c-9133-4b20-b59e-4bc9b1687b4f",
                                                          usb_device_name="/dev/proboter_probe-21",
                                                          baud_rate=115200,
                                                          is_light_controller=False)

    # Probes
    # Probe 1.1
    probe_11 = await ProbeConfig.create(name="1.1",
                                        order_index=3,
                                        probe_type=ProbeType.P11,
                                        tmat_to_glob=np.array([
                                            [
                                                0.993226546349076,
                                                -0.003059603002199207,
                                                0.0005575967345172293,
                                                7.779447843936979
                                            ],
                                            [
                                                0.002309721747836912,
                                                1.0000245416015465,
                                                0.0027115383742523894,
                                                5.186901044866231
                                            ],
                                            [
                                                -0.0023677134649509398,
                                                -0.006617668087014238,
                                                0.9373629028285523,
                                                -30.55491789525287
                                            ],
                                            [
                                                0,
                                                0,
                                                0,
                                                1
                                            ]
                                        ]),
                                        pos_x_safety_position=np.array(
                                            [70, 100, 5]),
                                        neg_x_safety_position=np.array(
                                            [-150, 100, 5]),
                                        axes_controller=axes_controller_1,
                                        proboter_id=proboter_1.id)

    await ProbeCalibrationConfig(calibration_feed=1000,
                                 home_before_calibration=True,
                                 initial_probe_positions=np.array([
                                     [
                                         8,
                                         5,
                                         0
                                     ],
                                     [
                                         -4,
                                         5,
                                         0
                                     ],
                                     [
                                         -4,
                                         -15,
                                         0
                                     ],
                                     [
                                         8,
                                         -15,
                                         0
                                     ]
                                 ]),
                                 probe=probe_11).save()

    # Probe 1
    probe_1 = await ProbeConfig.create(name="1",
                                       order_index=2,
                                       probe_type=ProbeType.P1,
                                       tmat_to_glob=np.array([
                                           [
                                               0.9925151268151038,
                                               -0.007332200347849316,
                                               -0.015201581659851353,
                                               21.226364322640254
                                           ],
                                           [
                                               0.0038516722390262714,
                                               0.9990421126448797,
                                               0.014090286921444019,
                                               -8.893311470593448
                                           ],
                                           [
                                               0.007696482659481167,
                                               -0.010431782735958708,
                                               0.9990553482152436,
                                               -22.695996834516308
                                           ],
                                           [
                                               0,
                                               0,
                                               0,
                                               1
                                           ]
                                       ]),
                                       pos_x_safety_position=np.array(
                                           [80, 80, 0]),
                                       neg_x_safety_position=np.array(
                                           [-140, 80, 0]),
                                       axes_controller=axes_controller_2,
                                       proboter=proboter_1)

    await ProbeCalibrationConfig(calibration_feed=1000,
                                 home_before_calibration=True,
                                 initial_probe_positions=np.array([
                                     [
                                         -3,
                                         18,
                                         0
                                     ],
                                     [
                                         -15,
                                         18,
                                         0
                                     ],
                                     [
                                         -15,
                                         -2,
                                         0
                                     ],
                                     [
                                         -3,
                                         -2,
                                         0
                                     ]
                                 ]),
                                 probe=probe_1).save()

    # Probe 2
    probe_2 = await ProbeConfig.create(name="2",
                                       order_index=1,
                                       probe_type=ProbeType.P2,
                                       tmat_to_glob=np.array([
                                           [
                                               0.9952825743544294,
                                               -0.005912494064656992,
                                               -0.005255874224526504,
                                               -7.489499990582077
                                           ],
                                           [
                                               0.0025705675749856383,
                                               0.9990808657242483,
                                               0.009389689338493648,
                                               4.803937305995607
                                           ],
                                           [
                                               0.009604709858075416,
                                               -0.008367736928721958,
                                               1.0036497764765941,
                                               -24.657945892895327
                                           ],
                                           [
                                               0,
                                               0,
                                               0,
                                               1
                                           ]
                                       ]),
                                       pos_x_safety_position=np.array(
                                           [125, 80, 0]),
                                       neg_x_safety_position=np.array(
                                           [-100, 80, 0]),
                                       axes_controller=axes_controller_3,
                                       proboter=proboter_1)

    await ProbeCalibrationConfig(calibration_feed=1000,
                                 home_before_calibration=True,
                                 initial_probe_positions=np.array([
                                     [
                                         25,
                                         5,
                                         0
                                     ],
                                     [
                                         13,
                                         5,
                                         0
                                     ],
                                     [
                                         13,
                                         -15,
                                         0
                                     ],
                                     [
                                         25,
                                         -15,
                                         0
                                     ]
                                 ]),
                                 probe=probe_2).save()

    # Probe 2.1
    probe_21 = await ProbeConfig.create(name="2.1",
                                        order_index=0,
                                        probe_type=ProbeType.P21,
                                        tmat_to_glob=np.array([
                                            [
                                                0.9955063896433682,
                                                -0.006325335507924912,
                                                -0.024094240294292805,
                                                -0.7489590457459155
                                            ],
                                            [
                                                0.0036336653752381243,
                                                0.9987652010654637,
                                                0.021878124256109025,
                                                -6.597349234365499
                                            ],
                                            [
                                                0.006621721213755103,
                                                -0.006795413133690583,
                                                0.998949986626887,
                                                -28.239957251271758
                                            ],
                                            [
                                                0,
                                                0,
                                                0,
                                                1
                                            ]
                                        ]),
                                        pos_x_safety_position=np.array(
                                            [130, 90, 5]),
                                        neg_x_safety_position=np.array(
                                            [-110, 90, 5]),
                                        axes_controller=axes_controller_4,
                                        proboter=proboter_1)

    await ProbeCalibrationConfig(calibration_feed=1000,
                                 home_before_calibration=True,
                                 initial_probe_positions=np.array([
                                     [
                                         22,
                                         18,
                                         0
                                     ],
                                     [
                                         10,
                                         18,
                                         0
                                     ],
                                     [
                                         10,
                                         -2,
                                         0
                                     ],
                                     [
                                         22,
                                         -2,
                                         0
                                     ]
                                 ]),
                                 probe=probe_21).save()

    # Cameras
    # Camera 1 - USB microscope (MOVABLE)
    camera_1 = await MovableCameraConfig.create(name="Prototype (movable)",
                                                resolution_width=640,
                                                resolution_height=480,
                                                framerate=25,
                                                camera_matrix=np.array([
                                                    [2419.8714041022095, 0.0,
                                                     368.4589198145625],
                                                    [0.0, 2432.4347718737677,
                                                     348.0828525752433],
                                                    [0.0, 0.0, 1.0]]),
                                                distortion_coefficients=np.array([[0.029241597712360692,
                                                                                   -2.894855059738245,
                                                                                   0.012715599956771772,
                                                                                   0.008878334726425477,
                                                                                   86.9308653805658]]),
                                                tmat_camera_rotation=np.array([
                                                    [
                                                        0.04144111620381073,
                                                        0.9884510417490275,
                                                        -0.14576409692734624,
                                                        0
                                                    ],
                                                    [
                                                        -0.9870509372399745,
                                                        0.017874956136582118,
                                                        -0.15940807142928282,
                                                        0
                                                    ],
                                                    [
                                                        -0.15496154742861315,
                                                        0.15048263690000185,
                                                        0.9763922853086008,
                                                        0
                                                    ],
                                                    [
                                                        0,
                                                        0,
                                                        0,
                                                        1
                                                    ]
                                                ]),
                                                tmat_ref_to_probe=np.array([
                                                    [
                                                        0.9926882943065743,
                                                        -0.0005473852898575133,
                                                        0.03564076410644573,
                                                        -15.843824607514277
                                                    ],
                                                    [
                                                        0.008874264963220878,
                                                        -0.9976474802429183,
                                                        -0.017119020592442385,
                                                        -28.399383425910575
                                                    ],
                                                    [
                                                        0.03525581953381574,
                                                        0.017072588749834364,
                                                        -0.9992180317967967,
                                                        122.22012088553195
                                                    ],
                                                    [
                                                        0,
                                                        0,
                                                        0,
                                                        1
                                                    ]
                                                ]),
                                                axes_controller=axes_controller_2,
                                                proboter=proboter_1)

    await MovableCameraCalibrationConfig(camera_delay=5.0,
                                         calibration_feed=1000,
                                         home_before_calibration=True,
                                         initial_positions=np.array(
                                             ((32, 85),
                                              (-28, 85),
                                              (-28, 5),
                                              (32, 5))),
                                         camera=camera_1).save()

    # Camera 2 - Static camera system of the PROBoter prototype
    camera_2 = await StaticCameraConfig.create(name="Prototype (static)",
                                               usb_device_name="/dev/proboter_camera-static",
                                               resolution_width=640,
                                               resolution_height=480,
                                               framerate=20,
                                               camera_matrix=np.array([
                                                   [
                                                       1377.7849579142357,
                                                       0,
                                                       1023.9088611932771
                                                   ],
                                                   [
                                                       0,
                                                       1377.1297337840913,
                                                       585.305591100558
                                                   ],
                                                   [
                                                       0,
                                                       0,
                                                       1
                                                   ]
                                               ]),
                                               distortion_coefficients=np.array([[
                                                   -0.4339360784824869,
                                                   0.26596545933855065,
                                                   0.0006596062861746274,
                                                   0.0012195013662689666,
                                                   -0.09205635953372691
                                               ]]),
                                               tmat_to_global=np.array([
                                                   [
                                                       -0.9994378619009724,
                                                       0.008744007003474065,
                                                       -0.032365143910323656,
                                                       0
                                                   ],
                                                   [
                                                       -0.008645065592941798,
                                                       -0.9999575242264099,
                                                       -0.003195713360505391,
                                                       0
                                                   ],
                                                   [
                                                       -0.03239171251580406,
                                                       -0.0029141181362421303,
                                                       0.9994710025187232,
                                                       0
                                                   ],
                                                   [
                                                       2.461537603089295,
                                                       -5.757457612556936,
                                                       332.23032614512084,
                                                       1
                                                   ]
                                               ]),
                                               proboter=proboter_1)

    await StaticCameraCalibrationConfig(image_resolution=np.array([1920, 1080]),
                                        brightness_threshold=200,
                                        camera=camera_2).save()

    # Signal multiplexer board
    await SignalMultiplexerConfig(name="Default",
                                  baud_rate=9600,
                                  usb_device_name="/dev/proboter_signal-multiplexer",
                                  channel_1_probe=probe_1,
                                  channel_2_probe=probe_11,
                                  channel_3_probe=probe_2,
                                  channel_4_probe=probe_21,
                                  proboter=proboter_1).save()

    # Picoscope
    await PicoscopeConfig(name="PicoScope PS5000a",
                          proboter=proboter_1).save()

    # UART interface adapter
    await UartInterfaceAdapterConfig(
        usb_device_name="/dev/proboter_uart-interface",
        rx_multiplexer_channel_1=SignalMultiplexerChannel.ONE,
        rx_multiplexer_channel_2=SignalMultiplexerChannel.THREE,
        tx_multiplexer_channel_1=SignalMultiplexerChannel.TWO,
        tx_multiplexer_channel_2=SignalMultiplexerChannel.FOUR,
        proboter=proboter_1
    ).save()

    # Target power controller
    await TargetPowerControllerConfig(
        baud_rate=9600,
        usb_device_name="/dev/proboter_target-power-controller",
        proboter=proboter_1
    ).save()

    # Calibration board
    await ReferenceBoardConfig(name="Default (black)",
                               inner_brass_pin_width=11.95,
                               inner_brass_pin_height=19.95,
                               raised_brass_pin_width=59.6,
                               raised_brass_pin_height=39.9,
                               outer_white_pin_width=109.9,
                               outer_white_pin_height=89.8,
                               outer_brass_pin_width=109.9,
                               outer_brass_pin_height=89.8,
                               thickness=5.1,
                               marker_width=18.2,
                               marker_height=18.2,
                               marker_grid_width=60,
                               marker_grid_height=80).save()

    # Close the database connection
    await connections.close_all()
