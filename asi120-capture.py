#!/usr/bin/env python3

# Copyright 2026 Martin Junius
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ChangeLog
# Version 0.1 / 2026-06-28
#       Single capture script for PyZWOASI and ASI 120 MM

VERSION = "0.1 / 2026-06-28"
AUTHOR  = "Martin Junius"
NAME    = "asi120-test"
DESC    = "PyZWOASI capture for ASI120MM"

# Standard library
import sys
import argparse
import time

# Extra modules, not part of standard library, on Ubuntu install via apt-get or pip
import cv2
import numpy as np
import pyzwoasi
from pyzwoasi import ZWOCamera
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose import verbose, warning, error


TIME_FORMAT = "%Y-%m-%d %H:%M:%S UTC%z"


# Command line options
class Options:
    camera   = 0                # -c --camera
    gain     = 0                # -g --gain         0 ... 100
    offset   = 0                # -o --offset       0 ... 20
    exposure = 0.1              # -e --exposure
    binning  = 2                # -b --binning
    bandwith = 40               #                   40 ... 100
    image   = "image.jpg"       # -o --output



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = DESC,
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-c", "--camera", type=int, help=f"camera index (default: {Options.camera})")
    arg.add_argument("-g", "--gain", type=int, help=f"camera gain (default: {Options.gain})")
    arg.add_argument("-o", "--offset", type=int, help=f"camera offset (default: {Options.offset})")
    arg.add_argument("-b", "--binning", type=int, help=f"camera binning, 1 (1x1) or 2 (2x2) (default: {Options.binning})")
    arg.add_argument("-e", "--exposure", type=float, help=f"camera exposure time/s (default: {Options.exposure})")
    arg.add_argument("-i", "--image", type=str, help=f"image filename (default: {Options.image})")

    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info)
        ic(args)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()

    # Camera options
    if args.camera:
        Options.camera = args.camera
    if args.gain:
        Options.gain = args.gain
    if args.offset:
        Options.offset = args.offset
        warning("offset ignored!")
    if args.binning:
        Options.binning = args.binning
        if Options.binning != 1 and Options.binning != 2:
            error("argument -b/--binning: must be 1 or 2")
    if args.exposure:
        Options.exposure = args.exposure
        if Options.exposure <= 0:
            error("argument -e/--exposure: must be > 0")
    if args.image:
        Options.image = args.image

    # Check for ASI cameras
    n_cameras = pyzwoasi.getNumOfConnectedCameras()
    if (n_cameras == 0):
        error("No ASI cameras connected")
    for idx in range(0, n_cameras):
        verbose(f"camera {idx}: {pyzwoasi.getCameraProperty(idx).Name.decode('utf-8')}")
    if Options.camera < 0 or Options.camera >= n_cameras:
        error(f"camera index must be in range 0 ... {n_cameras-1}")

    # Only work with 1st camera (0)
    with ZWOCamera(Options.camera) as camera:
        camera.gain = Options.gain
        camera.softwareBinning = Options.binning

        # Extra .astype(np.uint8) to avoid error messages
        # -----------------------------------------------
        # cv2.error: OpenCV(5.0.0) :-1: error: (-5:Bad argument) in function 'putText'
        # > Overload resolution failed:
        # >  - img marked as output argument, but provided NumPy array marked as readonly
        # >  - Expected Ptr<cv::UMat> for argument 'img'
        imgdata = camera.shot(exposureTime_us = int(Options.exposure * 1e6), imageType=0) .astype(np.uint8)

        # Image data is a NumPy array
        ic(imgdata)

        # Evaluate data
        mean = np.average(imgdata)
        min  = np.min(imgdata)
        max  = np.max(imgdata)
        ic(mean, min, max)

        # add date
        font = cv2.FONT_HERSHEY_SIMPLEX
        # FIXME: position (360, 400) is very camera / binning specific!
        cv2.putText(imgdata, time.strftime(TIME_FORMAT), (360,460), font, .6, (255), 1, cv2.LINE_AA)

        cv2.imwrite(Options.image, imgdata)



if __name__ == "__main__":
    main()
