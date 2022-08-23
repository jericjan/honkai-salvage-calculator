import cv2
import numpy as np
from PIL import ImageGrab, Image
import pyautogui as pg
from pytesseract import pytesseract
from tkinter import StringVar, Button, Label, Tk, Frame
from threading import Thread
import re
import uuid
img_dict = {
    "phase_shifters":"Phase Shifters",
    "twin_sakura_will":"Twin Sakura Will",
    "torus":"Einstein's Torus",
    "nano":"Nanoceramic",
    "skill_mats":"Advanced Skill Material"
}

sellables = {
    "twin_sakura_will":"Twin Sakura Will",
    "nano":"Nanoceramic",
    "skill_mats":"Advanced Skill Material"
}
   
path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.tesseract_cmd = path_to_tesseract
window=Tk()
info = Frame(window,name="info")
info.pack(side="top", fill="x")
solutions_frame = Frame(window,name="solutions")
solutions_frame.pack(side="top", fill="x", pady = 10)
def GUI():
    global window
    
    string_vars = {}
    for name in img_dict:
        name = StringVar() 
    for name, clean_name in img_dict.items():
        lbl = Label(master=info, name=name, text=f"{clean_name}: [Not detected]")        
        lbl.pack()
        
        
    for idx, thing in enumerate(sellables.items()):
        name, clean_name = thing
        chunk_frame = Frame(solutions_frame,name=str(idx))
        chunk_frame.pack(side="top")
        lbl = Label(master=chunk_frame, text="You should sell:")
        lbl.pack(side="left")
        lbl = Label(master=chunk_frame, name=name, text=f"?? {clean_name}")
        print(str(lbl))
        lbl.pack(side="left")
    window.title("Salvage calculator")

def calculate():
        shifter_count = get_value("phase_shifters")
        will_count = get_value("twin_sakura_will")
        if shifter_count and will_count:
            sell_will = will_count - (shifter_count / 3)
            if sell_will < 0:
                sell_will = 0
            label = window.nametowidget(".solutions.0.twin_sakura_will")   
            label.configure(text=f"{sell_will} Twin Sakura Will(s)") 
            
        torus_count = get_value("torus")
        nano_count = get_value("nano")
        if torus_count and nano_count:
            sell_nano = nano_count - ( (torus_count * 45) / 100 )
            if sell_nano < 0:
                sell_nano = 0
            label = window.nametowidget(".solutions.1.nano")   
            label.configure(text=f"{sell_nano} Nanoceramic(s)") 

            
        skill_mats_count = get_value("skill_mats")
        if skill_mats_count:
            sell_mats_1 = skill_mats_count - 80
            sell_mats_2 = skill_mats_count - 30
            if sell_mats_1 < 0:
                sell_mats_1 = 0
            if sell_mats_2 < 0:
                sell_mats_2 = 0
            label = window.nametowidget(".solutions.2.skill_mats")   
            label.configure(text=f"{sell_mats_1} or {sell_mats_2} Advanced Skill Material(s)")        

        window.after(1000,calculate)
def get_value(name):
    "gets the label item's value"
    try:
        label = window.nametowidget(f".info.{name}")   
    except KeyError:
        return False
    text = label['text']
    value = re.findall(r"\d+",text)
    if value:
        return int(value[0])
    return False
    

# def increase_brightness(img, value=30):
    # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # h, s, v = cv2.split(hsv)

    # lim = 255 - value
    # v[v > lim] = 255
    # v[v <= lim] += value

    # final_hsv = cv2.merge((h, s, v))
    # img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    # return img

def adjust_contrast_brightness(img, contrast:float=1.0, brightness:int=0):
    """
    Adjusts contrast and brightness of an uint8 image.
    contrast:   (0.0,  inf) with 1.0 leaving the contrast as is
    brightness: [-255, 255] with 0 leaving the brightness as is
    """
    brightness += int(round(255*(1-contrast)/2))
    return cv2.addWeighted(img, contrast, img, 0, brightness)

def scanner():
    print("FOOO")
    while True:
        for filename, name in img_dict.items():
            screen = np.array(ImageGrab.grab())
            screen = cv2.cvtColor(src=screen, code=cv2.COLOR_BGR2RGB)        
            thing = pg.locateOnScreen(f"images/{filename}.png", confidence=0.8)
            if thing:
                start_row = thing.top+thing.height
                end_row = start_row+30
                start_column = thing.left+20
                end_column = thing.left+thing.width-20
                cropped = screen[start_row:end_row,start_column:end_column]  
                lower_blue = np.array([0, 0, 19])
                upper_blue = np.array([0, 0, 71])      
                frame_HSV = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)                
                mask = cv2.inRange(frame_HSV, lower_blue, upper_blue)
                mask  = cv2.GaussianBlur(mask,(5,5),0)
                cropped = cv2.cvtColor(cropped, cv2.COLOR_RGB2RGBA)
                cropped = cv2.bitwise_and(cropped, cropped, mask = mask)
                
                print(cropped.shape)
                pilimage = Image.fromarray(cropped)
                pilimage = pilimage.crop(pilimage.getbbox())
                cropped = np.array(pilimage)
                trans_mask = cropped[:,:,3] == 0
                cropped[trans_mask] = [255, 255, 255, 255]
                
                scale_percent = 500 # percent of original size
                old_dim = (cropped.shape[1], cropped.shape[0])
                width = int(cropped.shape[1] * scale_percent / 100)
                height = int(cropped.shape[0] * scale_percent / 100)
                dim = (width, height)
                  
                # resize image
                # cropped = cv2.resize(cropped, dim, interpolation = cv2.INTER_LANCZOS4)                
                cropped = cv2.bitwise_not(cropped)
                # cropped = increase_brightness(cropped, value=20)
                cropped = adjust_contrast_brightness(cropped, 2, 1)
                # sharpen_filter = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                # cropped = cv2.filter2D(cropped, -1, sharpen_filter)
                # cropped = cv2.resize(cropped, old_dim, interpolation = cv2.INTER_NEAREST)        
                # cropped = cv2.resize(cropped, dim, interpolation = cv2.INTER_AREA)    
                cropped = cv2.bitwise_not(cropped)
                white = [255,255,255]
                thickness = 5
                cropped = cv2.copyMakeBorder(cropped, thickness, thickness, thickness, thickness, cv2.BORDER_CONSTANT,value=white)
                black = [0,0,255]
                thickness = 3
                cropped = cv2.copyMakeBorder(cropped, thickness, thickness, thickness, thickness, cv2.BORDER_CONSTANT,value=black)
                white = [255,255,255]
                thickness = 2
                cropped = cv2.copyMakeBorder(cropped, thickness, thickness, thickness, thickness, cv2.BORDER_CONSTANT,value=white)
                black = [0,0,255]
                thickness = 1
                cropped = cv2.copyMakeBorder(cropped, thickness, thickness, thickness, thickness, cv2.BORDER_CONSTANT,value=black)

                # cropped = cv2.bitwise_not(cropped)
                text = pytesseract.image_to_string(cropped)
                
                if text.strip():
                    print(f"1 - {name} - {text.strip()}")
                    text = text.strip()
                    if re.search(r"x +\d+|x\d+|\d+",text):
                        text = re.findall(r"\d+",text)[0]
                        try:
                            label = window.nametowidget(f".info.{filename}")   
                        except KeyError:
                            print(f"'.{filename}' not found")
                            continue
                        print(f"{name} - {text.strip()}")
                        label.configure(text=f"{name}: {text}") 
                # cv2.imshow("uncropped", screen[thing.top:thing.top+thing.height,thing.left:thing.left+thing.width]) 
                # cv2.imshow("cropped", cropped) 
                # cv2.imshow("cropped", cropped) 
                # cv2.waitKey(1)
                # cv2.imwrite("thing.png", cropped)
            else:
                pass
                # print("Not found")

thread = Thread(target = scanner)
thread2 = Thread(target = GUI)
thread3 = Thread(target = calculate)
thread.start()
thread2.start()
thread3.start()
window.mainloop()    
