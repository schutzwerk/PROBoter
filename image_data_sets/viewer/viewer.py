#!/usr/bin/env -S pipenv run python
"""
Image data set viewer / downloader helper script
"""
import os
import json
import socket
import urllib
import logging
import zipfile
import argparse
from pathlib import Path
from typing import Dict, Any

import fiftyone as fo


log = logging.getLogger('main')


def download_data_set_images(data_set_dir: str) -> Dict[str, Any]:
    """
    Download data set images if required
    """
    # Load the data set labels
    label_file = Path(data_set_dir, 'labels.json').resolve()
    log.info('Loading COCO labels from file %s', label_file)
    with open(label_file, 'r', encoding='utf-8') as lbl_file:
        coco_data = json.loads(lbl_file.read())

    # Check for each image if it already exists or needs to be downloaded
    failed = []
    coco_images = coco_data['images']
    for idx, coco_image in enumerate(coco_images):
        image_url = coco_image['coco_url']
        image_file = Path(data_set_dir, coco_image['file_name'])
        # Check if the image must be downloaded
        if not image_file.exists():
            log.debug('Downloading image %s (%d / %d)',
                      image_file, idx + 1, len(coco_images))
            try:
                # Download the image
                with urllib.request.urlopen(image_url, None, 5) as response:
                    # Write to the destination file
                    with open(image_file, 'wb') as img_file:
                        img_file.write(response.read())
            except urllib.error.HTTPError as exc:
                log.error('Download of %s failed: HTTP error %d',
                          image_url, exc.code)
                failed.append(idx)
            except urllib.error.URLError:
                log.error('Download of %s failed: Invalid image URL',
                          image_url)
                failed.append(idx)
            except socket.timeout:
                log.error('Download of %s failed: Timeout',
                          image_url)
                failed.append(idx)

    # Remove failed images from the COCO data set in descending(!) order
    failed.reverse()
    for idx in failed:
        del coco_data['images'][idx]

    # Status update
    if len(failed) > 0:
        log.warning("%d images could not be downloaded", len(failed))

    return coco_data


def main():
    """
    CLI main function
    """
    # Logging setup
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(message)s",
                        force=True)
    logging.addLevelName(logging.DEBUG, "[*]")
    logging.addLevelName(logging.INFO, "[*]")
    logging.addLevelName(logging.WARNING, "[W]")
    logging.addLevelName(logging.ERROR, "[E]")

    # Parse the available data sets in COCO format
    current_dir = os.path.dirname(__file__)
    data_set_dir = os.path.join(current_dir, '../')
    data_sets = [f[:-4] for f in os.listdir(data_set_dir)
                 if os.path.isfile(os.path.join(data_set_dir, f))
                 and f.endswith('.zip')]

    # Parse the input arguments
    parser = argparse.ArgumentParser('PCB and pin data set viewer')
    parser.add_argument('dataset', type=str, choices=data_sets)
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose')
    args = parser.parse_args()

    # Adjust log level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(levelname)s %(message)s",
                            force=True)

    # Check if dataset directory exists
    selected_data_set_zip = os.path.join(data_set_dir, args.dataset + '.zip')
    selected_data_set_dir = os.path.join(data_set_dir, args.dataset)
    if not os.path.exists(selected_data_set_dir):
        # Create the data set directory
        log.info('Creating data set folder')
        os.mkdir(selected_data_set_dir)
        # Extract the data set
        log.info('Extracting data set')
        with zipfile.ZipFile(selected_data_set_zip, 'r') as zip_ref:
            zip_ref.extractall(selected_data_set_dir)

        # Download data set images if required
        coco_data = download_data_set_images(selected_data_set_dir)

        # Updating COCO data
        label_file = Path(selected_data_set_dir, 'labels.json')
        log.info("Updating COCO label data")
        with open(label_file, 'w', encoding='utf-8') as lbl_file:
            lbl_file.write(json.dumps(coco_data, indent=2))

    # Import the dataset
    dataset = fo.Dataset.from_dir(
        data_path=selected_data_set_dir,
        labels_path=os.path.join(selected_data_set_dir, 'labels.json'),
        dataset_type=fo.types.COCODetectionDataset
    )

    log.info('Starting viewer application')
    session = fo.launch_app(dataset)
    session.wait()


if __name__ == '__main__':
    main()
