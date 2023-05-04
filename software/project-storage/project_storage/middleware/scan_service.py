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

import logging

import cv2
import numpy as np

from project_storage.converter import PcbScanFile
from project_storage.image_merger import ImageMergerCpu
from project_storage.model import db, PcbScan, PcbScanImage

from .pcb_service import PcbService


class ScanService:
    """
    Service that provides operations manage PCB image scans

    PCB image scans can be loaded and saved. It is also possible to import
    existing scan files or create new ones with the PROBoter hardware platform.
    """

    log = logging.getLogger(__name__)

    @staticmethod
    def get_pcb_scans():
        """
        Return a list of all stored PCB scans
        """
        return PcbScan.query.all()

    @staticmethod
    def get_pcb_scan_by_id(scan_id: int):
        """
        Return a single PCB scan
        """
        return PcbScan.query.filter_by(id=scan_id).one()

    @staticmethod
    def get_pcb_scans_by_pcb_id(pcb_id: int):
        """
        Return a list of PCB scan ids associated with pcb
        with id pcb_id
        """
        result = PcbScan.query.filter_by(pcb_id=pcb_id).all()
        return result

    @classmethod
    def delete_pcb_scan_by_id(cls, scan_id: int):
        """
        Delete a PCB scan and all of it's images from the storage
        """
        cls.log.info("Deleting PCB scan with ID %d", scan_id)
        scan = PcbScan.query.filter_by(id=scan_id).one()
        db.session.delete(scan)
        db.session.commit()

    @classmethod
    def create_or_update_scan(cls, scan: PcbScan) -> PcbScan:
        """
        Create a new PcbScan or update an existing one

        :param scan: PcbScan to create or update
        :type scan: PcbScan
        :return: The newly created or updated scan
        :rtype: PcbScan
        """
        if scan.id is None:
            cls.log.info("Creating new PcbScan")
        else:
            cls.log.info("Updating PCB scan with ID %d", scan.id)

        # Update the scan preview image
        cls._update_scan_preview(scan)

        db.session.add(scan)
        db.session.commit()

        return scan

    @classmethod
    def create_or_update_scan_image(
            cls, scan_image: PcbScanImage) -> PcbScanImage:
        """
        Create a new Pcb scan image or update an existing one

        :param scan_image: Pcb scan image to create or update
        :type scan_image: PcbScanImage
        :return: The newly created or updated scan image
        :rtype: PcbScanImage
        """
        if scan_image.id is None:
            cls.log.info("Creating new Pcb scan image")
        else:
            cls.log.info("Updating PCB scan with image ID %d", scan_image.id)

        # Save the PCB scan image
        db.session.add(scan_image)
        db.session.commit()

        # Update the scan preview image
        cls._update_scan_preview(scan_image.scan)

        return scan_image

    @staticmethod
    def get_merged_pcb_scan_image(scan_id: int,
                                  resolution: float = 0.01) -> np.ndarray:
        """
        Generate a merged image of all images
        contained in a PCB scan

        :param scan_id: Unique identifier of the scan to merge
        :type scan_id: int
        :return: The merged image
        :rtype: np.ndarray
        """
        # Fetch the scan from the database
        scan = PcbScan.query.filter_by(id=scan_id).one()

        # Merge the scan images
        merger = ImageMergerCpu()
        final_image = merger.merge_scan(scan, resolution)

        return final_image

    @staticmethod
    def get_individual_pcb_scan_image(
            scan_id: int, scan_image_id: int) -> np.ndarray:
        """
        Return the image data of an individual PCB scan image

        :param scan_id: Unique identifier of the scan
        :type scan_id: int
        :param scan_image_id: Unique identifier of the scan image
        :type scan_image_id: int
        :return: Image data of the scan image
        :rtype: np.ndarray
        """
        scan_image = PcbScanImage.query.filter_by(
            id=scan_image_id, scan_id=scan_id).one()
        return scan_image.image_data

    @staticmethod
    def get_pcb_scan_preview(scan_id: int) -> np.ndarray:
        """
        Generate a preview from the merged images
        contained in a scan.

        :param scan_id: Unique identifier of the scan to merge
        :type scan_id: int
        :return: The merged image
        :rtype: np.ndarray
        """
        scan = PcbScan.query.filter_by(id=scan_id).one()
        return scan.preview_image_data

    @classmethod
    def import_pcb_scan_from_file(cls, pcb_id: int, scan_file: str) -> PcbScan:
        """
        Import a PCB scan from an exported scan archive

        :param pcb_id: The id of the pcb this scan is associated with
        :type pcb_id: int
        :param scan_file: File like object to import
        :type scan_file: object
        :return: The imported PCB scan
        :rtype: PcbScan
        :raise ScanFileFormatException: If the scan file contains invalid data
        """
        cls.log.info('Importing PCB image file')
        scan = PcbScanFile.read_from_zip(scan_file)
        scan.pcb_id = pcb_id

        # Persist the new scan
        cls.create_or_update_scan(scan)

        return scan

    @classmethod
    def export_pcb_scan_to_file(cls, scan_id, file_io) -> None:
        """
        Export a single PCB scan and all it's images to a ZIP file

        :param scan_id: Unique identifier of the PCB scan to export
        :type scan_id: int
        :param file_obj: The file-like object the data will be written to
        :type file_obj: object
        """
        cls.log.info("Exporting PCB scan %d", scan_id)

        # Fetch the corresponding PCB scan
        scan = PcbScan.query.filter_by(id=scan_id).one()

        # Export as Zip file
        PcbScanFile.export_to_zip_file(scan, file_io)
        cls.log.info("Zip file export of PCB scan %d finished", scan.id)

    @classmethod
    def make_preview_from_scan(cls, scan: PcbScan,
                               max_dim: int = 480) -> np.ndarray:
        """
        Generates a PCB scan preview image

        :param scan: PCB scan
        :type scan: PcbScan
        :param max_dim: The max. dimension of the generated preview image.
                        The PCB scan is resized so that the largest image dimension
                        has the size of this parameter.

        """
        cls.log.info('Generating PCB scan preview image')
        merger = ImageMergerCpu()
        # A resolution of 0.1 mm/pixel should be enough for a preview image
        merged_scan = merger.merge_scan(scan, 0.1)

        return cls.scale_to_max(merged_scan, max_dim)

    @staticmethod
    def scale_to_max(image: np.ndarray, max_dim: int) -> np.ndarray:
        """
        Scales an image so that it's largest dimension
        has a defined value.

        :param image: The image to scale.
        :param max_dim: The size of the largest dimension after rescaling.
        :return: The rescaled image.
        """
        scale = max_dim / max(image.shape[0], image.shape[1])
        new_shape = (int(image.shape[1] * scale), int(image.shape[0] * scale))
        return cv2.resize(image, new_shape)

    @classmethod
    def _update_scan_preview(cls, scan: PcbScan) -> None:
        """
        Update the preview image of a PCB scan

        :param scan: PCB scan to update
        :type scan: PcbScan
        """
        cls.log.info("Updating preview image of scan")

        # Update the scan preview image
        if len(scan.images) > 0:
            preview = cls.make_preview_from_scan(scan, 200)
        else:
            preview = np.zeros((200, 200, 3), dtype=np.uint8)

        scan.preview_image_data = preview
        scan.preview_image_width = preview.shape[1]
        scan.preview_image_height = preview.shape[0]
        scan.preview_image_channels = preview.shape[2]

        db.session.add(scan)
        db.session.commit()

        # Check if the scan is the only one belonging to the PCB
        # If this is the case, the PCB preview image is also updated
        pcb = PcbService.get_pcb_by_id(scan.pcb_id)
        cls.log.info("PCB scans: %d", len(pcb.scans))
        if len(pcb.scans) == 1:
            PcbService.update_pcb_preview_image(pcb, preview)
