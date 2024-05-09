import tkinter as tk
import ctypes
user = ctypes.windll.user32

import cv2
from PIL import Image, ImageTk

import copy
import numpy as np

cam_port = 0
cam = cv2.VideoCapture(cam_port)
image_on_canvas = None

import mediapipe as mp

# Initialize MediaPipe Hands module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

    def dump(self):
        return [int(val) for val in (self.left, self.top, self.right, self.bottom)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', ctypes.c_ulong)
    ]


def get_monitors():
    retval = []
    CBFUNC = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)

    def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        # print("cb: %s %s %s %s %s %s %s %s" % (hMonitor, type(hMonitor), hdcMonitor, type(hdcMonitor), lprcMonitor, type(lprcMonitor), dwData, type(dwData)))
        data = [hMonitor]
        data.append(r.dump())
        retval.append(data)
        return 1
    cbfunc = CBFUNC(cb)
    temp = user.EnumDisplayMonitors(0, 0, cbfunc, 0)
    # print(temp)
    return retval


def monitor_areas():
    retval = []
    monitors = get_monitors()
    for hMonitor, extents in monitors:
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        mi.rcMonitor = RECT()
        mi.rcWork = RECT()
        res = user.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
        
        x1, y1 = mi.rcMonitor.left, mi.rcMonitor.top
        x2, y2 = mi.rcMonitor.right, mi.rcMonitor.bottom
        width = x2 - x1
        height = y2 - y1
        
        data = [x1, y1, x2, y2, width, height]
        retval.append(data)
    return retval

def generate_menu(master: tk.Tk, menu: list):
    def menu_command(function):
        def command():
            function()
        return command

    def create_menu_items(parent, items):
        for item in items:
            if item['type'] == 'option':
                parent.add_command(label=item['name'], command=menu_command(item['function']))
            elif item['type'] == 'menu':
                submenu = tk.Menu(parent, tearoff=0)
                parent.add_cascade(label=item['name'], menu=submenu)
                create_menu_items(submenu, item['items'])

    menubar = tk.Menu(master)
    master.config(menu=menubar)

    for item in menu:
        if item['type'] == 'option':
            menubar.add_command(label=item['name'], command=menu_command(item['function']))
        elif item['type'] == 'menu':
            submenu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label=item['name'], menu=submenu)
            create_menu_items(submenu, item['items'])

monitors_areas_ = monitor_areas()
monitor_areas = monitors_areas_[-1]

controller = tk.Tk()

preview_canvas = tk.Canvas(controller, highlightthickness=0, background="#121212")
preview_canvas.pack(fill="both", expand=True)

result, wc_image = cam.read()
wc_height, wc_width, wc_channels = wc_image.shape

cn_width = wc_width
cn_height = wc_height

resized = False

default_fps = 24
fps = copy.copy(default_fps)

sc_w = monitors_areas_[0][4]
sc_h = monitors_areas_[0][5]

controller.geometry(f"{cn_width}x{cn_height}+{int(sc_w / 2 - cn_width / 2)}+{int(sc_h / 2 - cn_height / 2)}")

display = tk.Toplevel(controller)
display.config(background="black")

display.overrideredirect(True)

x_minus = 0 #8
y_minus = 0 #27

display.geometry(f"{monitor_areas[4]}x{monitor_areas[5]}+{monitor_areas[0] - x_minus}+{monitor_areas[1] - y_minus}")

def update():
    controller.title(f"MITouch Controller ; {wc_width}x{wc_height} ; #{cam_port} ; {fps}FPS ; Resized : {resized}")

pvw_points = []
pvw_pointA_x = 0
pvw_pointA_y = 0
pvw_pointB_x = 0
pvw_pointB_y = 0

def calibrate_points(img):
    global image, images, pvw_pointA_x, pvw_pointA_y, pvw_pointB_x, pvw_pointB_y
    # Convertir l'image de la webcam en HSV pour une meilleure détection des couleurs
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower1 = np.array([30, 100, 40])  # Vert (#00FF29)
    upper1 = np.array([80, 255, 255])

    lower4 = np.array([0, 100, 100])  # Bleu
    upper4 = np.array([10, 255, 255])

    # Masque pour isoler les pixels dans la plage de couleur spécifiée
    mask1 = cv2.inRange(hsv_img, lower1, upper1)
    mask4 = cv2.inRange(hsv_img, lower4, upper4)

    # Trouver les contours des objets dans le masque
    contours1, _1 = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours4, _4 = cv2.findContours(mask4, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    overlay_tk_image = ...#ImageTk.PhotoImage(overlay_image)

    # Si des contours sont trouvés
    if contours1:
        max_contour = max(contours1, key=cv2.contourArea)
        x1, y1, w, h = cv2.boundingRect(max_contour)
        #cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 13), 2)
        """if image:
            preview_canvas.delete(image)"""
        #image = canvas.create_image(x, y, anchor=tk.NW, image=overlay_tk_image)
        
        images = []
        images.append(overlay_tk_image)

    if contours4:
        max_contour = max(contours4, key=cv2.contourArea)
        x4, y4, w, h = cv2.boundingRect(max_contour)
        #cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        """if image:
            preview_canvas.delete(image)"""
        #image = canvas.create_image(x, y, anchor=tk.NW, image=overlay_tk_image)
        
        images = []
        images.append(overlay_tk_image)

    for k, line in enumerate(pvw_points):
        preview_canvas.delete(line)
        pvw_points.pop(k)

    if contours1 and contours4:
        pvw_points.append(preview_canvas.create_text(x4, y4, fill="red", text="PointA"))
        pvw_points.append(preview_canvas.create_text(x1, y1, fill="red", text="PointB"))
        pvw_pointA_x, pvw_pointA_y = x4, y4
        pvw_pointB_x, pvw_pointB_y = x1, y1

"""
La Webcam sera pointé vers l'écran, l'écran aura deux points pour calibrer le ratio entre ce que vois la caméra et le canvas de Tkinter.
Les coordonnés des deux points sont dans les variables :
    - pvw_pointA_x
    - pvw_pointA_y
    - pvw_pointB_x
    - pvw_pointB_y
"""

def convertWebcamPointToDisplay(x:int, y:int):
    global cn_width, cn_height, ds_w, ds_h, pvw_pointA_x, pvw_pointA_y, pvw_pointB_x, pvw_pointB_y

    webcam_distance = ((pvw_pointB_x - pvw_pointA_x)**2 + (pvw_pointB_y - pvw_pointA_y)**2)**0.5
    
    canvas_distance = ((ds_w - ds_points_size)**2 + (ds_h - ds_points_size)**2)**0.5
    
    ratio = canvas_distance / webcam_distance
    
    converted_x = int((x - pvw_pointA_x) * ratio + ds_points_size)
    converted_y = int((y - pvw_pointA_y) * ratio + ds_points_size)

    return converted_x, converted_y

def convertDisplayPointToWebcam(x:int, y:int):
    global cn_width, cn_height, ds_w, ds_h, pvw_pointA_x, pvw_pointA_y, pvw_pointB_x, pvw_pointB_y

    webcam_distance = ((pvw_pointB_x - pvw_pointA_x)**2 + (pvw_pointB_y - pvw_pointA_y)**2)**0.5
    
    canvas_distance = ((ds_w - ds_points_size)**2 + (ds_h - ds_points_size)**2)**0.5
    
    ratio = webcam_distance / canvas_distance

    converted_x = int((x - ds_points_size) * ratio + pvw_pointA_x)
    converted_y = int((y - ds_points_size) * ratio + pvw_pointA_y)

    return converted_x, converted_y

pointer_x = 120
pointer_y = 120

landmarks_canvas = []

def drag_pointer(event):
    global pointer_x, pointer_y
    pointer_x, pointer_y = event.x, event.y
    preview_canvas.coords(d, event.x, event.y, event.x + 8, event.y + 8)

"""d = preview_canvas.create_oval(120, 120, 120 + 8, 120 + 8, fill="red")
preview_canvas.tag_bind(d, "<B1-Motion>", drag_pointer)"""

def loop():
    global image_on_canvas, d, dzz, pointer_x, pointer_y
    update()
    if cam.isOpened():
        success, img = cam.read()
        if success:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if resized:
                img = cv2.resize(img, (controller.winfo_width(), controller.winfo_height()))

            calibrate_points(img)
            
            for i_, landmark in enumerate(landmarks_canvas):
                ds.delete(landmark)
                landmarks_canvas.pop(i_)

            results = hands.process(img)
    
            # Check if hands are detected
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Initialize a list to store landmark positions
                    #landmark_positions = []
                    # Extract landmark positions and append to the list
                    image_height, image_width, _ = img.shape
                    for landmark in hand_landmarks.landmark:
                        x = int(landmark.x * image_width)
                        y = int(landmark.y * image_height)
                        #landmark_positions.append((landmark.x, landmark.y))
                        
                        _x, _y = convertWebcamPointToDisplay(x, y)
                        landmarks_canvas.append(ds.create_oval(_x, _y, _x + 10, _y + 10, fill="yellow"))

            """preview_canvas.tag_raise(d)

            _x, _y = convertWebcamPointToDisplay(copy.deepcopy(pointer_x), copy.deepcopy(pointer_y))
            ds.coords(dzz, _x, _y, _x + ds_points_size, _y + ds_points_size)"""

            """_x, _y = convertDisplayPointToWebcam(120, 120)
            if d == None:
                d = preview_canvas.create_oval(_x, _y, _x + 8, _y + 8, fill="red")
            else:
                preview_canvas.delete(d)
                d = preview_canvas.create_oval(_x, _y, _x + 8, _y + 8, fill="red")"""

            img = ImageTk.PhotoImage(Image.fromarray(img))
            if image_on_canvas is None:
                image_on_canvas = preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
            else:
                preview_canvas.itemconfig(image_on_canvas, image=img)
            preview_canvas.image = img
    controller.after(int(1000 / fps), loop)

def change_fps(factor:int, replace:bool=False):
    global fps
    factor = copy.copy(factor)
    if not replace:
        pre = copy.copy(fps) + factor
    else:
        pre = factor
    if pre >= 1:
        fps = pre
    else:
        fps = 1
    update()

def change_resized():
    global resized
    if resized: resized = False
    else: resized = True

menu = [
    {
        "name": "Preview",
        "type": "menu",
        "items": [
            {
                "name": "Change FPS",
                "type": "menu",
                "items": [
                    {
                        "name": "Decrease 50",
                        "type": "option",
                        "function": lambda: change_fps(-50)
                    },
                    {
                        "name": "Decrease 20",
                        "type": "option",
                        "function": lambda: change_fps(-20)
                    },
                    {
                        "name": "Decrease 10",
                        "type": "option",
                        "function": lambda: change_fps(-10)
                    },
                    {
                        "name": "Decrease 5",
                        "type": "option",
                        "function": lambda: change_fps(-5)
                    },
                    {
                        "name": "Decrease 2",
                        "type": "option",
                        "function": lambda: change_fps(-2)
                    },
                    {
                        "name": "Decrease 1",
                        "type": "option",
                        "function": lambda: change_fps(-1)
                    },
                    {
                        "name": f"Reset to {default_fps}",
                        "type": "option",
                        "function": lambda: change_fps(default_fps, True)
                    },
                    {
                        "name": "Increase 1",
                        "type": "option",
                        "function": lambda: change_fps(1)
                    },
                    {
                        "name": "Increase 2",
                        "type": "option",
                        "function": lambda: change_fps(2)
                    },
                    {
                        "name": "Increase 5",
                        "type": "option",
                        "function": lambda: change_fps(5)
                    },
                    {
                        "name": "Increase 10",
                        "type": "option",
                        "function": lambda: change_fps(10)
                    },
                    {
                        "name": "Increase 20",
                        "type": "option",
                        "function": lambda: change_fps(20)
                    },
                    {
                        "name": "Increase 50",
                        "type": "option",
                        "function": lambda: change_fps(50)
                    }
                ]
            },
            {
                "name": "Webcam resize",
                "type": "option",
                "function": change_resized
            }
        ]
    }
]

generate_menu(controller, menu)

ds = tk.Canvas(display, background="white", highlightthickness=0)

class ref:
    w = monitor_areas[4]
    h = monitor_areas[5]
    
class cs:
    w = wc_width
    h = wc_height

if cs.w > cs.h:
    ds_w = int(cs.w * ref.h / cs.h)
    ds_h = int(ref.h)
    ds.configure(width=ds_w, height=ds_h)
else:
    ds_w = int(ref.w)
    ds_h = int(cs.h * ref.w / cs.w)
    ds.configure(width=ds_w, height=ds_h)

ds.place(x=int(ref.w / 2 - ds_w / 2), y=int(ref.h / 2 - ds_h / 2))

ds_points_size = 40

ds_pointA = ds.create_rectangle(0, 0, ds_points_size, ds_points_size, fill="blue", outline="")
ds_pointB = ds.create_rectangle(ds_w - ds_points_size, ds_h - ds_points_size, ds_w, ds_h, fill="green", outline="")

#dzz = ds.create_rectangle(120, 120, 120 + ds_points_size, 120 + ds_points_size, fill="yellow", outline="")

controller.after(800, loop)
controller.mainloop()