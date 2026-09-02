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
# Version 0.1 / 2026-09-01
#       Looping auto capture script for PyZWOASI and ASI120MM

VERSION = "0.1 / 2026-09-01"
AUTHOR  = "Martin Junius"
NAME    = "asi120-auto"
DESC    = "PyZWOASI auto capture webcam for ASI120MM"

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

# Max numbers of auto-exposure attempts
MAXTRY  = 15
# Expected mean ADU (0..255) and allowed deviation
MEANADU = 128
DEVADU  = 20
EXPOSURE_THRESHOLD = int(1.0 * 1e6) # us

# ASI120MM
#   gain 1 ... 29
#   offset 1 ... 512; +100 -> ~+25 ADU min value
#   exposure 0.000001 ... 3600 s
MINGAIN   = 0
MAXGAIN   = 100
STEPGAIN  = 20
MINOFFSET = 0
MAXOFFSET = 20
MINEXP    = int(0.000001 * 1e6)     # us
MAXEXP    = int(8 * 1e6)            # us


# Command line options
class Options:
    camera   = 0                # -c --camera
    gain     = 0                # -g --gain         0 ... 100
    offset   = 0                # -o --offset       0 ... 20
    exposure = 0.1              # -e --exposure
    binning  = 2                # -b --binning
    bandwith = 40               #                   40 ... 100
    image   = "image.jpg"       # -o --output



def write_image(camera, imgdata):
    exposure = camera.exposure / 1e6
    gain = camera.gain

    # Remove hot pixels
    imgdata = cv2.medianBlur(imgdata, 3)

    # Normalize to 0 .. 255
    imgdata = cv2.normalize(imgdata, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # add date and exposure/gain
    height, width = imgdata.shape
    font = cv2.FONT_HERSHEY_SIMPLEX
    txt  = f"{time.strftime(TIME_FORMAT)}           {exposure:.2g}s (Gain {gain:d})"
    cv2.putText(imgdata, txt, (20, height-20), font, 1.2/Options.binning, (255), 1, cv2.LINE_AA)

    cv2.imwrite(Options.image, imgdata)



def init_camera(camera):
    camera.exposure = int(Options.exposure * 1e6)
    camera.gain = Options.gain
    camera.softwareBinning = Options.binning



def single_exposure(camera):
    # Extra .astype(np.uint8) to avoid error messages
    # -----------------------------------------------
    # cv2.error: OpenCV(5.0.0) :-1: error: (-5:Bad argument) in function 'putText'
    # > Overload resolution failed:
    # >  - img marked as output argument, but provided NumPy array marked as readonly
    # >  - Expected Ptr<cv::UMat> for argument 'img'
    imgdata = camera.shot(exposureTime_us = camera.exposure, imageType=0) .astype(np.uint8)

    ic(imgdata)
    return imgdata



def auto_exposure(camera):
    count = MAXTRY
    low = MEANADU - DEVADU
    high = MEANADU + DEVADU
    imgdata = None
    last_exp_inc = False
    last_exp_dec = False
    last_gain_inc = False
    last_gain_dec = False
    last_exp = 0

    while count > 0:
        ic("--- ITERATION ---")
        ic(count, camera.gain, camera.exposure)
        count -= 1

        imgdata = single_exposure(camera)
        mean = np.average(imgdata)
        min = np.min(imgdata)
        ic(low, high, mean, min)
        height, width = imgdata.shape
        verbose(f"image: {width}x{height}, avg={mean:.1f}, min={min}")

        if mean >= high:
            # exposure too bright
            if camera.exposure <= EXPOSURE_THRESHOLD and camera.gain > MINGAIN and not last_gain_inc:
                # decrease gain
                camera.gain -= STEPGAIN
                if camera.gain < MINGAIN: camera.gain = MINGAIN
                last_gain_dec = True
            else:
                # decrease exposure time
                if camera.exposure <= MINEXP:
                    camera.exposure = MINEXP # just to be sure
                    ic("already at MINEXP")
                    break;
                new_exp = camera.exposure * MEANADU/mean
                if new_exp < MINEXP:
                    new_exp = MINEXP
                camera.exposure = int(new_exp)
                last_exp_dec = True
                last_gain_dec = False
            ic("too bright, new exposure:")
            ic(camera.exposure, camera.gain)
        elif mean <= low:
            # exposure too dark
            if camera.exposure >= EXPOSURE_THRESHOLD and camera.gain < MAXGAIN and not last_gain_dec:
                # increase gain
                camera.gain += STEPGAIN
                if camera.gain > MAXGAIN: camera.gain = MAXGAIN
                last_gain_inc = True
            else:
                # increase exposure time
                if camera.exposure >= MAXEXP:
                    camera.exposure = MAXEXP # just to be sure
                    ic("alreay at MAXEXP")
                    break;
                new_exp = camera.exposure * MEANADU/mean
                if new_exp > MAXEXP:
                    new_exp = MAXEXP
                camera.exposure = int(new_exp)
                last_gain_inc = False
                last_exp_inc  = True
            ic("too dark, new exposure:")
            ic(camera.exposure, camera.gain)
        else:
            # exposure ok
            ic("ok, saving image")
            break

    verbose(f"auto-exposure {camera.exposure/1e6:.3g}s gain={camera.gain} mean={mean:.0f}")
    write_image(camera, imgdata)



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
    arg.add_argument("-l", "--loop", type=float, help=f"loop exposure, interval LOOP s")

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
        init_camera(camera)

        if args.loop:
            loop = args.loop
            verbose(f"looping exposure every {loop} s ... Crtl-C to interrupt")
            try:
                # looping exposure
                while True:
                    t1 = time.perf_counter()
                    auto_exposure(camera)
                    t2 = time.perf_counter()
                    sleep = loop - (t2 - t1)
                    if(sleep > 0):
                        time.sleep(sleep)
            except KeyboardInterrupt:
                # Catch Ctrl-C
                verbose("looping interrupted, terminating")
                pass
        else:
            auto_exposure(camera)



if __name__ == "__main__":
    main()
