"The Main File"

import re
from tkinter import Label, Tk, Frame, filedialog
from tkinter.messagebox import showinfo, askyesno
from threading import Thread
import sys
import os
import time

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
    window.title("Salvage calculator")


def calculate():
    "calculates the # of items needed to be sold"
    shifter_count = get_value("phase_shifters")
    will_count = get_value("twin_sakura_will")
    if shifter_count and will_count:
        sell_will = will_count - (shifter_count / 3)
        sell_will = max(sell_will, 0)
        label = window.nametowidget(".solutions.0.twin_sakura_will")
        label.configure(text=f"{sell_will} Twin Sakura Will(s)")

    torus_count = get_value("torus")
    nano_count = get_value("nano")
    if torus_count and nano_count:
        sell_nano = nano_count - ((torus_count * 45) / 100)
        sell_nano = max(sell_nano, 0)
        label = window.nametowidget(".solutions.1.nano")
        label.configure(text=f"{sell_nano} Nanoceramic(s)")

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


def scanner():
    "calls thing_locater in threads"
    found_all = False
    while not found_all:
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

        # Wait for all to complete
        for thread in threads:
            thread.join()
        print(f"---------------END - {(time.time() - start_time):.2f}")
        
        found_items = [get_value(item) for item in img_dict]
        if all(found_items):
           found_all = True            

thread = Thread(target=scanner)
thread.daemon = True
thread2 = Thread(target=make_gui)
thread2.daemon = True
thread3 = Thread(target=calculate)
thread3.daemon = True
thread.start()
thread2.start()
thread3.start()
window.mainloop()
