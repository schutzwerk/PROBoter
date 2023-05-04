# Copyright (C) 2022 SCHUTZWERK GmbH
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

import json
import logging
from zipfile import ZipFile, ZIP_DEFLATED

import cv2
import schema
import numpy as np

from project_storage.model import PcbScan, PcbScanImage
from .validators import to_np_array, to_datetime


class PcbScanFileFormatException(Exception):
    """
    Exception that is raised if the file format
    of a PCB scan is invalid
    """


class PcbScanFile:
    """
    Allows the import of previously exported PCB scans
    """

    log = logging.getLogger(__name__)

    DATE_TIME_FORMAT = '%m/%d/%Y %H:%M:%S'

    SCAN_IMAGE_SCHEMA = schema.Schema({
        'created': to_datetime(DATE_TIME_FORMAT),
        'width': int,
        'height': int,
        'channels': int,
        'tmat': to_np_array((4, 4), dtype=np.float32),
        'camera-matrix': to_np_array((3, 3), dtype=np.float32),
        'depth-map': to_np_array((-1, -1), dtype=np.float32),
        'z-offset': float,
        'file': str
    })

    SCAN_DATA_SCHEMA = schema.Schema({
        schema.Optional('version', default='1.0'): str,
        'name': str,
        'created': to_datetime(DATE_TIME_FORMAT),
        'x-min': float,
        'x-max': float,
        'y-min': float,
        'y-max': float,
        'images': [SCAN_IMAGE_SCHEMA]
    }, ignore_extra_keys=True)

    @classmethod
    def read_from_zip(cls, scan_file: str) -> PcbScan:
        """
        Read a previously exported PCB scan from a Zip file

        :param scan_file: Filename or file-like object to parse
        :type scan_file: str
        :raises PcbScanFileFormatException: If the scan file does not exist
        :raises PcbScanFileFormatException: If the scan file format is invalid
        :raises PcbScanFileFormatException: If a scan image file does not exist
        :return: The imported PCB scan
        :rtype: PcbScan
        """
        with ZipFile(scan_file, 'r') as zfile:
            # Check for the scan data file
            file_list = zfile.namelist()
            if not 'scan.json' in file_list:
                raise PcbScanFileFormatException('Missing scan data file')

            # Load the scan data
            try:
                scan_data = json.loads(zfile.read('scan.json'))
                scan_data = cls.SCAN_DATA_SCHEMA.validate(scan_data)
            except (schema.SchemaError, json.JSONDecodeError):
                raise PcbScanFileFormatException('Invalid scan data') from None

            # Create the PCB scan
            cls.log.info("Found valid PCB image scan '%s'", scan_data['name'])
            pcb_scan = PcbScan(name=scan_data['name'],
                               created=scan_data['created'],
                               x_min=scan_data['x-min'],
                               x_max=scan_data['x-max'],
                               y_min=scan_data['y-min'],
                               y_max=scan_data['y-max'])

            # Import the scan images
            for i, img_data in enumerate(scan_data['images']):
                cls.log.info("Importing scan image %d of %d",
                             i + 1, len(scan_data['images']))

                # Load the image data
                if not img_data['file'] in zfile.namelist():
                    raise PcbScanFileFormatException(
                        f'Image file {img_data["file"]} not found')

                raw_image = zfile.read(img_data['file'])
                nparr = np.fromstring(raw_image, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # Create the scan image
                pcb_img = PcbScanImage(
                    created=img_data['created'],
                    image_data=img,
                    image_width=img.shape[1],
                    image_height=img.shape[0],
                    image_channels=img.shape[2],
                    tmat=np.array(img_data['tmat']),
                    camera_matrix=np.array(img_data['camera-matrix']))

                pcb_scan.images.append(pcb_img)

        return pcb_scan

    @classmethod
    def export_to_zip_file(cls, scan: PcbScan, file_obj: str) -> None:
        """
        Export a single PCB scan and all it's images to a ZIP file

        :param scan_id: Unique identifier of the PCB scan to export
        :type scan_id: int
        :param file_obj: The file-like object the data will be written to
        :type file_obj: object
        """
        # Create the output file
        with ZipFile(file_obj, 'w', ZIP_DEFLATED) as zfile:
            # Set the filename
            zfile.filename = f'scan_{scan.id}.zip'

            # Meta information
            meta_info = {'version': '1.0',
                         'name': scan.name,
                         'created': scan.created.strftime(cls.DATE_TIME_FORMAT),
                         'x-min': scan.x_min,
                         'x-max': scan.x_max,
                         'y-min': scan.y_min,
                         'y-max': scan.y_max,
                         'images': []
                         }

            # Append the scan images
            for i, scan_img in enumerate(scan.images):
                cls.log.debug("Exporting scan image %d of %d",
                              i + 1, len(scan.images))
                # Save the image data
                scan_img: PcbScanImage = scan_img
                _, encoded_img = cv2.imencode('.png', scan_img.image_data)
                img_file = f'{i}.png'
                zfile.writestr(img_file, encoded_img)

                # Append the image metadata
                meta_info['images'].append(
                    {
                        'created': scan.created.strftime(cls.DATE_TIME_FORMAT),
                        'width': scan_img.image_width,
                        'height': scan_img.image_height,
                        'channels': scan_img.image_channels,
                        'tmat': scan_img.tmat.tolist(),
                        'camera-matrix': scan_img.camera_matrix.tolist(),
                        'z-offset': scan_img.z_offset,
                        'file': img_file
                    })

            # Write the combined meta data
            zfile.writestr('scan.json', json.dumps(meta_info))
