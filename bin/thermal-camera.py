#!/home/pi/src/thermal-imaging/bin/python

save_path = "/home/pi/thermal-images"

# Imports take a while to execute, so interleave them as used
import os

import ST7789 as ST7789
disp = ST7789.ST7789(
  port=0,
  cs=ST7789.BG_SPI_CS_BACK,  # BG_SPI_CS_BACK or BG_SPI_CS_FRONT
  dc=25,
  backlight=26,               # 18 for back BG slot, 19 for front BG slot.
  spi_speed_hz=80 * 1000 * 1000,
  offset_left=0
)
disp.begin()
width = disp.width
height = disp.height

from PIL import Image, ImageDraw, ImageFont
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

def clear_screen(f=(0, 0, 0)):
    draw.rectangle((0, 0, width, height), outline=f, fill=f)
    disp.display(image)

clear_screen((0, 255, 255))

font_name = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FH = 16
fnt = ImageFont.truetype(font_name, FH)
caretfnt = ImageFont.truetype(font_name, FH * 2)
WHITE = (255, 255, 255)
line_number = 0

def init_text(text):
    global line_number
    draw.text((5, 5 + line_number * (FH + 2)), text, font=fnt, fill=WHITE)
    line_number += 1
    disp.display(image)

clear_screen()
init_text("Display initialized")

import RPi.GPIO as GPIO

import mlx90640
dev = mlx90640.MLX90640()
dev.i2c_init("/dev/i2c-1")
dev.set_refresh_rate(4)

init_text("Camera found")

# auto, FLIR default, indoor mammals, hot spots, extremes
ranges = ((0.0, 0.0), (10.0, 32.22),
        (20.0, 32.0), (20.0, 50.0), (-10.0, 200.0))

# globals used by button_press callback
freeze_frame = False
temp_range = 0
chordA = False
chordB = False
isF = False
emissivity = 0.95 # emissivity correction
reticle = int(768 / 2 - 16)
selected = list() 

import re
file_pattern = re.compile(r"image(\d{4}).png")

import functools
flatmap = lambda f, xs: [y for ys in xs for y in f(ys)]

def image_ordinal(f):
    if not os.path.isfile(os.path.join(save_path, f)):
        return ()
    m = re.match(file_pattern, f)
    return [int(m.group(1))] if m is not None else ()

def next_ordinal():
    return max([0] +
            [x for x in flatmap(image_ordinal, os.listdir(save_path))]) + 1

def save_image():
    global saving
    global is_dirty
    os.makedirs(save_path, exist_ok=True)
    saving = True
    is_dirty = False
    image.save("%s/image%04d.png" % (save_path, next_ordinal()))
    saving = False

colors = []
scale = []

# button pin assignments
A = 5
B = 6
L = 27
R = 23
U = 17
D = 22
C = 4
def button_press(x):
    global chordA
    global chordB
    global isF
    global emissivity
    global reticle
    global selected
    global temp_range
    global freeze_frame
    global is_dirty
    global scale
    global colors

    if not (x == A and chordA or x == B and chordB):
        is_dirty = True

    if x == A and not chordA:
        if GPIO.input(B) == 0:
            chordB = True
            colors = pm3d_colors if colors is not pm3d_colors else rainbow_colors
            scale = pm3d_scale if scale is not pm3d_scale else rainbow_scale
        else:
            freeze_frame = not freeze_frame
    else:
        chordA = False

    if x == B and not chordB:
        if GPIO.input(A) == 0:
            chordA = True
            clear_screen()
            disp.set_backlight(0)
            exit()
        else:
            isF = not isF
    else:
        chordB = False

    if x == U:
        if GPIO.input(B) == 0:
            chordB = True
            emissivity = min(emissivity + 0.05, 1.00)
        else:
            reticle = max(reticle - 32, 0)
    if x == D:
        if GPIO.input(B) == 0:
            chordB = True
            emissivity = max(emissivity - 0.05, 0.05)
        else:
            reticle = min(reticle + 32, 768)
    if x == L:
        if GPIO.input(B) == 0:
            temp_range = max(0, temp_range - 1)
            chordB = True
        else:
            reticle = min(reticle + 1, 768)
    if x == R:
        if GPIO.input(B) == 0:
            temp_range = min(len(ranges) - 1, temp_range + 1)
            chordB = True
        else: 
            reticle = max(reticle - 1, 0)
    if x == C:
        if GPIO.input(B) == 0:
            chordB = True
            if freeze_frame:
                # capture image to disk
                pass
            else:
                selected = []
        elif GPIO.input(A) == 0:
            chordA = True
            save_image()
        else:
            if reticle in selected:
                selected.remove(reticle)
            else:
                selected.append(reticle)
            while len(selected) > 4:
                del selected[0]

GPIO.setmode(GPIO.BCM)
for pin in [A, B, L, R, U, D, C]:
    GPIO.setup(pin, GPIO.IN)
    GPIO.add_event_detect(pin, GPIO.RISING)
    GPIO.add_event_callback(pin, button_press)

init_text("Buttons configured")

import math
def pm3d(steps):
    def _pm3d(x):
        r = round(255 * math.sqrt(x))
        g = round(255 * math.pow(x, 3))
        b = round(255 * max(math.sin(2 * math.pi * x), 0))
        return (int(r) | int(g) << 8 | int(b) << 16)
    return [x for x in map(lambda _x: _pm3d(_x / steps), range(0, steps))]

from colour import Color
rainbow_colors = list(Color('indigo').range_to(Color('red'), 256))
rainbow_colors = [(int(c.red * 255) | int(c.green * 255) << 8 |
    int(c.blue * 255) << 16) for c in rainbow_colors]
pm3d_colors = pm3d(256)

rainbow_scale = list(Color('red').range_to(Color('indigo'), 144 - 2 * FH - 4))
rainbow_scale = [(int(c.red * 255) | int(c.green * 255) << 8 |
    int(c.blue * 255) << 16) for c in rainbow_scale]

pm3d_scale = pm3d(144 - 2 * FH - 4)
pm3d_scale.reverse()

scale = pm3d_scale
colors = pm3d_colors

init_text("Palettes initialized")

def is_autorange():
    return ranges[temp_range][0] == ranges[temp_range][1]

def range_max(n):
    return n if is_autorange() else ranges[temp_range][1]

def range_min(n):
    return n if is_autorange() else ranges[temp_range][0]

def draw_scale(draw, min_temp, max_temp):
    for (r,x) in enumerate(scale):
        draw.line((8, r + FH + 2, 24, r + FH + 2), fill=x)

    # scale
    draw.text((0, 0), "%.1f\u00b0" % display_unit(range_max(max_temp)),
            font=fnt, fill=WHITE)
    draw.text((0, 144 - FH), "%.1f\u00b0" % display_unit(range_min(min_temp)),
            font=fnt, fill=WHITE)


P = 6 # pixel sampling size

subscripts = ["\u2081", "\u2082", "\u2083", "\u2084", "\u2085", "\u2086"]
def draw_reticle(draw):
    for (i,r) in enumerate(selected):
        y = r / 32
        x = r % 32
        draw.line((P * (31 - x) + 48, P * y + 6,
            P * (31 - x) + P + 48, P * y + 6),
                fill=WHITE)
        draw.line((P * (31 - x) + 48 + 6, P * y,
            P * (31 - x) + 48 + 6, P * y + P),
                fill=WHITE)
        draw.line((P * (31 - x) + 48, P * y,
            P * (31 - x) + P + 48, P * y),
                fill=WHITE)
        draw.line((P * (31 - x) + 48, P * y,
            P * (31 - x) + 48, P * y + P),
                fill=WHITE)
        draw.text((P * (31 - x) + 48 + P, P * y - P / 2),
                subscripts[i], font=fnt, fill=WHITE)
    y = reticle / 32
    x = reticle % 32
    draw.line((P * (31 - x) + 48, P * y + 3, P * (31 - x) + P + 48, P * y + 3),
            fill=WHITE)
    draw.line((P * (31 - x) + 48 + 3, P * y, P * (31 - x) + 48 + 3, P * y + P),
            fill=WHITE)

def draw_minmax(min_pt, max_pt):
    for (i, p) in enumerate((min_pt, max_pt)):
        y = p / 32
        x = p % 32
        draw.text((P * (31 - x) + 48 - FH / 4, P * y - FH / 2),
                "\u02c5" if i == 0 else "\u02c4", font=caretfnt,
                fill=WHITE if i == 0 else (50, 50, 50))

selected_locations = [(0, 204), (0, 224), (120, 204), (120, 224)]

def draw_selected(draw, frame):
    for i in range(0, len(selected)):
        draw.text(selected_locations[i], "+%s = %.1f\u00b0" %
                (subscripts[i], display_unit(frame[selected[i]])),
                font=fnt, fill=WHITE)

def display_unit(measurement):
    if not isF:
        return measurement
    else:
        return (measurement * 9/5) + 32

def clamp(x, in_min, in_max):
    return max(in_min, min(x, in_max))

def map_value(x, in_min, in_max, out_min, out_max):
    return int((clamp(x, in_min, in_max) - in_min) * (out_max - out_min) /
            (in_max - in_min) + out_min)

is_dirty = True
saving = False
def freeze_frame_status():
    marker = "\u03a3" if saving else ("*" if is_dirty else "\u2713")
    draw.text((width - FH, height - FH), marker, font=fnt, fill=WHITE)

def analyze_px(acc, px):
    min_temp = min(acc[0], px[1])
    max_temp = max(acc[1], px[1])
    min_pt = px[0] if min_temp != acc[0] else acc[2]
    max_pt = px[0] if max_temp != acc[1] else acc[3]
    return (min_temp, max_temp, min_pt, max_pt)

def render(frame, ta):
    (min_temp, max_temp, min_pt, max_pt) = functools.reduce(
            analyze_px, enumerate(frame), (999, -999, 0, 0))
    pixels = list(map(lambda x: colors[map_value(x,
        range_min(min_temp), range_max(max_temp), 0, len(colors) - 1)], frame))

    for x in range(0, 32):
        for y in range(0, 24):
            c = pixels[y * 32 + x]
            draw.rectangle((
                (31 - x) * P + 48,
                y * P,
                (31 - x) * P + P + 48,
                y * P + P
                ), outline=c, fill=c)
    # clear the bottom box
    draw.rectangle((0, 144, 240, 240), outline=0, fill=0)
    # clear the vertical column
    draw.rectangle((0, 0, 48, 240), outline=0, fill=0)

    #draw.text((120, 152), "\u03b5 = %0.2f" % emissivity, font=fnt, fill=WHITE)
    draw.text((96, 152), "Ta = %.1f\u00b0" % display_unit(ta),
            font=fnt, fill=WHITE)

    draw.text((200, 152), "\u00b0 = %s" % ("F" if isF else "C"),
            font=fnt, fill=WHITE)
    draw.text((0, 152), "+ = %.1f\u00b0" % display_unit(frame[reticle]),
            font=fnt, fill=WHITE)
    #draw.text((0, 172), "Ta = %.1f\u00b0" % display_unit(ta),
    #        font=fnt, fill=WHITE)
    draw.text((0, 172), "\u03b5 = %0.2f" % emissivity, font=fnt, fill=WHITE)
    draw.text((84, 172), "%.1f\u00b0 < T < %.1f\u00b0" %
            (display_unit(min_temp), display_unit(max_temp)),
            font=fnt, fill=WHITE)

    draw_scale(draw, min_temp, max_temp)
    draw_reticle(draw)
    draw_minmax(min_pt, max_pt)
    draw_selected(draw, frame)

# fetch and apply parameters
dev.dump_eeprom()
init_text("EEPROM settings fetched")
dev.extract_parameters()

init_text("Camera parameters applied")

wait_for_valid = 0
while True:

    try:
        dev.get_frame_data()
        ta = dev.get_ta() - 8.0 # ambient adjustment
        frame = dev.calculate_to(emissivity, ta)
        if wait_for_valid < 2:
            if wait_for_valid == 0:
                init_text("Waiting for valid data...")
            wait_for_valid += 1
            continue
        render(last_frame if freeze_frame else frame,
                last_ta if freeze_frame else ta)
        if not freeze_frame:
            last_frame = frame
            last_ta = ta
            is_dirty = True
            saving = False
        else:
            freeze_frame_status()
        disp.display(image)

    except ValueError as err:
        # these happen, no biggie - retry
        print("Got an error: %s" % err)
        continue
