# DIY Thermal Camera #

This is a simple thermal camera that can be built using off-the-shelf parts
from Adafruit (albeit with a long lead time due to component shortages).

[Reddit post about it](https://www.reddit.com/r/functionalprint/comments/nfmj6n/diy_thermal_camera/)

## BOM ##

* [Adafruit 1.3" PiTFT Bonnet](https://www.adafruit.com/product/4506)
* [Raspberry Pi Zero W](https://www.adafruit.com/product/3400)
  * You'll want with headers if you don't have any you can solder yourself
* [MLX90640 IR Thermal Camera](https://www.adafruit.com/product/4407)
* [MicroSD card](https://www.adafruit.com/product/2820)
* [StemmaQT cable](https://www.adafruit.com/product/4210)

## Features ##

* Auto-start at boot
  * This software runs on a Raspberry Pi Zero W, as a result it needs to boot.
    When it boots, it automatically starts up via systemd
* Freeze frame
  * Pause capturing to examine the current frame, all view settings can be
    manipulated to look at individual pixel temperatures, adjust corrections,
    scales, etc.
* Capture to PNG
  * Saves images to `~pi/thermal-images`
* MTP support for transferring images
  * Exposes `~pi/thermal-images` over MTP for Windows,
    macOS (Android File Transfer) and Linux machines
* Selectable temperature ranges
  * Available temperature ranges are: auto-range (min, max),
    outdoor body detection (10-32C), indoor body detection (20-32C), hot spot
    identification (20-50C), and extremes (-10 - 200C)
* Switchable C/F temperature scale
* Adjustable emissivity correction
  * Adjustable from 0.05 to 1.00 in 0.05 increments. Default at 0.95
* Movable reticle showing temperature under the crosshairs
* Four lockable reticle points for indicating temperature
  * Temperature at 7 points can be tracked in real time: under the reticle, at
    the four locked reticle points, and the min and max points
* Switchable color range (Gnuplot PM3D, and a basic rainbow)
* Display of estimated ambient temparture
  * This can be warmer than ambient, depending on the temperature of the Pi
    inside the case.

### Controls ###

* Hold A (left button) and then B (right) together at the same time to exit
* Hold B and then A together at the same time to change the scale palette
  to PM3D or rainbow
* Press A by itself to freeze-frame, press again to release freeze-frame
* Press B by itself to toggle the temperature units between C and F
* Press U(p), L(eft), R(ight), D(own) by themselves to move the center reticle
* Hold B and press U to adjust emissivity correction up by 0.05
* Hold B and press D to adjust emissivity correction down by 0.05
* Hold B and press L or R to scroll through temperature ranges
* Press C(enter) by itself to lock a reticle location for temperature readout
* Hold B and press C to clear all selected reticle locations
* Hold A and press C to save the current screen to disk as PNG

## Instructions ##

This solution involves installing software from raspbian packages, python3
packages using `venv` and `pip`, and some locally compiled components
[uMTP-Responder](https://github.com/viveris/uMTP-Responder)

In addition to software, there is minimal hardware assembly and 3D printed
parts.

### Software ###

* $ `sudo apt install python3-venv`
* $ `python3 -m venv --system-site-packages ~/src/thermal-imaging`
* $ `cd ~/src && git clone https://github.com/pfn/thermal-camera thermal-imaging`
* $ `cd ~/src/thermal-imaging/bin`
* $ `./pip install ST7789`
* $ `./pip install mlx90640-driver`
* $ `./pip install mlx90640-driver-devicetree`
* $ `./pip install colour`
* $ `./pip install pillow`
* $ `./pip install RPi.GPIO`
* $ `sudo mkdir /etc/umtprd`
* $ `sudo cp ../conf/umtprd.conf /etc/umtprd/`
* $ `sudo cp ../conf/thermal-camera.service /etc/systemd/system/`
* $ `sudo cp ../conf/umtp-responder.service /etc/systemd/system/`
* $ `ln -s armv7l ../lib/python3.7/site-packages/mlx90640/libs/armv6l`
* $ `ln -s armv7l ../lib/python3.7/site-packages/mlx90640_devicetree/libs/armv6l`
* $ `cd ~/src && git clone https://github.com/viveris/uMTP-Responder`
* $ `cd uMTP-Responder && make`
* Add `dtoverlay=dwc2` to the bottom of `/boot/config.txt`
* $ `sudo systemctl enable thermal-camera`
* $ `sudo systemctl enable umtp-responder`
* Reboot the Pi


For any missing packages, `sudo apt install` them as appropriate.

### Hardware ###

Print 2x of the buttons, 4x of the spacers, the top and bottom of the case.

Solder headers onto the Pi if necessary.

Attach the StemmaQT cable to the camera and TFT bonnet.

Place the Pi into the bottom of the case. And place the 4 spacers onto the
nubs that protrude through the Pi.

Press the TFT bonnet down into place onto the Pi.

Position the camera on the bottom of the case and place the lens through the
hole.

Put the top of the case onto a flat surface, and put the buttons into the
button holes.

Run a bead of super glue around the edges and press the case together.

All done!
