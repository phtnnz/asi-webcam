# INDI Python Utils

Python scripts for image capture with ZWO ASI cameras, currently tailored ASI 120 MM

Copyright 2026 Martin Junius

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


## References

Based on the following code examples for PyIndi:

https://github.com/indilib/pyindi-client/tree/master/examples \
https://github.com/jkoenig72/indiCapture


## Installation

On Linux Ubuntu (Server) 22.04 LTS, Python 3.10

The following system-wide packages must be installed:
```
sudo apt-get install python-is-python3
sudo apt-get install python3-icecream
```

Optionally, INDI can be installed for testing the camera, I didn't get PyIndi to work with the ASI 120 MM, though.
```
sudo apt-add-repository ppa:mutlaqja/ppa
sudo apt-get update
sudo apt-get install libindi1 indi-bin
sudo apt-get install indi-qhy
sudo apt-get install indi-asi
sudo apt-get install python3-indi-client
```

TBD: these packages will be updated by pip, see below?
```
sudo apt-get install python3-opencv
sudo apt-get install python3-numpy
```

For native control of ASI camera install the PyZWOASI package, the one at PyPI seems to be outdated.
```
pip install ./packages/pyzwoasi-0.2.6-py3-none-any.whl
```

### ASI 120 MM

#### Firmware !!! ###

The ASI 120 MM camera will only work with Linux if the "compatibility" firmware is installed. Alas, the corresponding download is no longer available from ZWO. The updater ```FWupdate_V1.0.exe``` and firmware ```ASI120MM-compatible.iic``` are required. See [here](./ASI120-links.txt) for possible sources on the Web, the download you want is ```FWUpdate_Windows_v1.1.zip```

```
> lsusb
[...]
Bus 001 Device 006: ID 03c3:120a ZWOptical company   ASI120MM
[...]

```

Optionally, if INDI is installed
```
> asi_camera_test
[...]

> indiserver -v indi_asi_ccd
[...]
```

If ```asi_camera_test``` throws errors (core dump), then the compatibilty firmware (see above) isn't installed.
If successful, the test program will write the image file ```image_001.raw```, use
```
> convert -size 1280x960 -depth 8 gray:image_001.raw image_001.png
```
to convert the raw file to a viewable PNG (ImageMagick must be installed).


#### Debugging ####

Extra debug output of the ZWO ASI SDK can be enabled by editing the File ```~/.ZWO/ASIconfig.xml``` and setting
```
<DebugPrint type="3">01</DebugPrint>
```
(```01``` debug, ```00``` no debug)

Logfiles can be found under ```~/.ZWO/asicamerasdk/```.


#### INDI Config ####

ASI 120 MM camera specific configuration can be found here ```~/.indi/ZWO CCD ASI120MM_config.xml```
