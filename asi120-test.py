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
#       Test script for PyZWOASI and ASI 120 MM

VERSION = "0.1 / 2026-06-28"
AUTHOR  = "Martin Junius"
NAME    = "asi120-test"
DESC    = "PyZWOASI test for ASI120MM"

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



# Command line options
class Options:
    camera   = "ZWO CCD ASI120MM"           # -c --camera
    gain     = 0                            # -g --gain         0 ... 100
    offset   = 0                            # -o --offset       0 ... 20
    exposure = 0.1                          # -e --exposure
    binning  = 2                            # -b --binning
    bandwith = 40                           #                   40 ... 100



def ic_camera(camera: ZWOCamera) -> None:
    ic(camera.imageType,
       camera.bufferSize,
       camera.exposure,
       camera.exposureLimits,
       camera.gain,
       camera.gainLimits,
       camera.softwareBinning,
       camera.hardwareBinning,
       camera.hardwareBinningLimits,
       camera.roi,
       camera.highSpeedMode,
       camera.bandwidth,
       camera.temperature,
       camera.cooler)
    ic(camera._dictControlType)

def ic_info() -> None:
    ic(pyzwoasi.getSDKVersion())
    info = pyzwoasi.getCameraProperty(0)
    ic( info.Name.decode('utf-8'),
        info.CameraID,
        info.MaxHeight,
        info.MaxWidth,
        bool(info.IsColorCam),
        info.BayerPattern,
        list(info.SupportedBins),
        info.SupportedVideoFormat,
        info.PixelSize,
        bool(info.MechanicalShutter),
        bool(info.ST4Port),
        bool(info.IsCoolerCam),
        bool(info.IsUSB3Host),
        bool(info.IsUSB3Camera),
        info.ElecPerADU,
        info.BitDepth,
        bool(info.IsTriggerCam),
    )



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = DESC,
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-g", "--gain", type=int, help="camera gain")
    arg.add_argument("-o", "--offset", type=int, help="camera offset")
    arg.add_argument("-b", "--binning", type=int, help="camera binning, 1 (1x1) or 2 (2x2)")
    arg.add_argument("-e", "--exposure", type=float, help="camera exposure time/s")

    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info)
        ic(args)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()

    # Camera options
    if args.gain:
        Options.gain  = args.gain
    if args.offset:
        Options.offset  = args.offset
        warning("offset ignored!")
    if args.binning:
        Options.binning  = args.binning
        if Options.binning != 1 and Options.binning != 2:
            error("argument -b/--binning: must be 1 or 2")
    if args.exposure:
        Options.exposure = float(args.exposure)
        if Options.exposure <= 0:
            error("argument -e/--exposure: must be > 0")


    # Check for ASI cameras
    n_cameras = pyzwoasi.getNumOfConnectedCameras()
    if (n_cameras == 0):
        error("No ASI cameras connected")
    ic_info()

    # Only work with 1st camera (0)
    with ZWOCamera(0) as camera:
        ic(camera)
        ic_camera(camera)
        camera.gain = Options.gain
        imgdata = camera.shot(exposureTime_us = int(Options.exposure * 1e6), imageType=0) 
        # Image data is a NumPy array
        ic(imgdata)

        # Evaluate data
        mean = np.average(imgdata)
        min  = np.min(imgdata)
        max  = np.max(imgdata)
        ic(mean, min, max)

        cv2.imwrite("image.jpg", imgdata)



if __name__ == "__main__":
    main()
