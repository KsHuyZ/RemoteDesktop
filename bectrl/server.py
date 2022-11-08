from asyncio import start_server
import struct
import socket
from PIL import ImageGrab
from cv2 import cv2
import numpy as np
import threading
import time
import pyautogui as ag
import mouse
from _keyboard import getKeycodeMapping
from tkinter import messagebox


port = 9999
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 140))
ip = s.getsockname()[0]


# 画面周期
IDLE = 0.05

# Mouse wheel sensitivity
SCROLL_NUM = 5

bufsize = 1024

host = ('0.0.0.0', 140)
# A TCP based echo server
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the IP address and the port number
soc.bind(host)
# listen for incoming connections
soc.listen(1)
# Compression ratio 1-100 The smaller the value, the higher the compression ratio and the more serious the loss of image quality.
IMQUALITY = 50

lock = threading.Lock()

# if sys.platform == "win32":
#     from ._keyboard_win import keycodeMapping
# elif platform.system() == "Linux":
#     from ._keyboard_x11 import keycodeMapping
# elif sys.platform == "darwin":
#     from ._keyboard_osx import keycodeMapping

# ctrl device by listen action by socket


def ctrl(conn):
    '''
    Read control commands and restore operations locally
    '''
    keycodeMapping = {}

    def Op(key, op, ox, oy):
        # print(key, op, ox, oy)
        if key == 4:
            # mouse move
            mouse.move(ox, oy)
        elif key == 1:
            if op == 100:
                # left mouse down
                ag.mouseDown(button=ag.LEFT)
            elif op == 117:
                # left mouse up
                ag.mouseUp(button=ag.LEFT)
        elif key == 2:
            # scroll
            if op == 0:
                # up
                ag.scroll(-SCROLL_NUM)
            else:
                # down
                ag.scroll(SCROLL_NUM)
        elif key == 3:
            # mousse right click
            if op == 100:
                # mousse right click
                ag.mouseDown(button=ag.RIGHT)
            elif op == 117:
                # none
                ag.mouseUp(button=ag.RIGHT)
        else:
            k = keycodeMapping.get(key)
            if k is not None:
                if op == 100:
                    ag.keyDown(k)
                elif op == 117:
                    ag.keyUp(k)
    try:
        plat = b''
        while True:
            plat += conn.recv(3-len(plat))
            if len(plat) == 3:
                break
        print("Plat:", plat.decode())
        keycodeMapping = getKeycodeMapping(plat)
        base_len = 6
        while True:
            cmd = b''
            rest = base_len - 0
            while rest > 0:
                cmd += conn.recv(rest)
                rest -= len(cmd)
            key = cmd[0]
            op = cmd[1]
            x = struct.unpack('>H', cmd[2:4])[0]
            y = struct.unpack('>H', cmd[4:6])[0]
            Op(key, op, x, y)
    except:
        return


# compressed np image
img = None
# encoded image
imbyt = None


def handle(conn):
    global img, imbyt
    lock.acquire()
    if imbyt is None:
        imorg = np.asarray(ImageGrab.grab())
        _, imbyt = cv2.imencode(
            ".jpg", imorg, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
        imnp = np.asarray(imbyt, np.uint8)
        img = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
    lock.release()
    lenb = struct.pack(">BI", 1, len(imbyt))
    conn.sendall(lenb)
    conn.sendall(imbyt)
    while True:
        # fix for linux
        time.sleep(IDLE)
        gb = ImageGrab.grab()
        imgnpn = np.asarray(gb)
        _, timbyt = cv2.imencode(
            ".jpg", imgnpn, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
        imnp = np.asarray(timbyt, np.uint8)
        imgnew = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
        # Calculate image difference
        imgs = imgnew ^ img
        if (imgs != 0).any():
            # image quality change
            pass
        else:
            continue
        imbyt = timbyt
        img = imgnew
        # lossless compression
        _, imb = cv2.imencode(".png", imgs)
        l1 = len(imbyt)  # original image size
        l2 = len(imb)  # difference image size
        if l1 > l2:
            # transmit differentiated images
            lenb = struct.pack(">BI", 0, l2)
            conn.sendall(lenb)
            conn.sendall(imb)
        else:
            # Pass the original encoded image
            lenb = struct.pack(">BI", 1, l1)
            conn.sendall(lenb)
            conn.sendall(imbyt)


while True:
    conn, addr = soc.accept()
    answer =  messagebox.askyesno(title="Confirmation",
                             message="Someone connected to you")
    if(answer is True):
        threading.Thread(target=handle, args=(conn,)).start()
        threading.Thread(target=ctrl, args=(conn,)).start()
        print("Starting listening connect!")

    
    if soc.close():
        print("Stop connected")
        break
