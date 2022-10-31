from ast import Str
from email import message
from math import radians
from msilib.schema import Error
import tkinter
from tkinter import *
import tkinter.messagebox
import struct
import socket
from turtle import color
import numpy as np
from PIL import Image, ImageTk
import threading
from vidstream import *
import re
from cv2 import cv2
import time
import sys
import platform
import pyperclip
from plyer import notification

root = tkinter.Tk()

nunitoFont = "Nunito 13 bold"

# get ip


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip = s.getsockname()[0]
val = tkinter.StringVar()

root.title("YourViewer")

root.iconbitmap(r'../img/desktop.ico')
root.geometry("800x600")
root.configure(bg="#1e1e1e")


#import image
connect_icon = PhotoImage(file="../img/connect.png")
size_icon = PhotoImage(file="../img/size.png")
ip_icon = PhotoImage(file="../img/ip.png")
transfer_icon = PhotoImage(file="../img/transfer.png")
copy_icon = PhotoImage(file="../img/copy.png")


# layout config
right_frame = Frame(root, width=800, bg="#1e1e1e")
right_frame.grid(row=0, column=0)


ipConnect_frame = Frame(right_frame, width=200, height=600, bg="#1e1e1e")
ipConnect_frame.grid(row=0, column=1)
ipConnectTitle_frame = Frame(
    ipConnect_frame, width=200, height=600, bg="#1e1e1e")
ipConnectTitle_frame.grid(row=0, column=0)
Label(ipConnectTitle_frame, text="Allow Remote Control",  fg="white", bg="#1e1e1e",
      font=(nunitoFont)).grid(row=0, column=0)
ipConnectContent_frame = Frame(ipConnect_frame, width=190, height=600,
                               bg="#252526")
ipConnectContent_frame.grid(row=1, column=0, ipadx=20, ipady=5)
Label(ipConnectContent_frame, text="Your IP :", image=ip_icon, fg="white", bg="#252526",
      font=(nunitoFont), compound=LEFT).grid(row=0, column=0)

Label(ipConnectContent_frame, text=ip, fg="white", bg="#252526",
      font=("Nunito 16 bold")).grid(row=1, column=0, padx=10, pady=5)


ipControl_frame = Frame(right_frame, width=200, height=600, bg="#1e1e1e")
ipControl_frame.grid(row=0, column=2)
ipControlTitle_frame = Frame(
    ipControl_frame, width=200, height=600, bg="#1e1e1e")
ipControlTitle_frame.grid(row=0, column=0)
Label(ipControlTitle_frame, text="Control Remote Computer",  fg="white", bg="#1e1e1e",
      font=(nunitoFont)).grid(row=0, column=0)

ipControlContent_frame = Frame(ipControl_frame, width=190, height=200,
                               bg="#252526")
ipControlContent_frame.grid(row=1, column=0, ipadx=20, ipady=5)
Label(ipControlContent_frame, text=" Partner IP :", image=transfer_icon, fg="white", bg="#252526",
      font=(nunitoFont), compound=LEFT).grid(row=0, column=0)


# img/s
IDLE = 0.05

# scale
scale = 1

# Initial transmission screen size
fixw, fixh = 0, 0

# scale flag
wscale = False

# show canvas
showcan = None

# socket缓冲区大小
bufsize = 10240

# 线程
th = None

# socket
soc = None

# socks5

socks5 = None

# Platform
PLAT = b''
if sys.platform == "win32":
    PLAT = b'win'
elif sys.platform == "darwin":
    PLAT = b'osx'
elif platform.system() == "Linux":
    PLAT = b'x11'

# Create socket


def SetSocket(hs):
    global soc, host_en

    # create socket connect
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.connect((hs[0], int(hs[1])))


def Copy():
    pyperclip.copy(ip+":80")
    notification.notify(title="Copy", message="Copy to cliboard",
                        app_icon="../img/desktop.ico", app_name="YourViewer", timeout=10)


Button(ipConnectContent_frame,  text="Copy", width=120, image=copy_icon, command=Copy, font=(
    nunitoFont), fg="white", bg="#515092", border=None, cursor="hand2", compound=LEFT).grid(row=2, column=0)


def SetScale(x):
    global scale, wscale
    scale = float(x) / 100
    wscale = True


def ShowProxy():
    # show proxy settings
    global root

    def set_s5_addr():
        global socks5
        socks5 = s5_en.get()
        if socks5 == "":
            socks5 = None
        pr.destroy()
    pr = tkinter.Toplevel(root)
    s5v = tkinter.StringVar()
    s5_lab = tkinter.Label(pr, text="Socks5 Host:")
    s5_en = tkinter.Entry(pr, show=None, font=('Nunito', 14), textvariable=s5v)
    s5_btn = tkinter.Button(pr, text="OK", command=set_s5_addr)
    s5_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
    s5_en.grid(row=0, column=1, padx=10, pady=10, ipadx=40, ipady=0)
    s5_btn.grid(row=1, column=0, padx=10, pady=10, ipadx=30, ipady=0)
    s5v.set("127.0.0.1:88")


def ShowScreen():
    global showcan, root, soc, th, wscale
    # if(SetSocket() is None):
    #     return
    # host = host_en.get()
    # hs = host.split(":")
    # if len(hs) != 2:
    #     return

    def byipv4(ip, port):
        print("By IpV4")
        return struct.pack(">BBBBBBBBH", 5, 1, 0, 1, ip[0], ip[1], ip[2], ip[3], port)

    def byhost(host, port):
        print("By host")
        d = struct.pack(">BBBB", 5, 1, 0, 3)
        blen = len(host)
        d += struct.pack(">B", blen)
        d += host.encode()
        d += struct.pack(">H", port)
        return d
    host = host_en.get()
    if host is None:
        tkinter.messagebox.showinfo('Error', 'Server setup error!')
        return
    hs = host.split(":")
    if len(hs) != 2:
        tkinter.messagebox.showinfo('Error', 'Server setup error!')
        return
    if socks5 is not None:
        ss = socks5.split(":")
        print(ss)
        if len(ss) != 2:
            tkinter.messagebox.showinfo('Error', 'Wrong proxy settings!')
            return
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((ss[0], int(ss[1])))

        soc.sendall(struct.pack(">BB", 5, 0))
        recv = soc.recv(2)
        if recv[1] != 0:
            tkinter.messagebox.showinfo('Error', 'Proxy Response Error！')
            return
        if re.match(r'^\d+?\.\d+?\.\d+?\.\d+?:\d+$', host) is None:
            # host domain access rights
            hand = byhost(hs[0], int(hs[1]))
            soc.sendall(hand)
        else:
            # host ip access
            ip = [int(i) for i in hs[0].split(".")]
            port = int(hs[1])
            hand = byipv4(ip, port)
            soc.sendall(hand)
        # Proxy Response
        rcv = b''
        while len(rcv) != 10:
            rcv += soc.recv(10-len(rcv))
        if rcv[1] != 0:
            tkinter.messagebox.showinfo(
                'Error', 'The agent responded with an error!')
            return

    if showcan is None:
        wscale = True
        showcan = tkinter.Toplevel(root)
        th = threading.Thread(target=run)
        th.start()
    else:
        soc.close()
        showcan.destroy()


host_en = tkinter.Entry(ipControlContent_frame, show=None,
                        font=('Nunito', 14), textvariable=val)
host_en.grid(row=1, column=0)
show_btn = tkinter.Button(ipControlContent_frame,  text="Connect", width=180, image=connect_icon, command=ShowScreen, font=(
    nunitoFont), fg="white", bg="#515092", border=None, cursor="hand2", compound=LEFT)
show_btn.grid(row=5, column=0, padx=10, pady=30)


# host_lab = tkinter.Label(root, text="Host:")

# host_en = tkinter.Entry(root, show=None, font=('Arial', 14), textvariable=val)


sca_lab = tkinter.Label(ipControlContent_frame, text=" Scale :", image=size_icon,
                        font=nunitoFont, bg="#252526", fg="white", compound=LEFT)
sca = tkinter.Scale(ipControlContent_frame, from_=10, to=100, orient=tkinter.HORIZONTAL, length=100,
                    showvalue=100, resolution=0.1, tickinterval=50, command=SetScale, bg="#515092", fg="white", font=nunitoFont)

sca_lab.grid(row=3, column=0, padx=10, pady=10, ipadx=0, ipady=0)
sca.grid(row=4, column=0, padx=0, pady=0, ipadx=100, ipady=0)


# proxy_btn = tkinter.Button(root, text="Proxy", command=ShowProxy)
# show_btn = tkinter.Button(root, text="Show", command=ShowScreen)
# host_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
# host_en.grid(row=0, column=1, padx=0, pady=0, ipadx=40, ipady=0)
# sca_lab.grid(row=1, column=0, padx=10, pady=10, ipadx=0, ipady=0)
# sca.grid(row=1, column=1, padx=0, pady=0, ipadx=100, ipady=0)
# ip_lab.grid(row=2, column=0, padx=10, pady=10, ipadx=0, ipady=0)
# ips.grid(row=2, column=1, padx=0, pady=0, ipadx=100, ipady=0)
# proxy_btn.grid(row=3, column=0, padx=0, pady=10, ipadx=30, ipady=0)
# show_btn.grid(row=3, column=1, padx=0, pady=10, ipadx=30, ipady=0)
# Button(ipConnectContent_frame, text="Proxy", command=ShowProxy, font=(
#     nunitoFont), fg="white", bg="#515092", border=None, cursor="hand2").grid(row=3, column=0)

sca.set(50)
val.set('127.0.0.1:80')
last_send = time.time()


def BindEvents(canvas):
    global soc, scale
    '''
    Handle Events
    '''
    def EventDo(data):
        soc.sendall(data)
    # Left mouse down

    def LeftDown(e):
        return EventDo(struct.pack('>BBHH', 1, 100, int(e.x/scale), int(e.y/scale)))

    def LeftUp(e):
        return EventDo(struct.pack('>BBHH', 1, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<1>", func=LeftDown)
    canvas.bind(sequence="<ButtonRelease-1>", func=LeftUp)

    # Right mouse down
    def RightDown(e):
        return EventDo(struct.pack('>BBHH', 3, 100, int(e.x/scale), int(e.y/scale)))

    def RightUp(e):
        return EventDo(struct.pack('>BBHH', 3, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<3>", func=RightDown)
    canvas.bind(sequence="<ButtonRelease-3>", func=RightUp)

    # scroll mouse

    if PLAT == b'win' or PLAT == 'osx':
        # windows/mac
        def Wheel(e):
            if e.delta < 0:
                return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
            else:
                return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<MouseWheel>", func=Wheel)
    elif PLAT == b'x11':
        def WheelDown(e):
            return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))

        def WheelUp(e):
            return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<Button-4>", func=WheelUp)
        canvas.bind(sequence="<Button-5>", func=WheelDown)

    # mouse swipe
    # 100ms send
    def Move(e):
        global last_send
        cu = time.time()
        if cu - last_send > IDLE:
            last_send = cu
            sx, sy = int(e.x/scale), int(e.y/scale)
            return EventDo(struct.pack('>BBHH', 4, 0, sx, sy))
    canvas.bind(sequence="<Motion>", func=Move)

    # keyboard
    def KeyDown(e):
        return EventDo(struct.pack('>BBHH', e.keycode, 100, int(e.x/scale), int(e.y/scale)))

    def KeyUp(e):
        return EventDo(struct.pack('>BBHH', e.keycode, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<KeyPress>", func=KeyDown)
    canvas.bind(sequence="<KeyRelease>", func=KeyUp)


def run():
    global wscale, fixh, fixw, soc, showcan
    host = host_en.get()
    hs = host.split(":")
    SetSocket(hs)
    # Send platform information
    soc.sendall(PLAT)
    lenb = soc.recv(5)
    imtype, le = struct.unpack(">BI", lenb)
    imb = b''
    while le > bufsize:
        t = soc.recv(bufsize)
        imb += t
        le -= len(t)
    while le > 0:
        t = soc.recv(le)
        imb += t
        le -= len(t)
    data = np.frombuffer(imb, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    h, w, _ = img.shape
    fixh, fixw = h, w
    imsh = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
    imi = Image.fromarray(imsh)
    imgTK = ImageTk.PhotoImage(image=imi)
    cv = tkinter.Canvas(showcan, width=w, height=h, bg="white")
    cv.focus_set()
    BindEvents(cv)
    cv.pack()
    cv.create_image(0, 0, anchor=tkinter.NW, image=imgTK)
    h = int(h * scale)
    w = int(w * scale)
    while True:
        if wscale:
            h = int(fixh * scale)
            w = int(fixw * scale)
            cv.config(width=w, height=h)
            wscale = False
        try:
            lenb = soc.recv(5)
            imtype, le = struct.unpack(">BI", lenb)
            imb = b''
            while le > bufsize:
                t = soc.recv(bufsize)
                imb += t
                le -= len(t)
            while le > 0:
                t = soc.recv(le)
                imb += t
                le -= len(t)
            data = np.frombuffer(imb, dtype=np.uint8)
            ims = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if imtype == 1:

                img = ims
            else:

                img = img ^ ims
            imt = cv2.resize(img, (w, h))
            imsh = cv2.cvtColor(imt, cv2.COLOR_RGB2RGBA)
            imi = Image.fromarray(imsh)
            imgTK.paste(imi)
        except:
            showcan = None
            ShowScreen()
            return


root.mainloop()
