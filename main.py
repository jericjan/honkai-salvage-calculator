"The Main File"

import re
from tkinter import Label, Tk, Frame, filedialog, Button
from tkinter.messagebox import showinfo, askyesno
from threading import Thread
import sys
import os
import time
import math
from datetime import datetime, timedelta

import cv2
import numpy as np
from PIL import ImageGrab, Image
import pyautogui as pg
from pytesseract import pytesseract
from win32gui import FindWindow, GetWindowRect



img_dict = {
    "phase_shifters": "Phase Shifters",
    "twin_sakura_will": "Twin Sakura Will",
    "torus": "Einstein's Torus",
    "nano": "Nanoceramic",
    "skill_mats": "Advanced Skill Material",
}

sellables = {
    "twin_sakura_will": "Twin Sakura Will",
    "nano": "Nanoceramic",
    "skill_mats": "Advanced Skill Material",
}

PATH_TO_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if not os.path.exists(PATH_TO_TESSERACT):
    tesseract_installed = askyesno(
        title="Tesseract not found",
        message="Can't find Tesseract. Do you have it installed?",
    )
    if tesseract_installed:
        PATH_TO_TESSERACT = filedialog.askopenfilename(
            title="Select the location of tesseract.exe",
            filetypes=[("Tesseract", "tesseract.exe")],
        )
    else:
        sys.exit()
pytesseract.tesseract_cmd = PATH_TO_TESSERACT
window = Tk()
info = Frame(window, name="info")
info.pack(side="top", fill="x")
solutions_frame = Frame(window, name="solutions")
solutions_frame.pack(side="top", fill="x", pady=10)


def get_window_size():
    "Gets the game's window size"
    try:
        window_rect = GetWindowRect(FindWindow(None, "Honkai Impact 3"))
    except:
        try:
            window_rect = GetWindowRect(FindWindow(None, "Honkai Impact 3rd"))
        except:
            showinfo(
                title="Game not running",
                message="Can't find a running HI3 game. Exiting...",
            )
            sys.exit()
    left, top, width, height = window_rect
    width = width - left
    height = height - top
    return (width, height)


if get_window_size() != (1286, 749):
    showinfo(
        title="Hey!",
        message="The game needs to be running in 1280x720 windowed mode for this program to work. Sorry.",
    )
    sys.exit()


def make_gui():
    "makes the GUI for the # of items, and items needed to be sold"
    
    scan_mats_button = Button(master=info,text="Scan Mats",command=lambda: run_in_thread(scanner))
    scan_mats_button.pack()    
    
    for name, clean_name in img_dict.items():
        lbl = Label(master=info, name=name, text=f"{clean_name}: [Not detected]")
        lbl.pack()

    for idx, thing in enumerate(sellables.items()):
        name, clean_name = thing
        chunk_frame = Frame(solutions_frame, name=str(idx))
        chunk_frame.pack(side="top")
        lbl = Label(master=chunk_frame, text="You should sell:")
        lbl.pack(side="left")
        lbl = Label(master=chunk_frame, name=name, text=f"?? {clean_name}")
        lbl.pack(side="left")
    stam_button = Button(master=window,text="Calculate Stamina",command=lambda: run_in_thread(stamina))
    stam_button.pack()
    stam_text = Label(master=window,name="stam_text",text="")
    stam_text.pack()
    window.title("Salvage calculator")
    calc_thread = Thread(target=calculate)
    calc_thread.daemon = True
    calc_thread.start()    

def stamina():
    screen = np.array(ImageGrab.grab())
    screen = cv2.cvtColor(src=screen, code=cv2.COLOR_BGR2RGB)
    thing = pg.locate(f"images/stamina.png", screen, confidence=0.8)
    if thing:
        start_row = thing.top +10
        end_row = thing.top + thing.height
        start_column = thing.left + thing.width
        end_column = start_column + 120
        cropped = screen[start_row:end_row, start_column:end_column]
        cropped = cv2.bitwise_not(cropped)
        white = [255, 255, 255]
        red = [0, 0, 255]
        cropped = make_border(cropped, white, 5)
        cropped = make_border(cropped, red, 3)
        cropped = make_border(cropped, white, 2)
        cropped = make_border(cropped, red, 1)    
        text = pytesseract.image_to_string(cropped)
        label = window.nametowidget(".stam_text")
        if re.findall(r"\d{1,3}/\d{1,3}",text):
            curr_stam, max_stam = [int(x) for x in text.strip().split('/')]
            full_hours = (max_stam - curr_stam) / 10
            hours = math.floor(full_hours)
            if not (full_hours % 1) == 0:
                minutes = (full_hours - hours) * 60
            else:
                minutes = 0
            time_when_max = (datetime.now() + timedelta(hours=hours,minutes=minutes)).strftime('%b %d - %I:%M %p')
            label.configure(text=f"{curr_stam}/{max_stam}\n" \
            f"Full stamina in {hours}H:{minutes:.0f}M\n" \
            f"{time_when_max}")
        else:        
            label.configure(text="I scanned it wrong.")
    
    
def calculate():
    "calculates the # of items needed to be sold"
    shifter_count = get_value("phase_shifters")
    will_count = get_value("twin_sakura_will")
    if shifter_count and will_count:
        sell_will = will_count - (shifter_count / 3)
        sell_will = max(sell_will, 0)
        label = window.nametowidget(".solutions.0.twin_sakura_will")
        label.configure(text=f"{sell_will:.2f} Twin Sakura Will(s)")

    torus_count = get_value("torus")
    nano_count = get_value("nano")
    if torus_count and nano_count:
        sell_nano = nano_count - ((torus_count * 45) / 100)
        sell_nano = max(sell_nano, 0)
        label = window.nametowidget(".solutions.1.nano")
        label.configure(text=f"{sell_nano:.2f} Nanoceramic(s)")

    skill_mats_count = get_value("skill_mats")
    if skill_mats_count:
        sell_mats_1 = skill_mats_count - 80
        sell_mats_2 = skill_mats_count - 30
        sell_mats_1 = max(sell_mats_1, 0)
        sell_mats_2 = max(sell_mats_2, 0)
        label = window.nametowidget(".solutions.2.skill_mats")
        label.configure(text=f"{sell_mats_1}-{sell_mats_2} Advanced Skill Material(s)")

    window.after(1000, calculate)


def get_value(name):
    "gets the label item's value"
    try:
        label = window.nametowidget(f".info.{name}")
    except KeyError:
        return False
    text = label["text"]
    value = re.findall(r"\d+", text)
    if value:
        return int(value[0])
    return False


def adjust_contrast_brightness(img, contrast: float = 1.0, brightness: int = 0):
    """
    Adjusts contrast and brightness of an uint8 image.
    contrast:   (0.0,  inf) with 1.0 leaving the contrast as is
    brightness: [-255, 255] with 0 leaving the brightness as is
    """
    brightness += int(round(255 * (1 - contrast) / 2))
    return cv2.addWeighted(img, contrast, img, 0, brightness)


def make_border(img, color, thickness):
    "adds borders to an image"
    return cv2.copyMakeBorder(
        img,
        thickness,
        thickness,
        thickness,
        thickness,
        cv2.BORDER_CONSTANT,
        value=color,
    )


def thing_locater(screen, filename, name):
    "Looks for the item on the screen and sends the amount to the GUI"
    thing = pg.locate(f"images/{filename}.png", screen, confidence=0.8)
    if thing:
        # crops to the target item count
        start_row = thing.top + thing.height
        end_row = start_row + 30
        start_column = thing.left + 20
        end_column = thing.left + thing.width - 20
        cropped = screen[start_row:end_row, start_column:end_column]

        # masks the image to be clearer
        lower_color = np.array([0, 0, 19])
        upper_color = np.array([0, 0, 71])
        frame_hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(frame_hsv, lower_color, upper_color)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        cropped = cv2.cvtColor(cropped, cv2.COLOR_RGB2RGBA)
        cropped = cv2.bitwise_and(cropped, cropped, mask=mask)

        # uses PIL to crop to bounding box of the numbers
        pilimage = Image.fromarray(cropped)
        pilimage = pilimage.crop(pilimage.getbbox())
        cropped = np.array(pilimage)

        # add white bg
        trans_mask = cropped[:, :, 3] == 0
        cropped[trans_mask] = [255, 255, 255, 255]

        # inverts
        cropped = cv2.bitwise_not(cropped)

        # adjusts brightness and contrast
        cropped = adjust_contrast_brightness(cropped, 2, 1)

        # inverts again, idk
        cropped = cv2.bitwise_not(cropped)

        # adds borders
        white = [255, 255, 255]
        red = [0, 0, 255]
        cropped = make_border(cropped, white, 5)
        cropped = make_border(cropped, red, 3)
        cropped = make_border(cropped, white, 2)
        cropped = make_border(cropped, red, 1)

        # reads the numbers
        text = pytesseract.image_to_string(cropped)
        if text.strip():
            text = text.strip()
            if re.search(r"x +\d+|x\d+|\d+", text):
                text = re.findall(r"\d+", text)[0]
                try:
                    label = window.nametowidget(f".info.{filename}")
                except KeyError:
                    print(f"'.{filename}' not found")
                    return
                print(f"{name} - {text.strip()}")
                label.configure(text=f"{name}: {text}")

def run_in_thread(func):
    le_thread = Thread(target=func)
    le_thread.start()
def scanner():
    "calls thing_locater in threads"
    start_time = time.time()
    threads = []
    for filename, name in img_dict.items():
        print(f"Looking for {filename}...")
        screen = np.array(ImageGrab.grab())
        screen = cv2.cvtColor(src=screen, code=cv2.COLOR_BGR2RGB)
        locater_thread = Thread(target=thing_locater, args=(screen, filename, name))
        threads.append(locater_thread)

    # Start them all
    for thread in threads:
        thread.start()

    print(f"---------------END - {(time.time() - start_time):.2f}")
        
        


gui_thread = Thread(target=make_gui)
gui_thread.daemon = True
gui_thread.start()

window.mainloop()
